#!/usr/bin/env python3
"""Shared PE + capstone helper for S03-K2. Read-only on gamemd.exe."""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories()
DATA = pe.__data__

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            off = s.PointerToRawData + (rva - s.VirtualAddress)
            return off
    # headers
    if 0 <= rva < pe.OPTIONAL_HEADER.SizeOfHeaders:
        return rva
    return None

def sec_of(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.rstrip(b'\0').decode('latin1')
    return None

def read(va, n):
    o = va2off(va)
    if o is None: return b''
    return DATA[o:o+n]

def u8(va):  return read(va,1)[0] if read(va,1) else None
def u16(va):
    b = read(va,2); return int.from_bytes(b,'little') if len(b)>=2 else None
def u32(va):
    b = read(va,4); return int.from_bytes(b,'little') if len(b)>=4 else None

def dis(va, nbytes=64, count=0):
    """Yield capstone insns starting at va. skipdata=True."""
    b = read(va, nbytes)
    if not b: return
    it = md.disasm(b, va)
    for i, ins in enumerate(it):
        yield ins
        if count and i+1 >= count: break

def dis_one(va):
    for ins in dis(va, 16, 1):
        return ins
    return None

def dump(va, nbytes=64, count=20):
    for ins in dis(va, nbytes, count):
        ops = ', '.join(ins.op_str.split(','))
        print(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic:8} {ins.op_str}")

def sections():
    out=[]
    for s in pe.sections:
        out.append((s.Name.rstrip(b'\0').decode('latin1'), s.VirtualAddress+IB,
                    s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData, hex(s.Characteristics)))
    return out

if __name__ == '__main__':
    print("ImageBase", hex(IB), "SizeOfImage", hex(pe.OPTIONAL_HEADER.SizeOfImage))
    for n,va,vs,pr,rs,ch in sections():
        print(f"  {n:8} VA={va:08X} VS={vs:8X} raw={pr:8X}/{rs:8X} {ch}")
