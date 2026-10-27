"""Tool friction regression tests (Play-Nice v2 plan, step 1).

One test per usability-report item fixed in tools/contractctl:

  1. init-project wrote `triggers: {}` -> adopt/resolve crashed on the raw
     string; now the parser reads `{}`/`[]` as empty map/list and the
     scaffolded manifest is valid YAML end to end.
  2. adopt printed the same missing-file error twice -> once + next step.
  3. missing manifest says plain words and a next step; resolve and
     freshness agree on fail-closed exit 2.
  4. onboard's and attest's NEXT lines include --manifest.
  5. a shell-split --impact value gets a quoting error, not an argparse dump.
  6. `status` with no manifest in the tree labels itself as library health.
  9. `show <unknown>` suggests `contractctl list` and the closest ids.
 10. resolve --tag on a manifest without triggers says the tag had no effect.
 11. commit --help output default is truthful; --manifest/--task/--revision
     carry help strings; top-level --help lists every subcommand.
 12. contractctl --version exists.
 13. onboard accepts --role agent as an alias of worker.

All tests run offline against this checkout; no network, no GitHub.
"""

import re
from pathlib import Path

from conftest import CT, REPO, run_py

# `lib` (contractctl imported from this checkout) comes from conftest.py.


def run_ct(args, cwd=None):
    return run_py(CT, args, cwd=cwd or REPO)


# --------------------------------------------------------- 1. parser + scaffold


def test_parser_reads_empty_flow_collections(lib):
    """`{}` parses as an empty map and `[]` as an empty list, not strings."""
    assert lib._parse_scalar("{}") == {}
    assert lib._parse_scalar("[]") == []
    assert lib._parse_scalar("{ }") == {}


def test_init_project_then_adopt_and_resolve_succeed(tmp_path):
    """The crash the report found: init-project -> adopt -> resolve must all
    work on the scaffolded manifest, not explode on `triggers: {}`."""
    r = run_ct(["init-project", str(tmp_path), "--id", "scratch", "--name", "Scratch"])
    assert r.returncode == 0, r.stdout + r.stderr
    manifest = tmp_path / ".project" / "contracts" / "adoption.yaml"
    assert manifest.is_file()
    text = manifest.read_text(encoding="utf-8")
    assert "triggers: {}" not in text, "the crashing placeholder is gone"
    assert "PIN-TO-ADOPTED-SHA" not in text, "the manifest is pinned to a real revision"

    a = run_ct(["adopt", "--manifest", str(manifest)])
    assert a.returncode == 0, a.stdout + a.stderr
    assert "ADOPTION VALID" in a.stdout

    res = run_ct(["resolve", "--manifest", str(manifest), "--task", "add a login button"])
    assert res.returncode == 0, res.stdout + res.stderr
    assert "resolved" in res.stdout

    pv = run_ct(["project", "validate", str(tmp_path / ".project")])
    assert pv.returncode == 0, pv.stdout + pv.stderr


# --------------------------------------------- 2. adopt: one error, with a next


def test_adopt_missing_manifest_reports_once_with_next(tmp_path):
    missing = tmp_path / "nope.yaml"
    r = run_ct(["adopt", "--manifest", str(missing)])
    assert r.returncode == 1
    assert "ADOPTION INVALID" in r.stdout
    problem_lines = [ln for ln in r.stdout.splitlines() if "no adoption manifest at" in ln]
    assert len(problem_lines) == 1, r.stdout  # was printed twice before the fix
    assert "next: contractctl init-adoption" in r.stdout


# ------------------------------- 3. missing manifest: plain words, exit 2 both


def _assert_missing_manifest_plain(output: str, path: str) -> None:
    assert "no adoption manifest at" in output
    assert "has not adopted Play-Nice yet" in output
    assert "next: contractctl init-adoption --project" in output
    assert path in output


