"""Play-Nice v2 tool surface: verify / check / start + manifest-free resolve.

Covers every command, state and exit code from the v2 plan step-4 brief
(docs/decisions/2026-09-26-play-nice-v2.md). Fully offline: URL mode runs
against a local http.server bound to 127.0.0.1 on an ephemeral port; no
test touches the internet. Libraries resolve via PLAY_NICE_LIBRARY pointed
at this checkout; floor version and receipt are read from the floor page,
never hard-coded (evidence over memory).
"""

import functools
import http.server
import json
import os
import re
import socket
import subprocess
import sys
import threading
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
PLAYNICE = REPO / "tools" / "playnice" / "playnice.py"
CONTRACTCTL = REPO / "tools" / "contractctl" / "contractctl.py"

_FLOOR_TEXT = (REPO / "contracts" / "everyone" / "FLOOR.md").read_text(encoding="utf-8")
FLOOR_V = re.search(r"(?m)^version:\s*(\S+)", _FLOOR_TEXT).group(1)
FLOOR_R = re.search(r"<!--\s*contract-receipt:\s*([a-z0-9-]+)", _FLOOR_TEXT).group(1)

MARK_START = "<!-- play-nice:start -->"
MARK_END = "<!-- play-nice:end -->"
FUTURE = (date.today() + timedelta(days=90)).isoformat()
PAST = (date.today() - timedelta(days=1)).isoformat()


def run_pn(args, cwd, extra_env=None):
    env = {**os.environ, "PLAY_NICE_LIBRARY": str(REPO)}
    env.update(extra_env or {})
    return subprocess.run(
        [sys.executable, str(PLAYNICE), *args],
        capture_output=True, text=True, cwd=str(cwd), env=env, timeout=120,
    )


def run_ct(args, cwd):
    return subprocess.run(
        [sys.executable, str(CONTRACTCTL), *args],
        capture_output=True, text=True, cwd=str(cwd), timeout=120,
    )


def agents_block(version=FLOOR_V):
    return (
        f"{MARK_START}\n"
        f"This project follows Play-Nice (floor {version}).\n\n"
        "1. **Say what's true, and how you know.**\n\n"
        f"Start each handoff with: Play-Nice floor {version} · receipt {FLOOR_R}\n"
        f"{MARK_END}\n"
    )


GOOD_PAGE = (
    '<!doctype html><html lang="en"><head><title>t</title></head><body>\n'
    "<h1>Hi</h1>\n<h2>Sub</h2>\n"
    '<img src="a.png" alt="a cat">\n'
    '<form><label for="q">Question</label><input id="q" type="text"></form>\n'
    "</body></html>\n"
)


def library_head():
    r = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True
    )
    return r.stdout.strip()


# ------------------------------------------------------------------ verify


def test_verify_current_plain_and_json(tmp_path):
    r = run_pn(["verify", f"Play-Nice floor {FLOOR_V} · receipt {FLOOR_R}"], tmp_path)
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout.startswith("CURRENT")
    assert "next:" in r.stdout
    j = run_pn(
        ["verify", f"Play-Nice floor {FLOOR_V} · receipt {FLOOR_R}", "--json"], tmp_path
    )
    data = json.loads(j.stdout)
    assert data["state"] == "CURRENT" and data["exit"] == 0
    assert data["floor_version"] == FLOOR_V


def test_verify_accepts_dash_and_bar_separators(tmp_path):
    for sep in ("-", "|"):
        r = run_pn(["verify", f"Play-Nice floor {FLOOR_V} {sep} receipt {FLOOR_R}"], tmp_path)
        assert r.returncode == 0, f"sep {sep}: {r.stdout}"


def test_verify_read_part_with_current_and_old_alias_ids(tmp_path):
    line = f"Play-Nice floor {FLOOR_V} · receipt {FLOOR_R} · read floor, assume-unknown, web-ui"
    r = run_pn(["verify", line, "--json"], tmp_path)
    assert r.returncode == 0, r.stdout
    data = json.loads(r.stdout)
    assert data["state"] == "CURRENT"
    assert data["given"]["read"] == ["floor", "assume-unknown", "web-ui"]


def test_verify_out_of_date_old_version(tmp_path):
    r = run_pn(["verify", f"Play-Nice floor 0.9.0 · receipt {FLOOR_R}"], tmp_path)
    assert r.returncode == 1
    assert f"OUT OF DATE: floor is now {FLOOR_V}, read contracts/everyone/FLOOR.md" in r.stdout


