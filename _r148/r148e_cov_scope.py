#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 E：解开 R148D 暴露的「4 条记录 vs 18 条」矛盾 —— 是**口径**不同，不是数字错。
两个互不相同的口径：
  S1 路径中含 /COVERAGE/ 目录（R138 用的口径）
  S2 basename 精确 == coverage.tsv（我 R148D 用的口径）
判据：两条都要能同时被复算，且互相不能推出对方。
"""
import io, json, os

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
TIER = os.path.join(R14, 'R17_R101_TIER_FINAL_4417', 'tier_final_4417.tsv')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


L = io.open(TIER, encoding='utf-8', newline='').read().split('\n')
R = [l.split('\t') for l in L[1:] if l.strip()]

S2 = [r for r in R if os.path.basename(r[0]) == 'coverage.tsv']
S1 = [r for r in R if '/COVERAGE/' in r[0] and os.path.basename(r[0]) == 'coverage.tsv']
S1b = [r for r in R if '/COVERAGE/' in r[0]]          # 不带 basename 限制（放宽，看是否有多余）

ck('1 S1（路径含 /COVERAGE/ 且 basename 命中）= 4', len(S1) == 4, [r[0] for r in S1])
ck('2 S2（basename 命中，不限目录）= 18', len(S2) == 18, len(S2))
ck('3 S1 ⊂ S2 且真包含（S2 - S1 = 14）', set(r[0] for r in S1) < set(r[0] for r in S2)
   and len(S2) - len(S1) == 14, len(S2) - len(S1))
sz1 = [int(r[1]) for r in S1]
ck('4 S1 的四个字节 = 4,147,334 / 3,659,609 / 3,663,149 / 3,683,786（与 R138 原文逐位相同）',
   sorted(sz1) == sorted([4147334, 3659609, 3663149, 3683786]), sorted(sz1))
ck('5 S1 形态 = 主份 1 + _hygiene 下 COVERAGE 子目录 3 份',
   sum(1 for r in S1 if r[0] == 'next_re_20261117_r14/COVERAGE/coverage.tsv') == 1
   and sum(1 for r in S1 if '/_hygiene/' in r[0]) == 3,
   [r[0] for r in S1])
ck('6 S2 - S1 的 14 条不在 COVERAGE/ 目录下（是别的世代备份路径）',
   all('/COVERAGE/' not in r[0] for r in S2 if r[0] not in set(x[0] for x in S1)), '')
ck('7 反控：S1 的判据不能从 S2 推出（S2 里 14 条不在 /COVERAGE/ 下）',
   len([r for r in S2 if '/COVERAGE/' not in r[0]]) == 14, '')
ck('8 反控：放宽成「路径含 /COVERAGE/ 不管 basename」会多出别的文件',
   len(S1b) > len(S1), (len(S1b), len(S1)))
ck('9 反控：S1b 里非 coverage.tsv 的样本', 
   sorted(set(os.path.basename(r[0]) for r in S1b if os.path.basename(r[0]) != 'coverage.tsv'))[:6],
   sorted(set(os.path.basename(r[0]) for r in S1b if os.path.basename(r[0]) != 'coverage.tsv'))[:6])
print('\nS1b 多出的文件名：%s' %
      sorted(set(os.path.basename(r[0]) for r in S1b if os.path.basename(r[0]) != 'coverage.tsv')))
json.dump(dict(fails=fails, S1=[r[0] for r in S1], S1_sizes=sorted(sz1),
               S2_count=len(S2), S1b_count=len(S1b),
               s1b_names=sorted(set(os.path.basename(r[0]) for r in S1b))),
          open(os.path.join(ROOT, '_r148', 'r148e_cov_scope.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
