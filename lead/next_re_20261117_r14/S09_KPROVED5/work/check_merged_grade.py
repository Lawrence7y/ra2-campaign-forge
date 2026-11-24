import os, csv
base = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
cov = os.path.join(base, 'COVERAGE', 'coverage.tsv')
# coverage header uses comma, data uses TAB; read raw
grade = {}
name = {}
with open(cov, encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i == 0: continue
        parts = line.rstrip('\n').split('\t')
        if len(parts) < 5: continue
        grade[parts[0]] = parts[4]
        name[parts[0]] = parts[2]

merged = ['004A9840','004A9DD0','004AA050','004AAD30','004AAE90','004AB9B0','004ACE70','004E2690','004E2830','00557730','00557830','00565B00','00577920','005BDF70','005BE6D0','0063FB20','0063FEA0','006568A0','0069DEB0','006A5310','006A5840','006A7780','006A7D70','006ABD30','006D02B0','006D0680','00723EC0']
print('entry grade name')
cnt={}
for e in merged:
    g = grade.get(e,'MISSING')
    cnt[g]=cnt.get(g,0)+1
    print(e, g, name.get(e,''))
print('---grade distribution', cnt)
