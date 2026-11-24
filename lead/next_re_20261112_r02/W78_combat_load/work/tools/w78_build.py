#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W78 BUILD — offline, NO LOCK, NO gamemd.exe.

Builds TWO package variants of the SAME 60x60 real-combat map:
  * annih : win = destroy_all_forces(British)   [PRIMARY, Task 2]
  * time  : win = survive(55)                   [FALLBACK, same combat load]

Both via the proven W76 command:
  python -m ra2forge build --design <design> --out <out> --feature-set <fs>
run with the v15 patched package root as cwd (battlemd.mode=inplace emits the
[SOV1]-rewritten BATTLEMD.INI; mapselmd.mode=clone_append emits MAPSELMD.INI).

Everything writes ONLY inside W78_combat_load.  git is read-only.
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

TAG = "build"

SURVIVE_SECONDS = 55


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_time_design(sink) -> Path:
    """Same combat layout, but the win objective becomes survive(55)."""
    d = json.loads(C.DESIGN_ANN.read_text(encoding="utf-8"))
    objs = d["missions"][0]["objectives"]
    new = []
    for o in objs:
        if o.get("type") == "destroy_all_forces":
            new.append({"type": "survive", "seconds": SURVIVE_SECONDS})
        else:
            new.append(o)
    d["missions"][0]["objectives"] = new
    d["missions"][0]["title"] = "W78 Combat Load M1 (time-trigger fallback)"
    d["missions"][0]["briefing"] = (
        "W78 REAL COMBAT LOAD (time variant). Both sides armed; enemy hunts "
        "your base; survive 55 seconds under real combat load.")
    C.DESIGN_TIME.write_text(json.dumps(d, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    sink.step("time_design_written", path=str(C.DESIGN_TIME),
              objectives=new)
    return C.DESIGN_TIME


def build_one(sink, label: str, design: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    rec = C.v15_cmd(sink, "build_" + label,
                    ["build", "--design", str(design), "--out", str(out_dir),
                     "--feature-set", str(C.FEATURE_SET)])
    pkg = out_dir / "W78CombatLoad"
    if rec["exit_code"] != 0:
        raise RuntimeError("build %s exit %s: %s" %
                           (label, rec["exit_code"], rec["stderr_tail"][-2000:]))
    # package identity (v15 install's package-identity gate needs it)
    (pkg / "ra2forge_package.json").write_text(
        json.dumps({"tool": "ra2forge",
                    "package_id": "org.ra2forge.w78.combatload.%s" % label,
                    "package_version": "1.0"}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return {"label": label, "design": str(design), "out": str(out_dir),
            "pkg": str(pkg), "exit_code": rec["exit_code"],
            "stdout_tail": rec["stdout_tail"][-3000:]}


def verify_pkg(sink, label: str, pkg: Path, expect_annih: bool) -> dict:
    rep = {"label": label, "pkg": str(pkg)}
    files = []
    for p in sorted(pkg.rglob("*"), key=lambda x: x.as_posix().lower()):
        if p.is_file():
            files.append({"rel": p.relative_to(pkg).as_posix(),
                          "size": p.stat().st_size, "sha256": L.sha256_file(p)})
    rep["files"] = files
    names = {f["rel"] for f in files}
    rep["has_battlemd_ini"] = "BATTLEMD.INI" in names
    rep["has_no_battlemd98"] = "BATTLEMD98.INI" not in names
    rep["has_map"] = "RA2F_M1.MAP" in names
    rep["has_mapselmd"] = "MAPSELMD.INI" in names
    rep["has_mix"] = "expandmd98.mix" in names
    rep["has_package_json"] = "ra2forge_package.json" in names

    b = (pkg / "BATTLEMD.INI").read_bytes()
    rep["battlemd"] = {"size": len(b), "sha256": sha(b),
                       "crlf": b.count(b"\r\n"),
                       "bare_lf": b.count(b"\n") - b.count(b"\r\n"),
                       "sov1_scenario": b.count(b"Scenario=RA2F_M1.MAP"),
                       "official_scenario": b.count(b"Scenario=SOV01umd.MAP")}

    t = (pkg / "RA2F_M1.MAP").read_bytes().decode("latin-1")
    d = {}
    for ln in t.splitlines():
        if ln.startswith("NextScenario="):
            d["NextScenario"] = ln.split("=", 1)[1]
        elif ln.startswith("EndOfGame="):
            d["EndOfGame"] = ln.split("=", 1)[1]
        elif ln.startswith("SkipMapSelect="):
            d["SkipMapSelect"] = ln.split("=", 1)[1]
        elif ln.startswith("Size="):
            d["MapSize"] = ln.split("=", 1)[1]
    d["has_nacnst"] = "NACNST" in t
    d["has_mtnk_count"] = t.count("MTNK")
    d["british_units"] = t.count("British,")
    d["hunt_mission"] = t.count(",Hunt,")
    d["elapsed_time_event"] = (",13," in t)
    d["all_destroyed_event"] = (",11," in t)
    d["all_to_hunt_action"] = (",6," in t)
    d["winner_is_action"] = (",1," in t)
    d["survive_tag"] = ("Objective: survive" in t)
    d["destroy_tag"] = ("Objective: destroy" in t)
    d["reveal_action"] = (",16," in t)
    rep["map"] = d

    ms = (pkg / "MAPSELMD.INI").read_bytes()
    rep["mapselmd"] = {"size": len(ms), "sha256": sha(ms),
                       "crlf": ms.count(b"\r\n"),
                       "bare_lf": ms.count(b"\n") - ms.count(b"\r\n"),
                       "scenario_m1": ms.count(b"Scenario=RA2F_M1.MAP")}

    # assertions
    assert rep["has_battlemd_ini"] and rep["has_no_battlemd98"], rep
    assert rep["has_map"] and rep["has_mapselmd"] and rep["has_mix"] and rep["has_package_json"], rep
    assert rep["battlemd"]["sov1_scenario"] == 1, rep["battlemd"]
    assert rep["battlemd"]["official_scenario"] == 0, rep["battlemd"]
    assert rep["battlemd"]["bare_lf"] == 0, rep["battlemd"]
    assert d["NextScenario"] == "", d
    assert d["EndOfGame"] == "yes", d
    assert d["SkipMapSelect"] == "no", d
    assert "0,0,60,60" in d.get("MapSize", ""), d
    assert d["has_nacnst"] and d["has_mtnk_count"] >= 10, d
    assert d["british_units"] >= 10, d
    assert d["hunt_mission"] >= 10, d
    assert d["all_to_hunt_action"], d
    assert d["reveal_action"], d
    assert rep["mapselmd"]["scenario_m1"] >= 1, rep["mapselmd"]
    if expect_annih:
        assert d["all_destroyed_event"] and d["destroy_tag"], d
        assert not d["survive_tag"], d
    else:
        assert d["elapsed_time_event"] and d["survive_tag"], d
        assert not d["destroy_tag"], d
    rep["verdict"] = "PASS"
    sink.step("package_verify_" + label, **rep)
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build: NO lock taken, NO gamemd.exe launched",
                  v15=str(C.V15), feature_set=str(C.FEATURE_SET))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline phase: %r" % residual)

        tdesign = make_time_design(sink)

        b_ann = build_one(sink, "annih", C.DESIGN_ANN, C.WORK / "pkg_annih")
        b_time = build_one(sink, "time", tdesign, C.WORK / "pkg_time")
        rep["builds"] = [b_ann, b_time]

        v_ann = verify_pkg(sink, "annih", C.PKG_ANN, expect_annih=True)
        v_time = verify_pkg(sink, "time", C.PKG_TIME, expect_annih=False)
        rep["verify"] = [v_ann, v_time]

        # W59 observation-point reference (transcribed from W63/W76 lib)
        rep["w59_offsets"] = {"scen_ptr": "0x00A8B230",
                              "filename": "+0x125C", "stage_idx": "+0x35A0",
                              "end_of_game": "+0x34AC", "skip_score": "+0x34AE",
                              "skip_mapsel": "+0x34B0", "battle_idx": "+0x34CC",
                              "frame": "0x00A8ED84"}

        # design summary (both variants share the same combat layout)
        ann = json.loads(C.DESIGN_ANN.read_text(encoding="utf-8"))
        m = ann["missions"][0]
        rep["combat_layout"] = {
            "size": m["size"], "theater": m["theater"],
            "player_house": m["player"]["house"],
            "enemy_house": "British",
            "player_structures": len(m["structures"]),
            "player_units": sum(1 for u in m["units"] if u["owner"] == "Russians"),
            "player_infantry": sum(1 for u in m["infantry"] if u["owner"] == "Russians"),
            "enemy_units": sum(1 for u in m["units"] if u["owner"] == "British"),
            "enemy_infantry": sum(1 for u in m["infantry"] if u["owner"] == "British"),
            "enemy_mission": "Hunt",
            "objectives_annih": m["objectives"],
            "win_annih": "destroy_all_forces(British) -> AllDestroyed(4) -> WinnerIs(8)",
            "win_time": "survive(55) -> ElapsedTime(55) -> WinnerIs(8)",
        }
        ok = True
        sink.step("build_result", ok=ok, **rep["combat_layout"])
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
