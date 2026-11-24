#!/usr/bin/env python3
"""W127l: the EIP=0 signature -- is it one crash copied, or many events?

At the fault site (0x47C4FD: call [eax+0x2c]) the registers tell the story:
  ESI = node pointer, EAX = the node's first dword used as a vtable.
If EAX lies OUTSIDE every image section, the "vtable" is not a vtable at all
=> the node's memory was freed/reused => dangling chain entry (②-b, UAF).

This prints ESI/EAX for every DISTINCT EIP=0 log and checks EAX against the
image ranges.
"""
import collections
import hashlib
import os
import re

ROOTS = [
    r"D:\Project\ra2-campaign-forge\ra2youli",
    r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10",
    r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02",
]
# image sections (VA ranges)
SECTIONS = [
    (".text", 0x00401000, 0x007E038D),
    (".rdata", 0x007E1000, 0x00811074),
    (".data", 0x00812000, 0x00B79BE4),
    (".rsrc", 0x00B7A000, 0x00B92128),
    (".detour", 0x00B93000, 0x00B95718),
]


def in_image(v):
    return any(lo <= v < hi for _, lo, hi in SECTIONS)


def section_of(v):
    for n, lo, hi in SECTIONS:
        if lo <= v < hi:
            return n
    return "OUTSIDE-IMAGE"


REG = re.compile(r"(Eax|Ebx|Ecx|Edx|Esi|Edi|Ebp|Esp)\s*:\s*([0-9A-Fa-f]{8})")

seen = {}
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
            if "Eip:00000000" not in txt:
                continue
            sha = hashlib.sha1(b).hexdigest()
            if sha in seen:
                seen[sha]["files"].append(p)
                continue
            regs = dict(REG.findall(txt))
            seen[sha] = {"files": [p], "regs": regs}

print("distinct EIP=0 logs: %d" % len(seen))
print("%-10s %-6s %-12s %-12s %-12s %-14s %s" %
      ("sha1", "files", "ESI(node)", "EAX('vtab')", "EDI(want)", "EAX section", "EAX valid vtable?"))
print("-" * 110)
n_out = 0
for sha, d in sorted(seen.items(), key=lambda kv: -len(kv[1]["files"])):
    r = d["regs"]
    esi = int(r.get("Esi", "0"), 16)
    eax = int(r.get("Eax", "0"), 16)
    edi = int(r.get("Edi", "0"), 16)
    sec = section_of(eax)
    ok = "YES" if sec in (".rdata", ".data") else "NO"
    if ok == "NO":
        n_out += 1
    print("%-10s %-6d 0x%08X   0x%08X   0x%08X     %-14s %s" %
          (sha[:10], len(d["files"]), esi, eax, edi, sec, ok))

print("\nEAX outside .rdata/.data (=> dangling/reused node): %d / %d distinct logs"
      % (n_out, len(seen)))
print("\nEDI (the WhatAmI value being searched for) values:",
      sorted({d["regs"].get("Edi") for d in seen.values()}))

print("\n=== sample paths per distinct log ===")
for sha, d in sorted(seen.items(), key=lambda kv: -len(kv[1]["files"]))[:6]:
    print("  %s  (%d files)  e.g. %s" % (sha[:10], len(d["files"]),
          os.path.relpath(d["files"][0], r"D:\Project\ra2-campaign-forge")))
