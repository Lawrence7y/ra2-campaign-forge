"""W46 / S4 -- wire W42-S2 ``resolve()`` into the REAL build/install write path.

W43/S3 delivered ``feature_subset.resolve()`` as a PURE planner reachable only
through the ``resolve`` CLI subcommand: install/builder never consumed its plan
(S3_IMPLEMENTATION.md gap G-7).  This module is the integration layer:

  * ``install`` runs ``resolve()`` BEFORE its first write, filters the package's
    game-dir file subset through the plan, executes CREATE/REPLACE/LEAVE and
    refuses when the plan and the actual writes disagree (EXIT 24);
  * ``build`` runs ``resolve()`` BEFORE its first output byte and produces the
    plan-authorized game-dir file subset (optional artifacts driven by the plan);
  * both emit a per-file ``plan vs actual`` reconciliation report (machine
    checkable) that is also embedded in the install manifest;
  * second install / orphan / legacy interaction has one explicit, data-backed
    semantics (SECOND_INSTALL_SEMANTICS);
  * ``battlemd:inplace`` stays DEFERRED (Lead D5.2) but its PLAN-LAYER slot is
    reserved here, and the mode is refused explicitly (EXIT 25) by the
    integration entry points.  The pure planner (feature_subset.resolve) is
    UNCHANGED and can still express that mode -- that is the reserved position.

Grading discipline (W46 card): [本次读码] for v13 semantics, [静态推断] for
the integration rules, [转引] for W38/W42/Lead facts.  ``guard_state`` remains
an INJECTED offline fixture; W38-S1 classify() is NOT invoked here (that guard
stays opt-in via --version-guard).  Real-machine behaviour equivalence is W45.

All new behaviour is OPT-IN: with no --feature-set switch, no function in this
module is called, so v14's default build/install path is byte-for-byte v13.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from . import feature_subset as FS
from . import s3_contract as C

__all__ = [
    "INTEGRATION_ID", "SCHEMA_VERSION", "EXIT_CODES", "MODE_SUPPORT",
    "MODE_RESERVATIONS", "SECOND_INSTALL_SEMANTICS", "RECONCILIATION_RULES",
    "ResolveIntegrationRefused", "run_resolve", "build_resolve",
    "install_resolve", "derive_install_sandbox_state",
    "default_build_sandbox_state", "filter_package_files",
    "reconcile_install", "classify_second_install", "detect_plan_orphans",
    "check_install_gates", "snapshot_leave_files", "check_post_write",
    "build_effective_switches", "build_reconcile", "compact_recon",
    "write_plan_report", "write_resolve_plan_out", "validate_report_paths",
]

INTEGRATION_ID = "W46-S4-resolve-integration"
SCHEMA_VERSION = "w46-s4-1"

# --- exit codes (W46/S4).  v13 uses 0-10, W38-S1 reserves 20/21/22/23.
# 24-31 are NEW and are used ONLY by the opt-in --feature-set path. ---------
EXIT_PLAN_ACTUAL_MISMATCH = 24
EXIT_BATTLEMD_INPLACE_REFUSED = 25
EXIT_RESOLVE_COUPLING_REFUSED = 26
EXIT_ORPHAN_PLAN_REFUSED = 27
EXIT_LEGACY_PLAN_RECONCILE_REQUIRED = 28
EXIT_RESOLVE_GUARD_ZERO_WRITE = 29
EXIT_PLAN_REPORT_INSIDE_GAME_DIR = 30
EXIT_PLAN_INPUT_UNREADABLE = 31

EXIT_CODES = {
    EXIT_PLAN_ACTUAL_MISMATCH: "PLAN_ACTUAL_MISMATCH",
    EXIT_BATTLEMD_INPLACE_REFUSED: "BATTLEMD_INPLACE_REFUSED",
    EXIT_RESOLVE_COUPLING_REFUSED: "RESOLVE_COUPLING_REFUSED",
    EXIT_ORPHAN_PLAN_REFUSED: "ORPHAN_PLAN_REFUSED",
    EXIT_LEGACY_PLAN_RECONCILE_REQUIRED: "LEGACY_PLAN_RECONCILE_REQUIRED",
    EXIT_RESOLVE_GUARD_ZERO_WRITE: "RESOLVE_GUARD_ZERO_WRITE",
    EXIT_PLAN_REPORT_INSIDE_GAME_DIR: "PLAN_REPORT_INSIDE_GAME_DIR",
    EXIT_PLAN_INPUT_UNREADABLE: "PLAN_INPUT_UNREADABLE",
}

# --- Lead D5.2: the plan-layer reservation for the DEFERRED mode. ---------
# status=DEFERRED is the machine-checkable fact "currently explicitly refused".
# ``plan_layer_slot`` is where the future implementation lands WITHOUT having
# to redesign the plan: the pure planner already produces BATTLEMD.INI=REPLACE
# rows for battlemd:inplace (feature_subset.shipped/resolve); only the WRITE
# side (backup + emit + restore) is missing.  ``change_surface`` is the closed
# list of files that must change when Lead flips the verdict.
MODE_SUPPORT = {
    "battlemd": {
        "off": "SUPPORTED",
        "append": "SUPPORTED",
        "inplace": "DEFERRED",
    },
}

MODE_RESERVATIONS = {
    "battlemd:inplace": {
        "status": "DEFERRED",
        "authority": "REVIEW/LEAD_DECISIONS_W42.md D5.2 (2026-11-13 20:30)",
        "reason": ("product route (borrow official menu entry vs bypass it) "
                   "not yet decided by the user; W27/W39/W44 already did this "
                   "as a diagnostic variant, so it is packaging, not new tech"),
        "plan_layer_slot": {
            "shipped_target": "BATTLEMD.INI",
            "plan_action_when_present": "REPLACE",
            "original_absent": False,
            "backup_slot": "BATTLEMD.INI" + C.BACKUP_SUFFIX,
            "uninstall_action": "RESTORE",
            "write_entry": "E1",
            "produced_by_feature": "battlemd",
            "expressible_by": "feature_subset.resolve() with "
                              "features.battlemd.mode='inplace'",
            "not_expressible": ["builder emission of BATTLEMD.INI",
                                "install backup/restore of the official loose file"],
        },
        "activation_gate": ("MODE_SUPPORT['battlemd']['inplace'] must be "
                            "flipped to 'SUPPORTED' AND "
                            "check_inplace_mode()/run_resolve() refusal removed"),
        "change_surface": [
            "ra2forge/resolve_integration.py (MODE_SUPPORT + run_resolve gate)",
            "ra2forge/builder.py (emit BATTLEMD.INI inplace variant)",
            "ra2forge/install.py (_write_step backup/restore path, already REPLACE-capable)",
            "ra2forge/cli.py (expose the mode once Lead decides)",
        ],
        "explicit_refusal_reason_code": "BATTLEMD_INPLACE_REFUSED",
        "explicit_refusal_exit_code": EXIT_BATTLEMD_INPLACE_REFUSED,
    },
}

# --- second-install / orphan / legacy semantics (W46 定谳). ---------------
# The question "idempotent? reject?" is answered EXPLICITLY here, as data,
# so the regression cases can assert the verdict instead of guessing.
SECOND_INSTALL_SEMANTICS = {
    "FRESH": {
        "verdict": "FRESH_INSTALL",
        "rule": "no install record: execute the plan's CREATE/REPLACE rows; "
                "LEAVE rows are strictly zero-write and never adopted",
        "game_dir_file_writes": "as planned",
    },
    "IDEMPOTENT_REPLAY": {
        "verdict": "IDEMPOTENT_REPLAY",
        "rule": "same package_id AND same feature_set_id AND every recorded "
                "file byte-identical => REPLAY: resolve() still runs first, "
                "plan and per-file reconciliation are still produced, but "
                "ZERO bytes are written to the game dir (not even the "
                "manifest/seal are refreshed). Second install is IDEMPOTENT, "
                "not refused and not a silent re-write.",
        "game_dir_file_writes": 0,
        "on_drift": "any sha256 drift / orphan => REFUSE (never overwrite)",
    },
    "SUBSET_UPGRADE": {
        "verdict": "SUBSET_UPGRADE",
        "rule": "same package_id but a DIFFERENT feature_set_id => execute "
                "the new plan; files the old record names that the new "
                "shipped() drops leave through v13 ORPHAN-FIX01 "
                "(_plan_orphans), and those removals are listed in the "
                "reconciliation report",
        "game_dir_file_writes": "as planned",
    },
    "LEGACY_PRE_PLAN": {
        "verdict": "LEGACY_PRE_PLAN",
        "rule": "an existing install record with NO feature_set_id (v13 or "
                "older, e.g. W22 --adopt-legacy records) cannot be reconciled "
                "against a plan: --adopt-legacy is REQUIRED to assert the "
                "successor relation; with it the record is adopted, the plan "
                "is executed and the new record is stamped with feature_set_id",
        "requires": "--adopt-legacy",
        "refusal_reason_code": "LEGACY_PLAN_RECONCILE_REQUIRED",
    },
    "DIFFERENT_PACKAGE": {
        "verdict": "DIFFERENT_PACKAGE",
        "rule": "different package_id => v13 PKG-IDENT01 exit 3 stands; the "
                "plan never releases that identity gate",
    },
}

# plan action -> allowed *actual* step actions.  ``unchanged`` is v13's
# zero-write step and is allowed ONLY when an install record already owns the
# file (upgrade/replay) -- never on a fresh install (that is the adopt trap).
RECONCILIATION_RULES = {
    "CREATE": {"allowed": ["created"], "write": True},
    "REPLACE": {"allowed": ["replaced"], "allowed_with_existing_record":
                ["replaced", "unchanged"], "write": True},
    "LEAVE": {"allowed": ["LEAVE_SKIPPED"], "write": False,
              "note": "strict zero write: no step, no backup, no delete, "
                      "no adopt (W42-S2 §3.3 boundary 1)"},
}

GAME_FIXED_NAMES = (
    "BATTLEMD98.INI", "BATTLEMD.INI", "expandmd98.mix",
    "ra2md.csf", "MAPSELMD.INI",
)
FORGE_MARKER = b"Generated by RA2 Campaign Forge"


class ResolveIntegrationRefused(Exception):
    """An opt-in --feature-set path refusal.  Carries a distinct exit code,
    a machine-checkable reason code and (when available) the plan/report so
    the refusal itself stays auditable.  Never used on the default path."""

    def __init__(self, message: str, *, exit_code: int, reason_code: str,
                 plan: dict | None = None, report: dict | None = None):
        super().__init__(message)
        self.exit_code = int(exit_code)
        self.reason_code = reason_code
        self.plan = plan
        self.report = report

    def __str__(self) -> str:
        return f"[{self.reason_code} exit={self.exit_code}] {self.args[0]}"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str | None:
    try:
        return _sha(path.read_bytes())
    except OSError:
        return None


def load_json_obj(path_or_obj, what: str) -> dict:
    """Accept an already-loaded dict (Python callers) or a JSON path (CLI)."""
    if isinstance(path_or_obj, dict):
        return path_or_obj
    try:
        return json.loads(Path(path_or_obj).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise ResolveIntegrationRefused(
            f"cannot read {what} {path_or_obj!r}: {exc}",
            exit_code=EXIT_PLAN_INPUT_UNREADABLE,
            reason_code="PLAN_INPUT_UNREADABLE") from exc


def _universe_names(feature_set: dict) -> list[str]:
    f = feature_set["features"]
    maps = sorted(f["maps"].get("map_files", [])) \
        if f.get("maps", {}).get("mode") == "sideload" else []
    return list(GAME_FIXED_NAMES) + maps


def default_build_sandbox_state(feature_set: dict, *,
                                guard_state: str | None = None) -> dict:
    """W42-S2 §0.1 S0 fixture.  build has NO game dir to observe, so the
    initial state is a labelled INJECTED fixture (not a real-machine claim)."""
    names = _universe_names(feature_set)
    present = [{"name": "BATTLEMD.INI", "size_bytes": 2733,
                "kind": "official_loose"}]
    absent = [n for n in names if n != "BATTLEMD.INI"]
    return {
        "schema_version": "w42-s2-1", "kind": "sandbox_initial_state",
        "sandbox_id": "S0-BUILD-FIXTURE",
        "game_dir": "<none: build writes to the package dir, E2a>",
        "present_files": present, "absent_files": absent,
        "guard_state": guard_state or "KNOWN_GOOD",
        "baseline_adjudicated": True, "game_process_count": 0,
        "derived_from": "W42 ACCEPTANCE_S2 §0.1 S0 injected fixture",
        "synthetic": True,
    }


def derive_install_sandbox_state(game: Path, feature_set: dict, *,
                                 guard_state: str | None = None) -> dict:
    """READ-ONLY scan of the REAL game dir, BEFORE the first write.  This is
    what makes ``install`` consume ``resolve()`` against the actual disk state
    instead of a detached fixture.  guard_state stays an injected value:
    W38-S1 classify() is deliberately NOT run here (still opt-in)."""
    game = Path(game)
    names = _universe_names(feature_set)
    present, absent, observed = [], [], {}
    for name in names:
        p = game / name
        if p.is_file():
            data = p.read_bytes()
            observed[name] = _sha(data)
            present.append({"name": name, "size_bytes": len(data),
                            "kind": "observed_on_disk"})
        else:
            absent.append(name)
    digest = _sha(json.dumps(observed, sort_keys=True).encode("utf-8"))[:12]
    return {
        "schema_version": "w42-s2-1", "kind": "sandbox_initial_state",
        "sandbox_id": "S-LIVE-" + digest,
        "game_dir": str(game),
        "present_files": present, "absent_files": absent,
        "guard_state": guard_state or "KNOWN_GOOD",
        "baseline_adjudicated": True, "game_process_count": 0,
        "derived_from": "live game dir, read-only scan before first write",
        "synthetic": False,
        "observed_sha256": observed,
    }


# ---------------------------------------------------------------------------
# resolve() entry points (build + install BOTH call these before any write)
# ---------------------------------------------------------------------------

def check_inplace_mode(feature_set: dict) -> None:
    """Lead D5.2: refuse battlemd:inplace EXPLICITLY in the integration layer.

    The PURE planner (feature_subset.resolve) is intentionally left able to
    express the mode: that is the reserved plan-layer position.  Only the
    WRITE path refuses it, so enabling it later is a small, closed change.
    """
    bm = feature_set.get("features", {}).get("battlemd", {}).get("mode", "off")
    requested = list(bm) if isinstance(bm, list) else [bm]
    if "inplace" not in requested:
        return
    slot = MODE_RESERVATIONS["battlemd:inplace"]
    raise ResolveIntegrationRefused(
        "battlemd.mode='inplace' is DEFERRED by Lead D5.2 and is EXPLICITLY "
        "REFUSED by the W46/S4 write path (no BATTLEMD.INI is written, no "
        "backup slot is created). The pure plan layer still reserves the "
        f"slot: shipped_target={slot['plan_layer_slot']['shipped_target']}, "
        f"action={slot['plan_layer_slot']['plan_action_when_present']}, "
        f"backup={slot['plan_layer_slot']['backup_slot']}, "
        f"uninstall={slot['plan_layer_slot']['uninstall_action']}. "
        f"change_surface={len(slot['change_surface'])} files. "
        f"authority={slot['authority']}. Zero bytes written.",
        exit_code=EXIT_BATTLEMD_INPLACE_REFUSED,
        reason_code="BATTLEMD_INPLACE_REFUSED",
        report={"mode_reservations": MODE_RESERVATIONS,
                "mode_support": MODE_SUPPORT,
                "refused_mode": "battlemd:inplace"})


def run_resolve(feature_set: dict, sandbox_state: dict, *,
                guard_state: str | None = None) -> dict:
    """The ONE place where W42-S2 resolve() is invoked for a real write path.

    Returns a plan COPY with an added ``integration{}`` block (the read-only
    S2 schema is not modified).  Raises on: deferred mode (25), coupling
    refusal (26).
    """
    check_inplace_mode(feature_set)
    plan = dict(FS.resolve(feature_set, sandbox_state,
                           guard_state=guard_state))
    plan["integration"] = {
        "integration_id": INTEGRATION_ID,
        "schema_version": SCHEMA_VERSION,
        "mode_support": MODE_SUPPORT,
        "plan_layer_reservations": MODE_RESERVATIONS,
        "resolve_invoked_before_write": True,
        "guard_state_source": ("injected offline fixture; W38-S1 classify() "
                               "NOT invoked (guard stays --version-guard opt-in)"),
    }
    if not plan.get("coupling_passed", False):
        codes = list(plan.get("reason_codes", []))
        raise ResolveIntegrationRefused(
            "resolve() refused the feature-set BEFORE any write: "
            f"reason_codes={codes}; install_write_set=[]; "
            "effective_game_dir_write_bytes=0. Zero bytes written.",
            exit_code=EXIT_RESOLVE_COUPLING_REFUSED,
            reason_code="RESOLVE_COUPLING_REFUSED",
            plan=plan,
            report={"plan": plan, "reason_codes": codes})
    return plan


def write_resolve_plan_out(path, plan: dict, *, game_dir=None) -> None:
    """Persist the RAW plan early, so even a later refusal is auditable."""
    if path is None:
        return
    write_plan_report(path, {"phase": "resolve", "kind": "file_subset_plan",
                             "plan": plan}, game_dir=game_dir)


def build_resolve(feature_set, sandbox_state=None, *, guard_state=None,
                  resolve_plan_out=None) -> dict:
    f = load_json_obj(feature_set, "feature-set")
    s = (load_json_obj(sandbox_state, "sandbox-state")
         if sandbox_state is not None else default_build_sandbox_state(
             f, guard_state=guard_state))
    plan = run_resolve(f, s, guard_state=guard_state)
    write_resolve_plan_out(resolve_plan_out, plan)
    _check_guard_zero_write(plan, "build")
    return plan


def install_resolve(feature_set, sandbox_state, game, *, guard_state=None,
                    resolve_plan_out=None, plan_report=None) -> dict:
    game = Path(game)
    validate_report_paths(game, resolve_plan_out, plan_report)
    f = load_json_obj(feature_set, "feature-set")
    s = (load_json_obj(sandbox_state, "sandbox-state")
         if sandbox_state is not None else derive_install_sandbox_state(
             game, f, guard_state=guard_state))
    plan = run_resolve(f, s, guard_state=guard_state)
    write_resolve_plan_out(resolve_plan_out, plan, game_dir=game)
    _check_guard_zero_write(plan, "install")
    return plan


def _check_guard_zero_write(plan: dict, phase: str) -> None:
    """W42-S2 §6 C1/C3: feature-set NEVER changes guard_state; a non
    KNOWN_GOOD injected state means ZERO effective writes.  In the write path
    that is a refusal (the plan is preserved in the report as 'planned but
    denied')."""
    if plan.get("guard_state") == "KNOWN_GOOD":
        return
    raise ResolveIntegrationRefused(
        f"{phase}: injected guard_state={plan.get('guard_state')} is not "
        "KNOWN_GOOD => ALL_GAME_DIR_WRITES denied (W42-S2 §6 C3). The "
        "feature-set did NOT change the guard verdict; the plan is preserved "
        f"({len(plan.get('files', []))} rows, planned install_write_set="
        f"{plan.get('install_write_set')}) but zero bytes are written.",
        exit_code=EXIT_RESOLVE_GUARD_ZERO_WRITE,
        reason_code="RESOLVE_GUARD_ZERO_WRITE",
        plan=plan,
        report={"plan": plan, "phase": phase,
                "guard_state_unchanged_by_s2": True})


# ---------------------------------------------------------------------------
# package subset gate + per-file reconciliation
# ---------------------------------------------------------------------------

def filter_package_files(files: list, plan: dict) -> list:
    """G-7: the package's game-dir file subset MUST equal plan.shipped().

    A package member the plan marks LEAVE (or a plan CREATE/REPLACE with no
    package member) is a plan/actual mismatch => refuse BEFORE the first write.
    """
    got = {Path(p).name for p in files}
    want = set(plan.get("shipped", []))
    if got != want:
        raise ResolveIntegrationRefused(
            "PLAN_ACTUAL_MISMATCH at the package subset gate: package game-dir "
            f"members={sorted(got)} but plan.shipped()={sorted(want)}. "
            f"missing_from_package={sorted(want - got)} "
            f"unauthorised_by_plan={sorted(got - want)}. Zero bytes written.",
            exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
            reason_code="PLAN_ACTUAL_MISMATCH",
            plan=plan,
            report={"phase": "package_subset_gate", "package_members": sorted(got),
                    "plan_shipped": sorted(want)})
    return list(files)


def reconcile_install(plan: dict, steps: list, *, old_entries: dict,
                      allow_unchanged: bool, orphan_modes: dict | None = None,
                      second_install: dict | None = None) -> dict:
    """Per-file plan vs actual reconciliation for install (machine checkable).

    ``actual_action`` is v13's real step action (created / replaced /
    unchanged) or LEAVE_SKIPPED / MANIFEST_OR_SEAL_WRITE / REPLAY_NOOP.
    Every row carries an explicit ``consistent`` boolean; the verdict is MATCH
    only when all rows are consistent.
    """
    step_by = {s["name"]: s for s in steps}
    rows: list[dict] = []
    for r in plan.get("files", []):
        name, layer, pa = r["name"], r["layer"], r["action"]
        if layer == "game_dir_metadata":
            actual = "REPLAY_NOOP" if (second_install or {}).get("verdict") == \
                "IDEMPOTENT_REPLAY" else "MANIFEST_OR_SEAL_WRITE"
            consistent = pa in ("CREATE", "REPLACE")
            rows.append({
                "name": name, "layer": layer, "planned_action": pa,
                "actual_action": actual, "write_bytes": 0,
                "consistent": consistent,
                "note": "install record + seal written by install_package()",
            })
            continue
        step = step_by.get(name)
        if step is None:
            cleanup_mode = (orphan_modes or {}).get(name)
            if cleanup_mode:
                # G-8: a SUBSET_UPGRADE (subset SHRINK) retires a file the
                # PREVIOUS install record owned.  That is NOT a LEAVE of a
                # foreign file: it is v13 ORPHAN-FIX01 cleanup of OUR OWN
                # previous file, and the plan authorises it explicitly.
                actual = "ORPHAN_CLEANUP:" + cleanup_mode
                write_bytes = 0
                consistent = (pa == "LEAVE"
                              and (second_install or {}).get("verdict")
                              == "SUBSET_UPGRADE"
                              and cleanup_mode in ("remove", "remove_absent",
                                                   "restore", "missing"))
                note = ("planned orphan cleanup of a file the previous "
                        "install record owned (NOT an adoption of a foreign "
                        "file); W42-S2 §3.3 boundary 3 handed this to S3+")
            else:
                actual, write_bytes = "LEAVE_SKIPPED", 0
                consistent = (pa == "LEAVE")
                note = RECONCILIATION_RULES["LEAVE"]["note"]
        else:
            actual = step["action"]
            write_bytes = step["size"] if actual in ("created", "replaced") else 0
            allowed = list(RECONCILIATION_RULES.get(pa, {}).get("allowed", []))
            if pa == "REPLACE" and allow_unchanged:
                allowed = list(RECONCILIATION_RULES["REPLACE"][
                    "allowed_with_existing_record"])
            consistent = actual in allowed
            if actual == "unchanged" and name not in old_entries:
                # v13 would ADOPT an unregistered byte-identical file; the
                # plan's LEAVE discipline forbids it (W42-S2 §3.3 boundary 1).
                consistent = False
            note = (f"step action={actual}, original_absent="
                    f"{bool(step.get('original_absent'))}")
        rows.append({
            "name": name, "layer": layer, "planned_action": pa,
            "actual_action": actual, "write_bytes": write_bytes,
            "consistent": consistent, "note": note,
        })
    verdict = "MATCH" if all(x["consistent"] for x in rows) else "MISMATCH"
    planned_writes = sorted(r["name"] for r in rows
                            if r["layer"] == "game_dir"
                            and r["planned_action"] in ("CREATE", "REPLACE"))
    actual_writes = sorted(r["name"] for r in rows
                           if r["write_bytes"] > 0)
    return {
        "schema_version": SCHEMA_VERSION,
        "integration_id": INTEGRATION_ID,
        "phase": "install",
        "feature_set_id": plan.get("feature_set_id"),
        "plan_guard_state": plan.get("guard_state"),
        "verdict": verdict,
        "rows": rows,
        "planned_game_dir_write_set": planned_writes,
        "actual_game_dir_write_set": actual_writes,
        "effective_game_dir_write_bytes": sum(r["write_bytes"] for r in rows),
        "allow_unchanged": bool(allow_unchanged),
        "second_install": second_install or {},
        "orphan_cleanup": orphan_modes or {},
        "reconciliation_rules": RECONCILIATION_RULES,
    }


def compact_recon(recon: dict) -> dict:
    """The manifest-sized copy of the reconciliation (per-file rows kept)."""
    return {
        "schema_version": SCHEMA_VERSION,
        "integration_id": INTEGRATION_ID,
        "verdict": recon["verdict"],
        "feature_set_id": recon["feature_set_id"],
        "rows": recon["rows"],
        "planned_game_dir_write_set": recon["planned_game_dir_write_set"],
        "actual_game_dir_write_set": recon["actual_game_dir_write_set"],
        "effective_game_dir_write_bytes":
            recon["effective_game_dir_write_bytes"],
        "second_install": recon.get("second_install", {}).get("verdict"),
    }


# ---------------------------------------------------------------------------
# second install / orphan / legacy gates (all BEFORE the first write)
# ---------------------------------------------------------------------------

def classify_second_install(plan: dict, manifest: dict | None,
                            new_package_id: str) -> dict:
    if manifest is None:
        verdict = "FRESH"
    elif manifest.get("feature_set_id") is None:
        verdict = "LEGACY_PRE_PLAN"
    elif manifest.get("package_id") not in (None, "unknown", new_package_id):
        verdict = "DIFFERENT_PACKAGE"
    elif manifest.get("feature_set_id") != plan["feature_set_id"]:
        verdict = "SUBSET_UPGRADE"
    else:
        verdict = "IDEMPOTENT_REPLAY"
    return {
        "verdict": verdict,
        "rule": SECOND_INSTALL_SEMANTICS[verdict],
        "old_feature_set_id": (manifest or {}).get("feature_set_id"),
        "new_feature_set_id": plan.get("feature_set_id"),
        "old_package_id": (manifest or {}).get("package_id"),
        "new_package_id": new_package_id,
        "semantics_table": SECOND_INSTALL_SEMANTICS,
    }


def detect_plan_orphans(game: Path, plan: dict, manifest: dict | None,
                        steps: list) -> list[dict]:
    """G-8: an unrecorded OUR-LIKE file in the plan's game-dir universe.

    v13 would silently ADOPT a byte-identical unregistered file (and warn
    that a later uninstall WILL DELETE it).  Under --feature-set that is a
    refusal: the plan cannot account for a file the install record never
    owned.  Remedy: uninstall --legacy / remove it by hand, or adopt a
    Legacy record with --adopt-legacy.
    """
    game = Path(game)
    old = {e.get("name") for e in (manifest or {}).get("files", [])
           if isinstance(e, dict) and e.get("name")}
    pkg_sha = {}
    for s in steps:
        src = s.get("src")
        if src is not None:
            h = _sha_file(Path(src))
            if h:
                pkg_sha[Path(src).name] = h
    out: list[dict] = []
    for name in _universe_names_from_plan(plan):
        p = game / name
        if not p.is_file() or name in old:
            continue
        try:
            data = p.read_bytes()
        except OSError:
            continue
        why = None
        if name in pkg_sha and _sha(data) == pkg_sha[name]:
            why = "byte-identical to a package member (unrecorded 'ours')"
        elif FORGE_MARKER in data[:400]:
            why = "carries the ra2forge marker (unrecorded 'ours')"
        if why:
            out.append({"name": name, "why": why,
                        "sha256": _sha(data), "planned_action":
                        next((r["action"] for r in plan["files"]
                              if r["name"] == name), "UNKNOWN")})
    return out


def _universe_names_from_plan(plan: dict) -> list[str]:
    return [r["name"] for r in plan.get("files", [])
            if r["layer"] == "game_dir"]


def check_install_gates(feature_plan: dict, install_plan: dict, game: Path,
                        adopt_legacy: bool) -> None:
    """The ordered refusal gates for the opt-in install path.  Every one of
    them runs BEFORE the first filesystem write."""
    # 1. guard state zero-write (W42-S2 §6 C3)
    _check_guard_zero_write(feature_plan, "install")
    # 2. legacy / pre-plan record
    second = install_plan.get("second_install") or {}
    if second.get("verdict") == "LEGACY_PRE_PLAN" and not adopt_legacy:
        raise ResolveIntegrationRefused(
            "LEGACY_PLAN_RECONCILE_REQUIRED: the existing install record has "
            "NO feature_set_id (v13 or older, e.g. a W22 --adopt-legacy "
            "record) and cannot be reconciled against a resolve() plan. "
            "Re-run with --adopt-legacy to assert the successor relation, or "
            "uninstall the recorded package first. Zero bytes written.",
            exit_code=EXIT_LEGACY_PLAN_RECONCILE_REQUIRED,
            reason_code="LEGACY_PLAN_RECONCILE_REQUIRED",
            plan=feature_plan, report={"second_install": second})
    # 3. orphans
    orphans = install_plan.get("plan_orphans") or []
    if orphans:
        raise ResolveIntegrationRefused(
            "ORPHAN_PLAN_REFUSED: unrecorded ra2forge-like files on disk "
            f"({[o['name'] for o in orphans]}) cannot be reconciled against "
            "the plan; v13 would silently adopt them (and a later uninstall "
            "would delete them). Remove them / uninstall --legacy, or use "
            "--adopt-legacy for a legacy record. Zero bytes written.",
            exit_code=EXIT_ORPHAN_PLAN_REFUSED,
            reason_code="ORPHAN_PLAN_REFUSED",
            plan=feature_plan, report={"orphans": orphans})
    # 4. plan vs actual
    recon = install_plan.get("plan_reconciliation") or {}
    if recon.get("verdict") != "MATCH":
        bad = [r for r in recon.get("rows", []) if not r["consistent"]]
        raise ResolveIntegrationRefused(
            "PLAN_ACTUAL_MISMATCH: the write plan and the actual steps "
            f"disagree ({len(bad)} row(s)): "
            + json.dumps(bad, ensure_ascii=False)[:800]
            + ". Zero bytes written.",
            exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
            reason_code="PLAN_ACTUAL_MISMATCH",
            plan=feature_plan, report={"reconciliation": recon})


def snapshot_leave_files(game: Path, plan: dict,
                         orphan_modes: dict | None = None) -> dict:
    """Byte-level snapshot of every TRUE LEAVE row, taken BEFORE the first
    write.  Names retired by the previous record's orphan cleanup are NOT
    LEAVE rows (G-8), so they are excluded from this snapshot."""
    game = Path(game)
    cleanup = set((orphan_modes or {}).keys())
    return {r["name"]: _sha_file(game / r["name"])
            for r in plan.get("files", [])
            if r["layer"] == "game_dir" and r["action"] == "LEAVE"
            and r["name"] not in cleanup}


def check_post_write(plan: dict, entries: list, game: Path,
                     leave_before: dict, recon: dict) -> None:
    """Post-write reconciliation, BEFORE the manifest is committed.  A raise
    here is inside install_package()'s journaled try-block, so the existing
    rollback restores the pre-run bytes (best-effort)."""
    game = Path(game)
    for e in entries:
        p = game / e["name"]
        if not p.is_file() or _sha_file(p) != e.get("sha256"):
            raise OSError(
                "PLAN_ACTUAL_MISMATCH (post-write): " + str(e["name"])
                + " does not carry the bytes the plan recorded; install "
                  "record NOT written, rolling back")
    cleanup = set(recon.get("orphan_cleanup") or {})
    for name, before in leave_before.items():
        if name in cleanup:
            continue  # G-8: planned orphan cleanup, not a LEAVE row
        after = _sha_file(game / name)
        if after != before:
            raise OSError(
                f"PLAN_ACTUAL_MISMATCH (post-write): LEAVE file {name} was "
                "touched (strict zero-write violated); install record NOT "
                "written, rolling back")
    wrote = sorted(e["name"] for e in entries
                   if e.get("action") in ("created", "replaced"))
    if wrote != recon["actual_game_dir_write_set"]:
        raise OSError(
            "PLAN_ACTUAL_MISMATCH (post-write): actual write set "
            f"{wrote} != reconciled {recon['actual_game_dir_write_set']}; "
            "install record NOT written, rolling back")


# ---------------------------------------------------------------------------
# build: plan-driven optional artifact emission + reconciliation
# ---------------------------------------------------------------------------

def build_effective_switches(plan: dict, *, design_map_names: list[str],
                             csf_out, csf_base, mapselmd: bool,
                             mapselmd_base, raw_desc: str, out: Path) -> dict:
    """Derive the effective build switches FROM the plan, before any write.

    The G1 baseline (BATTLEMD98.INI + maps + expandmd98.mix) is emitted by the
    design-driven build; the plan must AUTHORISE it.  Optional artifacts
    (MAPSELMD.INI / ra2md.csf) are driven BY the plan: a plan CREATE turns
    them on even without the old switch, and the old switch without a plan
    CREATE is a mismatch (never a silent full package).
    """
    shipped = set(plan.get("shipped", []))
    baseline = {"BATTLEMD98.INI", "expandmd98.mix"} | set(design_map_names)
    if not baseline <= shipped:
        raise ResolveIntegrationRefused(
            "PLAN_ACTUAL_MISMATCH at the build subset gate: the design-driven "
            f"baseline {sorted(baseline)} is not fully authorised by "
            f"plan.shipped()={sorted(shipped)} "
            f"(unauthorised={sorted(baseline - shipped)}). A build cannot "
            "emit a game-dir file the plan marks LEAVE. Zero bytes written.",
            exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
            reason_code="PLAN_ACTUAL_MISMATCH", plan=plan,
            report={"phase": "build_subset_gate", "baseline": sorted(baseline),
                    "plan_shipped": sorted(shipped)})

    eff_mapselmd = bool(mapselmd)
    if "MAPSELMD.INI" in shipped:
        eff_mapselmd = True
    elif eff_mapselmd:
        raise ResolveIntegrationRefused(
            "PLAN_ACTUAL_MISMATCH: --mapselmd would emit MAPSELMD.INI but the "
            "plan marks it LEAVE. Zero bytes written.",
            exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
            reason_code="PLAN_ACTUAL_MISMATCH", plan=plan)
    if mapselmd_base is not None and not eff_mapselmd:
        raise ResolveIntegrationRefused(
            "PLAN_ACTUAL_MISMATCH: --mapselmd-base requires a plan that ships "
            "MAPSELMD.INI. Zero bytes written.",
            exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
            reason_code="PLAN_ACTUAL_MISMATCH", plan=plan)

    eff_csf_out = csf_out
    if "ra2md.csf" in shipped:
        if not raw_desc:
            raise ResolveIntegrationRefused(
                "PLAN_ACTUAL_MISMATCH: the plan ships ra2md.csf but the "
                "design has an empty campaign.description, so no CSF label "
                "(and no complete CSF) can be emitted. Zero bytes written.",
                exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
                reason_code="PLAN_ACTUAL_MISMATCH", plan=plan)
        if eff_csf_out is None:
            eff_csf_out = str(Path(out) / "ra2md.csf")
    else:
        if eff_csf_out is not None:
            raise ResolveIntegrationRefused(
                "PLAN_ACTUAL_MISMATCH: --csf-out would emit ra2md.csf but the "
                "plan marks it LEAVE. Zero bytes written.",
                exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
                reason_code="PLAN_ACTUAL_MISMATCH", plan=plan)
        if csf_base is not None:
            raise ResolveIntegrationRefused(
                "PLAN_ACTUAL_MISMATCH: --csf-base requires a plan that ships "
                "ra2md.csf. Zero bytes written.",
                exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
                reason_code="PLAN_ACTUAL_MISMATCH", plan=plan)
    return {
        "csf_out": eff_csf_out,
        "mapselmd": eff_mapselmd,
        "plan_driven": {
            "MAPSELMD.INI": "MAPSELMD.INI" in shipped and not mapselmd,
            "ra2md.csf": "ra2md.csf" in shipped and csf_out is None,
        },
        "plan_shipped": sorted(shipped),
    }


def build_reconcile(plan: dict, out: Path, *, plan_report=None) -> dict:
    """Per-file plan vs actually-emitted reconciliation for build."""
    out = Path(out)
    emitted = {p.name for p in out.iterdir() if p.is_file()}
    rows: list[dict] = []
    for r in plan.get("files", []):
        name, layer, pa = r["name"], r["layer"], r["action"]
        if layer == "game_dir_metadata":
            rows.append({
                "name": name, "layer": layer, "planned_action": pa,
                "actually_emitted": False, "consistent": True,
                "handled_by": "install (manifest/seal, not a build artifact)",
            })
            continue
        e = name in emitted
        want = pa in ("CREATE", "REPLACE")
        rows.append({
            "name": name, "layer": layer, "planned_action": pa,
            "actually_emitted": e, "consistent": (e == want),
            "note": ("emitted into package dir" if e else
                     "not emitted (plan LEAVE)"),
        })
    game_names = set(_universe_names_from_plan(plan))
    emitted_game = sorted(emitted & game_names)
    verdict = ("MATCH" if all(x["consistent"] for x in rows)
               and emitted_game == sorted(plan.get("shipped", []))
               else "MISMATCH")
    report = {
        "schema_version": SCHEMA_VERSION,
        "integration_id": INTEGRATION_ID,
        "phase": "build",
        "feature_set_id": plan.get("feature_set_id"),
        "verdict": verdict,
        "rows": rows,
        "plan_shipped": sorted(plan.get("shipped", [])),
        "actually_emitted_game_dir_files": emitted_game,
        "plan_guard_state": plan.get("guard_state"),
        "resolve_invoked_before_write": True,
    }
    if verdict == "MATCH":
        (out / "ra2forge_plan_reconciliation.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False,
                       default=str) + "\n", encoding="utf-8")
    if plan_report is not None:
        write_plan_report(plan_report, report)
    if verdict != "MATCH":
        bad = [r for r in rows if not r["consistent"]]
        raise ResolveIntegrationRefused(
            "PLAN_ACTUAL_MISMATCH (build): emitted game-dir subset "
            f"{emitted_game} != plan.shipped()={sorted(plan.get('shipped', []))}; "
            f"inconsistent rows={bad}",
            exit_code=EXIT_PLAN_ACTUAL_MISMATCH,
            reason_code="PLAN_ACTUAL_MISMATCH", plan=plan, report=report)
    return report


