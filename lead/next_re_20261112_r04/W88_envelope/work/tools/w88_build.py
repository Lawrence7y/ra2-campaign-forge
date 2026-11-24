#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W88 BUILD - offline, NO LOCK, NO gamemd.exe.  C-ladder (Lead pivot 2).

BASELINE = the W85 signed GREEN control arm geometry (trip_control_dose1500_static,
300.15 s all green, A8ED50 all zero, X87E8E0 constant): 100x100 TEMPERATE,
player Russians = NACNST(54,50) + NAPOWRx6 (56, col 46..56 step 2) + TESLAx12
(rows 61-63) + 300 MTNK Guard (rows 66-95, cols 32-50); enemy 3 houses
(British 2-17 / Confederation 42-57 / Arabs 82-97), each GAPOWR(row 8, col
c0+7) + 400 MTNK (rows 12-41).  Total declared 1522 objects.

Ladder (one variable each, all measured FROM the green baseline):
  C0  exact re-run of the green control (all Guard)          -> reproducibility
  C1  only British 30 MTNK -> Hunt (rest 1170 Guard)         -> minimal dose
  C2  all 1200 enemy MTNK -> Hunt                            -> positive control (crash expected, W85 P-arm analogue)
  C3  C2 + NAPOWR col spacing 2 -> 3 (foundation overlap removed; NOTE: changes footprint, not a pure single variable - documented)
  C4  C2 + map INI append [NAPOWR] Crewed=no (post-build byte edit of the
      BUILT PACKAGE map; ra2forge has no rules-override support.  CAVEAT:
      whether the engine honours a rules section in the scenario INI cannot be
      proven statically - documented in the report)
  C5  C2 + C3 + C4 (both mitigations)

