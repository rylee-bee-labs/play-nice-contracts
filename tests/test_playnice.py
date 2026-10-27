"""playnice orchestrator regression tests — fully offline.

The authoritative Play-Nice remote is a LOCAL bare repository, the library is
a git-initialized copy of this checkout, and GitHub is a fake `gh` binary
(PLAY_NICE_GH) driven by a JSON scenario. `playnice` runs as a subprocess, so
the tests cover the real CLI surface end to end. No test touches GitHub or the
network: every remote is a path to a temporary bare repo.

Coverage (per the playnice design doc):
  - freshness CURRENT applies the gate; BEHIND / UNREACHABLE fail closed
  - the global floor can raise a pinned manifest; a pinned floor never blocks
  - automatic update policy may re-pin a manifest (review never does)
  - repository behind is fast-forwarded only when clean; dirty is preserved
  - carryover discovery: handoffs, stale commitments, branches, PRs, issues
  - automation (merge / close / prune) runs ONLY with an ACTIVE permit and
    explicit grants; stale permits are re-validated live
  - worker packet inherits the contract bundle + source revision
  - agent failure surfaces as exit 3 and no post-work mutations
  - no-github runs never invoke the gh binary
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import PLAYNICE, REPO, bare_clone, git0, head, run_py

FAKEGH = REPO / "tests" / "fakegh.py"
FAKEAGENT = REPO / "tests" / "fakeagent.py"
EXAMPLE_CONFIG = REPO / "examples" / "global-playnice.yaml"

sys.path.insert(0, str(REPO))  # allow `import tools.playnice.playnice` in unit tests

_TASK = "update the onboarding checklist"

# --------------------------------------------------------------- fixtures


@pytest.fixture()
def lib(tmp_path, library_git_copy):
    """A git-initialized copy of the library checkout (the contract source)."""
    return library_git_copy(tmp_path / "lib")


@pytest.fixture()
def pn_remote(lib, tmp_path):
    """Authoritative play-nice remote (local bare repo)."""
    return bare_clone(lib, tmp_path / "pn_remote.git")


@pytest.fixture()
def fakegh(tmp_path):
    gh = tmp_path / "fakegh"
    shutil.copy(FAKEGH, gh)
    gh.chmod(0o755)
    return gh


def run_lib_ct(lib, args):
    """Run contractctl from a library checkout copy (keeps its own lock in sync)."""
    return run_py(lib / "tools" / "contractctl" / "contractctl.py", args, timeout=120)


def advance_remote(repo, remote, message="new upstream commit"):
    """Commit in `repo` and push, moving the authoritative remote ahead."""
    (repo / "upstream.txt").write_text(message + "\n")
    assert git0(repo, "add", "upstream.txt").returncode == 0
    r = git0(repo, "commit", "-qm", message, "--no-gpg-sign")
    assert r.returncode == 0, r.stderr
    r = git0(repo, "push", "--quiet", str(remote), "main:main")
    assert r.returncode == 0, r.stderr
    return head(repo)


def manifest_text(remote, sha, *, policy="require-current", update="review"):
    return (
        "schema: play-nice/adoption-v1\n"
        "source:\n"
        f"  repository: {remote}\n"
        f"  revision: {sha}\n"
        "always:\n"
        "  - truth-and-evidence\n"
        "  - status-and-state\n"
        "  - recovery-and-history\n"
        "  - ask-for-help\n"
        "freshness:\n"
        f"  policy: {policy}\n"
        "  ref: main\n"
        f"  update: {update}\n"
    )


def make_consumer(
    tmp_path,
    lib,
    pn_remote,
    *,
    policy="require-current",
    update="review",
    source_override=None,
    pre_files=None,
):
    repo = tmp_path / "consumer"
    repo.mkdir()
    git0(repo, "init", "-q", "-b", "main")
    git0(repo, "config", "user.email", "test@example.invalid")
    git0(repo, "config", "user.name", "Test")
    (repo / "baseline.txt").write_text("baseline\n")
    git0(repo, "add", "baseline.txt")
    assert git0(repo, "commit", "-qm", "baseline", "--no-gpg-sign").returncode == 0
    for name, content in (pre_files or {}).items():
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        git0(repo, "add", str(p))
    m = repo / ".contracts" / "adoption.yaml"
    m.parent.mkdir(parents=True)
    m.write_text(
        manifest_text(
            source_override or pn_remote, head(lib), policy=policy, update=update
        )
    )
    git0(repo, "add", str(m))
    assert git0(repo, "commit", "-qm", "adoption", "--no-gpg-sign").returncode == 0
    # the origin is a bare clone of the consumer's FINAL state, so the repo
    # tracks a remote that already contains every commit it has made
    bare_clone(repo, tmp_path / "consumer_remote.git")
    git0(repo, "remote", "add", "origin", str(tmp_path / "consumer_remote.git"))
    assert git0(repo, "fetch", "--quiet", "origin").returncode == 0
    r = git0(repo, "branch", "--set-upstream-to=origin/main", "main")
    assert r.returncode == 0, r.stderr
    return repo


def write_test_config(tmp_path, *, merge=True, close=True, prune=True, agent_py=None):
    cfg = tmp_path / "global.yaml"
    parts = [
        "play_nice:",
        "  freshness: pinned",
        "github:",
        f"  merge_ready_pull_requests: {'true' if merge else 'false'}",
        f"  close_proven_resolved_issues: {'true' if close else 'false'}",
        f"  remove_proven_merged_branches: {'true' if prune else 'false'}",
    ]
    if agent_py:
        parts += [
            "agent:",
            f"  command: {sys.executable}",
            "  args:",
            f"    - {agent_py}",
        ]
    cfg.write_text("\n".join(parts) + "\n", encoding="utf-8")
    return cfg


def pn_env(tmp_path, lib, gh=None, scenario=None, **extra):
    env = {
        **os.environ,
        "PLAY_NICE_LIBRARY": str(lib),
        # isolate from any real user-level global config on this machine
        "PLAY_NICE_CONFIG": str(tmp_path / "no-such-global.yaml"),
    }
    for k, v in extra.items():
        env[str(k)] = str(v)
    if gh is not None:
        env["PLAY_NICE_GH"] = str(gh)
        if scenario is not None:
            sfile = tmp_path / "scenario.json"
            sfile.write_text(json.dumps(scenario), encoding="utf-8")
            env["PLAY_NICE_FAKE_GH_SCENARIO"] = str(sfile)
    return env


def run_pn(args, env, cwd):
    return run_py(PLAYNICE, args, cwd=cwd, env=env, timeout=180)


def gh_log(tmp_path):
    p = tmp_path / "gh.log"
    return p.read_text(encoding="utf-8").splitlines() if p.exists() else []


def ready_pr(n=12, title="a ready change"):
    return {
        "number": n,
        "title": title,
        "headRefName": f"ready-{n}",
        "baseRefName": "main",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "APPROVED",
        "statusCheckRollup": [
            {"name": "ci", "status": "COMPLETED", "conclusion": "SUCCESS"}
        ],
        "url": f"https://example.invalid/pr/{n}",
    }


def scenario(tmp_path, *, prs=None, issues=None, merged=None, merge_fail=False):
    s = {"log": str(tmp_path / "gh.log")}
    if prs is not None:
        s["pr_list"] = prs
    if issues is not None:
        s["issue_list"] = issues
    if merged is not None:
        s["pr_list_merged"] = merged
    if merge_fail:
        s["merge_fail"] = True
    return s


# ========================================================= 1. freshness gate


def test_work_current_permits_and_writes_handoff(lib, pn_remote, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    env = pn_env(tmp_path, lib)
    r = run_pn(
        work := ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "REMOTE FRESHNESS: CURRENT" in r.stdout
    assert "CONTRACT GATE: PASS" in r.stdout
    assert "COMMITMENT: ACTIVE" in r.stdout
    assert "WORK PERMIT: ACTIVE" in r.stdout
    assert (
        "NEXT: agent not launched (--no-launch); preflight permit written" in r.stdout
    )

    permit_path = consumer / ".contracts" / "work-permit.json"
    assert permit_path.is_file()
    permit = json.loads(permit_path.read_text(encoding="utf-8"))
    assert permit["work_permit"] == "ACTIVE"
    assert permit["play_nice"]["status"] == "CURRENT"
    assert permit["play_nice"]["policy"] == "require-current"
    assert permit["play_nice"]["enforced"] is True
    assert permit["repository"]["status"] == "CURRENT"
    assert permit["carryover"]["status"] == "RECONCILED"
    assert permit["contract_gate"] == "PASS"
    assert permit["commitment"]["status"] == "ACTIVE"
    bundle = permit["worker_packet"]["INHERITED_CONTRACT_BUNDLE"]
    assert re.fullmatch(r"[0-9a-f]{64}", bundle)
    assert permit["worker_packet"]["PLAY_NICE_SOURCE_REVISION"] == head(pn_remote)

    hd = consumer / ".agent" / "HANDOFF.md"
    assert hd.is_file()
    assert "NEXT: agent not launched" in hd.read_text(encoding="utf-8")
    sessions = list((consumer / ".contracts" / "sessions").glob("*.json"))
    assert sessions, "session artifact must be written by the gate"


_AGENTS_WITH_VERIFY = """# AGENTS.md

