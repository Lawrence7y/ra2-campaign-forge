#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T1a closed-loop cursor->cell positioning using hover global 0x88095C.
Iteratively: read hover cell, compute error to target, move by error*invJ, repeat.
Read-only RPM + synthetic SetCursorPos. No memory writes.
Usage: goto_cell.py <Tx> <Ty> [startX startY]
"""
import sys, time, ctypes, json, os
from ctypes import wintypes as wt
import w177_core as W
import wc_probe as C

u32=ctypes.windll.user32; u32.SetProcessDPIAware()
u32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
u32.GetCursorPos.argtypes=[ctypes.POINTER(wt.POINT)]
HERE=os.path.dirname(os.path.abspath(__file__))
EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
HOVER=0x0088095C

# empirical inverse Jacobian (physical px per cell) derived from t1a_v1_verify sweep
INVJ=((50.66,-58.25),(28.0,12.66))
SAFE=(200,2200,180,1300)  # xmin,xmax,ymin,ymax (physical)

def read_cell(m):
    v=m.u32(HOVER)
    return (v&0xFFFF,(v>>16)&0xFFFF,v)

def clamp(x,y):
    return (max(SAFE[0],min(SAFE[1],x)), max(SAFE[2],min(SAFE[3],y)))

def goto(m,tx,ty,start=(1300,600),maxit=50,dwell=0.28,verbose=True):
    px,py=start
    u32.SetCursorPos(int(px),int(py)); time.sleep(dwell)
    trace=[]
    for it in range(maxit):
        cx,cy,v=read_cell(m)
        ex=tx-cx; ey=ty-cy
        rec={"it":it,"screen":[px,py],"cell":[cx,cy],"err":[ex,ey],"hover":hex(v)}
        trace.append(rec)
        if verbose: print("it%02d screen=(%d,%d) cell=(%d,%d) err=(%+d,%+d)"%(it,px,py,cx,cy,ex,ey))
        if ex==0 and ey==0:
            return {"ok":True,"screen":[px,py],"cell":[cx,cy],"iters":it,"trace":trace}
        dx=ex*INVJ[0][0]+ey*INVJ[0][1]
        dy=ex*INVJ[1][0]+ey*INVJ[1][1]
        npx,npy=clamp(px+dx,py+dy)
        if (npx,npy)==(px,py) and (ex,ey)!=(0,0):
            # stuck at clamp -> need scroll
            return {"ok":False,"reason":"clamped","screen":[px,py],"cell":[cx,cy],"err":[ex,ey],"trace":trace}
        px,py=npx,npy
        u32.SetCursorPos(int(px),int(py)); time.sleep(dwell)
    cx,cy,v=read_cell(m)
    return {"ok":False,"reason":"maxit","screen":[px,py],"cell":[cx,cy],"err":[tx-cx,ty-cy],"trace":trace}

def main():
    tx=int(sys.argv[1]); ty=int(sys.argv[2])
    start=(int(sys.argv[3]),int(sys.argv[4])) if len(sys.argv)>4 else (1300,600)
    m=W.Mem(W.pid_of())
    cam0=C.cam_origin(m)
    r=goto(m,tx,ty,start)
    cam1=C.cam_origin(m)
    r["cam0"]=cam0; r["cam1"]=cam1
    print("RESULT",json.dumps({k:r[k] for k in ("ok","screen","cell","err") if k in r},ensure_ascii=False),"cam0",cam0,"cam1",cam1)
    op=os.path.join(EVID,"goto_%d_%d.json"%(tx,ty))
    with open(op,"w",encoding="utf-8") as f: json.dump(r,f,ensure_ascii=False,indent=2)
    print("saved",op)
    m.close()

if __name__=='__main__':main()
