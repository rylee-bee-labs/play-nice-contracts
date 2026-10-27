"""Shared test fixtures and helpers.

Before this file, six test modules each copied the whole library with
shutil.copytree and then ran `git init` / `git add -A` / `git commit` for
every test. Hashing and compressing the tree for the baseline commit cost
about 0.2 s per test, about 30 s of a serial run, and left ~250 loose Git
objects per test for pytest to delete later.

Now each test session (each xdist worker) builds one baseline repository per
copy recipe, and every test gets its own copy of that repository, `.git`
included. The copy has the same files, the same branch (`main`), the same
user config and one "baseline" commit, as before. Copies without Git
history stay without Git history.

Test modules import the plain helpers with `from conftest import ...`.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CT = REPO / "tools" / "contractctl" / "contractctl.py"
PLAYNICE = REPO / "tools" / "playnice" / "playnice.py"

# Never copied: Git history, local environments, caches and commitment state.
COPY_SKIP = (".git", ".venv", "__pycache__", ".pytest_cache", ".contract-commitments")

# Copied by no test copy because no test or tool reads it. docs/images holds
# one 1.9 MB picture (a third of the tree): the tools never open it and the
# text scanner skips binary files. Paths are relative to the library root.
NOT_NEEDED = ("docs/images",)


# --------------------------------------------------------------- running things


def git0(repo, *a, timeout=60):
    """Run git in `repo`; return the CompletedProcess (no check)."""
    return subprocess.run(
        ["git", "-C", str(repo), *a], capture_output=True, text=True, timeout=timeout
    )


def head(path) -> str:
    return git0(path, "rev-parse", "HEAD").stdout.strip()


def bare_clone(src, dest):
    r = subprocess.run(
        ["git", "clone", "--quiet", "--bare", str(src), str(dest)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert r.returncode == 0, r.stderr
    return Path(dest)


def run_py(script, args, cwd=None, env=None, timeout=60):
    """Run a Python tool with this interpreter and capture its output.

    cwd=None keeps the current directory; env is passed to subprocess as is
    (None inherits the environment). with_env() builds os.environ plus extras.
    """
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True,
        text=True,
        cwd=None if cwd is None else str(cwd),
        timeout=timeout,
        env=env,
    )


def with_env(extra=None, **more):
    """A copy of os.environ with `extra` and keyword values added."""
    return {**os.environ, **(extra or {}), **more}


def load_module(path: Path, name: str):
    """Import a module from a file path under the given module name."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_CT_CACHE: dict[str, object] = {}


def _load_ct_from(tmp_repo):
    """Import contractctl from a copied repo, bypassing the module cache."""
    key = str(tmp_repo)
    if key not in _CT_CACHE:
        _CT_CACHE[key] = load_module(
            Path(tmp_repo) / "tools" / "contractctl" / "contractctl.py",
            f"ct_{abs(hash(key))}",
        )
    return _CT_CACHE[key]


# --------------------------------------------------------------- library copies


def _ignore(skip):
    by_name = shutil.ignore_patterns(*skip)
    not_needed = {}
    for rel in NOT_NEEDED:
        parent, _, name = rel.rpartition("/")
        not_needed.setdefault(str(REPO / parent) if parent else str(REPO), set()).add(name)

    def ignore(src, names):
        out = set(by_name(src, names))
        out |= not_needed.get(str(Path(src)), set()) & set(names)
        return out

    return ignore


def copy_library(dest, skip=COPY_SKIP) -> Path:
    """Copy the library tree to dest, without Git history."""
    dest = Path(dest)
    shutil.copytree(REPO, dest, symlinks=True, ignore=_ignore(skip))
    return dest


@pytest.fixture(scope="session")
def library_git_copy(tmp_path_factory):
    """Return make(dest, skip=COPY_SKIP): a Git copy of the library at dest.

    The copy is a repository on `main` with user.email test@example.invalid,
    user.name Test, and one commit "baseline" holding every copied file.
    The baseline is built once per session per `skip` and copied per test.
    """
    templates: dict[tuple, Path] = {}

    def _template(skip) -> Path:
        if skip not in templates:
            t = copy_library(tmp_path_factory.mktemp("library-baseline") / "lib", skip)
            for args in (
                ("init", "-q", "-b", "main"),
                ("config", "user.email", "test@example.invalid"),
                ("config", "user.name", "Test"),
                # no background maintenance: `git commit` can start a detached
                # `git maintenance run` whose lock and temp-pack files vanish
                # while copytree copies this repo for a test (seen on CI).
                # The copies inherit these settings.
                ("config", "maintenance.auto", "false"),
                ("config", "gc.auto", "0"),
                ("config", "gc.autoDetach", "false"),
                ("add", "-A"),
                ("commit", "-qm", "baseline", "--no-gpg-sign"),
                # one pack file instead of ~250 loose objects: every copy
                # (and pytest's clean-up of old copies) touches fewer files
                ("repack", "-a", "-d", "-q"),
            ):
                r = git0(t, *args)
                assert r.returncode == 0, (args, r.stderr)
            templates[skip] = t
        return templates[skip]

    def make(dest, skip=COPY_SKIP) -> Path:
        dest = Path(dest)
        shutil.copytree(_template(tuple(skip)), dest, symlinks=True)
        # the index records inode numbers; refresh it for the new files
        r = git0(dest, "update-index", "-q", "--refresh")
        assert r.returncode == 0, r.stderr
        return dest

    return make


@pytest.fixture()
def lib():
    """contractctl imported from this checkout. Modules that need a copy of
    the library instead define their own `lib` fixture, which wins."""
    sys.path.insert(0, str(REPO / "tools" / "contractctl"))
    import contractctl as ct

    yield ct
    sys.path.pop(0)