## Verify

Run before calling a change done:

```sh
$ python3 -m pytest -q
ruff check .
```

## Handoff
Write it.
"""


def test_work_permit_carries_the_repo_verify_commands(lib, pn_remote, tmp_path):
    consumer = make_consumer(
        tmp_path, lib, pn_remote, pre_files={"AGENTS.md": _AGENTS_WITH_VERIFY}
    )
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        pn_env(tmp_path, lib),
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "VERIFY: DECLARED (2 command(s) from AGENTS.md)" in r.stdout
    permit = json.loads(
        (consumer / ".contracts" / "work-permit.json").read_text(encoding="utf-8")
    )
    assert permit["verify"]["state"] == "DECLARED"
    assert permit["worker_packet"]["VERIFY"] == ["python3 -m pytest -q", "ruff check ."]


def test_work_without_verify_section_says_unknown_and_still_permits(
    lib, pn_remote, tmp_path
):
    consumer = make_consumer(
        tmp_path, lib, pn_remote, pre_files={"AGENTS.md": "# AGENTS.md\n\n## Rules\nbe kind\n"}
    )
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        pn_env(tmp_path, lib),
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "VERIFY: UNKNOWN (AGENTS.md has no `## Verify` section)" in r.stdout
    assert "WORK PERMIT: ACTIVE" in r.stdout
    permit = json.loads(
        (consumer / ".contracts" / "work-permit.json").read_text(encoding="utf-8")
    )
    assert permit["worker_packet"]["VERIFY"] == []


def test_worker_prompt_names_the_verify_commands():
    from tools.playnice import playnice as pn

    permit = {
        "worker_packet": {},
        "repository": {"branch": "main", "revision": "abc"},
        "play_nice": {"status": "CURRENT", "revision": "def"},
        "verify": {"state": "DECLARED", "commands": ["make test"]},
    }
    prompt = pn.build_agent_prompt(permit, "do it", Path("/lib"))
    assert "Done means this repository's Verify commands pass" in prompt
    assert "$ make test" in prompt
    permit["verify"] = {"state": "UNKNOWN", "reason": "no AGENTS.md"}
    assert "VERIFY: UNKNOWN (no AGENTS.md)" in pn.build_agent_prompt(permit, "x", Path("/l"))


def test_work_behind_blocks_without_permit(lib, pn_remote, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    advance_remote(lib, pn_remote, "move the authoritative remote ahead")
    env = pn_env(tmp_path, lib)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "REMOTE FRESHNESS: BEHIND" in r.stdout
    assert "CONTRACT COMMITMENT: INACTIVE" in r.stdout
    assert "fail closed" in r.stdout
    assert not (consumer / ".contracts" / "work-permit.json").exists()
    assert not (consumer / ".contracts" / "sessions").exists()


def test_work_unreachable_fails_closed(lib, pn_remote, tmp_path):
    gone = tmp_path / "gone.git"
    consumer = make_consumer(tmp_path, lib, pn_remote, source_override=gone)
    env = pn_env(tmp_path, lib)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "REMOTE FRESHNESS: UNREACHABLE" in r.stdout
    assert not (consumer / ".contracts" / "work-permit.json").exists()


def test_global_floor_require_current_blocks_pinned_manifest(lib, pn_remote, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote, policy="pinned")
    advance_remote(lib, pn_remote, "remote moved")
    cfg = write_test_config(tmp_path)
    # floor require-current (default is pinned; raise it here)
    text = cfg.read_text(encoding="utf-8").replace(
        "play_nice:\n  freshness: pinned", "play_nice:\n  freshness: require-current", 1
    )
    cfg.write_text(text, encoding="utf-8")
    env = pn_env(tmp_path, lib)
    r = run_pn(
        [
            "work",
            "--repo",
            str(consumer),
            "--config",
            str(cfg),
            "--no-github",
            "--no-launch",
            _TASK,
        ],
        env,
        consumer,
    )
    assert r.returncode == 2, r.stdout + r.stderr
    assert "(enforced=True)" in r.stdout
    assert "global floor" in r.stdout
    assert not (consumer / ".contracts" / "work-permit.json").exists()


def test_pinned_policy_never_blocks_backward_compat(lib, pn_remote, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote, policy="pinned")
    advance_remote(lib, pn_remote, "remote moved")
    env = pn_env(tmp_path, lib)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "REMOTE FRESHNESS: BEHIND" in r.stdout
    assert "(enforced=False)" in r.stdout
    assert "WORK PERMIT: ACTIVE" in r.stdout
    permit = json.loads(
        (consumer / ".contracts" / "work-permit.json").read_text(encoding="utf-8")
    )
    assert permit["play_nice"]["enforced"] is False


def test_automatic_update_policy_repins(lib, pn_remote, tmp_path):
    """A real contract change past an automatic pin: the equivalence rule does
    NOT apply (normative surfaces differ); playnice syncs the pin and only
    then reaches CURRENT."""
    consumer = make_consumer(tmp_path, lib, pn_remote, update="automatic")
    # mutate AFTER the consumer pinned a clean HEAD, keeping lib self-consistent
    t = lib / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    text = t.read_text()
    # rotate the receipt too: MINOR-class change semantics (validate enforces it)
    m = re.search(r"<!-- contract-receipt: ([a-z-]+) -->", text)
    assert m and m.group(1) == "kestrel-flint-loom", m  # fixture sanity
    text = text.replace(m.group(0), "<!-- contract-receipt: basalt-quill-ember -->")
    assert "version: 2.0.0" in text, "fixture: version moved; update the test"
    text = text.replace("version: 2.0.0", "version: 2.1.0")
    t.write_text(text)
    cl = lib / "CHANGELOG.md"
    cl.write_text(
        cl.read_text().replace(
            "## [Unreleased]\n",
            "## [Unreleased]\n\n- truth-and-evidence 2.0.0 → 2.1.0 (test fixture change)\n",
        )
    )
    idx = lib / "CONTRACT_INDEX.md"
    idx.write_text(
        idx.read_text().replace(
            "| `truth-and-evidence` | Truth and Evidence | 2.0.0 | canonical |",
            "| `truth-and-evidence` | Truth and Evidence | 2.1.0 | canonical |",
        )
    )
    lk = run_lib_ct(lib, ["lock"])
    assert lk.returncode == 0, lk.stdout + lk.stderr  # lock regenerated before commit
    advance_remote(lib, pn_remote, "new attested revision")
    env = pn_env(tmp_path, lib)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "synced: pin refreshed" in r.stdout
    assert "REMOTE FRESHNESS: CURRENT  (after sync)" in r.stdout
    manifest = (consumer / ".contracts" / "adoption.yaml").read_text(encoding="utf-8")
    assert head(lib) in manifest, "manifest pin must be re-pinned to the remote head"


def test_automatic_equivalence_skips_sync_treadmill(lib, pn_remote, tmp_path):
    """Docs-only commits past an automatic pin read CURRENT via the
    equivalence rule: no sync churn, permit issued at the pinned revision."""
    consumer = make_consumer(tmp_path, lib, pn_remote, update="automatic")
    pinned = head(lib)
    advance_remote(lib, pn_remote, "docs-only commit past the pin")
    env = pn_env(tmp_path, lib)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "REMOTE FRESHNESS: CURRENT" in r.stdout
    assert "WORK PERMIT: ACTIVE" in r.stdout
    manifest = (consumer / ".contracts" / "adoption.yaml").read_text(encoding="utf-8")
    assert pinned in manifest, "pin must stay put — equivalence makes syncing pointless"


# ========================================================= 2. repository state


def test_repo_behind_is_fast_forwarded_clean(lib, pn_remote, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    scratch = tmp_path / "scratch"
    r = subprocess.run(
        ["git", "clone", "--quiet", str(consumer), str(scratch)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    git0(scratch, "config", "user.email", "test@example.invalid")
    git0(scratch, "config", "user.name", "Test")
    advance_remote(
        scratch, str(tmp_path / "consumer_remote.git"), "consumer origin moves ahead"
    )
    remote_head = head(scratch)
    assert head(consumer) != remote_head
    env = pn_env(tmp_path, lib)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    permit = json.loads(
        (consumer / ".contracts" / "work-permit.json").read_text(encoding="utf-8")
    )
    assert permit["repository"]["status"] == "CURRENT"
    assert head(consumer) == remote_head, "consumer must be fast-forwarded"


def test_dirty_repo_preserved_not_clobbered(lib, pn_remote, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    (consumer / "wip.txt").write_text("half-finished\n")
    (consumer / "baseline.txt").write_text("locally modified\n")
    env = pn_env(tmp_path, lib)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "REPOSITORY: DIRTY" in r.stdout
    permit = json.loads(
        (consumer / ".contracts" / "work-permit.json").read_text(encoding="utf-8")
    )
    assert permit["repository"]["dirty"] is True
    assert (consumer / "wip.txt").read_text() == "half-finished\n"
    assert (consumer / "baseline.txt").read_text() == "locally modified\n"


# ========================================================= 3. carryover


def test_unfinished_handoff_discovered(lib, pn_remote, tmp_path):
    consumer = make_consumer(
        tmp_path,
        lib,
        pn_remote,
        pre_files={".agent/HANDOFF.md": "NEXT: finish the deploy\n"},
    )
    env = pn_env(tmp_path, lib)
    r = run_pn(["status", "--repo", str(consumer), "--no-github"], env, consumer)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CARRYOVER: partial — PARTIAL" in r.stdout
    assert "handoff:.agent/HANDOFF.md" in r.stdout
    assert "UNKNOWN" in r.stdout


def test_clean_repo_carryover_reconciled(lib, pn_remote, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    env = pn_env(tmp_path, lib)
    r = run_pn(["status", "--repo", str(consumer), "--no-github"], env, consumer)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CARRYOVER: complete — RECONCILED (0 items)" in r.stdout
    assert "REPOSITORY: healthy — CURRENT" in r.stdout
    assert "ADOPTION: healthy — contracts CURRENT" in r.stdout
    data = json.loads(
        run_pn(
            ["status", "--repo", str(consumer), "--no-github", "--json"], env, consumer
        ).stdout
    )
    assert data["carryover"]["state"] == "complete"
    assert data["carryover"]["legacy_state"] == "RECONCILED"
    assert data["adoption"] == "healthy"
    assert data["play_nice"]["status"] == "CURRENT"
    assert data["repository"]["state"] == "healthy"
    assert data["repository"]["status"] == "CURRENT"


# ========================================================= 4. github layer


def test_merge_ready_pr_merged_under_permit(lib, pn_remote, fakegh, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    cfg = write_test_config(tmp_path, agent_py=FAKEAGENT)
    s = scenario(tmp_path, prs=[ready_pr(12)])
    env = pn_env(
        tmp_path,
        lib,
        gh=fakegh,
        scenario=s,
        FAKE_AGENT_LOG=str(tmp_path / "agent.json"),
    )
    r = run_pn(
        ["work", "--repo", str(consumer), "--config", str(cfg), "merge the ready pr"],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "agent finished; reconciling post-work" in r.stdout
    assert "merged: pr:12" in r.stdout
    assert "NEXT: nothing required" in r.stdout
    log = gh_log(tmp_path)
    assert any(l.startswith("pr merge 12 --merge") for l in log), log
    # worker packet inherits the gate's bundle + authoritative revision
    permit = json.loads(
        (consumer / ".contracts" / "work-permit.json").read_text(encoding="utf-8")
    )
    session = json.loads(
        sorted((consumer / ".contracts" / "sessions").glob("*.json"))[-1].read_text(
            encoding="utf-8"
        )
    )
    wp = permit["worker_packet"]
    assert wp["INHERITED_CONTRACT_BUNDLE"] == session["bundle_sha256"]
    assert wp["PLAY_NICE_SOURCE_REVISION"] == session["source"]["revision"]
    assert wp["PARENT_CONTRACT_COMMITMENT"] == "ACTIVE"
    assert wp["PLAY_NICE_SOURCE_REVISION"] == head(pn_remote)
    assert permit["library"] == session["library_revision"]
    # the fake agent received the inhertiance env + prompt
    agent = json.loads((tmp_path / "agent.json").read_text(encoding="utf-8"))
    assert agent["PLAY_NICE_LIBRARY"] == str(lib)
    assert agent["PLAY_NICE_PERMIT"] == str(
        consumer / ".contracts" / "work-permit.json"
    )
    assert "INHERITED CONTRACT BUNDLE" in agent["argv"][-1]
    assert "VERIFY: UNKNOWN (no AGENTS.md)" in agent["argv"][-1]


@pytest.mark.parametrize(
    "mutate,expect_skip,expect_next",
    [
        (
            {
                "statusCheckRollup": [
                    {"name": "ci", "status": "COMPLETED", "conclusion": "FAILURE"}
                ]
            },
            "checks not green",
            "WAITING_FOR_HELP: PR(s) awaiting CI",
        ),
        (
            {"reviewDecision": "REVIEW_REQUIRED"},
            "review required",
            "WAITING_FOR_HELP: a PR requires human review before merge",
        ),
    ],
)
def test_not_ready_prs_are_not_merged(
    lib, pn_remote, fakegh, tmp_path, mutate, expect_skip, expect_next
):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    cfg = write_test_config(tmp_path, agent_py=FAKEAGENT)
    pr = ready_pr(12)
    pr.update(mutate)
    s = scenario(tmp_path, prs=[pr])
    env = pn_env(tmp_path, lib, gh=fakegh, scenario=s)
    r = run_pn(
        ["work", "--repo", str(consumer), "--config", str(cfg), "merge the ready pr"],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "skip: pr:12" in r.stdout
    assert expect_skip in r.stdout
    assert f"NEXT: {expect_next}" in r.stdout
    assert not any(l.startswith("pr merge") for l in gh_log(tmp_path)), gh_log(tmp_path)


def test_conflicting_pr_blocked_not_merged(lib, pn_remote, fakegh, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    cfg = write_test_config(tmp_path, agent_py=FAKEAGENT)
    pr = ready_pr(12)
    pr["mergeable"] = "CONFLICTING"
    pr["reviewDecision"] = "REVIEW_REQUIRED"
    s = scenario(tmp_path, prs=[pr])
    env = pn_env(tmp_path, lib, gh=fakegh, scenario=s)
    r = run_pn(
        ["work", "--repo", str(consumer), "--config", str(cfg), "merge the ready pr"],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "skip: pr:12" in r.stdout
    assert "BLOCKED" in r.stdout
    assert "NEXT: BLOCKED: carryover items: pr:12" in r.stdout
    assert not any(l.startswith("pr merge") for l in gh_log(tmp_path)), gh_log(tmp_path)


def _prepare_permit(lib, pn_remote, tmp_path, task=_TASK):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    env = pn_env(tmp_path, lib)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", task],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    git0(consumer, "add", ".contracts", ".agent")
    assert git0(consumer, "commit", "-qm", "artifacts", "--no-gpg-sign").returncode == 0
    return consumer, env


def test_issue_resolved_by_merged_pr_is_closed(lib, pn_remote, fakegh, tmp_path):
    consumer, env = _prepare_permit(lib, pn_remote, tmp_path)
    cfg = write_test_config(tmp_path)
    s = scenario(
        tmp_path,
        issues=[
            {"number": 7, "title": "leftover", "url": "https://example.invalid/i/7"}
        ],
        merged=[{"number": 5, "title": "fix", "body": "Closes #7"}],
    )
    env = pn_env(
        tmp_path,
        lib,
        gh=fakegh,
        scenario=s,
        FAKE_AGENT_LOG=str(tmp_path / "unused.json"),
    )
    r = run_pn(
        ["reconcile", "--repo", str(consumer), "--config", str(cfg)], env, consumer
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "closed: issue:7" in r.stdout
    assert any(l.startswith("issue close 7") for l in gh_log(tmp_path)), gh_log(
        tmp_path
    )


def test_ambiguous_issue_left_open(lib, pn_remote, fakegh, tmp_path):
    consumer, env = _prepare_permit(lib, pn_remote, tmp_path)
    cfg = write_test_config(tmp_path)
    s = scenario(
        tmp_path,
        issues=[
            {"number": 7, "title": "leftover", "url": "https://example.invalid/i/7"}
        ],
        merged=[],
    )
    env = pn_env(
        tmp_path,
        lib,
        gh=fakegh,
        scenario=s,
        FAKE_AGENT_LOG=str(tmp_path / "unused.json"),
    )
    r = run_pn(
        ["reconcile", "--repo", str(consumer), "--config", str(cfg)], env, consumer
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "keep: issue:7" in r.stdout
    assert not any(l.startswith("issue close") for l in gh_log(tmp_path)), gh_log(
        tmp_path
    )


def test_merged_branch_pruned_and_unmerged_preserved(lib, pn_remote, fakegh, tmp_path):
    consumer, env = _prepare_permit(lib, pn_remote, tmp_path)
    # branch merged into main AND pushed to origin -> prune candidate
    git0(consumer, "checkout", "-q", "-b", "old-feature")
    (consumer / "feature.txt").write_text("feature\n")
    git0(consumer, "add", "feature.txt")
    assert git0(consumer, "commit", "-qm", "feature", "--no-gpg-sign").returncode == 0
    assert git0(consumer, "push", "--quiet", "origin", "old-feature").returncode == 0
    git0(consumer, "checkout", "-q", "main")
    assert (
        git0(consumer, "merge", "-qm", "merge feature", "old-feature").returncode == 0
    )
    assert git0(consumer, "push", "--quiet", "origin", "main").returncode == 0
    # branch NOT merged -> must be preserved
    git0(consumer, "checkout", "-q", "-b", "new-work")
    (consumer / "wip.txt").write_text("wip\n")
    git0(consumer, "add", "wip.txt")
    assert git0(consumer, "commit", "-qm", "wip", "--no-gpg-sign").returncode == 0
    git0(consumer, "checkout", "-q", "main")
    cfg = write_test_config(tmp_path)
    s = scenario(tmp_path, prs=[], issues=[])
    env = pn_env(
        tmp_path,
        lib,
        gh=fakegh,
        scenario=s,
        FAKE_AGENT_LOG=str(tmp_path / "unused.json"),
    )
    r = run_pn(
        ["reconcile", "--repo", str(consumer), "--config", str(cfg)], env, consumer
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "deleted-local: branch:old-feature" in r.stdout
    assert "deleted-remote: branch:old-feature" in r.stdout
    assert "keep: branch:new-work" in r.stdout
    branches = git0(consumer, "branch", "--format=%(refname:short)").stdout.split()
    assert "old-feature" not in branches
    assert "new-work" in branches
    remote_heads = subprocess.run(
        [
            "git",
            "--git-dir",
            str(tmp_path / "consumer_remote.git"),
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
        ],
        capture_output=True,
        text=True,
    ).stdout.split()
    assert "old-feature" not in remote_heads


def test_reconcile_without_permit_is_read_only(lib, pn_remote, fakegh, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    cfg = write_test_config(tmp_path)
    s = scenario(tmp_path, prs=[ready_pr(12)])
    env = pn_env(tmp_path, lib, gh=fakegh, scenario=s)
    r = run_pn(
        ["reconcile", "--repo", str(consumer), "--config", str(cfg)], env, consumer
    )
    assert r.returncode == 4, r.stdout + r.stderr
    assert "no ACTIVE work permit" in r.stdout
    assert not (consumer / ".contracts" / "work-permit.json").exists()
    assert not any(l.startswith("pr merge") for l in gh_log(tmp_path)), gh_log(tmp_path)


def test_stale_permit_blocks_mutations_live_revalidation(
    lib, pn_remote, fakegh, tmp_path
):
    consumer, env = _prepare_permit(lib, pn_remote, tmp_path)
    advance_remote(lib, pn_remote, "authoritative remote moves after the permit")
    cfg = write_test_config(tmp_path)
    s = scenario(tmp_path, prs=[ready_pr(12)])
    env = pn_env(tmp_path, lib, gh=fakegh, scenario=s)
    r = run_pn(
        ["reconcile", "--repo", str(consumer), "--config", str(cfg)], env, consumer
    )
    assert r.returncode == 4, r.stdout + r.stderr
    assert "mutations stay blocked" in r.stdout
    assert not any(l.startswith("pr merge") for l in gh_log(tmp_path)), gh_log(tmp_path)


def test_agent_failure_exits_3_no_mutations(lib, pn_remote, fakegh, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    cfg = write_test_config(tmp_path, agent_py=FAKEAGENT)
    s = scenario(tmp_path, prs=[ready_pr(12)])
    env = pn_env(
        tmp_path,
        lib,
        gh=fakegh,
        scenario=s,
        FAKE_AGENT_LOG=str(tmp_path / "agent.json"),
        FAKE_AGENT_RC="7",
    )
    r = run_pn(
        ["work", "--repo", str(consumer), "--config", str(cfg), "merge the ready pr"],
        env,
        consumer,
    )
    assert r.returncode == 3, r.stdout + r.stderr
    assert "agent exited 7" in r.stdout
    assert "inspect the failure before further mutation" in r.stdout
    assert not any(l.startswith("pr merge") for l in gh_log(tmp_path)), gh_log(tmp_path)


def test_no_github_invokes_nothing(lib, pn_remote, fakegh, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    s = scenario(tmp_path, prs=[ready_pr(12)])
    env = pn_env(tmp_path, lib, gh=fakegh, scenario=s)
    r = run_pn(
        ["work", "--repo", str(consumer), "--no-github", "--no-launch", _TASK],
        env,
        consumer,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert not (tmp_path / "gh.log").exists(), (
        "gh must never be invoked under --no-github"
    )
    r2 = run_pn(
        ["status", "--repo", str(consumer), "--no-github", "--json"], env, consumer
    )
    assert r2.returncode == 0
    assert "github" not in json.loads(r2.stdout)


def test_gh_unavailable_fails_closed(lib, pn_remote, tmp_path):
    consumer, env = _prepare_permit(lib, pn_remote, tmp_path)
    broken = tmp_path / "broken-gh"
    broken.write_text("#!/bin/sh\necho boom >&2\nexit 1\n", encoding="utf-8")
    broken.chmod(0o755)
    cfg = write_test_config(tmp_path)
    env = pn_env(tmp_path, lib, gh=None, FAKE_AGENT_LOG=str(tmp_path / "unused.json"))
    env["PLAY_NICE_GH"] = str(broken)
    r = run_pn(
        ["reconcile", "--repo", str(consumer), "--config", str(cfg)], env, consumer
    )
    out = r.stdout + r.stderr
    assert "GITHUB STATE" in out or "UNKNOWN" in out
    assert not any(l.startswith("pr merge") for l in gh_log(tmp_path) if l), out


# ========================================================= 5. status + config


def test_status_without_adoption_manifest_is_unknown(tmp_path, lib):
    repo = tmp_path / "bare-repo"
    repo.mkdir()
    git0(repo, "init", "-q", "-b", "main")
    git0(repo, "config", "user.email", "test@example.invalid")
    git0(repo, "config", "user.name", "Test")
    (repo / "a.txt").write_text("x\n")
    git0(repo, "add", "a.txt")
    assert git0(repo, "commit", "-qm", "x", "--no-gpg-sign").returncode == 0
    env = pn_env(tmp_path, lib)
    r = run_pn(["status", "--repo", str(repo), "--no-github", "--json"], env, repo)
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads(r.stdout)
    assert data["play_nice"]["status"] == "UNKNOWN"


def test_repo_identity_parses_github_urls(lib, pn_remote, tmp_path):
    consumer = make_consumer(tmp_path, lib, pn_remote)
    import tools.playnice.playnice as pn  # import from the worktree

    assert pn.repo_identity(consumer) is None  # local-path origin -> no -R flag
    git0(
        consumer,
        "remote",
        "set-url",
        "origin",
        "https://github.com/rylee-test/test-repo.git",
    )
    assert pn.repo_identity(consumer) == "rylee-test/test-repo"


def test_example_config_parses_and_validates():
    import tools.playnice.playnice as pn

    cfg = pn.load_global_config(EXAMPLE_CONFIG)
    assert cfg["play_nice"]["freshness"] == "require-current"
    assert cfg["github"]["merge_method"] == "merge"
    assert cfg["agent"]["command"] == "opencode"
    assert cfg["agent"]["args"] == ["run"]


def test_config_errors_fail_loudly(tmp_path, lib):
    import tools.playnice.playnice as pn

    bad = tmp_path / "bad.yaml"
    bad.write_text("bogus_top_key: 1\n", encoding="utf-8")
    with pytest.raises(pn.ConfigError):
        pn.load_global_config(bad)
    bad.write_text("play_nice:\n  freshness: whenever\n", encoding="utf-8")
    with pytest.raises(pn.ConfigError):
        pn.load_global_config(bad)
    bad.write_text("github:\n  merge_ready_pull_requests: maybe\n", encoding="utf-8")
    with pytest.raises(pn.ConfigError):
        pn.load_global_config(bad)


def test_config_values_drop_inline_comments():
    """`command: codex  # my agent` is the command `codex`, and a commented
    boolean is still a boolean; a `#` inside quotes or a word is kept."""
    sys.path.insert(0, str(REPO / "tools" / "playnice"))
    try:
        import playnice as pn
    finally:
        sys.path.pop(0)
    assert pn._coerce("codex  # my agent") == "codex"
    assert pn._coerce("true # yes") is True
    assert pn._coerce('"a # b"  # note') == "a # b"
    assert pn._coerce("x#y") == "x#y"
    assert pn._coerce("[a, b] # list") == ["a", "b"]
