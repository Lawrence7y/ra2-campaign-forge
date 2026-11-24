"""Validate S10-K2 coverage_delta.tsv: 6 cols, hex8, no dup, grade legal, all in coverage, S10."""
import csv,os,re
ROOT=r'D:\Project\ra2-campaign-forge'
D=os.path.join(ROOT,r'lead\next_re_20261117_r14\S10-K2\coverage_delta.tsv')
COV=os.path.join(ROOT,r'lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
cov={}
with open(COV,encoding='utf-8') as f:
    for r in csv.DictReader(f,delimiter='\t'): cov[r['entry'].upper()]=r
rows=list(csv.reader(open(D,encoding='utf-8'),delimiter='\t'))
L=[]; ok=True
def P(s):
    global ok
    L.append(str(s)); print(s)
P('delta rows: %d'%len(rows))
seen=set()
for i,r in enumerate(rows):
    if len(r)!=6: P('FAIL row%d cols=%d'%(i,len(r))); ok=False; continue
    e,sub,nm,sem,gr,ev=r
    if not re.fullmatch(r'[0-9A-F]{8}',e): P('FAIL row%d entry %s'%(i,e)); ok=False
    if sub!='S10': P('FAIL row%d subsystem %s'%(i,sub)); ok=False
    if gr not in ('[已证]','[静态推断]','[未证]'): P('FAIL row%d grade %s'%(i,gr)); ok=False
    if e in seen: P('FAIL dup %s'%e); ok=False
    seen.add(e)
    if e not in cov: P('WARN %s not in coverage (new entry)'%e)
    else:
        if cov[e]['subsystem']!='S10': P('WARN %s coverage subsystem=%s'%(e,cov[e]['subsystem']))
        if cov[e]['grade']=='[已证]': P('WARN %s already [已证] in coverage'%e)
P('all structural checks: %s'%('PASS' if ok else 'FAIL'))
with open(os.path.join(ROOT,r'lead\next_re_20261117_r14\S10-K2\EVIDENCE\validate_delta.txt'),'w',encoding='utf-8') as f: f.write('\n'.join(L)+'\n')