def test_verify_newer_floor_than_library_is_invalid_not_out_of_date(tmp_path):
    """A floor this library has never had is not "out of date": re-reading the
    current floor would not help, so say what the two possibilities are."""
    major = int(FLOOR_V.split(".")[0]) + 1
    r = run_pn(["verify", f"Play-Nice floor {major}.0.0 · receipt {FLOOR_R}", "--json"], tmp_path)
    assert r.returncode == 2, r.stdout
    data = json.loads(r.stdout)
    assert data["state"] == "INVALID"
    assert "newer than this library" in data["message"] and "git pull" in data["next"]
    assert FLOOR_R not in data["message"] + data["next"]


def test_verify_wrong_receipt_on_current_version_is_invalid(tmp_path):
    r = run_pn(["verify", f"Play-Nice floor {FLOOR_V} · receipt wrong-word-here"], tmp_path)
    assert r.returncode == 2
    assert "not on floor" in r.stdout
    assert FLOOR_R not in r.stdout + r.stderr


def test_verify_invalid_malformed_shows_example(tmp_path):
    r = run_pn(["verify", "I read the rules, promise"], tmp_path)
    assert r.returncode == 2
    assert "INVALID:" in r.stdout
    assert f"example: Play-Nice floor {FLOOR_V} · receipt <word from the floor>" in r.stdout
    # The receipt word is the proof of reading: verify never reveals it.
    assert FLOOR_R not in r.stdout + r.stderr
    j = run_pn(["verify", "I read the rules, promise", "--json"], tmp_path)
    assert FLOOR_R not in j.stdout


def test_verify_invalid_bad_version_shape(tmp_path):
    r = run_pn(["verify", "Play-Nice floor two-point-oh · receipt amber-reef-fog"], tmp_path)
    assert r.returncode == 2
    assert "INVALID:" in r.stdout and "1.0.0" in r.stdout


def test_verify_invalid_unknown_read_id_names_it(tmp_path):
    line = f"Play-Nice floor {FLOOR_V} · receipt {FLOOR_R} · read floor, not-a-thing"
    r = run_pn(["verify", line, "--json"], tmp_path)
    assert r.returncode == 2
    data = json.loads(r.stdout)
    assert data["state"] == "INVALID" and data["exit"] == 2
    assert "not-a-thing" in data["message"]


def test_verify_could_not_find_library_exits_two(tmp_path):
    empty = tmp_path / "nowhere"
    empty.mkdir()
    r = run_pn(
        ["verify", f"Play-Nice floor {FLOOR_V} · receipt {FLOOR_R}"],
        tmp_path,
        extra_env={"PLAY_NICE_LIBRARY": str(empty)},
    )
    assert r.returncode == 2
    assert "INVALID:" in r.stdout and "PLAY_NICE_LIBRARY" in r.stdout


# ---------------------------------------------------------------- check: repo


def test_check_missing_path_could_not_check(tmp_path):
    r = run_pn(["check", str(tmp_path / "no-such-folder")], tmp_path)
    assert r.returncode == 2
    assert "could not check" in r.stdout


def test_check_clean_repo_plays_nice(tmp_path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)  # nothing to scan beyond the block
    (repo / "AGENTS.md").write_text(agents_block(), encoding="utf-8")
    (repo / "notes.txt").write_text("a plain file with nothing banned\n", encoding="utf-8")
    r = run_pn(["check", str(repo), "--json"], tmp_path)
    assert r.returncode == 0, r.stdout
    data = json.loads(r.stdout)
    assert data["state"] == "plays nice"
    assert data["label"] == f"plays nice · v{FLOOR_V}"
    ids = {c["id"]: c for c in data["checks"]}
    assert ids["agents-file"]["state"] == "healthy"
    assert ids["html-basics"]["state"] == "not_configured"
    assert ids["secrets"]["state"] == "healthy"
    assert ids["adoption"]["state"] == "not_configured"
    assert ids["unsafe-html"]["state"] == "not_configured"
    # the replaced words stay in JSON for one release
    assert ids["agents-file"]["legacy_state"] == "worked"
    assert ids["adoption"]["legacy_state"] == "skipped"


