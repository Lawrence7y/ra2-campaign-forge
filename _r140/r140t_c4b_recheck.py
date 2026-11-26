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
# vt refs: record every hit
vthits=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in cand:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vthits.append((vt,v))
print('cand %d  COL %d  vt hits %d  distinct vt %d  distinct col in hits %d'
      % (len(cand),len(COL),len(vthits),len({v for v,_ in vthits}),len({c for _,c in vthits})))
byC=collections.defaultdict(list)
for vt,c in vthits: byC[c].append(vt)
print()
print('=== definition (b) under every reasonable variant ===')
variants={}
def add(name,s): variants[name]=s; print('  %-62s %d %s'%(name,len(s),'  <<< 1211' if len(s)==1211 else ('  <<< 1203' if len(s)==1203 else '')))
notAU=lambda c: not TDs[col2td[c]].startswith(b'.?AU')
add('over 1216: notAU & exactly-1 vt hit', {c for c in cand if notAU(c) and len(byC.get(c,[]))==1})
add('over 1214: notAU & exactly-1 vt hit', {c for c in COL if notAU(c) and len(byC.get(c,[]))==1})
add('over 1216: notAU & exactly-1 DISTINCT vt', {c for c in cand if notAU(c) and len(set(byC.get(c,[])))==1})
add('over 1214: notAU & exactly-1 DISTINCT vt', {c for c in COL if notAU(c) and len(set(byC.get(c,[])))==1})
add('over 1216: exactly-1 vt hit (AU included)', {c for c in cand if len(byC.get(c,[]))==1})
add('over 1214: exactly-1 vt hit (AU included)', {c for c in COL if len(byC.get(c,[]))==1})
add('over 1214: exactly-1 DISTINCT vt (AU incl)', {c for c in COL if len(set(byC.get(c,[])))==1})
add('over 1216: notAU & backed', {c for c in cand if notAU(c) and c in byC})
# reference (a)
A={c for c in COL if dw(c+4)<=0x1000}
add('(a) 1214 & mdisp<=0x1000', A)
print()
print('=== symmetric differences against (a)=1211 ===')
for k,v in variants.items():
    print('  %-62s |diff|=%d' % (k, len(v^A)))
print()
print('=== the 2 AU classes and where they sit ===')
for c in sorted(c for c in cand if TDs[col2td[c]].startswith(b'.?AU')):
    print('  %s %s  nvt=%d  pCD=%s  in COL=%s' % (hex(c),TDs[col2td[c]].decode(),len(byC.get(c,[])),hex(dw(c+16)) if dw(c+16) else 'null', c in COL))
print()
print('=== which COLs have >1 vt hit ===')
for c,vs in byC.items():
    if len(vs)>1: print('  %s %s nvt=%d  vts=%s' % (hex(c),TDs[col2td[c]].decode(),len(vs),[hex(v) for v in vs]))
print()
print('=== what 8 extra does the auditor-1203 drop vs my 1211? trying: exclude those with duplicated TD? ===')
b={c for c in cand if notAU(c) and len(byC.get(c,[]))==1}
print('  my (b) size', len(b))
for lbl,f in [('also require lowest-VA in its TD', None)]:
    pass
bytd=collections.defaultdict(list)
for c in cand: bytd[col2td[c]].append(c)
low={t:min(cs) for t,cs in bytd.items()}
add('over 1216: notAU & 1vt & lowest-VA', {c for c in b if c==low[col2td[c]]})
hi={t:max(cs) for t,cs in bytd.items()}
add('over 1216: notAU & 1vt & highest-VA', {c for c in b if c==hi[col2td[c]]})
add('over 1216: notAU & 1vt & td-unique', {c for c in b if len(bytd[col2td[c]])==1})
json.dump({k:len(v) for k,v in variants.items()}, open('_r140/r140t.json','w'), indent=1)
