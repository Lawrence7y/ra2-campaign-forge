#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""静态验证 RTTI 链：用 pefile 把 VA 映射到文件偏移，做只读 u8/u16/u32。
验证 BUILDING_VT=0x7E3EBC 以及 OBJECT_class 等已知 vt 的 COL+0xC->TD+8 链。
"""
import os
import pefile

GAME = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(GAME, fast_load=True)
DATA = open(GAME, "rb").read()
IB = pe.OPTIONAL_HEADER.ImageBase


def va2off(va):
    rva = va - IB
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            off = s.PointerToRawData + (rva - s.VirtualAddress)
            if off < len(DATA):
                return off
    return None


class FMem:
    def u8(self, va):
        o = va2off(va)
        return DATA[o] if o is not None else None

    def u16(self, va):
        o = va2off(va)
        return int.from_bytes(DATA[o:o+2], "little") if o is not None else None

    def u32(self, va):
        o = va2off(va)
        return int.from_bytes(DATA[o:o+4], "little") if o is not None and o+4 <= len(DATA) else None


import dsnap

VTS = {
    "BuildingClass": 0x7E3EBC,
    # 更多候选稍后从 vftable 表取；这里先验证一个
}

m = FMem()
for label, vt in VTS.items():
    # 模拟 obj: 构造一个只含 vptr 的伪对象，vptr=vt
    class FakeObj:
        pass
    # 直接走链：vptr=vt -> col=dword[vt-4]
    col = m.u32(vt - 4)
    td = m.u32(col + 0xC) if col else None
    name = b""
    if td:
        for i in range(96):
            v = m.u8(td + 8 + i)
            if v is None or v == 0:
                break
            name += bytes([v])
    print("%-16s vt=0x%08X col=%s td=%s name=%s" % (
        label, vt, hex(col) if col else None, hex(td) if td else None,
        name.decode("latin-1", "replace")))
