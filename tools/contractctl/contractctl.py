#!/usr/bin/env python3
"""contractctl — resolve, validate, lock, and attest play-nice contracts.

Minimal-dependency (stdlib-only) CLI for the play-nice-contracts library.

Subcommands:
  list                  list contracts (id, version, status, layer)
  show <id>             print a contract's canonical content
  validate              validate the whole library (schemas, receipts, index)
  resolve               resolve the applicable contract set for a task
                        (works without an adoption manifest: floor + role
                        base set + library-trigger matches)
  lock                  generate contracts.lock.json (deterministic)
  diff                  compare the contract set between two library revisions
  scan                  scan a tree for banned public-boundary shapes
  index                 report or repair CONTRACT_INDEX.md columns
  init-adoption         write a starter adoption manifest
  upgrade-check         am I current, what changed, what do I run next?
  attest                produce a CONTRACT_ATTESTATION v1 block
  verify-attestation    re-verify an attestation against the library
  commit                activate the CONTRACT OPERATIONAL COMMITMENT artifact
  session-status        ACTIVE / STALE / INACTIVE for a commitment
  adopt                 validate a project adoption manifest
  init-project          scaffold a .project/ context folder
  project               .project/ subcommands (validate)
  participant           participant-pack subcommands (list, validate)
  validate-question     validate a question / help-request artifact
  onboard               guided reading plan for a role
  status                library health summary (not this project's state)
  freshness             verify the authoritative remote revision (fail closed)
  sync                  refresh the adoption pin to the remote revision

Run with --help or <subcommand> --help for details.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = REPO_ROOT / "contracts"
SCHEMA_DIR = REPO_ROOT / "schema"
LOCKFILE = REPO_ROOT / "contracts.lock.json"
INDEX_FILE = REPO_ROOT / "CONTRACT_INDEX.md"
VERSION_FILE = REPO_ROOT / "VERSION"
QUESTION_SCHEMA = SCHEMA_DIR / "question.schema.json"

FM_DELIM = "---"
FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
RECEIPT_RE = re.compile(r"<!--\s*contract-receipt:\s*([a-z]+(?:-[a-z]+){2})\s*-->")
CONTRACT_ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")
GITSHA_RE = re.compile(r"^[a-f0-9]{7,64}$")
# v2 packs: the layer is the pack, and the directory is named after it.
LAYER_DIRS = {
    "everyone": "everyone",
    "work": "work",
    "people": "people",
    "surfaces": "surfaces",
    "sites": "sites",
    "integration": "integration",
    "access": "access",
}

ALIASES_FILE = REPO_ROOT / "aliases.json"


def load_aliases() -> dict[str, str]:
    """Old (v1) contract ids -> the v2 contract that holds their rules."""
    try:
        return dict(json.loads(ALIASES_FILE.read_text()).get("aliases", {}))
    except (OSError, ValueError):
        return {}


def canonical_id(cid: str, lib_ids) -> str:
    """Map an old id to its v2 id; unknown ids come back unchanged."""
    if cid in lib_ids:
        return cid
    return load_aliases().get(cid, cid)
VALID_STATUS = {"canonical", "draft", "deprecated", "retired"}
ATTEST_STATUSES = {"ACCEPTED", "CONFLICT", "N/A"}

ATTESTATION_FORMAT = "CONTRACT_ATTESTATION v1"


class CTError(Exception):
    """A contractctl failure with a stable message."""


class CTManifestMissing(CTError):
    """No adoption manifest at the expected path: the folder has not adopted yet.

    Carries the path so callers can print the fix-forward step in plain words.
    """

    def __init__(self, path):
        self.path = Path(path)
        super().__init__(
            f"no adoption manifest at {path} — this folder has not adopted Play-Nice yet."
        )


def _suggested_project_name() -> str:
    """A clean --project suggestion derived from the current directory name."""
    name = re.sub(r"[^a-z0-9-]+", "-", Path.cwd().name.lower()).strip("-")
    return name or "my-project"


def print_missing_manifest_hint(err: CTManifestMissing, *, stream=None) -> None:
    """Plain next step after a missing-manifest error, on the given stream."""
    stream = stream or sys.stderr
    print(f"  next: contractctl init-adoption --project {_suggested_project_name()}", file=stream)


# ---------------------------------------------------------------- yaml subset
# Minimal YAML front-matter parser for the shapes this library actually uses.
# Supports: nested maps, lists of scalars, one level of list-of-maps, scalars,
# and empty flow collections (`{}` -> {}, `[]` -> []).


def _parse_scalar(s: str):
    s = s.strip()
    # strip trailing YAML comments (unquoted ' #' to end of line)
    if " #" in s and not s.startswith('"'):
        s = s.split(" #", 1)[0].strip()
    if s in ("null", "~", ""):
        return None
    if s == "none":
        return "none"  # keep the literal; conflicts: none is meaningful
    if s.lower() in ("true", "false"):
        return s.lower() == "true"
    if s.startswith("{") and s.endswith("}") and not s[1:-1].strip():
        return {}  # empty flow mapping, not the string "{}"
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_parse_scalar(p.strip()) for p in inner.split(",")]
    if s.startswith('"') and s.endswith('"') and len(s) >= 2:
        return s[1:-1]
    return s


def _yaml_block_to_dict(lines: list[str], indent_stack=None) -> dict:
    """Parse a small YAML subset: mapping keys, nested via indentation."""
    out: dict = {}
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if not line.strip() or line.strip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\s*)([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            raise CTError(f"yaml: cannot parse line: {line!r}")
        indent, key, rest = m.group(1), m.group(2), m.group(3).strip()
        if rest in (">-", ">", "|-", "|", ">"):
            # folded/literal block scalar: consume deeper-indented lines
            child_indent = len(indent)
            block: list[str] = []
            j = i + 1
            while j < n:
                nxt = lines[j]
                if nxt.strip() == "":
                    block.append(nxt)
                    j += 1
                    continue
                nxt_indent = len(nxt) - len(nxt.lstrip())
                if nxt_indent <= child_indent:
                    break
                block.append(nxt.strip())
                j += 1
            joined = " ".join(block).strip()
            out[key] = " ".join(joined.split())
            i = j
            continue
        if rest:
            out[key] = _parse_scalar(rest)
            i += 1
            continue
        # child block: collect lines deeper than this key's indent
        child_indent = len(indent)
        block: list[str] = []
        j = i + 1
        while j < n:
            nxt = lines[j]
            if nxt.strip() == "":
                block.append(nxt)
                j += 1
                continue
            nxt_indent = len(nxt) - len(nxt.lstrip())
            if nxt_indent <= child_indent:
                break
            block.append(nxt)
            j += 1
        # list or map child? A block is a list only if its first
        # non-empty line is a dash item; otherwise it is a map whose
        # values may themselves be lists (map-of-lists).
        first = next(
            (b for b in block if b.strip() and not b.lstrip().startswith("#")), ""
        )
        if re.match(r"^\s*-\s", first):
            out[key] = _yaml_list(block)
        else:
            out[key] = _yaml_block_to_dict(block)
        i = j
    return out


def _yaml_list(block: list[str]):
    """Parse a list whose items are '- scalar' or '- key: val' map items,
    including nested lists/maps inside those items (indentation-based)."""
    items: list = []
    i = 0
    n = len(block)
    while i < n:
        line = block[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = re.match(r"^(\s*)-\s+(.*)$", line)
        if not m:
            raise CTError(f"yaml: cannot parse list line: {line!r}")
        dash_indent, rest = len(m.group(1)), m.group(2)
        kv = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", rest)
        if not kv:
            items.append(_parse_scalar(rest))
            i += 1
            continue
        # map item: collect this item's lines (deeper than the dash, or
        # continuation keys at the item's key indent) until the next dash item
        item_indent = dash_indent + 2
        item_lines = [rest]
        j = i + 1
        while j < n:
            nxt = block[j]
            if nxt.strip() == "":
                j += 1
                continue
            nxt_indent = len(nxt) - len(nxt.lstrip())
            if nxt_indent <= dash_indent and re.match(r"^\s*-\s", nxt):
                break
            if nxt_indent < item_indent:
                break
            item_lines.append(nxt)
            j += 1
        # parse the item as a mini-document starting at the key
        items.append(
            _yaml_block_to_dict(
                [" " * item_indent + l if k else l for k, l in enumerate(item_lines)]
            )
        )
        i = j
    return items


def parse_front_matter(text: str) -> dict:
    m = FM_RE.match(text)
    if not m:
        raise CTError("front matter: missing '---' delimited YAML header")
    lines = m.group(1).split("\n")
    data = _yaml_block_to_dict(lines)
    # 'applies'/'triggers' etc. may be inline lists from _parse_scalar already
    return data


# ---------------------------------------------------------------- discovery


def find_contract_files() -> list[Path]:
    files = []
    for layer, dirname in LAYER_DIRS.items():
        d = CONTRACTS_DIR / dirname
        if d.is_dir():
            files.extend(d.glob("*.md"))
    return sorted(files)


def parse_contract_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        fm = parse_front_matter(text)
    except CTError as e:
        raise CTError(f"{path.relative_to(REPO_ROOT)}: {e}")
    receipts = RECEIPT_RE.findall(text)
    return {
        "path": path,
        "rel_path": path.relative_to(REPO_ROOT).as_posix(),
        "front_matter": fm,
        "receipts": receipts,  # all receipt comments in the file
        "text": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def load_library() -> list[dict]:
    out = []
    for f in find_contract_files():
        out.append(parse_contract_file(f))
    return out


# ---------------------------------------------------------------- validation


def validate_library(lib: list[dict] | None = None) -> list[str]:
    errors: list[str] = []
    if lib is None:
        lib = load_library()
    if not lib:
        return ["library: no contracts found under contracts/"]

    seen_ids: dict[str, str] = {}
    seen_receipts: dict[str, str] = {}
    fm_contract_schema = _load_json_schema("contract.schema.json")

    for c in lib:
        fm = c["front_matter"]
        p = c["rel_path"]

        # required keys + types per contract.schema.json (structural re-check)
        for key in ("contract_id", "title", "version", "status"):
            if key not in fm:
                errors.append(f"{p}: front matter missing required key '{key}'")
        if errors and errors[-1].startswith(f"{p}: front matter missing"):
            continue

        cid = fm.get("contract_id", "")
        version = str(fm.get("version", ""))
        status = fm.get("status", "")

        if not CONTRACT_ID_RE.match(str(cid)):
            errors.append(f"{p}: invalid contract_id {cid!r}")
        if not SEMVER_RE.match(version):
            errors.append(f"{p}: invalid version {version!r}")
        if status not in VALID_STATUS:
            errors.append(
                f"{p}: invalid status {status!r} (valid: {sorted(VALID_STATUS)})"
            )
        layer = fm.get("layer", "")
        if layer not in LAYER_DIRS:
            errors.append(f"{p}: missing/invalid layer {layer!r}")

        # filename should match id
        stem = c["path"].stem
        expected = str(cid).upper().replace("-", "_")
        if stem != expected:
            errors.append(f"{p}: filename {stem}.md does not match contract_id {cid}")

        # id uniqueness
        if cid in seen_ids:
            errors.append(f"{p}: duplicate contract_id {cid} (also {seen_ids[cid]})")
        else:
            seen_ids[cid] = p

        # receipt: exactly one, in canonical form, unique across library
        if len(c["receipts"]) == 0:
            errors.append(
                f"{p}: missing receipt comment (<!-- contract-receipt: word-word-word -->)"
            )
        elif len(c["receipts"]) > 1:
            errors.append(f"{p}: multiple receipt comments found ({c['receipts']})")
        else:
            r = c["receipts"][0]
            if r in seen_receipts:
                errors.append(
                    f"{p}: duplicate receipt {r} (also in {seen_receipts[r]})"
                )
            else:
                seen_receipts[r] = p

        # applies/triggers shape
        for key in ("applies", "triggers"):
            v = fm.get(key)
            if v is None:
                continue
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                errors.append(f"{p}: '{key}' must be a list of strings")

        # schema-level validation of the front matter (subset; JSON Schema
        # keyword coverage is enforced where jsonschema is unavailable)
        err = _validate_against_contract_schema(fm, fm_contract_schema, p)
        if err:
            errors.extend(err)

    # CONTRACT_INDEX.md must reference every canonical contract id
    index_ids = _index_contract_ids()
    for cid in seen_ids:
        if cid not in index_ids:
            errors.append(
                f"index drift: contract '{cid}' missing from CONTRACT_INDEX.md"
            )
    for cid in index_ids:
        if cid not in seen_ids:
            errors.append(
                f"index drift: CONTRACT_INDEX.md lists unknown contract '{cid}'"
            )

    # Receipt-rotation discipline: meaningful changes must rotate receipts
    errors.extend(check_receipt_rotation(lib))

    # Index columns (version/status) must match canonical, not just ids
    errors.extend(check_index_sync(lib))

    # Changelog continuity: [Unreleased] exists and covers meaningful bumps
    errors.extend(check_changelog_discipline(lib))

    return errors


def _load_json_schema(name: str) -> dict:
    p = SCHEMA_DIR / name
    if not p.is_file():
        raise CTError(f"schema file missing: {name}")
    return json.loads(p.read_text(encoding="utf-8"))


def _validate_against_contract_schema(fm: dict, schema: dict, where: str) -> list[str]:
    """Structural enforcement of contract.schema.json rules (no jsonschema dep)."""
    errs = []
    props = schema.get("properties", {})
    required = schema.get("required", [])
    for key in required:
        if key not in fm:
            errs.append(f"{where}: schema requires '{key}'")
    for key, val in fm.items():
        if key not in props:
            if schema.get("additionalProperties") is False:
                errs.append(f"{where}: schema forbids additional property '{key}'")
            continue
        ps = props[key]
        if "enum" in ps and val not in ps["enum"]:
            errs.append(f"{where}: '{key}' value {val!r} not in enum {ps['enum']}")
        if ps.get("type") == "string":
            if not isinstance(val, str):
                errs.append(f"{where}: '{key}' must be a string")
            elif "pattern" in ps and not re.match(ps["pattern"], val):
                errs.append(f"{where}: '{key}' violates pattern {ps['pattern']}")
            elif (
                "maxLength" in ps
                and isinstance(val, str)
                and len(val) > ps["maxLength"]
            ):
                errs.append(f"{where}: '{key}' exceeds maxLength {ps['maxLength']}")
        if ps.get("type") == "array":
            if not isinstance(val, list):
                errs.append(f"{where}: '{key}' must be an array")
            elif "minItems" in ps and len(val) < ps["minItems"]:
                errs.append(f"{where}: '{key}' needs >= {ps['minItems']} items")
    return errs


def _index_contract_ids() -> set[str]:
    ids: set[str] = set()
    if INDEX_FILE.is_file():
        text = INDEX_FILE.read_text(encoding="utf-8")
        # registry rows only: the v2 aliases table also has backticked ids in
        # table cells, and an id named only as a redirect target is not a
        # registered contract (it would mask a missing row from drift checks)
        for m in _INDEX_ROW_RE.finditer(text):
            ids.add(m.group(1))
    return ids


_INDEX_ROW_RE = re.compile(
    r"^\|\s*`([a-z0-9]+(?:-[a-z0-9]+)*)`\s*\|[^|]*\|\s*([0-9]+\.[0-9]+\.[0-9]+)\s*\|\s*([a-z]+)\s*\|",
    re.MULTILINE,
)


def index_rows() -> dict[str, tuple[str, str]]:
    """{id: (version, status)} parsed from CONTRACT_INDEX.md rows."""
    if not INDEX_FILE.is_file():
        return {}
    return {
        m.group(1): (m.group(2), m.group(3))
        for m in _INDEX_ROW_RE.finditer(INDEX_FILE.read_text(encoding="utf-8"))
    }


def index_drift_details(lib: list[dict]) -> list[tuple[str, str, str, str, str]]:
    """(id, got_version, got_status, want_version, want_status) for every index
    row whose version/status disagrees with canonical. Membership drift (rows
    present/missing) is reported separately by validate_library."""
    rows = index_rows()
    out: list[tuple[str, str, str, str, str]] = []
    for c in lib:
        fm = c["front_matter"]
        cid = fm["contract_id"]
        want = (str(fm.get("version", "")), str(fm.get("status", "")))
        got = rows.get(cid)
        if got is not None and got != want:
            out.append((cid, got[0], got[1], want[0], want[1]))
    return out


def check_index_sync(lib: list[dict]) -> list[str]:
    """CONTRACT_INDEX.md rows must match the canonical library exactly — not
    just id membership, but version and status too. The index routes; when
    its columns drift from the contracts, agents trust a wrong registry."""
    if not INDEX_FILE.is_file():
        return ["index drift: CONTRACT_INDEX.md is missing"]
    return [
        f"index drift: '{cid}' row says {gv}/{gs}, canonical is {wv}/{ws}"
        for cid, gv, gs, wv, ws in index_drift_details(lib)
    ]


def rewrite_index_row(text: str, cid: str, want_version: str, want_status: str) -> tuple[str, int]:
    """Replace one row's version and status cells in place (deterministic;
    leaves every other byte of the index untouched)."""
    pat = re.compile(
        r"^(\|\s*`" + re.escape(cid)
        + r"`\s*\|[^|]*\|\s*)([0-9]+\.[0-9]+\.[0-9]+)(\s*\|\s*)([a-z]+)(\s*\|)",
        re.MULTILINE,
    )
    return pat.subn(lambda m: f"{m.group(1)}{want_version}{m.group(3)}{want_status}{m.group(5)}", text)


# ---------------------------------------------------------------- public-boundary scan
# The same check this library runs on itself, made reusable by adopters.
# Findings report a pattern LABEL and path — never the matched text — so the
# output stays redacted (public-private-boundaries). Needles are assembled by
# concatenation so this list never contains the literal shapes it scans for.
SCAN_PATTERNS: tuple[tuple[str, str], ...] = (
    ("credential:github-token-prefix", "gh" + "p_"),
    ("credential:github-oauth-prefix", "gh" + "o_"),
    ("credential:aws-access-key-prefix", "AK" + "IA"),
    ("key-header:private-key", "BEGIN PRIVATE " + "KEY"),
    ("key-header:rsa", "BEGIN " + "RSA"),
    ("topology:private-ip", "192.168" + "."),
    ("topology:private-domain", "hulganfamily.duck" + "dns.org"),
    ("topology:private-ip", "10.0" + "."),
)
SCAN_SKIP_PARTS = (".git", ".venv", "__pycache__", ".pytest_cache", ".contract-commitments")


def scan_surface(root: Path) -> list[dict]:
    """Banned public-boundary shapes under root. Redacted findings only."""
    hits: list[dict] = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or any(part in SCAN_SKIP_PARTS for part in f.parts):
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError, OSError):
            continue  # binary/unreadable: the text scanner skips (documented)
        for label, needle in SCAN_PATTERNS:
            if needle in text:
                hits.append({
                    "path": f.relative_to(root).as_posix(),
                    "kind": label.split(":", 1)[0],
                    "pattern": label,
                })
    return hits


# ---------------------------------------------------------------- lockfile


def build_lock(lib: list[dict] | None = None) -> dict:
    if lib is None:
        lib = load_library()
    entries = []
    for c in sorted(lib, key=lambda x: x["front_matter"].get("contract_id", "")):
        fm = c["front_matter"]
        entries.append(
            {
                "id": fm["contract_id"],
                "version": str(fm["version"]),
                "path": c["rel_path"],
                "sha256": c["sha256"],
                "receipt": c["receipts"][0] if c["receipts"] else None,
                "status": fm["status"],
            }
        )
    return {
        "schema": "play-nice/lock-v1",
        "generated_from": {
            "contract_count": len(entries),
        },
        "contracts": entries,
    }


def write_lock() -> dict:
    lock = build_lock()
    LOCKFILE.write_text(
        json.dumps(lock, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return lock


def load_lock() -> dict:
    if not LOCKFILE.is_file():
        raise CTError("contracts.lock.json not found; run 'contractctl lock'")
    return json.loads(LOCKFILE.read_text(encoding="utf-8"))


def verify_lock(lib: list[dict] | None = None) -> list[str]:
    errors = []
    if lib is None:
        lib = load_library()
    lock = load_lock()
    current = {c["front_matter"]["contract_id"]: c for c in lib}
    locked = {e["id"]: e for e in lock.get("contracts", [])}

    for cid, e in locked.items():
        if cid not in current:
            errors.append(
                f"lock drift: locked contract '{cid}' no longer exists in library"
            )
            continue
        c = current[cid]
        if e["sha256"] != c["sha256"]:
            errors.append(
                f"lock drift: '{cid}' content hash changed (was {e['sha256'][:12]}, now {c['sha256'][:12]})"
            )
        if str(e["version"]) != str(c["front_matter"]["version"]):
            errors.append(
                f"lock drift: '{cid}' version changed ({e['version']} → {c['front_matter']['version']})"
            )
        if e.get("receipt") != (c["receipts"][0] if c["receipts"] else None):
            errors.append(
                f"lock drift: '{cid}' receipt changed ({e.get('receipt')} → {c['receipts'][0] if c['receipts'] else None})"
            )
    for cid in current:
        if cid not in locked:
            errors.append(
                f"lock drift: library contract '{cid}' missing from contracts.lock.json (run lock)"
            )
    return errors


# ---------------------------------------------------------------- bundle identity
# Bundle identity represents the RESOLVED contract set (the contracts selected
# for a task), not the whole library. Two sessions resolving different task
# scopes get different bundle identities; the same scope + same library gets
# a byte-stable identity. The full library is itself representable as a set
# (all contracts) for lockfile purposes.


def _bundle_material(contract_refs: list[str]) -> str:
    """Canonical material: sorted id@version#sha256 refs."""
    return "|".join(sorted(contract_refs))


