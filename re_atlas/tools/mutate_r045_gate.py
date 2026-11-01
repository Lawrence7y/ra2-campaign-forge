# -*- coding: utf-8 -*-
"""R-045 mutation suite for the +0xA0 count-lifecycle gate (tools/r045_count_lifecycle" + py).
Measured-first: kill-sets follow WINDOW COVERAGE (shared bytes kill every assertion whose
window/census covers them -- expectations list them all; exact-set scoring).
In-process runpy (no subprocess).
"""
import io, os, runpy, contextlib, sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r045_count_lifecycle" + chr(46) + "py")

CASES = [
    # site bytes: store opcode/disp shared with Z6 census; imm-only bytes hit just the window.
    ("C1 Z1 store opcode c7->90 (win+census)",   {0x6916C7: 0x90}, {"Z1", "Z6"}),
    ("C2 Z1 imm0 lowbyte 00->01 (win only)",    {0x6916CD: 0x01}, {"Z1"}),
    ("C3 Z1 vptr-imm 10->11 (win only)",        {0x6916D2: 0x11}, {"Z1"}),
    ("C4 Z2 store disp a0->a1 (win+census)",    {0x691C90: 0xA1}, {"Z2", "Z6"}),
    ("C5 Z3 store opcode 89->90 (win+census)",  {0x691A5B: 0x90}, {"Z3", "Z6"}),
    ("C6 Z4 store disp a0->a1 (win+census)",    {0x6918D2: 0xA1}, {"Z4", "Z6"}),
    ("C7 Z5 load disp a0->a1 (win+census)",     {0x69154C: 0xA1}, {"Z5", "Z6"}),
    ("C8 Z7 inc byte 40->90 (shared Z7+Z8)",     {0x691946: 0x90}, {"Z7", "Z8"}),
    ("C9 Z7 store disp a0->a1 (Z7+Z8+Z6)",       {0x691949: 0xA1}, {"Z7", "Z6", "Z8"}),
    ("C10 census-only byte at 0x69191F disp",   {0x691924: 0xA1}, {"Z6"}),
    # added post-Z4-flip: xor-edi-edi head breaks Z4 window ONLY (census keys on the store)
    ("C11 Z4 xor-pair head 33->90 (win only)",  {0x6918CA: 0x90}, {"Z4"}),
    # element-store SIB disp a4: NOT in +0xA0 census by design -- Z8-only kill
    ("C12 Z8 element-store disp a4->b4 (win only)", {0x691934: 0xB4}, {"Z8"}),
    ("C13 Z8 inc-chain disp a0->a1 (Z8+Z7+Z6)", {0x691942: 0xA1}, {"Z7", "Z8", "Z6"}),
]

def run(mut):
    os.environ["R045_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and parts[0].startswith("Z") and len(parts) > 1 and parts[1] == "FAIL:":
            killed.add(parts[0])
    return rc, killed

ok_all = True
n_ok = 0
for name, mut, expect in CASES:
    rc, killed = run(mut)
    score_ok = (killed == expect) and (rc != 0)
    n_ok += 1 if score_ok else 0
    print("%-44s expect=%s killed=%s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False
print("\n== R-045 mutation %d/%d killed (exact-set) ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all else 1)
