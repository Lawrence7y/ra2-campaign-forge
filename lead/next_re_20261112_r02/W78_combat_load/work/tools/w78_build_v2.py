#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W78 BUILD v2 — offline, NO LOCK, NO gamemd.exe.

Trip 1 (distant enemy, rows 8-14) produced a long-range STALEMATE: real combat
(craters / muzzle flash / smoke) but no side eliminated within 150 s, so the
annihilation win never fired.  v2 moves the SAME enemy force much closer to the
player base (rows 40-45) so the engagement is decisive and VISIBLE on camera.

Builds two variants of the v2 combat layout into SEPARATE directories, so the
v1 (trip 1) packages + evidence stay intact:
  * work/pkg_v2_annih/W78CombatLoad  : win = destroy_all_forces(British)
  * work/pkg_v2_time/W78CombatLoad   : win = survive(55)

Only writes inside W78_combat_load.  git is read-only.
"""
from __future__ import annotations

import hashlib
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w78_lib as L
import w78_common as C

TAG = "build_v2"
SURVIVE_SECONDS = 55

# (row, col) of the British tanks / infantry — close to the Russian tank line
# (rows 46-48, cols 25-35), inside the entry camera view.
V2_ENEMY_TANKS = [(42, 34), (42, 38), (42, 42), (44, 36), (44, 44), (40, 40)]
V2_ENEMY_INF = [(43, 32), (43, 38), (43, 44), (45, 34), (45, 42), (41, 36)]

DESIGN_V2 = C.WORK / "w78_design_v2.json"
DESIGN_V2_TIME = C.WORK / "w78_design_v2_time.json"
PKG_ANN2 = C.WORK / "pkg_v2_annih" / "W78CombatLoad"
PKG_TIME2 = C.WORK / "pkg_v2_time" / "W78CombatLoad"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_v2(sink):
    d = json.loads(C.DESIGN_ANN.read_text(encoding="utf-8"))
    m = d["missions"][0]
    et, ei = 0, 0
    for u in m["units"]:
        if u["owner"] == "British":
            u["row"], u["col"] = V2_ENEMY_TANKS[et]
            et += 1
    for u in m["infantry"]:
        if u["owner"] == "British":
            u["row"], u["col"] = V2_ENEMY_INF[ei]
            ei += 1
    assert et == len(V2_ENEMY_TANKS) and ei == len(V2_ENEMY_INF), (et, ei)
    m["title"] = "W78 Combat Load M1 v2 (close enemy)"
    m["briefing"] = ("W78 REAL COMBAT LOAD v2. Enemy assault force starts close "
                     "to your base. Destroy ALL British forces (annihilation variant).")
    DESIGN_V2.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    dt = json.loads(json.dumps(d))
    mt = dt["missions"][0]
    new = []
    for o in mt["objectives"]:
        if o.get("type") == "destroy_all_forces":
            new.append({"type": "survive", "seconds": SURVIVE_SECONDS})
        else:
            new.append(o)
    mt["objectives"] = new
    mt["title"] = "W78 Combat Load M1 v2 (close enemy, time-trigger fallback)"
    mt["briefing"] = ("W78 REAL COMBAT LOAD v2 (time variant). Enemy assault force "
                      "starts close to your base; survive 55 s of real combat.")
    DESIGN_V2_TIME.write_text(json.dumps(dt, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    sink.step("v2_designs_written", annih=str(DESIGN_V2), time=str(DESIGN_V2_TIME),
              enemy_tanks=V2_ENEMY_TANKS, enemy_inf=V2_ENEMY_INF,
              objectives_annih=m["objectives"], objectives_time=new)
    return DESIGN_V2, DESIGN_V2_TIME


def build_one(sink, label, design, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = C.v15_cmd(sink, "build_v2_" + label,
                    ["build", "--design", str(design), "--out", str(out_dir),
                     "--feature-set", str(C.FEATURE_SET)])
    pkg = out_dir / "W78CombatLoad"
    if rec["exit_code"] != 0:
        raise RuntimeError("build v2 %s exit %s: %s" %
                           (label, rec["exit_code"], rec["stderr_tail"][-2000:]))
    (pkg / "ra2forge_package.json").write_text(
        json.dumps({"tool": "ra2forge",
                    "package_id": "org.ra2forge.w78.combatload.v2.%s" % label,
                    "package_version": "1.0"}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return {"label": label, "pkg": str(pkg), "exit_code": rec["exit_code"]}


def verify(sink, label, pkg, expect_annih):
    rep = {"label": label, "pkg": str(pkg)}
    b = (pkg / "BATTLEMD.INI").read_bytes()
    rep["battlemd"] = {"size": len(b), "sha256": sha(b),
                       "sov1_scenario": b.count(b"Scenario=RA2F_M1.MAP"),
                       "official_scenario": b.count(b"Scenario=SOV01umd.MAP"),
                       "bare_lf": b.count(b"\n") - b.count(b"\r\n")}
    t = (pkg / "RA2F_M1.MAP").read_bytes().decode("latin-1")
    d = {"NextScenario": "", "EndOfGame": "", "SkipMapSelect": "", "MapSize": ""}
    for ln in t.splitlines():
        if ln.startswith("Size="):
            d["MapSize"] = ln.split("=", 1)[1]
        for k in ("NextScenario", "EndOfGame", "SkipMapSelect"):
            if ln.startswith(k + "="):
                d[k] = ln.split("=", 1)[1]
    d["units_count"] = t.count("British,MTNK")
    d["inf_count"] = t.count("British,E1")
    d["hunt_mission"] = t.count(",Hunt,")
    d["all_destroyed_event"] = (",11,0,4" in t)
    d["elapsed_55_event"] = (",13,0,55" in t)
    d["all_to_hunt_action"] = (",6,0,4" in t)
    d["reveal_action"] = (",16," in t)
    d["winner_is_action"] = (",1,0,8" in t)
    rep["map"] = d
    assert rep["battlemd"]["sov1_scenario"] == 1 and rep["battlemd"]["official_scenario"] == 0
    assert rep["battlemd"]["bare_lf"] == 0
    assert d["NextScenario"] == "" and d["EndOfGame"] == "yes" and d["SkipMapSelect"] == "no"
    assert "0,0,60,60" in d["MapSize"]
    assert d["units_count"] == 6 and d["inf_count"] == 6 and d["hunt_mission"] >= 12
    assert d["all_to_hunt_action"] and d["reveal_action"] and d["winner_is_action"]
    if expect_annih:
        assert d["all_destroyed_event"] and not d["elapsed_55_event"], d
    else:
        assert d["elapsed_55_event"] and not d["all_destroyed_event"], d
    rep["verdict"] = "PASS"
    sink.step("package_verify_v2_" + label, **rep)
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build v2 (close enemy): NO lock, NO gamemd.exe")
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline phase: %r" % residual)
        da, dt = make_v2(sink)
        rep["builds"] = [build_one(sink, "annih", da, C.WORK / "pkg_v2_annih"),
                         build_one(sink, "time", dt, C.WORK / "pkg_v2_time")]
        rep["verify"] = [verify(sink, "annih", PKG_ANN2, True),
                         verify(sink, "time", PKG_TIME2, False)]
        rep["layout_v2"] = {
            "change_from_v1": "British units moved from rows 8-14 to rows 40-45 (close to Russian base)",
            "enemy_tanks": V2_ENEMY_TANKS, "enemy_infantry": V2_ENEMY_INF,
            "win_annih": "destroy_all_forces(British) -> AllDestroyed(4) -> WinnerIs(8)",
            "win_time": "survive(55) -> ElapsedTime(55) -> WinnerIs(8)",
        }
        ok = True
        sink.step("build_v2_result", ok=ok, **rep["layout_v2"])
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / "BUILD_V2_RESULT.json").write_text(
            json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
