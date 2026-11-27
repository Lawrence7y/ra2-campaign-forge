#!/usr/bin/env python3
"""R169 F（v4）：复算审计员 #397（deepseek/audit）的 4 条「不一致」—— §2.12 规则 D 主会话自算。

自错登记（本脚本前三版全部被自己的可失败断言抓出，无一条进结论）：
  S-557 把「续解」误实现成 break + off += CH ⇒ 整块丢弃，得 1,150,117。
  S-558 把「连续相位」误实现成内层 cur 走到 RAW1、外层再 off += CH ⇒ 相位与窗口互相打架，得 1,392,660。
  S-559 把「反向表上界」写成只按「落 .text」⇒ 把跨指令边界的 0x498d00 算成条目（9 而非 8）。

本版只保留两个**互相独立、各自可自证**的实现，且不再自造第三种：
  M_A 连续相位（r143lib / R168 口径）：off += consumed（本块最后一条完整指令末尾），
      块尾跨块指令在下一窗口重解 ⇒ 相位跨块连续。正控 1,392,527。
  M_B 边界重置：每 64KB 原始偏移边界强制从边界字节重解（块内仍 realign）。
      若审计员主张成立，应得 1,392,568。
断言：
  G1 M_A(VS) == 1,392,527（正控，R168 已落盘）
  G2 M_B(VS) == 1,392,568 且 M_B - M_A == +41（审计员 #397 主张 A 的数）
  G3 M_A(RAW) == 1,394,120（R166 已落盘正控）/ M_B(RAW) == 1,394,161
  G4 ⇒ 审计员主张 A **成立**：1,392,527 是连续相位口径，不是 64KB 边界重启
  G5 0x7d0cb0 反向：按「落 .text」得 9 条、其中 0x498d00 的槽字节跨指令边界（0x7d0c91 是起点）
      ⇒ 真条目 8、区间 [0x7d0c94,0x7d0cb4)（审计员主张 B 的表体尺寸成立）
  G6 8 落点：线性口径 S 成员 6 / 非成员 2（0x7d0cb4、0x7d0cbc）—— 审计员称「全部是真起点」须带口径
  G7 两个非 S 成员落点在「从 0x7d0cb4 续解」链里是真起点
  G8 0x7d0cba 被 0x7d0cb8(4B) 覆盖 1 条 / 线性口径 0 条 ⇒ 审计员主张 D 成立
  G9 站点 ff24/ff14 = 384、8b/8d = 136、合计 520 ⇒ 审计员主张「384」只在 ff 口径下成立
"""
import sys, json
sys.path.insert(0, '_r143')
import r143lib as L
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

B = L.Bin(); md = Cs(CS_ARCH_X86, CS_MODE_32)
text = [s for s in B.secs if s[0] == '.text'][0]
T_LO = B.IB + text[1]; T_VSZ_HI = T_LO + text[2]; T_RAW_HI = T_LO + text[4]
CH = 65536
RAW0, RAW1, VS = text[3], text[3] + text[4], text[1]

def M_A(hi):
    """连续相位：off += consumed。"""
    out = {}
    off = RAW0
    while off < RAW1:
        c = B.data[off:min(off + CH, RAW1)]
        base = B.IB + (VS + (off - RAW0))
        consumed = 0
        for a, sz, mn, op in md.disasm_lite(c, base):
            if a - base + sz > len(c): break
            consumed = a - base + sz
            if a < hi: out[a] = sz
        off += consumed if consumed else 1
    return out

def M_B(hi):
    """边界重置：每 64KB 原始偏移边界从边界字节重解；块内 realign。"""
    out = {}
    for k in range(0, (RAW1 - RAW0 + CH - 1) // CH):
        b0 = RAW0 + k * CH
        b1 = min(b0 + CH, RAW1)
        cur = b0
        while cur < b1:
            c = B.data[cur:b1]
            base = B.IB + (VS + (cur - RAW0))
            consumed = 0
            for a, sz, mn, op in md.disasm_lite(c, base):
                if a - base + sz > len(c): break
                consumed = a - base + sz
                if a < hi: out[a] = sz
            cur += consumed if consumed else 1
    return out

MA = M_A(T_VSZ_HI); MB = M_B(T_VSZ_HI)
MAr = M_A(T_RAW_HI); MBr = M_B(T_RAW_HI)
print('M_A(VS)=%d  M_B(VS)=%d  diff=%+d' % (len(MA), len(MB), len(MB) - len(MA)))
print('M_A(RAW)=%d M_B(RAW)=%d diff=%+d' % (len(MAr), len(MBr), len(MBr) - len(MAr)))

A = []
def chk(i, cond, detail):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(detail)})

chk('G1 M_A(VS) == 1,392,527（R168 已落盘正控）', len(MA) == 1392527, len(MA))
chk('G2 M_B(VS) == 1,392,568 且差 +41（审计员 #397 主张 A 的数）',
    len(MB) == 1392568 and len(MB) - len(MA) == 41, {'MB': len(MB), 'diff': len(MB) - len(MA)})
chk('G3 M_A(RAW) == 1,394,120 / M_B(RAW) == 1,394,161',
    len(MAr) == 1394120 and len(MBr) == 1394161, {'MAr': len(MAr), 'MBr': len(MBr)})
