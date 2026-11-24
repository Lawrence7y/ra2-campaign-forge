import sys, os, struct, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

def sec_of(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + s.Misc_VirtualSize:
            return s.Name.rstrip(b'\0').decode()
    return '?'

print("=== R1: entry 0x7B10C0 出现在几张表 ===")
hits = find_u32_va(0x007B10C0)
print(f"count={len(hits)}")
for h in hits:
    back = None
    for b in range(4, 0x100, 4):
        p = u32(h-b-4)
        if sec_of(p)=='.rdata' and is_va(p) and u32(p)==0:
            ptd=u32(p+12)
            if is_va(ptd) and cstring(ptd+8).startswith('.?'):
                back=(h-b, b//4, p, cstring(ptd+8), u32(p+4)); break
    print(f"   slot@{h:08X} -> {back}")

print()
print("=== R1: 构造器 007B0D90 所在写入指令字节 ===")
dump(0x007B0DA4, 6)
print("  -> 0x7F794C imm32 write sites 总数(前面已算)=1")

print()
print("=== R2: 全局 MouseClass 构造区 0040D180..0040D1D0 ===")
dump(0x0040D180, 0x50)

print()
print("=== R2: entry 0x4F45B0 在几张表（已知9） ===")
print("  (前已枚举 9 张，MouseClass 主表 slot17)")
