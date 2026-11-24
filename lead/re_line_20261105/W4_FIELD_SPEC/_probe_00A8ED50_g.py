# -*- coding: utf-8 -*-
"""W4 只读探针 #7：把此前内联一次性命令固化为可复跑产物（0x00A8ED50 补证）"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine
e = Engine()
print("SHA256", e.sha)
print("COVERAGE", e.coverage)

def das(name, a, n):
    print("\n---", name, hex(a), "+", hex(n), "---")
    for v, b, m, o in e.disasm(a, n):
        print(" ", hex(v), b, m, o)

print("\n=== 1) 向量 vptr 槽（0x7E4678 / 0x7E4698） ===")
for base in (0x7E4678, 0x7E4698):
    print("VPTR", hex(base))
    for off in (0, 4, 8, 0xC, 0x10, 0x14):
        print("  +", hex(off), "SLOT_VA", hex(base + off), "u32", hex(e.u32(base + off)))
print("BulletClass 对象 vptr 0x7E46E4 槽:")
for off in (0, 4, 8, 0xC, 0x10, 0x5C):
    print("  +", hex(off), "SLOT_VA", hex(0x7E46E4 + off), "u32", hex(e.u32(0x7E46E4 + off)))

print("\n=== 2) 0x46B890 IndexOf 函数体（Del 的 [vptr+0x10]） ===")
das("IndexOf_46B890", 0x46B890, 0x30)

print("\n=== 3) 0x46AFF0 函数体（清场循环 0x5344DD 的 [objvptr+0x08]） ===")
das("fn_46AFF0", 0x46AFF0, 0x38)

print("\n=== 4) 0x5F3900 基类构造（+0x90=1，+0x98=0） ===")
das("ctor_5F3900", 0x5F3900, 0x92)

print("\n=== 5) 0x5F3D20 附近（+0x98 读取门） ===")
das("ctx_5F3D20", 0x5F3D24, 0x58)

print("\n=== 6) 原始 LE 字节全镜像核算 ===")
for label, needle in [("0xA8ED50 disp32", bytes.fromhex("50eda800")),
                      ("0x4E6860 funcptr", bytes.fromhex("60684e00")),
                      ("0xA8ED40 disp32", bytes.fromhex("40eda800"))]:
    pos, L = 0, []
    while True:
        j = e.raw.find(needle, pos)
        if j < 0:
            break
        L.append(j)
        pos = j + 1
    print(label, "count", len(L))
    for j in L:
        hit = None
        for nm, a, vs, rp, rs in e.SEC:
            if rp <= j < rp + rs:
                hit = (nm, hex(a + (j - rp)))
                break
        print("   off", hex(j), "->", hit)

print("\n=== 7) CRT 初始化器表 .data 0x813200..0x813230 ===")
for i in range(0, 0x30, 4):
    v = 0x813200 + i
    print(" ", hex(v), e.rd(v, 4).hex(), hex(e.u32(v)))

print("\n=== 8) disp_hits 复核 + 0x55B8F0 直接调用者 ===")
h = e.disp_hits(0xA8ED50)
print("total", len(h), "W", [hex(a) for a, w, m, o in h if w == "W"],
      "R", [hex(a) for a, w, m, o in h if w == "R"])
tb = e.raw[e.TB:e.TB + e.TSZ]
for tgt in (0x55B8F0, 0x55B8E0, 0x55B880, 0x55D360):
    for op, nm in ((0xE8, "call"), (0xE9, "jmp")):
        hits = [e.TLO + j for j in range(len(tb) - 4)
                if tb[j] == op and e.TLO + j + 5 + int.from_bytes(tb[j+1:j+5], "little", signed=True) == tgt]
        print("XREF", nm, hex(tgt), "n", len(hits), [hex(x) for x in hits[:12]])

print("\n=== 9) MainLogicFrame 0x55D360 头 ===")
das("MLF_head", 0x55D360, 0x30)

print("\nDONE7")