def test_check_missing_agents_fix_needed_points_at_start(tmp_path):
    repo = tmp_path / "repo2"
    repo.mkdir()
    r = run_pn(["check", str(repo)], tmp_path)
    assert r.returncode == 1
    assert "STATE: fix needed" in r.stdout
    assert "no AGENTS.md" in r.stdout
    assert "fix: playnice start" in r.stdout


def test_check_html_basics_problems_report_file_line(tmp_path):
    repo = tmp_path / "webbad"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(agents_block(), encoding="utf-8")
    (repo / "index.html").write_text(
        '<!doctype html><html><head><title>x</title></head><body>\n'
        "<h1>A</h1>\n<h3>C</h3>\n"
        '<img src="a.png">\n'
        '<form><input id="email" type="text"></form>\n'
        "</body></html>\n",
        encoding="utf-8",
    )
    r = run_pn(["check", str(repo)], tmp_path)
    assert r.returncode == 1
    out = r.stdout
    assert "index.html:3: heading skips a level" in out
    assert "index.html:4: <img> has no alt attribute" in out
    assert "index.html:5: <input id=email> has no label" in out
    assert "<html> has no lang attribute" in out
    assert "STATE: fix needed" in out
    # aria-label and wrapping controls pass
    (repo / "index.html").write_text(GOOD_PAGE, encoding="utf-8")
    r2 = run_pn(["check", str(repo)], tmp_path)
    assert r2.returncode == 0, r2.stdout


def test_check_unsafe_html_flags_built_innerHTML(tmp_path):
    repo = tmp_path / "webunsafe"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(agents_block(), encoding="utf-8")
    (repo / "index.html").write_text(GOOD_PAGE, encoding="utf-8")
    (repo / "app.js").write_text(
        "fetch('/api').then(r => r.json()).then(d => {\n"
        "  document.getElementById('out').innerHTML = `<p>${d.name}</p>`;\n"
        "});\n",
        encoding="utf-8",
    )
    r = run_pn(["check", str(repo)], tmp_path)
    assert r.returncode == 1
    assert "app.js:2: innerHTML is assigned a built string" in r.stdout
    assert "fix: use textContent or escape" in r.stdout
    (repo / "app.js").write_text(
        "fetch('/api').then(r => r.json()).then(d => {\n"
        "  document.getElementById('out').textContent = d.name;\n"
        "});\n",
        encoding="utf-8",
    )
    r2 = run_pn(["check", str(repo)], tmp_path)
    assert r2.returncode == 0, r2.stdout


def test_check_secrets_reuses_contractctl_scan(tmp_path):
    repo = tmp_path / "secretspot"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(agents_block(), encoding="utf-8")
    # built at runtime so this test file itself never carries the shape
    (repo / "deploy.env").write_text("TOKEN=" + "gh" + "p_" + "abc123xyz\n", encoding="utf-8")
    r = run_pn(["check", str(repo)], tmp_path)
    assert r.returncode == 1
    assert "deploy.env: credential:github-token-prefix" in r.stdout
    assert "floor rule 11" in r.stdout  # the fix wording, values not echoed
    (repo / "deploy.env").write_text("TOKEN is in Vault under app/token\n", encoding="utf-8")
    r2 = run_pn(["check", str(repo)], tmp_path)
    assert r2.returncode == 0, r2.stdout


def test_check_behind_when_floor_newer_than_recorded(tmp_path):
    repo = tmp_path / "behindrepo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(agents_block("0.0.1"), encoding="utf-8")
    r = run_pn(["check", str(repo), "--json"], tmp_path)
    assert r.returncode == 1
    data = json.loads(r.stdout)
    assert data["state"] == "behind" and data["behind"] is True
    assert data["label"] == f"behind · v{FLOOR_V} is out"
    assert data["next"] == "playnice start"


def test_check_badge_written_with_state_words(tmp_path):
    repo = tmp_path / "badgerepo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(agents_block(), encoding="utf-8")
    out = repo / "b.svg"
    r = run_pn(["check", str(repo), "--badge", str(out)], tmp_path)
    assert r.returncode == 0
    svg = out.read_text(encoding="utf-8")
    assert f"plays nice · v{FLOOR_V}" in svg
    assert "<title>Play-Nice: plays nice · v" in svg and 'role="img"' in svg
    # behind and fix needed use their own templates
    (repo / "AGENTS.md").write_text(agents_block("0.0.1"), encoding="utf-8")
    r2 = run_pn(["check", str(repo), "--badge", str(out)], tmp_path)
    assert r2.returncode == 1
    assert f"behind · v{FLOOR_V} is out" in out.read_text(encoding="utf-8")
    (repo / "AGENTS.md").unlink()
    r3 = run_pn(["check", str(repo), "--badge", str(out)], tmp_path)
    assert r3.returncode == 1
    assert "fix needed" in out.read_text(encoding="utf-8")


