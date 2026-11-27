#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161b_blindspot.py —— 复算 R160 审计员 #373 报的「等长互换盲区」到底有多大，逐口径。

R160 摘要记：#373 新增盲区「F18/F36 各320B、F28/F34 各348B 互换在 --ignore-pin 下 exit0」，
主会话复算 C1/C2「成立」，并给出「87.83% 正文（col2+col5=84,746B）」。
本轮把这三处数字全部从盘上重算，并把「等长」拆成五种口径（整行互换 / 只换 col2 / 只换 col5 /
只换 col4 / 只换 grade），因为 v2 的 D5/D6/D7 是**逐列**判的，口径不同结论可以相反。
"""
import io
import re
import sys
from collections import defaultdict

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
P = T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

txt = io.open(P, encoding='utf-8', newline='').read()
lines = [l for l in txt.split('\n') if l]
rows = [l.split('\t') for l in lines]
hdr, data = rows[0], rows[1:]
N = len(data)

def groups(keyf):
    g = defaultdict(list)
    for r in data:
        g[keyf(r)].append(r[0])
    return g

def pairs(g):
    out = []
    for k, ids in g.items():
        if len(ids) > 1:
            for i in range(len(ids)):
                for j in range(i + 1, len(ids)):
                    out.append((ids[i], ids[j], k))
    return out

L = lambda s: len(s.encode())
print('== 0 · 口径常数 ==')
col2_d = sum(L(r[1]) for r in data); col5_d = sum(L(r[4]) for r in data)
col3_d = sum(L(r[2]) for r in data); col4_d = sum(L(r[3]) for r in data)
h2, h5 = L(hdr[1]), L(hdr[4])
print('  数据行：col2=%d col3=%d col4=%d col5=%d 和=%d' % (col2_d, col3_d, col4_d, col5_d, col2_d+col3_d+col4_d+col5_d))
print('  表头行：col2=%d col5=%d （和 %d）' % (h2, h5, h2 + h5))
ck('0.1 数据行 col2+col5 实测 == 84,726（R160 记的 84,746 = 本值 + 表头 20 B）',
   col2_d + col5_d == 84726 and h2 + h5 == 20, col2_d + col5_d)
ck('0.2 含表头口径 == 84,746（R160 那个数的真实口径，题面未声明）',
   col2_d + col5_d + h2 + h5 == 84746, col2_d + col5_d + h2 + h5)
col1_d = sum(L(r[0]) for r in data)
hdr_all = sum(L(x) for x in hdr)
data_all = col1_d + col2_d + col3_d + col4_d + col5_d
ck('0.3a 54 数据行字段总和 == 96,444', data_all == 96444, data_all)
ck('0.3b 含表头字段总和 == 96,490（= 96,444 + 表头 46）', data_all + hdr_all == 96490,
   (data_all, hdr_all))
print('  R160 的 87.83%% 复算 = 84,746/96,490 = %.4f%%（含表头口径）' % (100.0 * 84746 / 96490))
print('  纯数据行同口径    = 84,726/96,444 = %.4f%%' % (100.0 * 84726 / 96444))
ck('0.4 两种口径都落在 87.8~87.9 之间（差 0.18 个百分点，不改变量级结论）',
   87.75 < 100.0 * 84746 / 96490 < 87.90 and 87.75 < 100.0 * 84726 / 96444 < 87.90,
   (round(100.0 * 84746 / 96490, 4), round(100.0 * 84726 / 96444, 4)))

print('\n== 1 · 五种「等长」口径各自的候选对 ==')
specs = [
    ('整行四列同时等长（含 grade）', lambda r: (L(r[1]), L(r[2]), L(r[3]), L(r[4]))),
    ('col2+col4+col5 等长（不含 grade）', lambda r: (L(r[1]), L(r[3]), L(r[4]))),
    ('只换 col2（col2 等长）', lambda r: L(r[1])),
    ('只换 col5（col5 等长）', lambda r: L(r[4])),
    ('只换 col4（col4 等长）', lambda r: L(r[3])),
]
res = {}
for name, kf in specs:
    g = groups(kf); pp = pairs(g); res[name] = pp
    print('  %-32s 组(>=2)=%2d  对=%3d  样例=%s'
          % (name, sum(1 for v in g.values() if len(v) > 1), len(pp),
             ', '.join('%s/%s' % (a, b) for a, b, _ in pp[:4])))

print('\n== 2 · R160 摘要点名的两对，逐列实测 ==')
d = {r[0]: r for r in data}
for a, b in (('F18', 'F36'), ('F28', 'F34')):
    ra, rb = d[a], d[b]
    print('  %s: col2=%d col3=%d col4=%d col5=%d' % (a, L(ra[1]), L(ra[2]), L(ra[3]), L(ra[4])))
    print('  %s: col2=%d col3=%d col4=%d col5=%d' % (b, L(rb[1]), L(rb[2]), L(rb[3]), L(rb[4])))
    print('     同列等长? col2=%s col5=%s col4=%s ; grade 相同=%s'
          % (L(ra[1]) == L(rb[1]), L(ra[4]) == L(rb[4]), L(ra[3]) == L(rb[3]), ra[2] == rb[2]))
    if a == 'F18':
        ck('2.F18 F18/F36 **不是整行可换**（col2 与 grade 都不同 ⇒ R160 摘要里「F18/F36 各320B 互换」是只换 col5）',
           L(ra[1]) != L(rb[1]) and ra[2] != rb[2] and L(ra[4]) == L(rb[4]),
           (L(ra[1]), L(rb[1]), ra[2], rb[2]))
    else:
        ck('2.F28 F28/F34 只 col2 等长、col5 不等（⇒ 「各348B」说的是 col2，不是整行）',
           L(ra[1]) == L(rb[1]) and L(ra[4]) != L(rb[4]) and ra[2] == rb[2],
           (L(ra[1]), L(rb[1]), L(ra[4]), L(rb[4]), ra[2], rb[2]))

print('\n== 3 · v2 的真实断言面（决定哪些口径真能过）==')
G = io.open(R + '/_r160/facts_floors.py', encoding='utf-8').read()
has = lambda pat: re.search(pat, G, re.M) is not None
ck('3.1 v2 有逐 fid grade 表（D5）', has(r'^GRADES = \{'), None)
ck('3.2 v2 有逐 fid 字节下界表（D6，不许缩）', has(r'^FLOORS = \{'), None)
ck('3.3 v2 有逐 fid 证据清单（D7）', has(r'^EVID = \{'), None)
ck('3.4 v2 无 col2/col5 的内容哈希（⇒ 等长改写/互换的确不可见）',
   not has(r'col2|statement_sha|CONTENT_SHA'), None)

print('\n== 4 · 结论量 ==')
big = res['只换 col2（col2 等长）'] + res['只换 col5（col5 等长）']
ck('4.1 「只换 col2」与「只换 col5」的候选对都非空', len(res['只换 col2（col2 等长）']) > 0
   and len(res['只换 col5（col5 等长）']) > 0, (len(res['只换 col2（col2 等长）']), len(res['只换 col5（col5 等长）'])))
ck('4.2 整行四列同时等长的候选对为 0（整行互换这条路走不通）',
   len(res['整行四列同时等长（含 grade）']) == 0, len(res['整行四列同时等长（含 grade）']))
print('  ⇒ 盲区真实形态不是「F18/F36 整行互换」，而是**同列等长互换**：col2 %d 对、col5 %d 对'
      % (len(res['只换 col2（col2 等长）']), len(res['只换 col5（col5 等长）'])))
print('FAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
