# -*- coding: utf-8 -*-
"""虚表全量枚举 + 函数形状分类（构造器 vs 析构器 vs 其它）。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import u32, va_in, read_cstr, find_containing_atlas_func
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
md.detail = True


def vt_slots(vb, limit=64):
    out = []
    for i in range(limit):
        v = u32(vb + 4 * i)
        if v is None or not R.in_text(v):
            break
        out.append(v)
    return out


def shape(ea, size):
    """函数形状签名：是否先调基类 ctor 再装 vptr / 是否 dl=1 / 是否有 delete。"""
    code = R.read_va(ea, size or 0x120)
    insns = list(md.disasm(code, ea))
    first_write = None
    first_call = None
    flags = {"mov_dl_1": False, "call_before_install": False, "install_before_call": False,
             "has_push_imm_1": False, "calls": []}
    for ins in insns:
        if ins.id == 0:
            continue
        if ins.id == 0xB8 and len(ins.operands) == 2 and ins.operands[0].type == 1 \
           and ins.operands[0].reg == 0x1D and ins.operands[1].type == 2 and (ins.operands[1].imm & 0xFF) == 1:
            flags["mov_dl_1"] = True
        if ins.mnemonic in ("mov", "push", "pop", "and", "or", "xor", "test", "lea", "cmp", "nop"):
            pass
    return insns


def analyze_vt(vb):
    slots = vt_slots(vb)
    print("vtable %08X  vlen=%d  COL@-4=%08X" % (vb, len(slots), u32(vb - 4) or 0))
    for i, t in enumerate(slots):
        f = find_containing_atlas_func(t)
        print("  slot#%-2d off=+0x%02X -> %08X  atlas_func=%s" %
              (i, 4 * i, t, f[1] if f else "(none)"))


def entry_shapes(vb):
    """对虚表里每个槽函数，判定它是否装该虚表（[reg]=vb），及其形状。"""
    slots = vt_slots(vb)
    for i, t in enumerate(slots):
        code = R.read_va(t, 0x180)
        insns = list(md.disasm(code, t))
        installers = [ins for ins in insns
                      if ins.mnemonic == "mov" and len(ins.operands) == 2
                      and ins.operands[0].type == 3 and ins.operands[1].type == 2
                      and (ins.operands[1].imm & 0xFFFFFFFF) == vb]
        if not installers:
            continue
        first_call = next((x for x in insns if x.id == 0xE8), None)
        inst = installers[0]
        dl1 = any(x.mnemonic == "mov" and len(x.operands) == 2
                  and x.operands[0].type == 1 and x.operands[0].reg == 0x1D
                  and x.operands[1].type == 2 and (x.operands[1].imm & 0xFF) == 1 for x in insns)
        print("  slot#%-2d %08X installs@%08X  first_call=%s  dl=1:%s  %s" %
              (i, t, inst.address,
               "%08X" % first_call.operands[0].imm if first_call and first_call.operands[0].type == 2 else None,
               dl1,
               "CTOR(先调基类)" if first_call and first_call.address < inst.address
               else "DTOR?(先装表后干活)"))


if __name__ == "__main__":
    mode = sys.argv[1]
    for a in sys.argv[2:]:
        vb = int(a, 16)
        if mode == "vt":
            analyze_vt(vb)
        else:
            entry_shapes(vb)
        print()
