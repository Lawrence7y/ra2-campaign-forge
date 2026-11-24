# -*- coding: utf-8 -*-
"""Lead 独立复算：0xA8ED80 / 0xA8ED84 的引用与写点（不复用 RE-N02 的脚本）。

方法（与 RE-N02 不同）：
  1. 用 capstone 从 .text 起点线性反汇编，收集每条指令的操作数里出现的目标绝对地址；
  2. 用 objdump 风格的独立判据：先从原始字节找 4 字节小端模式，再对每个命中
     用「多起点解码 + 取最短覆盖指令」得到候选指令，两条通道结果对照；
  3. 打印每条引用指令的 VA / 字节 / 文本 / 目标 / 判定(读|写|取址|调用参数) / 宽度。
只读磁盘，不启动任何进程。
"""
import struct
import sys
from collections import Counter, defaultdict

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import X86_OP_MEM, X86_OP_IMM, X86_OP_REG

EXE = r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"
TARGETS = {0x00A8ED80: "F_80", 0x00A8ED84: "F_84", 0x00A8ED7C: "F_7C", 0x00A8ED88: "F_88"}

pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
data = open(EXE, "rb").read()
secs = {s.Name.rstrip(b"\x00").decode("latin1"): s for s in pe.sections}
text = secs[".text"]
tb = data[text.PointerToRawData: text.PointerToRawData + text.SizeOfRawData]
tva = IB + text.VirtualAddress

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True

WRITE_MNEM = {"mov", "add", "sub", "inc", "dec", "or", "and", "xor", "not", "neg",
              "xchg", "movzx", "movsx", "adc", "sbb", "shl", "shr", "sar", "test",
              "cmpxchg", "xadd"}


def width_of(op):
    """操作数宽度（字节）。"""
    try:
        return op.size
    except Exception:
        return None


def refs_via_linear():
    """通道 1：线性反汇编，收操作数里含目标地址的指令。"""
    out = defaultdict(list)          # target -> [(va, bytes, mnem, opstr, kind, width)]
    for insn in md.disasm(tb, tva):
        if not insn.operands:
            continue
        for ti, t in enumerate(TARGETS):
            hit = None
            kind = None
            width = None
            for oi, op in enumerate(insn.operands):
                # (a) 内存操作数 disp == target
                if op.type == X86_OP_MEM and op.mem.disp == t and op.mem.base == 0 and op.mem.index == 0:
                    hit = True
                    width = op.size
                    kind = "write" if oi == 0 else "read"
                    break
                # (b) 立即数 == target（lea / push / mov reg,imm）
                if op.type == X86_OP_IMM and op.imm == t:
                    hit = True
                    kind = "address_take" if insn.mnemonic == "lea" else "imm_arg"
                    break
            if hit:
                out[t].append((insn.address, insn.bytes.hex(" "), insn.mnemonic,
                               insn.op_str, kind, width))
    return out


def refs_via_bytes():
    """通道 2：原始字节 4 字节小端搜索 + 多起点解码取最短覆盖。"""
    out = defaultdict(list)
    for t in TARGETS:
        pat = struct.pack("<I", t)
        i = 0
        while True:
            j = tb.find(pat, i)
            if j < 0:
                break
            best = None
            for back in range(0, 16):
                s = j - back
                if s < 0:
                    continue
                for insn in md.disasm(tb[s:s + 16], tva + s):
                    if insn.address <= tva + j and tva + j + 4 <= insn.address + insn.size:
                        if best is None or back < best[1]:
                            best = (insn, back)
                        break
            if best is not None:
                insn, back = best
                out[t].append((insn.address, insn.bytes.hex(" "), insn.mnemonic,
                               insn.op_str, "byte-hit(back=%d)" % back, None))
            i = j + 1
    return out


lin = refs_via_linear()
byt = refs_via_bytes()

print("=" * 100)
print("镜像: %s  ImageBase=0x%08X  .text RVA=0x%X rawsize=0x%X" %
      (EXE.split("\\")[-1], IB, text.VirtualAddress, text.SizeOfRawData))
print("=" * 100)

for t, name in TARGETS.items():
    L = lin.get(t, [])
    B = byt.get(t, [])
    print("\n### %s @ 0x%08X" % (name, t))
    print("  线性反汇编命中 : %d" % len(L))
    print("  字节模式命中   : %d  (去重前)" % len(B))
    kinds = Counter(x[4] for x in L)
    widths = Counter(x[5] for x in L if x[5] is not None)
    print("  分类           : %s" % dict(kinds))
    print("  内存操作数宽度 : %s" % dict(widths))
    # 列出写类与取址类
    for label, want in (("写类(write)", "write"), ("取址(lea)", "address_take"),
                        ("立即数参数", "imm_arg")):
        sel = [x for x in L if x[4] == want]
        if sel:
            print("  --- %s: %d 条 ---" % (label, len(sel)))
            for va, b, m, o, k, w in sel[:30]:
                print("    0x%08X  %-22s %-6s %-30s w=%s" % (va, b, m, o, w))
    # 读类里宽度分布示例
    rd = [x for x in L if x[4] == "read"]
    if rd:
        wc = Counter(x[5] for x in rd)
        print("  --- 读类 %d 条，宽度分布 %s；前 8 条 ---" % (len(rd), dict(wc)))
        for va, b, m, o, k, w in rd[:8]:
            print("    0x%08X  %-22s %-6s %-30s w=%s" % (va, b, m, o, w))

print("\n" + "=" * 100)
print("说明：本脚本只读磁盘字节；未启动游戏、未 attach、未读活进程内存。")
