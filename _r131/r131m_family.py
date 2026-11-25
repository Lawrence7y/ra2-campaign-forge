#!/usr/bin/env python3
# R131 r131m: family-robust instantiation census.
# The wrapper body has 106 bytes; between two instantiations the ONLY differing byte is 0x4e
# (low byte of the 2nd IID imm32). To census the WHOLE family (not just this one shape),
# mask every field that is legitimately per-instance or displacement-dependent:
#   - both IID imm32s                       (2 x 4 bytes)
#   - the jz/jl rel8 displacements          (4 x 1 byte)
# Everything else must match byte-for-byte. Controls:
#   P1 must find both known instantiations
#   P2 flipping one non-masked byte must find 0
#   P3 mask width must be <= 12 bytes of 106
import json, struct, hashlib
import pefile
EXE='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r131/r131m_family.json'
pe=pefile.PE(EXE, fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
ts=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
tlo=base+ts.VirtualAddress; data=ts.get_data()
FN=0x6bedb0; LEN=106
body=bytearray(data[FN-tlo:FN-tlo+LEN])
REL8=[0x09,0x17,0x36,0x47]          # jz/jl rel8 displacements: 7406@0x08 7452@0x16 7c4c@0x35 7c11@0x46
IID32=[(0x22,4),(0x4e,4)]
msk=bytearray(LEN)
for o in REL8: msk[o]=1
for o,n in IID32:
    for k in range(o,o+n): msk[k]=1
R={'len':LEN,'rel8_offsets':REL8,'iid32':IID32,'masked':sum(msk),
   'body_sha':hashlib.sha256(bytes(body)).hexdigest()[:16]}
# sanity: the offsets we mask must really be those instructions' bytes
assert body[0x08]==0x74 and body[0x16]==0x74 and body[0x35]==0x7c and body[0x46]==0x7c
def scan(pat, m, start=0):
    out=[]; L=len(pat); i=start
    while i<=len(data)-L:
        ok=True
        for j in range(L):
            if m[j]: continue
            if data[i+j]!=pat[j]: ok=False; break
        if ok: out.append(tlo+i); i+=L
        else: i+=1
    return out
hits=scan(bytes(body), msk)
R['instantiations']=[hex(h) for h in hits]
print('masked bytes: %d / %d'%(sum(msk),LEN))
print('family instantiations:',len(hits),R['instantiations'])
def callers(target):
    out=[]; i=0
    while True:
        i=data.find(b'\xe8',i)
        if i<0 or i+5>len(data): break
        rel=struct.unpack('<i',data[i+1:i+5])[0]
        if tlo+i+5+rel==target: out.append(tlo+i)
        i+=1
    return out
def guidat(va):
    for s in pe.sections:
        lo=base+s.VirtualAddress; hi=lo+max(s.Misc_VirtualSize,s.SizeOfRawData)
        if lo<=va<hi:
            o=va-lo; d=s.get_data()
            if o+16>len(d): return None
            g=d[o:o+16]; a,b,c=struct.unpack('<IHH',g[:8])
            return '{%08X-%04X-%04X-%s-%s}'%(a,b,c,g[8:10].hex().upper(),g[10:].hex().upper())
    return None
R['detail']=[]
for h in hits:
    o=h-tlo
    iid1=struct.unpack('<I', data[o+0x22:o+0x26])[0]
    iid2=struct.unpack('<I', data[o+0x4e:o+0x52])[0]
    d={'va':hex(h),'iid1':hex(iid1),'iid2':hex(iid2),
       'iid1_guid':guidat(iid1),'iid2_guid':guidat(iid2),
       'callers':[hex(x) for x in callers(h)]}
    R['detail'].append(d)
    print('  %s  iid1=%s %s'%(d['va'],d['iid1'],d['iid1_guid']))
    print('        iid2=%s %s  callers=%d %s'%(d['iid2'],d['iid2_guid'],len(d['callers']),d['callers']))
R['total_callers']=sum(len(d['callers']) for d in R['detail'])
print('total call sites across family:',R['total_callers'])
# P2: flip a non-masked byte
mut=bytearray(body); mut[0x05]^=0xff
R['P2_flipped_copies']=len(scan(bytes(mut),msk))
# P3
R['P3_mask_ok']=sum(msk)<=12
print('P2 flipped-byte copies:',R['P2_flipped_copies'],'P3',R['P3_mask_ok'])
# raw-only exact-body copies (reference for R130's claim)
R['exact_copies']=data.count(bytes(body))
print('exact 106-byte copies:',R['exact_copies'])
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1)
