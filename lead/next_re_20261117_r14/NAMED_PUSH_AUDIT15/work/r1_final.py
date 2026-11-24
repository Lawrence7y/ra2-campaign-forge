import sys, os, struct, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

ENTRY = 0x007B10C0
CTOR  = 0x007B0D90

print("=== 1) BCD 解析：确认 0x80EA28 是 BCD 而非第二个 COL ===")
for bcd in (0x0080EA28, 0x0080EA10):
    raw = rd(bcd, 0x18)
    print(f" BCD @{bcd:08X}: {raw.hex(' ')}")
    ptd = u32(bcd)
    print(f"   pTypeDescriptor={ptd:08X} name='{cstring(ptd+8) if is_va(ptd) else '?'}'")
    print(f"   attributes/numContained/mdisp/mflags = {u32(bcd+4):#x} {u32(bcd+8):#x} {u32(bcd+12):#x} {u32(bcd+16):#x}")

print()
print("=== 2) COL @0080EA60 六字段（含 pSelf？）===")
print("  raw20:", rd(0x0080EA60, 20).hex(' '))
print("  raw24:", rd(0x0080EA60, 24).hex(' '))
print("  sig=%d offset=%d cdOffset=%d pTD=%08X pCHD=%08X" % (u32(0x80EA60), u32(0x80EA64), u32(0x80EA68), u32(0x80EA6C), u32(0x80EA70)))

print()
print("=== 3) 直接 call/jmp 到本 entry 007B10C0 ===")
calls = find_rel_calls(ENTRY)
print(f"  count={len(calls)}")
for a,m,b in calls[:20]:
    print(f"   {a:08X} {m} {b}")

print()
print("=== 4) 构造器 007B0D90 的 5 个调用点上下文（看是否 operator new 后的实例化）===")
for a in (0x0052E3F1, 0x00540926, 0x00560533, 0x00685B21, 0x00686189):
    print(f" --- caller window around {a:08X} ---")
    dump(a-0x28, 0x30)
    print()
