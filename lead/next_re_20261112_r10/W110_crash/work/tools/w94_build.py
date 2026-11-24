#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""W94 BUILD - offline, NO LOCK required beyond owner gate, NO gamemd.exe.

Builds ONE matrix cell package from a cell spec JSON (written by
batch_runner.py), generalizing the W88 C-ladder knobs (W88_build.py is the
proven source; geometry constants copied verbatim):

  spec = {
    "cell": "c3",                     # cell id (dir/file name component)
    "arm": {
      "hunt_all": true,               # all 3 enemy houses Hunt
      "hunt_british": 0,              # minimal-dose knob (British n units)
      "napowr_step": 3,               # NAPOWR col spacing 2 or 3
      "crewed": false                 # append [NAPOWR] Crewed=no to built map
    }
  }

Presets (resolved by batch_runner.py from arm_template + overrides):
  C6  = hunt_all, step3          C2  = hunt_all, step2
  C1  = hunt_british=30, step2   C7  = hunt_all, step2, crewed
  C0/CTRL = all Guard (hunt_all=false, hunt_british=0)

Outputs (per cell):
  work/w94_design_<cell>.json      design JSON (input to ra2forge build)
  work/pkg_<cell>/W94Probe/        built package
  out/inputs/<cell>/               D4 archive: design + built map/INIs + sha256
  out/BUILD_<cell>.json            build proof

The frozen W85 TESLA grid is 2x2-overlapping by the naive check but is the
SIGNED GREEN baseline - asserted only for NAPOWR, the factor actually under
test (verbatim W88 note).
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
import w94_lib as L
import w94_common as C

TAG = "build"

# ---- W85 control-arm geometry (signed green; verbatim W88) ------------------
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
# [W98] enemy_zone knob - geometric manipulation of march workload (NEVER
# Speed=; W96 proved the speed knob design-invalid):
#   "far"  => original W85/C6 enemy zones (rows 12-41, cols per house zone) -
#             long march before contact.  g_idle (all Guard) and g_far (all
#             Hunt) both use this.
#   "near" => the 3x400 enemy MTNK are relocated (COORDINATES ONLY - counts,
#             types, missions, structures all unchanged) to the nearest free
#             cells hugging the player base, so contact is ~1 s and there is
#             essentially no march.  g_near uses this with hunt_all=true.
# Distance metric: Chebyshev distance from the cell to the NEAREST player-owned
# object cell (structure anchor or player tank).  Fill order: nearest first,
# ties by (row, col).  Placement pool excludes every occupied cell (structure
# 2x2 footprints, player tank cells, enemy GAPOWR footprints) and stays in
# map bounds 0..99.  The achieved min/max/mean distance is recorded in the
# build proof and in the design briefing (D4 archive).
ENEMY_ZONE_KNOBS = ("far", "near")
NEAR_POOL_MIN = 1200


def chebyshev(r, c, cells):
    return min(max(abs(r - pr), abs(c - pc)) for pr, pc in cells)


def near_enemy_slots():
    """Nearest-first free cells hugging the player base (deterministic)."""
    anchors = ([NACNST_CELL] + NAPOWR_CELLS_STEP3 + TESLA_CELLS)
    occupied = set()
    for r, c in anchors:
        for rr in (r, r + 1):
            for cc in (c, c + 1):
                occupied.add((rr, cc))
    for r, c in grid_slots(*PLAYER_UNIT_GRID)[:PLAYER_MTNK_N]:
        occupied.add((r, c))
    for house in ENEMY_ZONE_COLS:   # enemy GAPOWR footprints (rows 8-9)
        r0, c0 = 8, ENEMY_ZONE_COLS[house][0] + 7
        occupied.add((r0, c0)); occupied.add((r0, c0 + 1))
        occupied.add((r0 + 1, c0)); occupied.add((r0 + 1, c0 + 1))
    cand = []
    for r in range(0, MAP_N):
        for c in range(0, MAP_N):
            if (r, c) in occupied:
                continue
            cand.append((chebyshev(r, c, anchors), r, c))
    radius = 3
    while True:
        pool = sorted(x for x in cand if x[0] <= radius)
        if len(pool) >= NEAR_POOL_MIN or radius >= MAP_N:
            break
        radius += 1
    if len(pool) < NEAR_POOL_MIN:
        raise RuntimeError("near pool too small: %d (<%d)"
                           % (len(pool), NEAR_POOL_MIN))
    slots = [(r, c) for _d, r, c in pool[:NEAR_POOL_MIN]]
    dists = [d for d, _r, _c in pool[:NEAR_POOL_MIN]]
    stats = {"radius_used": radius, "n": len(slots),
             "dist_min": min(dists), "dist_max": max(dists),
             "dist_mean": round(sum(dists) / len(dists), 3)}
    return slots, stats
