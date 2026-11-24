# -*- coding: utf-8 -*-
"""W4 只读探针 #2（0x00A8ED50 补证）：
  * 4E6850 初始化/析构全函数体字节
  * Add 0x4663E0 对齐入口、Del 0x466607 对齐入口
  * +0x98 活跃标志的字节宽度与全局 VA（重点：具体是哪个标志、哪个字节、哪个 VA）
  * 其余 12 个读点所在函数的紧邻上下文
  * vtable/ctor 的 B 函数体核实（0x410230、0x5F3B80、0x4666E0 的 +0x98 使用）
零真机、零活进程、零采样实现。
"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("SHA256", eng.sha)
print("COVERAGE", eng.coverage)

def das(name, a, n):
    print("\n---", name, hex(a), "+", hex(n), "---")
    for va, b, m, op in eng.disasm(a, n):
        print(" ", hex(va), b, m, op)

print("\n=== A) CRT 初始化/析构 0x4E6850..0x4E68E0 ===")
das("CRT_BulletArray", 0x4E6850, 0xA0)

print("\n=== B) Add 对齐入口 0x4663E0..0x4664C0（含前序与 vtable 装入） ===")
das("Bullet_Add_full", 0x4663E0, 0xE0)

print("\n=== C) Del 对齐入口 0x466607..0x466660 ===")
das("Bullet_Del_aligned", 0x466607, 0x59)

print("\n=== D) +0x98 活跃标志：Bullet 更新循环逐字节 ===")
print("--- 0x55B93F..0x55B966 (Bullet loop) ---")
for va, b, m, op in eng.disasm(0x55B93F, 0x27):
    print(" ", hex(va), b, m, op)
print("--- 0x55B8F0..0x55B918 (Anim loop, 对照) ---")
for va, b, m, op in eng.disasm(0x55B8F0, 0x28):
    print(" ", hex(va), b, m, op)

print("\n=== E) +0x98 标志的写入点：找 byte ptr [reg+0x98] 且宽度=1 ===")
f = eng.disp_hits_field(0x98)
byte98 = [(a, w, m, o) for a, w, m, o in f if "byte ptr" in o]
print("FIELD_0x98_BYTE total", len(byte98), "W", len([x for x in byte98 if x[1] == "W"]), "R", len([x for x in byte98 if x[1] == "R"]))
for a, w, m, o in byte98[:60]:
    print("  ", hex(a), w, m, o)

print("\n=== F) 12 个读点邻域（判断消费方：读来干什么） ===")
for a, n in [(0x5344C0, 0x40), (0x650528, 0x60), (0x67CC50, 0x40), (0x7193C0, 0x40),
             (0x466460, 0x60), (0x466618, 0x40)]:
    das("reader_ctx", a, n)

print("\n=== G) 0x410230 / 0x5F3B80 函数体头（进 B 核实） ===")
das("fn_410230", 0x410230, 0x40)
das("fn_5F3B80", 0x5F3B80, 0x40)

print("\n=== H) vtable 0x7E4678 / 0x7E4698 / 0x7E46E4 槽 ===")
for v in (0x7E4678, 0x7E4698, 0x7E46E4, 0x7E4740):
    print("VFT", hex(v), "u32", hex(eng.u32(v)), "raw", eng.rd(v, 16).hex())

print("\n=== I) rel32 调用者：0x4E6850 / 0x4E6890 / 0x4663E0 / 0x466607 / 0x55D360 ===")
tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
def callers(t):
    return [eng.TLO + j for j in range(len(tb)-4)
            if tb[j] == 0xE8 and eng.TLO+j+5+int.from_bytes(tb[j+1:j+5], "little", signed=True) == t]
for t in (0x4E6850, 0x4E6890, 0x4E68A0, 0x4663E0, 0x466607, 0x55D360, 0x410230, 0x5F3B80):
    c = callers(t)
    print("CALLERS", hex(t), "n", len(c), [hex(x) for x in c[:20]])

print("\n=== J) 0xA8ED4D / 0xA8ED4C / 0xA8ED4E 邻字节标志（IsAllocated/IsInitialized） ===")
for v in (0xA8ED4C, 0xA8ED4D, 0xA8ED4E, 0xA8ED4F):
    print("FLAG", hex(v), "fo", eng.fo(v), "byte", eng.rd(v, 1).hex())
h = eng.disp_hits_field(0xA8ED4D)
print("disp_hits(0xA8ED4D)", [(hex(a), w, m, o) for a, w, m, o in h])
# 直接绝对引用（若以 disp32 出现，disp_hits 会报）
for v in (0xA8ED4C, 0xA8ED4D, 0xA8ED4E):
    hh = eng.disp_hits(v)
    print("ABS", hex(v), "n", len(hh), [(hex(a), w, m, o) for a, w, m, o in hh])

print("\nDONE2")
