# -*- coding: utf-8 -*-
"""W4 只读探针 #6（间接写点归属 + 第二道门）"""
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

print("\n=== 1) 间接写 0x46B5E9 的函数体（vptr 0x7E4678 +0xC = 0x46B5E0） ===")
das("fn_46B5E0", 0x46B5E0, 0x30)
print("\n=== 2) 间接写 0x46B87B 的函数体（vptr 0x7E4698 +0x10 = 0x46B780） ===")
das("fn_46B780", 0x46B780, 0x100)
print("\n=== 3) 第二道门 +0x90 在 Update 体内（0x4666F7..0x466705） ===")
print("bytes 0x4666F7:", eng.rd(0x4666F7, 14).hex())
das("Update_gate2", 0x4666F2, 0x20)
print("\n=== 4) +0x90 旗标写入点是否包含 BulletClass 构造链 ===")
f = eng.disp_hits_field(0x90)
b = [(a, w, m, o) for a, w, m, o in f if "byte ptr" in o and w == "W"]
print("byte_0x90_W count", len(b))
for a, w, m, o in b:
    print(" ", hex(a), m, o)
print("\n=== 5) 0x7E46E4 +0x5C 槽与 ctor 写入 vptr 的对应 ===")
print("ctor writes 0x7E46E4 at 0x466425:", eng.rd(0x466425, 6).hex())
print("u32(0x7E4740) =", hex(eng.u32(0x7E4740)), "=> BulletClass::Update")
print("\n=== 6) 0x5344DD call [ecx+8] 属于哪个对象（清场） ===")
print("0x5344C6 call 0x725C70 ; 0x5344E8 call 0x725C70")
das("ctx_5344C6", 0x5344C6, 0x28)
print("\nDONE6")
