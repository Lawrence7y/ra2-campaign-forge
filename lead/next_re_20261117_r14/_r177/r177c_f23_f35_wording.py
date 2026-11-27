#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r177c：核 R177 任务单 ① 的两条「补」是否已在盘上；核 F35「缺一手权威」方向。
每条都配正控（必中）与反控（自造串必 0）。
"""
import csv, glob, os, re, sys

TIER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ok = fail = 0
def chk(c, m, extra=''):
    global ok, fail
    if c: ok += 1; print('  PASS ' + m + (('  ' + str(extra)) if extra else ''))
    else: fail += 1; print('  FAIL ' + m + (('  ' + str(extra)) if extra else ''))

V559 = os.path.join(TIER, 'R17_R128_FACTINDEX_V559', 'FACT_INDEX.tsv')
rows = {r[0]: r for r in csv.reader(open(V559, encoding='utf-8'), delimiter='\t')}
F23, F35 = rows['F23'], rows['F35']

print('=== A. F23 两条「补」的在场性（statement + limitations）===')
A1 = '1 行无归属'      # 12 行分解余 1 行
A2 = '4,147,334'      # coverage.tsv 字节数
A3 = '已失'
for tok, name in ((A1, '12 行分解余 1 行无归属'), (A2, 'coverage.tsv 4,147,334 B'), (A3, '已失')):
    st, lim = F23[1].count(tok), F23[4].count(tok)
    print('  %-28s statement=%d limitations=%d' % (name, st, lim))
chk(F23[1].count(A1) >= 1 and F23[4].count(A1) >= 1, 'A1 在 F23 两列都在场')
chk(F23[1].count(A2) >= 1 and F23[4].count(A2) >= 1, 'A2 在 F23 两列都在场')
chk(F23[1].count(A3) >= 1 and F23[4].count(A3) >= 1, 'A3 在 F23 两列都在场')
# 反控：自造串必须 0
chk(F23[1].count('1 行无归属XX') == 0, '反控 A1 变体 0 命中')
chk(F23[1].count('4,147,335') == 0, '反控 4,147,335 0 命中')

print()
print('=== B. 这两条「补」的首现版本（闭世界：V530..V559 全扫）===')
vers = []
for d in glob.glob(os.path.join(TIER, 'R17_R*_FACTINDEX_V5*')):
    m = re.search(r'_V(\d+)$', d)
    if m and int(m.group(1)) >= 530: vers.append((int(m.group(1)), d))
vers.sort()
first = {}
for v, d in vers:
    rr = {r[0]: r for r in csv.reader(open(os.path.join(d, 'FACT_INDEX.tsv'), encoding='utf-8'), delimiter='\t')}
    f = rr['F23']
    first[v] = (f[1].count(A1), f[4].count(A1), f[1].count(A2), f[4].count(A2))
prev = (0, 0, 0, 0)
for v, _ in vers:
    cur = first[v]
    if cur != prev:
        print('  V%d  A1(st,lim)=%d,%d  A2(st,lim)=%d,%d   <- 变化' % (v, *cur))
        prev = cur
print('  V530 起首版：', vers[0][0], first[vers[0][0]])
chk(first[vers[0][0]] == (0, 0, 0, 0), 'V530（闭世界首版）两串均 0 ⇒ 首现晚于 V530')
chk(first[559] == first[558] and first[558] == first[557], 'V557/V558/V559 三版 F23 四计数相同（未被后轮污染）')

print()
print('=== C. F35「缺一手权威」方向（R159 已判定该说法过强）===')
B1 = '缺一手权威'
for col, nm in ((1, 'statement'), (4, 'limitations')):
    idx = [m.start() for m in re.finditer(re.escape(B1), F35[col])]
    print('  %-12s 次数=%d 位置=%r' % (nm, len(idx), idx[:8]))
chk(F35[1].count(B1) >= 1, 'F35.statement 里「缺一手权威」在场（作为被撤回对象）')
chk('已撤回' in F35[1], 'F35.statement 含「已撤回」')
chk('不得再写' in F35[1], 'F35.statement 含「不得再写」')
chk('无外部规范权威' in F35[4], 'F35.limitations 含新措辞「无外部规范权威」')
chk('都过强' in F35[4], 'F35.limitations 含「都过强」断言')
# 反控：这三串不在的写法
chk(F35[4].count('缺一手权威XX') == 0, '反控 变体 0 命中')

print()
print('=== D. 若按 R177 任务单字面「补 proved_strict 定义缺一手权威」会与正文冲突 ===')
# 现状：statement ① 明写该说法已撤回、不得再写
ban = '已撤回，不得再写' in F35[1].replace('\n', '')
print('  statement 逐字含「已撤回，不得再写」=', ban)
chk(ban, '正文内有明确的禁令句 ⇒ 按任务单字面补充会自相矛盾')

print()
print('RESULT: %d PASS / %d FAIL' % (ok, fail))
sys.exit(1 if fail else 0)
