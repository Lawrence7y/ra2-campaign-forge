#!/usr/bin/env python3
"""W46 / B-line S4 -- S4_1..S4_8 regression cases (resolve() integration).

Bound into regress_dlc_v14.py via bind_s4(globals()); every case uses the
EXACT SAME Case harness (per-case log, check(), run_module/run_python) as the
82 preserved v13 cases.  Pure offline: no game launched, no attach, only the
card's own sandbox/ and out/ are written.  W21-W45 and the repo ra2forge/ are
READ-ONLY references.

Coverage (S3_IMPLEMENTATION.md gaps G-7 / G-8 / G-9 + the W46 task card):
  1. resolve() wired into the REAL build/install write path; plan vs actual
     per-file reconciliation; mismatch => refuse with zero writes (S4_1/S4_2/S4_3)
  2. second install (IDEMPOTENT_REPLAY 定谳) / orphan / legacy interaction
     (S4_4/S4_5/S4_6)
  3. battlemd:inplace DEFERRED (Lead D5.2): plan-layer slot reserved, mode
     explicitly refused with a machine-checkable assertion (S4_7)
  4. no new switch => v14 build byte-for-byte identical to v13; source delta
     additive + localised; no __pycache__/*.pyc (S4_8)
"""
from __future__ import annotations

import copy
import json


class _NS:
    pass


G = _NS()


def bind_s4(g: dict) -> None:
    for k, v in g.items():
        if not k.startswith("__"):
            setattr(G, k, v)
    G.V14_ROOT = G.V12_ROOT
    G.CARD = G.W43_ROOT
    G.V14_REF_ROOT = (G.W43_ROOT / "baseline_v14" / "W46_resolve_integration"
                        / "ra2forge_patched_v14")


# ---------------------------------------------------------------------------
# fixture helpers
# ---------------------------------------------------------------------------

def _w(path, obj) -> None:
    G.w(path, json.dumps(obj, indent=2, ensure_ascii=False))


def _design(tag: str = "W46S4",
            package_id: str = "org.ra2forge.w46-s4") -> dict:
    d = G._ms_design(tag, ["CP1", "CP2"], package_id=package_id)
    d["campaign"]["description"] = "W46/S4 integration regression campaign."
    return d


def _base_fsid(fsid: str) -> dict:
    return {
        "schema_version": "w42-s2-1", "kind": "feature_set",
        "feature_set_id": fsid,
        "features": {
            "maps": {"mode": "sideload",
                     "map_files": ["CP1.MAP", "CP2.MAP"],
                     "chain": ["CP1", "CP2"]},
            "battlemd": {"mode": "append", "ids": ["BATTLE01"],
                         "description_ref": "raw"},
            "mix": {"mode": "repack",
                    "source_map_set": ["CP1.MAP", "CP2.MAP"],
                    "target_name": "expandmd98.mix"},
            "csf": {"mode": "off"},
            "mapselmd": {"mode": "off"},
        },
    }


def _full_csf() -> dict:
    return {"mode": "clone_append", "base": "official_full_clone",
            "official_label_count": 5211, "labels": ["RA2F:00000001"],
            "target_name": "ra2md.csf", "official_full_min": 5211}


def _full_mapselmd() -> dict:
    return {"mode": "clone_append", "base": "official_full_clone",
            "official_stage_count": 14, "official_size_bytes": 5573,
            "bundled_official_sha256":
                "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52",
            "stages": ["S1", "S2"], "target_name": "MAPSELMD.INI"}


def _f1(fsid="W46-S4-F1") -> dict:
    return _base_fsid(fsid)


def _f2(fsid="W46-S4-F2") -> dict:
    d = _base_fsid(fsid)
    d["features"]["csf"] = _full_csf()
    d["features"]["battlemd"] = {"mode": "append", "ids": ["BATTLE01"],
                                 "description_ref": "csf_label"}
    return d


def _f3(fsid="W46-S4-F3") -> dict:
    d = _base_fsid(fsid)
    d["features"]["mapselmd"] = _full_mapselmd()
    return d


def _f0(fsid="W46-S4-F0") -> dict:
    d = _base_fsid(fsid)
    for k in d["features"]:
        d["features"][k] = {"mode": "off"}
    return d


def _f_inplace(fsid="W46-S4-INPLACE") -> dict:
    d = _base_fsid(fsid)
    d["features"]["csf"] = _full_csf()
    d["features"]["battlemd"] = {"mode": "inplace", "ids": ["BATTLE01"],
                                 "description_ref": "csf_label"}
    return d


def _f_minimal_csf(fsid="W46-S4-NEG") -> dict:
    d = _base_fsid(fsid)
    d["features"]["csf"] = {"mode": "clone_append", "base": "minimal",
                            "official_label_count": 1,
                            "labels": ["RA2F:00000001"],
                            "target_name": "ra2md.csf"}
    d["features"]["battlemd"] = {"mode": "append", "ids": ["BATTLE01"],
                                 "description_ref": "csf_label"}
    return d


def _s0() -> dict:
    """W42 ACCEPTANCE_S2 §0.1 S0 injected fixture (pure-planner cases)."""
    return {
        "schema_version": "w42-s2-1", "kind": "sandbox_initial_state",
        "sandbox_id": "S0", "game_dir": "<fixture>",
        "present_files": [{"name": "BATTLEMD.INI", "size_bytes": 2733,
                           "kind": "official_loose"}],
        "absent_files": ["BATTLEMD98.INI", "CP1.MAP", "CP2.MAP",
                         "expandmd98.mix", "ra2md.csf", "MAPSELMD.INI"],
        "guard_state": "KNOWN_GOOD", "baseline_adjudicated": True,
        "game_process_count": 0,
    }


def _fsfile(c, name: str, obj: dict):
    p = c.dir / name
    _w(p, obj)
    return p


