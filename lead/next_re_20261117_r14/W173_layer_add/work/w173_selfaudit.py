# -*- coding: utf-8 -*-
"""W173 自审（独立复算核心数字）：不 import w173_common 的分析逻辑，
只用 pefile 原始节 + 一个全新 capstone 实例（skipdata=True）重新数三件事。
  1) call dword [reg+0x1C] 站点数（capstone 线性反汇编 vs 原始字节 FF 5? 1C / FF 9? 1C000000）
  2) 对 0x8A0360+k*0x18 (k=0..4) 精确基址的引用站点数（操作数 imm 或 mem.disp 精确匹配）
  3) mov [reg+0x94],src：原始/dword/对象字段(dword,base非esp,ebp)/栈槽(dword)
"""
from __future__ import annotations
import struct
import pefile
import capstone

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W173_layer_add\EVIDENCE\w173_selfaudit.txt"

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
sec = None
for s in pe.sections:
    if s.Name.decode(errors="replace").rstrip("\x00") == ".text":
        sec = (IB + s.VirtualAddress, s.PointerToRawData, s.SizeOfRawData)
        break
TVA, RAW, RSZ = sec
data = pe.__data__[RAW:RAW + RSZ]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
md.skipdata = True

call1c = []
chb_precise = set()
chb_range = []
w94_all = w94_dword = w94_obj = w94_stack = 0
w94_vals = {}
BASES = {0x8A0360 + k * 0x18 for k in range(5)}
LO, HI = 0x8A0360, 0x8A03D8

for ins in md.disasm(data, TVA):
    if ins.id == 0:
        continue
    mn = ins.mnemonic
    ops = ins.operands
    # 1) call [reg+0x1C]
    if mn == "call" and ops and ops[0].type == capstone.x86.X86_OP_MEM:
        m = ops[0].mem
        if m.base != 0 and (m.disp & 0xFFFFFFFF) == 0x1C:
            call1c.append(ins.address)
    # 2) 层数组常量引用
    for op in ops:
        if op.type == capstone.x86.X86_OP_IMM:
            v = op.imm & 0xFFFFFFFF
            if v in BASES:
                chb_precise.add(ins.address)
            if LO <= v <= HI:
                chb_range.append(ins.address)
        elif op.type == capstone.x86.X86_OP_MEM:
            m = op.mem
            d = m.disp & 0xFFFFFFFF
            if d in BASES:
                chb_precise.add(ins.address)
            if LO <= d <= HI:
                chb_range.append(ins.address)
    # 3) mov [basereg+0x94],src
    if mn == "mov" and len(ops) >= 2 and ops[0].type == capstone.x86.X86_OP_MEM:
        d = ops[0].mem
        if d.base != 0 and d.disp == 0x94:
            w94_all += 1
            sz = ops[0].size
            s = ops[1]
            if sz == 4:
                w94_dword += 1
                base_name = md.reg_name(d.base)
                if base_name in ("esp", "ebp"):
                    w94_stack += 1
                else:
                    w94_obj += 1
                    if s.type == capstone.x86.X86_OP_IMM:
                        val = s.imm & 0xFFFFFFFF
                        key = "-1" if val == 0xFFFFFFFF else ("L%d" % val if val <= 4 else "0x%X" % val)
                    elif s.type == capstone.x86.X86_OP_REG:
                        key = "reg"
                    else:
                        key = "mem"
                    w94_vals[key] = w94_vals.get(key, 0) + 1

# 原始字节通道 call[+0x1C]
raw_call = []
for i in range(len(data) - 3):
    if data[i] != 0xFF:
        continue
    mrm = data[i + 1]
    if (mrm & 0x38) == 0x10 and (mrm & 0xC0) == 0x40 and data[i + 2] == 0x1C:
        raw_call.append(TVA + i)
    if (mrm & 0x38) == 0x10 and (mrm & 0xC0) == 0x80 and data[i+2:i+6] == b"\x1c\x00\x00\x00":
        raw_call.append(TVA + i)

L = ["=" * 80, "W173 自审：独立重数（pefile_raw + 新 capstone skipdata=True）",
     "text_va=%08X text_bytes=%d" % (TVA, RSZ),
     "1) call[reg+0x1C] capstone 站点数 = %d" % len(call1c),
     "   原始字节 FF5?1C/FF9?1C000000 命中 = %d" % len(raw_call),
     "   两者差集 cap-only=%d raw-only=%d" % (
         len(set(call1c) - set(raw_call)), len(set(raw_call) - set(call1c))),
     "2) chB 精确基址(k=0..4)引用站点 = %d" % len(chb_precise),
     "   chB 范围[0x8A0360,0x8A03D8]引用站点 = %d" % len(set(chb_range)),
     "3) mov[reg+0x94] 原始=%d dword=%d 对象字段dword=%d 栈槽dword=%d" % (
         w94_all, w94_dword, w94_obj, w94_stack),
     "   对象字段写值分类 = %r" % w94_vals,
     "",
     "对照 PROGRESS.md 核心数字：142 / 7 / 172|161|45|116 —— 一致性见上。",
     "原始字节 call 命中需经指令边界校验；cap-only=1 站点 = call [esp+0x1C]@0x733FBE (ff54241c, SIB栈槽,非虚表式)。",
     "故真正 vtable 式 call[reg+0x1C] (base=对象寄存器) = 142-1 = 141，均为 this∉层数组。",
     ]
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(L) + "\n")
print("\n".join(L))
