"""playnice uses contractctl's helpers instead of its own copies.

The copies had drifted. Each test names the difference that existed before
the copy was removed, and pins the behavior that was kept. The two YAML
parsers stay separate on purpose (see `_parse_yaml_simple`); their
differences are pinned here so a merge cannot change a file's meaning
unnoticed.
"""

import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools" / "contractctl"))
sys.path.insert(0, str(REPO / "tools" / "playnice"))
import contractctl as ct  # noqa: E402
import playnice as pn  # noqa: E402


# ------------------------------------------------------------ remote URL
# Before: playnice expanded `~/lib` (contractctl passed it to git unexpanded,
# and git does not expand it), and turned `a/b/c` into
# https://github.com/a/b/c.git (contractctl passed it through as a path).
# Kept: contractctl's rules, plus the `~` expansion.


def test_playnice_has_no_remote_url_copy():
    assert not hasattr(pn, "_remote_url")


@pytest.mark.parametrize("given, want", [
    ("~/src/lib", str(Path.home() / "src" / "lib")),
    ("a/b/c", "a/b/c"),
    ("owner/repo", "https://github.com/owner/repo.git"),
    ("git@github.com:o/r.git", "git@github.com:o/r.git"),
    ("https://example.org/x.git", "https://example.org/x.git"),
    ("/abs/path", "/abs/path"),
])
def test_remote_url(given, want):
    assert ct.remote_url(given) == want
    assert pn.own_contractctl().remote_url(given) == want


# ------------------------------------------------------------ floor + receipt
# Before: playnice read any `[a-z0-9-]+` receipt word from the floor;
# contractctl's RECEIPT_RE (and `contractctl validate`) needs three lowercase
# words. Kept: contractctl's, so a floor contractctl rejects is not read.


def fake_library(tmp_path, receipt):
    lib = tmp_path / "lib"
    (lib / "tools" / "contractctl").mkdir(parents=True)
    shutil.copy(REPO / "tools" / "contractctl" / "contractctl.py",
                lib / "tools" / "contractctl" / "contractctl.py")
    floor = (REPO / "contracts" / "everyone" / "FLOOR.md").read_text(encoding="utf-8")
    real = ct.RECEIPT_RE.search(floor).group(1)
    (lib / "contracts" / "everyone").mkdir(parents=True)
    (lib / "contracts" / "everyone" / "FLOOR.md").write_text(
        floor.replace(real, receipt), encoding="utf-8")
    return lib


def test_floor_comes_from_contractctl():
    cc = pn.import_contractctl(REPO)
    floor = pn.load_v2_floor(cc)
    text = (REPO / "contracts" / "everyone" / "FLOOR.md").read_text(encoding="utf-8")
    assert floor["version"] == cc.floor_version()
    assert floor["receipt"] == cc.RECEIPT_RE.search(text).group(1)


def test_floor_receipt_must_be_three_words(tmp_path):
    good = pn.import_contractctl(fake_library(tmp_path / "a", "one-two-three"))
    assert pn.load_v2_floor(good)["receipt"] == "one-two-three"
    bad = pn.import_contractctl(fake_library(tmp_path / "b", "one-2"))
    with pytest.raises(pn.CheckUnavailable):
        pn.load_v2_floor(bad)


# ------------------------------------------------------------ index + ids
# Before: playnice grepped contract_id/status from every folder under
# contracts/ and read aliases.json itself; the results matched contractctl's
# load_library() and canonical_id() today, so nothing changes.


def test_index_and_read_ids_come_from_contractctl():
    cc = pn.import_contractctl(REPO)
    index = pn.load_v2_index(cc)
    assert index == {c["front_matter"]["contract_id"]: c["front_matter"]["status"]
                     for c in cc.load_library()}
    assert pn.canonical_read_id(cc, "floor", index) == "floor"
    assert pn.canonical_read_id(cc, "assume-unknown", index) == "truth-and-evidence"
    assert pn.canonical_read_id(cc, "no-such-contract", index) is None


# ------------------------------------------------------------ YAML (kept two)


@pytest.mark.parametrize("text, config, manifest", [
    ("30", 30, "30"),                    # config needs ints; a pin of digits stays text
    ("'q'", "q", "'q'"),                 # config strips single quotes
    ('"a # b"  # note', "a # b", '"a # b"  # note'),
    ("x\t# c", "x", "x\t# c"),           # tab comment
    ("None", None, "None"),
    ("none", "none", "none"),            # `conflicts: none` is a real value
    ("TRUE", "TRUE", True),
    ("{}", "{}", {}),
])
def test_yaml_scalar_differences_are_pinned(text, config, manifest):
    assert pn._coerce(text) == config
    assert ct._parse_scalar(text) == manifest


def test_manifest_revision_of_digits_stays_text():
    assert ct._yaml_block_to_dict(["revision: 1234567"]) == {"revision": "1234567"}
    assert pn._parse_yaml_simple("revision: 1234567", where="t") == {"revision": 1234567}
