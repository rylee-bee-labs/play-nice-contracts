"""Releases: `contractctl release` prepares one in the working tree, and
`release-notes` prints what the release workflow publishes."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


@pytest.fixture()
def lib_copy(tmp_path):
    dest = tmp_path / "lib"
    shutil.copytree(
        REPO, dest, symlinks=True,
        ignore=shutil.ignore_patterns(".git", "docs", "assets", "__pycache__", ".pytest_cache"),
    )
    return dest


def ct(repo, *args):
    return subprocess.run(
        [sys.executable, str(repo / "tools" / "contractctl" / "contractctl.py"), *args],
        cwd=str(repo), capture_output=True, text=True, timeout=60,
    )


def _next_minor(v):
    a, b, _c = (int(x) for x in v.split("."))
    return f"{a}.{b + 1}.0"


def test_release_moves_unreleased_and_bumps_version(lib_copy):
    old = (lib_copy / "VERSION").read_text().strip()
    new = _next_minor(old)
    # give the copy an entry of its own: right after a release the real
    # [Unreleased] is empty
    cl = lib_copy / "CHANGELOG.md"
    cl.write_text(cl.read_text().replace(
        "## [Unreleased]\n", "## [Unreleased]\n\n### Added\n- a test entry\n", 1))
    before = cl.read_text()
    unreleased = before.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0].strip()
    assert "- a test entry" in unreleased
    r = ct(lib_copy, "release", new, "--date", "2026-10-27")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (lib_copy / "VERSION").read_text().strip() == new
    after = (lib_copy / "CHANGELOG.md").read_text()
    assert f"## [Unreleased]\n\n## [{new}] - 2026-10-27\n\n" in after
    notes = ct(lib_copy, "release-notes", new)
    assert notes.returncode == 0 and notes.stdout.strip() == unreleased
    readme = (lib_copy / "README.md").read_text()
    assert f"library {new}" in readme and f"library {old}" not in readme
    # the result still validates, and there is nothing left to release
    assert ct(lib_copy, "validate").returncode == 0
    again = ct(lib_copy, "release", _next_minor(new), "--date", "2026-10-28")
    assert again.returncode == 1 and "nothing to release" in again.stderr


@pytest.mark.parametrize("args, why", [
    (("0.0.1",), "not newer"),
    (("banana",), "not a version"),
    (("9.0.0", "--date", "27/10/2026"), "not a date"),
])
def test_release_refuses_bad_input(lib_copy, args, why):
    r = ct(lib_copy, "release", *args)
    assert r.returncode == 1 and why in r.stderr, r.stderr
    assert (lib_copy / "VERSION").read_text() == (REPO / "VERSION").read_text()


def test_release_notes_for_unknown_version_names_the_fix(lib_copy):
    r = ct(lib_copy, "release-notes", "9.9.9")
    assert r.returncode == 1
    assert "contractctl release 9.9.9" in r.stderr


def test_release_workflow_publishes_from_release_notes():
    wf = (REPO / ".github" / "workflows" / "release.yml").read_text()
    assert "VERSION" in wf and "release-notes" in wf and "gh release create" in wf
    assert "contents: write" in wf
    # by-hand runs for an earlier version: the input reaches the script only
    # through env (never pasted into it), and the tag goes on the commit where
    # VERSION became that version, found from main's history
    assert "IN_VERSION: ${{ inputs.version }}" in wf
    lines = [ln for ln in wf.splitlines() if "${{ inputs." in ln]
    assert all(ln.strip().startswith("IN_VERSION:") for ln in lines), lines
    assert "git rev-list --reverse origin/main -- VERSION" in wf
    assert '--latest="$latest"' in wf