def _build(c, design: dict, tag: str, extra=()) -> tuple:
    dp = c.dir / f"design_{tag}.json"
    _w(dp, design)
    out_dir = c.dir / f"out_{tag}"
    rc, out, err = c.run_module(
        G.V14_ROOT, ["build", "--design", str(dp), "--out", str(out_dir),
                     *extra], f"v14-build-{tag}")
    return rc, out, err, out_dir / design["campaign"]["name"]


def _golden(c, sub: str = "") -> object:
    game = c.dir / ("game" + sub)
    G.make_golden(game)
    return game


def _install(c, pkg, game, fpath, extra=()) -> tuple:
    return c.run_module(
        G.V14_ROOT,
        ["install", "--package", str(pkg), "--game", str(game),
         "--feature-set", str(fpath), *extra], "v14-install")


def _report(path) -> dict:
    try:
        return json.loads(G.Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _row(recon: dict, name: str) -> dict:
    for r in recon.get("rows", []):
        if r["name"] == name:
            return r
    return {}


def _manifest(game) -> dict:
    try:
        return json.loads((G.Path(game) / G.MANIFEST).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


# ===========================================================================
# S4_1 - build consumes resolve(): plan-driven subset + per-file reconciliation
# ===========================================================================

def case_S4_1(fx) -> object:
    """G-7 (build side): resolve() runs before the first output byte; the plan
    DRIVES the optional game-dir artifacts; plan vs actual is reconciled per
    file; a mismatch refuses with ZERO output."""
    c = G.Case("S4_1")
    d = _design("S4Build")
    f1 = _fsfile(c, "f1.json", _f1())
    f2 = _fsfile(c, "f2.json", _f2())
    f3 = _fsfile(c, "f3.json", _f3())
    f0 = _fsfile(c, "f0.json", _f0())

    rep1 = c.dir / "build_rep_f1.json"
    raw1 = c.dir / "build_raw_f1.json"
    rc, out, err, pkg = _build(
        c, d, "f1",
        ["--feature-set", str(f1), "--plan-report", str(rep1),
         "--resolve-plan-out", str(raw1)])
    r1 = _report(rep1)
    raw = _report(raw1).get("plan", {})
    c.check("S4_1a: F1 plan-driven build exits 0", rc == 0, err)
    c.check("S4_1b: build reconciliation verdict=MATCH",
            r1.get("verdict") == "MATCH", str(r1.get("verdict")))
    c.check("S4_1c: EVERY per-file row is consistent",
            bool(r1.get("rows")) and all(x["consistent"] for x in r1["rows"]),
            str([x for x in r1.get("rows", []) if not x["consistent"]]))
    c.check("S4_1d: emitted game-dir subset == plan.shipped()",
            r1.get("actually_emitted_game_dir_files")
            == ["BATTLEMD98.INI", "CP1.MAP", "CP2.MAP", "expandmd98.mix"]
            and r1.get("plan_shipped") == r1.get("actually_emitted_game_dir_files"),
            str(r1.get("actually_emitted_game_dir_files")))
    c.check("S4_1e: LEAVE rows are NOT emitted (BATTLEMD.INI / ra2md.csf / "
            "MAPSELMD.INI)",
            all(_row(r1, n)["planned_action"] == "LEAVE"
                and _row(r1, n)["actually_emitted"] is False
                for n in ("BATTLEMD.INI", "ra2md.csf", "MAPSELMD.INI")),
            str(r1.get("rows")))
    c.check("S4_1f: metadata rows are attributed to install, not build",
            all(_row(r1, n)["consistent"] and "install" in _row(r1, n).get("handled_by", "")
                for n in ("ra2forge_install.json", "ra2forge_install.json.seal")))
    c.check("S4_1g: resolve() ran BEFORE the first write (raw plan persisted)",
            raw.get("integration", {}).get("resolve_invoked_before_write") is True
            and raw.get("feature_set_id") == "W46-S4-F1", str(raw.get("integration")))
    c.check("S4_1h: package carries the in-package reconciliation artifact",
            (pkg / "ra2forge_plan_reconciliation.json").is_file())
    br = (pkg / "BUILD_REPORT.txt").read_text(encoding="utf-8") \
        if (pkg / "BUILD_REPORT.txt").is_file() else ""
    c.check("S4_1i: BUILD_REPORT.txt records the plan-driven build",
            "W46/S4 plan-driven build" in br and "W46-S4-F1" in br)

    # F3: MAPSELMD.INI is emitted BY THE PLAN, without --mapselmd.
    rep3 = c.dir / "build_rep_f3.json"
    rc3, _o3, e3, pkg3 = _build(
        c, d, "f3", ["--feature-set", str(f3), "--plan-report", str(rep3)])
    r3 = _report(rep3)
    c.check("S4_1j: F3 build (no --mapselmd) exits 0", rc3 == 0, e3)
    c.check("S4_1k: plan DRIVES MAPSELMD.INI emission",
            (pkg3 / "MAPSELMD.INI").is_file()
            and _row(r3, "MAPSELMD.INI")["planned_action"] == "CREATE"
            and _row(r3, "MAPSELMD.INI")["actually_emitted"] is True,
            str(_row(r3, "MAPSELMD.INI")))
    c.check("S4_1l: F3 build reconciliation still MATCH",
            r3.get("verdict") == "MATCH", str(r3.get("verdict")))

    # F2: ra2md.csf + csf_patch.json emitted BY THE PLAN, without --csf-out.
    rep2 = c.dir / "build_rep_f2.json"
    rc2, _o2, e2, pkg2 = _build(
        c, d, "f2", ["--feature-set", str(f2), "--plan-report", str(rep2)])
    r2 = _report(rep2)
    c.check("S4_1m: F2 build (no --csf-out) exits 0", rc2 == 0, e2)
    c.check("S4_1n: plan DRIVES ra2md.csf emission (complete official clone)",
            (pkg2 / "ra2md.csf").is_file() and (pkg2 / "csf_patch.json").is_file()
            and _row(r2, "ra2md.csf")["actually_emitted"] is True,
            str(_row(r2, "ra2md.csf")))
    c.check("S4_1o: F2 build reconciliation MATCH", r2.get("verdict") == "MATCH")

    # Mismatch: --mapselmd with a plan that marks MAPSELMD.INI LEAVE.
    out_bad = c.dir / "out_mismatch"
    rc_bad, _o, e_bad, _pkg = _build(
        c, d, "mismatch", ["--feature-set", str(f1), "--mapselmd"])
    c.check("S4_1p: switch/plan disagreement is REFUSED (exit 24)",
            rc_bad == 24 and "PLAN_ACTUAL_MISMATCH" in (e_bad + _o),
            f"rc={rc_bad} {e_bad}")
    c.check("S4_1q: refusal leaves ZERO build output", not out_bad.exists())
    # F0 all-off: build cannot emit its G1 baseline under an empty plan.
    out_f0 = c.dir / "out_f0"
    rc_f0, _o, e_f0, _pkg = _build(c, d, "f0", ["--feature-set", str(f0)])
    c.check("S4_1r: all-off F0 plan refuses the baseline build (exit 24)",
            rc_f0 == 24 and "PLAN_ACTUAL_MISMATCH" in (e_f0 + _o),
            f"rc={rc_f0} {e_f0}")
    c.check("S4_1s: F0 refusal leaves ZERO build output", not out_f0.exists())
    return c


# ===========================================================================
# S4_2 - install consumes resolve(): plan vs actual reconciliation
# ===========================================================================

def case_S4_2(fx) -> object:
    """G-7 (install side): resolve() runs BEFORE the first write; the plan is
    CONSUMED by package_files()/steps; per-file plan vs actual is MATCH; LEAVE
    rows are strictly zero-write; default (no switch) path unchanged."""
    c = G.Case("S4_2")
    d = _design("S4Install")
    f1 = _fsfile(c, "f1.json", _f1())
    _rc, _o, _e, pkg = _build(c, d, "pkg", ["--feature-set", str(f1)])
    game = _golden(c)
    before_leave = G.hashlib.sha256(
        (game / "BATTLEMD.INI").read_bytes()).hexdigest()
    rep = c.dir / "install_rep.json"
    raw = c.dir / "install_raw.json"
    rc, out, err = _install(
        c, pkg, game, f1,
        ["--plan-report", str(rep), "--resolve-plan-out", str(raw)])
    r = _report(rep)
    recon = r.get("plan_reconciliation", {})
    m = _manifest(game)
    c.check("S4_2a: plan-driven install exits 0", rc == 0, err)
    c.check("S4_2b: plan vs actual verdict=MATCH",
            recon.get("verdict") == "MATCH", str(recon.get("verdict")))
    c.check("S4_2c: EVERY per-file row is consistent",
            bool(recon.get("rows")) and all(x["consistent"] for x in recon["rows"]),
            str([x for x in recon.get("rows", []) if not x["consistent"]]))
    c.check("S4_2d: planned write set == actual write set == 4 CREATE files",
            recon.get("planned_game_dir_write_set")
            == recon.get("actual_game_dir_write_set")
            == ["BATTLEMD98.INI", "CP1.MAP", "CP2.MAP", "expandmd98.mix"],
            str(recon.get("actual_game_dir_write_set")))
    c.check("S4_2e: CREATE rows map to real 'created' steps",
            all(_row(recon, n)["planned_action"] == "CREATE"
                and _row(recon, n)["actual_action"] == "created"
                for n in ("BATTLEMD98.INI", "CP1.MAP", "CP2.MAP",
                          "expandmd98.mix")))
    c.check("S4_2f: LEAVE rows are LEAVE_SKIPPED (no step, no adopt)",
            all(_row(recon, n)["planned_action"] == "LEAVE"
                and _row(recon, n)["actual_action"] == "LEAVE_SKIPPED"
                and _row(recon, n)["write_bytes"] == 0
                for n in ("BATTLEMD.INI", "ra2md.csf", "MAPSELMD.INI")))
    c.check("S4_2g: official BATTLEMD.INI is byte-unchanged (strict LEAVE)",
            G.hashlib.sha256((game / "BATTLEMD.INI").read_bytes()).hexdigest()
            == before_leave)
    c.check("S4_2h: no ra2md.csf / MAPSELMD.INI / backup slots appeared",
            not (game / "ra2md.csf").exists()
            and not (game / "MAPSELMD.INI").exists()
            and not list(game.glob("*.ra2forge.bak")))
    c.check("S4_2i: reconciliation is persisted in the manifest (per-file rows)",
            m.get("plan_actual_reconciliation", {}).get("verdict") == "MATCH"
            and len(m.get("plan_actual_reconciliation", {}).get("rows", [])) == 9
            and m.get("feature_set_id") == "W46-S4-F1"
            and m.get("plan_mode") == "W46-S4-resolve-integration-opt-in",
            str(sorted(m.keys())))
    c.check("S4_2j: first install classified FRESH",
            r.get("second_install", {}).get("verdict") == "FRESH",
            str(r.get("second_install", {}).get("verdict")))
    rawp = _report(raw).get("plan", {})
    c.check("S4_2k: raw plan carries the integration + reservation block",
            rawp.get("integration", {}).get("resolve_invoked_before_write") is True
            and "battlemd:inplace" in rawp.get("integration", {})
            .get("plan_layer_reservations", {}))
    # Default path (no --feature-set) is untouched: manifest has NO plan keys.
    game2 = _golden(c, "_default")
    rc2, _o2, e2 = c.run_module(
        G.V14_ROOT, ["install", "--package", str(pkg), "--game", str(game2)],
        "v14-default-install")
    m2 = _manifest(game2)
    c.check("S4_2l: default (no switch) install still exits 0", rc2 == 0, e2)
    c.check("S4_2m: default path manifest has NO plan keys (byte-compatible)",
            "feature_set_id" not in m2 and "plan_actual_reconciliation" not in m2
            and "plan_mode" not in m2, str(sorted(m2.keys())))
    return c


# ===========================================================================
# S4_3 - install refusal gates: mismatch / coupling / guard / report path
# ===========================================================================

def case_S4_3(fx) -> object:
    """「计划与实际写入必须一致；不一致即拒绝」 + the other opt-in gates, all
    with a byte-level zero-write proof."""
    c = G.Case("S4_3")
    d = _design("S4Gates")
    f1 = _fsfile(c, "f1.json", _f1())
    fneg = _fsfile(c, "fneg.json", _f_minimal_csf())
    _rc, _o, _e, pkg = _build(c, d, "pkg", ["--feature-set", str(f1)])
    game = _golden(c)

    # (a) tamper the package: an extra .MAP the plan never authorised.
    (pkg / "EXTRA.MAP").write_bytes((pkg / "CP1.MAP").read_bytes())
    before = G.sha_tree(game)
    rc, out, err = _install(c, pkg, game, f1)
    c.check("S4_3a: package/plan mismatch is REFUSED (exit 24)",
            rc == 24 and "PLAN_ACTUAL_MISMATCH" in (out + err),
            f"rc={rc} {err}")
    c.check("S4_3b: refusal is byte-level ZERO WRITE",
            before == G.sha_tree(game))
    c.check("S4_3c: refusal names the unauthorised file",
            "EXTRA.MAP" in (out + err), (out + err)[-500:])
    (pkg / "EXTRA.MAP").unlink()

    # (b) injected non-KNOWN_GOOD guard state: plan preserved, zero writes.
    rawp = c.dir / "raw_unknown.json"
    before = G.sha_tree(game)
    rc, out, err = _install(
        c, pkg, game, f1,
        ["--guard-state", "UNKNOWN", "--resolve-plan-out", str(rawp)])
    pl = _report(rawp).get("plan", {})
    c.check("S4_3d: non-KNOWN_GOOD guard refuses with exit 29",
            rc == 29 and "RESOLVE_GUARD_ZERO_WRITE" in (out + err),
            f"rc={rc} {err}")
    c.check("S4_3e: guard refusal is byte-level ZERO WRITE",
            before == G.sha_tree(game))
    c.check("S4_3f: plan is PRESERVED (planned but denied), guard unchanged",
            pl.get("guard_state") == "UNKNOWN"
            and pl.get("coupling_passed") is True
            and bool(pl.get("install_write_set"))
            and pl.get("effective_game_dir_write_bytes") == 0
            and pl.get("guard_state_unchanged_by_s2") is True,
            str({k: pl.get(k) for k in ("guard_state", "coupling_passed",
                                        "effective_game_dir_write_bytes")}))

    # (c) resolve() coupling refusal (W42 B8 minimal CSF) => exit 26.
    before = G.sha_tree(game)
    rc, out, err = _install(c, pkg, game, fneg)
    c.check("S4_3g: resolve() coupling refusal => exit 26",
            rc == 26 and "RESOLVE_COUPLING_REFUSED" in (out + err),
            f"rc={rc} {err}")
    c.check("S4_3h: coupling refusal names MINIMAL_CSF_REFUSED and is ZERO WRITE",
            "MINIMAL_CSF_REFUSED" in (out + err)
            and before == G.sha_tree(game))

    # (d) report paths must never land inside the game dir (W38 A7 spirit).
    inner = game / "plan_report.json"
    before = G.sha_tree(game)
    rc, out, err = _install(c, pkg, game, f1,
                            ["--plan-report", str(inner)])
    c.check("S4_3i: report path inside game dir refused with exit 30",
            rc == 30 and "PLAN_REPORT_INSIDE_GAME_DIR" in (out + err),
            f"rc={rc} {err}")
    c.check("S4_3j: A7 refusal is byte-level ZERO WRITE and wrote no report",
            before == G.sha_tree(game) and not inner.exists())
    raw_inner = game / "raw_plan.json"
    rc, out, err = _install(c, pkg, game, f1,
                            ["--resolve-plan-out", str(raw_inner)])
    c.check("S4_3k: --resolve-plan-out inside game dir also refused (30)",
            rc == 30 and before == G.sha_tree(game)
            and not raw_inner.exists(), f"rc={rc} {err}")
    return c


# ===========================================================================
# S4_4 - second install = IDEMPOTENT_REPLAY (定谳)
# ===========================================================================

def case_S4_4(fx) -> object:
    """「同一包重复安装（幂等？拒绝？）」: IDEMPOTENT_REPLAY -- allowed, but
    ZERO game-dir writes; resolve() and the reconciliation still run."""
    c = G.Case("S4_4")
    d = _design("S4Replay")
    f1 = _fsfile(c, "f1.json", _f1())
    _rc, _o, _e, pkg = _build(c, d, "pkg", ["--feature-set", str(f1)])
    game = _golden(c)
    rc1, _o1, e1 = _install(c, pkg, game, f1)
    c.check("S4_4a: first install exits 0", rc1 == 0, e1)
    before = G.sha_tree(game)
    m_before = G.hashlib.sha256(
        (game / G.MANIFEST).read_bytes()).hexdigest()
    rep = c.dir / "replay_rep.json"
    rc2, _o2, e2 = _install(c, pkg, game, f1,
                            ["--plan-report", str(rep)])
    r = _report(rep)
    recon = r.get("plan_reconciliation", {})
    c.check("S4_4b: SECOND install is ALLOWED (exit 0), not refused", rc2 == 0, e2)
    c.check("S4_4c: verdict is IDEMPOTENT_REPLAY",
            r.get("status") == "idempotent_replay"
            and r.get("second_install", {}).get("verdict") == "IDEMPOTENT_REPLAY",
            str(r.get("status")))
    c.check("S4_4d: ZERO game-dir file writes",
            r.get("game_dir_file_writes") == 0
            and recon.get("effective_game_dir_write_bytes") == 0
            and recon.get("actual_game_dir_write_set") == [],
            str(recon.get("actual_game_dir_write_set")))
    c.check("S4_4e: game dir is BYTE-IDENTICAL before/after (manifest too)",
            before == G.sha_tree(game)
            and m_before == G.hashlib.sha256(
                (game / G.MANIFEST).read_bytes()).hexdigest())
    c.check("S4_4f: resolve()+reconciliation still ran and is MATCH",
            recon.get("verdict") == "MATCH"
            and bool(recon.get("rows"))
            and all(x["consistent"] for x in recon["rows"]),
            str(recon.get("verdict")))
    c.check("S4_4g: REPLACE rows map to zero-write 'unchanged' steps",
            all(_row(recon, n)["planned_action"] == "REPLACE"
                and _row(recon, n)["actual_action"] == "unchanged"
                and _row(recon, n)["write_bytes"] == 0
                for n in ("BATTLEMD98.INI", "CP1.MAP", "CP2.MAP",
                          "expandmd98.mix")))
    c.check("S4_4h: metadata rows are REPLAY_NOOP (record not refreshed)",
            all(_row(recon, n)["actual_action"] == "REPLAY_NOOP"
                for n in ("ra2forge_install.json",
                          "ra2forge_install.json.seal")))
    code = f"""
import sys, json
sys.path.insert(0, {str(G.V14_ROOT)!r})
from ra2forge import resolve_integration as RI
print(json.dumps({{
  "verdict": RI.SECOND_INSTALL_SEMANTICS["IDEMPOTENT_REPLAY"]["verdict"],
  "writes": RI.SECOND_INSTALL_SEMANTICS["IDEMPOTENT_REPLAY"]["game_dir_file_writes"],
  "table": sorted(RI.SECOND_INSTALL_SEMANTICS),
  "codes": RI.EXIT_CODES,
}}))
"""
    rc3, o3, e3 = c.run_python(G.V14_ROOT, code, "S4-semantics-table")
    try:
        t = json.loads(o3.strip().splitlines()[-1])
    except (ValueError, IndexError):
        t = {}
    c.check("S4_4i: the 定谳 semantics are DATA (idempotent replay, 0 writes)",
            rc3 == 0 and t.get("verdict") == "IDEMPOTENT_REPLAY"
            and t.get("writes") == 0
            and set(t.get("table", [])) == {
                "FRESH", "IDEMPOTENT_REPLAY", "SUBSET_UPGRADE",
                "LEGACY_PRE_PLAN", "DIFFERENT_PACKAGE"},
            str(t))
    c.check("S4_4j: new exit codes are >= 24 (no clash with v13 0-10 / "
            "W38-S1 20-23)",
            bool(t.get("codes")) and all(int(k) >= 24 for k in t["codes"]),
            str(t.get("codes")))
    return c


# ===========================================================================
# S4_5 - subset upgrade / downgrade + orphan cleanup (G-8)
# ===========================================================================

def case_S4_5(fx) -> object:
    """A DIFFERENT feature_set_id is a SUBSET_UPGRADE: the new plan executes,
    and files the OLD record owned but the new shipped() drops leave through
    v13 ORPHAN-FIX01 -- explicitly reconciled, never silently adopted."""
    c = G.Case("S4_5")
    d = _design("S4Upgrade")
    f1 = _fsfile(c, "f1.json", _f1())
    f3 = _fsfile(c, "f3.json", _f3())
    _r1, _o1, _e1, pkg1 = _build(c, d, "p1", ["--feature-set", str(f1)])
    _r3, _o3, _e3, pkg3 = _build(c, d, "p3", ["--feature-set", str(f3)])
    game = _golden(c)
    rc_a, _oa, ea = _install(c, pkg3, game, f3)
    c.check("S4_5a: F3 first install exits 0 and ships MAPSELMD.INI",
            rc_a == 0 and (game / "MAPSELMD.INI").is_file(), ea)
    rep = c.dir / "downgrade_rep.json"
    rc_b, ob, eb = _install(c, pkg1, game, f1,
                            ["--plan-report", str(rep)])
    r = _report(rep)
    recon = r.get("plan_reconciliation", {})
    m = _manifest(game)
    c.check("S4_5b: subset downgrade (F3 -> F1) exits 0", rc_b == 0, eb)
    c.check("S4_5c: verdict SUBSET_UPGRADE", r.get("second_install", {}).get(
        "verdict") == "SUBSET_UPGRADE", str(r.get("second_install", {}).get("verdict")))
    c.check("S4_5d: reconciliation MATCH", recon.get("verdict") == "MATCH",
            str(recon.get("verdict")))
    c.check("S4_5e: MAPSELMD.INI retired through ORPHAN-FIX01 cleanup",
            not (game / "MAPSELMD.INI").exists()
            and recon.get("orphan_cleanup", {}).get("MAPSELMD.INI") == "remove"
            and _row(recon, "MAPSELMD.INI")["actual_action"]
            == "ORPHAN_CLEANUP:remove"
            and _row(recon, "MAPSELMD.INI")["consistent"] is True,
            str(_row(recon, "MAPSELMD.INI")))
    c.check("S4_5f: manifest records the dropped orphan and the new fsid",
            m.get("feature_set_id") == "W46-S4-F1"
            and any(x.get("name") == "MAPSELMD.INI"
                    for x in m.get("removed_orphans", [])),
            str(m.get("removed_orphans")))
    c.check("S4_5g: LEAVE rows other than the cleaned orphan stay zero-write",
            all(_row(recon, n)["actual_action"] == "LEAVE_SKIPPED"
                for n in ("BATTLEMD.INI", "ra2md.csf")))
    # reverse direction: F1 -> F3 re-creates MAPSELMD.INI as a CREATE
    rep2 = c.dir / "upgrade_rep.json"
    rc_c, _oc, ec = _install(c, pkg3, game, f3,
                             ["--plan-report", str(rep2)])
    r2 = _report(rep2)
    c.check("S4_5h: subset upgrade (F1 -> F3) re-creates MAPSELMD.INI",
            rc_c == 0 and (game / "MAPSELMD.INI").is_file(), ec)
    c.check("S4_5i: upgrade reconciliation MATCH, MAPSELMD row CREATE->created",
            r2.get("plan_reconciliation", {}).get("verdict") == "MATCH"
            and _row(r2.get("plan_reconciliation", {}), "MAPSELMD.INI")
            .get("actual_action") == "created",
            str(_row(r2.get("plan_reconciliation", {}), "MAPSELMD.INI")))
    return c


# ===========================================================================
# S4_6 - orphan / legacy / different-package interaction (G-8)
# ===========================================================================

def case_S4_6(fx) -> object:
    c = G.Case("S4_6")
    d = _design("S4Legacy")
    d2 = _design("S4Other", package_id="org.ra2forge.w46-OTHER")
    f1 = _fsfile(c, "f1.json", _f1())
    _r, _o, _e, pkg = _build(c, d, "pkg", ["--feature-set", str(f1)])
    _r2, _o2, _e2, pkg_other = _build(c, d2, "pkgother",
                                      ["--feature-set", str(f1)])

    # (a) orphan: unrecorded byte-identical 'ours' file on disk.
    g1 = _golden(c, "_orphan")
    (g1 / "BATTLEMD98.INI").write_bytes((pkg / "BATTLEMD98.INI").read_bytes())
    before = G.sha_tree(g1)
    rc, out, err = _install(c, pkg, g1, f1)
    c.check("S4_6a: unrecorded 'ours' orphan REFUSED (exit 27)",
            rc == 27 and "ORPHAN_PLAN_REFUSED" in (out + err),
            f"rc={rc} {err}")
    c.check("S4_6b: orphan refusal is byte-level ZERO WRITE (no manifest)",
            before == G.sha_tree(g1) and not (g1 / G.MANIFEST).exists())
    c.check("S4_6c: refusal names the orphan",
            "BATTLEMD98.INI" in (out + err))

    # (b) legacy / pre-plan record (v13-style, no feature_set_id).
    g2 = _golden(c, "_legacy")
    rc0, _o0, e0 = c.run_module(
        G.V14_ROOT, ["install", "--package", str(pkg), "--game", str(g2)],
        "v14-default-install-legacy")
    ml0 = _manifest(g2)
    c.check("S4_6d: v13-style default install produces a PRE-PLAN manifest",
            rc0 == 0 and "feature_set_id" not in ml0, e0)
    before = G.sha_tree(g2)
    rc1, out1, err1 = _install(c, pkg, g2, f1)
    c.check("S4_6e: pre-plan record + plan REFUSED (exit 28)",
            rc1 == 28 and "LEGACY_PLAN_RECONCILE_REQUIRED" in (out1 + err1),
            f"rc={rc1} {err1}")
    c.check("S4_6f: legacy refusal is byte-level ZERO WRITE",
            before == G.sha_tree(g2))
    rep = c.dir / "legacy_rep.json"
    rc2, out2, err2 = _install(c, pkg, g2, f1,
                               ["--adopt-legacy", "--plan-report", str(rep)])
    m = _manifest(g2)
    r = _report(rep)
    c.check("S4_6g: --adopt-legacy releases the plan gate (exit 0)",
            rc2 == 0, err2)
    c.check("S4_6h: adopted record is stamped with feature_set_id + flag",
            m.get("feature_set_id") == "W46-S4-F1"
            and m.get("plan_legacy_adopted") is True
            and m.get("second_install") == "LEGACY_PRE_PLAN",
            str({k: m.get(k) for k in ("feature_set_id",
                                       "plan_legacy_adopted",
                                       "second_install")}))
    c.check("S4_6i: adopted reconciliation MATCH",
            r.get("plan_reconciliation", {}).get("verdict") == "MATCH"
            and r.get("second_install", {}).get("verdict") == "LEGACY_PRE_PLAN",
            str(r.get("plan_reconciliation", {}).get("verdict")))

    # (c) different package_id: v13 PKG-IDENT01 exit 3 still stands.
    g3 = _golden(c, "_other")
    rc3, _o3, e3 = _install(c, pkg, g3, f1)
    c.check("S4_6j: plan-driven first install for the identity test", rc3 == 0, e3)
    before = G.sha_tree(g3)
    rc4, out4, err4 = _install(c, pkg_other, g3, f1)
    c.check("S4_6k: different package_id still refuses with exit 3",
            rc4 == 3 and "package identity mismatch" in (out4 + err4).lower(),
            f"rc={rc4} {err4}")
    c.check("S4_6l: identity refusal is byte-level ZERO WRITE",
            before == G.sha_tree(g3))
    return c


# ===========================================================================
# S4_7 - W60 / Lead D5.2 UNFROZEN: battlemd:inplace is now IMPLEMENTED
# ===========================================================================

def case_S4_7(fx) -> object:
    c = G.Case("S4_7")
    finplace = _fsfile(c, "finplace.json", _f_inplace())
    sb = _fsfile(c, "s0.json", _s0())
    d = _design("S4Inplace")

    code = f"""
import sys, json
sys.path.insert(0, {str(G.V14_ROOT)!r})
from ra2forge import feature_subset as FS
p = FS.resolve(FS.load_json({str(finplace)!r}), FS.load_json({str(sb)!r}))
row = [r for r in p["files"] if r["name"] == "BATTLEMD.INI"][0]
print(json.dumps({{
  "coupling_passed": p["coupling_passed"],
  "shipped": p["shipped"],
  "row": {{k: row[k] for k in ("name","action","original_absent",
                             "backup_slot","uninstall")}},
}}))
"""
    rc, out, err = c.run_python(G.V14_ROOT, code, "S4-inplace-pure-plan")
    try: t = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError): t = {}
    c.check("S4_7a: pure planner still EXPRESSES battlemd:inplace",
            rc == 0 and t.get("coupling_passed") is True
            and "BATTLEMD.INI" in t.get("shipped", []), str(t))
    c.check("S4_7b: inplace plan row is REPLACE / backup / RESTORE",
            t.get("row", {}).get("action") == "REPLACE"
            and t.get("row", {}).get("backup_slot")
            == "BATTLEMD.INI.ra2forge.bak"
            and t.get("row", {}).get("uninstall", {}).get("action") == "RESTORE",
            str(t.get("row")))
    rc2, out2, err2 = c.run_module(
        G.V14_ROOT, ["resolve", "--feature-set", str(finplace),
                     "--sandbox", str(sb)], "v15-resolve-inplace")
    c.check("S4_7c: the pure 'resolve' CLI is UNCHANGED (exit 0)",
            rc2 == 0 and "BATTLEMD.INI" in out2, err2)

    code2 = f"""
import sys, json
sys.path.insert(0, {str(G.V14_ROOT)!r})
from ra2forge import resolve_integration as RI
slot = RI.MODE_RESERVATIONS["battlemd:inplace"]
print(json.dumps({{
  "support": RI.MODE_SUPPORT["battlemd"],
  "status": slot["status"],
  "slot": slot["plan_layer_slot"],
  "surface": slot["change_surface"],
  "exit": slot["explicit_refusal_exit_code"],
  "code": slot["explicit_refusal_reason_code"],
}}))
"""
    rc3, out3, err3 = c.run_python(G.V14_ROOT, code2, "S4-inplace-reservation")
    try: r = json.loads(out3.strip().splitlines()[-1])
    except (ValueError, IndexError): r = {}
    c.check("S4_7d: MODE_SUPPORT marks inplace SUPPORTED (Lead D5.2 unfrozen)",
            rc3 == 0 and r.get("support", {}).get("inplace") == "SUPPORTED"
            and r.get("status") == "IMPLEMENTED", str(r.get("support")))
    c.check("S4_7e: reserved plan-layer slot has the right shape",
            r.get("slot", {}).get("shipped_target") == "BATTLEMD.INI"
            and r.get("slot", {}).get("plan_action_when_present") == "REPLACE"
            and r.get("slot", {}).get("backup_slot")
            == "BATTLEMD.INI.ra2forge.bak"
            and r.get("slot", {}).get("uninstall_action") == "RESTORE",
            str(r.get("slot")))
    c.check("S4_7f: W60 change surface is CLOSED and names the rewriter",
            1 <= len(r.get("surface", [])) <= 6
            and any("battlemd_inplace.py" in x for x in r.get("surface", [])),
            str(r.get("surface")))
    c.check("S4_7g: D5.2 exit-25 refusal is RETIRED (kept as legacy data only)",
            r.get("exit") == 25 and r.get("code") == "BATTLEMD_INPLACE_REFUSED")

    code3 = f"""
import sys, json
sys.path.insert(0, {str(G.V14_ROOT)!r})
from ra2forge import resolve_integration as RI
F = RI.load_json_obj({str(finplace)!r}, "feature-set")
S = RI.default_build_sandbox_state(F)
try:
    RI.run_resolve(F, S)
    print(json.dumps({{"raised": False}}))
except RI.ResolveIntegrationRefused as e:
    print(json.dumps({{"raised": True, "exit": e.exit_code,
                       "code": e.reason_code}}))
"""
    rc6, out6, err6 = c.run_python(G.V14_ROOT, code3, "S4-run-resolve-gate")
    try: g6 = json.loads(out6.strip().splitlines()[-1])
    except (ValueError, IndexError): g6 = {}
    c.check("S4_7h: run_resolve() NO LONGER refuses (D5.2 unfrozen)",
            rc6 == 0 and g6.get("raised") is False, str(g6))
    fmin = _fsfile(c, "finplace_min.json", _f_inplace_min())
    rc_b, out_b, err_b, pkg_i = _build(
        c, d, "inplace_w60", ["--feature-set", str(fmin)])
    c.check("S4_7i: W60 build with inplace SUCCEEDS and emits BATTLEMD.INI",
            rc_b == 0 and (pkg_i / "BATTLEMD.INI").is_file(),
            f"rc={rc_b} {err_b}")
    c.check("S4_7j: NO BATTLEMD98.INI in an inplace package (route (b) excluded)",
            not (pkg_i / "BATTLEMD98.INI").exists())
    return c


# ===========================================================================
# S4_8 - backward compatibility (SHA-256) + source delta + hygiene
# ===========================================================================

def case_S4_8(fx) -> object:
    c = G.Case("S4_8")
    d = _design("S4Compat")
    dp = c.dir / "design_compat.json"
    _w(dp, d)
    o13 = c.dir / "out_v13"
    o14 = c.dir / "out_v14"
    rc13, _o13, e13 = c.run_module(
        G.V13_REF_ROOT, ["build", "--design", str(dp), "--out", str(o13)],
        "v13-ref-default-build")
    rc14, _o14, e14 = c.run_module(
        G.V14_ROOT, ["build", "--design", str(dp), "--out", str(o14)],
        "v14-default-build")
    p13 = o13 / d["campaign"]["name"]
    p14 = o14 / d["campaign"]["name"]
    t13, t14 = G.sha_tree(p13), G.sha_tree(p14)

    def _tree_map(tree):
        out = {}
        for ln in tree.splitlines():
            sha, size, rel = ln.split(None, 2)
            out[rel.strip()] = (sha, int(size))
        return out

    m13, m14 = _tree_map(t13), _tree_map(t14)
    names = sorted(set(m13) | set(m14))
    rows = ["W46 S4 backward-compatibility SHA-256 table (v14 vs v13)",
            "build: NO --feature-set / NO new switch (default path)",
            f"v13 (READ-ONLY ref): {G.V13_REF_ROOT}",
            f"v14 (this card):     {G.V14_ROOT}",
            "",
            f"{'file':40s} {'bytes':>8s}  {'v13 sha256':64s}  "
            f"{'v14 sha256':64s}  match"]
    n_match = 0
    for rel in names:
        s13 = m13.get(rel, ("<missing>", -1))
        s14 = m14.get(rel, ("<missing>", -1))
        match = s13 == s14
        n_match += int(match)
        rows.append(f"{rel:40s} {s13[1]:8d}  {s13[0]:64s}  "
                    f"{s14[0]:64s}  {'MATCH' if match else 'DIFF'}")
    rows += ["", f"files: {len(names)}  identical: {n_match}  "
             f"different: {len(names) - n_match}",
             f"VERDICT: {'IDENTICAL' if t13 == t14 else 'DIFFERENT'}"]
    table = "\n".join(rows) + "\n"
    (G.OUT / "SHA256_COMPAT_V14_V13.txt").write_text(table, encoding="utf-8")
    c.note("v14<->v13 SHA-256 table written to out/SHA256_COMPAT_V14_V13.txt:\n"
           + table)
    c.check("S4_8a: v13 + v14 default builds both exit 0",
            rc13 == 0 and rc14 == 0, f"{rc13}/{rc14} {e13} {e14}")
    c.check("S4_8b: NO new switch => build BYTE-FOR-BYTE IDENTICAL to v13",
            t13 == t14 and bool(t13.splitlines()), f"v13:\n{t13}\n\nv14:\n{t14}")
    c.check("S4_8c: all 8 expected artifacts MATCH",
            len(names) == 8 and n_match == len(names), str(names))
    c.check("S4_8d: neither build emits ra2md.csf / MAPSELMD.INI",
            "ra2md.csf" not in t13 and "MAPSELMD.INI" not in t13
            and "ra2md.csf" not in t14 and "MAPSELMD.INI" not in t14)

    # source delta (v13 -> v14) is additive + localised
    # W60: source delta is v14 -> v15 (both LOCAL to this card).
    # W81 guard restore: the delta walk is back to the WHOLE package root
    # (undoing W77's ra2forge/-only narrowing, which had dropped the
    # "no new file may appear at the package root" guard).  The
    # lead-prescribed product doc docs/ONE_PACKAGE_AT_A_TIME.md (W77 task
    # step 4) is now listed EXPLICITLY in expected_added below -- admitting
    # the file belongs in the package instead of shrinking the scan.  Any
    # OTHER stray file anywhere under the package root (v14ref or v16 side)
    # flips S4_8e via added/removed, which is exactly the guard this
    # restores.  The three S4_8 check() texts/verdicts below stay verbatim
    # W60/W77-inherited; the desc's "(3 changed + 2 added)" counts the
    # SOURCE files, matching the historical naming.
    v14ref = G.V14_REF_ROOT
    v14files = {p.relative_to(v14ref).as_posix():
                G.hashlib.sha256(p.read_bytes()).hexdigest()
                for p in v14ref.rglob("*") if p.is_file()}
    v15files = {p.relative_to(G.V14_ROOT).as_posix():
                G.hashlib.sha256(p.read_bytes()).hexdigest()
                for p in G.V14_ROOT.rglob("*") if p.is_file()}
    changed = sorted(k for k in v14files if k in v15files
                     and v14files[k] != v15files[k])
    added = sorted(k for k in v15files if k not in v14files)
    removed = sorted(k for k in v14files if k not in v15files)
    (G.OUT / "V15_SOURCE_DELTA.json").write_text(
        json.dumps({"changed": changed, "added": added, "removed": removed},
                   indent=2) + "\n", encoding="utf-8")
    c.note("changed v14->v15 source files: " + json.dumps(changed))
    c.note("added v14->v15 files: " + json.dumps(added))
    expected_changed = {"ra2forge/builder.py", "ra2forge/install.py",
                        "ra2forge/resolve_integration.py"}
    # W81: docs/ONE_PACKAGE_AT_A_TIME.md added EXPLICITLY (whole-package
    # whitelist); everything else under the package root stays forbidden.
    # Order matters: `added` is sorted(), so the whitelist is kept in the
    # same lexicographic order.
    expected_added = ["docs/ONE_PACKAGE_AT_A_TIME.md",
                      "ra2forge/battlemd_inplace.py",
                      "ra2forge/data/BATTLEMD.OFFICIAL.INI"]
    c.check("S4_8e (W60): v14->v15 source delta is CLOSED (3 changed + 2 added)",
            set(changed) == expected_changed and added == expected_added
            and removed == [],
            f"changed={changed} added={added} removed={removed}")
    untouched = ["ra2forge/verify.py", "ra2forge/feature_subset.py",
                 "ra2forge/csf.py", "ra2forge/s3_contract.py",
                 "ra2forge/version_guard.py", "ra2forge/mapselmd.py",
                 "ra2forge/cli.py", "ra2forge/data/E1_KNOWN_GOOD.json",
                 "ra2forge/data/guard_decision_table.json"]
    c.check("S4_8f (W60): verify.py / pure planner / guard / CLI / data UNCHANGED "
            "(no other guard weakened)",
            all(v14files.get(k) == v15files.get(k) and k in v15files
                for k in untouched),
            str([k for k in untouched if v14files.get(k) != v15files.get(k)]))
    pyc = [p.relative_to(G.V14_ROOT).as_posix()
           for p in G.V14_ROOT.rglob("*")
           if p.is_file() and (p.suffix == ".pyc"
                               or "__pycache__" in p.parts)]
    c.check("S4_8g: NO __pycache__/*.pyc in the v14 delivery package",
            pyc == [], str(pyc))
    return c


S4_CASES = {
    "S4_1": case_S4_1, "S4_2": case_S4_2, "S4_3": case_S4_3,
    "S4_4": case_S4_4, "S4_5": case_S4_5, "S4_6": case_S4_6,
    "S4_7": case_S4_7, "S4_8": case_S4_8,
}


def _f_inplace_min(fsid="W60-S4-INPLACE-MIN") -> dict:
    """Minimal VALID inplace feature-set for the unfrozen write path."""
    return {
        "schema_version": "w42-s2-1", "kind": "feature_set",
        "feature_set_id": fsid,
        "features": {
            "maps": {"mode": "sideload",
                     "map_files": ["CP1.MAP", "CP2.MAP"],
                     "chain": ["CP1", "CP2"]},
            "battlemd": {"mode": "inplace", "scenario": "ECH01.MAP",
                         "description_ref": "raw"},
            "mix": {"mode": "repack",
                    "source_map_set": ["CP1.MAP", "CP2.MAP"],
                    "target_name": "expandmd98.mix"},
            "csf": {"mode": "off"},
            "mapselmd": {"mode": "off"},
        },
    }
