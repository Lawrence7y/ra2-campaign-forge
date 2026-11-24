import sys, os, struct, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

print("=== 1) 0x40D180..0x40D1F0 —— 全局 MouseClass 构造区 ===")
dump(0x0040D180, 0x70)

print()
print("=== 2) 找到包含 0x40D1B6 的函数起点 ===")
# heuristic: walk back for prologue; also check section/other anchor
for start in range(0x0040D1B6, 0x0040D000, -1):
    pass
# print a wide window instead
dump(0x0040D160, 0x60)

print()
print("=== 3) 是否有 push <addr>; call 0x7C978A (atexit 注册) 指向相关函数 ===")
for a, m, b in find_rel_calls(0x007C978A):
    print(f"   callsite {a:08X} {m} {b}")
    # show preceding pushes
    dump(a-0x10, 0x10)
    print()

print()
print("=== 4) 0x87F7E8 是否被当作 MouseClass 全局实例（引用点）===")
h = find_u32_va(0x0087F7E8)
print(f"count={len(h)}")
for x in h[:12]: print(f"   {x:08X}")
