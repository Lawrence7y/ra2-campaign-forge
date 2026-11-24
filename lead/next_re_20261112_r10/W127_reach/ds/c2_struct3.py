"""C2 part 5 (final for C2): correctly-aligned structural comparison.

0x6D1680 is a garbage decode -- it is the MIDDLE of `call [eax+0x34]`
(FF 50 34) at 0x6D167F. The real mirror of A (0x6D14F0) is the code at
0x6D1682, i.e. A+0x192. Verify by aligning on the mov esi,0xb0c1c0 shape.
"""
from base import BUF, IB, u32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
def dis(lo, hi):
    return list(md.disasm(bytes(BUF[lo - IB: hi - IB]), lo))

print("=== bytes around 0x6D1674..0x6D1690 ===")
print(bytes(BUF[0x006D1674 - IB: 0x006D1690 - IB]).hex())
print()
print("decode attempt from 0x6D1674 (correct instruction boundary):")
for ins in dis(0x006D1674, 0x6D16A0):
    print("  %08X %-16s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
print()
print("decode attempt from 0x6D1680 (claim target -- lands mid-instruction):")
for ins in dis(0x6D1680, 0x6D16A0):
    print("  %08X %-16s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

# A body vs the code at A+0x192
A = dis(0x006D14F0, 0x006D1564)
B = dis(0x006D1682, 0x006D16F6)
print()
print("A=0x6D14F0 insns=%d   B'=0x6D1682 insns=%d" % (len(A), len(B)))
print()
print("%-40s | %-40s | cmp" % ("A 0x6D14F0", "B' 0x6D1682"))
print("-" * 98)
diffs = []
for i in range(max(len(A), len(B))):
    a = A[i] if i < len(A) else None
    b = B[i] if i < len(B) else None
    sa = ("%08X %-7s %s" % (a.address, a.mnemonic, a.op_str)) if a else "-"
    sb = ("%08X %-7s %s" % (b.address, b.mnemonic, b.op_str)) if b else "-"
    if a and b:
        eq = (a.mnemonic == b.mnemonic)
        if eq and a.op_str.startswith("0x") and b.op_str.startswith("0x"):
            # normalise: branch targets in B' should be A-target + 0x192
            da = int(a.op_str, 16); db = int(b.op_str, 16)
            if a.mnemonic.startswith("j") or a.mnemonic == "call":
                eq = (da + 0x192 == db)
            else:
                eq = (a.op_str == b.op_str)
        elif eq:
            eq = (a.op_str == b.op_str)
        mark = "same" if eq else "DIFF"
        if not eq:
            diffs.append((a, b))
    else:
        mark = "len"
        diffs.append((a, b))
    print("%-40s | %-40s | %s" % (sa, sb, mark))

print()
print("total differing positions: %d / %d" % (len(diffs), max(len(A), len(B))))
print()
print("=== differing instructions in detail ===")
for a, b in diffs:
    print("  A:", ("%08X %s %s" % (a.address, a.mnemonic, a.op_str)) if a else "-")
    print("  B:", ("%08X %s %s" % (b.address, b.mnemonic, b.op_str)) if b else "-")
    if a: print("      A bytes:", a.bytes.hex())
    if b: print("      B bytes:", b.bytes.hex())
    print()

print("=== how does A's 116-byte body end vs B' ===")
print("A last insn:", "%08X %s %s" % (A[-1].address, A[-1].mnemonic, A[-1].op_str))
print("B' last insn:", "%08X %s %s" % (B[-1].address, B[-1].mnemonic, B[-1].op_str))
