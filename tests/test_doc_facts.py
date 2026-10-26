"""Hand-written docs state the same versions, receipt and rule count as the source.

Added 2026-10-26 so a version bump cannot leave the docs behind silently.
Sources of truth:

- library version: VERSION
- floor version and receipt word: contracts/everyone/FLOOR.md
- playnice version: PLAYNICE_VERSION in tools/playnice/playnice.py
- number of floor rules: the numbered list under FLOOR.md's `## Rules`

Text between docsgen markers is written by an outside tool and is skipped.
Contract text (contracts/) is governed by its own versioning. Dated history
(CHANGELOG.md, docs/background/, docs/decisions/, docs/research/) is left as
written.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FLOOR = REPO / "contracts" / "everyone" / "FLOOR.md"
PLAYNICE = REPO / "tools" / "playnice" / "playnice.py"

HISTORY_DIRS = ("docs/background/", "docs/decisions/", "docs/research/")

DOCSGEN = re.compile(
    r"<!-- docsgen:start:([\w-]+) -->.*?<!-- docsgen:end:\1 -->", re.S)
PLAY_NICE_BLOCK = re.compile(r"<!-- play-nice:start -->.*?<!-- play-nice:end -->", re.S)

# "library 2.0.0", "Floor `1.0.0`", "playnice 0.1.0"
VERSION_CLAIM = re.compile(
    r"\b(library|floor|playnice)\b[ \t`*]*v?(\d+\.\d+\.\d+)", re.I)
# "Play-Nice floor 1.0.0 · receipt honey-cell-lantern"; placeholders are skipped
PROOF_LINE = re.compile(
    r"Play-Nice floor\s+(\S+?)(?:\s+[·|-]\s+receipt\s+([^\s`\"']+))?(?=[\s`\"']|$)")
RECEIPT_WORD = re.compile(r"^[a-z]+(?:-[a-z]+)+$")
RULE_COUNT = re.compile(r"\b(\d+)\s+(?:floor\s+)?rules\b", re.I)


def _floor_text():
    return FLOOR.read_text(encoding="utf-8")


def library_version():
    return (REPO / "VERSION").read_text(encoding="utf-8").strip()


def floor_version():
    return re.search(r"(?m)^version:\s*(\S+)", _floor_text()).group(1)


def floor_receipt():
    return re.search(r"<!-- contract-receipt:\s*(\S+)\s*-->", _floor_text()).group(1)


def playnice_version():
    m = re.search(r'(?m)^PLAYNICE_VERSION\s*=\s*"([^"]+)"',
                  PLAYNICE.read_text(encoding="utf-8"))
    assert m, "tools/playnice/playnice.py has no PLAYNICE_VERSION = \"...\" line"
    return m.group(1)


def floor_rule_count():
    rules = re.search(r"(?ms)^## Rules\s*$(.*?)(?=^## |\Z)", _floor_text()).group(1)
    return len(re.findall(r"(?m)^\d+\.\s", rules))


def _blank(m):
    """Replace a match with the same number of newlines, so line numbers hold."""
    return "\n" * m.group(0).count("\n")


def hand_written(rel):
    text = (REPO / rel).read_text(encoding="utf-8")
    return DOCSGEN.sub(_blank, text)


def doc_files():
    files = ["README.md", "AGENTS.md", "CONTRIBUTING.md"]
    for p in sorted((REPO / "docs").rglob("*.md")):
        rel = p.relative_to(REPO).as_posix()
        if not rel.startswith(HISTORY_DIRS):
            files.append(rel)
    return files


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def in_play_nice_block(text, pos):
    return any(m.start() <= pos < m.end() for m in PLAY_NICE_BLOCK.finditer(text))


def fix_hint(text, pos, wanted):
    if in_play_nice_block(text, pos):
        return "run `playnice start .` to rewrite the play-nice block"
    return f"change it to {wanted!r}"


def units(text):
    """Paragraphs, with each table row and list item as its own unit."""
    pos = 0
    for i, para in enumerate(re.split(r"(\n[ \t]*\n)", text)):
        if i % 2 == 0 and para.strip():  # odd items are the blank-line separators
            starts = [m.start() for m in re.finditer(r"(?m)^(?:\||[-*] |\d+\. )", para)]
            cuts = sorted({0, *starts}) + [len(para)]
            for a, b in zip(cuts, cuts[1:]):
                yield pos + a, para[a:b]
        pos += len(para)


def test_version_claims_match_the_source():
    current = {
        "library": (library_version(), "VERSION"),
        "floor": (floor_version(), "contracts/everyone/FLOOR.md"),
        "playnice": (playnice_version(), "PLAYNICE_VERSION in tools/playnice/playnice.py"),
    }
    seen = set()
    wrong = []
    for rel in ("README.md", "AGENTS.md"):
        text = hand_written(rel)
        for m in VERSION_CLAIM.finditer(text):
            kind, stated = m.group(1).lower(), m.group(2)
            seen.add((rel, kind))
            want, source = current[kind]
            if stated != want:
                wrong.append(
                    f"{rel}:{line_of(text, m.start())}: says {m.group(0)!r}, but the "
                    f"{kind} version is {want} (from {source}); "
                    + fix_hint(text, m.start(), m.group(0).replace(stated, want)))
    assert not wrong, "docs state an old version:\n" + "\n".join(wrong)
    missing = [k for k in current if ("README.md", k) not in seen]
    assert not missing, (
        f"README.md no longer states the {', '.join(missing)} version, so this test "
        "checks nothing there; keep the version table, or update this test")


def test_proof_lines_match_the_floor():
    version, receipt = floor_version(), floor_receipt()
    wrong = []
    checked = 0
    for rel in doc_files():
        text = hand_written(rel)
        for m in PROOF_LINE.finditer(text):
            stated_v, stated_r = m.group(1), (m.group(2) or "").rstrip(".,;:)")
            where = f"{rel}:{line_of(text, m.start())}"
            if re.fullmatch(r"\d+\.\d+\.\d+", stated_v):
                checked += 1
                if stated_v != version:
                    wrong.append(f"{where}: proof line names floor {stated_v}; "
                                 + fix_hint(text, m.start(), f"Play-Nice floor {version}"))
            if RECEIPT_WORD.match(stated_r) and stated_r != receipt:
                # the word itself is not printed, like `playnice verify`: read the floor
                hint = ("run `playnice start .` to rewrite the play-nice block"
                        if in_play_nice_block(text, m.start()) else
                        "copy the word from the contract-receipt comment in "
                        "contracts/everyone/FLOOR.md")
                wrong.append(f"{where}: proof line has receipt {stated_r!r}, which is not "
                             f"the floor's receipt word; {hint}")
    assert not wrong, "proof lines out of date:\n" + "\n".join(wrong)
    assert checked, "found no proof line with a version; the pattern may be broken"


def test_floor_rule_counts_match():
    count = floor_rule_count()
    assert count, "found no numbered rules under ## Rules in contracts/everyone/FLOOR.md"
    wrong = []
    for rel in doc_files():
        text = hand_written(rel)
        for start, unit in units(text):
            if "floor" not in unit.lower():
                continue
            for m in RULE_COUNT.finditer(unit):
                if int(m.group(1)) != count:
                    pos = start + m.start()
                    wrong.append(
                        f"{rel}:{line_of(text, pos)}: says {m.group(0)!r}, but the floor "
                        f"has {count} rules; change it to {m.group(0).replace(m.group(1), str(count))!r}"
                        " (or drop the count)")
    assert not wrong, "floor rule counts out of date:\n" + "\n".join(wrong)


def test_patterns_catch_what_they_should():
    """Guards the guards: each pattern fires on the real shapes in these docs."""
    assert VERSION_CLAIM.search("| Library `2.0.0` |").group(2) == "2.0.0"
    assert VERSION_CLAIM.search("playnice 0.1.0 · library").group(1) == "playnice"
    assert not VERSION_CLAIM.search("playnice verify")
    m = PROOF_LINE.search('verify "Play-Nice floor 1.0.0 · receipt honey-cell-lantern"')
    assert m.groups() == ("1.0.0", "honey-cell-lantern")
    m = PROOF_LINE.search("`Play-Nice floor <version> · receipt <word> · read <ids>`")
    assert m.group(1) == "<version>"  # a placeholder: skipped by the test
    assert RULE_COUNT.search("the 17 floor rules").group(1) == "17"
    assert [u for _, u in units("| a |\n| Floor | 3 rules |\n\n- x\n- y")] == [
        "| a |\n", "| Floor | 3 rules |", "- x\n", "- y"]