def test_check_adoption_manifest_states(tmp_path):
    repo = tmp_path / "adoptrepo"
    (repo / ".contracts").mkdir(parents=True)
    (repo / "AGENTS.md").write_text(agents_block(), encoding="utf-8")
    base = (
        "schema: play-nice/adoption-v1\n"
        "project: t\n"
        "source:\n"
        "  repository: rylee-bee-labs/play-nice-contracts\n"
        f"  revision: {library_head()}\n"
    )
    # old ids -> worked, with suggestions of the new ids
    (repo / ".contracts" / "adoption.yaml").write_text(
        base + "always:\n  - assume-unknown\n", encoding="utf-8"
    )
    r = run_pn(["check", str(repo)], tmp_path)
    assert r.returncode == 0, r.stdout
    assert "'assume-unknown' now lives as 'truth-and-evidence'" in r.stdout
    # unknown id -> needs_fix
    (repo / ".contracts" / "adoption.yaml").write_text(
        base + "always:\n  - no-such-contract\n", encoding="utf-8"
    )
    r2 = run_pn(["check", str(repo)], tmp_path)
    assert r2.returncode == 1
    assert "no-such-contract" in r2.stdout and "not a library contract" in r2.stdout
    # stale pin -> needs_fix
    (repo / ".contracts" / "adoption.yaml").write_text(
        base.replace(library_head(), "f" * 40) + "always:\n  - truth-and-evidence\n",
        encoding="utf-8",
    )
    r3 = run_pn(["check", str(repo)], tmp_path)
    assert r3.returncode == 1
    assert "pin" in r3.stdout and "is not the current library revision" in r3.stdout


def test_check_json_and_plain_carry_the_same_states(tmp_path):
    repo = tmp_path / "parityrepo"
    repo.mkdir()
    (repo / "AGENTS.md").write_text(agents_block(), encoding="utf-8")
    (repo / "page.html").write_text("<html><body><img src='x'></body></html>", encoding="utf-8")
    plain = run_pn(["check", str(repo)], tmp_path)
    js = run_pn(["check", str(repo), "--json"], tmp_path)
    assert plain.returncode == js.returncode == 1
    data = json.loads(js.stdout)
    width = max(len(s) for s in ("healthy", "needs_attention", "not_configured"))
    for c in data["checks"]:
        assert set(c) == {"id", "name", "state", "words", "fix", "legacy_state"}
        assert c["state"] in ("healthy", "needs_attention", "not_configured")
        assert c["legacy_state"] == {"healthy": "worked", "needs_attention": "needs_fix",
                                     "not_configured": "skipped"}[c["state"]]
        if c["state"] == "needs_attention":
            assert f"{c['state']:{width}s} {c['name']}" in plain.stdout


def test_every_check_state_is_a_shared_status_word(tmp_path):
    """Floor rule 8: each per-check result `check` prints, in plain text and
    JSON, is a word from schema/status.schema.json."""
    enum = set(json.loads((REPO / "schema" / "status.schema.json").read_text())["enum"])
    sys.path.insert(0, str(REPO / "tools" / "playnice"))
    try:
        import playnice as pn
    finally:
        sys.path.pop(0)
    assert set(pn.CHECK_STATES) <= enum
    assert set(pn.LEGACY_CHECK_STATES) == set(pn.CHECK_STATES)
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "AGENTS.md").write_text(agents_block(), encoding="utf-8")
    messy = tmp_path / "messy"
    messy.mkdir()
    (messy / "page.html").write_text("<html><body><img src='x'></body></html>", encoding="utf-8")
    seen = set()
    for repo in (clean, messy, REPO):
        data = json.loads(run_pn(["check", str(repo), "--json"], tmp_path).stdout)
        plain = run_pn(["check", str(repo)], tmp_path).stdout
        for c in data["checks"]:
            seen.add(c["state"])
            assert re.search(rf"(?m)^  {re.escape(c['state'])} +{re.escape(c['name'])}:", plain)
        printed = re.findall(r"(?m)^  ([a-z_]+) +[A-Z/]", plain)
        assert printed and set(printed) <= enum, printed
    assert seen <= enum
    assert {"healthy", "needs_attention", "not_configured"} <= seen


