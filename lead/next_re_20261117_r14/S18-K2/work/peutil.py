#!/usr/bin/env python3
"""S18-K2 PE + capstone helper. Independent of function_atlas.tsv.
Provides: VA->file offset, byte reads, boundary-checked disassembly, sweep calls/jmps.
"""
import pefile
from capstone import *
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories()
DATA = pe.__data__
SECTIONS = []
for s in pe.sections:
    SECTIONS.append((s.VirtualAddress, s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData),
                     s.PointerToRawData, s.SizeOfRawData, s.Name.rstrip(b'\x00').decode('ascii', 'replace')))

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True

def va2off(va):
    rva = va - IB
    for (lo, hi, pr, sz, nm) in SECTIONS:
        if lo <= rva < hi:
            off = pr + (rva - lo)
            if off < len(DATA):
                return off
    return None

def read(va, n):
    off = va2off(va)
    if off is None:
        return None
    return DATA[off:off+n]

def u8(va):
    b = read(va, 1)
    return b[0] if b else None

def u16(va):
    b = read(va, 2)
    return int.from_bytes(b, 'little') if b and len(b) == 2 else None

def u32(va):
    b = read(va, 4)
    return int.from_bytes(b, 'little') if b and len(b) == 4 else None

def disasm(va, count=40, maxbytes=2048):
    off = va2off(va)
    if off is None:
        return []
    code = DATA[off:off+maxbytes]
    out = []
    for ins in md.disasm(code, va):
        out.append(ins)
        if len(out) >= count:
            break
    return out

def fmt(ins):
    return "%08X  %-20s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str)

def dump(va, count=40, maxbytes=2048):
    for ins in disasm(va, count, maxbytes):
        print(fmt(ins))

def section_of(va):
    rva = va - IB
    for (lo, hi, pr, sz, nm) in SECTIONS:
        if lo <= rva < hi:
            return nm
    return '?'

if __name__ == '__main__':
    print("sections:")
    for s in SECTIONS:
        print("  RVA %08X..%08X  raw@%08X size=%08X %s" % s)
    print("md skipdata:", md.skipdata)
