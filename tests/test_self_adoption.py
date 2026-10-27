"""Self-adoption: the library checking itself, truthfully and without a pin treadmill.

A commit cannot pin its own final SHA, so the library's own manifest
(`source.self: true`) is checked by ancestry: the pin must be a commit in the
history being checked. External adopters keep the strict pin check.
"""

import json
import os
import re
import shutil
import subprocess
import sys

import pytest

from conftest import REPO, git0

# This module's copies keep .contract-commitments (the others skip it).
_SKIP = (".git", ".venv", "__pycache__", ".pytest_cache")


def git(repo, *a):
    r = git0(repo, *a)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture()
def lib(tmp_path, library_git_copy):
    """A git copy of the library whose own manifest is a self-adoption."""
    repo = library_git_copy(tmp_path / "lib", skip=_SKIP)
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "clone", "-q", "--bare", str(repo), str(remote)], check=True)
    set_pin(repo, git(repo, "rev-parse", "HEAD"), repository=str(remote))
    commit(repo, "pin the baseline")
    git(repo, "push", "-q", str(remote), "main:main")
    return repo, remote


def set_pin(repo, sha, repository=None, self_flag=True):
    m = repo / ".contracts" / "adoption.yaml"
    t = m.read_text()
    t = re.sub(r"(?m)^  revision: \S+$", f"  revision: {sha}", t)
    t = re.sub(r"(?m)^  self: \S+\n", "", t)
    if self_flag:
        t = t.replace(f"  revision: {sha}\n", f"  revision: {sha}\n  self: true\n")
    if repository:
        t = re.sub(r"(?m)^  repository: \S+$", f"  repository: {repository}", t)
    m.write_text(t)