def resolved_refs(
    lock: dict, contract_ids: list[str] | set[str] | None = None
) -> list[str]:
    """id@version#sha256 refs for the given ids (all lockfile entries if None)."""
    ids = set(contract_ids) if contract_ids is not None else None
    refs = []
    for e in lock["contracts"]:
        if ids is None or e["id"] in ids:
            refs.append(f"{e['id']}@{e['version']}#{e['sha256']}")
    return refs


def bundle_receipt(lock: dict, contract_ids: list[str] | set[str] | None = None) -> str:
    """Deterministic three-word bundle receipt for the RESOLVED set.

    Not a credential; identifies a set of contract versions/hashes.
    """
    material = _bundle_material(resolved_refs(lock, contract_ids))
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
    words = _RECEIPT_WORDS
    n = len(words)
    i = int(digest[:16], 16)
    w1 = words[(i >> 0) % n]
    w2 = words[(i >> 24) % n]
    w3 = words[(i >> 48) % n]
    return f"{w1}-{w2}-{w3}"


def bundle_sha256(lock: dict, contract_ids: list[str] | set[str] | None = None) -> str:
    """SHA-256 over the exact resolved-set material (id@version#sha256)."""
    material = _bundle_material(resolved_refs(lock, contract_ids))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


_RECEIPT_WORDS = (
    "amber",
    "aster",
    "basalt",
    "beacon",
    "bramble",
    "cedar",
    "cinder",
    "clover",
    "compass",
    "dell",
    "dovetail",
    "driftwood",
    "echo",
    "ember",
    "fable",
    "fathom",
    "fern",
    "gable",
    "gatehouse",
    "harbor",
    "heather",
    "hollow",
    "inkstone",
    "jetty",
    "juniper",
    "kindle",
    "lantern",
    "latch",
    "ledger",
    "loam",
    "maple",
    "marble",
    "meadow",
    "nectar",
    "north",
    "opal",
    "orchard",
    "orbit",
    "prairie",
    "quartz",
    "quay",
    "ridge",
    "rill",
    "river",
    "sable",
    "sail",
    "stone",
    "thicket",
    "timber",
    "tundra",
    "urnfield",
    "vellum",
    "velvet",
    "window",
    "willow",
    "wren",
    "yarrow",
    "zenith",
)


# ---------------------------------------------------------------- resolution


def load_adoption(manifest_path: Path) -> dict:
    if not manifest_path.is_file():
        raise CTManifestMissing(manifest_path)
    text = manifest_path.read_text(encoding="utf-8")
    # strip front-matter delimiter style if present, else parse whole as yaml
    m = FM_RE.match(text)
    body = m.group(1) if m else re.sub(r"\A---\s*\n", "", text)
    try:
        data = _yaml_block_to_dict(body.split("\n"))
    except CTError as e:
        raise CTError(f"adoption manifest: {e}")
    if data.get("schema") != "play-nice/adoption-v1":
        raise CTError(
            f"adoption manifest: schema must be 'play-nice/adoption-v1', got {data.get('schema')!r}"
        )
    return data


# ---------------------------------------------------------------- manifest discovery
# One search order for every command that needs an adoption manifest, shared
# with `playnice` (tools/playnice/playnice.py find_adoption_manifest).
MANIFEST_CANDIDATES = (
    ".contracts/adoption.yaml",
    ".project/contracts/adoption.yaml",
    ".contracts/adoption.yml",
    ".project/contracts/adoption.yml",
)
MANIFEST_DEFAULT_NOTE = (
    "(default: the first of .contracts/adoption.yaml, "
    ".project/contracts/adoption.yaml found here)"
)
MANIFEST_HELP = "adoption manifest " + MANIFEST_DEFAULT_NOTE
# commands that cannot run without a manifest: --manifest defaults by discovery
NEEDS_MANIFEST = ("upgrade-check", "attest", "commit", "adopt", "freshness", "sync")


def discover_manifest(base: Path | None = None) -> Path:
    """The adoption manifest under `base` (default: the current directory).

    Returns the first existing candidate, or the primary path when none
    exists, so a "not found" error names the expected place.
    """
    base = base or Path(".")
    for rel in MANIFEST_CANDIDATES:
        if (base / rel).is_file():
            return base / rel
    return base / MANIFEST_CANDIDATES[0]


# ---------------------------------------------------------------- task matching
#
# One matcher for both resolution paths (manifest surfaces and the library's
# own contract triggers). Deterministic and stdlib-only: a trigger matches
# when its words appear in the task as whole words, in order. "ui" no longer
# fires inside "suite" or "build", and "log" no longer fires inside "login".
# Light plural folding means "tests" matches "test" and "pages" matches "page".

_WORD_RE = re.compile(r"[a-z0-9]+(?:\.[a-z0-9]+)*")


def _fold_word(w: str) -> str:
    """Fold simple English plurals so 'scripts' matches 'script'."""
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def match_words(text: str) -> list[str]:
    """Lowercase, split on anything that is not a letter or digit, fold plurals.

    Hyphens, slashes and underscores separate words, so 'event-driven' and
    'event driven' match each other. Dots inside a word are kept
    ('robots.txt').
    """
    return [_fold_word(w) for w in _WORD_RE.findall(str(text).lower())]


def phrase_in(phrase: str, task_words: list[str]) -> bool:
    """True when every word of `phrase` appears in `task_words`, in order, adjacent."""
    pw = match_words(phrase)
    if not pw:
        return False
    n = len(pw)
    return any(task_words[i : i + n] == pw for i in range(len(task_words) - n + 1))


def match_term(term: str, task_words: list[str], tags: set[str]) -> str | None:
    """How `term` matched, or None.

    Returns 'tag' when an explicit --tag names it (exact, or the same words),
    'task' when its words appear in the task text.
    """
    t = str(term).lower()
    if t in tags or match_words(t) in [match_words(x) for x in tags]:
        return "tag"
    if phrase_in(t, task_words):
        return "task"
    return None


def _surface_match(surface: str, task_words: list[str], tags: set[str]) -> str | None:
    """Manifest surfaces: the whole surface name, or the loose form kept for
    compatibility — 'external-api' also matches a task that says 'api'."""
    how = match_term(surface, task_words, tags)
    if how:
        return how
    words = match_words(surface)
    if (
        len(words) > 1
        and words[0] in ("external", "agent", "human", "ui", "api", "cli", "web", "integration")
        and words[-1] in task_words
    ):
        return "task"
    return None


def resolve_set(
    manifest: dict, task: str = "", task_tags: list[str] | None = None
) -> dict:
    """Resolve the smallest applicable contract set.

    Selection sources (in order): the floor; manifest always; manifest
    triggers whose surface appears in the task or the tags; library
    contracts whose own triggers appear in the task or the tags. Unknown
    contract references fail.

    Returns:
      selected: id -> why (the last source that selected it; kept for
                attestations and older callers)
      reasons:  id -> every reason, each {"source", "trigger", "via"}
                (via = "tag" | "task" | None), so a selection can be explained
    """
    lib = {c["front_matter"]["contract_id"]: c for c in load_library()}
    selected: dict[str, str] = {}  # id -> why
    reasons: dict[str, list[dict]] = {}
    errors: list[str] = []

    def add(cid: str, why: str, source: str, trigger=None, via=None):
        cid = canonical_id(cid, lib)
        if cid in lib:
            selected[cid] = why
            reasons.setdefault(cid, []).append(
                {"source": source, "trigger": trigger, "via": via}
            )
        else:
            errors.append(f"manifest references unknown contract '{cid}'")

    # The floor applies to every participant, whatever the manifest says.
    if "floor" in lib:
        add("floor", "floor", "floor")
    for cid in manifest.get("always", []) or []:
        add(cid, "always", "always")

    tags = {str(t).lower() for t in (task_tags or [])}
    task_words = match_words(task) if task else []
    if task or tags:
        triggers = manifest.get("triggers", {}) or {}
        if not isinstance(triggers, dict):
            errors.append(
                "manifest: 'triggers' must be a mapping of surface -> contract "
                "list (write 'triggers:' for none, not a scalar value)"
            )
            triggers = {}
        for surface, cids in triggers.items():
            via = _surface_match(str(surface), task_words, tags)
            if via:
                for cid in cids or []:
                    add(cid, f"trigger:{surface}", "manifest-trigger", str(surface), via)

    # library-level trigger matching: contracts whose own triggers appear in the task
    for cid, c in lib.items():
        trig = c["front_matter"].get("triggers") or []
        for t in trig:
            t = str(t).lower()
            if t in ("always", "always-applicable"):
                continue
            via = match_term(t, task_words, tags)
            if via:
                add(cid, f"library-trigger:{t}", "library-trigger", t, via)
                break

    return {
        "selected": selected,
        "reasons": reasons,
        "errors": errors,
        "library_size": len(lib),
    }


# ---------------------------------------------------------------- attestation

COMMITMENT_BODY = """I have loaded and verified the complete applicable contract set for this task.

I accept these contracts as operating constraints for this session and will
actively use their information when making decisions.

I will apply them to improve the interaction between every relevant side,
including humans, agents, tools, APIs, services, interfaces, automation,
data, repositories, and future maintainers.

I will prefer behavior that is:

- truthful
- accessible
- understandable
- interoperable
- respectful of finite human attention
- respectful of external systems
- inspectable
- recoverable
- reversible where practical
- explicit about uncertainty
- provider/tool neutral where appropriate
- friendly to both human and machine consumers

I will not treat these contracts as passive documentation.

I will not silently weaken, bypass, contradict, or ignore an applicable
contract for convenience.

When implementation choices create tension between participants, I will use
the applicable contracts to seek an outcome that improves the interaction
between them rather than optimizing one side at the unnecessary expense of
another.

If contracts genuinely conflict, required evidence is unavailable, or the
safe interpretation is unclear, I will preserve that state honestly and
surface the conflict rather than inventing certainty.

I understand that "play nice together" means designing the boundary between
systems as carefully as the systems themselves."""


FLOOR_IMPACT = "the floor applies to all work; proof is the floor receipt line"


def _with_floor_impact(task_impact: dict[str, str]) -> dict[str, str]:
    """The floor needs no per-task sentence: add a standard one if absent.
    Impacts written under an old (v1) id count for the v2 contract that
    now holds it."""
    aliases = load_aliases()
    merged: dict[str, str] = {"floor": FLOOR_IMPACT}
    for cid, sentence in (task_impact or {}).items():
        new = aliases.get(cid, cid)
        merged[new] = f"{merged[new]}; {sentence}" if new in merged and new != "floor" else sentence
    return merged


def make_attestation(
    manifest_path: Path,
    task: str,
    task_impact: dict[str, str],
    revision: str = "uncommitted",
    format_text: str = True,
    task_tags: list[str] | None = None,
    resolved_ids: set[str] | None = None,
) -> dict | str:
    """Attest an exact contract set.

    resolved_ids: when provided (e.g. by build_commitment for workers), attest
    EXACTLY this set — no re-resolution. This is the governing invariant:
    the contract set attested must be exactly the contract set committed.
    """
    task_impact = _with_floor_impact(task_impact)
    manifest = load_adoption(manifest_path)
    if resolved_ids is not None:
        # verify every id is real and known to the lockfile; no re-resolution
        lib_all = {c["front_matter"]["contract_id"]: c for c in load_library()}
        unknown = [cid for cid in resolved_ids if cid not in lib_all]
        if unknown:
            raise CTError(
                "attestation: unknown contract ids in resolved set: "
                + ", ".join(sorted(unknown))
            )
        res = {
            "selected": {cid: "inherited-or-resolved" for cid in resolved_ids},
            "errors": [],
            "library_size": len(lib_all),
        }
    else:
        res = resolve_set(manifest, task, task_tags)
    if res["errors"]:
        raise CTError("resolution errors:\n  " + "\n  ".join(res["errors"]))
    lib = {c["front_matter"]["contract_id"]: c for c in load_library()}
    lock = load_lock()
    # Fail closed on lock drift: an attestation against a drifted lockfile
    # would pin stale hashes and must not be produced.
    drift = verify_lock(list(lib.values()))
    if drift:
        raise CTError(
            "attestation blocked — lockfile drift (run contractctl lock):\n  "
            + "\n  ".join(drift)
        )
    locked = {e["id"]: e for e in lock["contracts"]}
    selected_ids = set(res["selected"])
    b_receipt = bundle_receipt(lock, selected_ids)

    loaded = []
    conflicts = []
    for cid, why in sorted(res["selected"].items()):
        c = lib[cid]
        entry = locked.get(cid)
        impact = task_impact.get(cid)
        status = "ACCEPTED"
        conflict = None
        if impact is None:
            status = "CONFLICT"
            conflict = (
                "missing task-impact acknowledgement (see contract-attestation rule 6)"
            )
            conflicts.append(f"{cid}: {conflict}")
        loaded.append(
            {
                "contract_id": cid,
                "version": str(c["front_matter"]["version"]),
                "sha256": c["sha256"],
                "receipt": c["receipts"][0],
                "status": status,
                "conflict": conflict,
            }
        )

    gate = "PASS" if not conflicts else "BLOCKED"
    att = {
        "format": ATTESTATION_FORMAT,
        "bundle": {
            "library_version": library_version(),
            "library_revision": revision,
            "receipt": b_receipt,
            "sha256": bundle_sha256(lock, selected_ids),
            "scope": "resolved-set",
        },
        "loaded": loaded,
        "task_impact": [f"{k}: {v}" for k, v in sorted(task_impact.items())],
        "conflicts": "; ".join(conflicts) if conflicts else "none",
        "gate": gate,
    }
    if format_text:
        return format_attestation_text(att, res)
    return att


def format_attestation_text(att: dict, res: dict) -> str:
    lines = [ATTESTATION_FORMAT, ""]
    lines.append("bundle:")
    lines.append(f"  library_version: {att['bundle'].get('library_version', '?')}")
    lines.append(f"  library_revision: {att['bundle'].get('library_revision', '?')}")
    lines.append(f"  receipt: {att['bundle']['receipt']}")
    lines.append(f"  sha256: {att['bundle'].get('sha256', '?')}")
    lines.append("  scope: resolved-set")
    lines.append("")
    lines.append("loaded:")
    for e in att["loaded"]:
        lines.append(f"  {e['contract_id']}@{e['version']}")
        lines.append(f"    receipt: {e['receipt']}")
        lines.append(f"    sha256: {e['sha256']}")
        lines.append(f"    status: {e['status']}")
    lines.append("")
    lines.append("task-impact:")
    for t in att["task_impact"]:
        lines.append(f"  - {t}")
    lines.append("")
    lines.append(f"conflicts: {att['conflicts']}")
    lines.append("")
    lines.append(f"CONTRACT GATE: {att['gate']}")
    return "\n".join(lines)


def verify_attestation(att_path: Path, manifest_path: Path | None = None) -> list[str]:
    errors: list[str] = []
    raw = att_path.read_text(encoding="utf-8")
    # Accept the text block format; parse it
    parsed = _parse_attestation_text(raw)
    if parsed is None:
        # try JSON
        try:
            att = json.loads(raw)
        except json.JSONDecodeError:
            return ["attestation: unparseable (neither text block nor JSON)"]
    else:
        att = parsed

    lib = {c["front_matter"]["contract_id"]: c for c in load_library()}
    lock = load_lock()
    locked = {e["id"]: e for e in lock["contracts"]}

    if att.get("format") != ATTESTATION_FORMAT:
        errors.append(f"attestation: format must be {ATTESTATION_FORMAT!r}")
    gate = att.get("gate")
    if gate not in ("PASS", "BLOCKED"):
        errors.append(f"attestation: gate must be PASS or BLOCKED, got {gate!r}")

    # lock drift fails closed: cannot verify against a stale lockfile
    drift = verify_lock(list(lib.values()))
    if drift:
        errors.extend(f"lock drift: {d}" for d in drift)
        return errors

    # bundle checks: the bundle is the RESOLVED set (the loaded contracts)
    b = att.get("bundle", {})
    loaded_ids = {
        e.get("contract_id") for e in att.get("loaded", []) if e.get("contract_id")
    }
    expected_receipt = bundle_receipt(lock, loaded_ids)
    if b.get("receipt") != expected_receipt:
        errors.append(
            f"attestation: bundle receipt mismatch (attested {b.get('receipt')!r}, current resolved-set receipt {expected_receipt!r}) — library changed, resolution changed, or stale attestation"
        )
    if b.get("sha256") and b.get("sha256") != bundle_sha256(lock, loaded_ids):
        errors.append("attestation: resolved-set bundle sha256 mismatch")

    loaded = att.get("loaded", [])
    if not loaded:
        errors.append("attestation: no contracts loaded")
    for e in loaded:
        cid = e.get("contract_id", "")
        if cid not in lib:
            errors.append(f"attestation: unknown contract '{cid}'")
            continue
        c = lib[cid]
        if e.get("receipt") != (c["receipts"][0] if c["receipts"] else None):
            errors.append(
                f"attestation: wrong receipt for '{cid}' (got {e.get('receipt')!r}, want {c['receipts'][0]!r})"
            )
        if e.get("sha256") != c["sha256"]:
            errors.append(f"attestation: wrong hash for '{cid}'")
        if e.get("version") != str(c["front_matter"]["version"]):
            errors.append(
                f"attestation: wrong version for '{cid}' ({e.get('version')} vs {c['front_matter']['version']})"
            )
        if e.get("status") not in ATTEST_STATUSES:
            errors.append(
                f"attestation: invalid status {e.get('status')!r} for '{cid}'"
            )
        if e.get("status") == "CONFLICT" and not e.get("conflict"):
            errors.append(f"attestation: CONFLICT for '{cid}' without explanation")

    if not att.get("task_impact"):
        errors.append("attestation: missing task-impact acknowledgement")

    # mandatory contracts from manifest must be present
    if manifest_path is not None:
        manifest = load_adoption(manifest_path)
        loaded_ids = {e.get("contract_id") for e in loaded}
        for cid in manifest.get("always", []) or []:
            if cid not in loaded_ids:
                errors.append(
                    f"attestation: mandatory contract '{cid}' (manifest always) not loaded"
                )

    # gate consistency
    if gate == "PASS":
        if any(e.get("status") == "CONFLICT" for e in loaded):
            errors.append("attestation: gate PASS but a loaded contract is CONFLICT")
        if att.get("conflicts") not in (None, "none", ""):
            errors.append("attestation: gate PASS but conflicts recorded")
    return errors


