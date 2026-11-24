#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""正确 VA 映射地反汇编 [0x1005EE48] 的全部 4 处引用，并检查是否有 A3 形态写入。"""
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

DLL = Path(r"D:\Project\ra2-campaign-forge\ra2youli\ddraw.dll")
data = DLL.read_bytes()
pe = pefile.PE(data=data, fast_load=False)
ib = pe.OPTIONAL_HEADER.ImageBase
ADDR = 0x1005EE48
pat = ADDR.to_bytes(4, "little")

secs = []
for s in pe.sections:
    secs.append((s.Name.rstrip(b"\0").decode(), s.VirtualAddress, s.PointerToRawData,
                 max(s.Misc_VirtualSize, s.SizeOfRawData)))
    print(f"{secs[-1][0]:10s} RVA=0x{s.VirtualAddress:06X} raw=0x{s.PointerToRawData:06X} size=0x{secs[-1][3]:06X}")


def off2va(off):
    for name, rva, raw, size in secs:
        if raw <= off < raw + size:
            return ib + rva + (off - raw), name
    return None, None


def va2off(va):
    rva = va - ib
    for name, srva, raw, size in secs:
        if srva <= rva < srva + size:
            return raw + (rva - srva)
    return None


md = Cs(CS_ARCH_X86, CS_MODE_32)

hits = []
st = 0
while True:
    i = data.find(pat, st)
    if i < 0:
        break
    hits.append(i)
    st = i + 1

print(f"\n命中 {len(hits)} 处，逐个按正确 VA 反汇编上下文：\n")
for off in hits:
    va, sec = off2va(off)
    start = va - 0x20
    o = va2off(start)
    blob = data[o : o + 0x50]
    print(f"=== off 0x{off:06X} VA 0x{va:08X} ({sec}) ===")
    for insn in md.disasm(blob, start):
        mark = "  <<< 引用点" if insn.address <= va < insn.address + len(insn.bytes) else ""
        print(f"  0x{insn.address:08X}  {insn.bytes.hex():<22s} {insn.mnemonic:8s} {insn.op_str}{mark}")
        if insn.address > va + 0x10:
            break
    print()

# A3 形态：mov [abs], eax
print("=== 找 'a3 48 ee 05 10'（mov [0x1005EE48], eax） ===")
pat_a3 = b"\xa3" + pat
print("命中", data.count(pat_a3), "处")

# 附近 .data 变量清单（看 0x1005EE40..0x1005EE60 有哪些常量）
print("\n=== 该全局前后 0x20 字节的内容（文件静态初值，全 0 = .data 零初始化） ===")
o = va2off(ADDR)
print("  bytes:", data[o - 0x20 : o + 0x20].hex(" "))
