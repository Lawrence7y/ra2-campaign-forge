#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W79 BUILD - offline, NO LOCK, NO gamemd.exe.

Generates 4 designs and builds 4 packages into SEPARATE directories:

  TASK A (3x SURVIVE, IDENTICAL LAYOUT, only the seconds differ)
    pkg_s8   : survive(8)
    pkg_s20  : survive(20)
    pkg_s55  : survive(55)
  Layout: 60x60 TEMPERATE; Russians 10 MTNK + 4 E2 + 3 structures (STATIC,
  no mission), at the W78 positions; British 4 E1 infantry STATIC (no Hunt,
  rows 5-8, far away) -> the enemy side always has live units, so an
  "all enemy forces destroyed" win is impossible and no combat occurs.
  Objectives: text(at_second=1) [W76 proven pattern] + survive(N).

  TASK B (ANNIHILATION)
    pkg_ann : 40 Russian MTNK ALL mission=Hunt; 4 British E1 STATIC (no Hunt)
    placed CLOSE (rows 44-45) to the tank line; win = destroy_all_forces(British).
    NO survive objective (avoid mixing two win conditions).

Build command (proven W76/W78):
  python -m ra2forge build --design <d> --out <o> --feature-set <fs>
run with the v15 patched package root as cwd.

Everything writes ONLY inside W79_survive_and_annih.  git is read-only.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import w79_lib as L
import w79_common as C

TAG = "build"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------- layouts
RUSSIAN_STRUCTURES = [
    {"owner": "Russians", "type": "NACNST", "row": 50, "col": 30},
    {"owner": "Russians", "type": "NAPOWR", "row": 52, "col": 27},
    {"owner": "Russians", "type": "NAPOWR", "row": 52, "col": 33},
]
RUSSIAN_UNITS = [
    {"owner": "Russians", "type": "MTNK", "row": 47, "col": 25},
    {"owner": "Russians", "type": "MTNK", "row": 47, "col": 28},
    {"owner": "Russians", "type": "MTNK", "row": 47, "col": 31},
    {"owner": "Russians", "type": "MTNK", "row": 47, "col": 34},
    {"owner": "Russians", "type": "MTNK", "row": 48, "col": 26},
    {"owner": "Russians", "type": "MTNK", "row": 48, "col": 29},
    {"owner": "Russians", "type": "MTNK", "row": 48, "col": 32},
    {"owner": "Russians", "type": "MTNK", "row": 48, "col": 35},
    {"owner": "Russians", "type": "MTNK", "row": 46, "col": 28},
    {"owner": "Russians", "type": "MTNK", "row": 46, "col": 33},
]
RUSSIAN_INF = [
    {"owner": "Russians", "type": "E2", "row": 49, "col": 28},
    {"owner": "Russians", "type": "E2", "row": 49, "col": 32},
    {"owner": "Russians", "type": "E2", "row": 50, "col": 27},
    {"owner": "Russians", "type": "E2", "row": 50, "col": 33},
]
# Weak, STATIC, alive enemy: keeps the British house non-eliminated for the
# whole run (rules out "all enemy forces destroyed" as the win source) while
# producing no combat (both sides static, ~40 rows apart).
WEAK_ENEMY_INF = [
    {"owner": "British", "type": "E1", "row": 5, "col": 18},
    {"owner": "British", "type": "E1", "row": 6, "col": 28},
    {"owner": "British", "type": "E1", "row": 7, "col": 38},
    {"owner": "British", "type": "E1", "row": 8, "col": 24},
]


def make_annih_tanks():
    """40 Russian MTNK, all mission=Hunt, spread rows 42..50 / cols 16..44."""
    out = []
    coords = []
    for row in range(42, 51):          # 42..50
        for col in range(16, 45, 3):   # 16,19,22,...,43 (10 per row)
            coords.append((row, col))
    for row, col in coords[:40]:
        out.append({"owner": "Russians", "type": "MTNK",
                    "row": row, "col": col, "mission": "Hunt"})
    assert len(out) == 40
    return out


# 4 British E1 STATIC, placed just above the tank grid (row 36) on columns
# that do NOT collide with any tank cell (tank cols are 16,19,...,43).
ANN_ENEMY_INF = [
    {"owner": "British", "type": "E1", "row": 36, "col": 24},
    {"owner": "British", "type": "E1", "row": 36, "col": 27},
    {"owner": "British", "type": "E1", "row": 36, "col": 30},
    {"owner": "British", "type": "E1", "row": 36, "col": 33},
]


