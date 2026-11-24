
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
COV=os.path.join(OUT,'snapshot','coverage_pinned.tsv')   # pinned; see snapshot/SNAPSHOT.json
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



# ---------- global-anchored install model (v2) ----------
# A vptr install is "global-anchored" when the store target is a static global
# (abs store), or a register store whose base register was loaded with a global
# address in the same function.
DATA_LO, DATA_HI = 0x812000, 0xB79A28
def is_global_addr(a):
    return DATA_LO <= a < DATA_HI
def enclosing_idx(fn):
    j = bisect.bisect_right(starts_sorted, fn) - 1
    return j
def base_reg_global(site):
    """scan back <=25 insns within same fn for 'mov reg, <global addr>' / 'lea reg,[global]'"""
    i = idx[site]; fn = enclosing(site); res = {}
    for k in range(i-1, max(-1, i-26), -1):
        a = addrs[k]
        if enclosing(a) != fn: break
        if a in movreg:
            reg, imm = movreg[a]
            if is_global_addr(imm): res[reg] = imm
    return res
global_installs = []   # (vt, global, site, kind, fn, dtor)
for site, vt, kind, dest in store_imm:
    fn = enclosing(site)
    if kind == 'abs':
        global_installs.append(dict(vt=vt, global_addr=dest, site=site, kind='abs',
                                    fn=fn, dtor=fn in registered))
    else:
        global_installs.append(dict(vt=vt, global_addr=None, site=site, kind='reg',
                                    fn=fn, dtor=fn in registered))
by_vt_global = {}
for it in global_installs:
    if it['global_addr'] is not None:
        by_vt_global.setdefault(it['vt'], []).append(it)
print('global-anchored installs', sum(len(v) for v in by_vt_global.values()),
      'tables with global install', len(by_vt_global), file=sys.stderr)

# ---- helpers exported ----
def load_rows():
    rows=[]
    with open(COV,encoding='utf8') as f:
        hdr=f.readline()
        for line in f:
            p=line.rstrip('\n').split('\t')
            if len(p)<5: continue
            rows.append(dict(entry=int(p[0],16),sub=p[1],name=p[2],sem=p[3],grade=p[4]))
    return rows
direct_targets=set(calltgt.values())|set(jmptgt.values())
pos_index={}
for pos,v,sn in allpos: pos_index.setdefault(v,[]).append(pos)

def classify(E):
    det=dict(entry=E)
    det['direct_call']= E in set(calltgt.values())
    det['direct_jmp'] = E in set(jmptgt.values())
    det['immref_sites']=immref.get(E)
    if det['direct_call'] or det['direct_jmp']: return 'C',det
    if det['immref_sites']:
        det['c_kind']='immref'; return 'C',det
    pos_list=pos_index.get(E,[])
    if not pos_list:
        det['reason']='no code/data reference at all'; return 'D',det
    tabs=[]
    for P in pos_list:
        T=run_start_of_pos[P]
        for c in run_cands.get(run_of_pos[P],[]):
            if c<=P: T=c
        K=(P-T)//4
        ins=by_vt.get(T,[]); live=[x for x in ins if not x['dtor']]; dead=[x for x in ins if x['dtor']]
        tabs.append(dict(pos=P,table=T,slot=K,col=col_at.get(T,(None,None))[1],
                         live=live,dtor=dead,static_init=datapos_by_val.get(T,[]),
                         run_start=run_start_of_pos[P]))
    det['tables']=tabs
    if any(t['live'] or t['static_init'] for t in tabs): return 'A',det
    if any(t['dtor'] for t in tabs): return 'B',det
    return 'D',det

