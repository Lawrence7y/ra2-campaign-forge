# -*- coding: utf-8 -*-
"""回扫函数起点 + 构造器安装点/调用者上下文取证。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

def back_func_start(addr, maxback=0x600):
    """从 addr 向前找 ret(C3 / C2 xx xx) + 对齐填充(CC/90) 之后的位置作为函数起点。"""
    lo = max(TEXT_VA, addr - maxback)
    for p in range(addr - 1, lo, -1):
        b = va_read(p, 1)
        if not b: continue
        if b[0] == 0xC3:
            nxt = p + 1
            pad = va_read(nxt, 8)
            if pad and all(x in (0xCC, 0x90, 0x00) for x in pad[:4]):
                return nxt
        elif b[0] == 0xC2:
            if p + 3 <= addr:
                pad = va_read(p + 3, 8)
                if pad and all(x in (0xCC, 0x90, 0x00) for x in pad[:4]):
                    return p + 3
    return None

def dump(ea, end, note=""):
    print("\n--- %s..%s  %s ---" % (hx(ea), hx(end), note))
    for ins in np_core._md.disasm(va_read(ea, end - ea), ea):
        b = va_read(ins.address, ins.size).hex(" ")
        print("  %s  %-20s %-8s %s" % (hx(ins.address), b, ins.mnemonic, ins.op_str))

print("### 回扫未覆盖写点的函数起点 ###")
for w in (0x0046CC16, 0x0071A5AD, 0x0071A5DD, 0x006CE717, 0x006CE74D):
    fs = back_func_start(w)
    print("  write %s -> func_start %s" % (hx(w), hx(fs) if fs else "?"))

print("\n\n### CampaignClass 构造器候选 0046CB60 ###")
dump(0x0046CB60, 0x0046CB60 + 172, "CampaignClass ctor?")
print("\n### 其调用者上下文 006C02D1 ###")
dump(0x006C02B0, 0x006C02E0, "caller ctx")
print("\n### 0046CE10 (另一写点函数) ###")
dump(0x0046CE10, 0x0046CE10 + 0xC0, "0046CE10 head")

print("\n\n### TemporalClass 构造器候选 0071A450 ###")
dump(0x0071A450, 0x0071A450 + 138, "Temporal ctor?")
print("\n### 其调用者上下文 006C074C ###")
dump(0x006C0720, 0x006C0760, "caller ctx")
print("\n### 0071A4E0 ###")
dump(0x0071A4E0, 0x0071A4E0 + 0xC0, "0071A4E0 head")
print("\n### 其调用者上下文 006F4194 ###")
dump(0x006F4170, 0x006F41B0, "caller ctx")
print("\n### 0071A660 ###")
dump(0x0071A660, 0x0071A660 + 100, "0071A660")
