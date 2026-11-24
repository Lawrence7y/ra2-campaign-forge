#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal read-only PE helper: RVA<->offset, byte reads, capstone disasm."""
import hashlib, pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IMAGE_BASE = 0x400000

_pe = pefile.PE(PATH, fast_load=True)
_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True

def sha256():
    h = hashlib.sha256()
    with open(PATH,'rb') as f:
        for b in iter(lambda: f.read(1<<20), b''):
            h.update(b)
    return h.hexdigest().upper()

def rva2off(rva):
    return _pe.get_offset_from_rva(rva)

def va2off(va):
    return rva2off(va - IMAGE_BASE)

def read_va(va, n):
    off = va2off(va)
    return _pe.__data__[off:off+n]

def dword_va(va):
    return int.from_bytes(read_va(va,4),'little')

def word_va(va):
    return int.from_bytes(read_va(va,2),'little')

def byte_va(va):
    return read_va(va,1)[0]

def disasm(va, nbytes, count=None):
    code = read_va(va, nbytes)
    out=[]
    for i in _md.disasm(code, va):
        out.append(i)
        if count and len(out)>=count:
            break
    return out

def fmt(insn):
    return f"{insn.address:08X}  {insn.bytes.hex():<20} {insn.mnemonic:<8} {insn.op_str}"

def section_of_va(va):
    rva = va-IMAGE_BASE
    for s in _pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.Name.decode(errors='replace').rstrip('\x00')
    return '?'

if __name__ == '__main__':
    print("SHA256:", sha256())
    print("ImageBase:", hex(_pe.OPTIONAL_HEADER.ImageBase))
    for s in _pe.sections:
        print(s.Name.decode(errors='replace').rstrip('\x00'),
              hex(IMAGE_BASE+s.VirtualAddress),
              hex(s.Misc_VirtualSize), hex(s.SizeOfRawData))
