
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
    col=dword(vt-4)
    if not col: return None
    td=dword(col+0xC)
    if not td: return None
    s=read(td+8,120).split(b'\x00')[0]
    return s.decode('latin1') if s else None
for v in (0x7ece34,0x7ecd68,0x7ecd44,0x7f2ec0,0x7f2ea4,0x7f2e9c,0x7f2e94,0x7e4dd8,0x7efe44,0x7e3354,0x7ee6c8,0x7ee7e4,0x7ee7f4,0x7f0904,0x7e2000,0x7e4dd8):
    print(hex(v), rtti(v))
