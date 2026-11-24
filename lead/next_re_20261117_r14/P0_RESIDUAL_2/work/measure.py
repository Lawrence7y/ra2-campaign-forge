#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure prologue/form-filter recall on positives vs baseline BEFORE designing verdict."""
import sys, os, collections, random
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from res2_common import *

pe = PE(); sw = Sweep(pe); at = Atlas()
cov = load_set(COVERAGE)
gate = load_set(GATE, 0, True, lambda p: p[8] == "FUNC")
resid = load_set(RESID, 0, True, lambda p: p[2] == "FUNC")

pool = []
for va in range((pe.tlo + 15) // 16 * 16, pe.thi, 16):
    if at.in_atlas(va): continue
    if sw.endmap.get(va) not in TERM: continue
    ins = sw.insn_at(pe, va)
    if ins is None or ins.mnemonic in JCC or ins.id == 0: continue
    pool.append(va)
poolset = set(pool)

print("N_pool=%d  pool∩cov=%d  pool\\cov=%d" % (
    len(pool), len(poolset & cov), len(poolset - cov)))

# positives = gate + resid, restricted to pool
pos = sorted((gate | resid) & poolset)
print("positives in pool=%d (gate=%d resid=%d)" % (
    len(pos), len(gate & poolset), len(resid & poolset)))

# form filter pieces
def probe(a):
    b = pe.try_read(a, 8)
    return dict(b0=b[0] if b else None,
                c4a=form_c4a(b), leaf=leafpat(b),
                form=form_c4a(b) or leafpat(b),
                not_e8e9eb=(b[0] not in E8E9EB) if b else False,
                push=(0x50 <= b[0] <= 0x57) if b else False,
                push_ebp=(b[0]==0x55), push_ecx=(b[0]==0x51),
                subesp=(b[0] in (0x83,0x81) and b[1]==0xEC) if len(b)>1 else False,
                pushimm=(b[0]==0x68),
                mov_edi_edi=(len(b)>=3 and b[0]==0x8B and b[1]==0xFF),
                )

cpos = collections.Counter()
for a in pos:
    p = probe(a)
    cpos['form'] += p['form']; cpos['c4a'] += p['c4a']; cpos['leaf'] += p['leaf']
    cpos['push'] += p['push']; cpos['push_ebp'] += p['push_ebp']
    cpos['push_ecx'] += p['push_ecx']; cpos['subesp'] += p['subesp']
    cpos['pushimm'] += p['pushimm']; cpos['mov_edi_edi'] += p['mov_edi_edi']
    cpos['not_e8e9eb'] += p['not_e8e9eb']
print("\nPOSITIVES (%d):" % len(pos))
for k in ['not_e8e9eb','form','c4a','leaf','push','push_ebp','push_ecx','subesp','pushimm','mov_edi_edi']:
    print("  %-12s %4d/%d = %.1f%%" % (k, cpos[k], len(pos), 100.0*cpos[k]/len(pos)))

# broadened prologue: any push reg/imm OR sub esp OR mov edi,edi OR lea ecx
def broad(b):
    if not b or len(b)<2: return False
    return (0x50<=b[0]<=0x57) or b[0] in (0x68,0x55,0x6A) or \
           (b[0] in (0x83,0x81) and b[1]==0xEC) or \
           (len(b)>=3 and b[0]==0x8B and b[1]==0xFF) or \
           b[0] in (0x8B,0x89,0x8D,0x33,0x31)  # common leaf starters

# first byte histogram on positives
fb = collections.Counter(probe(a)['b0'] for a in pos)
print("\nPOSITIVES first-byte histogram (top 20):")
for k,v in fb.most_common(20):
    print("  %02X : %4d" % (k,v) if k is not None else "  ?? : %4d"%v)

# baseline: atlas interior 16-aligned (known non-entry)
random.seed(20261117)
interior = []
for e,sz in at.rows:
    for va in range((e+16+15)//16*16, e+sz, 16):
        interior.append(va)
base = random.sample(interior, 5000)
cb = collections.Counter()
for a in base:
    p = probe(a)
    for k in ['form','c4a','leaf','push','push_ebp','push_ecx','subesp','pushimm','mov_edi_edi','not_e8e9eb']:
        cb[k]+=p[k]
    cb['broad']+=broad(pe.try_read(a,8))
cp = collections.Counter()
for a in pos:
    cp['broad']+=broad(pe.try_read(a,8))
print("\nBASELINE atlas-interior 5000 (non-entries):")
for k in ['form','c4a','leaf','push','push_ebp','push_ecx','subesp','pushimm','mov_edi_edi','broad','not_e8e9eb']:
    print("  %-12s %4d/5000 = %.1f%%" % (k, cb[k], 100.0*cb[k]/5000))
print("\nPOSITIVES broad = %d/%d = %.1f%%" % (cp['broad'],len(pos),100.0*cp['broad']/len(pos)))

# pool\cov breakdown: how many pass form / broad / first byte
newc = sorted(poolset - cov)
cn = collections.Counter()
for a in newc:
    p = probe(a)
    cn['form']+=p['form']; cn['broad']+=broad(pe.try_read(a,8))
    cn['not_e8e9eb']+=p['not_e8e9eb']
print("\nNEW (pool\\cov) n=%d: form=%d broad=%d not_e8e9eb=%d" % (
    len(newc), cn['form'], cn['broad'], cn['not_e8e9eb']))
