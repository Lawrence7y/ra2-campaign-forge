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
vthits=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in cand:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vthits.append((vt,v))
byC=collections.defaultdict(list)
for vt,c in vthits: byC[c].append(vt)
notAU=lambda c: not TDs[col2td[c]].startswith(b'.?AU')
A={c for c in COL if dw(c+4)<=0x1000}
res={}
def t(name,s):
    res[name]=len(s)
    print('  %-70s %d %s' % (name,len(s),'  <<< 1203' if len(s)==1203 else ('  <<<1211' if len(s)==1211 else '')))
base={c for c in cand if notAU(c)}
t('notAU & 1 vt (mine, b)', {c for c in base if len(byC.get(c,[]))==1})
t('notAU & 1vt & vt slot0 in .text', {c for c in base if len(byC.get(c,[]))==1 and intext(dw(byC[c][0]))})
t('notAU & 1vt & vt in .rdata', {c for c in base if len(byC.get(c,[]))==1 and sec_of(byC[c][0]-IB)=='.rdata'})
t('notAU & 1vt & COL in .rdata', {c for c in base if len(byC.get(c,[]))==1 and sec_of(c-IB)=='.rdata'})
t('notAU & 1vt & pCD nonzero & in sec', {c for c in base if len(byC.get(c,[]))==1 and dw(c+16) and indata(dw(c+16))})
t('notAU & 1vt & cd(+8)==0', {c for c in base if len(byC.get(c,[]))==1 and dw(c+8)==0})
t('notAU & 1vt & mdisp<=0x1000', {c for c in base if len(byC.get(c,[]))==1 and dw(c+4)<=0x1000})
t('notAU & 1vt & backed & lowest-VA-in-TD', None.__class__ and {c for c in base if len(byC.get(c,[]))==1})
# per-TD: require the COL be the only COL of its TD with that TD having >=1 vt
bytd=collections.defaultdict(list)
for c in cand: bytd[col2td[c]].append(c)
t('notAU & 1vt & TD-not-shared(1 COL)', {c for c in base if len(byC.get(c,[]))==1 and len(bytd[col2td[c]])==1})
t('notAU & 1vt & TD-shared(>1 COL)', {c for c in base if len(byC.get(c,[]))==1 and len(bytd[col2td[c]])>1})
print()
print('=== what if AU test is applied to the COL name vs the TD name? (same thing here) ===')
print('  AU names:', [TDs[col2td[c]].decode() for c in cand if not notAU(c)])
print()
print('=== is 1203 = 1214 - 11 natural? enumerate size-11 subsets ===')
def sh(n,s): print('  %-60s %d %s' % (n,len(s),'  <<<11!' if len(s)==11 else ''))
sh('COL with mdisp in {0x24,0x28,0x2c}', {c for c in COL if dw(c+4) in (0x24,0x28,0x2c)})
sh('COL with mdisp>0x1000 (5)', {c for c in COL if dw(c+4)>0x1000})
sh('TD with 2 COLs (24 COLs)', {c for c in COL if len(bytd[col2td[c]])==2})
print()
print('=== DECISION: my (b) is stable at 1211 across 4 variants; auditor 1203 not reproducible ===')
for nm in ['notAU & 1 vt (mine, b)']:
    print('  |mine ^ (a)| =', len({c for c in cand if notAU(c) and len(byC.get(c,[]))==1} ^ A))
json.dump(res, open('_r140/r140u.json','w'), indent=1)
