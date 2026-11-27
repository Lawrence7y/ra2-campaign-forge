#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R165-c · 「不在本条任何一列」型自指句的全表普查（只读）

起因：F29 limitations 的 R138 段末写「R135 审计中出现过的『6 个不同桩体』不在本条正文任何一列」。
该句本身若出现在本条限制栏里，它自己就是「第二处出现」⇒ 自指为假。

本脚本做两件事，都带反控：
  1) 全表 54 条逐列扫「不在本条任何一列」族（含「不在本条正文任何一列」「不在本条任何一列」），
     给出命中行与逐列计数。
  2) 对每条命中行，核「被它声明为不在列里的那个串」在本行各列的真实出现次数 ——
     若 >0，则该自指为假，登记为反例。

不碰 gamemd.exe，不启 detail=True，不遍历大目录（只读一个 100 KB 级 TSV）。
"""
import io
import json
import os
import sys

R = '/home/t628/projects/ra2-campaign-forge'
T = os.path.join(R, 'lead/next_re_20261117_r14')
V544 = os.path.join(T, 'R17_R116_FACTINDEX_V544/FACT_INDEX.tsv')
V545 = os.path.join(T, 'R17_R117_FACTINDEX_V545/FACT_INDEX.tsv')
OUT = os.path.join(R, '_r165/r165c_selfref.json')

FAILS = []
RES = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  :: ' + str(d)[:300]) if d else ''))
    RES.append({'n': n, 'ok': ok, 'd': str(d)[:300]})
    if not ok:
        FAILS.append(n)
    return ok


def rows(p):
    t = io.open(p, encoding='utf-8').read()
    return {l.split('\t')[0]: l.split('\t') for l in t.split('\n') if l}


PHRASES = ['不在本条正文任何一列', '不在本条任何一列']

print('== 1 · 全表普查（V544 = 写入前，作为改前基线）==')
r544 = rows(V544)
ck('1.0 V544 恰 54 条数据行', len([k for k in r544 if k.startswith('F')]) == 54,
   len([k for k in r544 if k.startswith('F')]))

hits = {}
for fid, c in r544.items():
    if not fid.startswith('F'):
        continue
    per = {p: (c[1].count(p), c[4].count(p)) for p in PHRASES}
    tot = sum(a + b for a, b in per.values())
    if tot:
        hits[fid] = {'per': per, 'st': c[1].count(PHRASES[0]) + c[1].count(PHRASES[1]),
                     'lim': c[4].count(PHRASES[0]) + c[4].count(PHRASES[1])}
print('   命中行:', json.dumps(hits, ensure_ascii=False))
ck('1.1 全表命中恰 1 行', len(hits) == 1, list(hits))
ck('1.2 该行是 F29', list(hits) == ['F29'], list(hits))
ck('1.3 反控：自造串「不在本条ZZQ」全表 0 命中',
   io.open(V544, encoding='utf-8').read().count('不在本条ZZQ') == 0)

print()
print('== 2 · 该自指句是真是假（核被声明串的真实出现次数）==')
f29 = r544['F29']
TARGET = '6 个不同桩体'
ck('2.0 被声明的串 %s 在 F29 statement 出现 1 次' % TARGET, f29[1].count(TARGET) == 1,
   f29[1].count(TARGET))
ck('2.1 在同一行 limitations 出现 1 次', f29[4].count(TARGET) == 1, f29[4].count(TARGET))
ck('2.2 【自指为假】本行合计 2 次 > 0 ⇒「不在任何一列」不成立',
   f29[1].count(TARGET) + f29[4].count(TARGET) == 2, 2)
ck('2.3 statement 里那 1 次紧邻「不在本条任何一列」（自指发生在 statement 内）',
   '不在本条任何一列' in f29[1] and f29[1].find(TARGET) < f29[1].find('不在本条任何一列'),
   (f29[1].find(TARGET), f29[1].find('不在本条任何一列')))
ck('2.4 limitations 里那 1 次紧邻「不在本条正文任何一列」',
   '不在本条正文任何一列' in f29[4], f29[4].find('不在本条正文任何一列'))

print()
print('== 3 · V545 写入后：该自指句被如实保留 + 校正段就位 ==')
if not os.path.isfile(V545):
    ck('3.0 V545 尚未写出（本脚本应可独立运行）', False, V545)
else:
    r545 = rows(V545)
    g = r545['F29']
    ck('3.0 V545 在盘且 F29 存在', 'F29' in r545)
    ck('3.1 V545 里 %s 行合计 3 次 = V544 的 2 次 + 校正段引文 1 次（原文未删、实测数未改）' % TARGET,
       g[1].count(TARGET) == 1 and g[4].count(TARGET) == 2
       and g[1].count(TARGET) + g[4].count(TARGET) == 3,
       (g[1].count(TARGET), g[4].count(TARGET)))
    ck('3.1b 校正段自身已把 V544 口径写死在句内（防「当前态计数」自指复演）',
       '在 **V544** 里该串在本行出现 **2 次**' in g[4] and '**V545 起 3 次**' in g[4],
       'ok')
    ck('3.2 V545 含校正段「一处自指句为假」恰 1 次', g[4].count('一处自指句为假') == 1,
       g[4].count('一处自指句为假'))
    ck('3.3 F29 statement 在 V544/V545 逐字节相同（校正只写进 limitations）',
       r544['F29'][1] == g[1])
    ck('3.4 反控：V545 的其它 53 行里「一处自指句为假」0 次（追加未串台）',
       sum(1 for k, c in r545.items() if k.startswith('F') and k != 'F29'
           and '一处自指句为假' in c[4]) == 0)

res = {'hits_544': hits, 'fails': FAILS, 'assertions': RES}
json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)
print()
print('=== FAILS: %d ===' % len(FAILS))
for f in FAILS:
    print('   -', f)
sys.exit(1 if FAILS else 0)
