# -*- coding: utf-8 -*-
"""辅助函数体 + 全局对象 vptr 安装点定位。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

def dump_func(ea, maxn=90, note=""):
    data = va_read(ea, 400)
    insns = list(np_core._md.disasm(data, ea))
    print("\n--- func %s %s ---" % (hx(ea), note))
    n = 0
    for ins in insns:
        b = va_read(ins.address, ins.size).hex(" ")
        print("  %s  %-20s %-8s %s" % (hx(ins.address), b, ins.mnemonic, ins.op_str))
        n += 1
        if n >= maxn or ins.id == X86_INS_RET:
            break

for ea, note in [(0x410320, "slot6 callee"), (0x410380, "slot5 callee"),
                 (0x410960, "slot5 body call"), (0x4109C0, "slot8 body call"),
                 (0x7C8E17, "operator new?"), (0x7C8B3D, "operator delete?"),
                 (0x4101F0, "Temporal slot8 body call"), (0x7258D0, "Campaign slot8 body call")]:
    dump_func(ea, note=note)

print("\n\n######## 全局对象 vptr 安装点 ########")
# 搜索 C7 05 <abs> <vt> 形式的全局写入
def find_global_vptr_writes(abs_addr):
    out = []
    needle = b"\xC7\x05" + struct.pack("<I", abs_addr)
    st = 0
    while True:
        i = TEXT_DATA.find(needle, st)
        if i < 0: break
        vt = struct.unpack_from("<I", TEXT_DATA, i + 6)[0]
        out.append((TEXT_VA + i, vt))
        st = i + 1
    return out

for g in (0xA83CF8, 0xB0EC60, 0xA83D4C, 0x8871E0, 0xA8E7AC):
    print("\n global %s vptr writes:" % hx(g))
    ws = find_global_vptr_writes(g)
    if not ws:
        print("   (none via C7 05)")
    for wa, vt in ws:
        rs = resolve_slot_by_vt(vt, 0) if va_in(vt) else None
        print("   write@%s -> vt=%s rtti=%s" % (hx(wa), hx(vt), rs["rtti_name"] if rs else "?"))
        if rs:
            t4 = u32(vt + 0x10)
            print("      slot4(+0x10) = %s  (in_text=%s)" % (hx(t4), in_text(t4)))
