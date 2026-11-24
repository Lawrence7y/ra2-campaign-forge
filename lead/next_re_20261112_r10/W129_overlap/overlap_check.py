#!/usr/bin/env python3
"""W129: CORRECT footprint-based overlap checker for ②-b (成因 A).

Why this exists
---------------
`w94_build.py:overlap_cells()` hardcodes a **2x2** footprint for every building:
    def overlap_cells(cells):
        \"\"\"2x2 footprint check: (r,c) covers rows r..r+1, cols c..c+1.\"\"\"
For NAPOWR the real footprint is **3x2** (measured; see below), so with column
spacing 2 -> spans 46-48,48-50,... which DO overlap, yet the 2x2 model gives
46-47,48-49,... which do NOT. Result: `assert overlap_cells(...) is None` is
**vacuously true** and the guard has never actually checked anything
(ledger §630-3 flagged this as an 整改项).

Footprint evidence for NAPOWR = 3x2
-----------------------------------
* ledger §669: 真机测得 "16 格 = 4x4，6 格 = 3x2"; NAPOWR is the only building
  whose spacing the experiments vary, and 3x2 is the 6-cell shape.
* independent arithmetic check (this script's selftest): with width 3 and
  step 2, adjacent buildings share exactly 1 column x 2 rows = 2 cells, and
  there are 5 adjacent pairs -> **10 overlapping cells**, which reproduces the
  hand-computed "10 格" from ledger §630-3 that had never been verified by a
  tool. With step 3 -> 0. This is a *falsifiable* consistency check, not an
  assumption: if the footprint were 2x2 the count would be 0, not 10.

Footprints are per-type and MUST be supplied explicitly: an unknown type is a
hard error (fail-closed), never silently defaulted -- that is exactly the bug
class this replaces.
"""
from __future__ import annotations

import argparse
import json
import sys

# Type -> (width, height). Only entries that are actually evidenced are listed.
# NAPOWR: 3x2 (see module docstring).
FOOTPRINTS = {
    "NAPOWR": (3, 2),
}


def footprint_cells(row: int, col: int, w: int, h: int):
    """Cells covered by a building anchored at (row,col) with footprint (w,h).

    RA2 anchors a building's footprint at its top-left (north-west) cell for
    the purposes of occupancy (ledger §2.4: footprint coords are relative to
    the anchor, which is (trunc(x/256), trunc(y/256)))."""
    return {(row + dy, col + dx) for dy in range(h) for dx in range(w)}


def overlap_report(structures, footprints=None):
    """Return (occupied_cell_map, collisions, overlapping_cell_count).

    structures: iterable of dicts with 'type', 'row', 'col'.
    footprints: mapping type -> (w,h); defaults to FOOTPRINTS.
    Unknown type -> ValueError (fail-closed).
    """
    fp = dict(FOOTPRINTS if footprints is None else footprints)
    occupied = {}          # cell -> list of building indices
    per_building = []      # index -> set of cells
    for i, s in enumerate(structures):
        t = s["type"]
        if t not in fp:
            raise ValueError("no footprint known for building type %r "
                             "(refusing to guess; add it to FOOTPRINTS)" % (t,))
        w, h = fp[t]
        cells = footprint_cells(int(s["row"]), int(s["col"]), w, h)
        per_building.append(cells)
        for c in cells:
            occupied.setdefault(c, []).append(i)

    collisions = {c: idxs for c, idxs in occupied.items() if len(idxs) > 1}
    return occupied, per_building, collisions


def summarize(structures, footprints=None):
    occupied, per_building, collisions = overlap_report(structures, footprints)
    involved = sorted({i for idxs in collisions.values() for i in idxs})
    return {
        "buildings": len(per_building),
        "cells_total": sum(len(c) for c in per_building),
        "overlapping_cells": len(collisions),
        "buildings_involved": len(involved),
        "pairs": len({tuple(sorted(idxs)) for idxs in collisions.values()}),
    }


def selftest():
    # W85 control geometry, verbatim from w94_build.py
    STEP2 = [(56, 46), (56, 48), (56, 50), (56, 52), (56, 54), (56, 56)]
    STEP3 = [(56, 46), (56, 49), (56, 52), (56, 55), (56, 58), (56, 61)]
    ok = True

    print("=== selftest: NAPOWR 3x2 ===")
    for name, cells, expect in (("step2", STEP2, 10), ("step3", STEP3, 0)):
        st = [{"type": "NAPOWR", "row": r, "col": c} for r, c in cells]
        s = summarize(st)
        good = s["overlapping_cells"] == expect
        ok &= good
        print("  %-6s overlapping_cells=%-3d expect=%-3d  %s   (%d buildings, %d cells total)"
              % (name, s["overlapping_cells"], expect, "OK" if good else "FAIL",
                 s["buildings"], s["cells_total"]))

    print("\n=== falsification: if the footprint were 2x2 the step2 count would be 0 ===")
    st2 = [{"type": "NAPOWR", "row": r, "col": c} for r, c in STEP2]
    s22 = summarize(st2, {"NAPOWR": (2, 2)})
    print("  2x2 model -> overlapping_cells=%d  (this is why the old assert was vacuous)"
          % s22["overlapping_cells"])
    ok &= (s22["overlapping_cells"] == 0)

    print("\n=== fail-closed on unknown type ===")
    try:
        summarize([{"type": "NOCRLD_X", "row": 0, "col": 0}])
        print("  FAIL: unknown type was accepted")
        ok = False
    except ValueError as e:
        print("  OK: raised -> %s" % str(e)[:80])

    print("\nSELFTEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--design", help="design JSON containing {'structures': [...]}")
    ap.add_argument("--json", action="store_true", help="emit JSON summary")
    a = ap.parse_args()

    if a.selftest:
        return selftest()
    if a.design:
        d = json.load(open(a.design, encoding="utf-8"))
        st = d.get("structures") or d.get("map", {}).get("structures") or []
        try:
            s = summarize(st)
        except ValueError as e:
            print("ERROR: %s" % e)
            print("       (add the missing type to FOOTPRINTS after evidencing it)")
            return 2
        if a.json:
            print(json.dumps(s, indent=2))
        else:
            for k, v in s.items():
                print("%-20s %s" % (k, v))
        return 0 if s["overlapping_cells"] == 0 else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
