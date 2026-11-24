"""Dump compact evidence summary for all 1292 slice functions -> EVIDENCE/slice_evidence_summary.tsv.
Columns: row entry size ncaller vfrtti vslot yrpp strings imports callee_named sample
"""
import os, json
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); PROJECT=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
EVID=os.path.join(BASE,'EVIDENCE'); ATLAS=os.path.join(PROJECT,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')
TAB=chr(9)
with open(ATLAS,encoding='utf-8',errors='replace') as f: lines=f.read().splitlines()
sl=lines[1:1293]
yrpp=json.load(open(os.path.join(HERE,'yrpp_names.json'),encoding='utf-8'))
yin={int(k):v for k,v in yrpp.items()}
vf=json.load(open(os.path.join(HERE,'rtti_vtables.json'),encoding='utf-8'))['func_map']
vfin={int(k):v for k,v in vf.items()}
ev=json.load(open(os.path.join(EVID,'evidence_raw.json'),encoding='utf-8'))
cg=json.load(open(os.path.join(EVID,'callgraph.json'),encoding='utf-8'))
with open(os.path.join(EVID,'slice_evidence_summary.tsv'),'w',encoding='utf-8') as out:
    out.write('row\tentry\tsize\tncallers\tvfrtti\tvfslot\tyrpp\tstrings\timports\tncallees\tncallers_actual\n')
    for i,ln in enumerate(sl,1):
        p=ln.split(TAB); e=int(p[0],16)
        vfrtti='|'.join(sorted(set(m['cls'] for m in vfin.get(e,[]))))[:60]
        vfslot=','.join(str(m['slot']) for m in vfin.get(e,[])[:4])
        yp=';'.join(r['full'] for r in yin.get(e,[]))[:80]
        e0=ev.get(str(e),{})
        strs=';'.join(x['s'][:40] for x in e0.get('strings',[])[:5])
        imps=';'.join(x['name'].split('!')[-1] for x in e0.get('imports',[])[:5])
        out.write('%d\t%08X\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\n'%(
            i,e,p[1],p[3],vfrtti,vfslot,yp,strs,imps,len(e0.get('callees',[])),len(cg.get(str(e),[]))))
print('written')
