#!/usr/bin/env python3
"""W127g: global census of every crash log in the project by EIP.

Motivation: §825 predicts that a NULL [0x887368] reaching FUN_00724580 faults at
EIP=0x724596 reading address 0x250 -- the same access address as the known crash
at 0x724737. If any historical log shows that EIP, the second path is not just
statically reachable but empirically hit.

Parses: 'Eip:00724737', 'Access address:00000250', 'Bytes at CS:EIP (...) : ...'
"""
import collections
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
PAT_EIP = re.compile(r"Eip\s*[:=]\s*([0-9A-Fa-f]{8})")
PAT_ACC = re.compile(r"Access address\s*[:=]\s*([0-9A-Fa-f]{8})", re.I)
PAT_BYTES = re.compile(r"Bytes at CS:EIP\s*\(([0-9A-Fa-f]{8})\)\s*:\s*([0-9A-Fa-f ]+)")
PAT_TYPE = re.compile(r"(EXCEPTION_[A-Z_]+)")

rows = []
scanned = 0
for dirpath, _dirnames, filenames in os.walk(ROOT):
    if ".git" in dirpath:
        continue
    for fn in filenames:
        low = fn.lower()
        if not (low.startswith("except") and low.endswith(".txt")):
            continue
        p = os.path.join(dirpath, fn)
        try:
            if os.path.getsize(p) > 2_000_000:
                continue
            txt = open(p, "rb").read().decode("latin-1", "replace")
        except OSError:
            continue
        scanned += 1
        eips = PAT_EIP.findall(txt)
        accs = PAT_ACC.findall(txt)
        types = PAT_TYPE.findall(txt)
        byt = PAT_BYTES.search(txt)
        rows.append({
            "path": p,
            "rel": os.path.relpath(p, ROOT),
            "mtime": os.path.getmtime(p),
            "size": os.path.getsize(p),
            "eip": eips[0].upper() if eips else None,
            "n_eip": len(eips),
            "acc": accs[0].upper() if accs else None,
            "type": types[0] if types else None,
            "bytes": (byt.group(2).strip() if byt else None),
        })

print("scanned %d except*.txt files, %d with a parseable Eip" %
      (scanned, sum(1 for r in rows if r["eip"])))

hist = collections.Counter(r["eip"] for r in rows if r["eip"])
print("\n=== EIP histogram ===")
for eip, n in hist.most_common():
    print("  EIP %s : %d file(s)" % (eip, n))

print("\n=== files whose EIP is NOT the known 00724737 ===")
for r in sorted((r for r in rows if r["eip"] and r["eip"] != "00724737"),
                key=lambda r: -r["mtime"]):
    print("  %s  eip=%s acc=%s type=%s size=%d" %
          (r["rel"], r["eip"], r["acc"], r["type"], r["size"]))

print("\n=== access addresses seen (any EIP) ===")
for acc, n in collections.Counter(r["acc"] for r in rows if r["acc"]).most_common():
    print("  acc %s : %d" % (acc, n))

print("\n=== the 00724737 files: bytes-at-eip must all agree ===")
sig = collections.Counter((r["bytes"] or "")[:47] for r in rows if r["eip"] == "00724737")
for s, n in sig.most_common():
    print("  %d x  %s" % (n, s))
