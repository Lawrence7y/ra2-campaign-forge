# -*- coding: utf-8 -*-
"""D37-CENSUS step 3 (final): full-table class_to_sub reattribution matrix.

class_to_sub rule — VERBATIM from COVERAGE/coverage_README.md lines 14-18:
  * RTTI class keyword map: LocomotionClass*->S11, TeamClass*->S14, HouseClass*->S14,
    WeaponTypeClass*->S13, *CommandClass->S09, T_Blit*/T_RLEBlit*->S07, 等(etc.)
  * container templates (T_VectorClass_*/T_DynamicVectorClass_*/T_TClassFactory_*/
    T_VectorCursor_* 等) -> S22
  * 映射不出 -> S22 (垃圾桶 default)

Implementation discipline (no invented rules):
  - ONLY the explicitly written keyword families are used; the trailing "等" is NOT
    expanded with keywords from classify.py or anywhere else.
  - "X*" = prefix match; "*X" = suffix match (as the notation states).
  - container templates take priority over the element-type keyword (D-37's point:
    a VectorClass<WeaponTypeClass*> is a container -> S22, not S13).
  - A row is reattributed only when class_to_sub gives a DEFINITE target (keyword or
    container) that differs from its current subsystem. Rows with no RTTI class or
    an unmapped class keep their current subsystem: the README's "映射不出->S22"
    default is stated in the P0-GATE-NEW-ENTRY context, not as a whole-table order
    to garbage-collect every existing row (doing so would erase all 21 subsystems).
  - RTTI class comes ONLY from self-derived vtable slots (.rdata COL chain), never
    from function_atlas.tsv bounds.
  - FAIL-CLOSED for 错源 ⑯ (same address in N vtables): an entry whose memberships
    map to >1 distinct target is NOT reattributed (stays put). Base-class level
    cannot be recovered from a flat keyword match; e.g. 00410210 sits in 76 vtables
    (AbstractClass..WeaponTypeClass), 004C9150 in 205. Only single-target entries
    ( overwhelmingly container templates, which all map to S22 ) are moved.

Outputs: S22_CENSUS.tsv, REATTRIB_MATRIX.tsv, reattrib_summary.json,
         FULL_REATTRIB.tsv (every moved row, audit trail).
"""
import os,re,sys,struct,collections,json,math,csv
import pefile
sys.stdout.reconfigure(encoding='utf-8')
HERE=os.path.dirname(os.path.abspath(__file__));PROJ=os.path.abspath(os.path.join(HERE,'..','..','..','..'))
ROOT=os.path.join(PROJ,'lead','next_re_20261117_r14');DEL=os.path.abspath(os.path.join(HERE,'..'))
EXE=os.path.join(PROJ,'ra2youli','gamemd.exe');COV=os.path.join(ROOT,'COVERAGE','coverage.tsv')
ATL=os.path.join(PROJ,'lead','next_re_20261112_r10','W130_atlas','function_atlas.tsv')

# ---------- RTTI vtable slots (.rdata only) ----------
pe=pefile.PE(EXE);IB=pe.OPTIONAL_HEADER.ImageBase;SZ=pe.OPTIONAL_HEADER.SizeOfImage
def sec(n):return [s for s in pe.sections if s.Name.rstrip(b'\0').decode('latin1')==n][0]
t=sec('.text');r=sec('.rdata');TLO=IB+t.VirtualAddress;THI=TLO+t.Misc_VirtualSize;RLO=IB+r.VirtualAddress;RSZ=r.SizeOfRawData
blob=open(EXE,'rb').read()
def off(va):
    rv=va-IB
    if rv<0 or rv>=SZ:return None
    for s in pe.sections:
        sv=s.VirtualAddress;vs=max(s.Misc_VirtualSize,s.SizeOfRawData)
        if sv<=rv<sv+vs:
            o=s.PointerToRawData+(rv-sv);return o if 0<=o<len(blob) else None
    return None
def u32(va):
    o=off(va);return struct.unpack_from('<I',blob,o)[0] if o is not None and o+4<=len(blob) else None
