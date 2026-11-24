# -*- coding: utf-8 -*-
"""环④：主虚表 007E3EBC 的 .text 安装点，判 ctor vs atexit 析构器（㉓）。"""
import os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

MAIN_VT = 0x007E3EBC

def decode_install(va):
    """给 c7_05 / c7_rm / reg_load 站点所在指令反汇编一小段，返回可读形式。"""
    out = []
    for ins in C.disasm(va, 40)[:4]:
        out.append("%08X: %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))
    return out

def check_install_site(write_va):
    """写点所在函数 + 是否 atexit + 是否先调基类 ctor。"""
    base_va = write_va if write_va else None
    f = C.atlas_covering(base_va)
    res = dict(write_va="%08X" % write_va, in_func=(f[1] if f else None),
               func_size=(f[2] if f else None))
    if f:
        res["atexit"] = C.is_atexit_registered(f[0])
        res["atexit_bool"] = bool(res["atexit"])
        # 该函数内是否有构造器特征：先 call 基类 ctor（0x410170/0x410800 族）再写 vt
        insns = C.disasm(f[0], f[2])
        prior_calls = [i for i in insns if i.id == C.X86_INS_CALL and i.address < write_va
                       and i.operands and i.operands[0].type == C.X86_OP_IMM]
        res["prior_calls"] = ["%08X" % (i.operands[0].imm & 0xFFFFFFFF) for i in prior_calls[-4:]]
        res["first_insn"] = ("%08X: %s %s" % (insns[0].address, insns[0].mnemonic, insns[0].op_str)) if insns else None
    return res

if __name__ == "__main__":
    sites = C.find_vtable_imm_sites(MAIN_VT)
    print("MAIN_VT=%08X 立即数出现点：" % MAIN_VT)
    for kind in ("c7_05", "c7_rm", "reg_load"):
        print("\n-- %s (%d)" % (kind, len(sites[kind])))
        for s in sites[kind]:
            va = s.get("write_va") or s.get("load_va")
            info = check_install_site(va)
            extra = (" global=%08X" % s["global_"]) if "global_" in s else ""
            print("   %08X%s atexit=%s func=%s size=%s" %
                  (va, extra, info.get("atexit_bool"), info.get("in_func"), info.get("func_size")))
            for line in decode_install(va - 8):
                print("        " + line)
            print("        first_insn=%s prior_calls=%s" % (info.get("first_insn"), info.get("prior_calls")))
