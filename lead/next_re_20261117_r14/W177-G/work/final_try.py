#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final T2: stop all units, pick stable infantry cell, place NAPOWR with offset anchor
so infantry cell is covered by footprint, verify building+infantry same cell."""
import sys,time,ctypes,json,os
from ctypes import wintypes as wt
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import dsnap as D
import goto_cell as G
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[wt.DWORD,wt.DWORD,wt.DWORD,wt.DWORD,ctypes.c_size_t]
u32.keybd_event.argtypes=[ctypes.c_ubyte,ctypes.c_ubyte,ctypes.c_uint,ctypes.c_size_t]
HOVER=0x0088095C; ICON=(2328,480)
HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")

def click(x,y):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.22)
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.09); u32.mouse_event(0x0004,0,0,0,0); time.sleep(0.35)

def scan_inf(m):
    ph=P.player_house(m); base=m.u32(P.CELL_ARRAY); mapc=P.MAP_SINGLETON
    w=m.u32(mapc+0x14C); h=m.u32(mapc+0x150); out={}
    for cy in range(h):
        rb=base+((cy<<9))*4; buf=ctypes.create_string_buffer(w*4); got=ctypes.c_size_t(0)
        if not W.k32.ReadProcessMemory(m.h,ctypes.c_void_p(rb),buf,w*4,ctypes.byref(got)): continue
        for cx in range(w):
            cell=int.from_bytes(buf.raw[cx*4:cx*4+4],'little')
            if not cell or cell==P.INVALID_CELL: continue
            q=m.u32(cell+0xE4); seen=set(); n=0
            while q and q not in seen and n<20:
                seen.add(q); nm,_=D.rtti_name(m,q)
                if nm and 'InfantryClass' in nm and m.u32(q+0x21C)==ph: n+=1
                q=m.u32(q+0x30)
            if n: out["%d,%d"%(cx,cy)]=n
    return out

def detail(m,cx,cy):
    base=m.u32(P.CELL_ARRAY); cell=m.u32(base+((cy<<9)+cx)*4)
    if not cell or cell==P.INVALID_CELL: return {"valid":False}
    out={"cell":hex(cell),"nodes":[]}; seen=set(); q=m.u32(cell+0xE4)
    while q and q not in seen and len(out["nodes"])<20:
        seen.add(q); nm,_=D.rtti_name(m,q)
        out["nodes"].append({"this":hex(q),"rtti":nm,"owner":hex(m.u32(q+0x21C)) if m.u32(q+0x21C) else None,"layer":m.u32(q+0x94)})
        q=m.u32(q+0x30)
    return out

def main():
    tag=sys.argv[1] if len(sys.argv)>1 else "final"
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    rec={"tag":tag}
    # STOP all: box select whole left map area then press S
    u32.SetCursorPos(250,250); time.sleep(0.15)
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.15)
    u32.SetCursorPos(1150,950); time.sleep(0.3)
    u32.mouse_event(0x0004,0,0,0,0); time.sleep(0.3)
    u32.keybd_event(0x53,0,0,0); time.sleep(0.08); u32.keybd_event(0x53,0,2,0)  # S
    time.sleep(0.6)
    inf=scan_inf(m); rec["inf_after_stop"]=inf
    print("inf cells after stop",inf)
    # pick a cell with >=2 infantry; choose one with highest X for offset room
    cands=[(k,int(v)) for k,v in inf.items() if v>=2]
    if not cands:
        print("no inf cell >=2"); json.dump(rec,open(os.path.join(EVID,"final_%s.json"%tag),"w"),ensure_ascii=False,indent=2); m.close(); return 2
    cands.sort(key=lambda z:(-z[1],-int(z[0].split(',')[0])))
    tx,ty=[int(x) for x in cands[0][0].split(',')]
    rec["target"]=[tx,ty]; print("target",tx,ty,"n",cands[0][1])
    rec["baseline"]=detail(m,tx,ty)
    # wait stability 2s
    time.sleep(2.0)
    rec["baseline_stable"]=detail(m,tx,ty)
    print("stable check", [n["rtti"] for n in rec["baseline_stable"].get("nodes",[])])
    # order fresh NAPOWR: click icon once, wait ready, click icon to pick up
    click(*ICON)
    c0=m.u32(ph+0x30C)
    for _ in range(40):
        time.sleep(0.3)
        # readiness via sidebar visual not reliable; wait fixed 8s
        break
    time.sleep(8.0)
    rec["credit_after_order"]=m.u32(ph+0x30C)
    click(*ICON)  # pick up
    time.sleep(0.3)
    # anchor = target - (2,0): footprint covers target as right column
    ax,ay=tx-2,ty
    g=G.goto(m,ax,ay,start=(1300,600)); rec["goto"]={k:g[k] for k in ("ok","screen","cell","err") if k in g}
    time.sleep(0.4)
    v=m.u32(HOVER); rec["hover_pre"]=(v&0xFFFF,(v>>16)&0xFFFF)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"final_%s_hover.png"%tag))
    print("hover pre",rec["hover_pre"])
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.08); u32.mouse_event(0x0004,0,0,0,0)
    time.sleep(2.0)
    # scan region around target for building+infantry same cell
    reg={}
    for dy in range(-1,3):
        for dx in range(-3,2):
            cx,cy=tx+dx,ty+dy
            d=detail(m,cx,cy)
            infn=[n for n in d.get("nodes",[]) if n["rtti"] and "InfantryClass" in n["rtti"]]
            bldn=[n for n in d.get("nodes",[]) if n["rtti"] and "BuildingClass" in n["rtti"]]
            if infn or bldn: reg["%d,%d"%(cx,cy)]={"inf":infn,"bld":bldn}
    rec["region"]=reg
    print("region:")
    for k,v2 in sorted(reg.items()):
        print("  ",k,"inf",len(v2["inf"]),"bld",len(v2["bld"]))
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"final_%s_after.png"%tag))
    json.dump(rec,open(os.path.join(EVID,"final_%s.json"%tag),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    m.close()

if __name__=='__main__':main()
