# -*- coding: utf-8 -*-
"""B3 深度核验：对 00748190 的 ③b② 站点逐字节取证，
并与 B2 已收 00524D70 同型站点对照；解析全局列表对象与 [edx+0x10] 目标。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

def dump(va, n):
    b = R.read_va(va, n)
    print(" ".join("%02X" % x for x in b))

print("="*90)
print("B3 ROW 00748190")
print("="*90)
print("full body disasm:")
for line in R.disasm_body(0x748190, 141):
    print("  %08X: %-10s %-34s %s" % (line.address, line.mnemonic, line.op_str, line.bytes.hex()))

print("\n-- 3b2 site bytes @0x7481CA .. 0x7481D2 --")
dump(0x7481CA, 8)

print("\n-- loop body bytes @0x7481E7 .. 0x7481FF --")
dump(0x7481E7, 0x18)

print("\n-- compare B2 PASS row 00524D70 site --")
print("call@0x524DAA bytes:")
dump(0x524DAA, 8)
print("loop@0x524DC7 bytes:")
dump(0x524DC7, 0x18)

print("\n-- resolve global list object @0xA83CE0 --")
g = W.u32(0xA83CE0)
print("  [0xA83CE0] = %08X (list object ptr)" % g if g else "  [0xA83CE0] = None")
if g:
    vt = W.u32(g)
    print("  list obj vptr [g] = %08X" % vt if vt else "  list obj vptr None")
    if vt:
        slot10 = W.u32(vt + 0x10)
        print("  [vptr+0x10] callee = %08X" % slot10 if slot10 else "  [vptr+0x10] None")
        if slot10 and R.in_text(slot10):
            print("  callee in_text=True, disasm first 20:")
            for line in R.disasm_body(slot10, 80)[:20]:
                print("    %08X: %-10s %s" % (line.address, line.mnemonic, line.op_str))

print("\n-- resolve B2 global list @0xA8E348 for comparison --")
g2 = W.u32(0xA8E348)
print("  [0xA8E348] = %08X" % g2 if g2 else "  None")
if g2:
    vt2 = W.u32(g2)
    print("  vptr = %08X" % vt2 if vt2 else "  None")
    if vt2:
        s2 = W.u32(vt2 + 0x10)
        print("  [vptr+0x10] callee = %08X" % s2 if s2 else "  None")
