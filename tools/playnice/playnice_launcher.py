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
   When an update fails (offline, say) the clone already there is used, and
   every run warns until an update succeeds.

`playnice --version` adds which checkout and commit the rules come from.

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
# in the managed clone's .git folder: last update attempt, last success,
# and why the last attempt failed (removed by the next success)
UPDATE_MARK = "play-nice-last-update"
SYNCED_MARK = "play-nice-last-synced"
ERROR_FILE = "play-nice-update-error"


class LauncherError(Exception):
    """No library checkout could be found or made; the message says why."""


def is_library(path: Path) -> bool:
    return (path / PLAYNICE_REL).is_file() and (path / FLOOR_REL).is_file()


def cache_dir(env) -> Path:
    base = env.get("PLAY_NICE_CACHE")
    return (Path(base) if base else Path.home() / ".cache" / "play-nice") / "contracts"


def _git(*args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True, timeout=timeout)


def _stamp(path: Path, when: float) -> None:
    path.touch()
    os.utime(path, (when, when))


def _day(ts: float) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(ts))


def ensure_clone(target: Path, repository: str, now: float | None = None) -> str | None:
    """Clone `repository` into `target`, or fast-forward it once a day.

    Returns a warning while the clone may be stale: on every run after a
    failed update until an update succeeds, so old rules never look freshly
    synced. Raises LauncherError when there is no clone and one cannot be
    made (first use needs git and the network)."""
    now = time.time() if now is None else now
    git_dir = target / ".git"
    tried, synced, error = git_dir / UPDATE_MARK, git_dir / SYNCED_MARK, git_dir / ERROR_FILE
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
            raise LauncherError("first use clones the library, and git is not installed")
        except subprocess.TimeoutExpired:
            raise LauncherError(f"cloning {repository} took longer than 5 minutes")
        if r.returncode != 0 or not is_library(target):
            raise LauncherError(
                f"first use clones the library, and cloning {repository} failed: "
                f"{r.stderr.strip() or 'not a library checkout'}"
            )
        _stamp(tried, now)
        _stamp(synced, now)
        return None
    if not git_dir.is_dir():
        return f"the library in {target} is not a git clone, so it is never updated"
    if not (tried.is_file() and now - tried.stat().st_mtime < UPDATE_EVERY):
        _stamp(tried, now)  # one attempt a day, even offline
        why = None
        try:
            r = _git("-C", str(target), "pull", "--ff-only", "--quiet", timeout=60)
            if r.returncode != 0:
                why = (r.stderr.strip().splitlines() or ["unknown error"])[-1]
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            why = "git is not installed" if isinstance(e, FileNotFoundError) else "timed out"
        if why is None:
            _stamp(synced, now)
            error.unlink(missing_ok=True)
        else:
            error.write_text(f"{_day(now)} {why}\n", encoding="utf-8")
    if error.is_file():
        last = _day(synced.stat().st_mtime) if synced.is_file() else "an unknown date"
        why = error.read_text(encoding="utf-8").strip()
        return (f"the library in {target} may be out of date: its last update failed "
                f"({why}); using the copy last updated {last}")
    return None


def find_library(cwd: Path, env) -> tuple[Path, str, str | None]:
    """(library checkout, how it was chosen, warning or None), in the order
    of the module doc."""
    override = env.get("PLAY_NICE_LIBRARY")
    if override:
        p = Path(override).expanduser().resolve()
        if not is_library(p):
            raise LauncherError(
                f"PLAY_NICE_LIBRARY={p} is not a Play-Nice library checkout "
                f"(needs {PLAYNICE_REL.as_posix()} and {FLOOR_REL.as_posix()})"
            )
        return p, "PLAY_NICE_LIBRARY", None
    for up in (cwd, *cwd.parents):
        if is_library(up):
            return up, "the checkout you are in", None
    target = cache_dir(env)
    warning = ensure_clone(target, env.get("PLAY_NICE_REPOSITORY") or DEFAULT_REPOSITORY)
    return target, "managed clone", warning


def describe(lib: Path, how: str) -> str:
    """Which rules are running: the checkout, its commit, and for the
    managed clone when it last updated."""
    try:
        r = _git("-C", str(lib), "rev-parse", "--short=12", "HEAD", timeout=10)
        commit = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "unknown"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        commit = "unknown"
    extra = ""
    if how == "managed clone":
        synced = lib / ".git" / SYNCED_MARK
        extra = f", last updated {_day(synced.stat().st_mtime)}" if synced.is_file() else ", never updated"
        if (lib / ".git" / ERROR_FILE).is_file():
            extra += ", last update failed"
    return f"rules from {lib} at commit {commit} ({how}{extra})"


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
        lib, how, warning = find_library(Path.cwd(), os.environ)
        if warning:
            print(f"playnice: warning: {warning}", file=sys.stderr)
        mod = load_playnice(lib)
    except LauncherError as e:
        print(f"playnice: cannot find the Play-Nice library: {e}", file=sys.stderr)
        print("  next: check git and the network, or set PLAY_NICE_LIBRARY to a "
              "checkout of the library", file=sys.stderr)
        return 2
    if "--version" not in argv:
        return mod.main(argv)
    try:
        rc = mod.main(argv)
    except SystemExit as e:  # argparse's version action exits
        rc = e.code if isinstance(e.code, int) else 0
    print(describe(lib, how))
    return rc


if __name__ == "__main__":
    sys.exit(main())
