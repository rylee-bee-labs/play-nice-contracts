#!/usr/bin/env python3
"""playnice — global agent-work entry point.

One command owns the whole lifecycle:

    playnice work "fix the settings page"

The wrapper: refreshes truth -> reconciles old work -> loads Play Nice ->
launches the agent -> verifies and cleans up afterward. If something
genuinely needs a human, it says so; otherwise it finishes the lifecycle
itself and ends with a durable handoff.

`contractctl` (tools/contractctl in the Play Nice library) remains the
lower-level engine; this tool is the orchestration layer on top of it.

Deterministic machinery: every state transition is computed from Git /
contract state / gh JSON. UNKNOWN stays UNKNOWN (fail closed). No test
depends on live GitHub — tests substitute local bare repositories for the
authoritative remote and a fake `gh` binary.

The v2 surface (docs/decisions/2026-09-26-play-nice-v2.md, step 4) adds three
zero-friction commands beside the lifecycle ones:

    playnice verify "<receipt line>"   is that line current for the library?
    playnice check [PATH|URL] [--badge FILE]   check a repo or a site; badge
    playnice start [PATH] [--dry-run]  set a repo up: AGENTS.md, badge, CI

Exit codes:
  0  success (work finished or nothing required; verify CURRENT; check plays nice)
  1  usage / internal error; verify OUT OF DATE; check fix needed or behind
  2  fail-closed gate (freshness / gate / permit blocked); verify INVALID;
     check could not run (bad path, no library, network down)
  3  agent exited nonzero
  4  needs human help (WAITING_FOR_HELP / BLOCKED)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

PLAYNICE_VERSION = "0.1.0"

# ----------------------------------------------------------------- config

DEFAULT_CONFIG_PATHS = (
    Path(os.environ.get("PLAY_NICE_CONFIG", ""))
    if os.environ.get("PLAY_NICE_CONFIG")
    else Path.home() / ".config" / "play-nice" / "global.yaml"
)

CACHE_DIR = (
    Path(os.environ["PLAY_NICE_CACHE"])
    if os.environ.get("PLAY_NICE_CACHE")
    else Path.home() / ".cache" / "play-nice"
)
LIBRARY_CACHE = CACHE_DIR / "contracts"

KNOWN_CONFIG_KEYS = {
    "play_nice": {"repository", "ref", "freshness"},
    "repositories": {
        "fetch_before_work",
        "prune_remotes",
        "inspect_previous_work",
        "reconcile_before_new_work",
    },
    "github": {
        "inspect_pull_requests",
        "inspect_issues",
        "inspect_ci",
        "merge_ready_pull_requests",
        "close_proven_resolved_issues",
        "remove_proven_merged_branches",
        "merge_method",
        "bin",
    },
    "safety": {
        "unknown_fails_closed",
        "respect_branch_protection",
        "respect_required_reviews",
        "respect_authorization",
        "never_force_push_by_default",
    },
    "handoff": {"required", "path"},
    "agent": {"command", "args"},
    "post": {"verify_command", "create_pull_request", "push", "timeout_minutes"},
}

FRESHNESS_POLICIES = ("pinned", "require-current")
GH_MERGE_METHODS = ("merge", "squash", "rebase")

DISPOSITIONS = (
    "DONE",
    "MERGED",
    "CLOSED",
    "STILL_ACTIVE",
    "DEFERRED",
    "WAITING_FOR_HELP",
    "UNKNOWN",
    "BLOCKED",
)


def default_config() -> dict:
    return {
        "play_nice": {
            "repository": "rylee-bee-labs/play-nice-contracts",
            "ref": "main",
            "freshness": "pinned",  # the global floor; manifests may raise
        },
        "repositories": {
            "fetch_before_work": True,
            "prune_remotes": True,
            "inspect_previous_work": True,
            "reconcile_before_new_work": True,
        },
        "github": {
            "inspect_pull_requests": True,
            "inspect_issues": True,
            "inspect_ci": True,
            "merge_ready_pull_requests": False,  # explicit opt-in
            "close_proven_resolved_issues": False,  # explicit opt-in
            "remove_proven_merged_branches": False,  # explicit opt-in
            "merge_method": "merge",
            "bin": "gh",
        },
        "safety": {
            "unknown_fails_closed": True,
            "respect_branch_protection": True,
            "respect_required_reviews": True,
            "respect_authorization": True,
            "never_force_push_by_default": True,
        },
        "handoff": {
            "required": True,
            "path": "",
        },
        "agent": {
            "command": "opencode",
            "args": ["run"],
        },
        "post": {
            "verify_command": "",
            "create_pull_request": False,
            "push": False,
            "timeout_minutes": 0,
        },
    }


def _merge_deep(base: dict, override: dict, where: str) -> dict:
    out = dict(base)
    for k, v in override.items():
        if k not in base and k not in KNOWN_CONFIG_KEYS.get(where, set()):
            raise ConfigError(
                f"unknown key '{where}.{k}' in global config "
                f"(known: {sorted(KNOWN_CONFIG_KEYS.get(where, set()))})"
            )
        if isinstance(v, dict):
            if not isinstance(base.get(k), dict):
                raise ConfigError(f"config key '{where}.{k}' must be a mapping")
            out[k] = _merge_deep(base[k], v, f"{where}.{k}")
        else:
            out[k] = v
    return out


class ConfigError(Exception):
    pass


def load_global_config(path: Path | None = None) -> dict:
    cfg = default_config()
    p = path or DEFAULT_CONFIG_PATHS
    if not p.exists():
        return cfg
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        raise ConfigError(f"cannot read global config {p}: {e}")
    import re as _re

    body = text
    m = _re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, _re.DOTALL)
    if m:
        body = m.group(1)
    data = _parse_yaml_simple(body, where="<global config>")
    if not isinstance(data, dict):
        raise ConfigError(f"global config {p} must be a mapping")
    out = _merge_deep(cfg, data, "")
    _validate_config(out)
    return out


def _validate_config(cfg: dict) -> None:
    """Enum/type validation. Unknown values fail loudly, never reinterpreted."""
    freshness = cfg["play_nice"]["freshness"]
    if freshness not in FRESHNESS_POLICIES:
        raise ConfigError(
            f"play_nice.freshness must be one of {FRESHNESS_POLICIES}, got {freshness!r}"
        )
    method = cfg["github"]["merge_method"]
    if method not in GH_MERGE_METHODS:
        raise ConfigError(
            f"github.merge_method must be one of {GH_MERGE_METHODS}, got {method!r}"
        )
    agent_cmd = cfg["agent"]["command"]
    if not isinstance(agent_cmd, str) or not agent_cmd.strip():
        raise ConfigError("agent.command must be a non-empty command name")
    if not isinstance(cfg["agent"]["args"], list) or not all(
        isinstance(a, str) for a in cfg["agent"]["args"]
    ):
        raise ConfigError("agent.args must be a list of strings")
    to = cfg["post"]["timeout_minutes"]
    if not isinstance(to, int) or to < 0:
        raise ConfigError("post.timeout_minutes must be a non-negative integer")
    if not isinstance(cfg["handoff"]["path"], str):
        raise ConfigError("handoff.path must be a string")
    non_bool_keys = {"merge_method", "bin", "path", "verify_command", "timeout_minutes"}
    for section in ("github", "safety", "repositories", "handoff", "post"):
        for k, v in cfg[section].items():
            if k == "timeout_minutes":
                if not isinstance(v, int):
                    raise ConfigError(f"{section}.{k} must be an integer")
                continue
            if k in non_bool_keys:
                continue
            if not isinstance(v, bool):
                raise ConfigError(f"{section}.{k} must be a boolean, got {v!r}")


def _parse_yaml_simple(text: str, where: str) -> dict:
    """Minimal deterministic YAML-subset parser (nested mappings + scalar lists).

    The project's own parser lives in contractctl; this tool touches only the
    small YAML shapes used by play-nice config. Anything not understood fails
    loudly instead of being silently reinterpreted.
    """
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.strip() in ("---", "..."):
            continue
        content = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        lines.append((indent, content))
    if not lines:
        return {}

    root: dict = {}
    stack: list[tuple[int, dict]] = [(-1, root)]  # (indent, mapping frame)
    i = 0
    while i < len(lines):
        indent, content = lines[i]
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]

        if content.startswith("- "):
            # scalar list item attached to the nearest open list key
            holder = _find_list_holder(stack, indent)
            if holder is None:
                raise ConfigError(f"{where}:{i + 1}: list item outside a list key")
            holder.append(_coerce(content[2:].strip()))
            i += 1
            continue

        if ":" not in content:
            raise ConfigError(
                f"{where}:{i + 1}: expected 'key: value', got {content!r}"
            )
        key, val = _split_scalar(content, where, i)
        if val == "":
            # lookahead: `- ` deeper -> list; otherwise nested mapping
            nxt = lines[i + 1] if i + 1 < len(lines) else None
            if nxt is not None and nxt[0] > indent and nxt[1].startswith("- "):
                lst: list = []
                parent[key] = lst
                stack.append((indent, {"_LIST_@": lst}))
                i += 1
                continue
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
            i += 1
            continue
        parent[key] = _coerce(val)
        i += 1
    _drop_placeholder(root)
    return root


def _find_list_holder(stack: list, indent: int) -> list | None:
    for f_indent, frame in reversed(stack):
        if f_indent < indent:
            lst = frame.get("_LIST_@")
            if lst is not None:
                return lst
    return None


def _drop_placeholder(node):
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if k == "_LIST_@":
                del node[k]
            else:
                _drop_placeholder(v)
    elif isinstance(node, list):
        for v in node:
            _drop_placeholder(v)


def _split_scalar(content: str, where: str, lineno: int) -> tuple[str, str]:
    idx = content.find(":")
    key = content[:idx].strip()
    val = content[idx + 1 :].strip()
    if not key:
        raise ConfigError(f"{where}:{lineno + 1}: empty key")
    return key, val


def _coerce(val: str):
    v = val.strip()
    if not v:
        return ""
    if v.startswith('"') and v.endswith('"') and len(v) >= 2:
        return v[1:-1]
    if v.startswith("'") and v.endswith("'") and len(v) >= 2:
        return v[1:-1]
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    if v in ("null", "None", "~"):
        return None
    if v.startswith("[") and v.endswith("]"):
        body = v[1:-1].strip()
        if not body:
            return []
        return [_coerce(part.strip()) for part in body.split(",")]
    if re.fullmatch(r"-?\d+", v):
        try:
            return int(v)
        except ValueError:
            pass
    return v


# ----------------------------------------------------------------- library


def find_library(config: dict, cwd: Path, env: dict | None = None) -> Path:
    """Locate the canonical Play Nice library checkout (holds contractctl)."""
    env = env or os.environ
    override = env.get("PLAY_NICE_LIBRARY")
    if override:
        p = Path(override).resolve()
        if not (p / "tools" / "contractctl" / "contractctl.py").is_file():
            raise PlayNiceError(
                f"PLAY_NICE_LIBRARY={p} is not a play-nice-contracts checkout "
                "(tools/contractctl/contractctl.py missing)"
            )
        return p
    # running inside a checkout of the library itself?
    probe = cwd
    for up in [cwd, *cwd.parents]:
        if (up / "contracts").is_dir() and (
            up / "tools" / "contractctl" / "contractctl.py"
        ).is_file():
            return up
    # managed cache clone
    target = LIBRARY_CACHE
    ct = target / "tools" / "contractctl" / "contractctl.py"
    if not ct.is_file():
        if not shutil.which("git"):
            raise PlayNiceError(
                "git not found; cannot bootstrap the Play Nice library cache"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        repo = config["play_nice"]["repository"]
        r = subprocess.run(
            ["git", "clone", "--quiet", _remote_url(repo), str(target)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if r.returncode != 0:
            raise PlayNiceError(
                f"cannot clone Play Nice library {repo}: {r.stderr.strip() or 'unknown error'}"
            )
    if config["repositories"]["fetch_before_work"]:
        ref = config["play_nice"]["ref"]
        r = subprocess.run(
            ["git", "-C", str(target), "fetch", "--quiet", "origin", ref],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0 and not ct.is_file():
            raise PlayNiceError(f"cannot fetch Play Nice library: {r.stderr.strip()}")
    return target


def _remote_url(repository: str) -> str:
    if repository.startswith(("/", "./", "../", "~")) or Path(repository).exists():
        return str(Path(repository).expanduser().resolve())
    if "://" in repository:
        return repository
    if "@" in repository and ":" in repository:
        return repository
    # owner/repo shorthand
    owner, _, name = repository.partition("/")
    if not owner or not name:
        raise PlayNiceError(f"cannot interpret repository {repository!r}")
    return f"https://github.com/{owner}/{name}.git"


def import_contractctl(lib: Path):
    """Import the contractctl engine from the canonical library checkout."""
    import importlib.util

    path = lib / "tools" / "contractctl" / "contractctl.py"
    spec = importlib.util.spec_from_file_location("contractctl", path)
    if spec is None or spec.loader is None:
        raise PlayNiceError(f"cannot import contractctl from {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["contractctl"] = mod
    spec.loader.exec_module(mod)
    return mod


class PlayNiceError(Exception):
    pass


# ----------------------------------------------------------------- git helpers


def git(
    repo: Path, *args: str, check: bool = True, timeout: int = 120
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=check,
    )


def git0(repo: Path, *args: str, timeout: int = 120) -> subprocess.CompletedProcess:
    return git(repo, *args, check=False, timeout=timeout)


def is_git_repo(path: Path) -> bool:
    return git0(path, "rev-parse", "--is-inside-work-tree").returncode == 0


# ----------------------------------------------------------------- repo state


def collect_repo_state(repo: Path, cfg: dict) -> dict:
    """Phase 2 — repository freshness: fetch, prune, classify. Never destroys work."""
    out = {
        "root": str(repo),
        "branch": None,
        "head": None,
        "upstream": None,
        "dirty": False,
        "dirty_files": [],
        "status": "UNKNOWN",
        "detail": "",
        "remotes": [],
        "default_branch": None,
        "fetched": False,
        "pruned": False,
        "worktrees": [],
    }
    if not is_git_repo(repo):
        out["detail"] = f"not a git repository: {repo}"
        return out
    r = git0(repo, "rev-parse", "--abbrev-ref", "HEAD")
    out["branch"] = r.stdout.strip() if r.returncode == 0 else "HEAD"
    r = git0(repo, "rev-parse", "HEAD")
    out["head"] = r.stdout.strip() if r.returncode == 0 else None
    r = git0(repo, "status", "--porcelain=v1", "--branch")
    out["status_raw"] = r.stdout
    dirty = [ln for ln in r.stdout.splitlines() if ln and not ln.startswith("##")]
    out["dirty"] = bool(dirty)
    out["dirty_files"] = dirty
    for ln in r.stdout.splitlines():
        if ln.startswith("## "):
            rest = ln[3:]
            if "..." in rest:
                branch, upstream = rest.split("...", 1)
                out["branch"] = branch or out["branch"]
                up = upstream.split(" ")[0]
                out["upstream"] = up
    r = git0(repo, "remote")
    out["remotes"] = r.stdout.split()
    # default branch from origin/HEAD
    r = git0(repo, "symbolic-ref", "refs/remotes/origin/HEAD")
    if r.returncode == 0:
        m = re.match(r"refs/remotes/origin/(.+)", r.stdout.strip())
        out["default_branch"] = m.group(1) if m else None
    if not out["default_branch"]:
        out["default_branch"] = "main"
    wt_list = [
        ln.split()[1]
        for ln in git0(repo, "worktree", "list", "--porcelain").stdout.splitlines()
        if ln.startswith("worktree ")
    ]
    out["worktrees"] = [w for w in wt_list if Path(w).resolve() != repo.resolve()]
    r = git0(repo, "ls-remote", "--symref", "origin", "HEAD")
    if r.returncode == 0:
        m = re.search(r"ref: refs/heads/(\S+)\s+HEAD", r.stdout)
        if m:
            out["default_branch"] = m.group(1)

    if cfg["repositories"]["fetch_before_work"] and out["remotes"]:
        fetch_args = ["fetch", "--quiet"]
        if cfg["repositories"]["prune_remotes"]:
            fetch_args.append("--prune")
        fetch_args.append("origin")
        fr = git0(repo, *fetch_args, timeout=300)
        out["fetched"] = fr.returncode == 0
        out["detail"] = (
            "" if fr.returncode == 0 else f"fetch failed: {fr.stderr.strip()[:200]}"
        )
        if cfg["repositories"]["prune_remotes"] and fr.returncode == 0:
            out["pruned"] = True

    # ahead/behind vs upstream
    if out["upstream"]:
        r = git0(
            repo, "rev-list", "--left-right", "--count", f"HEAD...{out['upstream']}"
        )
        if r.returncode == 0:
            left, _, right = r.stdout.strip().partition("\t")
            out["ahead"] = int(left)
            out["behind"] = int(right)
        r = git0(repo, "merge-base", "--is-ancestor", out["upstream"], "HEAD")
        out["upstream_in_head"] = r.returncode == 0

    out["status"] = classify_repo(out)
    return out


def classify_repo(s: dict) -> str:
    if not s.get("head"):
        return "EMPTY_OR_UNKNOWN"
    if s.get("dirty"):
        return "DIRTY"
    if s.get("upstream") is None:
        return "NO_UPSTREAM" if s.get("remotes") else "NO_REMOTE"
    ahead = s.get("ahead", 0)
    behind = s.get("behind", 0)
    if ahead == 0 and behind == 0:
        return "CURRENT"
    if ahead > 0 and behind == 0:
        return "AHEAD"
    if ahead == 0 and behind > 0:
        return "BEHIND"
    return "DIVERGED"


def reconcile_repo(repo: Path, cfg: dict) -> dict:
    """Deterministic reconcile: fetch (above) + fast-forward ONLY when clean."""
    s = collect_repo_state(repo, cfg)
    if s["status"] == "BEHIND" and cfg["repositories"]["reconcile_before_new_work"]:
        if s.get("branch") and s.get("branch") != "HEAD" and s.get("upstream"):
            if s["branch"] == "main" or s["default_branch"] == s["branch"]:
                r = git0(repo, "merge", "--ff-only", s["upstream"], timeout=300)
                if r.returncode == 0:
                    s["reconciled"] = True
                    s["status"] = "CURRENT"
                    s["detail"] = "fast-forwarded to upstream"
                else:
                    s["detail"] = f"ff-only failed: {r.stderr.strip()[:200]}"
    return s


# ------------------------------------------------------------- freshness


def find_adoption_manifest(repo: Path, explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = repo / p
        return p if p.is_file() else None
    candidates = [
        ".contracts/adoption.yaml",
        ".project/contracts/adoption.yaml",
        ".contracts/adoption.yml",
        ".project/contracts/adoption.yml",
    ]
    for rel in candidates:
        p = repo / rel
        if p.is_file():
            return p
    return None


def play_nice_check(manifest_path: Path, lib: Path, global_cfg: dict) -> dict:
    """Phase 1 — establish the authoritative remote revision (fail closed)."""
    cc = import_contractctl(lib)
    manifest = cc.load_adoption(manifest_path)
    result = cc.check_freshness(manifest_path)
    mf = manifest.get("freshness") or {}
    manifest_requires = mf.get("policy", "pinned") == "require-current"
    global_requires = global_cfg["play_nice"]["freshness"] == "require-current"
    enforced = manifest_requires or global_requires
    out = dict(result)
    out["enforced"] = enforced
    out["manifest_policy"] = mf.get("policy", "pinned")
    out["manifest_update"] = mf.get("update", "review")
    out["global_requires"] = global_requires
    if global_requires and not manifest_requires:
        out["detail"] = out.get("detail", "") + (
            "; global floor requires current contracts"
            if out["detail"]
            else "global floor requires current contracts"
        )
    return out


def freshness_blocked(fr: dict) -> bool:
    """Returns True when the freshness state must fail closed under enforcement."""
    if not fr.get("enforced"):
        return False
    return fr["status"] != "CURRENT"


def sync_pin_if_allowed(manifest_path: Path, fr: dict, lib: Path) -> dict:
    """Refresh the adoption pin per the manifest's update policy (never pinned)."""
    if fr.get("status") not in ("BEHIND", "DIVERGED"):
        return {"performed": False, "detail": "freshness is current; nothing to sync"}
    if not fr.get("remote_revision"):
        return {"performed": False, "detail": "no remote revision to sync to"}
    if (
        fr.get("manifest_update") != "automatic"
        or fr.get("manifest_policy") != "require-current"
    ):
        return {
            "performed": False,
            "detail": "update policy requires explicit review (never silently adopt)",
        }
    cc_path = lib / "tools" / "contractctl" / "contractctl.py"
    r = subprocess.run(
        [sys.executable, str(cc_path), "sync", "--manifest", str(manifest_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if r.returncode != 0:
        return {"performed": False, "detail": r.stderr.strip() or r.stdout.strip()}
    return {
        "performed": True,
        "detail": "pin refreshed to authoritative remote revision",
    }


# ------------------------------------------------------------- carryover

HANDOFF_PATTERNS = (
    "HANDOFF*.md",
    "*.handoff.md",
    "HANDOFF.md",
    "STATE.md",
    "CURRENT.md",
)


def discover_carryover(repo: Path, cfg: dict, gh: dict | None) -> dict:
    """Phase 3 — discover what previous work left behind; classify it."""
    items: list[dict] = []
    if cfg["repositories"]["inspect_previous_work"]:
        for sub in (".agent", ".project", ".contracts", "."):
            base = repo / sub
            if not base.is_dir():
                continue
            for pattern in HANDOFF_PATTERNS:
                for f in sorted(base.glob(pattern)):
                    if f.is_file():
                        items.append(_handoff_item(f, repo))
        sessions = repo / ".contracts" / "sessions"
        if sessions.is_dir():
            for f in sorted(sessions.glob("*.json")):
                items.append(_session_item(f))

    # branches (local), excluding current + the default branch
    st = collect_repo_state(repo, cfg)
    branch = st.get("branch")
    default = st.get("default_branch", "main")
    br = git0(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    for b in br.stdout.split():
        if b in (branch, default):
            continue
        r = git0(
            repo,
            "merge-base",
            "--is-ancestor",
            b,
            f"origin/{default}" if default else "HEAD",
        )
        merged = r.returncode == 0
        items.append(
            {
                "kind": "branch",
                "label": f"branch:{b}",
                "detail": f"merged into {default}"
                if merged
                else "not merged into default",
                "disposition": "MERGED" if merged else "UNKNOWN",
                "action": "delete-if-proven-no-longer-needed" if merged else "preserve",
                "evidence": f"merge-base --is-ancestor {b} origin/{default}"
                if merged
                else "no merge proof",
            }
        )
    # worktrees
    for wt in st.get("worktrees", []):
        items.append(
            {
                "kind": "worktree",
                "label": f"worktree:{wt}",
                "detail": "linked worktree",
                "disposition": "STILL_ACTIVE",
                "action": "preserve",
                "evidence": "git worktree list",
            }
        )
    # PRs / issues via gh (inspection only)
    if gh is not None and cfg["github"]["inspect_pull_requests"]:
        for pr in gh.get("prs", []):
            items.append(_pr_item(pr, cfg))
    if gh is not None and cfg["github"]["inspect_issues"]:
        for iss in gh.get("issues", []):
            items.append(_issue_item(iss))
    return {"items": items, "state": carryover_state(items)}


def _handoff_item(f: Path, repo: Path) -> dict:
    text = ""
    try:
        text = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    m = re.search(r"(?m)^NEXT:\s*(.+)$", text)
    next_line = m.group(1).strip() if m else None
    disp = "DONE"
    if next_line and next_line.lower() not in ("nothing required", "none", "n/a"):
        disp = "UNKNOWN"
        low = next_line.lower()
        if "waiting_for_help" in low or "needs help" in low or "help" in low:
            disp = "WAITING_FOR_HELP"
        elif "defer" in low:
            disp = "DEFERRED"
        elif "blocked" in low or "block" in low:
            disp = "BLOCKED"
    try:
        label = f"handoff:{f.relative_to(repo)}"
    except ValueError:
        label = f"handoff:{f.name}"
    return {
        "kind": "handoff",
        "label": label,
        "detail": f"NEXT: {next_line}" if next_line else "no NEXT line",
        "disposition": disp,
        "action": "read-and-continue"
        if disp in ("UNKNOWN", "STILL_ACTIVE", "WAITING_FOR_HELP", "BLOCKED")
        else "none",
        "evidence": str(f),
    }


def _session_item(f: Path) -> dict:
    data = {}
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    stat = data.get("commitment")
    task = data.get("task", "")
    disp = {"ACTIVE": "STILL_ACTIVE", "STALE": "UNKNOWN", "INACTIVE": "DEFERRED"}.get(
        str(stat), "UNKNOWN"
    )
    return {
        "kind": "commitment",
        "label": f"commitment:{f.name}",
        "detail": f"task={task!r} state={stat}",
        "disposition": disp,
        "action": "revalidate" if disp != "DEFERRED" else "none",
        "evidence": str(f),
    }


def _pr_item(pr: dict, cfg: dict) -> dict:
    n = pr.get("number")
    ready = _pr_ready(pr, cfg)
    if ready is True:
        disp = "STILL_ACTIVE"
        action = "merge-when-permit-active"
    elif ready is False and _pr_hard_block(pr):
        disp = "BLOCKED"
        action = "resolve-or-defer"
    elif ready is False:
        disp = "WAITING_FOR_HELP"
        action = "await-checks-or-review"
    else:
        disp = "UNKNOWN"
        action = "preserve"
    return {
        "kind": "pr",
        "label": f"pr:{n}",
        "detail": f"{pr.get('title', '')[:80]} [{pr.get('headRefName', '')}]",
        "disposition": disp,
        "action": action,
        "evidence": json.dumps(_pr_ready_fields(pr), sort_keys=True),
    }


def _issue_item(iss: dict) -> dict:
    n = iss.get("number")
    resolved = iss.get("_resolved_by", None)
    if resolved:
        disp = "CLOSED"
        action = "close-with-provenance"
    else:
        disp = "STILL_ACTIVE"
        action = "leave-open"
    return {
        "kind": "issue",
        "label": f"issue:{n}",
        "detail": iss.get("title", "")[:80],
        "disposition": disp,
        "action": action,
        "evidence": f"merged PR #{resolved} references close"
        if resolved
        else "no resolution proof",
    }


def carryover_state(items: list[dict]) -> str:
    if not items:
        return "RECONCILED"
    if any(i.get("disposition") == "UNKNOWN" for i in items):
        return "PARTIAL"
    return "RECONCILED"


# ------------------------------------------------------------- github layer


def gh_bin(cfg: dict, env: dict | None = None) -> str | None:
    env = env or os.environ
    if env.get("PLAY_NICE_GH"):
        return env["PLAY_NICE_GH"]
    if cfg["github"]["bin"] != "gh":
        return cfg["github"]["bin"]
    return shutil.which("gh")


def repo_identity(repo: Path) -> str | None:
    r = git0(repo, "remote", "get-url", "origin")
    url = r.stdout.strip() if r.returncode == 0 else ""
    m = re.search(
        r"(?:github\.com[/:]|git@github\.com:)([^/]+)/([^/]+?)(?:\.git)?$", url
    )
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    m = re.match(r"([\w.-]+/[\w.-]+?)(?:\.git)?$", url)
    if m and "/" in url:
        return m.group(1)
    return None


def gh_query(
    bin_path: str, repo: Path, args: list[str], timeout: int = 60
) -> subprocess.CompletedProcess:
    ident = repo_identity(repo)
    cmd = [bin_path]
    if ident:
        cmd += ["-R", ident]
    cmd += args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def gh_json(bin_path: str, repo: Path, args: list[str]) -> list | dict | None:
    r = gh_query(bin_path, repo, args)
    if r.returncode != 0:
        return None
    try:
        return json.loads(r.stdout)
    except ValueError:
        return None


def collect_github_state(repo: Path, cfg: dict, env: dict | None = None) -> dict:
    """Read-only GitHub inspection: PRs, issues, per-PR CI. UNKNOWN on failure."""
    bin_path = gh_bin(cfg, env)
    out = {"available": bool(bin_path), "prs": [], "issues": [], "note": ""}
    if not bin_path:
        out["note"] = (
            "gh not available; GitHub state UNKNOWN (fail closed for mutations)"
        )
        return out
    try:
        if cfg["github"]["inspect_pull_requests"]:
            prs = gh_json(
                bin_path,
                repo,
                [
                    "pr",
                    "list",
                    "--state",
                    "open",
                    "--json",
                    "number,title,headRefName,baseRefName,isDraft,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,url",
                ],
            )
            if prs is None:
                out["note"] += "pr list UNKNOWN; "
            else:
                for pr in prs:
                    out["prs"].append(_enrich_pr(bin_path, repo, pr, cfg))
        if cfg["github"]["inspect_issues"]:
            issues = gh_json(
                bin_path,
                repo,
                ["issue", "list", "--state", "open", "--json", "number,title,url"],
            )
            if issues is None:
                out["note"] += "issue list UNKNOWN; "
            else:
                for i in issues:
                    i["_resolved_by"] = _issue_resolved_by(bin_path, repo, i["number"])
                out["issues"] = issues
        if out["note"]:
            out["available"] = False
            out["note"] = (out["note"].rstrip("; ")
                           + " — next: run `gh auth status` to check gh can reach this repo")
    except (OSError, subprocess.TimeoutExpired) as e:
        out["available"] = False
        out["note"] = f"github inspection failed: {e}"
    return out


def _enrich_pr(bin_path: str, repo: Path, pr: dict, cfg: dict) -> dict:
    """Attach the deterministic readiness evidence for one PR."""
    n = pr.get("number")
    out = dict(pr)
    out["_ready"] = _pr_ready(pr, cfg)
    checks = pr.get("statusCheckRollup") or []
    failures = [
        c.get("name")
        for c in checks
        if c.get("conclusion") in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT")
    ]
    pending = [
        c.get("name")
        for c in checks
        if c.get("status") in ("IN_PROGRESS", "QUEUED", "PENDING")
        or (c.get("conclusion") in (None, "PENDING"))
    ]
    out["_failing_checks"] = failures
    out["_pending_checks"] = pending
    return out


def _pr_ready_fields(pr: dict) -> dict:
    return {
        "draft": pr.get("isDraft"),
        "mergeable": pr.get("mergeable"),
        "mergeStateStatus": pr.get("mergeStateStatus"),
        "reviewDecision": pr.get("reviewDecision"),
        "failing": (pr.get("_failing_checks") or [])
        if "_failing_checks" in pr
        else [
            c.get("name")
            for c in (pr.get("statusCheckRollup") or [])
            if c.get("conclusion") in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT")
        ],
    }


def _pr_hard_block(pr: dict) -> bool:
    return (
        bool(pr.get("_failing_checks") or pr.get("_pending_checks"))
        or pr.get("mergeable") == "CONFLICTING"
        or pr.get("mergeStateStatus") in ("BLOCKED", "BEHIND")
    )


def _pr_ready(pr: dict, cfg: dict) -> bool:
    """Objective readiness only — never 'probably okay'."""
    if pr.get("isDraft"):
        return False
    if pr.get("mergeable") not in ("MERGEABLE", True):
        return False
    if pr.get("mergeStateStatus") not in ("CLEAN", "UNSTABLE", None):
        # BEHIND / BLOCKED / DIRTY / DRAFT / HAS_HOOKS / UNKNOWN -> not ready
        return False
    if pr.get("statusCheckRollup") is not None:
        for c in pr.get("statusCheckRollup") or []:
            if c.get("conclusion") in ("FAILURE", "ERROR", "CANCELLED", "TIMED_OUT"):
                return False
            if c.get("status") in ("IN_PROGRESS", "QUEUED", "PENDING"):
                return False
    if (
        cfg["safety"]["respect_required_reviews"]
        or cfg["github"]["merge_ready_pull_requests"]
    ):
        if pr.get("reviewDecision") == "REVIEW_REQUIRED":
            return False
    return True


def _issue_resolved_by(bin_path: str, repo: Path, number: int) -> int | None:
    """Proven resolution: a merged PR whose head/body references 'close/fix #number'."""
    prs = gh_json(
        bin_path,
        repo,
        ["pr", "list", "--state", "merged", "--json", "number,body,title"],
    )
    if prs is None:
        return None
    pat = re.compile(rf"(?im)(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#{number}\b")
    for pr in prs:
        body = (pr.get("body") or "") + " " + (pr.get("title") or "")
        if pat.search(body):
            return pr.get("number")
    return None


# ------------------------------------------------------------- auto-finish


def reconcile_github(
    repo: Path, cfg: dict, permit: dict, gh: dict, env: dict | None = None
) -> list[dict]:
    """Phases 4–6 — merge ready PRs / close proven issues / prune merged branches.

    Runs ONLY under an ACTIVE work permit AND explicit config grants.
    """
    ops: list[dict] = []
    bin_path = gh_bin(cfg, env)
    if not permit or permit.get("work_permit") != "ACTIVE":
        return [{"op": "skip", "detail": "no ACTIVE work permit; mutation blocked"}]
    if not bin_path:
        return [
            {
                "op": "skip",
                "detail": "gh unavailable; remote state UNKNOWN (fail closed)",
            }
        ]
    if cfg["github"]["merge_ready_pull_requests"]:
        for pr in sorted(gh.get("prs", []), key=lambda p: p.get("number") or 0):
            n = pr.get("number")
            if pr.get("_ready") is True:
                method = cfg["github"]["merge_method"]
                r = gh_query(
                    bin_path, repo, ["pr", "merge", str(n), f"--{method}"], timeout=120
                )
                ops.append(
                    {
                        "op": "merged" if r.returncode == 0 else "merge-failed",
                        "target": f"pr:{n}",
                        "detail": r.stdout.strip()
                        or r.stderr.strip()
                        or f"gh pr merge {n} --{method}",
                    }
                )
            else:
                ops.append(
                    {
                        "op": "skip",
                        "target": f"pr:{n}",
                        "detail": _skip_reason(pr),
                    }
                )
    if cfg["github"]["close_proven_resolved_issues"]:
        for iss in gh.get("issues", []):
            n = iss.get("number")
            by = iss.get("_resolved_by")
            if by:
                r = gh_query(
                    bin_path,
                    repo,
                    [
                        "issue",
                        "close",
                        str(n),
                        "--comment",
                        f"closed by merged PR #{by} (playnice automated reconcile; provenance)",
                    ],
                    timeout=120,
                )
                ops.append(
                    {
                        "op": "closed" if r.returncode == 0 else "close-failed",
                        "target": f"issue:{n}",
                        "detail": f"resolved by merged PR #{by}",
                    }
                )
            else:
                ops.append(
                    {
                        "op": "keep",
                        "target": f"issue:{n}",
                        "detail": "no resolution proof",
                    }
                )
    if cfg["github"]["remove_proven_merged_branches"]:
        ops += _prune_branches(repo, cfg, gh, bin_path)
    return ops


def _skip_reason(pr: dict) -> str:
    if pr.get("isDraft"):
        return "draft"
    if pr.get("mergeable") == "CONFLICTING":
        return "conflicts"
    if pr.get("_failing_checks") or pr.get("_pending_checks"):
        return "checks not green"
    if pr.get("reviewDecision") == "REVIEW_REQUIRED":
        return "review required"
    if pr.get("mergeStateStatus") not in ("CLEAN", "UNSTABLE", None):
        return f"mergeStateStatus={pr.get('mergeStateStatus')}"
    return "not objectively ready"


def _prune_branches(repo: Path, cfg: dict, gh: dict, bin_path: str) -> list[dict]:
    ops: list[dict] = []
    st = collect_repo_state(repo, cfg)
    default = st.get("default_branch", "main")
    cur = st.get("branch")
    wt_paths = set(st.get("worktrees", []))
    # head branches of open PRs
    open_heads = {str(p.get("headRefName")) for p in gh.get("prs", [])}
    merged_heads = {
        str(p.get("headRefName")) for p in gh.get("prs", []) if p.get("mergedAt")
    }
    br = git0(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads")
    for b in br.stdout.split():
        if b in (cur, default, "HEAD"):
            continue
        r = git0(
            repo,
            "merge-base",
            "--is-ancestor",
            b,
            f"origin/{default}" if True else default,
        )
        merged_local = r.returncode == 0
        if b in open_heads:
            continue
        if b in wt_paths:
            continue
        if not merged_local:
            ops.append(
                {
                    "op": "keep",
                    "target": f"branch:{b}",
                    "detail": "not merged (preserved)",
                }
            )
            continue
        if (
            "origin/" + b
            in git0(
                repo, "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"
            ).stdout.split()
        ):
            r = git0(repo, "push", "origin", "--delete", b, timeout=120)
            if r.returncode == 0:
                ops.append(
                    {
                        "op": "deleted-remote",
                        "target": f"branch:{b}",
                        "detail": "merged into default",
                    }
                )
            else:
                ops.append(
                    {
                        "op": "delete-failed",
                        "target": f"branch:{b}",
                        "detail": r.stderr.strip()[:120],
                    }
                )
        r = git0(repo, "branch", "-d", b)
        if r.returncode == 0:
            ops.append(
                {
                    "op": "deleted-local",
                    "target": f"branch:{b}",
                    "detail": "merged into default",
                }
            )
        else:
            ops.append(
                {
                    "op": "keep",
                    "target": f"branch:{b}",
                    "detail": f"refused: {r.stderr.strip()[:120]}",
                }
            )
    return ops


# ------------------------------------------------------------- contract gate


def generate_impact(manifest_path: Path, task: str, lib: Path) -> dict[str, str]:
    """Deterministic task-impact acknowledgements for the resolved set.

    The orchestrator's commitment is a machine-checkable permit: for every
    selected contract it generates one explicit acknowledgement from the
    contract's own statement of what it governs, scoped to this task. The
    executing agent performs its OWN task-specific attestation as a worker
    (inheritance enforced by contractctl) — this floor is never a substitute.
    """
    cc = import_contractctl(lib)
    manifest = cc.load_adoption(manifest_path)
    res = cc.resolve_set(manifest, task)
    if res["errors"]:
        raise PlayNiceError(
            "commitment: resolution errors:\n  " + "\n  ".join(res["errors"])
        )
    by_id = {c["front_matter"]["contract_id"]: c for c in cc.load_library()}
    snippet = " ".join(task.split())[:120]
    impact: dict[str, str] = {}
    for cid, why in sorted(res["selected"].items()):
        c = by_id.get(cid)
        title = (c["front_matter"].get("title") if c else None) or cid
        purpose = _purpose_sentence(c) if c else ""
        impact[cid] = (
            f"task '{snippet}': {title} applies ({why}); {purpose}"
            if purpose
            else f"task '{snippet}': {title} applies ({why})"
        )
    return impact


def _purpose_sentence(c: dict) -> str:
    m = re.search(r"## Purpose\n+(.*?)(?:\n\n|\n## )", c.get("text", ""), re.DOTALL)
    if not m:
        return ""
    para = " ".join(m.group(1).split())
    return para[:200]


def run_contract_gate(
    manifest_path: Path, task: str, lib: Path, role: str = "orchestrator"
) -> dict:
    """Phase 7 — resolve / read / verify / attest / commit via contractctl."""
    cc_path = lib / "tools" / "contractctl" / "contractctl.py"
    impact = generate_impact(manifest_path, task, lib)
    cmd = [
        sys.executable,
        str(cc_path),
        "commit",
        "--manifest",
        str(manifest_path),
        "--task",
        task,
        "--role",
        role,
    ]
    for cid, sentence in sorted(impact.items()):
        cmd += ["--impact", f"{cid}={sentence}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    text = r.stdout + r.stderr
    if r.returncode != 0:
        fr_state = re.search(r"REMOTE FRESHNESS: (\w+)", text)
        state = "UNKNOWN"
        if "CONTRACT COMMITMENT: STALE" in text:
            state = "STALE"
        elif (
            "CONTRACT COMMITMENT: INACTIVE" in text or "CONTRACT GATE: BLOCKED" in text
        ):
            state = "INACTIVE"
        return {
            "ok": False,
            "state": state,
            "freshness_state": fr_state.group(1) if fr_state else None,
            "output": text.strip(),
        }
    m = re.search(r"session artifact written: (.+)$", r.stdout, re.MULTILINE)
    artifact_path = Path(m.group(1).strip()) if m else None
    artifact = {}
    if artifact_path and artifact_path.is_file():
        try:
            artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        except ValueError:
            artifact = {}
    return {
        "ok": True,
        "state": "ACTIVE",
        "artifact_path": str(artifact_path) if artifact_path else None,
        "artifact": artifact,
        "output": r.stdout,
        "impact": impact,
        "library_revision": artifact.get("library_revision"),
    }


# ------------------------------------------------------------- work permit


_VERIFY_HEADING = re.compile(r"^##[ \t]+verify\b.*$", re.IGNORECASE | re.MULTILINE)


def read_verify_section(repo: Path) -> dict:
    """The repo's own definition of done: the `## Verify` section of its AGENTS.md.

    DECLARED carries the section text and the commands in its fenced code blocks;
    UNKNOWN says which part is missing. Never blocks work: a missing section is
    surfaced in the permit, the work output and the worker prompt, so it gets added."""
    ag = repo / "AGENTS.md"
    if not ag.is_file():
        return {"state": "UNKNOWN", "reason": "no AGENTS.md", "source": None, "commands": []}
    text = ag.read_text(encoding="utf-8", errors="replace")
    m = _VERIFY_HEADING.search(text)
    if not m:
        return {"state": "UNKNOWN", "reason": "AGENTS.md has no `## Verify` section",
                "source": "AGENTS.md", "commands": []}
    rest = text[m.end():]
    nxt = re.search(r"^#{1,2}[ \t]+\S", rest, re.MULTILINE)
    body = (rest[: nxt.start()] if nxt else rest).strip()
    commands: list[str] = []
    for block in re.findall(r"^```[^\n]*\n(.*?)^```", body, re.MULTILINE | re.DOTALL):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(line[2:] if line.startswith("$ ") else line)
    if not commands:
        return {"state": "UNKNOWN", "reason": "`## Verify` names no command in a code block",
                "source": "AGENTS.md", "commands": [], "text": body}
    return {"state": "DECLARED", "source": "AGENTS.md", "commands": commands, "text": body}


def write_permit(
    repo: Path,
    manifest_path: Path,
    task: str,
    fr: dict,
    repo_state: dict,
    carryover: dict,
    gate: dict,
) -> dict:
    """Phase 8 — a secret-free machine-readable work permit."""
    artifact = gate.get("artifact") or {}
    source = artifact.get("source") or {}
    verify = read_verify_section(repo)
    permit = {
        "format": "play-nice/work-permit-v1",
        "work_permit": "ACTIVE",
        "task": task,
        "play_nice": {
            "status": fr.get("status", "UNKNOWN"),
            "revision": fr.get("remote_revision"),
            "source_repository": source.get("repository") or fr.get("repository"),
            "ref": fr.get("ref") or source.get("ref"),
            "policy": fr.get("manifest_policy", "pinned"),
            "enforced": bool(fr.get("enforced")),
        },
        "repository": {
            "status": repo_state.get("status", "UNKNOWN"),
            "revision": repo_state.get("head"),
            "branch": repo_state.get("branch"),
            "dirty": bool(repo_state.get("dirty")),
        },
        "carryover": {
            "status": carryover.get("state", "RECONCILED"),
            "items": carryover.get("items", []),
        },
        "contract_gate": artifact.get("contract_gate", "PASS"),
        "commitment": {
            "status": artifact.get("commitment", "ACTIVE"),
            "bundle_sha256": artifact.get("bundle_sha256"),
            "bundle_receipt": artifact.get("bundle_receipt"),
            "task": artifact.get("task"),
            "role": artifact.get("role", "session"),
            "artifact": gate.get("artifact_path"),
        },
        "verify": verify,
        "worker_packet": {
            "INHERITED_CONTRACT_BUNDLE": artifact.get("bundle_sha256"),
            "PLAY_NICE_SOURCE_REVISION": source.get("revision"),
            "PARENT_CONTRACT_COMMITMENT": artifact.get("commitment", "ACTIVE"),
            "VERIFY": verify["commands"],
        },
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "library": gate.get("library_revision"),
    }
    out = manifest_path.parent / "work-permit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(permit, indent=2) + "\n", encoding="utf-8")
    permit["_path"] = str(out)
    return permit


def load_permit(repo: Path, manifest_path: Path | None = None) -> dict | None:
    if manifest_path is not None:
        p = manifest_path.parent / "work-permit.json"
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                return None
    for rel in (".contracts/work-permit.json", ".project/contracts/work-permit.json"):
        p = repo / rel
        if p.is_file():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                return None
    return None


def commitment_still_active(
    manifest_path: Path, task: str, lib: Path
) -> tuple[bool, str]:
    """Live revalidation: session-status re-checks remote freshness under
    require-current, so a stale commitment (remote moved since the permit) is
    never treated as authorization to mutate."""
    cc_path = lib / "tools" / "contractctl" / "contractctl.py"
    r = subprocess.run(
        [
            sys.executable,
            str(cc_path),
            "session-status",
            "--manifest",
            str(manifest_path),
            "--role",
            "orchestrator",
            "--task",
            task,
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    text = r.stdout + r.stderr
    active = "CONTRACT COMMITMENT: ACTIVE" in text
    if active:
        return True, "commitment ACTIVE (freshness re-verified)"
    m = re.search(r"CONTRACT COMMITMENT: (\w+)", text)
    return False, f"commitment {m.group(1) if m else 'UNKNOWN'} — {text.strip()[:160]}"


# ------------------------------------------------------------- agent launch


def build_agent_prompt(permit: dict, task: str, lib: Path) -> str:
    wp = permit["worker_packet"]
    return (
        "WORK PERMIT: ACTIVE — playnice orchestrator session\n"
        f"task: {task}\n"
        f"repo: {permit['repository']['branch']} @{permit['repository']['revision']}\n"
        f"PLAY NICE: {permit['play_nice']['status']} @{(permit['play_nice'].get('revision') or '')[:12]}\n"
        f"library: {lib} (contractctl lives here; PLAY_NICE_LIBRARY is set)\n"
        f"INHERITED CONTRACT BUNDLE: {wp.get('INHERITED_CONTRACT_BUNDLE')}\n"
        f"PLAY_NICE_SOURCE_REVISION: {wp.get('PLAY_NICE_SOURCE_REVISION')}\n"
        f"PARENT CONTRACT COMMITMENT: {wp.get('PARENT_CONTRACT_COMMITMENT')}\n"
        "\n"
        "Instructions:\n"
        "1. Follow this repository's AGENTS.md, then resolve and read the applicable\n"
        "   Play-Nice contracts from the library at $PLAY_NICE_LIBRARY.\n"
        "2. Run your OWN worker contract gate before mutating: contractctl commit\n"
        '   --manifest <manifest> --task "<your task>" --worker --parent-bundle\n'
        "   <INHERITED_CONTRACT_BUNDLE> with --impact for every resolved contract,\n"
        "   including the inherited set. Workers inherit; they may strengthen\n"
        "   constraints, never weaken them, and may not resolve a weaker source.\n"
        "3. Do the bounded task. Stay in scope and in the repository.\n"
        "4. Commit your work with explicit paths (never `git add -A` in shared\n"
        "   checkouts), push, and open a PR when that is the workflow.\n"
        "5. End your reply with the standard handoff sections\n"
        "   (CURRENT / CHANGED / VERIFIED / CONTRACTS / UNKNOWN / DEFERRED / NEXT).\n"
        f"{_verify_instructions(permit.get('verify') or {})}"
        "\n"
        f"THE WORK: {task}"
    )


def _verify_instructions(verify: dict) -> str:
    """Step 6 of the worker prompt: how this repo says done is proven."""
    if verify.get("state") == "DECLARED":
        cmds = "".join(f"     $ {c}\n" for c in verify["commands"])
        return (
            "6. Done means this repository's Verify commands pass (AGENTS.md `## Verify`).\n"
            "   Run each one and put the command and its output in VERIFIED:\n" + cmds
        )
    return (
        f"6. VERIFY: UNKNOWN ({verify.get('reason', 'not declared')}). Say which checks you\n"
        "   ran in VERIFIED, mark anything unrun UNVERIFIED, and propose a `## Verify`\n"
        "   section for AGENTS.md in NEXT.\n"
    )


def launch_agent(
    cfg: dict, repo: Path, task: str, permit: dict, lib: Path, env: dict | None = None
) -> int:
    command = cfg["agent"]["command"]
    args = list(cfg["agent"]["args"] or [])
    if not shutil.which(command):
        raise PlayNiceError(
            f"agent command '{command}' not found on PATH; install it or set "
            "agent.command in the play-nice global config"
        )
    prompt = build_agent_prompt(permit, task, lib)
    full = [command, *args, prompt]
    e = dict(os.environ)
    e["PLAY_NICE_LIBRARY"] = str(lib)
    e["PLAY_NICE_PERMIT"] = permit.get("_path") or ""
    timeout = cfg["post"].get("timeout_minutes") or 0
    print(f"launching agent: {' '.join(full[:3])} ...")
    r = subprocess.run(
        full, cwd=str(repo), env=e, timeout=(timeout * 60) if timeout else None
    )
    return r.returncode


# ------------------------------------------------------------- handoff


def handoff_path(repo: Path, cfg: dict) -> Path:
    p = cfg["handoff"].get("path") or ""
    if p:
        path = Path(p)
        if not path.is_absolute():
            path = repo / path
        return path
    if (repo / ".project").is_dir():
        return repo / ".project" / "HANDOFF.md"
    return repo / ".agent" / "HANDOFF.md"


def format_handoff(
    repo: Path,
    cfg: dict,
    fr: dict,
    repo_state: dict,
    carryover: dict,
    gate: dict,
    permit: dict,
    ops: list[dict],
    agent_rc: int | None,
    task: str,
    next_line: str,
) -> str:
    lines: list[str] = []
    lines.append(
        f"CURRENT: {repo_state.get('branch')} @{str(repo_state.get('head'))[:12]} "
        f"(dirty={bool(repo_state.get('dirty'))})"
    )
    lines.append(f"CHANGED: playnice orchestration for task {task!r}")
    if ops:
        for op in ops:
            lines.append(f"  - {op.get('op')}: {op.get('target')} ({op.get('detail')})")
    lines.append("VERIFIED: " + _verified_line(gate, fr, repo_state))
    lines.append("CONTRACTS: " + _contracts_line(gate))
    lines.append("UNKNOWN: " + _unknown_line(fr, repo_state, carryover, agent_rc))
    lines.append("DEFERRED: " + _deferred_line(carryover))
    lines.append(f"NEXT: {next_line}")
    return "\n".join(lines) + "\n"


def _verified_line(gate: dict, fr: dict, repo_state: dict) -> str:
    bits = []
    bits.append(f"play nice {fr.get('status')}")
    bits.append(f"repo {repo_state.get('status')}")
    if gate.get("ok"):
        bits.append("contract gate PASS (receipts+hashes verified by contractctl)")
    return "; ".join(bits)


def _contracts_line(gate: dict) -> str:
    if not gate.get("ok"):
        return f"gated: {gate.get('state', 'UNKNOWN')}"
    a = gate.get("artifact") or {}
    return (
        f"bundle {a.get('bundle_receipt')} ({str(a.get('bundle_sha256'))[:12]}) "
        f"gate {a.get('contract_gate')} commitment {a.get('commitment')} role {a.get('role')}"
    )


def _unknown_line(
    fr: dict, repo_state: dict, carryover: dict, agent_rc: int | None
) -> str:
    bits = []
    if fr.get("status") != "CURRENT":
        bits.append(f"freshness {fr.get('status')}")
    if repo_state.get("status") == "UNKNOWN":
        bits.append("repository state UNKNOWN")
    if carryover.get("state") == "PARTIAL":
        bits.append("carryover PARTIAL (see items)")
    if agent_rc is not None and agent_rc != 0:
        bits.append(f"agent exited {agent_rc}")
    return ", ".join(bits) or "none"


def _deferred_line(carryover: dict) -> str:
    items = [
        i for i in carryover.get("items", []) if i.get("disposition") == "DEFERRED"
    ]
    if not items:
        return "none"
    return "; ".join(i.get("label", "") for i in items[:5])


def write_handoff(repo: Path, cfg: dict, text: str) -> Path:
    p = handoff_path(repo, cfg)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


# ------------------------------------------------------------- NEXT


def compute_next(
    fr: dict,
    repo_state: dict,
    carryover: dict,
    gate: dict,
    ops: list[dict],
    agent_rc: int | None,
    cfg: dict,
    launched: bool,
) -> str:
    if not launched:
        return "agent not launched (--no-launch); preflight permit written"
    if agent_rc not in (0, None):
        return f"agent exited {agent_rc}; inspect the failure before further mutation"
    if repo_state.get("dirty"):
        return "working tree is dirty; inspect and commit/park the changes"
    if fr.get("enforced") and fr.get("status") != "CURRENT":
        return f"play nice freshness {fr.get('status')}; refresh and re-gate before mutation"
    if not gate.get("ok"):
        return f"contract gate {gate.get('state', 'UNKNOWN')}; resolve, then re-run"
    failed = [
        o
        for o in ops
        if o.get("op") in ("merge-failed", "delete-failed", "close-failed")
    ]
    if failed:
        return (
            f"{len(failed)} reconcile operation(s) failed; inspect: "
            f"{failed[0].get('detail', '')[:120]}"
        )
    waiting = [
        o
        for o in ops
        if o.get("op") == "skip" and "review required" in o.get("detail", "")
    ]
    if waiting:
        return "WAITING_FOR_HELP: a PR requires human review before merge"
    if cfg["github"]["merge_ready_pull_requests"]:
        needs_ci = [
            o
            for o in ops
            if o.get("op") == "skip" and "checks not green" in o.get("detail", "")
        ]
        if needs_ci:
            return "WAITING_FOR_HELP: PR(s) awaiting CI"
    blocked = [
        i for i in carryover.get("items", []) if i.get("disposition") == "BLOCKED"
    ]
    if blocked:
        return "BLOCKED: carryover items: " + ", ".join(
            i.get("label", "") for i in blocked[:5]
        )
    unknown = [
        i for i in carryover.get("items", []) if i.get("disposition") == "UNKNOWN"
    ]
    if unknown:
        return "carryover has `UNKNOWN` items (preserved): " + ", ".join(
            i.get("label", "") for i in unknown[:5]
        )
    return "nothing required"


# ------------------------------------------------------------- orchestration


def _print_permit(fr: dict, repo_state: dict, carryover: dict, gate: dict) -> None:
    print(
        f"PLAY NICE: {fr.get('status')} ({fr.get('ref') or '?'} @{str(fr.get('remote_revision') or '')[:12]})"
    )
    print(
        f"REPOSITORY: {repo_state.get('status')} ({repo_state.get('branch')} @{str(repo_state.get('head') or '')[:12]}, dirty={bool(repo_state.get('dirty'))})"
    )
    print(
        f"CARRYOVER: {carryover.get('state')} ({len(carryover.get('items', []))} items)"
    )
    gate_ok = gate.get("ok")
    print(
        f"CONTRACT GATE: {gate.get('artifact', {}).get('contract_gate', 'FAIL') if gate_ok else 'FAIL'}"
    )
    print(
        f"COMMITMENT: {gate.get('artifact', {}).get('commitment', 'INACTIVE') if gate_ok else 'INACTIVE'}"
    )
    print("WORK PERMIT: ACTIVE")


def _verify_line(verify: dict) -> str:
    if verify.get("state") == "DECLARED":
        return f"VERIFY: DECLARED ({len(verify['commands'])} command(s) from AGENTS.md)"
    return f"VERIFY: UNKNOWN ({verify.get('reason', 'not declared')})"


def cmd_work(args) -> int:
    cfg = load_global_config(Path(args.config) if args.config else None)
    if args.no_github:
        cfg["github"] = {
            **cfg["github"],
            "inspect_pull_requests": False,
            "inspect_issues": False,
            "inspect_ci": False,
            "merge_ready_pull_requests": False,
            "close_proven_resolved_issues": False,
            "remove_proven_merged_branches": False,
        }
    env = dict(os.environ)
    if args.agent:
        cfg["agent"]["command"] = args.agent
    repo = Path(args.repo).resolve()
    task = args.task
    json_mode = bool(getattr(args, "json_output", False))

    def emit(line: str = "", *, err: bool = False) -> None:
        """Human prose, suppressed under --json (which gets one JSON object)."""
        if not json_mode:
            print(line, file=sys.stderr if err else sys.stdout)

    def finish(rc: int, state: str, **fields) -> int:
        if json_mode:
            payload: dict = {
                "command": "work",
                "state": state,
                "task": task or None,
                "freshness": None,
                "permit_path": None,
                "handoff_path": None,
                "next": None,
            }
            payload.update(fields)
            print(json.dumps(payload, indent=2, sort_keys=True))
        return rc

    if not task:
        emit(
            'playnice: a task is required (e.g. playnice work "fix the settings page")',
            err=True,
        )
        return finish(1, "NO_TASK")
    manifest_path = find_adoption_manifest(repo, args.manifest)
    if manifest_path is None:
        emit(
            "PLAY NICE: UNKNOWN — no adoption manifest found in this repository.\n"
            "  A participating repo carries `.contracts/adoption.yaml` (or\n"
            "  `.project/contracts/adoption.yaml`). Copy an example and pin the\n"
            "  reviewed revision: `cp examples/<repo>.adoption.yaml <repo>/.contracts/adoption.yaml`",
            err=True,
        )
        return finish(2, "NO_MANIFEST")

    lib = find_library(cfg, Path.cwd(), env)
    fr = play_nice_check(manifest_path, lib, cfg)
    emit(
        f"REMOTE FRESHNESS: {fr.get('status')}  (enforced={bool(fr.get('enforced'))})"
    )
    if fr.get("remote_revision"):
        emit(f"  authoritative revision: {fr['remote_revision']}")
    if freshness_blocked(fr):
        emit(f"  - {fr.get('detail', '')}")
        sync = sync_pin_if_allowed(manifest_path, fr, lib)
        if sync["performed"]:
            emit(f"  synced: {sync['detail']}")
            fr = play_nice_check(manifest_path, lib, cfg)
            emit(f"REMOTE FRESHNESS: {fr.get('status')}  (after sync)")
        else:
            if sync.get("detail"):
                emit(f"  (no auto-sync: {sync['detail']})")
        if freshness_blocked(fr):
            emit(
                "CONTRACT COMMITMENT: INACTIVE — mutating work stays blocked (fail closed)"
            )
            return finish(2, "INACTIVE", freshness=fr.get("status"))

    repo_state = reconcile_repo(repo, cfg)
    gh = None
    if cfg["github"]["inspect_pull_requests"] or cfg["github"]["inspect_issues"]:
        gh = collect_github_state(repo, cfg, env)
        if gh.get("note") and not gh.get("available"):
            emit(f"GITHUB STATE: {gh['note']}")
    carryover = discover_carryover(repo, cfg, gh)
    for item in carryover["items"]:
        emit(
            f"  carryover: {item.get('disposition'):16s} {item.get('label')} — {item.get('action')}"
        )
    if carryover["state"] != "RECONCILED":
        emit(
            f"CARRYOVER: {carryover['state']} — unknown items are preserved, never guessed"
        )

    gate = run_contract_gate(manifest_path, task, lib, role="orchestrator")
    if not gate["ok"]:
        emit(gate["output"])
        emit(f"\nCONTRACT GATE: {gate['state']}")
        emit("CONTRACT COMMITMENT: INACTIVE")
        return finish(
            2, "GATE_BLOCKED", freshness=fr.get("status"), gate_state=gate["state"]
        )
    emit(gate["output"])

    permit = write_permit(repo, manifest_path, task, fr, repo_state, carryover, gate)
    if not json_mode:
        _print_permit(fr, repo_state, carryover, gate)
    emit(_verify_line(permit.get("verify") or {}))
    emit(f"permit: {permit.get('_path')}")

    if args.no_launch:
        next_line = compute_next(fr, repo_state, carryover, gate, [], None, cfg, False)
        hd = write_handoff(
            repo,
            cfg,
            format_handoff(
                repo,
                cfg,
                fr,
                repo_state,
                carryover,
                gate,
                permit,
                [],
                None,
                task,
                next_line,
            ),
        )
        emit(f"handoff: {hd}")
        emit(f"NEXT: {next_line}")
        return finish(
            0,
            "PERMITTED",
            freshness=fr.get("status"),
            permit_path=permit.get("_path"),
            handoff_path=str(hd),
            next=next_line,
        )

    agent_rc = launch_agent(cfg, repo, task, permit, lib, env)
    ops: list[dict] = []
    if agent_rc == 0:
        emit("agent finished; reconciling post-work ...")
        if (
            cfg["github"]["merge_ready_pull_requests"]
            or cfg["github"]["close_proven_resolved_issues"]
            or cfg["github"]["remove_proven_merged_branches"]
        ):
            gh2 = collect_github_state(repo, cfg, env)
            ops = reconcile_github(repo, cfg, permit, gh2, env)
            for op in ops:
                emit(
                    f"  reconcile: {op.get('op')}: {op.get('target')} — {op.get('detail', '')}"
                )
        else:
            emit("  (github reconcile disabled in config)")
    else:
        emit(f"agent exited {agent_rc}")

    next_line = compute_next(fr, repo_state, carryover, gate, ops, agent_rc, cfg, True)
    hd = write_handoff(
        repo,
        cfg,
        format_handoff(
            repo,
            cfg,
            fr,
            repo_state,
            carryover,
            gate,
            permit,
            ops,
            agent_rc,
            task,
            next_line,
        ),
    )
    emit(f"handoff: {hd}")
    emit(f"NEXT: {next_line}")
    return finish(
        0 if agent_rc == 0 else 3,
        "COMPLETED" if agent_rc == 0 else "AGENT_FAILED",
        freshness=fr.get("status"),
        permit_path=permit.get("_path"),
        handoff_path=str(hd),
        next=next_line,
        agent_rc=agent_rc,
    )


def cmd_status(args) -> int:
    """Read-only inspection: freshness + repo + carryover + GitHub state."""
    cfg = load_global_config(Path(args.config) if args.config else None)
    if args.no_github:
        cfg["github"] = {
            **cfg["github"],
            "inspect_pull_requests": False,
            "inspect_issues": False,
            "inspect_ci": False,
        }
    env = dict(os.environ)
    repo = Path(args.repo).resolve()
    # a repo that cannot be opened is an error, not an UNKNOWN that exits 0
    # (matches `playnice work`, which fails closed the same way)
    if not repo.is_dir() or not is_git_repo(repo):
        print(
            f"error: repo not found or not a git repository: {repo}", file=sys.stderr
        )
        print(
            "  next: point --repo at an existing git checkout, or run this inside one",
            file=sys.stderr,
        )
        return 2
    manifest_path = find_adoption_manifest(repo, args.manifest)
    lib = find_library(cfg, Path.cwd(), env)
    out: dict = {}
    if manifest_path is None:
        out["adoption"] = "UNKNOWN"
        out["play_nice"] = {
            "status": "UNKNOWN",
            "enforced": False,
            "detail": "no adoption manifest found in this repository",
        }
    else:
        fr = play_nice_check(manifest_path, lib, cfg)
        out["play_nice"] = fr
    out["checks"] = _status_checks(repo)
    out["readiness"] = work_readiness(manifest_path, out.get("play_nice") or {})
    rs = collect_repo_state(repo, cfg)
    out["repository"] = rs
    gh = None
    if cfg["github"]["inspect_pull_requests"] or cfg["github"]["inspect_issues"]:
        gh = collect_github_state(repo, cfg, env)
        out["github"] = gh
    co = discover_carryover(repo, cfg, gh)
    out["carryover"] = {
        "state": co["state"],
        "items": [
            {
                "kind": i.get("kind"),
                "label": i.get("label"),
                "detail": i.get("detail"),
                "disposition": i.get("disposition"),
                "action": i.get("action"),
            }
            for i in co["items"]
        ],
    }
    if args.json_output:
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0
    fr = out.get("play_nice") or {}
    fr = {**fr, "status": fr.get("status", "UNKNOWN")}
    ck = out["checks"]
    print(f"CHECKS: {ck['state']} — {ck['words']}")
    if manifest_path is None:
        print("ADOPTION: not configured — no adoption manifest, so contracts are "
              "not enforced here (that is fine for ordinary use)")
    else:
        mode = "enforced" if fr.get("enforced") else "not enforced"
        print(f"ADOPTION: {fr.get('status')} ({mode}) — {fr.get('detail') or 'no detail'}")
    rd = out["readiness"]
    print(f"WORK READINESS: {rd['state']} — {rd['words']}")
    if rd.get("next"):
        print(f"  next: {rd['next']}")
    print(
        f"REPOSITORY: {out['repository'].get('status')} ({out['repository'].get('branch')} @{str(out['repository'].get('head') or '')[:12]}, dirty={bool(out['repository'].get('dirty'))})"
    )
    print(
        f"CARRYOVER: {out['carryover']['state']} ({len(out['carryover']['items'])} items)"
    )
    for item in out["carryover"]["items"]:
        print(
            f"  carryover: {item.get('disposition'):16s} {item.get('label')} — {item.get('action')}"
        )
    if out.get("github"):
        g = out["github"]
        print(
            f"GITHUB: available={bool(g.get('available'))} prs={len(g.get('prs', []))} issues={len(g.get('issues', []))}"
        )
        if g.get("note"):
            print(f"  {g['note']}")
    permit = load_permit(repo, manifest_path)
    if permit:
        print(f"WORK PERMIT: {permit.get('work_permit')} (task: {permit.get('task')})")
        if permit.get("commitment"):
            print(
                f"  commitment: {permit['commitment'].get('status')} "
                f"bundle {str(permit['commitment'].get('bundle_sha256'))[:12]}"
            )
    else:
        print("WORK PERMIT: none on file")
    return 0


def cmd_rules(args) -> int:
    """`playnice rules TASK`: the resolver, from the front door."""
    repo = Path(args.repo).expanduser().resolve()
    try:
        lib = v2_library_root(repo)
        cc = import_contractctl(lib)
    except (CheckUnavailable, PlayNiceError) as e:
        print(f"error: {e}\n  next: set PLAY_NICE_LIBRARY to a play-nice-contracts checkout")
        return 2
    mp = find_adoption_manifest(repo)
    try:
        m = cc.load_adoption(mp) if mp else {
            "always": list(cc.ROLE_BASE_SETS["agent"]), "triggers": {}}
    except cc.CTError as e:
        print(f"error: {e}")
        return 1
    res = cc.resolve_set(m, args.task, args.tag)
    titles = {c["front_matter"]["contract_id"]: c["front_matter"].get("title", "")
              for c in cc.load_library()}
    task_matched = any(r["trigger"] and r["via"] != "tag"
                       for rs in res["reasons"].values() for r in rs)
    if args.json_output:
        print(json.dumps({
            "command": "rules", "task": args.task, "manifest": str(mp) if mp else None,
            "contracts": [{"id": cid, "title": titles.get(cid, ""),
                           "reasons": res["reasons"].get(cid, [])}
                          for cid in sorted(res["selected"])],
            "errors": res["errors"], "exit": 1 if res["errors"] else 0,
            "task_matched": task_matched,
        }, indent=2, sort_keys=True))
        return 1 if res["errors"] else 0
    if res["errors"]:
        for e in res["errors"]:
            print(f"error: {e}")
        return 1
    src = f"from {mp.relative_to(repo)}" if mp else "from the library defaults (no adoption manifest)"
    print(f"RULES for {args.task!r} — {len(res['selected'])} contracts, {src}")
    for cid in sorted(res["selected"]):
        why = []
        for r in res["reasons"].get(cid, []):
            if r["trigger"]:
                why.append(f"{r['trigger']!r}" + (" (tag)" if r["via"] == "tag" else ""))
            else:
                why.append(r["source"])
        print(f"  {cid:28s} {titles.get(cid, '')} — {', '.join(dict.fromkeys(why))}")
    if not task_matched:
        print("note: no word in the task matched a trigger; these are the contracts "
              "that always apply. Name what you are building (page, API, login, "
              "secret...) to get the specific ones.")
    print("next: read each one, then start your handoff with the proof line")
    return 0


def _status_checks(repo: Path) -> dict:
    """The same verdict `playnice check` gives, summarized for `status`."""
    try:
        res = run_repo_check(repo, None)
    except Exception as e:  # status is read-only inspection: never crash on it
        return {"state": "unknown", "words": f"could not run the checks: {e}"}
    if res.get("state") == "unknown":
        return {"state": "unknown", "words": res.get("error") or "could not run the checks"}
    failing = [c["name"] for c in res.get("checks", []) if c["state"] == "needs_fix"]
    words = ("every baseline check passed" if not failing
             else "needs a fix: " + "; ".join(failing) + " (run playnice check)")
    return {"state": res["label"], "words": words}


def work_readiness(manifest_path: Path | None, fr: dict) -> dict:
    """Can `playnice work` proceed here, and if not, what blocks it?

    Mirrors the gates in cmd_work: an adoption manifest is required, and
    under enforcement the contracts must be CURRENT, unless the manifest's
    update: automatic lets work refresh the pin itself first.
    """
    if manifest_path is None:
        return {"state": "blocked",
                "words": "playnice work needs an adoption manifest; checks and "
                         "verify do not",
                "next": "contractctl init-adoption"}
    if not freshness_blocked(fr):
        return {"state": "ready", "words": "playnice work can start", "next": None}
    auto = (fr.get("manifest_update") == "automatic"
            and fr.get("manifest_policy") == "require-current"
            and fr.get("status") in ("BEHIND", "DIVERGED")
            and fr.get("remote_revision"))
    if auto:
        return {"state": "ready",
                "words": f"contracts are {fr['status']}; playnice work refreshes the "
                         "pin first (update: automatic)",
                "next": None}
    return {"state": "blocked",
            "words": f"contracts are {fr.get('status')} and enforced"
                     + (f" ({fr['detail']})" if fr.get("detail") else ""),
            "next": "contractctl upgrade-check"}


def cmd_reconcile(args) -> int:
    """Standalone carryover + auto-finish. Mutations need an ACTIVE permit."""
    cfg = load_global_config(Path(args.config) if args.config else None)
    if args.no_github:
        cfg["github"] = {
            **cfg["github"],
            "inspect_pull_requests": False,
            "inspect_issues": False,
            "inspect_ci": False,
            "merge_ready_pull_requests": False,
            "close_proven_resolved_issues": False,
            "remove_proven_merged_branches": False,
        }
    env = dict(os.environ)
    repo = Path(args.repo).resolve()
    json_mode = bool(getattr(args, "json_output", False))

    def emit(line: str = "", *, err: bool = False) -> None:
        """Human prose, suppressed under --json (which gets one JSON object)."""
        if not json_mode:
            print(line, file=sys.stderr if err else sys.stdout)

    def finish(rc: int, state: str, **fields) -> int:
        if json_mode:
            payload: dict = {
                "command": "reconcile",
                "state": state,
                "carryover": None,
                "permit_path": None,
                "handoff_path": None,
                "next": None,
            }
            payload.update(fields)
            print(json.dumps(payload, indent=2, sort_keys=True))
        return rc

    manifest_path = find_adoption_manifest(repo, args.manifest)
    lib = find_library(cfg, Path.cwd(), env)
    if manifest_path is None:
        emit("reconcile: no adoption manifest found; run a gate first", err=True)
        return finish(2, "NO_MANIFEST")
    permit = load_permit(repo, manifest_path)
    permit_path = None
    if permit is not None:
        for cand in (
            manifest_path.parent / "work-permit.json",
            repo / ".contracts" / "work-permit.json",
            repo / ".project" / "contracts" / "work-permit.json",
        ):
            if cand.is_file():
                permit_path = str(cand)
                break
    gh = None
    if cfg["github"]["inspect_pull_requests"] or cfg["github"]["inspect_issues"]:
        gh = collect_github_state(repo, cfg, env)
        if gh.get("note"):
            emit(f"GITHUB STATE: {gh['note']}")
    co = discover_carryover(repo, cfg, gh)
    for item in co["items"]:
        emit(
            f"  carryover: {item.get('disposition'):16s} {item.get('label')} — {item.get('action')}"
        )
    carryover_state = co["state"]
    if not permit or permit.get("work_permit") != "ACTIVE":
        emit(
            "reconcile: no ACTIVE work permit on file — run `playnice work` to gate first"
        )
        emit("read-only reconciliation above; mutations stay blocked")
        return finish(
            4, "READ_ONLY", carryover=carryover_state, permit_path=permit_path
        )
    ok, detail = commitment_still_active(manifest_path, permit.get("task", ""), lib)
    if not ok:
        emit(f"reconcile: {detail}")
        emit("mutations stay blocked until a fresh gate passes")
        return finish(
            4,
            "STALE_COMMITMENT",
            carryover=carryover_state,
            permit_path=permit_path,
            reason=detail,
        )
    ops = reconcile_github(repo, cfg, permit, gh, env)
    for op in ops:
        emit(
            f"  reconcile: {op.get('op')}: {op.get('target')} — {op.get('detail', '')}"
        )
    next_line = compute_next({}, {}, co, {"ok": True}, ops, None, cfg, True)
    emit(f"NEXT: {next_line}")
    return finish(
        0,
        "RECONCILED",
        carryover=carryover_state,
        permit_path=permit_path,
        next=next_line,
        ops=ops,
    )


# ================================================================ v2 surface
# verify / check / start — the zero-friction commands from the v2 plan
# (docs/decisions/2026-09-26-play-nice-v2.md, step 4). Stdlib only. Every
# message says what happened, then the next step; --json carries the same
# facts. No network except `check <url>` (10 s timeout, one attempt).
# Exit codes: verify 0 current / 1 out of date / 2 invalid; check 0 plays
# nice / 1 fix needed or behind / 2 could not check; start 0 / 2 error.

LIBRARY_URL = "https://github.com/rylee-bee-labs/play-nice-contracts"
FLOOR_REL = "contracts/everyone/FLOOR.md"
CONTRACTCTL_REL = "tools/contractctl/contractctl.py"
BADGE_REL = "assets/badge"
MARK_START = "<!-- play-nice:start -->"
MARK_END = "<!-- play-nice:end -->"
WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SEMVER_RE = re.compile(r"\d+\.\d+\.\d+")
VERSION_SHAPE_RE = re.compile(r"\d+\.\d+(?:\.\d+)?")
CONTACT_RE = re.compile(r"^(mailto:|https:|http:|tel:)")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

WALK_SKIP_DIRS = {
    ".git", "node_modules", "vendor", "third_party", "dist", "build", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".tox", ".mypy_cache", "dist", "build", ".contract-commitments",
}
FRONTEND_DEPS = {
    "react", "react-dom", "vue", "svelte", "preact", "solid-js",
    "@angular/core", "next", "nuxt", "astro",
}
API_ROUTE_RES = (
    re.compile(r"@app\.(?:route|get|post|put|delete|patch)\s*\("),
    re.compile(r"@router\.(?:get|post|put|delete|patch)\s*\("),
    re.compile(r"\bapp\.(?:get|post|put|delete|patch|all)\s*\(\s*[\"'`]"),
    re.compile(r"\brouter\.(?:get|post|put|delete)\s*\(\s*[\"'`]"),
    re.compile(r"\burlpatterns\b"),
    re.compile(r"BaseHTTPRequestHandler"),
    re.compile(r"\bexpress\s*\("),
)
SOURCE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".mjs", ".cjs", ".go", ".rb"}
SCRIPT_EXTS = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".vue", ".svelte", ".html", ".htm"}
PACK_TITLES = {
    "everyone": "Everyone",
    "work": "Agents and work",
    "people": "People",
    "surfaces": "Surfaces",
    "sites": "Sites",
    "integration": "Integration",
    "access": "Access",
}


class CheckUnavailable(Exception):
    """check/verify could not run: missing folder, no library, network down."""


def v2_library_root(cwd: Path) -> Path:
    """Find the Play-Nice library checkout offline: env, own checkout, parents."""
    env = os.environ.get("PLAY_NICE_LIBRARY")
    if env:
        p = Path(env).expanduser()
        if not (p / FLOOR_REL).is_file() or not (p / CONTRACTCTL_REL).is_file():
            raise CheckUnavailable(
                f"PLAY_NICE_LIBRARY={p} is not a play-nice-contracts checkout "
                f"(needs {FLOOR_REL} and {CONTRACTCTL_REL})"
            )
        return p.resolve()
    own = Path(__file__).resolve().parents[2]
    if (own / FLOOR_REL).is_file() and (own / CONTRACTCTL_REL).is_file():
        return own
    for up in (cwd, *cwd.parents):
        if (up / FLOOR_REL).is_file() and (up / CONTRACTCTL_REL).is_file():
            return up
    raise CheckUnavailable("no Play-Nice library checkout found")


def version_tuple(v: str) -> tuple:
    parts = [int(x) for x in v.split(".")]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def load_v2_floor(lib: Path) -> dict:
    """Version, receipt word and verbatim Rules list from the floor page."""
    text = (lib / FLOOR_REL).read_text(encoding="utf-8")
    fm = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    block = fm.group(1) if fm else ""
    version = re.search(r"(?m)^version:\s*(\S+)", block)
    receipt = re.search(r"<!--\s*contract-receipt:\s*([a-z0-9-]+)\s*-->", text)
    rules = re.search(r"(?ms)^## Rules\s*\n(.*?)^## ", text)
    if not version or not receipt or not rules:
        raise CheckUnavailable(f"{lib / FLOOR_REL} has no version, receipt or Rules section")
    return {
        "version": version.group(1),
        "receipt": receipt.group(1),
        "rules": rules.group(1).rstrip(),
    }


def load_v2_index(lib: Path) -> dict:
    """{ids: contract_id -> status, aliases: old id -> new id} from the library."""
    ids: dict[str, str] = {}
    cdir = lib / "contracts"
    if cdir.is_dir():
        for d in sorted(cdir.iterdir()):
            if not d.is_dir():
                continue
            for f in sorted(d.glob("*.md")):
                t = f.read_text(encoding="utf-8", errors="replace")
                cid = re.search(r"(?m)^contract_id:\s*(\S+)\s*$", t)
                st = re.search(r"(?m)^status:\s*(\S+)\s*$", t)
                if cid:
                    ids[cid.group(1)] = st.group(1) if st else "canonical"
    try:
        aliases = json.loads((lib / "aliases.json").read_text(encoding="utf-8")).get("aliases", {})
    except (OSError, ValueError):
        aliases = {}
    return {"ids": ids, "aliases": aliases}


def canonical_read_id(cid: str, index: dict) -> str | None:
    """Resolve a read id to a library contract id (old ids via aliases.json)."""
    if cid in index["ids"]:
        return cid
    mapped = index["aliases"].get(cid)
    return mapped if mapped in index["ids"] else None


# ------------------------------------------------------------------- verify

def split_receipt_line(line: str) -> list[str]:
    """Split on '·' or whitespace-held '-' / '|'; hyphenated words stay intact."""
    normalized = re.sub(r"\s+[-|]\s+", " · ", line)
    return [seg.strip() for seg in normalized.split("·") if seg.strip() != ""]


def parse_verify_line(line: str, index: dict) -> tuple[dict | None, str | None]:
    """Grammar from CONTRACT_PROOF.md Machine notes:
    'Play-Nice floor <version> · receipt <word>' optionally followed by
    ' · read <id>, <id>' (old ids allowed via aliases.json). Returns
    (parsed, None) or (None, problem).
    """
    segs = split_receipt_line(line)
    if not segs:
        return None, "the line is empty"
    m = re.fullmatch(r"Play-Nice floor (\S+)", segs[0])
    if not m:
        return None, f"the line must start with 'Play-Nice floor <version>', got '{segs[0]}'"
    version = m.group(1)
    if not VERSION_SHAPE_RE.fullmatch(version):
        return None, f"floor version must look like 1.0.0, got '{version}'"
    if len(segs) < 2:
        return None, "no 'receipt <word>' part after the version"
    m = re.fullmatch(r"receipt (\S+)", segs[1])
    if not m:
        return None, f"expected 'receipt <word>', got '{segs[1]}'"
    receipt = m.group(1)
    if not WORD_RE.fullmatch(receipt):
        return None, f"receipt word must be lowercase words joined with '-', got '{receipt}'"
    read: list[str] = []
    if len(segs) > 2:
        if len(segs) > 3:
            return None, "too many parts; the line ends with the optional 'read <id>, <id>'"
        m = re.fullmatch(r"read (.*)", segs[2])
        if not m:
            return None, f"expected 'read <id>, <id>', got '{segs[2]}'"
        read = [part.strip() for part in m.group(1).split(",") if part.strip()]
        if not read:
            return None, "'read' has no contract ids after it"
        bad = [cid for cid in read if not WORD_RE.fullmatch(cid)]
        if bad:
            return None, f"read ids must be lowercase ids like 'web-ui': {', '.join(bad)}"
        unknown = [cid for cid in read if canonical_read_id(cid, index) is None]
        if unknown:
            return None, (
                "unknown read ids (not library contracts, not aliases): "
                + ", ".join(unknown)
            )
    return {"version": version, "receipt": receipt, "read": read}, None


def cmd_verify(args) -> int:
    line = (args.line or "").strip()
    out: dict = {"command": "verify", "line": line}
    try:
        lib = v2_library_root(Path.cwd())
        floor = load_v2_floor(lib)
        index = load_v2_index(lib)
    except CheckUnavailable as e:
        out.update(
            state="INVALID", exit=2, message=str(e),
            next="set PLAY_NICE_LIBRARY to a play-nice-contracts checkout",
        )
        _finish_verify(args, out)
        return 2
    out["floor_version"] = floor["version"]
    out["example"] = (
        # Never print the real receipt word: it is the proof of reading.
        f"Play-Nice floor {floor['version']} · receipt <word from the floor> · read floor"
    )
    parsed, problem = parse_verify_line(line, index)
    if problem:
        out.update(
            state="INVALID", exit=2, message=problem,
            next="copy the version, the receipt word and the ids from the pages you actually read",
        )
        _finish_verify(args, out)
        return 2
    out["given"] = parsed
    current = (
        version_tuple(parsed["version"]) == version_tuple(floor["version"])
        and parsed["receipt"] == floor["receipt"]
    )
    if current:
        out.update(
            state="CURRENT", exit=0,
            message=f"floor {floor['version']} and the receipt word match this library",
            next="keep working",
        )
    elif version_tuple(parsed["version"]) == version_tuple(floor["version"]):
        out.update(
            state="INVALID", exit=2,
            message=f"that receipt word is not on floor {floor['version']}",
            next=f"read {FLOOR_REL} and copy the receipt word from it",
        )
    else:
        out.update(
            state="OUT_OF_DATE", exit=1,
            message=f"floor is now {floor['version']}, read {FLOOR_REL}",
            next="re-read that page and write a fresh line from it",
        )
    _finish_verify(args, out)
    return out["exit"]


def _finish_verify(args, out: dict) -> None:
    if args.json_output:
        print(json.dumps(out, indent=2, sort_keys=True))
        return
    head = {
        "CURRENT": "CURRENT",
        "OUT_OF_DATE": f"OUT OF DATE: {out['message']}",
        "INVALID": f"INVALID: {out['message']}",
    }[out["state"]]
    print(head)
    if out["state"] == "INVALID" and out.get("example"):
        print(f"  example: {out['example']}")
    if out.get("next"):
        print(f"  next: {out['next']}")


# ------------------------------------------------------------- detection

def walk_files(root: Path):
    """Yield files under root, skipping machinery directories."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in WALK_SKIP_DIRS)
        for f in sorted(filenames):
            yield Path(dirpath) / f


def _read_text(path: Path, limit: int = 400_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def detect_repo_kinds(target: Path) -> dict:
    """What is this repo? web UI / API / CLI / agent-facing. No setup file."""
    kinds = {"web": False, "api": False, "cli": False, "agent": (target / "AGENTS.md").is_file()}
    html_files: list[tuple[str, str]] = []
    for f in walk_files(target):
        rel = f.relative_to(target).as_posix()
        suffix = f.suffix.lower()
        if suffix in (".html", ".htm") and len(html_files) < 50:
            html_files.append((rel, _read_text(f)))
        if suffix == ".json" and f.name == "package.json":
            try:
                data = json.loads(_read_text(f))
            except ValueError:
                data = {}
            deps = {**(data.get("dependencies") or {}), **(data.get("devDependencies") or {})}
            if set(deps) & FRONTEND_DEPS:
                kinds["web"] = True
            if data.get("bin"):
                kinds["cli"] = True
        if suffix in SOURCE_EXTS and not kinds["api"]:
            text = _read_text(f)
            if any(rx.search(text) for rx in API_ROUTE_RES):
                kinds["api"] = True
        if suffix in SOURCE_EXTS and not kinds["cli"]:
            text = _read_text(f)
            if re.search(r"^\s*(?:import|from)\s+(?:argparse|click)\b", text, re.MULTILINE):
                kinds["cli"] = True
        if suffix == ".toml" and f.name == "pyproject.toml" and not kinds["cli"]:
            text = _read_text(f)
            if "[project.scripts]" in text or "console_scripts" in text:
                kinds["cli"] = True
    kinds["web"] = kinds["web"] or bool(html_files)
    return {**kinds, "html_files": html_files}


def packs_for(kinds: dict) -> list[str]:
    """Packs that apply to a repo, by detection (decision doc, pack table)."""
    packs = ["everyone", "work"]
    if kinds["web"]:
        packs += ["people", "surfaces", "sites", "access"]
    if kinds["api"]:
        packs += ["surfaces", "integration", "access"]
    if kinds["cli"]:
        packs += ["surfaces"]
    out: list[str] = []
    for p in packs:
        if p not in out:
            out.append(p)
    return out


def detected_words(kinds: dict) -> str:
    labels = [n for k, n in (("web", "web UI"), ("api", "API"), ("cli", "CLI"), ("agent", "agent-facing")) if kinds.get(k)]
    return ", ".join(labels) or "plain code"


# ------------------------------------------------------- html-basics checks

class _PageScan(HTMLParser):
    """Collects form controls, imgs, <html lang> and heading order."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.controls: list[dict] = []
        self.label_fors: set[str] = set()
        self.imgs: list[tuple[int, bool]] = []
        self.headings: list[tuple[int, int]] = []
        self.has_html = False
        self.html_lang: str | None = None
        self._open_labels = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        line = self.getpos()[0]
        if tag == "label":
            self._open_labels += 1
            if a.get("for"):
                self.label_fors.add(a["for"])
            return
        if tag in ("input", "select", "textarea"):
            self.controls.append({
                "tag": tag,
                "id": a.get("id"),
                "line": line,
                "type": (a.get("type") or "").lower(),
                "wrapped": self._open_labels > 0,
                "aria": bool(a.get("aria-label") or a.get("aria-labelledby")),
            })
        elif tag == "img":
            self.imgs.append((line, "alt" in a))
        elif tag == "html":
            self.has_html = True
            self.html_lang = a.get("lang")
        elif re.fullmatch(r"h[1-6]", tag):
            self.headings.append((int(tag[1]), line))

    def handle_endtag(self, tag):
        if tag == "label" and self._open_labels > 0:
            self._open_labels -= 1


def html_basics_problems(label: str, text: str) -> list[str]:
    p = _PageScan()
    try:
        p.feed(text)
        p.close()
    except Exception:
        return [f"{label}:1: page could not be parsed as HTML"]
    problems: list[str] = []
    for c in p.controls:
        if c["type"] == "hidden":
            continue  # hidden inputs are not shown to anyone
        if c["wrapped"] or c["aria"] or (c["id"] and c["id"] in p.label_fors):
            continue
        which = f"{c['tag']} id={c['id']}" if c["id"] else c["tag"]
        problems.append(f"{label}:{c['line']}: <{which}> has no label (use <label for>, wrap it, or aria-label)")
    if p.has_html and not p.html_lang:
        problems.append(f"{label}:1: <html> has no lang attribute")
    for line, has_alt in p.imgs:
        if not has_alt:
            problems.append(f"{label}:{line}: <img> has no alt attribute")
    prev = None
    for level, line in p.headings:
        if prev is not None and level > prev + 1:
            problems.append(f"{label}:{line}: heading skips a level (h{prev} then h{level})")
        prev = level
    return problems


UNSAFE_ASSIGN_RE = re.compile(r"\.innerHTML\s*\+?=")


def unsafe_html_problems(rel: str, text: str) -> list[str]:
    """innerHTML assigned a built string: template interpolation or '+' concat.
    A heuristic for 'set from fetched data' — it warns, and the fix is plain."""
    lines = text.splitlines()
    problems: list[str] = []
    for i, line in enumerate(lines):
        if not UNSAFE_ASSIGN_RE.search(line):
            continue
        rhs = " ".join(lines[i : i + 3]).split("=", 1)[-1] if "=" not in line else \
            " ".join(lines[i : i + 3]).split(".innerHTML", 1)[-1]
        if re.search(r"\$\{", rhs) or re.search(r"[\"'`]\s*\+\s*[A-Za-z_$]|[A-Za-z_$][\w$]*\s*\+\s*[\"'`]", rhs):
            problems.append(f"{rel}:{i + 1}: innerHTML is assigned a built string")
    return problems


# ------------------------------------------------------------ badge (SVG)

BADGE_TEMPLATES = {"plays nice": "badge-current.svg", "behind": "badge-behind.svg", "fix needed": "badge-fix.svg"}


def badge_svg(lib: Path, kind: str, label: str) -> str:
    """Fill an assets/badge template with the real label, in words."""
    text = (lib / BADGE_REL / BADGE_TEMPLATES[kind]).read_text(encoding="utf-8")
    old = re.search(r"<title>Play-Nice: (.*)</title>", text).group(1)
    tw = int(re.search(r'width="(\d+)"', text).group(1))
    width = 44 + 7 * len(label)
    text = re.sub(r"<svg([^>]*?)width=\"\d+\"", rf'<svg\1width="{width}"', text, count=1)
    text = re.sub(r'viewBox="0 0 \d+ 28"', f'viewBox="0 0 {width} 28"', text, count=1)
    text = text.replace(f'width="{tw}"', f'width="{width}"', 1)  # the pill rect
    return text.replace(old, label)


# ------------------------------------------------------------- summary

def summarize(checks: list[dict], recorded: str | None, current: str) -> dict:
    """plays nice | behind | fix needed (behind wins over a stale-only block)."""
    needs = [c for c in checks if c["state"] == "needs_fix"]
    behind = bool(recorded) and version_tuple(current) > version_tuple(recorded)
    only_stale_block = (
        behind and needs and all(c["id"] == "agents-file" for c in needs)
    )
    if needs and not only_stale_block:
        return {"state": "fix needed", "kind": "fix needed", "behind": behind,
                "label": "fix needed", "exit": 1}
    if behind:
        return {"state": "behind", "kind": "behind", "behind": True,
                "label": f"behind · v{current} is out", "exit": 1}
    return {"state": "plays nice", "kind": "plays nice", "behind": behind,
            "label": f"plays nice · v{current}", "exit": 0}


def _check_item(cid, name, state, words, fix=None) -> dict:
    return {"id": cid, "name": name, "state": state, "words": words, "fix": fix}


def recorded_floor(target: Path) -> str | None:
    ag = target / "AGENTS.md"
    if not ag.is_file():
        return None
    text = _read_text(ag)
    m = re.search(
        re.escape(MARK_START) + r"(.*?)" + re.escape(MARK_END), text, re.DOTALL
    )
    if not m:
        return None
    v = re.search(r"Play-Nice \(floor ([0-9][0-9.]*)\)", m.group(1))
    return v.group(1) if v else None


def check_agents_file(target: Path, floor: dict) -> dict:
    name = "AGENTS.md Play-Nice block"
    ag = target / "AGENTS.md"
    if not ag.is_file():
        return _check_item("agents-file", name, "needs_fix",
                           "no AGENTS.md in this folder", "playnice start")
    if MARK_START not in _read_text(ag):
        return _check_item("agents-file", name, "needs_fix",
                           "AGENTS.md has no play-nice block", "playnice start")
    rec = recorded_floor(target)
    if rec is None:
        return _check_item("agents-file", name, "needs_fix",
                           "the play-nice block records no floor version", "playnice start")
    if version_tuple(rec) == version_tuple(floor["version"]):
        return _check_item("agents-file", name, "worked",
                           f"block present and current (floor {rec})")
    return _check_item("agents-file", name, "needs_fix",
                       f"block records floor {rec}; the floor is now {floor['version']}",
                       "playnice start")


def check_html_basics(target: Path, kinds: dict) -> dict:
    name = "HTML basics (labels, lang, alt, headings)"
    if not kinds["web"]:
        return _check_item("html-basics", name, "skipped", "no web UI detected")
    problems: list[str] = []
    for rel, text in kinds["html_files"]:
        problems.extend(html_basics_problems(rel, text))
    if not problems:
        return _check_item("html-basics", name, "worked",
                           f"{len(kinds['html_files'])} page(s) checked: every control labeled, "
                           "<html lang> set, every <img> has alt, headings in order")
    shown = "; ".join(problems[:8])
    more = f" (+{len(problems) - 8} more)" if len(problems) > 8 else ""
    return _check_item("html-basics", name, "needs_fix", f"{len(problems)} problem(s): {shown}{more}",
                       "add the missing label/alt/lang; keep heading levels in order")


def check_unsafe_html(target: Path, kinds: dict) -> dict:
    name = "No innerHTML built from fetched data"
    if not kinds["web"]:
        return _check_item("unsafe-html", name, "skipped", "no web UI detected")
    problems: list[str] = []
    for f in walk_files(target):
        if f.suffix.lower() not in SCRIPT_EXTS:
            continue
        problems.extend(unsafe_html_problems(f.relative_to(target).as_posix(), _read_text(f)))
    if not problems:
        return _check_item("unsafe-html", name, "worked", "no innerHTML built from fetched data")
    shown = "; ".join(problems[:8])
    more = f" (+{len(problems) - 8} more)" if len(problems) > 8 else ""
    return _check_item("unsafe-html", name, "needs_fix",
                       f"{len(problems)} spot(s): {shown}{more}", "use textContent or escape")


def check_secrets(cc, target: Path) -> dict:
    name = "No secrets in the repo"
    try:
        hits = cc.scan_surface(target)
    except OSError as e:
        return _check_item("secrets", name, "skipped", f"scan could not run: {e}")
    if not hits:
        return _check_item("secrets", name, "worked",
                           "no banned public-boundary shapes found (values redacted scan)")
    shown = "; ".join(f"{h['path']}: {h['pattern']}" for h in hits[:8])
    more = f" (+{len(hits) - 8} more)" if len(hits) > 8 else ""
    return _check_item("secrets", name, "needs_fix", f"{len(hits)} finding(s): {shown}{more}",
                       "remove the values; names and where they are stored are fine (floor rule 11)")


def _self_pin_relation(lib: Path, pin: str) -> tuple[str, str | None]:
    """(words, problem) for a self-adoption pin: it must be in HEAD's history."""
    if not pin:
        return "", "self-adoption manifest pins no revision"
    exists = git0(lib, "cat-file", "-e", f"{pin}^{{commit}}")
    if exists.returncode != 0:
        shallow = git0(lib, "rev-parse", "--is-shallow-repository").stdout.strip() == "true"
        if shallow:
            return "", (f"cannot prove pin {pin[:12]} is in this history: the clone is "
                        "shallow (fetch full history)")
        return "", (f"pin {pin[:12]} is not a commit in this repository "
                    "(a squash-merged branch commit?)")
    anc = git0(lib, "merge-base", "--is-ancestor", pin, "HEAD")
    if anc.returncode != 0:
        return "", f"pin {pin[:12]} is not in the history of this checkout"
    ahead = git0(lib, "rev-list", "--count", f"{pin}..HEAD").stdout.strip() or "?"
    return (f"self-adoption: pin {pin[:12]} is in this checkout's history "
            f"({ahead} commit(s) since)"), None


def check_adoption(cc, target: Path, lib: Path, index: dict) -> dict:
    name = "Adoption manifest"
    mf = target / ".contracts" / "adoption.yaml"
    if not mf.is_file():
        return _check_item("adoption", name, "skipped", "no .contracts/adoption.yaml")
    try:
        manifest = cc.load_adoption(mf)
    except cc.CTError as e:
        return _check_item("adoption", name, "needs_fix", f"manifest invalid: {e}",
                           "fix .contracts/adoption.yaml (contractctl adopt shows the rules)")
    refs = list(manifest.get("always") or [])
    for cids in (manifest.get("triggers") or {}).values():
        refs += list(cids or [])
    problems: list[str] = []
    suggestions: list[str] = []
    for raw in refs:
        cid = canonical_read_id(str(raw), index)
        if cid is None:
            problems.append(f"'{raw}' is not a library contract and has no alias")
        elif str(raw) != cid:
            if index["ids"].get(cid) == "retired":
                problems.append(f"'{raw}' maps to retired '{cid}' — drop it or name a live one")
            else:
                suggestions.append(f"'{raw}' now lives as '{cid}'")
    pin = str((manifest.get("source") or {}).get("revision") or "")
    head = git0(lib, "rev-parse", "HEAD")
    head_rev = head.stdout.strip() if head.returncode == 0 else ""
    claim = cc.self_adoption_claim(manifest, mf, lib)
    is_library = target.resolve() == lib.resolve()
    pin_words = "pin matches this library checkout"
    fix = "update the ids and re-pin the revision (contractctl sync)"
    if claim is not None and claim != "ok":
        problems.append(claim)
        fix = "drop source.self from this manifest"
    elif claim == "ok":
        # Self-adoption: a commit cannot carry its own SHA, so the pin must be
        # in this checkout's history rather than equal to HEAD.
        pin_words, problem = _self_pin_relation(lib, pin)
        if problem:
            problems.append(problem)
            fix = "pin a commit that is already on main"
    elif head_rev and pin and pin != head_rev:
        msg = f"pin {pin[:12]} is not the current library revision {head_rev[:12]}"
        if is_library:
            msg += " (this is the library itself: set source.self: true to check by ancestry)"
        problems.append(msg)
    if problems:
        return _check_item("adoption", name, "needs_fix", "; ".join(problems), fix)
    words = f"all manifest ids resolve; {pin_words}"
    if suggestions:
        words += " — retired ids: " + "; ".join(sorted(set(suggestions)))
    return _check_item("adoption", name, "worked", words)


# ------------------------------------------------------------- check: repo

def run_repo_check(target: Path, badge: str | None) -> dict:
    """All facts for `playnice check PATH`; writes the badge when asked."""
    try:
        if not target.is_dir():
            raise CheckUnavailable(f"{target} is not a folder")
        lib = v2_library_root(target)
        floor = load_v2_floor(lib)
        index = load_v2_index(lib)
        cc = import_contractctl(lib)
    except (CheckUnavailable, PlayNiceError) as e:
        hint = (
            "point playnice check at an existing folder, or a https:// URL"
            if str(e).endswith("is not a folder")
            else "set PLAY_NICE_LIBRARY to a play-nice-contracts checkout"
        )
        return {"mode": "repo", "target": str(target), "state": "unknown",
                "exit": 2, "error": str(e), "next": hint}
    kinds = detect_repo_kinds(target)
    checks = [
        check_agents_file(target, floor),
        check_html_basics(target, kinds),
        check_unsafe_html(target, kinds),
        check_secrets(cc, target),
        check_adoption(cc, target, lib, index),
    ]
    rec = recorded_floor(target)
    summary = summarize(checks, rec, floor["version"])
    result = {
        "mode": "repo", "target": str(target),
        "detected": {k: bool(kinds.get(k)) for k in ("web", "api", "cli", "agent")},
        "floor": {"current": floor["version"], "recorded": rec},
        "checks": checks, "exit": summary["exit"], **{k: summary[k] for k in ("state", "behind", "label")},
    }
    if badge and summary["state"] != "unknown":
        bpath = Path(badge)
        try:
            bpath.parent.mkdir(parents=True, exist_ok=True)
            bpath.write_text(badge_svg(lib, summary["kind"], summary["label"]), encoding="utf-8")
            result["badge"] = str(bpath)
        except OSError as e:
            result["badge_error"] = str(e)
    result["next"] = {
        "plays nice": "nothing to do — re-run `playnice check` in CI to redraw the badge",
        "behind": "playnice start",
        "fix needed": "fix the items above, then run playnice check again",
    }[summary["state"]]
    return result


# ------------------------------------------------------------- check: URL

def _fetch(url: str, timeout: int = 10) -> tuple[int, bytes]:
    """One attempt, 10 s timeout, no retries. Net failure -> CheckUnavailable."""
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "playnice/2.0 check"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read(5_000_000)
    except urllib.error.HTTPError as e:
        return e.code, b""
    except (urllib.error.URLError, OSError) as e:
        raise CheckUnavailable(f"network error for {url}: {e}")


def validate_site_claim(data) -> list[str]:
    """schema/play-nice-site.schema.json checked by hand (stdlib only)."""
    if not isinstance(data, dict):
        return ["the file must be a JSON object"]
    errors: list[str] = []
    missing = [k for k in ("version", "packs", "contact", "expires") if k not in data]
    if missing:
        errors.append("missing required field(s): " + ", ".join(missing))
    extra = sorted(set(data) - {"version", "packs", "contact", "expires", "agent_card"})
    if extra:
        errors.append("unknown field(s): " + ", ".join(extra))
    if "version" in data and not (isinstance(data["version"], str) and SEMVER_RE.fullmatch(data["version"])):
        errors.append("version must be a semantic version like 1.0.0")
    packs = data.get("packs")
    if "packs" in data:
        if not isinstance(packs, list) or not packs:
            errors.append("packs must be a non-empty list of pack ids")
        else:
            bad = [p for p in packs if not (isinstance(p, str) and WORD_RE.fullmatch(p) and len(p) <= 48)]
            if bad:
                errors.append("pack ids must be lowercase like 'sites': " + ", ".join(map(str, bad)))
            if len(set(packs)) != len(packs):
                errors.append("packs must not repeat an id")
    if "contact" in data and not (isinstance(data["contact"], str) and CONTACT_RE.match(data["contact"])):
        errors.append("contact must be a mailto:, http(s): or tel: URI")
    if "expires" in data:
        exp = data["expires"]
        if not (isinstance(exp, str) and DATE_RE.fullmatch(exp)):
            errors.append("expires must be a UTC date like 2027-03-01")
        else:
            try:
                if date.fromisoformat(exp) < date.today():
                    errors.append(f"the claim expired on {exp} — a stale claim is not a claim")
            except ValueError:
                errors.append(f"expires is not a real date: {exp}")
    if "agent_card" in data and not (isinstance(data["agent_card"], str) and data["agent_card"].startswith("https://")):
        errors.append("agent_card must be an https:// URL")
    return errors


def run_url_check(url: str, badge: str | None) -> dict:
    """`playnice check https://site`: the well-known claim, the page, /llms.txt."""
    base = url.rstrip("/")
    try:
        lib = v2_library_root(Path.cwd())
        floor = load_v2_floor(lib)
    except CheckUnavailable as e:
        return {"mode": "url", "target": url, "state": "unknown", "exit": 2,
                "error": str(e), "next": "set PLAY_NICE_LIBRARY to a play-nice-contracts checkout"}
    checks: list[dict] = []
    site_version: str | None = None
    name = "Play-Nice site file"
    try:
        code, body = _fetch(base + "/.well-known/play-nice.json")
    except CheckUnavailable as e:
        return {"mode": "url", "target": url, "state": "unknown", "exit": 2,
                "error": str(e), "next": "check the address or try again later"}
    if code == 404:
        checks.append(_check_item("site-file", name, "needs_fix",
                                  "no /.well-known/play-nice.json — the site makes no Play-Nice claim",
                                  "publish version, packs, contact and expires (schema/play-nice-site.schema.json)"))
    elif code != 200:
        return {"mode": "url", "target": url, "state": "unknown", "exit": 2,
                "error": f"HTTP {code} for /.well-known/play-nice.json",
                "next": "check the address or try again later"}
    else:
        try:
            data = json.loads(body.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            data = None
            problems = ["the file is not valid JSON"]
        else:
            problems = validate_site_claim(data)
        if problems:
            checks.append(_check_item("site-file", name, "needs_fix",
                                      "; ".join(problems),
                                      "fix /.well-known/play-nice.json to match schema/play-nice-site.schema.json"))
        else:
            site_version = str(data["version"])
            checks.append(_check_item(
                "site-file", name, "worked",
                f"version {site_version}, packs {', '.join(data['packs'])}, "
                f"contact {data['contact']}, expires {data['expires']}"))
    # the delivered page: same html-basics as a repo
    try:
        code, body = _fetch(base + "/")
    except CheckUnavailable as e:
        return {"mode": "url", "target": url, "state": "unknown", "exit": 2,
                "error": str(e), "next": "check the address or try again later"}
    if code != 200:
        checks.append(_check_item("html-basics", "HTML basics (labels, lang, alt, headings)",
                                  "needs_fix", f"site root answered HTTP {code}",
                                  "make https://... serve the page"))
    else:
        problems = html_basics_problems(base + "/", body.decode("utf-8", errors="replace"))
        if problems:
            checks.append(_check_item("html-basics", "HTML basics (labels, lang, alt, headings)",
                                      "needs_fix",
                                      f"{len(problems)} problem(s): " + "; ".join(problems[:8]),
                                      "add the missing label/alt/lang; keep heading levels in order"))
        else:
            checks.append(_check_item("html-basics", "HTML basics (labels, lang, alt, headings)",
                                      "worked", "the delivered page passes html-basics"))
    # /llms.txt: a SHOULD — skipped with a note when absent
    try:
        code, _ = _fetch(base + "/llms.txt")
    except CheckUnavailable:
        checks.append(_check_item("llms-txt", "/llms.txt", "skipped", "could not be reached"))
    else:
        if code == 200:
            checks.append(_check_item("llms-txt", "/llms.txt", "worked", "published"))
        elif code == 404:
            checks.append(_check_item("llms-txt", "/llms.txt", "skipped",
                                      "not published (the sites pack recommends it)"))
        else:
            checks.append(_check_item("llms-txt", "/llms.txt", "skipped", f"HTTP {code}"))
    summary = summarize(checks, site_version, floor["version"])
    result = {
        "mode": "url", "target": base,
        "floor": {"current": floor["version"], "recorded": site_version},
        "checks": checks,
        "exit": summary["exit"],
        **{k: summary[k] for k in ("state", "behind", "label")},
    }
    if badge and result["state"] != "unknown":
        bpath = Path(badge)
        try:
            bpath.parent.mkdir(parents=True, exist_ok=True)
            bpath.write_text(badge_svg(lib, summary["kind"], summary["label"]), encoding="utf-8")
            result["badge"] = str(bpath)
        except OSError as e:
            result["badge_error"] = str(e)
    result["next"] = {
        "plays nice": "nothing to do — refresh the claim before it expires",
        "behind": f"update the site's version (floor {floor['version']} is current) and re-run the check",
        "fix needed": "fix the items above, then run playnice check again",
    }[result["state"]]
    return result


def cmd_check(args) -> int:
    target = args.target
    if re.match(r"https?://", target):
        result = run_url_check(target, args.badge)
    else:
        result = run_repo_check(Path(target).expanduser().resolve(), args.badge)
    if args.json_output:
        print(json.dumps(result, indent=2, sort_keys=True))
        return result["exit"]
    what = result["target"]
    if result["mode"] == "repo" and result.get("detected"):
        what += f" — detected: {detected_words(result['detected'])}"
    print(f"CHECK: {what}")
    if result["state"] == "unknown":
        print(f"  could not check: {result.get('error', 'unknown')}")
        print(f"  next: {result.get('next', '')}")
        return result["exit"]
    for c in result["checks"]:
        print(f"  {c['state']:9s} {c['name']}: {c['words']}")
        if c["state"] == "needs_fix" and c.get("fix"):
            print(f"            fix: {c['fix']}")
    print(f"STATE: {result['label']}")
    if result.get("badge"):
        print(f"badge: wrote {result['badge']}")
    if result.get("badge_error"):
        print(f"badge: could not write — {result['badge_error']}")
    print(f"NEXT: {result['next']}")
    return result["exit"]


# ------------------------------------------------------------- start

def build_start_block(floor: dict, packs: list[str]) -> str:
    lines = [
        MARK_START,
        "<!-- written by `playnice start` — refresh with the same command, not by hand -->",
        f"This project follows Play-Nice (floor {floor['version']}).",
        "",
        floor["rules"],
        "",
        "Packs that apply to this repo:",
    ]
    for p in packs:
        lines.append(f"- {PACK_TITLES.get(p, p)} — {LIBRARY_URL}/tree/main/contracts/{p}")
    lines += [
        "",
        f"Start each handoff with: Play-Nice floor {floor['version']} · receipt {floor['receipt']}",
        MARK_END,
    ]
    return "\n".join(lines)


def apply_start_block(text: str, block: str) -> str:
    """Replace the marked block in place; append it when there is none."""
    pattern = re.escape(MARK_START) + r".*?" + re.escape(MARK_END)
    if re.search(pattern, text, re.DOTALL):
        return re.sub(pattern, lambda _m: block, text, count=1, flags=re.DOTALL)
    return text.rstrip("\n") + "\n\n" + block + "\n"


WORKFLOW_YML = """# written by `playnice start` — the Play-Nice check on every push and PR.
#
# Path assumption: the library is checked out to .play-nice-library below, so
# the tool lives at .play-nice-library/tools/playnice/playnice.py. If you
# vendor the tools elsewhere, change the run line to match.
name: play-nice
on:
  push:
  pull_request:
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with:
          repository: rylee-bee-labs/play-nice-contracts
          path: .play-nice-library
      - run: python3 .play-nice-library/tools/playnice/playnice.py check --badge playnice-badge.svg
"""


def cmd_start(args) -> int:
    target = Path(args.path).expanduser().resolve()
    try:
        if not target.is_dir():
            raise CheckUnavailable(f"{target} is not a folder")
        lib = v2_library_root(target)
        floor = load_v2_floor(lib)
    except CheckUnavailable as e:
        if args.json_output:
            print(json.dumps({"command": "start", "path": str(target), "state": "error",
                              "exit": 2, "error": str(e)}, indent=2, sort_keys=True))
        else:
            print(f"error: {e}\n  next: set PLAY_NICE_LIBRARY to a play-nice-contracts checkout")
        return 2
    kinds = detect_repo_kinds(target)
    packs = packs_for(kinds)
    block = build_start_block(floor, packs)
    ag = target / "AGENTS.md"
    readme = target / "README.md"
    badge = target / "playnice-badge.svg"
    workflow = target / ".github" / "workflows" / "playnice.yml"
    has_readme = readme.is_file()
    readme_needs = has_readme and "playnice-badge.svg" not in _read_text(readme)
    has_github = (target / ".github").is_dir()

    if args.dry_run:
        plan = {
            "command": "start", "dry_run": True, "path": str(target),
            "detected": {k: bool(kinds.get(k)) for k in ("web", "api", "cli", "agent")},
            "floor_version": floor["version"], "packs": packs,
            "plan": [
                ("create " if not ag.is_file() else "update ") + "AGENTS.md play-nice block",
                ("add badge line to README.md" if readme_needs else
                 ("README.md already has the badge" if has_readme else "no README.md — skipped")),
                "run check and write playnice-badge.svg",
                ("write .github/workflows/playnice.yml" if has_github
                 else "no .github/ — no workflow written"),
            ],
            "exit": 0,
        }
        if args.json_output:
            print(json.dumps(plan, indent=2, sort_keys=True))
            return 0
        print(f"PLAN (nothing written): {target} — detected: {detected_words(kinds)}")
        for item in plan["plan"]:
            print(f"  - {item}")
        print("next: run playnice start again without --dry-run")
        return 0

    actions: list[str] = []
    if ag.is_file():
        ag.write_text(apply_start_block(_read_text(ag), block), encoding="utf-8")
        actions.append("updated the play-nice block in AGENTS.md")
    else:
        ag.write_text(block + "\n", encoding="utf-8")
        actions.append("created AGENTS.md with the play-nice block")
    if readme_needs:
        text = _read_text(readme)
        lines = text.splitlines()
        at = next((i for i, ln in enumerate(lines) if ln.startswith("# ")), None)
        insert = at + 1 if at is not None else 0
        snippet = ["", f"[![Play-Nice](playnice-badge.svg)]({_badge_link(target, has_github)})"]
        lines[insert:insert] = snippet
        readme.write_text("\n".join(lines) + "\n", encoding="utf-8")
        actions.append("added the badge line to README.md")
    elif has_readme:
        actions.append("README.md already had the badge line")
    result = run_repo_check(target, str(badge))
    if result.get("badge"):
        actions.append(f"wrote {badge.name} ({result['label']})")
    if has_github:
        workflow.parent.mkdir(parents=True, exist_ok=True)
        workflow.write_text(WORKFLOW_YML, encoding="utf-8")
        actions.append("wrote .github/workflows/playnice.yml")
    else:
        actions.append("no .github/ — skipped the workflow")

    nxt = ("CI will redraw the badge on every push" if has_github
           else "playnice check")
    if args.json_output:
        print(json.dumps({
            "command": "start", "path": str(target), "dry_run": False,
            "floor_version": floor["version"], "packs": packs,
            "detected": {k: bool(kinds.get(k)) for k in ("web", "api", "cli", "agent")},
            "actions": actions, "check_state": result["state"], "badge": result.get("badge"),
            "exit": 0, "next": nxt,
        }, indent=2, sort_keys=True))
        return 0
    print("did:")
    for item in actions:
        print(f"  - {item}")
    print(f"next: {nxt}")
    return 0


def _badge_link(target: Path, has_workflow: bool) -> str:
    """Where the README badge points: the check run that draws it, when start
    writes that workflow and the repo has a GitHub origin; otherwise the
    library, because there is no check run to link to yet."""
    origin = repo_identity(target) if (has_workflow and is_git_repo(target)) else None
    if origin:
        return f"https://github.com/{origin}/actions/workflows/playnice.yml"
    return LIBRARY_URL


def _version_line() -> str:
    """playnice's own version plus the library and floor it is running with."""
    try:
        lib = v2_library_root(Path.cwd())
        return import_contractctl(lib).version_line("playnice", PLAYNICE_VERSION)
    except Exception:
        return f"playnice {PLAYNICE_VERSION} · library unknown · floor unknown"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="playnice",
        description="Play-Nice from one command. Most people need start, check, "
        "verify, rules and status. work and reconcile run agent work end to end "
        "for orchestrators. contractctl is the lower-level engine underneath.",
    )
    ap.add_argument(
        "--version", action="version", version=_version_line()
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser(
        "verify",
        help="is a receipt line current for the library today? (exit 0/1/2)",
        description='Check one "Play-Nice floor <version> · receipt <word>'
        '[ · read <id>, <id>]" line against the library.',
    )
    p.add_argument("line", help='the receipt line, in quotes')
    p.add_argument("--json", action="store_true", dest="json_output")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser(
        "check",
        help="check a repo (PATH) or a site (URL); optional --badge FILE (exit 0/1/2)",
        description="Works with no setup file: detects what the repo is, runs the "
        "checkable rules, and says plays nice, behind, or fix needed.",
    )
    p.add_argument("target", nargs="?", default=".", help="repo path or https:// URL (default: .)")
    p.add_argument("--badge", default=None, metavar="FILE", help="write the bee badge SVG here")
    p.add_argument("--json", action="store_true", dest="json_output")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser(
        "start",
        help="set a repo up for Play-Nice — zero questions (exit 0/2)",
        description="Writes the play-nice block into AGENTS.md (floor rules verbatim, "
        "pack links for what this repo is), the badge line into README.md, the badge "
        "itself, and a CI workflow when .github/ exists.",
    )
    p.add_argument("path", nargs="?", default=".", help="repo path (default: .)")
    p.add_argument("--dry-run", action="store_true", help="print the plan; write nothing")
    p.add_argument("--json", action="store_true", dest="json_output")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser(
        "rules",
        help="which contracts apply to a task, and why (exit 0/1)",
        description="Resolves the contracts for a task from this repo's adoption "
        "manifest, or from the library defaults when there is none. The same "
        "resolver `playnice work` and `contractctl resolve` use.",
    )
    p.add_argument("task", help='the work, in plain words, e.g. "add a settings page"')
    p.add_argument("--repo", default=".", help="repo whose manifest to use (default: .)")
    p.add_argument("--tag", action="append", default=[], help="explicit surface tag (repeatable)")
    p.add_argument("--json", action="store_true", dest="json_output")
    p.set_defaults(func=cmd_rules)

    p = sub.add_parser(
        "status",
        help="read-only: repository checks, contract adoption, and work readiness",
    )
    p.add_argument("--repo", default=".")
    p.add_argument("--config", default=None)
    p.add_argument("--manifest", default=None)
    p.add_argument("--no-github", action="store_true")
    p.add_argument("--json", action="store_true", dest="json_output")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("work", help="orchestrators: run the full agent lifecycle for a task")
    p.add_argument(
        "task", nargs="?", help='the work to do, e.g. "fix the settings page"'
    )
    p.add_argument(
        "--repo", default=".", help="target repository (default: current directory)"
    )
    p.add_argument("--config", default=None, help="path to the global play-nice config")
    p.add_argument("--manifest", default=None, help="path to the adoption manifest")
    p.add_argument(
        "--agent", default=None, help="override agent command (e.g. codex, kilo, aider)"
    )
    p.add_argument(
        "--no-launch",
        action="store_true",
        help="preflight + permit only; do not launch the agent",
    )
    p.add_argument(
        "--no-github",
        action="store_true",
        help="disable GitHub inspection and mutations",
    )
    p.add_argument("--json", action="store_true", dest="json_output")
    p.set_defaults(func=cmd_work)

    p = sub.add_parser(
        "reconcile",
        help="orchestrators: carryover + auto-finish (mutations need an ACTIVE permit)",
    )
    p.add_argument("--repo", default=".")
    p.add_argument("--config", default=None)
    p.add_argument("--manifest", default=None)
    p.add_argument("--no-github", action="store_true")
    p.add_argument("--json", action="store_true", dest="json_output")
    p.set_defaults(func=cmd_reconcile)
    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if not (sys.argv[1:] if argv is None else argv):
        parser.print_help(sys.stderr)
        print("\nstart here: playnice start (set a repo up) or playnice check .",
              file=sys.stderr)
        return 2
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except ConfigError as e:
        print(f"playnice: config error: {e}", file=sys.stderr)
        return 2
    except PlayNiceError as e:
        print(f"playnice: {e}", file=sys.stderr)
        return 2
    except CheckUnavailable as e:
        print(f"could not check: {e}", file=sys.stderr)
        return 2
    except subprocess.TimeoutExpired as e:
        print(f"playnice: timeout: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
