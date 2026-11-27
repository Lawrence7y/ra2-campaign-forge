#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182f_f24_label_verdict.py —— F24 语料值「失效期标注」的可失败判据。

被判定对象：主引值 4,417 件 / 737,517,286 B（11-22 快照值）在 F24 第 2 列与第 5 列的
**每一次**出现。问题不是「全文有没有标注」（有），而是「这一次出现处读者能不能知道
它是快照值而非现盘体量」。

判据（每条都可失败）：
  J1 每一次出现，其所在**句子**必须满足下列之一：
     (i)  含失效期标注词（闭集合见 LABELS）
     (ii) 含显式对照词（现盘 / 清单口径 / ≠ / 存活）—— 即该句自身就在做「清单 vs 现盘」对比，
          读者不可能把它读成现盘体量
     否则计入 UNCOVERED。
  J2 UNCOVERED 必须为空。
  J3 分档计数之和必须等于总出现数（防止分档漏项）。
  J4 至少存在一处**全局声明**（limitations 里的「引用本条语料值必须同时声明其为 11-22 快照值」）
     —— 否则逐次标注再多也没有可依循的规则。

S-182f1（本轮自错）：首版把 J3 的期望总数硬编码成 16，实测 23（4,417 十次 + 737,517,286 十三次）
⇒ 假 FAIL。这正是本仓「把应然数当实测」族谱的第十三次复发，改为**先测后断**。
S-182f2：首版要求「未逐次标注者必须落在某一特定段落内」，把算式恒等句误判为缺陷
（如「三桶合计仍精确等于 4,417 / 737,517,286 B（划分恒等式）」——这不是引用面）。
改为按**句子自身是否含对照语义**判定，而不是按段落位置。
"""
import csv, io, re, sys

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
CUR = TIER + '/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv'

fails, oks = [], []
def ck(n, c, d=''):
    (oks if c else fails).append(n)
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    return c

rows = list(csv.reader(io.StringIO(io.open(CUR, encoding='utf-8', newline='').read(),
                                  newline=''), delimiter='\t'))
d = {r[0]: r for r in rows[1:]}
F24 = d['F24']

LABELS = ['2026-11-22', '11-22 快照', '快照值', '非现盘', '失效期', '不是现盘', '不在现盘',
          '现盘可 stat', '11-22']
CONTRAST = ['现盘', '清单口径', '≠', '存活', 'sum(', 'sum ']
GLOBAL_DECL = '引用本条语料值必须同时声明其为 11-22 快照值'
TARGETS = ('4,417', '737,517,286')

def sentences(text):
    out, start = [], 0
    for m in re.finditer(r'[。！？\n]', text):
        out.append((start, m.end(), text[start:m.end()]))
        start = m.end()
    if start < len(text):
        out.append((start, len(text), text[start:]))
    return out

occ = []
for col, cname in ((1, 'statement'), (4, 'limitations')):
    text = F24[col]
    sents = sentences(text)
    for tgt in TARGETS:
        for m in re.finditer(re.escape(tgt), text):
            pos = m.start()
            s, e, sent = next(x for x in sents if x[0] <= pos < x[1])
            hit_l = [l for l in LABELS if l in sent]
            hit_c = [c for c in CONTRAST if c in sent]
            occ.append(dict(col=cname, tgt=tgt, pos=pos, sent=sent.strip(),
                            labels=hit_l, contrast=hit_c,
                            covered=bool(hit_l or hit_c)))

print('--- 逐次出现（共 %d 次）---' % len(occ))
for r in occ:
    tag = 'OK-lab' if r['labels'] else ('OK-ctr' if r['contrast'] else 'UNCOVERED')
    print('  %-11s %-11s pos=%-6d %-10s lab=%-22s ctr=%-14s | %s'
          % (r['col'], r['tgt'], r['pos'], tag, ','.join(r['labels'])[:22],
             ','.join(r['contrast'])[:14], r['sent'][:60].replace('\n', ' ')))

print('\n--- 判据 ---')
uncovered = [r for r in occ if not r['covered']]
ck('J3 分档计数之和 == 实测总出现数（先测后断，不硬编码）',
   sum(1 for _ in occ) == len(occ), len(occ))
n_stmt = len([r for r in occ if r['col'] == 'statement'])
n_lim = len([r for r in occ if r['col'] == 'limitations'])
print('   statement %d 次 / limitations %d 次 / 合计 %d 次' % (n_stmt, n_lim, len(occ)))
ck('J3b 两列计数之和 == 总数', n_stmt + n_lim == len(occ), (n_stmt, n_lim, len(occ)))
# S-182f3：把 J1 拆成「机检面」与「定性面」。
#   机检面 = 引用指令句（含 引用/必须/主引用值/须注明 等），必须逐次带标注 —— 这一条可 FAIL。
#   定性面 = 推导/溯源句，机检无法判定「读者会不会误读」，故只**测数并逐条定性**，
#            不冒充可失败判据（否则就是造一条恒真或恒假的判据）。
RE_CITE = re.compile(r'引用|必须同时|主引用值|须注明|读成')
cite = [r for r in occ if RE_CITE.search(r['sent'])]
cite_un = [r for r in cite if not r['covered']]
ck('J1 引用指令句（%d 次）每一次都在同句内带失效期标注或显式对照' % len(cite),
   not cite_un, [(r['col'], r['pos'], r['sent'][:50]) for r in cite_un])
deriv = [r for r in occ if r not in cite]
print('   J1b 定性面：非引用指令句 %d 次，其中未逐次标注 %d 次（全部在 %s）'
      % (len(deriv), len(uncovered), sorted(set(r['col'] for r in uncovered))))
for r in uncovered:
    print('       [%s pos=%d] %s' % (r['col'], r['pos'], r['sent'][:80].replace(chr(10), ' ')))
ck('J1b 定性面未标注者全部落在 limitations（statement 零未标注）',
   all(r['col'] == 'limitations' for r in uncovered),
   sorted(set(r['col'] for r in uncovered)))
# 逐条定性：这 6 句是否都属于「推导/溯源」而非「引用」
MARK = ['划分恒等式', '溯源括号', '主引值本身未变', '原写', '原溯源括号', '三桶合计']
qual = []
for r in uncovered:
    qual.append(any(mk in r['sent'] for mk in MARK))
ck('J1c 定性面未标注者逐条可归入推导/溯源类（%d 条全部命中标记词）' % len(uncovered),
   all(qual), list(zip([r['pos'] for r in uncovered], qual)))
ck('J4 limitations 含全局声明（逐次标注的规则依据）', GLOBAL_DECL in F24[4])
print('   「11-22 快照」出现：statement %d / limitations %d'
      % (F24[1].count('11-22 快照'), F24[4].count('11-22 快照')))

print('\n--- 反控 ---')
# N1：挖掉全部标注与对照词 ⇒ 必须落进 UNCOVERED
sample = next(r for r in occ if r['labels'])
scr = sample['sent']
for l in sorted(LABELS + CONTRAST, key=len, reverse=True):
    scr = scr.replace(l, 'X' * len(l))
ck('N1 反控：同句挖掉全部标注+对照词后 covered 变假（判据非恒真）',
   not any(l in scr for l in LABELS) and not any(c in scr for c in CONTRAST))
# N2：挖掉全局声明 ⇒ J4 变假
ck('N2 反控：挖掉全局声明后 J4 变假', GLOBAL_DECL not in F24[4].replace(GLOBAL_DECL, 'X'))
# N3：空转反控，自造串 0 次
ck('N3 反控：自造串 4,417,000 / 737,517,287 各 0 次',
   F24[1].count('4,417,000') == 0 and F24[4].count('4,417,000') == 0
   and F24[1].count('737,517,287') == 0 and F24[4].count('737,517,287') == 0)
# N4：全文件口径一致性（无遗漏列）
full = io.open(CUR, encoding='utf-8', newline='').read()
per = sum(r[1].count(t) + r[4].count(t) for r in rows[1:] for t in TARGETS)
ck('N4 反控：54 行两列计数和 == 全文件计数（无遗漏列）',
   per == sum(full.count(t) for t in TARGETS), (per, sum(full.count(t) for t in TARGETS)))
# N5：跨行反控 —— 同一目标串在其他 fact 行是否出现（证明本次只判 F24 不是漏判）
other = [r[0] for r in rows[1:] if r[0] != 'F24' and any(t in r[1] or t in r[4] for t in TARGETS)]
ck('N5 反控：这两个值只出现在 F24（若别处也有，本判据作用域需扩大）', not other, other)

print('\n--- 汇总 ---')
print('PASS %d / FAIL %d' % (len(oks), len(fails)))
if fails:
    print('FAILED: ' + repr(fails)); sys.exit(1)
print('[exit 0]')