def cs(va,cap=256):
    o=off(va)
    if o is None or o+cap>len(blob):return b''
    b=blob[o:o+cap];z=b.find(b'\0');return b[:z] if z>0 else b''
def rn(cp):
    if not(IB<=cp<IB+SZ):return None
    sig=u32(cp);td=u32(cp+0xC);pcd=u32(cp+0x10)
    if sig not in(0,1) or td is None or not(IB<=td<IB+SZ) or pcd is None:return None
    nm=cs(td+8)
    return nm.decode('latin1') if nm.startswith(b'.?AV') or nm.startswith(b'.?AU') else None
def dem(x):
    if x.startswith('.?AV') or x.startswith('.?AU'):x=x[4:]
    if x.endswith('@@'):x=x[:-2]
    return x.replace('?$','T_').replace('@','::')
rdb=blob[r.PointerToRawData:r.PointerToRawData+RSZ];nw=len(rdb)//4;w=struct.unpack_from('<%dI'%nw,rdb,0)
def it(v):return TLO<=v<THI
fmap=collections.defaultdict(list);i=0;n_tables=n_slots=0
while i<nw:
    if it(w[i]):
        j=i
        while j<nw and it(w[j]):j+=1
        cp=w[i-1] if i>=1 else 0;raw=rn(cp)
        if raw is not None:
            n_tables+=1;n_slots+=(j-i);c=dem(raw)
            for k in range(j-i):fmap[w[i+k]].append((c,raw,k))
        i=j
    else:i+=1
print('RTTI self-attest: %d tables / %d slots (baseline 1214/14044)'%(n_tables,n_slots))

# ---------- class_to_sub: written rule, strict prefix/suffix ----------
CONT=('vectorclass','tclassfactory','vectorcursor','dynamicvector')  # exactly the 4 written families (DynamicVectorClass subsumes VectorClass)
def c2s(c,raw):
    low=c.lower(); rl=raw.lower()
    # container templates first (priority); match demangled 'T_VectorClass::' or raw '?$VectorClass@'
    if any(k in low or k in rl for k in CONT):return 'S22'
    base=low.rstrip(':')
    if base.startswith('locomotionclass'):return 'S11'
    if base.startswith('teamclass') or base.startswith('houseclass'):return 'S14'
    if base.startswith('weapontypeclass'):return 'S13'
    if base.endswith('commandclass'):return 'S09'
    if base.startswith('t_blit') or base.startswith('rleblit'):return 'S07'
    return None

# ---------- coverage + atlas ----------
def ne(e):
    e=e.strip().upper()
    if e.startswith('0X'):e=e[2:]
    try:return '%08X'%int(e,16)
    except:return e
atlas=set()
with open(ATL,encoding='utf-8-sig') as f:
    for i,ln in enumerate(f):
        if i==0:continue
        p=ln.rstrip('\r\n').split('\t')
        if p and p[0].strip():atlas.add(ne(p[0]))
cov=[]
with open(COV,encoding='utf-8-sig') as f:
    for row in list(csv.reader(f,delimiter='\t'))[1:]:
        if len(row)>=8:cov.append(dict(entry=ne(row[0]),sub=row[1].strip(),name=row[2].strip(),sem=row[3],grade=row[4].strip()))
print('coverage=%d atlas=%d'%(len(cov),len(atlas)))
RE_SLOT=re.compile(r'::v?slot\d+$');RE_CSUB=re.compile(r'::sub_[0-9A-Fa-f]+$')
def named_counts(rows):
    L=S14=ST=proved=provedST=0
    for rr in rows:
        nm=rr['name']
        if nm and not nm.startswith('sub_'):
            L+=1
            if not RE_CSUB.search(nm):
                S14+=1
                if not RE_SLOT.search(nm):ST+=1
        if rr['grade']=='[已证]':
            proved+=1
            if '[未证]' not in rr['sem']:provedST+=1
    return dict(named_L=L,named_S14=S14,named_strict=ST,proved=proved,proved_strict=provedST)
