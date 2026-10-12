"""The front door: playnice as the one entry point, consistent defaults.

Covers the usability audit of 2026-10-12, PR 3: status keeps checks,
adoption and work readiness apart; manifest discovery is the same
everywhere; onboard defaults to worker; --version labels each number; the
badge link agrees with its docs; the wrapper works through a symlink.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAYNICE = REPO / "tools" / "playnice" / "playnice.py"
CONTRACTCTL = REPO / "tools" / "contractctl" / "contractctl.py"

sys.path.insert(0, str(REPO / "tools" / "contractctl"))
sys.path.insert(0, str(REPO / "tools" / "playnice"))
import contractctl as ct  # noqa: E402
import playnice as pn  # noqa: E402

FLOOR_V = re.search(
    r"(?m)^version:\s*(\S+)",
    (REPO / "contracts/everyone/FLOOR.md").read_text(encoding="utf-8"),
).group(1)
LIB_V = (REPO / "VERSION").read_text().strip()


def run(tool, args, cwd):
    env = {**os.environ, "PLAY_NICE_LIBRARY": str(REPO)}
    return subprocess.run(
        [sys.executable, str(tool), *args],
        capture_output=True, text=True, cwd=str(cwd), env=env, timeout=120,
    )


def git_repo(path):
    path.mkdir(parents=True, exist_ok=True)
    for a in (["init", "-q"], ["config", "user.email", "t@example.invalid"],
              ["config", "user.name", "T"]):
        subprocess.run(["git", "-C", str(path), *a], check=True)
    (path / "README.md").write_text("# demo\n")
    subprocess.run(["git", "-C", str(path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "init"], check=True)
    return path


# ------------------------------------------------------------ versions


def test_version_lines_label_every_number(tmp_path):
    pv = run(PLAYNICE, ["--version"], tmp_path).stdout.strip()
    cv = run(CONTRACTCTL, ["--version"], tmp_path).stdout.strip()
    assert pv == f"playnice {pn.PLAYNICE_VERSION} · library {LIB_V} · floor {FLOOR_V}"
    assert cv == f"contractctl {LIB_V} · library {LIB_V} · floor {FLOOR_V}"


# ------------------------------------------------------------ defaults


def test_manifest_discovery_is_the_same_in_both_tools():
    import inspect

    src = inspect.getsource(pn.find_adoption_manifest)
    for rel in ct.MANIFEST_CANDIDATES:
        assert f'"{rel}"' in src, rel
    order = [src.index(f'"{rel}"') for rel in ct.MANIFEST_CANDIDATES]
    assert order == sorted(order)


def test_commands_find_a_project_manifest_without_flags(tmp_path):
    (tmp_path / ".project/contracts").mkdir(parents=True)
    (tmp_path / ".project/contracts/adoption.yaml").write_text(
        "schema: play-nice/adoption-v1\nsource:\n"
        "  repository: rylee-bee-labs/play-nice-contracts\n"
        "  revision: 0123456789abcdef0123456789abcdef01234567\n"
        "always:\n  - truth-and-evidence\n"
    )
    assert ct.discover_manifest(tmp_path) == tmp_path / ".project/contracts/adoption.yaml"
    r = run(CONTRACTCTL, ["adopt"], tmp_path)
    assert "0123456789ab" in r.stdout + r.stderr  # it read that manifest
    assert "required" not in r.stderr
    r = run(CONTRACTCTL, ["upgrade-check"], tmp_path)
    assert "required" not in r.stderr


def test_missing_manifest_names_the_expected_place(tmp_path):
    r = run(CONTRACTCTL, ["upgrade-check"], tmp_path)
    assert r.returncode != 0
    assert ".contracts/adoption.yaml" in r.stdout + r.stderr


def test_onboard_defaults_to_worker(tmp_path):
    r = run(CONTRACTCTL, ["onboard"], tmp_path)
    assert r.returncode == 0, r.stderr
    assert "role: worker" in r.stdout


# ------------------------------------------------------------ status


def test_status_separates_checks_adoption_and_readiness(tmp_path):
    repo = git_repo(tmp_path / "plain")
    assert run(PLAYNICE, ["start", str(repo)], tmp_path).returncode == 0
    r = run(PLAYNICE, ["status", "--repo", str(repo), "--no-github"], tmp_path)
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert re.search(r"(?m)^CHECKS: plays nice", out)  # agrees with playnice check
    assert re.search(r"(?m)^ADOPTION: not configured", out)
    assert re.search(r"(?m)^WORK READINESS: blocked — playnice work needs an adoption manifest", out)
    assert "PLAY NICE: UNKNOWN" not in out  # no bare UNKNOWN beside a pass
    j = json.loads(run(PLAYNICE, ["status", "--repo", str(repo), "--no-github", "--json"],
                       tmp_path).stdout)
    assert j["checks"]["state"].startswith("plays nice")
    assert j["readiness"]["state"] == "blocked"
    assert j["play_nice"]["status"] == "UNKNOWN"  # machine field kept for callers


def test_status_check_line_matches_playnice_check(tmp_path):
    repo = git_repo(tmp_path / "bare")  # no AGENTS.md: check says fix needed
    check = run(PLAYNICE, ["check", str(repo)], tmp_path)
    status = run(PLAYNICE, ["status", "--repo", str(repo), "--no-github"], tmp_path)
    assert "fix needed" in check.stdout
    assert re.search(r"(?m)^CHECKS: fix needed — needs a fix: AGENTS.md", status.stdout)


def test_work_readiness_rules():
    blocked = {"enforced": True, "status": "BEHIND", "manifest_update": "review",
               "manifest_policy": "require-current", "remote_revision": "a" * 40}
    assert pn.work_readiness(Path("m"), blocked)["state"] == "blocked"
    auto = {**blocked, "manifest_update": "automatic"}
    assert pn.work_readiness(Path("m"), auto)["state"] == "ready"
    assert pn.work_readiness(Path("m"), {"enforced": False, "status": "UNKNOWN"})["state"] == "ready"
    assert pn.work_readiness(None, {})["next"] == "contractctl init-adoption"


# ------------------------------------------------------------ rules


def test_playnice_rules_explains_each_contract(tmp_path):
    r = run(PLAYNICE, ["rules", "add a settings page"], tmp_path)
    assert r.returncode == 0, r.stderr
    assert re.search(r"(?m)^  web-ui\s+Web UI — 'page'", r.stdout)
    j = json.loads(run(PLAYNICE, ["rules", "fix the test suite", "--json"], tmp_path).stdout)
    ids = {c["id"] for c in j["contracts"]}
    assert "testing-and-evidence" in ids and "web-ui" not in ids


def test_help_leads_with_everyday_commands(tmp_path):
    out = run(PLAYNICE, ["--help"], tmp_path).stdout
    listing = out[out.index("positional arguments"):]
    assert listing.index("    rules") < listing.index("    work") < listing.index("    reconcile")
    assert "orchestrators" in out


# ------------------------------------------------------------ badge + wrapper


def test_badge_links_to_check_runs_only_when_a_workflow_is_written(tmp_path):
    with_ci = git_repo(tmp_path / "ci")
    (with_ci / ".github").mkdir()
    subprocess.run(["git", "-C", str(with_ci), "remote", "add", "origin",
                    "https://github.com/someone/thing.git"], check=True)
    no_ci = git_repo(tmp_path / "noci")
    subprocess.run(["git", "-C", str(no_ci), "remote", "add", "origin",
                    "https://github.com/someone/other.git"], check=True)
    assert run(PLAYNICE, ["start", str(with_ci)], tmp_path).returncode == 0
    assert run(PLAYNICE, ["start", str(no_ci)], tmp_path).returncode == 0
    assert "someone/thing/actions/workflows/playnice.yml" in (with_ci / "README.md").read_text()
    assert "actions/workflows" not in (no_ci / "README.md").read_text()


def test_wrapper_works_through_a_symlink(tmp_path):
    link = tmp_path / "bin" / "playnice"
    link.parent.mkdir()
    link.symlink_to(REPO / "tools" / "playnice" / "playnice")
    r = subprocess.run([sys.executable, str(link), "--version"], capture_output=True,
                       text=True, cwd=str(tmp_path), timeout=60)
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("playnice ")


def test_receipt_docs_say_declaration_not_proof():
    for rel in ("README.md", "AGENTS.md"):
        text = (REPO / rel).read_text(encoding="utf-8")
        assert "does not independently prove comprehension or compliance" in text, rel
    proof = (REPO / "contracts/work/CONTRACT_PROOF.md").read_text(encoding="utf-8")
    assert "The line proves you read the rules" not in proof
