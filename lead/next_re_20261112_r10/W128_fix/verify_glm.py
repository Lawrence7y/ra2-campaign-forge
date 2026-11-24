#!/usr/bin/env python3
"""W128l: verify the GLM audit's two open caveats + its 74-disp accounting.

Claim A: `.text` has 74 occurrences of disp32 0x00887368 =
         69 (8B 0D mov ecx) + 1 (A1 mov eax) + 1 (8B 35 mov esi) + 3 writes.
Claim B: 0x6A707F and 0x7777F3 dereference the pointer DIRECTLY with a virtual
         call, guarded only by `cmp ecx, ebx/esi` where ebx/esi==0 is unproven.
Claim C: there are exactly 30 direct call/jmp targets == 0x724730.

Everything is re-derived from raw bytes here.
"""
import collections
import struct

import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
TEXT_VA, TEXT_END = 0x00401000, 0x007E038D
text = img[TEXT_VA - ib:TEXT_END - ib]

G = (0x00887368).to_bytes(4, "little")
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

print("=== A. every disp32 occurrence of 0x00887368 and its opcode ===")
# find the disp32, then look at the preceding 1-2 bytes to identify the form
forms = collections.Counter()
sites = []
i = text.find(G)
while i != -1:
    va = TEXT_VA + i                       # address of the disp32 itself
    prev2 = text[i - 2:i] if i >= 2 else b""
    prev1 = text[i - 1:i] if i >= 1 else b""
    kind = "?"
    insn_at = None
    if prev2 == b"\x8b\x0d":
        kind = "mov ecx,[g] (8B 0D)"; insn_at = va - 2
    elif prev1 == b"\xa1":
        kind = "mov eax,[g] (A1)"; insn_at = va - 1
    elif prev2 == b"\x8b\x35":
        kind = "mov esi,[g] (8B 35)"; insn_at = va - 2
    elif prev2 == b"\x89\x1d":
        kind = "mov [g],ebx (89 1D) WRITE"; insn_at = va - 2
    elif prev2 == b"\x89\x35":
        kind = "mov [g],esi (89 35) WRITE"; insn_at = va - 2
    elif prev2 == b"\x89\x15":
        kind = "mov [g],edx (89 15) WRITE"; insn_at = va - 2
    forms[kind] += 1
    sites.append((insn_at, kind))
    i = text.find(G, i + 1)

total = sum(forms.values())
print("total disp32 occurrences: %d" % total)
for k, n in forms.most_common():
    print("   %-28s %d" % (k, n))

print("\n=== A2. context of the non-8B0D forms ===")
for insn_at, kind in sites:
    if insn_at is None or kind.startswith("mov ecx"):
        continue
    lo = max(TEXT_VA, insn_at - 12)
    print("\n  --- %s @0x%08X" % (kind, insn_at))
    for ins in md.disasm(img[lo - ib: insn_at + 26 - ib], lo):
        mark = "  <== here" if ins.address <= insn_at < ins.address + ins.size else ""
        print("     %08X  %-20s %s %s%s" % (ins.address, ins.bytes.hex(),
                                            ins.mnemonic, ins.op_str, mark))

print("\n=== C. direct call/jmp to 0x724730 ===")
calls = []
for ins in md.disasm(text, TEXT_VA):
    if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
        if int(ins.op_str, 16) == 0x00724730:
            calls.append(ins.address)
print("count: %d" % len(calls))
print("  ", ", ".join("0x%08X" % c for c in calls))