def classify_v2(E):
    """Global-anchored A/B/C/D. Live value == a CONSTRUCTOR (non-atexit) write of
    the table into a static global. Dtor-only == every global-anchored write of
    that table sits in an atexit-registered destroy routine (or a dtor reached
    from one)."""
    det = dict(entry=E)
    det['direct_call'] = E in set(calltgt.values())
    det['direct_jmp'] = E in set(jmptgt.values())
    det['immref_sites'] = immref.get(E)
    if det['direct_call'] or det['direct_jmp']:
        det['c_kind'] = 'direct_branch'; return 'C', det
    if det['immref_sites']:
        det['c_kind'] = 'immref'; return 'C', det
    pos_list = pos_index.get(E, [])
    if not pos_list:
        det['reason'] = 'no code/data reference at all'; return 'D', det
    tabs = []
    for P in pos_list:
        T = run_start_of_pos[P]
        for c in run_cands.get(run_of_pos[P], []):
            if c <= P: T = c
        K = (P - T) // 4
        gi = by_vt_global.get(T, [])
        live = [x for x in gi if not x['dtor']]
        dead = [x for x in gi if x['dtor']]
        tabs.append(dict(pos=P, table=T, slot=K, col=col_at.get(T, (None, None))[1],
                         live=live, dtor=dead, static_init=datapos_by_val.get(T, []),
                         run_start=run_start_of_pos[P]))
    det['tables'] = tabs
    if any(t['live'] or t['static_init'] for t in tabs): return 'A', det
    if any(t['dtor'] for t in tabs): return 'B', det
    return 'D', det

# ---------- v3: slot-0/1 destructor signature for register stores ----------
def table_entries(T, n=40):
    out=[]
    for k in range(n):
        v=dword(T+4*k)
        if v is None or not (TEXT_LO<=v<TEXT_HI): break
        out.append(v)
    return out
def installer_is_dtor(fn, T):
    """A virtual function cannot be a constructor. If the installing function is
    itself slot 0/1 of the very table it installs, it is that class's destructor
    (MSVC places ~X at slot 0 and the scalar deleting dtor at slot 1)."""
    ent=table_entries(T)
    return len(ent)>1 and fn in ent[:2]
installs_all=[]
for site, vt, kind, dest in store_imm:
    fn=enclosing(site)
    d = (fn in registered) or installer_is_dtor(fn, vt)
    installs_all.append(dict(site=site,vt=vt,kind=kind,
        global_addr=(dest if kind=='abs' else None),fn=fn,dtor=d,via='imm_store'))
for site,(reg,vt) in movreg.items():
    i=idx[site]; fn=enclosing(site)
    for k in range(i+1,min(i+7,len(addrs))):
        a=addrs[k]
        if enclosing(a)!=fn: break
        if a in store_reg and reg in store_reg[a]:
            installs_all.append(dict(site=a,vt=vt,kind='reg',global_addr=None,fn=fn,
                dtor=(fn in registered) or installer_is_dtor(fn,vt),via='reg_move',ldr=site))
            break
by_vt_all={}
for it in installs_all: by_vt_all.setdefault(it['vt'],[]).append(it)
print('v3 installs',len(installs_all),'dtor-side',sum(1 for i in installs_all if i['dtor']),
      'tables',len(by_vt_all),file=sys.stderr)

def classify_v3(E):
    det=dict(entry=E)
    det['direct_call']=E in set(calltgt.values())
    det['direct_jmp']=E in set(jmptgt.values())
    det['immref_sites']=immref.get(E)
    if det['direct_call'] or det['direct_jmp']:
        det['c_kind']='direct_branch'; return 'C',det
    if det['immref_sites']:
        det['c_kind']='immref'; return 'C',det
    pos_list=pos_index.get(E,[])
    if not pos_list:
        det['reason']='no code/data reference at all'; return 'D',det
    tabs=[]
    for P in pos_list:
        T=run_start_of_pos[P]
        for c in run_cands.get(run_of_pos[P],[]):
            if c<=P: T=c
        K=(P-T)//4
        ins=by_vt_all.get(T,[])
        live=[x for x in ins if not x['dtor']]; dead=[x for x in ins if x['dtor']]
        tabs.append(dict(pos=P,table=T,slot=K,col=col_at.get(T,(None,None))[1],
                         live=live,dtor=dead,static_init=datapos_by_val.get(T,[]),
                         run_start=run_start_of_pos[P]))
    det['tables']=tabs
    if any(t['live'] or t['static_init'] for t in tabs): return 'A',det
    if any(t['dtor'] for t in tabs): return 'B',det
    return 'D',det

