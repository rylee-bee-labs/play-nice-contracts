"""The installed `playnice` command (tools/playnice/playnice_launcher.py).

uv and pipx install only the launcher. It finds a library checkout
(PLAY_NICE_LIBRARY, the folder it runs in, or a managed clone in the cache)
and runs that checkout's own playnice.py. These tests use a local bare
repository as the library's remote, so they never touch the network.
"""

from __future__ import annotations

import os
import sys
import time

import pytest

from conftest import REPO, bare_clone, git0, head, load_module, run_py, with_env

LAUNCHER = REPO / "tools" / "playnice" / "playnice_launcher.py"


@pytest.fixture()
def launcher():
    return load_module(LAUNCHER, "playnice_launcher_under_test")


@pytest.fixture()
def remote(library_git_copy, tmp_path):
    work = library_git_copy(tmp_path / "work")
    return work, bare_clone(work, tmp_path / "remote.git")


def test_env_override_wins(launcher, tmp_path):
    lib, warning = launcher.find_library(tmp_path, {"PLAY_NICE_LIBRARY": str(REPO)})
    assert lib == REPO and warning is None


def test_env_override_must_be_a_library(launcher, tmp_path):
    with pytest.raises(launcher.LauncherError, match="not a Play-Nice library checkout"):
        launcher.find_library(tmp_path, {"PLAY_NICE_LIBRARY": str(tmp_path)})


def test_folder_inside_a_checkout_is_used(launcher):
    lib, _ = launcher.find_library(REPO / "contracts" / "work", {})
    assert lib == REPO


def test_first_use_clones_into_the_cache(launcher, remote, tmp_path):
    work, bare = remote
    env = {"PLAY_NICE_CACHE": str(tmp_path / "cache"), "PLAY_NICE_REPOSITORY": str(bare)}
    lib, warning = launcher.find_library(tmp_path / "elsewhere", env)
    assert lib == tmp_path / "cache" / "contracts"
    assert warning is None
    assert head(lib) == head(work)


def test_the_clone_is_fast_forwarded_once_a_day(launcher, remote, tmp_path):
    work, bare = remote
    target = tmp_path / "cache" / "contracts"
    launcher.ensure_clone(target, str(bare))
    (work / "NEW.txt").write_text("new\n")
    git0(work, "add", "NEW.txt")
    assert git0(work, "commit", "-qm", "new", "--no-gpg-sign").returncode == 0
    assert git0(work, "push", "-q", str(bare), "main").returncode == 0
    # within a day: no update
    assert launcher.ensure_clone(target, str(bare)) is None
    assert not (target / "NEW.txt").exists()
    # a day later: fast-forwarded
    assert launcher.ensure_clone(target, str(bare), now=time.time() + 2 * 86400) is None
    assert (target / "NEW.txt").is_file()


def test_offline_keeps_the_clone_and_warns(launcher, remote, tmp_path):
    _work, bare = remote
    target = tmp_path / "cache" / "contracts"
    launcher.ensure_clone(target, str(bare))
    git0(target, "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    warning = launcher.ensure_clone(target, str(bare), now=time.time() + 2 * 86400)
    assert warning and "using it as it is" in warning
    # one attempt a day: the next run is quiet again
    assert launcher.ensure_clone(target, str(bare), now=time.time() + 2 * 86400) is None
    assert launcher.is_library(target)


def test_a_foreign_folder_in_the_cache_is_never_overwritten(launcher, tmp_path):
    target = tmp_path / "cache" / "contracts"
    target.mkdir(parents=True)
    (target / "mine.txt").write_text("keep\n")
    with pytest.raises(launcher.LauncherError, match="not a Play-Nice library checkout"):
        launcher.ensure_clone(target, str(tmp_path / "nowhere.git"))
    assert (target / "mine.txt").read_text() == "keep\n"


def test_command_runs_the_checkouts_playnice(tmp_path):
    r = run_py(LAUNCHER, ["--version"], cwd=tmp_path,
               env=with_env(PLAY_NICE_LIBRARY=str(REPO)))
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("playnice ") and "floor " in r.stdout


def test_command_explains_when_no_library_can_be_found(tmp_path):
    env = with_env(PLAY_NICE_CACHE=str(tmp_path / "cache"),
                   PLAY_NICE_REPOSITORY=str(tmp_path / "missing.git"))
    env.pop("PLAY_NICE_LIBRARY", None)
    r = run_py(LAUNCHER, ["--version"], cwd=tmp_path, env=env)
    assert r.returncode == 2
    assert "cannot find the Play-Nice library" in r.stderr
    assert "next:" in r.stderr


@pytest.mark.skipif(sys.version_info < (3, 11), reason="tomllib is Python 3.11+")
def test_pyproject_installs_only_the_launcher():
    import tomllib

    data = tomllib.loads((REPO / "pyproject.toml").read_text())
    assert data["project"]["dependencies"] == []
    assert data["project"]["scripts"] == {"playnice": "playnice_launcher:main"}
    assert data["tool"]["setuptools"]["py-modules"] == ["playnice_launcher"]
    pkg_dir = data["tool"]["setuptools"]["package-dir"][""]
    assert (REPO / pkg_dir / "playnice_launcher.py").is_file()
    assert data["tool"]["setuptools"]["dynamic"]["version"] == {"file": "VERSION"}