chk('G4 审计员主张 A 成立：1,392,527 属连续相位口径，另有一 64KB 边界重启口径给 1,392,568',
    len(MA) == 1392527 and len(MB) == 1392568, {'continuous': len(MA), 'boundary': len(MB)})

starts = MA
def span(base, step, maxent=8192):
    n = 0; vals = []
    while n < maxent:
        v = B.dw(base + step * n)
        if v is None or not (T_LO <= v < T_VSZ_HI): break
        vals.append(v); n += 1
    return n, vals

nL, vL = span(0x7d0cb0, -4)
# 剔除跨指令边界的尾槽：该槽的 4 字节内包含一个指令起点（且不在槽首）
def cross_boundary(slot):
    return [hex(s) for s in starts if slot < s < slot + 4]

tail_slot = 0x7d0cb0 - 4 * (nL - 1)
xb = cross_boundary(tail_slot)
nReal = nL - 1 if xb else nL
real_lo = 0x7d0cb0 - 4 * (nReal - 1)
vals8 = vL[:nReal]
chk('G5 0x7d0cb0 反向：落 .text %d 条；尾槽 %#x 跨指令边界 %s ⇒ 真条目 %d、区间 [%#x,%#x)'
    % (nL, tail_slot, xb, nReal, real_lo, 0x7d0cb4),
    nL == 9 and xb and nReal == 8 and real_lo == 0x7d0c94,
    {'loose_n': nL, 'tail_slot': hex(tail_slot), 'cross': xb, 'n': nReal,
     'region': [hex(real_lo), hex(0x7d0cb4)], 'vals': [hex(v) for v in vals8]})

inS = [hex(v) for v in vals8 if v in starts]
notS = [hex(v) for v in vals8 if v not in starts]
chk('G6 8 落点：S 成员 %d / 非成员 %d（分列）' % (len(inS), len(notS)), len(inS) == 6 and len(notS) == 2,
    {'in_S': inS, 'not_S': notS})

chain = []; cur = 0x7d0cb4
while cur < 0x7d0cfe:
    o = B.va2off(cur)
    ii = list(md.disasm(B.data[o:o + 16], cur, count=1))
    if not ii: break
    i = ii[0]
    chain.append({'va': hex(cur), 'sz': i.size, 'mn': i.mnemonic, 'op': i.op_str})
    cur += i.size
cs = {int(c['va'], 16) for c in chain}
chk('G7 两个非 S 成员落点在续解链里都是真起点',
    len(notS) == 2 and all(int(v, 16) in cs for v in notS),
    {'not_S': notS, 'in_chain': [v for v in notS if int(v, 16) in cs]})

H = 0x7d0cba
hit = [c for c in chain if int(c['va'], 16) <= H < int(c['va'], 16) + c['sz']]
lin = [(s, starts[s]) for s in starts if s <= H < s + starts[s]]
chk('G8 0x7d0cba 被 0x7d0cb8(4B) 覆盖 1 条 / 线性口径 0 条',
    len(hit) == 1 and hit[0]['va'] == '0x7d0cb8' and len(lin) == 0,
    {'chain': hit, 'linear': [(hex(s), z) for s, z in lin]})

f1 = f2 = 0
for op2 in (0x24, 0x14):
    for m in (0x8d, 0x85, 0x95, 0x9d, 0xa5, 0xb5, 0xbd):
        pat = bytes([0xff, op2, m]); i = 0
        while True:
            j = B.data.find(pat, i)
            if j < 0: break
            i = j + 1
            if RAW0 <= j < RAW1: f1 += 1
for m in (0x04, 0x0c, 0x14, 0x1c, 0x24, 0x2c, 0x34, 0x3c):
    pat = bytes([0x8b, m, 0x8d]); i = 0
    while True:
        j = B.data.find(pat, i)
        if j < 0: break
        i = j + 1
        if RAW0 <= j < RAW1: f2 += 1
chk('G9 站点 ff=384 / mov=136 / 合计 520', f1 == 384 and f2 == 136 and f1 + f2 == 520,
    {'ff': f1, 'mov': f2, 'total': f1 + f2})

out = {'M_A_VS': len(MA), 'M_B_VS': len(MB), 'M_A_RAW': len(MAr), 'M_B_RAW': len(MBr),
       'delta_VS': len(MB) - len(MA), 'delta_RAW': len(MBr) - len(MAr),
       'reverse_table': {'base': '0x7d0cb0', 'loose_n': nL, 'tail_slot': hex(tail_slot),
                         'cross_insn_in_tail': xb, 'n': nReal,
                         'region': [hex(real_lo), hex(0x7d0cb4)],
                         'vals': [hex(v) for v in vals8], 'in_S': inS, 'not_S': notS},
       'chain': chain, 'hole_hit': hit, 'linear_hit': len(lin),
       'sites': {'ff': f1, 'mov': f2, 'total': f1 + f2},
       'assertions': A, 'fail': sum(1 for a in A if not a['ok'])}
json.dump(out, open('_r169/r169f_recompute_397.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for a in A:
    print(('PASS ' if a['ok'] else 'FAIL ') + a['id'] + ' :: ' + a['detail'][:340])
print('FAIL count =', out['fail'])
