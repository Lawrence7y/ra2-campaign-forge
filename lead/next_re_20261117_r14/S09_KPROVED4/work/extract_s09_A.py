"""Extract S09 A-set rows (strict 2∩4) from SURVEY_RING24 classification.tsv.
Cross-reference coverage.tsv for current grade/name/semantics.
Exclude already-merged 18 + 2 judged-invalid; print full detail.
"""
import csv, json
from pathlib import Path

ROOT = Path(r'D:\Project\ra2-campaign-forge')
R14 = ROOT/'lead'/'next_re_20261117_r14'
CLASS = R14/'SURVEY_RING24'/'EVIDENCE'/'classification.tsv'
COV = R14/'COVERAGE'/'coverage.tsv'
OUT = R14/'S09_KPROVED4'/'work'

# already-merged 18 (from card)
MERGED = set('''004AAE90 005BDF70 006A5310 004AB9B0 0063FEA0 006A7780 004ACE70 006ABD30 006A5840 006D0680 0063FB20 005BE6D0 004E2690 00557730 004A9840 004A9DD0 004AA050 004AAD30'''.split())
INVALID = set('00654320 0069DEB0'.split())

# coverage.tsv: header comma, data TAB
cov = {}
with COV.open(encoding='utf-8') as f:
    lines = f.read().splitlines()
for ln in lines[1:]:
    parts = ln.split('\t')
    if len(parts) >= 5:
        cov[parts[0].upper()] = dict(name=parts[2], sem=parts[3], grade=parts[4], conf=parts[7] if len(parts)>7 else '')

rows = []
with CLASS.open(encoding='utf-8') as f:
    rd = csv.DictReader(f, delimiter='\t')
    for r in rd:
        if r['subsystem']=='S09' and r['class_PRIMARY']=='A':
            e = r['entry'].upper()
            c = cov.get(e, {})
            rows.append(dict(
                entry=e,
                rtti=r['rtti_classes'], vt=r['rtti_vt'], slot=r['rtti_slot'],
                ndir=int(r['n_direct_out']), sites=r['ring4_direct_sites'],
                livevt=r['ring4_livevt'],
                ext_lo=r['ext_lo'], ext_hi=r['ext_hi'], size=int(r['atlas_size']),
                cname=r['name'],
                cov_name=c.get('name',''), cov_sem=c.get('sem',''), grade=c.get('grade',''),
                merged=e in MERGED, invalid=e in INVALID,
            ))

# strict direct vs livevt split
ndir = sum(1 for x in rows if x['ndir']>0)
nlive = sum(1 for x in rows if x['ndir']==0)
remaining = [x for x in rows if not x['merged'] and not x['invalid']]

json.dump(rows, open(OUT/'s09_A_full.json','w'), ensure_ascii=False, indent=1)
json.dump(remaining, open(OUT/'s09_A_remaining.json','w'), ensure_ascii=False, indent=1)

print('S09 A strict total =', len(rows), ' direct=',ndir,' livevt=',nlive)
print('merged present in A =', sum(1 for x in rows if x['merged']), 'of 18')
print('invalid present in A =', sum(1 for x in rows if x['invalid']))
print('remaining =', len(remaining))
print('grade histogram remaining:', {g:sum(1 for x in remaining if x['grade']==g) for g in set(x['grade'] for x in remaining)})
print()
for x in remaining:
    print(f"{x['entry']} sz={x['size']:<5} dir={x['ndir']:<2} vt={x['vt']:<10} slot={x['slot']:<4} cls={x['rtti'][:55]:<55} grade={x['grade']:<10} name={x['cov_name']}")
