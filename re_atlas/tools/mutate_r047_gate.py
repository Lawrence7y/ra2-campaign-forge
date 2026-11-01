# -*- coding: utf-8 -*-
"""R-047 mutation suite (tools/r047_l20_triggersave" + py).
Measured-first (G-65): every byte offset re-derived THIS run from the authoritative
window dump --
  field disp byte VA = operand VA + 2 (enc 8b/8a <modrm> <disp>);
  call rel32 first byte = call VA + 1;
  base-call opcode byte = 0x726799.
FIRST-DRAFT FAILURE (recorded honestly in evidence §3): field disp offsets came from the
phantom-dump listing (double-cursor helper) -- M3's 0x726837 lay OUTSIDE the 0x86-byte
window (no-op => rc=0), and disp byte sits at +2 not +1. M4 is DISCRIMINATING: 24->54
breaks T2 (window) AND T3 (54 appears, 24 vanishes) but leaves T4 (call set) intact --
proving T3's zero is real. S1 reads RTTI JSON (unmutatable) -> excluded, stated.
"""
import io, os, runpy, contextlib, sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r047_l20_triggersave" + chr(46) + "py")

CASES = [
    ("M1 base-call opcode E8->90 (win+callset)", {0x726799: 0x90}, {"T2", "T4"}),
    ("M2 field24 disp 24->25 (win+census)",      {0x7267A0: 0x25}, {"T2", "T3"}),
    ("M3 field34 disp 34->35 (win+census)",      {0x7267E3: 0x35}, {"T2", "T3"}),
    ("M4 field24 disp 24->54 (win+census)",      {0x7267A0: 0x54}, {"T2", "T3"}),
    ("M5 writer-call rel low (win+callset)",     {0x7267AE: 0x00}, {"T2", "T4"}),
    ("M6 WhatAmI imm 26->27",                    {0x726941: 0x27}, {"T1"}),
    ("M7 namepair26 id byte",                    {0x816EE0 + 0x26 * 8 + 4: 0x27}, {"T1"}),
    ("M8 vtable slot13 low byte",                {0x7F5858 + 0x34: 0x91}, {"T1"}),
    ("M9 handler E8 entry site head (T5)",       {0x726540: 0x90}, {"T5"}),
    ("M10 Save tail ret opcode (win only)",      {0x726814: 0xC3}, {"T2"}),
    ("M11 writer 0x4A1D50 head (callset)",       {0x4A1D50: 0x90}, {"T4"}),
    ("M12 namepair26 ptr word0 (T1)",            {0x816EE0 + 0x26 * 8: 0x00}, {"T1"}),
]

def run(mut):
    os.environ["R047_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and parts[0].startswith("T") and len(parts) > 1 and parts[1] == "FAIL:":
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
    print("%-46s expect=%s killed=%s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False
print("\n== R-047 mutation %d/%d killed (exact-set; S1=RTTI-JSON 不可杀，如实不列) ==" % (n_ok, len(CASES)))
# G-79 machine reconciliation (R-059 pattern; R-061 aux batch 2): counted
# assertions T1..T5 must each have >=1 killer in the measured union; S1 is
# structural (reads RTTI JSON, not binary bytes) and excluded from denominator.
COUNTED = tuple("T%d" % i for i in range(1, 6))
uncovered = [x for x in COUNTED if x not in killed_union]
if uncovered:
    print("\nG-79 COVERAGE RED: counted assertions with ZERO killer: %s" % uncovered)
    sys.exit(1)
print("\nG-79 coverage: all %d counted assertions have >=1 killer" % len(COUNTED))
sys.exit(0 if ok_all else 1)
