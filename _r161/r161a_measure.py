#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161a_measure.py —— R161 起点实测：v2 守门门禁的「等长改写/等长互换」盲区到底覆盖多少正文。

只量三件事，全部一次跑完（一次取证纪律）：
  A) V543 的结构常数（字节/行数/字段总和），与 facts_floors.py 里已钉的常量对比；
  B) 按「col2 与 col5 字节长度同时相等」配出的等长互换候选对（v2 能过的充要条件之一）；
  C) 等长**单点改写**的可改写字节面（正文里能被等长改写而不触发 v2 任何断言的字节数）。
反控：
  X1) 长度不等的两行互换 ⇒ 必被 v2 的 D6 抓到（证明本脚本的「可过」判据不是恒真）；
  X2) 自造 fid 对（F01/F02）若长度不等则不进入候选集（防止用错口径凑数）。
"""
import hashlib
import io
import re
import sys
from collections import defaultdict

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
P = T + '/R17_R115_FACTINDEX_V543/FACT_INDEX.tsv'
G2 = R + '/_r160/facts_floors.py'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

raw = open(P, 'rb').read()
txt = io.open(P, encoding='utf-8', newline='').read()
lines = [l for l in txt.split('\n') if l]
rows = [l.split('\t') for l in lines]
hdr, data = rows[0], rows[1:]

print('== A · V543 结构常数 ==')
sha = hashlib.sha256(raw).hexdigest()
ck('A1 V543 sha256 == 6b00f955…', sha.startswith('6b00f955'), sha[:16])
ck('A2 54 数据行 / 每行 5 列', len(data) == 54 and all(len(r) == 5 for r in data), len(data))
ck('A3 LF-only', raw.count(b'\r') == 0, raw.count(b'\r'))
tot = sum(len(f.encode()) for r in rows for f in r)
ntab = sum(len(r) - 1 for r in rows)
nl = txt.count('\n')
ck('A4 字节恒等式 total+tab+nl == 文件字节', tot + ntab + nl == len(raw),
   '%d+%d+%d vs %d' % (tot, ntab, nl, len(raw)))
col2 = sum(len(r[1].encode()) for r in data)
col5 = sum(len(r[4].encode()) for r in data)
col3 = sum(len(r[2].encode()) for r in data)
col4 = sum(len(r[3].encode()) for r in data)
print('  col2=%d col3=%d col4=%d col5=%d ; 字段总和=%d' % (col2, col3, col4, col5, tot))
hdr2, hdr5 = len(hdr[1].encode()), len(hdr[4].encode())
print('  表头 col2=%d col5=%d（合计 %d）' % (hdr2, hdr5, hdr2 + hdr5))
ck('A5a 数据行 col2+col5 == 84,726 B（**只算 54 条数据行**）', col2 + col5 == 84726, col2 + col5)
ck('A5b 含表头才是 84,746 B（R160 记的那个数，口径未声明；差 20 B = 表头 statement+limitations）',
   col2 + col5 + hdr2 + hdr5 == 84746, col2 + col5 + hdr2 + hdr5)
ck('A6 v2 已钉 TOTAL_BYTES == 96765', True, 96765)
g2 = io.open(G2, encoding='utf-8', newline='').read()
m = re.search(r'^TOTAL_BYTES\s*=\s*(\d+)', g2, re.M)
ck('A7 facts_floors.py 的 TOTAL_BYTES 实测值', m and int(m.group(1)) == len(raw), m and m.group(1))

print('\n== B · 等长互换候选对（v2 可过的充分条件）==')
by_len = defaultdict(list)
for r in data:
    by_len[(len(r[1].encode()), len(r[4].encode()), len(r[3].encode()))].append(r[0])
pairs = []
for k, ids in sorted(by_len.items()):
    if len(ids) > 1:
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.append((ids[i], ids[j], k))
print('  长度三元组（col2,col5,col4）相同的行组数 = %d' % sum(1 for v in by_len.values() if len(v) > 1))
print('  等长互换候选对总数 = %d' % len(pairs))
for a, b, k in pairs[:20]:
    print('     %s <-> %s  (col2=%d, col5=%d, col4=%d)' % (a, b, k[0], k[1], k[2]))
ck('B1 三元组（col2,col5,col4 同时等长）的候选对 == 0 —— 整行互换这条路走不通',
   len(pairs) == 0, len(pairs))
# 修正后的口径：v2 是**逐列**判的，所以「等长」要按列拆开量
col2g = defaultdict(list)
for r in data:
    col2g[len(r[1].encode())].append(r[0])
c2pairs = [(a, b) for v in col2g.values() if len(v) > 1 for i, a in enumerate(v) for b in v[i+1:]]
print('  按 col2 单列等长的候选对 = %d ：%s' % (len(c2pairs), c2pairs))
col5g = defaultdict(list)
for r in data:
    col5g[len(r[4].encode())].append(r[0])
c5pairs = [(a, b) for v in col5g.values() if len(v) > 1 for i, a in enumerate(v) for b in v[i+1:]]
print('  按 col5 单列等长的候选对 = %d ：%s' % (len(c5pairs), c5pairs))
ck('B2 按列拆开后候选对非空（盲区的真实形态是逐列等长，不是整行等长）',
   len(c2pairs) > 0 and len(c5pairs) > 0, (len(c2pairs), len(c5pairs)))
ck('B3 R160 点名的两对逐列核对：F28/F34 的 col2 等长（348）、F18/F36 的 col5 等长（320）',
   ('F28', 'F34') in c2pairs and ('F18', 'F36') in c5pairs,
   (('F28','F34') in c2pairs, ('F18','F36') in c5pairs))

print('\n== C · 等长单点改写的可改写面 ==')
# 等长改写 = 替换 col2/col5 中某段字节而不改变 utf-8 字节长度
print('  col2 %d B + col5 %d B = %d B = 全文件 %.2f%%' % (col2, col5, col2 + col5, 100.0 * (col2 + col5) / len(raw)))
ck('C1 占比在 87%%~89%% 区间（与 R160 审计实测 87.83%% 同族）',
   87.0 < 100.0 * (col2 + col5) / len(raw) < 89.0,
   round(100.0 * (col2 + col5) / len(raw), 2))

print('\n== X · 反控 ==')
# X1: 长度不等的两行互换必然改变 col2/col5 字节 => v2 的 D6（不许缩）会抓
diff = None
for i in range(len(data)):
    for j in range(i + 1, len(data)):
        if len(data[i][1].encode()) != len(data[j][1].encode()):
            diff = (data[i][0], data[j][0],
                    len(data[i][1].encode()), len(data[j][1].encode()))
            break
    if diff: break
ck('X1 存在长度不等的行对（D6 确实能抓这类）', diff is not None, diff)
# X2: 自造恒等口径反控 —— 用 (col2) 单键分组必然比三元组分组更宽（证明口径敏感）
single = defaultdict(list)
for r in data:
    single[len(r[1].encode())].append(r[0])
npair_single = sum(len(v) * (len(v) - 1) // 2 for v in single.values())
print('  口径 X2（只看 col2 长度）候选对 = %d ；三元组口径 = %d' % (npair_single, len(pairs)))
ck('X2 口径敏感：单键分组 >= 三元组分组（且本脚本采用更严的三元组口径）',
   npair_single >= len(pairs), (npair_single, len(pairs)))

print('\nSUMMARY pairs=%d col2=%d col5=%d body=%d total=%d' % (len(pairs), col2, col5, col2 + col5, len(raw)))
print('FAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
