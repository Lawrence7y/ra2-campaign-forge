"""
S11-K2 reusable PE/capstone helper — byte-level channel, independent of function_atlas.tsv.
ImageBase 0x400000, capstone skipdata=True (R14 discipline #2).
"""
import pefile, struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
PE = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = PE.OPTIONAL_HEADER.ImageBase
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True

_SECS = []
for _s in PE.sections:
    _nm = _s.Name.rstrip(b'\0').decode('latin1')
    _SECS.append((_nm, _s.VirtualAddress, _s.Misc_VirtualSize, _s.SizeOfRawData, _s.PointerToRawData))
SEC_BY_NAME = {s[0]: s for s in _SECS}

def sections():
    return list(_SECS)

def va2off(va):
    rva = va - IMAGE_BASE
    for nm, vaoff, vsize, rsize, praw in _SECS:
        if vaoff <= rva < vaoff + max(vsize, rsize):
            return praw + (rva - vaoff)
    raise ValueError('VA 0x%X not in any section' % va)

def section_of(va):
    rva = va - IMAGE_BASE
    for nm, vaoff, vsize, rsize, praw in _SECS:
        if vaoff <= rva < vaoff + max(vsize, rsize):
            return nm
    return '?'

def in_section(va, name):
    rva = va - IMAGE_BASE
    for nm, vaoff, vsize, rsize, praw in _SECS:
        if nm == name and vaoff <= rva < vaoff + vsize:
            return True
    return False

def sec_range(name):
    nm, vaoff, vsize, rsize, praw = SEC_BY_NAME[name]
    return IMAGE_BASE+vaoff, IMAGE_BASE+vaoff+min(vsize,rsize), IMAGE_BASE+vaoff+max(vsize,rsize)

def is_code(va):
    return in_section(va, '.text')

_FILE = open(EXE, 'rb')
def rd(va, n):
    _FILE.seek(va2off(va)); return _FILE.read(n)
def u32(va): return struct.unpack('<I', rd(va,4))[0]
def u16(va): return struct.unpack('<H', rd(va,2))[0]
def u8(va):  return struct.unpack('<B', rd(va,1))[0]

def disasm(va, nbytes, stop_ret=False):
    code = rd(va, nbytes)
    out=[]
    for ins in MD.disasm(code, va):
        out.append(ins)
        if stop_ret and ins.mnemonic == 'ret': break
    return out

def fmt(ins):
    return '%08X  %-20s %-8s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)

if __name__ == '__main__':
    print('imageBase=%08X' % IMAGE_BASE)
    for n,va,vs,rs,pr in _SECS:
        print('%-10s VA=%08X VSize=%08X Raw=%08X' % (n,va,vs,rs))
