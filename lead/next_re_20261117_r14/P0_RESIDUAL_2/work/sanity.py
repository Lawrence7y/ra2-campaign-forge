#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recon sanity: verify lib loads, SHA, set sizes, sweep, qualified pool."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from res2_common import *

print("SHA", sha256_file(), "MATCH" if sha256_file() == SHA256 else "MISMATCH")
pe = PE()
print(".text [%08X,%08X) size=%d" % (pe.tlo, pe.thi, pe.thi - pe.tlo))
sw = Sweep(pe)
print("sweep insns=%d skipped_bytes=%d" % (sw.n, sw.nskip))
at = Atlas()
print("atlas rows=%d" % at.n)
cov = load_set(COVERAGE)
print("coverage entries=%d" % len(cov))
gate = load_set(GATE, 0, True, lambda p: p[8] == "FUNC")
print("gate FUNC entries=%d" % len(gate))
resid = load_set(RESID, 0, True, lambda p: p[2] == "FUNC")
print("resid FUNC entries=%d" % len(resid))
allfunc = cov | gate | resid
print("cov|gate|resid union distinct=%d" % len(allfunc))

# qualified pool (audit a13 definition)
pool = []
for va in range((pe.tlo + 15) // 16 * 16, pe.thi, 16):
    if at.in_atlas(va):
        continue
    if sw.endmap.get(va) not in TERM:
        continue
    ins = sw.insn_at(pe, va)
    if ins is None or ins.mnemonic in JCC or ins.id == 0:
        continue
    pool.append(va)
print("qualified pool N_pool=%d" % len(pool))
asked = [0x7775C0, 0x535E50, 0x4824D4]
for a in asked:
    print("%08X in_cov=%s in_gate=%s in_resid=%s in_pool=%s align16=%s first=%s pred=%s" % (
        a, a in cov, a in gate, a in resid, a in set(pool), a % 16 == 0,
        (pe.byte(a), pe.try_read(a, 4).hex()) if pe.in_text(a) else None,
        sw.pred(pe, a) if pe.in_text(a) else None))
