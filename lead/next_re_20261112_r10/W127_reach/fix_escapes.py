#!/usr/bin/env python3
"""Detect and repair escape-sequence corruption introduced by non-raw Python strings.

Two known bites:
  "lead\\next_re_..."  -> '\\n' became a NEWLINE  => "lead" + LF + "ext_re_..."
  "W127_reach\\verify_ds_claims.py" -> '\\v' became VT (0x0B) => "reach" + VT + "erify..."
"""
import io
import re
import sys

LEDGER = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
s = io.open(LEDGER, encoding="utf-8").read()

CTRL = {0x0B: "VT(\\v)", 0x0C: "FF(\\f)", 0x08: "BS(\\b)", 0x07: "BEL(\\a)", 0x00: "NUL"}
print("=== control characters present ===")
found = {}
for i, ch in enumerate(s):
    o = ord(ch)
    if o < 0x20 and ch not in "\r\n\t":
        found.setdefault(o, []).append(i)
for o, idxs in found.items():
    print("  0x%02X %-8s count=%d" % (o, CTRL.get(o, "?"), len(idxs)))
    for i in idxs[:6]:
        print("      ...%r..." % s[max(0, i - 28):i + 28])

print("\n=== suspicious 'lead' + newline + 'ext_re_' pattern ===")
pat = re.compile(r"lead" + chr(10) + r"ext_re_(\d+)")
hits = pat.findall(s)
print("  occurrences:", len(hits), hits[:5])

# ---- repairs (raw strings on purpose) ----
fixes = [
    ("lead" + chr(10) + "ext_re_20261112_r10", r"lead\next_re_20261112_r10"),
    ("lead" + chr(10) + "ext_re_20261112_r02", r"lead\next_re_20261112_r02"),
    ("lead" + chr(13) + chr(10) + "ext_re_20261112_r10", r"lead\next_re_20261112_r10"),
    ("lead" + chr(13) + chr(10) + "ext_re_20261112_r02", r"lead\next_re_20261112_r02"),
    ("W127_reach" + chr(11) + "erify_ds_claims.py", r"W127_reach\verify_ds_claims.py"),
    ("W127_reach" + chr(12) + "ix", r"W127_reach\fix"),
]
n_fix = 0
for bad, good in fixes:
    c = s.count(bad)
    if c:
        s = s.replace(bad, good)
        n_fix += c
        print("  repaired %d x %r -> %r" % (c, bad[:40], good[:40]))

# generic: any remaining VT/FF/BS between two word chars -> backslash + letter
def generic(m):
    global n_fix
    n_fix += 1
    return "\\" + m.group(2)


s2, n = re.subn("([A-Za-z_])" + "([\x0b\x0c\x08])" + "([A-Za-z_])",
                lambda m: m.group(1) + "\\" + m.group(3), s)
if n:
    print("  generic repairs:", n)
    s = s2

if n_fix == 0:
    print("nothing to repair")
io.open(LEDGER, "w", encoding="utf-8", newline="").write(s)
back = io.open(LEDGER, encoding="utf-8").read()
left = [(hex(ord(c)), back.count(c)) for c in set(back)
        if ord(c) < 0x20 and c not in "\r\n\t"]
print("\nafter repair: chars=%d remaining control chars=%s" % (len(back), left))
i = back.find("## §829-1")
print("\ncheck:\n" + back[i:i + 320])
