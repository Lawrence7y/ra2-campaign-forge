#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R101 四件套写入（写入纪律：wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验）"""
import os, io, json, hashlib, datetime, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
BASE = 'lead/next_re_20261117_r14/R17_LEAD_BASELINE'
R14 = 'lead/next_re_20261117_r14/R14_COMMON.md'
LOCK = 'lead/LEAD_LOCK'
G3 = 'lead/GOAL_THREE_TARGETS_20261018.md'
SB = 'lead/next_re_20261117_r14/STATUS_BOARD.md'
TS = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

EXPECT = {R14: ('R14_COMMON', 1081), LOCK: ('LEAD_LOCK', 137),
          G3: ('GOAL_THREE_TARGETS', 337), SB: ('STATUS_BOARD', 0)}

def sha(b): return hashlib.sha256(b).hexdigest()

def backup(path, cr_expected):
    b = open(path, 'rb').read()
    cr = b.count(b'\r')
    assert cr == cr_expected, 'CR 不符 %s: %d != %d' % (path, cr, cr_expected)
    tag = EXPECT[path][0]
    dst = '%s/SUPERSEDED.before_r101_%s_%s.md' % (BASE, tag, TS)
    fd = os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)   # wx 独占
    with os.fdopen(fd, 'wb') as f:
        f.write(b)
    back = open(dst, 'rb').read()
    assert sha(back) == sha(b), '备份回读 sha256 不符'
    print('BACKUP %s -> %s (%d B, sha %s)' % (path, dst, len(b), sha(b)[:16]))
    return sha(b), cr

def commit(path, add_bytes, cr_expected):
    old_sha, cr = backup(path, cr_expected)
    b = open(path, 'rb').read()
    assert sha(b) == old_sha, '写入前旧文件已被改动'
    newb = b + add_bytes
    with open(path, 'wb') as f:
        f.write(newb)
    back = open(path, 'rb').read()
    assert back == newb, '回读不符'
    assert back.count(b'\r') == cr, 'CR 变了：%d -> %d' % (cr, back.count(b'\r'))
    print('WROTE %s  +%d B  (CR %d 保持, LF %d -> %d)'
          % (path, len(add_bytes), cr, b.count(b'\n'), back.count(b'\n')))
    return len(add_bytes)

which = sys.argv[1] if len(sys.argv) > 1 else 'all'
plan = json.load(open('_r101/payload.json'))
total = 0
if which in ('all', 'r14'):
    total += commit(R14, plan['r14'].encode('utf-8'), 1081)
if which in ('all', 'lock'):
    total += commit(LOCK, plan['lock'].encode('utf-8'), 137)
if which in ('all', 'g3'):
    total += commit(G3, plan['g3'].encode('utf-8'), 337)
if which in ('all', 'sb'):
    total += commit(SB, plan['sb'].encode('utf-8'), 0)
print('TOTAL +%d B' % total)
