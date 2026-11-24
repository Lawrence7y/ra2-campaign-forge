#!/usr/bin/env python3
"""W128g: locate the 3 null-unsafe sequences in FUN_006f3f40 precisely.

Third defect (ledger §831): the code reads
    mov ecx,[eax]            ; ecx = obj
    mov edx,[ecx+0xAC]       ; edx may be 0   <-- no check
    mov al,[edx+0x155/0x159/0x15A]
so with [obj+0xAC]==0 it faults reading offset 0x155 etc.

This finds every occurrence inside the function and prints enough context to
design a null-safe replacement that fits in the original bytes.
"""
import json

import capstone
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)

FN, SIZE = 0x006F3F40, 953
body = img[FN - ib: FN - ib + SIZE]
print("function 0x%08X .. 0x%08X (%d bytes)" % (FN, FN + SIZE - 1, SIZE))

LOAD_EDX = bytes.fromhex("8b91ac000000")   # mov edx,[ecx+0xAC]
hits = []
i = body.find(LOAD_EDX)
while i != -1:
    hits.append(FN + i)
    i = body.find(LOAD_EDX, i + 1)
print("\n'mov edx,[ecx+0xAC]' occurrences inside the function: %d" % len(hits))

for va in hits:
    print("\n=== at 0x%08X ===" % va)
    lo = va - 16
    for ins in md.disasm(img[lo - ib: va + 0x28 - ib], lo):
        mark = " <== LOAD [ecx+0xAC]" if ins.address == va else ""
        print("   %08X  %-22s %s %s%s" % (ins.address, ins.bytes.hex(),
                                          ins.mnemonic, ins.op_str, mark))

# also find the byte reads through edx
print("\n=== all 'mov al,[edx+imm32]' in the function ===")
for ins in md.disasm(body, FN):
    if ins.mnemonic == "mov" and ins.op_str.startswith("al, byte ptr [edx"):
        print("   %08X  %-22s %s %s" % (ins.address, ins.bytes.hex(),
                                        ins.mnemonic, ins.op_str))
