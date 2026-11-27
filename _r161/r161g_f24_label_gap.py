#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161g_f24_label_gap.py —— 量 R137 目标③ 的真实落地程度：F24 里 10 次 4,417 中几次带失效期限定。

r161f 已证「声明句存在」（③b PASS）。但「存在一句声明」不等于「引用有作用域」：
本脚本逐次量**每一次出现的最近限定距离**，并区分 statement / limitations 两列分别读的顺序，
因为读者是按列顺序读的 —— 主引用值出现在第 330 字符，而第一个失效期限定若出现在第 4,889 字符，
顺序阅读就会先拿到裸值。
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
d = {l.split('\t')[0]: l.split('\t') for l in ne[1:]}
r = d['F24']
QUAL = ('失效期', '11-22 快照', '11-22快照', '2026-11-22 快照', '快照值', '不是现盘')

def occ(text, needle):
    return [m.start() for m in re.finditer(re.escape(needle), text)]

def nearest_qual(text, pos):
    best = None
    for q in QUAL:
        for m in re.finditer(re.escape(q), text):
            dist = min(abs(m.start() - pos), abs(pos - m.start()))
            if best is None or dist < best[0]:
                best = (dist, q, m.start())
    return best

for col, name in ((1, 'statement'), (4, 'limitations')):
    t = r[col]
    print('\n== 列 %s（%d 字符 / %d 字节）==' % (name, len(t), len(t.encode())))
    for needle in ('4,417', '737,517,286'):
        ps = occ(t, needle)
        print('  %-12s 出现 %2d 次' % (needle, len(ps)))
        for p in ps:
            nq = nearest_qual(t, p)
            print('     @%-6d 最近限定 = %-14s 距离 %s 字符' % (p, nq[1] if nq else 'NONE', nq[0] if nq else '-'))

print('\n== 结论量 ==')
st = r[1]; lm = r[4]
first_val = min([p for p in occ(st, '4,417')] or [10 ** 9])
first_qual = min([m.start() for q in QUAL for m in re.finditer(re.escape(q), st)] or [10 ** 9])
print('  statement 里 4,417 首现 @%s；第一个失效期限定 @%s' % (first_val, first_qual))
ck('① 主引用值出现在失效期声明**之前**（顺序阅读会先拿到裸值）',
   first_val < first_qual, (first_val, first_qual))
gap = first_qual - first_val
print('  两者相距 %d 字符' % gap)

st_occ = occ(st, '4,417'); lm_occ = occ(lm, '4,417')
def close(t, p, win=200):
    nq = nearest_qual(t, p)
    return bool(nq) and nq[0] <= win
st_qual = sum(1 for p in st_occ if close(st, p))
lm_qual = sum(1 for p in lm_occ if close(lm, p))
print('  200 字符内有限定的次数：statement %d/%d、limitations %d/%d'
      % (st_qual, len(st_occ), lm_qual, len(lm_occ)))
ck('② statement 列 10 次引用中带限定的 ≤ 2（大多数是裸值）',
   st_qual <= 2, st_qual)
ck('③ limitations 里也只有少数带限定（限定是**集中一处**而非逐次）',
   lm_qual <= 2, lm_qual)

tot = len(st_occ) + len(lm_occ)
print('  ⇒ 全行 4,417 共 %d 次，200 字符内带失效期限定的仅 %d 次' % (tot, st_qual + lm_qual))
ck('④ 该缺口是真实存在的（带限定次数 < 总次数的一半）',
   st_qual + lm_qual < tot / 2.0, (st_qual + lm_qual, tot))

print('\n== 反控 ==')
synth = '对象证据集合 = 4,417 文件 / 737,517,286 B。' * 1
ck('X1 自造裸值串：0 次带限定（判据不恒真）',
   sum(1 for p in occ(synth, '4,417') if close(synth, p)) == 0)
synth2 = '本条语料值是 11-22 快照值：4,417 文件。'
ck('X2 自造带限定串：1 次带限定（判据不恒假）',
   sum(1 for p in occ(synth2, '4,417') if close(synth2, p)) == 1)
ck('X3 自造串里没有 4,417 时得 0 次（不虚报）', len(occ('没有这个数', '4,417')) == 0)

print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
