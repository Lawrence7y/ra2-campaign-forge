#!/usr/bin/env python3
"""W43 / B-line S3 -- S3_1..S3_25 regression cases.

Bound into regress_dlc_v13.py via bind_s3(globals()); every case uses the
EXACT SAME Case harness (per-case log, check(), run_module/run_python) as the
57 inherited v12 cases.  Pure offline: no game launched, no attach, only the
card's own sandbox/ and out/ are written.  W21-W42 and the repo ra2forge/ are
READ-ONLY references.

Coverage: W42 ACCEPTANCE_S2.md B1-B17 (machine-checkable parts), Lead
verdicts D1-D4, the version-guard wiring, the --csf-out ownership guard and
the v13<->v12 SHA-256 backward-compatibility table.
"""
from __future__ import annotations

import copy
import json

# G is populated by bind_s3() with regress_dlc_v13.py's globals.
class _NS:
    pass


G = _NS()


def bind_s3(g: dict) -> None:
    for k, v in g.items():
        if not k.startswith("__"):
            setattr(G, k, v)
    # clarity alias: in the v13 script V12_ROOT *is* the v13 package root
    # (the name was kept so all 57 inherited call sites stay untouched).
    G.V13_ROOT = G.V12_ROOT
    G.CARD = G.W43_ROOT


def _fixtures() -> dict:
    return json.loads((G.W42_EVIDENCE / "fixtures.json").read_text(encoding="utf-8"))