def metrics(rows_by_sub):
    out={}
    for s in sorted(k for k in rows_by_sub if re.match(r'^S\d\d$',k)):
        rows=rows_by_sub[s];a=len(rows);c=named_counts(rows);tn,tp=math.ceil(0.9*a),math.ceil(0.5*a)
        out[s]=dict(atlas_n=a,**c,thu_named=tn,thu_proved=tp,
            pct_named_R14=round(100.0*c['named_S14']/a,2) if a else 0.0,
            pct_proved=round(100.0*c['proved']/a,2) if a else 0.0,
            nominal=(c['named_S14']>=tn and c['proved']>=tp),
            strict=(c['named_S14']>=tn and c['proved_strict']>=tp))
    return out

# per-entry RTTI target (deterministic; fail-closed on 错源 ⑯ ambiguity)
def entry_target(e):
    mem=fmap.get(int(e,16))
    if not mem:return (None,None)
    # include None as a value: if the entry sits in N vtables and only one derived
    # class matches a keyword while the base/others are unmapped, that is 错源 ⑯
    # (base-class level) and must NOT be reattributed. Only when EVERY membership
    # maps to the SAME non-None target is the attribution unambiguous.
    vals=set(c2s(c,raw) for c,raw,slot in mem)
    if vals=={None}:return ('UNMAPPED',mem)
    if len(vals)==1:return (next(iter(vals)),mem)
    return ('AMBIGUOUS',mem)   # 错源 ⑯: multi-table entry, keep current

# ---- before mapping ----
before_rows=collections.defaultdict(list)
for rr in cov:
    if rr['entry'] in atlas:before_rows[rr['sub']].append(rr)
before=metrics(before_rows)
sp={}
with open(os.path.join(ROOT,'RULING_R15_20261119','work','strict_panel.tsv'),encoding='utf-8') as f:
    hd=f.readline().rstrip('\n').split('\t')
    for ln in f:
        p=ln.rstrip('\n').split('\t');sp[p[0]]=dict(zip(hd,p))
diffs=[(s,k,before[s][k],sp[s][q]) for s in before for k,q in [('atlas_n','atlas_n'),('named_S14','named_S14'),('proved','proved_n')] if str(before[s][k])!=sp[s][q]]
print('BEFORE vs canonical strict_panel.tsv: %s'%('MATCH' if not diffs else 'DIFF %r'%diffs[:6]))
print('BEFORE nominal:',[s for s in sorted(before) if before[s]['nominal']],' strict:',[s for s in sorted(before) if before[s]['strict']])

# ---- full-table reattribution ----
after_sub={rr['entry']:rr['sub'] for rr in cov}
moved=[]
for rr in cov:
    tgt,mem=entry_target(rr['entry'])
    if tgt and tgt not in ('UNMAPPED','AMBIGUOUS') and tgt!=rr['sub']:
        moved.append(dict(entry=rr['entry'],frm=rr['sub'],to=tgt,name=rr['name'],
                          cls=(mem[0][0] if mem else ''),atlas=(rr['entry'] in atlas)))
        after_sub[rr['entry']]=tgt
print('FULL-TABLE moves=%d (atlas-in %d)'%(len(moved),sum(1 for m in moved if m['atlas'])))
print('move pairs:',dict(collections.Counter((m['frm'],m['to']) for m in moved)))

after_rows=collections.defaultdict(list)
for rr in cov:
    if rr['entry'] in atlas:after_rows[after_sub[rr['entry']]].append(rr)
after=metrics(after_rows)
print('AFTER nominal:',[s for s in sorted(after) if after[s]['nominal']],' strict:',[s for s in sorted(after) if after[s]['strict']])

# ---- S22 census rows (target under written rule) ----
s22=[rr for rr in cov if rr['sub']=='S22']
census=[]
for rr in s22:
    e=rr['entry']
    tgt,mem=entry_target(e)
    if mem:
        cls_slot='; '.join('%s@slot%d'%(c,k) for c,_,k in mem[:12])
        nameable='YES'
    else:
        cls_slot='';nameable='NO'
    # S22 census target: definite single target used; ambiguous/unmapped -> S22 (fail-closed)
    target=tgt if (tgt and tgt not in ('UNMAPPED','AMBIGUOUS')) else 'S22'
    census.append((e,rr['grade'],nameable,cls_slot,target,'S22'))