# [W96] map-INI override pathway probes (W95 audit §5 signed probe + the
# card's m3/m4).  Vanilla rules have NO per-house speed bias (only the global
# GameSpeedBias) and all 4 houses share the MTNK type, so:
#   speed_all_mtnk    => [MTNK] Speed=1 is TYPE-GLOBAL (player MTNK slows too).
#   player_slow_clone => player tanks are BUILT as HTNK and the map appends an
#                        [HTNK] section that clones the full MTNK stat block
#                        with Speed=1 (enemy MTNK untouched).
SPEED_ALL_MTNK_OVERRIDE = "[MTNK]\r\nSpeed=1\r\n"
PLAYER_SLOW_CLONE_OVERRIDE = ("[HTNK]\r\n"
    "UIName=Name:MTNK\r\n"
    "Name=Grizzly Battle Tank (Speed1 clone)\r\n"
    "Image=GTNK\r\n"
    "Primary=105mm\r\n"
    "Strength=300\r\n"
    "Category=AFV\r\n"
    "Armor=heavy\r\n"
    "Turret=yes\r\n"
    "IsTilter=yes\r\n"
    "Crusher=yes\r\n"
    "TooBigToFitUnderBridge=true\r\n"
    "TechLevel=2\r\n"
    "Sight=8\r\n"
    "Speed=1\r\n"
    "CrateGoodie=no\r\n"
    "Cost=700\r\n"
    "Soylent=700\r\n"
    "Points=25\r\n"
    "ROT=5\r\n"
    "IsSelectableCombatant=yes\r\n"
    "Explosion=TWLT070,S_BANG48,S_BRNL58,S_CLSN58,S_TUMU60\r\n"
    "DieSound=GenVehicleDie\r\n"
    "MoveSound=GrizzlyTankMoveStart\r\n"
    "CrushSound=TankCrush\r\n"
    "MaxDebris=2\r\n"
    "Locomotor={4A582741-9839-11d1-B709-00A024DDAFD1}\r\n"
    "MovementZone=Normal\r\n"
    "ThreatPosed=15\r\n"
    "DamageParticleSystems=SparkSys,SmallGreySSys\r\n"
    "VeteranAbilities=STRONGER,FIREPOWER,SIGHT,FASTER\r\n"
    "EliteAbilities=SELF_HEAL,STRONGER,FIREPOWER,ROF\r\n"
    "Accelerates=false\r\n"
    "ImmuneToVeins=yes\r\n"
    "OpportunityFire=yes\r\n"
    "ElitePrimary=105mmE\r\n"
    "BuildTimeMultiplier=1.5\r\n")

VALID_ARM_KEYS = ("hunt_all", "hunt_british", "napowr_step", "crewed", "unit_scale",
                  "speed_all_mtnk", "player_slow_clone", "enemy_zone")


def grid_slots(row0, row1, col0, col1):
    return [(r, c) for r in range(row0, row1 + 1) for c in range(col0, col1 + 1)]


