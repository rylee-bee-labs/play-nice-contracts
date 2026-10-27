"""License map consistency — the map must be one story, machine-checked.

Established 2026-09-20 after a drift class that prose review does not
catch: README claiming one license while per-directory LICENSE files
said others. This test fails if the files ever disagree again.

Map: contracts/ + docs/ text -> CC BY-SA 4.0; tooling/schemas/tests ->
MIT; identity -> TRADEMARKS.md (descriptive, not a grant).

Note on pattern discipline: every license-token scan here uses word
boundaries. Naive substring checks for "MPL" match IMPLIED and
EXAMPLES — a false-positive class this test file itself shipped once.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# exact token "MPL"/"MPL-2.0"/"Mozilla", not IMPLIED/EXAMPLES/...
MPL_TOKEN = re.compile(r"\bMPL(-2\.0)?\b|\bMozilla\b")

# words that legitimately mark a license mention as history, not claim
HISTORICAL = ("baseline", "histor", "supersed", "relicens", "moved from",
              "changelog", "experiment", "whipsaw", "drift")


def _mentions_history(line: str) -> bool:
    low = line.lower()
    return any(w in low for w in HISTORICAL)


def _primary_declaration(text: str) -> str:
    """The bolded license named in the 'licensed under the **X**' clause."""
    m = re.search(r"licensed\s+under\s+the\s+\*\*([^*]+)\*\*", text)
    assert m, "no primary license declaration found"
    return m.group(1)


def test_root_license_is_mit():
    text = (REPO / "LICENSE").read_text()
    assert "MIT License" in text
    assert not MPL_TOKEN.search(text), "root LICENSE still references MPL/Mozilla"


def test_contracts_license_is_cc_by_sa():
    text = (REPO / "contracts" / "LICENSE.md").read_text()
    assert "Creative Commons" in _primary_declaration(text)
    assert "CC BY-SA 4.0" in text


def test_docs_license_is_cc_by_sa():
    text = (REPO / "docs" / "LICENSE.md").read_text()
    assert "Creative Commons" in _primary_declaration(text)
    assert "CC BY-SA 4.0" in text


def test_docs_license_scope_matches_layout():
    """harness/ moved under docs/ in 2.1.0 and is CC BY-SA; profiles moved
    to examples/profiles/ and stay MIT under the root LICENSE."""
    text = (REPO / "docs" / "LICENSE.md").read_text()
    scope = text.split("## Scope", 1)[1].split("\n## ", 1)[0]
    assert "`docs/background/harness/`" in scope
    assert (REPO / "docs" / "background" / "harness").is_dir()
    assert "profiles" not in scope, "examples/profiles/ is MIT, not docs scope"
    assert not (REPO / "harness").exists() and not (REPO / "profiles").exists()


def test_readme_license_section_matches_map():
    text = (REPO / "README.md").read_text()
    m = re.search(r"^## License\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    assert m, "README has no ## License section"
    section = m.group(1)
    assert "CC BY-SA" in section, "README License section omits CC BY-SA (contracts/docs)"
    assert "MIT" in section, "README License section omits MIT (code)"
    for line in section.splitlines():
        for m2 in MPL_TOKEN.finditer(line):
            assert _mentions_history(line), \
                f"README License section asserts MPL as current: {line!r}"


def test_trademarks_point_at_existing_license_files():
    text = (REPO / "TRADEMARKS.md").read_text()
    refs = re.findall(r"`([A-Za-z0-9_./-]*LICENSE[^`]*)`", text)
    assert refs, "TRADEMARKS.md references no license files"
    for ref in refs:
        assert (REPO / ref).is_file(), f"TRADEMARKS.md references missing file {ref}"


def test_no_stale_mpl_claims_in_live_prose():
    """Live prose must not present MPL as current. CHANGELOG and git
    history may mention it as history."""
    live = ["README.md", "AGENTS.md", "LICENSE", "TRADEMARKS.md",
            "contracts/LICENSE.md", "docs/LICENSE.md", "CONTRIBUTING.md"]
    offenders = []
    for name in live:
        text = (REPO / name).read_text()
        for i, line in enumerate(text.splitlines(), 1):
            if MPL_TOKEN.search(line) and not _mentions_history(line):
                offenders.append(f"{name}:{i}: {line.strip()!r}")
    assert not offenders, "MPL presented as current:\n" + "\n".join(offenders)


def test_pattern_discipline_self_check():
    """Guards the guard: the token regex must not fire on the false
    positives this file originally shipped with, and must fire on the
    real claim."""
    for trap in ("EXPRESS OR IMPLIED, INCLUDING", "HUMAN EXAMPLES, GOOD EXAMPLES",
                 "simple template", "accomplMPLed"):
        assert not MPL_TOKEN.search(trap), f"false positive: {trap!r}"
    for real in ("licensed under Mozilla Public License 2.0",
                 "code moved from MPL-2.0 to MIT baseline",
                 "the MPL tooling layer"):
        assert MPL_TOKEN.search(real), f"missed real token: {real!r}"
