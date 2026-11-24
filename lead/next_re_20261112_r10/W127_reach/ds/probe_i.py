from base import BUF, IB, u32, s32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
tl = 0x00401000
print("=== decode 0x401000.. up to 0x4F9000 and find the last function entry ===")
# Collect instruction addresses; the function entry containing 0x4F8F82 is the
# last decoded dec/jmp target or the byte after a ret+padding.
# Simpler: decode backwards is unsafe. Instead find candidate prologues by
# scanning for the exact 55 8B EC pattern AND check they are reachable.
cands = []
for va in range(0x00401000, 0x00500000):
    i = va - IB
    if BUF[i] == 0x55 and BUF[i+1] == 0x8B and BUF[i+2] == 0xEC:
        cands.append(va)
near = [c for c in cands if 0x004F0000 <= c <= 0x004F9000]
print("  55 8B EC prologues in 0x4F0000..0x4F9000: %s" % ["%08X"%x for x in near])
# also look for the classic 'sub esp, N' + push style entries
print()
print("=== try decoding from each of those and see which encloses 0x4F8F82 ===")
for c in near:
    if c > 0x4F8F82: continue
    ok = True
    addr = c
    hit = False
    for ins in md.disasm(bytes(BUF[c-IB: c-IB + 0x2000]), c):
        if ins.address == 0x004F8F82:
            hit = True
            break
        if ins.address > 0x004F8F82:
            break
    print("  from %08X covers 0x4F8F82: %s" % (c, hit))
