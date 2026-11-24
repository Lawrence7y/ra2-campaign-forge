import sys, os, struct, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditlib import *

ENTRY = 0x004F45B0

print("=== 1) 全镜像中 0x004F45B0 作为 4 字节指针的出现处 ===")
hits = find_u32_va(ENTRY)
print(f"count = {len(hits)}")
def sec_of(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + s.Misc_VirtualSize:
            return s.Name.rstrip(b'\0').decode()
    return '?'
for h in hits:
    print(f"   {h:08X}  sec={sec_of(h)}  [h-4]={u32(h-4):08X}  [h+4]={u32(h+4):08X}")

print()
print("=== 2) 每个命中处：是不是某张 vtable 的槽？推 vt 起点 + COL ===")
for h in hits:
    # walk back to find candidate vt start: scan backwards for a slot whose [x-4] is a COL ptr in .rdata
    for back in range(4, 0x100, 4):
        cand_vt = h - back
        p = u32(cand_vt-4)
        if sec_of(p) == '.rdata' and is_va(p):
            sig = u32(p)
            if sig == 0:
                pTD = u32(p+12)
                if is_va(pTD):
                    nm = cstring(pTD+8)
                    if nm.startswith('.?'):
                        print(f"   slot@{h:08X} -> vt={cand_vt:08X} slot#={back//4} COL={p:08X} COL.offset={u32(p+4)} TD={pTD:08X} '{nm}'")
                        break

print()
print("=== 3) 函数尾部：看调用约定（ret / ret N）与 ecx 角色 ===")
ins = list(disasm(ENTRY, 0x400))
print(f"  decoded {len(ins)} insns")
for i in ins:
    if i.mnemonic == 'ret':
        print("   RET:", fmt_insn(i))
        break
print("  first 6 insns:")
for i in ins[:6]: print("   ", fmt_insn(i))