# ---------------------------------------------------------------- check: URL


@pytest.fixture()
def serve(tmp_path):
    """Serve a dict of {relative path: text} over a local http.server."""
    import socketserver

    servers = []

    def _serve(files):
        root = tmp_path / f"www{len(servers)}"
        for rel, content in files.items():
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

        class Quiet(http.server.SimpleHTTPRequestHandler):
            def log_message(self, *a):
                pass

        srv = socketserver.ThreadingTCPServer(
            ("127.0.0.1", 0), functools.partial(Quiet, directory=str(root))
        )
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        return f"http://127.0.0.1:{srv.server_address[1]}"

    yield _serve
    for srv in servers:
        srv.shutdown()
        srv.server_close()


def claim(**over):
    data = {
        "version": FLOOR_V,
        "packs": ["sites"],
        "contact": "mailto:hello@example.org",
        "expires": FUTURE,
    }
    data.update(over)
    return json.dumps(data)


def test_check_url_good_site(tmp_path, serve):
    url = serve({
        ".well-known/play-nice.json": claim(),
        "index.html": GOOD_PAGE,
        "llms.txt": "# pages\n\n- /: home\n",
    })
    r = run_pn(["check", url, "--json"], tmp_path)
    assert r.returncode == 0, r.stdout
    data = json.loads(r.stdout)
    assert data["mode"] == "url" and data["state"] == "plays nice"
    states = {c["id"]: c["state"] for c in data["checks"]}
    assert states == {"site-file": "healthy", "html-basics": "healthy", "llms-txt": "healthy"}
    assert data["label"] == f"plays nice · v{FLOOR_V}"


def test_check_url_agent_card_https_ok(tmp_path, serve):
    url = serve({
        ".well-known/play-nice.json": claim(agent_card="https://example.org/.well-known/agent-card.json"),
        "index.html": GOOD_PAGE,
        "llms.txt": "x",
    })
    assert run_pn(["check", url], tmp_path).returncode == 0


def test_check_url_missing_claim_fix_needed(tmp_path, serve):
    url = serve({"index.html": GOOD_PAGE, "llms.txt": "x"})
    r = run_pn(["check", url], tmp_path)
    assert r.returncode == 1
    assert "makes no Play-Nice claim" in r.stdout
    assert "STATE: fix needed" in r.stdout


def test_check_url_expired_claim_is_not_current(tmp_path, serve):
    url = serve({
        ".well-known/play-nice.json": claim(expires=PAST),
        "index.html": GOOD_PAGE,
        "llms.txt": "x",
    })
    r = run_pn(["check", url], tmp_path)
    assert r.returncode == 1
    assert f"expired on {PAST}" in r.stdout


def test_check_url_invalid_fields_named(tmp_path, serve):
    url = serve({
        ".well-known/play-nice.json": json.dumps(
            {"version": "not-semver", "packs": [], "contact": "hello", "expires": "31-2027", "nope": 1}
        ),
        "index.html": GOOD_PAGE,
        "llms.txt": "x",
    })
    r = run_pn(["check", url], tmp_path)
    assert r.returncode == 1
    out = r.stdout
    assert "version must be a semantic version" in out
    assert "packs must be a non-empty list" in out
    assert "contact must be a mailto:" in out
    assert "expires must be a UTC date" in out
    assert "unknown field(s): nope" in out


def test_check_url_html_problems(tmp_path, serve):
    url = serve({
        ".well-known/play-nice.json": claim(),
        "index.html": "<html><body><img src='a'></body></html>",
        "llms.txt": "x",
    })
    r = run_pn(["check", url], tmp_path)
    assert r.returncode == 1
    assert "has no alt attribute" in r.stdout


def test_check_url_no_llms_txt_skipped_with_note(tmp_path, serve):
    url = serve({".well-known/play-nice.json": claim(), "index.html": GOOD_PAGE})
    r = run_pn(["check", url], tmp_path)
    assert r.returncode == 0, r.stdout
    assert "llms.txt" in r.stdout and "not published" in r.stdout
    assert re.search(r"(?m)^  not_configured +/llms\.txt: not published", r.stdout)
    data = json.loads(run_pn(["check", url, "--json"], tmp_path).stdout)
    enum = set(json.loads((REPO / "schema" / "status.schema.json").read_text())["enum"])
    assert {c["state"] for c in data["checks"]} <= enum


