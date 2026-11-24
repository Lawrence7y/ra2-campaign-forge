#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W85 BUILD - offline, NO LOCK, NO gamemd.exe.

Pilot 双臂（同图同布局同对象数，单变量 = 敌方 units mission 赋值）：

  pkg_pressure : 加压臂。敌 3 house（British/Confederation/Arabs）各
                 GAPOWR x1 + MTNK x400，全部 mission=Hunt —— 三路大兵团
                 同时向玩家推进，强制高强度交战。
  pkg_control  : 对照臂。同一张 100x100 TEMPERATE 图、同一布局、同一对象数，
                 唯一差异：敌方 MTNK mission=Guard（原地不动），预期零交战。

  共同：玩家 Russians = NACNST x1 + NAPOWR x6 + TESLA x12 + MTNK x300(全 Guard)。
  声明对象总数 = 319(玩家) + 3x401(敌) = 1522；其中 units 1500（>> W19 B″ 800 声明）。
  Objectives: text@1 ONLY（builder 自动加 AllDestroyed(Russians)->Loser(8)，
  单任务 EndOfGame=yes）。无 survive（survive 会提前触发胜利结束）。

  剂量依据：W19 已证 800 声明对象可加载运行；W84 df 已证 Hunt 单位无触发器
  自主接敌。若真机首趟异常退出/极端卡死 => 降规模 3x200（写进 PROGRESS）。

Build command (W84 已验证):
  python -m ra2forge build --design <d> --out <o> --feature-set <fs>
run with the v15 patched package root as cwd.

Everything writes ONLY inside W85_pressure.  git is read-only.
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
import w85_lib as L
import w85_common as C

TAG = "build"

# ---- 冻结的布局参数（两臂共用，代码同一函数生成）----
MAP_SIZE = [100, 100]
# 剂量参数化：默认 400/300（首趟崩溃后按预冻结预案降档，档位历史写 PROGRESS）。
# W85_DOSE_ENEMY / W85_DOSE_PLAYER 环境变量可覆盖；两臂必须同 dose（单变量=mission）。
ENEMY_MTNK_PER_HOUSE = int(os.environ.get("W85_DOSE_ENEMY", "400").strip() or "400")
PLAYER_MTNK_N = int(os.environ.get("W85_DOSE_PLAYER", "300").strip() or "300")
# W85_ENEMY_HOUSES: 逗号分隔的 house 白名单（缺省三 house）。单 house 探针 =
# W85_ENEMY_HOUSES="British"。两臂必须同一集合（单变量=mission）。
ENEMY_HOUSES = tuple(
    h.strip() for h in os.environ.get(
        "W85_ENEMY_HOUSES", "British,Confederation,Arabs").split(",") if h.strip())
ENEMY_ZONE_COLS = {"British": (2, 17), "Confederation": (42, 57), "Arabs": (82, 97)}
ENEMY_UNIT_ROWS = (12, 41)          # 敌方 MTNK 网格行范围
PLAYER_UNIT_GRID = (66, 95, 32, 50)  # 玩家 MTNK 网格 rows 66..95, cols 32..50

TESLA_N = int(os.environ.get("W85_TESLA_N", "12").strip() or "12")
NO_NACNST = os.environ.get("W85_NO_NACNST", "0").strip() == "1"
TESLA_CELLS = [(62, 44), (62, 48), (62, 52), (62, 56),
               (63, 42), (63, 46), (63, 50), (63, 54), (63, 58),
               (61, 45), (61, 49), (61, 53)][:TESLA_N]
NAPOWR_CELLS = [(56, 46), (56, 48), (56, 50), (56, 52), (56, 54), (56, 56)]
NACNST_CELL = (54, 50)


def grid_slots(row0, row1, col0, col1):
    """行优先网格槽位（含端点，spacing=1）。"""
    return [(r, c) for r in range(row0, row1 + 1) for c in range(col0, col1 + 1)]


def player_structures():
    out = []
    if not NO_NACNST:
        out.append({"owner": "Russians", "type": "NACNST", "row": NACNST_CELL[0],
                    "col": NACNST_CELL[1]})
    out += [{"owner": "Russians", "type": "NAPOWR", "row": r, "col": c}
            for r, c in NAPOWR_CELLS]
    out += [{"owner": "Russians", "type": "TESLA", "row": r, "col": c}
            for r, c in TESLA_CELLS]
    assert len(out) == (0 if NO_NACNST else 1) + 6 + TESLA_N
    return out