def test_resolve_without_manifest_uses_library_defaults(tmp_path):
    """v2: no manifest is not an error for resolve; it answers from the
    library defaults and says so. (An explicitly named missing manifest
    still fails closed: tests/test_playnice_v2.py.)"""
    r = run_ct(["resolve", "--task", "add a login button"], cwd=tmp_path)
    assert r.returncode == 0, r.stderr
    assert "resolved from the library defaults" in r.stdout
    assert "floor" in r.stdout


def test_freshness_missing_manifest_fails_closed_exit_2(tmp_path):
    r = run_ct(["freshness"], cwd=tmp_path)
    assert r.returncode == 2  # existing policy kept
    _assert_missing_manifest_plain(r.stderr, ".contracts/adoption.yaml")


# ------------------------------------------------- 4. NEXT lines carry --manifest


def test_onboard_next_step_is_the_proof_line():
    """v2: onboarding starts at the floor and ends with the one-line proof,
    not the retired attest ritual."""
    r = run_ct(["onboard", "--role", "worker"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "contracts/everyone/FLOOR.md" in r.stdout.split("=== HIGH-PRIORITY", 1)[0]
    next_block = r.stdout.split("=== NEXT ===", 1)[1]
    assert "Play-Nice floor" in next_block and "playnice verify" in next_block, next_block
    assert "attest" not in next_block


def _resolved_ids(manifest: Path, task: str) -> list[str]:
    r = run_ct(["resolve", "--manifest", str(manifest), "--task", task])
    assert r.returncode == 0, r.stdout + r.stderr
    return [
        ln.strip()
        for ln in r.stdout.splitlines()
        if re.fullmatch(r"  [a-z0-9-]+", ln)
    ]


def test_attest_next_commit_line_includes_manifest(tmp_path):
    """A passing attest prints the exact next commit command — with --manifest."""
    m = tmp_path / "adoption.yaml"
    m.write_text(
        "schema: play-nice/adoption-v1\n"
        "project: friction\n"
        "source:\n"
        "  repository: rylee-bee-labs/play-nice-contracts\n"
        "  revision: 0000000000000000000000000000000000000000\n"
        "always:\n"
        "  - truth-and-evidence\n"
        "  - explicit-state\n",
        encoding="utf-8",
    )
    task = "fix the settings page copy"
    ids = _resolved_ids(m, task)
    assert ids, "expected a non-empty resolved set"
    impact_args = []
    for cid in ids:
        impact_args += ["--impact", f"{cid}=reviewed and accepted for this task"]
    r = run_ct(["attest", "--manifest", str(m), "--task", task, *impact_args])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CONTRACT GATE: PASS" in r.stdout
    assert f"contractctl commit --manifest {m}" in r.stdout, r.stdout


# ---------------------------------------------- 5. split --impact quoting error


def test_commit_split_impact_value_says_quote_it(tmp_path):
    m = tmp_path / "adoption.yaml"
    r = run_ct(
        [
            "commit",
            "--manifest",
            str(m),
            "--task",
            "add a login button",
            "--impact",
            "truth-and-evidence=UNKNOWN",
            "stays",
            "UNKNOWN",
            "in",
            "status",
            "output",
        ]
    )
    assert r.returncode == 2
    assert "split by the shell" in r.stderr
    assert '--impact "truth-and-evidence=UNKNOWN stays UNKNOWN in status output"' in r.stderr
    assert "--impact-file" in r.stderr


def test_attest_split_impact_value_says_quote_it(tmp_path):
    r = run_ct(
        [
            "attest",
            "--manifest",
            str(tmp_path / "adoption.yaml"),
            "--task",
            "add a login button",
            "--impact",
            "explicit-state=UNKNOWN",
            "is",
            "reported",
            "honestly",
        ]
    )
    assert r.returncode == 2
    assert "split by the shell" in r.stderr
    assert "--impact-file" in r.stderr


def test_unrelated_junk_still_fails_like_argparse(tmp_path):
    r = run_ct(["resolve", "--task", "x", "--bogus-flag"], cwd=tmp_path)
    assert r.returncode == 2
    assert "unrecognized arguments" in r.stderr


# ------------------------------------------- 6. status labels library health


def test_status_without_project_manifest_is_labelled(tmp_path):
    r = run_ct(["status"], cwd=tmp_path)
    out = r.stdout
    assert out.startswith("LIBRARY HEALTH")
    assert "this project: no adoption manifest — run contractctl init-adoption" in out


def test_status_with_project_manifest_is_not_labelled():
    """The library checkout itself carries an adoption manifest; plain output."""
    assert (REPO / ".contracts" / "adoption.yaml").is_file()
    r = run_ct(["status"])
    assert not r.stdout.startswith("LIBRARY HEALTH")
    assert "this project" not in r.stdout


# ----------------------------------------------- 9. show suggestions, 10. tag


def test_show_unknown_suggests_list_and_closest():
    r = run_ct(["show", "truth-and-evidenc"])
    assert r.returncode == 1
    assert "contractctl list" in r.stderr
    assert "closest:" in r.stderr
    assert "truth-and-evidence" in r.stderr


def test_show_unknown_far_miss_still_points_at_list():
    r = run_ct(["show", "not-a-contract"])
    assert r.returncode == 1
    assert "run `contractctl list`" in r.stderr


def test_resolve_tag_without_triggers_says_no_effect(tmp_path):
    m = tmp_path / "adoption.yaml"
    m.write_text(
        "schema: play-nice/adoption-v1\n"
        "project: friction\n"
        "source:\n"
        "  repository: rylee-bee-labs/play-nice-contracts\n"
        "  revision: 0000000000000000000000000000000000000000\n"
        "always:\n"
        "  - truth-and-evidence\n"
        "triggers:\n",
        encoding="utf-8",
    )
    r = run_ct(["resolve", "--manifest", str(m), "--task", "ship it", "--tag", "governance"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "--tag had no effect" in r.stdout


# ------------------------------------------------------ 11. help strings / docs


ALL_SUBCOMMANDS = {
    "list", "show", "validate", "resolve", "lock", "diff", "scan", "index",
    "init-adoption", "upgrade-check", "attest", "verify-attestation", "commit",
    "session-status", "adopt", "init-project", "project", "participant",
    "validate-question", "onboard", "status", "freshness", "sync",
}


def test_top_level_help_lists_every_subcommand():
    r = run_ct(["--help"])
    assert r.returncode == 0
    section = r.stdout.split("Subcommands:", 1)[1].split("Run with --help", 1)[0]
    listed = {ln.strip().split()[0] for ln in section.splitlines() if ln.strip()}
    missing = ALL_SUBCOMMANDS - listed
    assert not missing, f"undocumented in --help prose: {sorted(missing)}"


def test_commit_output_help_matches_real_default():
    r = run_ct(["commit", "--help"])
    assert "library root" not in r.stdout
    assert ".contracts/sessions/<role>-<task>.json" in r.stdout


def test_flag_help_strings_present():
    for cmd, expected in (
        ("resolve", "adoption manifest"),
        ("attest", "library revision to attest against"),
        ("commit", "library revision to commit against"),
        ("adopt", "adoption manifest to validate"),
    ):
        r = run_ct([cmd, "--help"])
        assert r.returncode == 0
        assert expected in r.stdout, (cmd, expected)


# ------------------------------------------------------------- 12. --version


def test_version_flag_exists():
    r = run_ct(["--version"])
    assert r.returncode == 0, r.stdout + r.stderr
    assert re.search(r"contractctl \d+\.\d+\.\d+", r.stdout), r.stdout


# --------------------------------------------- 13. onboard --role agent alias


def test_onboard_role_agent_is_worker_alias():
    agent = run_ct(["onboard", "--role", "agent"])
    worker = run_ct(["onboard", "--role", "worker"])
    assert agent.returncode == 0, agent.stdout + agent.stderr
    assert "role: worker" in agent.stdout
    assert agent.stdout == worker.stdout
