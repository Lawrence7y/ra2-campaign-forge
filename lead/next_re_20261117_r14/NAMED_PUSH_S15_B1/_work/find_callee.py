# -*- coding: utf-8 -*-
"""解析 FIND 站点的容器：全局 vptr -> 容器虚表 -> 槽 4(+0x10) -> Find 函数体，确认 -1 返回约定。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import _SECS, u32, va_in
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True

def find_global_vptr_writes(gva):
    """找 .text 中 `C7 05 <gva> <imm32>`（全局 vptr 静态装表）。"""
    out = []
    pat = b"\xc7\x05" + struct.pack("<I", gva)
    for nm, v0, sz, data in _SECS:
        if nm != ".text": continue
        st = 0
        while True:
            i = data.find(pat, st)
            if i < 0: break
            st = i + 1
            imm = struct.unpack_from("<I", data, i + 6)[0]
            out.append((v0 + i, imm))
    return out

def dumpf(va, n=0x60):
    ins = [i for i in md.disasm(R.read_va(va, n), va) if i.id != 0]
    for i in ins:
        print("      %08X  %-20s %s %s" % (i.address, " ".join("%02x" % b for b in i.bytes), i.mnemonic, i.op_str))
    return ins

GLOBALS = [0x00B0F658, 0x00B0F670, 0x00B0F1A0, 0x00A8EAE8, 0x00B0F708, 0x00A8EAF8]
print("=== 容器全局 vptr 静态装表点 ===")
for g in GLOBALS:
    ws = find_global_vptr_writes(g)
    print("\n[%08X] 装表点 %d 个" % (g, len(ws)))
    for va, imm in ws:
        print("   %08X -> vt %08X" % (va, imm))
        s4 = u32(imm + 0x10)
        s0 = u32(imm)
        print("       vt slot0=%08X  slot4(+0x10)=%08X" % (s0 or 0, s4 or 0))
        if s4 and R.in_text(s4):
            ins = [i for i in md.disasm(R.read_va(s4, 0x60), s4) if i.id != 0]
            has_m1 = any(i.id == X86_INS_OR and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG
                         and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_IMM
                         and (i.operands[1].imm & 0xFFFFFFFF) == 0xFFFFFFFF for i in ins)
            print("       Find 体前 %d 条；含 xor/or eax,-1 ？ %s" % (len(ins), has_m1))
            dumpf(s4, 0x50)
