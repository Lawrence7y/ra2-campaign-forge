#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T2: order NAPOWR, pick ghost, closed-loop cursor to foundation anchor covering
infantry target cell, click to place, then immediately (<=2 frames) read target cell
[+0xE4] chain; sample 3s for push/move. All read-only RPM + synthetic input."""
import os,sys,time,ctypes,json
from ctypes import wintypes as wt
from PIL import ImageGrab
import w177_core as W, wb_probe as P, dsnap as D
from w177_click import game_hwnd,force_foreground

HOVER=0x0088095C; CAMX=0x00886FA0; CAMY=0x00886FA4
SAFE=(250,2050,250,1300)
ICON=(2286,481)     # NAPOWR sidebar icon (screen)
TARGET=(27,85)      # infantry cell with 3 InfantryClass
ANCHOR=(26,83)      # hover anchor: foundation x26..28 y84..85 covers target; clear of NACNST(x30-33,y84-87)
HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.GetCursorPos.argtypes=[ctypes.POINTER(wt.POINT)]
u32.mouse_event.argtypes=[wt.DWORD,wt.DWORD,wt.DWORD,wt.DWORD,ctypes.c_size_t]

def click(x,y,dwell=0.3):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.2)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.09); u32.mouse_event(4,0,0,0,0); time.sleep(dwell)

def shot(tag):
    p=os.path.join(EVID,tag+".png"); ImageGrab.grab(all_screens=False).save(p); return p

def read_hover(m):
    v=m.u32(HOVER); return (v&0xFFFF,(v>>16)&0xFFFF)

def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))

def goto(m,tx,ty,start,mx=30):
    # reuse inline closed-loop (self-contained)
    sx,sy=start; trace=[]
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.34)
    for it in range(mx):
        cx,cy=read_hover(m); ex,ey=tx-cx,ty-cy
        trace.append({"it":it,"screen":[sx,sy],"cell":[cx,cy],"err":[ex,ey],"cam":[m.u32(CAMX),m.u32(CAMY)]})
        if ex==0 and ey==0:
            return {"ok":True,"screen":[sx,sy],"trace":trace}
        # prior inv (px per cell): JX=(50.7,28.0), JY=(-61,12.5)
        dsx=0.75*(50.7*ex-61.0*ey); dsy=0.75*(28.0*ex+12.5*ey)
        nsx,nsy=clamp(sx+dsx,sy+dsy)
        sx,sy=nsx,nsy
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.32)
    cx,cy=read_hover(m)
    return {"ok":False,"trace":trace,"final":[cx,cy],"err":[tx-cx,ty-cy]}

def cell_nodes(m,tx,ty,maxn=12):
    """Fast read of target cell's chain A: head + nodes (this/RTTI/owner)."""
    return D.cell_detail(m,tx,ty)

