#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r161m_addendum3.py —— 把 S-466/S-467 追加进 OR 段与看板第 161 轮（纯后缀追加，幂等）。"""
import io
import os
import re
import sys
import time

R = '/home/t628/projects/ra2-campaign-forge'
T = R + '/lead/next_re_20261117_r14'
BD = T + '/R17_LEAD_BASELINE'
SRC = R + '/_r161'
TARGETS = [
    (R + '/lead/LEAD_LOCK', r'(?ms)^##\s+OR ·.*?(?=^##\s+[A-Z]{2} ·|\Z)', SRC + '/addendum3_OR.md', 'OR3'),
    (T + '/STATUS_BOARD.md', r'(?ms)^##\s+🟢 R17 第 161 轮\b.*?(?=^##\s|\Z)', SRC + '/addendum3_board.md', 'board3'),
]
fails = []
def ck(n, c, d=''):
    ok = bool(c)
    print(('  PASS ' if ok else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not ok: fails.append(n)
    return ok
def rb(p):
    with open(p, 'rb') as f: return f.read()

for p, pat, add, tag in TARGETS:
    b0 = rb(p)
    txt = b0.decode('utf-8').replace('\r\n', '\n')
    m = re.search(pat, txt)
    ck('0.%s 段可定位' % tag, m is not None)
    add_t = io.open(add, encoding='utf-8', newline='').read()
    if 'S-467' in m.group(0):
        print('     %-8s 幂等：段内已含 S-467，跳过' % tag); continue
    seg_first = m.group(0).split('\n')[0]
    idx = b0.find(seg_first.encode('utf-8'))
    nxt = re.search(r'(?m)^##\s', txt[m.end():])
    if nxt:
        nl = txt[m.end():].split('\n')[0]
        b_idx = b0.find(nl.encode('utf-8'), idx + len(seg_first.encode('utf-8')))
    else:
        b_idx = len(b0)
    tail = b0[idx:b_idx].rstrip(b'\r\n')
    b1 = b0[:idx] + tail + add_t.encode('utf-8') + b0[idx + len(tail):]
    ck('1.%s 纯插入且增量为片段字节数' % tag,
       len(b1) - len(b0) == len(add_t.encode()) and b1.startswith(b0[:idx] + tail)
       and b1.endswith(b0[idx + len(tail):]), (len(b1) - len(b0), len(add_t.encode())))
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bp = os.path.join(BD, os.path.basename(p) + '.before_r161_add3_%s_%s.bak' % (tag, stamp))
    fd = os.open(bp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, 'wb') as f:
        f.write(b0)
    ck('1.%s 备份逐字节相同' % tag, rb(bp) == b0)
    with open(p, 'wb') as f:
        f.write(b1)
    ck('1.%s 回读一致' % tag, rb(p) == b1)
    print('     %-8s %d -> %d B (+%d)' % (tag, len(b0), len(b1), len(b1) - len(b0)))

print('\n== 2 · 不变量 ==')
ck('2.1 LEAD_LOCK CR 仍 137', rb(R + '/lead/LEAD_LOCK').count(b'\r') == 137)
ck('2.2 STATUS_BOARD CR 仍 0', rb(T + '/STATUS_BOARD.md').count(b'\r') == 0)
n = rb(T + '/STATUS_BOARD.md').decode().count('\n')
ck('2.3 看板行数 <= 300', n <= 300, n)
print('\nFAILS:', fails if fails else 'NONE')
sys.exit(1 if fails else 0)
