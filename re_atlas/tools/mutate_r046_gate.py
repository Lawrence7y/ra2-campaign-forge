# -*- coding: utf-8 -*-
"""R-046 mutation suite (tools/r046_ctor_vs_factory" + py).
Measured-first + shared-byte exact-set: a mutation kills EVERY assertion whose window
or census pattern covers it (expectations list them all). S1 is RTTI-JSON sourced
(not the mutated blob) => NOT killable by byte mutation -- registered honestly,
like R-044 X10 (structural checks go red only if the census artifact changes).
"""
import io, os, runpy, contextlib, sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r046_ctor_vs_factory" + chr(46) + "py")

CASES = [
    ("M1 ctor head opcode 8b->90",              {0x6916B0: 0x90}, {"C1"}),
    ("M2 ctor rel32 byte (target move)",        {0x6916B9: 0x00}, {"C1"}),
    ("M3 factory head 56->90",                  {0x691C00: 0x90}, {"C2"}),
    ("M4 guard call rel32 (C2/C7 shared)",      {0x691C0D: 0x00}, {"C2", "C7"}),
    ("M5 name-scan window tail d3->d4",         {0x691C49: 0xD4}, {"C2"}),
    ("M6 alloc size imm 0x234->0x235 (C2 only)",{0x691C63: 0x35}, {"C2"}),
    # TRI double-store site1 disp: window C3 + census pattern C6
    ("M7 site1 2nd-zero disp a0->a1",           {0x6916CB: 0xA1}, {"C3", "C6"}),
    ("M8 site2 2nd-zero disp a0->a1",           {0x691C8D: 0xA1}, {"C3", "C6"}),
    ("M9 site1 idx write 98->99",               {0x691765: 0x99}, {"C4", "C6"}),
    ("M10 site2 idx write 98->99",              {0x691D28: 0x99}, {"C4", "C6"}),
    ("M11 dtor head 51->90",                    {0x691770: 0x90}, {"C5"}),
    ("M12 compaction store 8b->90",             {0x6917CE: 0x90}, {"C5"}),
    ("M13 guard2 imm byte 81->80 (C7 only)",    {0x691C1E: 0x80}, {"C7"}),
]

def run(mut):
    os.environ["R046_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and parts[0].startswith("C") and len(parts) > 1 and parts[1] == "FAIL:":
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
print("\n== R-046 mutation %d/%d killed (exact-set) ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all else 1)