def overlap_cells(cells):
    """2x2 footprint check: (r,c) covers rows r..r+1, cols c..c+1.

    ⚠️ W129 NOTE: this model is WRONG for every building whose footprint is not
    2x2, and using it made the NAPOWR assertions VACUOUS (ledger §630-3):
    NAPOWR is 3x2, so with column spacing 2 the real spans are 46-48,48-50,...
    which overlap, while this 2x2 model gives 46-47,48-49,... which do not.
    Kept unchanged only so existing call sites that were signed against the 2x2
    model behave identically. New code must use overlap_cells_fp().
    """
    return overlap_cells_fp(cells, 2, 2)


def overlap_cells_fp(cells, w, h):
    """Footprint-aware overlap: (r,c) covers rows r..r+h-1, cols c..c+w-1.

    Returns the first colliding anchor, or None. Verified against the measured
    NAPOWR footprint (3x2): step2 -> 10 overlapping cells, step3 -> 0, which
    reproduces the hand-computed "10 格" from ledger §630-3 for the first time.
    """
    occ = set()
    for r, c in cells:
        for rr in range(r, r + h):
            for cc in range(c, c + w):
                if (rr, cc) in occ:
                    return (r, c)
                occ.add((rr, cc))
    return None


def overlap_cell_count_fp(cells, w, h):
    """Total cells covered by more than one building (footprint-aware)."""
    occ = {}
    for r, c in cells:
        for rr in range(r, r + h):
            for cc in range(c, c + w):
                occ[(rr, cc)] = occ.get((rr, cc), 0) + 1
    return sum(1 for v in occ.values() if v > 1)


# Measured footprints (ledger §669: "16 格 = 4x4，6 格 = 3x2"; NAPOWR is the
# only building whose spacing the experiments vary, and 6 cells = 3x2).
NAPOWR_FP = (3, 2)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def base_design(cell, arm):
    brief = ("W94 matrix cell %s: W85 green control geometry; NAPOWR spacing "
             "step %d; Hunt units: British %d%s; Crewed override %s."
             % (cell, arm["napowr_step"], arm["hunt_british"],
                " + all houses" if arm["hunt_all"] else "",
                "ON" if arm["crewed"] else "OFF"))
    return {
        "package": {"id": "org.ra2forge.w94.%s" % cell.lower(), "version": "1.0"},
        "campaign": {
            "id": "RA2F1",
            "name": "W94Probe",
            "description": "W94 matrix cell " + cell,
            "side": "soviet",
        },
        "missions": [{
            "name": "RA2F_M1",
            "title": "W94 %s M1" % cell,
            "briefing": brief,
            "theater": "TEMPERATE",
            "size": [MAP_N, MAP_N],
            "player": {"house": "Russians", "credits": 10000, "enemy_credits": 0},
            "waypoints": {"0": [52, 50], "1": [8, 50], "2": [8, 9]},
            "structures": [], "units": [], "infantry": [],
            "objectives": [{"type": "text", "text": "W94 %s PROBE" % cell,
                            "at_second": 1}],
        }],
    }


