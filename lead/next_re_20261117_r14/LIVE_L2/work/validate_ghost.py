#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Self-contained: check footprint ghost presence, then one placement with memory chain verdict."""
import os, time, ctypes, struct, json
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
from w177_click import game_hwnd, force_foreground

PID=41892; HOVER=0x88095C; CELL_ARRAY=0x87F924; INVALID=0xABDC50
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
    base=m.u32(CELL_ARRAY); idx=(cy<<9)+cx
    if not base or not (0<=idx<0x40000): return None
    c=m.u32(base+idx*4); return c if (c and c!=INVALID) else None
def chain_at(m,cx,cy):
    import dsnap as D
    c=cell_ptr(m,cx,cy)
    if not c: return {"valid":False,"lenA":0,"lenB":0,"rttiA":[],"rttiB":[],"nodesA":[],"nodesB":[]}
    out={"valid":True,"cell":hex(c)}
    for tag,off in (("A",0xE4),("B",0xE8)):
        head=m.u32(c+off); nodes=[]; seen=set(); p=head
        while p and len(nodes)<32 and p not in seen:
            seen.add(p); nodes.append(p); p=m.u32(p+0x30)
        out["head"+tag]=hex(head) if head else None; out["len"+tag]=len(nodes)
        out["nodes"+tag]=[hex(x) for x in nodes]
        out["rtti"+tag]=[(D.rtti_name(m,x)[0] or "?") for x in nodes]
    return out
def napowr(m,ph):
    import wb_probe as P
    out=[]
    for i,obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,obj)
        if b["owner_21C"]!=ph or b["type"]!="NAPOWR": continue
        c=b["cell"]; out.append({"addr":obj,"obj":hex(obj),"o1":b["o1_81"],"cell":[c["cellX"],c["cellY"]],"valid":c["valid"]})
    return out
def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))
def aim(target,maxit=30):
    m=W.Mem(PID)
    cp=PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx,sy=float(cp.x),float(cp.y)
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.2); cur=hcell(m)
    for it in range(maxit):
        if cur[0] is None: time.sleep(0.15); cur=hcell(m); continue
        ex,ey=target[0]-cur[0],target[1]-cur[1]
        if ex==0 and ey==0: m.close(); return True,cur,(sx,sy)
        dsx=0.8*(JX[0]*ex+JY[0]*ey); dsy=0.8*(JX[1]*ex+JY[1]*ey)
        sx,sy=clamp(sx+dsx,sy+dsy); u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.16); cur=hcell(m)
    m.close(); return (cur==target),cur,(sx,sy)

m=W.Mem(PID); ph=P.player_house(m)
print("STATE credit",rd(m,ph+0x30C),"napowr",napowr(m,ph),"hover",hcell(m),flush=True)
m.close()
# check footprint at current cursor position
cp=PNT(); u32.GetCursorPos(ctypes.byref(cp))
print("cursor",cp.x,cp.y,"cols",cols(cp.x,cp.y),flush=True)
for pt in [(1400,560),(113,62)]:
    # aim at nearby cell to show footprint
    if pt[0]<2000 and pt[1]<2000:
        ok,cur,s=aim(pt); print("aim",pt,"->",ok,cur,s,"cols",cols(s[0],s[1]),flush=True)
