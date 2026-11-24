# -*- coding: utf-8 -*-
"""Disassemble init fn 0x52BA60 around the BATTLE (0x52C605) and RULE (0x52C95C) enum call sites."""
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, CS_OPT_SKIPDATA
EXE=r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"; IB=0x400000
pe=pefile.PE(EXE,fast_load=False); data=open(EXE,"rb").read()
def v2o(va): return pe.get_offset_from_rva(va-IB)
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True
for start,end,label in [(0x52C5D0,0x52C640,"BATTLE enum call @0x52C605"),
                        (0x52C930,0x52C990,"RULE enum call @0x52C95C")]:
    code=data[v2o(start):v2o(end)]
    print(f"=== {label} ===")
    for insn in md.disasm(code,start):
        mark=" <<<" if insn.address in (0x52C605,0x52C95C) else ""
        print(f"0x{insn.address:08X}  {insn.mnemonic:<8} {insn.op_str}{mark}")
