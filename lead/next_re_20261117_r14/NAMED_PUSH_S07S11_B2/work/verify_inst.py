# -*- coding: utf-8 -*-
"""核实 slot0 三行主表 ctor 的 operator-new 实例化链 + ㉓ 写点全枚举（纯 ASCII 输出）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core
from capstone.x86 import X86_OP_IMM, X86_INS_CALL

NEW = 0x7C8E17

def callers_of(target):
    out = []
    for ia in core.IMM_INDEX.get(target, []):
        ins = core.INS_BY_ADDR[ia]
        if ins.id == X86_INS_CALL:
            out.append(ia)
    return out

def inst_chain(ctor):
    cs = callers_of(ctor)
    print("ctor %s callers=%s" % (core.hx(ctor), [core.hx(c) for c in cs]))
    for ca in cs:
        pre = core.dis_range(max(core.TEXT_VA, ca - 0x40), 0x40)
        pushes = [x for x in pre if x.mnemonic == "push" and x.operands and x.operands[0].type == X86_OP_IMM]
        news = [x for x in pre if x.id == X86_INS_CALL and x.operands and x.operands[0].type == X86_OP_IMM
                and (x.operands[0].imm & 0xFFFFFFFF) == NEW]
        callctor = [x for x in core.dis_range(ca - 4, 8) if x.id == X86_INS_CALL]
        print("   @%s push_imm=%s new=%s call@site=%s" % (
            core.hx(ca),
            [core.hx(x.operands[0].imm) for x in pushes[-6:]],
            [core.hx(x.address) for x in news],
            [(core.hx(x.address), core.hx(x.operands[0].imm & 0xFFFFFFFF)) for x in callctor
             if x.operands and x.operands[0].type == X86_OP_IMM]))

# 主表 ctor（装 [this+0] 的），逐行两个候选都查
for ctor in (0x0069EC50, 0x0069EE90,   # Ship
             0x00718000, 0x00719CA0,   # Teleport
             0x0075AA90, 0x0075C680,   # Walk
             0x006D1C20, 0x006D1E30, 0x006D1E80):  # Tactical
    inst_chain(ctor)

# ㉓ 写点全枚举：4 张主表，标 CTOR/DTOR
print("=== ㉓ vptr write-point enumeration ===")
for vt, label in ((0x007F2E58,"Ship"),(0x007F50CC,"Teleport"),(0x007F6AC4,"Walk"),(0x007F4348,"Tactical")):
    sites = [i for i in core.install_sites(vt) if core.is_vptr_store(i, vt)]
    for i in sites:
        af = core.atlas_func_of(i.address)
        fs, fz = (af if af else (i.address, 0x80))
        body = core.func_body(fs, fz)
        calls = []
        for x in body:
            if x.id == X86_INS_CALL and x.operands and x.operands[0].type == X86_OP_IMM:
                calls.append(x.operands[0].imm & 0xFFFFFFFF)
        dtor = 0x55A6F0 in calls or any(c in core.FREE_CALLS for c in calls)
        ctor = 0x55A6C0 in calls
        print("%s vt=%s write@%s func=%s sz=%d kind=%s" % (
            label, core.hx(vt), core.hx(i.address), core.hx(fs), fz,
            "DTOR" if dtor else ("CTOR" if ctor else "other")))
