#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 独立核验 W85 的两处承重：

A. 崩溃点静态字节：gamemd.exe 0x0051C2D3 处是否为 FF 90 D4 01 00 00
   （= call dword ptr [eax+0x1D4]），并核其所属函数上下文（前后指令）。
   —— 注意：except.txt 原始件未被 W85 归档，所以只能核"静态字节"这一半，
      不能核"当时确实崩在这里"（那是丢失的运行时证据）。

B. 对照臂 CPU 消耗率：从 analysis2.json 看窗口定义与数值，再用 ndjson 独立复算。
"""
import json
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe")
CARD = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r03\W85_pressure")

print("=" * 78)
print("A · 崩溃点静态字节 0x0051C2D3")
print("=" * 78)
data = EXE.read_bytes()
pe = pefile.PE(data=data, fast_load=False)
ib = pe.OPTIONAL_HEADER.ImageBase


def foff(va):
    rva = va - ib
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError(hex(va))


va = 0x0051C2D3
o = foff(va)
got = data[o : o + 6].hex(" ").upper()
want = "FF 90 D4 01 00 00"
print(f"  0x{va:08X}  foff=0x{o:06X}  got=[{got}]  want=[{want}]  {'MATCH' if got == want else 'MISMATCH'}")

md = Cs(CS_ARCH_X86, CS_MODE_32)
print("\n  --- 该点前后 12 条指令 ---")
start = va - 40
for insn in md.disasm(data[foff(start) : foff(start) + 96], start):
    mark = "  <<< 崩溃点" if insn.address == va else ""
    print(f"  0x{insn.address:08X}  {insn.bytes.hex():<16s} {insn.mnemonic:8s} {insn.op_str}{mark}")

print("\n" + "=" * 78)
print("B · 对照臂 CPU 消耗率（从 analysis2.json 读窗口口径）")
print("=" * 78)
a2 = json.loads((CARD / "out" / "analysis2.json").read_text(encoding="utf-8"))


def walk(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}" if path else k
            if isinstance(v, (int, float, str)) and any(
                t in k.lower() for t in ("cpu", "rate", "window", "consum", "ms_per", "elapsed")
            ):
                print(f"  {p} = {v}")
            walk(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:4]):
            walk(v, f"{path}[{i}]")


walk(a2)
