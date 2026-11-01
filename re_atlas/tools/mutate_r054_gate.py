# -*- coding: utf-8 -*-
"""R-054 mutation suite -- exact-set scoring (shape = R-047/048/050/051/052/053).

Every offset carries a pre-run "current byte == expect" mechanical assertion (G-67).
Kill lists derived from window membership, NOT from a guess:

  M1  fixup marker imm 0x12 -> 0x13 (@0x691E68, inside cmp [edx-4],0x12)   -> A1
  M2  entry-pair key writer disp A4 -> A6 (@0x691930)                       -> A2,B5
  M3  dispatch bound 0x90 -> 0x91 (@0x6DD8DD)                              -> A3
  M4  action-table slot 0x11 dword low byte 7B -> 7C (@0x6DFDEC+0x44)       -> A5
  M5  handler forwarding byte (@0x6DE396)                                   -> A5
  M6  0x6E11C0 head global low byte 4C -> 4D (@0x6E11C2)                    -> A6
  M7  "%d" template push low byte 6C -> 6D (@0x6918DB)                      -> B1
  M8  "%d" literal byte NUL->'x' (@0x817F6E)                                -> B2
  M9  format-class imm 0x42 -> 0x43 (@0x7C8F0B)                             -> B3
  M10 "%d,%d" literal byte (@0x81C000)                                      -> B4
  M11 entry-pair value writer disp A8 -> AA (@0x69193B)                     -> B5
  M12 count bound imm 0x32 -> 0x33 (@0x691927)                              -> B6
  M13 inline +0x9C store disp 9C -> 9E (@0x691A57)                          -> C1,C4,C5
      (C5 asserts the SAME byte as the 89-register encoding form, so it must die too;
       expectation corrected after the first run showed killed={C1,C4,C5}).
  M14 inline +0xA0 store disp A0 -> A2 (@0x691A5D)                          -> C1
  M15 vptr-quad byte at inline site (@0x691A63)                              -> C1,C3
  M16 "ScriptTypes" push low byte 28 -> 29 (@0x69197F)                       -> C6
  M17 shared base-init rel32 byte (@0x691A51)                                -> C7
  M18 registry vptr global low byte C8 -> C9 (@0x69171A)                     -> D1
  M19 dtor compaction byte (@0x6917D1)                                       -> D2
  M20 +0x98 store disp 98 -> 9A at factory site (@0x691D28)                  -> D4
  M21 slot16 disp 98 -> 9A (@0x691F92)                                       -> D4,D6
  M22 vector push displacement fc -> f8 (@0x6917D3)                          -> D2
"""
import contextlib
import io
import os
import runpy
import struct
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r054_l4_residuals" + chr(46) + "py")

