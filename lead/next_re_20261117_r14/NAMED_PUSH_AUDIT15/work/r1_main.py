import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

TD  = 0x0084D8F8
COL = 0x0080EA60
VT  = 0x007F794C

print("=== 1) 是否存在同 TD 的其他 vtable（多张表）===")
hits = find_u32_va(TD)
print(f"imm32 occurrences of TD {TD:08X}: {len(hits)}")
for h in hits:
    print(f"   {h:08X} ctx={hexb(h-16,32)}")
print()
print("=== 2) [vt-4]==COL 的出现次数（即本 COL 被几张表指到）===")
h2 = find_u32_va(COL)
print(f"occurrences of COL ptr {COL:08X}: {len(h2)}")
for h in h2:
    print(f"   {h:08X} -> candidate vt = {u32(h+4):08X}  first slot bytes={hexb(u32(h+4),4)}")

print()
print("=== 3) 0x80EA40..0x80EA70 原始字节（CHD/BCA 布局）===")
base = 0x0080EA30
raw = rd(base, 0x40)
for i in range(0, 0x40, 16):
    chunk = raw[i:i+16]
    print(f"  {base+i:08X}: {chunk.hex(' ')}   " + "".join(chr(c) if 32<=c<127 else '.' for c in chunk))

print()
print("=== 4) 谁调用构造器 007B0D90（活对象链）===")
for h in find_rel_calls(0x007B0D90):
    print(f"   {h[0]:08X} {h[2]}")
print("  (jmp 亦列于上)")

print()
print("=== 5) 真实派发点：call/jmp [reg+0x3C] 计数 ===")
cnt = 0
samples = []
for s in pe.sections:
    if s.Name.rstrip(b'\0') != b'.text': continue
    code = DATA[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
    sec_va = IB + s.VirtualAddress
    for i in disasm(sec_va, len(code)) if False else []:
        pass
md2 = Cs(CS_ARCH_X86, CS_MODE_32); md2.skipdata = True; md2.detail = False
for s in pe.sections:
    if s.Name.rstrip(b'\0') != b'.text': continue
    code = DATA[s.PointerToRawData:s.PointerToRawData+s.SizeOfRawData]
    sec_va = IB + s.VirtualAddress
    for i in md2.disasm(code, sec_va):
        if i.mnemonic in ('call','jmp') and i.op_str.startswith('dword ptr ['):
            if '+ 0x3c]' in i.op_str:
                cnt += 1
                if len(samples) < 8: samples.append((i.address, i.bytes.hex(), i.op_str))
print(f"  count(call/jmp dword ptr [rX + 0x3c]) = {cnt}")
for a,b,o in samples: print(f"   {a:08X}: {b:<14} {o}")
