# -*- coding: utf-8 -*-
"""R-053 mutation suite -- exact-set scoring (shape = R-047/048/050/051/052).

Every offset carries a pre-run "current byte == expect" mechanical assertion
(G-67). Kill lists derived from window membership:

  M1  flips site-A `push 0` immediate (arg1 NULL)      -> Z2 only.
  M2  flips site-B window byte (push edi)              -> Z3 only.
  M3  flips find-or-create key disp 0x24 -> 0x28        -> Z3 only.
  M4  flips site-C arg1 load disp 0xD0 -> 0xD4          -> Z4 only
      (Z10's census window is 0x6F06E0..0x6F2000, so this byte is outside it;
       expectation corrected after the first run showed killed={Z4}).
  M5  flips Tag ctor arg1 store +0x24 -> +0x28          -> Z5 only.
  M6  flips Tag ctor vptr imm low byte E0 -> E1         -> Z5 only.
  M7  flips ctor trigger-chain head disp 0xA0 -> 0xA4   -> Z6 only.
  M8  flips ctor trigger-chain next disp 0xA8 -> 0xAC   -> Z6 only.
  M9  flips TagTypeClass WhatAmI imm 2D -> 2E           -> Z7 only.
  M10 flips TagTypeClass GetSize imm A4 -> A5           -> Z7 only.
  M11 flips TagClass-vector install imm low A4 -> A5    -> Z8 only.
  M12 flips TagType-vector demote imm low 78 -> 79      -> Z8 only.
  M13 flips TagType lookup global 0xB0E784 -> 0xB0E788  -> Z9 only.
  M14 flips TeamType +0xD0 store disp -> +0xD4           -> Z10 only
      (Z4 reads the *TeamClass* ctor's arg1 path; different byte, so no cross-kill).
  M15 flips find-by-name `push 0xA4` -> 0xA8            -> Z10 only.
  M16 flips TagType dtor chain-next disp 0xA8 -> 0xAC   -> S1 only (structural).
  M17 retargets site-A `call 0x6E4DE0` rel32 low byte   -> Z1, Z2  (G-79 round
      R-061: Z1 was the zero-killer census claim; Z2 co-dies -- the mutated
      byte sits inside Z2's pinned window; red set measured, not predicted).
"""
import contextlib
import io
import os
import runpy
import struct
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r053_tag_arg1" + chr(46) + "py")

CASES = [
    ("M1 site-A arg1 push 0->1",   {0x6C20CB: 0x01}, {"Z2"},       {0x6C20CB: 0x00}),
    ("M2 site-B window byte",      {0x6E52D3: 0x58}, {"Z3"},       {0x6E52D3: 0x57}),
    ("M3 key disp 24->28",         {0x6E52BA: 0x28}, {"Z3"},       {0x6E52BA: 0x24}),
    ("M4 site-C arg1 disp D0->D4", {0x6E8D89: 0xD4}, {"Z4"},       {0x6E8D89: 0xD0}),
    ("M5 Tag arg1 store 24->28",   {0x6E4DF2: 0x28}, {"Z5"},       {0x6E4DF2: 0x24}),
    ("M6 Tag vptr imm E0->E1",     {0x6E4E09: 0xE1}, {"Z5"},       {0x6E4E09: 0xE0}),
    ("M7 chain head A0->A4",       {0x6E4F1F: 0xA4}, {"Z6"},       {0x6E4F1F: 0xA0}),
    ("M8 chain next A8->AC",       {0x6E4F4C: 0xAC}, {"Z6"},       {0x6E4F4C: 0xA8}),
    ("M9 TagType WhatAmI 2D->2E",  {0x6E6491: 0x2E}, {"Z7"},       {0x6E6491: 0x2D}),
    ("M10 TagType GetSize A4->A5", {0x6E64A1: 0xA5}, {"Z7"},       {0x6E64A1: 0xA4}),
    ("M11 Tag vec imm A4->A5",     {0x6E4D83: 0xA5}, {"Z8"},       {0x6E4D83: 0xA4}),
    ("M12 TagType demote 78->79",  {0x6E5B2E: 0x79}, {"Z8"},       {0x6E5B2E: 0x78}),
    ("M13 lookup global 84->88",   {0x6E5E85: 0x88}, {"Z9"},       {0x6E5E85: 0x84}),
    ("M14 TeamType D0->D4 store",  {0x6F135F: 0xD4}, {"Z10"},      {0x6F135F: 0xD0}),
    ("M15 find-by-name A4->A8",    {0x6E6367: 0xA8}, {"Z10"},      {0x6E6367: 0xA4}),
    ("M16 dtor chain A8->AC",      {0x6E5CDD: 0xAC}, {"S1"},       {0x6E5CDD: 0xA8}),
    # R-061 G-79 round: Z1 (E8-site exact census) had ZERO killer in M1..M16.
    # M17 retargets site-A's `call 0x6E4DE0` rel32 low byte 0d->0e (measured
    # 2026-10-26: red = {Z1, Z2}; Z2 co-dies because the mutated byte lies in
    # Z2's pinned window -- cross-assertion byte footprint, expected, per R-059 M18 precedent).
    ("M17 site-A call rel +1",     {0x6C20CF: 0x0E}, {"Z1", "Z2"}, {0x6C20CF: 0x0D}),
]

