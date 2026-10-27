"""Relative links in the docs resolve, and no "Moved to" pointer files remain.

The docs consolidation of 2026-10-12 moved the long-form background into
docs/background/ and left one-line "Moved to" pointers at the old paths.
Library 2.1.0 deleted them; links now point at docs/background/ directly.
"""

import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

LINK = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)


def markdown_files():
    out = subprocess.run(["git", "-C", str(REPO), "ls-files", "*.md"],
                         capture_output=True, text=True, check=True).stdout
    return [f for f in out.split() if (REPO / f).is_file()]


def relative_links(text):
    text = re.sub(r"```.*?```", "", text, flags=re.S)  # code blocks
    text = re.sub(r"`[^`\n]*`", "", text)  # inline code
    for m in LINK.finditer(text):
        target = m.group(1).strip("<>")
        if SCHEME.match(target) or target.startswith("#"):
            continue
        path = target.split("#")[0].split("?")[0]
        if path:
            yield path


def test_relative_links_resolve():
    broken = []
    for f in markdown_files():
        src = REPO / f
        for path in relative_links(src.read_text(encoding="utf-8")):
            target = (REPO / path.lstrip("/")) if path.startswith("/") else (src.parent / path)
            target = Path(os.path.normpath(target))
            if not target.exists():
                broken.append(f"{f}: {path}")
    assert not broken, "broken relative links:\n" + "\n".join(broken)


def test_no_moved_to_pointer_files():
    """Link to the new path instead of leaving a pointer file behind."""
    pointers = [f for f in markdown_files()
                if (REPO / f).read_text(encoding="utf-8").startswith("Moved to ")]
    assert not pointers, "pointer files (link to the new path instead):\n" + "\n".join(pointers)
