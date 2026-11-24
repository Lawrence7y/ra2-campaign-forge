#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W84 BUILD - offline, NO LOCK, NO gamemd.exe.

2 packages, both 60x60 TEMPERATE, RA2F_M1.MAP, EndOfGame=yes:

  pkg_df : DEFEAT ARM (the missing third terminal state).
           Player Russians = 1x TESLA (Soviet tesla coil, row 50 col 30) ONLY:
           no construction yard, no power plant, no units, no infantry.
           Enemy British = 30x MTNK (Grizzly) ALL mission=Hunt, rows
           38/40/42, cols 20..38 step 2 (10 per row).
           Objectives: text@1 ONLY -- NO win objective, NO survive.
           Builder auto-adds AllDestroyed(Russians)->Loser(8)
           (event ,11,0,8 / action ,2,0,8).
           WHY TESLA: W83c db v1 proved Hunt target acquisition IGNORES
           non-armed structures (tanks frozen 154 game-seconds vs 3 GAPOWR);
           W83c db v3 proved armed structures (ATESLA) ARE attacked and
           destroyed.  TESLA is the Soviet-native armed building (rulesmd
           section exists, W83c RULES_PROBE), so the Hunt tanks will destroy
           it => Russians reaches 0 units + 0 buildings => AllDestroyed =>
           defeat => EndOfGame => "restart this mission?" dialog
           (GUI:OK + GUI:Cancel).  Never clicked by the probe.

  pkg_wv : WIN CONTROL ARM (positive control for the classification).
           Forces swapped: Russians = NACNST + NAPOWR x2 + 30x MTNK (Guard,
           static); British = 1x GAPOWR @ (10,30) (unarmed, never attacked).
           Objectives: text@1 + survive(5) => win at frame ~= 15*5+90 = 165
           (W79 law).  Proves the probe classifies the victory score screen
           as victory_score_screen and NOT as defeat_restart_dialog.

Build command (proven W76/W78/W79/W83c):
  python -m ra2forge build --design <d> --out <o> --feature-set <fs>
run with the v15 patched package root as cwd.

Everything writes ONLY inside W84_defeat_dialog.  git is read-only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w84_lib as L
import w84_common as C

TAG = "build"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- layouts
DF_MY_BASE = [
    # armed Soviet tesla coil: the ONLY Russian object on the map.  Hunt-
    # acquirable (armed), unlike GAPOWR/GACNST (W83c db v1 lesson).
    {"owner": "Russians", "type": "TESLA", "row": 50, "col": 30},
]


def enemy_tanks_hunt():
    """30 British MTNK, ALL mission=Hunt, rows 38/40/42, cols 20..38 step 2."""
    out = []
    for row in (38, 40, 42):
        for col in range(20, 39, 2):
            out.append({"owner": "British", "type": "MTNK",
                        "row": row, "col": col, "mission": "Hunt"})
    assert len(out) == 30
    return out


WV_MY_STRUCTURES = [
    {"owner": "Russians", "type": "NACNST", "row": 50, "col": 30},
    {"owner": "Russians", "type": "NAPOWR", "row": 52, "col": 27},
    {"owner": "Russians", "type": "NAPOWR", "row": 52, "col": 33},
]


def my_tanks_guard():
    out = []
    for row in (42, 43, 44):
        for col in range(16, 44, 3):
            out.append({"owner": "Russians", "type": "MTNK",
                        "row": row, "col": col})
    assert len(out) == 30
    return out


WV_ENEMY_BASE = [
    {"owner": "British", "type": "GAPOWR", "row": 10, "col": 30},
]


def base_design(name, title, briefing):
    # campaign.name = PACKAGE FOLDER NAME emitted by ra2forge -> W84Probe
    return {
        "package": {"id": "org.ra2forge.w84." + name, "version": "1.0"},
        "campaign": {
            "id": "RA2F_W84",
            "name": "W84Probe",
            "description": "W84 defeat restart dialog live sample hunt",
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


def df_design():
    d = base_design("W84DefeatDialog",
                    "W84 df M1",
                    "W84 DEFEAT ARM. 1 Russian TESLA (armed, only object) vs "
                    "30 British MTNK all Hunt. NO win objective, NO survive. "
                    "Auto AllDestroyed(Russians)->Loser fires when the coil "
                    "dies => defeat restart dialog.")
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(DF_MY_BASE))
    m["units"] = enemy_tanks_hunt()
    m["objectives"] = [
        {"type": "text", "text": "W84 DF PROBE", "at_second": 1},
    ]
    return d


def wv_design():
    d = base_design("W84WinControl",
                    "W84 wv M1",
                    "W84 WIN CONTROL. Russians NACNST+NAPOWRx2+30 MTNK Guard "
                    "vs 1 British GAPOWR. Win = survive(5) only (frame ~165). "
                    "Positive control: score screen must NOT be classified as "
                    "the defeat dialog.")
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(WV_MY_STRUCTURES + WV_ENEMY_BASE))
    m["units"] = my_tanks_guard()
    m["objectives"] = [
        {"type": "text", "text": "W84 WV CTRL PROBE", "at_second": 1},
        {"type": "survive", "seconds": 5},
    ]
    return d


