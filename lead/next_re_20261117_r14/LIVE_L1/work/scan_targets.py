#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 scan_targets: enumerate player InfantryClass / UnitClass objects by cell from
AbstractClass::Array; report cell groups with counts and a stability re-read after a delay.
Read-only."""
import os, sys, ctypes, json, time
from collections import Counter
import w177_core as W
import wb_probe as P
import dsnap as D

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID = os.path.join(CARD, "EVIDENCE")

def scan(m, ph):
    aitems = m.u32(P.A_ABSTRACT_ITEMS); acount = m.u32(P.A_ABSTRACT)
    inf = Counter(); veh = Counter()
    inf_objs = {}; veh_objs = {}
    for i in range(acount):
        q = m.u32(aitems + 4*i)
        if not q or (q & 3): continue
        if m.u32(q+0x21C) != ph: continue
        nm, _ = D.rtti_name(m, q)
        if not nm: continue
        lx = m.u32(q+0x9C); ly = m.u32(q+0xA0)
        if lx is None or ly is None: continue
        cx, cy = (lx >> 8), (ly >> 8)
        if 'InfantryClass' in nm:
            inf[(cx, cy)] += 1; inf_objs.setdefault((cx, cy), []).append(hex(q))
        elif 'UnitClass' in nm:
            veh[(cx, cy)] += 1; veh_objs.setdefault((cx, cy), []).append(hex(q))
    return inf, veh, inf_objs, veh_objs

def main():
    delay = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
    tag = sys.argv[2] if len(sys.argv) > 2 else "targets"
    pid = W.pid_of()
    if not pid: print("no gamemd"); return 2
    m = W.Mem(pid); ph = P.player_house(m)
    inf1, veh1, io1, vo1 = scan(m, ph)
    time.sleep(delay)
    inf2, veh2, io2, vo2 = scan(m, ph)
    out = {"pid": pid, "delay_s": delay,
           "inf_cells": [{"cell": list(k), "n": v, "objs": io1[k]} for k, v in sorted(inf1.items())],
           "veh_cells": [{"cell": list(k), "n": v, "objs": vo1[k]} for k, v in sorted(veh1.items())],
           "inf_stable": {str(k): (inf1.get(k,0), inf2.get(k,0)) for k in set(inf1)|set(inf2)},
           "veh_stable": {str(k): (veh1.get(k,0), veh2.get(k,0)) for k in set(veh1)|set(veh2)},
           "frame": m.u32(W.A_FRAME)}
    m.close()
    json.dump(out, open(os.path.join(EVID, tag + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("inf cells:", [(k, v) for k, v in sorted(inf1.items())])
    print("veh cells:", [(k, v) for k, v in sorted(veh1.items())])
    print("saved", tag)
    return 0

if __name__ == "__main__":
    sys.exit(main())