def test_check_url_site_behind_library(tmp_path, serve):
    url = serve({
        ".well-known/play-nice.json": claim(version="0.5.0"),
        "index.html": GOOD_PAGE,
        "llms.txt": "x",
    })
    r = run_pn(["check", url, "--json"], tmp_path)
    assert r.returncode == 1
    data = json.loads(r.stdout)
    assert data["state"] == "behind"
    assert data["label"] == f"behind · v{FLOOR_V} is out"


def test_check_url_network_error_state_unknown(tmp_path):
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    r = run_pn(["check", f"http://127.0.0.1:{port}"], tmp_path)
    assert r.returncode == 2
    assert "could not check" in r.stdout and "next:" in r.stdout


def test_check_url_badge_written(tmp_path, serve):
    url = serve({
        ".well-known/play-nice.json": claim(),
        "index.html": GOOD_PAGE,
        "llms.txt": "x",
    })
    out = tmp_path / "site-badge.svg"
    r = run_pn(["check", url, "--badge", str(out)], tmp_path)
    assert r.returncode == 0
    assert f"plays nice · v{FLOOR_V}" in out.read_text(encoding="utf-8")


# ---------------------------------------------------------------- start


def test_start_empty_repo_creates_block_and_badge(tmp_path):
    repo = tmp_path / "fresh"
    repo.mkdir()
    r = run_pn(["start", str(repo), "--json"], tmp_path)
    assert r.returncode == 0, r.stdout
    data = json.loads(r.stdout)
    assert data["floor_version"] == FLOOR_V
    assert data["check_state"] == "plays nice"
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert MARK_START in text and MARK_END in text
    assert f"This project follows Play-Nice (floor {FLOOR_V})." in text
    assert "**Say what's true, and how you know.**" in text  # rules verbatim
    assert "Examples" not in text and "## Why" not in text  # rules only, no examples/why
    assert f"Start each handoff with: Play-Nice floor {FLOOR_V} · receipt {FLOOR_R}" in text
    badge = repo / "playnice-badge.svg"
    assert badge.is_file() and f"plays nice · v{FLOOR_V}" in badge.read_text(encoding="utf-8")
    assert not (repo / ".github" / "workflows" / "playnice.yml").exists()


def test_start_is_idempotent_and_keeps_other_content(tmp_path):
    repo = tmp_path / "again"
    repo.mkdir()
    (repo / "AGENTS.md").write_text("# my rules\n\nbuild: make\n", encoding="utf-8")
    run_pn(["start", str(repo)], tmp_path)
    run_pn(["start", str(repo)], tmp_path)
    text = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert text.count(MARK_START) == 1
    assert "# my rules" in text and "build: make" in text
    r = run_pn(["start", str(repo)], tmp_path)
    assert "updated the play-nice block in AGENTS.md" in r.stdout


def test_start_dry_run_writes_nothing(tmp_path):
    repo = tmp_path / "planned"
    repo.mkdir()
    r = run_pn(["start", str(repo), "--dry-run"], tmp_path)
    assert r.returncode == 0
    assert "PLAN (nothing written)" in r.stdout
    assert "run playnice start again without --dry-run" in r.stdout
    assert list(repo.iterdir()) == []


def test_start_web_repo_selects_packs_and_badges_readme(tmp_path):
    repo = tmp_path / "webs"
    repo.mkdir()
    (repo / "index.html").write_text(GOOD_PAGE, encoding="utf-8")
    (repo / "README.md").write_text("# Web S\n\nA site.\n", encoding="utf-8")
    r = run_pn(["start", str(repo)], tmp_path)
    assert r.returncode == 0, r.stdout
    block = (repo / "AGENTS.md").read_text(encoding="utf-8")
    for pack in ("people", "surfaces", "sites", "access"):
        assert f"tree/main/contracts/{pack}" in block
    readme = (repo / "README.md").read_text(encoding="utf-8")
    lines = readme.splitlines()
    assert lines[0].startswith("# ")
    assert "[![Play-Nice](playnice-badge.svg)](" in lines[2]
    assert "already had" not in r.stdout  # it was added this run
    # re-running does not duplicate the badge line
    r2 = run_pn(["start", str(repo)], tmp_path)
    assert r2.returncode == 0
    readme2 = (repo / "README.md").read_text(encoding="utf-8")
    assert readme2.count("playnice-badge.svg") == 1
    assert "already had the badge" in r2.stdout


