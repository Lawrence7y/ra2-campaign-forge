#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r182a_corpus_label_census.py —— F24 语料值「失效期标注」的**逐次出现**普查。

待答问题（不是全文字符串计数，而是每一次出现是否带标注）：
  F24 正文里主引值 4,417 件 / 737,517,286 B 每出现一次，是否在**同一作用域**内声明了
  「2026-11-22 快照值 / 非现盘体量」？现盘值 65 件 / 44,470,975 B 每出现一次，是否声明了
  「现盘实测 / 测量时刻」？

口径必须显式声明（本仓反复被咬的点）：作用域取三种并列报，不挑一种冒充结论：
  W1 = 同句（以 。！？\n 切分，；不切）
  W2 = ±120 字符窗（含出现点自身）
  W3 = ±300 字符窗
标注词集合是**闭集合**，先打印出来，任何扩项都要改这个常量。

正反控：
  P1 正控：把已知带标注的那一处（statement @959 附近的 2026-11-22 快照值）判为「已标注」。
  N1 反控：把标注词从窗口里人为挖掉后必须判为「未标注」。
  N2 反控：出现点偏移必须真能落到目标串上（取回切片逐字等于目标串）。
  N3 空转反控：不存在的值（自造串 4,417,000 件）出现次数必须是 0。
