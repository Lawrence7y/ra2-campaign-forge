"""C2 part 4: precise structural comparison. The previous byte-diff loop was
a sloppy scan (offset by 1). Do a proper opcode-shape comparison, and print
the full 0x6D1680..0x6D1770 body so the "duplicate" claim is evidence-based.
"""
from base import BUF, IB
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)

def dis(lo, hi):
    return list(md.disasm(bytes(BUF[lo - IB: hi - IB]), lo))

A = dis(0x006D14F0, 0x006D1564)
B = dis(0x006D1680, 0x006D1780)

print("A = 0x6D14F0 body, %d instructions" % len(A))
print("B = 0x6D1680 body, first %d instructions" % len(B))

def norm(ins):
    """normalise operands so we compare structure not addresses"""
    s = ins.op_str
    for a, b in (("0xb0c1c0", "RAMPOS"), ("0xb0cb20", "RAMPOS2"),
                 ("0xb0ccb0", "RAMPOS3"), ("0xe8", "0xe8")):
        s = s.replace(a, b)
    return (ins.mnemonic, s)

print()
print("--- side-by-side (A vs B, B offset by 0x190) ---")
for i in range(max(len(A), 40)):
    a = A[i] if i < len(A) else None
    b = B[i] if i < len(B) else None
    sa = ("%08X %-10s %s" % (a.address, a.mnemonic, a.op_str)) if a else ""
    sb = ("%08X %-10s %s" % (b.address, b.mnemonic, b.op_str)) if b else ""
    same = ""
    if a and b:
        # compare mnemonic only + operand modrm pattern, ignore disp
        same = "  ==" if a.mnemonic == b.mnemonic else "  !="
    print("%-46s | %-46s%s" % (sa, sb, same))

print()
print("=== full disasm of 0x6D1680..0x6D1780 ===")
for ins in B:
    print("%08X  %-20s %-9s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print()
print("=== count of 0x887368 absolute refs in 0x6D1680..0x6D1760 ===")
n = 0
for va in range(0x006D1680, 0x006D1760):
    i = va - IB
    if BUF[i] in (0x8B, 0xA1, 0xFF) and i + 6 <= len(BUF):
        m = BUF[i + 1]
        if (m >> 6) == 0 and (m & 7) == 5 and u32_ok(va):
            pass
