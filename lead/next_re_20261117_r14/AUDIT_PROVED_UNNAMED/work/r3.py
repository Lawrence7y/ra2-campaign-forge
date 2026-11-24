import pefile
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
raw=open(EXE,'rb').read()
secs=[(s.Name.rstrip(b'\x00').decode('latin1'),IB+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
def read(va,n):
    for n_,b,vs,pr,rs in secs:
        if b<=va<b+max(vs,rs): return raw[pr+(va-b):pr+(va-b)+n]
    return b''
def dword(va):
    b=read(va,4); return int.from_bytes(b,'little') if len(b)==4 else None
def rtti(vt):
    col=dword(vt-4); td=dword(col+0xC) if col else None
    return read(td+8,120).split(b'\x00')[0] if td else None
for v in (0x7ed0a4,):
    print(hex(v), rtti(v))
