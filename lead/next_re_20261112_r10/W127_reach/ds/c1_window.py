"""C1 part 2: the window-boundary question.

Two plausible readings of "后续24字节内":
  A) window = bytes at [site+6, site+6+24)   -> call insn start must be < site+30
  B) window = call insn must END by site+24  -> call start <= site+19

Also: does the encoding of the `mov` (segment prefix / rex-free variant) widen it?
"""
from base import BUF, IB, TEXT, s32, in_raw

PAT = bytes.fromhex("8B0D68738800")
TARGET = 0x00724730
CLAIMED = {0x654405,0x6ABFF4,0x6AC031,0x6D0613,0x6D0629,0x6D0659,0x6D0896,
           0x6D08A8,0x6D0935,0x6D09EC,0x6D127C,0x6D12F1,0x6D1367,0x6D13DC,
           0x6D153A,0x6D1551,0x6D15FA,0x6D1627,0x6D16BB,0x6D16D2}

start, end = TEXT["va"], TEXT["va"] + TEXT["vsize"]

# any prefix byte variants immediately before the mov (e.g. 3E 8B 0D ...)
print("=== prefix variants of mov ecx,[0x887368] anywhere in .text ===")
import collections
for va in range(start, end - 7):
    i = va - IB
    if BUF[i] == 0x8B and BUF[i+1:i+7] == PAT:
        prev = BUF[i-1] if i > 0 else None
        if prev in (0x2E,0x36,0x3E,0x26,0x64,0x65,0x66,0x67,0xF3,0xF2,0xF0):
            print("  %08X prefixed by %02X" % (va, prev))

def first_target_call(site, visit):
    """Walk fwd from site, decode calls one at a time (naive), return first
    call whose target is TARGET, else None."""
    for k in range(visit):
        va = site + k
        i = va - IB
        if BUF[i] == 0xE8:
            tgt = va + 5 + s32(va + 1)
            if tgt == TARGET:
                return va
    return None

rows = []
for va in range(start, end - 6):
    i = va - IB
    if BUF[i:i+6] == PAT:
        c = first_target_call(va, 24)
        rows.append((va, c))

print()
print("site      call@      delta  A(byte<=30)?  B(ends<=24)?" )
for v, c in rows:
    if c is None:
        continue
    d = c - v
    print("%08X  %s  %+3d   %-5s %-5s  %s" %
          (v, ("%08X" % c) if c else "   none", d,
           d < 30, d + 5 <= 24,
           "<<CLAIMED" if v in CLAIMED else "<<not in claim"))

A = [v for v,c in rows if c is not None and (c - v) < 30]
B = [v for v,c in rows if c is not None and (c - v) + 5 <= 24]
print()
print("reading A count:", len(A))
print("reading B count:", len(B))
print()
print("A-set == claimed set?", set(A) == CLAIMED)
print("A set minus claimed:", ["%08X"%x for x in sorted(set(A)-CLAIMED)])
print("claimed minus A set:", ["%08X"%x for x in sorted(CLAIMED-set(A))])
print()
print("B set minus claimed:", ["%08X"%x for x in sorted(set(B)-CLAIMED)])
print("claimed minus B set:", ["%08X"%x for x in sorted(CLAIMED-set(B))])

# Closest misses: sites whose nearest target-call delta is 30..40
print()
print("=== near-miss sites (first target call at delta 30..50) ===")
for v in range(start, end - 6):
    i = v - IB
    if BUF[i:i+6] == PAT:
        c = first_target_call(v, 60)
        if c is not None and 30 <= (c - v) <= 50:
            print("  %08X call@%08X delta=%d" % (v, c, c - v))
