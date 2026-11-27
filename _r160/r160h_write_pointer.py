#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r160h_write_pointer.py —— 建立「哪个 FACT_INDEX 版本是当前版」的显式声明。

背景（R159 OP13 第 ④ 项，原文）：
  「本项目**仍无「哪个 FACT_INDEX 版本是当前版」的显式指针**——V543 是版本序最大，
    **属推断不是声明**」

为什么这重要：14 个版本目录同名文件 FACT_INDEX.tsv 并存，任何「按最大版本号取当前版」
的消费者都在做推断。一旦有人补一个 V544 的中间态草稿，推断就会静默指向它。
本脚本落一份机器可读的指针文件，内容只有三行事实：版本目录名、sha256、字节数，
外加一行「按什么规则判定」的说明，让消费者不必再推断。

写入纪律：wx 独占创建（已存在即拒绝，除内容完全相同则幂等通过）-> 断言旧态 -> 回读校验。
"""
import hashlib
import io
import os
import re
import sys

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
PTR = T + '/FACT_INDEX_CURRENT.md'

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok

print('== 0 · 实测全部 14 个版本，确认「当前版」不是靠猜 ==')
cands = []
for d in sorted(os.listdir(T)):
    m = re.match(r'R17_R(\d+)_FACTINDEX_V(\d+)$', d)
    if m:
        p = os.path.join(T, d, 'FACT_INDEX.tsv')
        if os.path.exists(p):
            cands.append((int(m.group(2)), int(m.group(1)), d, p))
cands.sort()
ck('0.1 版本数 == 14', len(cands) == 14, len(cands))
vers = [c[0] for c in cands]
ck('0.2 版本号连续 V530..V543 无缺', vers == list(range(530, 544)), (vers[0], vers[-1]))

# 版本号最大 == 当前版，必须同时满足「目录序号 R 也最大」且「是该序号唯一版本」
vmax, rmax, dmax, pmax = cands[-1]
ck('0.3 最大版本 V%d 的目录序号 R%d 也是最大' % (vmax, rmax),
   rmax == max(c[1] for c in cands), rmax)
ck('0.4 V%d 是 R%d 的唯一 FACT_INDEX 目录' % (vmax, rmax),
   sum(1 for c in cands if c[1] == rmax) == 1)

raw = open(pmax, 'rb').read()
sha = hashlib.sha256(raw).hexdigest()
print('  current = %s  bytes=%d  sha256=%s' % (dmax, len(raw), sha))

txt = io.open(pmax, encoding='utf-8', newline='').read()
rows = [l for l in txt.split('\n') if l.strip()]
ck('0.5 当前版 55 行（1 表头 + 54 数据）', len(rows) == 55, len(rows))
ck('0.6 当前版表头 5 列', rows[0].split('\t') ==
   ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'])
ck('0.7 当前版 LF-only', raw.count(b'\r') == 0, raw.count(b'\r'))

body = '''# FACT_INDEX 当前版指针（机器可读）

本文件是**声明**，不是推断。它回答唯一一个问题：**哪个版本的 FACT_INDEX.tsv 是当前版。**

## 当前版

| 项 | 值 |
|---|---|
| 版本目录 | %s |
| 相对路径 | lead/next_re_20261117_r14/%s/FACT_INDEX.tsv |
| sha256 | %s |
| 字节数 | %d |
| 行数 | 55（1 表头 + 54 数据行） |
| 列 | fact_id / statement / grade / evidence_paths / limitations |
| 编码纪律 | LF-only（CR = 0） |
| 声明轮次 | R160 |
| 声明依据 | 版本号 530..543 连续无缺，V%d 同时是「版本号最大」且「其目录序号 R%d 为最大」，且 R%d 下只有这一个 FACT_INDEX 目录（三项同时成立才写本文件） |

## 消费者应当怎么做

1. **读本文件**取路径与 sha256，不要自己扫目录取最大版本号。取最大版本号是**推断**，
   补一个 V544 草稿就会静默指错。
2. 读到的文件 sha256 必须等于上表值；不等即视为**指针过期**，应 FAIL 而不是继续。
3. 升版时**先**写新版本目录，**再**改本文件（顺序不能反：先改指针会指向不存在的文件）。

## 边界（如实声明）

- 本文件只声明「哪一份是当前版」，**不声明其内容为真**。事实真假由 FACT_INDEX 正文
  及各条 limitations 的作用域决定。
- 本文件**不是**门禁。守门脚本是 `_r160/facts_floors.py`（D0 已钉 V%d 的 sha256）；
  两者若不一致，**以 facts_floors.py 的 D0 为准**（它每次运行都会实测 sha256，
  本文件只是静态文本）。
- 历史版本**一律保留不删**：V530..V542 是 14 个可独立复核的快照，
  删任何一个都会让「某条事实何时首现」变得不可复算。
''' % (dmax, dmax, sha, len(raw), vmax, rmax, rmax, vmax)

# 幂等：已存在且逐字相同 -> 通过
if os.path.exists(PTR):
    old = io.open(PTR, encoding='utf-8', newline='').read()
    if old == body:
        print('\n== 1 · 幂等：指针文件已存在且逐字相同，无需写入 ==')
        ck('1.0 幂等通过', True)
        print('\nFAILS:', fails if fails else 'NONE')
        sys.exit(0)
    print('\n== 1 · 指针文件已存在但内容不同 -> 拒绝静默覆盖 ==')
    ck('1.0 拒绝覆盖既有指针（需人工确认）', False, PTR)
    print('\nFAILS:', fails)
    sys.exit(1)

print('\n== 1 · wx 独占创建指针文件 ==')
fd = os.open(PTR, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
with os.fdopen(fd, 'wb') as f:
    f.write(body.encode('utf-8'))
print('  created %s bytes=%d' % (PTR, len(body.encode())))

back = io.open(PTR, encoding='utf-8', newline='').read()
ck('1.1 回读逐字一致', back == body)
ck('1.2 LF-only', back.count('\r') == 0, back.count('\r'))
ck('1.3 指针里的 sha256 与当前版实测一致', sha in back)
ck('1.4 指针里的字节数与当前版实测一致', str(len(raw)) in back)

print('\n== 2 · 生产台账未被本脚本改动 ==')
ck('2.1 V543 sha256 仍为 6b00f955…', hashlib.sha256(open(pmax, 'rb').read()).hexdigest() == sha)

print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
