"""C2 part 6: the correct mirror offset.

Observed correspondence:
  A 0x6D14F9  mov eax,[edi]            <-> B 0x6D167A  mov eax,[edi]
  A 0x6D14F0  push esi ; push edi ; mov edi,ecx ; mov esi,0xb0c1c0  (prologue)
  B 0x6D1674  push esi ; mov esi,0xb0c1c0                            (prologue)
so B = A + 0x181 for the loop body. Verify the whole shared region and show
that the two 0x887368 call sites in A have mirrors in B.
"""
from base import BUF, IB
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
def dis(lo, hi):
    return list(md.disasm(bytes(BUF[lo - IB: hi - IB]), lo))

SHIFT = 0x181
A = dis(0x006D14F9, 0x006D1564)          # loop body of A
B = dis(0x006D14F9 + SHIFT, 0x006D1564 + SHIFT)

print("A body 0x%08X..0x6D1564 (%d insns)" % (A[0].address, len(A)))
print("B body 0x%08X..0x%08X (%d insns)" % (B[0].address, B[-1].address, len(B)))
print()
print("%-40s | %-40s | cmp" % ("A", "B = A+0x181"))
print("-" * 98)
same = 0
diff = 0
for i in range(max(len(A), len(B))):
    a = A[i] if i < len(A) else None
    b = B[i] if i < len(B) else None
    sa = ("%08X %-7s %s" % (a.address, a.mnemonic, a.op_str)) if a else "-"
    sb = ("%08X %-7s %s" % (b.address, b.mnemonic, b.op_str)) if b else "-"
    eq = bool(a and b and a.mnemonic == b.mnemonic)
    if eq:
        if a.mnemonic.startswith("j") and a.op_str.startswith("0x"):
            eq = (int(a.op_str, 16) + SHIFT == int(b.op_str, 16))
        else:
            eq = (a.op_str == b.op_str)
    if eq: same += 1
    else: diff += 1
    print("%-40s | %-40s | %s" % (sa, sb, "same" if eq else "DIFF"))

print()
print("same=%d diff=%d" % (same, diff))
print()
print("=== the two 0x887368 sites in A and their mirrors in B ===")
for a_va in (0x006D153A, 0x006D1551):
    b_va = a_va + SHIFT
    print("  A %08X bytes=%s   ->  B %08X bytes=%s" %
          (a_va, bytes(BUF[a_va-IB:a_va-IB+6]).hex(),
           b_va, bytes(BUF[b_va-IB:b_va-IB+6]).hex()))
