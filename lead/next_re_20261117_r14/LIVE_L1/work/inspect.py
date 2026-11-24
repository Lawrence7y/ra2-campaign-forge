#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 inspect: full snapshot of NAPOWR objects (o1/cell/lenA), globals, hover, player buildings."""
import os, sys, ctypes, json, struct
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from PIL import ImageGrab

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID = os.path.join(CARD, "EVIDENCE")
HOVER = 0x88095C
k32 = ctypes.windll.kernel32
b4 = ctypes.create_string_buffer(4); got = ctypes.c_size_t(0)
def rd(m, va):
    if k32.ReadProcessMemory(m.h, ctypes.c_void_p(va), b4, 4, ctypes.byref(got)) and got.value == 4:
        return struct.unpack('<I', b4.raw)[0]
    return None
def hcell(m):
    v = rd(m, HOVER); return (v & 0xFFFF, (v >> 16) & 0xFFFF) if v else (None, None)

def main():
    pid = W.pid_of()
    if not pid: print("no gamemd"); return 2
    m = W.Mem(pid); ph = P.player_house(m)
    out = {"pid": pid, "frame": m.u32(W.A_FRAME), "mode": m.u32(W.A_MODE),
           "objects": m.u32(W.A_ABSTRACT), "playerHouse": hex(ph) if ph else None,
           "credits": rd(m, ph+0x30C), "hover": hcell(m),
           "cam": (rd(m, 0x886FA0), rd(m, 0x886FA4)),
           "bypass": D.bypass_globals(m)}
    # all building objects with detail
    blds = []
    for i, obj in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, obj)
        if b["owner_21C"] != ph:
            continue
        nm, _ = D.rtti_name(m, obj)
        cell = b["cell"]
        blds.append({"obj": hex(obj), "type": b["type"],
                     "o1_81": b["o1_81"], "o2_74": b["o2_74"], "o3_80": b["o3_80"],
                     "cell": [cell["cellX"], cell["cellY"]], "valid": cell["valid"],
                     "lenA": b["chains"]["lenA"], "lenB": b["chains"]["lenB"],
                     "canplace_1AC_u8": m.u8(obj+0x1AC),
                     "rtti": nm})
    out["player_buildings"] = blds
    m.close()
    tag = sys.argv[1] if len(sys.argv) > 1 else "inspect"
    json.dump(out, open(os.path.join(EVID, tag + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID, tag + ".png"))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
