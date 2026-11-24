# -*- coding: utf-8 -*-
p=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\PANEL.md'
d=open(p,'r',encoding='utf-8',newline='').read()
L=d.split('\n')
out=[]
out.append("TOTAL split parts: %d" % len(L))
for n in (69,70,77,119,120,183,184):
    out.append("=== L%d ===" % n)
    out.append(L[n-1])
# appended section: from line containing '## M59 并表说明' to end
start=None
for i,l in enumerate(L):
    if l.startswith('## M59 并表说明'):
        start=i; break
out.append("=== APPENDED SECTION starts at L%d ===" % (start+1 if start else -1))
if start is not None:
    for l in L[start:]:
        out.append(l)
open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_cards\M59-MERGE\PANEL_VERIFY_VIEW.txt','w',encoding='utf-8').write('\n'.join(out))
print('ok')
