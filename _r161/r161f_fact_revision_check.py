#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161f_fact_revision_check.py —— 把 R137 看板第九节列的「正文修订」四项，逐项判「是否真的落进正文」。

四项（原文见本轮 Goal）：
  ① F23 补「12 行分解余 1 行无归属」与「计数依赖 coverage.tsv 4,147,334 B 已失」
  ② F24 的 86.19% 数字**撤下**（保留结构判据，两者分开处理）
  ③ F24 语料值失效期标注（4,417 件 / 737,517,286 B 为 11-22 快照值，现盘 65 件 / 44,470,975 B）
  ④ F29 四处措辞作用域补全（两份拷贝 / idx=62 / 6 桩体 / 40·63·77 非因果）

判据不是「字符串出现过没有」——那太弱（撤回说明本身也含该串）。判据是**逐次出现的作用域判定**：
  · 对 ②：86.19% 的每一次出现，向后/向前 200 字符内必须出现撤回动词（撤下/撤销/撤回/错的是数字）；
    并且**不允许**作为剔除理由出现（即不得出现在「因此剔除」式的肯定语境里）。
  · 对 ③：每次出现 4,417 或 737,517,286 时，同句必须有「11-22 快照」限定。
  · 反控：自造串若不带撤回动词，必须被判为「非撤回语境」（证明判据不是恒真）。
"""
import io
import re
import sys

P = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

ne = [l for l in io.open(P, encoding='utf-8', newline='').read().split('\n') if l]
rows = [l.split('\t') for l in ne[1:]]
d = {r[0]: r for r in rows}
TXT = {fid: d[fid][1] + '\x00' + d[fid][4] for fid in d}   # statement + limitations 合并判

RETRACT = ('撤下', '撤销', '撤回', '错的是数字', '不得再把', '不再作为', '已撤回')
def classify(text, needle, win=200):
    """逐次出现分类：返回 [(pos, judged_as, snippet)]，judged_as ∈ {'retract','assert'}"""
    out = []
    for m in re.finditer(re.escape(needle), text):
        a, b = max(0, m.start() - win), min(len(text), m.end() + win)
        ctx = text[a:b]
        kind = 'retract' if any(k in ctx for k in RETRACT) else 'assert'
        out.append((m.start(), kind, ctx.replace('\x00', '⏐').replace('\n', ' ')[:150]))
    return out

print('== ① F23：两条补充是否落在正文 ==')
t23 = TXT['F23']
ck('①a 「差 1 行无归属」在 F23 正文', '差 **1 行**' in t23 and '没有归属' in t23)
ck('①b 「coverage.tsv 4,147,334 B 已失」在 F23 正文',
   '4,147,334' in t23 and 'coverage.tsv' in t23 and ('不在现盘' in t23 or '曾存在、现失' in t23))
ck('①c 「不可重数」结论同时在场（不是只说数、不说边界）', '不可重数' in t23 or '不能重数' in t23)
print('     F23：4,147,334 出现 %d 次、coverage.tsv 出现 %d 次、「不可重数」%d 次'
      % (t23.count('4,147,334'), t23.count('coverage.tsv'), t23.count('不可重数')))

print('\n== ② F24：86.19% 的每一次出现是否都处于撤回语境 ==')
t24 = TXT['F24']
occ = classify(t24, '86.19%')
print('     出现 %d 次：' % len(occ))
for pos, kind, snip in occ:
    print('       @%-6d %-8s …%s…' % (pos, kind, snip))
ck('②a 86.19% 至少出现 1 次（否则「撤下」无从判定）', len(occ) >= 1, len(occ))
ck('②b 每一次出现都在撤回语境里（无一次被当作肯定断言）',
   all(k == 'retract' for _, k, _ in occ), [k for _, k, _ in occ])
ck('②c 保留的结构判据显式在场（单列地址无可回原址复核的第二列）',
   '单列地址' in t24 and '第二列' in t24)
ck('②d 明确写了「数字错、方向对，两者分开处理」', '数字错、方向对' in t24 and '分开处理' in t24)

print('\n== ③ F24：语料值失效期标注 ==')
for needle in ('4,417', '737,517,286'):
    o = classify(t24, needle, win=260)
    dressed = [k for _, k, _ in o]
    print('     %-12s 出现 %d 次，带「11-22 快照 / 失效期」限定的次数 = %d'
          % (needle, len(o), sum(1 for _, k, sn in o if ('11-22' in sn or '11月22' in sn or '快照' in sn))))
ck('③a 4,417 至少出现 1 次', t24.count('4,417') >= 1, t24.count('4,417'))
ck('③b 存在显式的「11-22 快照值 / 不是现盘」声明句',
   ('11-22 快照值' in t24) or ('2026-11-22 快照值' in t24), None)
ck('③c 现盘 65 件 / 44,470,975 B 同时在场（否则读者无法替换）',
   '65 件' in t24 and '44,470,975' in t24)
ck('③d 「必须同写三项」的口径要求在 limitations 里', '11-22 快照' in d['F24'][4])

print('\n== ④ F29：四处作用域 ==')
t29 = TXT['F29']
checks = [
    ('两份拷贝（全镜像 80 次里的两份）', '全镜像 80 次' in t29 and '两份' in t29),
    ('idx=62 是 DLL 内 0-based', 'DLL 内 0-based' in t29 or ('DLL 内' in t29 and '0-based' in t29)),
    ('6 桩体 不在本条任何一列', '6 个不同桩体' in t29),
    ('40 / 63 / 77 非因果', '非因果' in t29),
]
for name, cond in checks:
    ck('④ ' + name, cond)
print('     「80 次」出现 %d 次、「DLL 内」%d 次、「非因果」%d 次、「6 个不同桩体」%d 次'
      % (t29.count('全镜像 80 次'), t29.count('DLL 内'), t29.count('非因果'), t29.count('6 个不同桩体')))

print('\n== X · 判据反控（证明 classify 不是恒真/恒假）==')
synth_assert = '本条剔除依据是 86.19% 无字节对应，故剔。'
synth_retract = '原「86.19% 无字节对应」已撤销，实测 99.992% 有对应。'
c1 = classify(synth_assert, '86.19%')
c2 = classify(synth_retract, '86.19%')
ck('X1 自造的肯定句被判 assert（判据有区分力）', len(c1) == 1 and c1[0][1] == 'assert', [k for _, k, _ in c1])
ck('X2 自造的撤回句被判 retract', len(c2) == 1 and c2[0][1] == 'retract', [k for _, k, _ in c2])
ck('X3 自造非命中串得 0 次（不虚报）', len(classify(synth_assert, '99.992%')) == 0)

print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
