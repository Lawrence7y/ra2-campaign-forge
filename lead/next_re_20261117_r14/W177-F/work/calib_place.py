#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-F T1 calibration: place one NAPOWR at a known cursor client pixel,
read back the actual occupied cells (via cell+0xE4 chain containing this object),
record camera scroll origin before/after and the building's Location cell.
Read-only memory + synthetic input; no writes to game process.
Usage: calib_place.py <sx> <sy> <tag>
"""
import sys, os, time, json, ctypes, struct
from ctypes import wintypes as wt
import w177_core as W
import wb_probe as P
import wc_probe as C

HERE = os.path.dirname(os.path.abspath(__file__))
EVID = os.path.join(os.path.dirname(HERE), "EVIDENCE")
u32 = ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
u32.mouse_event.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD, wt.DWORD, ctypes.c_size_t]
LD, LU = 0x0002, 0x0004
ICON = (2328, 480)

def bare_click(x, y):
    u32.SetCursorPos(x, y); time.sleep(0.15)
    u32.mouse_event(LD, 0, 0, 0, 0); time.sleep(0.07); u32.mouse_event(LU, 0, 0, 0, 0); time.sleep(0.12)

def player_napowr(m, ph):
    items = m.u32(P.A_ABSTRACT_ITEMS); count = m.u32(P.A_ABSTRACT)
    out = []
    for i in range(count):
        p = m.u32(items + 4 * i)
        if not p or (p & 3): continue
        if m.u32(p) == 0x7E3EBC and m.u32(p + 0x21C) == ph and P.ascii_at(m, m.u32(p + 0x520) + 0x24, 12) == "NAPOWR":
            out.append(p)
    return out

def obj_to_cell_xy(m, obj):
    x = m.u32(obj + P.O_LOCX); y = m.u32(obj + P.O_LOCY)
    if x is None or y is None: return None
    def s32(u):
        u &= 0xFFFFFFFF
        return u - 0x100000000 if u & 0x80000000 else u
    return (s32(x) >> 8, s32(y) >> 8)

def footprint_cells(m, target, maxcells=(0x40000)):
    """Scan whole cell array; return sorted [(cx,cy)] where target is on cell+0xE4 chain."""
    base = m.u32(P.CELL_ARRAY)
    if not base: return []
    hits = []
    mapc = P.MAP_SINGLETON
    w = m.u32(mapc + 0x14C); h = m.u32(mapc + 0x150)
    if not w or not h or w > 1024 or h > 1024: return []
    # bulk read each row
    import ctypes as C2
    for cy in range(h):
        rb = base + (cy << 9) * 4
        buf = C2.create_string_buffer(w * 4); got = C2.c_size_t(0)
        if not W.k32.ReadProcessMemory(m.h, C2.c_void_p(rb), buf, w * 4, C2.byref(got)): continue
        for cx in range(w):
            cell = int.from_bytes(buf.raw[cx*4:cx*4+4], "little")
            if not cell or cell == P.INVALID_CELL: continue
            p = m.u32(cell + 0xE4); seen = set()
            while p and p not in seen and len(seen) < 16:
                seen.add(p)
                if p == target:
                    hits.append((cx, cy)); break
                p = m.u32(p + 0x30)
    return sorted(hits)

def main():
    sx = int(sys.argv[1]); sy = int(sys.argv[2]); tag = sys.argv[3]
    pid = W.pid_of(); m = W.Mem(pid); ph = P.player_house(m)
    c0 = m.u32(ph + 0x30C)
    before = set(player_napowr(m, ph))
    rec = {"tag": tag, "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "pid": pid,
           "frame0": m.u32(W.A_FRAME), "credit_before": c0,
           "screen": [sx, sy], "cam_before": C.cam_origin(m),
           "existing_napowr": [hex(x) for x in before]}
    # order
    bare_click(*ICON); time.sleep(0.5)
    rec["credit_after_order"] = m.u32(ph + 0x30C)
    # wait ready: credit settles near c0-600 (allow harvester drift +-40); fallback fixed 5s
    target_credit = c0 - 600
    ready = False
    for _ in range(30):
        time.sleep(0.3)
        cc = m.u32(ph + 0x30C)
        if abs(cc - target_credit) <= 40:
            ready = True; break
    time.sleep(0.8)
    rec["credit_ready"] = m.u32(ph + 0x30C); rec["frame_ready"] = m.u32(W.A_FRAME); rec["ready_seen"] = ready
    # pickup
    bare_click(*ICON); time.sleep(0.35)
    u32.SetCursorPos(sx, sy); time.sleep(0.6)
    rec["cam_preclick"] = C.cam_origin(m)
    rec["cursor_preclick"] = [sx, sy]
    # screenshot footprint before click
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab(all_screens=False)
        img.save(os.path.join(EVID, "calib_%s_hover.png" % tag))
        # crop around cursor
        img.crop((max(0,sx-300),max(0,sy-250),min(2560,sx+300),min(1440,sy+250))).save(
            os.path.join(EVID, "calib_%s_hover_crop.png" % tag))
    except Exception as e:
        rec["shot_err"] = str(e)
    # sample high-freq around the click (2s) -- needed for T3 anyway
    cellbase = m.u32(P.CELL_ARRAY)
    # target cell unknown here (calibration on empty area); sample generic globals
    rows = []
    import w177_core as WC
    t0 = time.perf_counter(); clicked = False; click_t = None
    while True:
        t = time.perf_counter() - t0
        if not clicked and t >= 0.35:
            u32.mouse_event(LD, 0, 0, 0, 0); u32.mouse_event(LU, 0, 0, 0, 0)
            click_t = t; clicked = True
        rows.append([round(t,6), m.u32(WC.A_FRAME), C.cam_origin(m)["cam_x"], C.cam_origin(m)["cam_y"],
                     m.u32(0xA8E7AC), m.u8(0xA8E9A0)])
        if t >= 2.0: break
    wall = time.perf_counter() - t0
    hpath = os.path.join(EVID, "calib_%s_hifreq.jsonl" % tag)
    with open(hpath, "w", encoding="utf-8") as f:
        f.write(json.dumps({"tag":tag,"columns":["t","frame","cam_x","cam_y","a8e7ac","a8e9a0"],
                            "n":len(rows),"wall":wall,"rate":len(rows)/wall,"click_t":click_t},ensure_ascii=False)+"\n")
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    rec["hifreq_n"]=len(rows); rec["hifreq_rate"]=len(rows)/wall; rec["click_t"]=click_t
    rec["cam_postclick"] = C.cam_origin(m)
    time.sleep(1.0)
    # verify
    after = set(player_napowr(m, ph)); new = after - before
    rec["credit_after"] = m.u32(ph + 0x30C)
    rec["new_napowr"] = [hex(x) for x in new]
    rec["result"] = {}
    for obj in new:
        cells = footprint_cells(m, obj)
        rec["result"][hex(obj)] = {"location_cell": obj_to_cell_xy(m, obj),
                                    "occupied_cells": cells,
                                    "n_cells": len(cells)}
    # append to calibration jsonl
    with open(os.path.join(EVID, "calibration.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    opath = os.path.join(EVID, "calib_%s.json" % tag)
    with open(opath, "w", encoding="utf-8") as f: json.dump(rec, f, ensure_ascii=False, indent=2)
    print(json.dumps({k:rec[k] for k in ("tag","screen","cam_before","cam_preclick","cam_postclick","credit_before","credit_after","new_napowr","result","hifreq_rate")}, ensure_ascii=False))
    m.close(); return 0

if __name__ == "__main__": sys.exit(main())
