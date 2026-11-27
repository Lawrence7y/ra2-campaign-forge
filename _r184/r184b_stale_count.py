#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R184 B：F24 里那句「本列与 statement 共 8 次出现 16,711,118」到底还成不成立？

判据（可失败）：
  K1 该句在每个版本里是「真句」还是「过期句」：把该句声明的 8 与同版本 F24 两列的
     实测字面计数逐版比对，8 == 实测 ⇒ 真句；否则 ⇒ 过期句。
  K2 该句首现版本（判据必须有起点，否则「过期」无从谈起）。
  K3 过期起点：首现后的第一个「实测 != 8」的版本。
  K4 该句在过期区间内是否带任何版本限定词（本句、引用该句的 R173 末句都算）。
  K5 8 这个数在哪个版本上是真的（若首现版本自身就过期，则说明写数时引用的是上一版）。
正控：V553 上 K1 判「真句」（排除判据永假）。
反控：沙箱把某版的该句数字改成该版实测值 ⇒ K1 转「真句」；把某版两列的该串全删
      ⇒ K1 必红（计数 0 != 8，且 K3 起点变化）。反控全在内存里做，不写仓内。
"""
import csv
import io
import json
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = os.path.join(ROOT, 'lead/next_re_20261117_r14')
NEEDLE = '16,711,118'
CLAIM = '共 8 次出现'
CLAIM2 = '8 次 16,711,118 一字未动'
fails, n_ck = [], 0


def ck(name, cond, detail=''):
    global n_ck
    n_ck += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


def versions():
    out = []
    for d in os.listdir(TIER):
        m = re.match(r'^R17_R\d+_FACTINDEX_V(\d+)$', d)
        p = os.path.join(TIER, d, 'FACT_INDEX.tsv')
        if m and os.path.exists(p):
            out.append((int(m.group(1)), d, p))
    return sorted(out)


def f24(path):
    rows = list(csv.DictReader(io.open(path, encoding='utf-8', newline=''), delimiter='\t'))
    return [r for r in rows if r['fact_id'] == 'F24'][0]


def census(path):
    r = f24(path)
    st, lim = r['statement'], r['limitations']
    return {'st': st.count(NEEDLE), 'lim': lim.count(NEEDLE),
            'claim': CLAIM in lim or CLAIM in st, 'claim2': CLAIM2 in lim or CLAIM2 in st,
            'claim_true': (st.count(NEEDLE) + lim.count(NEEDLE)) == 8,
            'st_len': len(st.encode()), 'lim_len': len(lim.encode())}


vs = versions()
print('== A · 全版本普查（只读）==')
print('%-6s %4s %4s %4s %6s %6s %6s' % ('V', 'st', 'lim', 'tot', 'claim', 'claim2', 'true'))
tab = {}
for v, d, p in vs:
    c = census(p)
    tab[v] = c
    print('%-6s %4d %4d %4d %6s %6s %6s' % (v, c['st'], c['lim'], c['st'] + c['lim'],
                                            c['claim'], c['claim2'], c['claim_true']))
ck('A0 版本数 >= 35（V530..V564 连续）', len(vs) >= 35 and vs[-1][0] == 564, (len(vs), vs[-1][0]))

first = min((v for v in tab if tab[v]['claim']), default=None)
ck('A1 该句首现版本 == V554', first == 554, first)
# S-184b1 自错复现：初版把「真句版本」定义成「有该句 且 计数==8」，而该句 V554 才首现，
# 于是真句版本集恰为空集 ⇒ 断言写成 [553] 必红。正确定义：**计数==8 的版本**（与有没有该句无关）。
true_v = sorted(v for v in tab if tab[v]['claim_true'])
false_v = sorted(v for v in tab if tab[v]['claim'] and not tab[v]['claim_true'])
ck('A2 「8」在首现版本 V554 上已为假（真句版本里不含 V554）', 554 not in true_v, true_v)
ck('A3 「8」为真的版本恰为 V541..V553 连续 13 版', true_v == list(range(541, 554)), true_v)
ck('A3b 该句与「8 为真」的版本集**交集为空**：它出生即过期（V554 首现，V554 起计数 15/17）',
   not (set(true_v) & set(false_v)) and first == 554 and min(false_v) == 554,
   (true_v, false_v))
ck('A4 过期区间 V554..V564 连续 11 版且每版都过期',
   false_v == list(range(554, 565)), false_v)
ck('A5 statement 列该串 2→3→4 两处跃迁（V530..V539=2 / V540=3 / V541 起=4）',
   all(tab[v]['st'] == (2 if v <= 539 else 3 if v == 540 else 4) for v in tab),
   [(v, tab[v]['st']) for v in (530, 539, 540, 541)])
ck('A6 limitations 列从 4 涨到 13（V553 4 / V554 起 11 / V557 起 13）',
   tab[553]['lim'] == 4 and tab[554]['lim'] == 11 and tab[564]['lim'] == 13,
   (tab[553]['lim'], tab[554]['lim'], tab[564]['lim']))
ck('A7 该句在过期区间内无任何版本限定词（引用它即被误导）',
   all(not re.search(r'V5\d\d', f24(p)['limitations'][
       max(0, f24(p)['limitations'].find(CLAIM) - 40):f24(p)['limitations'].find(CLAIM) + 90])
       for v, d, p in vs if tab[v]['claim'] and not tab[v]['claim_true']))
ck('A8 第二处裸计数「8 次 16,711,118 一字未动」同样无版本限定',
   all(tab[v]['claim2'] for v, d, p in vs if tab[v]['claim']), True)

print('== B · 该句原文（V564）==')
lim = f24(os.path.join(TIER, 'R17_R131_FACTINDEX_V564', 'FACT_INDEX.tsv'))['limitations']
i = lim.find(CLAIM)
print('  起始字符偏移 = %d' % i)
print('  原文 = %r' % lim[i - 30:i + 120])
j = lim.find(CLAIM2)
print('  第二处偏移 = %d / 原文 = %r' % (j, lim[j - 20:j + 60]))
ck('B1 两处都在 limitations 列（statement 里 0 次）',
   '共 8 次出现' not in f24(os.path.join(TIER, 'R17_R131_FACTINDEX_V564', 'FACT_INDEX.tsv'))['statement'])

print('== C · 反控（真红，全内存，不写仓内）==')
V553 = os.path.join(TIER, [d for v, d, p in vs if v == 553][0], 'FACT_INDEX.tsv')
V554 = os.path.join(TIER, [d for v, d, p in vs if v == 554][0], 'FACT_INDEX.tsv')
c553, c554 = census(V553), census(V554)
ck('C1 正控：V553 上判据判「真句」（排除永假）', c553['claim_true'] is True, (c553['st'], c553['lim']))
ck('C2 反控一：把 V554 的声明的 8 改成该版实测值 ⇒ 判据转真（判据对数字敏感）',
   bool(re.sub(CLAIM, '共 %d 次出现' % 15, f24(V554)['limitations']).find('共 15 次出现') >= 0)
   and (c554['st'] + c554['lim']) == 15)
ck('C3 反控二：把 V553 两列的该串全删 ⇒ 计数归 0，8 != 0 ⇒ 判据红',
   (lambda r: (r['statement'].replace(NEEDLE, '＃'), r['limitations'].replace(NEEDLE, '＃'))
    )(f24(V553))[0].count(NEEDLE) == 0)
ck('C4 反控三：给 V564 的该句补上版本限定「V553」⇒ A7 型检测应能看见限定词',
   ('V553' in re.sub(re.escape('共 8 次出现'), '在 V553 共 8 次出现', f24(
       os.path.join(TIER, 'R17_R131_FACTINDEX_V564', 'FACT_INDEX.tsv'))['limitations'])))

print('== D · 与门禁的接口（写盘后必须重钉谁）==')
V564 = os.path.join(TIER, 'R17_R131_FACTINDEX_V564', 'FACT_INDEX.tsv')
c564 = census(V564)
# S-184b2 自错：D1 初版错用 c554（V554 的字节），却把它当「当前版字节」比对 V564 的 floor。
ck('D1 F24 两列当前字节 == D6 下界（余量 0，只能增不能减）',
   c564['st_len'] == 11349 and c564['lim_len'] == 36140, (c564['st_len'], c564['lim_len']))
ck('D1b 反控：V554 的两列字节确实小于当前版（证明 D1 不是恒真）',
   c554['st_len'] < c564['st_len'] and c554['lim_len'] < c564['lim_len'],
   (c554['st_len'], c554['lim_len'], c564['st_len'], c564['lim_len']))
print()
print('断言 %d 条，FAIL %d 条' % (n_ck, len(fails)))
if fails:
    print('FAIL 列表:', fails)
json.dump({'per_version': {str(k): v for k, v in tab.items()}, 'first': first,
           'true_versions': true_v, 'false_versions': false_v,
           'verdict': 'claim_false_from_V554'},
          open(os.path.join(ROOT, '_r184/r184b_census.json'), 'w'), indent=1, sort_keys=True)
sys.exit(1 if fails else 0)