def main():
    pid=W.pid_of()
    if not pid: print("gamemd not running"); return 2
    force_foreground(game_hwnd(pid),0.6)
    m=W.Mem(pid); ph=P.player_house(m)
    rec={"pid":pid,"target":TARGET,"anchor":ANCHOR,"icon":ICON}
    rec["pre_target"]=cell_nodes(m,*TARGET)
    rec["pre_credits"]=m.u32(ph+0x30C)
    rec["pre_frame"]=m.u32(W.A_FRAME)
    print("pre target nodesA",[n['rtti_name'] for n in rec["pre_target"].get("nodesA",[])],flush=True)
    # step 1: order NAPOWR (1st icon click)
    click(*ICON,0.4)
    rec["credits_just_after_order"]=m.u32(ph+0x30C)
    print("credits just after order",rec["credits_just_after_order"],"(pre",rec["pre_credits"],")",flush=True)
    time.sleep(10.0)   # wait for build ready
    rec["after_order_credits"]=m.u32(ph+0x30C)
    shot("t2_after_order")
    # step 2: pick up ghost (2nd icon click)
    click(*ICON,0.3)
    rec["after_pick_hover"]=read_hover(m)
    shot("t2_ghost_picked")
    print("picked ghost, hover",rec["after_pick_hover"],flush=True)
    # step 3: move cursor to safe start then closed-loop to anchor
    start=(680,480)
    g=goto(m,ANCHOR[0],ANCHOR[1],start)
    rec["goto_anchor"]=g
    print("goto anchor",g.get("ok"),g.get("screen"),g.get("final"),flush=True)
    if not g["ok"] and read_hover(m)!=ANCHOR:
        # try a second pass from current
        g2=goto(m,ANCHOR[0],ANCHOR[1],tuple(g["trace"][-1]["screen"]))
        rec["goto_anchor2"]=g2
    rec["hover_at_anchor"]=read_hover(m)
    rec["cam_at_anchor"]=[m.u32(CAMX),m.u32(CAMY)]
    shot("t2_hover_anchor")
    # step 4: click to place, immediately read target chain
    frame_before=m.u32(W.A_FRAME)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.06); u32.mouse_event(4,0,0,0,0)
    frame_click=m.u32(W.A_FRAME)
    # IMMEDIATE atomic-ish read
    imm=cell_nodes(m,*TARGET)
    frame_after=m.u32(W.A_FRAME)
    rec["landing"]={"frame_before":frame_before,"frame_click":frame_click,"frame_after":frame_after,
                    "frames_elapsed":frame_after-frame_before,
                    "target_cell":imm,
                    "nA":imm.get("lenA"),"nB":imm.get("lenB"),
                    "rttiA":[n.get("rtti_name") for n in imm.get("nodesA",[])],
                    "rttiB":[n.get("rtti_name") for n in imm.get("nodesB",[])],
                    "thisA":[n['this'] for n in imm.get("nodesA",[])]}
    # main criterion
    rttiA=rec["landing"]["rttiA"]
    rec["landing"]["has_building"]=any(r and 'BuildingClass' in r for r in rttiA)
    rec["landing"]["has_infantry"]=any(r and 'InfantryClass' in r for r in rttiA)
    rec["landing"]["main_ok"]=(rec["landing"]["nA"] or 0)>=2 and rec["landing"]["has_building"]
    print("LANDING nA=",rec["landing"]["nA"],"rttiA=",rttiA,"main_ok=",rec["landing"]["main_ok"],"frames=",frame_after-frame_before,flush=True)
    shot("t2_landing")
    # step 5: sample 3s (frame, target chain head/len, infantry this set, hover, cam)
    samples=[]
    t0=time.perf_counter()
    while time.perf_counter()-t0 < 3.0:
        d=cell_nodes(m,*TARGET)
        samples.append({"t":round(time.perf_counter()-t0,4),"frame":m.u32(W.A_FRAME),
                        "headA":d.get("headA"),"lenA":d.get("lenA"),
                        "rttiA":[n.get("rtti_name") for n in d.get("nodesA",[])],
                        "thisA":[n['this'] for n in d.get("nodesA",[])],
                        "headB":d.get("headB"),"lenB":d.get("lenB"),
                        "hover":read_hover(m),"cam":[m.u32(CAMX),m.u32(CAMY)]})
    rec["samples_3s"]=samples
    frames=sorted(set(s["frame"] for s in samples))
    rec["distinct_frames"]=len(frames)
    rec["sample_rate"]=len(samples)/3.0
    # push/move analysis: did infantry this set leave target?
    pre_inf=set(n['this'] for n in rec["pre_target"].get("nodesA",[]) if n.get('rtti_name') and 'InfantryClass' in n['rtti_name'])
    inf_after=[]
    for s in samples[-3:]:
        inf_after.append(set(t for t,r in zip(s["thisA"],s["rttiA"]) if r and 'InfantryClass' in r))
    rec["push_analysis"]={"pre_inf_this":sorted(pre_inf),"last_inf_this":[sorted(x) for x in inf_after],
                          "inf_left_target": bool(pre_inf and all(not pre_inf.intersection(x) for x in inf_after))}
    shot("t2_after_3s")
    m.close()
    p=os.path.join(EVID,"t2_place.json"); json.dump(rec,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print("saved",p,"rate",round(rec["sample_rate"],1),"distinct",rec["distinct_frames"],flush=True)
    return 0

if __name__=='__main__':sys.exit(main())
