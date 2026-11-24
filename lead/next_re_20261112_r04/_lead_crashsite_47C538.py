#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead：定位新鲜崩溃现场 EIP=0x0047C538 所属函数与其调用者。

字节 FF 50 2C = call dword ptr [eax+0x2C]，随后 cmp eax,6 / mov esi,[esi+0x30] / loop。
[esi+0x30] = ObjectClass::NextObject 的典型形态 ⇒ 疑似又一次 CellClass 对象链表遍历。
"""
import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs
from pathlib import Path

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe")
data = EXE.read_bytes()
pe = pefile.PE(data=data, fast_load=False)
ib = pe.OPTIONAL_HEADER.ImageBase


def foff(va):
    rva = va - ib
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError(hex(va))


eip = 0x0047C538
print("=" * 78)
print(f"EIP = 0x{eip:08X}   bytes@{foff(eip):06X} = {data[foff(eip):foff(eip)+6].hex(' ').upper()}")
print("=" * 78)

# 1) 反汇编 EIP 前后
start = eip - 0x40
md = Cs(CS_ARCH_X86, CS_MODE_32)
print("--- EIP 前后 ---")
for insn in md.disasm(data[foff(start):foff(start) + 0x90], start):
    mark = "  <<< EIP" if insn.address == eip else ""
    print(f"0x{insn.address:08X}  {insn.bytes.hex():<18s} {insn.mnemonic:8s} {insn.op_str}{mark}")

# 2) 找函数入口：向前找常见序言（55 8B EC / 83 EC ?? / 8B FF 55 8B EC / 53 8B ...）
print("\n--- 向前找函数序言（0x300 字节内） ---")
cands = []
for back in range(1, 0x300):
    va = eip - back
    b = data[foff(va):foff(va) + 3]
    if b in (b"\x55\x8b\xec", b"\x8b\xff\x55", b"\x53\x8b\xdc", b"\x56\x8b\xf4"):
        cands.append((va, b.hex()))
for va, h in cands[-6:]:
    print(f"  0x{va:08X}  {h}")

# 3) 找对 EIP 所在函数的引用（用候选入口地址搜小端）
print("\n--- 候选入口的小端全文件命中数 ---")
for va, h in cands[-3:]:
    pat = va.to_bytes(4, "little")
    n = data.count(pat)
    offs = []
    st = 0
    while True:
        i = data.find(pat, st)
        if i < 0:
            break
        offs.append(i)
        st = i + 1
    print(f"  0x{va:08X} ({h}) 命中 {n} 处: {[hex(o) for o in offs[:6]]}")