def enemy_structures():
    out = []
    for house in ENEMY_HOUSES:
        c0, _ = ENEMY_ZONE_COLS[house]
        mid = (c0 + 7)
        out.append({"owner": house, "type": "GAPOWR", "row": 8, "col": mid})
    assert len(out) == len(ENEMY_HOUSES)
    return out


def player_units():
    slots = grid_slots(PLAYER_UNIT_GRID[0], PLAYER_UNIT_GRID[1],
                       PLAYER_UNIT_GRID[2], PLAYER_UNIT_GRID[3])
    assert len(slots) >= PLAYER_MTNK_N, len(slots)
    return [{"owner": "Russians", "type": "MTNK", "row": r, "col": c,
             "mission": "Guard"} for r, c in slots[:PLAYER_MTNK_N]]


def enemy_units(mission):
    out = []
    for house in ENEMY_HOUSES:
        c0, c1 = ENEMY_ZONE_COLS[house]
        slots = grid_slots(ENEMY_UNIT_ROWS[0], ENEMY_UNIT_ROWS[1], c0, c1)
        assert len(slots) >= ENEMY_MTNK_PER_HOUSE, (house, len(slots))
        out += [{"owner": house, "type": "MTNK", "row": r, "col": c,
                 "mission": mission}
                for r, c in slots[:ENEMY_MTNK_PER_HOUSE]]
    return out


def base_design(name, title, briefing):
    return {
        "package": {"id": "org.ra2forge.w85." + name, "version": "1.0"},
        "campaign": {
            "id": "RA2F1",
            "name": "W85Probe",
            "description": "W85 pressure pilot: heavy force engagement vs static control",
            "side": "soviet",
        },
        "missions": [{
            "name": "RA2F_M1",
            "title": title,
            "briefing": briefing,
            "theater": "TEMPERATE",
            "size": list(MAP_SIZE),
            "player": {"house": "Russians", "credits": 10000, "enemy_credits": 0},
            "waypoints": {"0": [52, 50], "1": [8, 50], "2": [8, 9]},
            "structures": [], "units": [], "infantry": [], "objectives": [],
        }],
    }


def pressure_design():
    d = base_design("W85Pressure", "W85 pressure M1",
                    "W85 PRESSURE ARM. 3 enemy houses x400 Hunt MTNK converge "
                    "on the Russian base (300 Guard MTNK + 12 TESLA). "
                    "Forced heavy engagement, no win objective.")
    m = d["missions"][0]
    m["structures"] = player_structures() + enemy_structures()
    m["units"] = player_units() + enemy_units("Hunt")
    m["objectives"] = [{"type": "text", "text": "W85 PRESSURE PROBE",
                        "at_second": 1}]
    return d


def control_design():
    d = base_design("W85Control", "W85 control M1",
                    "W85 CONTROL ARM. Identical map/layout/object counts, "
                    "only change: enemy MTNK mission=Guard (static). "
                    "Expected zero engagement (0xA8ED50 ~0).")
    m = d["missions"][0]
    m["structures"] = player_structures() + enemy_structures()
    m["units"] = player_units() + enemy_units("Guard")
    m["objectives"] = [{"type": "text", "text": "W85 CONTROL PROBE",
                        "at_second": 1}]
    return d


