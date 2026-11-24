# -*- coding: utf-8 -*-
"""R16-FIX-B2-1ROW : rule self-test (read-only)."""
import os, sys
sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from host_rule import Image, HostRule, IB
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EXE = os.path.join(ROOT, "ra2youli", "gamemd.exe")
im = Image(EXE)
hr = HostRule(im)
VTF = 0x7E16B0
# site -> byte-derived host (see _explore.py output); 0x4019A6 corrected from audit's 0x401980
CAND = [
    (0x4019A6, 0x4019A0),
    (0x473A12, 0x4739F0),
    (0x473A4F, 0x473A30),
    (0x473A9B, 0x473A80),
    (0x535A76, 0x535A70),
    (0x697A37, 0x697840),
    (0x75951E, 0x759510),
    (0x4014AC, 0x4011C0),   # OLD broken site
]
for s, h in CAND:
    r = hr.classify(s, VTF, h)
    print("%08X host=%08X inbody=%s ins=%-34s stack=%s abs=%s this=%s chg=%s G4=%s dtorAft=%s sdd=%s ret=%s core=%s canon=%s dtor=%s gates=%s ctorcalls=%s" % (
        s, h, r["site_in_body"], r["ins"], r["target_is_stack"], r["target_is_abs"],
        r["this_from_ecx"], r["base_reg_changed"], r["base_ctor_before"],
        r["dtor_call_after"], r["sdd_sig"], r["returns_this"],
        r["host_is_ctor"], r["host_is_canonical_ctor"], r["host_is_dtor"],
        r["failed_gates"], r["ctor_call_targets"]))
