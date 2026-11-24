# -*- coding: utf-8 -*-
"""W4 只读探针 #3（0x00A8ED50 门控定点补证）：
  1) vtable 槽：0x7E46E4+0x5C 是否 = 0x4666E0（BulletClass::Update）
  2) 进 B 函数体：0x4666E0 内的 +0x90 二道门与 0x467FEE 早退
  3) +0x98 标志：具体字节宽度、是否有固定全局 VA、对象内偏移
  4) 读循环 0x55B8F0..0x55B966 的所属函数头/调用者
  5) 0x7193CC 对齐上下文、0x5F398D 标志写入上下文
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

print("\n=== 1) vtable 链路（进 B 函数体核实字节） ===")
print("u32(0x7E46E0) COL =", hex(eng.u32(0x7E46E0)))
print("u32(0x7E46E4) vptr[0] =", hex(eng.u32(0x7E46E4)))
print("u32(0x7E46E4+0x5C) =", hex(eng.u32(0x7E46E4 + 0x5C)), "  (slot VA", hex(0x7E46E4 + 0x5C), ")")
print("u32(0x7E4740) =", hex(eng.u32(0x7E4740)))
print("rd(0x7E46E0,4) =", eng.rd(0x7E46E0, 4).hex())
print("rd(0x7E46E4,4) =", eng.rd(0x7E46E4, 4).hex())
# 构造里写入对象的 vptr
print("ctor 0x466425 bytes =", eng.rd(0x466425, 6).hex(), "(c706 e4467e00)")

print("\n=== 2) BulletClass::Update 0x4666E0 函数体头（含 +0x90 二道门） ===")
das("Update_0x4666E0_head", 0x4666E0, 0x48)

print("\n=== 3) 0x467FEE 早退点（+0x90==0 的落点） ===")
das("Update_early_exit", 0x467FE0, 0x28)

print("\n=== 4) +0x98 / +0x90 字节宽度与写入点 ===")
for va in (0x55B954, 0x4666F7, 0x55B95A, 0x55B95C, 0x55B960, 0x55B94B, 0x55B951):
    # 逐址取 1..8 字节
    print("BYTES", hex(va), eng.rd(va, 8).hex(), "fo", eng.fo(va))
f98 = eng.disp_hits_field(0x98)
b98 = [(a, w, m, o) for a, w, m, o in f98 if "byte ptr" in o]
print("byte_0x98_W", [(hex(a), m, o) for a, w, m, o in b98 if w == "W"])
f90 = eng.disp_hits_field(0x90)
b90 = [(a, w, m, o) for a, w, m, o in f90 if "byte ptr" in o]
print("byte_0x90_total", len(b90), "W", len([x for x in b90 if x[1] == "W"]), "R", len([x for x in b90 if x[1] == "R"]))
print("byte_0x90_W", [(hex(a), m, o) for a, w, m, o in b90 if w == "W"][:40])

print("\n=== 5) +0x98 标志写入点上下文（0x5F398D、0x511404、0x636FB4） ===")
for a, n in [(0x5F3980, 0x28), (0x5113F8, 0x20), (0x636FA8, 0x20), (0x55BAC0, 0x30)]:
    das("flag_write_ctx", a, n)

print("\n=== 6) 读循环所属函数：向后找 ret 边界 + 调用者 ===")
# 打印 0x55B880..0x55B8F5 原始字节，找 0xC3/0xCC 填充
print("RAW 0x55B880..0x55B8F5:", eng.rd(0x55B880, 0x75).hex())
for a in range(0x55B880, 0x55B8F0):
    b = eng.rd(a, 1)
    if b in (b"\xc3", b"\xcc"):
        print("  boundary candidate", hex(a), b.hex())
# 可能的函数头：找 55 8b ec / 53 56 / 83 ec
for a in range(0x55B7E0, 0x55B900):
    d = eng.rd(a, 4)
    if d[:3] == b"\x55\x8b\xec" or d[:2] == b"\x53\x56" or d[:2] == b"\x83\xec":
        print("  prologue candidate", hex(a), d.hex())

tb = eng.raw[eng.TB: eng.TB + eng.TSZ]
def callers(t):
    return [eng.TLO + j for j in range(len(tb)-4)
            if tb[j] == 0xE8 and eng.TLO+j+5+int.from_bytes(tb[j+1:j+5], "little", signed=True) == t]
for t in (0x55B8F0, 0x55B8EC, 0x55B8E0, 0x55B8D0, 0x55B8C0, 0x55B880, 0x55B800):
    print("CALLERS", hex(t), "n", len(callers(t)), [hex(x) for x in callers(t)[:12]])

print("\n=== 7) 0x7193CC 对齐上下文 ===")
# 从 0x7193C0 反推对齐：试几个起点
for a in (0x7193C0, 0x7193C2, 0x7193C4, 0x7193C6, 0x7193C8, 0x7193CA, 0x7193CC):
    d = eng.disasm(a, 0x28)
    print(" try", hex(a), "->", [(hex(v), m, o) for v, b, m, o in d[:6]])
print("--- 0x7193A0..0x7193E0 (前一段，找函数头) ---")
das("ctx_7193A0", 0x7193A0, 0x48)

print("\n=== 8) 0x5344CB 所属：确认是清场循环 ===")
das("ctx_5344C0", 0x5344C0, 0x30)

print("\nDONE3")
