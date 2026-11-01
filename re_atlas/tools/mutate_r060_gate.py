# -*- coding: utf-8 -*-
"""R-060 mutation suite -- exact-set scoring over the corrected R-035 gate.

Replaces the R-035-era mutate_r035_gate.py (kept on disk, superseded; see LEDGER
R-060 honest ledger -- that file's M4 LABEL misdescribed its own mechanism: it
says "pure count and prefix set shrink", but flipping 0x81C6DD 't'->'_' leaves
the string PURE/PREFIX-matching and instead ADDS a methods value (21->22), which
is what actually reddened P8.  The test was alive; the narrative was wrong
(G-77 family).  C4 here targets the real ':' at 0x81C6E6 -- pure 5->4, pref
30->29 -- the mechanism the old label claimed.)

Expect-sets are MEASURED on this gate (out/_r060_mut_calib.txt round 1, then
round-2 verify) -- never hand-derived (round rule ① / G-71 cause 1).

The D-06 acceptance core: the discriminating pair C11/C12, each reddening the
*pure* assertion of only one reading:
  C11 displace CLEAN phantom 0x4077DE (its 5-byte window lies entirely inside
      the 10-byte `mov dword [0x87e820],0` at 0x4077DB, so the aligned call
      stream is untouched): P2/P3 (byte-scan quantities) RED and ***P2c -- the
      aligned-ONLY assertion -- stays GREEN*** (P2b/R2 also redden, each has a
      byte-scan-side conjunct).  A byte-scan-only defect is invisible to the
      aligned reading: exactly V-001 §七.5's distinguishability.
  C12 promote phantom 0x4011DB (8B->90 makes the E8 an aligned boundary):
      the aligned set GROWS -- P2c/P2b/P3b/R1/R2/R5 RED while ***P2/P3 (byte-
      scan) stay GREEN*** (the scan already counted this E8).  Same pair,
      reverse direction: neither reading can mask a defect in the other.
This is D-06 判据① 「560 幻影复现为 0」 in killable form.

G-79 tail-check: every counted tag needs >=1 killer (C14 added because P7 was
zero-killer after round 1: it measures the NAMED intersection, so the killer is
a unique real call INTO a named entry: call 0x406B1A -> 0x409360).
"""
import contextlib
import io
import os
import runpy
import struct
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "verify_r035_claims" + chr(46) + "py")


def T(*pairs):
    return {pairs[i]: pairs[i + 1] for i in range(0, len(pairs), 2)}

