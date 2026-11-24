# -*- coding: utf-8 -*-
"""在 gamemd.exe 里找「被 inc 的绝对全局」，并标注哪些其邻近有 ddraw 相关调用。

用途：为「渲染帧计数」找候选。只读磁盘。
"""
import struct
from collections import defaultdict

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_REG_INVALID

P = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
pe = pefile.PE(P)
IB = pe.OPTIONAL_HEADER.ImageBase
d = open(P, "rb").read()
secs = {s.Name.rstrip(b"\x00").decode("latin1"): s for s in pe.sections}
t = secs[".text"]
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
text = d[t.PointerToRawData: t.PointerToRawData + t.SizeOfRawData]
tva = IB + t.VirtualAddress

# IAT: ddraw 相关导入
ddraw_slots = set()
for e in pe.DIRECTORY_ENTRY_IMPORT:
    if "ddraw" in e.dll.decode().lower():
        for i in e.imports:
            ddraw_slots.add(i.address)
print("ddraw 相关 IAT 槽数:", len(ddraw_slots))

inc_globals = defaultdict(list)
ddraw_callsites = []
prev_few = []

for ins in md.disasm(text, tva):
    # 记 ddraw 调用点
    if ins.mnemonic == "call" and ins.operands and ins.operands[0].type == X86_OP_MEM:
        m = ins.operands[0].mem
        if m.disp in ddraw_slots:
            ddraw_callsites.append(ins.address)
    if ins.operands:
        dst = ins.operands[0]
        if (dst.type == X86_OP_MEM and dst.mem.base == X86_REG_INVALID
                and dst.mem.index == X86_REG_INVALID and ins.mnemonic == "inc"):
            inc_globals[dst.mem.disp].append(ins.address)

print("被 inc 的绝对全局数:", len(inc_globals))
ddraw_set = set(ddraw_callsites)
print("ddraw 直接调用点:", len(ddraw_callsites))

rows = []
for gva, sites in inc_globals.items():
    near = 0
    for s in sites:
        for c in ddraw_callsites:
            if abs(c - s) < 0x400:
                near += 1
                break
    rows.append((gva, len(sites), near))

rows.sort(key=lambda r: (-r[2], -r[1]))
print("\n前 20 个候选（按「附近有 ddraw 调用的 inc 点数」排序）:")
print("  %-12s %-6s %-6s %s" % ("global", "n_inc", "near", "所在节"))
for gva, n, near in rows[:20]:
    rva = gva - IB
    sec = None
    for nm, s in secs.items():
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            sec = nm
            break
    print("  0x%08X  %-6d %-6d %s" % (gva, n, near, sec))

# 已知字段对照
known = {0xA8ED84: "帧计数(32ms定拍)", 0xA8ED50: "候选BulletCnt", 0xB0CE88: "候选脏矩形",
         0x87E8E0: "候选代际"}
print("\n已知字段在本次普查中的位置:")
for gva, name in known.items():
    n = len(inc_globals.get(gva, []))
    print("  0x%08X  inc 点=%d   %s" % (gva, n, name))
print("\n说明：只读磁盘；未启动游戏。")
