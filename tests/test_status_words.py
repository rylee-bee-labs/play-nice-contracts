"""The shared status words are copied by hand into three Markdown files.

This one check keeps those copies equal to the schema enum, which is the
source. It reads the files; it generates nothing. A list that adds a word the
schema does not have, or leaves one out, fails and names the file and word.
"""

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCHEMA = REPO / "schema" / "status.schema.json"
COPIES = [
    "contracts/everyone/STATUS_AND_STATE.md",
    "docs/QUICK_REFERENCE.md",
    "contracts/everyone/FLOOR.md",
]
# The list starts at the first word of the vocabulary and ends at the next full stop.
LIST = re.compile(r"\bhealthy, warning, [A-Za-z_,\s]+?(?=\.(?:\s|$))")


def schema_words():
    return json.loads(SCHEMA.read_text())["enum"]


def list_words(text):
    m = LIST.search(" ".join(text.split()))
    assert m, "no status word list found"
    return [w.strip() for w in m.group(0).split(",")]


def problems(name, text, words):
    found = list_words(text)
    out = [f"{name}: '{w}' is not in the schema enum" for w in found if w not in words]
    out += [f"{name}: schema word '{w}' is missing" for w in words if w not in found]
    return out


def test_schema_meanings_cover_enum():
    schema = json.loads(SCHEMA.read_text())
    assert sorted(schema["$defs"]["meanings"]) == sorted(schema["enum"])


def test_status_lists_match_schema():
    words = schema_words()
    errors = []
    for name in COPIES:
        errors += problems(name, (REPO / name).read_text(), words)
    assert not errors, "\n".join(errors)


def test_playnice_maps_its_states_into_the_schema():
    """`playnice check` results and the words `playnice status` leads with
    are all shared words, and every freshness state has one."""
    import sys
    sys.path.insert(0, str(REPO / "tools" / "playnice"))
    try:
        import playnice as pn
    finally:
        sys.path.pop(0)
    words = set(schema_words())
    assert set(pn.CHECK_STATES) <= words
    for table in (pn.FRESHNESS_SHARED, pn.REPO_SHARED, pn.CARRYOVER_SHARED):
        assert set(table.values()) <= words, table
    cc = pn.import_contractctl(REPO)
    assert set(pn.FRESHNESS_SHARED) == set(cc.FRESHNESS_STATES)


def test_check_names_file_and_word():
    words = schema_words()
    base = (REPO / COPIES[2]).read_text()
    assert problems("x", base, words) == []
    added = base.replace("complete, failed.", "complete, failed, QUEUED.")
    assert problems("x", added, words) == ["x: 'QUEUED' is not in the schema enum"]
    dropped = base.replace("complete, failed.", "complete.")
    assert problems("x", dropped, words) == ["x: schema word 'failed' is missing"]
