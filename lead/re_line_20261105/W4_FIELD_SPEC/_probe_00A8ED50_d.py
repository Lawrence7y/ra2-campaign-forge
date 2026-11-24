# -*- coding: utf-8 -*-
"""W4 只读探针 #4（0x00A8ED50 收尾补证）"""
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

print("\n=== A) +0x98 标志：找对齐的 ObjectClass ctor 写点 ===")
for start in (0x5F38F0, 0x5F3900, 0x5F3910, 0x5F3920, 0x5F3928, 0x5F3930):
    d = eng.disasm(start, 0x80)
    hits = [(hex(v), b, m, o) for v, b, m, o in d if "0x98]" in o or "0x98" in o]
    print(" align", hex(start), "hits", hits[:5], "first", [(hex(v), m, o) for v, b, m, o in d[:3]])
das("aligned_5F3920", 0x5F3920, 0x80)

print("\n=== B) 更新循环函数边界与间接调用者 ===")
print("RAW 0x55B8D0..0x55B8F8:", eng.rd(0x55B8D0, 0x28).hex())
# 找 0x55B8F0 之后到 ret 的长度
d = eng.disasm(0x55B8F0, 0x400)
ret = [v for v, b, m, o in d if m.startswith("ret")]
print("first rets after 0x55B8F0", [hex(x) for x in ret[:6]], "insns", len(d))
# 全镜像中 0x55B8F0 的 4 字节 LE 出现处（函数指针/间接调用）
needle = bytes.fromhex("f0b85500")
pos, loc = 0, []
while True:
    j = eng.raw.find(needle, pos)
    if j < 0: break
    loc.append(j); pos = j + 1
print("RAW_f0b85500 count", len(loc), [hex(x) for x in loc])
for j in loc:
    for n, a, v, rp, rs in eng.SEC:
        if rp <= j < rp + rs:
            print("  ->", n, hex(a + (j - rp)))
            break

print("\n=== C) 0x7193CC 读循环：是否也过 +0x98 ===")
das("ctx_7193CC", 0x7193CC, 0x60)

print("\n=== D) 0x650534 / 0x67CC5F 循环是否过 +0x98 ===")
das("ctx_650534", 0x650534, 0x54)
das("ctx_67CC5F", 0x67CC5F, 0x30)

print("\n=== E) 确认 0x4664AB 与 0x466630 的确切字节 + 前置 inc/dec ===")
for a in (0x4664A2, 0x46662D):
    das("write_ctx", a, 0x20)

print("\n=== F) 0xA8ED50 是否被 atexit 析构写回（0x4E68A0 全函数体） ===")
das("dtor_4E68A0", 0x4E68A0, 0x3C)

print("\n=== G) vtable 里 [vptr+8] / [vptr+0x10] 槽（Add/Del 用到的扩容与 IndexOf） ===")
for off in (0, 4, 8, 0xC, 0x10, 0x5C):
    v = 0x7E46E4 + off
    print("SLOT", hex(v), "u32", hex(eng.u32(v)))

print("\nDONE4")
