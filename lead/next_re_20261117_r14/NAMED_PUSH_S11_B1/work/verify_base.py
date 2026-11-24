# -*- coding: utf-8 -*-
"""核验：基类 ctor 55A6C0 vs base dtor 55A6F0；三个 ctor 的尾部（是否 ret this）；四个 entry 的函数边界。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

def show(va, cap, label):
    print("\n== %s %s ==" % (label, hx(va)))
    ins = dis(va, read_va(va, cap))
    for i in ins:
        if i.id == 0:
            break
        mark = ""
        print("   %s  %-10s %-38s %s" % (hx(i.address), i.bytes.hex(), i.mnemonic + " " + i.op_str, mark))
        if i.id == X86_INS_RET:
            nx = read_va(i.address + i.size, 1)
            if nx[:1] in (b"\xcc", b"\x90", b""):
                break

show(0x0055A6C0, 0x80, "base ctor?")
show(0x0055A6F0, 0x80, "base dtor?")

print("\n== ctor tails ==")
for va in (0x004AF540, 0x004B5AB0, 0x0054AC40):
    at = atlas_func_of(va)
    print(" %s atlas=%s size=%s" % (hx(va), hx(at[0]) if at else None, at[1] if at else None))
    body = dis(va, read_va(va, at[1] if at else 0x200))
    tail = [i for i in body if i.id != 0][-6:]
    for i in tail:
        print("     %s  %-10s %s" % (hx(i.address), i.bytes.hex(), i.mnemonic + " " + i.op_str))

print("\n== 4 个 entry 的用户边界（atlas）==")
for ea in (0x004AF720, 0x004B62C0, 0x004B6470, 0x0054DC60):
    at = atlas_func_of(ea)
    print(" %s atlas=%s size=%s  first=%s" % (
        hx(ea), hx(at[0]) if at else None, at[1] if at else None,
        (dis(ea, read_va(ea, 8))[0].mnemonic + " " + dis(ea, read_va(ea, 8))[0].op_str) if dis(ea, read_va(ea, 8)) else None))
    if at:
        body = dis(ea, read_va(ea, at[1]))
        tail = [i for i in body if i.id != 0][-4:]
        for i in tail:
            print("       %s  %-10s %s" % (hx(i.address), i.bytes.hex(), i.mnemonic + " " + i.op_str))
