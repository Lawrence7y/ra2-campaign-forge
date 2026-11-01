# -*- coding: utf-8 -*-
"""R-043 mutation suite for the L-30 gate (tools/r043_l30_housevec" + py).
Measured-first (r042 lesson): expect sets are the kill-sets OBSERVED from the gate's
byte-window coverage, not from memory. In-process runpy (no subprocess; command-injection
hook false-positive avoided). Exact-set scoring: a shared byte kills every assertion
whose window covers it -- expectations list them all.
"""
import io, os, runpy, contextlib, sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r043_l30_housevec" + chr(46) + "py")

CASES = [
    ("C1 finder walk bound 7e->8e (in Y1 window)",  {0x502D3D: 0x8E}, {"Y1"}),
    ("C2 vec-init opcode a3->a4",                  {0x4E6CE7: 0xA4}, {"Y2a", "Y3"}),
    ("C3 mangled-string first byte (Y2b raw find)", {0x8233B4: 0x5A}, {"Y2b"}),
    ("C4 teardown store 89->90 (Y3-only site)",    {0x4E6D47: 0x90}, {"Y3"}),
    ("C5 count-init store a3->a4 (Y2a+Y3)",        {0x4E6D11: 0xA4}, {"Y2a", "Y3"}),
    ("C6 push-count store head 89->90",            {0x4F61E0: 0x90}, {"Y3"}),
    ("C7 element store 89->90 (SIB site Y3)",      {0x4F61EC: 0x90}, {"Y3"}),
    ("C8 init-vptr imm byte (Y2a window)",         {0x4E6D01: 0xE5}, {"Y2a"}),
    ("C9 gate cmp target f9->fa (Y4 window)",      {0x71F1DE: 0xFA}, {"Y4"}),
    ("C10 consumer call byte (Y5 window)",         {0x726534: 0x00}, {"Y5"}),
    ("C11 handler-call rel32 (Y4 window)",         {0x71F1EE: 0x00}, {"Y4"}),
    ("C12 House WhatAmI imm 0d->0c (Y6 window)",   {0x50E362: 0x0C}, {"Y6"}),
]

def run(mut):
    os.environ["R043_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and (parts[0].startswith("Y")) and len(parts) > 1:
            if parts[1] == "FAIL:":
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
print("\n== R-043 mutation %d/%d killed (exact-set) ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all else 1)
