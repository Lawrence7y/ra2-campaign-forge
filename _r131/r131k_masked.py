#!/usr/bin/env python3
# R131 r131k: PROVE the "shared template expansion" claim byte-wise.
# Hypothesis: 0x6bedb0 is one instantiation of a C++ template whose ONLY per-instance
# constant is the 2nd IID pushed (0x817bc0). Test: mask exactly the two IID imm32 fields
# inside the 106-byte body and search .text for every match. Each match is an instantiation;
# read the IID it carries. Controls:
#   P1 the known second site 0x41c250 MUST be found (it differs only by IID 0x817bc0->0x817bb0)
#   P2 a copy with ONE byte flipped outside the masked fields MUST NOT be found
#   P3 masking must not swallow the whole body (masked-byte count is small & known)
import json, struct, hashlib
import pefile
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131k_masked.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
secs={}
for s in pe.sections:
    nm=s.Name.rstrip(b'\x00').decode('latin-1')
    secs[nm]=(base+s.VirtualAddress, base+s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData), s)
tlo,thi,ts=secs['.text']; data=ts.get_data()
FN=0x6bedb0; LEN=106
body=data[FN-tlo:FN-tlo+LEN]
assert body[0x21]==0x68 and body[0x4d]==0x68, (body[0x21],body[0x4d])
assert body[0x22:0x26]==bytes.fromhex('c07b8100') and body[0x4e:0x52]==bytes.fromhex('c07b8100')
MASK=[(0x22,4),(0x4e,4)]   # imm32 of the two push 0x817bc0
R={'body_len':LEN,'mask_fields':[list(m) for m in MASK],
   'body_sha':hashlib.sha256(body).hexdigest()[:16]}
def find_masked(pat, msk):
    out=[]; L=len(pat); i=0
    while i<=len(data)-L:
        if data[i] not in (pat[0],):
            i+=1; continue
        ok=True
        for j in range(L):
            if msk[j]: continue
            if data[i+j]!=pat[j]: ok=False; break
        if ok: out.append(tlo+i); i+=L
        else: i+=1
    return out
msk=bytearray(LEN)
for off,n in MASK:
    for k in range(off,off+n): msk[k]=1
R['masked_byte_count']=sum(msk)
hits=find_masked(body, msk)
R['instantiations']=[]
for h in hits:
    o=h-tlo
    iid1=struct.unpack('<I', data[o+0x22:o+0x26])[0]
    iid2=struct.unpack('<I', data[o+0x4e:o+0x52])[0]
    R['instantiations'].append({'va':hex(h),'iid1':hex(iid1),'iid2':hex(iid2),'same':iid1==iid2})
print('masked-byte count:',sum(msk),'of',LEN)
print('instantiations found:',len(hits))
for x in R['instantiations']: print('   ',x)

# callers of each instantiation (E8 rel32)
def callers(target):
    out=[]; i=0
    while True:
        i=data.find(b'\xe8', i)
        if i<0 or i+5>len(data): break
        rel=struct.unpack('<i', data[i+1:i+5])[0]
        if tlo+i+5+rel==target: out.append(tlo+i)
        i+=1
    return out
R['callers']={hex(h):[hex(x) for x in callers(h)] for h in hits}
for k,v in R['callers'].items(): print('callers',k,v)

# P1 / P2 / P3 controls
p1 = 0x41c250 in hits
mut=bytearray(body); mut[0x05]^=0xff          # flip a byte well outside the mask
p2 = len(find_masked(bytes(mut), msk))==0
p3 = sum(msk)<=12
R['P1_known_second_site_found']=p1; R['P2_flipped_byte_not_found']=p2; R['P3_mask_is_small']=p3
print('P1',p1,'P2',p2,'P3',p3)

# read the IID GUIDs used
def guid(va):
    for nm,(lo,hi,s) in secs.items():
        if lo<=va<hi:
            o=va-(base+s.VirtualAddress); d=s.get_data()
            if o<0 or o+16>min(s.SizeOfRawData,len(d)): return None
            g=d[o:o+16]; d1,d2,d3=struct.unpack('<IHH',g[:8])
            return {'str':'{%08X-%04X-%04X-%s-%s}'%(d1,d2,d3,g[8:10].hex().upper(),g[10:].hex().upper()),
                    'hex':g.hex(),'section':nm}
    return None
R['iids']={hex(v):guid(v) for v in sorted({struct.unpack('<I',data[h-tlo+0x22:h-tlo+0x26])[0] for h in hits})}
print(json.dumps(R['iids'],indent=1))
# P4: IID constants must be inside .rdata/.data, and the two distinct ones differ
p4 = len(R['iids'])>=2 and all(v and v['section'] in ('.rdata','.data') for v in R['iids'].values())
R['P4_iids_are_real_guid_consts']=p4
print('P4',p4)
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
