"""Self-contained PE + capstone helpers for S13-KPROVED2.
Not imported from any other card. Uses pefile + capstone 5.0.7.
"""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = pe.get_data

def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

def section_of(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s
    return None

TEXT_VA = IB + pe.sections[0].VirtualAddress
TEXT_VS = pe.sections[0].Misc_VirtualSize
TEXT_END = TEXT_VA + TEXT_VS

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True

def u32(va):
    o = va2off(va)
    if o is None:
        return None
    b = DATA(o, 4)
    if len(b) < 4:
        return None
    return int.from_bytes(b, 'little')

def disasm_range(lo, hi):
    o = va2off(lo)
    if o is None:
        return []
    size = hi - lo
    if size <= 0:
        return []
    return list(MD.disasm(DATA(o, size), lo))
