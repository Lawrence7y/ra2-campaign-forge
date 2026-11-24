#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LIVE-L1 deploy_robust: deploy the MCV on the current in-game session with retries.
Read-only RPM + synthesized input."""
import os, sys, time, ctypes, json, struct
import w177_core as W
import wb_probe as P
import wc_probe as C
import dsnap as D
from w177_click import click_client, game_hwnd, force_foreground

CARD=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_L1"; EVID=os.path.join(CARD,"EVIDENCE")
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
    v=rd(m,0x88095C); return (v&0xFFFF,(v>>16)&0xFFFF) if v else (None,None)
def key_tap(vk):
    u32.keybd_event(vk,0,0,0); time.sleep(0.1); u32.keybd_event(vk,0,2,0); time.sleep(0.2)
def find_mcv(m,ph):
    ai=m.u32(P.A_ABSTRACT_ITEMS); ac=m.u32(P.A_ABSTRACT)
    for i in range(ac):
        q=m.u32(ai+4*i)
        if not q or (q&3) or m.u32(q+0x21C)!=ph: continue
        nm,_=D.rtti_name(m,q)
        if nm and 'UnitClass' in nm:
            lx=m.u32(q+0x9C); ly=m.u32(q+0xA0)
            if lx and ly: return (lx>>8,ly>>8), q
    return None,None
def cell_to_screen(cx,cy):
    # anchor (111,60)->(1400,600), JX=(55.6,25.9), JY=(-55.6,25.9)
    return (1400+55.6*(cx-111)-55.6*(cy-60), 600+25.9*(cx-111)+25.9*(cy-60))

def main():
    pid=W.pid_of()
    if not pid: print("no gamemd"); return 2
    m=W.Mem(pid); ph=P.player_house(m)
    pts=C.all_player_building_types(m,ph)
    print("start types",pts,"credits",rd(m,ph+0x30C))
    if "NACNST" in pts:
        print("already deployed"); m.close(); return 0
    mcv,obj=find_mcv(m,ph)
    print("mcv cell",mcv,"obj",hex(obj) if obj else None,"hover",hcell(m),"cam",(rd(m,0x886FA0),rd(m,0x886FA4)))
    m.close()
    if not mcv: print("NO MCV"); return 3
    # closed-loop from current cursor to MCV cell (camera may be scrolled)
    SAFE=(250,2050,250,1300)
    def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))
    m=W.Mem(pid); cp=PNT(); u32.GetCursorPos(ctypes.byref(cp)); sx,sy=cp.x,cp.y
    if not (SAFE[0]<=sx<=SAFE[1] and SAFE[2]<=sy<=SAFE[3]): sx,sy=1400,600
    jx=[55.6,25.9]; jy=[-55.6,25.9]
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.3); cur=hcell(m)
    cam0=(rd(m,0x886FA0),rd(m,0x886FA4))
    for it in range(30):
        if cur[0] is None: break
        ex,ey=mcv[0]-cur[0],mcv[1]-cur[1]
        print("  loop it",it,"screen",(round(sx),round(sy)),"cell",cur,"err",(ex,ey))
        if ex==0 and ey==0: break
        if (rd(m,0x886FA0),rd(m,0x886FA4))!=cam0: print("  camera moved"); break
        dsx=0.75*(jx[0]*ex+jy[0]*ey); dsy=0.75*(jx[1]*ex+jy[1]*ey)
        ox,oy=sx,sy; sx,sy=clamp(sx+dsx,sy+dsy)
        if (sx,sy)==(ox,oy): break
        u32.SetCursorPos(int(sx),int(sy)); time.sleep(0.28); cur=hcell(m)
    m.close()
    print("mcv screen closed-loop ~",(round(sx),round(sy)),"cur",cur)
    # try clicking at closed-loop position (and neighbors) + D
    cands=[(sx,sy),(sx+28,sy+13),(sx-28,sy-13)]
    for k,(cx,cy) in enumerate(cands):
        hwnd=game_hwnd(pid)
        fg=force_foreground(hwnd,0.6)
        cfg=u32.GetForegroundWindow()
        ok,info=click_client(pid,int(cx),int(cy),"left",settle=0.4,verify=True)
        print("attempt",k,"pos",(int(cx),int(cy)),"fg",fg,hex(cfg),"click",ok,flush=True)
        if not ok: continue
        # press D only if game is foreground
        if cfg==hwnd or force_foreground(hwnd,0.4):
            key_tap(0x44)
        time.sleep(2.5)
        m=W.Mem(pid); ph=P.player_house(m); pts=C.all_player_building_types(m,ph); cr=rd(m,ph+0x30C); m.close()
        print("   after D types",pts,"credits",cr,flush=True)
        if "NACNST" in pts:
            print("DEPLOYED pos",(int(cx),int(cy))); return 0
    print("DEPLOY FAILED"); return 4

if __name__=="__main__": sys.exit(main())
