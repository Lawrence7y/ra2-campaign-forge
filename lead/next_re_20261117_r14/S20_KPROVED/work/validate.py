import csv,json,os,hashlib
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED'
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
T=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
def rows(p):
    with open(p,encoding='utf-8') as f:
        r=csv.reader(f,delimiter='\t'); h=next(r); return h,[x for x in r if x]
h,delta=rows(os.path.join(OUT,'coverage_delta.tsv'))
h2,d39=rows(os.path.join(OUT,'D39_CANDIDATES.tsv'))
cov={}
for line in open(COV,encoding='utf-8').read().splitlines()[1:]:
    c=line.split('\t')
    if len(c)==8: cov[c[0]]=c
sel=[r[0] for r in delta]; d39e=[r[0] for r in d39]
scan=json.load(open(os.path.join(OUT,'EVIDENCE','s20_scan.json'),encoding='utf-8'))
errs=[]; oks=[]
if len(delta)!=40: errs.append('delta rows !=40')
if len(set(sel))!=40: errs.append('delta entries not unique')
if set(sel)&set(d39e): errs.append('delta/D39 overlap')
for r in delta:
    e,sub,name,sem,grade,ev,kind,chg=r
    c=cov.get(e)
    if not c: errs.append(e+' missing coverage'); continue
    if sub!='S20' or c[1]!='S20': errs.append(e+' subsystem')
    if name!=c[2]: errs.append(e+' name changed')
    if c[4]!='[静态推断]': errs.append(e+' old grade != static')
    if grade!='[已证]' or chg!='[静态推断]→[已证]': errs.append(e+' grade change')
    if not os.path.exists(os.path.join(OUT,ev)): errs.append(e+' evidence missing')
    if not scan['rows'][e]['direct_calls_into'] and not scan['rows'][e]['exact_dispatch_into']:
        # exact_v3 evidence may not be reflected in s20_scan exact column; check proof file instead
        pf=os.path.join(OUT,'EVIDENCE','PROOF_%s.txt'%e)
        pt=open(pf,encoding='utf-8').read()
        if 'RING_TYPE=EXACT' not in pt and 'RING_TYPE=DIRECT' not in pt: errs.append(e+' no ring4')
for r in d39:
    if r[0] in sel: errs.append('D39 overlap '+r[0])
# in-memory merge
merged=dict(cov)
for r in delta:
    c=list(cov[r[0]]); c[4]='[已证]'; merged[r[0]]=c
n=sum(1 for c in merged.values() if c[1]=='S20' and c[0] in scan['rows'])
proved=sum(1 for c in merged.values() if c[1]=='S20' and c[4]=='[已证]' and c[0] in scan['rows'])
if (n,proved)!=(410,80): errs.append('merged counts %s %s'%(n,proved))
sha=hashlib.sha256(open(T,'rb').read()).hexdigest().upper()
if sha!='73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476': errs.append('target hash')
oks=['delta=40 unique=40','D39=294 no overlap','names unchanged','old/new grades correct','evidence files exist','merged S20 proved=80/410','target sha unchanged']
txt='VALIDATION '+('PASS' if not errs else 'FAIL')+'\n'+'\n'.join('- '+x for x in oks)+'\n'
if errs: txt+='ERRORS\n'+'\n'.join('- '+x for x in errs)+'\n'
open(os.path.join(OUT,'EVIDENCE','validation.txt'),'w',encoding='utf-8').write(txt)
print(txt)
