#!/usr/bin/env python3
"""build_site.py — the Play-Nice website, generated from contracts/.

    python3 tools/site/build_site.py [--out _site] [--today YYYY-MM-DD]

Standard library only. Every page is built from the library itself, so the
site cannot drift from the contracts:

  index.html               the floor, a three-line start, and the packs
  packs/<pack>.html        the pack card (contractctl pack_cards())
  contracts/<id>.html      one page per contract; old ids redirect
  verify.html              paste a proof line: CURRENT / OUT OF DATE / INVALID
  .well-known/play-nice.json, llms.txt, robots.txt, 404.html

Each page has its facts as JSON beside it (index.json, packs/<pack>.json,
contracts/<id>.json, verify.json), from the same data as the HTML. Receipt
words are never published: verify.json holds only the SHA-256 of the
floor's receipt word, and contract pages drop the receipt comment.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import importlib.util
import json
import posixpath
import re
import shutil
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
GITHUB = "https://github.com/rylee-bee-labs/play-nice-contracts"
SITE_URL = "https://rylee-bee-labs.github.io/play-nice-contracts"
SITE_PACKS = ["sites"]  # the packs this site claims; keep it honest (friendly-site rule 5)
CLAIM_DAYS = 90  # the claim expires this long after a build; CI rebuilds weekly
START_LINES = (
    ("install the command", "uv tool install git+" + GITHUB),
    ("set a repo up", "playnice start"),
    ("check it", "playnice check ."),
)


def load_contractctl():
    path = REPO / "tools" / "contractctl" / "contractctl.py"
    spec = importlib.util.spec_from_file_location("contractctl_for_site", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------------- markdown

_LIST_RE = re.compile(r"^( *)([-*]|\d+\.)[ \t]+")
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*?)[ \t#]*$")


def slug(text: str) -> str:
    """A heading anchor the way GitHub makes them."""
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _starts_block(line: str) -> bool:
    s = line.lstrip(" ")
    return bool(_HEADING_RE.match(s) or s.startswith(("```", "|", ">")) or _LIST_RE.match(line))


def inline(text: str, link) -> str:
    """Markdown inline syntax to HTML; everything else is escaped."""
    keep: list[str] = []

    def hold(s: str) -> str:
        keep.append(s)
        return f"\x00{len(keep) - 1}\x00"

    text = re.sub(r"`([^`]+)`", lambda m: hold(f"<code>{html.escape(m.group(1))}</code>"), text)

    def a_link(m):
        label, url = m.group(1), m.group(2)
        return hold(f'<a href="{html.escape(link(url))}">{inline(label, link)}</a>')

    text = re.sub(r"!?\[([^\]]+)\]\(([^)\s]+)\)", a_link, text)
    text = re.sub(r"<(https?://[^>\s]+)>",
                  lambda m: hold(f'<a href="{html.escape(m.group(1))}">{html.escape(m.group(1))}</a>'),
                  text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"(?<![\w*])\*(?![\s*])(.+?)(?<![\s*])\*(?![\w*])", r"<em>\1</em>", text, flags=re.S)
    text = re.sub(r"(?<!\w)_(?![\s_])(.+?)(?<![\s_])_(?!\w)", r"<em>\1</em>", text, flags=re.S)
    while "\x00" in text:
        text = re.sub(r"\x00(\d+)\x00", lambda m: keep[int(m.group(1))], text)
    return text


def markdown(text: str, link) -> str:
    """The Markdown this library writes (headings, lists, tables, code,
    quotes, paragraphs) as HTML. HTML comments are dropped."""
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return _blocks(text.split("\n"), link)


def _blocks(lines: list[str], link) -> str:
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s:
            i += 1
            continue
        if s.startswith("```"):
            body = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(body)) + "</code></pre>")
            continue
        m = _HEADING_RE.match(s)
        if m and _indent(line) < 4:
            level, title = len(m.group(1)), m.group(2)
            out.append(f'<h{level} id="{slug(title)}">{inline(title, link)}</h{level}>')
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            out.append(_table(rows, link))
            continue
        if s.startswith(">"):
            body = []
            while i < n and lines[i].strip().startswith(">"):
                body.append(re.sub(r"^\s*> ?", "", lines[i]))
                i += 1
            out.append("<blockquote>" + _blocks(body, link) + "</blockquote>")
            continue
        if _LIST_RE.match(line):
            html_list, i = _list(lines, i, link)
            out.append(html_list)
            continue
        para = [s]
        i += 1
        while i < n and lines[i].strip() and not _starts_block(lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>" + inline("\n".join(para), link) + "</p>")
    return "\n".join(out)


def _list(lines: list[str], i: int, link) -> tuple[str, int]:
    first = _LIST_RE.match(lines[i])
    indent, ordered = len(first.group(1)), first.group(2)[-1] == "."
    items: list[list[str]] = []
    n = len(lines)
    while i < n:
        m = _LIST_RE.match(lines[i])
        if not (m and len(m.group(1)) == indent and (m.group(2)[-1] == ".") == ordered):
            break
        col = m.end()
        body = [lines[i][col:]]
        i += 1
        while i < n:
            ln = lines[i]
            if not ln.strip():
                j = i + 1
                while j < n and not lines[j].strip():
                    j += 1
                if j < n and _indent(lines[j]) > indent:
                    body.append("")
                    i += 1
                    continue
                break
            if _indent(ln) > indent:
                body.append(ln[min(col, _indent(ln)):])
            elif not _starts_block(ln) and body[-1].strip():
                body.append(ln.strip())  # lazy continuation of the item's text
            else:
                break
            i += 1
        items.append(body)
    tag = "ol" if ordered else "ul"
    start = int(first.group(2)[:-1]) if ordered else 1
    attr = f' start="{start}"' if ordered and start != 1 else ""
    parts = []
    for body in items:
        inner = _blocks(body, link)
        if inner.startswith("<p>") and inner.count("<p>") == 1 and "" not in body:
            inner = inner[3:].replace("</p>", "", 1)
        parts.append(f"<li>{inner}</li>")
    return f"<{tag}{attr}>" + "".join(parts) + f"</{tag}>", i


def _table(rows: list[str], link) -> str:
    def cells(row: str) -> list[str]:
        row = row.strip().strip("|")
        return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", row)]

    head = cells(rows[0])
    body = [cells(r) for r in rows[2:]] if len(rows) > 1 else []
    out = ['<div class="table-wrap" role="region" tabindex="0" aria-label="Table">', "<table>",
           "<thead><tr>" + "".join(f'<th scope="col">{inline(c, link)}</th>' for c in head) + "</tr></thead>",
           "<tbody>"]
    for r in body:
        out.append("<tr>" + "".join(f"<td>{inline(c, link)}</td>" for c in r) + "</tr>")
    out += ["</tbody>", "</table>", "</div>"]
    return "\n".join(out)


# ------------------------------------------------------------- the site


class Site:
    def __init__(self, cc, out: Path, today: date):
        self.cc = cc
        self.out = out
        self.today = today
        self.lib = cc.load_library()
        self.cards = cc.pack_cards(self.lib)
        self.library_version = cc.library_version()
        self.floor_version = cc.floor_version()
        self.by_path = {c["rel_path"]: c["front_matter"]["contract_id"] for c in self.lib}
        self.by_id = {c["front_matter"]["contract_id"]: c for c in self.lib}
        # an old id gets a redirect page, unless a live contract still uses it
        self.aliases = {k: v for k, v in cc.load_aliases().items()
                        if v in self.by_id and k not in self.by_id}
        r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short=12", "HEAD"],
                           capture_output=True, text=True)
        self.commit = r.stdout.strip() if r.returncode == 0 else "unknown"
        self.pages: list[tuple[str, str, str]] = []  # (path, title, description) for llms.txt

    # -- links

    def site_path(self, repo_rel: str) -> str | None:
        """The site page for a repo path, or None when it has none."""
        repo_rel = repo_rel.rstrip("/")
        if repo_rel in self.by_path:
            return f"contracts/{self.by_path[repo_rel]}.html"
        m = re.fullmatch(r"contracts/([a-z]+)(?:/README\.md)?", repo_rel)
        if m and m.group(1) in self.cc.LAYER_DIRS:
            return f"packs/{m.group(1)}.html"
        if repo_rel in ("CONTRACT_INDEX.md", "README.md", ""):
            return "index.html"
        return None

    def linker(self, source_rel: str, page: str):
        """Rewrite a Markdown link from repo file `source_rel` for site page `page`."""
        page_dir = posixpath.dirname(page)

        def link(url: str) -> str:
            if re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I) or url.startswith("#"):
                return url
            path, _, frag = url.partition("#")
            target = posixpath.normpath(posixpath.join(posixpath.dirname(source_rel), path))
            target = "" if target == "." else target
            page_for = self.site_path(target)
            if page_for:
                href = posixpath.relpath(page_for, page_dir or ".")
            else:
                kind = "tree" if (REPO / target).is_dir() else "blob"
                href = f"{GITHUB}/{kind}/main/{target}"
            return href + (f"#{frag}" if frag else "")

        return link

    def rel(self, page: str, target: str) -> str:
        return posixpath.relpath(target, posixpath.dirname(page) or ".")

    # -- writing

    def write(self, path: str, text: str) -> None:
        dest = self.out / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8", newline="\n")

    def write_json(self, path: str, data) -> None:
        self.write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")

    def page(self, path: str, title: str, description: str, body: str,
             json_path: str | None = None, crumbs: list[tuple[str, str]] | None = None,
             scripts: tuple[str, ...] = (), record: bool = True) -> None:
        r = lambda t: self.rel(path, t)  # noqa: E731
        nav = [("index.html", "Home"), ("index.html#packs", "Packs"),
               ("verify.html", "Check a proof line")]
        current = ' aria-current="page"'
        nav_html = "".join(
            f'<li><a href="{r(t)}"{current if t == path else ""}>{label}</a></li>'
            for t, label in nav
        ) + f'<li><a href="{GITHUB}">Source</a></li>'
        crumb_html = ""
        if crumbs:
            items = "".join(f'<li><a href="{r(t)}">{html.escape(label)}</a></li>' for t, label in crumbs)
            crumb_html = (f'<nav class="crumbs" aria-label="Breadcrumb"><ol>{items}'
                          f'<li aria-current="page">{html.escape(title)}</li></ol></nav>')
        alt = (f'<link rel="alternate" type="application/json" href="{r(json_path)}">'
               if json_path else "")
        as_json = (f' · <a href="{r(json_path)}">This page as JSON</a>' if json_path else "")
        script_tags = "".join(f'<script src="{r(s)}" defer></script>' for s in scripts)
        doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Play-Nice</title>
<meta name="description" content="{html.escape(description)}">
<link rel="stylesheet" href="{r('site.css')}">
<link rel="icon" href="{r('bee.svg')}" type="image/svg+xml">
{alt}{script_tags}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site">
<a class="brand" href="{r('index.html')}"><img src="{r('bee.svg')}" alt="" width="32" height="32"><span>Play-Nice</span></a>
<nav aria-label="Site"><ul>{nav_html}</ul></nav>
</header>
<main id="main">
{crumb_html}
{body}
</main>
<footer>
<div class="inner">
<p>Library {self.library_version} · floor {self.floor_version} · built from
<a href="{GITHUB}/commit/{self.commit}">{self.commit}</a> on {self.today.isoformat()}{as_json}</p>
<p>Contract text: CC BY-SA 4.0. Tools: MIT.
<a href="{GITHUB}/blob/main/contracts/LICENSE.md">License map</a>.</p>
<p class="buzzby"><span aria-hidden="true">🐝</span> Buzzby says: every page here is built
from the contracts on each change, so it says what the library says.</p>
</div>
</footer>
</body>
</html>
"""
        self.write(path, doc)
        if record:
            self.pages.append((path, title, description))

    # -- pages

    def build(self) -> None:
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        shutil.copyfile(HERE / "site.css", self.out / "site.css")
        shutil.copyfile(HERE / "verify.js", self.out / "verify.js")
        shutil.copyfile(REPO / "assets" / "badge" / "bee.svg", self.out / "bee.svg")
        self.write(".nojekyll", "")
        self.home()
        for card in self.cards:
            self.pack_page(card)
        for c in self.lib:
            self.contract_page(c)
        for old, new in sorted(self.aliases.items()):
            self.redirect_page(old, new)
        self.verify_page()
        self.not_found()
        self.well_known()
        self.llms_and_robots()

    def _floor_rules_html(self, page: str) -> str:
        floor = self.by_id["floor"]
        rules = self.cc.contract_section(floor["text"], "Rules")
        return markdown(rules, self.linker(floor["rel_path"], page))

    def _what_this_is(self) -> str:
        text = (REPO / "README.md").read_text(encoding="utf-8")
        m = re.search(r"(?ms)^## What this is\s*\n(.*?)(?=^## )", text)
        return " ".join(m.group(1).split()) if m else ""

    def home(self) -> None:
        path = "index.html"
        intro = self._what_this_is()
        start = "\n".join(f"# {why}\n{cmd}" for why, cmd in START_LINES)
        packs = []
        for card in self.cards:
            n = len(card["contracts"])
            packs.append(
                f'<li><a href="packs/{card["pack"]}.html">{html.escape(card["title"])}</a>: '
                f'{html.escape(card["blurb"])} <span class="facts">({n} contract{"s" if n != 1 else ""})</span></li>'
            )
        body = f"""<h1>Play-Nice</h1>
<p class="lead">{html.escape(intro)}</p>
<h2 id="start">Start in three lines</h2>
<pre><code>{html.escape(start)}</code></pre>
<p>Agents: start each handoff with a proof line naming the floor version, its
receipt word and the contracts you read, then <a href="verify.html">check it</a>.</p>
<h2 id="floor">The floor</h2>
<p>Version {self.floor_version}. One page that everyone agrees to first; every pack
goes deeper and none may go below it. <a href="contracts/floor.html">The floor on its own page</a>.</p>
{self._floor_rules_html(path)}
<h2 id="packs">The packs</h2>
<p>Each pack goes deeper for one kind of work. A pack page shows every contract in
short, with the rules it marks MUST.</p>
<ul class="packs">{''.join(packs)}</ul>
"""
        self.page(path, "Play-Nice", "Shared rules for people, agents, tools and sites: "
                  "one short floor, plus packs that go deeper.", body, json_path="index.json")
        floor = self.by_id["floor"]
        self.write_json("index.json", {
            "schema": "play-nice/site-home-v1",
            "library_version": self.library_version,
            "floor_version": self.floor_version,
            "commit": self.commit,
            "built": self.today.isoformat(),
            "intro": intro,
            "start": [{"command": cmd, "does": why} for why, cmd in START_LINES],
            "floor": {
                "page": "contracts/floor.html",
                "rules": [{"number": r["number"], "text": r["text"]}
                          for r in self.cc.contract_rules(floor["text"])],
            },
            "packs": [{"pack": c["pack"], "title": c["title"], "blurb": c["blurb"],
                       "page": f"packs/{c['pack']}.html", "json": f"packs/{c['pack']}.json",
                       "contracts": [e["id"] for e in c["contracts"]]} for c in self.cards],
            "verify": "verify.html",
        })

    def pack_page(self, card: dict) -> None:
        path = f"packs/{card['pack']}.html"
        md = self.cc.render_card(card)
        body = markdown(md, self.linker(card["path"], path))
        self.page(path, card["title"], card["blurb"] or f"The {card['title']} pack.", body,
                  json_path=f"packs/{card['pack']}.json", crumbs=[("index.html", "Home")])
        data = {k: v for k, v in card.items()}
        data["contracts"] = [
            {**e, "page": f"contracts/{e['id']}.html", "json": f"contracts/{e['id']}.json"}
            for e in card["contracts"]
        ]
        self.write_json(f"packs/{card['pack']}.json", {"schema": "play-nice/site-pack-v1", **data})

    def contract_page(self, c: dict) -> None:
        fm = c["front_matter"]
        cid = fm["contract_id"]
        pack = str(fm.get("layer", ""))
        path = f"contracts/{cid}.html"
        text = self.cc.FM_RE.sub("", c["text"], count=1)
        body_md = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip() + "\n"
        title = str(fm.get("title", cid))
        # the page's own H1 is the contract's "# Title" line
        facts = (f'<p class="facts"><code>{html.escape(cid)}</code> · version '
                 f'{html.escape(str(fm.get("version", "")))} · {html.escape(str(fm.get("status", "")))} · '
                 f'<a href="../packs/{pack}.html">{html.escape(self.cc.PACK_TITLES.get(pack, pack))} pack</a> · '
                 f'<a href="{GITHUB}/blob/main/{c["rel_path"]}">source</a></p>')
        rendered = markdown(body_md, self.linker(c["rel_path"], path))
        rendered = rendered.replace("</h1>", "</h1>\n" + facts, 1)
        self.page(path, title, str(fm.get("rationale", "")), rendered,
                  json_path=f"contracts/{cid}.json",
                  crumbs=[("index.html", "Home"),
                          (f"packs/{pack}.html", self.cc.PACK_TITLES.get(pack, pack))])
        self.write_json(f"contracts/{cid}.json", {
            "schema": "play-nice/site-contract-v1",
            "id": cid,
            "title": title,
            "version": str(fm.get("version", "")),
            "status": str(fm.get("status", "")),
            "pack": pack,
            "applies": fm.get("applies", []),
            "triggers": fm.get("triggers", []),
            "rationale": str(fm.get("rationale", "")),
            "in_short": " ".join(self.cc.contract_section(c["text"], "In short").split()),
            "rules": [{"number": r["number"], "text": r["text"], "must": r["must"]}
                      for r in self.cc.contract_rules(c["text"])],
            "source": f"{GITHUB}/blob/main/{c['rel_path']}",
            "markdown": body_md,
            "page": path,
        })

    def redirect_page(self, old: str, new: str) -> None:
        path = f"contracts/{old}.html"
        title = self.by_id[new]["front_matter"].get("title", new)
        body = (f"<h1>This contract has a new name</h1>\n<p><code>{html.escape(old)}</code> is "
                f'now <a href="{new}.html">{html.escape(str(title))}</a> (<code>{html.escape(new)}</code>).</p>')
        self.page(path, f"Moved: {old}", f"{old} is now {new}.", body, record=False)
        dest = self.out / path
        doc = dest.read_text(encoding="utf-8")
        doc = doc.replace('<meta charset="utf-8">',
                          f'<meta charset="utf-8">\n<meta http-equiv="refresh" content="0; url={new}.html">'
                          f'\n<link rel="canonical" href="{new}.html">', 1)
        dest.write_text(doc, encoding="utf-8", newline="\n")

    def verify_data(self) -> dict:
        floor = self.by_id["floor"]
        receipt = floor["receipts"][0]
        return {
            "schema": "play-nice/site-verify-v1",
            "floor_version": self.floor_version,
            "floor_path": "contracts/everyone/FLOOR.md",
            "receipt_sha256": hashlib.sha256(receipt.encode("utf-8")).hexdigest(),
            "contract_ids": sorted(self.by_id),
            "aliases": dict(sorted(self.aliases.items())),
        }

    def verify_page(self) -> None:
        path = "verify.html"
        self.write_json("verify.json", self.verify_data())
        body = f"""<h1>Check a proof line</h1>
<p>Paste the line an agent put at the top of its handoff. This page gives the same
answer as <code>playnice verify</code>, for floor {self.floor_version}.</p>
<form id="verify-form" class="verify" action="verify.html" method="get">
<label for="line">Proof line</label>
<div class="row">
<input id="line" name="line" type="text" autocomplete="off" spellcheck="false"
 placeholder="Play-Nice floor {self.floor_version} · receipt &lt;word&gt; · read floor">
<button type="submit">Check</button>
</div>
</form>
<div id="result" class="result" role="status" aria-live="polite" hidden></div>
<noscript><p>Checking on this page needs JavaScript. Without it, run
<code>playnice verify "&lt;the line&gt;"</code>.</p></noscript>
<h2 id="answers">What the answers mean</h2>
<dl>
<dt>CURRENT</dt><dd>The floor version and the receipt word match this library.</dd>
<dt>OUT OF DATE</dt><dd>The line names an older floor. Re-read <a href="contracts/floor.html">the floor</a> and write a fresh line.</dd>
<dt>INVALID</dt><dd>The line is malformed, names a contract that does not exist, or has a receipt word that is not on the floor.</dd>
</dl>
<h2 id="how">How it checks</h2>
<p>The page never shows the receipt word: it compares a SHA-256 of the word you paste
with <a href="verify.json">verify.json</a>, which is built from the floor. Nothing you
paste leaves your browser.</p>
<p>A proof line records what an agent declares it read. Checking it shows the line is
valid and current; it does not prove the rules were understood or followed.</p>
"""
        self.page(path, "Check a proof line", "Paste a Play-Nice proof line and see whether "
                  "it is current.", body, json_path="verify.json",
                  crumbs=[("index.html", "Home")], scripts=("verify.js",))

    def not_found(self) -> None:
        body = ('<h1>No page here</h1>\n<p>This address has no page. Contract pages live at '
                '<code>contracts/&lt;id&gt;.html</code>; old ids redirect to their new names.</p>\n'
                '<p>Next: <a href="index.html">the home page</a> lists the floor and every pack.</p>')
        self.page("404.html", "No page here", "This address has no page.", body, record=False)
        # GitHub Pages serves 404.html at any depth: make its links absolute
        dest = self.out / "404.html"
        doc = dest.read_text(encoding="utf-8")
        base = SITE_URL.rstrip("/") + "/"
        doc = re.sub(r'(href|src)="(?!https?:|#|/)([^"]*)"', lambda m: f'{m.group(1)}="{base}{m.group(2)}"', doc)
        dest.write_text(doc, encoding="utf-8", newline="\n")

    def site_claim(self) -> dict:
        return {
            "version": self.library_version,
            "packs": SITE_PACKS,
            "contact": f"{GITHUB}/issues",
            "expires": (self.today + timedelta(days=CLAIM_DAYS)).isoformat(),
        }

    def well_known(self) -> None:
        self.write_json(".well-known/play-nice.json", self.site_claim())

    def llms_and_robots(self) -> None:
        base = SITE_URL.rstrip("/")
        lines = ["# Play-Nice", "",
                 "> Shared rules for people, agents, tools and sites: one short floor, "
                 "plus packs that go deeper. Every page has its facts as JSON beside it.", "",
                 "## Start", "",
                 f"- [The floor and the packs]({base}/index.html): the home page "
                 f"([JSON]({base}/index.json))",
                 f"- [Check a proof line]({base}/verify.html) ([JSON]({base}/verify.json))", "",
                 "## Packs", ""]
        for card in self.cards:
            lines.append(f"- [{card['title']}]({base}/packs/{card['pack']}.html): {card['blurb']} "
                         f"([JSON]({base}/packs/{card['pack']}.json))")
        lines += ["", "## Contracts", ""]
        for card in self.cards:
            for e in card["contracts"]:
                lines.append(f"- [{e['title']}]({base}/contracts/{e['id']}.html): {e['in_short']}")
        lines += ["", "## Source", "", f"- [The library on GitHub]({GITHUB})", ""]
        self.write("llms.txt", "\n".join(lines))
        self.write("robots.txt", "User-agent: *\nAllow: /\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="build_site.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(REPO / "_site"), help="output folder (default: _site)")
    ap.add_argument("--today", default=None, help="build date, YYYY-MM-DD (default: today, UTC)")
    args = ap.parse_args(argv)
    today = date.fromisoformat(args.today) if args.today else date.today()
    cc = load_contractctl()
    site = Site(cc, Path(args.out).resolve(), today)
    try:
        site.build()
    except cc.CTError as e:
        print(f"SITE: FAILED — {e}", file=sys.stderr)
        return 1
    count = sum(1 for _ in site.out.rglob("*.html"))
    print(f"SITE: built {count} pages in {site.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
