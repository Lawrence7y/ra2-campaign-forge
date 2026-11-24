#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W91 BUILD - offline, NO gamemd.exe.  长途接敌设计（地理分离，趟内两阶段）.

Steps (env W91_STEP):
  P1  (v1, superseded): 100x100, player buildings-only, enemy 200 Hunt.
      Object count ~220 != 1522 => NOT comparable to C6/CTRL_C6 bands
      (lead correction 2026-11-14).  Kept for archive/evidence only.
  P2  (v1, superseded): P1 pushed to the extreme diagonal + [NAPOWR]
      Crewed=no post-build override (NOTE: W88 C7 showed Crewed=no does
      NOT prevent the crash - 1/1 crashed; this wording corrects an
      earlier erroneous "proven-effective" claim).  P2 crashed too.
  P3  (v2, current): object count EXACTLY like C6 (1522):
      - map 200x200 TEMPERATE (ra2forge supports 40..200 even squares)
      - player Russians bottom-right corner: NACNST x1 + NAPOWR x6
        (col step 3) + TESLA x12 + 300 MTNK Guard
      - enemy British/Confederation/Arabs x400 MTNK each = 1200, all
        Hunt, top-left diagonal far end + 3x GAPOWR (C6-like structure)
      => only new variable vs C6 = the geographic separation between the
      two forces.  Verdict = same-trip A/B ratio (self-consistent).

D4: design JSON + built map/INI/mix archived to out/inputs/<step>/ with sha256.
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
import w91_lib as L
import w91_common as C

TAG = "build"

ENEMY_UNIT = "MTNK"
CREWED_OVERRIDE = "[NAPOWR]\r\nCrewed=no\r\n"


def env_int(name, default):
    try:
        return int(os.environ.get(name, "") or default)
    except ValueError:
        return default


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


def napowr_cells(row, col0, n=6, step=3):
    return [(row, col0 + i * step) for i in range(n)]


def tesla_rows(rows, col0, n=6, step=3):
    out = []
    for r in rows:
        out += [(r, col0 + i * step) for i in range(n)]
    return out


def step_spec(step):
    """Full geometry spec per trip.  All building footprints (2x2) are kept
    pairwise disjoint; units never share a cell; units never sit on a
    building footprint."""
    if step.upper() == "P1":
        return {
            "size": 100,
            "nacnst": (88, 50),
            "napowr": napowr_cells(90, 44),
            "tesla": tesla_rows((92, 94), 40),
            "player_units": {"n": 0, "mission": "Guard", "rows": None,
                             "cols": None},
            "enemy_houses": [("British", 8, 32)],
            "enemy_rows": (4, 11),
            "enemy_per_house": 200,
            "gapowr": [],
            "waypoints": {"0": [52, 50], "1": [8, 50], "2": [8, 9]},
            "crewed_no": False,
        }
    if step.upper() == "P2":
        return {
            "size": 100,
            "nacnst": (92, 80),
            "napowr": napowr_cells(95, 74),
            "tesla": tesla_rows((90, 97), 74),
            "player_units": {"n": 0, "mission": "Guard", "rows": None,
                             "cols": None},
            "enemy_houses": [("British", 1, 25)],
            "enemy_rows": (1, 8),
            "enemy_per_house": 200,
            "gapowr": [],
            "waypoints": {"0": [52, 50], "1": [8, 50], "2": [8, 9]},
            "crewed_no": True,
        }
    if step.upper() == "P3":
        # 200x200, object count == C6 (1522).  Player bottom-right corner,
        # enemy top-left diagonal far end.  Approach ~230 cells straight
        # line => A-phase should be tens of seconds.
        return {
            "size": 200,
            "nacnst": (176, 160),
            "napowr": napowr_cells(178, 154),
            "tesla": tesla_rows((180, 182), 154),
            "player_units": {"n": 300, "mission": "Guard",
                             "rows": (185, 196), "cols": (148, 172)},
            "enemy_houses": [("British", 2, 35), ("Confederation", 36, 69),
                             ("Arabs", 70, 103)],
            "enemy_rows": (4, 15),
            "enemy_per_house": 400,
            "gapowr": [("British", 2, 9), ("Confederation", 2, 43),
                       ("Arabs", 2, 77)],
            "waypoints": {"0": [180, 160], "1": [10, 50], "2": [10, 10]},
            "crewed_no": False,
        }
    raise RuntimeError("unknown W91_STEP %s" % step)


