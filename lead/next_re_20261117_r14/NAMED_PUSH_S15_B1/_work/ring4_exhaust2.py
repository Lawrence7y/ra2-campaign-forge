# -*- coding: utf-8 -*-
"""㉓ 严格枚举 v2（修 bug：承载指令用「函数入口起线性反汇编」定位；函数体严格按 atlas size 裁剪）。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import _SECS, va_in, find_containing_atlas_func, is_atexit_registered
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
BASE_DTOR = 0x7258D0
DEL_FREE  = 0x7C8B3D

def resolve_func(va):
    """返回 (fva, size, src)；atlas 优先，否则向前找 ret 边界，再不行返回 (None,None,None)。"""
    f = find_containing_atlas_func(va)
    if f:
        return f[0], f[2], "atlas"
    lo = max(R.TEXT_VA, va - 0x500)
    code = R.read_va(lo, va - lo + 8)
    insns = [i for i in md.disasm(code, lo) if i.id != 0]
    end = None
    for i in insns:
        if i.id in (X86_INS_RET, X86_INS_JMP) and i.address + i.size <= va:
            end = i.address + i.size
    if end is not None:
        return end, (va - end) + 0x80, "scan"
    return None, None, None

def body(fva, size):
    return [i for i in md.disasm(R.read_va(fva, size), fva) if i.id != 0]

def covering(insns, va):
    for i in insns:
        if i.address <= va < i.address + i.size:
            return i
    return None

def shape_of(fva, size, vt):
    insns = body(fva, size)
    inst_k = None
    for k, i in enumerate(insns):
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM \
           and i.operands[1].type == X86_OP_IMM and (i.operands[1].imm & 0xFFFFFFFF) == vt:
            inst_k = k; break
    if inst_k is None:
        return dict(shape="NO_INSTALL", why="体内无 imm 装表指令", install=None, base_ctor=None,
                    n_calls=0, deldtor=False)
    inst = insns[inst_k]
    calls = [(k, i) for k, i in enumerate(insns)
             if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM]
    before = [(k, i) for k, i in calls if k < inst_k]
    has_base_dtor = any((i.operands[0].imm & 0xFFFFFFFF) == BASE_DTOR for _, i in calls)
    has_free = any((i.operands[0].imm & 0xFFFFFFFF) == DEL_FREE for _, i in calls)
    flag1 = [i for i in insns if i.id == X86_INS_TEST and len(i.operands) == 2
             and i.operands[0].type == X86_OP_MEM and i.operands[1].type == X86_OP_IMM
             and (i.operands[1].imm & 0xFF) == 1]
    dl1 = [i for i in insns[:inst_k] if i.id == X86_INS_MOV and len(i.operands) == 2
           and i.operands[0].type == X86_OP_REG and i.operands[0].reg == X86_REG_DL]
    rets = [i for i in insns if i.id == X86_INS_RET]
    why = []
    if dl1: why.append("install 前 mov dl,imm@%08X" % dl1[0].address)
    if before: why.append("install 前 call %08X@%08X" % (before[0][1].operands[0].imm & 0xFFFFFFFF, before[0][1].address))
    if has_base_dtor: why.append("体内 call 基类析构 007258D0")
    if flag1 and has_free: why.append("test byte[mem],1 + call 0x7C8B3D（删除析构器特征）")
    if rets: why.append("末 ret=%s" % rets[-1].mnemonic + " " + rets[-1].op_str)
    deldtor = bool(flag1 and has_free)
    if dl1 or has_base_dtor:
        shape = "DTOR"
    elif before:
        shape = "CTOR?"
    else:
        shape = "OTHER"
    return dict(shape=shape, why="; ".join(why), install=inst.address,
                base_ctor=(before[0][1].operands[0].imm & 0xFFFFFFFF) if before else None,
                n_calls=len(calls), deldtor=deldtor, ret=rets[-1].op_str if rets else None)

ROWS = {
    "007F443C": ("006E3E30", 29),
    "007F44E0": ("006E57A0", 29),
    "007F45C4": ("006E6470", 29),
    "007F5578": ("0071F930", 29),
    "007F5858": ("00726860", 111),
    "007F5904": ("00727BF0", 137),
}

def scan(vt_hex):
    vt = int(vt_hex, 16)
    row_hex, row_sz = ROWS[vt_hex]
    row_lo = int(row_hex, 16); row_hi = row_lo + row_sz
    needle = struct.pack("<I", vt)
    print("#" * 82)
    print("VT %s   本批行(%s)=[%08X,%08X)" % (vt_hex, row_hex, row_lo, row_hi))
    tot = 0
    for nm, v0, sz, data in _SECS:
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0: break
            st = i + 1
            va = v0 + i
            tot += 1
            if nm != ".text":
                print("  imm@%08X [%s]  <- 表槽/表本体（非 .text）" % (va, nm))
                continue
            fva, fsize, src = resolve_func(va)
            if fva is None:
                print("  imm@%08X [.text]  承载指令/函数定位失败" % va); continue
            insns = body(fva, fsize)
            ci = covering(insns, va)
            sh = shape_of(fva, fsize, vt)
            inrow = " ★在本行体内" if row_lo <= va < row_hi else ""
            print("  imm@%08X [.text] 承载=%s %-6s %-32s 函数=%08X(%s,%d)" %
                  (va, ("%08X" % ci.address) if ci else "????",
                   ci.mnemonic if ci else "?", ci.op_str if ci else "?",
                   fva, src, fsize) )
            print("      装表指令=%s  %s%s" %
                  (("%08X" % sh["install"]) if sh["install"] else "-", sh["shape"], inrow))
            print("      %s" % sh["why"])
            ax = is_atexit_registered(fva)
            print("      atexit注册=%s" % ([["%08X" % a, "%08X" % b] for a, b in ax] if ax else "无"))
    print("  该 vt 全镜像 imm32 出现点共 %d" % tot)

if __name__ == "__main__":
    for a in (sys.argv[1:] or list(ROWS)):
        scan(a)
