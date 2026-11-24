
# -*- coding: utf-8 -*-
"""AUDIT-ATEXIT analyze: classify every [已证] row A/B/C/D.
A live vptr = the vtable installed by a CONSTRUCTOR (non-atexit) write.
B = entry only sits in tables installed by atexit-registered destructors.
"""
import pickle, json, struct, sys, os, bisect, csv, random
from array import array
OUT=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.dirname(os.path.dirname(OUT))
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
ATLAS=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
COV=os.path.join(BASE,'COVERAGE','coverage.tsv')
blob=open(EXE,'rb').read()
d=pickle.load(open(os.path.join(OUT,'insns.pkl'),'rb'))
secs=d['secs']; TEXT_LO,TEXT_HI=d['text']
addrs,sizes,flags=d['addrs'],d['sizes'],d['flags']
pushval,calltgt,jmptgt=d['pushval'],d['calltgt'],d['jmptgt']
store_imm,store_reg,movreg,immref=d['store_imm'],d['store_reg'],d['movreg'],d['immref']
F_RET=1
idx={a:i for i,a in enumerate(addrs)}
def va2raw(v):
    for s in secs:
        if s['rawsize'] and s['va']<=v<s['va']+s['rawsize']:
            return s['rawptr']+(v-s['va'])
    return None
def dword(v):
    r=va2raw(v)
    return None if r is None else struct.unpack_from('<I',blob,r)[0]
def strz(v,maxn=200):
    r=va2raw(v)
    if r is None: return None
    return blob[r:r+maxn].split(b'\x00')[0]

# ---------- function starts ----------
atlas={}
with open(ATLAS,encoding='utf8') as f:
    next(f)
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)>=2 and p[0]: atlas[int(p[0],16)]=int(p[1])
rets=[addrs[i] for i in range(len(addrs)) if flags[i]&F_RET]
starts=set(atlas)|set(calltgt.values())
for r in rets:
    ofs=r+sizes[idx[r]]; i=idx.get(ofs)
    while i is not None and i<len(addrs):
        b=blob[va2raw(addrs[i]):va2raw(addrs[i])+sizes[i]]
        if b in (b'\x90',b'\xcc'): i+=1; continue
        starts.add(addrs[i]); break
starts_sorted=sorted(starts)
def enclosing(a):
    j=bisect.bisect_right(starts_sorted,a)-1
    return starts_sorted[j] if j>=0 else TEXT_LO
print('fn starts',len(starts_sorted),file=sys.stderr)

# ---------- atexit registrations ----------
regs=[]
n_atexit=0
for i,a in enumerate(addrs):
    if calltgt.get(a)==0x7C978A:
        n_atexit+=1
        for j in range(i-1,max(-1,i-41),-1):
            if addrs[j] in pushval: regs.append((a,addrs[j],pushval[addrs[j]]))
registered=set(r[2] for r in regs)
print('atexit calls',n_atexit,'push-registrations',len(regs),'distinct dtor fns',len(registered),file=sys.stderr)

# ---------- install sites ----------
installs=[]   # dict
for site,vt,kind,dest in store_imm:
    fn=enclosing(site)
    installs.append(dict(site=site,vt=vt,kind=kind,dest=dest,via='imm_store',fn=fn,dtor=fn in registered))
for site,(reg,vt) in movreg.items():
    i=idx[site]; fn=enclosing(site)
    for k in range(i+1,min(i+7,len(addrs))):
        a=addrs[k]
        if enclosing(a)!=fn: break
        if a in store_reg and reg in store_reg[a]:
            installs.append(dict(site=a,vt=vt,kind='reg',dest=None,via='reg_move',fn=fn,
                                 dtor=fn in registered,ldr=site))
            break
by_vt={}
for it in installs: by_vt.setdefault(it['vt'],[]).append(it)
n_dtor=sum(1 for i in installs if i['dtor'])
print('installs',len(installs),'dtor-side',n_dtor,'distinct vt installed',len(by_vt),file=sys.stderr)

# ---------- data code-pointer census: runs, COL anchors ----------
DATA=[s for s in secs if s['name'] in ('.rdata','.data')]
allpos=[]
for s in DATA:
    r=s['rawptr']; n=s['rawsize']//4
    for i in range(n):
        v=struct.unpack_from('<I',blob,r+i*4)[0]
        if TEXT_LO<=v<TEXT_HI: allpos.append((s['va']+i*4,v,s['name']))
allpos.sort()
runs=[];cur=[]
last=None;cursec=None
for pos,v,sn in allpos:
    if last is not None and pos==last+4 and cur and sn==cursec: cur.append((pos,v))
    else:
        if cur: runs.append(cur)
        cur=[(pos,v)]
    last=pos; cursec=sn
