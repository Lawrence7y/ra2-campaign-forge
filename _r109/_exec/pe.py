import pefile, struct, bisect
IB=0x400000
PATH='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
_pe=pefile.PE(PATH)
_img=open(PATH,'rb').read()
SECS=[]
for s in _pe.sections:
    nm=s.Name.decode().rstrip('\0')
    va=s.VirtualAddress+IB
    vsize=s.Misc_VirtualSize
    raw=s.PointerToRawData
    rsize=s.SizeOfRawData
    SECS.append(dict(name=nm, va=va, vsize=vsize, vend=va+vsize,
                     raw=raw, rsize=rsize,
                     delta=raw-va,                       # file_off = va + delta
                     rdelta=va-raw))                     # va = file_off + rdelta
BLOCK=b'\0'*0x400
def foff(va):
    for s in SECS:
        if s['va']<=va<s['vend']: return va+s['delta']
    return None
def rd(va,n):
    o=foff(va)
    if o is None or o+n>len(_img): return None
    return _img[o:o+n]
def u32(va):
    b=rd(va,4)
    return struct.unpack('<I',b)[0] if b else None
def u16(va):
    b=rd(va,2)
    return struct.unpack('<H',b)[0] if b else None
TEXT_LO,TEXT_HI=0x401000,0x7e1000
def in_text(va): return va is not None and TEXT_LO<=va<TEXT_HI
