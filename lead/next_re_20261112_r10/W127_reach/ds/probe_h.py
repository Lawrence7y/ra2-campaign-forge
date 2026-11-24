from base import BUF, IB, u32, blob
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32)
lo = 0x004F8E80
print("=== disasm 0x%08X..0x004F9000 ===" % lo)
n = 0
for ins in md.disasm(bytes(BUF[lo-IB: 0x004F9000-IB]), lo):
    print("%08X  %-18s %-9s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    n += 1
    if n > 130: break
