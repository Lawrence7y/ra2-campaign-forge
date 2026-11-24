"""Step 2b: proper common-base attribution via CHD BaseClassArray transitive closure."""
import json
from pathlib import Path
from s09lib import u32, cstr, is_ro

OUT = Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S09_KPROVED4')
WORK, EV = OUT/'work', OUT/'EVIDENCE'

cols=[]
with (EV/'VTABLES_ALL.tsv').open(encoding='utf-8') as f:
    next(f)
    for ln in f:
        p=ln.rstrip('\n').split('\t')
        cols.append(dict(vt=int(p[0],16),col=int(p[1],16),td=int(p[2],16),name=p[3]))

direct={}
for c in cols:
    col=c['col']; chd=u32(col+0x10)
    if not chd or not is_ro(chd): continue
    nb=u32(chd+8); pba=u32(chd+0xC)
    if not pba or not is_ro(pba) or not nb: continue
    bs=[]
    for i in range(nb):
        bcd=u32(pba+4*i); btd=u32(bcd) if bcd else None
        bn=cstr(btd+8) if btd else None
        if bn and bn!=c['name']: bs.append(bn)
    prev=direct.get(c['name'],[])
    if len(bs)>len(prev): direct[c['name']]=bs

def ancestors(name):
    seen=set(); stack=[name]
    while stack:
        n=stack.pop()
        if n in seen: continue
        seen.add(n)
        for b in direct.get(n,[]): stack.append(b)
    return seen

anc={n:ancestors(n) for n in direct}

def common_base(names):
    if not names: return None
    sets=[anc.get(n,{n}) for n in names]
    common=set.intersection(*sets)
    if not common: return None
    deepest=max(common, key=lambda x: len(anc.get(x,{x})))
    return deepest

feat=json.load(open(WORK/'features.json'))
ar=json.load(open(WORK/'attrib_raw.json'))
rows=[]
for r in json.load(open(WORK/'s09_A_remaining.json')):
    e=r['entry']
    names=[h['name'] for h in ar[e]['hits']]
    cb=common_base(names)
    feat[e]['common_base']=cb
    feat[e]['chains']={n:sorted(anc.get(n,{n}), key=lambda x:-len(anc.get(x,{x}))) for n in sorted(set(names))}
    rows.append((e,cb,len(names),';'.join(names),';'.join(sorted(set(str(h['slot']) for h in ar[e]['hits'])))))

json.dump(feat,open(WORK/'features.json','w'),ensure_ascii=False,indent=1)

def strip(n): return n.replace('.?AV','').replace('.?AU','').replace('@@','') if n else 'None'
with (EV/'CLASS_ATTRIB.tsv').open('w',encoding='utf-8') as f:
    f.write('entry\tholding_tables\tall_names\tcommon_base\tattributed_class\tslots\n')
    for e,cb,nn,names,slots in rows:
        f.write('%s\t%d\t%s\t%s\t%s\t%s\n'%(e,nn,names,strip(cb),strip(cb),slots))

for e,cb,nn,names,slots in rows:
    if nn>=2:
        print('%-8s nh=%2d common=%-26s slots=%s'%(e,nn,strip(cb),slots))
