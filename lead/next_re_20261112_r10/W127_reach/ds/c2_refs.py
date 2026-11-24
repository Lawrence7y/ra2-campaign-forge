"""C2: reachability of 0x6D14F0 / 0x6D1570 / 0x6D15F0.

Four reference classes, all computed by me:
 1. direct call/jmp rel32 in .text   (E8/E9 with target == f)
 2. address appearing as an immediate operand inside .text
 3. function pointer (dword) in .rdata / .data (file-backed bytes only!)
 4. virtual-table slot (implied by 3, but cross-checked against vtable runs)

For 1 and 4 I use capstone with md.skipdata=True over the whole .text, and I
ALSO do an independent byte-scan so that a capstone decode desync cannot hide
a reference.

Interior-address question is separate: a reference to f+8 is a reference to
code inside f, so I report any reference landing anywhere inside [f, f+size).
"""
from base import BUF, IB, TEXT, RDATA, DATA, u32, s32, in_raw, blob, cstr
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

TARGETS = {
    0x006D14F0: ("A", 116),
    0x006D1570: ("B", 0x15E3 - 0x15F0),
    0x006D15F0: ("C", 27),
}

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True

text_lo = TEXT["va"]
text_hi = TEXT["va"] + TEXT["vsize"]
code = bytes(BUF[text_lo - IB: text_hi - IB])

print("=== capstone linear sweep of .text (skipdata=True) ===")
n_insn = 0
directs = {}     # target_f -> list of (site, text)
imm_hits = {}    # f -> list of (site, insn text)
for ins in md.disasm(code, text_lo):
    n_insn += 1
    # class 1: direct call/jmp rel
    if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
        try:
            t = int(ins.op_str, 16)
        except ValueError:
            t = None
        if t is not None:
            for f in TARGETS:
                if f == t:
                    directs.setdefault(f, []).append((ins.address, ins.mnemonic, ins.op_str, "exact"))
                elif f < t < f + 0x200:
                    directs.setdefault(f, []).append((ins.address, ins.mnemonic, ins.op_str, "interior"))
    # class 2: address as immediate operand
    if ins.op_str:
        for f in TARGETS:
            h = hex(f)
            if h in ins.op_str or ("0x%x" % f) in ins.op_str:
                imm_hits.setdefault(f, []).append((ins.address, ins.mnemonic, ins.op_str))

print("instructions decoded:", n_insn)
print()
for f, (tag, sz) in TARGETS.items():
    print("--- target %s 0x%08X size=%d  range 0x%08X..0x%08X ---" % (tag, f, sz, f, f + sz))
    d = directs.get(f, [])
    print("  class1 (capstone direct call/jmp): %d" % len(d))
    for x in d:
        print("      site=%08X %s %s (%s)" % x)
    m = imm_hits.get(f, [])
    print("  class2 (imm operand text match):   %d" % len(m))
    for x in m:
        print("      site=%08X %s %s" % x)
    print()

# Independent byte scan for class 1 (rel32) -- no decoder involved.
print("=== independent raw-byte scan, class1 (E8/E9 + rel32) ===")
for f, (tag, sz) in TARGETS.items():
    found = []
    for va in range(text_lo, text_hi - 5):
        i = va - IB
        if BUF[i] in (0xE8, 0xE9):
            t = va + 5 + s32(va + 1)
            if f <= t < f + sz:
                found.append((va, t, "E8" if BUF[i] == 0xE8 else "E9"))
    print("  0x%08X: %d  %s" % (f, len(found), found))

# class 2 independent: raw dword search for the VA inside .text
print()
print("=== independent raw-byte scan, class2 (dword == VA inside .text) ===")
for f, (tag, sz) in TARGETS.items():
    found = []
    for va in range(text_lo, text_hi - 4):
        if u32(va) == f:
            found.append(va)
    print("  0x%08X: %d occurrences  %s" % (f, len(found), ["%08X" % x for x in found]))

# class 3: absolute dword in .rdata and .data, ONLY file-backed bytes.
print()
print("=== class3: dword == VA in .rdata/.data (file-backed bytes only) ===")
for sec, nm in ((RDATA, ".rdata"), (DATA, ".data")):
    lo = sec["va"]
    hi = lo + sec["rawsize"]          # IMPORTANT: rawsize, not vsize (BSS!)
    print("  %s scanning VA range %08X..%08X (rawsize=%08X, vsize=%08X)" %
          (nm, lo, hi, sec["rawsize"], sec["vsize"]))
    for f, (tag, sz) in TARGETS.items():
        found = []
        for va in range(lo, hi - 3):
            if u32(va) == f:
                found.append(va)
        print("    0x%08X: %d  %s" % (f, len(found), ["%08X" % x for x in found]))
    # also any interior pointer
    for f, (tag, sz) in TARGETS.items():
        found = []
        for va in range(lo, hi - 3):
            v = u32(va)
            if f < v < f + sz:
                found.append((va, v))
        if found:
            print("    0x%08X interior ptrs: %s" % (f, [("%08X->%08X" % x) for x in found]))

# class 3b: the whole image, for completeness (covers sections I was not told about)
print()
print("=== class3b: dword == VA anywhere in file-backed bytes (all sections) ===")
from base import SECTIONS
for s in SECTIONS:
    lo = s["va"]; hi = lo + s["rawsize"]
    for f, (tag, sz) in TARGETS.items():
        found = [va for va in range(lo, hi - 3) if u32(va) == f]
        if found:
            print("  %-8s 0x%08X -> %s" % (s["name"], f, ["%08X" % x for x in found]))

# Sanity: does the scan method find a KNOWN-good reference? pick 0x6D1200
# which we saw called from 0x6D094D.
print()
print("=== positive control: same scans for 0x6D1200 (must be nonzero) ===")
ctrl = 0x006D1200
c1 = [va for va in range(text_lo, text_hi - 5)
      if BUF[va-IB] in (0xE8,0xE9) and va+5+s32(va+1) == ctrl]
print("  class1 direct:", ["%08X" % x for x in c1])
c3 = []
for s in SECTIONS:
    for va in range(s["va"], s["va"] + s["rawsize"] - 3):
        if u32(va) == ctrl:
            c3.append((s["name"], va))
print("  class3 ptr:", [("%s:%08X" % x) for x in c3])
c2 = [va for va in range(text_lo, text_hi - 4) if u32(va) == ctrl]
print("  class2 imm:", ["%08X" % x for x in c2])