def spec_design(cell, arm):
    """Effective design from the normalized arm dict."""
    d = base_design(cell, arm)
    m = d["missions"][0]
    # [W96] player_slow_clone: player tanks are BUILT as HTNK (the map then
    # appends an [HTNK] MTNK-clone section with Speed=1; enemy MTNK untouched)
    player_type = "HTNK" if arm.get("player_slow_clone") else "MTNK"
    napowr = NAPOWR_CELLS_STEP2 if arm["napowr_step"] == 2 else NAPOWR_CELLS_STEP3
    zone = arm.get("enemy_zone", "far")
    near_stats = None
    if zone == "near":
        near_slots, near_stats = near_enemy_slots()
        m["briefing"] = (
            "W98 geometry split cell %s: W85 green control geometry; NAPOWR "
            "spacing step %d; enemy zone=NEAR (3x400 MTNK relocated to the "
            "nearest free cells hugging the player base; Chebyshev dist to "
            "nearest player object min %d / max %d / mean %.2f, fill radius "
            "%d); Hunt units: British %d%s; Crewed override %s."
            % (cell, arm["napowr_step"], near_stats["dist_min"],
               near_stats["dist_max"], near_stats["dist_mean"],
               near_stats["radius_used"], arm["hunt_british"],
               " + all houses" if arm["hunt_all"] else "",
               "ON" if arm["crewed"] else "OFF"))
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
    # player 300 tanks Guard (always - guaranteed NOT a forced-loss scenario)
    # [W123] unit_scale knob: default 1.0 keeps the validated baseline identical.
    _p_n = max(1, int(round(PLAYER_MTNK_N * float(arm.get("unit_scale", 1.0)))))
    pslots = grid_slots(*PLAYER_UNIT_GRID)
    assert len(pslots) >= _p_n
    units += [{"owner": "Russians", "type": player_type, "row": r, "col": c,
               "mission": "Guard"} for r, c in pslots[:_p_n]]
    # enemy 3x400 MTNK; Hunt dose per arm; zone per [W98] enemy_zone knob
    if zone == "near":
        nslots, _ = near_enemy_slots()
        houses = list(ENEMY_ZONE_COLS.keys())
        for hi, house in enumerate(houses):
            for r, c in nslots[hi * ENEMY_PER_HOUSE:(hi + 1) * ENEMY_PER_HOUSE]:
                hunt = arm["hunt_all"] or (house == "British"
                                           and arm["hunt_british"] > 0)
                units.append({"owner": house, "type": "MTNK", "row": r,
                              "col": c, "mission": "Hunt" if hunt else "Guard"})
    else:
        for house, (c0, c1) in ENEMY_ZONE_COLS.items():
            slots = grid_slots(ENEMY_UNIT_ROWS[0], ENEMY_UNIT_ROWS[1], c0, c1)
            assert len(slots) >= ENEMY_PER_HOUSE, (house, len(slots))
            for i, (r, c) in enumerate(slots[:ENEMY_PER_HOUSE]):
                hunt = arm["hunt_all"] or (house == "British"
                                           and i < arm["hunt_british"])
                units.append({"owner": house, "type": "MTNK", "row": r, "col": c,
                              "mission": "Hunt" if hunt else "Guard"})
    m["units"] = units
    # [W129] REAL footprint check (3x2), replacing the vacuous 2x2 one (§630-3).
    nap_cells = [(s["row"], s["col"]) for s in m["structures"]
                 if s["type"] == "NAPOWR"]
    ov_nap = overlap_cells_fp(nap_cells, *NAPOWR_FP)
    nap_ov_cells = overlap_cell_count_fp(nap_cells, *NAPOWR_FP)
    d["napowr_overlap_cells"] = nap_ov_cells
    # step3 must be strictly non-overlapping; step2 is the overlapping arm and
    # is expected to overlap (measured: 10 cells).
    assert ov_nap is None or napowr == NAPOWR_CELLS_STEP2, \
        ("NAPOWR overlap at %r in cell %s with step3 (cells=%d)"
         % (ov_nap, cell, nap_ov_cells))
    assert (nap_ov_cells == 0) == (napowr == NAPOWR_CELLS_STEP3), \
        ("NAPOWR overlap count %d does not match step arm %r in cell %s"
         % (nap_ov_cells, arm.get("napowr_step"), cell))
    return d


def apply_map_override(pkg: Path, text: str, label: str):
    """Append a rules-override section to the BUILT PACKAGE map (verbatim W88
    C4/C5 caveat: whether the scenario INI is parsed through the rules
    database is NOT statically provable - recorded, not resolved).  [W96]
    generalized: one call per appended section."""
    p = pkg / "RA2F_M1.MAP"
    b = p.read_bytes()
    sec = text.split("\r\n", 1)[0]
    if sec.encode("ascii") in b:
        raise RuntimeError("map already contains %s section" % sec)
    if not b.endswith(b"\r\n"):
        b += b"\r\n"
    b += text.encode("ascii")
    p.write_bytes(b)
    return {"file": "RA2F_M1.MAP", "label": label,
            "appended": text.replace("\r\n", "\\r\\n"),
            "size": len(b), "sha256": sha(b)}


