#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""核查 gamemd.exe 的 .detour 段到底是什么：全零填充？代码？跳板？

背景：YR 零售 gamemd.exe 通常没有名为 .detour 的段。本项目基线哈希
73201cc0… 被当作"官方未打补丁原版"的锚，若该段是外来注入，则基线前提要重估。
"""
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe")
data = EXE.read_bytes()
pe = pefile.PE(data=data, fast_load=False)
image_base = pe.OPTIONAL_HEADER.ImageBase

print(f"image_base=0x{image_base:08X} size={len(data)}")
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode("ascii", "replace")
    print(
        f"{name:10s} VA=0x{image_base + s.VirtualAddress:08X} "
        f"VSize=0x{s.Misc_VirtualSize:06X} RSize=0x{s.SizeOfRawData:06X} "
        f"PtrRaw=0x{s.PointerToRawData:06X} Characteristics=0x{s.Characteristics:08X}"
    )

print("\n=== section names seen in PE header ===")
print([s.Name.rstrip(b"\x00").decode("ascii", "replace") for s in pe.sections])

det = None
for s in pe.sections:
    if s.Name.rstrip(b"\x00").decode("ascii", "replace") == ".detour":
        det = s
        break
if det is None:
    raise SystemExit("no .detour")

blob = det.get_data()
va = image_base + det.VirtualAddress
print(f"\n.detour VA=0x{va:08X} len={len(blob)}")
nonzero = sum(1 for b in blob if b)
print(f"nonzero_bytes={nonzero} ({nonzero/len(blob):.2%})")
print("first 64 bytes:", blob[:64].hex())
print("last 64 bytes:", blob[-64:].hex())

# 非零区间分布
runs = []
i = 0
while i < len(blob):
    if blob[i]:
        j = i
        while j < len(blob) and blob[j]:
            j += 1
        runs.append((i, j))
        i = j
    else:
        i += 1
print(f"nonzero runs={len(runs)}")
for a, b in runs[:10]:
    print(f"  VA 0x{va + a:08X} .. 0x{va + b - 1:08X} ({b - a} B)  {blob[a:min(b, a + 48)].hex()}")

# 反汇编非零区
if runs:
    md = Cs(CS_ARCH_X86, CS_MODE_32)
    a, b = runs[0]
    print("\n=== disasm of first nonzero run ===")
    for insn in md.disasm(blob[a:b], va + a):
        print(f"0x{insn.address:08X}  {insn.mnemonic:8s} {insn.op_str}")
        if insn.address - (va + a) > 200:
            break
