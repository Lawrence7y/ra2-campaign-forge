# -*- coding: utf-8 -*-
"""收尾核验：0x4A3020 返回约定 + TClassFactory ctor 调用点上下文。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

def dump(ea, n, maxi=60):
    print("--- %s ---"%C.hx(ea))
    for ins in C.disasm_body(ea,n)[:maxi]:
        print("  %s: %-9s %s"%(C.hx(ins.address),ins.mnemonic,ins.op_str))
    print()

print("=== callee 0x4A3020 (slot4's checked call) ===")
dump(0x4A3020, 0x80)
print("=== TClassFactory ctor callers context ===")
for site,label in [(0x006BC468,"calls ctor 006BEE40"),(0x006BC599,"calls ctor 006BF5C0")]:
    dump(site-0x20, 0x50, 30)
