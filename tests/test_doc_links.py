"""Relative links in the docs resolve, and moved docs leave a pointer behind.

Added with the docs consolidation of 2026-10-12, which moved the long-form
background into docs/background/. Every old path keeps a one-line pointer so
links from other repositories and old commits still land somewhere.
"""

import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# old path -> new path; each old path must stay a pointer to the new one
MOVED = {
    "docs/PLAY-NICE-OPUS.md": "docs/background/PLAY-NICE-OPUS.md",
    "docs/PLAY-NICE-OPUS-TLDR.md": "docs/background/README.md",
    "docs/principles/scotty-principle.md": "docs/background/principles/scotty-principle.md",
    "docs/principles/trusted-translation.md": "docs/background/principles/trusted-translation.md",
    "docs/principles/world-with-manners.md": "docs/background/principles/world-with-manners.md",
    "docs/roles/trusted-steward.md": "docs/background/roles/trusted-steward.md",
    "docs/participant-notes/MINIMAX-2026-09-13.md":
        "docs/background/participant-notes/MINIMAX-2026-09-13.md",
    "docs/research/2026-09-26-contracts-map.md":
        "docs/background/research/2026-09-26-contracts-map.md",
    "docs/research/workshop-v3-v1-shell.md": "docs/background/research/workshop-v3-v1-shell.md",
    "docs/research/v2-packs/pack-work.md": "docs/background/research/v2-packs/pack-work.md",
}

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


def test_moved_docs_leave_a_pointer():
    for old, new in MOVED.items():
        assert (REPO / new).is_file(), new
        text = (REPO / old).read_text(encoding="utf-8")
        assert text.startswith("Moved to ["), old
        links = list(relative_links(text))
        assert len(links) == 1, old
        assert ((REPO / old).parent / links[0]).resolve() \
            == (REPO / new).resolve(), old
