#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-GATE-B reusable PE/capstone module. Read-only on target binary."""
import os, sys, struct
import pefile
from capstone import *
from capstone.x86 import *

BIN = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000

_pe = pefile.PE(BIN, fast_load=True)
_pe.parse_data_directories()

# Build VA -> file-offset mapping from sections
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
            if off < len(_DATA):
                return off
    return None

def read(va, n):
    off = va2off(va)
    if off is None:
        return b'\0' * n
    return _DATA[off:off+n]

def u8(va): return read(va,1)[0]
def u16(va): return struct.unpack('<H', read(va,2))[0]
def u32(va): return struct.unpack('<I', read(va,4))[0]

_md32 = Cs(CS_ARCH_X86, CS_MODE_32)
_md32.detail = True
_md32.skipdata = True

_md32_noskip = Cs(CS_ARCH_X86, CS_MODE_32)
_md32_noskip.detail = True
_md32_noskip.skipdata = False

def disasm(va, max_bytes, count=0, skipdata=True):
    """Yield (addr, size, mnemonic, op_str, insn) until max_bytes or count."""
    md = _md32 if skipdata else _md32_noskip
    code = read(va, max_bytes)
    n = 0
    for insn in md.disasm(code, va):
        yield insn
        n += 1
        if count and n >= count:
            break

def fmt_insn(insn):
    return "%08X  %-8s %s" % (insn.address, insn.mnemonic, insn.op_str)

def imm_target(insn):
    """Return direct call/jmp rel target VA if applicable."""
    if insn.mnemonic in ('call','jmp') and insn.operands:
        op = insn.operands[0]
        if op.type == X86_OP_IMM:
            return op.imm
    return None

if __name__ == '__main__':
    print("BIN", BIN, "size", len(_DATA))
    for name, sva, vsz, praw, rsz in _SECTIONS:
        print("%-8s VA=%08X..%08X raw=%08X..%08X" % (name, sva, sva+max(vsz,rsz), praw, praw+rsz))
