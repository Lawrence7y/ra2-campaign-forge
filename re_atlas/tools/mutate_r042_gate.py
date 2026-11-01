# -*- coding: utf-8 -*-
"""R-042 mutation suite for the L-29 gate (tools/r042_l29_field54" + py).
Workflow (measured-first): run the gate FIRST to confirm which assertions each byte
window covers, THEN set expected kill-sets. A shared byte legitimately kills EVERY
assertion whose window covers it -- the expectation lists them all (exact-set scoring).
In-process via runpy (no subprocess), env var drives the gate's in-memory blob copy.
"""
import importlib.util, io, os, runpy, sys, contextlib

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r042_l29_field54" + chr(46) + "py")

CASES = [
    ("C1 ctor zero-field 54->55",  {0x71E6C0: 0x55}, {"G1", "G8"}),  # disp byte shared: G1 window + G8 census
    ("C2 swizzle add-disp 54->55", {0x71F91D: 0x55}, {"G2"}),
    ("C3 Save item4 off 34->35",   {0x71F86D: 0x35}, {"G3"}),
    ("C4 handler head byte 90",    {0x71E940: 0x90}, {"G4"}),
    ("C5 store opcode 89->90",     {0x71F209: 0x90}, {"G5", "G8"}),
    ("C6 slot15 stub 33->90",      {0x4104A0: 0x90}, {"G6"}),
    ("C7 handler-call rel byte",   {0x726541: 0x00}, {"G7", "G9"}),
    ("C8 getter opcode 8b->90",    {0x71FA30: 0x90}, {"G6"}),
    ("C9 setter head 8b->90",      {0x71FA40: 0x90}, {"G9"}),
    ("C10 setter store 89->90",    {0x71FA44: 0x90}, {"G8", "G9"}),
]

def run(mut):
    os.environ["R042_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and (parts[0].startswith("G") or parts[0].startswith("S")) and len(parts) > 1:
            if parts[1] == "FAIL:":
                killed.add(parts[0])
    return rc, killed

ok_all = True
n_ok = 0
for name, mut, expect in CASES:
    rc, killed = run(mut)
    score_ok = (killed == expect) and (rc != 0)
    n_ok += 1 if score_ok else 0
    print("%-30s expect=%s killed=%s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False
print("\n== R-042 mutation %d/%d killed (exact-set) ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all else 1)
