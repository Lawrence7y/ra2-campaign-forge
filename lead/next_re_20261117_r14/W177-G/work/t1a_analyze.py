#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze t1a snapshots: find all stable mouse-driven changed dwords and their delta patterns."""
import os, sys, struct, json, collections
HERE=os.path.dirname(os.path.abspath(__file__))
EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
tag=sys.argv[1] if len(sys.argv)>1 else "k10"
DB=0x00812000
def load(name):
    p=os.path.join(EVID,"t1a_%s_%s.bin"%(tag,name))
    raw=open(p,"rb").read()
    return list(struct.unpack("<%dI"%(len(raw)//4),raw))
base=load("base"); xp=load("Xplus"); yp=load("Yplus"); ret=load("return")
N=len(base)
def sd(a,b):
    d=(b-a)&0xFFFFFFFF
    return d-0x100000000 if d&0x80000000 else d
chg=[]
for i in range(N):
    if base[i]!=xp[i] or base[i]!=yp[i]:
        stable=(base[i]==ret[i])
        chg.append((DB+i*4, base[i],xp[i],yp[i],ret[i],sd(base[i],xp[i]),sd(base[i],yp[i]),stable))
print("total dwords",N,"changed on X or Y move",len(chg),"stable(base==ret)",sum(1 for c in chg if c[7]))
pairs=collections.Counter((c[5],c[6]) for c in chg if c[7])
print("\n=== top stable (dX,dY) delta pairs ===")
for (dx,dy),n in pairs.most_common(40):
    print("  dX=%+7d dY=%+7d  n=%d"%(dx,dy,n))
print("\n=== stable changes with small deltas (|dX|,|dY|<=6000, not both 0) ===")
sel=[c for c in chg if c[7] and abs(c[5])<=6000 and abs(c[6])<=6000 and (c[5]!=0 or c[6]!=0)]
print("count",len(sel))
for c in sel[:250]:
    print("  %08X v=%08X/%08X/%08X dX=%+d dY=%+d ret=%s"%(c[0],c[1],c[2],c[3],c[5],c[6],c[1]==c[4]))
op=os.path.join(EVID,"t1a_%s_changes.json"%tag)
with open(op,"w",encoding="utf-8") as f:
    json.dump({"tag":tag,"n_changed":len(chg),"changes":[{"addr":hex(c[0]),"v0":hex(c[1]),"vx":hex(c[2]),"vy":hex(c[3]),"vr":hex(c[4]),"dX":c[5],"dY":c[6],"stable":c[7]} for c in chg]},f,indent=2)
print("saved",op)
