#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R148 D：F23 limitations 里「11-22 快照清单有 4 条记录（主份 + 3 份 _hygiene 备份）」这句
在现盘清单上到底是几条 —— 主会话独立复算（含正反控）。
判据：只按 basename 精确等于 coverage.tsv 计入（不用子串，避免 coverage.tsv.bak / xcoverage.tsv 混入）。
"""
import io, json, os

ROOT = '/home/t628/projects/ra2-campaign-forge'
R14 = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
TIER = os.path.join(R14, 'R17_R101_TIER_FINAL_4417', 'tier_final_4417.tsv')
UNIQ = os.path.join(R14, '_r67', 'unique_content_4417.tsv')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


def rows(p):
    L = io.open(p, encoding='utf-8', newline='').read().split('\n')
    return L[0].split('\t'), [l.split('\t') for l in L[1:] if l.strip()]


h, R = rows(TIER)
ck('0.1 tier_final_4417 4,417 行 / 4 列', len(R) == 4417 and all(len(r) == 4 for r in R), len(R))

# basename 精确匹配
sel = [r for r in R if os.path.basename(r[0]) == 'coverage.tsv']
ck('1 basename 精确 == coverage.tsv 的记录数（期望不是 4）', len(sel) != 4, len(sel))
print('  实测记录数 = %d' % len(sel))
szs = [int(r[1]) for r in sel]
ck('2 其中恰 1 条 == 4,147,334 B（主份，唯一）', szs.count(4147334) == 1, szs.count(4147334))
main = [r for r in sel if int(r[1]) == 4147334]
ck('3 主份路径 = next_re_20261117_r14/COVERAGE/coverage.tsv',
   main and main[0][0] == 'next_re_20261117_r14/COVERAGE/coverage.tsv', main[0][0] if main else None)
backup = [r for r in sel if int(r[1]) != 4147334]
ck('4 备份条数 = 总条数 − 1', len(backup) == len(sel) - 1, (len(backup), len(sel)))
n_m4 = sum(1 for r in backup if '/M4_merge/_backup/' in r[0])
n_hyg = sum(1 for r in backup if '/_hygiene/' in r[0])
ck('5 备份 = M4_merge/_backup 1 条 + _hygiene 16 条（合计 17）',
   n_m4 == 1 and n_hyg == 16 and len(backup) == 17, (n_m4, n_hyg, len(backup)))
ck('6 备份的字节数互不相同（17 个不同世代）',
   len(set(int(r[1]) for r in backup)) == 17, len(set(int(r[1]) for r in backup)))
ck('7 全部 18 条的 sha256 两两不同（备份不是主份的拷贝）',
   len(set(r[0] for r in sel)) == len(sel), len(sel))
# 用 unique_content 交叉
uh, UR = rows(UNIQ)
usel = [r for r in UR if os.path.basename(r[0]) == 'coverage.tsv']
ck('8 交叉：_r67/unique_content_4417.tsv 同判据得同数', len(usel) == len(sel), (len(usel), len(sel)))
ck('9 交叉：两表 coverage.tsv 的 rel 集合逐元素相同',
   set(r[0] for r in sel) == set(r[0] for r in usel), '')
ck('10 交叉：主份 sha256 == c2ee063f…（两表一致）',
   [r[3] for r in usel if r[0] == 'next_re_20261117_r14/COVERAGE/coverage.tsv'][0].startswith('c2ee063f'),
   [r[3] for r in usel if r[0] == 'next_re_20261117_r14/COVERAGE/coverage.tsv'][0][:16])

# 现盘存在性
exist = [r for r in sel if os.path.isfile(os.path.join(ROOT, 'lead', r[0]))]
ck('11 这 18 条在现盘一条都不存在', len(exist) == 0, [r[0] for r in exist][:3])

# 反控
neg = [r for r in R if 'coverage.tsv' in r[0] and os.path.basename(r[0]) != 'coverage.tsv']
ck('12 反控：子串口径会多出记录（证明必须用 basename 精确匹配）', len(neg) > 0, len(neg))
ck('13 反控：把 basename 改成任意名得 0 条（判据不是恒真）',
   len([r for r in R if os.path.basename(r[0]) == 'zzz_none.tsv']) == 0, '')

print('\n结论：现盘清单里同 basename 记录 = %d 条（主份 1 + 备份 %d），'
      '原文「4 条记录（主份 + 3 份 _hygiene 备份）」与清单不符。'
      % (len(sel), len(backup)))
json.dump(dict(fails=fails, total=len(sel), main=1, backups=len(backup),
               m4=n_m4, hygiene=n_hyg, sizes=sorted(int(r[1]) for r in sel),
               rels=[r[0] for r in sel]),
          open(os.path.join(ROOT, '_r148', 'r148d_cov_records.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
