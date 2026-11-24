#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Try placing NAPOWR with anchor adjacent to infantry cell so infantry is a non-anchor footprint cell."""
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

def cells_for(m):
    base=m.u32(P.CELL_ARRAY)
    out={}
    for (cx,cy) in [(35,85),(34,85),(36,85),(34,84),(35,84),(36,84),(35,86),(36,86)]:
        cell=m.u32(base+((cy<<9)+cx)*4)
        if not cell or cell==P.INVALID_CELL: out[(cx,cy)]=[]; continue
        nodes=[]; seen=set(); q=m.u32(cell+0xE4)
        while q and q not in seen and len(nodes)<20:
            seen.add(q); nm,_=D.rtti_name(m,q)
            nodes.append({"rtti":nm,"this":hex(q),"owner":hex(m.u32(q+0x21C)) if m.u32(q+0x21C) else None,"layer":m.u32(q+0x94)})
            q=m.u32(q+0x30)
        out[(cx,cy)]=nodes
    return out

def main():
    ax=int(sys.argv[1]); ay=int(sys.argv[2]); tag=sys.argv[3] if len(sys.argv)>3 else "off1"
    m=W.Mem(W.pid_of()); ph=P.player_house(m)
    rec={"anchor":[ax,ay],"before":cells_for(m)}
    g=G.goto(m,ax,ay,start=(1300,600)); rec["goto"]={k:g[k] for k in ("ok","screen","cell","err") if k in g}
    time.sleep(0.4)
    v=m.u32(HOVER); rec["hover_pre"]=(v&0xFFFF,(v>>16)&0xFFFF)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"offset_%s_hover.png"%tag))
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.08); u32.mouse_event(0x0004,0,0,0,0)
    time.sleep(2.0)
    rec["after"]=cells_for(m)
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,"offset_%s_after.png"%tag))
    # summarize building nodes anywhere in region
    for k in sorted(rec["after"]):
        b=[n for n in rec["after"][k] if n["rtti"] and "BuildingClass" in n["rtti"]]
        inf=[n for n in rec["after"][k] if n["rtti"] and "InfantryClass" in n["rtti"]]
        print("cell",k,"inf",len(inf),"bld",len(b))
    aitems=m.u32(P.A_ABSTRACT_ITEMS); acount=m.u32(P.A_ABSTRACT); naps=[]
    for i in range(acount):
        p=m.u32(aitems+4*i)
        if not p or (p&3): continue
        nm,_=D.rtti_name(m,p)
        if nm and 'BuildingClass' in nm and m.u32(p+0x21C)==ph:
            tp=m.u32(p+0x520); short=P.ascii_at(m,tp+0x24,12) if tp and tp!=0xffffffff else '?'
            if short=='NAPOWR': naps.append({"this":hex(p),"o1":m.u8(p+0x81),"o2":m.u8(p+0x74),"loc":[m.u32(p+0x9C)>>8,m.u32(p+0xA0)>>8]})
    rec["naps"]=naps; print("naps",naps)
    json.dump(rec,open(os.path.join(EVID,"offset_%s.json"%tag),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    m.close()

if __name__=='__main__':main()