DESIGNS = {
    "df": df_design(),
    "wv": wv_design(),
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
    d["british_mtnk"] = t.count("British,MTNK")
    d["russian_tesla"] = t.count("Russians,TESLA")
    d["russian_nacnst"] = t.count("Russians,NACNST")
    d["russian_napowr"] = t.count("Russians,NAPOWR")
    d["british_gapowr"] = t.count("British,GAPOWR")
    d["hunt_mission"] = t.count(",Hunt,")
    # event/action serialization is WITHOUT trailing comma after last param
    d["winner_is_action"] = bool(re.search(r",1,0,8(?!\d)", t))
    d["loser_action"] = bool(re.search(r",2,0,8(?!\d)", t))
    d["all_destroyed_russians_event"] = bool(re.search(r",11,0,8(?!\d)", t))
    d["all_destroyed_british_event"] = bool(re.search(r",11,0,4(?!\d)", t))
    d["all_buildings_destroyed_british"] = bool(re.search(r",10,0,4(?!\d)", t))
    d["elapsed_1"] = bool(re.search(r",13,0,1(?!\d)", t))
    d["elapsed_5"] = bool(re.search(r",13,0,5(?!\d)", t))
    d["elapsed_55"] = bool(re.search(r",13,0,55(?!\d)", t))
    d["survive_tag"] = ("Objective: survive" in t)
    rep["map"] = d

    ms = (pkg / "MAPSELMD.INI").read_bytes()
    rep["mapselmd"] = {"size": len(ms), "sha256": sha(ms),
                       "scenario_m1": ms.count(b"Scenario=RA2F_M1.MAP")}

    # ---- generic assertions (both packages) ----
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
    assert d["loser_action"], d                       # auto lose trigger present
    assert d["all_destroyed_russians_event"], d       # event ,11,0,8
    assert d["elapsed_1"], d                          # text@1 present

    if label == "df":
        assert d["russian_tesla"] == 1, d
        assert d["russian_nacnst"] == 0 and d["russian_napowr"] == 0, d
        assert d["russian_mtnk"] == 0, d
        assert d["british_mtnk"] == 30 and d["hunt_mission"] == 30, d
        assert d["british_gapowr"] == 0, d
        # NO win objective at all: no WinnerIs action, no survive, no
        # destroy-anything events on the British house.
        assert not d["winner_is_action"], d
        assert not d["elapsed_5"] and not d["elapsed_55"], d
        assert not d["all_buildings_destroyed_british"], d
        assert not d["all_destroyed_british_event"], d
    elif label == "wv":
        assert d["russian_nacnst"] == 1 and d["russian_napowr"] == 2, d
        assert d["russian_mtnk"] == 30 and d["hunt_mission"] == 0, d
        assert d["british_gapowr"] == 1 and d["british_mtnk"] == 0, d
        assert d["elapsed_5"] and d["survive_tag"] and d["winner_is_action"], d
    rep["verdict"] = "PASS"
    sink.step("package_verify_" + label, **rep)
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build 2 packages: NO lock, NO gamemd.exe",
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
        for label, design in DESIGNS.items():
            dpath = C.WORK / ("w84_design_%s.json" % label)
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
            pkg = out_dir / "W84Probe"
            (pkg / "ra2forge_package.json").write_text(
                json.dumps({"tool": "ra2forge",
                            "package_id": "org.ra2forge.w84.%s" % label,
                            "package_version": "1.0"}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            rep["builds"].append({"label": label, "pkg": str(pkg),
                                  "exit_code": rec["exit_code"]})
            rep["verify"][label] = verify_pkg(sink, label, pkg)

        rep["w59_offsets"] = {"scen_ptr": "0x00A8B230",
                              "filename": "+0x125C", "stage_idx": "+0x35A0",
                              "end_of_game": "+0x34AC", "skip_score": "+0x34AE",
                              "skip_mapsel": "+0x34B0", "battle_idx": "+0x34CC",
                              "frame": "0x00A8ED84"}
        ok = True
        sink.step("build_result", ok=ok, n_packages=len(DESIGNS))
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
