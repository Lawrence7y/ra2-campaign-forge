#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A15: P3 calibration.  (a) MFC MessageMap: AFX_MSGMAP{sig,pBaseFn,pfnGetBaseMap} ->
   0x2A / 0x27 entries.  (b) 144 small-N WhatAmI: offset sweep 0..0x3C to test whether
   0x2C is THE canonical slot or just one of several."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from ds_img import BASE, IMG, SECS, in_raw, is_exec, u32, rd, secname

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())
vt = {int(k, 16): v for k, v in J["vt2name"].items()}

def is_whatami(fn, maxN=200):
    if fn is None or not is_exec(fn):
        return None
    b = rd(fn, 6)
    if b[0] != 0xB8 or b[5] not in (0xC3, 0xC2):
        return None
    n = int.from_bytes(b[1:5], "little")
    return n if n < maxN else None

print("=== (a) calibrate the 0x2C slot: MFC message-map getters live at +0x24/+0x28 ===")
cands = {}
for k in vt:
    for off in (0x20, 0x24, 0x28):
        n = is_whatami(u32(k + off), 0x10000)
        if n in (0x2A, 0x27):
            cands.setdefault(off, []).append((k, vt[k], n))
for off in sorted(cands):
    c = Counter(x[2] for x in cands[off])
    print(f"  +0x{off:02X}: {len(cands[off])} hits  {dict(c)}")
print()
print("  witnesses:")
for off in sorted(cands):
    for k, n, v in cands[off][:4]:
        fn = u32(k + off)
        print(f"    key=0x{k:08X} +0x{off:02X}->0x{fn:08X} imm=0x{v:X} {n}")

print()
print("=== (b) offset sweep: which +0xNN slot most often yields mov eax,smallN;ret ===")
print(f"{'off':<8}{'count':<8}{'of 1305':<12}")
best = []
for off in range(0, 0x40, 4):
    c = sum(1 for k in vt if is_whatami(u32(k + off)) is not None)
    best.append((off, c))
    print(f"+0x{off:02X}   {c:<8}{100*c/len(vt):>5.1f}%")

print()
print("=== (c) am I missing WhatAmI because .text coverage is incomplete?  sanity: ===")
print("  every one of the 144 small-N values, is target a real fn entry (preceded by ret/nop/padding)?")
ok = 0
tot = 0
for k in vt:
    n = is_whatami(u32(k + 0x2C))
    if n is None:
        continue
    tot += 1
    fn = u32(k + 0x2C)
    prev = rd(fn - 1, 1)[0]
    if prev in (0xC3, 0xC2, 0xCC, 0x90):
        ok += 1
print(f"  {ok}/{tot} have a ret/int3/nop byte immediately before (plausible fn boundary)")

print()
print("=== (d) the 1305 keys: how many have ANY WhatAmI at ANY slot 0..0x3C? ===")
any_ = 0
multi_off = Counter()
for k in vt:
    offs = [off for off in range(0, 0x40, 4) if is_whatami(u32(k + off)) is not None]
    if offs:
        any_ += 1
        multi_off[len(offs)] += 1
print(f"  keys with >=1 WhatAmI pattern at any slot 0..0x3C: {any_}/1305")
print("  number of matching slots per such key:", dict(multi_off))
