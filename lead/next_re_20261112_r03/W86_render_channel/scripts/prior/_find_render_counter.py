# -*- coding: utf-8 -*-
"""在 cnc-ddraw (ddraw.dll) 里找「每帧递增」的计数器候选。

思路：
  1. capstone 线性扫描 .text，收集 `inc dword ptr [abs]`（FF 05 disp32）与
     `add dword ptr [abs], imm`（83 05 / 81 05）等写全局的指令；
  2. 按目标全局地址聚合，统计每个全局被写的次数与所在函数附近的线索；
  3. 特别关注 maxfps 相关：搜索立即数 0x3C(60) 的比较/乘法附近出现的全局。
只读磁盘，不启动进程。
"""
import struct
from collections import defaultdict

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_INVALID

P = r"D:\Project\ra2-campaign-forge\ra2youli\ddraw.dll"
pe = pefile.PE(P, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
d = open(P, "rb").read()
secs = {s.Name.rstrip(b"\x00").decode("latin1"): s for s in pe.sections}
t = secs[".text"]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

text = d[t.PointerToRawData: t.PointerToRawData + t.SizeOfRawData]
tva = IB + t.VirtualAddress


def rva_of(va):
    return va - IB


print("=" * 78)
print("ddraw.dll  ImageBase=0x%08X  .text VA=0x%08X size=%d" % (IB, tva, len(text)))

writes = defaultdict(list)   # global_va -> [(insn_addr, mnem, opstr, kind)]
imm60_sites = []

for ins in md.disasm(text, tva):
    # 记录含立即数 60 的指令（maxfps 线索）
    for op in ins.operands:
        if op.type == X86_OP_IMM and op.imm == 60:
            imm60_sites.append(ins)
            break
    if not ins.operands:
        continue
    dst = ins.operands[0]
    if dst.type != X86_OP_MEM:
        continue
    if dst.mem.base != X86_REG_INVALID or dst.mem.index != X86_REG_INVALID:
        continue
    gva = dst.mem.disp
    if ins.mnemonic in ("inc", "dec"):
        kind = "inc" if ins.mnemonic == "inc" else "dec"
    elif ins.mnemonic == "add" and len(ins.operands) > 1 and ins.operands[1].type == X86_OP_IMM:
        kind = "add"
    elif ins.mnemonic == "mov":
        kind = "mov"
    else:
        continue
    writes[gva].append((ins.address, ins.mnemonic, ins.op_str, kind, ins.bytes.hex(" ")))

# 排序：inc 次数多的优先
inc_only = {g: v for g, v in writes.items() if any(x[3] == "inc" for x in v)}
print("\n含 inc 的全局数 =", len(inc_only))
ranked = sorted(inc_only.items(), key=lambda kv: -len(kv[1]))
print("\n前 25 个「被 inc 最多」的全局（候选帧计数）：")
print("  %-12s %-5s %s" % ("global", "n_inc", "样例指令"))
for gva, lst in ranked[:25]:
    incs = [x for x in lst if x[3] == "inc"]
    sec = None
    rva = rva_of(gva)
    for n, s in secs.items():
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            sec = n
            break
    print("  0x%08X  %-5d %-8s %s @0x%X" % (gva, len(incs), sec, incs[0][2], incs[0][0]))

print("\n" + "=" * 78)
print("含立即数 60 (0x3C) 的指令数 =", len(imm60_sites))
for ins in imm60_sites[:15]:
    print("  0x%08X  %-22s %s %s" % (ins.address, ins.bytes.hex(" "), ins.mnemonic, ins.op_str))
print("=" * 78)
print("说明：只读磁盘；未启动游戏。")
