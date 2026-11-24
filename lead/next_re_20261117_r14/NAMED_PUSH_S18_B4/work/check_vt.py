# -*- coding: utf-8 -*-
"""核查 005D8170 的 vtable 0x7EEEBC 是否有静态构造安装点(决定④)，复核三个真名函数的 ②。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W
def hx(x): return "%08X" % (x & 0xFFFFFFFF)

for e, vt in [("005D8170", 0x7EEEBC), ("0071F8C0", 0x7F5578)]:
    print("=== %s vtable %s ===" % (e, hx(vt)))
    w = W.find_vtable_writes(vt)
    print("   global writes(C7 05):", [hx(x["write_va"]) for x in w["global"]])
    print("   regdisp writes(C7 rm):", [hx(x) for x in w["regdisp"]])
    print("   imm loads(B8+r):", [hx(x) for x in w["imm_load"]])
    # 额外宽松扫描：lea reg,[vt] (8D ...) 或 mov reg,vt 后 mov [reg+off],reg
    needle = struct.pack("<I", vt)
    hits=[]
    for off in range(0, len(W.TEXT_DATA)-4):
        if W.TEXT_DATA[off:off+4]==needle:
            va=W.TEXT_VA+off
            prev = W.TEXT_DATA[off-1] if off>=1 else 0
            hits.append((hx(va), "%02X"%prev))
    print("   raw imm occurrences in .text (va,prevbyte):", hits[:20], " total=%d"%len(hits))

print("\n=== 真名函数 dword refs (②) ===")
for e in ["0064A0C0","0064DEA0","006516F0"]:
    print("  ", e, W.find_dword_refs(int(e,16)))
