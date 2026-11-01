# -*- coding: utf-8 -*-
"""R-057 mutation suite -- exact-set scoring (shape = R-047..R-056).

Every offset carries a pre-run "current byte == expect" assertion (G-67).
Kill sets are derived from each assertion's READ FOOTPRINT (G-75: a differential /
set-shaped assertion is inherently cross-window, so list every assertion whose read
range covers the mutated address, not the ones that seem semantically related).

  M1  flip twin A's +0x4 count read           -> A2, A3, A1? (A1 is a footprint SET)
  M2  flip twin A's +0xC sorted flag read     -> A1, A2
  M3  flip twin A's +0xC flag SET              -> A2
  M4  flip twin A's +0x10 cache clear         -> A1, A2
  M5  flip twin A's array-base read           -> A1, A3
  M6  flip twin A's stride                    -> A3
  M7  flip 0x52A4D0's this==ecx               -> B1, S2
  M8  flip 0x52A4D0's array base +0x2C        -> B2, S2, D1
  M9  flip 0x52A4D0's count +0x30             -> B3, S2
  M10 flip 0x52A4D0's sorted flag +0x38       -> B4, D2, S2
  M11 flip 0x52A4D0's cache +0x3C read        -> B5, S2
  M12 flip 0x528A10's `lea esi,[ebp+0x28]`    -> C2, D1, D2, E2, S3
  M13 flip 0x528A10's `mov esi,[ebp+8]`       -> C4
  M14 flip 0x528A10's `add esi,0x2C`          -> C4, C5
  M15 flip ctor zero-init block               -> F1
  M16 flip ctor vptr stamp                    -> F2
  M17 flip ctor sub-object lea                -> F3
  M18 flip the ebp write (C1's single site)   -> C1
"""
import contextlib
import io
import os
import runpy
import struct
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r057_container_ownership" + chr(46) + "py")

