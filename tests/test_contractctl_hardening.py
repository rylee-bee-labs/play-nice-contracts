"""contractctl: one default contract set, stronger validate, index --write
adding rows, and grouped --help (one table registers and lists commands)."""

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CT = REPO / "tools" / "contractctl" / "contractctl.py"
PN = REPO / "tools" / "playnice" / "playnice.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_ct(args, cwd, ct_path=CT):
    return subprocess.run(
        [sys.executable, str(ct_path), *args],
        capture_output=True, text=True, cwd=str(cwd), timeout=60,
    )


@pytest.fixture()
def ct():
    return _load(CT, "ct_hardening")


@pytest.fixture()
def copy(tmp_path):
    """A copy of the library (no Git history: base-revision checks skip)."""
    dest = tmp_path / "lib"
    shutil.copytree(
        REPO, dest, symlinks=True,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", ".pytest_cache", ".contract-commitments"),
    )
    return dest, _load(dest / "tools" / "contractctl" / "contractctl.py", f"ct_{id(dest)}")


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert old in text, f"fixture moved: {old!r} not in {path.name}; update the test"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# ------------------------------------------------ 1. one default contract set


def test_default_set_is_everyone_basics_plus_agent_work(ct):
    assert set(ct.DEFAULT_CONTRACT_SET) == {
        "truth-and-evidence", "status-and-state", "recovery-and-history", "ask-for-help",
        "agent-behavior", "bounded-work", "handoff-and-continuity",
        "testing-and-evidence", "contract-proof",
    }
    layers = {c["front_matter"]["contract_id"]: c["front_matter"]["layer"]
              for c in ct.load_library()}
    assert all(cid in layers for cid in ct.DEFAULT_CONTRACT_SET)
    assert {layers[c] for c in ct.DEFAULT_CONTRACT_SET} == {"everyone", "work"}


