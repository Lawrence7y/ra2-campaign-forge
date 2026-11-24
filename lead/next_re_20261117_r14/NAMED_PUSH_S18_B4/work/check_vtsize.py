# -*- coding: utf-8 -*-
"""检查 VCChatEventSink 双 vtable 是否为主虚表（小成员表陷阱）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import witness_core as W
for vt in ['007F76B4','007F77A4','007F766C','007F78E4']:
    vb=int(vt,16)
    # count consecutive non-null slots up to next COL-like boundary
    vals=[]
    for i in range(0,80):
        v=W.u32(vb+4*i)
        if v is None: break
        vals.append(v)
    print("vt=%s  COL[-4]=%08X  nslots_scanned=%d" % (vt, W.u32(vb-4) or 0, len(vals)))
    print("   first 8:", [hex(x) for x in vals[:8]])
    print("   last  8:", [hex(x) for x in vals[-8:]])