# ---------- v4: global destructor-function set (slot 0/1 of ANY table) ----------
def table_entries(T,n=60):
    out=[]
    for k in range(n):
        v=dword(T+4*k)
        if v is None: break
        if not (TEXT_LO<=v<TEXT_HI):
            out.append(None); continue
        out.append(v)
    return out
# every COL-anchored table + every observed install target is a table start
table_starts=set(col_at.keys())|set(by_vt.keys())
dtor_fns=set()
for T in table_starts:
    ent=table_entries(T,4)
    for k in (0,1):
        if k<len(ent) and ent[k]: dtor_fns.add(ent[k])
dtor_fns|=set(registered)
print('dtor fns (slot0/1 of any table + atexit-registered)',len(dtor_fns),file=sys.stderr)
installs_all2=[]
for site,vt,kind,dest in store_imm:
    fn=enclosing(site)
    installs_all2.append(dict(site=site,vt=vt,kind=kind,
        global_addr=(dest if kind=='abs' else None),fn=fn,
        dtor=(fn in dtor_fns),via='imm_store'))
for site,(reg,vt) in movreg.items():
    i=idx[site]; fn=enclosing(site)
    for k in range(i+1,min(i+7,len(addrs))):
        a=addrs[k]
        if enclosing(a)!=fn: break
        if a in store_reg and reg in store_reg[a]:
            installs_all2.append(dict(site=a,vt=vt,kind='reg',global_addr=None,fn=fn,
                dtor=(fn in dtor_fns),via='reg_move',ldr=site))
            break
by_vt_all2={}
for it in installs_all2: by_vt_all2.setdefault(it['vt'],[]).append(it)
print('v4 installs',len(installs_all2),'dtor-side',sum(1 for i in installs_all2 if i['dtor']),
      'tables',len(by_vt_all2),file=sys.stderr)

def classify_v4(E):
    det=dict(entry=E)
    det['direct_call']=E in set(calltgt.values())
    det['direct_jmp']=E in set(jmptgt.values())
    det['immref_sites']=immref.get(E)
    if det['direct_call'] or det['direct_jmp']:
        det['c_kind']='direct_branch'; return 'C',det
    if det['immref_sites']:
        det['c_kind']='immref'; return 'C',det
    pos_list=pos_index.get(E,[])
    if not pos_list:
        det['reason']='no code/data reference at all'; return 'D',det
    tabs=[]
    for P in pos_list:
        T=run_start_of_pos[P]
        for c in run_cands.get(run_of_pos[P],[]):
            if c<=P: T=c
        K=(P-T)//4
        ins=by_vt_all2.get(T,[])
        live=[x for x in ins if not x['dtor']]; dead=[x for x in ins if x['dtor']]
        tabs.append(dict(pos=P,table=T,slot=K,col=col_at.get(T,(None,None))[1],
                         live=live,dtor=dead,static_init=datapos_by_val.get(T,[]),
                         run_start=run_start_of_pos[P]))
    det['tables']=tabs
    if any(t['live'] or t['static_init'] for t in tabs): return 'A',det
    if any(t['dtor'] for t in tabs): return 'B',det
    return 'D',det

# ---------- v5: live-value test with base-subobject override detection ----------
# A vptr write W into [base_reg] is NOT live if, later in the same function,
# the same base register receives another vtable (base-subobject prologue), or
# if the containing function is a destructor (slot 0/1 of any table or atexit-registered).
def store_writes_in_fn(sites_fn):
    return sites_fn
