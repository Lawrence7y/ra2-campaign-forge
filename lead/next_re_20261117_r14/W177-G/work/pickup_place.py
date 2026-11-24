#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pick up ready ghost from icon (single click), verify visually, then place via hover global."""
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
HOVER=0x0088095C; ICON=(2328,480)
HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")

def click(x,y):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.25)
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.1); u32.mouse_event(0x0004,0,0,0,0); time.sleep(0.4)

def chain(m,cx,cy):
    base=m.u32(P.CELL_ARRAY); idx=(cy<<9)+cx; cell=m.u32(base+idx*4)
    if not cell or cell==P.INVALID_CELL: return {"valid":False}
    out={"cell":hex(cell),"nodes":[]}; seen=set(); q=m.u32(cell+0xE4)
    while q and q not in seen and len(out["nodes"])<20:
        seen.add(q); nm,_=D.rtti_name(m,q)
        out["nodes"].append({"this":hex(q),"rtti":nm,"layer":m.u32(q+0x94)}); q=m.u32(q+0x30)
    return out

def main():
    tx=int(sys.argv[1]); ty=int(sys.argv[2]); tag=sys.argv[3] if len(sys.argv)>3 else "pk"
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    rec={"target":[tx,ty]}
    rec["credit0"]=m.u32(ph+0x30C)
    # click icon to pick up ghost
    click(*ICON)
    rec["credit_after_icon"]=m.u32(ph+0x30C)
    time.sleep(0.3)
    # screenshot after pickup (cursor at icon)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"pickup_%s.png"%tag))
    print("after icon click credit",rec["credit_after_icon"])
    # goto target
    g=G.goto(m,tx,ty,start=(1300,600)); rec["goto"]={k:g[k] for k in ("ok","screen","cell","err") if k in g}
    print("goto",rec["goto"])
    time.sleep(0.3)
    v=m.u32(HOVER); rec["hover_pre"]=(v&0xFFFF,(v>>16)&0xFFFF)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"ghost_hover_%s.png"%tag))
    # click place
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.08); u32.mouse_event(0x0004,0,0,0,0)
    time.sleep(1.5)
    rec["after"]=chain(m,tx,ty); print("after",json.dumps(rec["after"],ensure_ascii=False)[:400])
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"placed_%s.png"%tag))
    # naps state
    aitems=m.u32(P.A_ABSTRACT_ITEMS); acount=m.u32(P.A_ABSTRACT); naps=[]
    for i in range(acount):
        p=m.u32(aitems+4*i)
        if not p or (p&3): continue
        nm,_=D.rtti_name(m,p)
        if nm and 'BuildingClass' in nm and m.u32(p+0x21C)==ph:
            tp=m.u32(p+0x520); short=P.ascii_at(m,tp+0x24,12) if tp and tp!=0xffffffff else '?'
            if short=='NAPOWR': naps.append({"this":hex(p),"o1":m.u8(p+0x81),"o2":m.u8(p+0x74),"loc":[m.u32(p+0x9C)>>8,m.u32(p+0xA0)>>8]})
    rec["naps"]=naps; print("naps",naps,"credit",m.u32(ph+0x30C))
    json.dump(rec,open(os.path.join(EVID,"pickup_%s.json"%tag),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    m.close()

if __name__=='__main__':main()