if cur: runs.append(cur)
run_of_pos={}; run_start_of_pos={}
for ri,rn in enumerate(runs):
    for pos,v in rn: run_of_pos[pos]=ri; run_start_of_pos[pos]=rn[0][0]
def is_col(p):
    td=dword(p+0xC)
    if td is None or td<0x400000: return None
    s=strz(td+8,200)
    if s and (s[:3]==b'?AV' or s[:4]==b'.?AV'):
        try: return s.decode('ascii')
        except: return None
    return None
col_at={}
for pos,v,sn in allpos:
    c=dword(pos-4)
    if c is None or c<0x400000: continue
    nm=is_col(c)
    if nm: col_at[pos]=(c,nm)
print('code ptr slots',len(allpos),'runs',len(runs),'COL anchors',len(col_at),file=sys.stderr)
pos2val={pos:v for pos,v,sn in allpos}
# candidate table starts inside each run
run_cands={}
for k in col_at: run_cands.setdefault(run_of_pos[k],set()).add(k)
for vt in by_vt:
    if vt in run_of_pos: run_cands.setdefault(run_of_pos[vt],set()).add(vt)
for ri,rn in enumerate(runs): run_cands.setdefault(ri,set()).add(rn[0][0])
run_cands={ri:sorted(v) for ri,v in run_cands.items()}

# data static-init: dword in .data equal to a table start, outside any run
datapos_by_val={}
for s in DATA:
    if s['name']!='.data': continue
    r=s['rawptr']; n=s['rawsize']//4
    for i in range(n):
        v=struct.unpack_from('<I',blob,r+i*4)[0]
        if 0x400000<=v<0xC00000 and (s['va']+i*4) not in pos2val:
            datapos_by_val.setdefault(v,[]).append(s['va']+i*4)

# ---------- coverage ----------
rows=[]
with open(COV,encoding='utf8') as f:
    hdr=f.readline()
    for line in f:
        p=line.rstrip('\n').split('\t')
        if len(p)<5: continue
        rows.append(dict(entry=int(p[0],16),sub=p[1],name=p[2],sem=p[3],grade=p[4]))
proved=[r for r in rows if r['grade']=='[已证]']
atlas_set=set(atlas)
print('coverage rows',len(rows),'proved',len(proved),file=sys.stderr)

direct_targets=set(calltgt.values())|set(jmptgt.values())

def classify(E):
    """returns (cls, detail dict)"""
    det=dict(entry=E)
    det['direct_call'] = E in set(calltgt.values())
    det['direct_jmp'] = E in set(jmptgt.values())
    det['immref_sites'] = immref.get(E)
    if det['direct_call'] or det['direct_jmp']:
        return 'C', det
    if det['immref_sites']:
        det['c_kind']='immref'
        return 'C', det
    pos_list=[pos for pos,v,sn in allpos if v==E]
    if not pos_list:
        det['reason']='no code/data reference at all'
        return 'D', det
    tabs=[]
    for P in pos_list:
        T=run_start_of_pos[P]
        for c in run_cands.get(run_of_pos[P],[]):
            if c<=P: T=c
        K=(P-T)//4
        ins=by_vt.get(T,[])
        live=[i for i in ins if not i['dtor']]
        dead=[i for i in ins if i['dtor']]
        stat=datapos_by_val.get(T,[])
        tabs.append(dict(pos=P,table=T,slot=K,col=(col_at.get(T,(None,None))[1]),
                         live=live,dtor=dead,static_init=stat,
                         run_start=run_start_of_pos[P]))
    det['tables']=tabs
    anylive=any(t['live'] or t['static_init'] for t in tabs)
    anydtor=any(t['dtor'] for t in tabs)
    if anylive: return 'A', det
    if anydtor: return 'B', det
    return 'D', det

res={}
cls_of={}
for r in proved:
    c,det=classify(r['entry'])
    cls_of[r['entry']]=c
    res.setdefault(c,[]).append((r,det))
counts={k:len(v) for k,v in sorted(res.items())}
print('COUNTS',counts,file=sys.stderr)
pickle.dump(dict(res={k:[(r,{kk:(vv if kk!='tables' else [{k2:v2 for k2,v2 in t.items() if k2 not in ()} for t in vv]) for kk,vv in det.items()}) for r,det in v] for k,v in res.items()},
                counts=counts, cls_of=cls_of,
                registered=sorted(registered), n_atexit=n_atexit, n_regs=len(regs),
                n_install=len(installs), n_dtor_install=n_dtor,
                n_runs=len(runs), n_col=len(col_at), n_atlas=len(atlas),
                col_at=col_at, datapos=datapos_by_val, starts_n=len(starts_sorted)),
            open(os.path.join(OUT,'res.pkl'),'wb'), protocol=4)
print('WROTE res.pkl',file=sys.stderr)