CASES = [
    ("M1 twinA +4 count read",    {0x52B4F5: 0x05}, {"A1", "A2"},          {0x52B4F5: 0x04}),
    ("M2 twinA +C flag read",     {0x52B500: 0x0D}, {"A1", "A2"},          {0x52B500: 0x0C}),
    ("M3 twinA +C flag set",      {0x52B521: 0x0D}, {"A1", "A2"},          {0x52B521: 0x0C}),
    ("M4 twinA +10 cache clear",  {0x52B51A: 0x11}, {"A1", "A2"},          {0x52B51A: 0x10}),
    ("M5 twinA array base read",  {0x52B52A: 0x3F}, {"A3"},                {0x52B52A: 0x3E}),
    ("M6 twinA stride",           {0x52B53D: 0x08}, {"A3"},                {0x52B53D: 0xC7}),
    ("M7 52A4D0 this==ecx",       {0x52A4DF: 0xF2}, {"B1"},                {0x52A4DF: 0xF1}),
    ("M8 52A4D0 array base",      {0x52A52C: 0x2D}, {"B2", "D2", "S2"}, {0x52A52C: 0x2C}),
    ("M9 52A4D0 count",           {0x52A547: 0x31}, {"B3", "D2", "S2"}, {0x52A547: 0x30}),
    ("M10 52A4D0 sorted flag",    {0x52A527: 0x39}, {"B4", "S2"},       {0x52A527: 0x38}),
    ("M11 52A4D0 cache read",     {0x52A51C: 0x3D}, {"B5", "D2", "S2"}, {0x52A51C: 0x3C}),
    ("M12 528A10 container B",    {0x528B18: 0x29}, {"C2", "D3"},          {0x528B18: 0x28}),
    ("M13 528A10 arg load",       {0x528A57: 0x09}, {"C4"},                {0x528A57: 0x08}),
    ("M14 528A10 rebase",         {0x528A88: 0x2D}, {"C4"},                {0x528A88: 0x2C}),
    ("M15 ctor zero-init block",  {0x52CC23: 0x29}, {"F1"},                {0x52CC23: 0x28}),
    ("M16 ctor vptr stamp",       {0x52CC38: 0xF5}, {"F2"},                {0x52CC38: 0xF4}),
    ("M17 ctor sub-object lea",   {0x52CC0D: 0x0D}, {"F3"},                {0x52CC0D: 0x0C}),
    ("M18 ebp write site",        {0x528A1F: 0xEA}, {"C1"},                {0x528A1F: 0xE9}),
    # ---- displacements done at ALL sites of a field, so the SET-shaped assertions
    # ---- (A1/A3/S2) and the interleave assertions (D1/D2) become reachable.
    #      A single-site mutation cannot move a set member: G-75 cause 1.
    ("M19 twinA +4 at BOTH sites", {0x52B4F5: 0x05, 0x52B52F: 0x05},
     {"A1", "A2", "A3"}, {0x52B4F5: 0x04, 0x52B52F: 0x04}),
    ("M20 twinA +C at BOTH sites", {0x52B500: 0x0D, 0x52B521: 0x0D},
     {"A1", "A2"}, {0x52B500: 0x0C, 0x52B521: 0x0C}),
    ("M21 twinA +0 -> disp8 form", {0x52B52A: 0x46},
     {"A3"}, {0x52B52A: 0x3E}),
    ("M22 52A4D0 +2C all 4 sites",
     {0x52A52C: 0x2D, 0x52A54F: 0x2D, 0x52A57E: 0x2D, 0x52A59C: 0x2D},
     {"B2", "D2", "S2"}, {0x52A52C: 0x2C, 0x52A54F: 0x2C, 0x52A57E: 0x2C, 0x52A59C: 0x2C}),
    ("M23 52A4D0 +38 all 4 sites",
     {0x52A527: 0x39, 0x52A543: 0x39, 0x52A579: 0x39, 0x52A595: 0x39},
     {"B4", "S2"}, {0x52A527: 0x38, 0x52A543: 0x38, 0x52A579: 0x38, 0x52A595: 0x38}),
    # ---- whole-function retarget: if 0x52A4D0 suddenly HAS a caller, E1/E2/E3 must die.
    ("M24 give 52A4D0 a caller",  {0x528AA8: 0x24, 0x528AA9: 0x1A}, {"E1", "E2"},
     {0x528AA8: 0x44, 0x528AA9: 0x2A}),
    # ---- aimed at D1: the LIVE caller 0x52772C that proves the +0x2C embedding
    ("M25 live caller count read", {0x52772E: 0x31}, {"D1"},          {0x52772E: 0x30}),
    ("M26 live caller rebase",     {0x527731: 0x2D}, {"D1", "D2", "D3"},  {0x527731: 0x2C}),
    ("M27 live caller ecx set",    {0x52774E: 0xCF}, {"D1"},          {0x52774E: 0xCE}),
    # ---- R-059 G-79 reconciliation: C3 / C5 had ZERO killers in M1..M27 (suite
    #      reported 27/27 -- N = cases, not assertions).  D2's first draft was pure
    #      literal arithmetic (`0x2C+0x4==0x30`) -- byte-wise UNKILLABLE (G-77);
    #      the gate now FOLDS FROM BYTES (rebase imm8, twin cache disp, A4D0's three
    #      host disps), so D2 has five byte-killers.  Red-sets measured empirically.
    ("M28 C3 count disp",          {0x528B21: 0x05}, {"C3"},          {0x528B21: 0x04}),
    ("M29 C5 count disp",          {0x528A85: 0x31}, {"C5"},          {0x528A85: 0x30}),
    ("M30 D2 twin cache disp",     {0x527740: 0x11}, {"D2"},          {0x527740: 0x10}),
    ("M31 D2 A4D0 base disp",      {0x52A52C: 0x2D}, {"B2", "D2", "S2"}, {0x52A52C: 0x2C}),
    ("M32 D2 A4D0 cache disp",     {0x52A51C: 0x3D}, {"B5", "D2", "S2"}, {0x52A51C: 0x3C}),
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

LABELS = ("A1", "A2", "A3",
          "B1", "B2", "B3", "B4", "B5",
          "C1", "C2", "C3", "C4", "C5",
          "D1", "D2", "D3",
          "E1", "E2",
          "F1", "F2", "F3",
          "S1", "S2", "S3")


def run(mut):
    os.environ["R057_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
    buf = io.StringIO()
    rc = None
    try:
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
    print("%-26s expect=%-22s killed=%-22s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False

# G-79 (R-059): every COUNTED assertion needs >=1 killer -- the suite fraction is
# over CASES and hides zero-killer assertions inside an all-green run.
COUNTED = ("A1", "A2", "A3",
           "B1", "B2", "B3", "B4", "B5",
           "C1", "C2", "C3", "C4", "C5",
           "D1", "D2", "D3",
           "E1", "E2",
           "F1", "F2", "F3")
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    ok_all = False
else:
    print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))

print("\n== R-057 mutation %d/%d 精确集合击杀 ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