def apply_crewed_override(pkg: Path):
    return apply_map_override(pkg, CREWED_OVERRIDE, "crewed")


def verify_pkg(sink, cell: str, pkg: Path, arm: dict) -> dict:
    dsn = spec_design(cell, arm)   # independent re-derivation for expectations
    rep = {"cell": cell, "pkg": str(pkg)}
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
    d["russian_htnk"] = t.count("=Russians,HTNK,")
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

    assert rep["battlemd"]["ra2f_scenario"] == 1, rep["battlemd"]
    assert rep["battlemd"]["official_scenario"] == 0, rep["battlemd"]
    assert rep["battlemd"]["bare_lf"] == 0, rep["battlemd"]
    assert d.get("NextScenario") == "", d
    assert d.get("EndOfGame") == "yes", d
    assert d.get("SkipMapSelect") == "no", d
    assert "0,0,%d,%d" % (MAP_N, MAP_N) in d.get("Size", ""), d
    assert rep["mapselmd"]["scenario_m1"] >= 1, rep["mapselmd"]
    assert d["loser_action"] and d["all_destroyed_russians_event"], d
    assert d["elapsed_1"], d
    assert not d["survive_tag"] and not d["winner_is_action"], d
    assert d["russian_nacnst"] == 1, d
    assert d["russian_napowr"] == 6, d
    assert d["russian_tesla"] == 12, d
    if arm.get("player_slow_clone"):
        assert d["russian_htnk"] == PLAYER_MTNK_N, d
        assert d["russian_mtnk"] == 0, d
    else:
        assert d["russian_mtnk"] == PLAYER_MTNK_N, d
        assert d["russian_htnk"] == 0, d
    assert d["gapowr_total"] == 3, d
    for house, want in (("british", ENEMY_PER_HOUSE),
                        ("confederation", ENEMY_PER_HOUSE),
                        ("arabs", ENEMY_PER_HOUSE)):
        assert d["%s_mtnk" % house] == want, (house, d)
    hunt_expected = (arm["hunt_all"] and 3 * ENEMY_PER_HOUSE) \
        or (arm["hunt_british"] or 0)
    assert d["hunt_mission"] == hunt_expected, (cell, d["hunt_mission"])
    _pn = max(1, int(round(PLAYER_MTNK_N * float(arm.get("unit_scale", 1.0)))))
    assert d["guard_mission"] == _pn + 3 * ENEMY_PER_HOUSE \
        - hunt_expected, (cell, d["guard_mission"])
    assert arm["crewed"] == d["crewed_override_present"], (cell, d)
    # [W96] map-INI override presence checks (APPEND evidence only - whether
    # the engine ADOPTS the override is exactly what m3/m4 measure live)
    d["speed_all_mtnk_override_present"] = bool(re.search(
        r"\[MTNK\]\s*Speed=1", t))
    d["player_slow_clone_override_present"] = bool(re.search(
        r"\[HTNK\]\s*.*?Speed=1", t, re.S))
    assert bool(arm.get("speed_all_mtnk")) == \
        d["speed_all_mtnk_override_present"], (cell, d)
    assert bool(arm.get("player_slow_clone")) == \
        d["player_slow_clone_override_present"], (cell, d)
    nap = NAPOWR_CELLS_STEP2 if arm["napowr_step"] == 2 else NAPOWR_CELLS_STEP3
    # [W129] footprint-aware: 3x2, not the vacuous 2x2 model (§630-3).
    _nap_ov = overlap_cell_count_fp(nap, *NAPOWR_FP)
    if nap == NAPOWR_CELLS_STEP3:
        assert overlap_cells_fp(nap, *NAPOWR_FP) is None, (nap, _nap_ov)
        assert _nap_ov == 0, ("step3 arm has %d overlapping cells" % _nap_ov)
    else:
        assert _nap_ov > 0, ("step2 arm expected to overlap, got %d" % _nap_ov)
    # [W98] enemy_zone geometry self-check on the re-derived design
    zone = arm.get("enemy_zone", "far")
    enemy_units = [u for u in dsn["missions"][0]["units"]
                   if u["owner"] in ENEMY_ZONE_COLS and u["type"] == "MTNK"]
    assert len(enemy_units) == 3 * ENEMY_PER_HOUSE, len(enemy_units)
    coords = [(u["row"], u["col"]) for u in enemy_units]
    assert len(set(coords)) == len(coords), "duplicate enemy cells"
    anchors = ([NACNST_CELL] + NAPOWR_CELLS_STEP3 + TESLA_CELLS
               + grid_slots(*PLAYER_UNIT_GRID)[:PLAYER_MTNK_N])
    dists = [chebyshev(r, c, anchors) for r, c in coords]
    rep["enemy_zone"] = {"zone": zone,
                         "dist_min": min(dists), "dist_max": max(dists),
                         "dist_mean": round(sum(dists) / len(dists), 3)}
    if zone == "near":
        # every enemy tank hugs the base: contact range, not a march
        # ( NOTE: a few near cells may overlap the OLD far-zone column ranges
        #   simply because they are within the fill radius of the base
        #   anchors - that is correct placement, not a far-zone leftover.)
        assert max(dists) <= 15, ("near zone max dist too large", max(dists))
    rep["verdict"] = "PASS"
    sink.step("package_verify_" + cell, **rep)
    return rep


