#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Disassemble disputed rows for manual verification."""
from engine import Bin
import capstone
bin_=Bin()
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=False; md.skipdata=True
for va in (0x402F80,0x405AB0,0x4063A0,0x40A600,0x40BDA0,0x404120,0x407080):
    print(f'--- {va:08X} ---')
    chunk=bin_.read(va-8,80)
    for ins in md.disasm(chunk,va-8):
        mark='>>' if ins.address==va else '  '
        print(f'{mark} {ins.address:08X} {ins.bytes.hex():<16} {ins.mnemonic} {ins.op_str}')
        if ins.address>va+40: break