"""
import csv, io, re, sys

TIER = '/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
CUR = TIER + '/R17_R131_FACTINDEX_V563/FACT_INDEX.tsv'

# 标注词闭集合（分两组：主引值需要「快照/失效」类；现盘值需要「现盘/测量时刻」类）
LABELS_SNAP = ['2026-11-22', '11-22 快照', '11-22 快照值', '快照值', '非现盘', '失效期',
               '不是现盘', '不在现盘', '现盘可 stat']
LABELS_DISK = ['现盘', '测量时刻', 'stat']

TARGETS = {
    'SNAP_FILES': re.compile(r'4,417'),
    'SNAP_BYTES': re.compile(r'737,517,286'),
    'DISK_FILES': re.compile(r'65 件'),
    'DISK_BYTES': re.compile(r'44,470,975'),
}

fails, oks = [], []
def ck(name, cond, detail=''):
    (oks if cond else fails).append(name)
    print(('  PASS  ' if cond else '  FAIL  ') + name + (('  ' + str(detail)) if detail else ''))
    return cond

def sentences(text):
    """返回 [(start, end, sent)]，句子分隔符为 。！？与换行（保留分隔符在句内）。"""
    out, start = [], 0
    for m in re.finditer(r'[。！？\n]', text):
        e = m.end()
        out.append((start, e, text[start:e]))
        start = e
    if start < len(text):
        out.append((start, len(text), text[start:]))
    return out

def sent_index(sents, pos):
    for i, (s, e, _) in enumerate(sents):
        if s <= pos < e:
            return i
    return None

def has_label(window, labels):
    return [l for l in labels if l in window]

rows = list(csv.reader(io.StringIO(io.open(CUR, encoding='utf-8', newline='').read(),
                                  newline=''), delimiter='\t'))
d = {r[0]: r for r in rows[1:]}
print('--- 文件与行 ---')
print('CUR = %s' % CUR)
print('F24 statement chars %d / limitations chars %d / F23..F35 行数 %d'
      % (len(d['F24'][1]), len(d['F24'][4]), len(rows) - 1))
print('LABELS_SNAP = %r' % (LABELS_SNAP,))
print('LABELS_DISK = %r' % (LABELS_DISK,))

print('\n--- 逐次出现表 ---')
table = []
for col, cname in ((1, 'statement'), (4, 'limitations')):
    text = d['F24'][col]
    sents = sentences(text)
    for tname, pat in TARGETS.items():
        for m in pat.finditer(text):
            pos = m.start()
            labels = LABELS_SNAP if tname.startswith('SNAP') else LABELS_DISK
            si = sent_index(sents, pos)
            s, e, sent = sents[si]
            w1 = sent
            w2 = text[max(0, pos - 120):pos + 120]
            w3 = text[max(0, pos - 300):pos + 300]
            pb = [0] + [mm.start() for mm in re.finditer(r'【', text)] + [len(text)]
            pi = max(i for i in range(len(pb) - 1) if pb[i] <= pos < pb[i + 1])
            w4 = text[pb[pi]:pb[pi + 1]]
            table.append(dict(col=cname, target=tname, pos=pos, senti=si, parai=pi,
                              head=w4[:26].replace(chr(10), ' '),
                              hit=sorted(set(m.group(0) for m in pat.finditer(text))),
                              L1=has_label(w1, labels), L2=has_label(w2, labels),
                              L3=has_label(w3, labels), L4=has_label(w4, labels)))
for r in table:
    print('  %-11s %-11s pos=%-6d sent=%-2d para=%-2d W1=%-3s W2=%-3s W3=%-3s W4=%-3s head=%s'
          % (r['col'], r['target'], r['pos'], r['senti'], r['parai'],
             'Y' if r['L1'] else 'n', 'Y' if r['L2'] else 'n',
             'Y' if r['L3'] else 'n', 'Y' if r['L4'] else 'n', r['head']))

print('\n--- 汇总（三种作用域并列，不挑一种）---')
summary = {}
for tname in TARGETS:
    for col in ('statement', 'limitations'):
        sub = [r for r in table if r['target'] == tname and r['col'] == col]
        if not sub:
            continue
        summary[(tname, col)] = tuple(sum(1 for r in sub if r[k]) for k in ('L1','L2','L3','L4'))
        print('  %-11s %-11s occ=%2d  labeled W1/W2/W3/W4 = %d/%d/%d/%d'
              % (tname, col, len(sub), *summary[(tname, col)]))

print('\n--- 未标注清单（口径 W2 = ±120 字符，最保守的一档）---')
unlabeled = [r for r in table if not r['L2']]
for r in unlabeled:
    text = d['F24'][1] if r['col'] == 'statement' else d['F24'][4]
    print('  %-11s %-11s pos=%-6d ... %s' % (r['col'], r['target'], r['pos'],
          text[r['pos'] - 60:r['pos'] + 60].replace('\n', ' ')))
print('  合计未标注(W2) = %d / %d 次出现' % (len(unlabeled), len(table)))

print('\n--- 正反控 ---')
# P1 正控：statement 里含「2026-11-22 快照值」的句子，其 SNAP_FILES 出现须判为已标注
st = d['F24'][1]
p1 = [r for r in table if r['col'] == 'statement' and r['target'] == 'SNAP_FILES' and r['L1']]
ck('P1 正控：statement 至少一处 SNAP_FILES 在同句内带标注', len(p1) >= 1, len(p1))
# N1 反控：把标注词挖掉后必须判为未标注
if p1:
    r = p1[0]
    sents = sentences(st)
    s, e, sent = sents[r['senti']]
    # S-182a1：首版只挖掉 '2026-11-22' 与 '快照值' 两个词，而该句同时还含 '非现盘'
    # ⇒ has_label 仍为真、反控假 FAIL。反控必须把**闭集合里每一个词**都挖掉。
    scrubbed = sent
    for _l in sorted(LABELS_SNAP, key=len, reverse=True):
        scrubbed = scrubbed.replace(_l, 'X' * len(_l))
    ck('N1 反控：同句挖掉闭集合全部标注词后 has_label 必须为假',
       not has_label(scrubbed, LABELS_SNAP), has_label(scrubbed, LABELS_SNAP))
# N2 反控：偏移切片逐字等于目标串
ok2 = True
for r in table:
    text = d['F24'][1] if r['col'] == 'statement' else d['F24'][4]
    if TARGETS[r['target']].match(text, r['pos']) is None:
        ok2 = False
ck('N2 反控：每个 pos 处 pattern.match 命中（偏移没有漂）', ok2)
# N3 空转反控：自造串 0 次
ck('N3 反控：自造串 4,417,000 件 出现 0 次',
   d['F24'][1].count('4,417,000') == 0 and d['F24'][4].count('4,417,000') == 0)
# N4 反控：全文件计数与按行累加一致（防止漏列）
full = io.open(CUR, encoding='utf-8', newline='').read()
s_per_row = sum(r[1].count('4,417') + r[4].count('4,417') for r in rows[1:])
ck('N4 反控：全部 54 行第2/5列 4,417 计数和 == 全文件计数（无遗漏列）',
   s_per_row == full.count('4,417'), (s_per_row, full.count('4,417')))

print('\n--- 汇总 ---')
print('PASS %d / FAIL %d' % (len(oks), len(fails)))
if fails:
    print('FAILED: ' + repr(fails)); sys.exit(1)
print('[exit 0]')
