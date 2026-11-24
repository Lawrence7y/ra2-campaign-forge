#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A10 (P3): what does slot +0x2C point at when it is NOT `mov eax,N; ret`?
Classify every one of the 1305, with >= 8 concrete byte witnesses."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, cstr, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}

def whatami(va):
    fn = u32(va + 0x2C)
    if fn is None:
        return ("slot-unreadable", fn)
    if fn == 0:
        return ("slot==NULL", fn)
    if not in_raw(fn):
        return ("target-no-bytes", fn)
    if not is_exec(fn):
        return (f"target-in-{secname(fn)}", fn)
    b = rd(fn, 8)
    if b[0] == 0xB8 and b[5] in (0xC3, 0xC2):
        return ("whatami-mov-eax-ret", fn)
    if b[0] == 0xB8:
        return ("mov-eax-but-no-ret", fn)
    if b[0] == 0xC3:
        return ("ret-only", fn)
    if b[0] == 0x33 and b[1] == 0xC0:
        return ("xor-eax,eax (ret 0)", fn)
    return ("other-code", fn)

cls = Counter()
byc = defaultdict(list)
for k, n in vt.items():
    c, fn = whatami(k)
    cls[c] += 1
    byc[c].append((k, n, fn))

print("=== P3: slot +0x2C target classification over all 1305 ===")
for c, v in cls.most_common():
    print(f"  {c:<24}{v}")
print("  TOTAL", sum(cls.values()))

print()
print("=== per-answer, split .text keys (the 87 bogus) from the rest ===")
for c in cls:
    tt = sum(1 for k, n, fn in byc[c] if secname(k) == ".text")
    print(f"  {c:<24} total={cls[c]:<6} of-which-.text-keys={tt}")

print()
print("=== BYTE WITNESSES: 12 samples per non-conforming class ===")
SHOW = ["slot==NULL", "target-no-bytes", "target-in-.rdata", "other-code",
        "ret-only", "xor-eax,eax (ret 0)", "mov-eax-but-no-ret", "target-in-.data"]
for c in SHOW:
    rows = byc.get(c, [])
    if not rows:
        print(f"\n--- {c}: none ---")
        continue
    print(f"\n--- {c}  (n={cls[c]}) ---")
    for k, n, fn in rows[:12]:
        if fn is None:
            print(f"  key=0x{k:08X} {n[:44]:<44} slotbytes=unreadable")
            continue
        if not in_raw(fn):
            print(f"  key=0x{k:08X} {n[:44]:<44} fn=0x{fn:08X} sec={secname(fn)} NO FILE BYTES (BSS)")
            continue
        b = rd(fn, 16) or b""
        txt = ""
        if is_exec(fn):
            # try to render the first few bytes as a plausible insn
            txt = "<.text>"
        print(f"  key=0x{k:08X} {n[:44]:<44} fn=0x{fn:08X} sec={secname(fn):<10} "
              f"bytes={b.hex()} {txt}")
        if not is_exec(fn) and in_raw(fn):
            # what does it look like as data?
            print(f"                     as dwords: {[hex(u32(fn+4*i) or 0) for i in range(4)]}"
                  f"  ascii={b[:16]!r}")

print()
print("=== DISCRIMINATOR: is +0x2C a valid vtable slot only where a WhatAmI sits? ===")
# Compare: among keys where +0x2C parses, what is the neighbour slot +0x28 / +0x30?
print("  keys with parseable WhatAmI:", cls["whatami-mov-eax-ret"])
print("  keys WITHOUT:", len(vt) - cls["whatami-mov-eax-ret"])

print()
print("=== are the non-parseable ones SHORT vtables (slot 0x2C beyond table end)? ===")
# Heuristic: walk slots from key upward; a slot > ~0x80 into .rdata that isn't a .text ptr
def table_end(key, limit=0x200):
    a = key
    while a < key + limit:
        v = u32(a)
        if v is None:
            return a, "no-bytes"
        if v == 0:
            return a, "null"
        if not is_exec(v):
            return a, f"non-exec({secname(v)})"
        a += 4
    return key + limit, "limit"

ends = Counter()
endof = {}
for k in vt:
    e, why = table_end(k)
    endof[k] = (e, why)
    ends[(e - k) // 4] += 1
print("  slot count before first non-code slot, histogram (top 15):")
for n, c in ends.most_common(15):
    print(f"    {n} slots: {c}")

print()
print("  0x2C = slot index", 0x2C // 4)
print("  keys whose table ends BEFORE slot 11 (0x2C):",
      sum(1 for k, (e, why) in endof.items() if (e - k) // 4 <= 11))
print("  keys whose table ends AT/BEFORE 0x2C and +0x2C is in the next table's header:",
      sum(1 for k, (e, why) in endof.items() if (e - k) // 4 <= 11))
