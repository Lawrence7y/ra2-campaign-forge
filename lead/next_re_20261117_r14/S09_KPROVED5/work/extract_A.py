import csv, json, os
base = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
cls = os.path.join(base, 'SURVEY_RING24', 'EVIDENCE', 'classification.tsv')
rows = []
with open(cls, encoding='utf-8') as f:
    r = csv.DictReader(f, delimiter='\t')
    for row in r:
        rows.append(row)
print('total rows', len(rows))
s09 = [x for x in rows if x['subsystem'] == 'S09']
print('S09 rows', len(s09))
# A main caliber = ②仅RTTI (has2_rtti==1) AND ④严格档 (has4_strict==1)
A = [x for x in s09 if x['has2_rtti'] == '1' and x['has4_strict'] == '1']
print('S09 A (has2_rtti & has4_strict)', len(A))
# breakdown by channel
direct = [x for x in A if int(x['n_direct_out']) > 0 or (x['ring4_direct_sites'] and x['ring4_direct_sites'].strip())]
livevt = [x for x in A if x['livevt_valid'] == '1']
print('A with direct sites', len(direct), 'A livevt_valid', len(livevt))
for x in A:
    print(x['entry'], 'slot='+x['rtti_slot'], 'dout='+x['n_direct_out'], 'lv='+x['livevt_valid'],
          'rtti_cls='+x['rtti_classes'], 'vt='+x['rtti_vt'], 'name='+x['name'],
          'sites='+x['ring4_direct_sites'][:80])
with open(os.path.join(base,'S09_KPROVED5','work','A_set.json'),'w',encoding='utf-8') as g:
    json.dump(A, g, ensure_ascii=False, indent=1)
