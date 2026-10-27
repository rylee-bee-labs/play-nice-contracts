"""Remote freshness regression tests (v2 contract-proof pack).

Covers the required cases with a LOCAL bare git repository substituted for
the authoritative remote — no test depends on live GitHub network access:

 1. remote == adopted revision -> CURRENT -> commit ACTIVE
 2. remote newer -> commitment cannot become ACTIVE (STALE)
 3. remote unreachable -> UNKNOWN/UNREACHABLE, fail closed under require-current
 4. existing pinned policy keeps backward-compatible behavior
 5. changing the remote revision invalidates an existing commitment
 6. updating to the new revision requires new resolve/attest/commit
 7. worker inheritance preserves source revision + freshness requirements
 8. freshness metadata is written to the session artifact
 9. machine-readable output has deterministic stable values
10. all remotes are local bare repositories (offline); git ls-remote is the
    real deterministic mechanism (no mock of the git layer needed).
"""

import json
import re

import pytest

from conftest import CT, bare_clone, git0, run_py, with_env

_TASK = "rotate the deploy credentials and update the health checks"
_TASK_IMPACT = {
    "truth-and-evidence": "rotation verified by live check, not by report",
    "status-and-state": "statuses use the shared vocabulary with observed_at",
    "recovery-and-history": "rollback documented and journaled before rotation",
    "identity-and-roles": "each deploy role scoped to its own job",
    "ask-for-help": "unknown provider semantics asked, not guessed",
    "secrets-and-data": "rotated credentials handled by reference, never in logs",
    "public-and-private": "rotation notes keep private topology out of public places",
    "testing-and-evidence": "health checks re-run after rotation with command and grade",
    "observability": "dashboards show post-rotation state honestly, not cached green",
}
_INHERITED_IMPACT = {f"{k}=inherited: {k} governed" for k in _TASK_IMPACT}


# --------------------------------------------------------------- fixtures

_RUNTIME = {"ct_path": CT}


@pytest.fixture()
def tmp_repo(tmp_path, library_git_copy):
    """A git-initialized copy of the library (the consuming context)."""
    repo = library_git_copy(tmp_path / "lib")
    # contractctl resolves REPO_ROOT from its own path: use THIS copy so
    # library_revision() and the merge-base ancestry checks run against it
    _RUNTIME["ct_path"] = repo / "tools" / "contractctl" / "contractctl.py"
    yield repo


@pytest.fixture()
def remote(tmp_repo):
    """A local bare repo standing in for the authoritative remote."""
    return bare_clone(tmp_repo, tmp_repo.parent / "remote.git")


@pytest.fixture()
def manifest(tmp_repo, remote):
    """require-current adoption manifest pinned at the local HEAD."""
    sha = git0(tmp_repo, "rev-parse", "HEAD").stdout.strip()
    m = tmp_repo / ".contracts" / "adoption.yaml"
    m.parent.mkdir(exist_ok=True)
    m.write_text(
        "schema: play-nice/adoption-v1\n"
        "source:\n"
        f"  repository: {remote}\n"
        f"  revision: {sha}\n"
        "always:\n"
        "  - truth-and-evidence\n"
        "  - status-and-state\n"
        "  - recovery-and-history\n"
        "  - identity-and-roles\n"
        "  - ask-for-help\n"
        "freshness:\n"
        "  policy: require-current\n"
        "  ref: main\n"
        "  update: review\n"
    )
    return m


def run_ct(args, cwd=None, ct_path=None, env=None):
    return run_py(ct_path or _RUNTIME["ct_path"], args, cwd=cwd, env=with_env(env))


def impact_args(impact: dict) -> list[str]:
    out = []
    for k, v in impact.items():
        out += ["--impact", f"{k}={v}"]
    return out


def _commit(manifest, task, extra=()):
    """Well-formed commit invocation with the full task-impact set."""
    return run_ct(
        [
            "commit",
            "--manifest",
            str(manifest),
            "--task",
            task,
            *impact_args(_TASK_IMPACT),
            *extra,
        ]
    )


