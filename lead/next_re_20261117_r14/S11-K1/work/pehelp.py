"""
S11-K1 reusable PE/capstone helper -- byte-level channel, independent of function_atlas.tsv.
VA->file offset via pefile; read dwords; linear capstone disasm with skipdata=True (R14 discipline #2).
boundary_check returns 'unknown' on span>=max_bytes (discipline #3 / R14_COMMON §8.1-6).
"""
import pefile
import struct
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
PE = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = PE.OPTIONAL_HEADER.ImageBase
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True  # R14 discipline #2: never silently stop on undecodable bytes

_SECS = []
for _s in PE.sections:
    _nm = _s.Name.rstrip(b'\0').decode('latin1')
    _SECS.append((_nm, _s.VirtualAddress, _s.Misc_VirtualSize, _s.SizeOfRawData,
                  _s.PointerToRawData))

def sections():
    return list(_SECS)

def va2off(va):
    rva = va - IMAGE_BASE
    for nm, vaoff, vsize, rsize, praw in _SECS:
        if vaoff <= rva < vaoff + max(vsize, rsize):
            off = praw + (rva - vaoff)
            return off
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

def is_code(va):
    try:
        return in_section(va, '.text')
    except Exception:
        return False

_FILE = open(EXE, 'rb')

def rd(va, n):
    _FILE.seek(va2off(va))
    return _FILE.read(n)

def u32(va):
    return struct.unpack('<I', rd(va, 4))[0]

def u16(va):
    return struct.unpack('<H', rd(va, 2))[0]

def u8(va):
    return struct.unpack('<B', rd(va, 1))[0]

def disasm(va, nbytes, stop_ret=False):
    """Linear disasm from va; returns list of capstone insns (skipdata=True)."""
    code = rd(va, nbytes)
    out = []
    for ins in MD.disasm(code, va):
        out.append(ins)
        if stop_ret and ins.mnemonic == 'ret':
            break
    return out

def ins_boundaries(va, nbytes):
    return {i.address for i in disasm(va, nbytes)}

def fmt(ins):
    return '%08X  %-24s %-8s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)

def boundary_check(target, base, span_bytes, max_bytes, boundaries):
    """Return 'unknown' if span>=max_bytes (no verdict), else True if target in boundaries."""
    if span_bytes >= max_bytes:
        return 'unknown'
    return target in boundaries

if __name__ == '__main__':
    print('imageBase=%08X' % IMAGE_BASE)
    for nm, vaoff, vsize, rsize, praw in _SECS:
        print('%-10s VA=%08X VSize=%08X Raw=%08X PtrRaw=%08X' % (nm, vaoff, vsize, rsize, praw))
