#!/usr/bin/env python3
"""Independent re_lib for S10-K6: read-only PE/RTTI/disassembly helpers."""
from pathlib import Path
import struct, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG
ROOT = Path(r'D:\Project\ra2-campaign-forge')
EXE = ROOT / 'ra2youli' / 'gamemd.exe'
PE = pefile.PE(str(EXE), fast_load=True)
IB = PE.OPTIONAL_HEADER.ImageBase
def sections(): return PE.sections
def va_to_off(va):
    va=int(va)&0xffffffff
    for s in PE.sections:
        b=s.VirtualAddress+IB
        if b<=va<b+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+(va-b)
    raise KeyError(hex(va))
def read(va,n):
    o=va_to_off(va)
    with EXE.open('rb') as f: f.seek(o); return f.read(n)
def u16(va): return struct.unpack('<H',read(va,2))[0]
def u32(va): return struct.unpack('<I',read(va,4))[0]
def i32(va): return struct.unpack('<i',read(va,4))[0]
def cstr(va,n=512):
    b=read(va,n); return b.split(b'\0',1)[0].decode('latin1')
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.skipdata=True; MD.detail=True
def disasm(va,count=200,stop_ret=True,max_bytes=8192):
    out=[]
    for i in MD.disasm(read(va,max_bytes),va):
        out.append(i)
        if len(out)>=count: break
        if stop_ret and (i.mnemonic=='ret' or i.mnemonic.startswith('ret ')): break
    return out
def fmt(i): return f'{i.address:08X}  {i.bytes.hex(" "):<24s}  {i.mnemonic} {i.op_str}'.rstrip()
def block(va,**kw): return '\n'.join(fmt(i) for i in disasm(va,**kw))
def dump(va,n=128):
    b=read(va,n)
    return '\n'.join(f'{va+j:08X}  '+' '.join(f'{x:02X}' for x in b[j:j+16]) for j in range(0,len(b),16))
def rtti_from_col(col):
    sig=u32(col); off,cdoff,td=struct.unpack('<iii',read(col+4,12))
    if sig not in (0,1) or abs(off)>0x10000 or abs(cdoff)>0x10000: return None
    try:
        nm_va=td+8; nm=cstr(nm_va,256)
        if nm.startswith('.?AV') and nm.endswith('@@'): return td,nm
    except Exception: pass
    return None
def vtable_at(vtobj):
    try: col=u32(vtobj-4)
    except Exception: return None,None
    r=rtti_from_col(col)
    return (col,r) if r else (None,None)
def find_dword_refs(value,limit=20000,aligned=1):
    hits=[]
    for s in PE.sections:
        if not (s.Characteristics & 0x40000040): continue
        base=IB+s.VirtualAddress; raw=s.PointerToRawData
        n=min(s.SizeOfRawData,s.Misc_VirtualSize or s.SizeOfRawData)
        if n<=0 or raw<=0: continue
        data=read(base,n)
        start=(-base)%aligned if aligned>1 else 0
        for j in range(start,len(data)-3,aligned):
            if struct.unpack_from('<I',data,j)[0]==value:
                hits.append(base+j)
                if len(hits)>=limit: return hits
    return hits
def find_vtable_containing(func_va,max_back=128):
    found=[]
    for ref in find_dword_refs(func_va):
        best=None
        for p in range(ref-4,max(0,ref-4*max_back)-1,-4):
            try: col=u32(p)
            except Exception: continue
            r=rtti_from_col(col)
            if r:
                best=(p+4,col,r,(ref-(p+4))//4); break
        found.append((ref,best))
    return found
def section_of(va):
    for s in PE.sections:
        b=IB+s.VirtualAddress
        if b<=va<b+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.Name.decode('latin1').rstrip('\0')
    return '?'
def is_code(va): return section_of(va)=='.text'
