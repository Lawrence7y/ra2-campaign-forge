#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared read-only probe + input helpers for LIVE-L2 (self-contained, no page imports)."""
import ctypes, struct, time
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import dsnap as D

PID = None  # set by caller
HOVER=0x88095C; CAMX=0x886FA0; CAMY=0x886FA4; FRAME=0xA8ED84
JX=(55.6,25.9); JY=(-55.6,25.9); SAFE=(500,2020,400,1090)
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
try: u32.SetProcessDPIAware()
except Exception: pass
class PNT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
u32.GetCursorPos.argtypes=[ctypes.POINTER(PNT)]; u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]
b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)

def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
    return None
def hcell(m):
    v=rd(m,HOVER); return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def cols(sx,sy,rad=110):
    im=ImageGrab.grab(bbox=(int(sx-rad),int(sy-rad),int(sx+rad),int(sy+rad)),all_screens=False).convert("RGB")
    px=im.load(); w,h=im.size; g=r=0
    for y in range(h):
        for x in range(w):
            R,G,B=px[x,y]
            if G>180 and R<90 and B<90: g+=1
            elif R>180 and G<90 and B<90: r+=1
    return {"green":g,"red":r,"total":w*h}
def cell_ptr(m,cx,cy):
    base=m.u32(P.CELL_ARRAY); idx=(cy<<9)+cx
    if not base or not (0<=idx<0x40000): return None
    c=m.u32(base+idx*4); return c if (c and c!=P.INVALID_CELL) else None
def chain_at(m,cx,cy):
    c=cell_ptr(m,cx,cy)
    if not c: return {"valid":False,"cell":None,"lenA":0,"lenB":0,"rttiA":[],"rttiB":[],"nodesA":[],"nodesB":[]}
    out={"valid":True,"cell":hex(c),"selfcx":m.u16(c+P.CELL_CX),"selfcy":m.u16(c+P.CELL_CY)}
    for tag,off in (("A",P.CELL_E4),("B",P.CELL_E8)):
        head=m.u32(c+off); nodes=[]; seen=set(); p=head
        while p and len(nodes)<32 and p not in seen:
            seen.add(p); nodes.append(p); p=m.u32(p+P.O_NEXT)
        out["head"+tag]=hex(head) if head else None; out["len"+tag]=len(nodes)
        out["nodes"+tag]=[hex(x) for x in nodes]
        out["rtti"+tag]=[(D.rtti_name(m,x)[0] or "?") for x in nodes]
    return out
def napowr(m,ph):
    out=[]
    for i,obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,obj)
        if b["owner_21C"]!=ph or b["type"]!="NAPOWR": continue
        c=b["cell"]
        out.append({"addr":obj,"obj":hex(obj),"o1":b["o1_81"],"o2":b["o2_74"],
                    "cell":[c["cellX"],c["cellY"]],"valid":c["valid"],"lenA":b["chains"]["lenA"]})
    return out
def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))
def aim(target,maxit=34,settle=0.16,cam_guard=True):
    m=W.Mem(PID)
    cp=PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx,sy=float(cp.x),float(cp.y)
    if not (SAFE[0]<=sx<=SAFE[1] and SAFE[2]<=sy<=SAFE[3]): sx,sy=1400.0,700.0
    cam0=(rd(m,CAMX),rd(m,CAMY)); trace=[]; ok=False; cur=(None,None)
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.22); cur=hcell(m)
    for it in range(maxit):
        if cur[0] is None: time.sleep(0.15); cur=hcell(m); continue
        ex,ey=target[0]-cur[0],target[1]-cur[1]
        trace.append({"it":it,"screen":[round(sx,1),round(sy,1)],"cell":list(cur),"err":[ex,ey],
                      "cam":[rd(m,CAMX),rd(m,CAMY)],"frame":rd(m,FRAME)})
        if cam_guard and (rd(m,CAMX),rd(m,CAMY))!=cam0: break
        if ex==0 and ey==0: ok=True; break
        dsx=0.8*(JX[0]*ex+JY[0]*ey); dsy=0.8*(JX[1]*ex+JY[1]*ey)
        ox,oy=sx,sy; sx,sy=clamp(sx+dsx,sy+dsy)
        if (round(sx),round(sy))==(round(ox),round(oy)): break
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(settle); cur=hcell(m)
    m.close(); return ok,cur,(sx,sy),trace
def click_here(dwell=0.7):
    m=W.Mem(PID); fb=rd(m,FRAME); m.close()
    u32.mouse_event(0x0002,0,0,0,0); time.sleep(0.07)
    u32.mouse_event(0x0004,0,0,0,0); time.sleep(dwell)
    m=W.Mem(PID); fa=rd(m,FRAME); m.close(); return fb,fa
