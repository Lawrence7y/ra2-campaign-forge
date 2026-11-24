#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107i_regcheck.py —— 核对 R106 判据「必须看判界寄存器，不是索引寄存器」的鉴别力

自错登记 E-i1：本脚本初版用「从 H 往回试解 1..24 字节、取能恰好结束在 H 的那条」找上一条指令，
并把 H 原地改成 found.address 继续回退。实测 cmp 全部拿不到（cmp=None 18/19），
根因是回退窗口内取「第一个能对齐的」不唯一（同一位置常有多种对齐解），且 H 被改写后
后续窗口整体错位。已改为：先用 64KB 分块 disasm_lite 铺满全 .text 得到权威指令起点集合，
再在集合上二分回看，不再自行试解。

R106 §EH4 声称：看错寄存器会 100% 拿噪声（原话「实测 18/19 错」）。
本脚本独立重算：逐张比较 cmp reg,BOUND 的 reg 与 jmp [reg*4+表] 的 reg，并按两级/直接形态分列。
"""
import bisect, hashlib, json, os, struct, sys
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
OUT = '_r107/r107i_regcheck.json'
EXE = 'ra2bench/gamemd.exe'
EXE_SHA = '73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476'
checks = []


def ck(n, c, d=''):
    checks.append({'name': n, 'ok': bool(c), 'detail': str(d)})
    print(('PASS ' if c else 'FAIL ') + n + ((' | ' + str(d)) if d != '' else ''), flush=True)
    return bool(c)


raw = open(EXE, 'rb').read()
ck('S0 exe sha256', hashlib.sha256(raw).hexdigest() == EXE_SHA, hashlib.sha256(raw).hexdigest()[:16])
e = struct.unpack_from('<I', raw, 0x3c)[0]
nsec, = struct.unpack_from('<H', raw, e + 6)
osz, = struct.unpack_from('<H', raw, e + 20)
opt = e + 24
IB = struct.unpack_from('<I', raw, opt + 28)[0]
secs = []
for i in range(nsec):
    o = opt + osz + i * 40
    nm = raw[o:o + 8].rstrip(b'\0').decode()
    vs, rva, rs, ra = struct.unpack_from('<IIII', raw, o + 8)
    secs.append((nm, rva, vs, ra, rs))


def off(va):
    r = va - IB
    for nm, srva, vs, ra, rs in secs:
        if srva <= r < srva + max(vs, rs):
            return ra + (r - srva)
    return None


tn, trva, tvs, tra, trs = next(s for s in secs if s[0] == '.text')
TS = IB + trva
TE = TS + tvs
ml = Cs(CS_ARCH_X86, CS_MODE_32)
ml.detail = False
ml.skipdata = True
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.detail = True
md.skipdata = True

starts = []
pos = TS
while pos < TE:
    hi = min(pos + 65536, TE)
    buf = raw[off(pos):off(hi) + 16]
    last = pos
    for a, sz, m, o in ml.disasm_lite(buf, pos):
        if a >= hi:
            break
        last = a + sz
        starts.append(a)
    if last <= pos:
        last = pos + 1
    pos = last
ck('S1 全段指令起点 %d 条' % len(starts), len(starts) == 1392592, len(starts))


def insn_at(a):
    return next(md.disasm(raw[off(a):off(a) + 16], a), None)


D = json.load(open('_r106/r106f_switchsem.json'))['tables']
ROWS = []
for t in D:
    H = int(t['holder'], 16)
    j = insn_at(H)
    jm = j.operands[0].mem
    idx = j.reg_name(jm.index)
    # 在权威起点集合上二分回看，找最近一条 cmp reg,imm
    i = bisect.bisect_left(starts, H) - 1
    cmp_reg = cmp_at = cmp_imm = None
    for _ in range(40):
        if i < 0:
            break
        g = insn_at(starts[i])
        if g is not None and g.mnemonic == 'cmp' and len(g.operands) == 2 \
                and g.operands[0].type == 1 and g.operands[1].type == 2:
            cmp_reg = g.reg_name(g.operands[0].reg)
            cmp_at = g.address
            cmp_imm = g.operands[1].imm & 0xFFFFFFFF
            break
        i -= 1
    ck('R0 %s 拿到 cmp reg,imm' % t['table'], cmp_reg is not None, cmp_at)
    same = (cmp_reg == idx)
    ROWS.append({'table': t['table'], 'index_reg': idx, 'cmp_reg': cmp_reg,
                 'cmp_at': hex(cmp_at) if cmp_at else None, 'cmp_imm': cmp_imm,
                 'same_register': same, 'two_level': t['two_level']})
    print('%-10s two=%-5s idx=%-3s cmp=%-3s same=%-5s bound=%s'
          % (t['table'], t['two_level'], idx, cmp_reg, same, cmp_imm), flush=True)

nsame = sum(1 for r in ROWS if r['same_register'])
tl = [r for r in ROWS if r['two_level']]
direct = [r for r in ROWS if not r['two_level']]
ck('R1 判界寄存器 == 索引寄存器 的表数', True, '%d 相同 / %d 不同' % (nsame, 19 - nsame))
ck('R2 两级形态 %d 张里两寄存器相同的张数（构造上应全不相同）' % len(tl),
   all(not r['same_register'] for r in tl),
   [(r['table'], r['index_reg'], r['cmp_reg']) for r in tl if r['same_register']])
same_direct = [r['table'] for r in direct if r['same_register']]
ck('R3 直接形态 %d 张里两寄存器相同的张数（>0 即 R106「18/19 错」被推翻）' % len(direct),
   True, '%d 张: %s' % (len(same_direct), same_direct))
ck('R4 直接形态 9 张全部两寄存器相同 => 在直接形态上看哪只都等价，看错不会错',
   len(same_direct) == len(direct), same_direct)
ck('R5 全部「不同」的都落在两级形态里（两寄存器不同不是普遍规律，是两级形态的构造性特征）',
   all(r['two_level'] for r in ROWS if not r['same_register']),
   [(r['table'], r['two_level']) for r in ROWS if not r['same_register'] and not r['two_level']])
truth = '看错 register 会错 %d/19 = %.1f%%（不是 100%%）' % (19 - nsame, 100.0 * (19 - nsame) / 19)
ck('R6 R106「看错会 100%% 拿噪声（18/19）」不成立：实测错 %d/19' % (19 - nsame),
   (19 - nsame) < 18, truth)
json.dump({'checks': checks, 'rows': ROWS, 'n_same': nsame, 'n_diff': 19 - nsame,
           'verdict': truth}, open(OUT, 'w'), ensure_ascii=False, indent=1)
nf = sum(1 for c in checks if not c['ok'])
print('\n断言 %d 项 FAIL %d' % (len(checks), nf))
sys.exit(1 if nf else 0)