def test_start_cli_repo_selects_surfaces_only(tmp_path):
    repo = tmp_path / "clis"
    repo.mkdir()
    (repo / "tool.py").write_text("import argparse\nargparse.ArgumentParser()\n", encoding="utf-8")
    run_pn(["start", str(repo)], tmp_path)
    block = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "tree/main/contracts/surfaces" in block
    assert "tree/main/contracts/sites" not in block


def test_start_writes_workflow_when_github_exists(tmp_path):
    repo = tmp_path / "cied"
    (repo / ".github").mkdir(parents=True)
    r = run_pn(["start", str(repo)], tmp_path)
    assert r.returncode == 0
    wf = repo / ".github" / "workflows" / "playnice.yml"
    assert wf.is_file()
    text = wf.read_text(encoding="utf-8")
    assert "Path assumption" in text
    assert "python3 .play-nice-library/tools/playnice/playnice.py check --badge playnice-badge.svg" in text


def test_start_bad_path_exits_two(tmp_path):
    r = run_pn(["start", str(tmp_path / "missing")], tmp_path)
    assert r.returncode == 2
    assert "next:" in (r.stdout + r.stderr)


def test_start_then_check_agrees_plays_nice(tmp_path):
    repo = tmp_path / "loop"
    repo.mkdir()
    r = run_pn(["start", str(repo)], tmp_path)
    assert r.returncode == 0
    c = run_pn(["check", str(repo), "--json"], tmp_path)
    assert c.returncode == 0
    assert json.loads(c.stdout)["state"] == "plays nice"


# ------------------------------------------------ contractctl: resolve


def test_resolve_without_manifest_agent_defaults(tmp_path):
    r = run_ct(["resolve", "--task", "do the thing"], tmp_path)
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert "no adoption manifest: resolved from the library defaults" in out
    for cid in ("floor", "agent-behavior", "bounded-work", "handoff-and-continuity",
                "testing-and-evidence", "contract-proof"):
        assert cid in out


def test_resolve_without_manifest_human_and_service_sets(tmp_path):
    h = run_ct(["resolve", "--role", "human", "--task", ""], tmp_path)
    assert h.returncode == 0
    for cid in ("accessibility", "attention-and-quiet", "depth-on-demand",
                "plain-language", "what-why-next", "floor"):
        assert cid in h.stdout
    assert "agent-behavior" not in h.stdout  # no task, no triggers
    s = run_ct(["resolve", "--role", "service", "--task", ""], tmp_path)
    assert s.returncode == 0
    for cid in ("api", "calling-other-services", "events-and-caching",
                "status-and-state", "versions-and-discovery"):
        assert cid in s.stdout
    assert "contract-proof" not in s.stdout


def test_resolve_without_manifest_still_applies_library_triggers(tmp_path):
    r = run_ct(["resolve", "--task", "build a website page with a form"], tmp_path)
    assert r.returncode == 0, r.stderr
    assert "web-ui" in r.stdout and "friendly-site" in r.stdout


def test_resolve_explicit_missing_manifest_still_errors(tmp_path):
    r = run_ct(["resolve", "--manifest", str(tmp_path / "nope.yaml"), "--task", "x"], tmp_path)
    assert r.returncode == 1
    assert "no adoption manifest at" in r.stderr


def test_resolve_with_manifest_is_unchanged(tmp_path):
    r = run_ct(["resolve", "--manifest", str(REPO / ".contracts" / "adoption.yaml"),
                "--task", "rotate the deploy credentials"], tmp_path)
    assert r.returncode == 0, r.stderr
    assert "no adoption manifest" not in r.stdout
    assert "floor" in r.stdout and "truth-and-evidence" in r.stdout


# ------------------------------------------------------------- surfaces


def test_new_commands_documented_in_help(tmp_path):
    r = run_pn(["--help"], tmp_path)
    for word in ("verify", "check", "start"):
        assert word in r.stdout
    c = run_ct(["resolve", "--help"], tmp_path)
    assert "--role" in c.stdout and "agent" in c.stdout