def advance_remote(tmp_repo, remote, message="new upstream commit"):
    """Commit locally and push, so the authoritative remote moves ahead."""
    (tmp_repo / "trivia.txt").write_text(message + "\n")
    assert git0(tmp_repo, "add", "trivia.txt").returncode == 0
    r = git0(tmp_repo, "commit", "-qm", message, "--no-gpg-sign")
    assert r.returncode == 0, r.stderr
    r = git0(tmp_repo, "push", "--quiet", str(remote), "main:main")
    assert r.returncode == 0, r.stderr
    return git0(tmp_repo, "rev-parse", "HEAD").stdout.strip()


def repin(manifest, sha):
    manifest.write_text(
        re.sub(r"revision: [0-9a-f]{7,64}", f"revision: {sha}", manifest.read_text())
    )


# --------------------------------------------------------------- 1. CURRENT


def test_current_remote_allows_active_commit(tmp_repo, remote, manifest):
    r = run_ct(["freshness", "--manifest", str(manifest)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "REMOTE FRESHNESS: CURRENT" in r.stdout
    c = _commit(manifest, _TASK)
    assert c.returncode == 0, c.stdout + c.stderr
    assert "CONTRACT COMMITMENT: ACTIVE" in c.stdout
    assert "REMOTE FRESHNESS: CURRENT" in c.stdout


# --------------------------------------------------- 2. remote moved ahead


def test_remote_newer_blocks_commit_as_stale(tmp_repo, remote, manifest):
    advance_remote(tmp_repo, remote, "upstream changed")
    r = run_ct(["freshness", "--manifest", str(manifest)])
    assert r.returncode == 1
    assert "REMOTE FRESHNESS: BEHIND" in r.stdout
    c = _commit(manifest, _TASK)
    assert c.returncode != 0
    assert "REMOTE FRESHNESS: BEHIND" in c.stdout
    assert "CONTRACT COMMITMENT: STALE" in c.stdout
    assert "CONTRACT COMMITMENT: ACTIVE" not in c.stdout


# ----------------------------------------------- 3. unreachable / no pin


def test_unreachable_remote_fails_closed(tmp_repo, remote, manifest):
    m2 = tmp_repo / ".contracts" / "unreachable.yaml"
    m2.write_text(
        manifest.read_text().replace(str(remote), str(tmp_repo.parent / "missing.git"))
    )
    r = run_ct(["freshness", "--manifest", str(m2)])
    assert r.returncode == 2
    assert "REMOTE FRESHNESS: UNREACHABLE" in r.stdout
    c = _commit(m2, _TASK)
    assert c.returncode != 0
    assert "CONTRACT COMMITMENT: INACTIVE" in c.stdout
    assert "CONTRACT COMMITMENT: ACTIVE" not in c.stdout


def test_missing_pin_is_unknown(tmp_repo, remote, manifest):
    m2 = tmp_repo / ".contracts" / "nopin.yaml"
    m2.write_text(manifest.read_text().split("revision:")[0] + "revision: 0000000\n")
    r = run_ct(["freshness", "--manifest", str(m2)])
    assert r.returncode == 2
    assert "REMOTE FRESHNESS: UNKNOWN" in r.stdout


# ------------------------------------------------- 4. pinned compat


def test_pinned_policy_stays_backward_compatible(tmp_repo, remote, tmp_path):
    """Existing behavior: pinned policy never contacts the remote at commit
    and stays ACTIVE even when the remote has moved ahead."""
    sha = git0(tmp_repo, "rev-parse", "HEAD").stdout.strip()
    m = tmp_path / "pinned.yaml"
    m.write_text(
        "schema: play-nice/adoption-v1\n"
        "source:\n"
        f"  repository: {remote}\n"
        f"  revision: {sha}\n"
        "always:\n"
        "  - truth-and-evidence\n"
        "  - status-and-state\n"
        "freshness:\n"
        "  policy: pinned\n"
    )
    advance_remote(tmp_repo, remote)
    r = run_ct(["freshness", "--manifest", str(m)])
    assert "REMOTE FRESHNESS: BEHIND" in r.stdout  # observed when asked...
    c = run_ct(
        [
            "commit",
            "--manifest",
            str(m),
            "--task",
            "rotate the deploy credentials and update the health checks",
            *impact_args(_TASK_IMPACT),
        ]
    )
    assert c.returncode == 0, c.stdout + c.stderr  # ...but never gates pin
    assert "CONTRACT COMMITMENT: ACTIVE" in c.stdout
    art = json.loads(
        next((tmp_path / ".contracts" / "sessions").glob("session-*.json")).read_text()
    )
    assert art["freshness"]["enforced"] is False


# ------------------------- 5. changed remote invalidates a commitment


def test_remote_change_invalidates_existing_commitment(tmp_repo, remote, manifest):
    c = _commit(manifest, _TASK)
    assert c.returncode == 0, c.stdout + c.stderr
    s1 = run_ct(["session-status", "--manifest", str(manifest), "--task", _TASK])
    assert s1.returncode == 0, s1.stdout
    assert "CONTRACT COMMITMENT: ACTIVE" in s1.stdout

    advance_remote(tmp_repo, remote, "upstream changed the contracts")
    s2 = run_ct(["session-status", "--manifest", str(manifest), "--task", _TASK])
    assert s2.returncode != 0
    assert "CONTRACT COMMITMENT: ACTIVE" not in s2.stdout
    assert "STALE" in s2.stdout
    assert "fetch/update" in s2.stdout


# ------------------- 6. adopting a new revision requires the full cycle


def test_recommit_required_after_remote_update(tmp_repo, remote, manifest):
    c = _commit(manifest, _TASK)
    assert c.returncode == 0
    advance_remote(tmp_repo, remote)

    # update: review refuses to auto-adopt newer contracts
    s = run_ct(["sync", "--manifest", str(manifest)])
    assert s.returncode == 2
    assert "REVIEW REQUIRED" in s.stdout
    # read-only inspection stays allowed after the change
    r = run_ct(["resolve", "--manifest", str(manifest), "--task", _TASK])
    assert r.returncode == 0, r.stdout + r.stderr
    # ...but mutation stays blocked until the pin is (re-)reviewed
    c2 = _commit(manifest, _TASK)
    assert c2.returncode != 0

    new_sha = git0(tmp_repo, "rev-parse", "HEAD").stdout.strip()
    repin(manifest, new_sha)
    a = run_ct(
        [
            "attest",
            "--manifest",
            str(manifest),
            "--task",
            _TASK,
            *impact_args(_TASK_IMPACT),
        ]
    )
    assert a.returncode == 0, a.stdout
    assert "CONTRACT GATE: PASS" in a.stdout
    assert run_ct(["freshness", "--manifest", str(manifest)]).returncode == 0
    c3 = _commit(manifest, _TASK)
    assert c3.returncode == 0, c3.stdout + c3.stderr
    assert "CONTRACT COMMITMENT: ACTIVE" in c3.stdout


def test_automatic_equivalence_reads_current_on_docs_drift(tmp_repo, remote, manifest):
    """The pin treadmill ends here: under update: automatic, a provable-ancestor
    pin whose normative surfaces (contracts/ + schema/) are byte-identical to
    the remote reads CURRENT despite post-merge docs commits ahead of the pin."""
    manifest.write_text(
        manifest.read_text().replace("update: review", "update: automatic")
    )
    assert _commit(manifest, _TASK).returncode == 0
    advance_remote(tmp_repo, remote, "docs-only commit past the pin")
    r = run_ct(["freshness", "--manifest", str(manifest)])
    assert r.returncode == 0, r.stdout
    assert "REMOTE FRESHNESS: CURRENT" in r.stdout
    assert "equivalence" in r.stdout
    j = json.loads(run_ct(["freshness", "--manifest", str(manifest), "--json"]).stdout)
    assert j["status"] == "CURRENT"
    assert j["equivalence"]["adopted_verdict"] == "EQUIVALENT"


def test_automatic_contract_change_still_behind(tmp_repo, remote, manifest):
    """Counter-test: when the normative set actually changes, automatic mode
    stays BEHIND — review (sync → re-commit) is still required."""
    manifest.write_text(
        manifest.read_text().replace("update: review", "update: automatic")
    )
    assert _commit(manifest, _TASK).returncode == 0
    # move the remote with a real contract change
    t = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    assert "version: 2.0.0" in t.read_text(), "fixture: version moved; update the test"
    t.write_text(t.read_text().replace("version: 2.0.0", "version: 2.0.1"))
    assert git0(tmp_repo, "add", "-A").returncode == 0
    assert git0(tmp_repo, "commit", "-qm", "contract patch", "--no-gpg-sign").returncode == 0
    assert git0(tmp_repo, "push", "--quiet", str(remote), "main:main").returncode == 0
    r = run_ct(["freshness", "--manifest", str(manifest)])
    assert r.returncode == 1
    assert "REMOTE FRESHNESS: BEHIND" in r.stdout
    assert "equivalence_not_met" in r.stdout
    c = _commit(manifest, _TASK)
    assert "CONTRACT COMMITMENT: ACTIVE" not in c.stdout


def test_review_policy_never_uses_equivalence(tmp_repo, remote, manifest):
    """Equivalence is an update: automatic affordance only; review mode keeps
    strict exact-match semantics (pin lag stays visible until reviewed)."""
    advance_remote(tmp_repo, remote, "docs-only commit past the pin")
    r = run_ct(["freshness", "--manifest", str(manifest)])
    assert r.returncode == 1
    assert "REMOTE FRESHNESS: BEHIND" in r.stdout
    assert "equivalence" not in r.stdout


def test_sync_automatic_updates_pin_but_not_commitment(tmp_repo, remote, manifest):
    manifest.write_text(
        manifest.read_text().replace("update: review", "update: automatic")
    )
    assert _commit(manifest, _TASK).returncode == 0
    # a REAL contract change: sync must repin but the old commitment stays STALE
    t = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    assert "version: 2.0.0" in t.read_text(), "fixture: version moved; update the test"
    t.write_text(t.read_text().replace("version: 2.0.0", "version: 2.0.1"))
    assert git0(tmp_repo, "add", "-A").returncode == 0
    assert git0(tmp_repo, "commit", "-qm", "contract patch", "--no-gpg-sign").returncode == 0
    assert git0(tmp_repo, "push", "--quiet", str(remote), "main:main").returncode == 0
    s = run_ct(["sync", "--manifest", str(manifest)])
    assert s.returncode == 0, s.stdout
    assert "STALE" in s.stdout and "resolve" in s.stdout
    # the pin moved, no fresh commitment was made -> fail closed
    s2 = run_ct(["session-status", "--manifest", str(manifest), "--task", _TASK])
    assert s2.returncode != 0
    assert "STALE" in s2.stdout


# ---------------------------------------- 7. worker inheritance / packets


def test_worker_inherits_freshness_and_source_revision(tmp_repo, remote, manifest):
    orch = _commit(manifest, _TASK, extra=["--role", "orchestrator"])
    assert orch.returncode == 0, orch.stdout + orch.stderr
    assert "REMOTE FRESHNESS: CURRENT" in orch.stdout
    art_dir = tmp_repo / ".contracts" / "sessions"
    parent = json.loads(next(art_dir.glob("orchestrator-*.json")).read_text())

    w = run_ct(
        [
            "commit",
            "--manifest",
            str(manifest),
            "--task",
            "update a compose file",
            "--worker",
            "--parent-bundle",
            parent["bundle_sha256"],
            *impact_args(_TASK_IMPACT),
        ]
    )
    assert w.returncode == 0, w.stdout + w.stderr
    assert "PLAY_NICE_SOURCE_REVISION:" in w.stdout
    assert "INHERITED CONTRACT BUNDLE:" in w.stdout
    assert "PARENT CONTRACT COMMITMENT: ACTIVE" in w.stdout
    wart = json.loads(next(art_dir.glob("worker-*.json")).read_text())
    assert wart["source"]["revision"] == parent["source"]["revision"]
    assert wart["freshness"]["status"] == "CURRENT"

    # a worker whose parent used a different source revision is blocked:
    # workers may not resolve a weaker/older source than their parent
    advance_remote(tmp_repo, remote, "upstream changed again")
    repin(manifest, git0(tmp_repo, "rev-parse", "HEAD").stdout.strip())
    w2 = run_ct(
        [
            "commit",
            "--manifest",
            str(manifest),
            "--task",
            "update a compose file",
            "--worker",
            "--parent-bundle",
            parent["bundle_sha256"],
            *impact_args(_TASK_IMPACT),
        ]
    )
    assert w2.returncode != 0
    assert (
        ("PLAY_NICE_SOURCE_REVISION" in w2.stdout)
        or ("source revision" in w2.stderr)
        or ("REMOTE FRESHNESS" in w2.stdout)
    )


def test_worker_without_parent_bundle_fails_closed(tmp_repo, remote, manifest):
    c = run_ct(
        [
            "commit",
            "--manifest",
            str(manifest),
            "--task",
            "update a compose file",
            "--worker",
            *impact_args(_TASK_IMPACT),
        ]
    )
    assert c.returncode != 0


# ---------------------------------------- 8. freshness metadata in artifact


def test_freshness_metadata_written_to_artifact(tmp_repo, remote, manifest):
    c = _commit(manifest, _TASK)
    assert c.returncode == 0, c.stdout + c.stderr
    art = json.loads(
        next((tmp_repo / ".contracts" / "sessions").glob("session-*.json")).read_text()
    )
    fr = art["freshness"]
    assert fr["status"] == "CURRENT"
    assert fr["policy"] == "require-current"
    assert fr["enforced"] is True
    assert fr["ref"] == "refs/heads/main"
    assert re.match(r"^[0-9a-f]{40}$", fr["remote_revision"])
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", fr["checked_at"])
    assert re.match(r"^[0-9a-f]{40}$", art["play_nice_source_revision"])
    blob = json.dumps(art)  # no secrets by construction
    for bad in ("token", "password", "api_key"):
        assert bad not in blob


# -------------------------------------- 9. machine-readable determinism


def test_freshness_json_is_deterministic(tmp_repo, remote, manifest):
    r1 = run_ct(["freshness", "--manifest", str(manifest), "--json"])
    r2 = run_ct(["freshness", "--manifest", str(manifest), "--json"])
    assert r1.returncode == 0 == r2.returncode
    d1, d2 = json.loads(r1.stdout), json.loads(r2.stdout)
    assert d1 == d2  # stable values across runs (no timestamps in JSON)
    assert d1["status"] == "CURRENT"
    assert d1["policy"] == "require-current"
    assert d1["enforced"] is True
    assert d1["ref"] == "refs/heads/main"
    assert re.match(r"^[0-9a-f]{40}$", d1["remote_revision"])


# ---------------------------------- 10. schema / validation integration


def test_adoption_rejects_invalid_freshness_policy(tmp_path):
    bad = tmp_path / "adoption.yaml"
    bad.write_text(
        "schema: play-nice/adoption-v1\n"
        "source:\n"
        "  repository: rylee-bee-labs/play-nice-contracts\n"
        "  revision: deadbeef\n"
        "freshness:\n"
        "  policy: auto-current\n"
    )
    r = run_ct(["adopt", "--manifest", str(bad)], cwd=str(tmp_path))
    assert r.returncode != 0
    assert "freshness.policy" in r.stdout


# v1 had two tests here asserting the remote-freshness block lived in the
# contract TEXT (contract-attestation 1.3.0 rules 21-27). The v2 pack review
# (docs/research/v2-packs/pack-work.md) deliberately retired that block:
# remote freshness is contractctl behavior, documented in the tool, not a
# contract rule — so the text assertions have no v2 home. The behavior they
# protected is still covered by every test above.


# ---------------------------------------- 11. upgrade-check (composed answer)


def test_upgrade_check_current_says_no_action(tmp_repo, remote, manifest):
    r = run_ct(["upgrade-check", "--manifest", str(manifest)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "no action" in r.stdout


def test_upgrade_check_docs_drift_needs_review_only(tmp_repo, remote, manifest):
    advance_remote(tmp_repo, remote, "docs-only commit past the pin")
    r = run_ct(["upgrade-check", "--manifest", str(manifest)])
    assert r.returncode == 1, r.stdout
    assert "BEHIND" in r.stdout
    assert "next:" in r.stdout


def test_upgrade_check_flags_always_set_impact(tmp_repo, remote, manifest):
    t = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    assert "version: 2.0.0" in t.read_text(), "fixture: version moved; update the test"
    t.write_text(t.read_text().replace("version: 2.0.0", "version: 2.1.0"))
    assert git0(tmp_repo, "add", "-A").returncode == 0
    assert git0(tmp_repo, "commit", "-qm", "contract bump", "--no-gpg-sign").returncode == 0
    assert git0(tmp_repo, "push", "--quiet", str(remote), "main:main").returncode == 0
    r = run_ct(["upgrade-check", "--manifest", str(manifest)])
    assert r.returncode == 1, r.stdout
    assert "MEANINGFUL" in r.stdout
    assert "always-set impact" in r.stdout
    assert "truth-and-evidence" in r.stdout
    assert "re-attestation required" in r.stdout
