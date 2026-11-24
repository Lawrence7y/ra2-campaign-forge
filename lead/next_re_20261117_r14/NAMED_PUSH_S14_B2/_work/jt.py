# -*- coding: utf-8 -*-
"""核 006E9140 的 ③b① 跳转表：表地址 0x6E9F74、65 项、每路目标块首尾可辨。
输出 _work/jt_006E9140.txt：逐项目标 + 该块首 3 条 + 终止指令 + 块内 call 目标。
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2
from capstone import *
from capstone.x86 import *

WORK = os.path.dirname(os.path.abspath(__file__))
TABLE = 0x6E9F74
N = 65
JMP = 0x6E945B
BOUND = 0x6E944B      # cmp eax,0x40
JA = 0x6E9455         # ja 0x6e95ab

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

lines = []
def P(*a):
    lines.append(" ".join(str(x) for x in a))

# 边界检查字节
P("== 边界检查 ==")
for va in (BOUND, JA, JMP):
    ins = list(md.disasm(R.read_va(va, 8), va))[0]
    P("  %08X  %-20s %-8s %s   (in .text=%s)" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, R.in_text(va)))

P("== 跳表 %08X (%d 项, 在 .text=%s) ==" % (TABLE, N, R.in_text(TABLE)))
targets = []
for c in range(N):
    t = C2.u32(TABLE + 4 * c)
    ok = t is not None and R.in_text(t)
    targets.append(t)
    P("  case %2d (0x%02X) slot=%08X -> %s %s" % (c, c, TABLE + 4 * c,
      ("%08X" % t) if t else "None", "" if ok else "<<NOT .text>>"))

uniq = []
for t in targets:
    if t not in uniq:
        uniq.append(t)
P("== 去重目标 %d 个 ==" % len(uniq))

P("== 逐路块形态 ==")
for t in uniq:
    insns = list(md.disasm(R.read_va(t, 160), t))
    first = insns[:3]
    calls = []
    term = None
    for ins in insns:
        if ins.id == 0:
            continue
        if ins.id == X86_INS_CALL and ins.operands and ins.operands[0].type == X86_OP_IMM:
            calls.append("%08X" % (ins.operands[0].imm & 0xFFFFFFFF))
        if ins.mnemonic.startswith("ret") or ins.id == X86_INS_JMP:
            term = (ins.address, ins.mnemonic, ins.op_str)
            break
    P("  --- block %08X" % t)
    for ins in first:
        P("       %08X  %-16s %-8s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
    P("       terminator=%s  calls=%s" % (term, calls))

txt = "\n".join(lines)
open(os.path.join(WORK, "jt_006E9140.txt"), "w", encoding="utf-8").write(txt + "\n")
print(txt)
