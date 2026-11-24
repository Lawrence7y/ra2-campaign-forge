import csv,re,json,math
from pathlib import Path
B=Path(r'D:\Project\ra2-campaign-forge')
cov=B/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
at=B/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
FIELDS=['entry','subsystem','name','one_line_semantics','grade','evidence_path','n_sources','conflict']
def rows(p):
    lines=p.read_text(encoding='utf-8-sig').splitlines()
    out=[]
    for line in lines[1:]:
        if not line.strip(): continue
        parts=line.split('\t')
        if len(parts)<len(FIELDS): parts += ['']*(len(FIELDS)-len(parts))
        out.append(dict(zip(FIELDS,parts[:len(FIELDS)])))
    return out
C=rows(cov); A=rows(at)
ae={r['entry'].strip().upper() for r in A}
pat=re.compile(r'::SUB_[0-9A-F]{8}$',re.I)
slot=re.compile(r'::(?:V?SLOT)[0-9]+$',re.I)
from collections import Counter
out={'cov_rows':len(C),'atlas_rows':len(A),'grades':dict(Counter(r['grade'].strip() for r in C)),'sub':{}}
for i in range(1,23):
 s='S%02d'%i
 rs=[r for r in C if r.get('subsystem','').strip().upper()==s and r['entry'].strip().upper() in ae]
 def nm(r):
  n=r.get('name','').strip(); L=bool(n) and not n.upper().startswith('SUB_'); S=L and not pat.search(n.upper()); T=S and not slot.search(n.upper())
  return L,S,T
 namedL=sum(nm(r)[0] for r in rs); namedS=sum(nm(r)[1] for r in rs); namedT=sum(nm(r)[2] for r in rs)
 proved=sum(r['grade'].strip()=='[已证]' for r in rs); stat=sum(r['grade'].strip()=='[静态推断]' for r in rs)
 thr=math.ceil(len(rs)/2)
 out['sub'][s]={'n':len(rs),'namedL':namedL,'namedS':namedS,'namedT':namedT,'proved':proved,'static':stat,'threshold':thr,'gap':max(0,thr-proved)}
print(json.dumps(out,ensure_ascii=False,indent=2))
