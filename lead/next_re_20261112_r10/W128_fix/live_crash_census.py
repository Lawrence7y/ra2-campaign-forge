#!/usr/bin/env python3
"""W128e: crash signatures in LIVE outputs only.

Distinction that matters: the harness archives each run's pre-existing
except.txt into `<trip>\\baseline_except\\`, so those files are INHERITED copies,
not evidence that the trip crashed. A live output is a `sandbox_game\\except.txt`
or an `except_*.txt` written directly into an out/ root.

This answers: across independent runs, which signature dominates?
"""
import collections
import hashlib
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge\lead"
PAT_EIP = re.compile(r"Eip\s*[:=]\s*([0-9A-Fa-f]{8})")
PAT_ACC = re.compile(r"Access address\s*[:=]\s*([0-9A-Fa-f]{8})", re.I)

live = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip archived baseline copies entirely
    if "baseline_except" in dirpath:
        continue
    for fn in filenames:
        low = fn.lower()
        if not (low.startswith("except") and low.endswith(".txt")):
            continue
        p = os.path.join(dirpath, fn)
        rel = os.path.relpath(p, ROOT)
        # a live output lives in a sandbox_game dir or directly in an out/ root
        if not (os.path.basename(dirpath) == "sandbox_game" or
                os.path.basename(os.path.dirname(dirpath)) in ("out",)):
            continue
        try:
            if os.path.getsize(p) > 1_000_000:
                continue
            b = open(p, "rb").read()
        except OSError:
            continue
        txt = b.decode("latin-1", "replace")
        eip = PAT_EIP.search(txt)
        acc = PAT_ACC.search(txt)
        live.append({
            "rel": rel,
            "eip": eip.group(1).upper() if eip else None,
            "acc": acc.group(1).upper() if acc else None,
            "sha": hashlib.sha1(b).hexdigest()[:12],
            "mtime": os.path.getmtime(p),
        })

print("live crash logs found: %d\n" % len(live))
print("%-58s %-10s %-10s %-14s" % ("path (relative to lead\\)", "EIP", "Access", "sha1[:12]"))
print("-" * 100)
for r in sorted(live, key=lambda r: -r["mtime"]):
    print("%-58s %-10s %-10s %-14s" % (r["rel"][:58], r["eip"], r["acc"], r["sha"]))

print("\n=== signature histogram (live only) ===")
h = collections.Counter((r["eip"], r["acc"]) for r in live)
for (eip, acc), n in h.most_common():
    print("  EIP=%-10s Access=%-10s : %d" % (eip, acc, n))

print("\n=== distinct contents (live only) ===")
print("  ", len({r["sha"] for r in live}))