# ---------- write deliverables ----------
with open(os.path.join(DEL,'S22_CENSUS.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('entry\tgrade\tnameable\tclass_and_slot\tclass_to_sub_target\tcurrent_sub\n')
    for row in census:
        f.write('\t'.join(str(x).replace('\t',' ') for x in row)+'\n')
print('wrote S22_CENSUS.tsv (%d rows)'%len(census))

cols=['S','before_atlas_n','after_atlas_n','delta_n','before_named_S14','after_named_S14',
      'before_proved','after_proved','before_proved_strict','after_proved_strict',
      'before_thu_named','after_thu_named','before_thu_proved','after_thu_proved',
      'before_nominal_dod','after_nominal_dod','before_strict_dod','after_strict_dod',
      'before_pct_named','after_pct_named','before_pct_proved','after_pct_proved']
with open(os.path.join(DEL,'REATTRIB_MATRIX.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('\t'.join(cols)+'\n')
    for s in sorted(before):
        b=before[s];a=after[s]
        f.write('\t'.join(str(x) for x in [s,b['atlas_n'],a['atlas_n'],a['atlas_n']-b['atlas_n'],
            b['named_S14'],a['named_S14'],b['proved'],a['proved'],b['proved_strict'],a['proved_strict'],
            b['thu_named'],a['thu_named'],b['thu_proved'],a['thu_proved'],
            int(b['nominal']),int(a['nominal']),int(b['strict']),int(a['strict']),
            b['pct_named_R14'],a['pct_named_R14'],b['pct_proved'],a['pct_proved']])+'\n')
print('wrote REATTRIB_MATRIX.tsv')

with open(os.path.join(DEL,'FULL_REATTRIB.tsv'),'w',encoding='utf-8',newline='') as f:
    f.write('entry\tfrom\tto\trtti_class\tname\tatlas_in\n')
    for m in sorted(moved,key=lambda x:(x['frm'],x['to'],x['entry'])):
        f.write('%s\t%s\t%s\t%s\t%s\t%s\n'%(m['entry'],m['frm'],m['to'],m['cls'].replace('\t',' '),m['name'].replace('\t',' '),int(m['atlas'])))
print('wrote FULL_REATTRIB.tsv (%d rows)'%len(moved))

summary=dict(n_tables=n_tables,n_slots=n_slots,
    s22_total=len(s22),s22_in=sum(1 for r in s22 if r['entry'] in atlas),
    s22_out=sum(1 for r in s22 if r['entry'] not in atlas),
    grade=dict(collections.Counter(r['grade'] for r in s22)),
    nameable=sum(1 for c in census if c[2]=='YES'),
    unnameable=sum(1 for c in census if c[2]=='NO'),
    total_moves=len(moved),atlas_moves=sum(1 for m in moved if m['atlas']),
    move_pairs={ '%s->%s'%k:v for k,v in collections.Counter((m['frm'],m['to']) for m in moved).items() },
    before_nominal=[s for s in sorted(before) if before[s]['nominal']],
    after_nominal=[s for s in sorted(after) if after[s]['nominal']],
    before_strict=[s for s in sorted(before) if before[s]['strict']],
    after_strict=[s for s in sorted(after) if after[s]['strict']],
    before=before,after=after)
with open(os.path.join(HERE,'reattrib_summary.json'),'w',encoding='utf-8') as f:
    json.dump(summary,f,ensure_ascii=False,indent=1)
print('wrote reattrib_summary.json')
print('\n=== DOD COMPARISON ===')
for s in sorted(before):
    b=before[s];a=after[s]
    if b['nominal']!=a['nominal'] or b['strict']!=a['strict']:
        print('  %s: nominal %s->%s strict %s->%s atlas %d->%d'%(s,b['nominal'],a['nominal'],b['strict'],a['strict'],b['atlas_n'],a['atlas_n']))
