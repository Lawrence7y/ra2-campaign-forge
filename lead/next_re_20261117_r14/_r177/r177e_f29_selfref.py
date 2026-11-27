#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r177e：F29 的「6 个不同桩体」自指计数逐版实测。
R170 段自称「该串在 statement 1 次、limitations 2 次（R138 段与 R165 段各 1）、合计 3 次」。
若 R170 段自身含该串，则写下的同一刻就变成 3（合计 4）—— 与 S-624/S-636 同族的自指。
本脚本只测量、不下结论；正反控成对。
"""
import csv, glob, os, re, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = '6 个不同桩体'
SELF_OLD = '不在本条任何一列'
SELF_NEW = '不参与本条任何计数'

ok = fail = 0
def chk(c, m, extra=''):
    global ok, fail
    if c: ok += 1; print('  PASS ' + m + (('  ' + str(extra)) if extra else ''))
    else: fail += 1; print('  FAIL ' + m + (('  ' + str(extra)) if extra else ''))

vers = []
for d in glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V5*')):
    m = re.search(r'_V(\d+)$', d)
    if m: vers.append((int(m.group(1)), d))
vers.sort()
sel = [(v, d) for v, d in vers if v >= 540]
print('versions:', [v for v, _ in sel])
print()
print('%-6s %-8s %-8s %-8s %-8s %-10s %-10s' % ('ver', 'T(st)', 'T(lim)', 'T(tot)', 'len_lim', 'OLD(st,lim)', 'NEW(st,lim)'))
table = {}
for v, d in sel:
    rr = {r[0]: r for r in csv.reader(open(os.path.join(d, 'FACT_INDEX.tsv'), encoding='utf-8'), delimiter='\t')}
    f = rr['F29']
    st, lim = f[1], f[4]
    row = (st.count(TARGET), lim.count(TARGET), st.count(SELF_OLD), lim.count(SELF_OLD),
           st.count(SELF_NEW), lim.count(SELF_NEW), len(lim))
    table[v] = row
    print('%-6d %-8d %-8d %-8d %-8d %-10s %-10s' % (
        v, row[0], row[1], row[0] + row[1], row[6],
        '%d,%d' % (row[2], row[3]), '%d,%d' % (row[4], row[5])))

print()
print('=== 断言 ===')
# R170 是在 V550 落的（看板/LEAD_LOCK 记 R170 改 F29.statement 末句）
chk(table[550][4] >= 1, 'V550 起 statement 含新措辞「不参与本条任何计数」')
chk(table[550][2] == 0, 'V550 起 statement 无旧措辞「不在本条任何一列」', table[550][2])
chk(table[550][3] == 3, 'V550 起 limitations 旧措辞 = 3 次（R170 段自身引文 +1）', table[550][3])
# R170 段自称 limitations 2 次
print('  V559 实测：stmt=%d lim=%d tot=%d' % (table[559][0], table[559][1], table[559][0] + table[559][1]))
chk(table[559][1] == 3, 'V559 limitations 实测「6 个不同桩体」= 3 次（R170 段自称 2 次 ⇒ 自指 +1）')
chk(table[559][0] + table[559][1] == 4, 'V559 合计 = 4（R170 段自称「合计 3 次」⇒ 自指 +1）')
chk(table[549][1] == 2, 'V549 limitations TARGET = 2（R170 落盘前基线）', table[549][1])
chk(table[550][1] - table[549][1] == 1, 'V549->V550 limitations 增量 = +1（R170 段的段内引文？或 R165 引文）',
    table[550][1] - table[549][1])
print()
print('=== R170 段自身的原文（逐字取回）===')
rr = {r[0]: r for r in csv.reader(open(os.path.join(TIER, 'R17_R128_FACTINDEX_V559', 'FACT_INDEX.tsv'),
                                      encoding='utf-8'), delimiter='\t')}
lim = rr['F29'][4]
i = lim.find('【R170 补')
seg = lim[i:]
print(seg)
print()
print('  该段内 TARGET 次数 =', seg.count(TARGET), ' 该段字符数 =', len(seg))
chk(seg.count(TARGET) == 1, 'R170 段自身含 TARGET 1 次 ⇒ 写下即污染自己的计数')
chk('合计 **3** 次' in seg, 'R170 段逐字写「合计 3 次」')
print()
print('RESULT: %d PASS / %d FAIL' % (ok, fail))
sys.exit(1 if fail else 0)
