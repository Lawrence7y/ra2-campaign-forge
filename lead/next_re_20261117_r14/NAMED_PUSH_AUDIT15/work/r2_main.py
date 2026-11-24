import sys, os, struct, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

VT  = 0x007E1964
COL = 0x007FAB38
TD  = 0x00816C90
ENTRY = 0x004F45B0

print("=== 1) MouseClass 主表 0x7E1964 全 dump ===")
print("  [vt-4] =", hex(u32(VT-4)), " (expect COL 0x7FAB38)")
for off in range(0, 0x70, 4):
    v = u32(VT+off)
    mark = "  <<< slot17 (0x44) = entry" if off == 0x44 else ""
    print(f"   slot{off//4:<2} vt+{off:#04x} @{VT+off:08X} = {v:08X}{mark}")

print()
print(f"=== 2) COL @{COL:08X} / TD ===")
print("  raw:", rd(COL,20).hex(' '))
print(f"  sig={u32(COL)} offset={u32(COL+4)} cdOffset={u32(COL+8)} pTD={u32(COL+12):08X} pCHD={u32(COL+16):08X}")
print(f"  TD name = '{cstring(TD+8)}'   pVFTable={u32(TD):08X}")

print()
print(f"=== 3) 全镜像 imm32 写点 for 0x7E1964 ===")
hits = find_u32_va(VT)
print(f"count = {len(hits)}")
for h in hits:
    print(f"   operand@{h:08X}  instr@~{h-2:08X}  ctx={hexb(h-8,16)}")

print()
print("=== 4) 直接 call/jmp 到 entry 004F45B0 ===")
c = find_rel_calls(ENTRY)
print(f"count={len(c)}")
for a,m,b in c[:20]: print(f"   {a:08X} {m} {b}")
