#!/usr/bin/env python3
"""W127k: dedupe the crash logs by content, then identify the 0x6F40A2 fault.

Dedup matters: the harness copies each run's except.txt into per-trip
baseline_except\\ dirs, so 102 files are NOT 102 crash events.

For S1 (EIP=0x6F40A2, EDX=0, read of 0x155) locate the faulting instruction,
its enclosing function, and what [edx+0x155] is.
"""
import collections
import hashlib
import os
import re
import struct

import capstone
import pefile

ROOTS = [
    r"D:\Project\ra2-campaign-forge\ra2youli",
    r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10",
    r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02",
]
PAT_EIP = re.compile(r"Eip\s*[:=]\s*([0-9A-Fa-f]{8})")
PAT_ACC = re.compile(r"Access address\s*[:=]\s*([0-9A-Fa-f]{8})", re.I)

groups = collections.defaultdict(list)
for root in ROOTS:
    for dirpath, _d, filenames in os.walk(root):
        for fn in filenames:
            low = fn.lower()
            if not (low.startswith("except") and low.endswith(".txt")):
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) > 1_000_000:
                    continue
                b = open(p, "rb").read()
            except OSError:
                continue
            txt = b.decode("latin-1", "replace")
            eip = PAT_EIP.search(txt)
            acc = PAT_ACC.search(txt)
            key = (eip.group(1).upper() if eip else None,
                   acc.group(1).upper() if acc else None,
                   hashlib.sha1(b).hexdigest())
            groups[key].append(p)

print("=== distinct crash contents (EIP, access, sha1) ===")
for (eip, acc, sha), paths in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    print("\nEIP=%s acc=%s  sha1=%s  files=%d" % (eip, acc, sha[:12], len(paths)))
    trips = sorted({p.split(os.sep)[-3] if p.endswith("except.txt") else p.split(os.sep)[-1]
                    for p in paths})
    print("   sample: %s" % os.path.relpath(paths[0], r"D:\Project\ra2-campaign-forge"))
    print("   distinct parent dirs: %d" % len(trips))

# ---- identify the 0x6F40A2 fault ----
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = True

FAULT = 0x006F40A2
print("\n\n=== S1 fault site 0x%08X ===" % FAULT)
print("bytes on disk at fault:", img[FAULT - ib:FAULT - ib + 6].hex(" "))
for ins in md.disasm(img[FAULT - 0x20 - ib:FAULT + 0x40 - ib], FAULT - 0x20):
    mark = " <== FAULT" if ins.address <= FAULT < ins.address + ins.size else ""
    print("   %08X  %-20s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))

# enclosing function: walk back to a plausible entry (ret + padding) for context
print("\n=== who calls/jumps near it: search for direct refs to 0x%08X-0x%08X ==="
      % (FAULT - 0x100, FAULT))
text = img[0x00401000 - ib:0x007E038D - ib]
hits = 0
for ins in md.disasm(text, 0x00401000):
    if ins.mnemonic in ("call", "jmp") and ins.op_str.startswith("0x"):
        t = int(ins.op_str, 16)
        if FAULT - 0x100 <= t <= FAULT + 0x40:
            print("   %s @0x%08X -> 0x%08X" % (ins.mnemonic, ins.address, t))
            hits += 1
print("   (%d refs)" % hits)

# is there a string/known table at the +0x155 offset semantics? show nearby symbol-ish data
print("\n=== data at 0x6F40A2's .text neighbours (function entry candidates) ===")
# find preceding ret+padding
va = FAULT
while va > 0x00401000:
    if img[va - 1 - ib] == 0xC3:  # ret
        print("   candidate entry just after ret at 0x%08X" % va)
        break
    va -= 1
