# S13-K9 common: PE loader + address helpers (self-written)
import struct, pefile
BIN=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe=pefile.PE(BIN, fast_load=True)
IB=pe.OPTIONAL_HEADER.ImageBase
DATA=open(BIN,'rb').read()
SECS=[]
for s in pe.sections:
    SECS.append((s.Name.rstrip(b'\x00').decode(errors='replace'),s.VirtualAddress,s.Misc_VirtualSize,s.PointerToRawData,s.SizeOfRawData))

def rva2off(rva):
    for n,va,vs,pr,rs in SECS:
        if va<=rva<va+max(vs,rs):
            o=pr+(rva-va)
            if o<len(DATA): return o
    return None

def va2off(va): return rva2off(va-IB)

def rd(va,n):
    o=va2off(va)
    if o is None: return None
    return DATA[o:o+n]

def u32(va):
    b=rd(va,4)
    return struct.unpack('<I',b)[0] if b and len(b)==4 else None

def u8(va):
    b=rd(va,1)
    return b[0] if b else None

def sec_of(va):
    r=va-IB
    for n,v,vs,pr,rs in SECS:
        if v<=r<v+max(vs,rs): return n
    return None

def in_text(va):
    return sec_of(va)=='.text'

# section containing .text range
def text_range():
    for n,v,vs,pr,rs in SECS:
        if n=='.text': return (IB+v, IB+v+min(vs,rs))
    return None
