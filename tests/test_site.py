"""The generated website (tools/site/build_site.py).

Built into a temporary folder from this checkout, then checked the way a
visitor and a machine would see it: every page passes the HTML basics,
every internal link and anchor resolves, the JSON beside each page carries
the same facts, the site passes `playnice check <url>` when served, and the
proof-line page answers exactly like `playnice verify`.
"""

from __future__ import annotations

import functools
import html.parser
import http.server
import json
import re
import shutil
import subprocess
import threading
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import pytest

from conftest import PLAYNICE, REPO, load_module, run_py

BUILD = REPO / "tools" / "site" / "build_site.py"
TODAY = "2026-10-27"


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    out = tmp_path_factory.mktemp("site") / "out"
    r = run_py(BUILD, ["--out", str(out), "--today", TODAY])
    assert r.returncode == 0, r.stderr
    return out


@pytest.fixture(scope="module")
def pn():
    return load_module(PLAYNICE, "playnice_for_site_tests")


@pytest.fixture(scope="module")
def cc():
    return load_module(REPO / "tools" / "contractctl" / "contractctl.py", "contractctl_for_site_tests")


def html_pages(site):
    return sorted(p for p in site.rglob("*.html"))


class _Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if a.get(key):
                self.links.append(a[key])


def test_every_page_passes_html_basics(site, pn):
    problems = []
    for p in html_pages(site):
        text = p.read_text()
        problems += pn.html_basics_problems(str(p.relative_to(site)), text)
        problems += pn.unsafe_html_problems(str(p.relative_to(site)), text)
    assert problems == []


def test_every_contract_and_pack_has_a_page_and_json(site, cc):
    for c in cc.load_library():
        cid = c["front_matter"]["contract_id"]
        assert (site / "contracts" / f"{cid}.html").is_file()
        data = json.loads((site / "contracts" / f"{cid}.json").read_text())
        assert data["version"] == str(c["front_matter"]["version"])
        assert [r["number"] for r in data["rules"]] == [r["number"] for r in cc.contract_rules(c["text"])]
    for card in cc.pack_cards():
        data = json.loads((site / "packs" / f"{card['pack']}.json").read_text())
        assert [e["id"] for e in data["contracts"]] == [e["id"] for e in card["contracts"]]
        assert [e["rules"] for e in data["contracts"]] == [e["rules"] for e in card["contracts"]]


def test_internal_links_and_anchors_resolve(site):
    ids = {}
    broken = []
    for p in html_pages(site):
        parser = _Links()
        parser.feed(p.read_text())
        ids[p] = parser.ids
    for p in html_pages(site):
        if p.name == "404.html":
            continue  # absolute links to the published site
        parser = _Links()
        parser.feed(p.read_text())
        for link in parser.links:
            parts = urlsplit(link)
            if parts.scheme or link.startswith("//"):
                continue
            target = (p.parent / parts.path).resolve() if parts.path else p
            if not target.exists():
                broken.append(f"{p.relative_to(site)} -> {link}")
            elif parts.fragment and target.suffix == ".html" and parts.fragment not in ids.get(target, set()):
                broken.append(f"{p.relative_to(site)} -> {link} (no such anchor)")
    assert broken == []


def test_pages_hide_nothing_in_comments(site):
    # friendly-site rule 9: no text in comments; this also drops receipts
    for p in html_pages(site):
        assert "<!--" not in p.read_text(), p


def test_the_verify_data_never_holds_a_receipt_word(site, cc):
    words = {w for c in cc.load_library() for w in c["receipts"]}
    for name in ("verify.json", "verify.html", "verify.js", "index.json"):
        text = (site / name).read_text()
        assert not any(w in text for w in words), name


def test_site_claim_is_valid_and_expires(site, pn):
    claim = json.loads((site / ".well-known" / "play-nice.json").read_text())
    assert pn.validate_site_claim(claim) == []
    assert claim["version"] == (REPO / "VERSION").read_text().strip()
    assert claim["expires"] == (date.fromisoformat(TODAY) + timedelta(days=90)).isoformat()
    assert claim["packs"] == ["sites"]


def test_llms_txt_lists_every_contract(site, cc):
    text = (site / "llms.txt").read_text()
    for c in cc.load_library():
        assert f"/contracts/{c['front_matter']['contract_id']}.html" in text