def base_design(name, title, briefing):
    # NOTE: campaign.name is the PACKAGE FOLDER NAME emitted by ra2forge.  Keep
    # it identical for all four variants so every package sits at <out>/W79Probe.
    return {
        "package": {"id": "org.ra2forge.w79." + name, "version": "1.0"},
        "campaign": {
            "id": "RA2F_W79",
            "name": "W79Probe",
            "description": "W79 survive/annihilation discriminating experiment",
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


def survive_design(seconds: int) -> dict:
    d = base_design("W79Survive%d" % seconds,
                    "W79 survive(%d) M1" % seconds,
                    "W79 TASK A. survive(%d) win trigger; weak STATIC enemy "
                    "stays alive; no combat. ElapsedTime(%d) -> WinnerIs(Russians)."
                    % (seconds, seconds))
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(RUSSIAN_STRUCTURES))
    m["units"] = json.loads(json.dumps(RUSSIAN_UNITS))
    m["infantry"] = json.loads(json.dumps(RUSSIAN_INF)) + json.loads(json.dumps(WEAK_ENEMY_INF))
    m["objectives"] = [
        {"type": "text", "text": "W79 SURVIVE(%d) PROBE" % seconds, "at_second": 1},
        {"type": "survive", "seconds": seconds},
    ]
    return d


def annih_design() -> dict:
    d = base_design("W79Annih",
                    "W79 annih M1",
                    "W79 TASK B. 40 Russian MTNK all Hunt vs 4 STATIC British E1. "
                    "Win = destroy_all_forces(British). NO survive objective.")
    m = d["missions"][0]
    m["structures"] = json.loads(json.dumps(RUSSIAN_STRUCTURES))
    m["units"] = make_annih_tanks()
    m["infantry"] = json.loads(json.dumps(ANN_ENEMY_INF))
    m["objectives"] = [
        {"type": "text", "text": "W79 ANNIH PROBE", "at_second": 1},
        {"type": "destroy_all_forces", "enemy": "British"},
    ]
    return d


DESIGNS = {
    "s8":  (survive_design(8),  "survive", 8),
    "s20": (survive_design(20), "survive", 20),
    "s55": (survive_design(55), "survive", 55),
    "ann": (annih_design(),     "annih",   None),
}


def verify_pkg(sink, label: str, pkg: Path, kind: str, seconds) -> dict:
    rep = {"label": label, "pkg": str(pkg), "kind": kind, "seconds": seconds}
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
                       "sov1_scenario": b.count(b"Scenario=RA2F_M1.MAP"),
                       "official_scenario": b.count(b"Scenario=SOV01umd.MAP")}

    t = (pkg / "RA2F_M1.MAP").read_bytes().decode("latin-1")
    d = {}
    for ln in t.splitlines():
        for k in ("NextScenario", "EndOfGame", "SkipMapSelect", "Size"):
            if ln.startswith(k + "="):
                d[k] = ln.split("=", 1)[1]
    d["russian_mtnk"] = t.count("Russians,MTNK")
    d["russian_e2"] = t.count("Russians,E2")
    d["british_e1"] = t.count("British,E1")
    d["hunt_mission"] = t.count(",Hunt,")
    # Event/action params are serialized WITHOUT a trailing comma after the
    # last param (maplib.py:455-472), so use a numeric boundary, not a comma.
    d["elapsed_time_event_prefix"] = len(re.findall(r",13,0,\d+", t))
    d["elapsed_8"] = bool(re.search(r",13,0,8(?!\d)", t))
    d["elapsed_20"] = bool(re.search(r",13,0,20(?!\d)", t))
    d["elapsed_55"] = bool(re.search(r",13,0,55(?!\d)", t))
    d["all_destroyed_event"] = bool(re.search(r",11,0,4(?!\d)", t))
    d["winner_is_action"] = bool(re.search(r",1,0,8(?!\d)", t))
    d["survive_tag_prefix"] = ("Objective: survive" in t)
    d["destroy_tag_prefix"] = ("Objective: destroy" in t)
    rep["map"] = d

    ms = (pkg / "MAPSELMD.INI").read_bytes()
    rep["mapselmd"] = {"size": len(ms), "sha256": sha(ms),
                       "scenario_m1": ms.count(b"Scenario=RA2F_M1.MAP")}

    # ---- common assertions ----
    assert rep["has_battlemd_ini"] and rep["has_map"] and rep["has_mapselmd"]
    assert rep["has_mix"] and rep["has_package_json"], rep
    assert rep["battlemd"]["sov1_scenario"] == 1, rep["battlemd"]
    assert rep["battlemd"]["official_scenario"] == 0, rep["battlemd"]
    assert rep["battlemd"]["bare_lf"] == 0, rep["battlemd"]
    assert d.get("NextScenario") == "", d
    assert d.get("EndOfGame") == "yes", d
    assert d.get("SkipMapSelect") == "no", d
    assert "0,0,60,60" in d.get("Size", ""), d
    assert rep["mapselmd"]["scenario_m1"] >= 1, rep["mapselmd"]
    assert d["winner_is_action"], d

    if kind == "survive":
        assert d["russian_mtnk"] == 10 and d["russian_e2"] == 4, d
        assert d["british_e1"] == 4, d
        assert d["hunt_mission"] == 0, d          # NO combat in Task A
        assert d["survive_tag_prefix"], d
        assert not d["destroy_tag_prefix"], d
        assert not d["all_destroyed_event"], d
        # the ONLY ElapsedTime events are: text@1 and survive(seconds)
        key = {8: "elapsed_8", 20: "elapsed_20", 55: "elapsed_55"}[seconds]
        assert d[key], (key, d)
        others = {"elapsed_8", "elapsed_20", "elapsed_55"} - {key}
        assert not any(d[o] for o in others), (others, d)
    else:
        assert d["russian_mtnk"] == 40, d
        assert d["british_e1"] == 4, d
        assert d["hunt_mission"] == 40, d          # all 40 tanks Hunt
        assert d["all_destroyed_event"], d
        assert d["destroy_tag_prefix"], d
        assert not d["survive_tag_prefix"], d
        assert not (d["elapsed_8"] or d["elapsed_20"] or d["elapsed_55"]), d
    rep["verdict"] = "PASS"
    sink.step("package_verify_" + label, **rep)
    return rep


