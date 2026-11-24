"""C2 part 4b: corrected structural comparison at the right alignment.

Both entries are 116 bytes: A = 0x6D14F0, B = 0x6D1680 (= A + 0x190).
Compare instruction-by-instruction (mnemonic + operand shape, with the ramp
base normalised) to decide whether B is the reachable copy of A.
"""
from base import BUF, IB
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
def dis(lo, hi):
    return list(md.disasm(bytes(BUF[lo - IB: hi - IB]), lo))

A = dis(0x006D14F0, 0x006D1564)   # 116 bytes
B = dis(0x006D1680, 0x006D16F4)   # 116 bytes (A + 0x190)

print("A insns=%d  B insns=%d" % (len(A), len(B)))
print()
print("%-42s | %-42s | cmp" % ("A  0x6D14F0", "B  0x6D1680"))
print("-" * 100)
diffs = 0
for i in range(max(len(A), len(B))):
    a = A[i] if i < len(A) else None
    b = B[i] if i < len(B) else None
    sa = ("%08X %-8s %s" % (a.address, a.mnemonic, a.op_str)) if a else "-"
    sb = ("%08X %-8s %s" % (b.address, b.mnemonic, b.op_str)) if b else "-"
    if a and b:
        # relative-jump targets differ by 0x190 legitimately
        eq = (a.mnemonic == b.mnemonic)
        # normalise displacements: A's +0x190-relative branch target vs B's
        if eq and a.mnemonic in ("jl", "jge", "je", "jne", "jmp", "call"):
            da = int(a.op_str, 16) - 0x190 if a.op_str.startswith("0x") else None
            db = int(b.op_str, 16) if b.op_str.startswith("0x") else None
            eq = (da == db)
        mark = "same" if eq else "DIFF"
        if not eq:
            diffs += 1
    else:
        mark = "len"
        diffs += 1
    print("%-42s | %-42s | %s" % (sa, sb, mark))

print()
print("total differing positions:", diffs)
print()
print("=== 0x887368 absolute refs: A body vs B body ===")
from base import u32
def refs(lo, hi, tgt=0x00887368):
    out = []
    for va in range(lo, hi - 6):
        i = va - IB
        if BUF[i] in (0x8B, 0x89, 0xA1, 0xA3, 0x8D, 0xFF):
            m = BUF[i + 1]
            if (m >> 6) == 0 and (m & 7) == 5 and u32(va + 2) == tgt:
                out.append(va)
    return out
print("  A 0x6D14F0..0x6D1564 :", ["%08X" % x for x in refs(0x006D14F0, 0x006D1564)])
print("  B 0x6D1680..0x6D16F4 :", ["%08X" % x for x in refs(0x006D1680, 0x006D16F4)])
print()
print("=== full disasm 0x6D1680..0x6D1790 (real, reachable copy) ===")
for ins in dis(0x006D1680, 0x006D1790):
    print("%08X  %-20s %-9s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
