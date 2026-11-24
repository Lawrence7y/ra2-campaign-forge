#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-F T1 calibration v2: order NAPOWR, pickup ghost, hover each candidate,
click only on a GREEN footprint; read back occupied cells + Location + camera.
Read-only memory + synthetic input. Usage: calib_place2.py <tag> x1,y1 x2,y2 ...
"""
import sys, os, time, json, ctypes, struct
from ctypes import wintypes as wt
from PIL import ImageGrab
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

def footprint_cells(m, target):
    base = m.u32(P.CELL_ARRAY); mapc = P.MAP_SINGLETON
    w = m.u32(mapc + 0x14C); h = m.u32(mapc + 0x150)
    hits = []
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
                if p == target: hits.append((cx, cy)); break
                p = m.u32(p + 0x30)
    return sorted(hits)

def colors(img, sx, sy, rad=140):
    px = img.convert("RGB").load(); red=green=0
    for y in range(max(0,sy-rad), min(1440,sy+rad)):
        for x in range(max(0,sx-rad), min(2560,sx+rad)):
            R,G,B = px[x,y]
            if R>150 and G<90 and B<90: red+=1
            if G>140 and R<120 and B<120: green+=1
    return red,green

def sample_click(pid, dur=2.0, click_at=0.35, tag="x"):
    import w177_core as WC
    m = W.Mem(pid)
    rows=[]; t0=time.perf_counter(); clicked=False; click_t=None
    while True:
        t=time.perf_counter()-t0
        if not clicked and t>=click_at:
            u32.mouse_event(LD,0,0,0,0); u32.mouse_event(LU,0,0,0,0); click_t=t; clicked=True
        cam=C.cam_origin(m)
        rows.append([round(t,6), m.u32(WC.A_FRAME), cam["cam_x"], cam["cam_y"],
                     m.u32(0xA8E7AC), m.u8(0xA8E9A0)])
        if t>=dur: break
    wall=time.perf_counter()-t0
    hp=os.path.join(EVID,"calib_%s_hifreq.jsonl"%tag)
    with open(hp,"w",encoding="utf-8") as f:
        f.write(json.dumps({"tag":tag,"columns":["t","frame","cam_x","cam_y","a8e7ac","a8e9a0"],
                            "n":len(rows),"wall":wall,"rate":len(rows)/wall,"click_t":click_t},ensure_ascii=False)+"\n")
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    m.close()
    return len(rows), wall, len(rows)/wall, click_t

def main():
    tag=sys.argv[1]
    cands=[tuple(int(v) for v in a.split(",")) for a in sys.argv[2:]]
    pid=W.pid_of(); m=W.Mem(pid); ph=P.player_house(m)
    c0=m.u32(ph+0x30C); before=set(player_napowr(m,ph))
    rec={"tag":tag,"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),"pid":pid,
         "frame0":m.u32(W.A_FRAME),"credit_before":c0,"cam_before":C.cam_origin(m),
         "candidates":cands,"existing_napowr":[hex(x) for x in before]}
    # order
    bare_click(*ICON); time.sleep(0.5)
    rec["credit_after_order"]=m.u32(ph+0x30C)
    target_credit=c0-600; ready=False
    for _ in range(30):
        time.sleep(0.3)
        if abs(m.u32(ph+0x30C)-target_credit)<=40: ready=True;break
    time.sleep(0.8)
    rec["credit_ready"]=m.u32(ph+0x30C); rec["ready_seen"]=ready
    # pickup
    bare_click(*ICON); time.sleep(0.35)
    # hover candidates, pick first green
    chosen=None; hover_log=[]
    for i,(x,y) in enumerate(cands):
        u32.SetCursorPos(x,y); time.sleep(0.5)
        img=ImageGrab.grab(all_screens=False)
        r,g=colors(img,x,y)
        img.crop((max(0,x-260),max(0,y-220),min(2560,x+260),min(1440,y+220))).save(os.path.join(EVID,"calib2_%s_hover%d.png"%(tag,i)))
        hover_log.append({"screen":[x,y],"red":r,"green":g,"cam":C.cam_origin(m)})
        if g>1000 and r<2000:
            chosen=(x,y); break
    rec["hover_log"]=hover_log; rec["chosen"]=chosen
    if not chosen:
        rec["error"]="no green candidate"
        with open(os.path.join(EVID,"calib2_%s.json"%tag),"w",encoding="utf-8") as f:json.dump(rec,f,ensure_ascii=False,indent=2)
        print("NO GREEN",hover_log); m.close(); return 1
    x,y=chosen
    rec["cam_preclick"]=C.cam_origin(m)
    n,wall,rate,click_t=sample_click(pid,2.0,0.35,tag)
    rec["hifreq_n"]=n; rec["hifreq_wall"]=wall; rec["hifreq_rate"]=rate; rec["click_t"]=click_t
    rec["cam_postclick"]=C.cam_origin(m)
    time.sleep(1.0)
    after=set(player_napowr(m,ph)); new=after-before
    rec["credit_after"]=m.u32(ph+0x30C); rec["new_napowr"]=[hex(o) for o in new]; rec["result"]={}
    for obj in new:
        cells=footprint_cells(m,obj)
        loc=None
        lx=m.u32(obj+P.O_LOCX); ly=m.u32(obj+P.O_LOCY)
        if lx is not None and ly is not None:
            def s32(u):
                u&=0xFFFFFFFF; return u-0x100000000 if u&0x80000000 else u
            loc=[s32(lx)>>8, s32(ly)>>8]
        rec["result"][hex(obj)]={"location_cell":loc,"occupied_cells":cells,"n_cells":len(cells),
                                  "o1_81":m.u8(obj+0x81),"o2_74":m.u8(obj+0x74)}
    with open(os.path.join(EVID,"calibration.jsonl"),"a",encoding="utf-8") as f:
        f.write(json.dumps(rec,ensure_ascii=False)+"\n")
    with open(os.path.join(EVID,"calib2_%s.json"%tag),"w",encoding="utf-8") as f:json.dump(rec,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:rec[k] for k in ("tag","chosen","cam_before","cam_preclick","cam_postclick","credit_after","new_napowr","result","hifreq_rate")},ensure_ascii=False))
    m.close(); return 0

if __name__=="__main__": sys.exit(main())
