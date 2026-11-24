#!/usr/bin/env python3
"""W127n: STRICT re-derivation of the "N sites feed [0x887368] as this" counts.

The earlier this_census.py decided "ECX still holds the loaded value" by testing
whether a disassembled op_str starts with 'ecx,' / 'cx,' / 'cl,' / 'ch,'.
That string test MISSES writers such as:
    xchg ecx,eax        (op_str 'eax,ecx')
    xchg eax,ecx
    pop ecx             -> op_str 'ecx' (no comma) — actually caught, but be safe
    bswap ecx
    mul/div do NOT write ecx, but some forms do via edx:eax only (not ecx)

This version uses capstone's register-access analysis (detail=True) and asks
directly: does any instruction between the load and the call WRITE ecx?
Conservative: any write to ecx aborts the attribution.
"""
import collections
import capstone

import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
TEXT_VA, TEXT_END = 0x00401000, 0x007E038D
text = img[TEXT_VA - ib:TEXT_END - ib]

LOAD = bytes([0x8B, 0x0D]) + (0x00887368).to_bytes(4, "little")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

ECX = capstone.x86.X86_REG_ECX

loads = []
i = text.find(LOAD)
while i != -1:
    loads.append(TEXT_VA + i)
    i = text.find(LOAD, i + 1)
print("loads of [0x887368]: %d" % len(loads))

hist = collections.Counter()
sites = collections.defaultdict(list)
for va in loads:
    off = va - TEXT_VA
    window = text[off + 6: off + 6 + 80]
    for ins in md.disasm(window, va + 6):
        if ins.address - va > 80:
            break
        # is this a call/jmp with a direct target?
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            tgt = int(ins.op_str, 16)
            hist[tgt] += 1
            sites[tgt].append((va, ins.address))
            break
        # does it write ecx?
        _read, written = ins.regs_access()
        if ECX in written:
            break

print("\n=== STRICT histogram: callee <- #loads, ECX never rewritten in between ===")
for tgt, n in hist.most_common():
    print("  0x%08X : %d  (%d distinct call sites)"
          % (tgt, n, len({c for _l, c in sites[tgt]})))

print("\n=== call sites per callee ===")
for tgt, lst in sorted(sites.items()):
    cs = sorted({c for _l, c in lst})
    print("  0x%08X : %d sites" % (tgt, len(cs)))
    print("     " + ", ".join("0x%08X" % c for c in cs))

print("\n=== total distinct call sites across all callees: %d ==="
      % len({c for lst in sites.values() for _l, c in lst}))
