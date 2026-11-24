#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整只读快照：globals / houses+credits候选 / 全部BuildingClass详情 / 指定credits值扫描。
输出 JSON 到 stdout；--out 可选写文件（写到 W177-B/EVIDENCE）。"""
import argparse
import json
import os
import sys
import time

import w177_core as W
import wb_probe as P

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")


def hexn(v):
    return hex(v) if isinstance(v, int) and v else (None if not v else v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="snap")
    ap.add_argument("--scan-credit", type=int, default=None,
                    help="scan PlayerHouse for this displayed credits value (and *100)")
    ap.add_argument("--scan-size", type=int, default=0x160C0)
    ap.add_argument("--list-buildings", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    pid = W.pid_of()
    if not pid:
        print("no gamemd")
        return 2
    m = W.Mem(pid)
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "pid": pid,
           "globals": P.globals_snapshot(m)}
    ph = P.player_house(m)
    rec["playerHouse"] = hexn(ph)
    if ph:
        rec["playerHouse_fields"] = {
            "arrayIndex": m.u32(ph + P.HOUSE_ARRAYINDEX),
            "startingCredits": m.u32(ph + P.HOUSE_STARTINGCREDITS),
            "currentPlayer": m.u8(ph + P.HOUSE_CURRENTPLAYER),
            "playerControl": m.u8(ph + P.HOUSE_PLAYERCONTROL),
        }
    hitems, hcount, houses = P.house_array(m)
    rec["houseArray"] = {"items": hexn(hitems), "count": hcount,
                         "houses": [{"i": i, "h": hexn(h)} for i, h in houses]}
    if ph and a.scan_credit is not None:
        scan = {}
        for mult, val in [("x1", a.scan_credit), ("x100", a.scan_credit * 100)]:
            hits = P.scan_dword(m, ph, a.scan_size, val)
            scan[mult] = {"value": val, "offsets": [hex(o) for o in hits]}
        rec["creditScan"] = scan
    if a.list_buildings:
        aitems, acount, bl = P.enumerate_buildings(m)
        rec["buildings"] = {
            "abstractItems": hexn(aitems), "abstractCount": acount, "n": len(bl),
            "list": [P.one_building(m, i, obj) for i, obj in bl]
        }
    out = json.dumps(rec, ensure_ascii=False, indent=2)
    print(out)
    if a.out:
        path = a.out if os.path.isabs(a.out) else os.path.join(EVID, a.out)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out + "\n")
        print("saved -> %s" % path, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
