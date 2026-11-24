
import struct, pefile
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
blob=open(EXE,'rb').read()
pe=pefile.PE(EXE,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
for s in pe.sections:
    print(s.Name.rstrip(b'\x00'), hex(s.VirtualAddress+base), 'vsize',hex(s.Misc_VirtualSize),'rawsize',hex(s.SizeOfRawData),'rawptr',hex(s.PointerToRawData))
S={}
for s in pe.sections: S[s.Name.rstrip(b'\x00').decode('latin1')]=(s.VirtualAddress+base,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData)
va,vs,pr,rs=S['.rdata']
rd=blob[pr:pr+rs]
print('rd len',len(rd),'vs',vs)
lo,hi=va,va+len(rd)
def d32(a):
    o=a-lo
    if o<0 or o+4>len(rd): return None
    return struct.unpack_from('<I',rd,o)[0]
cand=0; colok=0; tdok=0; named=0
samples=[]
for a in range(lo,hi-8,4):
    v=d32(a)
    if v is None or not (lo<=v<hi): continue
    cand+=1
    td=d32(v+0xC)
    if td is None or not (lo<=td<hi): continue
    colok+=1
    o=td+8-lo
    if o<0 or o>=len(rd): continue
    e=rd.find(b'\x00',o,o+120)
    if e<0: continue
    nm=rd[o:e]
    if not nm.startswith(b'.?A'): continue
    named+=1
    if len(samples)<5: samples.append((hex(a),hex(v),hex(td),nm[:60]))
print('cand',cand,'colok',colok,'named',named)
print(samples)
# try known COL from docs: 0x7FC618 (BuildingTypeClass)
for va_try in (0x7FC618,0x7E3EBC):
    o=va_try-lo
    if 0<=o<len(rd):
        print(hex(va_try), 'dword=', [hex(struct.unpack_from('<I',rd,o+4*k)[0]) for k in range(4)])
