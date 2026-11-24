# -*- coding: utf-8 -*-
"""解析 [0x887640] 全局对象 vtable 的 slot 0x20/0x24/0x28/0x2c/0x30 等，
剖析被调函数返回值，判定是否为多值状态码。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
import retprof

for g in [0x887640]:
    vp=C2.u32(g)
    print("global %08X -> vptr %08X" % (g, vp if vp else 0))
    if vp is None: continue
    for off in [0x20,0x24,0x28,0x2c,0x30,0x48,0x54,0x64,0x80,0x94,0x98,0x9c,0xa0,0xa4]:
        f=C2.u32(vp+off)
        if f is None or not R.in_text(f): continue
        nm=R.ATLAS.get(R.hx(f),{}).get('size')
        rets=retprof.profile(f)
        vals=sorted(set(str(v) for a,v,b in rets))
        print("  slot[%02X]=%08X atlas=%s nrets=%d vals=%s" % (off,f,nm,len(rets),vals))
