#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 独立核验 W86 的承重断言（只读）。

1. ddraw.ini 是否存在 [gamemd] 段、其中 maxfps 值
2. ddraw.dll 四条承重字节序列
   - 0x10006884: a1 e8 94 05 10   mov eax,[0x100594E8]   (maxfps 读)
   - 0x1001E17D: a3 e8 94 05 10   mov [0x100594E8], eax  (maxfps 写)
   - 0x1001B01A: a3 20 f1 05 10   mov [0x1005F120], eax  (last_t 写 之一)
   - 0x10006D6C: 8b 15 20 f1 05 10 mov edx,[0x1005F120]  (last_t 读)
3. ddraw.dll 的 DllCharacteristics 是否含 DYNAMICBASE (0x0040)
4. ddraw.dll 里 0x1005F120 的出现次数（应=写入+读取点）
"""
from pathlib import Path

import pefile

INI = Path(r"D:\Project\ra2-campaign-forge\ra2youli\ddraw.ini")
DLL = Path(r"D:\Project\ra2-campaign-forge\ra2youli\ddraw.dll")


def show_ini():
    print("=" * 78)
    print("1 · ddraw.ini 的 [gamemd] 段")
    print("=" * 78)
    raw = INI.read_bytes()
    txt = raw.decode("utf-8", "replace")
    print(f"  bytes={len(raw)}  lines={txt.count(chr(10))+1}")
    lines = txt.splitlines()
    in_gam = False
    found = False
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if s.startswith("[") and s.endswith("]"):
            in_gam = s.lower() == "[gamemd]"
            if in_gam:
                found = True
                print(f"  L{i}: {s}   <-- 段开始")
            continue
        if in_gam:
            print(f"  L{i}: {s}")
    if not found:
        print("  !! 未找到 [gamemd] 段")
    # 也打印全局 [ddraw] 段的 maxfps
    print("\n  --- 全局 maxfps 行（任意段） ---")
    for i, ln in enumerate(lines, 1):
        if "maxfps" in ln and not ln.strip().startswith(";"):
            print(f"  L{i}: {ln.strip()}")


def main_dll():
    data = DLL.read_bytes()
    pe = pefile.PE(data=data, fast_load=False)
    ib = pe.OPTIONAL_HEADER.ImageBase
    print()
    print("=" * 78)
    print("2-4 · ddraw.dll")
    print("=" * 78)
    print(f"  ImageBase=0x{ib:08X}  size={len(data)}")
    dch = pe.OPTIONAL_HEADER.DllCharacteristics
    print(f"  DllCharacteristics=0x{dch:04X}  DYNAMICBASE={'YES' if dch & 0x40 else 'NO'}")

    def foff(va):
        rva = va - ib
        for s in pe.sections:
            if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
                return s.PointerToRawData + (rva - s.VirtualAddress), s.Name.rstrip(b"\0").decode()
        raise ValueError(hex(va))

    checks = [
        (0x10006884, "a1e8940510", "mov eax,[0x100594E8]  (maxfps 读)"),
        (0x1001E17D, "a3e8940510", "mov [0x100594E8],eax  (maxfps 写)"),
        (0x1001B01A, "a320f10510", "mov [0x1005F120],eax  (last_t 写)"),
        (0x10006D6C, "8b1520f10510", "mov edx,[0x1005F120]  (last_t 读)"),
    ]
    for va, want, label in checks:
        o, sec = foff(va)
        got = data[o : o + len(want) // 2].hex()
        print(
            f"  0x{va:08X} sec={sec:6s} foff=0x{o:06X} got={got} want={want} "
            f"{'MATCH' if got == want else 'MISMATCH'}   {label}"
        )

    # 全文件搜 0x1005F120 / 0x100594E8 的小端出现次数
    for name, va in (("0x1005F120(last_t)", 0x1005F120), ("0x100594E8(maxfps)", 0x100594E8)):
        pat = va.to_bytes(4, "little")
        n = data.count(pat)
        print(f"  小端 {name} 全文件出现 {n} 次")


if __name__ == "__main__":
    show_ini()
    main_dll()