DESIGNS = {
    "pressure": pressure_design(),
    "control": control_design(),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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
        for k in ("NextScenario", "EndOfGame", "SkipMapSelect", "Size",
                  "Official", "Player"):
            if ln.startswith(k + "="):
                d[k] = ln.split("=", 1)[1]
    d["declared_units_total"] = t.count("=Russians,MTNK,") \
        + t.count("=British,MTNK,") + t.count("=Confederation,MTNK,") \
        + t.count("=Arabs,MTNK,")
    d["russian_mtnk"] = t.count("=Russians,MTNK,")
    d["british_mtnk"] = t.count("=British,MTNK,")
    d["confederation_mtnk"] = t.count("=Confederation,MTNK,")
    d["arabs_mtnk"] = t.count("=Arabs,MTNK,")
    d["hunt_mission"] = t.count(",Hunt,")
    d["guard_mission"] = t.count(",Guard,")
    d["russian_tesla"] = t.count("=Russians,TESLA,")
    d["russian_nacnst"] = t.count("=Russians,NACNST,")
    d["russian_napowr"] = t.count("=Russians,NAPOWR,")
    d["gapowr_total"] = (t.count("=British,GAPOWR,") + t.count("=Confederation,GAPOWR,")
                         + t.count("=Arabs,GAPOWR,"))
    d["winner_is_action"] = bool(re.search(r",1,0,8(?!\d)", t))
    d["loser_action"] = bool(re.search(r",2,0,8(?!\d)", t))
    d["all_destroyed_russians_event"] = bool(re.search(r",11,0,8(?!\d)", t))
    d["elapsed_1"] = bool(re.search(r",13,0,1(?!\d)", t))
    d["survive_tag"] = ("Objective: survive" in t)
    rep["map"] = d

    ms = (pkg / "MAPSELMD.INI").read_bytes()
    rep["mapselmd"] = {"size": len(ms), "sha256": sha(ms),
                       "scenario_m1": ms.count(b"Scenario=RA2F_M1.MAP")}

    # ---- generic assertions ----
    assert rep["has_battlemd_ini"] and rep["has_map"] and rep["has_mapselmd"]
    assert rep["has_mix"] and rep["has_package_json"], rep
    assert rep["battlemd"]["ra2f_scenario"] == 1, rep["battlemd"]
    assert rep["battlemd"]["official_scenario"] == 0, rep["battlemd"]
    assert rep["battlemd"]["bare_lf"] == 0, rep["battlemd"]
    assert d.get("NextScenario") == "", d
    assert d.get("EndOfGame") == "yes", d
    assert d.get("SkipMapSelect") == "no", d
    assert "0,0,100,100" in d.get("Size", ""), d
    assert rep["mapselmd"]["scenario_m1"] >= 1, rep["mapselmd"]
    assert d["loser_action"], d
    assert d["all_destroyed_russians_event"], d
    assert d["elapsed_1"], d
    assert not d["survive_tag"], d
    assert not d["winner_is_action"], d
    # ---- 冻结的声明量（两臂完全一致，唯一差异 Hunt/Guard 计数）----
    assert d["russian_mtnk"] == PLAYER_MTNK_N, d
    for house in ENEMY_HOUSES:
        got = d.get("%s_mtnk" % house.lower(), 0)
        assert got == ENEMY_MTNK_PER_HOUSE, (house, got, d)
    assert d["declared_units_total"] == (PLAYER_MTNK_N
                                         + len(ENEMY_HOUSES) * ENEMY_MTNK_PER_HOUSE), d
    assert d["russian_tesla"] == TESLA_N, d
    assert d["russian_nacnst"] == (0 if NO_NACNST else 1), d
    assert d["russian_napowr"] == 6, d
    assert d["gapowr_total"] == len(ENEMY_HOUSES), d
    if label == "pressure":
        assert d["hunt_mission"] == len(ENEMY_HOUSES) * ENEMY_MTNK_PER_HOUSE, d
        assert d["guard_mission"] == PLAYER_MTNK_N, d
    elif label == "control":
        assert d["hunt_mission"] == 0, d
        assert d["guard_mission"] == PLAYER_MTNK_N \
            + len(ENEMY_HOUSES) * ENEMY_MTNK_PER_HOUSE, d
    rep["verdict"] = "PASS"
    sink.step("package_verify_" + label, **rep)
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build 2 packages: NO lock, NO gamemd.exe; "
                       "single variable = enemy units mission Hunt vs Guard; "
                       "frozen layout 100x100, units 1500, objects 1522",
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
        for label, design in DESIGNS.items():
            dpath = C.WORK / ("w85_design_%s.json" % label)
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
            pkg = out_dir / "W85Probe"
            (pkg / "ra2forge_package.json").write_text(
                json.dumps({"tool": "ra2forge",
                            "package_id": "org.ra2forge.w85.%s" % label,
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
