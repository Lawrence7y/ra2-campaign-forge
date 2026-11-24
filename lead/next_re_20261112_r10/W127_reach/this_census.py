#!/usr/bin/env python3
"""W127f: full census of "functions that receive [0x887368] as `this`".

The ledger counted only `mov ecx,[0x887368]; call 0x724730` (20 sites) and
concluded the single-point fix is a guard at 0x724730. But FUN_006d1660 also
does `mov ecx,[0x887368]; ...; call 0x724580`, and 0x724580 also first touches
this+0x250. So the defect surface is a *set of routines*, not one routine.

This script produces, for every one of the 69 loads of the global, the set of
call targets reachable in the following window, and a global histogram of
"callee <- how many loads feed it". Only byte-level facts.
"""
import collections
import struct
import pefile
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
TEXT_VA, TEXT_END = 0x00401000, 0x007E038D
text = img[TEXT_VA - ib:TEXT_END - ib]
LOAD = bytes([0x8B, 0x0D]) + (0x00887368).to_bytes(4, "little")

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True

# --- all direct call instructions in .text, indexed by address
calls = {}
for ins in md.disasm(text, TEXT_VA):
    if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
        calls[ins.address] = (int(ins.op_str, 16), ins.mnemonic)
print("direct call/jmp sites in .text: %d" % len(calls))

# --- all loads
loads = []
i = text.find(LOAD)
while i != -1:
    loads.append(TEXT_VA + i)
    i = text.find(LOAD, i + 1)
print("loads of [0x887368]: %d" % len(loads))

# --- for each load: every call in the next 48 bytes whose ECX still == the loaded value.
#     ECX-preservation proxy: no instruction in between writes ECX.
def ecx_written(ins):
    s = ins.op_str.replace(" ", "")
    return s.startswith("ecx,") or s.startswith("cx,") or s.startswith("cl,") or s.startswith("ch,")

hist = collections.Counter()
detail = []
for va in loads:
    off = va - TEXT_VA
    end = off + 6
    window = text[end:end + 48]
    hits = []
    for ins in md.disasm(window, va + 6):
        rel = ins.address - (TEXT_VA + end)
        if rel > 48:
            break
        if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
            hits.append((ins.address, int(ins.op_str, 16), ins.mnemonic))
            break                     # only the first call, ECX dies afterwards
        if ecx_written(ins):
            break                     # ECX reloaded -> this call is not ours
    for ca, tgt, m in hits:
        hist[tgt] += 1
        detail.append((va, ca, tgt, m))

print("\n=== histogram: callee <- #loads feeding it with ECX intact ===")
for tgt, n in hist.most_common():
    print("  0x%08X : %d" % (tgt, n))

def head_derefs_this(tva, n=8):
    """first instructions: do they touch [ecx+off] / [reg+off] derived from ecx?"""
    out = []
    for k, ins in enumerate(md.disasm(img[tva - ib:tva - ib + 48], tva)):
        out.append("%s %s" % (ins.mnemonic, ins.op_str))
        if k >= n:
            break
    return out

print("\n=== per-callee: does it take `this` (=ECX) and dereference it? ===")
for tgt, n in hist.most_common():
    print("\n  0x%08X  (%d loads)" % (tgt, n))
    for line in head_derefs_this(tgt):
        print("      " + line)

print("\n=== per-load detail ===")
for va, ca, tgt, m in detail:
    print("  load=0x%08X  %s@0x%08X -> 0x%08X" % (va, m, ca, tgt))

bytarget = collections.defaultdict(list)
for va, ca, tgt, m in detail:
    bytarget[tgt].append((va, ca))
print("\n=== distinct CALL SITES per callee ===")
for tgt, lst in sorted(bytarget.items()):
    print("  0x%08X : %d call sites: %s" % (tgt, len(lst),
          ", ".join("0x%08X" % c for _, c in lst)))