Historical B-ladder entries (B0/B1/B2/B3, W84-df-based) are KEPT for the
already-built packages and trip archives; they are defeat-dialog arms, not
stability baselines (Lead correction 2026-11-14: W84 df was a deliberate
loss scenario, the "stable precedent" citation was the card author's error).

D4: every step's design JSON + built map/INI/mix are archived to
out/inputs/<step>/ at build time with sha256.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w88_lib as L
import w88_common as C

TAG = "build"

# ---- W85 control-arm geometry (signed green) --------------------------------
MAP_N = 100
NACNST_CELL = (54, 50)
NAPOWR_CELLS_STEP2 = [(56, 46), (56, 48), (56, 50), (56, 52), (56, 54), (56, 56)]
NAPOWR_CELLS_STEP3 = [(56, 46), (56, 49), (56, 52), (56, 55), (56, 58), (56, 61)]
TESLA_CELLS = [(62, 44), (62, 48), (62, 52), (62, 56),
               (63, 42), (63, 46), (63, 50), (63, 54), (63, 58),
               (61, 45), (61, 49), (61, 53)]
PLAYER_UNIT_GRID = (66, 95, 32, 50)
PLAYER_MTNK_N = 300
ENEMY_ZONE_COLS = {"British": (2, 17), "Confederation": (42, 57), "Arabs": (82, 97)}
ENEMY_UNIT_ROWS = (12, 41)
ENEMY_PER_HOUSE = 400
CREWED_OVERRIDE = ("[NAPOWR]\r\nCrewed=no\r\n")


def grid_slots(row0, row1, col0, col1):
    return [(r, c) for r in range(row0, row1 + 1) for c in range(col0, col1 + 1)]


def overlap_cells(cells):
    """2x2 footprint check: (r,c) covers rows r..r+1, cols c..c+1."""
    occ = set()
    for r, c in cells:
        for rr in (r, r + 1):
            for cc in (c, c + 1):
                if (rr, cc) in occ:
                    return (r, c)
                occ.add((rr, cc))
    return None


def base_design(step, title, briefing):
    return {
        "package": {"id": "org.ra2forge.w88." + step.lower(), "version": "1.0"},
        "campaign": {
            "id": "RA2F1",
            "name": "W88Probe",
            "description": "W88 C-ladder step " + step,
            "side": "soviet",
        },
        "missions": [{
            "name": "RA2F_M1",
            "title": title,
            "briefing": briefing,
            "theater": "TEMPERATE",
            "size": [MAP_N, MAP_N],
            "player": {"house": "Russians", "credits": 10000, "enemy_credits": 0},
            "waypoints": {"0": [52, 50], "1": [8, 50], "2": [8, 9]},
            "structures": [], "units": [], "infantry": [],
            "objectives": [{"type": "text", "text": "W88 %s PROBE" % step,
                            "at_second": 1}],
        }],
    }


def step_design(step):
    """C-ladder designs; B0-B3 kept verbatim for the archived packages."""
    if step == "B0":
        d = base_design("B0", "W88 B0 M1", "W84 df replica (60x60, 1 TESLA, "
                        "30 British Hunt, no infrastructure). DEFEAT arm by "
                        "design - NOT a stability baseline (Lead correction).")
        d["missions"][0]["size"] = [60, 60]
        d["missions"][0]["waypoints"] = {"0": [50, 30], "1": [50, 30], "2": [10, 30]}
        d["missions"][0]["structures"] = [{"owner": "Russians", "type": "TESLA",
                                           "row": 50, "col": 30}]
        d["missions"][0]["units"] = [
            {"owner": "British", "type": "MTNK", "row": r, "col": c,
             "mission": "Hunt"}
            for r in (38, 40, 42) for c in range(20, 39, 2)]
        return d
    if step in ("B0",) or step.startswith("B"):
        raise RuntimeError("B-ladder steps other than B0 were superseded by the "
                           "C-ladder; packages for B1-B3 remain archived in "
                           "out/inputs/ but are not rebuilt")
    # ---- C-ladder ----
    # NOTE (2026-11-14 14:01, Get-Date): after C1 (30 Hunt) CRASHED, the C3/C4/
    # C5 baseline was moved from C2 (1200 Hunt) to C1 (30 Hunt) per the
    # pre-registered "C1 crashes => dose-independent => go straight to C3/C4"
    # branch; a smaller single difference to the trip that actually crashes.
    napowr = NAPOWR_CELLS_STEP2
    hunt_british = 0
    hunt_all = False
    apply_crewed = False
    if step == "C0":
        pass
    elif step == "C1":
        hunt_british = 30
    elif step == "C2":
        hunt_all = True
    elif step == "C3":
        hunt_british = 30
        napowr = NAPOWR_CELLS_STEP3
    elif step == "C4":
        hunt_british = 30
        apply_crewed = True
    elif step == "C5":
        hunt_british = 30
        napowr = NAPOWR_CELLS_STEP3
        apply_crewed = True
    elif step == "C6":
        # envelope probe: C3 fix (spacing 3, no foundation overlap) at FULL
        # dose (all 1200 enemy Hunt) - the original card question: is
        # "infrastructure + sustained maximal engagement" sustainable once the
        # overlap is removed?
        hunt_all = True
        napowr = NAPOWR_CELLS_STEP3
    elif step == "C7":
        # crew-only probe at FULL dose: [NAPOWR] Crewed=no (foundation overlap
        # KEPT, step 2) + all 1200 Hunt.  Discriminates the C4 ambiguity left
        # by C1's stochastic crash: green here (vs W85 same-dose overlap+crewed
        # arms crashing) is behavioural proof the map rules override is
        # honoured AND that crew spawn is necessary for the crash.
        hunt_all = True
        apply_crewed = True
    elif step.startswith("CTRL_C"):
        pass   # paired control of C<base>: all Guard, same layout
    else:
        raise RuntimeError("unknown step %s" % step)

    title = "W88 %s M1" % step
    briefing = ("W88 C-ladder %s: W85 green control geometry; NAPOWR spacing "
                "step %d; Hunt units: British %d%s; Crewed override %s."
                % (step,
                   napowr[1][1] - napowr[0][1],
                   hunt_british,
                   " + all houses" if hunt_all else "",
                   "ON" if apply_crewed else "OFF"))
    d = base_design(step, title, briefing)
    m = d["missions"][0]
    m["structures"] = (
        [{"owner": "Russians", "type": "NACNST", "row": NACNST_CELL[0],
          "col": NACNST_CELL[1]}]
        + [{"owner": "Russians", "type": "NAPOWR", "row": r, "col": c}
           for r, c in napowr]
        + [{"owner": "Russians", "type": "TESLA", "row": r, "col": c}
           for r, c in TESLA_CELLS]
        + [{"owner": house, "type": "GAPOWR", "row": 8,
            "col": ENEMY_ZONE_COLS[house][0] + 7}
           for house in ENEMY_ZONE_COLS])
    units = []
    # player 300 MTNK Guard
    pslots = grid_slots(*PLAYER_UNIT_GRID)
    assert len(pslots) >= PLAYER_MTNK_N
    units += [{"owner": "Russians", "type": "MTNK", "row": r, "col": c,
               "mission": "Guard"} for r, c in pslots[:PLAYER_MTNK_N]]
    # enemy 3x400 MTNK; Hunt dose per step
    for house, (c0, c1) in ENEMY_ZONE_COLS.items():
        slots = grid_slots(ENEMY_UNIT_ROWS[0], ENEMY_UNIT_ROWS[1], c0, c1)
        assert len(slots) >= ENEMY_PER_HOUSE, (house, len(slots))
        for i, (r, c) in enumerate(slots[:ENEMY_PER_HOUSE]):
            hunt = hunt_all or (house == "British" and i < hunt_british)
            units.append({"owner": house, "type": "MTNK", "row": r, "col": c,
                          "mission": "Hunt" if hunt else "Guard"})
    m["units"] = units
    # NOTE: the frozen W85 TESLA grid is 2x2-overlapping by the naive check but
    # is the SIGNED GREEN baseline (engine accepted it, 300 s) - asserted only
    # for NAPOWR, the factor actually under test.
    ov_nap = overlap_cells([(s["row"], s["col"]) for s in m["structures"]
                            if s["type"] == "NAPOWR"])
    assert ov_nap is None or napowr == NAPOWR_CELLS_STEP2, \
        ("NAPOWR overlap at %r in %s with step3" % (ov_nap, step))
    return {"_design": d, "_napowr": napowr, "_hunt_british": hunt_british,
            "_hunt_all": hunt_all, "_crewed": apply_crewed}


def parse_step(step):
    if step.startswith("CTRL_C"):
        out = step_design("C" + step[6:])
        out["_design"]["package"]["id"] = "org.ra2forge.w88.ctrl." + step.lower()
        out["_design"]["campaign"]["description"] = \
            "W88 paired control of %s (all units Guard)" % step
        out["_design"]["missions"][0]["title"] = "W88 %s M1" % step
        out["_design"]["missions"][0]["briefing"] = (
            "W88 paired control of %s: identical map/layout/objects, every "
            "unit mission=Guard; expected zero engagement." % step)
        for u in out["_design"]["missions"][0]["units"]:
            u["mission"] = "Guard"
        # control expectations: zero Hunt regardless of the base step's dose
        out["_hunt_all"] = False
        out["_hunt_british"] = 0
        return out
    return step_design(step)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_crewed_override(pkg: Path):
    """C4/C5: append a rules-override section to the BUILT PACKAGE map.
    ra2forge has no rules-override design field; this is the documented
    alternative.  Whether the scenario INI is parsed through the rules
    database is NOT statically provable - recorded as a caveat."""
    p = pkg / "RA2F_M1.MAP"
    b = p.read_bytes()
    if b"CREWED_OVERRIDE_SENTINEL" in b:   # never happens; guard idempotence
        raise RuntimeError("unexpected sentinel")
    if b"[NAPOWR]" in b:
        raise RuntimeError("map already contains [NAPOWR] section")
    if not b.endswith(b"\r\n"):
        b += b"\r\n"
    b += CREWED_OVERRIDE.encode("ascii")
    p.write_bytes(b)
    return {"file": "RA2F_M1.MAP", "appended": CREWED_OVERRIDE.replace("\r\n", "\\r\\n"),
            "size": len(b), "sha256": sha(b)}


def verify_pkg(sink, step: str, pkg: Path, spec: dict) -> dict:
    design = spec["_design"]
    rep = {"step": step, "pkg": str(pkg)}
    files = []
    for p in sorted(pkg.rglob("*"), key=lambda x: x.as_posix().lower()):
        if p.is_file():
            files.append({"rel": p.relative_to(pkg).as_posix(),
                          "size": p.stat().st_size, "sha256": L.sha256_file(p)})
    rep["files"] = files
    names = {f["rel"] for f in files}
    assert {"BATTLEMD.INI", "RA2F_M1.MAP", "MAPSELMD.INI", "expandmd98.mix",
            "ra2forge_package.json"} <= names, names
    b = (pkg / "BATTLEMD.INI").read_bytes()
    rep["battlemd"] = {"size": len(b), "sha256": sha(b),
                       "bare_lf": b.count(b"\n") - b.count(b"\r\n"),
                       "ra2f_scenario": b.count(b"Scenario=RA2F_M1.MAP"),
                       "official_scenario": b.count(b"Scenario=SOV01umd.MAP")}
    t = (pkg / "RA2F_M1.MAP").read_bytes().decode("latin-1")
    d = {}
    for ln in t.splitlines():
        for k in ("NextScenario", "EndOfGame", "SkipMapSelect", "Size"):
            if ln.startswith(k + "="):
                d[k] = ln.split("=", 1)[1]
    d["russian_mtnk"] = t.count("=Russians,MTNK,")
    d["british_mtnk"] = t.count("=British,MTNK,")
    d["confederation_mtnk"] = t.count("=Confederation,MTNK,")
    d["arabs_mtnk"] = t.count("=Arabs,MTNK,")
    d["russian_tesla"] = t.count("=Russians,TESLA,")
    d["russian_nacnst"] = t.count("=Russians,NACNST,")
    d["russian_napowr"] = t.count("=Russians,NAPOWR,")
    d["gapowr_total"] = sum(t.count("=%s,GAPOWR," % h) for h in ENEMY_ZONE_COLS)
    d["hunt_mission"] = t.count(",Hunt,")
    d["guard_mission"] = t.count(",Guard,")
    d["winner_is_action"] = bool(re.search(r",1,0,8(?!\d)", t))
    d["loser_action"] = bool(re.search(r",2,0,8(?!\d)", t))
    d["all_destroyed_russians_event"] = bool(re.search(r",11,0,8(?!\d)", t))
    d["elapsed_1"] = bool(re.search(r",13,0,1(?!\d)", t))
    d["survive_tag"] = ("Objective: survive" in t)
    d["crewed_override_present"] = bool(re.search(
        r"\[NAPOWR\]\s*.*?Crewed=no", t, re.S))
    rep["map"] = d
    ms = (pkg / "MAPSELMD.INI").read_bytes()
    rep["mapselmd"] = {"size": len(ms), "sha256": sha(ms),
                       "scenario_m1": ms.count(b"Scenario=RA2F_M1.MAP")}

    is_b0 = (step == "B0")
    n = 60 if is_b0 else MAP_N
    assert rep["battlemd"]["ra2f_scenario"] == 1, rep["battlemd"]
    assert rep["battlemd"]["official_scenario"] == 0, rep["battlemd"]
    assert rep["battlemd"]["bare_lf"] == 0, rep["battlemd"]
    assert d.get("NextScenario") == "", d
    assert d.get("EndOfGame") == "yes", d
    assert d.get("SkipMapSelect") == "no", d
    assert "0,0,%d,%d" % (n, n) in d.get("Size", ""), d
    assert rep["mapselmd"]["scenario_m1"] >= 1, rep["mapselmd"]
    assert d["loser_action"] and d["all_destroyed_russians_event"], d
    assert d["elapsed_1"], d
    assert not d["survive_tag"] and not d["winner_is_action"], d
    if is_b0:
        assert d["russian_tesla"] == 1 and d["british_mtnk"] == 30, d
        assert d["hunt_mission"] == 30 and d["guard_mission"] == 0, d
        assert d["russian_nacnst"] == 0 and d["russian_napowr"] == 0, d
    else:
        # player side always present (guaranteed NOT a forced-loss scenario)
        assert d["russian_nacnst"] == 1, d
        assert d["russian_napowr"] == 6, d
        assert d["russian_tesla"] == 12, d
        assert d["russian_mtnk"] == PLAYER_MTNK_N, d
        assert d["gapowr_total"] == 3, d
        for house, want in (("british", ENEMY_PER_HOUSE),
                            ("confederation", ENEMY_PER_HOUSE),
                            ("arabs", ENEMY_PER_HOUSE)):
            assert d["%s_mtnk" % house] == want, (house, d)
        hunt_expected = (spec["_hunt_all"] and 3 * ENEMY_PER_HOUSE) \
            or (spec["_hunt_british"] or 0)
        assert d["hunt_mission"] == hunt_expected, (step, d["hunt_mission"])
        assert d["guard_mission"] == PLAYER_MTNK_N + 3 * ENEMY_PER_HOUSE \
            - hunt_expected, (step, d["guard_mission"])
        assert spec["_crewed"] == d["crewed_override_present"], (step, d)
        # NAPOWR spacing assertion (step2 -> overlap expected in engine terms,
        # no 2x2 assert; step3 -> strictly disjoint even on 2x2 assumption)
        nap = spec["_napowr"]
        assert nap == NAPOWR_CELLS_STEP2 or nap == NAPOWR_CELLS_STEP3, nap
        if nap == NAPOWR_CELLS_STEP3:
            assert overlap_cells(nap) is None, nap
    rep["verdict"] = "PASS"
    sink.step("package_verify_" + step, **rep)
    return rep


def archive_inputs(sink, step: str, design: dict, pkg: Path):
    adir = C.OUT / "inputs" / step
    adir.mkdir(parents=True, exist_ok=True)
    rows = []
    dpath = adir / ("w88_design_%s.json" % step)
    dpath.write_text(json.dumps(design, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    rows.append({"file": dpath.name, "sha256": L.sha256_file(dpath)})
    for name in ("RA2F_M1.MAP", "BATTLEMD.INI", "MAPSELMD.INI",
                 "expandmd98.mix", "ra2forge_package.json"):
        src = pkg / name
        if src.is_file():
            dst = adir / name
            dst.write_bytes(src.read_bytes())
            rows.append({"file": name, "sha256": L.sha256_file(dst),
                         "size": dst.stat().st_size})
    sink.step("inputs_archived", step=step, dir=str(adir), rows=rows)
    return rows


def main() -> int:
    steps = [s.strip().upper() for s in
             os.environ.get("W88_STEPS", "C0,C1,C2,C3,C4,C5").split(",") if s.strip()]
    build_steps = []
    for s in steps:
        spec = parse_step(s)
        build_steps.append((s, spec))
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build: NO lock, NO gamemd.exe; C-ladder on the "
                       "signed-green W85 control geometry (Lead pivot 2); "
                       "inputs archived per step (D4)", steps=steps,
                  v15=str(C.V15), feature_set=str(C.FEATURE_SET))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline build phase: %r" % residual)
        if C.lock_owner() not in ("lead", ""):
            raise RuntimeError("lock owner not lead at offline phase: %r" % C.lock_read())

        rep["designs"] = {}
        rep["builds"] = []
        rep["verify"] = {}
        rep["inputs"] = {}
        for step, spec in build_steps:
            design = spec["_design"]
            dpath = C.design_path(step)
            dpath.write_text(json.dumps(design, ensure_ascii=False, indent=2),
                             encoding="utf-8")
            rep["designs"][step] = {
                "path": str(dpath),
                "n_struct": len(design["missions"][0]["structures"]),
                "n_units": len(design["missions"][0]["units"]),
                "size": design["missions"][0]["size"],
                "hunt_british": spec["_hunt_british"],
                "hunt_all": spec["_hunt_all"],
                "crewed_override": spec["_crewed"],
            }
            out_dir = C.WORK / ("pkg_" + step)
            out_dir.mkdir(parents=True, exist_ok=True)
            rec = C.v15_cmd(sink, "build_" + step,
                            ["build", "--design", str(dpath), "--out", str(out_dir),
                             "--feature-set", str(C.FEATURE_SET)])
            if rec["exit_code"] != 0:
                raise RuntimeError("build %s exit %s: %s" %
                                   (step, rec["exit_code"], rec["stderr_tail"][-2500:]))
            pkg = C.pkg_path(step)
            assert pkg.is_dir(), pkg
            (pkg / "ra2forge_package.json").write_text(
                json.dumps({"tool": "ra2forge",
                            "package_id": design["package"]["id"],
                            "package_version": "1.0"}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            crewed_edit = None
            if spec["_crewed"]:
                crewed_edit = apply_crewed_override(pkg)
                sink.step("crewed_override_applied", step=step, **crewed_edit)
            rep["builds"].append({"step": step, "pkg": str(pkg),
                                  "exit_code": rec["exit_code"],
                                  "crewed_edit": crewed_edit})
            rep["verify"][step] = verify_pkg(sink, step, pkg, spec)
            rep["inputs"][step] = archive_inputs(sink, step, design, pkg)

        rep["w59_offsets"] = {"scen_ptr": "0x00A8B230",
                              "filename": "+0x125C", "stage_idx": "+0x35A0",
                              "end_of_game": "+0x34AC", "skip_score": "+0x34AE",
                              "skip_mapsel": "+0x34B0", "battle_idx": "+0x34CC",
                              "frame": "0x00A8ED84"}
        ok = True
        sink.step("build_result", ok=ok, n_packages=len(build_steps))
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / "BUILD_RESULT.json").write_text(
            json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
