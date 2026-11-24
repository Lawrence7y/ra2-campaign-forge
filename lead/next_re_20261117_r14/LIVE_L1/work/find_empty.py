#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 find_empty: scan a cell rect for cells with no units/buildings in either chain.
Read-only. Also verify cell->screen mapping via 0x88095C after SetCursorPos."""
import os, sys, ctypes, json, struct, time
import w177_core as W
import wb_probe as P
import dsnap as D

CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID = os.path.join(CARD, "EVIDENCE")
HOVER = 0x88095C
k32 = ctypes.windll.kernel32; u32 = ctypes.windll.user32
b4 = ctypes.create_string_buffer(4); got = ctypes.c_size_t(0)
def rd(m, va):
    if k32.ReadProcessMemory(m.h, ctypes.c_void_p(va), b4, 4, ctypes.byref(got)) and got.value == 4:
        return struct.unpack('<I', b4.raw)[0]
    return None
def hcell(m):
    v = rd(m, HOVER); return (v & 0xFFFF, (v >> 16) & 0xFFFF) if v else (None, None)

def cell_ptr(m, cx, cy):
    base = m.u32(P.CELL_ARRAY)
    idx = (cy << 9) + cx
    if not base or idx < 0 or idx >= 0x40000: return None
    c = m.u32(base + idx*4)
    return c if (c and c != P.INVALID_CELL) else None

def occupied(m, cx, cy):
    c = cell_ptr(m, cx, cy)
    if not c: return True  # invalid/void treated as not-usable
    hA = m.u32(c+0xE4); hB = m.u32(c+0xE8)
    return bool(hA or hB)

def main():
    pid = W.pid_of()
    if not pid: print("no gamemd"); return 2
    m = W.Mem(pid)
    # occupied cells from targets
    out = {"frame": m.u32(W.A_FRAME), "empty": []}
    # scan x 100..120, y 50..68
    for cy in range(50, 69):
        for cx in range(100, 121):
            c = cell_ptr(m, cx, cy)
            if not c: continue
            if not occupied(m, cx, cy):
                out["empty"].append([cx, cy])
    # cell->screen calibration: JX=(55.6,25.9) JY=(-55.6,25.9), anchor (111,60)->(1400,600)
    try:
        u32.SetProcessDPIAware()
    except Exception:
        pass
    u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
    class PNT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    def probe_screen(sx, sy):
        u32.SetCursorPos(int(sx), int(sy)); time.sleep(0.25)
        return hcell(m)
    cal = []
    for sx, sy in [(1400,600),(1456,626),(1344,574),(1400,652),(1512,652)]:
        cal.append({"screen":[sx,sy],"hover":probe_screen(sx,sy)})
    out["calibration"] = cal
    m.close()
    tag = sys.argv[1] if len(sys.argv)>1 else "empty_scan"
    json.dump(out, open(os.path.join(EVID, tag+".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("empty count", len(out["empty"]))
    print("empty sample", out["empty"][:40])
    print("calibration", cal)
    return 0

if __name__ == "__main__":
    sys.exit(main())
