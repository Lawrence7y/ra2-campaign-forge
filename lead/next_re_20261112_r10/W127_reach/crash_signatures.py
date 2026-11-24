#!/usr/bin/env python3
"""W127j: characterise the two non-0x724737 crash signatures found by the census.

S1  EIP=0x006F40A2, access 0x155  (13 files)  -> possibly a THIRD defect
S2  EIP=0x00000000, access 0x00000000 (64 files) -> explain what these files are
"""
import hashlib
import os

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out"
SAMPLES = {
    "S1 (0x6F40A2)": [
        os.path.join(BASE, r"sandbox_game\except.txt"),
        os.path.join(BASE, r"_archive_range1\trip_range1_r1\baseline_except\except.txt"),
    ],
    "S2 (EIP=0)": [
        os.path.join(BASE, r"_archive_ai\trip_ai_guard_r1\baseline_except\except.txt"),
        os.path.join(BASE, r"_archive_run10\trip_crash_step2_r1\baseline_except\except.txt"),
    ],
}

for tag, paths in SAMPLES.items():
    for p in paths:
        if not os.path.exists(p):
            print("%s: MISSING %s" % (tag, p))
            continue
        b = open(p, "rb").read()
        txt = b.decode("latin-1", "replace")
        print("=" * 100)
        print("%s  %s" % (tag, os.path.relpath(p, BASE)))
        print("  size=%d sha1=%s" % (len(b), hashlib.sha1(b).hexdigest()[:16]))
        lines = [ln.rstrip() for ln in txt.splitlines()]
        keep = ("Exception", "EXCEPTION", "Access", "Eip", "Ebp", "Esp", "Ecx", "Edx",
                "Esi", "Edi", "Ebx", "Bytes", "Stack", "0020", "0021", "0022")
        for i, ln in enumerate(lines):
            if any(k in ln for k in keep):
                print("   %4d | %s" % (i, ln[:150]))
        print("   --- first 300 chars ---")
        print("   " + txt[:300].replace("\r\n", "\\n").replace("\n", "\\n"))
