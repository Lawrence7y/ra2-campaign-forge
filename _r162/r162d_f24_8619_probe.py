#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R162-D · F24 的 86.19% 到底是不是 bounds 段某个自然比值的产物（有界否定）

背景：R138 已把「86.19% 盘上无任何字节对应」从 F24 正文撤下，理由是 R136 三种独立实现
实测 99.992% 有对应。但**86.19% 这个数本身怎么来的**至今未定（COMPACT_STATE 待办第 3 条）。
本轮不再重复「它错了」，而是问一个可失败的问题：

    它是否等于 bounds 段（1,392,592 条 VA）的某个**自然比值**？

先登记候选口径（在跑之前写死，避免事后凑数）：
  K1  bounds 落在 .text 指令起始集里的比例          → 若它是「对齐率」口径
  K2  bounds 落在 .text 里的比例（不要求是指令起始）  → 若它是「越界率」补数
  K3  bounds 里「不是指令起始」的占比                → 若它是「错位率」
  K4  .text 指令起始被 bounds 覆盖的比例            → 若它是「覆盖率」反向写错
  K5  1,392,592 vs 1,654 之类其它分母的自然比       → 只测 1,392,592/1,617,xxx 一族

判据：若 5 个候选全部离 86.19% 超过 1 个百分点，则**「它是某自然比值」这套解释被否**，
下一轮应改从「生成器侧」（a2_sites 的生产脚本）找，而不是继续在比值空间里搜。

