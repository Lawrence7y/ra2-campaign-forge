#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 直接查 cnc-ddraw 的 [0x1005EE48]（W90 报 clamp=210）：
- 全文件找对该地址的写入（mov [abs], imm / mov [abs], reg / 其它）
- 找读取点，看它跟谁比
- 打印所有立即数 210 (0xD2) 的写入上下文
"""
from pathlib import Path

import pefile
from capstone import CS_ARCH_X86, CS_MODE_32, Cs

DLL = Path(r"D:\Project\ra2-campaign-forge\ra2youli\ddraw.dll")
data = DLL.read_bytes()
pe = pefile.PE(data=data, fast_load=False)
ib = pe.OPTIONAL_HEADER.ImageBase
ADDR = 0x1005EE48
pat = ADDR.to_bytes(4, "little")

print(f"ImageBase=0x{ib:08X}  size={len(data)}")
print(f"目标地址 0x{ADDR:08X}，小端 {pat.hex()}，全文件命中 {data.count(pat)} 处\n")


def foff(va):
    rva = va - ib
    for s in pe.sections:
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (rva - s.VirtualAddress)
    raise ValueError(hex(va))


md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

# 收集所有出现位置
hits = []
st = 0
while True:
    i = data.find(pat, st)
    if i < 0:
        break
    hits.append(i)
    st = i + 1

for off in hits:
    # 定位到指令起点：从 off-8 开始反汇编，找覆盖到 off 的那条指令
    base = max(0, off - 10)
    va = None
    for s in pe.sections:
        if s.PointerToRawData <= off < s.PointerToRawData + max(s.SizeOfRawData, 1):
            va = ib + s.VirtualAddress + (off - s.PointerToRawData)
            sec = s.Name.rstrip(b"\0").decode()
            break
    found = None
    for insn in md.disasm(data[base:off + 6], ib + (va - off) + base if va else base):
        if insn.address <= va < insn.address + len(insn.bytes):
            found = insn
            break
    print(f"off 0x{off:06X}  VA 0x{va:08X}  sec {sec}")
    if found:
        print(f"   -> 0x{found.address:08X}: {found.bytes.hex():<20s} {found.mnemonic} {found.op_str}")
    else:
        print("   -> 未能定位到指令边界（可能是数据区）")
    print()

# 专门找 "mov dword ptr [0x1005EE48], imm32"
print("=" * 70)
print("显式找 imm 写入（C7 05 / A3 形态）")
for opcode_desc, op in (("C7 05 (mov dword ptr [abs], imm32)", None),):
    pass
i = 0
while True:
    j = data.find(b"\xc7\x05", i)
    if j < 0:
        break
    if data[j + 2 : j + 6] == pat:
        imm = int.from_bytes(data[j + 6 : j + 10], "little")
        va = None
        for s in pe.sections:
            if s.PointerToRawData <= j < s.PointerToRawData + max(s.SizeOfRawData, 1):
                va = ib + s.VirtualAddress + (j - s.PointerToRawData)
                break
        print(f"  off 0x{j:06X} VA 0x{va:08X}  mov dword ptr [0x{ADDR:08X}], 0x{imm:X} ({imm})")
    i = j + 1