def test_old_ids_redirect(site, cc):
    for old, new in cc.load_aliases().items():
        page = (site / "contracts" / f"{old}.html").read_text()
        assert f'url={new}.html' in page


def test_build_is_repeatable(site, tmp_path):
    again = tmp_path / "again"
    r = run_py(BUILD, ["--out", str(again), "--today", TODAY])
    assert r.returncode == 0, r.stderr
    first = {p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()}
    second = {p.relative_to(again): p.read_bytes() for p in again.rglob("*") if p.is_file()}
    assert first == second


def test_served_site_passes_playnice_check(site):
    # today's date, so the claim is not expired whenever the suite runs
    live = site.parent / "live"
    if live.exists():
        shutil.rmtree(live)
    r = run_py(BUILD, ["--out", str(live)])
    assert r.returncode == 0, r.stderr
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(live))
    handler.log_message = lambda *a, **k: None
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}"
        r = run_py(PLAYNICE, ["check", url, "--json"])
    finally:
        server.shutdown()
    out = json.loads(r.stdout)
    assert out["state"] == "plays nice", out
    assert {c["id"]: c["state"] for c in out["checks"]} == {
        "site-file": "healthy", "html-basics": "healthy", "llms-txt": "healthy"}


# ------------------------------------------------------- one truth: verify

def _verify_lines(cc):
    floor = next(c for c in cc.load_library() if c["front_matter"]["contract_id"] == "floor")
    word = floor["receipts"][0]
    v = cc.floor_version()
    major, minor, patch = (int(x) for x in v.split("."))
    older = f"{major}.{minor}.{patch - 1}" if patch else f"{major - 1}.9.0" if not minor else f"{major}.{minor - 1}.0"
    old_id = next(iter(cc.load_aliases()))
    return [
        f"Play-Nice floor {v} · receipt {word}",
        f"Play-Nice floor {v} · receipt {word} · read floor, bounded-work",
        f"Play-Nice floor {v} - receipt {word} | read {old_id}",
        f"Play-Nice floor {'.'.join(v.split('.')[:2])} · receipt {word}",
        f"Play-Nice floor {v} · receipt wrong-word-here",
        f"Play-Nice floor {older} · receipt {word}",
        f"Play-Nice floor 99.0.0 · receipt {word}",
        f"Play-Nice floor {v} · receipt {word} · read no-such-contract",
        f"Play-Nice floor {v} · receipt {word} · read Web-UI",
        f"Play-Nice floor {v} · receipt {word} · read",
        f"Play-Nice floor {v} · receipt {word} · read floor · extra",
        f"Play-Nice floor {v} · receipt Not_A_Word",
        f"Play-Nice floor {v} · reciept {word}",
        f"Play-Nice floor {v}",
        "Play-Nice floor v1 · receipt x",
        "Play-Nice floor",
        "hello there",
        "   ",
    ]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_verify_page_answers_like_playnice_verify(site, cc, tmp_path):
    lines = _verify_lines(cc)
    want = []
    for line in lines:
        r = run_py(PLAYNICE, ["verify", line, "--json"])
        out = json.loads(r.stdout)
        want.append({k: out.get(k) for k in ("state", "message", "next")})
    script = tmp_path / "run.js"
    script.write_text(
        "const v = require(process.argv[2]);\n"
        "const data = JSON.parse(require('fs').readFileSync(process.argv[3], 'utf8'));\n"
        "const lines = JSON.parse(require('fs').readFileSync(process.argv[4], 'utf8'));\n"
        "const sha = t => Promise.resolve(require('crypto').createHash('sha256').update(t, 'utf8').digest('hex'));\n"
        "Promise.all(lines.map(l => v.verify(l, data, sha))).then(r => console.log(JSON.stringify(r)));\n"
    )
    (tmp_path / "lines.json").write_text(json.dumps(lines))
    r = subprocess.run(["node", str(script), str(site / "verify.js"), str(site / "verify.json"),
                        str(tmp_path / "lines.json")], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    got = json.loads(r.stdout)
    assert len(got) == len(want)
    for line, g, w in zip(lines, got, want):
        assert g == w, line
    assert {w["state"] for w in want} == {"CURRENT", "OUT_OF_DATE", "INVALID"}


def test_verify_page_text_matches_the_floor(site, cc):
    text = (site / "verify.html").read_text()
    assert f"for floor {cc.floor_version()}" in text
    assert re.search(r'<label for="line">', text)
