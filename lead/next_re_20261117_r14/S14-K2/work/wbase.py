#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wbase.py — S14-K2 通用反汇编底座 (capstone skipdata=True + pefile)
通道 A: 不读 function_atlas.tsv, 直接 PE 节表 + 原始字节。
"""
import pefile, struct
from capstone import *
from capstone.x86 import *

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB  = 0x400000

_pe = pefile.PE(EXE, fast_load=True)
_pe.parse_data_directories()
DATA = open(EXE, "rb").read()

SECS = []
for s in _pe.sections:
    name = s.Name.rstrip(b"\x00").decode("latin1")
    va = IB + s.VirtualAddress
    SECS.append((name, va, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))

TEXT = next(s for s in SECS if s[0] == ".text")
TEXT_VA, TEXT_VS, TEXT_RAW, TEXT_RSZ = TEXT[1], TEXT[2], TEXT[3], TEXT[4]
TEXT_END = TEXT_VA + TEXT_VS

MD = Cs(CS_ARCH_X86, CS_MODE_32)
MD.detail = True
MD.skipdata = True


def va2off(va):
    for name, v, vs, raw, rsz in SECS:
        if v <= va < v + max(vs, rsz):
            o = raw + (va - v)
            if o < len(DATA):
                return o
    return None


def rd8(va):
    o = va2off(va)
    return DATA[o] if o is not None else None


def rd16(va):
    o = va2off(va)
    return struct.unpack_from("<H", DATA, o)[0] if o is not None and o + 2 <= len(DATA) else None


def rd32(va):
    o = va2off(va)
    return struct.unpack_from("<I", DATA, o)[0] if o is not None and o + 4 <= len(DATA) else None


def bytes_at(va, n):
    o = va2off(va)
    return DATA[o:o + n] if o is not None else b""


def disasm(va, nbytes, stop_ret=True):
    """从 va 反汇编 nbytes, 返回 [(addr, mnemonic, op_str, insn)]"""
    out = []
    code = bytes_at(va, nbytes)
    for i in MD.disasm(code, va):
        out.append((i.address, i.mnemonic, i.op_str, i))
        if stop_ret and i.mnemonic in ("ret", "retf") and i.address > va:
            break
    return out


def disasm_range(va, end):
    return disasm(va, end - va, stop_ret=False)


def in_text(va):
    return TEXT_VA <= va < TEXT_END


def sections_dump():
    for name, v, vs, raw, rsz in SECS:
        print(f"{name:12s} VA=0x{v:08X} VS=0x{vs:X} raw=0x{raw:X} rsz=0x{rsz:X}")


if __name__ == "__main__":
    sections_dump()
    print("TEXT VA 0x%08X .. 0x%08X" % (TEXT_VA, TEXT_END))
    print("HouseClass::Update 0x4F8440 first bytes:", bytes_at(0x4F8440, 16).hex())
