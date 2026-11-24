"""W43 / S3 -- W42-S2 ``resolve()``: feature-set -> deterministic file subset.

This is the FIRST implementation of the S2 contract.  It is a PURE function:
no filesystem writes, no game process, no imports of install/builder.  It is
reachable only through the new ``resolve`` CLI subcommand or a direct import;
the legacy build/install/uninstall paths never touch it, so with no new
switch the produced artifacts stay byte-for-byte identical to v12.

Output shape
------------
``resolve()`` returns a SUPERSET of W42's ``$defs/fileSubsetPlan``.  S3 adds
``warnings[]`` (required by Lead verdict D3 but absent from the S2 schema),
``install_summary[]``, ``reason_codes[]``, ``manifest{}`` and a few derived
fields.  The S2 schema is READ-ONLY upstream and is NOT modified; the
extension is registered in DISAGREE.md D-W43-4.  All S2-required fields keep
their exact names/types.

Grading: [本次读码] for the v11/v12 semantics, [静态推断] for the resolver
rules, [转引] for the 5211 / 5573 / 074ccccd constants.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import s3_contract as C

__all__ = ["resolve", "shipped", "validate_g4", "build_plan_from_files"]


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _mode(features: dict, name: str) -> object:
    return features.get(name, {}).get("mode", "off")


def shipped(feature_set: dict) -> list[str]:
    """W42-S2 §3.2 shipped(F) -- pure function, no ambiguity."""
    f = feature_set["features"]
    out: list[str] = []
    if _mode(f, "maps") == "sideload":
        out.extend(f["maps"].get("map_files", []))
    bm = _mode(f, "battlemd")
    if bm == "append":
        out.append("BATTLEMD98.INI")
    elif bm == "inplace":
        out.append("BATTLEMD.INI")
    if _mode(f, "mix") == "repack":
        out.append("expandmd98.mix")
    if _mode(f, "csf") == "clone_append":
        out.append("ra2md.csf")
    if _mode(f, "mapselmd") == "clone_append":
        out.append("MAPSELMD.INI")
    return sorted(set(out))


def _owner(name: str, features: dict) -> str:
    """Which of the 5 features owns this FILE_UNIVERSE row."""
    if name == "BATTLEMD98.INI" or name == "BATTLEMD.INI":
        return "battlemd"
    if name.upper().endswith(".MAP"):
        return "maps"
    if name == "expandmd98.mix":
        return "mix"
    if name == "ra2md.csf":
        return "csf"
    if name == "MAPSELMD.INI":
        return "mapselmd"
    # metadata rows are not owned by any feature; the S2 plannedFile schema
    # requires produced_by_feature to be one of the 5 names, so we use the
    # deterministic sentinel "maps" and document the shaping in DISAGREE.md.
    return "maps"


def _universe(feature_set: dict) -> list[str]:
    f = feature_set["features"]
    fixed = ["BATTLEMD98.INI", "BATTLEMD.INI", "expandmd98.mix",
             "ra2md.csf", "MAPSELMD.INI"]
    maps = sorted(f["maps"].get("map_files", [])) \
        if _mode(f, "maps") == "sideload" else []
    return fixed + maps + list(C.FILE_UNIVERSE_META)


def _violation(rule_id: str, code: str, detail: str) -> dict:
    return {"rule_id": rule_id, "reason_code": code, "detail": detail}


def _check_coupling(feature_set: dict, *, csf_out_inside_game_dir: bool,
                    shipped_names: list[str]) -> tuple[list[dict], list[str]]:
    """W42-S2 §5 K1-K12. Returns (violations, deferred_reason_codes)."""
    f = feature_set["features"]
    v: list[dict] = []
    deferred: list[str] = []

    # K1 -- battlemd.mode must be a single value.
    bm = f["battlemd"].get("mode", "off")
    if isinstance(bm, list):
        v.append(_violation("K1", "BATTLEMD_MODE_CONFLICT",
                            "battlemd.mode is an array " + json.dumps(bm) +
                            "; append and inplace are mutually exclusive, a "
                            "single value in {off,append,inplace} is required."))
    bm_single = bm if isinstance(bm, str) else "off"
    csf_on = _mode(f, "csf") == "clone_append"
    bm_off = bm_single == "off"
    desc_ref = f["battlemd"].get("description_ref")

    # K2 / K3 -- CSF <-> BATTLEMD98.INI (STRONG pair, kept as hard refusal).
    if csf_on:
        if bm_off:
            v.append(_violation("K2", "CSF_WITHOUT_BATTLEMD",
                                "csf.mode=clone_append but battlemd.mode=off. "
                                "W36 §3.3.2: BATTLEMD98.INI x ra2md.csf is a "
                                "STRONG pair; the RA2F label in Description= "
                                "would otherwise be MISSING:RA2F:... (W30)."))
        elif desc_ref != "csf_label":
            v.append(_violation("K2", "CSF_LABEL_UNBOUND",
                                "csf.mode=clone_append requires "
                                "battlemd.description_ref=csf_label; got "
                                f"{desc_ref!r}. builder.py:131-137."))
        labels = f["csf"].get("labels", [])
        if not any(isinstance(x, str) and x.startswith("RA2F:") for x in labels):
            v.append(_violation("K2", "CSF_LABEL_UNBOUND",
                                "no RA2F:<8hex> label in csf.labels[]."))
    if desc_ref == "csf_label" and not csf_on:
        v.append(_violation("K3", "CSF_LABEL_UNBOUND",
                            "battlemd.description_ref=csf_label but "
                            "csf.mode is not clone_append; the bound label "
                            "would be unresolvable (W30 G-4 gap)."))

    # K4 -- csf completeness / integrity gate (S2 B8, Lead D1/D2).
    if csf_on:
        c = f["csf"]
        base = c.get("base")
        full_min = int(c.get("official_full_min", C.CSF_OFFICIAL_FULL_MIN))
        observed = int(c.get("official_label_count", 0))
        if base != "official_full_clone" or observed < full_min:
            v.append(_violation(
                "K4", "MINIMAL_CSF_REFUSED",
                f"MINIMAL_CSF_REFUSED: base={base!r} (MUST be "
                f"'official_full_clone'), official_label_count={observed} < "
                f"official_full_min={full_min} (a COMPLETE official clone has "
                f">= {full_min} official labels). " + C.CSF_INTEGRITY_GATE_REASON))

    # K5 -- MAPSELMD full-clone gate (S2 B9).
    if _mode(f, "mapselmd") == "clone_append":
        m = f["mapselmd"]
        problems = []
        if m.get("base") != "official_full_clone":
            problems.append(f"base={m.get('base')!r} != official_full_clone")
        if int(m.get("official_stage_count", 0)) != C.MAPSELMD_OFFICIAL_STAGE_COUNT:
            problems.append("official_stage_count != 14 official stages")
        if int(m.get("official_size_bytes", 0)) != C.MAPSELMD_OFFICIAL_SIZE_BYTES:
            problems.append("official_size_bytes != 5573 B")
        if m.get("bundled_official_sha256") != C.MAPSELMD_BUNDLED_OFFICIAL_SHA256:
            problems.append("bundled_official_sha256 != 074ccccd...")
        if problems:
            v.append(_violation(
                "K5", "MAPSELMD_NOT_FULL_CLONE",
                "MAPSELMD_NOT_FULL_CLONE: " + "; ".join(problems) +
                ". A complete official MAPSELMD.INI needs all 14 official "
                "sections, faction keys 1..7, Scenario= lines, 5573 B and "
                "bundled SHA " + C.MAPSELMD_BUNDLED_OFFICIAL_SHA256 +
                " (W34 D4, mapselmd.py:142-184)."))

    maps_on = _mode(f, "maps") == "sideload"
    mix_on = _mode(f, "mix") == "repack"
    maps_files = list(f["maps"].get("map_files", []))
    # K6 / K7 / K8 -- *.MAP <-> expandmd98.mix (STRONG pair).
    if maps_on and not mix_on:
        v.append(_violation("K6", "MAPS_WITHOUT_MIX",
                            "maps=sideload but mix=off; builder.py:143-147 "
                            "_verify_mix_contents requires exactly the maps "
                            "and 0 INI in expandmd98.mix."))
    if mix_on and not maps_on:
        v.append(_violation("K7", "MIX_WITHOUT_MAPS",
                            "mix=repack but maps=off; nothing to repack."))
    if mix_on and maps_on:
        src = list(f["mix"].get("source_map_set", []))
        if src != maps_files:
            v.append(_violation("K8", "MIX_MAP_SET_MISMATCH",
                                "mix.source_map_set=" + json.dumps(src) +
                                " != maps.map_files=" + json.dumps(maps_files)))
    # K9 / K10 -- *.MAP <-> MAPSELMD.INI (STRONG pair).
    msel_on = _mode(f, "mapselmd") == "clone_append"
    if msel_on and not maps_on:
        v.append(_violation("K9", "MAPSELMD_WITHOUT_MAPS",
                            "mapselmd=clone_append but maps=off; "
                            "W36 §3.3.2 *.MAP x MAPSELMD.INI is a STRONG pair."))
    if msel_on and maps_on:
        unresolved = []
        for st in f["mapselmd"].get("stages", []):
            scen = None
            if isinstance(st, dict):
                scen = st.get("Scenario") or st.get("scenario")
            elif isinstance(st, str) and "Scenario=" in st:
                scen = st.split("Scenario=", 1)[1].strip()
            elif isinstance(st, str) and st.upper().endswith(".MAP"):
                scen = st
            if scen and scen.upper().endswith(".MAP") and scen not in maps_files:
                unresolved.append(scen)
        if unresolved:
            v.append(_violation("K10", "MAPSELMD_SCENARIO_UNRESOLVED",
                                "unresolved stages[].Scenario=" +
                                json.dumps(unresolved) +
                                " not in maps.map_files=" + json.dumps(maps_files) +
                                " (W34 MAPSELMD_SPEC.md:150-158)."))

    # K12 -- csf-out inside a game dir is DEFERRED to S1 as E1 (B15).
    # W42 §4.3 / §6 C5: "K12 只做交给 S1，不自行放行".  We therefore emit
    # the reason code as a DEFERRED code, not a coupling violation: the plan
    # is still produced and guard_state decides allow/deny.  See DISAGREE D-W43-5.
    if csf_out_inside_game_dir:
        deferred.append("CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1")

    return v, deferred


def build_plan_from_files(files: list[dict]) -> dict:
    """W42-S2 §4.2: derive the four sets FROM files[] (never hand-filled)."""
    iws = [r["name"] for r in files if r["action"] in ("CREATE", "REPLACE")]
    backup = [r["backup_slot"] for r in files
              if r["action"] == "REPLACE" and r.get("backup_slot")]
    dele = [r["name"] for r in files if r["uninstall"]["action"] == "DELETE"]
    restore = [r["name"] for r in files if r["uninstall"]["action"] == "RESTORE"]
    return {"install_write_set": sorted(iws), "backup_set": sorted(backup),
            "uninstall_delete_set": sorted(dele),
            "uninstall_restore_set": sorted(restore)}


def _row(name: str, layer: str, action: str, feature_set_id: str,
         *, write_entry: str = "E1") -> dict:
    original_absent = (action == "CREATE")
    if action == "CREATE":
        uninstall = {"action": "DELETE", "remove_backup_slot": False,
                     "restore_from": None}
        backup_slot = None
    elif action == "REPLACE":
        backup_slot = name + C.BACKUP_SUFFIX
        uninstall = {"action": "RESTORE", "remove_backup_slot": True,
                     "restore_from": backup_slot}
    else:
        backup_slot = None
        uninstall = {"action": "NOOP", "remove_backup_slot": False,
                     "restore_from": None}
    return {
        "name": name,
        "layer": layer,
        "action": action,
        "original_absent": original_absent,
        "backup_slot": backup_slot,
        "produced_by_feature": _owner(name, {}),
        "write_entry": write_entry,
        "uninstall": uninstall,
    }


def validate_g4(plan: dict) -> list[dict]:
    """W42-S2 §7 / B16: every set must be derived from files[] and the
    feature_set_id must be in the manifest.  Returns K11 violations."""
    v = []
    derived = build_plan_from_files(plan.get("files", []))
    for key in ("install_write_set", "backup_set",
                "uninstall_delete_set", "uninstall_restore_set"):
        if sorted(plan.get(key, [])) != derived[key]:
            v.append(_violation(
                "K11", "G4_METADATA_DESYNC",
                f"{key} is not derived from files[]: got "
                f"{sorted(plan.get(key, []))} expected {derived[key]}."))
    if not plan.get("coupling_passed", True):
        return v
    if plan.get("manifest", {}).get("feature_set_id") != plan.get("feature_set_id"):
        v.append(_violation("K11", "G4_METADATA_DESYNC",
                            "feature_set_id missing from manifest; two "
                            "different subsets could produce the same digest."))
    if plan.get("coupling_passed", True):
        if plan.get("digest_inputs") and not plan.get("manifest", {}).get("package_digest"):
            v.append(_violation("K11", "G4_METADATA_DESYNC",
                                "digest_inputs present but manifest.package_digest absent."))
    return v


def resolve(feature_set: dict, sandbox_initial_state: dict, *,
            guard_state: str | None = None,
            csf_out_inside_game_dir: bool = False) -> dict:
    """W42-S2 §3/§5/§6/§7 ``resolve(F, S)`` -- PURE, deterministic.

    ``guard_state`` is an INJECTED fixture value (ACCEPTANCE_S2 §0); when
    omitted the sandbox_initial_state.guard_state is used.  A feature-set
    NEVER changes guard_state (§6 C1).  Under UNKNOWN/MISMATCH/DIR_INVALID
    the plan is preserved but ALL effective writes are zero (§6 C3).
    """
    fsid = feature_set["feature_set_id"]
    state = guard_state or sandbox_initial_state.get("guard_state", "KNOWN_GOOD")
    sid = sandbox_initial_state.get("sandbox_id", "S0")
    present = {p["name"] for p in sandbox_initial_state.get("present_files", [])}
    sh = shipped(feature_set)
    has_shipped = bool(sh)

    violations, deferred = _check_coupling(
        feature_set, csf_out_inside_game_dir=csf_out_inside_game_dir,
        shipped_names=sh)
    coupling_passed = not violations

    files: list[dict] = []
    for name in _universe(feature_set):
        if name in C.FILE_UNIVERSE_META:
            layer = "game_dir_metadata"
            action = "CREATE" if has_shipped and coupling_passed else "LEAVE"
        elif name in sh and name in present:
            layer = "game_dir"
            action = "REPLACE" if coupling_passed else "LEAVE"
        elif name in sh:
            layer = "game_dir"
            action = "CREATE" if coupling_passed else "LEAVE"
        else:
            layer = "game_dir"
            action = "LEAVE"
        row = _row(name, layer, action, fsid)
        row["produced_by_feature"] = _owner(name, feature_set["features"])
        files.append(row)

    # D3 / K12 + B15: the external csf-out write point is reclassified E1.
    if csf_out_inside_game_dir:
        files.append({
            "name": "ra2md.csf (csf_out_path)",
            "layer": "external_csf_out",
            "action": "LEAVE",           # no write authorised by S2 itself
            "original_absent": False,
            "backup_slot": None,
            "produced_by_feature": "csf",
            "write_entry": "E1",
            "uninstall": {"action": "NOOP", "remove_backup_slot": False,
                          "restore_from": None},
        })

    # --- digest_inputs: one deterministic line per SHIPPED file -------------
    # §3.4: a coupling refusal returns NO file plan at all (zero writes).
    digest_inputs = []
    if coupling_passed:
        for name in sh:
            digest_inputs.append(f"{name} {_sha(fsid + '|' + name + '|' + state)}")
        digest_inputs.sort()
    package_digest = _sha("\n".join(digest_inputs) + "|" + fsid) \
        if digest_inputs else ""

    sets = build_plan_from_files(files)
    manifest = {
        "entries": sorted(sets["install_write_set"]),
        "original_absent": [r["name"] for r in files
                            if r["original_absent"]],
        "removed_orphans": [],
        "package_digest": package_digest,
        "feature_set_id": fsid,
    }
    effective = (state == "KNOWN_GOOD") and coupling_passed
    effective_iws = sets["install_write_set"] if effective else []
    effective_bytes = sum(len(name) + 64 for name in
                          sets["install_write_set"]) if effective else 0

    reason_codes = [x["reason_code"] for x in violations] + list(deferred)

    warnings: list[dict] = []
    # --- D3: G3 "medium" edge warning, NEVER a hard refusal ---------------
    f = feature_set["features"]
    g3 = (_mode(f, "csf") == "clone_append"
          and _mode(f, "mapselmd") == "clone_append"
          and "BATTLEMD98.INI" not in sh)
    if g3:
        warnings.append({
            "code": C.G3_WARNING_CODE,
            "severity": "warning",
            "machine_checkable": True,
            "hard_reject": False,
            "features": ["csf", "mapselmd"],
            "missing_file": "BATTLEMD98.INI",
            "message": C.G3_WARNING_TEXT,
            "verdict": "Lead D3: warning + explicit confirmation, NO hard refusal.",
        })

    install_summary = [
        f"feature_set_id={fsid}",
        f"guard_state={state}",
        f"coupling_passed={coupling_passed}",
        f"planned_install_write_set={sets['install_write_set']}",
        f"effective_install_write_set={effective_iws}",
        f"effective_game_dir_write_bytes={effective_bytes}",
    ]
    for w in warnings:
        install_summary.append(f"[WARNING] {w['code']}: {w['message']}")
    if deferred:
        install_summary.append("[DEFER-TO-S1] " + ", ".join(deferred)
                               + ": write point reclassified to E1, "
                                 "allow/deny decided by W38-S1 classify().")

    plan = {
        "schema_version": "w42-s2-1",
        "kind": "file_subset_plan",
        "feature_set_id": fsid,
        "guard_state": state,
        "sandbox_id": sid,
        "coupling_passed": coupling_passed,
        "coupling_violations": violations,
        "files": files,
        **sets,
        "digest_inputs": digest_inputs,
        "wrote_game_dir": bool(effective and effective_iws),
        "effective_game_dir_write_bytes": effective_bytes,
        "guard_report_written_to": "<S3 write domain>",
        # ---- S3 extension (not in the read-only S2 schema) ---------------
        "reason_codes": reason_codes,
        "deferred_to_s1_reason_codes": deferred,
        "warnings": warnings,
        "install_summary": install_summary,
        "manifest": manifest,
        "effective_install_write_set": effective_iws,
        "shipped": sh,
        "guard_state_unchanged_by_s2": True,
        "g3_mid_coupling_triggered": g3,
        "detour_classification": C.DETOUR_CLASSIFICATION_DEFAULT,
    }
    # K11 / G4 self-consistency check (B16).
    g4 = validate_g4(plan)
    if g4:
        plan["coupling_violations"].extend(g4)
        plan["reason_codes"].extend(x["reason_code"] for x in g4)
        plan["coupling_passed"] = False
        plan["install_write_set"] = []
        plan["effective_install_write_set"] = []
        plan["effective_game_dir_write_bytes"] = 0
        plan["digest_inputs"] = []
        plan["wrote_game_dir"] = False
    return plan


def load_json(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))