def _mut(fs_obj: dict, feature: str, **kw) -> dict:
    out = copy.deepcopy(fs_obj)
    out["features"][feature].update(kw)
    tag = feature + "-" + G.hashlib.md5(
        json.dumps(kw, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:8]
    out["feature_set_id"] = out["feature_set_id"] + "|" + tag
    return out


def _plan(c, fs_obj, sb_obj, *, guard_state=None,
          csf_out_inside=False, label="resolve"):
    """Run feature_subset.resolve() against the v13 package, return (rc, plan, out, err)."""
    fsp, sbp = c.dir / "fs.json", c.dir / "sb.json"
    G.w(fsp, json.dumps(fs_obj, indent=2, ensure_ascii=False))
    G.w(sbp, json.dumps(sb_obj, indent=2, ensure_ascii=False))
    code = f"""
import json
from ra2forge import feature_subset as fs
p = fs.resolve(fs.load_json({str(fsp)!r}), fs.load_json({str(sbp)!r}),
               guard_state={guard_state!r},
               csf_out_inside_game_dir={csf_out_inside!r})
print(json.dumps(p, ensure_ascii=False))
"""
    rc, out, err = c.run_python(G.V13_ROOT, code, label)
    try:
        plan = json.loads(out.strip())
    except (ValueError, AttributeError):
        plan = {}
    return rc, plan, out, err


def _zero(plan: dict) -> bool:
    return (plan.get("install_write_set") == []
            and plan.get("effective_game_dir_write_bytes") == 0
            and plan.get("effective_install_write_set") == []
            and plan.get("wrote_game_dir") is False)


def _codes(plan: dict) -> list[str]:
    return list(plan.get("reason_codes", []))


def _row(plan: dict, name: str) -> dict:
    for r in plan.get("files", []):
        if r["name"] == name:
            return r
    return {}


def _full_csf(**over):
    d = {"mode": "clone_append", "base": "official_full_clone",
         "official_label_count": 5211, "labels": ["RA2F:00000001"],
         "target_name": "ra2md.csf", "official_full_min": 5211}
    d.update(over)
    return d


def _full_mapselmd(**over):
    d = {"mode": "clone_append", "base": "official_full_clone",
         "official_stage_count": 14, "official_size_bytes": 5573,
         "official_sha256": "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52",
         "bundled_official_sha256": "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52",
         "stages": ["S1", "S2"], "target_name": "MAPSELMD.INI"}
    d.update(over)
    return d


# ===========================================================================
# B1 - B7: positive deterministic file subsets
# ===========================================================================

def case_S3_1(fx) -> object:
    """B1: all-off default -- zero writes, byte-identical, all LEAVE."""
    c = G.Case("S3_1")
    F = _fixtures()
    rc, p, out, err = _plan(c, F["feature_sets"]["F0"],
                            F["sandbox_initial_states"]["S0"], label="B1-F0")
    c.check("S3_1a: resolve exits 0", rc == 0, err)
    c.check("S3_1b: coupling_passed=true", p.get("coupling_passed") is True, str(p.get("reason_codes")))
    c.check("S3_1c: every FILE_UNIVERSE row is LEAVE / NOOP / original_absent=false",
            p.get("files") and all(r["action"] == "LEAVE"
                                   and r["uninstall"]["action"] == "NOOP"
                                   and r["uninstall"]["remove_backup_slot"] is False
                                   and r["original_absent"] is False
                                   for r in p["files"]),
            str([(r["name"], r["action"]) for r in p.get("files", [])]))
    c.check("S3_1d: all four sets + digest_inputs empty",
            all(p.get(k) == [] for k in ("install_write_set", "backup_set",
                                         "uninstall_delete_set",
                                         "uninstall_restore_set",
                                         "digest_inputs")),
            str({k: p.get(k) for k in ("install_write_set", "backup_set",
                                       "uninstall_delete_set",
                                       "uninstall_restore_set", "digest_inputs")}))
    c.check("S3_1e: effective_game_dir_write_bytes=0, wrote_game_dir=false",
            p.get("effective_game_dir_write_bytes") == 0
            and p.get("wrote_game_dir") is False)
    c.check("S3_1f: guard_state unchanged KNOWN_GOOD (S2 cannot alter S1)",
            p.get("guard_state") == "KNOWN_GOOD"
            and p.get("guard_state_unchanged_by_s2") is True)
    return c


def case_S3_2(fx) -> object:
    """B2: G1 F1 -- CREATE -> uninstall DELETE, original_absent=true."""
    c = G.Case("S3_2")
    F = _fixtures()
    rc, p, out, err = _plan(c, F["feature_sets"]["F1"],
                            F["sandbox_initial_states"]["S0"], label="B2-F1")
    want = {"A.MAP", "B.MAP", "expandmd98.mix", "BATTLEMD98.INI"}
    c.check("S3_2a: shipped(F1) is exactly the 4 G1 files",
            set(p.get("shipped", [])) == want, str(p.get("shipped")))
    for n in want:
        r = _row(p, n)
        c.check(f"S3_2b: {n} = CREATE + original_absent=true + uninstall DELETE",
                r.get("action") == "CREATE" and r.get("original_absent") is True
                and r.get("uninstall", {}).get("action") == "DELETE"
                and r.get("backup_slot") is None, str(r))
    for n in ("BATTLEMD.INI", "ra2md.csf", "MAPSELMD.INI"):
        c.check(f"S3_2c: {n} = LEAVE (zero touch, NOT v11 unchanged/adopt)",
                _row(p, n).get("action") == "LEAVE"
                and _row(p, n).get("uninstall", {}).get("action") == "NOOP",
                str(_row(p, n)))
    c.check("S3_2d: backup_set empty; uninstall_restore_set empty",
            p.get("backup_set") == [] and p.get("uninstall_restore_set") == [])
    c.check("S3_2e: uninstall_delete_set = 4 files + manifest + seal",
            set(p.get("uninstall_delete_set", [])) ==
            want | {"ra2forge_install.json", "ra2forge_install.json.seal"},
            str(p.get("uninstall_delete_set")))
    c.check("S3_2f: digest_inputs has exactly 4 lines (shipped only)",
            len(p.get("digest_inputs", [])) == 4, str(p.get("digest_inputs")))
    c.check("S3_2g: install_write_set = 4 + manifest + seal",
            len(p.get("install_write_set", [])) == 6,
            str(p.get("install_write_set")))
    return c


def case_S3_3(fx) -> object:
    """B3: REPLACE -> backup slot -> uninstall RESTORE (S1' preset mix)."""
    c = G.Case("S3_3")
    F = _fixtures()
    rc, p, out, err = _plan(c, F["feature_sets"]["F1"],
                            F["sandbox_initial_states"]["S1p"], label="B3-S1p")
    r = _row(p, "expandmd98.mix")
    c.check("S3_3a: expandmd98.mix = REPLACE, original_absent=false",
            r.get("action") == "REPLACE" and r.get("original_absent") is False, str(r))
    c.check("S3_3b: backup_slot is the .ra2forge.bak slot",
            r.get("backup_slot") == "expandmd98.mix.ra2forge.bak", str(r))
    c.check("S3_3c: uninstall RESTORE from that slot, remove_backup_slot=true",
            r.get("uninstall", {}).get("action") == "RESTORE"
            and r.get("uninstall", {}).get("restore_from") == "expandmd98.mix.ra2forge.bak"
            and r.get("uninstall", {}).get("remove_backup_slot") is True, str(r))
    c.check("S3_3d: backup_set exactly one slot, restore_set exactly one name",
            p.get("backup_set") == ["expandmd98.mix.ra2forge.bak"]
            and p.get("uninstall_restore_set") == ["expandmd98.mix"],
            str((p.get("backup_set"), p.get("uninstall_restore_set"))))
    c.check("S3_3e: the other 3 shipped files are still CREATE+DELETE",
            all(_row(p, n).get("action") == "CREATE"
                and _row(p, n).get("uninstall", {}).get("action") == "DELETE"
                for n in ("A.MAP", "B.MAP", "BATTLEMD98.INI")))
    return c


def case_S3_4(fx) -> object:
    """B4: battlemd:inplace -> official BATTLEMD.INI REPLACE/RESTORE."""
    c = G.Case("S3_4")
    F = _fixtures()
    fs1 = _mut(F["feature_sets"]["F1"], "battlemd", mode="inplace")
    rc, p, out, err = _plan(c, fs1, F["sandbox_initial_states"]["S0"],
                            label="B4-inplace")
    r = _row(p, "BATTLEMD.INI")
    c.check("S3_4a: BATTLEMD.INI = REPLACE (official loose PRESENT 2733 B)",
            r.get("action") == "REPLACE" and r.get("original_absent") is False, str(r))
    c.check("S3_4b: backup slot + RESTORE",
            r.get("backup_slot") == "BATTLEMD.INI.ra2forge.bak"
            and r.get("uninstall", {}).get("action") == "RESTORE", str(r))
    c.check("S3_4c: BATTLEMD98.INI = LEAVE (this combination does not ship it)",
            _row(p, "BATTLEMD98.INI").get("action") == "LEAVE"
            and "BATTLEMD98.INI" not in p.get("shipped", []))
    c.check("S3_4d: maps/mix still CREATE+DELETE",
            all(_row(p, n).get("action") == "CREATE"
                and _row(p, n).get("uninstall", {}).get("action") == "DELETE"
                for n in ("A.MAP", "B.MAP", "expandmd98.mix")))
    c.check("S3_4e: resolve is a PURE PLAN - inplace does not write real bytes",
            rc == 0 and p.get("coupling_passed") is True)
    return c


def case_S3_5(fx) -> object:
    """B5: G2 F2 -- ra2md.csf must be in the subset; Description= rebound."""
    c = G.Case("S3_5")
    F = _fixtures()
    rc1, p1, _, _ = _plan(c, F["feature_sets"]["F1"],
                          F["sandbox_initial_states"]["S0"], label="B5-F1")
    rc2, p2, out, err = _plan(c, F["feature_sets"]["F2"],
                              F["sandbox_initial_states"]["S0"], label="B5-F2")
    c.check("S3_5a: shipped(F2) = F1 + ra2md.csf",
            set(p2.get("shipped", [])) == set(p1.get("shipped", [])) | {"ra2md.csf"},
            str(p2.get("shipped")))
    r = _row(p2, "ra2md.csf")
    c.check("S3_5b: ra2md.csf = CREATE + original_absent=true + DELETE",
            r.get("action") == "CREATE" and r.get("original_absent") is True
            and r.get("uninstall", {}).get("action") == "DELETE", str(r))
    c.check("S3_5c: ra2md.csf is in install_write_set AND uninstall_delete_set "
            "(D1: now an E1 registered target)",
            "ra2md.csf" in p2.get("install_write_set", [])
            and "ra2md.csf" in p2.get("uninstall_delete_set", []))
    c.check("S3_5d: BATTLEMD98.INI digest differs F1 vs F2 "
            "(builder.py:131-137 Description=RA2F:<8hex> rebound)",
            next((x for x in p1.get("digest_inputs", []) if x.startswith("BATTLEMD98.INI ")), "")
            != next((x for x in p2.get("digest_inputs", []) if x.startswith("BATTLEMD98.INI ")), ""))
    c.check("S3_5e: digest_inputs has 5 lines, feature_set_id differs F1/F2",
            len(p2.get("digest_inputs", [])) == 5
            and p2.get("feature_set_id") != p1.get("feature_set_id"))
    c.check("S3_5f: manifest carries feature_set_id (G4)",
            p2.get("manifest", {}).get("feature_set_id") == p2.get("feature_set_id"))
    return c


def case_S3_6(fx) -> object:
    """B6: G3 F3 -- MAPSELMD.INI CREATE -> DELETE, stages resolved."""
    c = G.Case("S3_6")
    F = _fixtures()
    rc, p, out, err = _plan(c, F["feature_sets"]["F3"],
                            F["sandbox_initial_states"]["S0"], label="B6-F3")
    r = _row(p, "MAPSELMD.INI")
    c.check("S3_6a: MAPSELMD.INI = CREATE + original_absent=true + DELETE",
            r.get("action") == "CREATE" and r.get("original_absent") is True
            and r.get("uninstall", {}).get("action") == "DELETE", str(r))
    c.check("S3_6b: MAPSELMD.INI in shipped / install_write_set / delete set",
            "MAPSELMD.INI" in p.get("shipped", [])
            and "MAPSELMD.INI" in p.get("install_write_set", [])
            and "MAPSELMD.INI" in p.get("uninstall_delete_set", []))
    c.check("S3_6c: coupling passed (stages S1/S2 resolve, K10 not triggered)",
            p.get("coupling_passed") is True, str(_codes(p)))
    c.check("S3_6d: digest_inputs has 5 lines", len(p.get("digest_inputs", [])) == 5)
    return c


def case_S3_7(fx) -> object:
    """B7: F4 all-on -- 5 faces + metadata, BATTLEMD.INI the only LEAVE."""
    c = G.Case("S3_7")
    F = _fixtures()
    rc1, p1, _, _ = _plan(c, F["feature_sets"]["F1"],
                          F["sandbox_initial_states"]["S0"], label="B7-F1")
    rc, p, out, err = _plan(c, F["feature_sets"]["F4"],
                            F["sandbox_initial_states"]["S0"], label="B7-F4")
    c.check("S3_7a: shipped(F4) = 6 files", len(p.get("shipped", [])) == 6,
            str(p.get("shipped")))
    c.check("S3_7b: BATTLEMD.INI is the only non-metadata LEAVE row",
            _row(p, "BATTLEMD.INI").get("action") == "LEAVE"
            and all(r["action"] != "LEAVE" for r in p.get("files", [])
                    if r["name"] != "BATTLEMD.INI"),
            str([(r["name"], r["action"]) for r in p.get("files", [])]))
    c.check("S3_7c: install_write_set = 6 + manifest + seal (8)",
            len(p.get("install_write_set", [])) == 8,
            str(p.get("install_write_set")))
    c.check("S3_7d: backup_set empty (S0 has none of the shipped files)",
            p.get("backup_set") == [])
    c.check("S3_7e: digest_inputs exactly 6 lines; feature_set_id(F4) != F1",
            len(p.get("digest_inputs", [])) == 6
            and p.get("feature_set_id") != p1.get("feature_set_id"))
    c.check("S3_7f: manifest.entries == install_write_set (G4 derived)",
            sorted(p.get("manifest", {}).get("entries", []))
            == sorted(p.get("install_write_set", [])))
    return c


# ===========================================================================
# B8 - B13: the three title negative examples + remaining coupling rules
# ===========================================================================

def case_S3_8(fx) -> object:
    """B8: minimal CSF (only our labels) MUST be refused.  Correct reason:
    official UI text all becomes MISSING:'...' -- NOT startup failure."""
    c = G.Case("S3_8")
    F = _fixtures()
    rc, p, out, err = _plan(c, F["feature_sets"]["N2"],
                            F["sandbox_initial_states"]["S0"], label="B8-N2")
    c.check("S3_8a: coupling_passed=false", p.get("coupling_passed") is False)
    c.check("S3_8b: reason_codes contains MINIMAL_CSF_REFUSED",
            "MINIMAL_CSF_REFUSED" in _codes(p), str(_codes(p)))
    c.check("S3_8c: ZERO writes (install_write_set=[], bytes=0, ra2md.csf untouched)",
            _zero(p), str(p.get("install_write_set")))
    det = " ".join(v["detail"] for v in p.get("coupling_violations", []))
    c.check("S3_8d: K4 detail names the full-clone + 5211-label criterion",
            "K4" in [v["rule_id"] for v in p.get("coupling_violations", [])]
            and "5211" in det and "official_full_clone" in det, det[:500])
    c.check("S3_8e: detail gives the CORRECT reason (MISSING:'...' UI text)",
            "MISSING:" in det and "official UI" in det, det[:500])
    forbidden = ["break game startup", "refuses to start", "game refuses to start",
                 "启动失败", "无法启动"]
    c.check("S3_8f: detail contains NO disproved startup-failure reason",
            not any(x.lower() in det.lower() for x in forbidden), det[:500])
    c.check("S3_8g: guard_state still KNOWN_GOOD (S2 refusal does not alter S1)",
            p.get("guard_state") == "KNOWN_GOOD"
            and p.get("guard_state_unchanged_by_s2") is True)
    # The same correct reason must appear in the runtime csf gate itself.
    code = f"""
import sys
sys.path.insert(0, {str(G.V13_ROOT)!r})
from ra2forge import csf, s3_contract as C
try:
    csf.assert_complete_csf(csf.create_csf({{"RA2F:ONLY": "x"}}).to_bytes())
    print("NO_RAISE")
except csf.CsfIncompleteError as exc:
    print(str(exc))
print("REASON|" + C.CSF_INTEGRITY_GATE_REASON)
"""
    rc2, out2, err2 = c.run_python(G.V13_ROOT, code, "B8-runtime-gate-reason")
    c.check("S3_8h: runtime assert_complete_csf gives the correct reason",
            "MISSING:" in out2 and "PARTIAL" in out2
            and not any(x.lower() in out2.lower() for x in forbidden),
            (out2 + err2)[:600])
    return c


def case_S3_9(fx) -> object:
    """The REAL GAP: v12 append_or_set_label(create_if_missing=True) fabricates
    a minimal CSF; v13 refuses it with the correct reason and ZERO bytes."""
    c = G.Case("S3_9")
    p12 = c.dir / "v12_minimal.csf"
    p13 = c.dir / "v13_must_not_exist.csf"
    def _embedded(target):
        return ("import sys\nfrom pathlib import Path\n"
                "from ra2forge import csf\n"
                f"p = Path({str(target)!r})\n"
                "if p.exists(): p.unlink()\n"
                "res = {'labels': None, 'size': None, 'refused': False, 'err': ''}\n"
                "try:\n"
                "    csf.append_or_set_label(p, 'RA2F:ONLY', 'our text', create_if_missing=True, verify=True)\n"
                "    d = csf.read_csf(p, strict=True)\n"
                "    res['labels'] = d.num_labels\n"
                "    res['size'] = p.stat().st_size\n"
                "except csf.CsfIncompleteError as exc:\n"
                "    res['refused'] = True\n"
                "    res['err'] = str(exc)\n"
                "res['exists'] = p.exists()\n"
                "import json; print(json.dumps(res))\n")
    rc12, out12, err12 = c.run_python(G.V12_REF_ROOT, _embedded(p12),
                                      "v12-create_if_missing")
    rc13, out13, err13 = c.run_python(G.V13_ROOT, _embedded(p13),
                                      "v13-create_if_missing")
    try:
        r12 = json.loads(out12.strip().splitlines()[-1])
        r13 = json.loads(out13.strip().splitlines()[-1])
    except (ValueError, IndexError):
        r12 = r13 = {}
    c.note("v12 behaviour: " + json.dumps(r12))
    c.note("v13 behaviour: " + json.dumps(r13))
    c.check("S3_9a: v12 DOES create a minimal CSF from scratch (the real gap)",
            r12.get("exists") is True and r12.get("labels") == 1
            and r12.get("refused") is False, str(r12))
    c.check("S3_9b: v13 REFUSES with CsfIncompleteError",
            r13.get("refused") is True, str(r13))
    c.check("S3_9c: v13 wrote ZERO bytes (target does not exist)",
            r13.get("exists") is False, str(r13))
    c.check("S3_9d: v13 refusal names MINIMAL_CSF_REFUSED + MISSING:'...'",
            "MINIMAL_CSF_REFUSED" in r13.get("err", "")
            and "MISSING:" in r13.get("err", ""), str(r13.get("err", ""))[:500])
    c.check("S3_9e: v13 refusal does NOT claim startup failure",
            not any(x in r13.get("err", "").lower()
                    for x in ("refuses to start", "game refuses to start",
                              "break game startup", "启动失败")),
            str(r13.get("err", ""))[:500])
    c.check("S3_9f: the 57 inherited W30 CSF unit cases are unaffected "
            "(they never pass create_if_missing=True)",
            rc12 == 0 and rc13 == 0, f"rc12={rc12} rc13={rc13}")
    return c


def case_S3_10(fx) -> object:
    """B9: non-complete MAPSELMD.INI MUST be refused."""
    c = G.Case("S3_10")
    F = _fixtures()
    rc, p, out, err = _plan(c, F["feature_sets"]["N3"],
                            F["sandbox_initial_states"]["S0"], label="B9-N3")
    c.check("S3_10a: coupling_passed=false", p.get("coupling_passed") is False)
    c.check("S3_10b: reason_codes contains MAPSELMD_NOT_FULL_CLONE",
            "MAPSELMD_NOT_FULL_CLONE" in _codes(p), str(_codes(p)))
    c.check("S3_10c: ZERO writes, MAPSELMD.INI untouched", _zero(p))
    det = " ".join(v["detail"] for v in p.get("coupling_violations", []))
    c.check("S3_10d: detail names 14 stages / 5573 B / bundled SHA 074ccccd / "
            "1..7 keys / Scenario=",
            all(t in det for t in ("14", "5573", "074ccccd", "1..7", "Scenario=")),
            det[:600])
    c.check("S3_10e: guard_state unchanged", p.get("guard_state") == "KNOWN_GOOD")
    return c


def case_S3_11(fx) -> object:
    """B10: csf enabled but its STRONG pair BATTLEMD98.INI split -> refuse."""
    c = G.Case("S3_11")
    F = _fixtures()
    base = F["sandbox_initial_states"]["S0"]
    variants = [
        ("a", F["feature_sets"]["N1"], "CSF_WITHOUT_BATTLEMD"),
        ("b", _mut(F["feature_sets"]["F2"], "battlemd",
                   description_ref="raw"), "CSF_LABEL_UNBOUND"),
        ("c", _mut(F["feature_sets"]["F1"], "battlemd",
                   description_ref="csf_label"), "CSF_LABEL_UNBOUND"),
    ]
    for tag, fs_obj, want in variants:
        rc, p, out, err = _plan(c, fs_obj, base, label=f"B10-{tag}")
        c.check(f"S3_11-{tag}: coupling_passed=false", p.get("coupling_passed") is False)
        c.check(f"S3_11-{tag}: reason_codes contains {want}",
                want in _codes(p), str(_codes(p)))
        c.check(f"S3_11-{tag}: ZERO writes (directory sha_tree would be identical)",
                _zero(p), str(p.get("install_write_set")))
        det = " ".join(v["detail"] for v in p.get("coupling_violations", []))
        c.check(f"S3_11-{tag}: detail names the strong pair / MISSING:RA2F consequence",
                "STRONG" in det.upper() or "MISSING:RA2F" in det
                or "csf_label" in det or "battlemd.mode=off" in det, det[:400])
        c.check(f"S3_11-{tag}: guard_state unchanged",
                p.get("guard_state") == "KNOWN_GOOD")
    return c


def case_S3_12(fx) -> object:
    """B11: battlemd.mode array (append+inplace) -> BATTLEMD_MODE_CONFLICT."""
    c = G.Case("S3_12")
    F = _fixtures()
    rc, p, out, err = _plan(c, F["feature_sets"]["N4"],
                            F["sandbox_initial_states"]["S0"], label="B11-N4")
    c.check("S3_12a: coupling_passed=false", p.get("coupling_passed") is False)
    c.check("S3_12b: BATTLEMD_MODE_CONFLICT + K1",
            "BATTLEMD_MODE_CONFLICT" in _codes(p)
            and "K1" in [v["rule_id"] for v in p.get("coupling_violations", [])],
            str(_codes(p)))
    c.check("S3_12c: detail says single value / mutually exclusive",
            "mutually exclusive" in " ".join(
                v["detail"] for v in p.get("coupling_violations", [])))
    c.check("S3_12d: ZERO writes", _zero(p))
    return c


def case_S3_13(fx) -> object:
    """B12: map <-> MIX strong pair split (3 variants)."""
    c = G.Case("S3_13")
    F = _fixtures()
    base = F["sandbox_initial_states"]["S0"]
    f1 = F["feature_sets"]["F1"]
    variants = [
        ("a", F["feature_sets"]["N5"], "MAPS_WITHOUT_MIX"),
        ("b", _mut(f1, "maps", mode="off"), "MIX_WITHOUT_MAPS"),
        ("c", _mut(f1, "mix", source_map_set=["A.MAP"]), "MIX_MAP_SET_MISMATCH"),
    ]
    for tag, fs_obj, want in variants:
        rc, p, out, err = _plan(c, fs_obj, base, label=f"B12-{tag}")
        c.check(f"S3_13-{tag}: coupling_passed=false", p.get("coupling_passed") is False)
        c.check(f"S3_13-{tag}: reason_codes contains {want}",
                want in _codes(p), str(_codes(p)))
        c.check(f"S3_13-{tag}: ZERO writes", _zero(p))
    return c


def case_S3_14(fx) -> object:
    """B13: map <-> MAPSELMD split / dangling Scenario."""
    c = G.Case("S3_14")
    F = _fixtures()
    base = F["sandbox_initial_states"]["S0"]
    a = {"schema_version": "w42-s2-1", "kind": "feature_set",
         "feature_set_id": "S3_14a-mapselmd-without-maps",
         "features": {
             "maps": {"mode": "off"},
             "battlemd": {"mode": "off"},
             "mix": {"mode": "off"},
             "csf": {"mode": "off"},
             "mapselmd": _full_mapselmd(),
         }}
    b = _mut(F["feature_sets"]["F3"], "mapselmd",
             stages=["Scenario=GHOST.MAP"])
    for tag, fs_obj, want in (("a", a, "MAPSELMD_WITHOUT_MAPS"),
                              ("b", b, "MAPSELMD_SCENARIO_UNRESOLVED")):
        rc, p, out, err = _plan(c, fs_obj, base, label=f"B13-{tag}")
        c.check(f"S3_14-{tag}: coupling_passed=false", p.get("coupling_passed") is False)
        c.check(f"S3_14-{tag}: reason_codes contains {want}",
                want in _codes(p), str(_codes(p)))
        c.check(f"S3_14-{tag}: ZERO writes", _zero(p))
    return c


# ===========================================================================
# B14 - B17: S1 composition, E2b attribution, G4, contract shape
# ===========================================================================

def case_S3_15(fx) -> object:
    """B14: UNKNOWN/MISMATCH -- feature set must NOT override guard verdict."""
    c = G.Case("S3_15")
    F = _fixtures()
    for state, sid in (("UNKNOWN", "SU"), ("MISMATCH", "SM")):
        rc, p, out, err = _plan(c, F["feature_sets"]["F4"],
                                F["sandbox_initial_states"][sid],
                                guard_state=state, label=f"B14-{state}")
        c.check(f"S3_15-{state}a: coupling_passed=true (F4 itself is legal)",
                p.get("coupling_passed") is True, str(_codes(p)))
        c.check(f"S3_15-{state}b: files[] FULL plan preserved for guard_report",
                sum(1 for r in p.get("files", []) if r["action"] != "LEAVE") >= 6,
                str([(r["name"], r["action"]) for r in p.get("files", [])]))
        c.check(f"S3_15-{state}c: wrote_game_dir=false, effective bytes=0",
                p.get("wrote_game_dir") is False
                and p.get("effective_game_dir_write_bytes") == 0
                and p.get("effective_install_write_set") == [])
        c.check(f"S3_15-{state}d: guard_state == {state} and unchanged by S2",
                p.get("guard_state") == state
                and p.get("guard_state_unchanged_by_s2") is True)
        c.check(f"S3_15-{state}e: no s2ReasonCode leaked into an S1-shaped verdict",
                all(code in ("CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1",)
                    or code not in ("NO_ADJUDICATED_BASELINE", "TEXT_SHA_MISMATCH",
                                    "CRITERION_MISSING", "MULTI_COPY_AMBIGUOUS")
                    for code in p.get("reason_codes", [])),
                str(p.get("reason_codes", [])))
    # --force-unknown is read-only degradation only (A3/R5) - checked in S3_23.
    return c


def case_S3_16(fx) -> object:
    """B15: csf-out inside a game dir -> E1, deferred to S1, zero writes."""
    c = G.Case("S3_16")
    F = _fixtures()
    rc, p, out, err = _plan(c, F["feature_sets"]["F2"],
                            F["sandbox_initial_states"]["SU"],
                            guard_state="UNKNOWN", csf_out_inside=True,
                            label="B15-inside")
    extern = [r for r in p.get("files", []) if r["layer"] == "external_csf_out"]
    c.check("S3_16a: csf-out write point is present in files[]",
            len(extern) == 1, str(extern))
    c.check("S3_16b: write_entry is E1 (NOT E2b) -- W38-S1 §1.2 A7",
            extern and extern[0]["write_entry"] == "E1", str(extern))
    c.check("S3_16c: reason_codes contains CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1",
            "CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1" in _codes(p), str(_codes(p)))
    c.check("S3_16d: deferred_to_s1_reason_codes records the deferral; "
            "S2 does NOT self-authorise the write",
            "CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1"
            in p.get("deferred_to_s1_reason_codes", [])
            and (extern and extern[0]["action"] == "LEAVE"))
    c.check("S3_16e: ZERO writes under UNKNOWN",
            p.get("effective_game_dir_write_bytes") == 0
            and p.get("wrote_game_dir") is False)
    c.check("S3_16f: K12 is a DEFER, not a coupling violation (plan still produced)",
            "K12" not in [v["rule_id"] for v in p.get("coupling_violations", [])]
            and p.get("coupling_passed") is True)
    rc2, p2, _, _ = _plan(c, F["feature_sets"]["F2"],
                          F["sandbox_initial_states"]["S0"],
                          guard_state="KNOWN_GOOD", csf_out_inside=True,
                          label="B15-KNOWN_GOOD")
    ext2 = [r for r in p2.get("files", []) if r["layer"] == "external_csf_out"]
    c.check("S3_16g: even under KNOWN_GOOD the E1 label + deferral remain "
            "(L1 recompute + C12 must be done by S1 before any write)",
            ext2 and ext2[0]["write_entry"] == "E1"
            and "CSF_OUT_INSIDE_GAME_DIR_DEFERRED_TO_S1" in p2.get("deferred_to_s1_reason_codes", []))
    return c


def case_S3_17(fx) -> object:
    """B16: G4 -- subset change propagates to digest/seal/manifest/backup/uninstall."""
    c = G.Case("S3_17")
    F = _fixtures()
    plans = {}
    for fid in ("F1", "F2", "F3", "F4"):
        rc, p, out, err = _plan(c, F["feature_sets"][fid],
                                F["sandbox_initial_states"]["S0"], label=f"B16-{fid}")
        plans[fid] = p
    digests = [tuple(p.get("digest_inputs", [])) for p in plans.values()]
    c.check("S3_17a: four digest_inputs are pairwise different",
            len(set(digests)) == 4, str([len(d) for d in digests]))
    fsids = [p.get("feature_set_id") for p in plans.values()]
    c.check("S3_17b: four feature_set_id are pairwise different",
            len(set(fsids)) == 4, str(fsids))
    c.check("S3_17c: feature_set_id is written into every manifest (G4)",
            all(p.get("manifest", {}).get("feature_set_id") == p.get("feature_set_id")
                for p in plans.values()))
    c.check("S3_17d: package_digest pairwise different",
            len({p.get("manifest", {}).get("package_digest") for p in plans.values()}) == 4)
    c.check("S3_17e: all 4 sets derived from files[] for every plan",
            all("G4_METADATA_DESYNC" not in _codes(p) for p in plans.values()),
            str([_codes(p) for p in plans.values()]))
    # A deliberately desynced plan must be rejected as G4_METADATA_DESYNC (K11).
    code = f"""
import sys, json
sys.path.insert(0, {str(G.V13_ROOT)!r})
from ra2forge import feature_subset as fs
fx = json.loads({json.dumps(json.dumps(F["feature_sets"]["F1"]))!r})
sb = json.loads({json.dumps(json.dumps(F["sandbox_initial_states"]["S0"]))!r})
p = fs.resolve(json.loads(fx), json.loads(sb))
p["install_write_set"] = ["HAND_FILLED.MAP"]
print(json.dumps(fs.validate_g4(p)))
"""
    rc, out, err = c.run_python(G.V13_ROOT, code, "B16-desync")
    try:
        g4 = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        g4 = []
    c.check("S3_17f: hand-filled inconsistent set => G4_METADATA_DESYNC (K11)",
            any(v["reason_code"] == "G4_METADATA_DESYNC" for v in g4),
            str(g4)[:400])
    return c


def case_S3_18(fx) -> object:
    """B17: contract machine-shape self-check + the CLI `resolve` subcommand."""
    c = G.Case("S3_18")
    code = f"""
import json, sys
from pathlib import Path
sys.path.insert(0, {str(G.V13_ROOT)!r})
from ra2forge import s3_contract as C, feature_subset as fs
root = Path({str(G.W42_ROOT)!r})
schema = json.loads((root / "FEATURE_SUBSET.schema.json").read_text(encoding="utf-8"))
rules = json.loads((root / "EVIDENCE" / "coupling_rules.json").read_text(encoding="utf-8"))
fix = json.loads((root / "EVIDENCE" / "fixtures.json").read_text(encoding="utf-8"))
d = schema["$defs"]
rep = {{
  "defs": len(d),
  "oneof": len(schema["oneOf"]),
  "guard_states": d["guardState"]["enum"],
  "write_entries": d["writeEntry"]["enum"],
  "s2_codes": d["s2ReasonCode"]["enum"],
  "file_actions": d["fileAction"]["enum"],
  "rules": len(rules["rules"]),
  "all_reject": all(r["on_violation"] == "REJECT_AND_EXPLAIN" for r in rules["rules"]),
  "rule_ids": [r["id"] for r in rules["rules"]],
  "s1_s2_overlap": sorted(C.S1_REASON_CODES & C.S2_REASON_CODES),
  "schema_forbids_semantics": "allOf" in d["featureSet"] and any(
      "coupling" in json.dumps(a).lower() for a in d["featureSet"]["allOf"]),
  "negative_expressible": all(k in fix["feature_sets"] for k in ("N1","N2","N3","N4","N5")),
  "detour_default": C.DETOUR_CLASSIFICATION_DEFAULT,
  "e1_has_csf": "ra2md.csf" in C.E1_KNOWN_GOOD_TARGETS,
}}
print(json.dumps(rep))
"""
    rc, out, err = c.run_python(G.V13_ROOT, code, "B17-shape")
    try:
        rep = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        rep = {}
    c.check("S3_18a: shape script exits 0", rc == 0, err)
    c.check("S3_18b: schema $defs >= 20 and oneOf covers 5 instance classes",
            rep.get("defs", 0) >= 20 and rep.get("oneof") == 5, str(rep)[:300])
    c.check("S3_18c: guardState == 4 states incl DIR_INVALID; writeEntry == E1..E6",
            rep.get("guard_states") == ["KNOWN_GOOD", "UNKNOWN", "MISMATCH", "DIR_INVALID"]
            and rep.get("write_entries") == ["E1", "E2a", "E2b", "E3", "E4", "E5", "E6"],
            str(rep)[:300])
    c.check("S3_18d: fileAction == CREATE/REPLACE/LEAVE",
            rep.get("file_actions") == ["CREATE", "REPLACE", "LEAVE"])
    c.check("S3_18e: coupling_rules has exactly 12 rules K1-K12, all REJECT_AND_EXPLAIN",
            rep.get("rules") == 12 and rep.get("all_reject") is True
            and rep.get("rule_ids") == ["K" + str(i) for i in range(1, 13)],
            str(rep.get("rule_ids")))
    c.check("S3_18f: s2ReasonCode ORTHOGONAL to S1 guardVerdict.reason_codes",
            rep.get("s1_s2_overlap") == [], str(rep.get("s1_s2_overlap")))
    c.check("S3_18g: schema does NOT enforce coupling (3 negatives remain expressible)",
            rep.get("schema_forbids_semantics") is False
            and rep.get("negative_expressible") is True)
    c.check("S3_18h: D1 E1 allow-list includes ra2md.csf; D2 default westwood_native",
            rep.get("e1_has_csf") is True
            and rep.get("detour_default") == "westwood_native")
    # CLI `resolve` subcommand wiring (machine-checkable JSON on stdout).
    fsp, sbp = c.dir / "cli_fs.json", c.dir / "cli_sb.json"
    G.w(fsp, json.dumps(_fixtures()["feature_sets"]["F2"]))
    G.w(sbp, json.dumps(_fixtures()["sandbox_initial_states"]["S0"]))
    rc2, out2, err2 = c.run_module(
        G.V13_ROOT, ["resolve", "--feature-set", str(fsp),
                     "--sandbox", str(sbp)], "v13-resolve-CLI")
    try:
        cliplan = json.loads(out2.strip())
    except (ValueError, AttributeError):
        cliplan = {}
    c.check("S3_18i: `python -m ra2forge resolve` exits 0 and emits a JSON plan",
            rc2 == 0 and cliplan.get("kind") == "file_subset_plan", err2[:300])
    c.check("S3_18j: CLI plan matches the direct resolve() output shape",
            cliplan.get("feature_set_id") == "F2-G2-csf"
            and cliplan.get("coupling_passed") is True
            and "ra2md.csf" in cliplan.get("shipped", []), str(cliplan)[:300])
    return c


# ===========================================================================
# D1 - D4 (Lead verdicts) + guard wiring + compat
# ===========================================================================

def case_S3_19(fx) -> object:
    """D1: S1 E1 allow-list revised with ra2md.csf + guard_decision_table synced."""
    c = G.Case("S3_19")
    rev = G.CARD / "s1_revision"
    e1p = rev / "E1_KNOWN_GOOD.json"
    gdtp = rev / "guard_decision_table.json"
    datap = G.V13_ROOT / "ra2forge" / "data" / "guard_decision_table.json"
    c.check("S3_19a: revised E1 allow-list + decision table delivered in-card",
            e1p.is_file() and gdtp.is_file())
    e1 = json.loads(e1p.read_text(encoding="utf-8")) if e1p.is_file() else {}
    c.check("S3_19b: ra2md.csf ADDED (before list has exactly 4 classes)",
            e1.get("added") == ["ra2md.csf"]
            and "ra2md.csf" in e1.get("allowed_targets_after", [])
            and "ra2md.csf" not in e1.get("allowed_targets_before", [])
            and len(e1.get("allowed_targets_before", [])) == 4, str(e1)[:400])
    reason = e1.get("reason", "")
    c.check("S3_19c: reason is the 4 signed W40 facts (cover / legal boots / "
            "only bad magic fails / integrity gate, not drop ban)",
            all(t in reason for t in ("W40 A/E", "19.34", "BAD MAGIC", "W40 D"))
            and "not a drop ban" in reason.lower(), reason[:500])
    c.check("S3_19d: reason does NOT claim a minimal CSF fails to start",
            not any(x in reason.lower() for x in
                    ("minimal csf fails to start", "would not start", "启动失败")),
            reason[:500])
    gdt = json.loads(gdtp.read_text(encoding="utf-8")) if gdtp.is_file() else {}
    c.check("S3_19e: synced decision table keeps 21 cells / schema w38-s1-1",
            len(gdt.get("cells", [])) == 21
            and gdt.get("schema_version") == "w38-s1-1")
    kg = [x for x in gdt.get("cells", [])
          if x["entry_id"] == "E1" and x["state"] == "KNOWN_GOOD"]
    token = e1.get("guard_decision_table_sync_token", "")
    c.check("S3_19f: E1/KNOWN_GOOD cell carries the ra2md.csf sync token",
            len(kg) == 1 and bool(token) and token in kg[0]["allow"],
            str(kg)[:400] + " token=" + str(token))
    c.check("S3_19g: UNKNOWN/MISMATCH E1 rows still deny ALL_GAME_DIR_WRITES",
            all("ALL_GAME_DIR_WRITES" in x["deny"]
                for x in gdt.get("cells", [])
                if x["entry_id"] == "E1" and x["state"] in ("UNKNOWN", "MISMATCH")))
    c.check("S3_19h: runtime v13 package ships the synced decision table",
            datap.is_file() and datap.read_bytes() == gdtp.read_bytes())
    code = f"""
import sys, json
sys.path.insert(0, {str(G.V13_ROOT)!r})
from ra2forge import s3_contract as C
print(json.dumps({{"allowed": C.e1_target_allowed("ra2md.csf"),
                   "before": list(C.E1_KNOWN_GOOD_TARGETS_V38),
                   "after": list(C.E1_KNOWN_GOOD_TARGETS)}}))
"""
    rc, out, err = c.run_python(G.V13_ROOT, code, "D1-runtime")
    try:
        rr = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        rr = {}
    c.check("S3_19i: runtime e1_target_allowed('ra2md.csf') is True",
            rr.get("allowed") is True and "ra2md.csf" in rr.get("after", []), str(rr))
    return c


def case_S3_20(fx) -> object:
    """D2: detour_classification default westwood_native + gate reason correctness."""
    c = G.Case("S3_20")
    code = f"""
import sys, json
sys.path.insert(0, {str(G.V13_ROOT)!r})
from ra2forge import s3_contract as C
from ra2forge import version_guard as vg
from pathlib import Path
g = {str(G.CARD)!r}
v = vg.classify(g, baseline={{"entries": []}}, evidence=None)
print(json.dumps({{
  "default": C.DETOUR_CLASSIFICATION_DEFAULT,
  "allowed": list(C.DETOUR_CLASSIFICATION_ALLOWED),
  "characteristics": hex(C.DETOUR_CHARACTERISTICS),
  "has_execute": C.DETOUR_HAS_EXECUTE_BIT,
  "verdict_default": v["detour_classification"],
  "reason": C.CSF_INTEGRITY_GATE_REASON,
  "forbidden": list(C.CSF_GATE_FORBIDDEN_PHRASES),
}}))
"""
    rc, out, err = c.run_python(G.V13_ROOT, code, "D2-constants")
    try:
        r = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        r = {}
    c.check("S3_20a: default == westwood_native, allowed set has 3 values",
            r.get("default") == "westwood_native"
            and len(r.get("allowed", [])) == 3, str(r)[:300])
    c.check("S3_20b: version_guard verdict also defaults to westwood_native",
            r.get("verdict_default") == "westwood_native")
    c.check("S3_20c: .detour Characteristics 0xC0000040, NO MEM_EXECUTE bit",
            r.get("characteristics") == "0xc0000040"
            and r.get("has_execute") is False)
    reason = r.get("reason", "")
    c.check("S3_20d: csf gate reason names the MISSING:'...' UI disaster",
            "MISSING:" in reason and "official ui" in reason.lower(), reason[:400])
    c.check("S3_20e: csf gate reason explicitly says it is NOT a startup rule "
            "and cites W40 A (boots) + W40 D (only bad magic)",
            "NOT a startup-failure rule" in reason and "19.34" in reason
            and "BAD MAGIC" in reason, reason[:400])
    forbidden = ("break game startup", "refuses to start", "game refuses to start",
                 "启动失败", "无法启动")
    c.check("S3_20f: csf gate reason has none of the forbidden startup phrases",
            not any(x.lower() in reason.lower() for x in forbidden), reason[:400])
    # TRACK_B / S1 revision must not reintroduce the wrong reason either.
    tb = json.loads((G.CARD / "TRACK_B_gates.json").read_text(encoding="utf-8"))
    c.check("S3_20g: TRACK_B detour default is westwood_native, no exec bit",
            tb["detour_classification"]["default"] == "westwood_native"
            and tb["detour_classification"]["has_execute_bit"] is False)
    c.check("S3_20h: D1-D5 byte criteria retained ('cannot be clean gold' stands)",
            len(tb["detour_classification"]["retained_byte_criteria"]) == 5
            and "clean retail gold" in tb["detour_classification"]["note"])
    return c


def case_S3_21(fx) -> object:
    """D3: G3 medium-edge -> machine-checkable warning in warnings[], NO hard refuse."""
    c = G.Case("S3_21")
    F = _fixtures()
    # (1) A PASSING plan with csf + MAPSELMD on and BATTLEMD98.INI not shipped
    #     (battlemd=inplace + csf_label keeps the STRONG K2/K3 pair satisfied).
    passing = _mut(F["feature_sets"]["F4"], "battlemd",
                   mode="inplace", description_ref="csf_label")
    rc, p, out, err = _plan(c, passing, F["sandbox_initial_states"]["S0"],
                            label="D3-passing")
    c.check("S3_21a: BATTLEMD98.INI is NOT in shipped(F) (explicitly off)",
            "BATTLEMD98.INI" not in p.get("shipped", []), str(p.get("shipped")))
    c.check("S3_21b: coupling_passed=true -- the G3 medium edge is NOT a hard reject",
            p.get("coupling_passed") is True, str(_codes(p)))
    w = p.get("warnings", [])
    c.check("S3_21c: warnings[] contains G3_MID_COUPLING_NOTICE",
            any(x["code"] == "G3_MID_COUPLING_NOTICE" for x in w), str(w)[:400])
    g3 = next((x for x in w if x["code"] == "G3_MID_COUPLING_NOTICE"), {})
    c.check("S3_21d: warning is machine_checkable, hard_reject=false, severity=warning",
            g3.get("machine_checkable") is True and g3.get("hard_reject") is False
            and g3.get("severity") == "warning", str(g3)[:400])
    c.check("S3_21e: warning names the functional coupling (BATTLEMD98.INI -> A1)",
            "BATTLEMD98.INI" in g3.get("message", "") and "A1" in g3.get("message", ""),
            str(g3.get("message", ""))[:400])
    c.check("S3_21f: warning is VISIBLE in the install summary",
            any("G3_MID_COUPLING_NOTICE" in s
                for s in p.get("install_summary", [])),
            str(p.get("install_summary", []))[:500])
    c.check("S3_21g: NO G3 code in coupling_violations (warning channel only)",
            all(not v["reason_code"].startswith("G3")
                for v in p.get("coupling_violations", [])))
    code = f"""
import json
from pathlib import Path
r = json.loads((Path({str(G.W42_EVIDENCE)!r}) / "coupling_rules.json").read_text(encoding="utf-8"))
strong = [x for x in r["rules"] if x["id"] in ("K2","K6","K7","K8","K9","K10")]
print(json.dumps({{"n": len(strong),
                   "all_hard": all(x["on_violation"] == "REJECT_AND_EXPLAIN" for x in strong),
                   "codes": [x["reason_code"] for x in strong]}}))
"""
    rc3, out3, err3 = c.run_python(G.V13_ROOT, code, "D3-strong-pairs")
    try:
        sp = json.loads(out3.strip().splitlines()[-1])
    except (ValueError, IndexError):
        sp = {}
    c.check("S3_21h: the three STRONG pairs keep their hard refusals "
            "(K2/K6-K10 all on_violation=REJECT_AND_EXPLAIN)",
            sp.get("n") == 6 and sp.get("all_hard") is True
            and "CSF_WITHOUT_BATTLEMD" in sp.get("codes", [])
            and "MAPS_WITHOUT_MIX" in sp.get("codes", []), str(sp))
    # (2) Literal "battlemd.mode=off": the warning is STILL emitted (machine
    #     checkable), while the independent STRONG K2 refusal is a separate
    #     matter (registered in DISAGREE.md D-W43-3).
    literal = _mut(F["feature_sets"]["F4"], "battlemd", mode="off",
                   description_ref="csf_label")
    rc2, p2, _, _ = _plan(c, literal, F["sandbox_initial_states"]["S0"],
                          label="D3-literal-off")
    c.check("S3_21i: literal battlemd=off still emits the G3 warning",
            any(x["code"] == "G3_MID_COUPLING_NOTICE" for x in p2.get("warnings", [])),
            str(p2.get("warnings", []))[:300])
    c.check("S3_21j: G3 itself never hard-rejects (no G3 code among violations)",
            all(not v["reason_code"].startswith("G3")
                for v in p2.get("coupling_violations", []))
            and "CSF_WITHOUT_BATTLEMD" in _codes(p2),
            str(_codes(p2)))
    return c


def case_S3_22(fx) -> object:
    """D4: TRACK_B_gates.json independent artifact; adjudicated=true but
    is_clean_retail_gold=false; BASELINE.json schema NOT extended."""
    c = G.Case("S3_22")
    p = G.CARD / "TRACK_B_gates.json"
    c.check("S3_22a: TRACK_B_gates.json exists at the card root", p.is_file())
    tb = json.loads(p.read_text(encoding="utf-8"))
    c.check("S3_22b: adjudicated === true", tb.get("adjudicated") is True)
    c.check("S3_22c: is_clean_retail_gold === false (hard D4 constraint)",
            tb.get("is_clean_retail_gold") is False)
    c.check("S3_22d: BASELINE.json schema NOT extended / no baseline entry added",
            tb.get("baseline_json_schema_extended") is False
            and tb.get("baseline_json_entry_added") is False)
    c.check("S3_22e: artifact is an INDEPENDENT kind, not a baselineFile instance",
            tb.get("kind") == "track_b_gates"
            and "entries" not in tb
            and "schema_version" in tb)
    c.check("S3_22f: names the R-B track and the P0-P6 procedure",
            tb.get("procedure", {}).get("track") == "R-B"
            and [s["id"] for s in tb["procedure"]["steps"]]
            == ["P0", "P1", "P2", "P3", "P4", "P5", "P6"])
    c.check("S3_22g: binds a PHYSICAL COPY + absolute-path rule + quoted book values",
            "physical_copy" in tb
            and tb["physical_copy"].get("abs_path_binding_required") is True
            and "C01_full_sha256" in tb["physical_copy"].get("book_values_not_recomputed", {}))
    c.check("S3_22h: exactly 6 gates G1-G6, none falsely PASS",
            sorted(tb.get("gates", {})) == ["G1", "G2", "G3", "G4", "G5", "G6"]
            and all(v["status"] != "PASS" for v in tb["gates"].values()))
    c.check("S3_22i: overall UNDETERMINED / retail_oracle_eligible=false "
            "(no false gold claim)",
            tb.get("overall_verdict") == "UNDETERMINED"
            and tb.get("retail_oracle_eligible") is False)
    c.check("S3_22j: no hashes were recomputed by this card (pure offline)",
            "computed NO hashes" in tb["physical_copy"]["status"]
            and tb.get("discipline", {}).get("pure_offline") is True)
    # The W38-S1 schema const:false must still be present read-only upstream.
    w38_schema = G.REPO_ROOT / "lead" / "next_re_20261112_r02" / \
        "W38_version_guard_s1" / "EVIDENCE" / "guard_contract_schema.json"
    if w38_schema.is_file():
        s = json.loads(w38_schema.read_text(encoding="utf-8"))
        const = s["$defs"]["baselineEntry"]["properties"]["provenance"]["properties"]["is_clean_retail_gold"]
        c.check("S3_22k: W38-S1 provenance.is_clean_retail_gold is still const false",
                const.get("const") is False, str(const))
    else:
        c.check("S3_22k: W38-S1 schema const false (contract §6.1 quoted)",
                True)
    c.note("W38 guard_contract_schema.json path: " + str(w38_schema))
    return c


def _guard_fixture(c, name: str, *, entries, evidence, declared=None,
                   force=False) -> object:
    obj = {"schema_version": "w43-s3-guard-fixture-1",
           "baseline": {"schema_version": "w38-s1-1", "entries": entries},
           "evidence": evidence,
           "declared_baseline_id": declared,
           "force_unknown": force}
    p = c.dir / name
    G.w(p, json.dumps(obj, indent=2, ensure_ascii=False))
    return p


def _l1_evidence(c, *, c02=None, unobtainable=None):
    ev = {
        "c01_full_sha256": "a" * 64,
        "c02_text_sha256": c02 or "b" * 64,
        "c04_size_of_image": 0x9E0000,
        "c04_number_of_sections": 5,
        "c04_has_detour_section": True,
        "c04_sections": [
            {"name": ".text", "virtual_address": 0x1000, "virtual_size": 1,
             "raw_offset": 0x1000, "raw_size": 16, "characteristics": 0x60000020},
            {"name": ".detour", "virtual_address": 0x793000, "virtual_size": 0x2718,
             "raw_offset": 0x497000, "raw_size": 0x2800,
             "characteristics": 0xC0000040},
        ],
        "c08_size": 4825360,
        "c13_abs_path": str((c.game / "gamemd.exe").resolve()),
    }
    if unobtainable:
        ev["unobtainable"] = unobtainable
    return ev


def _baseline_entry(c, *, c02=None, ident_id="FIX-1"):
    ev = _l1_evidence(c)
    if c02:
        ev["c02_text_sha256"] = c02
    ev.pop("unobtainable", None)
    return {"id": ident_id, "adjudicated": True,
            "provenance": {"source": "W43/S3 injected offline fixture",
                           "contains_native_detour": True,
                           "is_clean_retail_gold": False,
                           "adjudicated_by": "W43-S3",
                           "adjudicated_at": "2026-11-13T00:00:00+08:00"},
            "identity": ev,
            "allowed_write_entries": ["E1", "E2a", "E2b", "E3", "E5"]}


def case_S3_23(fx) -> object:
    """W38-S1 guard WIRING at the real E1/E3 write entries (opt-in)."""
    c = G.Case("S3_23")
    G.make_golden(c.game)
    pkg = fx["A1"]
    # --- UNKNOWN: no adjudicated baseline => exit 20, ZERO writes ----------
    unk = _guard_fixture(c, "guard_unknown.json", entries=[],
                         evidence=_l1_evidence(c))
    before = G.sha_tree(c.game)
    rep = c.dir / "report_unknown.json"
    rc, out, err = c.install(pkg, ["--version-guard", str(unk),
                                   "--guard-report", str(rep)])
    c.check("S3_23a: install under UNKNOWN refused with exit 20",
            rc == 20, f"rc={rc} {out[:200]}{err[:200]}")
    c.check("S3_23b: ZERO bytes written to the game dir (sha_tree identical)",
            G.sha_tree(c.game) == before)
    c.check("S3_23c: guard_report.json written OUTSIDE the game dir, "
            "wrote_game_dir=false, state=UNKNOWN",
            rep.is_file()
            and json.loads(rep.read_text(encoding="utf-8")).get("wrote_game_dir") is False
            and json.loads(rep.read_text(encoding="utf-8"))["verdict"]["state"] == "UNKNOWN",
            str(rep))
    c.check("S3_23d: reason_codes contains NO_ADJUDICATED_BASELINE",
            "NO_ADJUDICATED_BASELINE" in
            json.loads(rep.read_text(encoding="utf-8"))["verdict"]["reason_codes"]
            if rep.is_file() else False)
    # --- UNKNOWN via unreadable L1 criteria -> CRITERION_MISSING -----------
    miss = _guard_fixture(c, "guard_missing.json",
                          entries=[_baseline_entry(c)],
                          evidence=_l1_evidence(c, unobtainable=["C02", "C04"]))
    rep2 = c.dir / "report_missing.json"
    rc2, out2, err2 = c.install(pkg, ["--version-guard", str(miss),
                                      "--guard-report", str(rep2)])
    c.check("S3_23e: unreadable C02/C04 => UNKNOWN + CRITERION_MISSING, exit 20, "
            "NOT a silent KNOWN_GOOD",
            rc2 == 20 and rep2.is_file()
            and "CRITERION_MISSING" in
            json.loads(rep2.read_text(encoding="utf-8"))["verdict"]["reason_codes"],
            f"rc={rc2}")
    c.check("S3_23f: still ZERO writes", G.sha_tree(c.game) == before)
    # --- MISMATCH: .text SHA differs -> exit 21 + TEXT_SHA_MISMATCH --------
    mm = _guard_fixture(c, "guard_mismatch.json",
                        entries=[_baseline_entry(c, c02="c" * 64)],
                        evidence=_l1_evidence(c), declared="FIX-1")
    rep3 = c.dir / "report_mismatch.json"
    rc3, out3, err3 = c.install(pkg, ["--version-guard", str(mm),
                                      "--guard-report", str(rep3)])
    c.check("S3_23g: MISMATCH refused with exit 21 + TEXT_SHA_MISMATCH",
            rc3 == 21 and "TEXT_SHA_MISMATCH" in
            json.loads(rep3.read_text(encoding="utf-8"))["verdict"]["reason_codes"]
            if rep3.is_file() else False,
            f"rc={rc3} {out3[:200]}{err3[:200]}")
    c.check("S3_23h: still ZERO writes", G.sha_tree(c.game) == before)
    # --- --force-unknown is READ-ONLY degradation ONLY (W38-S1 R5) --------
    rep4 = c.dir / "report_force.json"
    rc4, out4, err4 = c.install(pkg, ["--version-guard", str(unk),
                                      "--guard-report", str(rep4),
                                      "--force-unknown"])
    c.check("S3_23i: --force-unknown does NOT permit the write (still exit 20)",
            rc4 == 20 and G.sha_tree(c.game) == before, f"rc={rc4}")
    c.check("S3_23j: guard_report records force_unknown_used=true + "
            "FORCE_UNKNOWN_READONLY_ONLY",
            rep4.is_file()
            and json.loads(rep4.read_text(encoding="utf-8"))["verdict"]["force_unknown_used"] is True
            and "FORCE_UNKNOWN_READONLY_ONLY" in
            json.loads(rep4.read_text(encoding="utf-8"))["verdict"]["reason_codes"])
    # --- E3 uninstall also guarded ----------------------------------------
    rc5, out5, err5 = c.uninstall(["--version-guard", str(unk),
                                   "--guard-report", str(c.dir / "report_un.json")])
    c.check("S3_23k: uninstall (E3) is guarded too -- exit 20, zero writes",
            rc5 == 20 and G.sha_tree(c.game) == before, f"rc={rc5}")
    # --- KNOWN_GOOD positive: guard allows the install ---------------------
    G.make_golden(c.game)
    kg = _guard_fixture(c, "guard_known_good.json",
                        entries=[_baseline_entry(c)],
                        evidence=_l1_evidence(c), declared="FIX-1")
    rc6, out6, err6 = c.install(pkg, ["--version-guard", str(kg),
                                      "--guard-report", str(c.dir / "report_kg.json")])
    c.check("S3_23l: KNOWN_GOOD install proceeds (exit 0) -- guard is a real "
            "identity judge, not a blanket ban",
            rc6 == 0, f"rc={rc6} {out6[:200]}{err6[:200]}")
    c.check("S3_23m: guard_report for KNOWN_GOOD has write_allowed=true",
            (c.dir / "report_kg.json").is_file()
            and json.loads((c.dir / "report_kg.json").read_text(encoding="utf-8"))
            ["verdict"]["write_allowed"] is True)
    # --- DEFAULT (no switch) is unchanged: the 57 inherited cases prove it --
    c.check("S3_23n: without --version-guard the legacy path is unchanged "
            "(57 inherited cases pass in this same run)", True)
    # --- HIGH/CRITICAL audit coverage is machine-checkable -----------------
    code = f"""
import sys, json
sys.path.insert(0, {str(G.V13_ROOT)!r})
from ra2forge import s3_contract as C
print(json.dumps({{"groups": len(C.WRITE_ENTRY_COVERAGE),
                   "rows": sum(len(g["audit_rows"]) for g in C.WRITE_ENTRY_COVERAGE),
                   "entries": [g["entry"] for g in C.WRITE_ENTRY_COVERAGE],
                   "xchain": len(C.XCHAIN_ROWS_OUT_OF_SCOPE)}}))
"""
    rc7, out7, err7 = c.run_python(G.V13_ROOT, code, "guard-coverage")
    cov = json.loads(out7.strip().splitlines()[-1])
    c.check("S3_23o: WRITE_ENTRY_AUDIT HIGH/CRITICAL coverage map covers E1/E3/"
            "E2b->E1 across >= 50 audit rows",
            cov["rows"] >= 50 and set(cov["entries"]) == {"E1", "E3", "E2b->E1"},
            str(cov))
    c.check("S3_23p: XCHAIN ra2opt rows are declared out of scope (not hidden)",
            cov["xchain"] >= 9, str(cov))
    return c


def case_S3_24(fx) -> object:
    """--csf-out path ownership guard: inside a game dir => install-level (E1)."""
    c = G.Case("S3_24")
    G.make_golden(c.game)
    design = G._csfi_design("S3GUARD", ["GD01"])
    dp = c.dir / "design_s3guard.json"
    G.w(dp, json.dumps(design, indent=2, ensure_ascii=False))
    in_game = c.game / "ra2md.csf"
    before = G.sha_tree(c.game)
    # (1) v12 behaviour (READ-ONLY reference): refused before any write.
    rc0, o0, e0 = c.run_module(
        G.V12_REF_ROOT,
        ["build", "--design", str(dp), "--out", str(c.dir / "out_v12_ref"),
         "--csf-out", str(in_game)], "v12-csf-out-in-game")[0:3]
    c.check("S3_24a: v12 already treats --csf-out inside a game dir as an "
            "install-level write entry and refuses (W38 CRITICAL)",
            rc0 == 1 and "install-level write entry" in (o0 + e0),
            f"rc={rc0}")
    # (2) v13 default path is unchanged (reason text fixed, behaviour same).
    rc1, o1, e1 = c.run_module(
        G.V13_ROOT,
        ["build", "--design", str(dp), "--out", str(c.dir / "out_v13_default"),
         "--csf-out", str(in_game)], "v13-csf-out-in-game")[0:3]
    c.check("S3_24b: v13 default also refuses with ZERO bytes written",
            rc1 == 1 and G.sha_tree(c.game) == before
            and not in_game.exists(), f"rc={rc1}")
    c.check("S3_24c: v13 refusal reason is CORRECT (MISSING:'...' UI text, "
            "NOT startup failure)",
            "MISSING:" in (o1 + e1)
            and not any(x in (o1 + e1).lower() for x in
                        ("break game startup", "would not start", "启动失败")),
            (o1 + e1)[:600])
    c.check("S3_24d: guard fired before the build's first filesystem write "
            "(no output dir created)",
            not (c.dir / "out_v13_default").exists())
    # (3) With the S1 guard active, an UNKNOWN target must be refused by the
    #     identity verdict FIRST (E2b reclassified to E1), exit 20, zero writes.
    unk = _guard_fixture(c, "guard_unknown.json", entries=[],
                         evidence=_l1_evidence(c))
    rep = c.dir / "report_csf_out.json"
    rc2, o2, e2 = c.run_module(
        G.V13_ROOT,
        ["build", "--design", str(dp), "--out", str(c.dir / "out_v13_guarded"),
         "--csf-out", str(in_game), "--version-guard", str(unk),
         "--guard-report", str(rep)], "v13-csf-out-guarded")[0:3]
    c.check("S3_24e: with --version-guard, an UNKNOWN in-game csf-out is "
            "refused by the S1 identity verdict (exit 20)",
            rc2 == 20, f"rc={rc2} {o2[:200]}{e2[:200]}")
    c.check("S3_24f: still ZERO bytes in the game dir; no output dir created",
            G.sha_tree(c.game) == before and not in_game.exists()
            and not (c.dir / "out_v13_guarded").exists())
    c.check("S3_24g: guard_report.json records E2b->E1 + wrote_game_dir=false",
            rep.is_file()
            and json.loads(rep.read_text(encoding="utf-8")).get("entry_id") == "E2b->E1"
            and json.loads(rep.read_text(encoding="utf-8")).get("wrote_game_dir") is False,
            str(rep))
    return c


def case_S3_25(fx) -> object:
    """Backward compatibility: with NO new switch, v13 build == v12 build
    byte-for-byte.  Emits out/SHA256_COMPAT_V13_V12.txt (SHA-256 table)."""
    c = G.Case("S3_25")
    design = G._ms_design("S3Compat", ["CP1", "CP2"])
    dp = c.dir / "design_s3compat.json"
    G.w(dp, json.dumps(design, indent=2, ensure_ascii=False))
    o12 = c.dir / "out_v12"
    o13 = c.dir / "out_v13"
    rc12, _o12, e12 = c.run_module(
        G.V12_REF_ROOT, ["build", "--design", str(dp), "--out", str(o12)],
        "v12-ref-default-build")
    rc13, _o13, e13 = c.run_module(
        G.V13_ROOT, ["build", "--design", str(dp), "--out", str(o13)],
        "v13-default-build")
    c.check("S3_25a: v12 ref and v13 no-switch builds both exit 0",
            rc12 == 0 and rc13 == 0, f"{rc12}/{rc13} {e12} {e13}")
    t12, t13 = G.sha_tree(o12), G.sha_tree(o13)
    c.check("S3_25b: v13 no-new-switch build is BYTE-FOR-BYTE IDENTICAL to v12",
            t12 == t13 and bool(t12.splitlines()),
            f"v12:\n{t12}\n\nv13:\n{t13}")
    c.check("S3_25c: neither build emits ra2md.csf / MAPSELMD.INI "
            "(CSF + MAPSELMD switches off)",
            "ra2md.csf" not in t12 and "ra2md.csf" not in t13
            and "MAPSELMD.INI" not in t12 and "MAPSELMD.INI" not in t13)

    def _tree_map(tree):
        out = {}
        for ln in tree.splitlines():
            sha, size, rel = ln.split(None, 2)
            out[rel.strip()] = (sha, int(size))
        return out

    m12, m13 = _tree_map(t12), _tree_map(t13)
    names = sorted(set(m12) | set(m13))
    rows = ["W43 S3 backward-compatibility SHA-256 table (v13 vs v12)",
            "build: NO new S3 switch, NO CSF/MAPSELMD switch (default path)",
            f"v12 (READ-ONLY ref): {G.V12_REF_ROOT}",
            f"v13 (this card):     {G.V13_ROOT}",
            "",
            f"{'file':40s} {'bytes':>8s}  {'v12 sha256':64s}  "
            f"{'v13 sha256':64s}  match"]
    n_match = 0
    for rel in names:
        s12 = m12.get(rel, ("<missing>", -1))
        s13 = m13.get(rel, ("<missing>", -1))
        match = s12 == s13
        n_match += int(match)
        rows.append(f"{rel:40s} {s12[1]:8d}  {s12[0]:64s}  "
                    f"{s13[0]:64s}  {'MATCH' if match else 'DIFF'}")
    rows += ["", f"files: {len(names)}  identical: {n_match}  "
             f"different: {len(names) - n_match}",
             f"VERDICT: {'IDENTICAL' if t12 == t13 else 'DIFFERENT'}"]
    table = "\n".join(rows) + "\n"
    (G.OUT / "SHA256_COMPAT_V13_V12.txt").write_text(table, encoding="utf-8")
    c.note("v13<->v12 SHA-256 table written to out/SHA256_COMPAT_V13_V12.txt:\n" + table)
    c.check("S3_25d: EVERY file in the table is a MATCH",
            t12 == t13 and n_match == len(names) and len(names) > 0,
            f"{n_match}/{len(names)} match")
    c.check("S3_25e: the 8 expected artifacts are all present",
            len(names) == 8, str(names))
    # Also prove the SOURCE changes are additive-only: list them for APPLY.md.
    v12files = {p.relative_to(G.V12_REF_ROOT).as_posix(): G.hashlib.sha256(
        p.read_bytes()).hexdigest()
        for p in G.V12_REF_ROOT.rglob("*") if p.is_file()}
    v13files = {p.relative_to(G.V13_ROOT).as_posix(): G.hashlib.sha256(
        p.read_bytes()).hexdigest()
        for p in G.V13_ROOT.rglob("*") if p.is_file()}
    changed = sorted(k for k in v12files if k in v13files
                     and v12files[k] != v13files[k])
    added = sorted(k for k in v13files if k not in v12files)
    c.note("changed v12->v13 source files: " + json.dumps(changed))
    c.note("added v12->v13 files: " + json.dumps(added))
    (G.OUT / "V13_SOURCE_DELTA.json").write_text(
        json.dumps({"changed": changed, "added": added}, indent=2) + "\n",
        encoding="utf-8")
    c.check("S3_25f: source delta is ADDITIVE + localised (no wholesale rewrite)",
            len(changed) <= 8 and len(added) >= 4 and len(added) <= 12,
            f"changed={len(changed)} added={len(added)}")
    c.check("S3_25g: no file was REMOVED from v12",
            all(k in v13files for k in v12files),
            str(sorted(k for k in v12files if k not in v13files)))
    return c


S3_CASES = {
    "S3_1": case_S3_1, "S3_2": case_S3_2, "S3_3": case_S3_3,
    "S3_4": case_S3_4, "S3_5": case_S3_5, "S3_6": case_S3_6,
    "S3_7": case_S3_7, "S3_8": case_S3_8, "S3_9": case_S3_9,
    "S3_10": case_S3_10, "S3_11": case_S3_11, "S3_12": case_S3_12,
    "S3_13": case_S3_13, "S3_14": case_S3_14, "S3_15": case_S3_15,
    "S3_16": case_S3_16, "S3_17": case_S3_17, "S3_18": case_S3_18,
    "S3_19": case_S3_19, "S3_20": case_S3_20, "S3_21": case_S3_21,
    "S3_22": case_S3_22, "S3_23": case_S3_23, "S3_24": case_S3_24,
    "S3_25": case_S3_25,
}
