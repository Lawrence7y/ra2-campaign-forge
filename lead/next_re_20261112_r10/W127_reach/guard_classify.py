#!/usr/bin/env python3
"""W127o: AUTHORITATIVE guard classification for every load of [0x887368].

Fixes two defects of the previous attempt:
  1. sub-register writes: `xor cl,cl` / `mov cx,..` write CL/CX, which capstone
     reports as X86_REG_CL / X86_REG_CX, NOT X86_REG_ECX -> must check all four.
  2. conditional branches: a `cmp ecx,0 / je skip` between the load and the call
     means the call is GUARDED. The previous script walked straight through it.

A site is classified:
  UNGUARDED : ECX still holds the loaded value at a direct call/jmp, and no
              conditional branch could skip that call.
  GUARDED   : some conditional branch between load and call targets past the
              call (so the call is skipped on some path)  -> not a crash site.
  CLOBBERED : ECX (or a sub-register) was written before any call.
  NOCALL    : no call/jmp within the window.
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

ECX_FAMILY = {capstone.x86.X86_REG_ECX, capstone.x86.X86_REG_CX,
              capstone.x86.X86_REG_CL, capstone.x86.X86_REG_CH}
JCC = {"je", "jne", "jz", "jnz", "jl", "jle", "jg", "jge", "jb", "jbe", "ja", "jae",
       "js", "jns", "jo", "jno", "jp", "jnp", "jpe", "jpo", "jcxz", "jecxz"}

loads = []
i = text.find(LOAD)
while i != -1:
    loads.append(TEXT_VA + i)
    i = text.find(LOAD, i + 1)

rows = []
for va in loads:
    off = va - TEXT_VA
    window = text[off + 6: off + 6 + 96]
    state = None
    call_addr = tgt = None
    reason = []
    skipped_by = []
    for ins in md.disasm(window, va + 6):
        if ins.address - va > 96:
            state = "NOCALL"
            break
        m = ins.mnemonic
        # conditional branch that could jump past a later call?
        if m in JCC and ins.op_str.startswith("0x"):
            dt = int(ins.op_str, 16)
            # remember it; decide later once we know the call address
            skipped_by.append((ins.address, dt))
            continue
        if m in ("call", "jmp") and ins.op_str.startswith("0x"):
            call_addr = ins.address
            tgt = int(ins.op_str, 16)
            state = "REACHED"
            break
        _r, w = ins.regs_access()
        if ECX_FAMILY & set(w):
            state = "CLOBBERED"
            reason.append("%s %s @0x%08X writes ecx-family"
                          % (m, ins.op_str, ins.address))
            break

    if state == "REACHED":
        # guarded if any conditional branch targets at/after the call address
        guards = [(a, d) for a, d in skipped_by if d > (call_addr or 0)]
        if guards:
            state = "GUARDED"
            reason.append("cond jumps past call: " +
                          ", ".join("%s@0x%08X->0x%08X" % (
                              next((i2.mnemonic for i2 in md.disasm(
                                  img[a - ib:a - ib + 8], a)), "jcc"), a, d)
                              for a, d in guards[:3]))
        else:
            state = "UNGUARDED"
            reason.append("no cond jump past call 0x%08X" % (call_addr or 0))

    rows.append((va, call_addr, tgt, state, "; ".join(reason)))

print("total loads: %d" % len(rows))
cnt = collections.Counter(r[3] for r in rows)
print("classification:", dict(cnt))

print("\n=== UNGUARDED sites grouped by callee ===")
g = collections.defaultdict(list)
for va, ca, tgt, st, why in rows:
    if st == "UNGUARDED":
        g[tgt].append((va, ca))
for tgt, lst in sorted(g.items(), key=lambda kv: -len(kv[1])):
    print("\n  callee 0x%08X : %d unguarded site(s)" % (tgt, len(lst)))
    for va, ca in lst:
        print("     load=0x%08X call=0x%08X" % (va, ca))

print("\n=== GUARDED sites (not crash sites) ===")
for va, ca, tgt, st, why in rows:
    if st == "GUARDED":
        print("  load=0x%08X call=0x%08X -> 0x%08X   %s" % (va, ca, tgt, why))

print("\n=== CLOBBERED / NOCALL ===")
for va, ca, tgt, st, why in rows:
    if st in ("CLOBBERED", "NOCALL"):
        print("  load=0x%08X %s  %s" % (va, st, why))

print("\n=== totals ===")
tot = collections.Counter()
for va, ca, tgt, st, why in rows:
    if st == "UNGUARDED":
        tot[tgt] += 1
print("  unguarded total: %d across %d callees" % (sum(tot.values()), len(tot)))
print(" ", {("0x%08X" % k): v for k, v in tot.items()})