CASES = [
    ("M1 fixup marker 12->13",     {0x691E69: 0x13}, {"A1"},       {0x691E69: 0x12}),
    ("M2 key writer A4->A6",       {0x691931: 0xA6}, {"A2", "B5"}, {0x691931: 0xA4}),
    ("M3 dispatch bound 90->91",   {0x6DD8DD: 0x91}, {"A3"},       {0x6DD8DD: 0x90}),
    ("M4 table slot 0x11",         {0x6DFE30: 0x7C}, {"A5"},       {0x6DFE30: 0x7B}),
    ("M5 handler rel32 byte",      {0x6DE397: 0x26}, {"A5"},       {0x6DE397: 0x25}),
    ("M6 6E11C0 global 3D->3E",    {0x6E11C2: 0x3E}, {"A6"},       {0x6E11C2: 0x3D}),
    ("M7 %d push 6C->6D",          {0x6918DB: 0x6D}, {"B1"},       {0x6918DB: 0x6C}),
    ("M8 %d NUL->x",               {0x817F6E: 0x78}, {"B2"},       {0x817F6E: 0x00}),
    ("M9 format class 42->43",     {0x7C8F0A: 0x43}, {"B3"},       {0x7C8F0A: 0x42}),
    ("M10 %d,%d literal",          {0x81C001: 0x65}, {"B4"},       {0x81C001: 0x64}),
    ("M11 value writer A8->AA",    {0x69193C: 0xAA}, {"B5"},       {0x69193C: 0xA8}),
    ("M12 count bound 32->33",     {0x691927: 0x33}, {"B6"},       {0x691927: 0x32}),
    ("M13 inline 9C->9E",          {0x691A57: 0x9E}, {"C1", "C4", "C5"}, {0x691A57: 0x9C}),
    ("M14 inline A0->A2",          {0x691A5D: 0xA2}, {"C1"},       {0x691A5D: 0xA0}),
    ("M15 inline vptr byte",       {0x691A64: 0x11}, {"C1", "C3"}, {0x691A64: 0x10}),
    ("M16 ScriptTypes push",       {0x69197E: 0x29}, {"C6"},       {0x69197E: 0x28}),
    ("M17 base-init rel32",        {0x691A51: 0xAC}, {"C7"},       {0x691A51: 0xAB}),
    ("M18 registry vptr C8->C9",   {0x69171A: 0xC9}, {"D1"},       {0x69171A: 0xC8}),
    ("M19 dtor compaction modrm",  {0x6917D2: 0x55}, {"D2", "D3"}, {0x6917D2: 0x54}),
    # D3 red under M19 is the R-061 disp32-SET pin reading this disp byte --
    # expected cross-kill, measured 2026-10-26 (same byte footprint rule as M18
    # in R-059: red sets come from measurement, not from semantic intuition).
    ("M20 +98 store 98->9A",       {0x691D28: 0x9A}, {"D4"},       {0x691D28: 0x98}),
    ("M21 slot16 disp 98->9A",     {0x691F92: 0x9A}, {"D4", "D6"}, {0x691F92: 0x98}),
    ("M22 vector push fc->f8",     {0x6917D4: 0xF8}, {"D2"},       {0x6917D4: 0xFC}),
    # R-061 G-79 round: A4/C2/D3/D5/D7 had ZERO killers. Red-sets measured
    # 2026-10-26; D3 additionally REWRITTEN from the byte-unkillable negative
    # census into a positive disp32-SET pin (out-of-set flip = M25).
    ("M23 A4 alias idx38 dword0",  {0x6DFE84: 0x01}, {"A4"},       {0x6DFE84: 0xDB}),
    ("M24 C2 xor ebx->xor eax",    {0x69198A: 0xC0}, {"C2"},       {0x69198A: 0xDB}),
    ("M25 D3 call disp 10->11",    {0x6917AC: 0x11}, {"D3"},       {0x6917AC: 0x10}),
    ("M26 D5 window head",         {0x691748: 0x90}, {"D5"},       {0x691748: 0x33}),
    ("M27 D7 push SIB 81->01",     {0x691741: 0x01}, {"D7"},       {0x691741: 0x81}),
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
    raise SystemExit("VERIFY-FAIL: 0x%08X unmapped" % va)


vbad = []
for name, mut, exp, cur_exp in CASES:
    for va, want in cur_exp.items():
        got = cur(va)
        if got != want:
            vbad.append("%s: VA 0x%08X cur=%02X want=%02X" % (name, va, got, want))
if vbad:
    print("PRE-RUN BYTE VERIFY FAILED (G-67 gate):")
    for x in vbad:
        print("  " + x)
    sys.exit(2)
print("pre-run byte verify: all offsets' current bytes match expectations\n")

LABELS = ("A1", "A2", "A3", "A4", "A5", "A6", "B1", "B2", "B3", "B4", "B5", "B6",
          "C1", "C2", "C3", "C4", "C5", "C6", "C7",
          "D1", "D2", "D3", "D4", "D5", "D6", "D7", "S1", "S2", "S3")


def run(mut):
    os.environ["R054_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
    buf = io.StringIO()
    rc = None
    try:
        # the gate writes its PASS/FAIL lines to stdout (R-054 style), so capture BOTH
        # streams -- capturing only stderr made every mutation look "unscored" (G-71 cause 3)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
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

# G-79 machine reconciliation (R-059 pattern). COUNTED = the 26 ok() labels
# (A1..A6 B1..B6 C1..C7 D1..D7, AST-enumerated from the gate 2026-10-26);
# G0/S1/S2/S3 are structural and excluded from the denominator.
COUNTED = tuple(["A%d" % i for i in range(1, 7)] + ["B%d" % i for i in range(1, 7)]
                + ["C%d" % i for i in range(1, 8)] + ["D%d" % i for i in range(1, 8)])
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    ok_all = False
else:
    print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))

print("\n== R-054 mutation %d/%d 精确集合击杀 ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