_reg_sites_by_fn={}
for site,(reg,vt) in movreg.items():
    i=idx[site]; fn=enclosing(site)
    for k in range(i+1,min(i+7,len(addrs))):
        a=addrs[k]
        if enclosing(a)!=fn: break
        if a in store_reg and reg in store_reg[a]:
            _reg_sites_by_fn.setdefault(fn,[]).append((a,reg,vt,site)); break
_imm_sites_by_fn={}
for site,vt,kind,dest in store_imm:
    fn=enclosing(site)
    _imm_sites_by_fn.setdefault(fn,[]).append((site,kind,dest,vt))

def is_overridden(fn, site, reg, vt):
    """is the same register re-written with a different vtable later in fn?"""
    later=[]
    for (a,r,v,_l) in _reg_sites_by_fn.get(fn,[]):
        if a>site and r==reg and v!=vt: later.append(a)
    for (a,kind,dest,v) in _imm_sites_by_fn.get(fn,[]):
        if a>site and kind=='reg' and v!=vt: later.append(a)
    return min(later) if later else None

def live_write(fn_site, reg, vt, site):
    fn=enclosing(site)
    if fn in registered: return False,'in atexit-registered fn'
    if fn in dtor_fns: return False,'in destructor fn (slot0/1)'
    ov=is_overridden(fn, site, reg, vt)
    if ov is not None: return False,'overridden later at %08X'%ov
    return True,''

installs_v5=[]   # (vt, site, kind, global_addr, fn, live, why)
for site,vt,kind,dest in store_imm:
    fn=enclosing(site)
    if kind=='abs':
        live = fn not in registered
        why = 'atexit-registered fn' if not live else ''
        installs_v5.append(dict(vt=vt,site=site,kind='abs',global_addr=dest,fn=fn,
                                live=live,why=why))
    else:
        live,why=live_write(fn,None,vt,site)
        installs_v5.append(dict(vt=vt,site=site,kind='reg',global_addr=None,fn=fn,
                                live=live,why=why))
for site,(reg,vt) in movreg.items():
    i=idx[site]; fn=enclosing(site)
    if fn in registered or fn in dtor_fns: continue
    for k in range(i+1,min(i+7,len(addrs))):
        a=addrs[k]
        if enclosing(a)!=fn: break
        if a in store_reg and reg in store_reg[a]:
            ov=is_overridden(fn,a,reg,vt)
            installs_v5.append(dict(vt=vt,site=a,kind='reg',global_addr=None,fn=fn,
                live=(ov is None),why=('overridden later at %08X'%ov) if ov else 'reg/ctor'))
            break
by_vt_v5={}
for it in installs_v5: by_vt_v5.setdefault(it['vt'],[]).append(it)
print('v5 installs',len(installs_v5),'live',sum(1 for i in installs_v5 if i['live']),
      'tables',len(by_vt_v5),file=sys.stderr)

def classify_v5(E):
    det=dict(entry=E)
    det['direct_call']=E in set(calltgt.values())
    det['direct_jmp']=E in set(jmptgt.values())
    det['immref_sites']=immref.get(E)
    if det['direct_call'] or det['direct_jmp']:
        det['c_kind']='direct_branch'; return 'C',det
    if det['immref_sites']:
        det['c_kind']='immref'; return 'C',det
    pos_list=pos_index.get(E,[])
    if not pos_list:
        det['reason']='no code/data reference at all'; return 'D',det
    tabs=[]
    for P in pos_list:
        T=run_start_of_pos[P]
        for c in run_cands.get(run_of_pos[P],[]):
            if c<=P: T=c
        K=(P-T)//4
        ins=by_vt_v5.get(T,[])
        live=[x for x in ins if x['live']]; dead=[x for x in ins if not x['live']]
        tabs.append(dict(pos=P,table=T,slot=K,col=col_at.get(T,(None,None))[1],
                         live=live,dtor=dead,static_init=datapos_by_val.get(T,[])))
    det['tables']=tabs
    if any(t['live'] or t['static_init'] for t in tabs): return 'A',det
    if any(t['dtor'] for t in tabs): return 'B',det
    return 'D',det
