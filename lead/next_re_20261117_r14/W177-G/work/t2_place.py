#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-G T2 placement + T3 sampling using hover-cell global (no calibration).
Target cell: infantry cell from find_inf_cells. Two-click NAPOWR build, cursor
positioned by closed-loop on 0x88095C. High-freq sampling with distinct-frames.
Read-only RPM + synthetic input; no memory writes/injection.
Usage: t2_place.py <Tx> <Ty> <tag>
"""
import sys, os, time, ctypes, struct, json
from ctypes import wintypes as wt
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
import goto_cell as G

u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[wt.DWORD,wt.DWORD,wt.DWORD,wt.DWORD,ctypes.c_size_t]
LD,LU=0x0002,0x0004
ICON=(2328,480)
HOVER=0x0088095C
A_FRAME=W.A_FRAME
A_REENTRY=0x00A8E7AC
HERE=os.path.dirname(os.path.abspath(__file__))
EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")

def bare_click(x,y):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.18)
    u32.mouse_event(LD,0,0,0,0); time.sleep(0.06); u32.mouse_event(LU,0,0,0,0); time.sleep(0.12)

def read_hover(m):
    v=m.u32(HOVER); return (v&0xFFFF,(v>>16)&0xFFFF,v)

def chain_detail(m,cx,cy):
    base=m.u32(P.CELL_ARRAY)
    if not base: return {"valid":False,"reason":"no cell array"}
    idx=(cy<<9)+cx
    cell=m.u32(base+idx*4)
    if not cell or cell==P.INVALID_CELL:
        return {"cell":hex(cell) if cell else None,"valid":False}
    out={"cell":hex(cell),"valid":True,"mapcx":m.u16(cell+0x24),"mapcy":m.u16(cell+0x26),
         "headA":hex(m.u32(cell+0xE4)) if m.u32(cell+0xE4) else None,
         "headB":hex(m.u32(cell+0xE8)) if m.u32(cell+0xE8) else None,"nodes":[]}
    seen=set(); p=m.u32(cell+0xE4)
    while p and p not in seen and len(out["nodes"])<32:
        seen.add(p)
        nm,_=D.rtti_name(m,p)
        out["nodes"].append({"this":hex(p),"rtti":nm,"owner":hex(m.u32(p+0x21C)) if m.u32(p+0x21C) else None,
                             "layer_94":m.u32(p+0x94),"next":hex(m.u32(p+0x30)) if m.u32(p+0x30) else None})
        p=m.u32(p+0x30)
    out["lenA"]=len(out["nodes"])
    return out

def sample_click(m,dur=2.2,click_at=0.4):
    rows=[]; t0=time.perf_counter(); clicked=False; click_t=None
    while True:
        t=time.perf_counter()-t0
        if not clicked and t>=click_at:
            u32.mouse_event(LD,0,0,0,0); u32.mouse_event(LU,0,0,0,0); click_t=t; clicked=True
        rows.append([round(t,6),m.u32(A_FRAME),m.u32(A_REENTRY),
                     m.u32(0x886FA0),m.u32(0x886FA4),
                     m.u32(HOVER)])
        if t>=dur: break
    wall=time.perf_counter()-t0
    return rows,wall,click_t

def main():
    tx=int(sys.argv[1]); ty=int(sys.argv[2]); tag=sys.argv[3] if len(sys.argv)>3 else "t2"
    pid=W.pid_of(); m=W.Mem(pid); ph=P.player_house(m)
    rec={"tag":tag,"pid":pid,"ts":time.strftime("%Y-%m-%dT%H:%M:%S%z"),
         "target":[tx,ty],"frame0":m.u32(A_FRAME),"credit0":m.u32(ph+0x30C),
         "cam0":C.cam_origin(m),"hover0":read_hover(m)}
    rec["baseline"]=chain_detail(m,tx,ty)
    print("baseline",json.dumps(rec["baseline"],ensure_ascii=False)[:300])
    # order NAPOWR
    bare_click(*ICON); time.sleep(0.5)
    rec["credit_after_order"]=m.u32(ph+0x30C)
    target_credit=rec["credit0"]-600
    ready=False
    for _ in range(40):
        time.sleep(0.3)
        if abs(m.u32(ph+0x30C)-target_credit)<=40: ready=True; break
    time.sleep(0.8)
    rec["credit_ready"]=m.u32(ph+0x30C); rec["ready_seen"]=ready
    print("order credit",rec["credit_after_order"],"ready",ready,rec["credit_ready"])
    # pick up ghost
    bare_click(*ICON); time.sleep(0.4)
    rec["cam_pickup"]=C.cam_origin(m)
    # closed-loop goto target using hover global
    g=G.goto(m,tx,ty,start=(1300,600),verbose=True)
    rec["goto"]={k:g[k] for k in ("ok","screen","cell","err","iters") if k in g}
    print("goto",rec["goto"])
    if not g["ok"]:
        rec["error"]="goto failed"
        json.dump(rec,open(os.path.join(EVID,"t2_%s.json"%tag),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
        m.close(); return 2
    # verify camera unchanged, hover stable
    time.sleep(0.4)
    rec["cam_preclick"]=C.cam_origin(m); rec["hover_preclick"]=read_hover(m)
    if rec["hover_preclick"][:2]!=(tx,ty):
        rec["error"]="hover drifted before click"
        json.dump(rec,open(os.path.join(EVID,"t2_%s.json"%tag),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
        m.close(); return 3
    # high-freq sample around placement click
    rows,wall,click_t=sample_click(m,2.2,0.4)
    n=len(rows); distinct=len(set(r[1] for r in rows)); rate=n/wall
    hp=os.path.join(EVID,"t2_%s_hifreq.jsonl"%tag)
    with open(hp,"w",encoding="utf-8") as f:
        f.write(json.dumps({"tag":tag,"columns":["t","frame","a8e7ac","cam_x","cam_y","hover"],
                            "n":n,"wall":wall,"rate":rate,"distinct_frames":distinct,"click_t":click_t},ensure_ascii=False)+"\n")
        for r in rows: f.write(json.dumps(r,ensure_ascii=False)+"\n")
    rec["hifreq"]={"n":n,"wall":wall,"rate":rate,"distinct_frames":distinct,"click_t":click_t}
    print("hifreq n=%d rate=%.0f distinct=%d"%(n,rate,distinct))
    time.sleep(1.2)
    rec["cam_postclick"]=C.cam_origin(m); rec["hover_postclick"]=read_hover(m)
    rec["after"]=chain_detail(m,tx,ty)
    rec["credit_after"]=m.u32(ph+0x30C)
    # screenshot
    try:
        ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"t2_%s_after.png"%tag))
    except Exception: pass
    json.dump(rec,open(os.path.join(EVID,"t2_%s.json"%tag),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    nodes=rec["after"].get("nodes",[])
    bld=[x for x in nodes if x["rtti"] and "BuildingClass" in x["rtti"]]
    print("AFTER lenA=%d building_nodes=%d"%(len(nodes),len(bld)))
    for x in nodes: print("  ",x)
    m.close(); return 0

if __name__=='__main__':sys.exit(main())
