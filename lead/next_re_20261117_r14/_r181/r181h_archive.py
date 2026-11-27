#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r181h_archive.py —— 看板 283 行 >= 260，搬走最早的 2 段（R164 / R171）到 BOARD_ARCHIVE。
纪律：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0；搬走内容逐字节可回读校验。
"""
import hashlib, io, os, sys

BRD = 'STATUS_BOARD.md'; ARC = 'BOARD_ARCHIVE.md'
BASE = 'R17_LEAD_BASELINE'
fails = []
def ck(n, c, d=''):
    print(('  PASS  ' if c else '  FAIL  ') + n + (('  ' + str(d)) if d else ''))
    if not c: fails.append(n)

b = io.open(BRD, encoding='utf-8', newline='').read()
a = io.open(ARC, encoding='utf-8', newline='').read()
B_SHA = hashlib.sha256(b.encode('utf-8')).hexdigest()
A_SHA = hashlib.sha256(a.encode('utf-8')).hexdigest()
ck('P1 board sha 命中实测基线', B_SHA == 'b19d3a01efba876cbea17b806cc94281d97582e12dcaaca741d08c7abfaa1323', B_SHA[:16])
ck('P2 board CR=0', b.count('\r') == 0, b.count('\r'))
ck('P3 archive CR=2952', a.count('\r\n') == 2952, a.count('\r\n'))
ck('P4 board 行数 283 >= 260（触发归档）', b.count('\n') == 283, b.count('\n'))

lines = b.split('\n')
heads = [i for i, l in enumerate(lines) if l.startswith('## ')]
ck('P5 恰 11 个段头', len(heads) == 11, len(heads))
ck('P6 前 3 个段头位置 = 0/26/57', heads[:3] == [0, 26, 57], heads[:3])
seg = lines[0:57]            # R164 + R171
rest = lines[57:]            # R172 起
ck('P7 搬走的段以 R164 开头', seg[0].startswith('## 🟢 R17 第 164 轮'))
ck('P8 搬走的段以 R171 结尾（R172 不在其中）',
   any(l.startswith('## 🟢 R17 第 171 轮') for l in seg)
   and not any(l.startswith('## 🟢 R17 第 172 轮') for l in seg))
ck('P9 留下的第一段是 R172', rest[0].startswith('## 🟢 R17 第 172 轮'))

seg_txt = '\n'.join(seg)
new_arc = a + '\n' + seg_txt + '\n'
new_brd = '\n'.join(rest)
ck('C1 归档后 board 行数 = 283-57 = 226', new_brd.count('\n') + 1 == 227, new_brd.count('\n') + 1)
ck('C2 归档后 board CR 仍为 0', new_brd.count('\r') == 0, new_brd.count('\r'))
ck('C3 归档后 archive CR 增益 = seg 内的 CR（0）⇒ 仍 2952',
   new_arc.count('\r\n') == 2952, new_arc.count('\r\n'))
# S-684：首版把搬走的字节写成 12070，实测**含分隔换行**是 12071。
# 严格账：seg(12070) + 分隔换行(1) + rest(47942) = 60013 = 原 board 字节数（逐字节闭合）。
ck('C4 搬走的字节 = 12071（含分隔换行；12071 + 47942 = 60013 逐字节闭合）',
   len(seg_txt.encode('utf-8')) + 1 == 12071
   and len(seg_txt.encode('utf-8')) + 1 + len('\n'.join(lines[57:]).encode('utf-8')) == len(b.encode()),
   (len(seg_txt.encode('utf-8')) + 1, len('\n'.join(lines[57:]).encode('utf-8')), len(b.encode())))
ck('C5 未搬走内容逐字节保留（board 剩余 == 原 board 的 rest 部分）',
   new_brd == '\n'.join(lines[57:]))
ck('C6 归档新增部分是原 board 前 57 行的逐字节复制',
   new_arc.startswith(a) and new_arc[len(a):] == '\n' + seg_txt + '\n')

if fails:
    print('拒绝写盘'); print('[exit 1] %d FAIL' % len(fails)); sys.exit(1)

import datetime
ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
for src, txt in ((BRD, b), (ARC, a)):
    bak = os.path.join(BASE, '%s.before_r181_archive_%s.bak' % (os.path.basename(src), ts))
    fd = os.open(bak, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    os.write(fd, txt.encode('utf-8')); os.close(fd)
    ck('W1 备份 %s' % os.path.basename(bak), open(bak, 'rb').read() == txt.encode('utf-8'))
ck('W2 写前 board 仍旧 sha', hashlib.sha256(open(BRD, 'rb').read()).hexdigest() == B_SHA)
ck('W3 写前 archive 仍旧 sha', hashlib.sha256(open(ARC, 'rb').read()).hexdigest() == A_SHA)
io.open(ARC, 'w', encoding='utf-8', newline='').write(new_arc)
io.open(BRD, 'w', encoding='utf-8', newline='').write(new_brd)
rb = open(BRD, 'rb').read(); ra = open(ARC, 'rb').read()
ck('W4 回读 board CR=0', rb.count(b'\r') == 0, rb.count(b'\r'))
ck('W5 回读 archive CR=2952', ra.count(b'\r\n') == 2952, ra.count(b'\r\n'))
# S-685：W6 首版写成 newlines + (0 if endswith nl else 1)，而文件确实以 \n 结尾
# ⇒ 该式恒等于 newlines = 226，与「文件有 227 行（最后一行以换行收尾）」这两个口径混用。
# 统一口径：**文件行数 = 换行符个数**（wc -l 口径），并单独断言「以换行结尾」。
ck('W6 回读 board 行数 = 226（wc -l 口径：换行符个数）且以换行收尾',
   rb.count(b'\n') == 226 and rb.endswith(b'\n'), (rb.count(b'\n'), rb.endswith(b'\n')))
print('board bytes %d -> %d ; archive bytes %d -> %d'
      % (len(b.encode()), len(rb), len(a.encode()), len(ra)))
print('fails=%d' % len(fails))
if fails: print(repr(fails)); sys.exit(1)
print('[exit 0]')
