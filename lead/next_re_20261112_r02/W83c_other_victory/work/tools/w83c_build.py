#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W83c BUILD - offline, NO LOCK, NO gamemd.exe.

5 packages, all 60x60 TEMPERATE, player Russians:

  TASK 1 (destroy_all_buildings)
    pkg_db  : exp  - 40 MTNK ALL Hunt vs 3 British GAPOWR (NO British units);
                     win = destroy_all_buildings(enemy=British); NO survive.
    pkg_dbc : ctrl - SAME layout/forces; win = survive(55) only.
    judgement: exp win frame << 915  =>  destroy_all_buildings fires.

  TASK 2 (destroy_building + living-enemy sub-question)
    pkg_tb  : exp  - 40 MTNK ALL Hunt vs 1 TAGGED British GAPOWR (tag w83c_tgt,
                     row 36 col 30, adjacent to the tank line) + 1 British E1
                     FAR away (row 5 col 18, static Guard);
                     win = destroy_building(structure_tag=w83c_tgt); NO survive.
                     => victory, if any, fires while the E1 is still alive.
    pkg_tbc : ctrl - SAME layout/forces; win = survive(55) only.
    judgement: exp win frame << 915 with E1 alive => "named building" semantics;
               win only after/with total annihilation or no win => implies
               all-enemy-dead semantics.

  TASK 3 (hunt_wave alone)
    pkg_hw  : 40 MTNK all static Guard vs 4 static British E1;
              objectives = text@1 + hunt_wave(house=British, at_second=3).
              NO win objective at all => builder emits NO win trigger.
              Expected: no victory screen ever (probe timeout).

Build command (proven W76/W78/W79):
  python -m ra2forge build --design <d> --out <o> --feature-set <fs>
run with the v15 patched package root as cwd.

Everything writes ONLY inside W83c_other_victory.  git is read-only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w83c_lib as L
import w83c_common as C

TAG = "build"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- layouts
RUSSIAN_STRUCTURES = [
    {"owner": "Russians", "type": "NACNST", "row": 50, "col": 30},
    {"owner": "Russians", "type": "NAPOWR", "row": 52, "col": 27},
    {"owner": "Russians", "type": "NAPOWR", "row": 52, "col": 33},
]


def tanks_hunt():
    """40 Russian MTNK, all mission=Hunt, rows 42..45, cols 16..43 step 3."""
    out = []
    for row in range(42, 46):
        for col in range(16, 44, 3):
            out.append({"owner": "Russians", "type": "MTNK",
                        "row": row, "col": col, "mission": "Hunt"})
    assert len(out) == 40
    return out


def tanks_guard():
    out = []
    for row in range(42, 46):
        for col in range(16, 44, 3):
            out.append({"owner": "Russians", "type": "MTNK",
                        "row": row, "col": col})
    assert len(out) == 40
    return out


DB_ENEMY_BUILDINGS = [
    # v2: ATESLA (Allied prism tower, ARMED) x3.  v1 used GAPOWR (defenseless)
    # and trip1 measured the Hunt tanks FROZEN for 154 game-seconds: RA2 Hunt
    # target acquisition ignores non-armed structures.  3 armed buildings are
    # still exactly "3 buildings, no enemy units".
    {"owner": "British", "type": "ATESLA", "row": 36, "col": 24},
    {"owner": "British", "type": "ATESLA", "row": 36, "col": 30},
    {"owner": "British", "type": "ATESLA", "row": 36, "col": 36},
]

TB_TARGET_BUILDING = [
    {"owner": "British", "type": "ATESLA", "row": 36, "col": 30,
     "tag": "w83c_tgt"},
]

# 1 British E1 far away (37+ rows from the tank line): still alive when the
# tagged building dies.  Static Guard (no mission field).
TB_FAR_ENEMY_INF = [
    {"owner": "British", "type": "E1", "row": 5, "col": 18},
]

HW_ENEMY_INF = [
    {"owner": "British", "type": "E1", "row": 36, "col": 24},
    {"owner": "British", "type": "E1", "row": 36, "col": 27},
    {"owner": "British", "type": "E1", "row": 36, "col": 30},
    {"owner": "British", "type": "E1", "row": 36, "col": 33},
]


