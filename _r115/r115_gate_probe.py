#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115_gate_probe —— 量化 C11 的三分类分区，找「永远通过」与「可静默摘除」的行。"""
import io, os, re, sys
R = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
rows = []
for ln in io.open(os.path.join(R, 'DISC_RECHECK.tsv'), encoding='utf-8').read().split('\n'):
    if not ln.strip(): continue
    c = ln.split('\t')
    if len(c) == 7 and c[0].strip().isdigit():
        rows.append(c)
print('data rows:', len(rows))
LANDABLE = {3,4,11,12,13,14,15,17,22,26,27,28}
FR = set()
for ln in io.open(os.path.join(R, 'DISC_UNVERIFIABLE.tsv'), encoding='utf-8').read().split('\n')[1:]:
    c = ln.split('\t')
    if c and c[0].strip().isdigit(): FR.add(int(c[0]))
has  = [int(r[0]) for r in rows if r[6].strip().startswith('有')]
none = [int(r[0]) for r in rows if not r[6].strip().startswith('有')]
print('claims-有 :', has, len(has))
print('claims-无 :', none, len(none))
print('frozen      :', sorted(FR), len(FR))
print()
print('--- 三分区 ---')
ok_cand     = [i for i in has if i not in FR]
frozen_has  = [i for i in has if i in FR]
print('可真检(有&未冻) =', len(ok_cand), ok_cand)
print('冻结行(有&冻)   =', len(frozen_has), frozen_has)
print('永远通过(无)     =', len(none), none)
print()
print('--- 漏洞 A：C11B_PIN_GAP 只钉住 LANDABLE 内的无行 ---')
gap_in_land = sorted(i for i in none if i in LANDABLE)
gap_out_land = sorted(i for i in none if i not in LANDABLE)
print('pinned by C11B:', gap_in_land, len(gap_in_land))
print('无行但不在 LANDABLE（既不钉也不报）:', gap_out_land, len(gap_out_land))
print()
print('--- 漏洞 B：有行可被静默翻成无 ---')
has_out_land = sorted(i for i in has if i not in LANDABLE)
print('有行且不在 LANDABLE（翻成无后无任何子项会变）:', has_out_land, len(has_out_land))
print('有行且在 LANDABLE（翻成无会触发 C11b drift）:', sorted(i for i in has if i in LANDABLE))
