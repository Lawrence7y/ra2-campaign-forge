#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""兜底核对：在 .text 原始字节里搜 IAT 槽地址的小端字节，以及 GetProcAddress/delay-load 迹象。
避免依赖 capstone 操作数解读。"""
from pathlib import Path

import pefile

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe")
IATS = {
    "DialogBoxParamA": 0x007E13D4,
    "DialogBoxIndirectParamA": 0x007E13D8,
    "CreateDialogIndirectParamA": 0x007E1450,
    "CreateDialogParamA": 0x007E1508,
}

data = EXE.read_bytes()
pe = pefile.PE(data=data, fast_load=False)
image_base = pe.OPTIONAL_HEADER.ImageBase

sections = {}
for s in pe.sections:
    n = s.Name.rstrip(b"\x00").decode("ascii", "replace")
    sections[n] = (image_base + s.VirtualAddress, s.get_data())
    print(f"{n:10s} VA=0x{image_base + s.VirtualAddress:08X} vsize={len(s.get_data())}")

text_va, text = sections[".text"]
print()
for name, iat in IATS.items():
    pat = iat.to_bytes(4, "little")
    offs = []
    start = 0
    while True:
        i = text.find(pat, start)
        if i < 0:
            break
        offs.append(i)
        start = i + 1
    print(f"{name:28s} IAT=0x{iat:08X}  .text raw hits={len(offs)} -> " +
          ", ".join(f"off 0x{o:06X}/VA 0x{text_va + o:08X}" for o in offs[:12]))
    if len(offs) > 12:
        print(f"   ... 还有 {len(offs) - 12} 处")

print()
# GetProcAddress / LoadLibrary 迹象 + 字符串里是否有 Dialog 名字（delay-load / 动态解析）
for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []) or []:
    dll = entry.dll.decode("ascii", "replace")
    names = {imp.name.decode("ascii", "replace") for imp in entry.imports if imp.name}
    for probe in ("GetProcAddress", "LoadLibraryA", "LoadLibraryExA", "LdrGetProcedureAddress"):
        if probe in names:
            print(f"IMPORT {probe} from {dll}")

raw = data
for s in (b"DialogBoxParamA", b"CreateDialogIndirectParamA", b"DialogBoxIndirectParamA"):
    print(f"string {s!r}: {'present' if s in raw else 'absent'}")

# 是否有 delay-load 目录
if hasattr(pe, "DIRECTORY_ENTRY_DELAY_IMPORT"):
    for e in pe.DIRECTORY_ENTRY_DELAY_IMPORT:
        print("DELAY_IMPORT", e.dll.decode("ascii", "replace"), len(e.imports))
else:
    print("no delay-import directory")
