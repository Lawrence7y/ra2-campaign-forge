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
    o=rva2off(va-IB)
    if o is None or o+4>len(data): return None
    return struct.unpack_from('<I',data,o)[0]
pat=re.compile(rb'\.\?A[VU][!-~]{1,200}?@@')
strings=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        for m in pat.finditer(data[raw:raw+rs]): strings.append((IB+va+m.start(), m.group()))
TDs={s-8 for s,_ in strings if dw(s-8) is not None and dw(s-4)==0 and sec_of(dw(s-8)-IB) in ('.data','.rdata')}
tdset=TDs
refs=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in tdset: refs.append((IB+va+i*4, v))
cols=[]
for r,td in refs:
    c=r-12
    if dw(c)==0 and dw(c+12)==td: cols.append((c,td))
colset={c for c,_ in cols}
vtrefs=[]
for nm,va,vs,raw,rs in secs:
    if nm in ('.data','.rdata'):
        blob=data[raw:raw+rs]
        for i in range(len(blob)//4):
            v=struct.unpack_from('<I',blob,i*4)[0]
            if v in colset:
                vt=IB+va+i*4+4
                if dw(vt-4)==v: vtrefs.append((vt,v))
backed={t for _,t in vtrefs}
print('COL=%d backed=%d vt=%d' % (len(colset),len(backed),len(vtrefs)))
md=Counter(dw(c+4) for c,_ in cols)
print('mdisp hist:', sorted(md.items()))
print('mdisp<=0x40:', sum(v for k,v in md.items() if k<=0x40), ' mdisp<=0x100:', sum(v for k,v in md.items() if k<=0x100))
# CHD validation at pCD
def chd_ok(pcd):
    if pcd is None or dw(pcd) is None: return False
    if dw(pcd)!=1: return False
    nb=dw(pcd+8)
    if nb is None or nb<1: return False
    bca=dw(pcd+12)
    if bca is None or sec_of(bca-IB) not in ('.data','.rdata'): return False
    return True
chd_okset={c for c,td in cols if dw(c+16) is not None and chd_ok(dw(c+16))}
print('CHD-valid COL:', len(chd_okset), 'backed:', len(chd_okset&backed))
# BCD chain: BCA[0] -> BCD ; BCD+0 == td ; BCD+24 == COL
def bcd_chain_ok(c, td):
    pcd=dw(c+16)
    if pcd is None: return False
    bca=dw(pcd+12)
    if bca is None: return False
    bcd=dw(bca)
    if bcd is None: return False
    return dw(bcd)==td and dw(bcd+24)==c
ok_set={c for c,td in cols if bcd_chain_ok(c,td)}
print('BCD-chain-valid COL:', len(ok_set), 'backed:', len(ok_set&backed))
# relaxed: BCD+0==td only
ok2={c for c,td in cols if (dw(c+16) is not None and dw(dw(dw(c+16)+12)) is not None and dw(dw(dw(c+16)+12))==td)}
print('BCD td-match COL:', len(ok2), 'backed:', len(ok2&backed))
# vtable validity: all entries in image or zerofill .data, require vt in .rdata
vt_img={v for v,t in vtrefs if sec_of(v-IB) in ('.data','.rdata')}
print('vt in image:', len(vt_img))
# backed restricted to CHD-valid
print('---')
print('TARGET F01: 1211 / 1201')
def rep(n,a,b): print('%-40s col=%-5d backed=%-5d %s' % (n,a,b,'<== MATCH' if (a,b)==(1211,1201) else ''))
rep('base', len(colset), len(backed))
rep('pCD nonzero', len({c for c,_ in cols if dw(c+16)}), len({c for c,_ in cols if dw(c+16)}&backed))
rep('CHD ok', len(chd_okset), len(chd_okset&backed))
rep('BCD chain ok', len(ok_set), len(ok_set&backed))
rep('BCD td-match', len(ok2), len(ok2&backed))
rep('mdisp<=0x40', len({c for c,_ in cols if dw(c+4)<=0x40}), len({c for c,_ in cols if dw(c+4)<=0x40}&backed))
# distinct by name string
names=Counter()
for c,td in cols: names[td]+=1
print('TD->COL count hist:', sorted(Counter(names.values()).items()))
json.dump({'col':len(colset),'backed':len(backed),'vt':len(vtrefs)},open('_r140/r140c.json','w'))
