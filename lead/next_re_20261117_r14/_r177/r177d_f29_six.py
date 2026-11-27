#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r177d：F29 里「6」这个数字的全部出现，逐个定性 —— 任务单 ④ 说「6 桩体=63 表内口径」，
先把盘上所有 6 的所指枚举出来，再看该表述是否与正文相符。
正控/反控成对。
"""
import csv, os, re, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V = os.path.join(TIER, 'R17_R128_FACTINDEX_V559', 'FACT_INDEX.tsv')
rows = {r[0]: r for r in csv.reader(open(V, encoding='utf-8'), delimiter='\t')}
F = rows['F29']
ok = fail = 0
def chk(c, m, extra=''):
    global ok, fail
    if c: ok += 1; print('  PASS ' + m + (('  ' + str(extra)) if extra else ''))
    else: fail += 1; print('  FAIL ' + m + (('  ' + str(extra)) if extra else ''))

print('=== A. 枚举 F29 两列里所有「6」的出现（含中文语境）===')
pat = re.compile(r'6')
events = []
for col, nm in ((1, 'statement'), (4, 'limitations')):
    t = F[col]
    for m in pat.finditer(t):
        i = m.start()
        ctx = t[max(0, i - 60):i + 60].replace('\n', ' ')
        events.append((nm, i, ctx))
print('  总命中数（含所有数字中的 6，如 63/77/46…）：', len(events))

print()
print('=== B. 按语义归类：抓「N 个…桩」型短语 ===')
phrases = ['个不同桩体', '只用到 6 个桩', '6 跳', '深度上限 6', '6 个桩', '6 个不同']
for p in phrases:
    st, lim = F[1].count(p), F[4].count(p)
    print('  %-16s statement=%d limitations=%d' % (p, st, lim))

print()
print('=== C. 三条不同的「6」各自的作用域是否写明 ===')
# C1 —— R135 自报的「6 个不同桩体」
c1 = '6 个不同桩体'
i1 = F[1].find(c1)
print('  C1 statement @%d: ...%s...' % (i1, F[1][max(0,i1-120):i1+140].replace('\n',' ') if i1>=0 else 'NOT FOUND'))
chk(i1 >= 0, 'C1「6 个不同桩体」在 statement 在场')
chk('不参与本条任何计数' in F[1], 'C1 的作用域句（不参与本条任何计数）在 statement 在场')
chk('R135 审计自报的中间数字' in F[1], 'C1 的来源句（R135 审计自报的中间数字）在 statement 在场')

# C2 —— R141 的「63 只用到 6 个桩」
c2 = '只用到 6 个桩'
i2 = F[4].find(c2)
print('  C2 limitations @%d: ...%s...' % (i2, F[4][max(0,i2-200):i2+260].replace('\n',' ') if i2>=0 else 'NOT FOUND'))
chk(i2 >= 0, 'C2「63 只用到 6 个桩」在 limitations 在场')
chk('其余 34 个桩' in F[4], 'C2 的补集（其余 34 个桩）写明 ⇒ 6 是 40 的子集')
chk('40−6' in F[4] or '40-6' in F[4], 'C2 显式出现「40−6」减法 ⇒ 基数锚在 40 而不是 63')

# C3 —— 跟链深度上限 6 跳
c3 = '上限 6 跳'
print('  C3「上限 6 跳」statement=%d limitations=%d' % (F[1].count(c3), F[4].count(c3)))
chk(F[1].count(c3) + F[4].count(c3) >= 1, 'C3 深度上限 6 跳在场')

print()
print('=== D. 任务单 ④ 的「6 桩体=63 表内口径」与正文是否相符 ===')
# 正文的真说法：6 是「40 个桩里 63 用到的 6 个」，基数 40，不是「63 表内」
claim_task = '63 表内口径'
print('  正文里「63 表内」字样出现次数：', F[1].count(claim_task) + F[4].count(claim_task))
chk(F[1].count(claim_task) + F[4].count(claim_task) == 0, '「63 表内口径」不是正文用词（任务单措辞）')
# 63 张表用的是 63 个桩吗？正文说 63 只用到 6 个桩 ⇒ 6 与 63 数值巧合
chk('6' in F[4] and '63' in F[4], '两个数都在 limitations')
print('  关键判据：6 的分母是 40（桩集合），63 的分母是 77（表数）⇒ 两者口径不同，不能互换')
chk('40 个 8 字节桩' in F[4] or '40 个桩' in F[4] or '40 个 8 字节' in F[4], '40 桩集合在 limitations 有定义')
chk('77 张' in F[1] or '77 张' in F[4], '77 张表在正文有定义')

print()
print('=== E. 反控（必须为假）===')
chk(F[4].count('只用到 6 个桩XX') == 0, '反控 变体 0 命中')
chk(F[4].count('6 个不同桩体') == 3, '实测：该串在 limitations 3 次（我原写「不在 limitations」，方向写反 ⇒ S-643）', F[4].count('6 个不同桩体'))

print()
print('RESULT: %d PASS / %d FAIL' % (ok, fail))
sys.exit(1 if fail else 0)
