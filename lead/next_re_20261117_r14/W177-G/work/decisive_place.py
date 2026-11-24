#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Decisive T2: ghost already in hand. Goto infantry cell, screenshot footprint, click, read chain."""
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
HOVER=0x0088095C
HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")

def chain(m,cx,cy):
    base=m.u32(P.CELL_ARRAY); idx=(cy<<9)+cx; cell=m.u32(base+idx*4)
    if not cell or cell==P.INVALID_CELL: return {"valid":False}
    out={"cell":hex(cell),"nodes":[]}; seen=set(); q=m.u32(cell+0xE4)
    while q and q not in seen and len(out["nodes"])<20:
        seen.add(q); nm,_=D.rtti_name(m,q)
        out["nodes"].append({"this":hex(q),"rtti":nm,"owner":hex(m.u32(q+0x21C)) if m.u32(q+0x21C) else None,"layer":m.u32(q+0x94)}); q=m.u32(q+0x30)
    return out

def count_colors(img,sx,sy,rad=90):
    px=img.convert("RGB").load(); red=green=0
    for y in range(max(0,sy-rad),min(1440,sy+rad)):
        for x in range(max(0,sx-rad),min(2560,sx+rad)):
            R,G,B=px[x,y]
            if R>150 and G<90 and B<90: red+=1
            if G>140 and R<120 and B<120: green+=1
    return red,green

def main():
    tx=int(sys.argv[1]); ty=int(sys.argv[2]); tag=sys.argv[3] if len(sys.argv)>3 else "d1"
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    rec={"target":[tx,ty],"baseline":chain(m,tx,ty)}
    g=G.goto(m,tx,ty,start=(1300,600)); rec["goto"]={k:g[k] for k in ("ok","screen","cell","err") if k in g}
    sx,sy=int(g["screen"][0]),int(g["screen"][1]); time.sleep(0.4)
    v=m.u32(HOVER); rec["hover_pre"]=(v&0xFFFF,(v>>16)&0xFFFF)
    im=ImageGrab.grab(all_screens=False)
    im.save(os.path.join(EVID,"decisive_%s_hover.png"%tag))
    rec["colors"]=count_colors(im,sx,sy)
    print("hover",rec["hover_pre"],"screen",(sx,sy),"colors(red,green)",rec["colors"])
    # click place
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.08); u32.mouse_event(0x0004,0,0,0,0)
    time.sleep(2.0)
    rec["after"]=chain(m,tx,ty)
    print("after",json.dumps(rec["after"],ensure_ascii=False)[:600])
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"decisive_%s_after.png"%tag))
    # naps
    aitems=m.u32(P.A_ABSTRACT_ITEMS); acount=m.u32(P.A_ABSTRACT); naps=[]
    for i in range(acount):
        p=m.u32(aitems+4*i)
        if not p or (p&3): continue
        nm,_=D.rtti_name(m,p)
        if nm and 'BuildingClass' in nm and m.u32(p+0x21C)==ph:
            tp=m.u32(p+0x520); short=P.ascii_at(m,tp+0x24,12) if tp and tp!=0xffffffff else '?'
            if short=='NAPOWR': naps.append({"this":hex(p),"o1":m.u8(p+0x81),"o2":m.u8(p+0x74),"loc":[m.u32(p+0x9C)>>8,m.u32(p+0xA0)>>8]})
    rec["naps"]=naps; print("naps",naps)
    json.dump(rec,open(os.path.join(EVID,"decisive_%s.json"%tag),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    m.close()

if __name__=='__main__':main()
