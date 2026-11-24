"""
W164 reusable PE reader (byte-level channel, independent of function_atlas.tsv).
VA->file offset via pefile; read dwords; linear capstone disasm with skipdata=True.
"""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_REG, X86_OP_IMM
import struct, sys

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
PE = pefile.PE(EXE, fast_load=True)
IMAGE_BASE = PE.OPTIONAL_HEADER.ImageBase
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True  # R12 discipline: never silently stop on undecodable bytes

def va2off(va):
    rva = va - IMAGE_BASE
    for s in PE.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError('VA 0x%X not in any section' % va)

def section_of(va):
    rva = va - IMAGE_BASE
    for s in PE.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.rstrip(b'\0').decode('latin1')
    return '?'

def rd(va, n):
    o = va2off(va)
    with open(EXE, 'rb') as f:
        f.seek(o); return f.read(n)

def u32(va):
    return struct.unpack('<I', rd(va, 4))[0]

def disasm(va, nbytes, stop_ret=False):
    """Linear disasm from va; yields (addr, mnemonic, op_str, bytes)."""
    code = rd(va, nbytes)
    out = []
    for ins in MD.disasm(code, va):
        out.append(ins)
        if stop_ret and (ins.mnemonic == 'ret' or ins.mnemonic.startswith('retf')):
            break
    return out

def ins_boundaries(va, nbytes):
    """Set of addresses that ARE instruction boundaries when linearly disassembled from va."""
    return {i.address for i in disasm(va, nbytes)}

def fmt(ins):
    return '%08X  %-24s %-8s %s' % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)

if __name__ == '__main__':
    print('imageBase=%08X' % IMAGE_BASE)
    for va in [0x7E7F7C, 0x7E7EB0, 0x7E7E8C]:
        print('%08X %s' % (va, section_of(va)))
