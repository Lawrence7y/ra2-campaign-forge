from base import BUF, IB, u32, s32, TEXT, blob
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32)
print("=== 0x006D05C0..0x006D0690 (includes 0x6D0613/0x6D0629/0x6D0659 sites) ===")
for ins in md.disasm(bytes(BUF[0x006D05C0-IB:0x006D06A0-IB]),0x006D05C0):
    m=""
    if ins.address in (0x006D0613,0x006D0629,0x006D0659): m="  <<< C1 hit"
    if ins.address==0x00724730: m=""
    print("  %08X %-18s %-9s %s%s" % (ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str,m))
print()
print("=== what is 0x00724730? (called with the global's ecx and a size push) ===")
for ins in md.disasm(bytes(BUF[0x00724730-IB:0x00724770-IB]),0x00724730):
    print("  %08X %-18s %-9s %s" % (ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    if ins.mnemonic=="ret": break
print()
print("=== 0x00724580 too (the sibling most non-qualifying sites call) ===")
for ins in md.disasm(bytes(BUF[0x00724580-IB:0x007245C0-IB]),0x00724580):
    print("  %08X %-18s %-9s %s" % (ins.address,ins.bytes.hex(),ins.mnemonic,ins.op_str))
    if ins.mnemonic=="ret": break
