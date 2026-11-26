import struct, re, json
from collections import Counter
import pefile
data=open('ra2bench/gamemd.exe','rb').read()
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
    if o is None or o+4>len(data): return None
    return struct.unpack_from('<I',data,o)[0]
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8:g for s,g in strings if dw(s-8) is not None and dw(s-4)==0 and sec_of(dw(s-8)-IB) in ('.data','.rdata')}
tdset=set(TDs)
cols=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset:
                c=IB+va+i*4-12
                if dw(c)==0 and dw(c+12)==v: cols.append((c,v))
colset={c for c,_ in cols}; col2td={c:t for c,t in cols}
print('COL', len(colset))
stat=Counter(); bad=[]
for c,td in cols:
    pcd=dw(c+16)
    if pcd is None: stat['pcd_null']+=1; bad.append((c,'null')); continue
    if sec_of(pcd-IB) not in ('.data','.rdata'): stat['pcd_out']+=1; bad.append((c,'outsec')); continue
    stat['pcd_in']+=1
print(stat, [(hex(c),r) for c,r in bad])
inimg=[c for c,_ in cols if dw(c+16) is not None and sec_of(dw(c+16)-IB) in ('.data','.rdata')]
print('in-image pCD count', len(inimg))
print('CHD signature hist:', Counter(dw(dw(c+16)) for c in inimg))
print('numBaseClasses hist:', sorted(Counter(dw(dw(c+16)+8) for c in inimg).items())[:10])
bca_ok=[c for c in inimg if dw(dw(c+16)+12) is not None and sec_of(dw(dw(c+16)+12)-IB) in ('.data','.rdata')]
print('BCA in-image:', len(bca_ok))
def chain(c, td):
    pcd=dw(c+16)
    if pcd is None: return False
    bca=dw(pcd+12)
    if bca is None: return False
    bcd=dw(bca)
    if bcd is None: return False
    return dw(bcd)==td and dw(bcd+24)==c
ok=[c for c,_ in cols if chain(c, col2td[c])]
print('BCD chain ok:', len(ok))
ok2=[c for c,_ in cols if dw(c+16) is not None and dw(dw(c+16)) is not None and dw(dw(dw(c+16)+12)) is not None and dw(dw(dw(c+16)+12))==col2td[c]]
print('BCD td-match only:', len(ok2))
c0=next(c for c,_ in cols if dw(c+16) is not None and sec_of(dw(c+16)-IB) in ('.data','.rdata'))
pcd=dw(c0+16)
print('example COL', hex(c0), TDs[col2td[c0]].decode())
print('  COL dwords:', [hex(dw(c0+4*i)) for i in range(5)])
print('  pCD', hex(pcd), 'CHD dwords:', [hex(dw(pcd+4*i)) for i in range(4)])
bca=dw(pcd+12); print('  BCA', hex(bca), 'entries:', [hex(dw(bca+4*i)) for i in range(3)])
bcd=dw(bca); print('  BCD', hex(bcd), 'dwords:', [hex(dw(bcd+4*i)) for i in range(8)])
json.dump({'col':len(colset),'inimg':len(inimg),'chain':len(ok)}, open('_r140/r140e.json','w'))
