#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 v2 experiment — corrected ghost state machine.
Ghost-in-hand verified by footprint-green probe (not o1). No-ghost baseline captured before pickup.
A=empty, B=infantry cell, C=own vehicle cell (B/C interleaved). Read-only RPM + synthesized input.
Only closes the pid it launches. Writes EVIDENCE/l1_v2_result.json + screenshots + trials_v2.tsv.
"""
import os, sys, time, ctypes, json, struct, subprocess
from collections import Counter
from PIL import ImageGrab
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

GAME=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"; CWD=r"D:\Project\ra2-campaign-forge\ra2youli"
CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"
EVID=os.path.join(CARD,"EVIDENCE"); WDIR=os.path.join(CARD,"work")
RESULT=os.path.join(EVID,"l1_v2_result.json"); TSV=os.path.join(EVID,"trials_v2.tsv")
PIDF=os.path.join(WDIR,"game.pid"); MY_PIDS=os.path.join(WDIR,"my_pids.txt")
HOVER=0x88095C; CAMX=0x886FA0; CAMY=0x886FA4; FRAME=0xA8ED84
SAFE=(420,2070,360,1120)   # tighter: avoid edge auto-scroll
JX0=(55.6,25.9); JY0=(-55.6,25.9)
PROBE_SCREEN=(1400,560)    # central known-reachable probe cell
u32=ctypes.windll.user32; k32=ctypes.windll.kernel32
try: u32.SetProcessDPIAware()
except Exception: pass
class PNT(ctypes.Structure): _fields_=[("x",ctypes.c_long),("y",ctypes.c_long)]
u32.GetCursorPos.argtypes=[ctypes.POINTER(PNT)]; u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.mouse_event.argtypes=[ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_ulong,ctypes.c_size_t]
b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
pid=None  # set in main; used by helper funcs
def rd(m,va):
    if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
        return struct.unpack('<I',b4.raw)[0]
def hcell(m):
    v=rd(m,HOVER); return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def shot(tag):
    ImageGrab.grab(all_screens=False).save(os.path.join(EVID,tag+".png"))
def key_tap(vk):
    u32.keybd_event(vk,0,0,0); time.sleep(0.08); u32.keybd_event(vk,0,2,0); time.sleep(0.12)
def click_raw(x,y,dwell=0.25):
    u32.SetCursorPos(int(x),int(y)); time.sleep(0.12)
    u32.mouse_event(2,0,0,0,0); time.sleep(0.07); u32.mouse_event(4,0,0,0,0); time.sleep(dwell)
def cols(sx,sy,rad=110):
    im=ImageGrab.grab(bbox=(int(sx-rad),int(sy-rad),int(sx+rad),int(sy+rad)),all_screens=False).convert("RGB")
    px=im.load(); w,h=im.size; g=r=0
    for y in range(h):
        for x in range(w):
            R,G,B=px[x,y]
            if G>180 and R<90 and B<90: g+=1
            elif R>180 and G<90 and B<90: r+=1
    return {"green":g,"red":r,"total":w*h}
def save(res): json.dump(res,open(RESULT,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

def cell_ptr(m,cx,cy):
    base=m.u32(P.CELL_ARRAY); idx=(cy<<9)+cx
    if not base or idx<0 or idx>=0x40000: return None
    c=m.u32(base+idx*4)
    return c if (c and c!=P.INVALID_CELL) else None

def cell_chain(m,cx,cy):
    c=cell_ptr(m,cx,cy)
    if not c: return {"valid":False,"lenA":0,"lenB":0,"rttiA":[],"rttiB":[]}
    out={"valid":True,"cell":hex(c)}
    for tag,off in (("A",0xE4),("B",0xE8)):
        head=m.u32(c+off); nodes=[]; seen=set(); p=head
        while p and len(nodes)<32 and p not in seen:
            seen.add(p); nodes.append(p); p=m.u32(p+0x30)
        out["head"+tag]=hex(head) if head else None; out["len"+tag]=len(nodes)
        out["rtti"+tag]=[(D.rtti_name(m,x)[0] or "?") for x in nodes]
        out["nodes"+tag]=[hex(x) for x in nodes]
    return out

def napowr(m,ph):
    out=[]
    for i,obj in P.enumerate_buildings(m)[2]:
        b=P.one_building(m,i,obj)
        if b["owner_21C"]!=ph or b["type"]!="NAPOWR": continue
        c=b["cell"]
        out.append({"obj":hex(obj),"o1":b["o1_81"],"o2":b["o2_74"],"cell":[c["cellX"],c["cellY"]],
                    "valid":c["valid"],"lenA":b["chains"]["lenA"]})
    return out

def closed_loop(m,anchor,tag=None,cam_guard=True):
    def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))
    cp=PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx,sy=cp.x,cp.y
    if not (SAFE[0]<=sx<=SAFE[1] and SAFE[2]<=sy<=SAFE[3]): sx,sy=1400,600
    cam0=(rd(m,CAMX),rd(m,CAMY)); jx=list(JX0); jy=list(JY0); trace=[]; ok=False
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.28); cur=hcell(m)
    for it in range(45):
        if cur[0] is None: time.sleep(0.2); cur=hcell(m); continue
        ex,ey=anchor[0]-cur[0],anchor[1]-cur[1]
        trace.append({"it":it,"screen":[round(sx,1),round(sy,1)],"cell":list(cur),"err":[ex,ey],
                      "cam":[rd(m,CAMX),rd(m,CAMY)],"frame":rd(m,FRAME)})
        if cam_guard and (rd(m,CAMX),rd(m,CAMY))!=cam0: break
        if ex==0 and ey==0: ok=True; break
        dsx=0.75*(jx[0]*ex+jy[0]*ey); dsy=0.75*(jx[1]*ex+jy[1]*ey)
        ox,oy=sx,sy; sx,sy=clamp(sx+dsx,sy+dsy)
        if (sx,sy)==(ox,oy): break
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.24)
        nxt=hcell(m)
        ddx,ddy=sx-ox,sy-oy; dcx,dcy=(nxt[0]-cur[0],nxt[1]-cur[1]) if nxt[0] is not None else (0,0)
        if abs(ddx)+abs(ddy)>=8:
            erx=dcx-(jx[0]*ddx+jy[0]*ddy); ery=dcy-(jx[1]*ddx+jy[1]*ddy); n2=ddx*ddx+ddy*ddy
            if n2>0:
                jx[0]+=0.5*erx*ddx/n2; jx[1]+=0.5*ery*ddx/n2
                jy[0]+=0.5*erx*ddy/n2; jy[1]+=0.5*ery*ddy/n2
        cur=nxt
    if tag:
        json.dump({"anchor":list(anchor),"ok":ok,"cur":list(cur) if cur[0] is not None else None,
                   "iters":len(trace),"Jfinal":{"jx":jx,"jy":jy},"trace":trace},
                  open(os.path.join(EVID,tag+"_closedloop.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    return ok,cur,(sx,sy),trace

def scan_units(m,ph):
    ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT); inf=Counter(); veh=Counter()
    for i in range(ac):
        q=m.u32(ai+4*i)
        if not q or (q&3) or m.u32(q+0x21C)!=ph: continue
        nm,_=D.rtti_name(m,q)
        if not nm: continue
        lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
        if lx is None or ly is None: continue
        c=(lx>>8,ly>>8)
        if 'InfantryClass' in nm: inf[c]+=1
        elif 'UnitClass' in nm: veh[c]+=1
    return inf,veh

def find_empty(m,occ,n=40):
    out=[]
    for cy in range(52,70):
        for cx in range(98,122):
            fc=[(x,y) for x in range(cx-1,cx+2) for y in range(cy,cy+2)]
            if any((x,y) in occ for x,y in fc): continue
            if any(not cell_ptr(m,x,y) for x,y in fc): continue
            out.append((cx,cy))
    return out[:n]

def ghost_ready(m,ph,icon,res,tag=""):
    """Return True if ghost is in hand (footprint green at probe). If not, order+pickup until yes."""
    for attempt in range(4):
        force_foreground(game_hwnd(pid),0.4)
        u32.SetCursorPos(*PROBE_SCREEN); time.sleep(0.32)
        c=cols(*PROBE_SCREEN)
        if c["green"]>=3000 or c["red"]>=3000:
            return True  # footprint present (green=valid or red=invalid). grass baseline ~1000; real footprint ~11000+
        # need to pick up. click icon once; observe credits
        m0=W.Mem(pid); pre=rd(m0,ph+0x30C); m0.close()
        force_foreground(game_hwnd(pid),0.4)
        ok,info=click_client(pid,icon[0],icon[1],"left",settle=0.35,verify=True)
        time.sleep(0.5)
        m1=W.Mem(pid); post=rd(m1,ph+0x30C); m1.close()
        ordered = post < pre-5
        if ordered:
            # wait build complete (credits settle)
            for i in range(100):
                time.sleep(0.4)
                m2=W.Mem(pid); cr=rd(m2,ph+0x30C); m2.close()
                if cr<=pre-580: break
            time.sleep(0.8)
            force_foreground(game_hwnd(pid),0.4)
            ok2,_=click_client(pid,icon[0],icon[1],"left",settle=0.35,verify=True)
            time.sleep(0.4)
            res.setdefault("orders",[]).append({"tag":tag,"attempt":attempt,"pre":pre,"post":post,"ordered":ordered,"pickup":ok2})
        else:
            res.setdefault("orders",[]).append({"tag":tag,"attempt":attempt,"pre":pre,"post":post,"ordered":False,"note":"icon click = pickup?"})
        save(res)
    u32.SetCursorPos(*PROBE_SCREEN); time.sleep(0.3)
    c=cols(*PROBE_SCREEN)
    res["ghost_ready_fail"]={"tag":tag,"final_colors":c}
    save(res)
    return c["green"]>=3000 or c["red"]>=3000

