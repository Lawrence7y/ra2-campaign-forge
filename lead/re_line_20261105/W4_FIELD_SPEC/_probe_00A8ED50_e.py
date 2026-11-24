# -*- coding: utf-8 -*-
"""W4 只读探针 #5（写点全集收尾）：vector vtable 槽 -> 间接 [this+0x10] 写点"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine
eng = Engine()
print("SHA256", eng.sha)
print("COVERAGE", eng.coverage)

print("\n=== 1) 向量 vptr 0x7E4678 / 0x7E4698 槽 ===")
for base in (0x7E4678, 0x7E4698):
    print("VPTR", hex(base))
    for off in (0, 4, 8, 0xC, 0x10, 0x14):
        print("  +", hex(off), "VA", hex(base+off), "u32", hex(eng.u32(base+off)))

print("\n=== 2) 扩容函数体 [0x46B910] 是否写 [this+0x10] ===")
def das(name, a, n):
    print("\n---", name, hex(a), "+", hex(n), "---")
    for va, b, m, op in eng.disasm(a, n):
        print(" ", hex(va), b, m, op)
das("vector_resize_46B910", 0x46B910, 0xB0)
print("\n=== 3) 0x46B560 / 0x410450 是否写 [this+0x10] ===")
das("vector_46B560", 0x46B560, 0x60)
das("vector_410450", 0x410450, 0x60)

print("\n=== 4) 全 .text 中 [reg+0x10] 写点里位于 0x46xxxx 的可能向量方法 ===")
f = eng.disp_hits_field(0x10)
w = [(a, m, o) for a, ww, m, o in f if ww == "W" and "0x10]" in o and 0x46A000 <= a < 0x46C000]
print("count", len(w))
for a, m, o in w[:40]:
    print(" ", hex(a), m, o)

print("\n=== 5) 0xA8ED4C/4D 向量标志 vs 对象 +0x98：确认不是同一个 ===")
print("0xA8ED4C (vector +0x0C byte) fo", eng.fo(0xA8ED4C))
print("0xA8ED4D (vector +0x0D byte) fo", eng.fo(0xA8ED4D))
print("对象 +0x98 是 [ecx+0x98]，ecx = Items[i]；Items 指针 VA = 0x00A8ED44")
print("0x55B954 bytes", eng.rd(0x55B954, 7).hex())
print("0x55B95A bytes", eng.rd(0x55B95A, 2).hex())
print("0x55B95C bytes", eng.rd(0x55B95C, 2).hex())
print("0x55B960 bytes", eng.rd(0x55B960, 3).hex())

print("\n=== 6) 确认 0x4E6891 / 0x4664AB / 0x466630 三处字节 ===")
for a in (0x4E6891, 0x4664AB, 0x466630):
    print(hex(a), eng.rd(a, 6).hex())

print("\nDONE5")
