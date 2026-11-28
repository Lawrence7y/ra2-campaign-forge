# -*- coding: utf-8 -*-
"""R222 m3: 解码器 0x7c7371 的三段展开体可达性与四张跳转表定位。

做法：在 0x7c7350..0x7c7f20 内线性反汇编，收集所有直接分支目标（jcc/jmp）与
间接跳转的跳转表基址；再对每个候选表读 dword 展开成边。输出：
 (1) 每段展开体的入口边（谁跳到段首）；
 (2) 四张表的基址、条目、每个条目对应块的 sub edi / sub esi / 尾部 jmp；
 (3) 反控：把某张表按 +4 字节整体错位读，条目必须全部落到非指令边界（报告是否如此）。
"""
import sys, re, struct
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True

LO, HI = 0x7c7350, 0x7c7f30


def dis(lo, hi):
    o = P.r2o(lo)
    buf = P.RAW[o:o + (hi - lo)]
    return [(i.address, i.bytes.hex(), i.mnemonic, i.op_str) for i in md.disasm(buf, lo)]


seq = dis(LO, HI)
print('range %08x..%08x insns %d' % (LO, HI, len(seq)))

edges = []            # (from, to, kind)
indirect_tables = []  # (from, table_va)
for a, bh, mn, op in seq:
    if mn.startswith('j') and op.startswith('0x'):
        edges.append((a, int(op, 16), mn))
    elif mn == 'jmp' and '[' in op:
        m = re.search(r'\[\w+\*4 \+ (0x[0-9a-f]+)\]', op)
        if m:
            indirect_tables.append((a, int(m.group(1), 16)))

print()
print('=== 间接跳转（8 分支表） ===')
for a, t in indirect_tables:
    print('%08x -> table %08x' % (a, t))

entries = (0x7c73c3, 0x7c7788, 0x7c7428, 0x7c77f0, 0x7c7bc0)
print()
print('=== 展开体入口的入边（谁跳进来） ===')
for e in entries:
    srcs = [(hex(f), k) for f, t, k in edges if t == e]
    print('%08x : %s' % (e, srcs if srcs else 'NONE'))

print()
print('=== 各 8 分支表的条目与块特征 ===')
tables = sorted(set([t for a, t in indirect_tables]))
# body2 的块表也可能在 0x7c7d4a 之后间接引用，indirect_tables 已覆盖
detail = {}
for a, bh, mn, op in seq:
    detail[a] = (mn, op)

for t in tables:
    vals = [struct.unpack_from('<I', P.RAW, P.r2o(t) + 4 * k)[0] for k in range(8)]
    print('--- table %08x ---' % t)
    print('   entries:', [hex(v) for v in vals])
    print('   all .text:', all(P.sec_of(v) == '.text' for v in vals))
    print('   all in this range:', all(LO <= v < HI for v in vals))
    for k, v in enumerate(vals):
        sub_edi = sub_esi = None
        jt = None
        for a2, bh2, mn2, op2 in seq:
            if v <= a2 < v + 0x40:
                if mn2 == 'sub' and op2.startswith('edi,') and sub_edi is None:
                    sub_edi = int(op2.split(',')[1], 0)
                if mn2 == 'sub' and op2.startswith('esi,') and sub_esi is None:
                    sub_esi = int(op2.split(',')[1], 0)
                if mn2 == 'jmp' and op2.startswith('0x') and jt is None:
                    jt = op2
        print('   [%d] %08x sub_edi %s sub_esi %s jmp %s' % (k, v, sub_edi, sub_esi, jt))

print()
print('=== 反控 R1：表 +4 错位读 ===')
t = tables[0]
vals_shift = [struct.unpack_from('<I', P.RAW, P.r2o(t) + 4 * k + 4)[0] for k in range(8)]
print('shifted:', [hex(v) for v in vals_shift])
print('shifted 仍在 code 段的条数:', sum(1 for v in vals_shift if P.sec_of(v) == '.text'))

print()
print('=== 表区与代码区的边界（表后是否直接接代码/对齐） ===')
for t in tables:
    nxt = P.RAW[P.r2o(t) + 32:P.r2o(t) + 48]
    print('%08x +32B: %s' % (t, nxt.hex()))
