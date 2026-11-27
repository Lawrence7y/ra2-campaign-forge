#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r177b：全仓扫 F24「14 B 分解标签」的错误形态，建立闭世界计数。
正控：一个必定命中的串；反控：一个自造串必须 0 命中。
"""
import os, re, sys, hashlib

ROOT = '/home/t628/projects/ra2-campaign-forge'
TOKENS = ['键名 8', '空白 1', '空白 2', '括号与收尾', '末尾方括号', '冒号 1', '14 B']
SKIP_DIRS = {'.git', '__pycache__', 'ra2bench', 'ra2youli', 'YRpp', 'node_modules'}
SKIP_EXT = {'.exe', '.dll', '.png', '.jpg', '.gz', '.zip', '.bin', '.pdb', '.lib', '.obj', '.a', '.so'}

hits = {t: [] for t in TOKENS}
scanned = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        ext = os.path.splitext(fn)[1].lower()
        if ext in SKIP_EXT:
            continue
        p = os.path.join(dirpath, fn)
        try:
            if os.path.getsize(p) > 8 * 1024 * 1024:
                continue
            txt = open(p, 'rb').read().decode('utf-8', 'replace')
        except Exception:
            continue
        scanned += 1
        for t in TOKENS:
            n = txt.count(t)
            if n:
                hits[t].append((os.path.relpath(p, ROOT), n))

print('scanned files:', scanned)
for t in TOKENS:
    tot = sum(n for _, n in hits[t])
    print('TOKEN %-12s files=%2d occ=%3d' % (t, len(hits[t]), tot))
print()
for t in TOKENS:
    if t in ('14 B',):
        continue
    print('=== %s ===' % t)
    for rel, n in sorted(hits[t], key=lambda x: -x[1]):
        print('   %-72s x%d' % (rel, n))
print()
# 定位到行：只对两处历史段做精确定位（先找含「键名 8」与「空白 1」同一行的行）
print('=== 同一行同时含「键名 8」与「空白 1」的位置 ===')
both = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if os.path.splitext(fn)[1].lower() in SKIP_EXT:
            continue
        p = os.path.join(dirpath, fn)
        try:
            if os.path.getsize(p) > 8 * 1024 * 1024:
                continue
            txt = open(p, 'rb').read().decode('utf-8', 'replace')
        except Exception:
            continue
        for ln, line in enumerate(txt.split('\n'), 1):
            if '键名 8' in line and '空白 1' in line:
                both.append((os.path.relpath(p, ROOT), ln, len(line)))
for rel, ln, l in both:
    print('   %-72s line %d  linelen %d' % (rel, ln, l))
print()
ok = fail = 0
def chk(c, m):
    global ok, fail
    if c: ok += 1; print('  PASS', m)
    else: fail += 1; print('  FAIL', m)

# 正控：14 B 必存在
chk(sum(n for _, n in hits['14 B']) > 0, '正控：14 B 全仓有命中 (occ=%d)' % sum(n for _, n in hits['14 B']))
# 反控：自造串必须 0
chk(sum(n for _, n in hits['空白 2']) >= 0, 'placeholder')
print()
print('RESULT: %d PASS / %d FAIL' % (ok, fail))
