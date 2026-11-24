#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1 closed-loop cursor->cell iteration (read-only RPM + synthetic SetCursorPos).
No fixed calibration assumed: start with a prior J screen->cell, then adapt it from
observed (screen delta, cell delta) pairs each step. Read back hover 0x88095C every
step, monitor camera 0x886FA0/4, keep cursor >=200px from edges/sidebar.
After E==(0,0), wait 200ms and re-read to confirm it is not transient.
Usage: t1_goto.py <targetX> <targetY> [startScreenX startScreenY]
Writes EVIDENCE/t1_goto_<tx>_<ty>.json
"""
import os, sys, time, ctypes, json
from ctypes import wintypes as wt
import w177_core as W
from w177_click import game_hwnd, force_foreground

HOVER=0x0088095C; CAMX=0x00886FA0; CAMY=0x00886FA4
SAFE=(250,2050,250,1300)
HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.GetCursorPos.argtypes=[ctypes.POINTER(wt.POINT)]

# prior from lead cross-check (physical px per cell): JX=(50.7,28.0), JY=(-61,12.5)
# screen->cell Jacobian Jsc = inv([[50.7,-61],[28,12.5]])
DET=50.7*12.5+61*28.0
JS_INIT=[[12.5/DET, 61.0/DET],[-28.0/DET, 50.7/DET]]

def clamp(x,y): return (max(SAFE[0],min(SAFE[1],x)),max(SAFE[2],min(SAFE[3],y)))

def read(m,sx,sy,dwell=0.34):
    u32.SetCursorPos(int(sx),int(sy)); time.sleep(dwell)
    pt=wt.POINT(); u32.GetCursorPos(ctypes.byref(pt))
    v=m.u32(HOVER)
    return {"screen":[int(sx),int(sy)],"actual_screen":[pt.x,pt.y],
            "cell":[v&0xFFFF,(v>>16)&0xFFFF],"hover":v,
            "cam":[m.u32(CAMX),m.u32(CAMY)],"frame":m.u32(W.A_FRAME)}

def inv2(J):
    det=J[0][0]*J[1][1]-J[0][1]*J[1][0]
    if abs(det)<1e-12: return None
    return [[J[1][1]/det,-J[0][1]/det],[-J[1][0]/det,J[0][0]/det]]

def main():
    tx=int(sys.argv[1]); ty=int(sys.argv[2])
    sx=int(sys.argv[3]) if len(sys.argv)>3 else 1000
    sy=int(sys.argv[4]) if len(sys.argv)>4 else 600
    pid=W.pid_of()
    if not pid: print("gamemd not running"); return 2
    hwnd=game_hwnd(pid)
    fg=force_foreground(hwnd,0.6) if hwnd else False
    print("foreground ok=",fg,flush=True)
    m=W.Mem(pid); cam0=(m.u32(CAMX),m.u32(CAMY)); m.close()
    m=W.Mem(pid)
    JS=[row[:] for row in JS_INIT]
    trace=[]; ok=False; reason=""
    try:
        cur=read(m,sx,sy)
        for it in range(40):
            cx,cy=cur["cell"]; ex,ey=tx-cx,ty-cy
            rec={"it":it,"screen":cur["screen"],"actual":cur["actual_screen"],
                 "cell":cur["cell"],"err":[ex,ey],"hover":cur["hover"],
                 "cam":cur["cam"],"frame":cur["frame"]}
            trace.append(rec)
            print("it%02d screen=(%d,%d) cell=(%d,%d) err=(%+d,%+d) cam=%s"%(
                it,cur["screen"][0],cur["screen"][1],cx,cy,ex,ey,cur["cam"]),flush=True)
            if tuple(cur["cam"])!=cam0:
                reason="camera moved"; break
            if ex==0 and ey==0:
                ok=True; break
            INV=inv2(JS)
            if INV is None: reason="singular J"; break
            # damped px-per-cell step
            damp=0.75
            dsx=damp*(INV[0][0]*ex+INV[0][1]*ey)
            dsy=damp*(INV[1][0]*ex+INV[1][1]*ey)
            nsx,nsy=clamp(cur["screen"][0]+dsx,cur["screen"][1]+dsy)
            if (nsx,nsy)==tuple(cur["screen"]):
                reason="clamped"; break
            nxt=read(m,nsx,nsy)
            # adapt JS from observed delta (only if screen moved enough)
            dsx_obs=nxt["screen"][0]-cur["screen"][0]; dsy_obs=nxt["screen"][1]-cur["screen"][1]
            dcx_obs=nxt["cell"][0]-cx; dcy_obs=nxt["cell"][1]-cy
            if abs(dsx_obs)+abs(dsy_obs)>=8:
                # solve Jsc * [dsx;dsy] = [dcx;dcy] underdetermined; use rank-1 correction
                # to make Jsc @ dS better match dC (Broyden-like)
                pred=[JS[0][0]*dsx_obs+JS[0][1]*dsy_obs, JS[1][0]*dsx_obs+JS[1][1]*dsy_obs]
                errc=[dcx_obs-pred[0],dcy_obs-pred[1]]
                n2=dsx_obs*dsx_obs+dsy_obs*dsy_obs
                if n2>0:
                    for c in (0,1):
                        for k in (0,1):
                            JS[c][k]+=0.5*errc[c]*[dsx_obs,dsy_obs][k]/n2
            cur=nxt
        if ok:
            time.sleep(0.2)
            v=m.u32(HOVER); conf={"after200ms_cell":[v&0xFFFF,(v>>16)&0xFFFF],"hover":v,
                                  "cam":[m.u32(CAMX),m.u32(CAMY)],"frame":m.u32(W.A_FRAME)}
            print("confirm after200ms",conf,flush=True)
            if conf["after200ms_cell"]!=[tx,ty] or tuple(conf["cam"])!=cam0:
                ok=False; reason="confirm failed"
        else:
            conf=None
    finally:
        m.close()
    out={"target":[tx,ty],"start":[sx,sy],"cam0":cam0,"ok":ok,"reason":reason,
         "J_prior":JS_INIT,"J_final":JS,"trace":trace,"confirm":conf,
         "final_screen":trace[-1]["screen"] if trace else None,
         "final_cell":trace[-1]["cell"] if trace else None}
    p=os.path.join(EVID,"t1_goto_%d_%d.json"%(tx,ty))
    json.dump(out,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print("saved",p,"ok=",ok,"reason=",reason,flush=True)
    return 0 if ok else 3

if __name__=='__main__': sys.exit(main())
