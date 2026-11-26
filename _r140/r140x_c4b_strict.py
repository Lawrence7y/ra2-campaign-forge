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
def intext(va): return va is not None and sec_of(va-IB)=='.text'
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
allrefs=collections.defaultdict(list)
for nm,va,vs,raw,rs in secs:
    blob=data[raw:raw+rs]
    for i in range(len(blob)//4):
        v=struct.unpack_from('<I',blob,i*4)[0]
        if v in cand:
            vt=IB+va+i*4+4
            if dw(vt-4)==v: allrefs[v].append((nm,vt))
A=1
def chk(n,c,x=''):
    global A
    print('  %s %-70s %s'%('PASS' if c else 'FAIL',n,x)); assert c,n; A+=1
notAU=lambda c: not TDs[col2td[c]].startswith(b'.?AU')
def count(pred):
    return {c for c in cand if notAU(c) and sum(1 for s,vt in allrefs.get(c,[]) if pred(s,vt))==1}
print('=== C4(b) under six vtable-validity predicates ===')
res={}
for name,pred in [
 ('P0 any dword hit (auditor)',      lambda s,vt: True),
 ('P1 vt in .data/.rdata (mine)',    lambda s,vt: s in ('.data','.rdata')),
 ('P2 vt in .rdata only',            lambda s,vt: s=='.rdata'),
 ('P3 slot0 in .text',               lambda s,vt: intext(dw(vt))),
 ('P4 slot0 in .text AND in data',   lambda s,vt: s in ('.data','.rdata') and intext(dw(vt))),
 ('P5 slot0 in .text AND .rdata',    lambda s,vt: s=='.rdata' and intext(dw(vt))),
]:
    s=count(pred); res[name]=len(s)
    print('  %-34s -> %d %s' % (name,len(s),'  <<< 1211' if len(s)==1211 else ('  <<< 1212' if len(s)==1212 else ('  <<<1203' if len(s)==1203 else ''))))
print()
A_set={c for c in COL if dw(c+4)<=0x1000}
print('  (a) mdisp<=0x1000 -> %d' % len(A_set))
print()
print('=== which predicate is CORRECT? test every ref of a few classes ===')
def classify(c):
    out=[]
    for s,vt in allrefs.get(c,[]):
        out.append('%s vt=%s slot0=%s(%s) data=%s slot0text=%s' % (s,hex(vt),hex(dw(vt)) if dw(vt) else None,
                    sec_of(dw(vt)-IB) if dw(vt) and dw(vt)>=IB else 'na', s in ('.data','.rdata'), intext(dw(vt))))
    return out
for c in (0x800040, 0x7fffb8, 0x806808):
    print(' COL %s %s' % (hex(c),TDs[col2td[c]].decode()))
    for l in classify(c): print('    ',l)
print()
print('=== decisive: DropPod 0x800040 has 5 data-section refs but only 1 with slot0 in .text ===')
dp=0x800040
n_all=len(allrefs[dp]); n_slot0=sum(1 for s,vt in allrefs[dp] if intext(dw(vt)))
print('  refs=%d  with slot0 in .text=%d' % (n_all,n_slot0))
chk('P4 (slot0 in .text) says DropPod has exactly 1 vtable; P1 says 5', n_slot0==1 and n_all==5)
print()
print('=== FINAL VERDICT on C4(b) ===')
p4=count(lambda s,vt: s in ('.data','.rdata') and intext(dw(vt)))
p3=count(lambda s,vt: intext(dw(vt)))
print('  under the strictest defensible vtable definition (P4), (b) =', len(p4))
print('  under P3 (slot0 in .text, any ref section), (b) =', len(p3))
print('  (a) =', len(A_set))
print('  |P4 ^ a| =', len(p4^A_set), ' |P3 ^ a| =', len(p3^A_set))
for nm,s in (('P4',p4),('P3',p3)):
    print('  %s vs (a): both-1211? %s ; same set? %s' % (nm, len(s)==1211, s==A_set))
json.dump(res, open('_r140/r140x.json','w'), indent=1)
print('TOTAL ASSERTIONS: %d PASS' % (A-1))