def main() -> int:
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build 4 packages: NO lock, NO gamemd.exe",
                  v15=str(C.V15), feature_set=str(C.FEATURE_SET))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline build phase: %r" % residual)
        if C.lock_owner() != "lead":
            raise RuntimeError("lock owner not lead at offline phase: %r" % C.lock_read())

        rep["designs"] = {}
        rep["builds"] = []
        rep["verify"] = []
        for label, (design, kind, sec) in DESIGNS.items():
            dpath = C.WORK / ("w79_design_%s.json" % label)
            dpath.write_text(json.dumps(design, ensure_ascii=False, indent=2),
                             encoding="utf-8")
            rep["designs"][label] = {
                "path": str(dpath), "kind": kind, "seconds": sec,
                "n_units": len(design["missions"][0]["units"]),
                "n_inf": len(design["missions"][0]["infantry"]),
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
            pkg = out_dir / "W79Probe"
            (pkg / "ra2forge_package.json").write_text(
                json.dumps({"tool": "ra2forge",
                            "package_id": "org.ra2forge.w79.%s" % label,
                            "package_version": "1.0"}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            rep["builds"].append({"label": label, "pkg": str(pkg),
                                  "exit_code": rec["exit_code"]})
            rep["verify"].append(verify_pkg(sink, label, pkg, kind, sec))

        # byte-identity of the 3 survive layouts except the survive parameter
        def strip_survive_variant(text):
            """Remove every line that mentions the survive objective or its
            ElapsedTime(N) event; everything else must be byte-identical."""
            keep = []
            for ln in text.splitlines():
                low = ln.lower()
                if "survive" in low:
                    continue
                if re.search(r",13,0,\d+", ln):
                    continue
                keep.append(ln)
            return keep

        maps = {}
        for label in ("s8", "s20", "s55"):
            maps[label] = (C.PKG[label] / "RA2F_M1.MAP").read_bytes().decode("latin-1")
        base_lines = strip_survive_variant(maps["s8"])
        rep["layout_identity"] = {}
        for label in ("s20", "s55"):
            cmp_lines = strip_survive_variant(maps[label])
            rep["layout_identity"][label] = {
                "identical_except_survive_lines": (base_lines == cmp_lines),
                "base_lines": len(base_lines), "cmp_lines": len(cmp_lines),
            }
        rep["w59_offsets"] = {"scen_ptr": "0x00A8B230",
                              "filename": "+0x125C", "stage_idx": "+0x35A0",
                              "end_of_game": "+0x34AC", "skip_score": "+0x34AE",
                              "skip_mapsel": "+0x34B0", "battle_idx": "+0x34CC",
                              "frame": "0x00A8ED84"}
        ok = True
        sink.step("build_result", ok=ok, n_packages=4)
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
