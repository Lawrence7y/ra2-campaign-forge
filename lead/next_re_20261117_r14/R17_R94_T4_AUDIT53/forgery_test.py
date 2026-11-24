# -*- coding: utf-8 -*-
"""Q4 forgery test: simulate 无 -> 有 forgery under CURRENT C11 vs PLANNED tri-state C11.
Read-only on lead files; writes only analysis3.json into this report dir.
"""
import csv, io, json, os, sys
BASE = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
ROOT = r'D:\Project\ra2-campaign-forge'
OUT  = os.path.join(BASE, r'R17_R94_T4_AUDIT53\analysis3.json')
sys.path.insert(0, BASE)
import recheck_verify as V

with io.open(os.path.join(BASE,'DISC_RECHECK.tsv'), encoding='utf-8', newline='') as f:
    rows = [r for r in csv.reader(f, delimiter='\t')]
hdr = rows[0]
data = rows[1:]

# discipline 11 is currently 无; its product = _r38\checkC3_report.md (no DISC_RECHECK line)
r11 = [r for r in data if r[0].strip()=='11'][0]
prod = r11[4].strip()
prod_abs = os.path.join(ROOT, prod.replace('/','\\'))
txt = io.open(prod_abs, encoding='utf-8', errors='replace').read()
n_disc_lines = sum(1 for l in txt.splitlines() if l.startswith('DISC_RECHECK '))

def current_c11(row):
    """exact logic from check_disc.py:238-254"""
    later = row[6].strip()
    if not later.startswith(u'有'):
        return ('UNVERIFIABLE', 'no-FAIL (col7 not startswith 有)')
    ok, detail = V.verify_recheck_line(ROOT, row)
    return ('FAIL' if not ok else 'OK', detail)

def planned_c11(row):
    """tri-state card R55-T2 lines 36-38: 可核->verify; 无自产出机制->不FAIL; 无->another count"""
    later = row[6].strip()
    if later.startswith(u'有·无自产出机制'):
        return ('UNVERIFIABLE', 'no-FAIL (new state exempt by design)')
    if later.startswith(u'有·可核'):
        ok, detail = V.verify_recheck_line(ROOT, row)
        return ('FAIL' if not ok else 'OK', detail)
    if later.startswith(u'有'):
        ok, detail = V.verify_recheck_line(ROOT, row)
        return ('FAIL' if not ok else 'OK', detail)
    return ('UNVERIFIABLE', 'no-FAIL (无)')

results = []
for label, newcol7 in [
    ('baseline (真实现状)', r11[6]),
    ('forgery A: 无 -> 有（后续轮回跑）', u'有（后续轮回跑）'),
    ('forgery B: 无 -> 有·无自产出机制', u'有·无自产出机制'),
    ('forgery C: 无 -> 有·可核', u'有·可核'),
]:
    forged = list(r11); forged[6] = newcol7
    cur = current_c11(forged)
    plan = planned_c11(forged)
    results.append({
        'case': label, 'col7': newcol7,
        'current_C11': {'state': cur[0], 'detail': cur[1][:120]},
        'planned_tristate_C11': {'state': plan[0], 'detail': plan[1][:120]},
        'caught_now': cur[0]=='FAIL',
        'caught_after': plan[0]=='FAIL',
    })

# Also verify the 12 rows that are "有 but not landable" would flip FAIL->noFAIL
landable = {3,4,11,12,13,14,15,17,22,26,27,28}
you_rows = [r for r in data if r[6].strip().startswith(u'有')]
flip = []
for r in you_rows:
    n = int(r[0])
    if n not in landable:   # these are the 12 "有 but not landable"
        forged = list(r); forged[6] = u'有·无自产出机制'
        cur = current_c11(forged); plan = planned_c11(forged)
        flip.append({'disc':n, 'old_col7':r[6], 'currently':cur[0], 'after_plan':plan[0]})

res = {
 'prod_path': prod, 'prod_DISC_RECHECK_line_count': n_disc_lines,
 'baseline_col7': r11[6],
 'forgery_cases': results,
 'flip_12_rows': flip,
 'flip_summary': {
    'n': len(flip),
    'currently_FAIL': sum(1 for x in flip if x['currently']=='FAIL'),
    'after_noFAIL': sum(1 for x in flip if x['after_plan']!='FAIL'),
 },
 'gate_counts': {
    'current': {'ok':0,'fail':17,'unver':11},
    'after_plan_estimate': {'ok':0,'fail':5,'unver':23},
    'note':'5 landable 有 rows (3,4,22,27,28) have no self-description line -> still FAIL; 12 flipped to no-FAIL; 11 无 + 12 = 23 unverifiable'
 }
}
with io.open(OUT,'w',encoding='utf-8') as f: json.dump(res,f,ensure_ascii=False,indent=2)
print('OK', OUT)
