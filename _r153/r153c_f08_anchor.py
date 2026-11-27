#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R153 C：两件事各自做成可失败判据。

(1) R149 §1204 一 的「12 个 fid、33 个锚点全部逐字命中」—— 那个 33 到底怎么数出来的？
    本脚本穷举 8 种可机械定义的候选口径，逐一给出计数，**只报数、不挑一个当答案**；
    若没有一种等于 33，就如实写「本轮未复现该计数口径」。

(2) F08 第二项证据 `R17_LEDGER_1064/SECTION.md(事项4)` 到底缺什么：
    a–e 三个细目 token（0x47C3D0 / 0x6F322F / 0x6F2B40）在
      - 台账 §1064 全节（0 处？）
      - 台账 §1064 事项 3 / 4 / 5（分别？）
      - R14_COMMON §2.9 一（1 / 2 / 2）
      - LEAD_LOCK / 看板归档（有多少行）
    并给出**候选修法**的机械核验：把第二项改成 §1064(事项3/4/5) 后，
    F08 statement 的哪些 token 落在这三个事项块内。

反控：所有判据都带「必须为真」与「必须为假」各一条。
"""
import hashlib
import os
import re
import sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
D = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
LED = os.path.join(ROOT, 'lead', 'GOAL_THREE_TARGETS_20261018.md')
LOCK = os.path.join(ROOT, 'lead', 'LEAD_LOCK')
RC = os.path.join(D, 'R14_COMMON.md')
ARC = os.path.join(D, 'BOARD_ARCHIVE.md')
F541 = os.path.join(D, 'R17_R113_FACTINDEX_V541', 'FACT_INDEX.tsv')

fails = []


def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok


lines = open(LED, encoding='utf-8', newline='').read().split('\n')
secs = [(i, re.match(r'^## §(\d+)', l).group(1)) for i, l in enumerate(lines)
        if re.match(r'^## §\d+', l)]
SEC = {}
for k, (i, num) in enumerate(secs):
    end = secs[k + 1][0] if k + 1 < len(secs) else len(lines)
    SEC[num] = (i, end)

rows = [l.split('\t') for l in open(F541, encoding='utf-8').read().split('\n') if l.strip()]
data = rows[1:]
BYID = {r[0]: r for r in data}

LEDREF = re.compile(r'R17_LEDGER_(\d+)')


def split_item(item):
    item = item.strip()
    i = item.find('(')
    if i < 0 or not item.endswith(')'):
        return item, None
    return item[:i], item[i + 1:-1]


# ---------- 甲类条目 ----------
items = []
for r in data:
    fid, stmt, ev = r[0], r[1], r[3]
    for it in ev.split(';'):
        it = it.strip()
        if not it or 'R17_LEDGER_10' not in it:
            continue
        path, anchor = split_item(it)
        if 'R17_LEDGER_10' not in path:
            continue
        m = LEDREF.search(path)
        sec = '1063' if m.group(1) == '1063R' else m.group(1)
        items.append({'fid': fid, 'sec': sec, 'anchor': anchor, 'stmt': stmt, 'raw': it})

print('=== (1) 「33 个锚点」口径穷举 ===')
print('甲类条目数（按 ; 切、路径含 R17_LEDGER_10）= %d' % len(items))
fids = sorted(set(x['fid'] for x in items))
print('唯一 fid 数 = %d' % len(fids))

# 事项号解析：只认「事项 N」与「事项N/M」；自由文本锚点另计
def anchor_nums(anchor):
    if not anchor:
        return []
    return [int(x) for x in re.findall(r'事项\s*(\d+)', anchor)]


cands = {}
cands['A 条目数'] = len(items)
cands['B 条目数 + 事项号展开口径'] = sum(max(1, len(anchor_nums(x['anchor']))) for x in items)
cands['C (fid, 节) 去重对数'] = len(set((x['fid'], x['sec']) for x in items))
cands['D (fid, 节, 事项) 三元组去重'] = len(set(
    (x['fid'], x['sec'], n) for x in items for n in (anchor_nums(x['anchor']) or [-1])))
cands['E fid 数 × 1（按 fid 计）'] = len(fids)
cands['F 全部 evidence_paths 项数（54 行）'] = sum(len([y for y in r[3].split(';') if y.strip()]) for r in data)
cands['G 全部 evidence_paths 失联项（R147 口径 43）'] = None
cands['H 甲类 token 唯一数'] = None
STOK = re.compile(r'`([^`]+)`|(0x[0-9A-Fa-f]{4,})|(?<![0-9A-Za-z_.])(\d{1,3}(?:,\d{3}){1,}|\d{3,})(?![0-9A-Za-z_])')
toks = set()
for x in items:
    for m in STOK.finditer(x['stmt']):
        toks.add(next(g for g in m.groups() if g is not None))
cands['H 甲类 token 唯一数'] = len(toks)
for k, v in cands.items():
    if v is None:
        continue
    mark = '  <== 等于 33' if v == 33 else ''
    print('  %-42s = %s%s' % (k, v, mark))
hit33 = [k for k, v in cands.items() if v == 33]
print('  等于 33 的口径：%s' % (hit33 if hit33 else '无（本轮未复现该计数）'))
ck('口径穷举结果如实登记（不强行凑 33）', True)

print()
print('=== (2) F08 第二项证据缺什么 ===')


def sec_block(num, item_no=None):
    i, e = SEC[num]
    body = lines[i:e]
    if item_no is None:
        return '\n'.join(body)
    starts = [(j, int(re.match(r'^###\s*(?:事项\s*)?(\d+)', l).group(1)))
              for j, l in enumerate(body)
              if re.match(r'^###\s*(?:事项\s*)?\d+', l)]
    blk = []
    for idx, (j, n) in enumerate(starts):
        if n == item_no:
            end = starts[idx + 1][0] if idx + 1 < len(starts) else len(body)
            blk.append('\n'.join(body[j:end]))
    return '\n'.join(blk)


AE = ['0x47C3D0', '0x6F322F', '0x6F2B40']
S1064 = sec_block('1064')
print('  §1064 全节 %d B' % len(S1064.encode()))
for t in AE:
    print('    %-10s §1064 全节 %d' % (t, S1064.count(t)))
for n in (3, 4, 5):
    b = sec_block('1064', n)
    print('  事项%d %d B ：%s' % (n, len(b.encode()), {t: b.count(t) for t in AE}))

# R14_COMMON §2.9 一
rc = open(RC, encoding='utf-8', newline='').read().split('\n')
i29 = [i for i, l in enumerate(rc) if l.startswith('## 2.9 ')][0]
i210 = [i for i, l in enumerate(rc) if l.startswith('## 2.10 ')][0]
s29 = rc[i29:i210]
j1 = [j for j, l in enumerate(s29) if l.startswith('### 一')][0]
j2 = [j for j, l in enumerate(s29) if l.startswith('### 二')][0]
s29_1 = '\n'.join(s29[j1:j2])
print('  R14_COMMON §2.9 一 %d B ：%s' % (len(s29_1.encode()), {t: s29_1.count(t) for t in AE}))
ck('正控：三个 a–e token 全部在 R14_COMMON §2.9 一 内（1/2/2）',
   all(s29_1.count(t) >= 1 for t in AE), [s29_1.count(t) for t in AE])
ck('反控：三个 a–e token 在台账 §1064 全节内 0 处（被引节根本没有这些数）',
   all(S1064.count(t) == 0 for t in AE), [S1064.count(t) for t in AE])

for name, p in (('LEAD_LOCK', LOCK), ('BOARD_ARCHIVE', ARC)):
    t = open(p, encoding='utf-8', newline='').read().split('\n')
    hit = [i + 1 for i, l in enumerate(t) if all(x in l for x in AE)]
    print('  %s 行级同时含三 token 的行数 = %d %s' % (name, len(hit), hit[:5]))

# ---------- 候选修法核验 ----------
print()
print('=== 候选修法核验：F08 第二项 -> §1064(事项3/4/5) ===')
f08 = BYID['F08']
ft = []
for m in STOK.finditer(f08[1]):
    ft.append(next(g for g in m.groups() if g is not None))
print('  F08 statement token 数 = %d：%s' % (len(ft), ft))
for n in (3, 4, 5):
    b = sec_block('1064', n)
    ins = [t for t in ft if t in b]
    print('  事项%d 命中 %d / %d ：%s' % (n, len(ins), len(ft), ins))
combo = sec_block('1064', 3) + '\n' + sec_block('1064', 4) + '\n' + sec_block('1064', 5)
ins = [t for t in ft if t in combo]
outs = [t for t in ft if t not in combo]
print('  事项3+4+5 合并命中 %d / %d ；未命中 %s' % (len(ins), len(ft), outs))
ck('候选修法：合并块命中 >= 2 且未命中项全部属 a–e 细目（只在 R14_COMMON）',
   len(ins) >= 2 and set(outs) <= set(AE), (len(ins), outs))
ck('第一项证据已覆盖 a–e（R14_COMMON §2.9一 在 evidence_paths 内）',
   '§2.9一' in f08[3].replace(' ', ''), f08[3][:80])

print()
print('=== 正反控 ===')
ck('反控：自造地址 0x42424242 在 §1064 0 命中', S1064.count('0x42424242') == 0)
ck('正控：0x47C620 在 §1064 事项3 命中', sec_block('1064', 3).count('0x47C620') >= 1)
ck('正控：不得升格 在 §1064 事项3 命中', '不得升格' in sec_block('1064', 3))
ck('反控：不得升格 不在 §1064 事项4', '不得升格' not in sec_block('1064', 4))

print('\nFAIL %d：%s' % (len(fails), fails))
sys.exit(1 if fails else 0)