CASES = [
    ("C1 sole E8 destroyed",       T(0x0040A755, 0x90),
     {"P2", "P2b", "P2c", "P3", "P3b", "P4", "R1", "R5"}),
    ("C2 anchor prologue broken",  T(0x00403A80, 0x00),
     {"P5", "R3", "R4", "R5"}),
    ("C3 both E9 referrers",       T(0x00404457, 0x90, 0x0040446F, 0x90),
     {"P2", "P4", "P6", "R1", "R2", "N2", "N4"}),
    ("C4 pure-name colon",         T(0x0081C6E6, 0x5F), {"P8", "P9"}),
    ("C5 name-push opcode",        T(0x00652CF3, 0x90), {"P4", "P9", "R1", "R2"}),
    ("C6 FILE callee destroyed",   T(0x0041099B, 0x90), {"P4", "P10", "R1"}),
    ("C7 INI reader call",         T(0x00410AA0, 0x90), {"P4", "P11", "R1"}),
    ("C8 N1 host orphaned",
     T(0x00403ACD, 0x90, 0x00403AFF, 0x90),
     {"P2", "P2b", "P2c", "P3", "P3b", "P4", "P5", "R1", "R3", "R4", "R5", "N1"}),
    ("C9 N3 pointer planted",
     T(0x0081B21A, 0x80, 0x0081B21B, 0x3A, 0x0081B21C, 0x40, 0x0081B21D, 0x00),
     {"N3"}),
    ("C10 N4 E9->E8 promote",      T(0x00404457, 0xE8),
     {"P2", "P2b", "P2c", "P3", "P3b", "P4", "P6", "R1", "R5", "N2", "N4"}),
    ("C11 clean phantom displace",
     T(0x004077DF, 0xFF, 0x004077E0, 0xFF, 0x004077E1, 0xFF, 0x004077E2, 0x7F),
     {"P2", "P2b", "P3", "P4", "R2"}),
    #  ^ MEASURED (round 1): byte-scan side reddens -- P2 (7,279->7,278), P3,
    #    P2b (phantom_sites 563->562 conjunct), R2 (lost_roots 560->559 conjunct),
    #    P4 (covered drops).  *** P2c/P3b/R1/R5 stay GREEN: the aligned reading is
    #    BLIND to this byte-scan-only defect -- V-001 §七.5's required
    #    distinguishability, and D-06 判据① in killable form. ***
    ("C12 phantom promote",        T(0x004011DA, 0x90),
     {"P2b", "P2c", "P3b", "P4", "R1", "R2", "R5"}),
    #  ^ REVERSE direction: making the phantom byte an aligned boundary GROWS the
    #    aligned set (P2b/P2c/P3b/R1/R2/R5 red) while P2/P3 (byte-scan) stay
    #    GREEN -- the byte scan counted this E8 all along.
    ("C13 head-0x40A090 prologue",  T(0x0040A090, 0x00),
     {"P4", "R3", "R4", "R5", "R6"}),
    ("C14 named-unique call cut",   T(0x00406B1B, 0xFF, 0x00406B1C, 0xFF,
                                      0x00406B1D, 0xFF, 0x00406B1E, 0x7F),
     {"P2", "P2b", "P2c", "P3", "P3b", "P4", "P5", "P7", "R1", "R3", "R4", "R5"}),
    #  ^ the P7 killer (G-79 round-1 coverage check flagged P7 zero-killer).
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


CUR_EXPECT = T(
    0x0040A755, 0xE8,
    0x00403A80, 0x81,
    0x00404457, 0xE9, 0x0040446F, 0xE9,
    0x0081C6E6, 0x3A,
    0x00652CF3, 0x68,
    0x0041099B, 0xE8,
    0x00410AA0, 0xE8,
    0x00403ACD, 0xE8, 0x00403AFF, 0xE8,
    0x0081B21A, 0x00, 0x0081B21B, 0x00, 0x0081B21C, 0x00, 0x0081B21D, 0x00,
    0x004077DF, 0x87, 0x004077E0, 0x00, 0x004077E1, 0x00, 0x004077E2, 0x00,
    0x004011DA, 0x8B,
    0x0040A090, 0x81,
    0x00406B1B, 0x41, 0x00406B1C, 0x28, 0x00406B1D, 0x00, 0x00406B1E, 0x00,
)
vbad = ["0x%08X cur=%02X want=%02X" % (va, cur(va), want)
        for va, want in CUR_EXPECT.items() if cur(va) != want]
if vbad:
    print("PRE-RUN BYTE VERIFY FAILED (G-67):")
    for x in vbad:
        print("  " + x)
    sys.exit(2)
print("pre-run byte verify: all mutation sites' current bytes match\n")

TAGS = ("P2", "P2b", "P2c", "P3", "P3b", "P4", "P5", "P6", "P7",
        "P8", "P9", "P10", "P11", "N1", "N2", "N3", "N4",
        "R1", "R2", "R3", "R4", "R5", "R6")


def run(mut):
    os.environ["R035_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
    buf = io.StringIO()
    rc = None
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            runpy.run_path(GATE, run_name="__main__")
        rc = 0
    except SystemExit as ex:
        rc = ex.code
    finally:
        os.environ.pop("R035_MUTATE", None)
    killed = set()
    for line in buf.getvalue().splitlines():
        if line.startswith("FAIL\t"):
            tag = line.split("\t")[1]
            if tag in TAGS:
                killed.add(tag)
    return rc, killed


rc0, base = run({})
print("baseline rc=%s failed=%s" % (rc0, sorted(base)))
if rc0 != 0 or base:
    print("BASELINE NOT GREEN -- abort")
    sys.exit(2)

ok_all = True
n_ok = 0
killed_union = set()
for name, mut, expect in CASES:
    rc, killed = run(mut)
    killed_union |= killed
    score_ok = (killed == expect) and (rc != 0)
    n_ok += 1 if score_ok else 0
    print("%-26s expect=%s killed=%s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False

uncovered = [x for x in TAGS if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted tags with ZERO killer: %s" % uncovered)
    ok_all = False
else:
    print("\nG-79 coverage: all %d counted tags have >=1 killer" % len(TAGS))

print("\n== R-060 mutation %d/%d 精确集合击杀 ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
