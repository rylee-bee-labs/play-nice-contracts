"""Task-to-contract matching: whole words, not substrings.

Regression tests for the usability audit of 2026-10-12: "ui" fired inside
"suite" and "build", "log" fired inside "login", and "add a settings page"
missed the web UI and accessibility contracts.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CT = REPO / "tools" / "contractctl" / "contractctl.py"

sys.path.insert(0, str(REPO / "tools" / "contractctl"))
import contractctl as ct  # noqa: E402

NO_MANIFEST = {"schema": "play-nice/adoption-v1", "always": [], "triggers": {}}


def picked(task, tags=None, manifest=None):
    return set(ct.resolve_set(manifest or NO_MANIFEST, task, tags)["selected"])


# ------------------------------------------------------------- false positives


@pytest.mark.parametrize(
    "task, absent",
    [
        ("fix the test suite", {"web-ui", "accessibility"}),  # "ui" in "suite"
        ("build a backup script", {"web-ui", "accessibility"}),  # "ui" in "build"
        ("add login with OIDC", {"secrets-and-data"}),  # "log" in "login"
        ("update the package", {"web-ui"}),  # "page" in "package"
        ("tune the guide text", {"web-ui", "accessibility"}),  # "ui" in "guide"
        ("rename the environment loader", {"secrets-and-data"}),  # "env"
    ],
)
def test_no_match_inside_other_words(task, absent):
    assert not (picked(task) & absent), picked(task) & absent


# ------------------------------------------------------------- plain requests


@pytest.mark.parametrize(
    "task, present",
    [
        ("add a settings page", {"web-ui", "accessibility", "plain-language"}),
        ("add login with OIDC", {"identity-and-roles"}),
        ("set up SSO for the admin panel", {"identity-and-roles"}),
        ("fix the test suite", {"testing-and-evidence"}),
        ("build a backup script", {"cli", "secrets-and-data"}),
        ("add two buttons to the form", {"web-ui", "accessibility"}),
        ("write some scripts", {"cli"}),  # plural folds to "script"
        ("rotate the logs", {"secrets-and-data"}),  # "logs" still means log
        ("make the UI keyboard friendly", {"web-ui", "accessibility"}),
    ],
)
def test_plain_requests_find_their_contracts(task, present):
    assert present <= picked(task), present - picked(task)


# Realistic tasks and the contracts any reviewer would agree apply. Found
# 2026-10-26: "website", "docs", "password", "webhook", "hand off" and
# "deprecate" each missed a contract here before their triggers were added.
@pytest.mark.parametrize(
    "task, present",
    [
        ("build a website", {"friendly-site", "web-ui", "accessibility", "plain-language"}),
        ("write docs for the API", {"plain-language", "api"}),
        ("write docs for a dashboard", {"plain-language"}),
        ("rotate an API key", {"secrets-and-data"}),
        ("add a settings page", {"web-ui", "accessibility"}),
        ("fix a flaky test", {"testing-and-evidence"}),
        ("add a CLI flag", {"cli"}),
        ("store user passwords", {"secrets-and-data", "identity-and-roles"}),
        ("add a webhook", {"events-and-caching", "calling-other-services"}),
        ("show status on the dashboard", {"status-and-state"}),
        ("animate the loading spinner", {"sensory-safety"}),
        ("hand off to the next agent", {"handoff-and-continuity"}),
        ("publish the repo publicly", {"public-and-private"}),
        ("add a login form", {"identity-and-roles", "web-ui", "accessibility"}),
        ("deprecate the v1 endpoint", {"api", "versions-and-discovery"}),
    ],
)
def test_realistic_tasks_select_their_contracts(task, present):
    assert present <= picked(task), present - picked(task)


def test_multi_word_triggers_need_their_words_in_order():
    assert "accessibility" in picked("check it works with a screen reader")
    assert "accessibility" not in picked("update the feed reader")  # "reader" alone
    assert "events-and-caching" in picked("move to event-driven updates")
    assert "events-and-caching" in picked("move to event driven updates")


def test_explicit_tags_still_match():
    assert "web-ui" in picked("", ["ui"])
    assert "web-ui" in picked("refactor", ["UI"])
    assert "identity-and-roles" in picked("refactor", ["access-control"])


# ------------------------------------------------------------- manifest surfaces


def test_manifest_surfaces_use_whole_words():
    m = {
        "schema": "play-nice/adoption-v1",
        "always": [],
        "triggers": {"agent": ["agent-behavior"], "ui": ["sensory-safety"]},
    }
    # "agent" is inside "management", "ui" inside "suite": neither should fire
    res = ct.resolve_set(m, "add user management to the suite")
    assert "sensory-safety" not in res["selected"]
    assert not any(
        r["source"] == "manifest-trigger" for r in res["reasons"].get("agent-behavior", [])
    )
    res = ct.resolve_set(m, "teach the agents to retry")
    assert {"source": "manifest-trigger", "trigger": "agent", "via": "task"} in res[
        "reasons"
    ]["agent-behavior"]


def test_manifest_loose_surface_compat_kept():
    """'external-api' still matches a task that only says 'API'."""
    m = ct.load_adoption(REPO / "examples" / "personal-world.adoption.yaml")
    res = ct.resolve_set(m, "call the weather API")
    assert any(
        r.get("trigger") == "external-api" for rs in res["reasons"].values() for r in rs
    )


# ------------------------------------------------------------- explainable output


def test_reasons_name_the_trigger_and_how_it_matched():
    res = ct.resolve_set(NO_MANIFEST, "add a settings page", ["git"])
    assert {"source": "floor", "trigger": None, "via": None} in res["reasons"]["floor"]
    web = res["reasons"]["web-ui"]
    assert {"source": "library-trigger", "trigger": "page", "via": "task"} in web
    git = res["reasons"]["git-and-worktrees"]
    assert {"source": "library-trigger", "trigger": "git", "via": "tag"} in git


def test_resolve_json_is_machine_readable(tmp_path):
    out = subprocess.run(
        [sys.executable, str(CT), "resolve", "--task", "add a settings page", "--json"],
        capture_output=True,
        text=True,
        cwd=tmp_path,  # no adoption manifest here
    )
    assert out.returncode == 0, out.stderr
    data = json.loads(out.stdout)
    assert data["schema"] == "play-nice/resolve-v1"
    assert data["manifest"] is None
    ids = {c["id"] for c in data["contracts"]}
    assert {"floor", "web-ui", "accessibility"} <= ids
    web = next(c for c in data["contracts"] if c["id"] == "web-ui")
    assert web["reasons"][0]["trigger"] == "page"


def test_matching_is_deterministic():
    a = ct.resolve_set(NO_MANIFEST, "add a settings page with a dark theme")
    b = ct.resolve_set(NO_MANIFEST, "add a settings page with a dark theme")
    assert a == b
