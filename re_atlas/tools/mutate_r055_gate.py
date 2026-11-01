# -*- coding: utf-8 -*-
"""R-055 mutation suite -- exact-set scoring (shape = R-047..R-054).

Every offset carries a pre-run "current byte == expect" mechanical assertion (G-67).
Kill lists derived from window membership, NOT from a guess.

  M1  flips the 0x52B4F0 call disp low byte at 0x528AA8    -> L26-1, L26-2
  M2  flips the 0x52B390 call disp low byte at 0x528B50    -> L26-1
  M3  flips 0x52B561's `mov eax,edx` (entry-ptr return)    -> L26-3
  M4  flips 0x52B390's `mov al,1` (bool return)            -> L26-4
  M5  flips 0x52B430's `je` target byte                    -> L26-5, L26-6
  M6  flips the shared cmp-fn push imm at 0x52B3C1         -> L26-7
  M7  flips the `mov eax,[esi+0x3C]` disp at 0x52A51B      -> L24-1, L24-5(no)
  M8  flips the cache-hit `cmp [eax],edi` at 0x52A521      -> L24-2
  M9  flips the cache-clear `mov [esi+0x3C],ebx` at 0x52A53F -> L24-3, L24-4
  M10 flips +0x10 cache clear disp at 0x52B3D5             -> L24-5
  M11 flips the ctor zero-init at 0x52CC31                 -> L24-6
  M12 flips one vptr-install global byte (0x887058 -> ...59) -> I3-1
  M13 flips 0x887058's own stamp site byte                 -> I3-1, I3-4
  M14 flips the S1 prologue byte of 0x52B4F0               -> S1 only (structural)
  M18 flips 0x52B390's head `push ebx` (L26-6 stream)      -> L26-6, S1 (G-79 round R-061)
  M19 flips one 0x52B4F0 caller's rel32 (L26-8 census)     -> L26-8 (G-79 round R-061)
  M20 flips an out-of-band 0x89F518 ref byte (I3-2 count)  -> I3-2 (G-79 round R-061)
  M21 flips a band 0x89F518 ref byte (I3-2 and I3-3)       -> I3-2, I3-3 (G-79 round R-061)

G-79 (R-061): the old `>=`/`<` thresholds on L26-6/L26-8/I3-2/I3-3 made every
single-byte flip invisible to those census labels -- zero killers in a suite
that printed 16/16 green. Converted to exact pins; red-sets re-measured.
"""
import contextlib
import io
import os
import runpy
import struct
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r055_ini_residuals" + chr(46) + "py")

CASES = [
    ("M1 call 52B4F0 disp",      {0x528AA8: 0x45}, {"L26-2", "L26-8"}, {0x528AA8: 0x44}),
    ("M2 call 52B390 disp",      {0x528B50: 0x3D}, {"L26-1", "L26-8"}, {0x528B50: 0x3C}),
    ("M3 entry-ptr return",      {0x52B564: 0xC3}, {"L26-3"},          {0x52B564: 0xC2}),
    ("M4 bool return mov al,1",  {0x52B3B4: 0x02}, {"L26-4"},          {0x52B3B4: 0x01}),
    ("M5 52B430 je target",      {0x52B44F: 0x69}, {"L26-5"},          {0x52B44F: 0x68}),
    ("M5b 52B430 sentinel imm",  {0x52B4A9: 0x2D}, {"L26-5b"},         {0x52B4A9: 0x2C}),
    ("M5c 52B4D0 bool return",   {0x52B4E2: 0x02}, {"L26-5c"},         {0x52B4E2: 0x01}),
    ("M6 cmp-fn push imm",       {0x52B3C2: 0xB8}, {"L26-7"},          {0x52B3C2: 0xB7}),
    ("M7 +0x3C load disp",       {0x52A51C: 0x3D}, {"L24-1"},          {0x52A51C: 0x3C}),
    ("M8 cache-hit cmp",         {0x52A522: 0x39}, {"L24-1", "L24-2"}, {0x52A522: 0x38}),
    ("M9 cache-clear disp",      {0x52A540: 0x3D}, {"L24-3", "L24-4"}, {0x52A540: 0x3C}),
    ("M10 +0x10 clear disp",     {0x52B3D5: 0x11}, {"L24-5"},          {0x52B3D5: 0x10}),
    ("M11 ctor zero-init disp",  {0x52CC32: 0x3D}, {"L24-6"},          {0x52CC32: 0x3C}),
    ("M12 vptr install global",  {0x40E243: 0x59}, {"I3-1", "I3-2", "I3-4"}, {0x40E243: 0x58}),
    ("M13 887058 stamp site",    {0x40E241: 0xC6}, {"I3-1", "I3-4"},   {0x40E241: 0xC7}),
    ("M14 52B4F0 prologue",      {0x52B4F1: 0x8C}, {"S1"},             {0x52B4F1: 0x8B}),
    # R-061 G-79 round: L26-6/L26-8/I3-2/I3-3 had ZERO killers (the old
    # thresholds `>=6`/`>=20`/`<10`/`>=18` masked every single-byte flip -- the
    # G-80 census twin at the gate layer). Red-sets measured 2026-10-26 against
    # the exact-pin gate; M1/M2/M12/M13 expectations updated for the cross-kills
    # the new exact counts introduced.
    ("M18 L26-6 head 53->5B",    {0x52B390: 0x5B}, {"L26-6", "S1"},    {0x52B390: 0x53}),
    ("M19 L26-8 4F0 caller rel", {0x527751: 0x9C}, {"L26-8"},          {0x527751: 0x9B}),
    ("M20 I3-2 outband ref",     {0x553344: 0xF4}, {"I3-2"},           {0x553344: 0xF5}),
    ("M21 I3-3 band ref",        {0x5C15AE: 0xF4}, {"I3-2", "I3-3"},   {0x5C15AE: 0x18}),
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

LABELS = ("L26-1", "L26-2", "L26-3", "L26-4", "L26-5", "L26-5b", "L26-5c", "L26-6", "L26-7", "L26-8",
          "L24-1", "L24-2", "L24-3", "L24-4", "L24-5", "L24-6",
          "I3-1", "I3-2", "I3-3", "I3-4", "S1", "S2", "S3")


def run(mut):
    os.environ["R055_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
    buf = io.StringIO()
    rc = None
    try:
        # capture BOTH streams: this gate prints PASS/FAIL to stdout (G-71 cause 3)
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
    print("%-28s expect=%-18s killed=%-18s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False

# G-79 machine reconciliation (R-059 pattern): the 20 counted ok() labels must
# each have >=1 killer; G0/S1/S2/S3 are structural (excluded from denominator).
COUNTED = ("L26-1", "L26-2", "L26-3", "L26-4", "L26-5", "L26-5b", "L26-5c",
           "L26-6", "L26-7", "L26-8",
           "L24-1", "L24-2", "L24-3", "L24-4", "L24-5", "L24-6",
           "I3-1", "I3-2", "I3-3", "I3-4")
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    ok_all = False
else:
    print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))

print("\n== R-055 mutation %d/%d 精确集合击杀 ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
