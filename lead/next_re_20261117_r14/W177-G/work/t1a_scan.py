#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1a hover-cell global finder — rigorous differential delta-signature scan.

Read-only: ReadProcessMemory of .data + synthetic SetCursorPos. No memory writes/inject.
Method:
  - Move cursor to base P0 (safe zone, >=200px from edges/sidebar).
  - P1 = P0 + (+10 X-cell) screen delta ; P2 = P0 + (+10 Y-cell) delta.
  - Snapshot whole .data (0x812000..0xB79BE4) as aligned dwords at each.
  - Find dwords whose delta matches a cell-coordinate signature:
      packed (Y<<9)+X : dX=+10, dY=+5120
      CellStruct lo=X : low16 dX=+10 ; hi=Y: high16 dY=+10
      separate X dword: +10 ; separate Y dword: +10
      lepton coords   : +2560
  - Also record value trace across a 5-point path for candidate validation.
Usage: t1a_scan.py <tag>
"""
import sys, os, time, ctypes, struct, json
from ctypes import wintypes as wt
import w177_core as W
import wc_probe as C

u32 = ctypes.windll.user32
u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.GetCursorPos.argtypes = [ctypes.POINTER(wt.POINT)]

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")

# .data section (physical VA, image already loaded at ImageBase 0x400000)
DATA_BASE = 0x00812000
DATA_SIZE = 0x00367BE4   # ends 0xB79BE4
N = DATA_SIZE // 4

# Jacobian (screen px per cell), from W177-F calibrated inverse:
#   +1 X cell -> (+50.85, +28.08) px ; +1 Y cell -> (-70.35, +28.34) px
JX = (50.85, 28.08)
JY = (-70.35, 28.34)
K = 10  # cells to move

def move(x, y, dwell=0.6):
    u32.SetCursorPos(int(x), int(y))
    time.sleep(dwell)
    pt = wt.POINT()
    u32.GetCursorPos(ctypes.byref(pt))
    return (pt.x, pt.y)

def snap(m):
    """Read .data as N aligned dwords. Returns list[int] or None."""
    buf = ctypes.create_string_buffer(DATA_SIZE)
    got = ctypes.c_size_t(0)
    ok = W.k32.ReadProcessMemory(m.h, ctypes.c_void_p(DATA_BASE), buf, DATA_SIZE, ctypes.byref(got))
    if not ok or got.value != DATA_SIZE:
        print("RPM failed got=%s need=%s" % (got.value, DATA_SIZE))
        return None
    return list(struct.unpack_from("<%dI" % N, buf.raw, 0))

def s16(v):
    v &= 0xFFFF
    return v - 0x10000 if v & 0x8000 else v

def classify(v0, vx, vy):
    """Return matching signature tags for a dword across base / X-move / Y-move."""
    tags = []
    d_x = (vx - v0) & 0xFFFFFFFF
    d_y = (vy - v0) & 0xFFFFFFFF
    # signed deltas
    def sd(a, b):
        d = (b - a) & 0xFFFFFFFF
        return d - 0x100000000 if d & 0x80000000 else d
    sx = sd(v0, vx); sy = sd(v0, vy)
    # packed index (Y<<9)+X : X-move +K, Y-move +K*512
    if sx == K and sy == K * 512:
        tags.append("packed_XpYp")
    if sx == -K and sy == -K * 512:
        tags.append("packed_XmYm")
    if sx == K and sy == -K * 512:
        tags.append("packed_XpYm")
    if sx == -K and sy == K * 512:
        tags.append("packed_XmYp")
    # separate X dword: changes on X-move only
    if sx in (K, -K) and sy == 0:
        tags.append("sep_X")
    # separate Y dword: changes on Y-move only
    if sy in (K, -K) and sx == 0:
        tags.append("sep_Y")
    # CellStruct {short X (lo), short Y (hi)}
    lo_dx = s16(vx) - s16(v0) if False else ((vx & 0xFFFF) - (v0 & 0xFFFF))
    hi_dy = ((vy >> 16) & 0xFFFF) - ((v0 >> 16) & 0xFFFF)
    lo_dy = ((vy & 0xFFFF) - (v0 & 0xFFFF))
    hi_dx = ((vx >> 16) & 0xFFFF) - ((v0 >> 16) & 0xFFFF)
    if lo_dx in (K, -K) and hi_dy in (K, -K) and lo_dy == 0 and hi_dx == 0:
        tags.append("cellstruct_XY")
    # lepton coords
    if sx in (K*256, -K*256) and sy == 0:
        tags.append("lepton_X")
    if sy in (K*256, -K*256) and sx == 0:
        tags.append("lepton_Y")
    return tags

def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "t1a"
    pid = W.pid_of()
    if not pid:
        print("no gamemd"); return 2
    m = W.Mem(pid)
    # base position: safe zone
    P0 = (1300, 600)
    P1 = (P0[0] + K*JX[0], P0[1] + K*JX[1])   # +K X cells
    P2 = (P0[0] + K*JY[0], P0[1] + K*JY[1])   # +K Y cells
    P0r = P0  # return to base for stability
    positions = [("base", P0), ("Xplus", P1), ("Yplus", P2), ("return", P0r)]
    snaps = {}
    trace_meta = []
    for name, (x, y) in positions:
        actual = move(x, y, 0.7)
        cam = C.cam_origin(m)
        s = snap(m)
        if s is None:
            m.close(); return 3
        snaps[name] = s
        trace_meta.append({"name": name, "want": [x, y], "actual": list(actual),
                           "cam": cam, "frame": m.u32(W.A_FRAME)})
        print("%-7s want=(%.0f,%.0f) actual=%s cam=%s" % (name, x, y, actual, cam))
        # save each snapshot compressed (raw dword list -> json is huge; store as binary)
        with open(os.path.join(EVID, "t1a_%s_%s.bin" % (tag, name)), "wb") as f:
            f.write(struct.pack("<%dI" % N, *s))

    base = snaps["base"]; xp = snaps["Xplus"]; yp = snaps["Yplus"]; ret = snaps["return"]
    # stability: base vs return should agree on nearly all dwords (game logic noise aside)
    results = []
    for i in range(N):
        v0 = base[i]; vx = xp[i]; vy = yp[i]; vr = ret[i]
        tags = classify(v0, vx, vy)
        if tags:
            va = DATA_BASE + i*4
            results.append({"addr": "0x%08X" % va, "offset": "0x%X" % (i*4),
                            "v_base": v0, "v_xplus": vx, "v_yplus": vy, "v_return": vr,
                            "tags": tags,
                            "base_eq_return": (v0 == vr)})
    out = {"tag": tag, "pid": pid,
           "data_base": hex(DATA_BASE), "data_size": hex(DATA_SIZE),
           "K": K, "JX": JX, "JY": JY,
           "positions": trace_meta,
           "n_dwords": N, "n_candidates": len(results),
           "candidates": results}
    op = os.path.join(EVID, "t1a_%s_scan.json" % tag)
    with open(op, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("scanned %d dwords, %d signature candidates -> %s" % (N, len(results), op))
    for r in results[:80]:
        print("  %s v=%08X/%08X/%08X tags=%s ret_eq=%s" % (
            r["addr"], r["v_base"], r["v_xplus"], r["v_yplus"], ",".join(r["tags"]), r["base_eq_return"]))
    m.close()
    return 0

if __name__ == "__main__":
    sys.exit(main())