def base_design(name, title, briefing):
    # campaign.name = PACKAGE FOLDER NAME emitted by ra2forge -> W83cProbe
    return {
        "package": {"id": "org.ra2forge.w83c." + name, "version": "1.0"},
        "campaign": {
            "id": "RA2F_W83",
            "name": "W83cProbe",
            "description": "W83c other victory conditions discriminating experiment",
            "side": "soviet",
        },
        "missions": [{
            "name": "RA2F_M1",
            "title": title,
            "briefing": briefing,
            "theater": "TEMPERATE",
            "size": [60, 60],
            "player": {"house": "Russians", "credits": 10000, "enemy_credits": 0},
            "waypoints": {"0": [50, 30], "1": [50, 30], "2": [10, 30]},
            "structures": [], "units": [], "infantry": [], "objectives": [],
        }],
    }


def db_design():
    d = base_design("W83cDestAllBldV2",
                    "W83c db M1",
                    "W83c TASK 1 exp v2. 40 Russian MTNK all Hunt vs 3 STATIC "
                    "British ATESLA (armed prism towers), no British units. "
                    "Win = destroy_all_buildings(British). NO survive objective.")
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(RUSSIAN_STRUCTURES + DB_ENEMY_BUILDINGS))
    m["units"] = tanks_hunt()
    m["objectives"] = [
        {"type": "text", "text": "W83c DB PROBE", "at_second": 1},
        {"type": "destroy_all_buildings", "enemy": "British"},
    ]
    return d


def dbc_design():
    d = base_design("W83cDestAllBldCtrl",
                    "W83c dbc M1",
                    "W83c TASK 1 ctrl. Same layout as db; win = survive(55) only.")
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(RUSSIAN_STRUCTURES + DB_ENEMY_BUILDINGS))
    m["units"] = tanks_hunt()
    m["objectives"] = [
        {"type": "text", "text": "W83c DB CTRL PROBE", "at_second": 1},
        {"type": "survive", "seconds": 55},
    ]
    return d


def tb_design():
    d = base_design("W83cDestBldgV2",
                    "W83c tb M1",
                    "W83c TASK 2 exp v2. 40 Russian MTNK all Hunt vs 1 TAGGED "
                    "British ATESLA (w83c_tgt, armed) + 1 FAR British E1 kept "
                    "alive. Win = destroy_building(w83c_tgt). NO survive.")
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(RUSSIAN_STRUCTURES + TB_TARGET_BUILDING))
    m["units"] = tanks_hunt()
    m["infantry"] = json.loads(json.dumps(TB_FAR_ENEMY_INF))
    m["objectives"] = [
        {"type": "text", "text": "W83c TB PROBE", "at_second": 1},
        {"type": "destroy_building", "structure_tag": "w83c_tgt"},
    ]
    return d


def tbc_design():
    d = base_design("W83cDestBldgCtrl",
                    "W83c tbc M1",
                    "W83c TASK 2 ctrl. Same layout as tb; win = survive(55) only.")
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(RUSSIAN_STRUCTURES + TB_TARGET_BUILDING))
    m["units"] = tanks_hunt()
    m["infantry"] = json.loads(json.dumps(TB_FAR_ENEMY_INF))
    m["objectives"] = [
        {"type": "text", "text": "W83c TB CTRL PROBE", "at_second": 1},
        {"type": "survive", "seconds": 55},
    ]
    return d


def hw_design():
    d = base_design("W83cHuntWave",
                    "W83c hw M1",
                    "W83c TASK 3. 40 static Russian MTNK vs 4 static British E1; "
                    "hunt_wave(British, at_second=3) only. NO win objective.")
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(RUSSIAN_STRUCTURES))
    m["units"] = tanks_guard()
    m["infantry"] = json.loads(json.dumps(HW_ENEMY_INF))
    m["objectives"] = [
        {"type": "text", "text": "W83c HW PROBE", "at_second": 1},
        {"type": "hunt_wave", "house": "British", "at_second": 3},
    ]
    return d


DESIGNS = {
    "db":  (db_design(),  "db"),
    "dbc": (dbc_design(), "dbc"),
    "tb":  (tb_design(),  "tb"),
    "tbc": (tbc_design(), "tbc"),
    "hw":  (hw_design(),  "hw"),
}


