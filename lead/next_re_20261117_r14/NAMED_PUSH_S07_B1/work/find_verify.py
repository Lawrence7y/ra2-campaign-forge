# -*- coding: utf-8 -*-
"""验证 slot8/slot0 析构行的 Find(-1) 可伪证性：
对每条行的 call [reg+0x10]，解析容器全局的活 vptr(构造器写) -> vt+0x10 = Find 函数，
核对其体内是否有 `or eax,-1` (83 C8 FF) 与命中返下标，从而证明 -1 哨兵来自字节。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import witness_core as W

# (entry, [(全局VA, call_site), ...])
ROWS = {
  "00421730": [(0x88A0F0,0x00421763),(0xB0F720,0x004217AC)],
  "004370C0": [(0x8B4190,0x00437107)],
  "00491210": [(0x89ECF8,0x00491261)],
  "00555150": [(0xABCA10,0x0055518A)],
}
def find_func_bytes(va, n=64):
    return R.read_va(va, n)

def find_live_vptr(global_va):
    """返回 global 处的 dword 值(运行时初值 vptr)；卡片禁动态执行，读 .data 静态初值。"""
    return W.u32(global_va)

for e, sites in ROWS.items():
    print("="*90)
    print("ROW", e)
    for g, cs in sites:
        vt = find_live_vptr(g)
        print("  global %08X @ call %08X -> live vptr = %s" % (g, cs, ("%08X"%vt) if vt else "None"))
        if vt:
            findva = W.u32(vt+0x10)
            print("    vt+0x10 = Find = %s" % ("%08X"%findva) if findva else "    vt+0x10 unreadable")
            if findva and R.in_text(findva):
                code = find_func_bytes(findva, 96)
                # 找 or eax,-1 (83 C8 FF) 和 ret
                has_or = b"\x83\xc8\xff" in code
                # 打印前 40 指令
                insns = R.disasm(findva, code)
                or_sites = []
                ret_sites = []
                cmp_sites = []
                for ins in insns:
                    if ins.id == 0: continue
                    if ins.mnemonic == "or" and "eax" in ins.op_str and "-1" in ins.op_str:
                        or_sites.append("%08X %s %s | %s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex()))
                    if ins.id == 0x00 and ins.mnemonic.startswith("ret") or ins.mnemonic.startswith("ret"):
                        ret_sites.append("%08X %s | %s"%(ins.address,ins.mnemonic,ins.bytes.hex()))
                    if ins.mnemonic == "cmp" and "[" in ins.op_str:
                        cmp_sites.append("%08X %s %s"%(ins.address,ins.mnemonic,ins.op_str))
                print("    has_or_eax_ff(bytes)=%s or_sites=%s" % (has_or, or_sites))
                print("    rets=%s" % ret_sites[:4])
                print("    cmp_mem=%s" % cmp_sites[:4])
                print("    first 12 insns of Find:")
                for ins in insns[:12]:
                    print("      %08X: %s %s | %s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex()))
