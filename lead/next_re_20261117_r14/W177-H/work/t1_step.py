#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1 step measurement (closed-loop, read-only RPM + synthetic SetCursorPos).
Measure screen->cell Jacobian at TWO safe anchors with large steps (robust vs cell
quantization), retest for consistency, and also record the literal +40px numbers.
Camera origin 0x886FA0/4 re-read at EVERY sample; abort if it moves.
Writes EVIDENCE/t1_steps.json.
"""
import os, sys, time, ctypes, json
from ctypes import wintypes as wt
import w177_core as W

HOVER=0x0088095C
CAMX=0x00886FA0; CAMY=0x00886FA4
MOUSEX=0x00B0CBF8; MOUSEY=0x00B0CBFC
SAFE=(250,2050,250,1300)   # xmin,xmax,ymin,ymax physical
HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.GetCursorPos.argtypes=[ctypes.POINTER(wt.POINT)]

def in_safe(x,y): return SAFE[0]<=x<=SAFE[1] and SAFE[2]<=y<=SAFE[3]

def move_read(m,x,y,dwell=0.38):
    if not in_safe(x,y): raise RuntimeError("cursor out of safe zone: (%d,%d)"%(x,y))
    u32.SetCursorPos(int(x),int(y)); time.sleep(dwell)
    v=m.u32(HOVER)
    if v is None: raise RuntimeError("RPM hover failed")
    return {"screen":[int(x),int(y)],
            "cell":[v&0xFFFF,(v>>16)&0xFFFF],"hover":v,
            "cam":[m.u32(CAMX),m.u32(CAMY)],
            "mousepx_logical":[m.u32(MOUSEX),m.u32(MOUSEY)],
            "frame":m.u32(W.A_FRAME)}

def measure(m,anchor,big=200,small=40):
    ax,ay=anchor; rows=[]
    seq=[("base",ax,ay),("X+%d"%big,ax+big,ay),("base2",ax,ay),
         ("Y+%d"%big,ax,ay+big),("base3",ax,ay),
         ("X+%d"%small,ax+small,ay),("base4",ax,ay),
         ("Y+%d"%small,ax,ay+small),("base5",ax,ay)]
    for name,x,y in seq:
        r=move_read(m,x,y); r["name"]=name; rows.append(r)
    return rows

def derive(rows,big=200,small=40):
    by={r["name"]:r for r in rows}
    b=by["base"]; xb=by["X+%d"%big]; yb=by["Y+%d"%big]
    xs=by["X+%d"%small]; ys=by["Y+%d"%small]
    # Jbig[c][k] = cell-component c change per +big px along screen axis k
    J=[[ (xb["cell"][c]-b["cell"][c])/float(big), (yb["cell"][c]-b["cell"][c])/float(big)] for c in (0,1)]
    lit40={"dxPerStep_XfromScreenX":(xs["cell"][0]-b["cell"][0])/float(small),
           "dyPerStep_XfromScreenX":(xs["cell"][1]-b["cell"][1])/float(small),
           "dxPerStep_YfromScreenY":(ys["cell"][0]-b["cell"][0])/float(small),
           "dyPerStep_YfromScreenY":(ys["cell"][1]-b["cell"][1])/float(small)}
    return {"J_cell_per_px":J,"literal_40px":lit40,
            "return_bases":[by[n]["cell"] for n in ("base","base2","base3","base4","base5")]}

def main():
    pid=W.pid_of()
    if not pid: print("gamemd not running"); return 2
    m=W.Mem(pid)
    cam0=(m.u32(CAMX),m.u32(CAMY))
    anchors=[(1000,600),(1400,800)]
    out={"pid":pid,"cam0":cam0,"anchors":anchors,"measurements":[],"ok":False}
    try:
        for a in anchors:
            rows=measure(m,a)
            d=derive(rows)
            out["measurements"].append({"anchor":a,"rows":rows,"derived":d})
            # camera must be fixed for every sample
            for r in rows:
                if tuple(r["cam"])!=cam0:
                    out["reason"]="camera moved at %s -> %s"%(r["screen"],r["cam"])
                    json.dump(out,open(os.path.join(EVID,"t1_steps.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
                    print("ABORT camera moved"); return 3
        J1=out["measurements"][0]["derived"]["J_cell_per_px"]
        J2=out["measurements"][1]["derived"]["J_cell_per_px"]
        # consistency: each component within max(0.0015 abs, 12% relative)
        diffs=[]
        for c in (0,1):
            for k in (0,1):
                a1,b1=J1[c][k],J2[c][k]
                tol=max(0.0015,0.12*max(abs(a1),abs(b1)))
                diffs.append({"c":c,"k":k,"v1":a1,"v2":b1,"absdiff":abs(a1-b1),"tol":tol,"ok":abs(a1-b1)<=tol})
        out["consistency"]=diffs
        # averaged J -> invert for px-per-cell
        J=[[(J1[c][k]+J2[c][k])/2.0 for k in (0,1)] for c in (0,1)]
        det=J[0][0]*J[1][1]-J[0][1]*J[1][0]
        out["J_avg"]=J; out["det"]=det
        if det!=0:
            out["INVJ_px_per_cell"]=[[J[1][1]/det,-J[0][1]/det],[-J[1][0]/det,J[0][0]/det]]
        out["ok"]=all(d["ok"] for d in diffs)
        cam1=(m.u32(CAMX),m.u32(CAMY)); out["cam1"]=cam1
        if cam1!=cam0: out["ok"]=False; out["reason"]="camera moved at end"
    finally:
        m.close()
    p=os.path.join(EVID,"t1_steps.json"); json.dump(out,open(p,"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print("saved",p,"ok=",out["ok"])
    for mm in out["measurements"]:
        d=mm["derived"]
        print("anchor",mm["anchor"],"J=",[[round(x,5) for x in row] for row in d["J_cell_per_px"]],"lit40=",d["literal_40px"],"bases=",d["return_bases"])
    print("consistency",[(d["c"],d["k"],round(d["absdiff"],5),round(d["tol"],5),d["ok"]) for d in diffs])
    print("J_avg",[[round(x,5) for x in row] for row in out.get("J_avg",[])],"INVJ",[[round(x,2) for x in row] for row in out.get("INVJ_px_per_cell",[])])
    return 0 if out["ok"] else 4

if __name__=='__main__': sys.exit(main())
