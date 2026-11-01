# -*- coding: utf-8 -*-
"""R-056 mutation suite -- exact-set scoring (shape = R-047..R-055).

Every offset carries a pre-run "current byte == expect" mechanical assertion (G-67).
Kill lists derived from window membership, NOT from a guess.

  M1  flips the twin's nop fence byte at 0x52B567        -> A1
  M2  flips the comparator immediate at 0x52B506        -> A3, A4(no: A4 reads the body)
  M3  flips the miss-path `xor eax,eax` opcode          -> A6
  M4  flips the comparator body byte                     -> A4, S3
  M5  flips the 0x7C8B48 call disp in the 2nd twin       -> A5
  M6  flips the kernel head byte                         -> B1
  M7  flips the kernel hit tail `mov eax,edx`            -> B2
  M8  flips the inlined-loop core byte (1st twin)        -> B5
  M9  flips the inlined-loop core byte (2nd twin)        -> B5
  M10 flips the teardown block byte at 0x52ABC8          -> C1
  M11 flips the host's vptr stamp                        -> C2
  M12 flips the virtual-delete arg push                  -> C3
  M13 flips the second facet vptr stamp                  -> C4
  M14 flips the host head byte                           -> C5
"""
import contextlib
import io
import os
import runpy
import struct
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r056_ini_lookup_family" + chr(46) + "py")

CASES = [
    ("M1 twin nop fence",        {0x52B569: 0x91}, {"A1"},        {0x52B569: 0x90}),
    ("M2 comparator imm",        {0x52B506: 0xA1}, {"A3"},        {0x52B506: 0xA0}),
    ("M3 miss xor eax,eax",      {0x52B55B: 0x34}, {"A2", "A6"},  {0x52B55B: 0x33}),
    ("M4 comparator body",       {0x52B721: 0x45}, {"A4", "S3"},  {0x52B721: 0x44}),
    ("M5 2nd twin worker call",  {0x52B641: 0x04}, {"A5"},        {0x52B641: 0x03}),
    ("M6 kernel head",           {0x52B6D1: 0x57}, {"B1"},        {0x52B6D1: 0x56}),
    ("M7 kernel hit tail",       {0x52B70E: 0x8D}, {"B2"},        {0x52B70E: 0x8B}),
    ("M8 1st inlined loop",      {0x52B536: 0x9A}, {"A2", "B5"},  {0x52B536: 0x99}),
    ("M9 2nd inlined loop",      {0x52B666: 0x9A}, {"A2", "B5"},  {0x52B666: 0x99}),
    ("M10 teardown block",       {0x52ABC6: 0x31}, {"C1"},        {0x52ABC6: 0x30}),
    ("M11 host vptr stamp",      {0x52AB89: 0x3D}, {"C2"},        {0x52AB89: 0x3C}),
    ("M12 virtual-delete arg",   {0x52ABB3: 0x02}, {"C3"},        {0x52ABB3: 0x01}),
    ("M13 facet vptr stamp",     {0x52AC1D: 0x05}, {"C4"},        {0x52AC1D: 0x04}),
    ("M14 host head",            {0x52AB81: 0x57}, {"C5"},        {0x52AB81: 0x56}),
    ("M15 non-host head",        {0x52AAC1: 0xCA}, {"C5b"},       {0x52AAC1: 0xC9}),
    ("M16 a caller retargets",   {0x528B39: 0xE4}, {"B6"},        {0x528B39: 0xE3}),
    # ---- R-059 G-79 reconciliation: M1..M16 left B3 / B4 / C6 with ZERO killers
    #      while the suite still reported 16/16 (the N is the CASE count, not the
    #      assertion count -- G-79).  Red-sets below are EMPIRICAL, measured against
    #      the gate after the R-059 rewrites (out/_probe_r059_remeasure.py).
    #      M17/M18 pack the full rel32 by ARITHMETIC, never hand bytes.
    ("M17 kernel caller retargets",
     dict((0x526BB3 + i, b) for i, b in enumerate(struct.pack("<i", 0x52B620 - 0x526BB7))),
     {"B3", "B6"}, {0x526BB3: 0x19, 0x526BB4: 0x4B, 0x526BB5: 0x00, 0x526BB6: 0x00}),
    ("M18 twinA worker->kernel",
     dict((0x52B511 + i, b) for i, b in enumerate(struct.pack("<i", 0x52B6D0 - 0x52B515))),
     {"A2", "A5", "B3", "B4"}, {0x52B511: 0x33, 0x52B512: 0xD6, 0x52B513: 0x29, 0x52B514: 0x00}),
    ("M19 C6 release-loop disp", {0x52ABDD: 0x41}, {"C6"},        {0x52ABDD: 0x40}),
    ("M20 C6 back-edge jne",     {0x52ABFC: 0xEB}, {"C6"},        {0x52ABFC: 0x75}),
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

LABELS = ("A1", "A2", "A3", "A4", "A5", "A6",
          "B1", "B2", "B3", "B4", "B5", "B6",
          "C1", "C2", "C3", "C4", "C5", "C5b", "C6",
          "S1", "S2", "S3")


def run(mut):
    os.environ["R056_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
    buf = io.StringIO()
    rc = None
    try:
        # capture BOTH streams (G-71 cause 3: this gate prints to stdout)
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
    print("%-26s expect=%-14s killed=%-14s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False

# G-79 (R-059): every COUNTED assertion needs >=1 killer; the suite's N/N fraction is
# over CASES and hides zero-killer assertions inside an all-green run.
COUNTED = ("A1", "A2", "A3", "A4", "A5", "A6",
           "B1", "B2", "B3", "B4", "B5", "B6",
           "C1", "C2", "C3", "C4", "C5", "C5b", "C6")
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    ok_all = False
else:
    print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))

print("\n== R-056 mutation %d/%d 精确集合击杀 ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
