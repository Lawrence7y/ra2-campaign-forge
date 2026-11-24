#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""A1: layer sanity -- prove index 0 == ImageBase, sections, raw coverage, and
reproduce the three headline counts (87 / 1305 / 185) from the JSON alone."""
from __future__ import annotations
import json
from collections import Counter, defaultdict
from ds_img import PE, SECS, BASE, IMG, RAW, sha_ok, sec_of, in_raw, secname, u32, rd

J = json.loads(open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\_lead_rtti_map.json",
                    encoding="utf-8").read())

print("SHA-256 match :", sha_ok())
print("FileSize      :", len(RAW))
print("MappedImage   :", len(IMG), hex(len(IMG)))
print("Index0 VA     :", hex(BASE))
print()
print("=== sections (file overlay) ===")
print(f"{'name':<10}{'VA':>12}{'VSize':>12}{'RawPtr':>10}{'RawSize':>10}{'exec':>6}{'wr':>4}")
for s in SECS:
    print(f"{s.name:<10}0x{s.va:08X}{s.vsize:>12X}{s.raw:>10X}{s.rsize:>10X}{str(s.exec):>6}{str(s.wr):>4}")

# --- layer sanity: MZ at index 0, and a known .text byte matches raw ---
print()
print("IMG[0:2]            =", IMG[0:2])
t = SECS[0]
off = t.raw
print(f"IMG[.text.va-BASE:+8] = {IMG[t.va-BASE:t.va-BASE+8].hex()}   RAW[.text.raw:+8] = {RAW[off:off+8].hex()}")
print("layer OK:", IMG[t.va - BASE:t.va - BASE + 8] == RAW[off:off + 8] and IMG[0:2] == b"MZ")

print()
print("=== json meta ===")
print("per_section :", J["per_section"])
print("td_count    :", J["td_count"])
print("col_count   :", J["col_count"])

vt = J["vt2name"]
print("len(vt2name):", len(vt))

print()
print("=== P1 reproduction: vt2name keys by section ===")
c = Counter()
bysec = defaultdict(list)
for k in vt:
    va = int(k, 16)
    sn = secname(va)
    c[sn] += 1
    bysec[sn].append(va)
for sn in sorted(c):
    print(f"  {sn:<14}{c[sn]}")
print("  total         ", sum(c.values()))
text_entries = sorted(bysec.get(".text", []))
print("  .text entries :", len(text_entries))
print("  first 12      :", [f"0x{v:08X}" for v in text_entries[:12]])
for probe in (0x443B24, 0x45CC44, 0x46C2D8):
    print(f"  0x{probe:08X} in vt2name: {('0x%08X' % probe) in vt}  name={vt.get('0x%08X' % probe)}  sec={secname(probe)}")

print()
print("=== P2 reproduction: same-name pairs 8 bytes apart ===")
byname = defaultdict(list)
for k, v in vt.items():
    byname[v].append(int(k, 16))
pairs8 = []
for name, addrs in byname.items():
    a = sorted(addrs)
    for i in range(len(a) - 1):
        if a[i + 1] - a[i] == 8:
            pairs8.append((a[i], a[i + 1], name))
# also: how many entries share a name at all (duplicate names)
dups = {n: v for n, v in byname.items() if len(v) > 1}
print("names with >1 vt:", len(dups), " total entries in them:", sum(len(v) for v in dups.values()))
print("adjacent-by-8 pairs:", len(pairs8))
for lo, hi, name in sorted(pairs8)[:15]:
    print(f"  0x{lo:08X} / 0x{hi:08X}  {name}   secs={secname(lo)},{secname(hi)}")
tgt = vt.get("0x007E1F24"), vt.get("0x007E1F2C")
print("  0x007E1F24 ->", tgt[0], " 0x007E1F2C ->", tgt[1])
print("  slot0/1/2/3 @0x007E1F24 :", [hex(u32(0x7E1F24 + 4 * i) or 0) for i in range(6)])
print("  slot0/1/2/3 @0x007E1F2C :", [hex(u32(0x7E1F2C + 4 * i) or 0) for i in range(6)])

print()
print("=== P3 reproduction: WhatAmI from slot +0x2C ===")
ok, nofn, nodata, notb8, badret, noexec = 0, 0, 0, 0, 0, 0
reasons = Counter()
samples_bad = []
for k, name in vt.items():
    va = int(k, 16)
    fn = u32(va + 0x2C)
    if fn is None:
        nofn += 1; reasons["slot-unreadable"] += 1; continue
    if fn == 0:
        nofn += 1; reasons["slot==0"] += 1; continue
    if not in_raw(fn):
        nodata += 1; reasons["target has no bytes (bss/unmapped)"] += 1
        samples_bad.append((va, name, fn, "nodata")); continue
    if not (sec_of(fn) and sec_of(fn).exec):
        noexec += 1; reasons["target outside .text"] += 1
        samples_bad.append((va, name, fn, "nonexec")); continue
    b = rd(fn, 6)
    if b[0] != 0xB8:
        notb8 += 1; reasons["not mov eax,N"] += 1
        samples_bad.append((va, name, fn, "notb8")); continue
    if b[5] not in (0xC3, 0xC2):
        badret += 1; reasons["ret not immediate"] += 1
        samples_bad.append((va, name, fn, "badret")); continue
    ok += 1
print("  parseable mov eax,N;ret :", ok, "/", len(vt))
print("  breakdown:", dict(reasons))
print("  whatami_rows in json    :", len(J["whatami_rows"]),
      " with n!=None:", sum(1 for r in J["whatami_rows"] if r["n"] is not None))