def verify_pkg(sink, label: str, pkg: Path) -> dict:
    rep = {"label": label, "pkg": str(pkg)}
    files = []
    for p in sorted(pkg.rglob("*"), key=lambda x: x.as_posix().lower()):
        if p.is_file():
            files.append({"rel": p.relative_to(pkg).as_posix(),
                          "size": p.stat().st_size, "sha256": L.sha256_file(p)})
    rep["files"] = files
    names = {f["rel"] for f in files}
    rep["has_battlemd_ini"] = "BATTLEMD.INI" in names
    rep["has_map"] = "RA2F_M1.MAP" in names
    rep["has_mapselmd"] = "MAPSELMD.INI" in names
    rep["has_mix"] = "expandmd98.mix" in names
    rep["has_package_json"] = "ra2forge_package.json" in names

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
    d["russian_mtnk"] = t.count("Russians,MTNK")
    d["russian_nacnst"] = t.count("Russians,NACNST")
    d["russian_napowr"] = t.count("Russians,NAPOWR")
    d["british_atsla"] = t.count("British,ATESLA")
    d["british_gapowr"] = t.count("British,GAPOWR")
    d["british_e1"] = t.count("British,E1")
    d["hunt_mission"] = t.count(",Hunt,")
    # event/action serialization is WITHOUT trailing comma after last param
    d["winner_is_action"] = bool(re.search(r",1,0,8(?!\d)", t))
    d["loser_action"] = bool(re.search(r",2,0,8(?!\d)", t))
    d["all_buildings_destroyed_british"] = bool(re.search(r",10,0,4(?!\d)", t))
    d["all_destroyed_british"] = bool(re.search(r",11,0,4(?!\d)", t))
    d["destroyed_by_any_event"] = bool(re.search(r",7,0,0(?!\d)", t))
    d["elapsed_1"] = bool(re.search(r",13,0,1(?!\d)", t))
    d["elapsed_3"] = bool(re.search(r",13,0,3(?!\d)", t))
    d["elapsed_55"] = bool(re.search(r",13,0,55(?!\d)", t))
    d["all_to_hunt_british"] = bool(re.search(r",6,0,4(?!\d)", t))
    d["raze_tag"] = ("Objective: raze British" in t)
    d["destroy_target_tag"] = ("Objective: destroy target" in t)
    d["survive_tag"] = ("Objective: survive" in t)
    d["hunt_tag"] = ("Enemy assault (British)" in t)
    d["tag_0C000000_count"] = len(re.findall(r"0C000000(?!\d)", t))
    rep["map"] = d

    ms = (pkg / "MAPSELMD.INI").read_bytes()
    rep["mapselmd"] = {"size": len(ms), "sha256": sha(ms),
                       "scenario_m1": ms.count(b"Scenario=RA2F_M1.MAP")}

    # ---- assertions ----
    assert rep["has_battlemd_ini"] and rep["has_map"] and rep["has_mapselmd"]
    assert rep["has_mix"] and rep["has_package_json"], rep
    assert rep["battlemd"]["ra2f_scenario"] == 1, rep["battlemd"]
    assert rep["battlemd"]["official_scenario"] == 0, rep["battlemd"]
    assert rep["battlemd"]["bare_lf"] == 0, rep["battlemd"]
    assert d.get("NextScenario") == "", d
    assert d.get("EndOfGame") == "yes", d
    assert d.get("SkipMapSelect") == "no", d
    assert "0,0,60,60" in d.get("Size", ""), d
    assert rep["mapselmd"]["scenario_m1"] >= 1, rep["mapselmd"]
    assert d["russian_mtnk"] == 40, d
    assert d["russian_nacnst"] == 1 and d["russian_napowr"] == 2, d
    assert d["loser_action"], d

    if label == "db":
        assert d["hunt_mission"] == 40, d
        assert d["british_atsla"] == 3 and d["british_e1"] == 0, d
        assert d["all_buildings_destroyed_british"], d
        assert not d["all_destroyed_british"], d
        assert not d["elapsed_55"], d
        assert d["raze_tag"] and d["winner_is_action"], d
    elif label == "dbc":
        assert d["hunt_mission"] == 40, d
        assert d["british_atsla"] == 3 and d["british_e1"] == 0, d
        assert d["elapsed_55"] and d["survive_tag"] and d["winner_is_action"], d
        assert not d["all_buildings_destroyed_british"], d
    elif label == "tb":
        assert d["hunt_mission"] == 40, d
        assert d["british_atsla"] == 1 and d["british_e1"] == 1, d
        assert d["destroyed_by_any_event"], d
        assert not d["all_buildings_destroyed_british"], d
        assert not d["all_destroyed_british"], d
        assert not d["elapsed_55"], d
        assert d["destroy_target_tag"] and d["winner_is_action"], d
        assert d["tag_0C000000_count"] >= 2, d
    elif label == "tbc":
        assert d["hunt_mission"] == 40, d
        assert d["british_atsla"] == 1 and d["british_e1"] == 1, d
        assert d["elapsed_55"] and d["survive_tag"] and d["winner_is_action"], d
        assert not d["destroyed_by_any_event"], d
        assert not d["destroy_target_tag"], d
        assert d["tag_0C000000_count"] >= 1, d   # structure carries the tag; no tag-linked trigger in ctrl
    elif label == "hw":
        assert d["british_e1"] == 4 and d["british_gapowr"] == 0, d
        assert d["hunt_mission"] == 0, d
        assert d["all_to_hunt_british"] and d["elapsed_3"] and d["elapsed_1"], d
        assert not d["winner_is_action"], d          # NO win trigger at all
        assert not d["elapsed_55"] and not d["survive_tag"], d
    rep["verdict"] = "PASS"
    sink.step("package_verify_" + label, **rep)
    return rep