只读 gamemd.exe。整段 .text 用 disasm_lite 64KB 流式（**严禁 detail=True 全段**）。
"""
import io
import json
import os
import struct
import sys

import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
EXE = 'ra2bench/gamemd.exe'
BOUNDS = 'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
OUT = '_r162/r162d_f24_8619_probe.json'
TARGET = 86.19

FAIL = 0
RES = []


def ck(name, cond, detail=''):
    global FAIL
    ok = bool(cond)
    if not ok:
        FAIL += 1
    RES.append({'id': name, 'ok': ok, 'detail': str(detail)[:400]})
    print(('PASS ' if ok else 'FAIL ') + name + (('  :: ' + str(detail)[:260]) if detail else ''))


# ---------------------------------------------------------------- 0 段表
print('== 0 段表与基线 ==')
data = open(EXE, 'rb').read()
N = len(data)
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.decode().rstrip('\x00'), s.VirtualAddress, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]
t = [s for s in secs if s[0] == '.text'][0]
TEXT_RAW, TEXT_RSZ, TEXT_VA, TEXT_VSZ = t[3], t[4], t[1], t[2]
TEXT_LO = IB + TEXT_VA
TEXT_HI = TEXT_LO + max(TEXT_VSZ, TEXT_RSZ)
print('  .text raw=%d rsz=%d va=%#x vsz=%d lo=%#x' % (TEXT_RAW, TEXT_RSZ, TEXT_VA, TEXT_VSZ, TEXT_LO))
ck('B0 ImageBase == 0x400000', IB == 0x400000, hex(IB))
ck('B1 .text 存在且 rsz > 1MB', TEXT_RSZ > 1 << 20, TEXT_RSZ)
ck('B2 gamemd.exe 字节数 == 4,825,360', N == 4825360, N)


def va_in_text(va):
    return TEXT_LO <= va < TEXT_HI


# ---------------------------------------------------------------- 1 流式扫描起始集
print('\n== 1 .text 指令起始集（64KB 分块 disasm_lite，跨块尾指令重读）==')
md = Cs(CS_ARCH_X86, CS_MODE_32)
starts = []
sizes = []
# S-476（自错，真实缺陷）：首版写的是
#     consumed = 0; for ...: consumed = a-base+sz
#     off += consumed if consumed else 65536
# 一旦某个字节 capstone 解不出（.text 里嵌数据），disasm_lite 立刻停、consumed == 0，
# 于是 **整整跳过 64 KB**。实测起始点只有 926,046 条，而 R143 同一遍 64 KB 分块扫描
# 明写 1,394,120 条 —— 差值 468,074 正是被跳过的块。
# 正确做法是解不出时只前进 **1 字节**重新对齐（下面 else 分支），不做整块跳过。
pos = 0
resync = 0
while pos < TEXT_RSZ:
    base = TEXT_LO + pos
    chunk = data[TEXT_RAW + pos:TEXT_RAW + min(pos + 65536, TEXT_RSZ)]
    consumed = 0
    for a, sz, mn, op in md.disasm_lite(chunk, base):
        if a - base + sz > len(chunk):
            break
        starts.append(a)
        sizes.append(sz)
        consumed = a - base + sz
    if consumed:
        pos += consumed
    else:
        pos += 1
        resync += 1
print('  起始点数 %d ; 首 %#x 末 %#x ; 单字节重对齐次数 %d'
      % (len(starts), starts[0], starts[-1], resync))
ck('C0 起始点数 > 900,000（与 R143 的 1,394,120 同量级，不是空扫）', len(starts) > 900000, len(starts))
ck('C1 起始点严格递增且无重复', all(starts[i] < starts[i + 1] for i in range(len(starts) - 1)),
   len(starts))
ck('C2 全部起始点落在 .text 内', va_in_text(starts[0]) and va_in_text(starts[-1]),
   (hex(starts[0]), hex(starts[-1])))
STARTSET = set(starts)

# ---------------------------------------------------------------- 2 bounds 段
print('\n== 2 bounds 段 ==')
J = json.load(open(BOUNDS))
bounds = J['bounds']
vals = [int(x, 16) for x in bounds]
print('  bounds 条数 %d ; 去重 %d ; 区间 %#x..%#x' % (len(vals), len(set(vals)), vals[0], vals[-1]))
ck('D0 bounds 条数 == 1,392,592', len(vals) == 1392592, len(vals))
ck('D1 bounds 无重复（单列地址，无第二列可回原址 —— 结构判据的事实基础）',
   len(set(vals)) == len(vals), len(set(vals)))
ck('D2 bounds 全部落在 .text 内', all(va_in_text(v) for v in vals[:5000])
   and va_in_text(vals[-1]), (hex(vals[0]), hex(vals[-1])))
# 反控：随便造 100 个 .data 里的地址，必须判「不在 .text」
dat = [s for s in secs if s[0] == '.data'][0]
probe = [IB + dat[1] + 4 * i for i in range(100)]
ck('D2r 反控：.data 地址全部判不在 .text', not any(va_in_text(v) for v in probe),
   hex(probe[0]))

# ---------------------------------------------------------------- 3 五个候选口径
print('\n== 3 五个预先登记的候选口径 ==')
# S-475（自错，性能缺陷）：首版写成 covered = sum(1 for a in starts if a in set(vals))，
# 那个 set(vals) 在**生成器每轮都重建一次** —— 1,392,592 条 set 构造 × 926,046 轮，
# 复杂度 O(n*m)，实测跑 >10 分钟仍未完成，被我自己 pkill 掉。
# 修法：set 只建一次（BOUNDSET），并改用「遍历较小的集合去查较大的集合」的方向。
BOUNDSET = set(vals)
on_start = sum(1 for v in vals if v in STARTSET)
off_start = len(vals) - on_start
covered = sum(1 for a in starts if a in BOUNDSET)
R = {
    'K1_bounds_on_instruction_start': 100.0 * on_start / len(vals),
    'K3_bounds_off_instruction_start': 100.0 * off_start / len(vals),
    'K4_text_starts_covered_by_bounds': 100.0 * covered / len(starts),
}
# K2：bounds 落在 .text 里的比例（按字节跨度口径，不是按起始集合）
R['K2_bounds_inside_text_pct'] = 100.0 * sum(1 for v in vals if va_in_text(v)) / len(vals)
# K5：以 1,392,592 为分母、把「指令起始集大小」当分子的几种写法
R['K5a_starts_over_bounds'] = 100.0 * len(starts) / len(vals)
R['K5b_off_start_over_starts'] = 100.0 * off_start / len(starts)
R['K5c_on_start_over_starts'] = 100.0 * on_start / len(starts)
for k in sorted(R):
    print('  %-36s = %10.4f%%   (Δ vs 86.19 = %+8.4f)' % (k, R[k], R[k] - TARGET))

deltas = {k: abs(v - TARGET) for k, v in R.items()}
best = min(deltas, key=deltas.get)
print('  最接近 86.19%% 的候选：%s Δ=%.4f 个百分点' % (best, deltas[best]))
ck('E0 K1 复现 99.9953%（修正扫描器后的真值；旧值 66.4959% 是跳块缺陷产物，见 S-476）',
   round(R['K1_bounds_on_instruction_start'], 4) == 99.9953,
   round(R['K1_bounds_on_instruction_start'], 4))
ck('E1 五个候选口径**没有一个**落在 86.19% ± 1 个百分点内',
   all(d > 1.0 for d in deltas.values()), {k: round(v, 4) for k, v in deltas.items()})
ck('E2 K1 + K3 == 100%（两个占比是互补的，不是两个独立量）',
   abs(R['K1_bounds_on_instruction_start'] + R['K3_bounds_off_instruction_start'] - 100.0) < 1e-9,
   round(R['K1_bounds_on_instruction_start'] + R['K3_bounds_off_instruction_start'], 6))
ck('E3 最接近的候选仍差 > 13 个百分点（不是"差一点"；门限按实测 13.69 定，不做事后放宽）',
   deltas[best] > 13.0, round(deltas[best], 4))

# ---- 3b bounds 的形态识别（这是本轮真正的业务发现）----
print('\n== 3b bounds 到底是什么：它是不是「.text 内、且在 VirtualSize 以内的指令起始集」？==')
VS_END = TEXT_LO + TEXT_VSZ
ENDSET = {a + sz for a, sz in zip(starts, sizes)}
BOUNDONLY = BOUNDSET - STARTSET          # 在 bounds 里、不是指令起始
STARTSONLY = STARTSET - BOUNDSET         # 是指令起始、不在 bounds 里
print('  .text 虚拟尾界 VS_END = %#x（lo + VirtualSize）' % VS_END)
print('  bounds 中不是起始的 %d 条；起始中不在 bounds 的 %d 条'
      % (len(BOUNDONLY), len(STARTSONLY)))
print('  65 条「非起始」的位移分布（相对前一条起始）: %s'
      % sorted(__import__('collections').Counter(
          v - max(a for a in starts if a < v) for v in sorted(BOUNDONLY)).items()))
ck('G0 「不在 bounds 的起始」全部落在 VirtualSize 之外（= 尾填充）',
   all(v >= VS_END for v in STARTSONLY) and len(STARTSONLY) > 0,
   (len(STARTSONLY), hex(min(STARTSONLY)) if STARTSONLY else None,
    hex(VS_END)))
ck('G0b 该尾填充段 = VS_END .. raw 尾，实测起点 0x7e038d、终点 0x7e0ffd',
   hex(min(STARTSONLY)) == '0x7e038d' and hex(max(STARTSONLY)) == '0x7e0ffd',
   (hex(min(STARTSONLY)), hex(max(STARTSONLY))))
ck('G1 「bounds 里非起始」只有 65 条（占比 %.4f%%）'
   % (100.0 * len(BOUNDONLY) / len(BOUNDSET)),
   len(BOUNDONLY) == 65, len(BOUNDONLY))
ck('G2 这 65 条全部落在 VirtualSize 以内（不是尾部填充）',
   all(v < VS_END for v in BOUNDONLY), len([v for v in BOUNDONLY if v >= VS_END]))
ck('G3 这 65 条全部落在某条指令**内部**（位移 1..7，与前一条起始正距离）',
   all(0 < (v - max(a for a in starts if a < v)) <= 7 for v in BOUNDONLY), len(BOUNDONLY))
S_VS = {a for a in STARTSET if a < VS_END}
print('  |起始 ∩ VirtualSize 内| = %d ; |bounds| = %d ; bounds ⊇ 它: %s'
      % (len(S_VS), len(BOUNDSET), S_VS <= BOUNDSET))
ck('G4 bounds ⊇ 「VirtualSize 内的全部指令起始」（严格超集，缺口 0 条）',
   S_VS <= BOUNDSET and len(BOUNDSET) - len(S_VS) == 65,
   (len(S_VS), len(BOUNDSET)))
# 反向：起始 ∩ VirtualSize 内的 100% 覆盖 ⇒ bounds 的本质就是指令起始集（去掉尾填充）
cov = 100.0 * len(S_VS) / len(BOUNDSET)
print('  ⟹ bounds 的 %.4f%% 是「VirtualSize 内的指令起始」；余下 %.4f%% 是 65 条指令内位移'
      % (cov, 100.0 - cov))
ck('G5 该解释的覆盖率 = 1,392,527 / 1,392,592 = 99.9953%（与 R136 的 99.992% 同向且更严）',
   round(cov, 4) == 99.9953 and len(S_VS) == 1392527, round(cov, 4))
# 86.19% 在这个新解释下有没有落点
share_starts_in_union = 100.0 * len(STARTSET) / len(STARTSET | ENDSET)
print('  新候选 K6 = |起始| / |起始 ∪ 结束| = %.4f%%' % share_starts_in_union)
ck('G6 新候选 K6 也不落在 86.19% ± 1 内（形态识别出来了，86.19% 仍无落点）',
   abs(share_starts_in_union - TARGET) > 1.0, round(share_starts_in_union, 4))
# 决定性否证：把候选空间里所有「A/B」形式（A,B 取自 8 个自然量）全排一遍，最近的那个也差多少
NAT = {'bounds': len(BOUNDSET), 'starts': len(starts), 'on_start': len(BOUNDSET & STARTSET),
       'off': len(BOUNDONLY), 'starts_in_vs': len(S_VS), 'starts_out_vs': len(STARTSONLY),
       'union_se': len(STARTSET | ENDSET), 'text_raw': TEXT_RSZ}
ratios = {}
for a, av in NAT.items():
    for b2, bv in NAT.items():
        if a == b2 or av == 0:
            continue
        ratios['%s/%s' % (a, b2)] = 100.0 * bv / av
rb = min(ratios, key=lambda k: abs(ratios[k] - TARGET))
print('  8 个自然量两两相除共 %d 个候选；最接近 86.19%% 的是 %s = %.4f%%（Δ=%+.4f）'
      % (len(ratios), rb, ratios[rb], ratios[rb] - TARGET))
ck('G7 自然量比值全空间（56 个候选）里**没有一个**命中 86.19% ± 1',
   min(abs(v - TARGET) for v in ratios.values()) > 1.0,
   round(min(abs(v - TARGET) for v in ratios.values()), 4))
ck('G8 全空间最接近的仍差 > 13 个百分点', abs(ratios[rb] - TARGET) > 13.0,
   round(abs(ratios[rb] - TARGET), 4))

# ---------------------------------------------------------------- 4 反控：判据不是恒真
print('\n== 4 反控：这个"否"有判别力吗 ==')
# 反控一：如果我改 TARGET 为 K1 的真实值，判据必须变成"命中"
T2 = R['K1_bounds_on_instruction_start']
hit_if_true = abs(R['K1_bounds_on_instruction_start'] - T2) <= 1.0
ck('F1 反控：把目标换成某候选自己的值，该候选必须落在 ±1 内（判据能给出"是"）',
   hit_if_true, T2)
# 反控二：S-477（自错）：首版断言「所有候选都在 [0,100] 内」，实测 K5a = 100.1097% 当场 FAIL。
# 原因不是算错：K5a 是 |starts| / |bounds| = 1,394,120 / 1,392,592，两个都是**计数**而且
# 分子比分母大（起始点比 bounds 多 1,528 条）⇒ 这是「计数比」，本来就可以 > 100%。
# 只有「份额类」候选（分子 ⊆ 分母）才必须 <= 100。断言要按口径分开写。
SHARE_KEYS = ['K1_bounds_on_instruction_start', 'K2_bounds_inside_text_pct',
              'K3_bounds_off_instruction_start', 'K4_text_starts_covered_by_bounds',
              'K5c_on_start_over_starts']
ck('F2 份额类候选（分子 ⊆ 分母）全部落在 [0,100]',
   all(0.0 <= R[k] <= 100.0 for k in SHARE_KEYS),
   {k: round(R[k], 2) for k in SHARE_KEYS})
ck('F2b 计数类候选 K5a 允许 > 100（1,394,120 / 1,392,592 = 100.1097%）',
   R['K5a_starts_over_bounds'] > 100.0 and round(R['K5a_starts_over_bounds'], 4) == 100.1097,
   round(R['K5a_starts_over_bounds'], 4))
ck('F2c K5b 是「非起始 / 起始」= 65/1,394,120，极小但不是 0（有 65 条确切存在）',
   0.0 < R['K5b_off_start_over_starts'] < 0.01,
   round(R['K5b_off_start_over_starts'], 6))

# ---------------------------------------------------------------- 5 收口
summary = {
    'exe_bytes': N, 'text_raw_size': TEXT_RSZ, 'instruction_starts': len(starts),
    'bounds': len(vals), 'bounds_distinct': len(set(vals)),
    'candidates': {k: round(v, 4) for k, v in R.items()},
    'target': TARGET, 'closest': best, 'closest_delta_pp': round(deltas[best], 4),
    'all_candidates_far': all(d > 1.0 for d in deltas.values()),
    'bounds_identity': {
        'bounds_minus_starts': len(BOUNDONLY),
        'starts_minus_bounds': len(STARTSONLY),
        'starts_minus_bounds_all_beyond_virtualsize': all(v >= VS_END for v in STARTSONLY),
        'virtualsize_end': hex(VS_END),
        'bounds_superset_of_vs_starts': S_VS <= BOUNDSET,
        'coverage_pct': round(cov, 4),
        'residual_65_all_inside_instructions': all(
            0 < (v - max(a for a in starts if a < v)) <= 7 for v in BOUNDONLY),
    },
    'K6_starts_over_union': round(share_starts_in_union, 4),
    'ratio_space_size': len(ratios),
    'ratio_space_closest': [rb, round(ratios[rb], 4), round(ratios[rb] - TARGET, 4)],
    'checks': len(RES), 'fails': FAIL,
}
os.makedirs('_r162', exist_ok=True)
with io.open(OUT, 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print('\n== 收口：%d 断言，%d FAIL ==' % (len(RES), FAIL))
print(json.dumps({k: v for k, v in summary.items()}, ensure_ascii=False, indent=1))
sys.exit(1 if FAIL else 0)
