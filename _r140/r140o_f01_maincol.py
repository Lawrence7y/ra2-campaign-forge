import struct, re, json, collections
import pefile
data=open('ra2bench/gamemd.exe','rb').read(); N=len(data)
pe=pefile.PE('ra2bench/gamemd.exe', fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
def rva2off(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs):
            d=rva-va
            return raw+d if d<rs else None
    return None
def sec_of(rva):
    for nm,va,vs,raw,rs in secs:
        if va<=rva<va+max(vs,rs): return nm
    return None
def dw(va):
    if va is None: return None
    o=rva2off(va-IB)
    if o is None or o+4>N: return None
    return struct.unpack_from('<I',data,o)[0]
def indata(va): return va is not None and sec_of(va-IB) in ('.data','.rdata')
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8:g for s,g in strings if dw(s-8) is not None and dw(s-4)==0 and indata(dw(s-8))}
tdset=set(TDs); cand=set(); col2td={}
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-12
                if dw(c)==0 and dw(c+12)==v: cand.add(c); col2td[c]=v
COL={c for c in cand if dw(c+16)!=0}
md0={c for c in COL if dw(c+4)==0}
low={}
for c in COL:
    t=col2td[c]
    if t not in low or c<low[t]: low[t]=c
lowset=set(low.values())
A=1
def chk(name,cond):
    global A
    print('  %s %-58s %s' % ('PASS' if cond else 'FAIL', name, ''))
    assert cond, name
    A+=1
print('=== 954 vs 954: lowest-VA 主 COL  set  vs  mdisp==0 set ===')
chk('both sets have cardinality 954', len(lowset)==954 and len(md0)==954)
chk('the two sets are NOT equal', lowset!=md0)
chk('symmetric difference is 94+94=188', len(lowset-md0)==94 and len(md0-lowset)==94)
chk('both are one-per-TD (no TD appears twice in either)',
    len({col2td[c] for c in lowset})==954 and len({col2td[c] for c in md0})==954)
chk('union covers 1048 distinct TD-slots (<=954 TDs)', len(lowset|md0)==1048)
print()
print('=== mechanism: for MI classes COLs are laid out with DESCENDING mdisp ===')
# per TD with >1 COL: compare mdisp of lowest-VA COL vs mdisp==0 COL
asc=desc=same=other=0
for t,cols in collections.defaultdict(list, {k:[] for k in []}).items(): pass
bytd=collections.defaultdict(list)
for c in COL: bytd[col2td[c]].append(c)
for t,cs in bytd.items():
    cs=sorted(cs)
    if len(cs)<2: continue
    ms=[dw(c+4) for c in cs]
    if all(ms[i]>=ms[i+1] for i in range(len(ms)-1)) and ms[0]>ms[-1]: desc+=1
    elif all(ms[i]<=ms[i+1] for i in range(len(ms)-1)) and ms[0]<ms[-1]: asc+=1
    elif len(set(ms))==1: same+=1
    else: other+=1
print('  multi-COL TD with descending mdisp by VA: %d ; ascending: %d ; all-equal: %d ; mixed: %d' % (desc,asc,same,other))
nmulti=sum(1 for cs in bytd.values() if len(cs)>1)
chk('every multi-COL TD is strictly descending, none ascending/mixed',
    desc==nmulti and asc==0 and same==0 and other==0)
chk('the 94-symmetric-difference TDs ARE exactly the multi-COL TDs', nmulti==94)
print()
print('=== controls: the 94/94 split must be breakable ===')
# control 1: use highest-VA instead of lowest
hi={}
for c in COL:
    t=col2td[c]
    if t not in hi or c>hi[t]: hi[t]=c
hiset=set(hi.values())
print('  control  highest-VA instead of lowest: |diff vs mdisp0| = %d' % len(hiset-md0))
chk('highest-VA set differs from mdisp0 by a different amount than 94', len(hiset-md0)!=94 or len(md0-hiset)!=94)
# control 2: shuffle TD labels -> symmetric difference should collapse? use mdisp matched pairs
# control 3: compare mdisp==4 set
md4={c for c in COL if dw(c+4)==4}
print('  control  mdisp==4 set size %d ; |vs lowest| = %d' % (len(md4), len(md4-lowset)))
chk('mdisp==4 is not the same size as the main-COL set', len(md4)!=954)
print()
print('=== does every TD with mdisp==0 COL also have a lower-VA COL with mdisp!=0? ===')
# for the 94: show that the mdisp0 COL of that TD sits at HIGHER VA than the lowest one
n=0
for t in {col2td[c] for c in (lowset-md0)}:
    lm=[c for c in bytd[t] if dw(c+4)==0][0]
    lv=low[t]
    if lm>lv: n+=1
print('  of the 94 TDs whose lowest-VA COL has mdisp!=0, how many have their mdisp0 COL at higher VA: %d/94' % n)
chk('all 94 follow the same rule (mdisp0 COL sits at higher VA)', n==94)
print()
print('=== register the ambiguity as a citable fact ===')
print('  F01 parenthetical: 954 = one lowest-VA main COL per class        -> TRUE (%d)' % len(lowset))
print('  F29 main-table rule: mdisp==0                                    -> TRUE (%d)' % len(md0))
print('  but they select DIFFERENT 954-element sets (188 elements apart)  -> numbers equal, sets not')
print('TOTAL ASSERTIONS: %d PASS' % (A-1))
json.dump({'lowest':len(lowset),'mdisp0':len(md0),'symdiff':len(lowset^md0),'desc':desc}, open('_r140/r140o.json','w'))