def build_design(step, s):
    n = s["size"]
    m = {
        "name": "RA2F_M1",
        "title": "W91 %s M1" % step,
        "briefing": ("W91 %s: geographic separation of march vs combat, "
                     "object count %d == C6.  Player Russians bottom-right: "
                     "NACNST 1 + NAPOWR 6 (step3) + TESLA 12 + %d MTNK Guard; "
                     "enemy 3x%d MTNK all Hunt (top-left diagonal) + %d "
                     "GAPOWR.  In-trip phases: A = A8ED50==0 and X87E8E0 "
                     "changing; B = after first A8ED50 nonzero."
                     % (step, s["nacnst"] is not None and (
                         1 + len(s["napowr"]) + len(s["tesla"])
                         + len(s["gapowr"]) + s["player_units"]["n"]
                         + 3 * s["enemy_per_house"]), s["player_units"]["n"],
                        s["enemy_per_house"], len(s["gapowr"]))),
        "theater": "TEMPERATE",
        "size": [n, n],
        "player": {"house": "Russians", "credits": 10000, "enemy_credits": 0},
        "waypoints": s["waypoints"],
        "structures": [],
        "units": [],
        "infantry": [],
        "objectives": [{"type": "text", "text": "W91 %s PROBE" % step,
                        "at_second": 1}],
    }
    m["structures"] = (
        [{"owner": "Russians", "type": "NACNST",
          "row": s["nacnst"][0], "col": s["nacnst"][1]}]
        + [{"owner": "Russians", "type": "NAPOWR", "row": r, "col": c}
           for r, c in s["napowr"]]
        + [{"owner": "Russians", "type": "TESLA", "row": r, "col": c}
           for r, c in s["tesla"]]
        + [{"owner": h, "type": "GAPOWR", "row": r, "col": c}
           for h, r, c in s["gapowr"]])
    units = []
    pu = s["player_units"]
    if pu["n"]:
        pslots = grid_slots(pu["rows"][0], pu["rows"][1],
                            pu["cols"][0], pu["cols"][1])
        assert len(pslots) >= pu["n"], (len(pslots), pu["n"])
        units += [{"owner": "Russians", "type": ENEMY_UNIT, "row": r, "col": c,
                   "mission": pu["mission"]} for r, c in pslots[:pu["n"]]]
    bocc = set()
    for st in m["structures"]:
        for rr in (st["row"], st["row"] + 1):
            for cc in (st["col"], st["col"] + 1):
                bocc.add((rr, cc))
    for house, c0, c1 in s["enemy_houses"]:
        slots = [rc for rc in grid_slots(s["enemy_rows"][0],
                                         s["enemy_rows"][1], c0, c1)
                 if rc not in bocc]
        assert len(slots) >= s["enemy_per_house"], (house, len(slots))
        units += [{"owner": house, "type": ENEMY_UNIT, "row": r, "col": c,
                   "mission": "Hunt"}
                  for r, c in slots[:s["enemy_per_house"]]]
    m["units"] = units
    return {
        "package": {"id": "org.ra2forge.w91." + step.lower(), "version": "1.0"},
        "campaign": {"id": "RA2F1", "name": "W88Probe",
                     "description": "W91 %s long-approach probe" % step,
                     "side": "soviet"},
        "missions": [m],
    }


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_pkg(sink, step: str, pkg: Path, design, s) -> dict:
    rep = {"step": step, "pkg": str(pkg)}
    files = []
    for fp in sorted(pkg.rglob("*"), key=lambda x: x.as_posix().lower()):
        if fp.is_file():
            files.append({"rel": fp.relative_to(pkg).as_posix(),
                          "size": fp.stat().st_size, "sha256": L.sha256_file(fp)})
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
    n = s["size"]
    d["russian_nacnst"] = t.count("=Russians,NACNST,")
    d["russian_napowr"] = t.count("=Russians,NAPOWR,")
    d["russian_tesla"] = t.count("=Russians,TESLA,")
    d["russian_mtnk"] = t.count("=Russians,MTNK,")
    for h, _, _ in s["enemy_houses"]:
        d["%s_mtnk" % h.lower()] = t.count("=%s,MTNK," % h)
    d["gapowr_total"] = sum(t.count("=%s,GAPOWR," % h)
                            for h, _, _ in s["enemy_houses"])
    d["hunt_mission"] = t.count(",Hunt,")
    d["guard_mission"] = t.count(",Guard,")
    d["winner_is_action"] = bool(re.search(r",1,0,8(?!\d)", t))
    d["loser_action"] = bool(re.search(r",2,0,8(?!\d)", t))
    d["all_destroyed_russians_event"] = bool(re.search(r",11,0,8(?!\d)", t))
    d["elapsed_1"] = bool(re.search(r",13,0,1(?!\d)", t))
    d["crewed_override_present"] = bool(re.search(
        r"\[NAPOWR\]\s*.*?Crewed=no", t, re.S))
    rep["map"] = d
    ms = (pkg / "MAPSELMD.INI").read_bytes()
    rep["mapselmd"] = {"size": len(ms), "sha256": sha(ms),
                       "scenario_m1": ms.count(b"Scenario=RA2F_M1.MAP")}
    assert rep["battlemd"]["ra2f_scenario"] == 1, rep["battlemd"]
    assert rep["battlemd"]["official_scenario"] == 0, rep["battlemd"]
    assert rep["battlemd"]["bare_lf"] == 0, rep["battlemd"]
    assert d.get("NextScenario") == "", d
    assert d.get("EndOfGame") == "yes", d
    assert d.get("SkipMapSelect") == "no", d
    assert "0,0,%d,%d" % (n, n) in d.get("Size", ""), d
    assert rep["mapselmd"]["scenario_m1"] >= 1, rep["mapselmd"]
    assert d["russian_nacnst"] == 1, d
    assert d["russian_napowr"] == 6, d
    assert d["russian_tesla"] == 12, d
    assert d["russian_mtnk"] == s["player_units"]["n"], d
    for h, _, _ in s["enemy_houses"]:
        assert d["%s_mtnk" % h.lower()] == s["enemy_per_house"], (h, d)
    assert d["gapowr_total"] == len(s["gapowr"]), d
    hunt_expected = 3 * s["enemy_per_house"] if s["gapowr"] else \
        len(s["enemy_houses"]) * s["enemy_per_house"]
    assert d["hunt_mission"] == hunt_expected, (step, d["hunt_mission"])
    assert d["guard_mission"] == s["player_units"]["n"], d
    assert d["loser_action"] and d["all_destroyed_russians_event"], d
    assert d["elapsed_1"], d
    assert not d["winner_is_action"], d
    assert d["crewed_override_present"] == bool(s.get("crewed_no")), d
    structs = design["missions"][0]["structures"]
    ov = overlap_cells([(st["row"], st["col"]) for st in structs])
    assert ov is None, ("structure overlap at %r" % (ov,))
    slots = [(u["row"], u["col"]) for u in design["missions"][0]["units"]]
    assert len(set(slots)) == len(slots)
    assert not (set(slots) & ov_cells_of(structs)), \
        "unit on a building footprint"
    for u in design["missions"][0]["units"]:
        assert 0 <= u["row"] < n and 0 <= u["col"] < n, u
    rep["verdict"] = "PASS"
    sink.step("package_verify_" + step, **rep)
    return rep


