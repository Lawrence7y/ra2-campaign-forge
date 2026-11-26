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
vts=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in COL:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vts.append((vt,v,IB+va+i*4))
backed={v for _,v,_ in vts}
bytd=collections.defaultdict(list)
for c in COL: bytd[col2td[c]].append(c)
low={t:min(cs) for t,cs in bytd.items()}; lowset=set(low.values())
hi={t:max(cs) for t,cs in bytd.items()}; hiset=set(hi.values())
md0={c for c in COL if dw(c+4)==0}
A=1
def chk(n,c):
    global A
    print('  %s %-62s' % ('PASS' if c else 'FAIL', n)); assert c, n; A+=1
print('=== R89 claim: "主 COL = 该 TD 的最低 VA COL, 954/954" ===')
chk('lowest-VA set has 954 elements (so the count matches)', len(lowset)==954)
chk('lowest-VA set IS NOT the mdisp==0 set (94 apart)', lowset!=md0 and len(lowset^md0)==188)
chk('HIGHEST-VA set IS EXACTLY the mdisp==0 set', hiset==md0)
chk('so the VA rule in R89 is inverted, not the count', len(hiset-md0)==0 and len(md0-hiset)==0)
print()
print('=== R89 claim: "与 dword[V-4] 不等 88 条" ===')
# for each TD, the COL that its primary vtable points back to: take the vtable whose slot0 is in .text and lowest VA? R89 said 'dword[V-4]'.
# Reconstruct: for each TD, choose the COL with lowest VA vtable among vtables pointing to any COL of this TD
best={}
for vt,c,_ in vts:
    t=col2td[c]
    if t not in best or vt<best[t][0]: best[t]=(vt,c)
print('  TDs with at least one vtable-backed COL: %d' % len(best))
mism=[(t,best[t][1],low[t]) for t in best if best[t][1]!=low[t]]
print('  #TD where vtable-pointed COL != lowest-VA COL : %d' % len(mism))
mism2=[(t,best[t][1],hi[t]) for t in best if best[t][1]!=hi[t]]
print('  #TD where vtable-pointed COL != highest-VA COL: %d' % len(mism2))
mism3=[(t,best[t][1],md0col) for t in best if (md0col:=[c for c in bytd[t] if dw(c+4)==0][0]) and best[t][1]!=md0col]
print('  #TD where vtable-pointed COL != mdisp==0 COL  : %d' % len(mism3))
print('  R89 wrote 88 ; reproducing any of these as 88 would confirm its chain:',
      'lowest' if len(mism)==88 else '', 'highest' if len(mism2)==88 else '', 'mdisp0' if len(mism3)==88 else '')
print()
print('=== which VA rule + which set actually satisfies "1 per TD" ? ===')
for nm,s in (('lowest',lowset),('highest',hiset),('mdisp0',md0)):
    print('  %-8s size=%d distinct TD=%d' % (nm,len(s),len({col2td[c] for c in s})))
print('TOTAL ASSERTIONS: %d PASS' % (A-1))
json.dump({'lowest':len(lowset),'highest':len(hiset),'md0':len(md0),
           'mism_low':len(mism),'mism_hi':len(mism2),'mism_md0':len(mism3)}, open('_r140/r140p.json','w'), indent=1)