def archive_inputs(sink, cell: str, design: dict, pkg: Path):
    adir = C.OUT / "inputs" / cell
    adir.mkdir(parents=True, exist_ok=True)
    rows = []
    dpath = adir / ("w94_design_%s.json" % cell)
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
    sink.step("inputs_archived", cell=cell, dir=str(adir), rows=rows)
    return rows


def normalize_arm(raw: dict) -> dict:
    unknown = set(raw) - set(VALID_ARM_KEYS)
    if unknown:
        raise RuntimeError("unknown arm keys: %r (valid: %r)"
                           % (sorted(unknown), VALID_ARM_KEYS))
    arm = {"hunt_all": bool(raw.get("hunt_all", False)),
           "hunt_british": int(raw.get("hunt_british", 0) or 0),
           "napowr_step": int(raw.get("napowr_step", 2) or 2),
           "crewed": bool(raw.get("crewed", False)),
           "speed_all_mtnk": bool(raw.get("speed_all_mtnk", False)),
           "player_slow_clone": bool(raw.get("player_slow_clone", False)),
           "enemy_zone": str(raw.get("enemy_zone", "far") or "far")}
    if arm["enemy_zone"] not in ENEMY_ZONE_KNOBS:
        raise RuntimeError("enemy_zone must be far|near: %r"
                           % arm["enemy_zone"])
    if arm["napowr_step"] not in (2, 3):
        raise RuntimeError("napowr_step must be 2 or 3: %r" % arm["napowr_step"])
    if not 0 <= arm["hunt_british"] <= ENEMY_PER_HOUSE:
        raise RuntimeError("hunt_british out of range: %r" % arm["hunt_british"])
    if arm["hunt_all"] and arm["hunt_british"]:
        raise RuntimeError("hunt_all and hunt_british are mutually exclusive")
    if arm["speed_all_mtnk"] and arm["player_slow_clone"]:
        raise RuntimeError("speed_all_mtnk and player_slow_clone are "
                           "mutually exclusive")
    return arm