def ov_cells_of(structs):
    occ = set()
    for st in structs:
        for rr in (st["row"], st["row"] + 1):
            for cc in (st["col"], st["col"] + 1):
                occ.add((rr, cc))
    return occ


def archive_inputs(sink, step: str, design: dict, pkg: Path):
    adir = C.OUT / "inputs" / step
    adir.mkdir(parents=True, exist_ok=True)
    rows = []
    dpath = adir / ("w91_design_%s.json" % step)
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
    step = os.environ.get("W91_STEP", "P3").strip().upper()
    s = step_spec(step)
    design = build_design(step, s)
    dpath = C.design_path(step)
    dpath.write_text(json.dumps(design, ensure_ascii=False, indent=2),
                     encoding="utf-8")
    sink = L.Sink(TAG)
    ok = False
    rep = {}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build: NO lock, NO gamemd.exe; W91 "
                       "geographic-separation design (v2: object count == C6)",
                  step=step, size=s["size"],
                  n_struct=len(design["missions"][0]["structures"]),
                  n_units=len(design["missions"][0]["units"]),
                  crewed_no=s["crewed_no"],
                  v15=str(C.V15), feature_set=str(C.FEATURE_SET))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual,
                  n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline build phase: %r"
                               % residual)
        if C.lock_owner() not in ("lead", "w91", ""):
            raise RuntimeError("lock owner not lead/w91 at offline phase: %r"
                               % C.lock_read())
        out_dir = C.WORK / ("pkg_" + step)
        out_dir.mkdir(parents=True, exist_ok=True)
        rec = C.v15_cmd(sink, "build_" + step,
                        ["build", "--design", str(dpath), "--out", str(out_dir),
                         "--feature-set", str(C.FEATURE_SET)])
        if rec["exit_code"] != 0:
            raise RuntimeError("build %s exit %s: %s"
                               % (step, rec["exit_code"], rec["stderr_tail"][-2500:]))
        pkg = C.pkg_path(step)
        assert pkg.is_dir(), pkg
        (pkg / "ra2forge_package.json").write_text(
            json.dumps({"tool": "ra2forge",
                        "package_id": design["package"]["id"],
                        "package_version": "1.0"}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        crewed_edit = None
        if s["crewed_no"]:
            mp = pkg / "RA2F_M1.MAP"
            b = mp.read_bytes()
            if b"[NAPOWR]" in b:
                raise RuntimeError("map already contains [NAPOWR] section")
            if not b.endswith(b"\r\n"):
                b += b"\r\n"
            b += CREWED_OVERRIDE.encode("ascii")
            mp.write_bytes(b)
            crewed_edit = {"file": "RA2F_M1.MAP",
                           "appended": CREWED_OVERRIDE.replace("\r\n", "\\r\\n"),
                           "size": len(b), "sha256": sha(b)}
            sink.step("crewed_override_applied", step=step, **crewed_edit)
        rep["build"] = {"step": step, "pkg": str(pkg),
                        "exit_code": rec["exit_code"], "crewed_edit": crewed_edit}
        rep["verify"] = verify_pkg(sink, step, pkg, design, s)
        rep["inputs"] = archive_inputs(sink, step, design, pkg)
        ok = True
        sink.step("build_result", ok=ok, step=step)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / ("BUILD_RESULT_%s.json" % step)).write_text(
            json.dumps(rep, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok, step=step,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
