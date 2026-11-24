#!/usr/bin/env python3
"""W127g (scoped): crash-log EIP census over the RELEVANT directories only.

Full-tree walk stalled (the project has an enormous out/ + .tmp/ tree), so this
limits to where gamemd crash logs from this game instance can live:
  ra2youli\\, lead\\next_re_20261112_r10\\, lead\\next_re_20261112_r02\\

Why it matters: §825 predicts a NULL [0x887368] reaching FUN_00724580 faults at
EIP=0x724596 on access address 0x250 -- the same access address as the known
0x724737 crash. A historical log with that EIP would make the second path an
empirical fact rather than a static one.
"""
import collections
import os
import re
import sys

ROOTS = [
    r"D:\Project\ra2-campaign-forge\ra2youli",
    r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10",
    r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02",
]
PAT_EIP = re.compile(r"Eip\s*[:=]\s*([0-9A-Fa-f]{8})")
PAT_ACC = re.compile(r"Access address\s*[:=]\s*([0-9A-Fa-f]{8})", re.I)
PAT_TYPE = re.compile(r"(EXCEPTION_[A-Z_]+)")

rows = []
scanned = 0
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
                txt = open(p, "rb").read().decode("latin-1", "replace")
            except OSError:
                continue
            scanned += 1
            eips = PAT_EIP.findall(txt)
            accs = PAT_ACC.findall(txt)
            types = PAT_TYPE.findall(txt)
            rows.append((p, eips[0].upper() if eips else None,
                         len(eips), accs[0].upper() if accs else None,
                         types[0] if types else None, os.path.getsize(p)))
            sys.stdout.flush()

print("scanned %d files; %d with Eip" % (scanned, sum(1 for r in rows if r[1])))
print("\n=== EIP histogram ===")
for eip, n in collections.Counter(r[1] for r in rows if r[1]).most_common():
    print("  %s : %d" % (eip, n))
print("\n=== access-address histogram ===")
for acc, n in collections.Counter(r[3] for r in rows if r[3]).most_common():
    print("  %s : %d" % (acc, n))
print("\n=== files with EIP != 00724737 ===")
for p, eip, ne, acc, typ, sz in rows:
    if eip and eip != "00724737":
        print("  %s\n     eip=%s acc=%s type=%s size=%d"
              % (os.path.relpath(p, r"D:\Project\ra2-campaign-forge"), eip, acc, typ, sz))
print("\n=== files with NO parseable Eip ===")
for p, eip, ne, acc, typ, sz in rows:
    if not eip:
        print("  %s (size=%d)" % (os.path.relpath(p, r"D:\Project\ra2-campaign-forge"), sz))
