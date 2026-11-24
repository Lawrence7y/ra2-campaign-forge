#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T3 dedicated high-rate sampling: target cell [+0xE4]/[+0xE8] head + chain length
(follow +0x30, cycle-safe) + node RTTI (cached per-node, refreshed when a new node appears)
+ hover 0x88095C + camera origin. Samples >=2s, full JSONL, reports distinct frames.
Read-only RPM + synthetic input only."""
import os,sys,time,ctypes,json
import w177_core as W, wb_probe as P, dsnap as D
from w177_click import game_hwnd,force_foreground

HOVER=0x0088095C; CAMX=0x886FA0; CAMY=0x886FA4; FRAME=0xA8ED84
TARGET=(27,85)   # infantry cell
HERE=os.path.dirname(os.path.abspath(__file__)); EVID=os.path.join(os.path.dirname(HERE),"EVIDENCE")
u32=ctypes.windll.user32
k32=ctypes.windll.kernel32

def main():
    pid=W.pid_of()
    if not pid: print("gamemd not running"); return 2
    force_foreground(game_hwnd(pid),0.5)
    m=W.Mem(pid)
    base=m.u32(P.CELL_ARRAY); INVALID=P.INVALID_CELL
    cell=m.u32(base+((TARGET[1]<<9)+TARGET[0])*4)
    if not cell or cell==INVALID: print("target cell invalid"); return 3
    pE4=cell+0xE4; pE8=cell+0xE8
    # bulk small buffers
    b4=ctypes.create_string_buffer(4); got=ctypes.c_size_t(0)
    import struct
    def rd(va):
        if k32.ReadProcessMemory(m.h,ctypes.c_void_p(va),b4,4,ctypes.byref(got)) and got.value==4:
            return struct.unpack('<I',b4.raw)[0]
        return None
    rtti_cache={}
    def rtti(p):
        if p not in rtti_cache:
            nm,_=D.rtti_name(m,p); rtti_cache[p]=nm
        return rtti_cache[p]
    def chain(head,maxn=16):
        nodes=[]; seen=set(); p=head; cyc=False
        while p and len(nodes)<maxn:
            if p in seen: cyc=True; break
            seen.add(p); nodes.append(p); p=rd(p+0x30)
        return nodes,cyc
    samples=[]
    t0=time.perf_counter(); dur=2.5
    while time.perf_counter()-t0<dur:
        t=time.perf_counter()-t0
        fr=rd(FRAME); h=rd(HOVER); cx=rd(CAMX); cy=rd(CAMY)
        hA=rd(pE4); hB=rd(pE8)
        nA,cycA=chain(hA); nB,cycB=chain(hB)
        samples.append({"t":round(t,6),"frame":fr,
                        "headA":hA,"lenA":len(nA),"cycA":cycA,
                        "nodesA":[hex(x) for x in nA],"rttiA":[rtti(x) for x in nA],
                        "headB":hB,"lenB":len(nB),"cycB":cycB,
                        "nodesB":[hex(x) for x in nB],"rttiB":[rtti(x) for x in nB],
                        "hover":h,"hover_cell":[h&0xFFFF if h else None,(h>>16)&0xFFFF if h else None],
                        "cam":[cx,cy]})
    m.close()
    p=os.path.join(EVID,"t3_hifreq.jsonl")
    with open(p,"w",encoding="utf-8") as f:
        for s in samples: f.write(json.dumps(s,ensure_ascii=False)+"\n")
    frames=sorted(set(s["frame"] for s in samples if s["frame"] is not None))
    dur_actual=samples[-1]["t"] if samples else 0
    out={"target":TARGET,"file":p,"n_samples":len(samples),"duration_s":dur_actual,
         "rate_per_s":len(samples)/dur_actual if dur_actual else 0,
         "distinct_frames":len(frames),"frame_min":frames[0] if frames else None,
         "frame_max":frames[-1] if frames else None,"rtti_cache":{hex(k):v for k,v in rtti_cache.items()}}
    json.dump(out,open(os.path.join(EVID,"t3_summary.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=2)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    return 0

if __name__=='__main__':sys.exit(main())
