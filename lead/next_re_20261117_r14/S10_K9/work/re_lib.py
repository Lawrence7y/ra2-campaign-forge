
from pathlib import Path
import pefile, capstone, struct
ROOT=Path(r'D:\Project\ra2-campaign-forge')
EXE=ROOT/'ra2youli/gamemd.exe'
PE=pefile.PE(str(EXE),fast_load=False)
BASE=PE.OPTIONAL_HEADER.ImageBase
MD=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
MD.detail=True
MD.skipdata=True

def sections():
    out=[]
    for s in PE.sections:
        out.append((s.Name.rstrip(b'\0').decode(errors='replace'),BASE+s.VirtualAddress,s.Misc_VirtualSize,s.SizeOfRawData,s.PointerToRawData))
    return out

def off(va):
    rva=va-BASE
    for s in PE.sections:
        if s.VirtualAddress<=rva<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            o=s.PointerToRawData+(rva-s.VirtualAddress)
            if o<s.PointerToRawData+s.SizeOfRawData:return o
    raise KeyError(hex(va))

def read(va,n):
    o=off(va); return PE.__data__[o:o+n]

def u32(va): return struct.unpack('<I',read(va,4))[0]

def i32(va): return struct.unpack('<i',read(va,4))[0]

def dis(va,n=None,stop_ret=False):
    if n is None:
        # until .text section end
        n=0x20000
    data=read(va,n)
    lines=[]
    for ins in MD.disasm(data,va):
        lines.append(f'{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}')
        if stop_ret and ins.mnemonic.startswith('ret'):break
    return '\n'.join(lines)

def cstring(va,n=256):
    b=read(va,n); z=b.find(b'\0'); return b[:z if z>=0 else len(b)].decode('latin1')

def xrefs32(target,section_name='.text'):
    hits=[]
    pat=struct.pack('<I',target)
    for name,va,vsz,rsz,ptr in sections():
        if name!=section_name:continue
        data=PE.__data__[ptr:ptr+rsz]
        pos=0
        while True:
            i=data.find(pat,pos)
            if i<0:break
            hits.append(va+i);pos=i+1
    return hits
