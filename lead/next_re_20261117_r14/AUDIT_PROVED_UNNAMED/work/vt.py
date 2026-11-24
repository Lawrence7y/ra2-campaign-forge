
import pefile,struct
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(EXE,fast_load=True); IB=pe.OPTIONAL_HEADER.ImageBase
raw=open(EXE,'rb').read()
secs=[(s.Name.rstrip(b'\x00').decode('latin1'),IB+s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData) for s in pe.sections]
RD=[s for s in secs if s[0]=='.rdata'][0]
def read(va,n):
    for n_,b,vs,pr,rs in secs:
        if b<=va<b+max(vs,rs): return raw[pr+(va-b):pr+(va-b)+n]
    return b''
def dword(va):
    b=read(va,4); return int.from_bytes(b,'little') if len(b)==4 else None
def rtti(vt):
    col=dword(vt-4)
    if not col or not (0x7e0000<=col<0x840000): return None
    td=dword(col+0xC)
    if not td or not (0x400000<=td<0x900000): return None
    s=read(td+8,120).split(b'\x00')[0]
    return s.decode('latin1') if s else None
def find_vt(entry):
    """find vtable(s) in .rdata containing this entry as a slot; return [(table_start, slot, name)]"""
    out=[]
    pat=struct.pack('<I',entry)
    base=RD[1]; start=RD[3]; ln=RD[4]
    i=0
    while True:
        j=raw.find(pat, start+i, start+ln-3)
        if j<0: break
        va=RD[1]+(j-RD[3])
        # walk back
        s=va
        while True:
            prev=dword(s-4)
            if prev and 0x401000<=prev<0x7e038d: s-=4
            else: break
        # walk forward
        e=va+4
        while True:
            nx=dword(e)
            if nx and 0x401000<=nx<0x7e038d: e+=4
            else: break
        nm=rtti(s)
        out.append((hex(s), (va-s)//4, nm, (e-s)//4))
        i=j-start+1
    return out
import sys
for a in sys.argv[1:]:
    e=int(a,16)
    print(a, find_vt(e)[:6])