def object_lines(t: str):
    """Object-placement lines only ([Structures]/[Units]/[Infantry] sections),
    for exp-vs-ctrl layout identity comparison."""
    want = {"[Structures]", "[Units]", "[Infantry]"}
    keep, cur = [], None
    for ln in t.splitlines():
        s = ln.strip()
        if s.startswith("["):
            cur = s if s in want else None
            continue
        if cur and s:
            keep.append(s)
    return sorted(keep)


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build 5 packages: NO lock, NO gamemd.exe",
                  v15=str(C.V15), feature_set=str(C.FEATURE_SET))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline build phase: %r" % residual)
        if C.lock_owner() != "lead":
            raise RuntimeError("lock owner not lead at offline phase: %r" % C.lock_read())

        rep["designs"] = {}
        rep["builds"] = []
        rep["verify"] = {}
        maps_text = {}
        for label, (design, _kind) in DESIGNS.items():
            dpath = C.WORK / ("w83c_design_%s.json" % label)
            dpath.write_text(json.dumps(design, ensure_ascii=False, indent=2),
                             encoding="utf-8")
            rep["designs"][label] = {
                "path": str(dpath),
                "n_units": len(design["missions"][0]["units"]),
                "n_inf": len(design["missions"][0]["infantry"]),
                "n_struct": len(design["missions"][0]["structures"]),
                "objectives": design["missions"][0]["objectives"],
            }
            out_dir = C.WORK / ("pkg_" + label)
            out_dir.mkdir(parents=True, exist_ok=True)
            rec = C.v15_cmd(sink, "build_" + label,
                            ["build", "--design", str(dpath), "--out", str(out_dir),
                             "--feature-set", str(C.FEATURE_SET)])
            if rec["exit_code"] != 0:
                raise RuntimeError("build %s exit %s: %s" %
                                   (label, rec["exit_code"], rec["stderr_tail"][-2500:]))
            pkg = out_dir / "W83cProbe"
            (pkg / "ra2forge_package.json").write_text(
                json.dumps({"tool": "ra2forge",
                            "package_id": "org.ra2forge.w83c.%s" % label,
                            "package_version": "1.0"}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            rep["builds"].append({"label": label, "pkg": str(pkg),
                                  "exit_code": rec["exit_code"]})
            rep["verify"][label] = verify_pkg(sink, label, pkg)
            maps_text[label] = (pkg / "RA2F_M1.MAP").read_bytes().decode("latin-1")

        # exp-vs-ctrl layout identity (object lines must be byte-equal)
        rep["layout_identity"] = {}
        for exp, ctrl in (("db", "dbc"), ("tb", "tbc")):
            a = object_lines(maps_text[exp])
            b = object_lines(maps_text[ctrl])
            rep["layout_identity"][exp + "_vs_" + ctrl] = {
                "identical_object_lines": (a == b),
                "n_lines": len(a),
            }
            assert a == b, rep["layout_identity"]

        rep["w59_offsets"] = {"scen_ptr": "0x00A8B230",
                              "filename": "+0x125C", "stage_idx": "+0x35A0",
                              "end_of_game": "+0x34AC", "skip_score": "+0x34AE",
                              "skip_mapsel": "+0x34B0", "battle_idx": "+0x34CC",
                              "frame": "0x00A8ED84"}
        ok = True
        sink.step("build_result", ok=ok, n_packages=5)
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
