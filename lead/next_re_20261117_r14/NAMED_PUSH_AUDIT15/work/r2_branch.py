import sys, os, struct, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

print("=== 1) 分支两路：jne 目标 004F4743 与 je 目标 004F474E ===")
dump(0x004F4743, 0x40)
print()
print("--- fall-through 区 004F45F7 .. ---")
dump(0x004F45F7, 0x20)

print()
print("=== 2) 构造器 005BDA40 的调用点（MouseClass 是否真被实例化）===")
c = find_rel_calls(0x005BDA40)
print(f"count={len(c)}")
for a,m,b in c[:15]: print(f"   {a:08X} {m} {b}")

print()
print("=== 3) 次表 0x7E195C 的 COL（判主/次）===")
COL2 = u32(0x7E195C-4)
print(f"  [0x7E195C-4] = {COL2:08X}")
if is_va(COL2):
    print(f"  sig={u32(COL2)} offset={u32(COL2+4):#x} cdOffset={u32(COL2+8):#x} pTD={u32(COL2+12):08X}")
    print(f"  TD name = '{cstring(u32(COL2+12)+8)}'")
    print(f"  次表 slot17 = {u32(0x7E195C+0x44):08X}")

print()
print("=== 4) entry 尾部 004F46F0..004F4775 ===")
dump(0x004F46F0, 0x90)
