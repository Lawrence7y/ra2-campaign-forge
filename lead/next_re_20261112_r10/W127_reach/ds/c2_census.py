"""C2 part 3: (a) prove 0x6D14F0 is a real function entry, (b) exhaustive
4-class reference census for all six entries in this cluster, including the
function-pointer class over the ENTIRE file-backed image (not just .rdata/.data)
so a vtable slot cannot be missed.

Pointer scan covers every section's file-backed bytes; .data BSS tail
(0x87E000..0xB79BE4) has NO file bytes and is reported as "cannot know".
"""
from base import BUF, IB, TEXT, RDATA, DATA, SECTIONS, u32, s32, in_raw

ENTRIES = [0x006D14F0, 0x006D1570, 0x006D15F0, 0x006D1610, 0x006D1660, 0x006D1680]

# ---- (a) does the claimed A contain an absolute 0x887368 reference? ----
print("=== check: does the neighbourhood reference 0x887368 as an absolute disp? ===")
def abs_refs_in(lo, hi, target):
    got = []
    for va in range(lo, hi - 6):
        i = va - IB
        # mod=00 rm=101  (disp32 absolute) forms used by mov r32,[abs] / push [abs]
        if BUF[i] in (0x8B, 0x89, 0xA1, 0xA3, 0x8D) :
            m = BUF[i + 1]
            mod = m >> 6
            rm = m & 7
            if mod == 0 and rm == 5:
                if u32(va + 2) == target:
                    got.append(va)
        if BUF[i] == 0xFF and (BUF[i+1] >> 6) == 0 and (BUF[i+1] & 7) == 5:
            if u32(va + 2) == target:
                got.append(va)
    return got
for nm, lo, hi in (("0x6D14F0+116", 0x006D14F0, 0x006D1564),
                   ("0x6D1640+0x200 (real copy)", 0x006D1640, 0x006D1760)):
    r = abs_refs_in(lo, hi, 0x00887368)
    print("  %-28s -> %d refs to 0x887368: %s" % (nm, len(r), ["%08X" % x for x in r]))

print()
print("=== byte-compare: is 0x6D14F0..0x6D1563 a duplicate of 0x6D1680..? ===")
# find best matching offset
src = bytes(BUF[0x006D14F0 - IB: 0x006D1564 - IB])
for cand in range(0x006D1660, 0x006D1740):
    blob = bytes(BUF[cand - IB: cand - IB + len(src)])
    # compare with the byte at +0x30 region skipped (0x6D1520 style vs 0x6D16A0)
    same = sum(1 for a, b in zip(src, blob) if a == b)
    print("  offset 0x%08X: %d/%d identical bytes" % (cand, same, len(src)))

print()
print("=== exhaustive reference census (4 classes) for cluster entries ===")
all_secs = [(s["name"], s["va"], s["va"] + s["rawsize"]) for s in SECTIONS]

for f in ENTRIES:
    # class1 direct rel call/jmp (byte-level, no decoder)
    c1 = []
    for va in range(TEXT["va"], TEXT["va"] + TEXT["vsize"] - 5):
        if BUF[va - IB] in (0xE8, 0xE9):
            if va + 5 + s32(va + 1) == f:
                c1.append((va, "call" if BUF[va-IB] == 0xE8 else "jmp"))
    # class2 immediate in .text (raw dword anywhere in .text)
    c2 = [va for va in range(TEXT["va"], TEXT["va"] + TEXT["vsize"] - 4)
          if u32(va) == f]
    # class3 pointer dword, all file-backed sections
    c3 = []
    for nm, lo, hi in all_secs:
        for va in range(lo, hi - 3):
            if u32(va) == f:
                c3.append((nm, va))
    print("0x%08X" % f)
    print("   class1 direct call/jmp : %d %s" % (len(c1), [("%s@%08X" % (k, a)) for a, k in c1]))
    print("   class2 imm dword in .text: %d %s" % (len(c2), ["%08X" % x for x in c2]))
    print("   class3 pointer dword    : %d %s" % (len(c3), [("%s:%08X" % x) for x in c3]))

print()
print("=== BSS caveat: .data file-backed vs virtual ===")
print("  .data va=%08X rawsize=%08X vsize=%08X" % (DATA["va"], DATA["rawsize"], DATA["vsize"]))
print("  file-backed end = %08X, virtual end = %08X" % (DATA["va"] + DATA["rawsize"], DATA["va"] + DATA["vsize"]))
print("  NO FILE BYTES in 0x%08X..0x%08X -> pointer scan there is impossible on disk"
      % (DATA["va"] + DATA["rawsize"], DATA["va"] + DATA["vsize"]))
print("  is 0x887368 raw-backed? ", in_raw(0x00887368, 4))
print("  is 0x6D14F0 referenced from BSS? unanswerable statically")

# Does 0x887368 itself have a static initializer in file bytes?
print()
print("  0x887368 static init bytes (if raw-backed):",
      "N/A - not in file bytes" if not in_raw(0x00887368, 4) else blob_hex(0x887368, 4))
