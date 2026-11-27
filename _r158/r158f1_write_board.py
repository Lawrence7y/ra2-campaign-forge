#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158f1_write_board.py — 向 STATUS_BOARD.md 追加第 158 轮记录。幂等；全 LF；CR 保持 0。
行数上限 300：写入前先量，若 >= 260 则拒绝并提示须先归档（本轮应不触发）。
"""
import hashlib, io, os, re, sys

R = '/home/t628/projects/ra2-campaign-forge'
P = R + '/lead/next_re_20261117_r14/STATUS_BOARD.md'
SEC_F = R + '/_r158/section_board_r158.md'
BAK = R + '/lead/next_re_20261117_r14/R17_LEAD_BASELINE/before_r158_board_20261127_064311.md'

EXPECT_OLD_SHA8 = 'dab4303753f44f19f241'
EXPECT_CR = 0
SEC_BYTES_MIN = 6000
BOARD_MAX = 300
ARCHIVE_TRIGGER = 260

fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok:
        fails.append(n)
    return ok

raw = io.open(P, encoding='utf-8', newline='').read()
sec_text = io.open(SEC_F, encoding='utf-8', newline='').read()
ck('0.1 节稿字节 >= 下界', len(sec_text.encode('utf-8')) >= SEC_BYTES_MIN,
   len(sec_text.encode('utf-8')))
ck('0.2 节稿 CR 为 0', sec_text.count('\r') == 0, sec_text.count('\r'))
ck('0.3 标题逐字', sec_text.startswith('## 🟢 R17 第 158 轮'), sec_text[:30])

_n0 = raw.replace('\r\n', '\n')
already = re.search(r'(?m)^##\s+🟢 R17 第 158 轮', _n0) is not None
lines_before = _n0.count('\n') + (0 if _n0.endswith('\n') else 1)
print('  写入前行数 =', lines_before)

if already:
    print('  [idempotent] 第 158 轮记录已存在，跳过写入')
else:
    ck('1.1 备份存在', os.path.exists(BAK), BAK)
    ck('1.2 旧 sha 前缀吻合',
       hashlib.sha256(open(P, 'rb').read()).hexdigest()[:20] == EXPECT_OLD_SHA8,
       hashlib.sha256(open(P, 'rb').read()).hexdigest()[:20])
    ck('1.3 旧 CR 计数 == 0', raw.count('\r') == EXPECT_CR, raw.count('\r'))
    ck('1.4 行数未达归档触发线 %d' % ARCHIVE_TRIGGER, lines_before < ARCHIVE_TRIGGER, lines_before)
    body = sec_text if sec_text.endswith('\n') else sec_text + '\n'
    new = raw.rstrip('\n') + '\n\n' + body
    add_lines = body.count('\n')
    # S-438：行数上限必须在**写盘之前**用实测值断言（原版放在写盘之后，违规已落到盘上）
    _nlines_new = new.replace('\r\n', '\n').count('\n')
    ck('1.5 写入后行数 <= %d（写盘前断言）' % BOARD_MAX, _nlines_new <= BOARD_MAX, _nlines_new)
    ck('1.5b 本段实测行数（不估算）', add_lines == sec_text.count('\n'), add_lines)
    if _nlines_new > BOARD_MAX:
        print('  [ABORT] 拒绝写盘：行数超限')
        print('\nFAILS=%d' % len(fails)); sys.exit(1)
    with io.open(P, 'w', encoding='utf-8', newline='') as f:
        f.write(new)
    print('  [written] 追加 %d 字节 / %d 行' % (len(body.encode('utf-8')), add_lines))

back = io.open(P, encoding='utf-8', newline='').read()
_n = back.replace('\r\n', '\n')
ck('2.1 CR 计数仍 == 0（全 LF）', back.count('\r') == 0, back.count('\r'))
nlines = _n.count('\n') + (0 if _n.endswith('\n') else 1)
ck('2.2 总行数 <= %d' % BOARD_MAX, nlines <= BOARD_MAX, nlines)
ck('2.3 第 158 轮标记恰 1 个', len(re.findall(r'(?m)^##\s+🟢 R17 第 158 轮', _n)) == 1,
   len(re.findall(r'(?m)^##\s+🟢 R17 第 158 轮', _n)))
ck('2.4 第 157 / 156 轮记录仍在（未覆盖）',
   len(re.findall(r'(?m)^##\s+🟢 R17 第 157 轮', _n)) == 1 and
   len(re.findall(r'(?m)^##\s+🟢 R17 第 156 轮', _n)) == 1,
   (len(re.findall(r'(?m)^##\s+🟢 R17 第 157 轮', _n)),
    len(re.findall(r'(?m)^##\s+🟢 R17 第 156 轮', _n))))
m = re.search(r'(?ms)^##\s+🟢 R17 第 158 轮.*?(?=^##\s|\Z)', _n)
ck('2.5 能切出第 158 轮段', m is not None, m is not None)
if m:
    b = m.group(0)
    nb = len(b.encode('utf-8'))
    ck('2.6 该段字节 >= %d' % SEC_BYTES_MIN, nb >= SEC_BYTES_MIN, nb)
    for tok in ('V533→V534', 'F29', 'F35', '1,392,592', '100.000000%', '86.188273%', 'S-437'):
        ck('2.7 段体含 %r' % tok, tok in b, tok in b)
ck('2.8 无 CRLF 混入', back.count('\r\n') == 0, back.count('\r\n'))
print('\nFAILS=%d bytes=%d lines=%d cr=%d' %
      (len(fails), len(back.encode('utf-8')), nlines, back.count('\r')))
sys.exit(0 if not fails else 1)
