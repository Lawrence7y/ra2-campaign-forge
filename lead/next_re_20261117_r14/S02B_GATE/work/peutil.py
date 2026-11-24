#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S02B_GATE reusable PE/capstone module. Read-only on target binary.
capstone 5.0.7 with skipdata=True (discipline #2). Never writes gamemd.exe.
"""
import struct
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_OP_REG

BIN = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000

_pe = pefile.PE(BIN, fast_load=True)
_pe.parse_data_directories()

_SECTIONS = []
for s in _pe.sections:
    name = s.Name.rstrip(b'\0').decode('latin-1')
    va = IB + s.VirtualAddress
    _SECTIONS.append((name, va, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

_DATA = open(BIN, 'rb').read()

def section_of(va):
    for name, sva, vsz, praw, rsz in _SECTIONS:
        if sva <= va < sva + max(vsz, rsz):
            return name, sva, vsz, praw, rsz
    return None

def va2off(va):
    for name, sva, vsz, praw, rsz in _SECTIONS:
        if sva <= va < sva + max(vsz, rsz):
            off = praw + (va - sva)
            if 0 <= off < len(_DATA):
                return off
    return None

def read(va, n):
    off = va2off(va)
    if off is None:
        return b'\0' * n
    return _DATA[off:off+n]

def u8(va):  return read(va, 1)[0]
def u16(va): return struct.unpack('<H', read(va, 2))[0]
def u32(va): return struct.unpack('<I', read(va, 4))[0]

_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = True
_md.skipdata = True

def disasm(va, max_bytes, count=0):
    """Yield capstone insn from va up to max_bytes; skipdata=True."""
    code = read(va, max_bytes)
    n = 0
    for insn in _md.disasm(code, va):
        yield insn
        n += 1
        if count and n >= count:
            break

def fmt(insn):
    return "%08X  %-9s %s" % (insn.address, insn.mnemonic, insn.op_str)

def fmt_bytes(insn):
    return insn.bytes.hex(' ')

def imm_target(insn):
    """Direct call/jmp rel target VA (X86_OP_IMM) or None."""
    if insn.mnemonic in ('call', 'jmp') and insn.operands:
        op = insn.operands[0]
        if op.type == X86_OP_IMM:
            return op.imm
    return None

def dump_range(va_start, va_end, out=print):
    """Disassemble [va_start, va_end) fully, no truncation."""
    for insn in disasm(va_start, va_end - va_start):
        out(fmt(insn))

if __name__ == '__main__':
    print("BIN", BIN, "size", len(_DATA))
    h = struct.pack('<I', 0)
    for name, sva, vsz, praw, rsz in _SECTIONS:
        print("%-8s VA=%08X..%08X raw=%08X..%08X" % (name, sva, sva+max(vsz,rsz), praw, praw+rsz))
