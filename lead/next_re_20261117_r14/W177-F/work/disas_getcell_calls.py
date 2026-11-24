#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static disassembly around GetCellAt(0x5657A0) call sites, read-only from gamemd.exe on disk.
Find where the pushed CellStruct arg comes from (hover cell global?).
"""
import sys, os
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OP_IMM, CS_OP_MEM

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000

def load():
    pe = pefile.PE(EXE, fast_load=True)
    data = open(EXE, "rb").read()
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    md.detail = True
    return pe, data, md

def rva2off(pe, rva):
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + s.Misc_VirtualSize:
            return s.PointerToRawData + (rva - s.VirtualAddress)
    return None

def disas_window(pe, data, md, va, before=0x100, after=0x60):
    rva = va - IB
    off = rva2off(pe, rva)
    if off is None:
        print("no section for", hex(va)); return
    start = off - before
    if start < 0: start = 0
    buf = data[start:off+after]
    start_va = va - (off - start)
    insns = list(md.disasm(buf, start_va))
    for ins in insns:
        mark = " <<< CALL 0x5657A0" if (ins.mnemonic in ("call","jmp") and ins.op_str.strip()=="0x5657a0") else ""
        # highlight pushes and movs involving dword globals
        print("%08X  %-8s %s%s" % (ins.address, ins.mnemonic, ins.op_str, mark))

def main():
    pe, data, md = load()
    for va in (0x43F2A7, 0x44947B):
        print("="*30, hex(va), "="*30)
        disas_window(pe, data, md, va, 0x120, 0x40)

if __name__ == "__main__": main()
