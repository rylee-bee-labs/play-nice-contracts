"""playnice_launcher — the `playnice` command that uv or pipx installs.

    uv tool install git+https://github.com/rylee-bee-labs/play-nice-contracts
    pipx install git+https://github.com/rylee-bee-labs/play-nice-contracts

The installed package holds only this file. It finds a Play-Nice library
checkout and runs that checkout's own tools/playnice/playnice.py, so the tool
and the rules it checks always come from the same revision, and installing
never pins old rules. The checkout is, in order:

1. PLAY_NICE_LIBRARY, when set;
2. the library checkout the current folder is inside;
3. a managed clone in ~/.cache/play-nice/contracts (PLAY_NICE_CACHE moves
   ~/.cache/play-nice), cloned on first use from PLAY_NICE_REPOSITORY
   (default: the public library) and fast-forwarded at most once a day.
   Offline, the clone already there is used as it is.

Standard library only, like the tools it runs.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_REPOSITORY = "https://github.com/rylee-bee-labs/play-nice-contracts"
PLAYNICE_REL = Path("tools") / "playnice" / "playnice.py"
FLOOR_REL = Path("contracts") / "everyone" / "FLOOR.md"
UPDATE_EVERY = 24 * 60 * 60  # seconds between fast-forwards of the managed clone
UPDATE_MARK = "play-nice-last-update"  # in the clone's .git folder


class LauncherError(Exception):
    """No library checkout could be found or made; the message says why."""


def is_library(path: Path) -> bool:
    return (path / PLAYNICE_REL).is_file() and (path / FLOOR_REL).is_file()


def cache_dir(env) -> Path:
    base = env.get("PLAY_NICE_CACHE")
    return (Path(base) if base else Path.home() / ".cache" / "play-nice") / "contracts"


def _git(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, timeout=timeout)


def ensure_clone(target: Path, repository: str, now: float | None = None) -> str | None:
    """Clone `repository` into `target`, or fast-forward it once a day.

    Returns a warning when an update failed (the existing clone is still
    used), None otherwise. Raises LauncherError when there is no clone and
    one cannot be made."""
    now = time.time() if now is None else now
    if not is_library(target):
        if target.exists() and any(target.iterdir()):
            raise LauncherError(
                f"{target} exists but is not a Play-Nice library checkout; "
                "move it away, or set PLAY_NICE_LIBRARY to a checkout"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            r = _git("clone", "--quiet", repository, str(target), timeout=300)
        except FileNotFoundError:
            raise LauncherError("git is not installed, so the library cannot be cloned")
        except subprocess.TimeoutExpired:
            raise LauncherError(f"cloning {repository} took longer than 5 minutes")
        if r.returncode != 0 or not is_library(target):
            raise LauncherError(
                f"could not clone {repository}: {r.stderr.strip() or 'not a library checkout'}"
            )
        (target / ".git" / UPDATE_MARK).touch()
        return None
    mark = target / ".git" / UPDATE_MARK
    if mark.is_file() and now - mark.stat().st_mtime < UPDATE_EVERY:
        return None
    if (target / ".git").is_dir():
        # one attempt a day, even offline: quiet when nothing changes
        mark.touch()
        os.utime(mark, (now, now))
    try:
        r = _git("-C", str(target), "pull", "--ff-only", "--quiet", timeout=60)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return f"could not update the library in {target} ({e.__class__.__name__}); using it as it is"
    if r.returncode != 0:
        why = (r.stderr.strip().splitlines() or ["unknown error"])[-1]
        return f"could not update the library in {target} ({why}); using it as it is"
    return None


def find_library(cwd: Path, env) -> tuple[Path, str | None]:
    """(library checkout, warning or None) by the order in the module doc."""
    override = env.get("PLAY_NICE_LIBRARY")
    if override:
        p = Path(override).expanduser().resolve()
        if not is_library(p):
            raise LauncherError(
                f"PLAY_NICE_LIBRARY={p} is not a Play-Nice library checkout "
                f"(needs {PLAYNICE_REL.as_posix()} and {FLOOR_REL.as_posix()})"
            )
        return p, None
    for up in (cwd, *cwd.parents):
        if is_library(up):
            return up, None
    target = cache_dir(env)
    warning = ensure_clone(target, env.get("PLAY_NICE_REPOSITORY") or DEFAULT_REPOSITORY)
    return target, warning


def load_playnice(lib: Path):
    path = lib / PLAYNICE_REL
    spec = importlib.util.spec_from_file_location("playnice", path)
    if spec is None or spec.loader is None:
        raise LauncherError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["playnice"] = mod
    spec.loader.exec_module(mod)
    return mod


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    try:
        lib, warning = find_library(Path.cwd(), os.environ)
        if warning:
            print(f"playnice: warning: {warning}", file=sys.stderr)
        mod = load_playnice(lib)
    except LauncherError as e:
        print(f"playnice: cannot find the Play-Nice library: {e}", file=sys.stderr)
        print("  next: check git and the network, or set PLAY_NICE_LIBRARY to a "
              "checkout of the library", file=sys.stderr)
        return 2
    return mod.main(argv)


if __name__ == "__main__":
    sys.exit(main())
