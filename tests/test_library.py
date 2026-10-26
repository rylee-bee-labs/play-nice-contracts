"""Play-nice contract library test suite.

Covers the required validation cases:
- duplicate IDs fail
- duplicate receipts fail
- missing receipt fails
- invalid version fails
- index drift fails
- lockfile drift detected
- hashes verified
- adoption schemas validated
- unknown contract rejected
- ALWAYS contracts always selected
- trigger selection works
- irrelevant contracts omitted
- bundle changes when contract changes
- stale pin detected
- incorrect receipt fails
- incorrect hash fails
- omitted mandatory contract fails
- conflict state representable
- offline validation works
- plus attestation end-to-end pass/fail and determinism checks.
"""

import copy
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CT = REPO / "tools" / "contractctl" / "contractctl.py"


# --------------------------------------------------------------- fixtures


@pytest.fixture()
def lib():
    sys.path.insert(0, str(REPO / "tools" / "contractctl"))
    import contractctl as ct

    yield ct
    sys.path.pop(0)


@pytest.fixture()
def tmp_repo(tmp_path, lib):
    """A copy of the library for mutation tests (keeps the real tree safe).
    Initialized as a Git repo with one baseline commit so Git-history-based
    enforcement (receipt rotation) is exercisable."""
    dest = tmp_path / "play-nice-contracts"
    shutil.copytree(
        REPO,
        dest / "play-nice-contracts",
        symlinks=True,
        ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", ".pytest_cache", ".contract-commitments"
        ),
    )
    repo = dest / "play-nice-contracts"

    def _git(*args):
        return subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=30
        )

    _git("init", "-b", "main")
    _git("config", "user.email", "test@example.invalid")
    _git("config", "user.name", "Test")
    _git("add", "-A")
    _git("commit", "-m", "baseline", "--no-gpg-sign")
    # contractctl resolves REPO_ROOT from its own path; run against the copy
    ct_path = repo / "tools" / "contractctl" / "contractctl.py"
    (repo / ".tests-ct-path").write_text(str(ct_path))
    yield repo


import os as _os


def artifact_dir(repo, manifest_rel="examples/homelab.adoption.yaml"):
    """Consumer-context artifact dir for a repo whose adoption manifest lives
    at manifest_rel: <manifest's parent>/.contracts/sessions/."""
    m = repo / manifest_rel
    if m.parent.name == ".contracts":
        return m.parent / "sessions"
    return m.parent / ".contracts" / "sessions"


def run_ct(args, cwd=None, ct_path=None, env=None):
    ct = ct_path or CT
    full_env = _os.environ.copy()
    if env:
        full_env.update(env)
    return subprocess.run(
        [sys.executable, str(ct), *args],
        capture_output=True,
        text=True,
        cwd=cwd or str(REPO),
        timeout=60,
        env=full_env,
    )


# --------------------------------------------------------------- library validity


def test_library_validates(lib):
    errors = lib.validate_library()
    assert errors == [], "\n".join(errors)


def test_receipts_unique(lib):
    receipts = []
    for c in lib.load_library():
        assert len(c["receipts"]) == 1, f"{c['rel_path']} receipt count"
        receipts.append(c["receipts"][0])
    assert len(receipts) == len(set(receipts))


def test_all_contracts_dual_use_structure(lib):
    """Each contract uses one complete shape: the v1 dual-use headings, or
    the v2 shape from docs/DESIGN_PHILOSOPHY.md (migration in progress)."""
    v1 = [
        "## Purpose",
        "## NORMATIVE RULES",
        "## RATIONALE",
        "## HUMAN EXAMPLES",
        "## ANTI-PATTERNS",
        "## ACCEPTANCE CHECKS",
    ]
    v2 = ["## In short", "## Applies when", "## Rules", "## Why", "## You're done when"]
    for c in lib.load_library():
        shape = v2 if "## In short" in c["text"] else v1
        for sec in shape:
            assert sec in c["text"], f"{c['rel_path']} missing {sec!r}"


def test_contract_count(lib):
    # Counts are derived, never hard-coded: the library must load exactly the
    # Markdown files shipped under contracts/ (v2 packs).
    lib_all = lib.load_library()
    files = sorted(
        str(f.relative_to(REPO))
        for f in (REPO / "contracts").rglob("*.md")
        if f.name != "LICENSE.md"
    )
    assert len(lib_all) == len(files)
    assert sorted(c["rel_path"] for c in lib_all) == files
    assert len(lib_all) >= 40  # v2 sanity: the merged packs are all present


