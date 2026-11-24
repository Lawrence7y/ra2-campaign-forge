#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1a verify: check 0x88095C is hover-cell CellStruct{X=lo16,Y=hi16}.
Fine sweep: move cursor in small steps; trace candidate dwords; verify CellClass
at (X,Y) has MapCoords +0x24/+0x26 == (X,Y) (self-consistency).
Read-only RPM + synthetic SetCursorPos. Usage: t1a_verify.py <tag>
"""
import sys, os, time, ctypes, struct, json
from ctypes import wintypes as wt
import w177_core as W
import wb_probe as P

u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.GetCursorPos.argtypes=[ctypes.POINTER(wt.POINT)]
HERE=os.path.dirname(os.path.abspath(__file__))
EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")

CAND=0x0088095C
MOUSE_X=0x00B0CBF8
MOUSE_Y=0x00B0CBFC

def move(x,y,dwell=0.35):
    u32.SetCursorPos(int(x),int(y)); time.sleep(dwell)
    pt=wt.POINT(); u32.GetCursorPos(ctypes.byref(pt)); return (pt.x,pt.y)

def check_cell(m,cx,cy):
    base=m.u32(P.CELL_ARRAY)
    if not base or cx<0 or cy<0 or cx>=512 or cy>=512: return None
    idx=(cy<<9)+cx
    cell=m.u32(base+idx*4)
    if not cell or cell==P.INVALID_CELL: return {"cx":cx,"cy":cy,"cell":None}
    return {"cx":cx,"cy":cy,"cell":hex(cell),
            "mapcx":m.u16(cell+0x24),"mapcy":m.u16(cell+0x26),
            "headA":hex(m.u32(cell+0xE4)) if m.u32(cell+0xE4) else None,
            "lenA":len(P.chain(m,m.u32(cell+0xE4))[0])}

def main():
    tag=sys.argv[1] if len(sys.argv)>1 else "v1"
    pid=W.pid_of(); m=W.Mem(pid)
    rows=[]
    # Sweep along down-right iso (X-cell axis): step physical (+25.4,+14.0) ~= 0.5 cell in X
    # and along down-left (Y-cell): step (-35,+14). Keep within safe zone.
    path=[]
    base=(1300,600)
    # 12 steps of +0.5 X cell
    for k in range(0,13):
        path.append(("X+%.1f"%(k*0.5), base[0]+k*25.4, base[1]+k*14.0))
    # return, then 12 steps of +0.5 Y cell
    path.append(("mid",base[0],base[1]))
    for k in range(0,13):
        path.append(("Y+%.1f"%(k*0.5), base[0]+k*(-35.2), base[1]+k*14.2))
    for name,x,y in path:
        act=move(x,y)
        v=m.u32(CAND)
        lo=v&0xFFFF; hi=(v>>16)&0xFFFF
        mx=m.u32(MOUSE_X); my=m.u32(MOUSE_Y)
        cc=check_cell(m,lo,hi)
        row={"name":name,"want":[round(x,1),round(y,1)],"actual":list(act),
             "cand":hex(v),"X_lo":lo,"Y_hi":hi,
             "mouse_px":[mx,my],"cell_check":cc,"frame":m.u32(W.A_FRAME)}
        rows.append(row)
        print("%-8s px=%s cand=%08X X=%3d Y=%3d mpx=(%d,%d) cell=%s mapcx/cy=%s/%s"%(
            name,act,v,lo,hi,mx,my, cc["cell"] if cc else None,
            cc.get("mapcx") if cc else None, cc.get("mapcy") if cc else None))
    op=os.path.join(EVID,"t1a_%s_verify.json"%tag)
    with open(op,"w",encoding="utf-8") as f:
        json.dump({"tag":tag,"cand":hex(CAND),"rows":rows},f,ensure_ascii=False,indent=2)
    print("saved",op)
    m.close()
    return 0

if __name__=="__main__": sys.exit(main())