# ---------------------------------------------------------------------------
# report writer (W38-S1 A7 spirit: reports never land inside the game dir)
# ---------------------------------------------------------------------------

def write_plan_report(path, payload: dict, *, game_dir=None) -> None:
    p = Path(path).resolve()
    if game_dir is not None:
        gd = Path(game_dir).resolve()
        try:
            common = os.path.commonpath([str(p), str(gd)])
        except ValueError:
            common = None
        if common == str(gd):
            raise ResolveIntegrationRefused(
                f"plan report path {p} resolves INSIDE the game directory "
                f"{gd} (W38-S1 §1.2 / ACCEPTANCE A7 path attribution); "
                "refusing to write an untracked artefact there",
                exit_code=EXIT_PLAN_REPORT_INSIDE_GAME_DIR,
                reason_code="PLAN_REPORT_INSIDE_GAME_DIR",
                report=payload)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2, ensure_ascii=False,
                            default=str) + "\n", encoding="utf-8")


def validate_report_paths(game: Path, *paths) -> None:
    """W38-S1 A7 spirit, applied BEFORE the first write: no W46/S4 report may
    ever land inside the game directory (that would be an untracked write)."""
    gd = Path(game).resolve()
    for raw in paths:
        if raw is None:
            continue
        p = Path(raw).resolve()
        try:
            common = os.path.commonpath([str(p), str(gd)])
        except ValueError:
            common = None
        if common == str(gd):
            raise ResolveIntegrationRefused(
                f"W46/S4 report path {p} resolves INSIDE the game directory "
                f"{gd}; refusing BEFORE any write (W38-S1 §1.2 / A7). "
                "Zero bytes written.",
                exit_code=EXIT_PLAN_REPORT_INSIDE_GAME_DIR,
                reason_code="PLAN_REPORT_INSIDE_GAME_DIR",
                report={"offending_path": str(p), "game_dir": str(gd)})