def commit(repo, msg, path="trivia.txt"):
    f = repo / path
    f.write_text((f.read_text() if f.exists() else "") + msg + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", msg, "--no-gpg-sign")
    return git(repo, "rev-parse", "HEAD")


def check(repo, target=None):
    env = {**os.environ, "PLAY_NICE_LIBRARY": str(repo)}
    r = subprocess.run(
        [sys.executable, str(repo / "tools/playnice/playnice.py"), "check", str(target or repo), "--json"],
        capture_output=True, text=True, env=env, timeout=120,
    )
    data = json.loads(r.stdout)
    return r.returncode, next(c for c in data["checks"] if c["id"] == "adoption")


def freshness(repo, manifest=None):
    r = subprocess.run(
        [sys.executable, str(repo / "tools/contractctl/contractctl.py"), "freshness",
         "--manifest", str(manifest or repo / ".contracts/adoption.yaml"), "--json"],
        capture_output=True, text=True, timeout=120,
    )
    return json.loads(r.stdout)


# ------------------------------------------------------------------ playnice check


def test_self_adoption_passes_by_ancestry_after_later_merges(lib):
    repo, _ = lib
    for i in range(3):  # later merges never need a pin bump
        commit(repo, f"later change {i}")
    commit(repo, "a contract-text change", "contracts/everyone/NOTE.txt")
    code, item = check(repo)
    assert code == 0, item
    assert item["state"] == "healthy"
    assert "self-adoption" in item["words"] and "in this checkout's history" in item["words"]


def test_self_pin_that_is_not_a_commit_is_a_fix(lib):
    repo, _ = lib
    set_pin(repo, "e570e2630702ddb6c61f7d1d89ab0ce439cdc608")
    code, item = check(repo)
    assert code == 1
    assert item["state"] == "needs_attention"
    assert "not a commit in this repository" in item["words"]


def test_self_pin_off_the_checked_history_is_a_fix(lib):
    repo, _ = lib
    git(repo, "checkout", "-q", "-b", "side")
    side = commit(repo, "side branch work")
    git(repo, "checkout", "-q", "main")
    set_pin(repo, side)
    code, item = check(repo)
    assert code == 1
    assert "not in the history of this checkout" in item["words"]


def test_self_claim_outside_the_library_is_rejected(lib, tmp_path):
    repo, _ = lib
    consumer = tmp_path / "consumer"
    (consumer / ".contracts").mkdir(parents=True)
    shutil.copy(repo / "AGENTS.md", consumer / "AGENTS.md")
    shutil.copy(repo / ".contracts/adoption.yaml", consumer / ".contracts/adoption.yaml")
    code, item = check(repo, consumer)
    assert code == 1
    assert "only valid in the library's own" in item["words"]


def test_external_adoption_stays_strict(lib, tmp_path):
    repo, _ = lib
    old = git(repo, "rev-parse", "HEAD")
    commit(repo, "library moves on")
    consumer = tmp_path / "consumer"
    (consumer / ".contracts").mkdir(parents=True)
    shutil.copy(repo / "AGENTS.md", consumer / "AGENTS.md")
    shutil.copy(repo / ".contracts/adoption.yaml", consumer / ".contracts/adoption.yaml")
    set_pin(consumer, old, self_flag=False)
    code, item = check(repo, consumer)
    assert code == 1
    assert "is not the current library revision" in item["words"]
    assert "set source.self" not in item["words"]  # the hint is for the library only


def test_library_without_self_flag_gets_a_pointed_hint(lib):
    repo, _ = lib
    set_pin(repo, git(repo, "rev-parse", "HEAD~1"), self_flag=False)
    code, item = check(repo)
    assert code == 1
    assert "set source.self: true" in item["words"]


# ------------------------------------------------------------------ contractctl freshness


def test_self_freshness_current_on_main_with_an_old_pin(lib):
    repo, remote = lib
    commit(repo, "a contract-text change", "contracts/everyone/NOTE.txt")
    git(repo, "push", "-q", str(remote), "main:main")
    fr = freshness(repo)
    assert fr["status"] == "CURRENT", fr
    assert fr["self_adoption"] is True


def test_self_freshness_current_on_a_branch_that_contains_main(lib):
    repo, _ = lib
    git(repo, "checkout", "-q", "-b", "feature")
    commit(repo, "feature work")
    assert freshness(repo)["status"] == "CURRENT"


def test_self_freshness_behind_when_remote_moved(lib):
    repo, remote = lib
    commit(repo, "upstream moves")
    git(repo, "push", "-q", str(remote), "main:main")
    git(repo, "reset", "-q", "--hard", "HEAD~1")
    fr = freshness(repo)
    assert fr["status"] == "BEHIND", fr


def test_self_freshness_invalid_pin_is_diverged(lib):
    repo, _ = lib
    git(repo, "checkout", "-q", "-b", "side")
    side = commit(repo, "never merged")
    git(repo, "checkout", "-q", "main")
    set_pin(repo, side)
    fr = freshness(repo)
    assert fr["status"] == "DIVERGED"
    assert "not in the history" in fr["detail"]


def test_self_claim_in_another_folder_is_unknown(lib, tmp_path):
    repo, _ = lib
    other = tmp_path / "elsewhere.yaml"
    shutil.copy(repo / ".contracts/adoption.yaml", other)
    fr = freshness(repo, other)
    assert fr["status"] == "UNKNOWN"
    assert "only valid in the library's own" in fr["detail"]


# ------------------------------------------------------------------ this repository


def test_this_library_passes_its_own_check_and_badge_matches(tmp_path):
    """The README badge is the committed result of `playnice check .`."""
    out = tmp_path / "badge.svg"
    env = {**os.environ, "PLAY_NICE_LIBRARY": str(REPO)}
    r = subprocess.run(
        [sys.executable, str(REPO / "tools/playnice/playnice.py"), "check", str(REPO),
         "--badge", str(out)],
        capture_output=True, text=True, env=env, timeout=120,
    )
    assert r.returncode == 0, r.stdout
    assert out.read_text() == (REPO / "playnice-badge.svg").read_text(), (
        "playnice-badge.svg is stale: run `playnice check . --badge playnice-badge.svg`"
    )
