# -*- coding: utf-8 -*-
"""㉓ 严格枚举：全镜像扫 vt 基址的 imm32 出现点 -> 定位承载它的指令 -> 分类。

分类口径（R14_COMMON §13.5 + 卡面）：
  (a) atexit 注册的全局析构器体内的写   -> EXCL_ATEXIT
  (b) 删除析构器体内的写（test byte [esp+X],1 + call 0x7C8B3D + ret 4）-> EXCL_DELDTOR
  (c) 普通析构器体内的写（dl=1 / call 0x7258D0 基类析构）-> EXCL_DTOR
  (d) 构造器体内（install 之前有基类 ctor 调用，且返回 this）-> CTOR   <= 唯一合格 ④ 锚
  (e) 其它（Load/方法内重装、无 atlas 函数）-> OTHER
"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import _SECS, u32, va_in, find_containing_atlas_func, is_atexit_registered
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
BASE_DTOR = 0x7258D0
DEL_FREE  = 0x7C8B3D

def occurrence_insn(va):
    """定位覆盖 va 的指令：从前 15 字节起试，取第一条 address<=va<address+size 的指令。"""
    sec = va_in(va)
    if not sec:
        return None
    for back in range(0, 16):
        start = va - back
        if va_in(start) != sec:
            break
        code = R.read_va(start, 16 + 15)
        if not code:
            break
        for i in md.disasm(code, start):
            if i.address <= va < i.address + i.size and i.id != 0:
                return i
            if i.address > va:
                break
    return None

def func_of(va):
    f = find_containing_atlas_func(va)
    if f:
        return f[0], f[1], f[2]
    # 不在 atlas：向前回溯找 push ebp;mov ebp,esp 或 ret 后的第一条，上限 0x400
    lo = max(R.TEXT_VA, va - 0x400)
    code = R.read_va(lo, va - lo + 8)
    insns = [i for i in md.disasm(code, lo) if i.id != 0]
    end = None
    for i in insns:
        if i.id == X86_INS_RET and i.address + i.size <= va:
            end = i.address + i.size
    return (end, None, None) if end else (None, None, None)

def shape_of(fva, vt, limit=0x400):
    """返回 (shape, why, install_va, base_ctor_va)"""
    code = R.read_va(fva, limit)
    insns = [i for i in md.disasm(code, fva) if i.id != 0]
    inst_k = None
    for k, i in enumerate(insns):
        if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_MEM \
           and i.operands[1].type == X86_OP_IMM and (i.operands[1].imm & 0xFFFFFFFF) == vt:
            inst_k = k
            break
    if inst_k is None:
        return ("NO_INSTALL", "该函数体内无 imm 形式装表指令", None, None)
    inst = insns[inst_k]
    calls = [(k, i) for k, i in enumerate(insns)
             if i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM]
    before = [(k, i) for k, i in calls if k < inst_k]
    cobs = [(k, i) for k, i in calls if k > inst_k]
    # 删除析构器特征
    has_flag1 = any(i.id == X86_INS_TEST and len(i.operands) == 2 and i.operands[1].type == X86_OP_IMM
                    and (i.operands[1].imm & 0xFF) == 1 for i in insns)
    has_free = any((i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM
                    and (i.operands[0].imm & 0xFFFFFFFF) == DEL_FREE) for i in insns)
    has_base_dtor = any((i.id == X86_INS_CALL and i.operands and i.operands[0].type == X86_OP_IMM
                         and (i.operands[0].imm & 0xFFFFFFFF) == BASE_DTOR) for i in insns)
    dl1 = any(i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG
              and i.operands[0].reg == X86_REG_DL for i in insns[:inst_k])
    why = []
    if dl1: why.append("install 前 mov dl,imm")
    if before: why.append("install 前 call %08X@%08X" % (before[0][1].operands[0].imm & 0xFFFFFFFF, before[0][1].address))
    if has_base_dtor: why.append("体内 call 基类析构 007258D0")
    if has_flag1 and has_free: why.append("test byte[esp+X],1 + call 0x7C8B3D（删除析构器特征）")
    if dl1 or has_base_dtor:
        shape = "DTOR"
    elif before:
        shape = "CTOR?"
    else:
        shape = "OTHER"
    return (shape, "; ".join(why), inst.address, before[0][1].operands[0].imm & 0xFFFFFFFF if before else None)

def scan(vt_hex, row_lo=None, row_hi=None):
    vt = int(vt_hex, 16)
    needle = struct.pack("<I", vt)
    print("#" * 80)
    print("VT %s   (rows 体外判定区间: %s..%s)" % (vt_hex,
          "%08X" % row_lo if row_lo else "-", "%08X" % row_hi if row_hi else "-"))
    hits = 0
    for nm, v0, sz, data in _SECS:
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0:
                break
            st = i + 1
            va = v0 + i
            hits += 1
            ins = occurrence_insn(va)
            if ins is None:
                print("  %08X [%s]  (无法定位承载指令)" % (va, nm)); continue
            if nm != ".text":
                print("  %08X [%s]  承载=%08X %s %s   << .rdata/.data 槽或表本体" %
                      (va, nm, ins.address, ins.mnemonic, ins.op_str)); continue
            fva, fname, fsize = func_of(ins.address)
            inrow = ""
            if row_lo is not None and row_lo <= ins.address < row_hi:
                inrow = "  ★在本行函数体内"
            print("  %08X [.text] 承载=%08X %-8s %-34s 函数=%s%s" %
                  (va, ins.address, ins.mnemonic, ins.op_str,
                   ("%08X(atlas size=%s)" % (fva, fsize)) if fname else
                   (("%08X(非atlas)" % fva) if fva else "?"), inrow))
            if fname or fva:
                ax = is_atexit_registered(fva) if fva else []
                sh, why, iv, bcv = shape_of(fva, vt)
                print("            shape=%s  %s" % (sh, why))
                if ax:
                    print("            ★ATEXIT 注册点: %s" % [["%08X" % a, "%08X" % b] for a, b in ax])
    print("  合计 imm32 出现点 %d" % hits)

if __name__ == "__main__":
    pairs = {
        "007F443C": (0x006E3E30, 0x006E3E30 + 29),
        "007F44E0": (0x006E57A0, 0x006E57A0 + 29),
        "007F45C4": (0x006E6470, 0x006E6470 + 29),
        "007F5578": (0x0071F930, 0x0071F930 + 29),
        "007F5858": (0x00726860, 0x00726860 + 111),
        "007F5904": (0x00727BF0, 0x00727BF0 + 137),
    }
    for a in (sys.argv[1:] or list(pairs)):
        lo, hi = pairs.get(a, (None, None))
        scan(a, lo, hi)
