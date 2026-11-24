
import pefile
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
raw=open(EXE,'rb').read()
secs=[(s.Name.rstrip(b'\x00').decode('latin1'),IB+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def va_of(off):
    for n,b,vs,pr,rs in secs:
        if pr<=off<pr+rs: return b+(off-pr)
def read(va,n):
    for n_,b,vs,pr,rs in secs:
        if b<=va<b+max(vs,rs): return raw[pr+(va-b):pr+(va-b)+n]
    return b''
for pat in (b'FOG.SHP', b'FOG', b'fog.shp'):
    i=0; hits=[]
    while True:
        j=raw.find(pat,i)
        if j<0: break
        hits.append((hex(va_of(j)), j)); i=j+1
    print(pat, len(hits), hits[:10])
for va in (0x81ce18,0x81ce10,0x82fd30,0x82fd40,0x82ffe4,0x82fff4):
    b=read(va,40); print(hex(va), b[:40])