def test_lock_paths_and_bytes_are_portable(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    lock = ct.build_lock()
    assert all("\\" not in c["path"] for c in lock["contracts"])
    result = run_ct(["lock"], ct_path=tmp_repo / "tools/contractctl/contractctl.py")
    assert result.returncode == 0, result.stderr
    raw = (tmp_repo / "contracts.lock.json").read_bytes()
    assert b"\r\n" not in raw
    assert json.loads(raw) == lock


@pytest.mark.parametrize("name", ["homelab", "personal-world", "vefr"])
def test_always_contract_requires_task_impact(lib, name):
    manifest = REPO / "examples" / f"{name}.adoption.yaml"
    task = "routine maintenance"
    selected = lib.resolve_set(lib.load_adoption(manifest), task)["selected"]
    assert selected["truth-and-evidence"] == "always"
    impacts = {
        cid: "Preserve the current bounded maintenance constraints."
        for cid in selected
        if cid != "truth-and-evidence"
    }
    blocked = lib.make_attestation(manifest, task, impacts)
    assert "CONTRACT GATE: BLOCKED" in blocked
    assert "missing task-impact" in blocked
    impacts["truth-and-evidence"] = (
        "ASSUMED: nothing beyond checked evidence is claimed; probe a strict reader "
        "before rollout, record contrary output and unknown on an inconclusive result."
    )
    accepted = lib.make_attestation(manifest, task, impacts)
    assert "CONTRACT GATE: PASS" in accepted


def test_always_contract_adoption_changes_bundle_and_invalidates_old_attestation(
    lib, tmp_path
):
    manifest = tmp_path / "adoption.yaml"
    source = (REPO / "examples/homelab.adoption.yaml").read_text()
    manifest.write_text(source.replace("  - truth-and-evidence\n", ""))
    task = "routine maintenance"
    before = lib.resolve_set(lib.load_adoption(manifest), task)["selected"]
    attestation = lib.make_attestation(
        manifest, task, {cid: "applied" for cid in before}
    )
    receipt = tmp_path / "attestation.txt"
    receipt.write_text(attestation)
    assert lib.verify_attestation(receipt, manifest) == []
    manifest.write_text(source)
    after = lib.resolve_set(lib.load_adoption(manifest), task)["selected"]
    assert lib.bundle_sha256(lib.load_lock(), set(before)) != lib.bundle_sha256(
        lib.load_lock(), set(after)
    )
    assert lib.verify_attestation(receipt, manifest)


def test_floor_is_discoverable_for_every_role():
    """v2: the always-applicable truth rules live on the floor (assume-unknown's
    rules were absorbed into truth-and-evidence and the floor). Every role must
    see the floor in its high-priority list — the v1 discoverability invariant."""
    for role in ["orchestrator", "worker", "ui", "cli", "service", "human"]:
        result = run_ct(["onboard", "--role", role, "--json"])
        assert result.returncode == 0, result.stderr
        data = json.loads(result.stdout)
        assert "floor" in {c["id"] for c in data["high_priority"]}


def test_assume_unknown_case_study_preserves_evidence_boundary():
    text = (REPO / "docs/background/research/workshop-v3-v1-shell.md").read_text()
    assert "reported case study" in text
    assert "UNVERIFIED" in text
    assert "counterfactual" in text
    assert "contracts/everyone/TRUTH_AND_EVIDENCE.md" in text  # assume-unknown lives here in v2
    assert not re.search(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", text)
    assert "figma.com/" not in text


# --------------------------------------------------------------- validation failures (mutation tests)

_CT_CACHE = {}


def _load_ct_from(tmp_repo):
    """Import contractctl from the copied repo, bypassing module cache."""
    import importlib.util

    key = str(tmp_repo)
    if key in _CT_CACHE:
        return _CT_CACHE[key]
    path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    spec = importlib.util.spec_from_file_location(f"ct_{abs(hash(key))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _CT_CACHE[key] = mod
    return mod


def test_duplicate_id_fails(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    src = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    dup = tmp_repo / "contracts" / "everyone" / "TRUTH_DUPLICATE.md"
    # same contract_id, different file, unique receipt → pure duplicate-id error
    text = src.read_text().replace("kestrel-flint-loom", "north-juniper-cedar")
    dup.write_text(text)
    errors = ct.validate_library()
    assert any("duplicate contract_id" in e for e in errors), errors


def test_duplicate_receipt_fails(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    src = tmp_repo / "contracts" / "everyone" / "STATUS_AND_STATE.md"
    target = tmp_repo / "contracts" / "everyone" / "WORKING_TOGETHER.md"
    text = target.read_text()
    # give WORKING_TOGETHER the same receipt as STATUS_AND_STATE
    text = text.replace("spool-hazel-drift", "tidal-quill-meadow")
    target.write_text(text)
    errors = ct.validate_library()
    assert any("duplicate receipt" in e for e in errors), errors


def test_missing_receipt_fails(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    target = tmp_repo / "contracts" / "people" / "HUMAN_RELIABILITY.md"
    text = target.read_text()
    text = text.replace("<!-- contract-receipt: pebble-thistle-wharf -->", "")
    target.write_text(text)
    errors = ct.validate_library()
    assert any("missing receipt" in e for e in errors), errors


def test_invalid_version_fails(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    target = tmp_repo / "contracts" / "everyone" / "RECOVERY_AND_HISTORY.md"
    assert "version: 2.0.0" in target.read_text(), "fixture: version moved; update the test"
    text = target.read_text().replace("version: 2.0.0", "version: banana")
    target.write_text(text)
    errors = ct.validate_library()
    assert any("invalid version" in e for e in errors), errors


def test_index_drift_fails(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    idx = tmp_repo / "CONTRACT_INDEX.md"
    text = idx.read_text()
    # remove a row → contract missing from index
    text = text.replace(
        "| `truth-and-evidence` | Truth and Evidence | 2.0.0 | canonical |",
        "| `ghost-contract` | Ghost | 2.0.0 | canonical |",
    )
    idx.write_text(text)
    errors = ct.validate_library()
    assert any("missing from CONTRACT_INDEX.md" in e for e in errors), errors
    assert any("unknown contract 'ghost-contract'" in e for e in errors), errors


def test_index_version_drift_fails(tmp_repo):
    """The index must match canonical version AND status columns, not just ids
    — the exact drift class that shipped silently in the wild (#21)."""
    ct = _load_ct_from(tmp_repo)
    idx = tmp_repo / "CONTRACT_INDEX.md"
    text = idx.read_text().replace(
        "| `truth-and-evidence` | Truth and Evidence | 2.0.0 | canonical |",
        "| `truth-and-evidence` | Truth and Evidence | 9.9.9 | canonical |",
    )
    idx.write_text(text)
    errors = ct.validate_library()
    assert any("index drift: 'truth-and-evidence'" in e for e in errors), errors


def test_index_status_drift_fails(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    idx = tmp_repo / "CONTRACT_INDEX.md"
    text = idx.read_text().replace(
        "| `truth-and-evidence` | Truth and Evidence | 2.0.0 | canonical |",
        "| `truth-and-evidence` | Truth and Evidence | 2.0.0 | draft |",
    )
    idx.write_text(text)
    errors = ct.validate_library()
    assert any("index drift: 'truth-and-evidence'" in e for e in errors), errors


def test_changelog_requires_unreleased_section(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    cl = tmp_repo / "CHANGELOG.md"
    text = cl.read_text().replace("## [Unreleased]", "## [Nope]")
    cl.write_text(text)
    errors = ct.validate_library()
    assert any("changelog: missing '## [Unreleased]'" in e for e in errors), errors


def test_changelog_guard_flags_unrecorded_meaningful_change(tmp_repo):
    """A MINOR bump vs HEAD with no new [Unreleased] bullet fails validate;
    recording it clears the error. PATCH-only changes are exempt."""
    ct = _load_ct_from(tmp_repo)
    t = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    assert "version: 2.0.0" in t.read_text(), "fixture: version moved; update the test"
    text = t.read_text().replace("version: 2.0.0", "version: 2.1.0")
    text = text.replace(
        "<!-- contract-receipt: kestrel-flint-loom -->",
        "<!-- contract-receipt: basalt-quill-ember -->",
    )
    t.write_text(text)
    idx = tmp_repo / "CONTRACT_INDEX.md"
    idx.write_text(
        idx.read_text().replace(
            "| `truth-and-evidence` | Truth and Evidence | 2.0.0 | canonical |",
            "| `truth-and-evidence` | Truth and Evidence | 2.1.0 | canonical |",
        )
    )
    errors = ct.validate_library()
    assert any("no new [Unreleased] bullet mentions it" in e for e in errors), errors
    cl = tmp_repo / "CHANGELOG.md"
    cl.write_text(
        cl.read_text().replace(
            "## [Unreleased]\n",
            "## [Unreleased]\n\n- truth-and-evidence 2.0.0 → 2.1.0 (a real new rule)\n",
        )
    )
    errors = ct.validate_library()
    assert not any("changelog:" in e for e in errors), errors


def test_diff_command_reports_changes(tmp_repo):
    """contractctl diff answers what changed between two revisions, including
    receipt rotation and always-set impact — the BEHIND-resolution question."""
    # Run the copy's own contractctl so its REPO_ROOT is the copy: the count
    # below comes from the copy's history, not the real checkout's.
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    # tmp_repo has one commit only; use HEAD..HEAD (zero-diff path)
    r = run_ct(["diff", "--from", "HEAD", "--to", "HEAD"], cwd=str(tmp_repo), ct_path=ct_path)
    assert r.returncode == 0, r.stdout + r.stderr
    # Count comes from the committed library, not a hard-coded number.
    committed = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "HEAD", "contracts/"],
        cwd=str(tmp_repo), capture_output=True, text=True, check=True,
    ).stdout.split()
    n = sum(1 for f in committed if f.endswith(".md") and not f.endswith("LICENSE.md"))
    assert f"unchanged: {n}" in r.stdout
    j = json.loads(
        run_ct(
            ["diff", "--from", "HEAD", "--to", "HEAD", "--json"], cwd=str(tmp_repo),
            ct_path=ct_path,
        ).stdout
    )
    assert j["added"] == [] and j["removed"] == [] and j["changed"] == []
    bad = run_ct(["diff", "--from", "deadbeef", "--to", "HEAD"], cwd=str(tmp_repo), ct_path=ct_path)
    assert bad.returncode == 2
    assert "UNKNOWN" in bad.stdout + bad.stderr  # fail closed, never guesses


def test_lockfile_drift_detected(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    lock = tmp_repo / "contracts.lock.json"
    data = json.loads(lock.read_text())
    data["contracts"][0]["sha256"] = "f" * 64
    lock.write_text(json.dumps(data))
    errors = ct.verify_lock()
    assert any("hash changed" in e for e in errors), errors


def test_lockfile_missing_contract_detected(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    lock = tmp_repo / "contracts.lock.json"
    data = json.loads(lock.read_text())
    removed = data["contracts"].pop()
    lock.write_text(json.dumps(data))
    errors = ct.verify_lock()
    assert any("missing from contracts.lock.json" in e for e in errors), errors


def test_hash_verification(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    import hashlib

    src = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    sha = hashlib.sha256(src.read_text().encode()).hexdigest()
    lock = json.loads((tmp_repo / "contracts.lock.json").read_text())
    entry = [e for e in lock["contracts"] if e["id"] == "truth-and-evidence"][0]
    assert entry["sha256"] == sha


# --------------------------------------------------------------- adoption


def test_adoption_examples_valid(lib):
    for name in ("personal-world", "vefr", "homelab"):
        path = REPO / "examples" / f"{name}.adoption.yaml"
        errors = lib.validate_adoption_manifest(path)
        assert errors == [], f"{name}: {errors}"


def test_adoption_unknown_contract_rejected(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    m = tmp_repo / "examples" / "vefr.adoption.yaml"
    text = m.read_text().replace("- testing-and-evidence", "- not-a-real-contract")
    m.write_text(text)
    errors = ct.validate_adoption_manifest(m)
    assert any("unknown contract" in e for e in errors), errors


def test_adoption_bad_schema_rejected(tmp_path):
    ct_path = REPO / "tools" / "contractctl" / "contractctl.py"
    bad = tmp_path / "adoption.yaml"
    bad.write_text("schema: wrong/schema\nsource: {repository: x}\n")
    r = run_ct(["adopt", "--manifest", str(bad)], ct_path=ct_path)
    assert r.returncode != 0
    assert "play-nice/adoption-v1" in (r.stdout + r.stderr)


# --------------------------------------------------------------- resolution


def test_always_contracts_selected(lib):
    m = lib.load_adoption(REPO / "examples" / "personal-world.adoption.yaml")
    res = lib.resolve_set(m, task="totally unrelated backend refactor")
    for cid in m["always"]:
        assert cid in res["selected"], cid


def test_trigger_selection_works(lib):
    m = lib.load_adoption(REPO / "examples" / "personal-world.adoption.yaml")
    res = lib.resolve_set(
        m, task="add GitHub provider and update Project UI", task_tags=["external-api"]
    )
    for cid in ("calling-other-services", "capabilities-not-vendors"):
        assert cid in res["selected"], cid


def test_irrelevant_contracts_omitted(lib):
    m = lib.load_adoption(REPO / "examples" / "homelab.adoption.yaml")
    res = lib.resolve_set(
        m, task="rename a variable in the deploy script", task_tags=["git"]
    )
    assert "sensory-safety" not in res["selected"]
    assert "depth-on-demand" not in res["selected"]
    # ALWAYS still applies
    for cid in m["always"]:
        assert cid in res["selected"]


def test_resolve_unknown_contract_errors(lib):
    fake = {"schema": "play-nice/adoption-v1", "always": ["ghost"], "triggers": {}}
    res = lib.resolve_set(fake, task="")
    assert any("unknown contract" in e for e in res["errors"])


# --------------------------------------------------------------- bundle + lock determinism


def test_lock_generation_deterministic(lib):
    a = lib.build_lock()
    b = lib.build_lock()
    assert a == b
    assert lib.bundle_receipt(a) == lib.bundle_receipt(b)


def test_bundle_changes_when_contract_changes(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    before = ct.bundle_receipt(ct.load_lock())
    target = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    text = target.read_text()
    target.write_text(text.replace("Keep honesty cheap.", "Keep honesty cheap, always."))
    # regenerate lock from mutated library
    lock2 = ct.build_lock()
    after = ct.bundle_receipt(lock2)
    assert before != after


# --------------------------------------------------------------- attestation


def _attest(tmp_repo, manifest, task, impact, ct_path):
    args = ["attest", "--manifest", str(manifest), "--task", task]
    for k, v in impact.items():
        args.append("--impact")
        args.append(f"{k}={v}")
    return run_ct(args, cwd=str(tmp_repo), ct_path=ct_path)


def test_good_attestation_passes_and_verifies(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "rotate the deploy credentials and update the health checks"
    # impact must cover every contract the resolver selects for this task
    impact = {
        "truth-and-evidence": "rotation verified by live check, not by report",
        "status-and-state": "statuses use the shared vocabulary with observed_at",
        "recovery-and-history": "rollback documented and journaled before rotation",
        "ask-for-help": "unknown provider semantics get asked, not guessed",
        "secrets-and-data": "rotated credentials handled by reference, never in logs",
        "public-and-private": "rotation notes keep private topology out of public places",
        "testing-and-evidence": "health checks re-run after rotation with command and grade",
        "observability": "dashboards show post-rotation state honestly, not cached green",
    }
    r = _attest(tmp_repo, manifest, task, impact, ct_path)
    assert "CONTRACT GATE: PASS" in r.stdout, r.stdout + r.stderr
    att_path = tmp_repo / "att.txt"
    att_path.write_text(r.stdout)
    v = run_ct(
        ["verify-attestation", str(att_path), "--manifest", str(manifest)],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert v.returncode == 0, v.stdout + v.stderr
    assert "ATTESTATION VERIFIED" in v.stdout


def test_missing_task_impact_blocks(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    r = run_ct(
        ["attest", "--manifest", str(manifest), "--task", "redeploy the stack"],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert "CONTRACT GATE: BLOCKED" in r.stdout
    assert "missing task-impact" in r.stdout


def test_incorrect_receipt_fails_verification(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    r = _attest(tmp_repo, manifest, task, impact, ct_path)
    att = tmp_repo / "att.txt"
    att.write_text(r.stdout.replace("kestrel-flint-loom", "wrong-wrong-wrong"))
    v = run_ct(["verify-attestation", str(att)], cwd=str(tmp_repo), ct_path=ct_path)
    assert v.returncode != 0
    assert "wrong receipt" in v.stdout


def test_incorrect_hash_fails_verification(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    r = _attest(tmp_repo, manifest, task, impact, ct_path)
    assert "PASS" in r.stdout
    att = tmp_repo / "att.txt"
    att.write_text(r.stdout)
    # corrupt one hash in the lockfile underneath: verification must fail
    # closed on lock drift (hardening #5) — never verify against a stale lock
    lock = tmp_repo / "contracts.lock.json"
    data = json.loads(lock.read_text())
    for e in data["contracts"]:
        if e["id"] == "status-and-state":
            e["sha256"] = "0" * 64
    lock.write_text(json.dumps(data))
    v = run_ct(["verify-attestation", str(att)], cwd=str(tmp_repo), ct_path=ct_path)
    assert v.returncode != 0
    assert "lock drift" in v.stdout


def test_omitted_mandatory_contract_fails_verification(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    r = _attest(tmp_repo, manifest, task, impact, ct_path)
    att = tmp_repo / "att.txt"
    # drop one mandatory (always) contract from the attestation text
    text = r.stdout
    lines = text.split("\n")
    out = []
    skip = 0
    for i, ln in enumerate(lines):
        if ln.strip() == "status-and-state@2.1.0":
            skip = 3  # skip the id + receipt + status lines
            continue
        if skip > 0:
            skip -= 1
            continue
        out.append(ln)
    att.write_text("\n".join(out))
    v = run_ct(
        ["verify-attestation", str(att), "--manifest", str(manifest)],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert v.returncode != 0
    assert "mandatory contract 'status-and-state'" in v.stdout


def test_stale_attestation_fails_after_library_change(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    r = _attest(tmp_repo, manifest, task, impact, ct_path)
    att = tmp_repo / "att.txt"
    att.write_text(r.stdout)
    # now change a contract and relock: the old attestation must fail
    target = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    target.write_text(
        target.read_text().replace(
            "Keep honesty cheap.", "Keep honesty cheap and durable."
        )
    )
    run_ct(["lock"], cwd=str(tmp_repo), ct_path=ct_path)
    v = run_ct(["verify-attestation", str(att)], cwd=str(tmp_repo), ct_path=ct_path)
    assert v.returncode != 0
    assert "bundle receipt mismatch" in v.stdout or "hash" in v.stdout


def test_conflict_state_representable(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    m = ct.load_adoption(manifest)
    lock = ct.load_lock()
    # fabricate an attestation with a CONFLICT and verify it parses + gates BLOCKED
    text = f"""CONTRACT_ATTESTATION v1

bundle:
  library_version: 0.1.0
  library_revision: test
  receipt: {ct.bundle_receipt(lock, {"truth-and-evidence"})}
  sha256: {ct.bundle_sha256(lock, {"truth-and-evidence"})}
  scope: resolved-set

loaded:
  truth-and-evidence@2.0.0
    receipt: kestrel-flint-loom
    status: CONFLICT

task-impact:
  - truth-and-evidence: evidence grades preserved in reports

conflicts: truth-and-evidence conflicts with status-and-state on unknown-vs-healthy rendering

CONTRACT GATE: BLOCKED
"""
    p = tmp_repo / "conflict.txt"
    p.write_text(text)
    errors = ct.verify_attestation(p)
    # CONFLICT with explanation is valid representation; nothing about shape should fail
    assert not any("status" in e for e in errors), errors


# --------------------------------------------------------------- operational commitment

_IMPACT_OK = {
    "truth-and-evidence": "rotation verified by live check, not by report",
    "status-and-state": "statuses use the shared vocabulary with observed_at",
    "recovery-and-history": "rollback documented and journaled before rotation",
    "ask-for-help": "unknown provider semantics asked, not guessed; waiting-for-help over retry",
    "secrets-and-data": "rotated credentials handled by reference, never in logs",
    "public-and-private": "rotation notes keep private topology out of public places",
    "testing-and-evidence": "health checks re-run after rotation with command and grade",
    "observability": "dashboards show post-rotation state honestly, not cached green",
}


def _commit_args(manifest, task, impact, extra=()):
    args = ["commit", "--manifest", str(manifest), "--task", task]
    for k, v in impact.items():
        args += ["--impact", f"{k}={v}"]
    return list(args) + list(extra)


def test_commitment_activates_and_status_reports(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "rotate the deploy credentials and update the health checks"
    r = run_ct(
        _commit_args(manifest, task, _IMPACT_OK), cwd=str(tmp_repo), ct_path=ct_path
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CONTRACT COMMITMENT: ACTIVE" in r.stdout
    assert "bundle_sha256:" in r.stdout
    s = run_ct(
        ["session-status", "--manifest", str(manifest)],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert s.returncode == 0, s.stdout
    assert "CONTRACT COMMITMENT: ACTIVE" in s.stdout


def test_commitment_blocked_without_impact(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    r = run_ct(
        ["commit", "--manifest", str(manifest), "--task", "rotate things"],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert r.returncode == 2
    assert "CONTRACT COMMITMENT: INACTIVE" in r.stderr
    assert "BLOCKED" in r.stderr


def test_commitment_records_exact_bundle(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "rotate the deploy credentials and update the health checks"
    r = run_ct(
        _commit_args(manifest, task, _IMPACT_OK), cwd=str(tmp_repo), ct_path=ct_path
    )
    assert r.returncode == 0
    # keyed artifact path, not a global singleton
    slug_dir = artifact_dir(tmp_repo)
    assert slug_dir.is_dir()
    arts = list(slug_dir.glob("session-*.json"))
    assert len(arts) == 1
    art = json.loads(arts[0].read_text())
    lock = ct.load_lock()
    selected = set(art["contracts"])
    # bundle identity is the RESOLVED set, not the whole library
    assert art["bundle_receipt"] == ct.bundle_receipt(lock, selected)
    assert art["bundle_sha256"] == ct.bundle_sha256(lock, selected)
    assert art["bundle_receipt"] != ct.bundle_receipt(lock)
    assert art["contract_gate"] == "PASS"
    assert art["commitment"] == "ACTIVE"
    assert selected == {
        "floor",
        "truth-and-evidence",
        "status-and-state",
        "recovery-and-history",
        "ask-for-help",
        "secrets-and-data",
        "public-and-private",
        "testing-and-evidence",
        "observability",
    }
    assert art["library_version"] == (REPO / "VERSION").read_text().strip()  # semver from VERSION
    # no secrets by construction: artifact only carries ids/hashes/words
    # (a contract id legitimately contains the word "secrets"; scan for
    # secret-SHAPED values, matching the repo-wide privacy test)
    blob = json.dumps(art).lower()
    for bad in ("password", "api_key", "gh" + "p_", "AK" + "IA"):
        assert bad not in blob


def test_resolved_set_bundle_differs_by_scope(tmp_repo):
    """Two different task scopes resolve different bundle identities (hardening #1)."""
    ct = _load_ct_from(tmp_repo)
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    lock = ct.load_lock()
    broad = set(
        ct.resolve_set(
            ct.load_adoption(manifest),
            "rotate the deploy credentials and update the health checks",
        )["selected"]
    )
    narrow = set(
        ct.resolve_set(ct.load_adoption(manifest), "update a compose file")["selected"]
    )
    assert ct.bundle_receipt(lock, broad) != ct.bundle_receipt(lock, narrow)
    assert ct.bundle_sha256(lock, broad) != ct.bundle_sha256(lock, narrow)
    # same scope → identical identity (deterministic)
    assert ct.bundle_receipt(lock, broad) == ct.bundle_receipt(lock, set(broad))


def test_library_version_vs_revision(tmp_repo):
    """Library semver and adopted git revision are distinct concepts (hardening #2)."""
    ct = _load_ct_from(tmp_repo)
    assert ct.library_version() == (REPO / "VERSION").read_text().strip()
    rev = ct.library_revision()
    assert rev != "unknown"
    assert rev != ct.library_version()  # git SHA when repo initialized


def test_stale_bundle_invalidates_commitment(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "rotate the deploy credentials and update the health checks"
    assert (
        run_ct(
            _commit_args(manifest, task, _IMPACT_OK), cwd=str(tmp_repo), ct_path=ct_path
        ).returncode
        == 0
    )
    # change the library (a PATCH, versioned as validate requires) → relock →
    # commitment must go STALE
    target = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    text = target.read_text()
    assert "version: 2.0.0" in text and "Keep honesty cheap." in text
    target.write_text(
        text.replace("Keep honesty cheap.", "Keep honesty cheap and durable.").replace(
            "version: 2.0.0", "version: 2.0.1"
        )
    )
    run_ct(["index", "--write"], cwd=str(tmp_repo), ct_path=ct_path)
    assert run_ct(["lock"], cwd=str(tmp_repo), ct_path=ct_path).returncode == 0
    s = run_ct(
        ["session-status", "--manifest", str(manifest), "--task", task],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert s.returncode != 0
    assert "STALE" in s.stdout
    assert "re-attest and re-commit" in s.stdout


def test_task_change_requires_reresolution(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    assert (
        run_ct(
            _commit_args(manifest, task, impact), cwd=str(tmp_repo), ct_path=ct_path
        ).returncode
        == 0
    )
    s = run_ct(
        ["session-status", "--manifest", str(manifest)],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    # same task → still ACTIVE
    assert s.returncode == 0
    # rewrite the recorded task to one that triggers more; simulate scope expansion
    art_path = next((artifact_dir(tmp_repo)).glob("session-*.json"))
    art = json.loads(art_path.read_text())
    art["task_fingerprint"] = (
        "rotate the deploy credentials and update the health checks"
    )
    art_path.write_text(json.dumps(art))
    s2 = run_ct(
        ["session-status", "--manifest", str(manifest)],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert s2.returncode != 0
    assert "additional contracts not in the commitment" in s2.stdout
    assert "secrets-and-data" in s2.stdout


def test_worker_commitment_requires_parent_bundle(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    r = run_ct(
        _commit_args(manifest, task, impact, extra=["--worker"]),
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert r.returncode != 0
    assert "parent-bundle" in r.stderr or "inherited bundle" in r.stderr


def test_worker_rejects_invented_parent_hash(tmp_repo):
    """Real inheritance (hardening #3): a worker may not claim an arbitrary parent
    hash — the parent bundle must exist as a recorded commitment."""
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    fake = "f" * 64
    r = run_ct(
        _commit_args(
            manifest, task, impact, extra=["--worker", "--parent-bundle", fake]
        ),
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert r.returncode != 0
    assert "parent bundle not found" in r.stderr


def test_worker_commitment_inherits_real_parent(tmp_repo):
    """End-to-end propagation: orchestrator commits first; worker inherits its
    recorded bundle; inheritance lines appear; parent constraints preserved."""
    ct = _load_ct_from(tmp_repo)
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    # 1. orchestrator commits on a broad task
    orch_task = "rotate the deploy credentials and update the health checks"
    r0 = run_ct(
        _commit_args(manifest, orch_task, _IMPACT_OK, extra=["--role", "orchestrator"]),
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert r0.returncode == 0, r0.stdout + r0.stderr
    orch_art = json.loads(
        next((artifact_dir(tmp_repo)).glob("orchestrator-*.json")).read_text()
    )
    parent_sha = orch_art["bundle_sha256"]

    # 2. worker with a narrower task inherits the orchestrator's bundle;
    #    inherited contracts join the resolved set (union — dropping is impossible)
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    # the parent's broad task pulled in four contracts the worker's narrow
    # task does not resolve — each inherited one needs its own acknowledgement
    for cid in (
        "secrets-and-data",
        "public-and-private",
        "testing-and-evidence",
        "observability",
    ):
        impact[cid] = f"inherited from parent: {cid} stays governed"
    r = run_ct(
        _commit_args(
            manifest, task, impact, extra=["--worker", "--parent-bundle", parent_sha]
        ),
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "INHERITED CONTRACT BUNDLE:" in r.stdout
    assert "PARENT CONTRACT COMMITMENT: ACTIVE" in r.stdout
    art_path = next((artifact_dir(tmp_repo)).glob("worker-*.json"))
    art = json.loads(art_path.read_text())
    assert art["role"] == "worker"
    assert art["inherited_bundle"] == parent_sha
    # the parent's whole applicable set is preserved via the union
    for cid in (
        "truth-and-evidence",
        "status-and-state",
        "recovery-and-history",
        "ask-for-help",
        "secrets-and-data",
        "public-and-private",
        "testing-and-evidence",
        "observability",
    ):
        assert cid in art["contracts"]
    # worker artifact verifies: parent recorded + no dropped constraints
    errs = ct.verify_commitment_artifact(art, manifest)
    assert errs == [], errs


def test_worker_attestation_covers_exact_union(tmp_repo):
    """Hardening: the contract set ATTESTED must be exactly the set COMMITTED.
    A worker inherits parent-only contracts (secrets-and-data and the other
    extras the broad task resolved); those inherited ones must appear in the
    worker's attestation, and the attested set must equal the committed set."""
    ct = _load_ct_from(tmp_repo)
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    # orchestrator on a broad task resolves secrets-and-data (credentials trigger)
    orch_task = "rotate the deploy credentials and update the health checks"
    r0 = run_ct(
        _commit_args(manifest, orch_task, _IMPACT_OK, extra=["--role", "orchestrator"]),
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert r0.returncode == 0, r0.stdout + r0.stderr
    parent_sha = json.loads(
        next((artifact_dir(tmp_repo)).glob("orchestrator-*.json")).read_text()
    )["bundle_sha256"]

    # worker's own task does NOT trigger secrets-and-data...
    worker_task = "update a compose file"
    own = set(ct.resolve_set(ct.load_adoption(manifest), worker_task)["selected"])
    assert "secrets-and-data" not in own
    # ...so when it inherits, secrets-and-data is a parent-only addition
    impact = {cid: "applied" for cid in own}
    impact["secrets-and-data"] = "inherited: credentials handled by reference"
    impact["public-and-private"] = "inherited: private notes stay private"
    impact["testing-and-evidence"] = "inherited: checks re-run with command and grade"
    impact["observability"] = "inherited: dashboards stay honest about state"
    # capture the attestation the worker's commitment used
    atts = {}
    orig_make_attestation = ct.make_attestation

    def spy(
        mpath,
        task,
        task_impact,
        revision="uncommitted",
        format_text=True,
        task_tags=None,
        resolved_ids=None,
    ):
        out = orig_make_attestation(
            mpath, task, task_impact, revision, format_text, task_tags, resolved_ids
        )
        if not format_text:
            atts["resolved_ids"] = resolved_ids
            atts["loaded"] = {e["contract_id"] for e in out["loaded"]}
        return out

    ct.make_attestation = spy
    try:
        w_art, _ = ct.build_commitment(
            manifest,
            worker_task,
            impact,
            role="worker",
            parent_bundle=parent_sha,
            worker=True,
        )
    finally:
        ct.make_attestation = orig_make_attestation
    # inherited parent-only contract IS in the attested set and committed set
    assert "secrets-and-data" in atts["loaded"]
    assert atts["loaded"] == set(w_art["contracts"]), "attested set != committed set"
    assert (
        atts["resolved_ids"] is not None and set(atts["resolved_ids"]) == atts["loaded"]
    )


def test_worker_missing_impact_for_inherited_contract_blocks(tmp_repo):
    """Missing task-impact for an inherited (parent-only) contract blocks
    attestation/commitment — inherited contracts are attested, not assumed."""
    ct = _load_ct_from(tmp_repo)
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    orch_task = "rotate the deploy credentials and update the health checks"
    orch_art, _ = ct.build_commitment(
        manifest, orch_task, dict(_IMPACT_OK), role="orchestrator"
    )
    ct.write_session_artifact(orch_art)
    worker_task = "update a compose file"
    own = set(ct.resolve_set(ct.load_adoption(manifest), worker_task)["selected"])
    assert "secrets-and-data" not in own
    w_impact = {cid: "applied" for cid in own}  # NO impacts for the inherited extras
    import pytest as _pq

    with _pq.raises(ct.CTError) as exc:
        ct.build_commitment(
            manifest,
            worker_task,
            w_impact,
            role="worker",
            parent_bundle=orch_art["bundle_sha256"],
            worker=True,
        )
    # every parent-only inherited contract is named in the block
    assert "secrets-and-data" in str(exc.value)


def test_worker_cannot_drop_parent_constraints(tmp_repo):
    """A worker claiming inheritance without acknowledging the inherited contracts
    is rejected — the union is forced, so weakening requires explicit refusal
    (which fails closed), not silent omission."""
    ct = _load_ct_from(tmp_repo)
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    # orchestrator commits on the credentials task (resolves secrets-and-data too)
    orch_task = "rotate the deploy credentials and update the health checks"
    orch_art, _ = ct.build_commitment(
        manifest, orch_task, dict(_IMPACT_OK), role="orchestrator"
    )
    ct.write_session_artifact(orch_art)
    # a worker claims inheritance but does not acknowledge the inherited extras
    worker_task = "update a compose file"  # does not itself trigger secrets-and-data
    w_impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    import pytest as _pq

    with _pq.raises(ct.CTError) as exc:
        ct.build_commitment(
            manifest,
            worker_task,
            w_impact,
            role="worker",
            parent_bundle=orch_art["bundle_sha256"],
            worker=True,
        )
    assert "inherited contracts need task-impact" in str(
        exc.value
    ) or "secrets-and-data" in str(exc.value)


def test_session_safe_keyed_artifacts(tmp_repo):
    """Parallel lanes get distinct artifacts (hardening #4) — no global singleton."""
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    t1 = "update a compose file"
    t2 = "rotate the deploy credentials and update the health checks"
    i1 = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    assert (
        run_ct(
            _commit_args(manifest, t1, i1), cwd=str(tmp_repo), ct_path=ct_path
        ).returncode
        == 0
    )
    assert (
        run_ct(
            _commit_args(manifest, t2, _IMPACT_OK), cwd=str(tmp_repo), ct_path=ct_path
        ).returncode
        == 0
    )
    arts = list((artifact_dir(tmp_repo)).glob("session-*.json"))
    assert len(arts) == 2  # keyed by task; both coexist
    # status default picks the newest, but keyed lookup finds each
    s1 = run_ct(
        ["session-status", "--manifest", str(manifest), "--task", t1],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    s2 = run_ct(
        ["session-status", "--manifest", str(manifest), "--task", t2],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert s1.returncode == 0 and s2.returncode == 0
    assert t1 in s1.stdout and t2 in s2.stdout


def test_session_isolation_across_projects(tmp_repo, tmp_path):
    """Hardening: two consuming PROJECTS with identical task strings and roles
    produce distinct commitment state — artifacts live in the consuming
    project's context, never a global library path."""
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    task = "identical integration task"
    role = "session"
    # "integration" also library-triggers bounded-work + calling-other-services
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
            "bounded-work",
            "calling-other-services",
        )
    }
    # two consumer projects, each with its own .contracts/ adoption manifest
    proj_a = tmp_path / "project-a"
    proj_b = tmp_path / "project-b"
    for proj in (proj_a, proj_b):
        (proj / ".contracts").mkdir(parents=True)
        shutil.copy(
            tmp_repo / "examples" / "homelab.adoption.yaml",
            proj / ".contracts" / "adoption.yaml",
        )
    for proj in (proj_a, proj_b):
        r = run_ct(
            _commit_args(proj / ".contracts" / "adoption.yaml", task, impact),
            cwd=str(proj),
            ct_path=ct_path,
        )
        assert r.returncode == 0, r.stdout + r.stderr
    # distinct artifact files in each project's own context
    art_a = json.loads(
        next((proj_a / ".contracts" / "sessions").glob(f"{role}-*.json")).read_text()
    )
    art_b = json.loads(
        next((proj_b / ".contracts" / "sessions").glob(f"{role}-*.json")).read_text()
    )
    assert art_a["session_dir"] != art_b["session_dir"]
    assert (
        str(proj_a) in art_a["session_dir"] and str(proj_b) not in art_a["session_dir"]
    )
    assert (
        str(proj_b) in art_b["session_dir"] and str(proj_a) not in art_b["session_dir"]
    )
    # the library checkout itself stays untouched — no workflow-state singleton
    assert not (tmp_repo / ".contract-commitments").exists() or not list(
        (tmp_repo / ".contract-commitments").glob(f"{role}-*.json")
    )
    # worktree isolation: CONTRACTCTL_SESSION_DIR pins a private dir per lane
    lane_dir = tmp_path / "lane-wt" / "sessions"
    r = run_ct(
        _commit_args(proj_a / ".contracts" / "adoption.yaml", task, impact),
        cwd=str(proj_a),
        ct_path=ct_path,
        env={"CONTRACTCTL_SESSION_DIR": str(lane_dir)},
    )
    assert r.returncode == 0
    assert (
        lane_dir
        / f"{role}-{re.sub(r'[^a-z0-9-]+', '-', task.lower()).strip('-')[:48]}.json"
    ).is_file()


def test_attestation_fails_closed_on_lock_drift(tmp_repo):
    """Hardening #5: attestation cannot be produced against a drifted lockfile."""
    ct = _load_ct_from(tmp_repo)
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    # corrupt the lockfile (simulate drift)
    lock = tmp_repo / "contracts.lock.json"
    data = json.loads(lock.read_text())
    data["contracts"][0]["sha256"] = "0" * 64
    lock.write_text(json.dumps(data))
    import pytest as _pq

    with _pq.raises(ct.CTError) as exc:
        ct.make_attestation(
            manifest,
            "update a compose file",
            {
                c: "x"
                for c in (
                    "truth-and-evidence",
                    "status-and-state",
                    "recovery-and-history",
                )
            },
        )
    assert "lockfile drift" in str(exc.value)


def test_commit_impact_file(tmp_repo):
    """Hardening #6: commit --impact-file parses 'id = sentence' lines."""
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    impact_file = tmp_repo / "impact.txt"
    impact_file.write_text(
        "truth-and-evidence = unknown stays unknown\n"
        "status-and-state = vocabulary with observed_at\n"
        "recovery-and-history = rollback documented and journaled\n"
        "ask-for-help = provider semantics asked, not guessed\n"
        "# comment line ignored\n"
    )
    r = run_ct(
        [
            "commit",
            "--manifest",
            str(manifest),
            "--task",
            "update a compose file",
            "--impact-file",
            str(impact_file),
        ],
        cwd=str(tmp_repo),
        ct_path=ct_path,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "CONTRACT COMMITMENT: ACTIVE" in r.stdout


def test_commitment_hash_mismatch_prevents_active(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    manifest = tmp_repo / "examples" / "homelab.adoption.yaml"
    task = "update a compose file"
    impact = {
        cid: "applied"
        for cid in (
            "truth-and-evidence",
            "status-and-state",
            "recovery-and-history",
            "ask-for-help",
        )
    }
    # corrupt the lockfile: a selected contract's hash no longer matches the file
    lock = tmp_repo / "contracts.lock.json"
    data = json.loads(lock.read_text())
    for e in data["contracts"]:
        if e["id"] == "truth-and-evidence":
            e["sha256"] = "0" * 64
    lock.write_text(json.dumps(data))
    r = run_ct(_commit_args(manifest, task, impact), cwd=str(tmp_repo), ct_path=ct_path)
    assert r.returncode != 0
    assert "hash mismatch" in r.stderr or "BLOCKED" in r.stderr


def test_session_status_inactive_when_no_artifact(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    s = run_ct(["session-status"], cwd=str(tmp_repo), ct_path=ct_path)
    assert s.returncode == 1
    assert "INACTIVE" in s.stdout


# --------------------------------------------------------------- project context / participant packs

EXAMPLE_PROJECT = REPO / "examples" / "project-context" / ".project"


def test_example_project_valid():
    r = run_ct(["project", "validate", str(EXAMPLE_PROJECT)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PROJECT VALID" in r.stdout


def test_example_participant_figma_valid():
    r = run_ct(
        ["participant", "validate", str(EXAMPLE_PROJECT / "participants" / "figma")]
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "PARTICIPANT VALID" in r.stdout
    assert "NOT authoritative for: product-policy" in r.stdout


def test_invalid_project_manifest_rejected(tmp_path):
    d = tmp_path / ".project"
    d.mkdir()
    (d / "project.yaml").write_text("schema: wrong\nid: x\n")
    r = run_ct(["project", "validate", str(d)])
    assert r.returncode != 0
    assert "play-nice/project-v1" in r.stdout
    # missing manifest entirely
    d2 = tmp_path / ".project2"
    d2.mkdir()
    r2 = run_ct(["project", "validate", str(d2)])
    assert r2.returncode != 0
    assert "missing project.yaml" in r2.stdout


def test_participant_missing_authoritative_boundary_rejected(tmp_path):
    pack = tmp_path / "bad-participant"
    pack.mkdir()
    (pack / "participant.yaml").write_text(
        "schema: play-nice/participant-v1\nid: bad\nname: Bad\ntype: agent\n"
        "relationship:\n  role: x\n  optional: true\n"
        "provenance:\n  supplied_by: test\n  observed_at: 2026-09-12T00:00:00Z\n"
    )
    r = run_ct(["participant", "validate", str(pack)])
    assert r.returncode != 0
    # authoritative_for AND not_authoritative_for both required; not-authoritative non-empty
    assert any("authoritative_for" in line for line in r.stdout.split("\n"))


def test_participant_secret_rejected(tmp_path):
    pack = tmp_path / "leaky"
    pack.mkdir()
    (pack / "participant.yaml").write_text(
        "schema: play-nice/participant-v1\nid: leaky\nname: Leaky\ntype: external-api\n"
        "relationship:\n  role: api\n  optional: true\n"
        "  authoritative_for: [enrichment]\n"
        "  not_authoritative_for: [product-truth]\n"
        "provenance:\n  supplied_by: test\n  observed_at: 2026-09-12T00:00:00Z\n"
    )
    (pack / "notes.txt").write_text('api_key = "sk-live-EXAMPLEKEY123456789012345"\n')
    r = run_ct(["participant", "validate", str(pack)])
    assert r.returncode != 0
    assert "possible inline secret" in r.stdout


def test_participant_capabilities_validation(tmp_path):
    pack = tmp_path / "p"
    pack.mkdir()
    (pack / "participant.yaml").write_text(
        "schema: play-nice/participant-v1\nid: p\nname: P\ntype: agent\n"
        "relationship:\n  role: helper\n  optional: true\n"
        "  authoritative_for: [analysis]\n"
        "  not_authoritative_for: [product-truth]\n"
        "provenance:\n  supplied_by: test\n  observed_at: 2026-09-12T00:00:00Z\n"
    )
    # capabilities: empty list + no limitations -> invalid
    (pack / "capabilities.yaml").write_text(
        "schema: play-nice/participant-capabilities-v1\nparticipant: p\n"
        "capabilities: []\nlimitations: []\n"
    )
    r = run_ct(["participant", "validate", str(pack)])
    assert r.returncode != 0
    assert "real discovered capabilities" in r.stdout
    assert "honest limitation" in r.stdout
    # participant mismatch -> invalid
    (pack / "capabilities.yaml").write_text(
        "schema: play-nice/participant-capabilities-v1\nparticipant: someone-else\n"
        "capabilities:\n  - id: x\n    description: does something useful\n"
        "limitations:\n  - cannot be trusted beyond its scope\n"
    )
    r2 = run_ct(["participant", "validate", str(pack)])
    assert r2.returncode != 0
    assert "must match id" in r2.stdout


def test_participant_canonicality_vocabulary(tmp_path):
    pack = tmp_path / "p"
    pack.mkdir()
    (pack / "participant.yaml").write_text(
        "schema: play-nice/participant-v1\nid: p\nname: P\ntype: forge\n"
        "relationship:\n  role: mirror\n  optional: true\n"
        "  authoritative_for: [mirror]\n"
        "  not_authoritative_for: [product-truth]\n"
        "provenance:\n  supplied_by: test\n  observed_at: 2026-09-12T00:00:00Z\n"
    )
    (pack / "references.yaml").write_text(
        "schema: play-nice/references-v1\nparticipant: p\n"
        "references:\n  - id: r1\n    type: file\n    status: super-authoritative\n"
    )
    r = run_ct(["participant", "validate", str(pack)])
    assert r.returncode != 0
    assert "canonicality vocabulary" in r.stdout


def test_participant_id_uniqueness(tmp_path):
    proj = tmp_path / ".project"
    (proj / "participants").mkdir(parents=True)
    base_manifest = (
        "schema: play-nice/participant-v1\nid: {id}\nname: {id}\ntype: agent\n"
        "relationship:\n  role: x\n  optional: true\n"
        "  authoritative_for: [a]\n"
        "  not_authoritative_for: [b]\n"
        "provenance:\n  supplied_by: test\n  observed_at: 2026-09-12T00:00:00Z\n"
    )
    for dirname in ("dup", "dup-copy"):
        p = proj / "participants" / dirname
        p.mkdir()
        (p / "participant.yaml").write_text(base_manifest.format(id="dup"))
    # fix directory names to match the id (validator requires dir==id);
    # two directories with the same id -> duplicate detection via project scan
    r = run_ct(["participant", "validate", str(proj / "participants" / "dup")])
    # single pack is fine
    assert r.returncode == 0
    # project-level: same id in two packs
    errs = None
    import contractctl as _ct  # noqa: F401  (not the copy; use file load)

    sys.path.insert(0, str(REPO / "tools" / "contractctl"))
    import importlib

    spec = importlib.util.spec_from_file_location(
        "ct_local", REPO / "tools" / "contractctl" / "contractctl.py"
    )
    ctm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ctm)
    errs = ctm.validate_participants(proj / "participants")
    assert any("duplicate participant id" in e for e in errs), errs


def test_machine_files_parse_without_markdown():
    """All pack machine files are YAML-parseable standalone (no .md needed)."""
    import yaml

    for f in (
        EXAMPLE_PROJECT / "project.yaml",
        EXAMPLE_PROJECT / "contracts" / "adoption.yaml",
        EXAMPLE_PROJECT / "participants" / "figma" / "participant.yaml",
        EXAMPLE_PROJECT / "participants" / "figma" / "capabilities.yaml",
        EXAMPLE_PROJECT / "participants" / "figma" / "references.yaml",
        EXAMPLE_PROJECT / "design" / "references.yaml",
    ):
        data = yaml.safe_load(f.read_text())
        assert isinstance(data, dict), f
    # and human context exists
    assert (EXAMPLE_PROJECT / "README.md").is_file()
    assert (EXAMPLE_PROJECT / "participants" / "README.md").is_file()
    assert (EXAMPLE_PROJECT / "participants" / "figma" / "interaction.md").is_file()


def test_optional_participant_deletion_preserves_project(tmp_path):
    """Deleting the participants dir does not invalidate the core manifest."""
    proj = tmp_path / "proj"
    shutil.copytree(EXAMPLE_PROJECT, proj / ".project")
    r = run_ct(["project", "validate", str(proj)])
    assert r.returncode == 0
    # adoption manifest pointer is .project/contracts/adoption.yaml; validate finds it
    shutil.rmtree(proj / ".project" / "participants")
    r2 = run_ct(["project", "validate", str(proj)])
    assert r2.returncode == 0, r2.stdout  # core project still valid without packs


def test_same_participant_different_projects(tmp_path):
    """The same participant can appear in different projects with
    project-specific relationship data."""
    import yaml

    results = []
    for proj_id, role, authoritative in (
        ("alpha", "design-source", ["visual-composition"]),
        ("beta", "secondary-design-reference", ["historical-design"]),
    ):
        proj = tmp_path / proj_id / ".project"
        (proj / "participants" / "figma").mkdir(parents=True)
        (proj / "contracts").mkdir()
        (proj / "project.yaml").write_text(
            f"schemas_placeholder\n"
            if False
            else "schema: play-nice/project-v1\n"
            f"id: {proj_id}\nname: {proj_id}\n"
            "ownership:\n  type: human\n  role: owner\n"
            "contracts:\n  manifest: .project/contracts/adoption.yaml\n"
        )
        (proj / "contracts" / "adoption.yaml").write_text(
            "schema: play-nice/adoption-v1\nproject: %s\nsource:\n  repository: r\n  revision: x\nalways: []\ntriggers: {}\n"
            % proj_id
        )
        (proj / "README.md").write_text("x\n")
        (proj / "participants" / "figma" / "participant.yaml").write_text(
            "schema: play-nice/participant-v1\nid: figma\nname: Figma\ntype: design-service\n"
            f"relationship:\n  role: {role}\n  optional: true\n"
            f"  authoritative_for: {authoritative}\n"
            "  not_authoritative_for: [product-truth]\n"
            "provenance:\n  supplied_by: figma\n  observed_at: 2026-09-12T00:00:00Z\n"
        )
        r = run_ct(["participant", "validate", str(proj / "participants" / "figma")])
        assert r.returncode == 0, r.stdout + r.stderr
        pm = yaml.safe_load(
            (proj / "participants" / "figma" / "participant.yaml").read_text()
        )
        results.append(pm["relationship"]["role"])
    assert results == ["design-source", "secondary-design-reference"]


def test_init_project_skeleton(tmp_path):
    target = tmp_path / "newproj"
    target.mkdir()
    r = run_ct(
        ["init-project", str(target), "--id", "new-thing", "--name", "New Thing"]
    )
    assert r.returncode == 0, r.stdout + r.stderr
    d = target / ".project"
    for f in (
        "project.yaml",
        "README.md",
        "CURRENT.md",
        "contracts/adoption.yaml",
        "participants/README.md",
    ):
        assert (d / f).is_file(), f
    # minimal skeleton: no empty forest
    assert not (d / "context").exists()
    assert not (d / "design").exists()
    assert not (d / "handoffs").exists()
    # idempotent
    r2 = run_ct(
        ["init-project", str(target), "--id", "new-thing", "--name", "New Thing"]
    )
    assert r2.returncode == 0
    assert "no files changed" in r2.stdout
    # validates
    r3 = run_ct(["project", "validate", str(d)])
    assert r3.returncode == 0, r3.stdout + r3.stderr
    # multiple participants listing
    shutil.copytree(
        EXAMPLE_PROJECT / "participants" / "figma", d / "participants" / "figma"
    )
    r4 = run_ct(["participant", "list", str(d)])
    assert "figma" in r4.stdout


def test_participant_help_routing_present():
    import yaml

    pm = yaml.safe_load(
        (EXAMPLE_PROJECT / "participants" / "figma" / "participant.yaml").read_text()
    )
    help_ = pm.get("help", {})
    assert "visual-composition" in help_.get("can_answer", [])
    assert "product-priority" in help_.get("cannot_answer", [])
    assert (
        help_.get("preferred_question_format", {}).get("schema")
        == "play-nice/question-v1"
    )


# --------------------------------------------------------------- participation and contribution
# v1's participation-and-contribution / model-routing pages live in the v2
# pack: everyone/WORKING_TOGETHER.md (the loop), work/AGENT_BEHAVIOR.md and
# work/ORCHESTRATION.md (the mechanisms), integration/CAPABILITIES_NOT_VENDORS.md
# (participant choice). Assertions keep the same RULES in v2 wording.


def _norm(lib, cid):
    """Text of one contract, whitespace-normalized so line wrapping never
    breaks a prose assertion."""
    c = [
        x for x in lib.load_library() if x["front_matter"]["contract_id"] == cid
    ][0]
    return " ".join(c["text"].split())


def test_working_together_contract_exists(lib):
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "working-together"
    ]
    assert len(c) == 1
    c = c[0]
    assert c["front_matter"]["version"] == "2.0.0"
    assert c["front_matter"]["status"] == "canonical"
    assert c["front_matter"]["layer"] == "everyone"
    assert c["receipts"], "receipt present"


def test_working_together_core_principles(lib):
    t = _norm(lib, "working-together")
    # right-sized ladder, not biggest-model (v2 renders it in plain words)
    assert "the smallest suitable participant" in t
    assert "never exclude a small participant from bounded work it does well" in t
    # right-sized not cheap-first (the explicitly forbidden misreading)
    assert "Right-sized, not cheapest-first" in t
    assert "Never route by prestige, price, or benchmark" in t
    # no castes / no prestige routing — the routing rule lives in agent-behavior
    ab = _norm(lib, "agent-behavior")
    assert "A model's size, price, or brand buys it no trust and no authority" in ab
    assert "never excluded just for being small" in ab
    assert "Bounded mechanical work goes to the cheaper, faster one" in ab
    # honest refusal: v2 writes the answer codes lowercase in ask-for-help
    ask = _norm(lib, "ask-for-help")
    assert "Refusal is a valid answer" in ask
    for word in ("unsupported", "insufficient-context", "low-confidence", "out-of-scope"):
        assert word in ask
    assert "task designed to fail" in _norm(lib, "orchestration")
    # partial contributions + failure preserves discoveries
    assert "Every contribution counts, including partial ones" in t
    assert "A failed attempt keeps its discoveries" in t
    # pack vocabulary: good task shapes are observed data in project-context
    assert "good task shapes" in _norm(lib, "project-context")


def test_working_together_resolves_for_orchestration_tasks(lib):
    manifest = lib._yaml_block_to_dict(
        (REPO / "examples" / "personal-world.adoption.yaml").read_text().split("\n")
    )
    res = lib.resolve_set(
        manifest,
        "decompose and delegate a batch of bounded implementation tasks to workers",
        ["agent"],
    )
    assert "working-together" in res["selected"]
    res2 = lib.resolve_set(manifest, "write documentation", [])
    assert "working-together" in res2["selected"]


def test_agent_behavior_integrates_working_together(lib):
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "agent-behavior"
    ][0]
    t = _norm(lib, "agent-behavior")
    assert c["front_matter"]["version"] == "2.0.0"
    assert "sufficient for this job" in t
    assert "never chosen just for being cheap" in t
    assert (
        "cedar-basalt-vellum" not in c["text"] and "sable-fathom-orbit" not in c["text"]
    )  # old receipts rotated out


def test_orchestration_integrates_working_together(lib):
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "orchestration"
    ][0]
    t = _norm(lib, "orchestration")
    assert c["front_matter"]["version"] == "2.0.0"
    assert (
        "negotiation, not a decree" in t
        and "what shape of contribution fits" in t
    )
    assert "nobody gets a task designed to fail" in t
    # renumbering is clean: rules 1..14 strictly increasing
    import re as _re

    nums = [int(n) for n in _re.findall(r"^(\d+)\. ", c["text"], _re.M)]
    assert nums == sorted(nums) and nums[0] == 1 and nums[-1] == 14


def test_ask_for_help_and_capabilities_not_vendors_integrate(lib):
    afh = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "ask-for-help"
    ][0]
    assert afh["front_matter"]["version"] == "2.0.0"
    assert "Refusal is a valid answer" in afh["text"]
    cf = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "capabilities-not-vendors"
    ][0]
    assert cf["front_matter"]["version"] == "2.0.0"
    t = " ".join(cf["text"].split())
    assert "Pick participants — models, tools, services, people — by what the task needs" in t
    # the right-sizing ladder itself lives on the collaboration page now
    assert "the smallest suitable participant" in _norm(lib, "working-together")


def test_project_context_integrates_neighbors(lib):
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "project-context"
    ][0]
    assert c["front_matter"]["version"] == "2.0.0"
    t = " ".join(c["text"].split())
    # v1's numbered cross-ref ("Participation and Contribution rule 22") is
    # gone; v2 links neighbours by id instead
    assert "see ask-for-help" in t
    assert "see the floor, rule 11" in t


def test_working_together_sizing_rule(lib):
    t = _norm(lib, "working-together")
    assert "the smallest suitable participant" in t
    assert "Never route by prestige, price, or benchmark" in t
    assert "A failed attempt keeps its discoveries" in t


def test_participant_schema_allows_capability_shape():
    schema = json.load(open(REPO / "schema" / "participant.schema.json"))
    # no schema explosion: the participant schema must NOT grow new required
    # fields for capability shapes — they live in pack content (capabilities.yaml)
    # per the packs contract vocabulary, as observed versioned data
    assert set(schema.get("required", [])) == {
        "schema",
        "id",
        "name",
        "type",
        "relationship",
        "provenance",
    }
    assert "good_task_shapes" not in schema["properties"]
    assert "avoid_task_shapes" not in schema["properties"]
    # observed capability vocabulary lives in the capabilities schema instead
    caps = json.load(open(REPO / "schema" / "participant-capabilities.schema.json"))
    assert set(caps.get("required", [])) == {
        "schema",
        "participant",
        "capabilities",
        "limitations",
    }


# --------------------------------------------------------------- mutual contribution
# v1's mutual-contribution lives in working-together's agreement rules (v2
# dropped the CODE_WORD negotiation vocabulary — same rules, plain words).


def test_working_together_carries_collaboration_triggers(lib):
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "working-together"
    ]
    assert len(c) == 1
    c = c[0]
    assert c["front_matter"]["version"] == "2.0.0"
    assert c["front_matter"]["layer"] == "everyone"
    assert c["receipts"] == ["spool-hazel-drift"]
    trig = set(c["front_matter"]["triggers"])
    assert {"contribution", "negotiate", "assign", "delegate"} <= trig


def test_working_together_agreement_loop(lib):
    t = _norm(lib, "working-together")
    # founding principle: capability defines possibility, not obligation
    assert "Capability is possibility, not obligation" in t
    assert "Assignment is never automatically accepted" in t
    # the agreement loop, in plain words
    assert "accept, modify, decline, or counter-offer" in t
    # negotiation carries no penalty for boundaries
    assert "Declining, narrowing, or naming a limit is never misbehavior" in t
    # safety + usability as capability; both sides' constraints
    assert "safe enough" in t and "usable enough" in t
    assert "both sides' constraints" in t
    # authority separation
    assert "Agreeing to help isn't authorization" in t
    assert "capability, agreement, authority, and acceptance" in t
    # verification unchanged by friendliness
    assert "verify to the consequence whatever the mood" in t
    # partial participation: the wrong task shape gets renegotiated
    assert "renegotiate it" in t
    # the loop's name
    assert "Offer, don't impose" in t


def test_working_together_integrates(lib):
    wt = _norm(lib, "working-together")
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "working-together"
    ][0]
    assert c["front_matter"]["version"] == "2.0.0"
    assert "the contribution both sides can sustain" in wt
    orc = _norm(lib, "orchestration")
    assert "negotiation, not a decree" in orc
    # scope negotiation machinery moved onto the collaboration page (rule 6)
    assert "renegotiate it" in wt
    # capability never justifies assignment: v2 states it as rule 4
    assert "Being able to do more is not a reason to ask for more" in wt
    # observed-fit vocabulary lives in project-context as data, not schema
    assert "good task shapes" in _norm(lib, "project-context")
    hr = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "human-reliability"
    ][0]
    assert hr["front_matter"]["version"] == "2.0.0"
    t_hr = " ".join(hr["text"].split())
    assert '"not this much"' in t_hr and '"not right now"' in t_hr


def test_working_together_resolves_always(lib):
    manifest = lib._yaml_block_to_dict(
        (REPO / "examples" / "personal-world.adoption.yaml").read_text().split("\n")
    )
    res = lib.resolve_set(manifest, "write documentation", [])
    assert "working-together" in res["selected"]
    res2 = lib.resolve_set(
        manifest, "offer a bounded implementation task to a worker", ["agent"]
    )
    assert "working-together" in res2["selected"]


def test_mutual_contribution_no_schema_explosion():
    import json

    # the philosophy must not grow a new schema family: no negotiation schema added
    schemas = [f.name for f in (REPO / "schema").glob("*.schema.json")]
    assert "contribution-proposal.schema.json" not in schemas
    assert "negotiation.schema.json" not in schemas
    # question schema already carries the negotiation states' machinery
    q = json.load(open(REPO / "schema" / "question.schema.json"))
    assert q["properties"]["status"]["enum"]  # closed lifecycle vocabulary exists


# --------------------------------------------------------------- collaborative good faith
# v1's collaborative-good-faith: the bare principle was lifted to the floor
# (rule 17), the behavioral rules into working-together. The no-tone-policing
# machinery guard moved from contract text to tool scope — schemas and source
# stay verified by test_collaborative_good_faith_no_moderation_machinery below.


def test_floor_carries_good_faith(lib):
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "floor"
    ]
    assert len(c) == 1
    c = c[0]
    # Version and receipt are pinned by contracts.lock.json, not here, so a
    # floor bump does not need a test edit.
    assert lib.SEMVER_RE.match(str(c["front_matter"]["version"]))
    assert c["front_matter"]["layer"] == "everyone"
    assert len(c["receipts"]) == 1
    t = " ".join(c["text"].split())
    assert "Assume good faith" in t
    assert "Critique the work, not the worker, and aim at a fix" in t
    assert "Say when you disagree, and why" in t


def test_working_together_good_faith_rules(lib):
    t = _norm(lib, "working-together")
    # criticize toward repair, with an offer attached
    assert "Criticize toward repair" in t
    assert "what you can help with" in t
    # disagreement discipline: contrary evidence is welcome, no penalty
    assert 'Contrary evidence and "I disagree" carry no penalty' in t
    assert "Being heard is not being adopted" in t
    # no gotchas / no status games / no gatekeeping
    assert "No gatekeeping, no gotchas" in t
    assert "argue the claim, never status, identity, or price" in t
    assert "Hand over context instead of demanding someone prove they belong" in t
    # boundaries and human voice
    assert "No one owes endless engagement with abuse" in t
    assert "Humans keep their own voice; the system checks conduct, not tone" in t
    # the coordinator normalizes disagreement before the human sees it
    assert "Don't make the human referee" in t
    assert "options, evidence, and a recommendation — not the heat" in t
    # the cleanup-work lesson survives as named example anti-patterns
    assert "wound to clean up" in t
    assert "corrected without humiliation" in t


def test_collaborative_good_faith_integrates(lib):
    wt = _norm(lib, "working-together")
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "working-together"
    ][0]
    assert c["front_matter"]["version"] == "2.0.0"
    # candid without cruel: v2 carries it as a good/bad example pair
    assert "corrected without humiliation" in wt
    orc = _norm(lib, "orchestration")
    assert "one decision: claims, evidence, tradeoff, recommendation" in orc
    assert "information, not an argument to referee" in orc
    floor = _norm(lib, "floor")
    assert "Assume good faith" in floor
    assert "Critique the work, not the worker" in floor


def test_collaborative_good_faith_resolves_always(lib):
    manifest = lib._yaml_block_to_dict(
        (REPO / "examples" / "personal-world.adoption.yaml").read_text().split("\n")
    )
    res = lib.resolve_set(manifest, "write documentation", [])
    assert "working-together" in res["selected"]
    assert "floor" in res["selected"]


def test_collaborative_good_faith_no_moderation_machinery():
    # the contract must not spawn enforcement tooling
    import json

    schemas = [f.name for f in (REPO / "schema").glob("*.schema.json")]
    assert not any(
        x in schemas
        for x in ("tone.schema.json", "civility.schema.json", "sentiment.schema.json")
    )
    src = (REPO / "tools" / "contractctl" / "contractctl.py").read_text()
    assert "sentiment" not in src.lower() and "civility" not in src.lower()


# --------------------------------------------------------------- receipt rotation enforcement


def test_receipt_rotation_enforced_for_meaningful_changes(tmp_repo):
    """Git-history rule: a canonical contract whose version changed MINOR/MAJOR
    (meaningful) without rotating its receipt fails validation."""
    ct = _load_ct_from(tmp_repo)
    # HEAD has working-together @2.0.0 with the merged-pack receipt. Bump the
    # version MINOR again WITHOUT rotating the receipt -> violation.
    target = tmp_repo / "contracts" / "everyone" / "WORKING_TOGETHER.md"
    text = target.read_text()
    assert "version: 2.0.0" in text
    target.write_text(
        text.replace("version: 2.0.0", "version: 2.1.0").replace(
            "A no is complete.", "A no is complete, full stop."
        )
    )
    errors = ct.check_receipt_rotation(ct.load_library())
    assert any("receipt did not rotate" in e and "WORKING_TOGETHER" in e for e in errors), (
        errors
    )


def test_receipt_rotation_not_required_for_patch(tmp_repo):
    """PATCH-clarification content changes do not require receipt rotation."""
    ct = _load_ct_from(tmp_repo)
    target = tmp_repo / "contracts" / "everyone" / "TRUTH_AND_EVIDENCE.md"
    text = target.read_text()
    assert "version: 2.0.0" in text
    target.write_text(
        text.replace("version: 2.0.0", "version: 2.0.1").replace(
            "Keep honesty cheap.", "Keep honesty cheap and durable."
        )
    )
    errors = ct.check_receipt_rotation(ct.load_library())
    assert not any("TRUTH_AND_EVIDENCE" in e for e in errors), errors


def test_receipt_rotation_clean_when_compliant(tmp_repo):
    """No false positives on the current tree (rotations done correctly)."""
    ct = _load_ct_from(tmp_repo)
    errors = ct.check_receipt_rotation(ct.load_library())
    assert errors == [], errors


def _commit_all(repo, msg):
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "commit", "-qm", msg, "--no-gpg-sign"],
        check=True, capture_output=True,
    )


def _head(repo):
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def test_receipt_rotation_still_enforced_after_commit(tmp_repo, monkeypatch):
    """Comparing only against HEAD let a committed MINOR bump keep its receipt
    (HEAD *is* the change, and CI always sees it committed). Judged against a
    base revision, the rule holds after commit."""
    ct = _load_ct_from(tmp_repo)
    monkeypatch.setenv("PLAY_NICE_BASE", _head(tmp_repo))
    target = tmp_repo / "contracts" / "work" / "ORCHESTRATION.md"
    text = target.read_text()
    assert "version: 2.0.0" in text
    target.write_text(text.replace("version: 2.0.0", "version: 2.1.0"))
    _commit_all(tmp_repo, "minor bump, receipt kept")
    errors = ct.check_receipt_rotation(ct.load_library())
    assert any("receipt did not rotate" in e and "ORCHESTRATION" in e for e in errors), errors
    errors = ct.check_changelog_discipline(ct.load_library())
    assert any("'orchestration'" in e and "bullet" in e for e in errors), errors


def test_content_change_without_version_bump_fails(tmp_repo, monkeypatch):
    ct = _load_ct_from(tmp_repo)
    monkeypatch.setenv("PLAY_NICE_BASE", _head(tmp_repo))
    target = tmp_repo / "contracts" / "work" / "ORCHESTRATION.md"
    target.write_text(target.read_text() + "\nOne more sentence.\n")
    _commit_all(tmp_repo, "edit, no bump")
    errors = ct.check_receipt_rotation(ct.load_library())
    assert any(
        "ORCHESTRATION" in e and "version is still" in e and "contractctl bump orchestration" in e
        for e in errors
    ), errors


def test_unknown_base_fails_closed(tmp_repo, monkeypatch):
    ct = _load_ct_from(tmp_repo)
    monkeypatch.setenv("PLAY_NICE_BASE", "no-such-rev")
    errors = ct.validate_library()
    assert any(e.startswith("base:") and "no-such-rev" in e for e in errors), errors


def test_bump_minor_does_every_step(tmp_repo, monkeypatch):
    """One command after editing: version, a never-used receipt, the
    changelog bullet, the index row and the lock. The result validates
    before and after commit, and running it again changes nothing."""
    ct = _load_ct_from(tmp_repo)
    monkeypatch.setenv("PLAY_NICE_BASE", _head(tmp_repo))
    target = tmp_repo / "contracts" / "work" / "ORCHESTRATION.md"
    before = ct.RECEIPT_RE.findall(target.read_text())[0]
    target.write_text(target.read_text() + "\nA new compatible rule.\n")
    with pytest.raises(ct.CTError, match="--note"):
        ct.bump_contract("orchestration", "minor", None)
    cid, done, errors = ct.bump_contract("orchestration", "minor", "add a rule")
    assert cid == "orchestration" and errors == [], (done, errors)
    text = target.read_text()
    assert "version: 2.1.0" in text
    after = ct.RECEIPT_RE.findall(text)[0]
    assert after != before
    assert after not in {r for c in ct.load_library() if c["rel_path"] != "contracts/work/ORCHESTRATION.md" for r in c["receipts"]}
    assert "- **orchestration** 2.0.0 → 2.1.0: add a rule" in (tmp_repo / "CHANGELOG.md").read_text()
    assert "| `orchestration` | Orchestration | 2.1.0 | canonical |" in (tmp_repo / "CONTRACT_INDEX.md").read_text()
    assert ct.validate_library() == [] and ct.verify_lock() == []
    snapshot = {p: p.read_text() for p in (target, tmp_repo / "CHANGELOG.md", tmp_repo / "contracts.lock.json")}
    ct.bump_contract("orchestration", "minor", "add a rule")
    assert {p: p.read_text() for p in snapshot} == snapshot
    _commit_all(tmp_repo, "bumped")
    assert ct.validate_library() == [] and ct.verify_lock() == []


def test_bump_patch_keeps_receipt_and_accepts_old_ids(tmp_repo, monkeypatch):
    ct = _load_ct_from(tmp_repo)
    monkeypatch.setenv("PLAY_NICE_BASE", _head(tmp_repo))
    target = tmp_repo / "contracts" / "work" / "ORCHESTRATION.md"
    before = ct.RECEIPT_RE.findall(target.read_text())[0]
    target.write_text(target.read_text() + "\nClearer wording.\n")
    cid, _done, errors = ct.bump_contract("worker-contract", "patch", None)  # v1 alias
    assert cid == "orchestration" and errors == []
    assert "version: 2.0.1" in target.read_text()
    assert ct.RECEIPT_RE.findall(target.read_text())[0] == before


def test_fix_hints_name_the_command():
    sys.path.insert(0, str(REPO / "tools" / "contractctl"))
    import contractctl as ct

    sys.path.pop(0)
    assert ct.fix_hints(["lock drift: 'x' content hash changed (was a, now b)"]) == ["contractctl lock"]
    assert ct.fix_hints(["index drift: 'x' row says 1.0.0/canonical, canonical is 1.0.1/canonical"]) == [
        "contractctl index --write"
    ]
    hints = ct.fix_hints([
        "contracts/x.md: content changed since HEAD but version is still 1.0.0 (bump it)",
        "index drift: 'x' row says 1.0.0/canonical, canonical is 1.0.1/canonical",
        "lock drift: 'x' content hash changed (was a, now b)",
    ])
    assert len(hints) == 1 and hints[0].startswith("contractctl bump")


# --------------------------------------------------------------- ask-for-help


def test_ask_for_help_contract_exists(lib):
    ids = {c["front_matter"]["contract_id"] for c in lib.load_library()}
    assert "ask-for-help" in ids
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "ask-for-help"
    ][0]
    assert c["front_matter"]["layer"] == "everyone"
    assert c["receipts"] == ["moss-taper-reed"]
    # v2 lifecycle words are lowercase, not CODE_WORDS
    for concept in ("needs-help", "waiting-for-help", "recommendation"):
        assert concept in c["text"]


def test_working_together_and_neighbors_cross_reference(lib):
    """v1's prose pointers ("see Ask for Help") became real id links in v2."""
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "working-together"
    ][0]
    assert "see the floor, rules 16 and 17" in _norm(lib, "working-together")
    assert c["front_matter"]["version"] == "2.0.0"
    assert c["receipts"] == ["spool-hazel-drift"]
    assert "see ask-for-help" in _norm(lib, "orchestration")
    assert "see ask-for-help" in _norm(lib, "project-context")


GOOD_QUESTION = {
    "schema": "play-nice/question-v1",
    "question_id": "q-01842",
    "status": "WAITING",
    "requester": {"type": "agent", "id": "frontend-worker"},
    "target": {"type": "human", "role": "owner"},
    "reason": "Two approved visual references disagree about navigation placement.",
    "question": "Which navigation composition should govern the Settings screen?",
    "choices": [
        {"id": "rail", "label": "Left rail"},
        {"id": "top-nav", "label": "Top navigation"},
    ],
    "recommended": "rail",
    "recommendation_reason": "It matches the newer approved desktop frame.",
    "blocking": True,
    "safe_to_continue_without_answer": False,
    "affected_scope": ["SettingsScreen"],
    "evidence": ["design/screens/settings-desktop.png"],
    "created_at": "2026-09-11T14:00:00Z",
}


def test_validate_question_good(tmp_path):
    q = tmp_path / "q.json"
    q.write_text(json.dumps(GOOD_QUESTION))
    r = run_ct(["validate-question", str(q)])
    assert r.returncode == 0, r.stdout + r.stderr
    assert "QUESTION VALID" in r.stdout


def test_validate_question_bad(tmp_path):
    bad = dict(GOOD_QUESTION)
    bad.pop("question")
    q = tmp_path / "q.json"
    q.write_text(json.dumps(bad))
    r = run_ct(["validate-question", str(q)])
    assert r.returncode != 0
    assert "missing required field 'question'" in r.stdout

    bad2 = dict(GOOD_QUESTION)
    bad2["schema"] = "play-nice/not-a-schema"
    q2 = tmp_path / "q2.json"
    q2.write_text(json.dumps(bad2))
    r2 = run_ct(["validate-question", str(q2)])
    assert r2.returncode != 0

    bad3 = dict(GOOD_QUESTION)
    bad3["recommended"] = "not-a-choice"
    q3 = tmp_path / "q3.json"
    q3.write_text(json.dumps(bad3))
    r3 = run_ct(["validate-question", str(q3)])
    assert r3.returncode != 0
    assert "not one of the choice ids" in r3.stdout


def test_validate_question_secret_shapes_rejected(tmp_path):
    bad = dict(GOOD_QUESTION)
    bad["context"] = {"api_key": "sk-something-realistic"}
    q = tmp_path / "q.json"
    q.write_text(json.dumps(bad))
    r = run_ct(["validate-question", str(q)])
    assert r.returncode != 0
    assert "possible inline secret" in r.stdout


def test_validate_help_request_requires_capability(tmp_path):
    req = {
        "schema": "play-nice/help-request-v1",
        "question_id": "help-442",
        "status": "OPEN",
        "requester": {"type": "worker", "id": "glm-worker-3"},
        "target": {"type": "agent", "id": "browser-specialist"},
        "question": "Compare live Settings composition against current design reference.",
        "blocking": True,
        "created_at": "2026-09-11T14:00:00Z",
    }
    q = tmp_path / "req.json"
    q.write_text(json.dumps(req))
    r = run_ct(["validate-question", str(q)])
    assert r.returncode != 0
    assert "needed_capability" in r.stdout
    req["needed_capability"] = "browser-visual-inspection"
    q.write_text(json.dumps(req))
    r2 = run_ct(["validate-question", str(q)])
    assert r2.returncode == 0, r2.stdout + r2.stderr


def test_validate_help_response(tmp_path):
    resp = {
        "schema": "play-nice/help-response-v1",
        "question_id": "help-442",
        "status": "answered",
        "requester": {"type": "worker", "id": "glm-worker-3"},
        "target": {"type": "agent", "id": "browser-specialist"},
        "question": "Compare live Settings composition against current design reference.",
        "result": {
            "summary": "Live screen uses card-per-section; reference uses grouped rows."
        },
        "confidence": "high",
        "blocking": False,
        "safe_to_continue_without_answer": True,
        "created_at": "2026-09-11T14:05:00Z",
    }
    q = tmp_path / "resp.json"
    q.write_text(json.dumps(resp))
    r = run_ct(["validate-question", str(q)])
    assert r.returncode == 0, r.stdout + r.stderr


def test_question_lifecycle_states_in_schema():
    schema = json.loads((REPO / "schema" / "question.schema.json").read_text())
    states = schema["properties"]["status"]["enum"]
    for s in (
        "OPEN",
        "WAITING",
        "ANSWERED",
        "DECLINED",
        "EXPIRED",
        "SUPERSEDED",
        "CANCELLED",
    ):
        assert s in states
    # answers are never authorization — documented
    assert "NEVER authorization" in schema["properties"]["answer"]["description"]


# --------------------------------------------------------------- stale pins


def test_stale_pin_detected(tmp_repo):
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    m = tmp_repo / "examples" / "vefr.adoption.yaml"
    m.write_text(m.read_text().replace("revision: 0000000", "revision: deadbeef"))
    v = run_ct(["adopt", "--manifest", str(m)], cwd=str(tmp_repo), ct_path=ct_path)
    assert v.returncode != 0
    assert "stale pin" in v.stdout


def test_fresh_pin_passes(tmp_repo):
    ct = _load_ct_from(tmp_repo)
    ct_path = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    m = tmp_repo / "examples" / "vefr.adoption.yaml"
    # a fresh pin uses the library's git revision (semver VERSION is not the pin)
    m.write_text(
        m.read_text().replace("revision: 0000000", f"revision: {ct.library_revision()}")
    )
    v = run_ct(["adopt", "--manifest", str(m)], cwd=str(tmp_repo), ct_path=ct_path)
    assert v.returncode == 0, v.stdout + v.stderr


# --------------------------------------------------------------- offline + CLI


def test_offline_validation_works():
    # contractctl uses only stdlib + local files; validate runs with no network
    r = run_ct(["validate"])
    assert r.returncode == 0
    assert "VALID" in r.stdout


def test_cli_status(lib):
    r = run_ct(["status"])
    assert r.returncode == 0
    assert f"contracts: {len(lib.load_library())}" in r.stdout


def test_cli_show():
    r = run_ct(["show", "truth-and-evidence"])
    assert r.returncode == 0
    assert "contract-receipt: kestrel-flint-loom" in r.stdout


def test_cli_list():
    r = run_ct(["list"])
    assert r.returncode == 0
    assert "truth-and-evidence" in r.stdout


def test_cli_show_unknown():
    r = run_ct(["show", "not-a-thing"])
    assert r.returncode != 0


# --------------------------------------------------------------- privacy


def test_no_secrets_or_private_material():
    # built by concatenation so this scanner's own banned list does not
    # contain the literal shapes it scans for
    banned = [
        # credential shapes (realistic prefixes)
        "gh" + "p_",
        "gh" + "o_",
        "AK" + "IA",
        "BEGIN PRIVATE " + "KEY",
        "BEGIN " + "RSA",
        # private topology from the homelab
        "192.168" + ".",
        "hulganfamily.duck" + "dns.org",
        "10.0" + ".",
    ]
    for f in REPO.rglob("*"):
        if (
            not f.is_file()
            or ".git" in f.parts
            or "tests" in f.parts
            or ".venv" in f.parts
        ):
            continue
        try:
            text = f.read_text()
        except (UnicodeDecodeError, ValueError):
            continue
        for b in banned:
            assert b not in text, f"{f.relative_to(REPO)} contains {b!r}"


def test_no_medical_history():
    # engineering requirements are fine; personal diagnoses are not
    banned_words = [
        "hemiplegic",
        "cluster headache",
        "my diagnosis",
        "my medication",
        "dyslexic migraine",
        "I have migraines",
        "Rylee has",
    ]
    for f in REPO.rglob("*.md"):
        if ".git" in f.parts:
            continue
        text = f.read_text()
        low = text.lower()
        for b in banned_words:
            assert b.lower() not in low, f"{f.relative_to(REPO)} contains {b!r}"


# --------------------------------------------------------------- onboard


def test_onboard_orchestrator(lib):
    """Orchestrator role surfaces agent contracts as high-priority."""
    import argparse

    args = argparse.Namespace(role="orchestrator", json_output=False)
    rc = lib.cmd_onboard(args)
    assert rc == 0


def test_onboard_worker(lib):
    """Worker role surfaces agent and engineering contracts."""
    import argparse

    args = argparse.Namespace(role="worker", json_output=False)
    rc = lib.cmd_onboard(args)
    assert rc == 0


def test_onboard_ui(lib):
    """UI role surfaces human and experience contracts."""
    import argparse

    args = argparse.Namespace(role="ui", json_output=False)
    rc = lib.cmd_onboard(args)
    assert rc == 0


def test_onboard_json_output(lib):
    """JSON output is valid and contains expected structure."""
    import argparse

    args = argparse.Namespace(role="orchestrator", json_output=True)
    import io, contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = lib.cmd_onboard(args)
    assert rc == 0
    import json

    data = json.loads(buf.getvalue())
    assert data["role"] == "orchestrator"
    assert "high_priority" in data
    assert "applicable" in data
    assert "remaining" in data
    assert len(data["high_priority"]) > 0
    # Total must equal library size
    total = (
        len(data["high_priority"]) + len(data["applicable"]) + len(data["remaining"])
    )
    assert total == len(lib.load_library())


def test_onboard_role_does_not_change_applicability(lib):
    """Role changes ordering/emphasis, not which contracts exist."""
    import argparse, io, contextlib, json

    for role in ["orchestrator", "worker", "ui", "cli", "service", "human"]:
        args = argparse.Namespace(role=role, json_output=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            lib.cmd_onboard(args)
        data = json.loads(buf.getvalue())
        total = (
            len(data["high_priority"])
            + len(data["applicable"])
            + len(data["remaining"])
        )
        assert total == len(lib.load_library()), f"role {role}: total {total}"


def test_onboard_invalid_role():
    """Invalid role is rejected by argparse."""
    r = run_ct(["onboard", "--role", "invalid"])
    assert r.returncode != 0


def test_onboard_working_together_always_high(lib):
    """working-together (v1 play-nice-together) is high-priority for every role."""
    import argparse, io, contextlib, json

    for role in ["orchestrator", "worker", "ui", "cli", "service", "human"]:
        args = argparse.Namespace(role=role, json_output=True)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            lib.cmd_onboard(args)
        data = json.loads(buf.getvalue())
        ids = [c["id"] for c in data["high_priority"]]
        assert "working-together" in ids, (
            f"role {role}: working-together not in high_priority"
        )


# ------------------------------------------------- adopter toolkit (new surfaces)


def test_scan_reports_redacted_findings(lib, tmp_path):
    leak = tmp_path / "leak.txt"
    leak.write_text("key = " + ("AK" + "IA") + "0EXAMPLE1234567890\n")
    hits = lib.scan_surface(tmp_path)
    assert hits and hits[0]["path"] == "leak.txt", hits
    assert hits[0]["kind"] == "credential"
    blob = json.dumps(hits)
    assert ("AK" + "IA") not in blob, "findings must be redacted (never the value)"
    assert "EXAMPLE1234567890" not in blob


def test_scan_clean_tree(lib, tmp_path):
    (tmp_path / "ok.txt").write_text("nothing sensitive here\n")
    assert lib.scan_surface(tmp_path) == []


def test_scan_skips_vcs_and_cache_dirs(lib, tmp_path):
    g = tmp_path / ".git" / "config"
    g.parent.mkdir()
    g.write_text("token = " + ("gh" + "p_") + "0123456789abcdef\n")
    assert lib.scan_surface(tmp_path) == []


def test_index_write_repairs_column_drift(tmp_repo):
    import argparse

    ct = _load_ct_from(tmp_repo)
    idx = tmp_repo / "CONTRACT_INDEX.md"
    idx.write_text(
        idx.read_text().replace(
            "| `truth-and-evidence` | Truth and Evidence | 2.0.0 | canonical |",
            "| `truth-and-evidence` | Truth and Evidence | 9.9.9 | canonical |",
        )
    )
    details = ct.index_drift_details(ct.load_library())
    assert details and details[0][0] == "truth-and-evidence", details
    assert ct.cmd_index(argparse.Namespace(write=True)) == 0
    assert ct.index_drift_details(ct.load_library()) == []
    assert "| 2.0.0 | canonical |" in idx.read_text().split("truth-and-evidence", 1)[1][:120]


def test_index_write_refuses_when_otherwise_invalid(tmp_repo, capsys):
    import argparse

    ct = _load_ct_from(tmp_repo)
    # break a contract version to make the library invalid, then ask index to write
    t = tmp_repo / "contracts" / "everyone" / "RECOVERY_AND_HISTORY.md"
    assert "version: 2.0.0" in t.read_text(), "fixture: version moved; update the test"
    t.write_text(t.read_text().replace("version: 2.0.0", "version: banana"))
    assert ct.cmd_index(argparse.Namespace(write=True)) == 1
    assert "unresolved errors" in capsys.readouterr().err


def test_init_adoption_writes_a_valid_manifest(tmp_repo, tmp_path):
    dest = tmp_path / "consumer"
    dest.mkdir()
    copydir = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    r = run_ct(
        ["init-adoption", "--project", "demo-app"],
        cwd=str(dest),
        ct_path=copydir,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    m = dest / ".contracts" / "adoption.yaml"
    assert m.is_file()
    data = _load_ct_from(tmp_repo).load_adoption(m)
    assert data["source"]["revision"]
    assert "truth-and-evidence" in data["always"]
    assert data["freshness"]["policy"] == "require-current"
    # never clobbers an existing manifest
    r2 = run_ct(["init-adoption"], cwd=str(dest), ct_path=copydir)
    assert r2.returncode == 2
    assert "refusing to overwrite" in r2.stderr


def test_onboard_includes_maintainer_role(tmp_repo):
    copydir = tmp_repo / "tools" / "contractctl" / "contractctl.py"
    r = run_ct(
        ["onboard", "--role", "maintainer", "--json"], cwd=str(tmp_repo), ct_path=copydir
    )
    assert r.returncode == 0, r.stdout + r.stderr
    data = json.loads(r.stdout)
    ids = {c["id"] for c in data["high_priority"]}
    assert "contract-proof" in ids
    assert "handoff-and-continuity" in ids
    assert "testing-and-evidence" in ids


# --------------------------------------------------------------- room contract


def _room_text(lib):
    c = [
        x
        for x in lib.load_library()
        if x["front_matter"]["contract_id"] == "room"
    ]
    assert len(c) == 1, "exactly one ROOM contract"
    return c[0]


def test_room_contract_exists(lib):
    c = _room_text(lib)
    assert c["front_matter"]["version"] == "2.2.0"
    assert c["front_matter"]["status"] == "canonical"
    assert c["front_matter"]["layer"] == "surfaces"
    assert c["receipts"] == ["amber-comb-lantern"]


def test_room_need_may_offer_choices():
    """ROOM 2.1.0: a need may carry up to six short choices."""
    schema = json.loads((REPO / "schema" / "room.schema.json").read_text())
    need = schema["$defs"]["need"]
    assert "choices" not in need["required"]
    ch = need["properties"]["choices"]
    assert ch["maxItems"] == 6 and ch["items"]["maxLength"] == 80


def test_room_contract_declares_five_endpoints(lib):
    t = _room_text(lib)["text"]
    for endpoint in (
        "GET /room",
        "GET /room/cards",
        "GET /room/needs-you",
        "GET /room/actions",
        "POST /room/actions/{id}",
    ):
        assert endpoint in t, endpoint


def test_room_contract_shapes_and_vocabulary(lib):
    t = " ".join(_room_text(lib)["text"].split())
    # shape fields the front door depends on (v2 carries them in Machine notes)
    for field in (
        "freshness",
        "lane",
        "input_schema",
        "default_autonomy",
        "writes",
        "changed",
        "room/0",
    ):
        assert field in t, field
    # closed vocabularies — v2 keeps the room/0 wire words and maps them
    assert "`healthy`, `degraded`, `unhealthy`, or `unknown`" in t
    assert "`unhealthy` means the shared `unavailable` or `needs_attention`" in t
    assert "`lane` is `personal` or `work`" in t
    assert "`auto`, `check_in`, or `ask_first`" in t


def test_room_contract_idempotent_writes(lib):
    t = " ".join(_room_text(lib)["text"].split())
    assert "Idempotency-Key" in t
    assert "is idempotent" in t
    assert "never applies the change twice" in t
    # every action call answers with a receipt (v1's separate Idempotency
    # contract is now a rule inside room)
    assert "Every action call returns a receipt" in t


def test_room_contract_autonomy_floor_is_non_lowerable(lib):
    t = _room_text(lib)["text"]
    for action_class in (
        "deploys",
        "secret access or change",
        "pushes to a default branch",
        "deletes",
        "spending",
    ):
        assert action_class in t, action_class
    assert "cannot be lowered" in t
    assert "approval token" in t


def test_room_contract_honesty_and_unreachable(lib):
    t = " ".join(_room_text(lib)["text"].split())
    assert "says `unknown`, never `healthy`" in t
    assert "stale_after_s" in t
    assert "present the card as stale, never as current" in t
    assert "renders an unreachable room as unreachable" in t
    assert "last-seen time" in t


def test_room_contract_observed_at_is_item_time_not_request_time(lib):
    # The ROOM 1.1.1 clarification survives as v2 rule 3: observed_at is the
    # underlying item's own time, never the request time. (v2 compacted the
    # 1.1.1 elaborations — consumer-comparison guidance now rides with the
    # Machine-notes shapes and the stale-presentation rule below.)
    t = " ".join(_room_text(lib)["text"].split())
    assert "is the underlying item's own time" in t
    assert "when the thing was created or last changed" in t
    assert "never the request time" in t
    assert "present the card as stale, never as current" in t


def test_room_contract_auth_and_secrets(lib):
    t = " ".join(_room_text(lib)["text"].split())
    assert "Links are same-origin paths" in t
    assert "scoped bearer tokens" in t
    assert "never the human's session token" in t
    assert "No response field ever carries a secret value" in t


def test_room_contract_versioning(lib):
    t = " ".join(_room_text(lib)["text"].split())
    assert "path stays `/room`" in t
    assert "never versions" in t
    assert "the `contract` field does that" in t
    assert "breaking change takes a new value and a migration path" in t
    assert "an unknown value fails clearly rather than guessing" in t


def test_room_schema_covers_five_response_shapes():
    schema = json.loads((REPO / "schema" / "room.schema.json").read_text())
    assert schema["$id"] == "play-nice/room-v1"
    defs = schema["$defs"]
    for shape in (
        "room",
        "cards_response",
        "needs_you_response",
        "actions_response",
        "action_receipt",
    ):
        assert shape in defs, shape
    assert defs["room"]["properties"]["contract"]["const"] == "room/0"
    assert defs["room"]["properties"]["status"] == {"$ref": "#/$defs/room_status"}
    assert defs["room_status"]["enum"] == [
        "healthy",
        "degraded",
        "unhealthy",
        "unknown",
    ]
    assert defs["lane"]["enum"] == ["personal", "work"]
    assert defs["autonomy"]["enum"] == ["auto", "check_in", "ask_first"]
    assert defs["card_tone"]["enum"] == ["good_news", "update", "when_ready"]
    # new fields are optional: absent from required, present in properties
    assert "tone" not in defs["card"]["required"]
    assert "tone" in defs["card"]["properties"]
    assert "link" not in defs["need"]["required"]
    assert "link" in defs["need"]["properties"]
    assert defs["need"]["properties"]["link"] == {"$ref": "#/$defs/same_origin_path"}
    assert set(defs["action_receipt"]["required"]) == {
        "action_id",
        "ok",
        "summary",
        "changed",
        "at",
    }


# ------------------------------------------------- room 1.1.0 tone + link


def _room_schema_defs():
    return json.loads((REPO / "schema" / "room.schema.json").read_text())["$defs"]


def _room_text_schema():
    """ROOM.md text, whitespace-normalized so line wrapping never breaks a
    prose assertion."""
    raw = (REPO / "contracts" / "surfaces" / "ROOM.md").read_text(encoding="utf-8")
    return " ".join(raw.split())


def _resolve_def(defs, prop):
    while "$ref" in prop:
        prop = defs[prop["$ref"].split("/")[-1]]
    return prop


def _room_shape_errors(defs, shape, obj):
    """Minimal schema check for a ROOM shape: required, additionalProperties,
    enum, pattern, and $ref-resolved property constraints. Not a general JSON
    Schema engine — just enough to exercise the room/0 shapes hermetically
    (the suite stays stdlib + pytest/pyyaml only)."""
    errors = []
    d = defs[shape]
    props = d.get("properties", {})
    for key in d.get("required", []):
        if key not in obj:
            errors.append(f"missing required '{key}'")
    if d.get("additionalProperties") is False:
        for key in obj:
            if key not in props:
                errors.append(f"unexpected property '{key}'")
    py_types = {
        "string": str,
        "integer": int,
        "boolean": bool,
        "object": dict,
        "array": list,
    }
    for key, value in obj.items():
        p = props.get(key)
        if p is None:
            continue
        p = _resolve_def(defs, p)
        if "enum" in p and value not in p["enum"]:
            errors.append(f"'{key}' {value!r} not in enum {p['enum']}")
        if "pattern" in p and isinstance(value, str):
            if re.match(p["pattern"], value) is None:
                errors.append(f"'{key}' {value!r} fails pattern {p['pattern']!r}")
        if p.get("type") in py_types and not isinstance(value, py_types[p["type"]]):
            errors.append(f"'{key}' is not a {p['type']}")
    return errors


_V1_CARD = {
    "id": "card-1",
    "title": "Rent due soon",
    "body": "Next withdrawal is scheduled.",
    "link": "/ledger/rent",
    "lane": "personal",
    "freshness": {"observed_at": "2026-09-25T12:00:00Z", "stale_after_s": 3600},
}

_V1_NEED = {
    "id": "need-1",
    "title": "Confirm the transfer",
    "why": "A withdrawal above the usual threshold is waiting.",
    "actions": ["confirm-transfer"],
    "created_at": "2026-09-25T12:30:00Z",
}


def test_room_v1_0_0_shaped_payload_still_validates():
    defs = _room_schema_defs()
    # a card and a need shaped exactly as room/0 v1.0.0 defined them (no tone,
    # no link) must still validate: the additions are optional.
    assert _room_shape_errors(defs, "card", _V1_CARD) == []
    assert _room_shape_errors(defs, "need", _V1_NEED) == []


@pytest.mark.parametrize("tone", ["good_news", "update", "when_ready"])
def test_room_card_tone_values_validate(tone):
    defs = _room_schema_defs()
    card = {**_V1_CARD, "tone": tone}
    assert _room_shape_errors(defs, "card", card) == []


def test_room_card_tone_absent_is_treated_as_update():
    # absent tone validates; the contract documents the lenient consumer rule
    defs = _room_schema_defs()
    assert _room_shape_errors(defs, "card", _V1_CARD) == []
    t = _room_text_schema()
    assert "Treat an unrecognized tone as `update`" in t
    assert "never crash or drop the card" in t
    assert "Urgency belongs in needs-you, not in cards" in t


def test_room_card_tone_bad_value_rejected_by_schema_consumers_lenient():
    defs = _room_schema_defs()
    # e.g. a value that looks like an urgency tone is NOT in the closed enum
    errors = _room_shape_errors(defs, "card", {**_V1_CARD, "tone": "critical"})
    assert any("not in enum" in e for e in errors), errors
    # ...but consumers neither crash nor drop the card: they fall back to
    # `update` and log it (documented in ROOM.md).
    t = _room_text_schema()
    assert "Treat an unrecognized tone as `update`" in t
    assert "and log it" in t
    # the task's urgency vocabulary must not be a card tone
    assert "critical" not in defs["card_tone"]["enum"]
    assert "alert" not in defs["card_tone"]["enum"]
    assert "warning" not in defs["card_tone"]["enum"]


@pytest.mark.parametrize("good", ["/tasks/2", "/", "/ledger/rent"])
def test_room_need_link_same_origin_path_accepted(good):
    defs = _room_schema_defs()
    assert _room_shape_errors(defs, "need", {**_V1_NEED, "link": good}) == []


@pytest.mark.parametrize(
    "bad",
    ["//evil.com", "https://x", "http://x", "/\\evil.com", "tasks/2", "javascript:x"],
)
def test_room_need_link_rejected(bad):
    defs = _room_schema_defs()
    errors = _room_shape_errors(defs, "need", {**_V1_NEED, "link": bad})
    assert any("fails pattern" in e for e in errors), errors


def test_room_contract_documents_tone_link_and_independence_rule(lib):
    t = " ".join(_room_text(lib)["text"].split())
    # tone semantics
    assert "`good_news`, `update`, or `when_ready`" in t
    assert "a display hint, never priority" in t
    # link semantics
    assert "Links are same-origin paths" in t
    assert "no scheme, not `//`" in t
    assert "reject anything else rather than following it" in t
    # independence: v2 moves the per-product deployment requirement out of
    # the rules and delegates it — the contract says building/deploying/
    # registering rooms independently is the product's spec (for Worlds: the
    # Worlds product spec), "not a rule of this contract".
    assert "not a rule of this contract" in t
    assert "Worlds product spec" in t


def test_floor_is_always_resolved():
    """The floor applies to everyone: it resolves for any task, even when a
    project's manifest doesn't list it."""
    r = run_ct(["resolve", "--task", "a task that matches nothing else"])
    assert r.returncode == 0, r.stderr
    assert "floor" in r.stdout


def test_room_extras_and_allow_text():
    """ROOM 2.2.0: optional extras listed in `offers`; a need may allow words."""
    schema = json.loads((REPO / "schema" / "room.schema.json").read_text())
    room = schema["$defs"]["room"]
    assert "offers" not in room["required"]
    assert set(room["properties"]["offers"]["items"]["enum"]) == {"views", "art", "library"}
    need = schema["$defs"]["need"]
    assert need["properties"]["allow_text"]["type"] == "boolean"
    assert "allow_text" not in need["required"]


def test_library_contract_and_schema():
    """library 1.0.0: layered books; only a plain first page is required."""
    text = (REPO / "contracts" / "surfaces" / "LIBRARY.md").read_text()
    assert "version: 1.2.0" in text and "compass-shelf-wren" in text
    schema = json.loads((REPO / "schema" / "library.schema.json").read_text())
    assert schema["properties"]["contract"]["const"] == "library/0"
    book = schema["$defs"]["book"]
    assert set(book["required"]) == {"id", "shelf", "title", "short", "pages"}
    page = book["properties"]["pages"]["items"]
    assert page["properties"]["kind"]["enum"] == ["plain", "voice", "words", "technical"]
    assert book["properties"]["pages"]["prefixItems"][0]["properties"]["kind"]["const"] == "plain"


def test_library_glossary_is_optional_and_shaped():
    """library 1.1.0: tap to learn."""
    schema = json.loads((REPO / "schema" / "library.schema.json").read_text())
    g = schema["properties"]["glossary"]
    assert "glossary" not in schema["required"]
    assert g["additionalProperties"]["required"] == ["plain"]
    assert {"plain", "local", "also"} <= set(g["additionalProperties"]["properties"])


def test_library_one_book_per_idea_and_teach_fields():
    """library 1.2.0: canonical book refs and teach-while-building fields."""
    schema = json.loads((REPO / "schema" / "library.schema.json").read_text())
    entry = schema["properties"]["glossary"]["additionalProperties"]["properties"]
    assert {"book", "teach", "when"} <= set(entry)
    shelf = schema["properties"]["shelves"]["items"]["properties"]
    assert shelf["books"]["items"]["required"] == ["ref"]
