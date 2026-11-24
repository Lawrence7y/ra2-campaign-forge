"""Independent final validation of C01 deliverables. Reads only, writes EVIDENCE/validation.txt."""
import os, re, json, collections
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); EVID=os.path.join(BASE,'EVIDENCE')
PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
ATLAS=os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB=chr(9)
checks=[]
def ck(name,ok,detail=''):
    checks.append((name,bool(ok),detail))

# atlas slice
al=open(ATLAS,encoding='utf-8',errors='replace').read().splitlines()[1:1293]
ck('atlas slice rows == 1292', len(al)==1292, str(len(al)))
ck('atlas total data rows == 12916', len(open(ATLAS,encoding='utf-8',errors='replace').read().splitlines())-1==12916)

# coverage_delta
cl=open(os.path.join(BASE,'coverage_delta.tsv'),encoding='utf-8').read().splitlines()
ck('coverage_delta header', cl[0]=='entry\tsubsystem\tname\tone_line_semantics\tgrade\tevidence_path', cl[0])
rows=cl[1:]
ck('coverage_delta rows == 1292', len(rows)==1292, str(len(rows)))
ck('coverage_delta all 6 cols', all(len(r.split(TAB))==6 for r in rows))
ents=[r.split(TAB)[0] for r in rows]
ck('coverage_delta unique entries', len(set(ents))==1292)
ck('coverage_delta hex8 entries', all(re.fullmatch(r'[0-9a-fA-F]{8}',e) for e in ents))
ck('coverage_delta entries == atlas slice entries', set(ents)==set(r.split(TAB)[0] for r in al))
subs=[r.split(TAB)[1] for r in rows]
ck('subsystems all S01-S22', all(re.fullmatch(r'S\d\d',s) and 1<=int(s[1:])<=22 for s in subs))
grades=[r.split(TAB)[4] for r in rows]
ck('grades valid', all(g in ('[已证]','[静态推断]','[未证]') for g in grades))
hi=grades.count('[已证]')
ck('high count == 102', hi==102, str(hi))
ck('grade sum', grades.count('[已证]')+grades.count('[静态推断]')+grades.count('[未证]')==1292)

# atlas_gaps
gl=open(os.path.join(BASE,'atlas_gaps.tsv'),encoding='utf-8').read().splitlines()
gaps=gl[1:]
ck('atlas_gaps rows == 2', len(gaps)==2, str(len(gaps)))
gtargs=[g.split(TAB)[0] for g in gaps]
ck('gap targets not in atlas slice', all(t.lower() not in [e.lower() for e in ents] for t in gtargs), str(gtargs))

# PROGRESS
pl=open(os.path.join(BASE,'PROGRESS.md'),encoding='utf-8').read().splitlines()
ck('PROGRESS <=60 lines', len(pl)<=60, str(len(pl)))
ck('PROGRESS has 3 core numbers', all(k in '\n'.join(pl) for k in ('1292','102','2')))

# files exist
for fn in ('UNKNOWNS.md','DISAGREE.md','EVIDENCE/evidence_raw.json','EVIDENCE/slice_disasm.txt',
           'EVIDENCE/callgraph.json','EVIDENCE/atlas_gaps_full.json','work/classify.py','work/scan_atlas_gaps.py'):
    ck('exists '+fn, os.path.exists(os.path.join(BASE,fn)))

# capstone skipdata in all analysis scripts
for fn in ('collect_evidence.py','scan_atlas_gaps.py','classify_gaps.py','verify_gaps.py','dump_disasm.py'):
    p=os.path.join(HERE,fn)
    if os.path.exists(p):
        ck(fn+' skipdata=True', 'skipdata=True' in open(p,encoding='utf-8').read())

# final report
out=[]
for name,ok,detail in checks:
    out.append(('PASS' if ok else 'FAIL')+'  '+name+('  ['+detail+']' if detail else ''))
open(os.path.join(EVID,'validation.txt'),'w',encoding='utf-8').write('\n'.join(out))
nfail=sum(1 for _,ok,_ in checks if not ok)
out.append('\nTOTAL=%d FAIL=%d'%(len(checks),nfail))
print('\n'.join(out))
