#!/usr/bin/env python3
"""T1: S19 target list. Case-normalize atlas (lower hex) vs coverage (upper hex)."""
import csv, re, os
ROOT = r'D:\Project\ra2-campaign-forge'
COV = os.path.join(ROOT, r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
ATL = os.path.join(ROOT, r'lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv')
OUT = os.path.join(ROOT, r'lead\next_re_20261117_r14\S19-K2\TARGETS.tsv')

def norm(e):
    e = e.strip().upper()
    # normalize to 8-digit hex uppercase
    try:
        return f'{int(e,16):08X}'
    except ValueError:
        return e

# atlas
atlas = {}
with open(ATL, encoding='utf-8') as f:
    r = csv.DictReader(f, delimiter='\t')
    for row in r:
        atlas[norm(row['entry'])] = row

# coverage S19
s19 = []
with open(COV, encoding='utf-8') as f:
    r = csv.DictReader(f, delimiter='\t')
    for row in r:
        if row['subsystem'].strip() == 'S19':
            s19.append(row)

# total coverage rows / grades
tot = 0; grades = {}
with open(COV, encoding='utf-8') as f:
    r = csv.DictReader(f, delimiter='\t')
    for row in r:
        tot += 1
        g = row['grade'].strip()
        grades[g] = grades.get(g,0)+1

def named_L(name):
    n = name.strip()
    return bool(n) and not n.startswith('sub_')
def named_S(name):
    n = name.strip()
    if not named_L(n): return False
    # Class::sub_XXXXXXXX placeholder (R14-R14 S 口径): any Class::sub_<hex>
    return re.search(r'::sub_[0-9A-Fa-f]+$', n) is None

# intersection
inter = []
for row in s19:
    e = norm(row['entry'])
    if e in atlas:
        inter.append((e, row, atlas[e]))

inter.sort(key=lambda x:int(x[0],16))

with open(OUT,'w',encoding='utf-8',newline='') as f:
    w = csv.writer(f, delimiter='\t', lineterminator='\n')
    w.writerow(['entry','subsystem','name','one_line_semantics','grade','evidence_path','conflict','atlas_size','atlas_n_instr','atlas_n_callers','atlas_n_callees','atlas_first_import','atlas_n_strings','atlas_strings'])
    for e,row,a in inter:
        w.writerow([e,'S19',row['name'],row['one_line_semantics'],row['grade'],row['evidence_path'],row['conflict'],
                    a['size'],a['n_instr'],a['n_callers'],a['n_callees'],a['first_import'],a['n_strings'],a['strings']])

# stats
allL = sum(named_L(r['name']) for r in s19)
allS = sum(named_S(r['name']) for r in s19)
allP = sum(r['grade'].strip()=='[已证]' for r in s19)
interL = sum(named_L(r['name']) for _,r,_ in inter)
interS = sum(named_S(r['name']) for _,r,_ in inter)
interP = sum(r['grade'].strip()=='[已证]' for _,r,_ in inter)
class_sub = sum(1 for r in s19 if re.search(r'::sub_[0-9A-Fa-f]+$', r['name'].strip()))
class_sub_inter = sum(1 for _,r,_ in inter if re.search(r'::sub_[0-9A-Fa-f]+$', r['name'].strip()))

print('coverage total rows =', tot)
print('coverage grades =', grades)
print('S19 all coverage rows =', len(s19))
print('S19 named_L =', allL, ' named_S =', allS, ' proved =', allP, ' Class::sub_ placeholders =', class_sub)
print('atlas entries =', len(atlas))
print('S19 ∩ atlas =', len(inter))
print('  named_L =', interL, f'({100*interL/len(inter):.2f}%)')
print('  named_S =', interS, f'({100*interS/len(inter):.2f}%)', ' Class::sub_ placeholders=',class_sub_inter)
print('  proved  =', interP, f'({100*interP/len(inter):.2f}%)')
print('S19 coverage rows NOT in atlas =', len(s19)-len(inter))
# 50% threshold
for denom,label in [(len(inter),'atlas_n'),(362,'card_362'),(357,'panel_357')]:
    need = denom//2 + 1  # strictly > half; threshold given as 181/362
    thr = (denom+1)//2
    print(f'50% threshold on {label}={denom}: need {thr} proved; currently {interP}; gap={thr-interP}')
