# -*- coding: utf-8 -*-
"""Disassemble the BATTLE enum fn 0x52CB90 (capstone skipdata=True, from entry)
and dump call sites with surrounding context, to see exact args to the merge fn."""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"; IB=0x400000
pe=pefile.PE(EXE,fast_load=False); data=open(EXE,"rb").read()
def v2o(va): return pe.get_offset_from_rva(va-IB)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for entry,size in [(0x52CB90,473)]:
    code=data[v2o(entry):v2o(entry)+size]
    print(f"=== disasm 0x{entry:X} size={size} ===")
    for insn in md.disasm(code,entry):
        print(f"0x{insn.address:08X}  {insn.mnemonic:<8} {insn.op_str}")