def _parse_attestation_text(raw: str) -> dict | None:
    """Parse the CONTRACT_ATTESTATION v1 text block back into data."""
    if ATTESTATION_FORMAT not in raw:
        return None
    loaded = []
    cur = None
    task_impact = []
    bundle = {
        "library_version": None,
        "library_revision": None,
        "receipt": None,
        "sha256": None,
        "scope": None,
    }
    conflicts = None
    gate = None
    in_impact = False
    for line in raw.split("\n"):
        s = line.strip()
        if s.startswith("library_version:") and cur is None:
            bundle["library_version"] = s.split(":", 1)[1].strip()
        elif s.startswith("library_revision:") and cur is None:
            bundle["library_revision"] = s.split(":", 1)[1].strip()
        elif s.startswith("receipt:") and cur is None:
            bundle["receipt"] = s.split(":", 1)[1].strip()
        elif s.startswith("sha256:") and cur is None:
            bundle["sha256"] = s.split(":", 1)[1].strip()
        elif s.startswith("scope:") and cur is None:
            bundle["scope"] = s.split(":", 1)[1].strip()
        elif re.match(r"^[a-z0-9-]+@\d+\.\d+\.\d+$", s):
            cid, ver = s.split("@")
            cur = {"contract_id": cid, "version": ver}
        elif cur is not None and s.startswith("receipt:"):
            cur["receipt"] = s.split(":", 1)[1].strip()
        elif cur is not None and s.startswith("sha256:"):
            cur["sha256"] = s.split(":", 1)[1].strip()
        elif cur is not None and s.startswith("status:"):
            cur["status"] = s.split(":", 1)[1].strip()
            loaded.append(cur)
            cur = None
        elif s.startswith("task-impact:"):
            in_impact = True
        elif s.startswith("conflicts:"):
            in_impact = False
            conflicts = s.split(":", 1)[1].strip()
        elif s.startswith("- ") and in_impact:
            task_impact.append(s[2:].strip())
        elif s.startswith("CONTRACT GATE:"):
            gate = s.split(":", 1)[1].strip()
    if gate is None:
        return None
    return {
        "format": ATTESTATION_FORMAT,
        "bundle": bundle,
        "loaded": loaded,
        "task_impact": task_impact,
        "conflicts": conflicts,
        "gate": gate,
    }


# ---------------------------------------------------------------- commitment

COMMITMENT_FORMAT = "CONTRACT OPERATIONAL COMMITMENT v1"
COMMITMENT_ACTIVE = "ACTIVE"
COMMITMENT_INACTIVE = "INACTIVE"


def _consumer_context_key(manifest_path: Path | None = None) -> str:
    """Identity of the consuming execution context.

    Resolution order:
    1. $CONTRACTCTL_SESSION_DIR — caller pins the artifact directory explicitly
       (any orchestration harness should set this per worktree/session).
    2. <manifest's consuming project root>/.contracts/sessions/ — the
       directory containing the adoption manifest (or its .contracts/ parent)
       anchors the artifacts to THAT project, so two consuming projects or two
       worktrees of the same project never collide.
    3. <library>/.contract-commitments/ — last-resort fallback when running
       inside the library itself with no manifest context.
    """
    env = os.environ.get("CONTRACTCTL_SESSION_DIR")
    if env:
        return env
    if manifest_path is not None:
        m = Path(manifest_path).resolve()
        if m.parent.name == ".contracts":
            root = m.parent  # <project>/.contracts/
            return str(root / "sessions")
        return str(m.parent / ".contracts" / "sessions")
    return str(REPO_ROOT / ".contract-commitments")


def default_artifact_path(
    role: str = "session", task: str = "", manifest_path: Path | None = None
) -> Path:
    """Project/worktree/session-safe artifact path.

    Artifacts live in the CONSUMING execution context (the project that owns
    the adoption manifest), never a global path in the contract library.
    Keyed by role+task so parallel sessions/workers coexist; callers may pin
    the directory with CONTRACTCTL_SESSION_DIR or --output.
    """
    d = Path(_consumer_context_key(manifest_path))
    d.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9-]+", "-", task.lower()).strip("-")[:48] or "untitled"
    return d / f"{role}-{slug}.json"


def build_commitment(
    manifest_path: Path,
    task: str,
    task_impact: dict[str, str],
    revision: str = "uncommitted",
    role: str = "session",
    parent_bundle: str | None = None,
    parent_manifest: Path | None = None,
    worker: bool = False,
    task_tags: list[str] | None = None,
) -> tuple[dict, str]:
    """Build the operational commitment for a task.

    Returns (artifact_dict, text_block). Raises CTError on any failure that
    must prevent the ACTIVE state: resolution errors, missing task-impact,
    conflicts, lock drift, or (for workers) an unverifiable parent bundle.
    """
    task_impact = _with_floor_impact(task_impact)
    manifest = load_adoption(manifest_path)
    # freshness gate: runs BEFORE resolution — a require-current policy must
    # establish the authoritative remote revision before anything mutates.
    gate_state, evidence = apply_freshness_gate(manifest, manifest_path)
    res = resolve_set(manifest, task, task_tags)
    if res["errors"]:
        raise CTError("commitment: resolution errors:\n  " + "\n  ".join(res["errors"]))

    lib = {c["front_matter"]["contract_id"]: c for c in load_library()}
    lock = load_lock()
    selected_ids = set(res["selected"])

    if worker:
        # Real inheritance: the parent bundle must be a resolvable bundle in
        # this library. The worker's resolved set is the UNION of the parent's
        # applicable contracts and the worker's own task-triggered contracts —
        # workers load inherited contracts, add task-specific ones, and therefore
        # cannot silently drop a parent constraint.
        if not parent_bundle:
            raise CTError(
                "commitment: worker commitment requires --parent-bundle (inherited bundle sha256)"
            )
        parent = find_commitment_by_bundle(parent_bundle, manifest_path)
        if parent is None:
            raise CTError(
                "commitment: parent bundle not found — an orchestrator commitment "
                "with this bundle_sha256 must exist under .contract-commitments/ "
                "(workers inherit a real parent bundle, not an arbitrary hash)"
            )
        parent_contracts = set(parent.get("contracts", []))
        parent_src = parent.get("source") or {}
        own_rev = str((manifest.get("source") or {}).get("revision", ""))
        if parent_src.get("revision") and own_rev and parent_src["revision"] != own_rev:
            raise CTError(
                "commitment: parent commitment used Play Nice source revision "
                f"{parent_src['revision'][:12]} but this manifest pins {own_rev[:12]} — "
                "a worker must not resolve a weaker/older source than its parent; "
                "re-commit under a parent committed against the current pin"
            )
        inherited_only = parent_contracts - selected_ids
        if inherited_only:
            # inherited contracts join the worker's resolved set; the worker must
            # acknowledge their impact too (attesting them, not merely inheriting)
            missing_impact = [c for c in inherited_only if c not in task_impact]
            if missing_impact:
                raise CTError(
                    "commitment: worker inherited contracts need task-impact "
                    f"acknowledgement too ({', '.join(sorted(missing_impact))}) — "
                    "a worker loads and attests the parent's applicable set, "
                    "never silently drops it"
                )
            selected_ids |= inherited_only
            res["selected"] = {
                cid: "inherited" if cid in inherited_only else why
                for cid, why in res["selected"].items()
            }
            for cid in inherited_only:
                res["selected"][cid] = "inherited"
        role = "worker"

    # every selected contract needs an impact acknowledgement (incl. inherited)
    missing_all = [cid for cid in selected_ids if cid not in task_impact]
    if missing_all:
        raise CTError(
            "commitment: missing task-impact acknowledgement for "
            f"{', '.join(sorted(missing_all))}"
        )

    # A PASS attestation over the EXACT (possibly unioned) set is a precondition;
    # its machinery also fails closed on lock drift. Governing invariant:
    # the set attested must be exactly the set committed.
    att = make_attestation(
        manifest_path,
        task,
        task_impact,
        revision,
        format_text=False,
        resolved_ids=selected_ids,
    )
    if att["gate"] != "PASS":
        raise CTError(
            "commitment: contract gate is BLOCKED — conflicts prevent the ACTIVE state:\n  "
            + str(att["conflicts"])
        )
    # defensive: the attested set must equal the committed set
    attested_ids = {e["contract_id"] for e in att["loaded"]}
    if attested_ids != selected_ids:
        raise CTError(
            "commitment: attestation/commitment set mismatch "
            f"(attested-only: {sorted(attested_ids - selected_ids)}, "
            f"committed-only: {sorted(selected_ids - attested_ids)})"
        )

    artifact = {
        "format": COMMITMENT_FORMAT,
        "role": role,  # session | orchestrator | worker
        "contract_gate": "PASS",
        "commitment": COMMITMENT_ACTIVE,
        "library_version": library_version(),
        "library_revision": revision,
        "bundle_receipt": bundle_receipt(lock, selected_ids),
        "bundle_sha256": bundle_sha256(lock, selected_ids),
        "bundle_scope": "resolved-set",
        "task": task,
        "task_fingerprint": task,
        "session_dir": str(
            default_artifact_path(role, task, manifest_path=manifest_path).parent
        ),
        "resolved_contracts": sorted(
            f"{cid}@{lib[cid]['front_matter']['version']}" for cid in selected_ids
        ),
        "contracts": sorted(selected_ids),
        "inherited_bundle": parent_bundle,
        "source": {
            "repository": str((manifest.get("source") or {}).get("repository", "")),
            "ref": evidence["ref"],
            "revision": str((manifest.get("source") or {}).get("revision", "")),
        },
        "freshness": evidence,
        "play_nice_source_revision": revision
        if revision != "uncommitted"
        else str((manifest.get("source") or {}).get("revision", "")),
        "activated_at": None,  # filled by caller with real timestamps if desired
    }

    text = format_commitment_text(artifact)
    return artifact, text


def _artifact_search_dirs(manifest_path: Path | None = None) -> list[Path]:
    """Directories to search for commitment artifacts, consumer-context first."""
    dirs: list[Path] = []
    seen: set[str] = set()
    primary = Path(_consumer_context_key(manifest_path))
    dirs.append(primary)
    # fallbacks: explicit env dirs may differ; library-local dir for
    # in-library sessions; never duplicate
    for d in (
        primary,
        Path(os.environ.get("CONTRACTCTL_SESSION_DIR", ""))
        if os.environ.get("CONTRACTCTL_SESSION_DIR")
        else None,
        REPO_ROOT / ".contract-commitments",
    ):
        if d is None:
            continue
        key = str(d.resolve()) if d.exists() or d.parent.exists() else str(d)
        if key not in seen:
            seen.add(key)
            if d not in dirs:
                dirs.append(d)
    return [d for d in dirs if d.is_dir()]