def test_default_set_agrees_across_resolve_init_adoption_and_init_project(ct, tmp_path):
    want = list(ct.DEFAULT_CONTRACT_SET)
    assert ct.ROLE_BASE_SETS["agent"] == want

    # no manifest: resolve's agent default (floor is added on top)
    r = run_ct(["resolve", "--task", "", "--json"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    got = {c["id"] for c in json.loads(r.stdout)["contracts"]}
    assert got == set(want) | {"floor"}

    # init-adoption
    a = tmp_path / "adopter"
    a.mkdir()
    r = run_ct(["init-adoption", "--project", "demo", "--revision", "0" * 40], a)
    assert r.returncode == 0, r.stdout + r.stderr
    assert ct.load_adoption(a / ".contracts" / "adoption.yaml")["always"] == want

    # init-project
    p = tmp_path / "proj"
    p.mkdir()
    r = run_ct(["init-project", str(p), "--id", "demo", "--name", "Demo"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert ct.load_adoption(p / ".project" / "contracts" / "adoption.yaml")["always"] == want


# ------------------------------------------------ 2. stronger validate


def test_pack_titles_match_playnice_and_index_headings(ct):
    pn = _load(PN, "pn_hardening")
    assert ct.PACK_TITLES == pn.PACK_TITLES
    assert set(ct.PACK_TITLES) == set(ct.LAYER_DIRS)
    index = (REPO / "CONTRACT_INDEX.md").read_text(encoding="utf-8")
    for title in ct.PACK_TITLES.values():
        assert f"\n## {title}\n" in index


def test_layer_must_match_pack_folder(copy):
    root, ct = copy
    _edit(root / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md",
          "layer: everyone", "layer: work")
    errors = ct.validate_library()
    assert any("layer 'work' does not match its pack folder 'everyone'" in e
               for e in errors), errors
    assert any("pack folder name" in h for h in ct.fix_hints(errors))


def test_required_body_sections(copy):
    root, ct = copy
    _edit(root / "contracts" / "work" / "BOUNDED_WORK.md", "\n## Why\n", "\n## Reasons\n")
    errors = ct.validate_library()
    assert any(e.endswith("BOUNDED_WORK.md: missing body section '## Why'")
               for e in errors), errors
    assert any("missing '## ' section" in h for h in ct.fix_hints(errors))


def test_index_title_purpose_and_section_checked(copy):
    root, ct = copy
    idx = root / "CONTRACT_INDEX.md"
    _edit(idx, "| `bounded-work` | Bounded Work |", "| `bounded-work` | Bounded Jobs |")
    _edit(idx, "pays to stop it. |", "pays. |")
    # move the friendly-site row from Sites into Access
    text = idx.read_text(encoding="utf-8")
    row = next(ln for ln in text.splitlines() if ln.startswith("| `friendly-site` "))
    text = text.replace(row + "\n", "")
    anchor = next(ln for ln in text.splitlines() if ln.startswith("| `public-and-private` "))
    idx.write_text(text.replace(anchor, row + "\n" + anchor), encoding="utf-8")
    errors = ct.validate_library()
    assert "index drift: 'bounded-work' Title is 'Bounded Jobs', front matter title is 'Bounded Work'" in errors
    assert "index drift: 'bounded-work' Purpose differs from its front-matter rationale" in errors
    assert "index drift: 'friendly-site' row is under '## Access', its pack section is '## Sites'" in errors
    hints = ct.fix_hints(errors)
    assert any("title and rationale" in h for h in hints)
    assert any("into its pack's table" in h for h in hints)


def test_aliases_checked_against_live_ids_and_old_names_table(copy):
    root, ct = copy
    aliases = root / "aliases.json"
    data = json.loads(aliases.read_text(encoding="utf-8"))
    data["aliases"]["handoff"] = "no-such-contract"   # dead target
    data["aliases"]["cli"] = "api"                     # shadows a live id
    aliases.write_text(json.dumps(data, indent=2), encoding="utf-8")
    _edit(root / "CONTRACT_INDEX.md", "| worker-contract | `orchestration` |\n", "")
    errors = ct.validate_library()
    assert "aliases: 'handoff' points to unknown contract 'no-such-contract'" in errors
    assert "aliases: 'cli' is a live contract id, so it cannot also be an old name" in errors
    assert any("'handoff' points to 'no-such-contract' in aliases.json but "
               "'handoff-and-continuity' in CONTRACT_INDEX.md" in e for e in errors), errors
    assert any("'worker-contract' → 'orchestration' is in aliases.json but not in the "
               "Old names table" in e for e in errors), errors
    assert any("Old names table" in h for h in ct.fix_hints(errors))


def test_new_checks_pass_on_the_real_tree(ct):
    errors = ct.validate_library()
    assert errors == [], "\n".join(errors)
    assert len(ct.index_old_names()) == len(ct.load_aliases())


# ------------------------------------------------ 3. index --write adds rows


def test_index_write_adds_missing_row_in_sorted_place(copy, capsys):
    root, ct = copy
    idx = root / "CONTRACT_INDEX.md"
    before = idx.read_text(encoding="utf-8")
    row = next(ln for ln in before.splitlines() if ln.startswith("| `orchestration` "))
    idx.write_text(before.replace(row + "\n", ""), encoding="utf-8")
    errors = ct.validate_library()
    assert "index drift: contract 'orchestration' missing from CONTRACT_INDEX.md" in errors
    assert "contractctl index --write" in ct.fix_hints(errors)
    assert ct.cmd_index(argparse.Namespace(write=False)) == 1
    assert ct.cmd_index(argparse.Namespace(write=True)) == 0
    # the generated row is byte-identical to the hand-written one, in place
    assert idx.read_text(encoding="utf-8") == before
    assert "added 1 row(s)" in capsys.readouterr().out


def test_index_write_keeps_and_reports_unknown_rows(copy, capsys):
    root, ct = copy
    idx = root / "CONTRACT_INDEX.md"
    _edit(idx, "| `truth-and-evidence` | Truth and Evidence | 2.0.0 | canonical |",
          "| `ghost-contract` | Truth and Evidence | 2.0.0 | canonical |")
    assert ct.cmd_index(argparse.Namespace(write=True)) == 1
    text = idx.read_text(encoding="utf-8")
    assert "| `ghost-contract` |" in text  # reported, not deleted
    lines = [ln for ln in text.split("## Agents and work")[0].splitlines()
             if ln.startswith("| `")]
    ids = [re.match(r"\| `([a-z0-9-]+)`", ln).group(1) for ln in lines]
    # re-added at its sorted place: just before the next id up
    assert ids.index("truth-and-evidence") + 1 == ids.index("working-together")
    out = capsys.readouterr().out
    assert "lists unknown contract 'ghost-contract'" in out
    assert "next: remove the row by hand" in out


def test_index_pack_tables_are_floor_first_then_alphabetical(ct):
    by_section: dict[str, list[str]] = {}
    for row in ct.index_table_rows():
        by_section.setdefault(row["section"], []).append(row["id"])
    for section, ids in by_section.items():
        assert ids == sorted(ids, key=ct._index_sort_key), section


# ------------------------------------------------ 4. grouped --help


def test_help_groups_come_from_the_one_command_table(ct, tmp_path):
    names = [n for _g, cmds in ct.COMMAND_GROUPS for n, _w in cmds]
    assert len(names) == len(set(names)), "a command is in two groups"
    # registered commands == the table (argparse lists its choices on error)
    r = run_ct(["no-such-command"], tmp_path)
    # Newer Pythons print the choices without quotes; accept either form.
    listed = r.stderr.split("choose from", 1)[1].split(")", 1)[0]
    choices = {c.strip().strip("'\"") for c in listed.split(",") if c.strip()}
    assert choices == set(names)
    # --help shows each group's title, then its commands, in table order
    out = run_ct(["--help"], tmp_path).stdout
    pos = -1
    for title, cmds in ct.COMMAND_GROUPS:
        pos = out.index(f"\n{title}\n", pos + 1)
        for name, _why in cmds:
            pos = out.index(f"\n  {name} ", pos)
    for name in names:
        assert run_ct([name, "--help"], tmp_path).returncode == 0, name
