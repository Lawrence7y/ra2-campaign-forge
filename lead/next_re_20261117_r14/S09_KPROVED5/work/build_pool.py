"""Build S09 A-set full (103) and the eligible remaining pool.
Exclusions: all 27 entries in the 4 prior S09_KPROVED{2,3,4} coverage_delta.tsv;
00654320 (③a judged invalid). Note 0069DEB0 (细则#1 fail) is inside the 27 already.
Cross-reference coverage.tsv for current grade/name/semantics.
"""
import csv, json, os
from pathlib import Path

ROOT = Path(r'D:\Project\ra2-campaign-forge')
R14 = ROOT/'lead'/'next_re_20261117_r14'
CLASS = R14/'SURVEY_RING24'/'EVIDENCE'/'classification.tsv'
COV = R14/'COVERAGE'/'coverage.tsv'
OUT = R14/'S09_KPROVED5'/'work'

# 27 entries appearing in the 4 prior delta files (22 actually merged=[已证] + 5 not merged)
DELTA = set('''004A9840 004A9DD0 004AA050 004AAD30 004AAE90 004AB9B0 004ACE70 004E2690
004E2830 00557730 00557830 00565B00 00577920 005BDF70 005BE6D0 0063FB20 0063FEA0
006568A0 0069DEB0 006A5310 006A5840 006A7780 006A7D70 006ABD30 006D02B0 006D0680 00723EC0'''.split())
INVALID = set('00654320 0069DEB0'.split())
MERGED22 = set('''004A9840 004A9DD0 004AA050 004AAD30 004AAE90 004AB9B0 004ACE70 004E2690
00557730 00557830 00577920 005BDF70 005BE6D0 0063FB20 0063FEA0 006568A0
006A5310 006A5840 006A7780 006ABD30 006D02B0 006D0680'''.split())

# coverage.tsv: header comma, data TAB
cov = {}
with COV.open(encoding='utf-8') as f:
    lines = f.read().splitlines()
for ln in lines[1:]:
    parts = ln.split('\t')
    if len(parts) >= 5:
        cov[parts[0].upper()] = dict(name=parts[2], sem=parts[3], grade=parts[4])

A = []
with CLASS.open(encoding='utf-8') as f:
    rd = csv.DictReader(f, delimiter='\t')
    for r in rd:
        if r['subsystem']=='S09' and r['has2_rtti']=='1' and r['has4_strict']=='1':
            e = r['entry'].upper()
            c = cov.get(e, {})
            A.append(dict(
                entry=e,
                rtti=r['rtti_classes'], vt=r['rtti_vt'], slot=r['rtti_slot'],
                ndir=int(r['n_direct_out']), sites=r['ring4_direct_sites'],
                livevt=r['ring4_livevt'],
                ext_lo=r['ext_lo'], ext_hi=r['ext_hi'], size=int(r['atlas_size']),
                cname=r['name'],
                cov_name=c.get('name',''), cov_sem=c.get('sem',''), grade=c.get('grade',''),
                in_delta=e in DELTA, invalid=e in INVALID, merged22=e in MERGED22,
            ))

ndir = sum(1 for x in A if x['ndir']>0)
nlive = sum(1 for x in A if x['ndir']==0)
# eligible = in A, not in any prior delta, not invalid, and direct-call caliber (ndir>0)
eligible = [x for x in A if not x['in_delta'] and not x['invalid'] and x['ndir']>0]
print('S09 A total =', len(A), ' direct=', ndir, ' livevt-only=', nlive)
print('in prior-delta (27) =', sum(1 for x in A if x['in_delta']))
print('merged22 present in A =', sum(1 for x in A if x['merged22']))
print('invalid present in A =', sum(1 for x in A if x['invalid']))
print('eligible pool (A minus 27 delta minus invalid, direct only) =', len(eligible))
from collections import Counter
print('grade histogram eligible:', dict(Counter(x['grade'] for x in eligible)))
json.dump(A, open(OUT/'s09_A_full.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(eligible, open(OUT/'s09_A_eligible.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print()
for x in eligible:
    print(f"{x['entry']} sz={x['size']:<5} dir={x['ndir']:<3} slot={x['slot']:<4} cls={x['rtti'][:48]:<48} grade={x['grade']:<10} name={x['cov_name']}")
