# -*- coding: utf-8 -*-
"""确认 00414290 被调 0x410260 的 HRESULT 返回（失败可伪证），作为 ③b② 证据。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

# 0xa8e968 / 0xa8b218 是运行时全局对象指针，落在 .data 未初始化区
# (VirtualSize 0x367be4 > RawSize 0x6c000)，静态不可读。
# 00410C30/0041CFE0 的可伪证性由调用点 cmp eax,-1 哨兵提供。
print("=== callee 0x410260 (00414290 的被调) ===")
for ins in MD.disasm(R.read_va(0x410260,160),0x410260):
    print("  %08X: %-8s %s | %s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex()))
