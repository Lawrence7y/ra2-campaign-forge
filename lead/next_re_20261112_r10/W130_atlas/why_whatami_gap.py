#!/usr/bin/env python3
"""W130b: why do only 185/1305 vtables yield a WhatAmI?

Hypotheses:
  H1 only PRIMARY vtables have WhatAmI at +0x2C (interface tables use that slot
     for an interface method)          -> check resolved-vs-primary correlation
  H2 unresolved slots point to a thunk / adjustor / non-B8 prologue
  H3 unresolved slots are whatami inherited from a base whose impl is B8 but the
     slot value is a `jmp` thunk to it -> look at the target's first bytes

Reads class_atlas.tsv + the image; prints a breakdown and samples.
"""
import collections
import json
import os
import struct

import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()


def u32(va):
    return struct.unpack("<I", img[va - ib:va - ib + 4])[0]


def is_code(v):
    return 0x00401000 <= v < 0x007E038D


rows = []
with open(os.path.join(HERE, "class_atlas.tsv"), encoding="utf-8") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        p = line.rstrip("\n").split("\t")
        rows.append(dict(zip(hdr, p)))

print("rows: %d" % len(rows))

counts = collections.Counter()
for r in rows:
    key = ("primary" if r["primary"] == "1" else "interface",
           "ami" if r["whatami"] else "no-ami")
    counts[key] += 1
print("\n=== resolved-vs-primary ===")
for k, v in sorted(counts.items()):
    print("  %-10s %-8s : %d" % (k[0], k[1], v))

# what do unresolved slots point at?
print("\n=== what the unresolved +0x2C slot points at ===")
kinds = collections.Counter()
samples = collections.defaultdict(list)
for r in rows:
    if r["whatami"]:
        continue
    vt = int(r["vt"], 16)
    impl = int(r["whatami_impl"], 16) if r["whatami_impl"] else None
    if impl is None:
        k = "no-slot"
    elif not is_code(impl):
        k = "not-code(%s)" % ("data" if 0x007E1000 <= impl < 0x00B95718 else "out")
    else:
        b = img[impl - ib: impl - ib + 8]
        if b[0] == 0xE9:
            k = "jmp-rel32(thunk)"
        elif b[:2] in (b"\x8B\xFF", b"\x8B\xC0", b"\x8B\xC9"):
            k = "mov-reg(thunk)"
        elif b[0] == 0xB8:
            k = "B8-but-not-ret(%02X%02X)" % (b[5], b[6])
        else:
            k = "other-prologue(%02X)" % b[0]
    kinds[k] += 1
    if len(samples[k]) < 5:
        samples[k].append((r["vt"], r["class"], r["whatami_impl"]))
for k, v in kinds.most_common():
    print("  %-26s %d" % (k, v))
    for vt, cls, impl in samples[k]:
        print("      %s %-34s slot=+%s" % (vt, cls[:34], impl))

# H3: does following one jmp level resolve them?
print("\n=== follow one jmp-rel32 level ===")
fixed = 0
still = 0
for r in rows:
    if r["whatami"]:
        continue
    impl = int(r["whatami_impl"], 16) if r["whatami_impl"] else None
    if impl is None or not is_code(impl):
        still += 1
        continue
    b = img[impl - ib: impl - ib + 8]
    if b[0] == 0xE9:
        tgt = impl + 5 + struct.unpack("<i", b[1:5])[0]
        if is_code(tgt):
            b2 = img[tgt - ib: tgt - ib + 8]
            if b2[0] == 0xB8 and b2[5] in (0xC3, 0xC2):
                fixed += 1
                continue
    still += 1
print("  resolved by following one jmp: %d" % fixed)
print("  still unresolved             : %d" % still)

# H2b: are unresolved ones concentrated in the interface tables?
print("\n=== unresolved by section ===")
byt = collections.Counter()
for r in rows:
    if not r["whatami"]:
        byt[r["section"]] += 1
print("  ", dict(byt))