BLOB = open(os.path.join(ROOT, "ra2youli", "gamemd.exe"), "rb").read()
e = struct.unpack_from("<I", BLOB, 0x3C)[0]
nsec = struct.unpack_from("<H", BLOB, e + 6)[0]
optsz = struct.unpack_from("<H", BLOB, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", BLOB, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", BLOB, tab + i * 40 + 8)
    SEC.append((vaddr, vsize, rawptr, rawsize))


def cur(va):
    rva = va - IB
    for s, vs, rp, rs in SEC:
        if s <= rva < s + vs:
            fo = rp + (rva - s)
            if fo < rp + rs:
                return BLOB[fo]
    raise SystemExit(f"VERIFY-FAIL: 0x{va:08X} unmapped")


vbad = []
for name, mut, exp, cur_exp in CASES:
    for va, want in cur_exp.items():
        got = cur(va)
        if got != want:
            vbad.append(f"{name}: VA 0x{va:08X} cur={got:02X} want={want:02X}")
if vbad:
    print("PRE-RUN BYTE VERIFY FAILED (G-67 gate):")
    for x in vbad:
        print("  " + x)
    sys.exit(2)
print("pre-run byte verify: all offsets' current bytes match expectations\n")

LABELS = tuple("Z%d" % i for i in range(1, 11)) + ("S1",)


def run(mut):
    os.environ["R053_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
    buf = io.StringIO()
    rc = None
    try:
        with contextlib.redirect_stderr(buf):
            runpy.run_path(GATE, run_name="__main__")
        rc = 0
    except SystemExit as ex:
        rc = ex.code
    killed = set()
    for line in buf.getvalue().splitlines():
        parts = line.split()
        if parts and parts[0] in LABELS and len(parts) > 1 and parts[1] == "FAIL:":
            killed.add(parts[0])
    return rc, killed


rc0, base = run({})
print("baseline rc=%s failed=%s" % (rc0, sorted(base)))
if rc0 != 0 or base:
    print("BASELINE NOT GREEN -- abort")
    sys.exit(2)

ok_all = True
n_ok = 0
killed_union = set()
for name, mut, expect, _ in CASES:
    rc, killed = run(mut)
    killed_union |= killed
    score_ok = (killed == expect) and (rc != 0)
    n_ok += 1 if score_ok else 0
    print("%-30s expect=%-12s killed=%-12s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False

# G-79 machine reconciliation (R-059 pattern): counted assertions Z1..Z10 must
# each have >=1 killer (S1 is structural, excluded from the denominator).
COUNTED = tuple("Z%d" % i for i in range(1, 11))
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    ok_all = False
else:
    print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))

print(f"\n== R-053 mutation {n_ok}/{len(CASES)} 精确集合击杀 ==")
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
