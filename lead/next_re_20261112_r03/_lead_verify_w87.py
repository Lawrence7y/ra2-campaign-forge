#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 独立核验 W87 的三处承重断言（只读，不启游戏、不改二进制）。

断言 1: 战役菜单对话框创建链
  0x0052DF48 = BA 00 EC 52 00        mov edx, 0x52EC00   (lpDialogFunc)
  0x0052DF4D = B9 94 00 00 00        mov ecx, 0x94       (资源 id 148)
  0x006226CB = FF 15 50 14 7E 00     call dword ptr [0x007E1450]  (CreateDialogIndirectParamA)
断言 2: 0x52ECB1 的 WM_COMMAND 分支只认 0x40E 与 0x686
断言 3: ra2forge/version_guard.py 的 L1_FIELDS 不含 ddraw.dll
"""
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe")
GUARD = Path(r"D:\Project\ra2-campaign-forge\ra2forge\version_guard.py")

data = EXE.read_bytes()
pe = pefile.PE(data=data, fast_load=False)
ib = pe.OPTIONAL_HEADER.ImageBase


def foff(va: int) -> int:
    for s in pe.sections:
        start = ib + s.VirtualAddress
        end = start + max(s.Misc_VirtualSize, s.SizeOfRawData)
        if start <= va < end:
            return s.PointerToRawData + (va - ib - s.VirtualAddress)
    raise ValueError(f"VA 0x{va:08X} 不在任何节")


def hexat(va: int, n: int) -> str:
    o = foff(va)
    return data[o : o + n].hex(" ").upper()


print("=" * 78)
print("断言 1 · 对话框创建链")
print("=" * 78)
expect = {
    0x0052DF48: ("BO 00 EC 52 00", "mov edx, 0x52EC00 (lpDialogFunc)"),
    0x0052DF4D: ("B9 94 00 00 00", "mov ecx, 0x94 (RT_DIALOG id=148)"),
    0x006226CB: ("FF 15 50 14 7E 00", "call dword ptr [0x007E1450] CreateDialogIndirectParamA"),
}
ok1 = True
for va, (want, label) in expect.items():
    got = hexat(va, len(want.split()))
    match = got == want
    ok1 &= match
    print(f"  0x{va:08X}  got=[{got}]  want=[{want}]  {'MATCH' if match else 'MISMATCH'}   {label}")
    print(f"            foff=0x{foff(va):06X}")

print()
print("=" * 78)
print("断言 2 · 0x52ECB1 WM_COMMAND 分支的比较常量")
print("=" * 78)
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
start_va = 0x0052ECB1
o = foff(start_va)
chunk = data[o : o + 420]
cmps = []
for insn in md.disasm(chunk, start_va):
    s = f"{insn.mnemonic} {insn.op_str}"
    if insn.mnemonic.startswith("cmp") or insn.mnemonic in ("jne", "je", "jz", "jnz", "and"):
        cmps.append((insn.address, s))
    if insn.address > start_va + 0x180:
        break
for a, s in cmps:
    print(f"  0x{a:08X}  {s}")

want_consts = {"0x40e", "0x686"}
seen = set()
for _, s in cmps:
    if s.startswith("cmp"):
        for tok in s.replace(",", " ").split():
            t = tok.strip()
            if t.startswith("0x"):
                seen.add(t.lower())
print(f"\n  cmp 常量集合 = {sorted(seen)}")
for c in want_consts:
    print(f"  含 {c}: {'YES' if c in seen else 'NO'}")
has_1771 = any(c in seen for c in ("0x6ea", "0x6eb", "0x6ec"))
print(f"  含 徽章 id (0x6ea/0x6eb/0x6ec): {'YES' if has_1771 else 'NO'}")
print(f"  ⇒ 断言 2 {'成立' if (want_consts <= seen and not has_1771) else '需人工复核'}")

print()
print("=" * 78)
print("断言 3 · version_guard.py 是否守 ddraw.dll")
print("=" * 78)
txt = GUARD.read_text(encoding="utf-8", errors="replace")
print(f"  file={GUARD} bytes={len(txt)}")
for key in ("ddraw", "DDRAW", "L1_FIELDS", "gamemd"):
    n = txt.count(key)
    print(f"  '{key}' 出现 {n} 次")
# 打印 L1_FIELDS 定义块
idx = txt.find("L1_FIELDS")
if idx >= 0:
    print("\n  --- L1_FIELDS 上下文 ---")
    print(txt[max(0, idx - 200) : idx + 900])
