# -*- coding: utf-8 -*-
"""S01-KPROVED helper: load gamemd.exe, disassemble, scan calls/vtables. READ-ONLY on exe."""
import sys, json, struct, hashlib
import pefile
from capstone import *
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
PE = pefile.PE(EXE, fast_load=False)
IB = PE.OPTIONAL_HEADER.ImageBase
MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True

SECTIONS = []
for s in PE.sections:
    name = s.Name.rstrip(b'\x00').decode('latin1')
    SECTIONS.append((name, IB + s.VirtualAddress, s.Misc_VirtualSize, s.SizeOfRawData, s.PointerToRawData, s.VirtualAddress))

def rva_to_off(rva):
    for name, va, vsize, rawsize, rawptr, va0 in SECTIONS:
        if va0 <= rva < va0 + max(vsize, rawsize):
            off = rawptr + (rva - va0)
            return off
    return None

def va_to_off(va):
    return rva_to_off(va - IB)

def read_va(va, n):
    off = va_to_off(va)
    if off is None: return b''
    return PE.__data__[off:off+n]

def u32(va):
    b = read_va(va, 4)
    return struct.unpack('<I', b)[0] if len(b)==4 else None

def disasm(va, size):
    code = read_va(va, size)
    out=[]
    for ins in MD.disasm(code, va):
        out.append(ins)
    return out

def fmt_ins(ins):
    s = f"{ins.address:08X}  {ins.bytes.hex():<20} {ins.mnemonic:<8} {ins.op_str}"
    return s

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv)>1 else 'info'
    if cmd=='info':
        print('IB=',hex(IB))
        for x in SECTIONS:
            print(f'{x[0]:<10} VA={x[1]:08X} VSize={x[2]:08X} RawSize={x[3]:08X}')
    elif cmd=='dis':
        va=int(sys.argv[2],16); size=int(sys.argv[3],0)
        for ins in disasm(va,size):
            print(fmt_ins(ins))
    elif cmd=='u32':
        for a in sys.argv[2:]:
            print(a, hex(u32(int(a,16)) or 0))
