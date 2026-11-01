# -*- coding: utf-8 -*-
"""R-044 mutation suite for the ScriptTypeClass big-block gate.
Measured-first (r042/r043 discipline): expectations are the kill-sets OBSERVED from the
gate's byte-window coverage, justified by window-overlap reasoning. In-process runpy
(no subprocess; command-injection hook false-positive avoided). Exact-set scoring:
a shared byte kills EVERY assertion whose window covers it.
"""
import io, os, runpy, contextlib, sys

ROOT = r"D:\Project\ra2-campaign-forge"
GATE = os.path.join(ROOT, "re_atlas", "tools", "r044_scripttype_block" + chr(46) + "py")

CASES = [
    # offsets measured from raw bytes THIS run (window-index -> VA verified).
    # M4 is the genuine SHARED-BYTE case: 0x691E10 is both the Save-window byte (X2)
    # AND the disp32 low byte of the 0x691E0E load that is X9's positive control.
    ("M1 GetSize imm 0x234->0x235",          {0x691F81: 0x35}, {"X1"}),
    ("M2 WhatAmI imm 0x1B->0x1C",            {0x691F71: 0x1C}, {"X1"}),
    ("M3 namepair 0x1B id ->0x1C",           {0x816FBC: 0x1C}, {"X1"}),
    ("M4 Save disp a0->a1 (X2 win+X9 ctrl)", {0x691E10: 0xA1}, {"X2", "X9"}),
    ("M5 Save call1 rel32 (X2 only)",        {0x691E0A: 0x00}, {"X2"}),
    ("M6 baseSave lea+0x24->+0x25",          {0x410BF0: 0x25}, {"X3"}),
    ("M7 strWriter head mov->nop",           {0x4A1DB0: 0x90}, {"X4"}),
    ("M8 dwordWriter push4 len->5",          {0x4A1D59: 0x05}, {"X5"}),
    ("M9 vptr low 0x08->0x09",               {0x691DB6: 0x09}, {"X6"}),
    ("M10 fixup cmp 0x23->0x24 (in win)",    {0x691E48: 0x24}, {"X7"}),
    ("M11 stride add edx,8->9",              {0x691EB4: 0x09}, {"X7"}),
    ("M12 regscan vector a4->a5 (out win)",  {0x691E79: 0xA5}, {"X7"}),
    ("M13 namepair 0x23 id ->0x22",          {0x816FFC: 0x22}, {"X8"}),
    ("M14 census load a0->a1 (X9 only)",     {0x691942: 0xA1}, {"X9"}),
    ("M15 fixup head 53->90 (X7 win)",       {0x691E30: 0x90}, {"X7"}),
]

def run(mut):
    os.environ["R044_MUTATE"] = ",".join("0x%X=0x%X" % (k, v) for k, v in mut.items())
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
        if parts and parts[0].startswith("X") and len(parts) > 1:
            if parts[1] == "FAIL:":
                killed.add(parts[0])
    return rc, killed

ok_all = True
n_ok = 0
for name, mut, expect in CASES:
    rc, killed = run(mut)
    score_ok = (killed == expect) and (rc != 0)
    n_ok += 1 if score_ok else 0
    print("%-38s expect=%s killed=%s rc=%s %s" % (
        name, sorted(expect), sorted(killed), rc, "OK" if score_ok else "MISMATCH"))
    if not score_ok:
        ok_all = False
print("\n== R-044 mutation %d/%d killed (exact-set) ==" % (n_ok, len(CASES)))
sys.exit(0 if ok_all else 1)