def main() -> int:
    spec_path = os.environ.get("W94_CELL_SPEC", "").strip()
    if not spec_path:
        raise SystemExit("W94_CELL_SPEC (path to cell spec JSON) required")
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    cell = str(spec["cell"]).strip()
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", cell):
        raise SystemExit("invalid cell id %r" % cell)
    arm = normalize_arm(spec.get("arm") or {})

    sink = L.Sink("build_" + cell)
    ok = False
    rep = {"cell": cell, "arm": arm}
    try:
        sink.step("meta_start", kind="meta_start", phase=TAG,
                  note="offline build of ONE matrix cell: NO gamemd.exe; "
                       "W85 green geometry generalized from W88 (D4 archive "
                       "per cell)", cell=cell, arm=arm, v15=str(C.V15),
                  feature_set=str(C.FEATURE_SET))
        residual = L.list_gamemd()
        sink.step("pre_launch_guard_offline", gamemd_processes=residual, n=len(residual))
        if residual:
            raise RuntimeError("residual gamemd at offline build phase: %r" % residual)

        design = spec_design(cell, arm)
        dpath = C.design_path(cell)
        dpath.parent.mkdir(parents=True, exist_ok=True)
        dpath.write_text(json.dumps(design, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        rep["design"] = {"path": str(dpath),
                         "n_struct": len(design["missions"][0]["structures"]),
                         "n_units": len(design["missions"][0]["units"]),
                         "size": design["missions"][0]["size"]}
        out_dir = C.WORK / ("pkg_" + cell)
        out_dir.mkdir(parents=True, exist_ok=True)
        rec = C.v15_cmd(sink, "build_" + cell,
                        ["build", "--design", str(dpath), "--out", str(out_dir),
                         "--feature-set", str(C.FEATURE_SET)])
        if rec["exit_code"] != 0:
            raise RuntimeError("build cell %s exit %s: %s" %
                               (cell, rec["exit_code"], rec["stderr_tail"][-2500:]))
        pkg = C.pkg_path(cell)
        assert pkg.is_dir(), pkg
        (pkg / "ra2forge_package.json").write_text(
            json.dumps({"tool": "ra2forge",
                        "package_id": design["package"]["id"],
                        "package_version": "1.0"}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        crewed_edit = None
        if arm["crewed"]:
            crewed_edit = apply_crewed_override(pkg)
            sink.step("crewed_override_applied", cell=cell, **crewed_edit)
        map_edits = [e for e in (crewed_edit,) if e]
        if arm["speed_all_mtnk"]:
            e1 = apply_map_override(pkg, SPEED_ALL_MTNK_OVERRIDE,
                                    "speed_all_mtnk")
            sink.step("speed_all_mtnk_override_applied", cell=cell, **e1)
            map_edits.append(e1)
        if arm["player_slow_clone"]:
            e2 = apply_map_override(pkg, PLAYER_SLOW_CLONE_OVERRIDE,
                                    "player_slow_clone")
            sink.step("player_slow_clone_override_applied", cell=cell, **e2)
            map_edits.append(e2)
        rep["build"] = {"pkg": str(pkg), "exit_code": rec["exit_code"],
                        "crewed_edit": crewed_edit, "map_edits": map_edits}
        rep["verify"] = verify_pkg(sink, cell, pkg, arm)
        rep["inputs"] = archive_inputs(sink, cell, design, pkg)
        rep["w59_offsets"] = {"scen_ptr": "0x00A8B230",
                              "filename": "+0x125C", "stage_idx": "+0x35A0",
                              "end_of_game": "+0x34AC", "skip_score": "+0x34AE",
                              "skip_mapsel": "+0x34B0", "battle_idx": "+0x34CC",
                              "frame": "0x00A8ED84"}
        ok = True
        sink.step("build_result", ok=ok, cell=cell)
    except Exception as e:
        sink.step("FATAL", error=repr(e), traceback=traceback.format_exc()[-6000:])
    finally:
        (C.OUT / ("BUILD_%s.json" % cell)).write_text(
            json.dumps(rep, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        sink.step("meta_end", kind="meta_end", phase=TAG, ok=ok, cell=cell,
                  gamemd_residual=L.list_gamemd(), lock_content=C.lock_read())
        sink.close()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
