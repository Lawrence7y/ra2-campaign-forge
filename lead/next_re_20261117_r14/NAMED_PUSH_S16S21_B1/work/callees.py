# -*- coding: utf-8 -*-
"""被调返约定取证：0x410380 / 0x410320 完整体；VectorClass slot4 候选。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

def dump(ea, end, note=""):
    print("\n--- %s..%s %s ---" % (hx(ea), hx(end), note))
    insns = list(np_core._md.disasm(va_read(ea, end - ea), ea))
    for ins in insns:
        b = va_read(ins.address, ins.size).hex(" ")
        print("  %s  %-20s %-8s %s" % (hx(ins.address), b, ins.mnemonic, ins.op_str))

dump(0x410380, 0x4103F0, "slot5 callee full")
dump(0x410320, 0x410380, "slot6 callee full")
dump(0x4101C0, 0x4101F0, "0x410960 calls this")
dump(0x004EC530, 0x004EC560, "DynamicVectorClass<CampaignClass*>::slot4")
dump(0x004EC420, 0x004EC450, "VectorClass<CampaignClass*>::slot4")
dump(0x0071B4D0, 0x0071B500, "DynamicVectorClass<TemporalClass*>::slot4")
dump(0x0071B3C0, 0x0071B3F0, "VectorClass<TemporalClass*>::slot4")

print("\n### 全局 vptr 安装点上下文 ###")
for wa in (0x004E6EFD, 0x004E6F28, 0x0071A3ED, 0x0071A418):
    dump(wa - 10, wa + 20, "install ctx")
