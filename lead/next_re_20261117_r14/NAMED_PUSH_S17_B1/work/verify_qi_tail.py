# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C
print("=== tail of 00410260 (SuperClass::QueryInterface, callee of call[eax] in 006BF690) ===")
for ins in C.disasm_body(0x00410260, 0xA0):
    if ins.address >= 0x004102D8:
        print("  %s: %-9s %-36s ; %s"%(C.hx(ins.address),ins.mnemonic,ins.op_str,ins.bytes.hex().upper()))
print("\n=== 004A3020 failure/success returns (callee of 004A2CD0) ===")
for ins in C.disasm_body(0x004A3020,0xD8):
    if ins.address in (0x004A3088,0x004A3089,0x004A3090,0x004A30BF,0x004A30C3,0x004A30C7,0x004A30C9,0x004A30CB,0x004A30CD,0x004A30D2,0x004A30D5):
        print("  %s: %-9s %-36s ; %s"%(C.hx(ins.address),ins.mnemonic,ins.op_str,ins.bytes.hex().upper()))
