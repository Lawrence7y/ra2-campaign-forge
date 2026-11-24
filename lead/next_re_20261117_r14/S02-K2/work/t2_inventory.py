# -*- coding: utf-8 -*-
import os, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
import s02_common as C

rows = C.load_targets()
print("total S02 targets:", len(rows))

# address band histogram (high 16 bits)
band = collections.Counter()
band_named = collections.Counter()
for r in rows:
    va = int(r["entry"], 16)
    b = (va >> 16) & 0xFFFF
    band[b] += 1
    if r["named_L"] == "1":
        band_named[b] += 1
print("\n=== address bands (0xXXXX0000): total / named ===")
for b in sorted(band):
    print("0x%04X0000: %3d / %d" % (b, band[b], band_named[b]))

# CRT region 0x7C0000-0x7DC000
crt = [r for r in rows if 0x7C0000 <= int(r["entry"],16) <= 0x7DCFFF]
print("\nCRT region 0x7C0000-0x7DCFFF: %d entries, %d named" %
      (len(crt), sum(1 for r in crt if r["named_L"]=="1")))

# all sub_ entries sorted by address
subs = sorted([r for r in rows if r["named_L"]=="0"], key=lambda r:int(r["entry"],16))
print("\n=== all %d unnamed S02 entries (entry grade size) ===" % len(subs))
for r in subs:
    print("%s %-10s size=%s" % (r["entry"], r["cov_grade"], r["atlas_size"]))
