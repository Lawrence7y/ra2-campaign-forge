# -*- coding: utf-8 -*-
"""对每个容器全局的两个静态装表点，解析 vt 与 Find(slot4) 真身，确认 -1 约定。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import _SECS, u32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True

SITES = [(0x00B0F658, 0x007255ED), (0x00B0F658, 0x00725618),
         (0x00B0F670, 0x0072536D), (0x00B0F670, 0x00725398),
         (0x00B0F1A0, 0x0071E63D), (0x00B0F1A0, 0x0071E668),
         (0x00A8EAE8, 0x004E65FD), (0x00A8EAE8, 0x004E6628),
         (0x00B0F708, 0x0072546D), (0x00B0F708, 0x00725498)]
for g, site in SITES:
    vt = u32(site + 6)
    s0 = u32(vt); s4 = u32(vt + 0x10)
    print("[%08X] 装表@%08X -> vt=%08X  slot0=%08X  Find(slot4)=%08X" % (g, site, vt, s0 or 0, s4 or 0))
    if s4 and R.in_text(s4):
        ins = [i for i in md.disasm(R.read_va(s4, 0x70), s4) if i.id != 0]
        m1 = [i for i in ins if i.id == X86_INS_OR and len(i.operands) == 2
              and i.operands[0].type == X86_OP_REG and i.operands[0].reg == X86_REG_EAX
              and i.operands[1].type == X86_OP_IMM and (i.operands[1].imm & 0xFFFFFFFF) == 0xFFFFFFFF]
        print("     Find 体 %d 条；or eax,-1 站点=%s" % (len(ins), ["%08X" % i.address for i in m1]))
        for i in ins[:12]:
            print("        %08X  %s %s" % (i.address, i.mnemonic, i.op_str))
