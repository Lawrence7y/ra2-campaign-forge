# -*- coding: utf-8 -*-
"""R-048 mutation suite -- exact-set scoring (harness shape = R-047).

Offsets re-derived THIS run against the FULL authoritative windows (byte arithmetic
restated from real dumps; 89 46 2c = opcode@store, modrm@+1, disp@+2):
  M2 harvest store 89 46 2c @0x726561 -> disp byte @0x726563.
  M3 ctor 88 5e 30 @0x725FB8 -> disp @0x725FBA.
  M8 first getter call e8 @0x726551 -> rel b0 @0x726552 (DA).
  M10 detach 2nd zero-store c7 41 2c @0x7266B4 -> disp @0x7266B6.
  M13 event ctor 89 5e 54 @0x71E6BE (R-042 census address) -> disp @0x71E6C0.

Shared-byte kill lists (G-65 rule: enumerate exhaustively):
  M6 (handler-call rel b0) breaks V6 AND V7 -- V7's positive control reads the SAME
     e8 byte at 0x726540 for the handler-entry census.
  M11/M12 (vtable slot bytes) break V10 only; S1 reads RTTI JSON -- binary mutations
     cannot kill it; excluded, stated honestly.

Each case flips one byte; expected set = algebraic consequence of which assertion
reads which byte (window equality / rel32 recomputation / decoded disp-set / census).
"""
import io, os, runpy, contextlib, sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r048_triggerclass_host" + chr(46) + "py")

CASES = [
    ("M1 guard+44 disp 44->45",              {0x7264C6: 0x45}, {"V1", "V2"}),
    ("M2 harvest+2C store disp 2C->2D",      {0x726563: 0x2D}, {"V2", "V4"}),
    ("M3 ctor +30 init disp 30->31",         {0x725FBA: 0x31}, {"V3"}),
    ("M4 ctor vptr imm b1 58->59",           {0x725FD1: 0x59}, {"V3"}),
    ("M5 getter +54 disp 54->55",            {0x71FA32: 0x55}, {"V5"}),
    ("M6 handler-call rel b0 FB->FC",        {0x726541: 0xFC}, {"V6", "V7"}),
    ("M7 finder-call rel b0 F8->FC",         {0x726534: 0xFC}, {"V6"}),
    ("M8 getter#1 rel b0 DA->DB",            {0x726552: 0xDB}, {"V4"}),
    ("M9 call-site E8->nop",                 {0x6E5414: 0x90}, {"V7"}),
    ("M10 detach +2C store disp 2C->2D",     {0x7266B6: 0x2D}, {"V8"}),
    ("M11 vtable slot10 low 90->91",         {0x7F5880: 0x91}, {"V10"}),
    ("M12 vtable slot13 low 90->91",         {0x7F588C: 0x91}, {"V10"}),
    ("M13 event ctor +54 store disp 54->53", {0x71E6C0: 0x53}, {"V9"}),
]

def run(mut):
    os.environ["R048_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and parts[0].startswith(("V", "S")) and len(parts) > 1 and parts[1] == "FAIL:":
            killed.add(parts[0])
    return rc, killed

ok_all = True
n_ok = 0
killed_union = set()
for name, mut, expect in CASES:
    rc, killed = run(mut)
    killed_union |= killed
    score_ok = (killed == expect) and (rc != 0)
    n_ok += 1 if score_ok else 0
    print("%-36s expect=%s killed=%s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False

print(f"\n== R-048 mutation {n_ok}/{len(CASES)} 精确集合击杀 ==")
# G-79 machine reconciliation (R-059 pattern; R-061 aux batch 2): counted
# assertions V1..V10 must each have >=1 killer; V0=fingerprint, S1=RTTI JSON
# (structurally unmutatable by binary flips) -- both excluded from denominator.
COUNTED = tuple("V%d" % i for i in range(1, 11))
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    sys.exit(1)
print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))
sys.exit(0 if ok_all and n_ok == len(CASES) else 1)