def find_commitment_by_bundle(
    bundle_sha: str, manifest_path: Path | None = None
) -> dict | None:
    """Find a recorded commitment (orchestrator or session) by its bundle sha256.

    Inheritance validates against recorded parent state in the SAME consuming
    context (plus the library-local fallback), so a worker cannot claim an
    invented parent.
    """
    for d in _artifact_search_dirs(manifest_path):
        for f in sorted(d.glob("*.json")):
            try:
                a = json.loads(f.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if (
                a.get("bundle_sha256") == bundle_sha
                and a.get("commitment") == COMMITMENT_ACTIVE
            ):
                if a.get("role") in ("orchestrator", "session"):
                    return a
    return None


def format_commitment_text(a: dict) -> str:
    lines = [COMMITMENT_FORMAT, ""]
    lines.append(COMMITMENT_BODY)
    lines.append("")
    lines.append(f"bundle: {a['bundle_receipt']}")
    lines.append(f"bundle_sha256: {a['bundle_sha256']}")
    lines.append(f"bundle_scope: {a.get('bundle_scope', 'resolved-set')}")
    if a.get("freshness"):
        fr = a["freshness"]
        lines.append(
            f"REMOTE FRESHNESS: {fr.get('status', 'UNKNOWN')}"
            + ("" if fr.get("enforced") else " (policy: pinned — not enforced)")
        )
        if fr.get("remote_revision"):
            lines.append(f"  remote_revision: {fr['remote_revision']}")
    if a.get("inherited_bundle"):
        lines.append(f"INHERITED CONTRACT BUNDLE: {a['inherited_bundle']}")
        lines.append(
            f"PLAY_NICE_SOURCE_REVISION: {a.get('play_nice_source_revision', 'unknown')}"
        )
        lines.append("PARENT CONTRACT COMMITMENT: ACTIVE")
    lines.append(f"role: {a['role']}")
    lines.append(f"task: {a['task']}")
    lines.append("")
    lines.append(f"CONTRACT COMMITMENT: {a['commitment']}")
    return "\n".join(lines)


def write_session_artifact(
    artifact: dict, path: Path | None = None, manifest_path: Path | None = None
) -> Path:
    """Persist the commitment into the consuming context (no secrets, by construction)."""
    p = path or default_artifact_path(
        artifact.get("role", "session"),
        artifact.get("task", ""),
        manifest_path=manifest_path,
    )
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    return p


def load_session_artifact(
    path: Path | None = None,
    role: str = "session",
    task: str = "",
    manifest_path: Path | None = None,
) -> dict | None:
    """Load the artifact for this role+task key, or the newest artifact when
    only a path/role is given. Searches the consuming context. Returns None
    when absent."""
    if path is not None:
        if not path.is_file():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
    slug = re.sub(r"[^a-z0-9-]+", "-", task.lower()).strip("-")[:48] or "untitled"
    for d in _artifact_search_dirs(manifest_path):
        candidates = sorted(
            d.glob(f"{role}-*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if task:
            exact = d / f"{role}-{slug}.json"
            if exact.is_file():
                candidates = [exact] + [c for c in candidates if c != exact]
        for c in candidates:
            try:
                return json.loads(c.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
    return None


def session_status(
    manifest_path: Path | None = None,
    artifact_path: Path | None = None,
    role: str = "session",
    task: str = "",
) -> tuple[str, list[str]]:
    """Report the current commitment state and any staleness.

    Returns (status_line, problems). Staleness rules:
    - library changed → resolved-set bundle receipt/sha no longer match → STALE
    - artifact task triggers additional contracts vs what was resolved → RE-RESOLVE
    - worker artifacts: parent bundle must still be a real recorded commitment
    """
    problems: list[str] = []
    artifact = load_session_artifact(
        artifact_path, role=role, task=task, manifest_path=manifest_path
    )
    if artifact is None:
        return "CONTRACT COMMITMENT: INACTIVE (no session artifact)", [
            "no commitment recorded for this session"
        ]

    lock = load_lock()
    recorded = set(artifact.get("contracts", []))
    cur_receipt = bundle_receipt(lock, recorded)
    cur_sha = bundle_sha256(lock, recorded)

    if artifact.get("commitment") != COMMITMENT_ACTIVE:
        problems.append("recorded commitment is not ACTIVE")
    if (
        artifact.get("bundle_receipt") != cur_receipt
        or artifact.get("bundle_sha256") != cur_sha
    ):
        problems.append(
            f"stale bundle — commitment was made against {artifact.get('bundle_receipt')}/{str(artifact.get('bundle_sha256'))[:12]}, "
            f"library now yields {cur_receipt}/{cur_sha[:12]} for this resolved set — re-attest and re-commit"
        )

    if manifest_path is not None and artifact.get("task_fingerprint"):
        manifest = load_adoption(manifest_path)
        res = resolve_set(manifest, artifact["task_fingerprint"])
        now = set(res["selected"])
        missing = now - recorded
        if missing:
            problems.append(
                "task now triggers additional contracts not in the commitment "
                f"({', '.join(sorted(missing))}) — re-resolution required"
            )

    if artifact.get("role") == "worker" and artifact.get("inherited_bundle"):
        parent = find_commitment_by_bundle(artifact["inherited_bundle"], manifest_path)
        if parent is None:
            problems.append(
                "parent commitment no longer recorded — inherited bundle "
                f"{artifact['inherited_bundle'][:12]} cannot be verified — re-commit under a live parent"
            )
        else:
            parent_rev = str((parent.get("source") or {}).get("revision", "") or "")
            own_rev = str((artifact.get("source") or {}).get("revision", "") or "")
            if parent_rev and own_rev and parent_rev != own_rev:
                problems.append(
                    f"parent used Play Nice source revision {parent_rev[:12]}, "
                    f"this worker committed against {own_rev[:12]} — re-commit under a current parent"
                )

    # live freshness re-check: require-current re-verifies the authoritative
    # remote each status call (fail closed); pinned never goes online.
    fr = artifact.get("freshness") or {}
    if fr.get("policy") == "require-current" and manifest_path is not None:
        fr_now = check_freshness(manifest_path)
        # rule 24: a changed authoritative revision invalidates a commitment
        # even when the new remote state is itself internally consistent.
        if fr_now.get("remote_revision") and fr_now["remote_revision"] != fr.get(
            "remote_revision"
        ):
            problems.append(
                f"remote freshness is stale: authoritative remote moved "
                f"({str(fr.get('remote_revision') or 'unknown')[:12]} → {fr_now['remote_revision'][:12]}) — "
                "fetch/update, re-resolve, re-attest, re-commit"
            )
        elif fr_now["status"] not in ("CURRENT",):
            problems.append(
                f"remote freshness {fr_now['status']} — freshness cannot be established, "
                "commitment is not trustworthy ACTIVE under require-current"
            )

    state = (
        "ACTIVE"
        if not problems
        else "STALE"
        if any("stale" in p for p in problems)
        else "INACTIVE"
    )
    if problems and "not ACTIVE" in problems[0]:
        state = "INACTIVE"
    summary = (
        f"CONTRACT COMMITMENT: {state}\n"
        f"  bundle: {artifact.get('bundle_receipt')} ({str(artifact.get('bundle_sha256'))[:12]}...)\n"
        f"  task: {artifact.get('task')}\n"
        f"  contracts: {len(recorded)} resolved\n"
        f"  role: {artifact.get('role', 'session')}"
    )
    for p in problems:
        summary += f"\n  - {p}"
    return summary, problems


def verify_commitment_artifact(
    artifact: dict, manifest_path: Path | None = None
) -> list[str]:
    """Verify a commitment artifact against the current library. Fail closed."""
    errors: list[str] = []
    if artifact.get("format") != COMMITMENT_FORMAT:
        errors.append(f"commitment: format must be {COMMITMENT_FORMAT!r}")
    if artifact.get("contract_gate") != "PASS":
        errors.append("commitment: requires a PASS contract gate")
    if artifact.get("commitment") != COMMITMENT_ACTIVE:
        errors.append("commitment: state is not ACTIVE")
    lock = load_lock()
    recorded = set(artifact.get("contracts", []))
    if artifact.get("bundle_receipt") != bundle_receipt(lock, recorded):
        errors.append(
            "commitment: resolved-set bundle receipt does not match current library (stale)"
        )
    if artifact.get("bundle_sha256") != bundle_sha256(lock, recorded):
        errors.append(
            "commitment: resolved-set bundle sha256 does not match current library (stale)"
        )
    if not artifact.get("contracts"):
        errors.append("commitment: no resolved contracts recorded")
    if not artifact.get("task"):
        errors.append("commitment: task not recorded")
    fr = artifact.get("freshness") or {}
    if fr.get("policy") == "require-current":
        if fr.get("status") != "CURRENT":
            errors.append(
                "commitment: freshness policy is require-current but recorded "
                f"status is {fr.get('status')!r} — ACTIVE requires CURRENT"
            )
        if not fr.get("remote_revision"):
            errors.append(
                "commitment: require-current artifact lacks remote freshness evidence"
            )
    if artifact.get("role") == "worker":
        if not artifact.get("inherited_bundle"):
            errors.append("commitment: worker commitment missing inherited bundle")
        else:
            parent = find_commitment_by_bundle(
                artifact["inherited_bundle"], manifest_path
            )
            if parent is None:
                errors.append(
                    "commitment: worker's inherited bundle has no recorded parent commitment"
                )
            else:
                dropped = set(parent.get("contracts", [])) - recorded
                if dropped:
                    errors.append(
                        f"commitment: worker dropped parent's applicable constraints ({', '.join(sorted(dropped))})"
                    )
    # every recorded contract must exist and hash-match
    locked = {e["id"]: e for e in lock["contracts"]}
    lib = {c["front_matter"]["contract_id"]: c for c in load_library()}
    for ref in artifact.get("contracts", []):
        if ref not in locked:
            errors.append(f"commitment: unknown contract '{ref}'")
        elif ref in lib and locked[ref]["sha256"] != lib[ref]["sha256"]:
            errors.append(
                f"commitment: contract '{ref}' content changed since commitment"
            )
    return errors


BASE_ENV = "PLAY_NICE_BASE"


def _git_out(*args: str) -> str | None:
    """stdout of a git command in the library checkout, or None on failure."""
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *args],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def comparison_base() -> tuple[str | None, str | None]:
    """The revision contract changes are judged against: (rev, error).

    Comparing against HEAD only works before a commit: once a change is
    committed (and always in CI) HEAD *is* the change, so nothing is checked.
    Order: $PLAY_NICE_BASE (set by `validate --base`; CI passes the PR's base
    commit), then the merge-base of HEAD and origin/main, then HEAD. No Git
    history at all gives (None, None): the checks are skipped, as documented.
    """
    if _git_out("rev-parse", "--git-dir") is None:
        return None, None
    override = os.environ.get(BASE_ENV, "").strip()
    if override:
        if _git_out("rev-parse", "--verify", "--quiet", f"{override}^{{commit}}") is None:
            return None, f"base: revision {override!r} not found (fetch it, or drop --base)"
        return override, None
    if _git_out("rev-parse", "--verify", "--quiet", "refs/remotes/origin/main") is not None:
        mb = _git_out("merge-base", "HEAD", "refs/remotes/origin/main")
        if mb and mb.strip():
            return mb.strip(), None
    return "HEAD", None


def _changed_since_base(lib: list[dict]) -> tuple[str | None, list[tuple[dict, str]], list[str]]:
    """(base, [(contract, text at base)] for canonical contracts whose text
    differs from the base, errors). New files are not listed."""
    base, err = comparison_base()
    if base is None:
        return None, [], [err] if err else []
    changed = []
    for c in lib:
        if c["front_matter"].get("status") != "canonical":
            continue
        prev = _git_out("show", f"{base}:{c['rel_path']}")
        if prev is None or prev == c["text"]:
            continue
        changed.append((c, prev))
    return base, changed, []


def _short(rev: str) -> str:
    return rev if rev == "HEAD" else rev[:12]


def check_receipt_rotation(lib: list[dict]) -> list[str]:
    """Mechanical enforcement: every contract change bumps the version, and
    meaningful (MINOR/MAJOR) changes rotate the receipt.

    Judged against comparison_base(), not just HEAD, so the rule still holds
    after the change is committed and in CI. Skipped (not failed) when Git
    history is unavailable (e.g. a fresh export).
    """
    base, changed, errors = _changed_since_base(lib)
    for c, prev in changed:
        fm = c["front_matter"]
        rel = c["rel_path"]
        cid = fm.get("contract_id", "?")
        try:
            prev_fm = parse_front_matter(prev)
        except CTError:
            continue
        prev_version = str(prev_fm.get("version", ""))
        cur_version = str(fm.get("version", ""))
        if prev_version == cur_version:
            errors.append(
                f"{rel}: content changed since {_short(base)} but version is "
                f"still {cur_version} (bump it: contractctl bump {cid} --patch, "
                "or --minor for a new rule)"
            )
            continue
        if not _beyond_patch(prev_version, cur_version):
            # PATCH = clarification only: no receipt rotation needed
            continue
        prev_receipts = RECEIPT_RE.findall(prev)
        cur_receipts = c["receipts"]
        if prev_receipts and cur_receipts and prev_receipts[0] == cur_receipts[0]:
            errors.append(
                f"{rel}: version changed {prev_version} -> {cur_version} "
                f"(meaningful) but receipt did not rotate (still {cur_receipts[0]})"
            )
    return errors


CHANGELOG_FILE = REPO_ROOT / "CHANGELOG.md"


def check_changelog_discipline(lib: list[dict]) -> list[str]:
    """Mechanical continuity: contract changes must be recorded.

    Two rules, both fail-closed only when verifiable (same philosophy as
    receipt rotation — no Git history means no claims):
      1. CHANGELOG.md must carry an [Unreleased] section for landed-but-
         unreleased changes.
      2. Every canonical contract whose content changed against the
         comparison base with a version bump beyond PATCH must be mentioned
         by a NEW bullet in the [Unreleased] section (diffed against the
         base's copy of the changelog).
    """
    if _git_out("rev-parse", "--git-dir") is None:
        return []  # no history available; cannot enforce (documented limitation)
    if not CHANGELOG_FILE.is_file():
        return ["changelog: CHANGELOG.md is missing"]

    def _unreleased_bullets(text: str) -> set[str]:
        m = re.search(
            r"^## \[Unreleased\]\s*\n(.*?)(?=^## \[|^\Z)",
            text,
            re.MULTILINE | re.DOTALL,
        )
        if not m:
            return set()
        return {ln.strip() for ln in m.group(1).splitlines() if ln.strip().startswith("-")}

    cur_text = CHANGELOG_FILE.read_text(encoding="utf-8")
    errors: list[str] = []
    if "## [Unreleased]" not in cur_text:
        errors.append(
            "changelog: missing '## [Unreleased]' section — landed changes "
            "need a home before the next release bump"
        )
    base, changed, base_errors = _changed_since_base(lib)
    if base is None:
        return errors  # base problems are reported once, by receipt rotation
    changed_meaningful: list[str] = []
    for c, prev in changed:
        try:
            prev_version = str(parse_front_matter(prev).get("version", ""))
        except CTError:
            continue
        cur_version = str(c["front_matter"].get("version", ""))
        if prev_version != cur_version and _beyond_patch(prev_version, cur_version):
            changed_meaningful.append(str(c["front_matter"]["contract_id"]))
    base_text = _git_out("show", f"{base}:CHANGELOG.md")
    if changed_meaningful and base_text is not None:
        new_bullets = _unreleased_bullets(cur_text) - _unreleased_bullets(base_text)
        blob = "\n".join(new_bullets).lower()
        for cid in changed_meaningful:
            if cid.lower() not in blob:
                errors.append(
                    f"changelog: '{cid}' has a meaningful version change since "
                    f"{_short(base)} but no new [Unreleased] bullet mentions it"
                )
    return errors


# ---------------------------------------------------------------- question/help artifacts


def validate_question(path: Path) -> list[str]:
    """Validate a play-nice/question|help-request|help-response artifact
    against schema/question.schema.json (structural subset enforcement)."""
    if not path.is_file():
        return [f"question: file not found: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"question: invalid JSON — {e}"]
    schema = json.loads(QUESTION_SCHEMA.read_text(encoding="utf-8"))
    errs: list[str] = []

    allowed_schemas = schema["properties"]["schema"]["enum"]
    if data.get("schema") not in allowed_schemas:
        errs.append(
            f"question: schema must be one of {allowed_schemas}, got {data.get('schema')!r}"
        )
    for key in schema.get("required", []):
        if key not in data:
            errs.append(f"question: missing required field '{key}'")

    statuses = schema["properties"]["status"]["enum"]
    # documented migration aliases: legacy lowercase forms parse but are
    # normalized (never emitted canonically)
    ALIASES = {"waiting_for_answer": "WAITING", "answered": "ANSWERED"}
    raw_status = data.get("status")
    status = ALIASES.get(raw_status, raw_status)
    if status not in statuses:
        errs.append(f"question: invalid status {raw_status!r} (valid: {statuses})")

    for pkey in ("requester", "target"):
        p = data.get(pkey)
        if p is None:
            continue
        if (
            not isinstance(p, dict)
            or p.get("type")
            not in schema["$defs"]["participant"]["properties"]["type"]["enum"]
        ):
            errs.append(
                f"question: {pkey}.type must be one of {schema['$defs']['participant']['properties']['type']['enum']}"
            )

    if data.get("schema") == "play-nice/help-request-v1" and not data.get(
        "needed_capability"
    ):
        errs.append("question: help-request-v1 requires 'needed_capability'")
    if data.get("schema") == "play-nice/help-response-v1":
        if not data.get("result"):
            errs.append("question: help-response-v1 requires 'result'")
        if status not in ("ANSWERED", "DECLINED", "EXPIRED"):
            errs.append(
                "question: help-response status must be ANSWERED, DECLINED, or EXPIRED"
            )

    if (
        data.get("blocking") is False
        and data.get("safe_to_continue_without_answer") is False
    ):
        errs.append("question: inconsistent — not blocking but not safe to continue")

    # secret-shape hygiene: help artifacts must not carry credential-like values
    blob = json.dumps(data).lower()
    for shape in ('api_key":', 'token":', 'password":', 'secret":'):
        if shape in blob:
            errs.append(
                f"question: possible inline secret near '{shape}' — help artifacts reference secrets symbolically, never inline"
            )

    # choices shape
    choices = data.get("choices")
    if choices is not None:
        if not isinstance(choices, list) or len(choices) < 2:
            errs.append("question: choices must be a list of at least 2 when present")
        else:
            for ch in choices:
                if not isinstance(ch, dict) or not ch.get("id") or not ch.get("label"):
                    errs.append("question: each choice needs 'id' and 'label'")
    rec = data.get("recommended")
    if rec is not None and choices is not None:
        if not any(c.get("id") == rec for c in choices):
            errs.append(f"question: recommended {rec!r} is not one of the choice ids")
    return errs


# ---------------------------------------------------------------- adoption


def validate_adoption_manifest(manifest_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        manifest = load_adoption(manifest_path)
    except CTError as e:
        return [str(e)]
    lib = {c["front_matter"]["contract_id"] for c in load_library()}
    schema = _load_json_schema("adoption.schema.json")
    # structural checks
    src = manifest.get("source")
    if (
        not isinstance(src, dict)
        or not src.get("repository")
        or not src.get("revision")
    ):
        errors.append("adoption: source.repository and source.revision are required")
    for cid in manifest.get("always", []) or []:
        if canonical_id(cid, lib) not in lib:
            errors.append(f"adoption: unknown contract in always: '{cid}'")
    triggers = manifest.get("triggers", {}) or {}
    if not isinstance(triggers, dict):
        errors.append(
            "adoption: 'triggers' must be a mapping of surface -> contract list; "
            "for no triggers write 'triggers:' (empty), not a scalar value"
        )
    else:
        for surface, cids in triggers.items():
            if not isinstance(cids, list):
                errors.append(f"adoption: triggers.{surface} must be a list")
                continue
            for cid in cids:
                if canonical_id(cid, lib) not in lib:
                    errors.append(
                        f"adoption: unknown contract in triggers.{surface}: '{cid}'"
                    )
    props = schema.get("properties", {})
    for key in manifest:
        if key not in props and schema.get("additionalProperties") is False:
            errors.append(f"adoption: schema forbids additional property '{key}'")
    try:
        freshness_config(manifest)
    except CTError as e:
        errors.append(str(e))
    return errors


def check_stale_pin(manifest_path: Path) -> list[str]:
    """Stale pin detection: the adoption revision must match this library's
    current git revision. The sentinel '0000000' marks an example/unadopted
    manifest and is reported as a reminder, not an error."""
    errors: list[str] = []
    try:
        manifest = load_adoption(manifest_path)
    except CTError as e:
        return [str(e)]
    current = library_revision()
    pinned = (manifest.get("source", {}) or {}).get("revision", "")
    if pinned == "0000000":
        # example placeholder: valid shape, but cannot be used for real adoption
        errors.append(
            "adoption: placeholder revision 0000000 — pin the adopted commit SHA "
            "before using this manifest in a project"
        )
        return errors
    if pinned and current and pinned != current:
        errors.append(
            f"adoption: stale pin — manifest pins revision {pinned}, library is at {current}"
        )
    return errors


def library_version() -> str:
    """Library semver (VERSION file). Independent from the adopted Git revision:
    version describes contract content; revision pins the exact adopted commit."""
    if VERSION_FILE.is_file():
        v = VERSION_FILE.read_text(encoding="utf-8").strip()
        if v:
            return v
    return "unknown"


def floor_version() -> str:
    """Version of the floor (contracts/everyone/FLOOR.md) — the number proof lines name."""
    floor = REPO_ROOT / "contracts" / "everyone" / "FLOOR.md"
    try:
        m = re.search(r"(?m)^version:\s*(\S+)", floor.read_text(encoding="utf-8"))
    except OSError:
        m = None
    return m.group(1) if m else "unknown"


def version_line(tool: str, tool_version: str | None = None) -> str:
    """One --version line naming each number and what it versions.

    The library (VERSION) versions the contract set, the floor is what proof
    lines name, and a tool may carry its own version. They are different
    things on purpose, so each is labeled rather than merged.
    """
    head = f"{tool} {tool_version}" if tool_version else tool
    return f"{head} · library {library_version()} · floor {floor_version()}"


def library_revision() -> str:
    """Adopted Git revision of the library (commit SHA when available, else VERSION)."""
    import subprocess

    try:
        sha = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        if SHA256_RE.match(sha) or (
            len(sha) >= 7 and all(c in "0123456789abcdef" for c in sha)
        ):
            return sha
    except Exception:
        pass
    return library_version()


# ---------------------------------------------------------------- freshness
# Remote freshness: before mutating work under a `require-current` freshness
# policy, the configured authoritative remote revision must be established by
# a deterministic git operation (`git ls-remote`). A local checkout, an
# adoption pin, a previous session, or cached information is never proof of
# remote freshness. Unknown is a valid state and fails closed.

FRESHNESS_STATES = ("CURRENT", "BEHIND", "DIVERGED", "UNREACHABLE", "UNKNOWN")
FRESHNESS_POLICIES = ("pinned", "require-current")
FRESHNESS_UPDATES = ("review", "automatic")
LS_REMOTE_TIMEOUT = 20


class CTFreshnessError(CTError):
    """Freshness gate failure. Carries the machine state for exact reporting."""

    def __init__(self, state: str, detail: str = ""):
        super().__init__(detail or f"remote freshness: {state}")
        self.state = state
        self.detail = detail


def freshness_config(manifest: dict) -> dict:
    """Freshness policy of an adoption manifest.

    Absent block means the legacy default: policy pinned, update review —
    existing manifests must not change behavior by upgrading contractctl.
    """
    fr = manifest.get("freshness")
    if fr is None:
        return {"policy": "pinned", "ref": "main", "update": "review"}
    if not isinstance(fr, dict):
        raise CTError("adoption manifest: 'freshness' must be a mapping")
    policy = fr.get("policy", "pinned")
    if policy not in FRESHNESS_POLICIES:
        raise CTError(
            f"adoption manifest: freshness.policy must be one of {list(FRESHNESS_POLICIES)}, got {policy!r}"
        )
    update = fr.get("update", "review")
    if update not in FRESHNESS_UPDATES:
        raise CTError(
            f"adoption manifest: freshness.update must be one of {list(FRESHNESS_UPDATES)}, got {update!r}"
        )
    ref = fr.get("ref", "main")
    if not isinstance(ref, str) or not ref or ref.startswith("refs/"):
        raise CTError(
            "adoption manifest: freshness.ref must be a branch name like 'main'"
        )
    return {"policy": policy, "ref": ref, "update": update}


def _remote_url(repository: str) -> str:
    """Repository identifier -> git URL. GitHub owner/repo shorthand expands
    to the canonical https URL; full URLs and local paths pass through."""
    if repository.startswith(("/", "./", "../")) or Path(repository).exists():
        return repository
    if "://" in repository or repository.startswith("git@"):
        return repository
    if re.match(r"^[\w.-]+/[\w.-]+$", repository):
        return f"https://github.com/{repository}.git"
    return repository


def git_ls_remote(repository: str, ref: str) -> str | None:
    """Deterministic remote head of refs/heads/<ref>.

    Returns the full SHA, or None when the ref does not exist on the remote.
    Raises CTFreshnessError(UNREACHABLE) when the remote cannot be queried.
    """
    url = _remote_url(repository)
    try:
        proc = subprocess.run(
            ["git", "ls-remote", url, f"refs/heads/{ref}"],
            capture_output=True,
            text=True,
            timeout=LS_REMOTE_TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError):
        raise CTFreshnessError(
            "UNREACHABLE", f"git ls-remote {url} failed (timeout/error)"
        )
    if proc.returncode != 0:
        raise CTFreshnessError(
            "UNREACHABLE",
            "git ls-remote failed: "
            + (proc.stderr.strip().splitlines() or ["unknown error"])[-1],
        )
    for line in proc.stdout.split("\n"):
        line = line.strip()
        if not line or "\t" not in line:
            continue
        sha, refname = line.split("\t", 1)
        if refname == f"refs/heads/{ref}" and GITSHA_RE.match(sha):
            return sha
    return None  # ref not found on remote


# Surfaces whose changes require re-review before a require-current pin may
# read CURRENT while the remote head has moved ahead. Everything else
# (docs-only commits, README, CHANGELOG, tooling) is reviewed as it merges.
EQUIVALENCE_SURFACES = ("contracts/", "schema/")


def _fetch_object(repo: Path, url: str, sha: str) -> bool:
    """Best-effort fetch of one commit object from the authoritative remote
    into the library checkout. True when the object exists locally after."""
    if _is_ancestor_library(repo, sha, sha) is True:
        return True  # already present (short-circuits the network path)
    try:
        r = subprocess.run(
            [
                "git",
                "-C",
                str(repo),
                "fetch",
                "--quiet",
                "--no-tags",
                url,
                sha,
            ],
            capture_output=True,
            text=True,
            timeout=LS_REMOTE_TIMEOUT,
        )
        if r.returncode != 0:
            return False
    except (OSError, subprocess.TimeoutExpired):
        return False
    probe = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    return probe.returncode == 0


def contract_set_equivalent(repo: Path, pin: str, remote: str, url: str) -> tuple[str, str]:
    """Compare the normative contract set between two library revisions.

    `repo` is the library checkout used for history and object access; `url`
    is the authoritative remote to fetch from when objects are missing.

    Returns (verdict, detail). Verdicts:
      EQUIVALENT   both revisions' contracts/ + schema/ trees are byte-identical
      CHANGED      at least one normative file differs between them
      UNVERIFIABLE history/objects unavailable — never treated as equivalent
    """
    if _is_ancestor_library(repo, pin, remote) is not True:
        return "UNVERIFIABLE", "pin is not a provable ancestor of the remote revision"
    have_pin = _is_ancestor_library(repo, pin, pin) is True
    have_remote = _is_ancestor_library(repo, remote, remote) is True
    if not (have_pin and have_remote):
        missing = remote if not have_remote else pin
        if not _fetch_object(repo, url, missing):
            return (
                "UNVERIFIABLE",
                "required objects are not available locally and could not be fetched",
            )
    # Compare by blob hash, not just commit-to-commit: when one side IS the
    # working tree (pin == local HEAD of a dirty checkout), uncommitted edits
    # to contracts/ or schema/ must count — otherwise a modified-but-unlocked
    # contract would be silently declared equivalent.
    def _tree(rev: str) -> dict[str, str] | None:
        try:
            r = subprocess.run(
                ["git", "-C", str(repo), "ls-tree", "-r", rev, "--", *EQUIVALENCE_SURFACES],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if r.returncode != 0:
            return None
        blobs = {}
        for line in r.stdout.splitlines():
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) >= 3:
                blobs[path] = parts[2]
        return blobs

    def _worktree() -> dict[str, str] | None:
        """Worktree state of the normative surfaces, keyed by relative path.

        Values are git-blob-compatible sha1 digests computed over the same
        content git hashed at commit time: git stores blob = sha1("blob
        {len}\0" + bytes), where bytes is the ON-DISK content with CRLF→LF
        normalization applied iff core.autocrlf says so. On Linux with
        autocrlf=false (and text=auto defaults never converting), disk bytes
        equal git bytes; we consult config anyway and fail closed to an
        empty mapping when normalization would differ from our assumption.
        """
        crlf = subprocess.run(
            ["git", "-C", str(repo), "config", "--get", "core.autocrlf"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if crlf.returncode == 0 and crlf.stdout.strip().lower() not in ("false", ""):
            return None  # cannot reproduce git's conversion deterministically
        blobs = {}
        for surface in EQUIVALENCE_SURFACES:
            d = repo / surface
            if not d.is_dir():
                continue
            for f in sorted(d.rglob("*")):
                if not f.is_file():
                    continue
                rel = f.relative_to(repo).as_posix()
                try:
                    raw = f.read_bytes()
                except OSError:
                    return None
                digest = hashlib.sha1(
                    b"blob %d\0" % len(raw) + raw
                ).hexdigest()
                blobs[rel] = digest
        return blobs

    head_sha = None
    try:
        hr = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        head_sha = hr.stdout.strip() if hr.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        pass

    def _side(rev: str):
        """(blobs, use_worktree_overlay) for one revision."""
        if head_sha and rev == head_sha:
            wt = _worktree()
            if wt is not None:
                return wt, True
        return _tree(rev), False

    ta, _overlay = _side(pin)
    tb, _ = _side(remote)
    if ta is None or tb is None:
        return "UNVERIFIABLE", "could not enumerate normative trees for comparison"
    # both maps hold git blob sha1s (ls-tree objects, or identical blob
    # reconstruction for the working tree), so plain comparison is exact
    changed = sorted(set(ta) ^ set(tb)) + [
        pth for pth in sorted(set(ta) & set(tb)) if ta[pth] != tb[pth]
    ]
    if changed:
        return (
            "CHANGED",
            "normative surfaces differ between pin and remote: "
            + ", ".join(changed[:8]),
        )
    return "EQUIVALENT", "contracts/ and schema/ are byte-identical between pin and remote"


def self_adoption_claim(
    manifest: dict, manifest_path: Path, library_root: Path | None = None
) -> str | None:
    """Is this the library adopting itself?

    None   the manifest makes no self-adoption claim (`source.self` unset/false)
    "ok"   `source.self: true` in the library's own .contracts/adoption.yaml
    other  the claim is invalid; the string says why

    A commit cannot pin its own final SHA, so self-adoption is checked by
    ancestry (the pin is in the history being checked), never by equality.
    The claim is only honored at the library root, so a consumer cannot use
    it to step around the strict external pin check.
    """
    src = manifest.get("source") or {}
    if src.get("self") is not True:
        return None
    root = (library_root or REPO_ROOT).resolve()
    try:
        where = Path(manifest_path).resolve()
    except OSError:
        where = Path(manifest_path)
    if where != root / ".contracts" / "adoption.yaml":
        return (
            "source.self: true is only valid in the library's own "
            ".contracts/adoption.yaml"
        )
    return "ok"


def _is_ancestor_library(repo: Path, a: str, b: str) -> bool | None:
    """True/False when ancestry is provable with local objects, else None."""
    try:
        probe = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{b}^{{commit}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if probe.returncode != 0:
            return None
        r = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", a, b],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if r.returncode == 0:
        return True
    if r.returncode == 1:
        return False
    return None


def check_freshness(manifest_path: Path) -> dict:
    """Establish the state of the configured authoritative remote revision.

    CURRENT   remote head equals the adopted revision AND the library
              checkout — or, under update: automatic, both revisions are
              provable ancestors of the remote and contracts/ + schema/ are
              byte-identical between them and it (equivalence rule; recorded
              as freshness.equivalence in commitment artifacts)
    BEHIND    differing revisions provably fast-forward (remote is ahead)
    DIVERGED  revisions differ without a proven fast-forward relationship
    UNREACHABLE  the remote could not be queried
    UNKNOWN   the check could not be established (no pin, ref missing, malformed)

    Fail closed: only CURRENT satisfies require-current.
    """
    manifest = load_adoption(manifest_path)
    cfg = freshness_config(manifest)
    src = manifest.get("source") or {}
    repository = str(src.get("repository", "") or "")
    adopted = str(src.get("revision", "") or "")
    local = library_revision()
    out = {
        "policy": cfg["policy"],
        "enforced": cfg["policy"] == "require-current",
        "ref": f"refs/heads/{cfg['ref']}",
        "repository": repository,
        "adopted_revision": adopted,
        "library_revision": local,
        "remote_revision": None,
        "status": "UNKNOWN",
        "detail": "",
    }
    if not repository:
        out["detail"] = "adoption manifest has no source.repository"
        return out
    if adopted in ("", "0000000"):
        out["detail"] = "no adopted revision pinned (pin the commit you reviewed)"
        return out

    try:
        remote = git_ls_remote(repository, cfg["ref"])
    except CTFreshnessError as e:
        out["status"] = e.state
        out["detail"] = e.detail
        return out
    out["remote_revision"] = remote
    if remote is None:
        out["detail"] = f"remote has no ref refs/heads/{cfg['ref']}"
        return out

    # normalize pins (short SHAs, branchy pins) against the library checkout
    def _normalize(pin: str) -> str:
        try:
            r = subprocess.run(
                [
                    "git",
                    "-C",
                    str(REPO_ROOT),
                    "rev-parse",
                    "--verify",
                    "--quiet",
                    pin + ("^{commit}" if not pin.startswith(("^", ":")) else ""),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if r.returncode == 0 and GITSHA_RE.match(r.stdout.strip()):
                return r.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
        return pin

    adopted = _normalize(adopted)
    if GITSHA_RE.match(local):
        local = _normalize(local)
    else:
        out["detail"] = (
            "cannot establish the local library revision (no git checkout) — "
            "the contract set in use cannot be compared to the remote"
        )
        return out
    out["adopted_revision"] = adopted
    out["library_revision"] = local

    claim = self_adoption_claim(manifest, manifest_path)
    if claim is not None:
        return _self_freshness(out, claim, adopted, local, remote)

    pins = {adopted, local}
    if pins == {remote}:  # every pin equals the remote head
        out["status"] = "CURRENT"
        return out
    # classify conservative: BEHIND only when the fast-forward is provable
    diverged = False
    for pin in pins:
        if _is_ancestor_library(REPO_ROOT, pin, remote) is not True:
            diverged = True
    url = _remote_url(repository)
    if not diverged:
        # Ancestor-with-unchanged-set rule: under update: automatic, a pin
        # that is a provable ancestor of the remote may read CURRENT when
        # BOTH the adopted pin and the checkout's own HEAD reach the remote
        # only through commits that leave contracts/ and schema/ byte-
        # identical. Review still happens as changes merge through PRs; this
        # ends the post-merge pin treadmill without weakening fail-closed
        # semantics (anything unverifiable stays BEHIND).
        if cfg["update"] == "automatic":
            verdicts = {}
            for pin in (adopted, local):
                v, d = contract_set_equivalent(REPO_ROOT, pin, remote, url)
                verdicts[pin] = (v, d)
            if all(v == "EQUIVALENT" for v, _ in verdicts.values()):
                out["status"] = "CURRENT"
                out["equivalence"] = {
                    "rule": "ancestor-pin + byte-identical contracts/ and schema/ to remote",
                    "adopted_verdict": verdicts[adopted][0],
                    "library_verdict": verdicts[local][0],
                }
                out["detail"] = (
                    f"remote {out['ref']} is {remote[:12]}; adopted pin {adopted[:12]} "
                    "is an ancestor with an unchanged contract set (equivalence rule)"
                )
                return out
            first_bad = next(
                (
                    f"{pin[:12]}: {v} — {d}"
                    for pin, (v, d) in verdicts.items()
                    if v != "EQUIVALENT"
                ),
                "",
            )
            out["equivalence_note"] = first_bad
    out["status"] = "DIVERGED" if diverged else "BEHIND"
    out["detail"] = (
        f"remote {out['ref']} is {remote[:12]}; adopted pin {adopted[:12]}; "
        "the contract set being used has not been reviewed at the remote revision"
        if out["status"] == "BEHIND"
        else f"remote {out['ref']} is {remote[:12]}; no proven fast-forward from the adopted revision {adopted[:12]}"
    )
    return out


def _self_freshness(out: dict, claim: str, adopted: str, local: str, remote: str) -> dict:
    """Freshness for the library adopting itself (see self_adoption_claim).

    CURRENT  the pin is in remote history and this checkout contains the
             remote head (main itself, or a branch that has merged main)
    BEHIND   this checkout is an ancestor of the remote head (pull)
    DIVERGED the pin is not in remote history, or the branch lacks main
    UNKNOWN  the claim is invalid, or ancestry cannot be proven locally
    """
    out["self_adoption"] = True
    if claim != "ok":
        out["detail"] = claim
        return out
    pin_in = _is_ancestor_library(REPO_ROOT, adopted, remote)
    has_remote = _is_ancestor_library(REPO_ROOT, remote, local)
    if pin_in is None or has_remote is None:
        out["detail"] = (
            f"cannot prove ancestry with local objects (fetch {out['ref']} and "
            "full history, then re-run)"
        )
        return out
    if not pin_in:
        out["status"] = "DIVERGED"
        out["detail"] = (
            f"self-adoption pin {adopted[:12]} is not in the history of "
            f"{out['ref']} {remote[:12]} (a squash-merged branch commit?); "
            "pin a commit that is on main"
        )
        return out
    if has_remote:
        out["status"] = "CURRENT"
        out["detail"] = (
            f"self-adoption: this checkout contains {out['ref']} {remote[:12]}; "
            f"pin {adopted[:12]} is in its history"
        )
        return out
    behind = _is_ancestor_library(REPO_ROOT, local, remote) is True
    out["status"] = "BEHIND" if behind else "DIVERGED"
    out["detail"] = (
        f"self-adoption: {out['ref']} {remote[:12]} is ahead of this checkout; pull it"
        if behind
        else f"self-adoption: this branch does not contain {out['ref']} "
        f"{remote[:12]}; merge main into it"
    )
    return out


def freshness_evidence(result: dict, *, enforced: bool) -> dict:
    """Secret-free freshness evidence for the session/commitment artifact."""
    ev = {
        "policy": result["policy"],
        "status": result["status"],
        "ref": result["ref"],
        "repository": result["repository"],
        "remote_revision": result.get("remote_revision"),
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checked_via": "git ls-remote",
        "enforced": enforced,
        "reason": result.get("detail", "") if result["status"] != "CURRENT" else "",
    }
    # CURRENT via the equivalence rule must be distinguishable from exact-match
    # CURRENT in recorded provenance (which revision was actually adopted).
    if result.get("equivalence"):
        ev["equivalence"] = result["equivalence"]
    return ev


def apply_freshness_gate(
    manifest: dict, manifest_path: Path
) -> tuple[str, dict | None]:
    """Commitment gate for the manifest's freshness policy.

    Returns ("ok", evidence) when mutation may proceed to the attestation gate.
    Raises CTFreshnessError when a require-current policy fails. A pinned
    policy never contacts the network at commit time (backward-compatible).
    """
    cfg = freshness_config(manifest)
    if cfg["policy"] != "require-current":
        return "ok", {
            "policy": "pinned",
            "status": "UNKNOWN",
            "ref": f"refs/heads/{cfg['ref']}",
            "repository": str((manifest.get("source") or {}).get("repository", "")),
            "remote_revision": None,
            "checked_at": None,
            "checked_via": None,
            "enforced": False,
            "reason": "not checked (policy: pinned)",
        }
    result = check_freshness(manifest_path)
    evidence = freshness_evidence(result, enforced=True)
    if result["status"] == "CURRENT":
        return "ok", evidence
    raise CTFreshnessError(result["status"], result.get("detail", ""))


# ---------------------------------------------------------------- project context / participant packs

CANONICALITY_STATES = {
    "canonical",
    "reference",
    "observed",
    "generated",
    "historical",
    "superseded",
    "stale",
    "unknown",
}
PARTICIPANT_TYPES = {
    "design-service",
    "forge",
    "agent",
    "automation",
    "test-tool",
    "deployment-system",
    "database",
    "external-api",
    "monitoring",
    "identity",
    "human-team",
    "other",
}
SECRET_SHAPE_RE = re.compile(
    r"(api[_-]?key|token|password|secret|cookie|credential)\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{16,}",
    re.IGNORECASE,
)


def _load_yaml_file(path: Path) -> dict:
    if not path.is_file():
        raise CTError(f"file not found: {path}")
    try:
        return _yaml_block_to_dict(path.read_text(encoding="utf-8").split("\n"))
    except CTError as e:
        raise CTError(f"{path}: {e}")


def _check_no_secrets(root: Path, errs: list[str]) -> None:
    """Scan every file under a participant pack / project dir for secret shapes."""
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
        for m in SECRET_SHAPE_RE.finditer(text):
            # allow symbolic references (values like 'vault: figma/oauth' won't
            # match the long-literal pattern; bare key: <long-literal> does)
            errs.append(
                f"{f}: possible inline secret near '{m.group(0)[:30]}...' — packs "
                "reference secrets symbolically (secret_reference:), never inline"
            )
            break  # one report per file is enough to act on


def validate_project(project_dir: Path) -> list[str]:
    """Validate a .project/ directory: manifest, adoption pointer, participants."""
    errs: list[str] = []
    d = Path(project_dir)
    if not d.is_dir():
        return [f"project: directory not found: {d}"]
    manifest = d / "project.yaml"
    if not manifest.is_file():
        errs.append("project: missing project.yaml (run: contractctl init-project)")
        return errs
    try:
        pm = _load_yaml_file(manifest)
    except CTError as e:
        return [str(e)]

    if pm.get("schema") != "play-nice/project-v1":
        errs.append(
            f"project: schema must be 'play-nice/project-v1', got {pm.get('schema')!r}"
        )
    for key in ("id", "name"):
        if not pm.get(key):
            errs.append(f"project: missing required field '{key}'")
    own = pm.get("ownership")
    if not isinstance(own, dict) or not own.get("type"):
        errs.append("project: ownership.type is required")
    ctr = pm.get("contracts")
    if not isinstance(ctr, dict) or not ctr.get("manifest"):
        errs.append("project: contracts.manifest pointer is required")
    else:
        candidate = Path(d.parent / str(ctr["manifest"]))
        if not candidate.is_file() and (d / ctr["manifest"]).is_file():
            candidate = d / ctr["manifest"]
        if not candidate.is_file():
            errs.append(f"project: adoption manifest not found at {ctr['manifest']}")
    # README explains the model (required once, per framework rule 28)
    if not (d / "README.md").is_file():
        errs.append("project: missing README.md (durable-context explanation)")
    # secret hygiene
    _check_no_secrets(d, errs)
    # participants
    pdir = pm.get("participants", {})
    pdir_path = d / (
        pdir.get("directory", "participants")
        if isinstance(pdir, dict)
        else "participants"
    )
    if pdir_path.is_dir():
        errs.extend(validate_participants(pdir_path))
    return [e for e in errs if e]


def validate_participants(participants_dir: Path) -> list[str]:
    """Validate every participant pack under a participants/ directory.
    Enforces ID uniqueness per project."""
    errs: list[str] = []
    d = Path(participants_dir)
    if not d.is_dir():
        return [f"participants: directory not found: {d}"]
    seen_ids: dict[str, str] = {}
    packs = sorted(p for p in d.iterdir() if p.is_dir())
    if not packs:
        return []  # no participants is valid
    for pack in packs:
        errs.extend(validate_participant(pack, seen_ids))
    return errs


def validate_participant(
    pack_dir: Path, seen_ids: dict[str] | None = None
) -> list[str]:
    """Validate one participant pack directory (play-nice/participant-v1)."""
    errs: list[str] = []
    d = Path(pack_dir)
    if seen_ids is None:
        seen_ids = {}
    if not d.is_dir():
        return [f"participant: not a directory: {d}"]

    pman = d / "participant.yaml"
    if not pman.is_file():
        return [f"{d.name}: missing participant.yaml"]
    try:
        pm = _load_yaml_file(pman)
    except CTError as e:
        return [str(e)]

    pid = str(pm.get("id", ""))
    if pm.get("schema") != "play-nice/participant-v1":
        errs.append(
            f"{d.name}: schema must be 'play-nice/participant-v1', got {pm.get('schema')!r}"
        )
    if not pid:
        errs.append(f"{d.name}: missing required field 'id'")
    if pid and pid != d.name:
        errs.append(f"{d.name}: directory name must match participant id '{pid}'")
    if pid and seen_ids is not None:
        if pid in seen_ids:
            errs.append(
                f"{d.name}: duplicate participant id '{pid}' (also {seen_ids[pid]})"
            )
        else:
            seen_ids[pid] = d.name
    if not pm.get("name"):
        errs.append(f"{d.name}: missing required field 'name'")
    if pm.get("type") not in PARTICIPANT_TYPES:
        errs.append(
            f"{d.name}: invalid type {pm.get('type')!r} (valid: {sorted(PARTICIPANT_TYPES)})"
        )

    rel = pm.get("relationship")
    if not isinstance(rel, dict):
        errs.append(f"{d.name}: relationship block is required")
    else:
        if not rel.get("role"):
            errs.append(f"{d.name}: relationship.role is required")
        if rel.get("optional") is not True:
            errs.append(
                f"{d.name}: relationship.optional must be true — required participants are an explicit, project-level justified exception, not a pack-level default"
            )
        af = rel.get("authoritative_for")
        naf = rel.get("not_authoritative_for")
        if not isinstance(af, list) or not af:
            errs.append(
                f"{d.name}: relationship.authoritative_for list is required (may be narrow)"
            )
        if not isinstance(naf, list) or not naf:
            errs.append(
                f"{d.name}: relationship.not_authoritative_for is required and non-empty — no participant owns everything"
            )

    auth = pm.get("authentication")
    if isinstance(auth, dict):
        if (
            "secret_reference" not in auth
            or "token" in str(auth).lower()
            and "vault" not in str(auth)
        ):
            errs.append(
                f"{d.name}: authentication must use symbolic secret_reference, never values"
            )
    prov = pm.get("provenance")
    if (
        not isinstance(prov, dict)
        or not prov.get("supplied_by")
        or not prov.get("observed_at")
    ):
        errs.append(f"{d.name}: provenance (supplied_by, observed_at) is required")

    # capabilities (referenced or inline-required)
    caps_file = d / "capabilities.yaml"
    if caps_file.is_file():
        try:
            caps = _load_yaml_file(caps_file)
        except CTError as e:
            errs.append(str(e))
            caps = None
        if caps is not None:
            if caps.get("schema") != "play-nice/participant-capabilities-v1":
                errs.append(
                    f"{d.name}: capabilities.schema must be 'play-nice/participant-capabilities-v1'"
                )
            if caps.get("participant") != (pid or None):
                errs.append(f"{d.name}: capabilities.participant must match id '{pid}'")
            clist = caps.get("capabilities")
            if not isinstance(clist, list) or not clist:
                errs.append(
                    f"{d.name}: capabilities list is required and non-empty (use real discovered capabilities)"
                )
            else:
                for c in clist:
                    if (
                        not isinstance(c, dict)
                        or not c.get("id")
                        or not c.get("description")
                    ):
                        errs.append(
                            f"{d.name}: each capability needs 'id' and 'description'"
                        )
            lims = caps.get("limitations")
            if not isinstance(lims, list) or not lims:
                errs.append(f"{d.name}: at least one honest limitation is required")

    # references
    refs_file = d / "references.yaml"
    if refs_file.is_file():
        try:
            refs = _load_yaml_file(refs_file)
        except CTError as e:
            errs.append(str(e))
            refs = None
        if refs is not None:
            if refs.get("schema") != "play-nice/references-v1":
                errs.append(
                    f"{d.name}: references.schema must be 'play-nice/references-v1'"
                )
            if refs.get("participant") != (pid or None):
                errs.append(f"{d.name}: references.participant must match id '{pid}'")
            rlist = refs.get("references")
            if not isinstance(rlist, list) or not rlist:
                errs.append(f"{d.name}: references list is required and non-empty")
            else:
                for r in rlist:
                    if not isinstance(r, dict) or not r.get("id") or not r.get("type"):
                        errs.append(f"{d.name}: each reference needs 'id' and 'type'")
                        continue
                    if r.get("status") not in CANONICALITY_STATES:
                        errs.append(
                            f"{d.name}: reference '{r.get('id')}' status {r.get('status')!r} not in canonicality vocabulary {sorted(CANONICALITY_STATES)}"
                        )

    # secret hygiene across the whole pack
    _check_no_secrets(d, errs)
    return errs


PROJECT_INIT_FILES = {
    "project.yaml": """schema: play-nice/project-v1

id: {id}
name: {name}

purpose:
  summary: >
    (One or two sentences: what is this project for?)

ownership:
  type: human
  role: owner

contracts:
  manifest: {adoption_path}

participants:
  directory: participants

status:
  vocabulary: play-nice/status-v1
""",
    "README.md": """# Project Context

This directory contains durable context that helps humans, bots, tools, and
external services work with this project without rediscovering the same
information each session.

- **Contracts** define how participants behave together.
- **Project context** defines what this project is.
- **Participant packs** describe how optional collaborators interact with it.

Participant data may enrich project truth but does not silently replace it.
See the `project-context-and-participant-packs` contract in the Play-Nice
library for the full model. No secrets here — ever.
""",
    "CURRENT.md": """# Current State

(Where things stand right now: what works, what is in flight, what is next.)
""",
    "contracts/adoption.yaml": """# Play-Nice adoption manifest. Pin the revision to the commit you adopt.
schema: play-nice/adoption-v1
project: {id}
source:
  repository: rylee-bee-labs/play-nice-contracts
  revision: {revision}

always:
  - truth-and-evidence
  - status-and-state
  - ask-for-help

triggers:

notes: >-
  Start minimal; add trigger surfaces as the project grows.
""",
    "participants/README.md": """# Participants

Each subdirectory is a participant pack: a shared boundary document describing
how this project and one collaborator (service, agent, team, tool) work
together. See the `project-context-and-participant-packs` contract.

Create a pack with: participant.yaml, capabilities.yaml, interaction.md,
references.yaml — only the sections that earn their place.
""",
}


def init_project(
    target: Path,
    project_id: str,
    name: str,
    adoption_path: str = ".project/contracts/adoption.yaml",
) -> list[str]:
    """Create a minimal useful .project/ skeleton. No forest of empty dirs."""
    created: list[str] = []
    d = Path(target) / ".project"
    d.mkdir(parents=True, exist_ok=True)
    (d / "contracts").mkdir(exist_ok=True)
    (d / "participants").mkdir(exist_ok=True)
    # pin the manifest to this library checkout's revision so the scaffolded
    # adoption is valid on day one (an unpinned placeholder was a crash magnet)
    revision = library_revision() or "0000000"
    for rel, template in PROJECT_INIT_FILES.items():
        p = d / rel
        if p.is_file():
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            template.format(
                id=project_id,
                name=name,
                adoption_path=adoption_path,
                revision=revision,
            ),
            encoding="utf-8",
        )
        created.append(str(p))
    return created


# ---------------------------------------------------------------- commands


def cmd_list(_args) -> int:
    lib = load_library()
    errors = validate_library(lib)
    if errors:
        print("LIBRARY INVALID — fix before use:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    for c in sorted(lib, key=lambda x: x["front_matter"]["contract_id"]):
        fm = c["front_matter"]
        print(
            f"{fm['contract_id']:42s} {str(fm['version']):8s} {fm['status']:10s} {fm.get('layer', '?'):16s} {c['rel_path']}"
        )
    print(f"\n{len(lib)} contracts")
    return 0


def cmd_show(args) -> int:
    lib = load_library()
    want = canonical_id(
        args.contract_id, {c["front_matter"].get("contract_id") for c in lib}
    )
    if want != args.contract_id:
        print(f"note: '{args.contract_id}' is now part of '{want}'", file=sys.stderr)
    for c in lib:
        if c["front_matter"].get("contract_id") == want:
            print(c["text"], end="")
            return 0
    ids = sorted(c["front_matter"].get("contract_id", "") for c in lib)
    print(
        f"unknown contract: {args.contract_id} — run `contractctl list` to see all {len(lib)} ids",
        file=sys.stderr,
    )
    close = difflib.get_close_matches(args.contract_id, ids, n=3)
    if close:
        print(f"  closest: {', '.join(close)}", file=sys.stderr)
    return 1


def fix_hints(errors: list[str]) -> list[str]:
    """The command that fixes each class of validate error, in the order to run them."""
    hints: list[str] = []

    def add(h: str) -> None:
        if h not in hints:
            hints.append(h)

    for e in errors:
        if "but version is still" in e or "receipt did not rotate" in e:
            add("contractctl bump <id> --patch|--minor|--major --note \"...\" (sets version, receipt, changelog, index, lock)")
        elif e.startswith("changelog:") and "bullet" in e:
            add("add a bullet naming the contract under '## [Unreleased]' in CHANGELOG.md (or: contractctl bump <id> --minor --note \"...\")")
        elif e.startswith("index drift: '") and "row says" in e:
            add("contractctl index --write")
        elif e.startswith("index drift:"):
            add("add or remove the row by hand in CONTRACT_INDEX.md (purpose = the contract's rationale)")
        elif e.startswith("base:"):
            add("git fetch origin main, or pass --base <rev> that exists here")
    if any(h.startswith("contractctl bump") for h in hints):
        # bump also writes the changelog bullet, the index row and the lock
        return [h for h in hints if not (
            h.startswith("contractctl index") or h.startswith("add a bullet"))]
    if any(e.startswith("lock drift") or "contracts.lock.json missing" in e for e in errors):
        add("contractctl lock")
    return hints


def print_fix_hints(errors: list[str], stream=None) -> None:
    for h in fix_hints(errors):
        print(f"next: {h}", file=stream or sys.stdout)


BUMP_LEVELS = ("patch", "minor", "major")


def _bumped(version: str, level: str) -> str:
    ma, mi, pa = (int(x) for x in version.split("."))
    if level == "major":
        return f"{ma + 1}.0.0"
    if level == "minor":
        return f"{ma}.{mi + 1}.0"
    return f"{ma}.{mi}.{pa + 1}"


def receipts_ever_used(lib: list[dict]) -> set[str]:
    """Every contract receipt in the library now or anywhere in its Git history."""
    used = {r for c in lib for r in c["receipts"]}
    log = _git_out("log", "--all", "-p", "--format=", "--", "contracts")
    if log:
        used.update(RECEIPT_RE.findall(log))
    return used


def new_receipt(seed: str, used: set[str]) -> str:
    """A deterministic three-word receipt that has never been used."""
    words = _RECEIPT_WORDS
    n = len(words)
    for k in range(10000):
        i = int(hashlib.sha256(f"{seed}#{k}".encode("utf-8")).hexdigest()[:16], 16)
        trio = (words[i % n], words[(i >> 20) % n], words[(i >> 40) % n])
        word = "-".join(trio)
        if len(set(trio)) == 3 and word not in used:
            return word
    raise CTError("could not find an unused receipt word")


def add_unreleased_bullet(text: str, bullet: str) -> str:
    """Insert bullet under '### Changed' in the hand-written '## [Unreleased]'
    section of CHANGELOG.md, creating the subheading if needed."""
    m = re.search(r"^## \[Unreleased\][^\n]*\n", text, re.MULTILINE)
    if not m:
        raise CTError("CHANGELOG.md has no '## [Unreleased]' section")
    nxt = re.search(r"^## \[", text[m.end():], re.MULTILINE)
    section = text[m.end(): m.end() + nxt.start()] if nxt else text[m.end():]
    h = re.search(r"^### Changed[ \t]*\n", section, re.MULTILINE)
    if h:
        pos = m.end() + h.end()
        return text[:pos] + bullet + "\n" + text[pos:]
    return text[: m.end()] + "\n### Changed\n" + bullet + "\n" + text[m.end():]


def bump_contract(cid: str, level: str, note: str | None) -> tuple[str, list[str], list[str]]:
    """Version, receipt, changelog, index and lock for one edited contract.

    Judged against comparison_base(), so running it twice (or switching
    --patch to --minor) gives the same result instead of bumping twice.
    Returns (contract id, what it did, remaining validate errors)."""
    if level not in BUMP_LEVELS:
        raise CTError(f"level must be one of {BUMP_LEVELS}")
    lib = load_library()
    by_id = {c["front_matter"]["contract_id"]: c for c in lib}
    cid = canonical_id(cid, by_id)
    if cid not in by_id:
        raise CTError(f"unknown contract '{cid}'")
    c = by_id[cid]
    meaningful = level != "patch"
    if meaningful and not (note and note.strip()):
        raise CTError(f"--{level} is a meaningful change: say what changed with --note \"...\"")
    text = c["text"]
    cur_version = str(c["front_matter"]["version"])
    base, _err = comparison_base()
    prev = _git_out("show", f"{base}:{c['rel_path']}") if base else None
    from_version, from_receipt = cur_version, (c["receipts"][0] if c["receipts"] else None)
    if prev is not None:
        try:
            from_version = str(parse_front_matter(prev).get("version", cur_version))
        except CTError:
            pass
        old = RECEIPT_RE.findall(prev)
        from_receipt = old[0] if old else from_receipt
    target = _bumped(from_version, level)
    done: list[str] = []

    fm_end = text.index("\n---", 3)
    head, rest = text[:fm_end], text[fm_end:]
    head, n = re.subn(r"^version:[ \t]*\S+[ \t]*$", f"version: {target}", head, count=1, flags=re.MULTILINE)
    if n != 1:
        raise CTError(f"{c['rel_path']}: no 'version:' line in front matter")
    text = head + rest
    done.append(f"version {from_version} → {target}" + ("" if target != cur_version else " (already set)"))

    cur_receipt = c["receipts"][0] if c["receipts"] else None
    if meaningful and cur_receipt and cur_receipt == from_receipt:
        word = new_receipt(f"{cid}@{target}#{cur_receipt}", receipts_ever_used(lib))
        text = RECEIPT_RE.sub(f"<!-- contract-receipt: {word} -->", text, count=1)
        done.append("receipt rotated")
    elif meaningful:
        done.append("receipt already rotated")
    c["path"].write_text(text, encoding="utf-8", newline="\n")

    if note and note.strip():
        cl = CHANGELOG_FILE.read_text(encoding="utf-8")
        base_cl = _git_out("show", f"{base}:CHANGELOG.md") if base else None
        if base_cl is not None and cl != base_cl and f"**{cid}**" in cl and f"**{cid}**" not in base_cl:
            done.append("CHANGELOG.md already has a new bullet for it")
        else:
            bullet = f"- **{cid}** {from_version} → {target}: {note.strip()}"
            CHANGELOG_FILE.write_text(add_unreleased_bullet(cl, bullet), encoding="utf-8", newline="\n")
            done.append("CHANGELOG.md bullet added under [Unreleased]")

    lib = load_library()
    details = index_drift_details(lib)
    if details:
        idx = INDEX_FILE.read_text(encoding="utf-8")
        for rcid, _gv, _gs, wv, ws in details:
            idx, _n = rewrite_index_row(idx, rcid, wv, ws)
        INDEX_FILE.write_text(idx, encoding="utf-8", newline="\n")
        done.append("CONTRACT_INDEX.md row updated")
    errors = validate_library(load_library())
    if not errors:
        write_lock()
        done.append("contracts.lock.json regenerated")
    return cid, done, errors


def cmd_bump(args) -> int:
    level = "major" if args.major else "minor" if args.minor else "patch"
    try:
        cid, done, errors = bump_contract(args.contract_id, level, args.note)
    except CTError as e:
        print(f"BUMP: FAILED — {e}", file=sys.stderr)
        return 1
    print(f"BUMP: {cid} ({level})")
    for d in done:
        print(f"  - {d}")
    if errors:
        print("not locked; fix these first:")
        for e in errors:
            print(f"  - {e}")
        print_fix_hints(errors)
        return 1
    if cid == "floor":
        print("next: playnice start .  (rewrites this repo's AGENTS.md block and badge)")
        print("next: update the floor proof-line examples the tests name, then ./tools/check.sh")
    else:
        print("next: ./tools/check.sh")
    return 0


def cmd_validate(args) -> int:
    if getattr(args, "base", None):
        os.environ[BASE_ENV] = args.base
    lib = load_library()
    errors = validate_library(lib)
    lock_errors = (
        verify_lock(lib)
        if LOCKFILE.is_file()
        else ["contracts.lock.json missing (run lock)"]
    )
    errors = errors + lock_errors
    if errors:
        print(f"INVALID — {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        print_fix_hints(errors)
        return 1
    print(
        f"VALID — {len(lib)} contracts; lockfile verified; receipts unique; index in sync"
    )
    return 0


def cmd_lock(_args) -> int:
    lib = load_library()
    errors = validate_library(lib)
    if errors:
        print("cannot lock an invalid library:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print_fix_hints(errors, sys.stderr)
        return 1
    lock = write_lock()
    print(
        f"wrote contracts.lock.json ({len(lock['contracts'])} contracts); bundle receipt: {bundle_receipt(lock)}"
    )
    return 0


# ---------------------------------------------------------------- diff (revision comparison)


def _rev_or_fail(rev: str) -> str | None:
    """Resolve a revision to a full SHA against the library checkout."""
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "--verify", f"{rev}^{{commit}}"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if r.returncode == 0 and GITSHA_RE.match(r.stdout.strip()):
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def _contract_entries_at_rev(repo: Path, rev: str) -> dict[str, dict] | None:
    """Parse every contract's front matter + receipt from a git revision.

    Returns {id: {version, status, receipt, path}} or None when the revision
    or the contracts/ tree cannot be read.
    """
    out = {}
    try:
        listing = subprocess.run(
            ["git", "-C", str(repo), "ls-tree", "-r", "--name-only", rev, "--", "contracts/"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if listing.returncode != 0:
            return None
        paths = [ln for ln in listing.stdout.splitlines() if ln.endswith(".md")]
        for p in paths:
            blob = subprocess.run(
                ["git", "-C", str(repo), "show", f"{rev}:{p}"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if blob.returncode != 0:
                return None
            try:
                fm = parse_front_matter(blob.stdout)
            except CTError:
                continue
            cid = str(fm.get("contract_id", ""))
            if not cid:
                continue
            receipts = RECEIPT_RE.findall(blob.stdout)
            out[cid] = {
                "version": str(fm.get("version", "")),
                "status": str(fm.get("status", "")),
                "receipt": receipts[0] if receipts else None,
                "path": p,
            }
        return out
    except (OSError, subprocess.TimeoutExpired):
        return None


def _beyond_patch(prev: str, cur: str) -> bool:
    try:
        pm, pd, pp = (int(x) for x in prev.split("."))
        cm, cd, cp = (int(x) for x in cur.split("."))
    except ValueError:
        return True  # unparseable versions: treat conservatively as meaningful
    return (cm, cd) != (pm, pd)


def compute_contract_diff(from_rev: str, to_rev: str) -> dict:
    """Deterministic comparison of the normative contract set between two
    library revisions. Answers: what changed, which changes are meaningful
    (MINOR/MAJOR ⇒ rotated receipt), and whether a consumer manifest's
    always-set is affected."""
    repo = REPO_ROOT
    a = _contract_entries_at_rev(repo, from_rev)
    b = _contract_entries_at_rev(repo, to_rev)
    result = {
        "from": from_rev,
        "to": to_rev,
        "added": [],
        "removed": [],
        "changed": [],
        "unchanged_count": 0,
        "meaningful_changes": 0,  # MINOR/MAJOR (receipt rotated or version beyond patch)
        "errors": [],
    }
    if a is None or b is None:
        result["errors"].append(
            "revisions unavailable locally; fetch them first (contractctl diff "
            "never guesses: UNKNOWN stays UNKNOWN)"
        )
        return result
    for cid in sorted(set(b) - set(a)):
        result["added"].append({"id": cid, **b[cid]})
    for cid in sorted(set(a) - set(b)):
        result["removed"].append({"id": cid, **a[cid]})
    for cid in sorted(set(a) & set(b)):
        ea, eb = a[cid], b[cid]
        if ea == eb:
            result["unchanged_count"] += 1
            continue
        meaningful = ea["receipt"] != eb["receipt"] or _beyond_patch(
            ea["version"], eb["version"]
        )
        result["changed"].append(
            {
                "id": cid,
                "from_version": ea["version"],
                "to_version": eb["version"],
                "from_status": ea["status"],
                "to_status": eb["status"],
                "receipt_rotated": ea["receipt"] != eb["receipt"],
                "meaningful": meaningful,
            }
        )
        if meaningful:
            result["meaningful_changes"] += 1
    return result


def _manifest_always_ids(manifest_path: Path | None) -> list[str]:
    if manifest_path is None or not manifest_path.is_file():
        return []
    try:
        m = load_adoption(manifest_path)
    except CTError:
        return []
    return [str(c) for c in (m.get("always") or [])]


def cmd_diff(args) -> int:
    """Compare the contract set between two library revisions."""
    from_rev = _rev_or_fail(args.from_rev)
    to_rev = _rev_or_fail(args.to_rev)
    if from_rev is None or to_rev is None:
        missing = args.from_rev if from_rev is None else args.to_rev
        print(f"DIFF: UNKNOWN — revision not resolvable locally: {missing}", file=sys.stderr)
        print("  fetch it into the library checkout first (fail closed)", file=sys.stderr)
        return 2
    d = compute_contract_diff(from_rev, to_rev)
    if d["errors"]:
        for e in d["errors"]:
            print(f"DIFF: {e}", file=sys.stderr)
        return 2
    if args.json_output:
        print(json.dumps(d, indent=2, sort_keys=False))
        return 0
    print(f"CONTRACT DIFF {from_rev[:12]} → {to_rev[:12]}")
    print(f"  unchanged: {d['unchanged_count']}")
    for e in d["added"]:
        print(f"  added:     {e['id']} @ {e['version']} ({e['status']})")
    for e in d["removed"]:
        print(f"  removed:   {e['id']} @ {e['version']} ({e['status']})")
    for e in d["changed"]:
        rot = ", receipt rotated" if e["receipt_rotated"] else ""
        kind = "MEANINGFUL" if e["meaningful"] else "clarification"
        print(
            f"  changed:   {e['id']} {e['from_version']} → {e['to_version']} "
            f"[{kind}{rot}]"
        )
    if d["meaningful_changes"] == 0 and not d["added"] and not d["removed"]:
        print("  → compatible: only clarifications (or nothing) since your pin")
    always = _manifest_always_ids(Path(args.manifest) if args.manifest else None)
    if always:
        touched = (
            {e["id"] for e in d["changed"]}
            | {e["id"] for e in d["added"]}
            | {e["id"] for e in d["removed"]}
        )
        hit = sorted(touched & set(always))
        if hit:
            print(f"  affects your always-set: {', '.join(hit)} — re-attest required")
        else:
            print("  your always-set is unaffected by this diff")
    return 0


# Base contract sets by participant role, used when a folder carries no
# adoption manifest (v2: `resolve` must answer, not error — the manifest
# stays optional). Floor and library-trigger matches are added on top.
ROLE_BASE_SETS = {
    "agent": [
        "agent-behavior",
        "bounded-work",
        "handoff-and-continuity",
        "testing-and-evidence",
        "contract-proof",
    ],
    "human": [
        "accessibility",
        "attention-and-quiet",
        "depth-on-demand",
        "plain-language",
        "what-why-next",
    ],
    "service": [
        "api",
        "calling-other-services",
        "events-and-caching",
        "status-and-state",
        "versions-and-discovery",
    ],
}


def cmd_resolve(args) -> int:
    explicit = args.manifest is not None
    manifest = Path(args.manifest) if explicit else discover_manifest()
    if manifest.is_file():
        m = load_adoption(manifest)
    elif explicit:
        # explicitly named but missing: still fail closed (a typo is not "none")
        m = load_adoption(manifest)
    else:
        print(
            "no adoption manifest: resolved from the library defaults",
            file=sys.stderr if getattr(args, "json", False) else sys.stdout,
        )
        m = {"always": list(ROLE_BASE_SETS[args.role]), "triggers": {}}
    res = resolve_set(m, args.task, (args.tag or []))
    if getattr(args, "json", False):
        print(
            json.dumps(
                {
                    "schema": "play-nice/resolve-v1",
                    "task": args.task,
                    "tags": sorted({str(t).lower() for t in (args.tag or [])}),
                    "manifest": str(manifest) if manifest.is_file() else None,
                    "library_size": res["library_size"],
                    "contracts": [
                        {"id": cid, "reasons": res["reasons"].get(cid, [])}
                        for cid in sorted(res["selected"])
                    ],
                    "errors": res["errors"],
                },
                indent=2,
            )
        )
        return 1 if res["errors"] else 0
    if res["errors"]:
        print("resolution errors:", file=sys.stderr)
        for e in res["errors"]:
            print(f"  - {e}", file=sys.stderr)
        return 1
    if (args.tag or []) and not (m.get("triggers") or {}):
        print(
            f"note: no trigger surfaces defined in {manifest}; --tag had no effect"
        )
    groups: dict[str, list[str]] = {}
    for cid, why in res["selected"].items():
        groups.setdefault(why, []).append(cid)
    for why in sorted(groups):
        print(f"{why.upper()}")
        for cid in sorted(groups[why]):
            print(f"  {cid}")
        print()
    print(
        f"resolved {len(res['selected'])} of {res['library_size']} contracts for task: {args.task!r}"
    )
    return 0


def cmd_attest(args) -> int:
    manifest = Path(args.manifest)
    impact = _read_impact_args(args)
    revision = args.revision or library_revision()
    out = make_attestation(
        manifest,
        args.task,
        impact,
        revision,
        task_tags=(getattr(args, "tag", None) or []),
    )
    print(out)
    if "CONTRACT GATE: PASS" in str(out):
        print()
        print("Next: activate the operational commitment before mutating work:")
        print(
            f"  contractctl commit --manifest {manifest} --task {shlex.quote(args.task)} "
            "--impact id=sentence ... (quote each value, or use --impact-file <file>)"
        )
    return 0 if "CONTRACT GATE: PASS" in str(out) else 2


def _read_impact_args(args) -> dict[str, str]:
    impact: dict[str, str] = {}
    for item in getattr(args, "impact", None) or []:
        if "=" not in item:
            raise CTError(f"--impact expects contract_id=sentence, got {item!r}")
        k, v = item.split("=", 1)
        impact[k.strip()] = v.strip()
    impact_file = getattr(args, "impact_file", None)
    if impact_file:
        for line in Path(impact_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                raise CTError(f"impact file line needs 'id = sentence': {line!r}")
            k, v = line.split("=", 1)
            impact[k.strip()] = v.strip()
    return impact


def cmd_commit(args) -> int:
    manifest = Path(args.manifest)
    impact = _read_impact_args(args)
    revision = args.revision or library_revision()
    role = "worker" if args.worker else args.role
    try:
        artifact, text = build_commitment(
            manifest,
            args.task,
            impact,
            revision,
            role=role,
            parent_bundle=args.parent_bundle,
            worker=args.worker,
            task_tags=(getattr(args, "tag", None) or []),
        )
    except CTFreshnessError as e:
        staleish = e.state in ("BEHIND", "DIVERGED")
        state = "STALE" if staleish else "INACTIVE"
        print(f"REMOTE FRESHNESS: {e.state}")
        print(f"CONTRACT COMMITMENT: {state}")
        if e.detail:
            print(f"  - {e.detail}")
        if staleish:
            print("  - fetch/update → resolve → read → attest → commit again")
        else:
            print(
                "  - freshness not established; mutating work stays blocked (fail closed)"
            )
        return 2
    except CTError as e:
        print(
            f"CONTRACT GATE: BLOCKED\nCONTRACT COMMITMENT: INACTIVE\n\n{e}",
            file=sys.stderr,
        )
        if isinstance(e, CTManifestMissing):
            print_missing_manifest_hint(e)
        return 2
    out = (
        Path(args.output)
        if args.output
        else default_artifact_path(role, args.task, manifest_path=manifest)
    )
    if args.text_only:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
    else:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(text)
    print()
    print(f"session artifact written: {out}")
    return 0


def cmd_session_status(args) -> int:
    manifest = Path(args.manifest) if args.manifest else None
    artifact_path = Path(args.artifact) if getattr(args, "artifact", None) else None
    role = getattr(args, "role", "session") or "session"
    task = getattr(args, "task", "") or ""
    summary, problems = session_status(manifest, artifact_path, role=role, task=task)
    print(summary)
    return 0 if not problems else 1


def cmd_validate_question(args) -> int:
    errors = validate_question(Path(args.question))
    if errors:
        print(f"QUESTION INVALID — {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    data = json.loads(Path(args.question).read_text(encoding="utf-8"))
    print(
        f"QUESTION VALID — {data.get('schema')} ({data.get('question_id', data.get('request_id', '?'))}), status={data.get('status')}, blocking={data.get('blocking')}"
    )
    return 0


def _resolve_project_dir(path: str) -> Path:
    p = Path(path)
    if p.name == ".project" or (p / "project.yaml").is_file():
        return p
    candidate = p / ".project"
    if candidate.is_dir():
        return candidate
    return p  # let validate report the miss clearly


def cmd_init_project(args) -> int:
    created = init_project(Path(args.target), args.id, args.name)
    if created:
        print("created:")
        for c in created:
            print(f"  {c}")
        print(
            "\nnext: edit project.yaml purpose; pin adoption revision; add participant packs as needed"
        )
        return 0
    print(".project/ already initialized (no files changed)")
    return 0


def cmd_project_validate(args) -> int:
    d = _resolve_project_dir(args.path)
    errors = validate_project(d)
    if errors:
        print(f"PROJECT INVALID — {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    pm = _load_yaml_file(d / "project.yaml")
    packs = (
        sorted(p.name for p in (d / "participants").iterdir() if p.is_dir())
        if (d / "participants").is_dir()
        else []
    )
    print(
        f"PROJECT VALID — {pm.get('id')} ({pm.get('name')}): {len(packs)} participant pack(s)"
    )
    for name in packs:
        print(f"  - {name}")
    return 0


def cmd_participant_validate(args) -> int:
    errors = validate_participant(Path(args.path))
    if errors:
        print(f"PARTICIPANT INVALID — {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    pm = _load_yaml_file(Path(args.path) / "participant.yaml")
    af = pm.get("relationship", {}).get("authoritative_for", [])
    naf = pm.get("relationship", {}).get("not_authoritative_for", [])
    print(f"PARTICIPANT VALID — {pm.get('id')} ({pm.get('type')})")
    print(f"  authoritative for: {', '.join(af)}")
    print(f"  NOT authoritative for: {', '.join(naf)}")
    return 0


def cmd_participant_list(args) -> int:
    d = _resolve_project_dir(args.path)
    pdir = d / "participants"
    if not pdir.is_dir():
        print("no participants directory")
        return 0
    packs = sorted(p for p in pdir.iterdir() if p.is_dir())
    if not packs:
        print("no participant packs")
        return 0
    for pack in packs:
        pman = pack / "participant.yaml"
        if not pman.is_file():
            print(f"{pack.name}: (missing participant.yaml)")
            continue
        try:
            pm = _load_yaml_file(pman)
        except CTError:
            print(f"{pack.name}: (unparseable manifest)")
            continue
        rel = pm.get("relationship", {})
        help_ = pm.get("help", {})
        pid = str(pm.get("id", pack.name))
        ptype = str(pm.get("type", "?"))
        prole = str(rel.get("role", "?"))
        print(f"{pid:20s} {ptype:18s} role={prole}")
        if isinstance(help_, dict) and help_.get("can_answer"):
            print(f"{'':20s} can answer: {', '.join(help_['can_answer'])}")
    return 0


def cmd_verify_attestation(args) -> int:
    att_path = Path(args.attestation)
    manifest = Path(args.manifest) if args.manifest else None
    errors = verify_attestation(att_path, manifest)
    if errors:
        print(f"ATTESTATION FAILED — {len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(
        "ATTESTATION VERIFIED — receipts, hashes, versions, and bundle match the current library"
    )
    return 0


def cmd_adopt(args) -> int:
    mp = Path(args.manifest)
    if not mp.is_file():
        # report a missing manifest once (both checkers used to report it),
        # and point at the command that creates it
        print("ADOPTION INVALID — 1 problem")
        print(
            f"  - no adoption manifest at {mp} — this folder has not adopted Play-Nice yet."
        )
        print(f"  next: contractctl init-adoption --manifest {mp}")
        return 1
    errors = validate_adoption_manifest(mp) + check_stale_pin(mp)
    errors = list(dict.fromkeys(errors))  # dedupe; a real problem, stated once
    if errors:
        noun = "problem" if len(errors) == 1 else "problems"
        print(f"ADOPTION INVALID — {len(errors)} {noun}:")
        for e in errors:
            print(f"  - {e}")
        return 1
    m = load_adoption(Path(args.manifest))
    print(
        f"ADOPTION VALID — {m.get('project', 'unnamed')}: always={len(m.get('always', []))} triggers={len(m.get('triggers', {}))}"
    )
    return 0


# ---------------------------------------------------------------- onboard

ROLE_KEYWORDS = {
    "orchestrator": {"agents", "orchestration", "project-management", "delegation"},
    "worker": {"agents", "automation", "engineering"},
    "ui": {"ui", "web", "product", "design"},
    "cli": {"cli", "tools"},
    "service": {"api", "infrastructure", "operations", "integration"},
    "human": {"humans", "product", "ui"},
    "maintainer": {"contracts", "governance", "documentation", "engineering", "agents"},
}

ROLE_HIGH_PRIORITY = {
    "orchestrator": [
        "play-nice-together",
        "truth-and-evidence",
        "ask-for-help",
        "orchestration",
        "model-routing",
        "bounded-work",
        "handoff",
        "contract-attestation",
        "agent-behavior",
        "worker-contract",
        "review-and-integration",
        "participation-and-contribution",
        "mutual-contribution",
        "collaborative-good-faith",
    ],
    "worker": [
        "play-nice-together",
        "truth-and-evidence",
        "ask-for-help",
        "agent-behavior",
        "bounded-work",
        "handoff",
        "worker-contract",
        "contract-attestation",
        "testing-and-verification",
    ],
    "ui": [
        "play-nice-together",
        "accessibility-floor",
        "human-reliability",
        "attention-and-focus",
        "quiet-when-healthy",
        "copy-and-language",
        "themes-and-personalization",
        "motion-and-feedback",
        "migraine-and-sensory-safety",
        "low-vision-and-reflow",
        "visual-fidelity-and-composition",
        "web-ui",
    ],
    "cli": [
        "play-nice-together",
        "truth-and-evidence",
        "cli",
        "machine-readable-output",
        "human-and-machine-parity",
        "failure-and-degradation",
        "explicit-state",
    ],
    "service": [
        "play-nice-together",
        "truth-and-evidence",
        "api",
        "friendly-api-client",
        "idempotency",
        "failure-and-degradation",
        "authorization",
        "authentication",
        "secrets",
        "external-mutations",
        "versioning-and-compatibility",
    ],
    "human": [
        "play-nice-together",
        "human-reliability",
        "ask-for-help",
        "attention-and-focus",
        "progress-and-closure",
        "collaborative-good-faith",
        "copy-and-language",
    ],
    "maintainer": [
        "play-nice-together",
        "truth-and-evidence",
        "contract-attestation",
        "provenance-and-audit",
        "stable-truth-replaceable-machinery",
        "documentation-and-continuity",
        "deterministic-first",
        "testing-and-verification",
        "versioning-and-compatibility",
        "git-and-worktrees",
        "dependency-discipline",
        "search-before-inventing",
        "public-private-boundaries",
    ],
}


def cmd_onboard(args) -> int:
    lib = load_library()
    errors = validate_library(lib)
    if errors:
        print("LIBRARY INVALID — fix before onboarding:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    role = args.role
    if role == "agent":
        # 'agent' is an accepted alias for 'worker': same reading plan, and
        # the role never grants or removes permissions either way.
        role = "worker"
    keywords = ROLE_KEYWORDS.get(role, set())
    # The priority table predates the v2 pack merge; map old ids through
    # aliases.json so role lists name the contracts that actually exist.
    lib_ids = {c["front_matter"]["contract_id"] for c in lib}
    high_ids = {canonical_id(cid, lib_ids) for cid in ROLE_HIGH_PRIORITY.get(role, [])}

    # Classify: high-priority (explicit list) vs applicable (by metadata match) vs remaining
    high = []
    applicable = []
    remaining = []

    for c in sorted(lib, key=lambda x: x["front_matter"]["contract_id"]):
        fm = c["front_matter"]
        cid = fm["contract_id"]
        applies = set(fm.get("applies") or [])
        triggers = set(fm.get("triggers") or [])
        meta = applies | triggers

        if cid in high_ids:
            high.append(c)
        elif keywords & meta or "always" in triggers or "always-applicable" in triggers:
            applicable.append(c)
        else:
            remaining.append(c)

    # Promote always-triggered from applicable to high if not already there
    for c in list(applicable):
        triggers = set(c["front_matter"].get("triggers") or [])
        if "always" in triggers or "always-applicable" in triggers:
            if c not in high:
                high.append(c)
                applicable.remove(c)

    if getattr(args, "json_output", False):
        out = {
            "role": role,
            "first": "contracts/everyone/FLOOR.md",
            "high_priority": [
                {
                    "id": c["front_matter"]["contract_id"],
                    "version": str(c["front_matter"]["version"]),
                    "title": c["front_matter"]["title"],
                }
                for c in high
            ],
            "applicable": [
                {
                    "id": c["front_matter"]["contract_id"],
                    "version": str(c["front_matter"]["version"]),
                    "title": c["front_matter"]["title"],
                }
                for c in applicable
            ],
            "remaining": [
                {
                    "id": c["front_matter"]["contract_id"],
                    "version": str(c["front_matter"]["version"]),
                    "title": c["front_matter"]["title"],
                }
                for c in remaining
            ],
            "note": "This is an onboarding plan, not an attestation. Reading order is a suggestion; all contracts remain applicable where their metadata matches your work.",
        }
        print(json.dumps(out, indent=2))
        return 0

    # Human-readable output
    lib_ver = library_version()
    print(f"PLAY-NICE ONBOARDING — role: {role}")
    print(f"library: {lib_ver} ({len(lib)} contracts)")
    print()

    print("=== FIRST: READ THE FLOOR ===")
    print()
    print("  contracts/everyone/FLOOR.md  (one page; applies to everyone)")
    print()

    print(f"=== HIGH-PRIORITY CONTRACTS FOR {role.upper()} ({len(high)}) ===")
    print()
    print("  Read these first. They are most likely to shape your work.")
    print()
    for i, c in enumerate(high, 1):
        fm = c["front_matter"]
        print(f"  {i:2d}. {fm['contract_id']}@{fm['version']}  — {fm['title']}")
        print(f"      {c['rel_path']}")
    print()

    if applicable:
        print(f"=== ALSO APPLICABLE ({len(applicable)}) ===")
        print()
        print("  These apply based on your role's triggers and metadata.")
        print()
        for c in applicable:
            fm = c["front_matter"]
            print(f"  - {fm['contract_id']}@{fm['version']}  — {fm['title']}")
        print()

    if remaining:
        print(f"=== REMAINING ({len(remaining)}) ===")
        print()
        print("  These may apply to specific tasks. Consult the contract index.")
        print()
        for c in remaining:
            fm = c["front_matter"]
            print(f"  - {fm['contract_id']}@{fm['version']}  — {fm['title']}")
        print()

    print("=== NEXT ===")
    print()
    print("  Start your handoff with the proof line from contracts/work/CONTRACT_PROOF.md:")
    print("    Play-Nice floor <version> · receipt <word> · read <ids you read>")
    print("  Check it with: playnice verify \"<that line>\"")
    print()
    print("  This tool prepares onboarding; you perform it.")
    print(
        "  A role determines reading order and emphasis, not permission or exemptions."
    )
    print("  All contracts remain applicable where their metadata matches your work.")

    return 0


def _project_manifest_in_tree() -> Path | None:
    """Adoption manifest of the CURRENT working tree, if this project adopted.

    Both documented locations count: `.contracts/adoption.yaml` and the
    `.project/contracts/adoption.yaml` written by init-project.
    """
    for cand in (
        Path(".contracts") / "adoption.yaml",
        Path(".project") / "contracts" / "adoption.yaml",
    ):
        if cand.is_file():
            return cand
    return None


def cmd_status(_args) -> int:
    lib = load_library()
    errors = validate_library(lib)
    n_canon = sum(1 for c in lib if c["front_matter"].get("status") == "canonical")
    lock_ok = not verify_lock(lib) if LOCKFILE.is_file() else False
    project_manifest = _project_manifest_in_tree()
    if project_manifest is None:
        # a green PASS here is the LIBRARY's health, not this project's state
        print("LIBRARY HEALTH (the installed Play-Nice library — not this project):")
    print(f"contracts: {len(lib)} ({n_canon} canonical)")
    print(f"validate:  {'PASS' if not errors else 'FAIL (' + str(len(errors)) + ')'}")
    print(f"lockfile:  {'VERIFIED' if lock_ok else 'MISSING/DRIFTED'}")
    print(f"revision:  {library_revision()}")
    if project_manifest is None:
        print("this project: no adoption manifest — run contractctl init-adoption")
    return 0 if (not errors and lock_ok) else 1


def _print_freshness(fr: dict) -> None:
    print(f"REMOTE FRESHNESS: {fr['status']}")
    print(
        f"  policy: {fr['policy']} ({'enforced' if fr['enforced'] else 'not enforced at commit'})"
    )
    print(f"  source: {fr['repository']} {fr['ref']}")
    if fr.get("remote_revision"):
        print(f"  remote_revision: {fr['remote_revision']}")
    print(f"  adopted_revision: {fr['adopted_revision']}")
    print(f"  library_revision: {fr['library_revision']}")
    if fr.get("detail"):
        print(f"  detail: {fr['detail']}")
    if fr.get("equivalence"):
        eq = fr["equivalence"]
        print(f"  equivalence: {eq['rule']}")
    if fr.get("equivalence_note"):
        print(f"  equivalence_not_met: {fr['equivalence_note']}")


def cmd_freshness(args) -> int:
    """Deterministic remote freshness check (the first preflight stage)."""
    manifest = Path(args.manifest)
    try:
        fr = check_freshness(manifest)
    except CTError as e:
        print(f"error: {e}", file=sys.stderr)
        if isinstance(e, CTManifestMissing):
            print_missing_manifest_hint(e)
        return 2
    if args.json_output:
        print(json.dumps({k: fr[k] for k in sorted(fr)}, sort_keys=True, indent=2))
    else:
        _print_freshness(fr)
    if fr["status"] == "CURRENT":
        return 0
    return 1 if fr["status"] in ("BEHIND", "DIVERGED") else 2


def cmd_sync(args) -> int:
    """Refresh the adoption pin to the authoritative remote revision.

    update: automatic — rewrites source.revision when the remote moved, then
    demands a fresh resolve → read → attest → commit cycle.
    update: review — detects the change, blocks mutation, and prints the
    required review path. Never silently adopts newer contracts.
    """
    manifest = Path(args.manifest)
    fr = check_freshness(manifest)
    _print_freshness(fr)
    cfg = freshness_config(load_adoption(manifest))
    if fr["status"] == "CURRENT":
        print("SYNC: NOTHING TO DO (REMOTE FRESHNESS: CURRENT)")
        return 0
    if fr["status"] not in ("BEHIND", "DIVERGED"):
        print(f"SYNC: BLOCKED — REMOTE FRESHNESS: {fr['status']} (fail closed)")
        return 2
    if cfg["update"] == "review":
        print(
            "SYNC: REVIEW REQUIRED — update: review never auto-adopts newer contracts."
        )
        print("  1. read what changed at the remote revision")
        print(f"  2. if accepted: pin source.revision to {fr.get('remote_revision')}")
        print("  3. resolve → read → attest → commit again (fresh commitment required)")
        return 2
    remote = fr.get("remote_revision")
    text = manifest.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r"(revision:\s*)([0-9a-f]{7,64})",
        rf"\g<1>{remote}",
        text,
        count=1,
    )
    if n != 1:
        print(
            "SYNC: FAILED — could not rewrite source.revision deterministically",
            file=sys.stderr,
        )
        return 2
    manifest.write_text(new_text, encoding="utf-8")
    print(f"SYNC: pin updated to {remote}")
    print(
        "SYNC: contracts are STALE — resolve → read → attest → commit required before mutation"
    )
    return 0


def cmd_scan(args) -> int:
    """Public-boundary scan, reusable by the library AND its adopters."""
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"SCAN: UNKNOWN — not a directory: {root}", file=sys.stderr)
        return 2
    hits = scan_surface(root)
    if getattr(args, "json_output", False):
        print(json.dumps({"root": str(root), "hits": hits, "clean": not hits}, indent=2))
    elif not hits:
        print(f"SCAN: CLEAN — {root} has no banned public-boundary shapes")
    else:
        print(f"SCAN: {len(hits)} finding(s) in {root} (values redacted):")
        for h in hits:
            print(f"  - {h['path']}: {h['pattern']}")
    return 1 if hits else 0


def cmd_index(args) -> int:
    """Report or repair CONTRACT_INDEX.md version/status columns.

    The index is derived data (see Stable Truth, Replaceable Machinery): the
    canonical files are the source, the index routes. This command makes the
    version/status columns auto-repairable so that drift class cannot recur.
    Membership drift (a missing or unknown row) is not auto-generated — a
    human/agent adds the row once, with its purpose line.
    """
    lib = load_library()
    errors = validate_library(lib)
    details = index_drift_details(lib)
    other = [
        e for e in errors
        if not (e.startswith("index drift: '") and "row says" in e)
    ]
    if not args.write:
        if not details:
            print("INDEX: version/status columns in sync with canonical")
            return 0 if not errors else 1
        print(f"INDEX DRIFT — {len(details)} row(s) disagree with canonical:")
        for cid, gv, gs, wv, ws in details:
            print(f"  - {cid}: {gv}/{gs} → {wv}/{ws}")
        print("  repair: contractctl index --write")
        return 1
    if other:
        print("cannot rewrite an index with unresolved errors:", file=sys.stderr)
        for e in other:
            print(f"  - {e}", file=sys.stderr)
        print_fix_hints(other, sys.stderr)
        return 1
    if not details:
        print("INDEX: already in sync (no changes)")
        return 0
    text = INDEX_FILE.read_text(encoding="utf-8")
    for cid, _gv, _gs, wv, ws in details:
        text, n = rewrite_index_row(text, cid, wv, ws)
        if n != 1:
            print(
                f"INDEX: FAILED — could not rewrite row for '{cid}' deterministically",
                file=sys.stderr,
            )
            return 2
    INDEX_FILE.write_text(text, encoding="utf-8", newline="\n")
    print(f"INDEX: repaired {len(details)} row(s) from canonical")
    for cid, gv, gs, wv, ws in details:
        print(f"  - {cid}: {gv}/{gs} → {wv}/{ws}")
    return 0


ADOPTION_ALWAYS_FLOOR = (
    "truth-and-evidence",
    "status-and-state",
    "recovery-and-history",
    "ask-for-help",
)


def _default_repository() -> str:
    own = REPO_ROOT / ".contracts" / "adoption.yaml"
    if own.is_file():
        try:
            return str((load_adoption(own).get("source") or {}).get("repository", "") or "")
        except CTError:
            pass
    return "rylee-bee-labs/play-nice-contracts"


def render_adoption_manifest(
    *,
    repository: str,
    revision: str,
    project: str,
    policy: str = "require-current",
    ref: str = "main",
    update: str = "review",
) -> str:
    """A minimal, schema-valid adoption manifest. `update: review` is the
    default because it never silently adopts newer contracts."""
    lines = [
        "schema: play-nice/adoption-v1",
        f"project: {project}",
        "source:",
        f"  repository: {repository}",
        f"  revision: {revision}",
        "always:",
    ]
    lines += [f"  - {cid}" for cid in ADOPTION_ALWAYS_FLOOR]
    lines += [
        "freshness:",
        f"  policy: {policy}",
        f"  ref: {ref}",
        f"  update: {update}",
    ]
    return "\n".join(lines) + "\n"


def cmd_init_adoption(args) -> int:
    """Seed a consumer adoption manifest instead of copying an example."""
    target = Path(args.manifest)
    if target.exists() and not args.force:
        print(
            f"INIT-ADOPTION: refusing to overwrite {target} (use --force)",
            file=sys.stderr,
        )
        return 2
    errors = validate_library(load_library())
    if errors:
        print(
            "cannot seed an adoption from an invalid library "
            "(run: contractctl validate):",
            file=sys.stderr,
        )
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    revision = args.revision or library_revision()
    repository = args.repository or _default_repository()
    project = args.project or Path.cwd().name
    text = render_adoption_manifest(
        repository=repository,
        revision=revision,
        project=project,
        policy=args.policy,
        update=args.update,
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    try:
        load_adoption(target)  # self-check: fail closed on our own output
    except CTError as e:
        target.unlink(missing_ok=True)
        print(f"INIT-ADOPTION: generated manifest failed validation: {e}", file=sys.stderr)
        return 1
    print(f"wrote {target}")
    print(f"  repository: {repository}")
    print(f"  revision:   {revision[:12]} (pinned)")
    print(f"  policy:     {args.policy} (update: {args.update})")
    print("next:")
    print(f'  contractctl resolve --manifest {target} --task "your task"')
    print(f'  contractctl attest  --manifest {target} --task "your task" --impact <id>=<sentence> ...')
    print(f'  contractctl commit  --manifest {target} --task "your task" --impact <id>=<sentence> ...')
    return 0


def cmd_upgrade_check(args) -> int:
    """One question: what must I do about my Play-Nice pin?

    Composes freshness (am I current?) with the contract diff (what changed?)
    and the manifest's always-set impact (does it require re-attestation?),
    then prints the exact next command. Exit 0 = no action, 1 = action needed,
    2 = freshness/diff could not be established (fail closed).
    """
    manifest = Path(args.manifest)
    if not manifest.is_file():
        print(f"UPGRADE-CHECK: UNKNOWN — no adoption manifest at {manifest}", file=sys.stderr)
        return 2
    m = load_adoption(manifest)
    cfg = freshness_config(m)
    fr = check_freshness(manifest)
    adopted = str((m.get("source") or {}).get("revision", "") or "")
    remote = fr.get("remote_revision")
    if getattr(args, "json_output", False):
        print(json.dumps({
            "manifest": str(manifest),
            "status": fr["status"],
            "policy": fr["policy"],
            "update": cfg["update"],
            "adopted_revision": adopted,
            "remote_revision": remote,
        }, indent=2))
        return 0 if fr["status"] == "CURRENT" else (1 if fr["status"] in ("BEHIND", "DIVERGED") else 2)
    print(f"UPGRADE CHECK — {manifest}")
    print(f"  freshness: {fr['status']} (policy: {fr['policy']}, update: {cfg['update']})")
    if fr["status"] == "CURRENT":
        print("  → no action: you are current with the authoritative revision")
        return 0
    if fr["status"] not in ("BEHIND", "DIVERGED"):
        print(f"  → {fr['status']}: freshness cannot be established (fail closed)")
        print("    contractctl freshness --manifest <m>   # inspect")
        return 2
    a = _rev_or_fail(adopted) if adopted else None
    b = _rev_or_fail(remote) if remote else None
    d = compute_contract_diff(a, b) if (a and b) else None
    print(f"  adopted: {adopted[:12] if adopted else 'unknown'}")
    print(f"  remote:  {remote[:12] if remote else 'unknown'}")
    if not d or d.get("errors"):
        print("  changes: UNKNOWN — the remote revision is not local yet")
        print("    git fetch  (in the library checkout), then re-run")
    else:
        print(
            f"  changes: {len(d['changed'])} changed, {len(d['added'])} added, "
            f"{len(d['removed'])} removed, {d['meaningful_changes']} meaningful"
        )
        for e in d["changed"]:
            kind = "MEANINGFUL" if e["meaningful"] else "clarification"
            print(f"    - {e['id']} {e['from_version']} → {e['to_version']} [{kind}]")
        for e in d["added"]:
            print(f"    - added {e['id']} @ {e['version']}")
        for e in d["removed"]:
            print(f"    - removed {e['id']} @ {e['version']}")
        always = _manifest_always_ids(manifest)
        if always:
            touched = (
                {e["id"] for e in d["changed"]}
                | {e["id"] for e in d["added"]}
                | {e["id"] for e in d["removed"]}
            )
            hit = sorted(touched & set(always))
            if hit:
                print(f"  always-set impact: {', '.join(hit)} — re-attestation required")
            else:
                print("  always-set impact: none (your floor contracts are unchanged)")
    if cfg["update"] == "review":
        print("  next: review the change above, then pin source.revision to the remote")
        print("        and re-run: resolve → read → attest → commit")
    else:
        print("  next: contractctl sync --manifest <m>  (update: automatic)")
        print("        then: resolve → read → attest → commit")
    return 1


def _split_impact_value(argv_eff: list[str], extras: list[str]) -> str | None:
    """Recover the likely full --impact value when the shell split it.

    The signature of the mistake (`--impact id=some words`) is: an --impact
    flag whose consumed value is a bare `id=word`, plus trailing non-flag
    leftovers. Returns the reconstructed value, or None when the extras do
    not look like a split --impact value.
    """
    if not extras or any(e.startswith("-") for e in extras):
        return None
    if "--impact" not in argv_eff:
        return None
    idx = max(i for i, tok in enumerate(argv_eff) if tok == "--impact")
    if idx + 1 >= len(argv_eff):
        return None
    first = argv_eff[idx + 1]
    if "=" not in first or " " in first or first.startswith("-"):
        return None
    return f"{first} {' '.join(extras)}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="contractctl",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--version",
        action="version",
        version=version_line("contractctl", library_version()),
        help="print contractctl and library version, then exit",
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="list contracts")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("show", help="print a contract's canonical content")
    p.add_argument("contract_id")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("validate", help="validate library + lockfile")
    p.add_argument(
        "--base",
        default=None,
        metavar="REV",
        help="judge contract changes against this revision (default: merge-base "
        "of HEAD and origin/main, else HEAD; env " + BASE_ENV + ")",
    )
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser(
        "bump",
        help="after editing a contract: set its version, rotate its receipt "
        "(minor/major), add the changelog bullet, refresh index and lock",
    )
    p.add_argument("contract_id")
    lv = p.add_mutually_exclusive_group(required=True)
    lv.add_argument("--patch", action="store_true", help="clarification; same meaning")
    lv.add_argument("--minor", action="store_true", help="compatible new rule (rotates the receipt)")
    lv.add_argument("--major", action="store_true", help="incompatible change (rotates the receipt)")
    p.add_argument("--note", default=None, help="changelog bullet text (required for --minor/--major)")
    p.set_defaults(func=cmd_bump)

    p = sub.add_parser("resolve", help="resolve applicable contracts for a task")
    p.add_argument(
        "--manifest",
        default=None,
        help=MANIFEST_HELP + "; without any manifest, resolve from the library defaults",
    )
    p.add_argument(
        "--task", default="", help="task description matched against trigger surfaces"
    )
    p.add_argument(
        "--tag",
        action="append",
        default=[],
        help="explicit surface tags for trigger matching (repeatable)",
    )
    p.add_argument(
        "--role",
        default="agent",
        choices=["agent", "human", "service"],
        help="base contract set when there is no adoption manifest (default: agent)",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="machine-readable output: each contract with every reason it was selected",
    )
    p.set_defaults(func=cmd_resolve)

    p = sub.add_parser("lock", help="regenerate contracts.lock.json")
    p.set_defaults(func=cmd_lock)

    p = sub.add_parser(
        "diff",
        help="compare the contract set between two library revisions",
    )
    p.add_argument("--from", dest="from_rev", required=True, metavar="REV")
    p.add_argument("--to", dest="to_rev", required=True, metavar="REV")
    p.add_argument(
        "--manifest",
        default=None,
        help="also report impact on this adoption manifest's always-set",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="machine-readable JSON output",
    )
    p.set_defaults(func=cmd_diff)

    p = sub.add_parser(
        "scan", help="scan a tree for banned public-boundary shapes (adopter-reusable)"
    )
    p.add_argument("--root", default=".", help="directory to scan (default: .)")
    p.add_argument(
        "--json", action="store_true", dest="json_output", help="machine-readable JSON"
    )
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser(
        "index", help="report or repair CONTRACT_INDEX.md version/status columns"
    )
    p.add_argument(
        "--write", action="store_true", help="rewrite drifted rows in place (deterministic)"
    )
    p.set_defaults(func=cmd_index)

    p = sub.add_parser(
        "init-adoption", help="write a starter adoption manifest (instead of copying an example)"
    )
    p.add_argument(
        "--manifest",
        default=".contracts/adoption.yaml",
        help="where to write the manifest (default: .contracts/adoption.yaml)",
    )
    p.add_argument("--repository", default=None, help="defaults to this library's own source")
    p.add_argument("--revision", default=None, help="defaults to this checkout's revision")
    p.add_argument("--project", default=None, help="project name (default: current dir name)")
    p.add_argument(
        "--policy", default="require-current", choices=["pinned", "require-current"]
    )
    p.add_argument("--update", default="review", choices=["review", "automatic"])
    p.add_argument("--force", action="store_true", help="overwrite an existing manifest")
    p.set_defaults(func=cmd_init_adoption)

    p = sub.add_parser(
        "upgrade-check",
        help="one answer: is my pin current, what changed, and what do I run next?",
    )
    p.add_argument("--manifest", default=None, help=MANIFEST_HELP)
    p.add_argument(
        "--json", action="store_true", dest="json_output", help="machine-readable JSON"
    )
    p.set_defaults(func=cmd_upgrade_check)

    p = sub.add_parser("attest", help="produce CONTRACT_ATTESTATION v1")
    p.add_argument(
        "--manifest", default=None, help=MANIFEST_HELP
    )
    p.add_argument(
        "--task", required=True, help="the task being attested (one description)"
    )
    p.add_argument(
        "--impact",
        action="append",
        default=[],
        metavar="ID=SENTENCE",
        help="contract_id=sentence task-impact acknowledgement (repeatable); quote values with spaces",
    )
    p.add_argument("--impact-file", help="file of 'id = sentence' lines")
    p.add_argument(
        "--revision",
        default="",
        help="library revision to attest against (default: this checkout's revision)",
    )
    p.add_argument(
        "--tag",
        action="append",
        default=[],
        help="explicit surface tags for trigger matching (repeatable)",
    )
    p.set_defaults(func=cmd_attest)

    p = sub.add_parser("commit", help="activate CONTRACT OPERATIONAL COMMITMENT v1")
    p.add_argument(
        "--manifest", default=None, help=MANIFEST_HELP
    )
    p.add_argument(
        "--task", required=True, help="the task being committed (one description)"
    )
    p.add_argument(
        "--impact",
        action="append",
        default=[],
        metavar="ID=SENTENCE",
        help="contract_id=sentence task-impact acknowledgement (repeatable); quote values with spaces",
    )
    p.add_argument("--impact-file", help="file of 'id = sentence' lines")
    p.add_argument(
        "--revision",
        default="",
        help="library revision to commit against (default: this checkout's revision)",
    )
    p.add_argument(
        "--tag",
        action="append",
        default=[],
        help="explicit surface tags for trigger matching (repeatable)",
    )
    p.add_argument(
        "--role",
        default="session",
        choices=["session", "orchestrator", "worker"],
        help="participant role in the propagation tree",
    )
    p.add_argument(
        "--worker",
        action="store_true",
        help="shortcut for --role worker; requires --parent-bundle",
    )
    p.add_argument(
        "--parent-bundle",
        default=None,
        help="inherited contract bundle hash (workers must carry the parent bundle)",
    )
    p.add_argument(
        "--output",
        default=None,
        help=(
            "where to write the session artifact (default: "
            ".contracts/sessions/<role>-<task>.json next to the manifest)"
        ),
    )
    p.add_argument(
        "--text-only",
        action="store_true",
        help="write the human-readable commitment text instead of JSON",
    )
    p.set_defaults(func=cmd_commit)

    p = sub.add_parser(
        "session-status", help="report current commitment state (ACTIVE/STALE/INACTIVE)"
    )
    p.add_argument(
        "--manifest",
        default=None,
        help="adoption manifest; enables task-change re-resolution detection",
    )
    p.add_argument(
        "--artifact",
        default=None,
        help="specific commitment artifact path (default: keyed .contract-commitments/)",
    )
    p.add_argument(
        "--role", default="session", choices=["session", "orchestrator", "worker"]
    )
    p.add_argument(
        "--task", default="", help="task key when looking up the keyed artifact"
    )
    p.set_defaults(func=cmd_session_status)

    p = sub.add_parser(
        "init-project",
        help="create a minimal .project/ skeleton (no empty directory forest)",
    )
    p.add_argument(
        "target",
        nargs="?",
        default=".",
        help="project root (default: current directory)",
    )
    p.add_argument(
        "--id", required=True, help="stable machine id (e.g. personal-world)"
    )
    p.add_argument("--name", required=True, help="human name")
    p.set_defaults(func=cmd_init_project)

    p = sub.add_parser("project", help="project-context subcommands")
    psub = p.add_subparsers(dest="project_command", required=True)
    pv = psub.add_parser("validate", help="validate a .project/ directory")
    pv.add_argument("path", help="path to the .project/ directory (or its parent)")
    pv.set_defaults(func=cmd_project_validate)

    p = sub.add_parser("participant", help="participant-pack subcommands")
    psub2 = p.add_subparsers(dest="participant_command", required=True)
    pav = psub2.add_parser("validate", help="validate one participant pack directory")
    pav.add_argument("path", help="path to the participant pack directory")
    pav.set_defaults(func=cmd_participant_validate)
    pal = psub2.add_parser("list", help="list participant packs in a project")
    pal.add_argument("path", help="path to the .project/ directory (or its parent)")
    pal.set_defaults(func=cmd_participant_list)

    p = sub.add_parser(
        "validate-question",
        help="validate a play-nice question / help-request / help-response artifact",
    )
    p.add_argument(
        "question", help="path to the JSON artifact (play-nice/question-v1 family)"
    )
    p.set_defaults(func=cmd_validate_question)

    p = sub.add_parser(
        "verify-attestation", help="verify an attestation against the library"
    )
    p.add_argument("attestation", help="path to the CONTRACT_ATTESTATION v1 artifact")
    p.add_argument(
        "--manifest",
        default=None,
        help="adoption manifest to verify the attestation against",
    )
    p.set_defaults(func=cmd_verify_attestation)

    p = sub.add_parser("adopt", help="validate a project adoption manifest")
    p.add_argument(
        "--manifest", default=None,
        help="adoption manifest to validate " + MANIFEST_DEFAULT_NOTE,
    )
    p.set_defaults(func=cmd_adopt)

    p = sub.add_parser("onboard", help="guided onboarding plan for a role")
    p.add_argument(
        "--role",
        default="worker",
        choices=[
            "orchestrator",
            "worker",
            "agent",
            "ui",
            "cli",
            "service",
            "human",
            "maintainer",
        ],
        help="participant role determining reading order and emphasis (default: worker; 'agent' is an alias for 'worker')",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="machine-readable JSON output",
    )
    p.set_defaults(func=cmd_onboard)

    p = sub.add_parser("status", help="one-line library health")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser(
        "freshness",
        help="verify the authoritative remote revision (first preflight stage)",
        description=(
            "Deterministically establish the state of the configured authoritative "
            "remote revision (git ls-remote). Fail closed: only CURRENT satisfies "
            "a require-current freshness policy."
        ),
    )
    p.add_argument(
        "--manifest",
        default=None,
        help=MANIFEST_HELP,
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="machine-readable JSON (deterministic field set)",
    )
    p.set_defaults(func=cmd_freshness)

    p = sub.add_parser(
        "sync",
        help="refresh the adoption pin to the authoritative remote revision",
        description=(
            "Detect a changed authoritative remote. update: automatic moves the "
            "pin and forces a fresh resolve/read/attest/commit cycle; update: "
            "review blocks and prints the review path instead."
        ),
    )
    p.add_argument(
        "--manifest",
        default=None,
        help=MANIFEST_HELP,
    )
    p.set_defaults(func=cmd_sync)

    argv_eff = list(argv) if argv is not None else sys.argv[1:]
    args, extras = ap.parse_known_args(argv_eff)
    if extras:
        # An unquoted --impact sentence gets split by the shell; argparse sees
        # the first word as the value and the rest as garbage. Say that plainly
        # instead of dumping argparse internals (exit 2, same as before).
        value = (
            _split_impact_value(argv_eff, extras)
            if getattr(args, "command", None) in ("commit", "attest")
            else None
        )
        if value is not None:
            print(
                "error: an --impact value contains spaces and was split by the shell.",
                file=sys.stderr,
            )
            print(f'  quote it:  --impact "{value}"', file=sys.stderr)
            print(
                "  or avoid quoting entirely: --impact-file <file> "
                "(one 'id = sentence' line per contract)",
                file=sys.stderr,
            )
            return 2
        ap.error(f"unrecognized arguments: {' '.join(extras)}")
    if args.command in NEEDS_MANIFEST and getattr(args, "manifest", None) is None:
        args.manifest = str(discover_manifest())
    try:
        return args.func(args)
    except CTError as e:
        print(f"error: {e}", file=sys.stderr)
        if isinstance(e, CTManifestMissing):
            print_missing_manifest_hint(e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
