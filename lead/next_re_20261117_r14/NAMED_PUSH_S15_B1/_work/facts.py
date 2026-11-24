# -*- coding: utf-8 -*-
"""逐行事实表：① 入口 / ② RTTI 链字节 / ③b 站点字节 / ④ 构造安装点字节。
输出 _work/facts_<entry>.txt 与 facts.json。所有判断都打印原始字节供复核。
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import (_SECS, u32, va_in, read_cstr, parse_col, parse_td,
                   find_containing_atlas_func, is_atexit_registered)
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True; md.detail = True
OUT = os.path.dirname(os.path.abspath(__file__))

# entry -> (名字, vtable基址, 期望槽号, 构造器, 装表指令, ③b 形态)
ROWS = [
    ("006E3E30", "TActionClass::slot6",       0x007F443C, 6,  0x006DD000, 0x006DD036, "SAVE"),
    ("006E57A0", "TagClass::slot6",           0x007F44E0, 6,  0x006E4DE0, 0x006E4E07, "SAVE"),
    ("006E6470", "TagTypeClass::slot6",       0x007F45C4, 6,  0x006E5B60, 0x006E5B8E, "SAVE"),
    ("0071F930", "TEventClass::slot6",        0x007F5578, 6,  0x0071E6A0, 0x0071E6C1, "SAVE"),
    ("0071FA80", "TEventClass::slot8",        0x007F5578, 8,  0x0071E6A0, 0x0071E6C1, "FIND"),
    ("00726860", "TriggerClass::slot5",       0x007F5858, 5,  0x00725FA0, 0x00725FCE, "LOAD"),
    ("007268D0", "TriggerClass::slot6",       0x007F5858, 6,  0x00725FA0, 0x00725FCE, "SAVE"),
    ("00726950", "TriggerClass::slot8",       0x007F5858, 8,  0x00725FA0, 0x00725FCE, "FIND"),
    ("00727BF0", "TriggerTypeClass::slot5",   0x007F5904, 5,  0x00726C80, 0x00726CD2, "LOAD"),
    ("00727C80", "TriggerTypeClass::slot6",   0x007F5904, 6,  0x00726C80, 0x00726CD2, "SAVE"),
]

def insns_of(va, size):
    return [i for i in md.disasm(R.read_va(va, size), va) if i.id != 0]

def raw(va, n):
    return R.read_va(va, n)

def hexb(b):
    return " ".join("%02x" % x for x in b)

def show(i):
    return "%08X  %-20s %s %s" % (i.address, hexb(i.bytes), i.mnemonic, i.op_str)

def sites_save(insns):
    """call X / test eax,eax / jl fail ; fail 落点 eax 原样返回 ; 成功路 xor eax,eax"""
    out = []
    for k, i in enumerate(insns):
        if i.id != X86_INS_CALL:
            continue
        t = insns[k + 1] if k + 1 < len(insns) else None
        j = insns[k + 2] if k + 2 < len(insns) else None
        if not (t and j and t.id == X86_INS_TEST and j.id in (X86_INS_JL, X86_INS_JGE, X86_INS_JE, X86_INS_JNE)):
            continue
        tgt = j.operands[0].imm if j.operands and j.operands[0].type == X86_OP_IMM else None
        landing = next((x for x in insns if x.address == tgt), None)
        nxt = insns[k + 3] if k + 3 < len(insns) else None
        out.append(dict(call=i, test=t, jcc=j, target=tgt, landing=landing, after=nxt,
                        callee=(i.operands[0].imm & 0xFFFFFFFF) if i.operands and i.operands[0].type == X86_OP_IMM else None,
                        gap=len(insns[k + 1:k + 2])))
    return out

def sites_find(insns):
    """call dword[reg+0x10] / cmp eax,-1 / je skip"""
    out = []
    for k, i in enumerate(insns):
        if i.id != X86_INS_CALL or not i.operands or i.operands[0].type != X86_OP_MEM:
            continue
        t = insns[k + 1] if k + 1 < len(insns) else None
        j = insns[k + 2] if k + 2 < len(insns) else None
        if not (t and j and t.id == X86_INS_CMP and j.id == X86_INS_JE):
            continue
        tgt = j.operands[0].imm if j.operands and j.operands[0].type == X86_OP_IMM else None
        out.append(dict(call=i, cmp=t, jcc=j, target=tgt,
                        mem=i.op_str))
    return out

def callee_profile(va):
    info = R.ATLAS.get("%08X" % va)
    if not info:
        return None
    ins = insns_of(va, info["size"])
    consts = [(i.address, i.operands[1].imm & 0xFFFFFFFF) for i in ins
              if i.id == X86_INS_MOV and len(i.operands) == 2 and i.operands[0].type == X86_OP_REG
              and i.operands[0].reg == X86_REG_EAX and i.operands[1].type == X86_OP_IMM]
    jl = [(i.address, i.operands[0].imm & 0xFFFFFFFF) for i in ins if i.id == X86_INS_JL]
    return dict(size=info["size"], eax_consts=consts, jl=jl,
                calls_ind=[i.address for i in ins if i.id == X86_INS_CALL
                           and i.operands and i.operands[0].type == X86_OP_MEM])

def main():
    allfacts = {}
    for entry, name, vt, slotn, ctor_va, install_va, kind in ROWS:
        ea = int(entry, 16)
        info = R.ATLAS.get(entry)
        size = info["size"] if info else 0x200
        insns = insns_of(ea, size)
        L = []
        A = lambda s="": L.append(s)
        A("# ROW %s   %s   形态=%s" % (entry, name, kind))
        A("")
        A("## 环① 入口与函数边界")
        A("entry=%08X  atlas_size=%d  n_decoded=%d  首=%s  末=%s" %
          (ea, size, len(insns), show(insns[0]), show(insns[-1])))
        A("in_text=%s  span=%d 覆盖==%d ; 末尾 ret 操作数=%s" %
          (R.in_text(ea), insns[-1].address + insns[-1].size - ea, size,
           insns[-1].op_str if insns[-1].id == X86_INS_RET else "非ret"))
        A("")
        A("## 环② 类身份（RTTI 链，独立取证）")
        slot_va = vt + 4 * slotn
        A("vt_base=%08X  slot#%d(+0x%02X)  slot_va=%08X  u32(slot_va)=%08X  ==entry? %s" %
          (vt, slotn, 4 * slotn, slot_va, u32(slot_va) or 0, u32(slot_va) == ea))
        A("slot_va 原始字节: %s" % hexb(raw(slot_va, 4)))
        A("slot0=%08X (主虚表判据 00410260)  slot0 原始: %s" %
          (u32(vt) or 0, hexb(raw(vt, 4))))
        col = u32(vt - 4)
        A("u32(vt_base-4)=COL=%08X  (绝对 VA，非 RVA)" % (col or 0))
        A("COL 原始字节(sig,off,cd,td,chd): %s" % hexb(raw(col, 20)))
        ci = parse_col(col)
        tdi = parse_td(ci["td"])
        A("COL.sig=%08X  COL.pTD=%08X  COL.pCHD=%08X" % (ci["sig"], ci["td"], ci["chd"]))
        A("TD 原始字节(+0..+15): %s" % hexb(raw(ci["td"], 16)))
        A("TD.pVFTable=%08X  TD.spare=%08X" % (u32(ci["td"]), u32(ci["td"] + 4)))
        A("TD+8 内联名串（不是指针）= '%s'  name_va=%08X" % (tdi["name"], tdi["name_va"]))
        nbase = u32(ci["chd"] + 8) if ci["chd"] else 0
        arr = u32(ci["chd"] + 0xC) if ci["chd"] else 0
        bases = []
        if arr and nbase and 0 < nbase < 16:
            for i in range(nbase):
                bc = u32(arr + 4 * i)
                btd = u32(bc) if bc else None
                bt = parse_td(btd) if btd else None
                if bt:
                    bases.append(bt["name"])
        A("CHD.nBaseClasses=%s  基类链=%s" % (nbase, bases))
        A("")
        A("## 环③b 站点（call 后返回约定被分支消费）")
        if kind == "FIND":
            for s in sites_find(insns):
                A("  " + show(s["call"]))
                A("  " + show(s["cmp"]))
                A("  " + show(s["jcc"]) + "   -> %08X" % (s["target"] or 0))
                A("      操作数=%s（容器虚表 Find 槽 +0x10）" % s["mem"])
        else:
            for s in sites_save(insns):
                A("  " + show(s["call"]))
                A("  " + show(s["test"]))
                A("  " + show(s["jcc"]) + "   -> %08X" % (s["target"] or 0))
                if s["after"]:
                    A("  " + show(s["after"]) + "   (fall-through 清零路)")
                if s["landing"]:
                    A("      失败落点 %08X: %s" % (s["landing"].address, show(s["landing"])))
                pr = callee_profile(s["callee"]) if s["callee"] else None
                if pr:
                    A("      被调 %08X size=%d  eax 立即数写入=%s  jl 站点=%s" %
                      (s["callee"], pr["size"],
                       [("%08X" % a, "%08X" % v) for a, v in pr["eax_consts"]],
                       [("%08X" % a, "%08X" % t) for a, t in pr["jl"]]))
                    A("      被调体内间接 call 站点=%s" % ["%08X" % a for a in pr["calls_ind"]])
        A("")
        A("## 环④ 使用见证（构造器装活表；与 ② 不同源）")
        csize = R.ATLAS.get("%08X" % ctor_va, {}).get("size")
        cins = insns_of(ctor_va, csize)
        A("构造器=%08X atlas_size=%s" % (ctor_va, csize))
        for i in cins[:6]:
            A("  " + show(i))
        A("  ...")
        ii = next((i for i in cins if i.address == install_va), None)
        A("装表指令=" + (show(ii) if ii else "缺失"))
        ax = is_atexit_registered(ctor_va)
        A("atexit 注册=%s" % ([["%08X" % a, "%08X" % b] for a, b in ax] if ax else "无"))
        A("装表点在行体[%08X,%08X)之外? %s" % (ea, ea + size, not (ea <= install_va < ea + size)))
        A("")
        with open(os.path.join(OUT, "facts_%s.txt" % entry), "w", encoding="utf-8") as f:
            f.write("\n".join(L) + "\n")
        allfacts[entry] = L
        print("\n".join(L))
        print("=" * 90)

if __name__ == "__main__":
    main()
