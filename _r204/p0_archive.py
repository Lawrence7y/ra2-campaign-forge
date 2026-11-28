#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 p0：STATUS_BOARD 295 行 >= 260，归档最早 2 段到 BOARD_ARCHIVE。
纪律：wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验。
不变式：BOARD_ARCHIVE CR 保持 2952；STATUS_BOARD CR 保持 0。
"""
import hashlib, os, time
ROOT='/home/t628/projects/ra2-campaign-forge'
D=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/R17_LEAD_BASELINE'
os.makedirs(BASE, exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
STAMP=time.strftime('%Y%m%d_%H%M%S')
BRD=D+'/STATUS_BOARD.md'; ARC=D+'/BOARD_ARCHIVE.md'
b=open(BRD,'rb').read(); a=open(ARC,'rb').read()
b0s, a0s = sha(b), sha(a)
assert b.count(b'\r')==0, ('board CR', b.count(b'\r'))
assert a.count(b'\r')==2952, ('arc CR', a.count(b'\r'))
lb=b.count(b'\n'); la=a.count(b'\n')
print('BEFORE board LF=%d CR=%d sha=%s | archive LF=%d CR=%d sha=%s' % (lb,b.count(b'\r'),b0s[:12],la,a.count(b'\r'),a0s[:12]))
lines=b.decode('utf-8').split('\n')
# 找前 3 个段起点，切掉前 2 段
starts=[i for i,l in enumerate(lines) if l.startswith('## ')]
assert len(starts)>=3, starts
cut=starts[2]
moved=lines[:cut]
keep=lines[cut:]
assert len(moved)==cut and cut>0
# 备份两份（wx 独占）
for p,old in ((BRD,b),(ARC,a)):
    bak='%s/%s.%s.bak'%(BASE,os.path.basename(p),STAMP)
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,old); os.close(fd)
    assert sha(open(bak,'rb').read())==sha(old)
# 写入：归档段追加到 ARCHIVE 末尾（原文不改），BOARD 只留第 3 段起
moved_txt='\n'.join(moved)
if not a.endswith(b'\n'): moved_txt='\n'+moved_txt
new_a=a+moved_txt.encode('utf-8')
if not new_a.endswith(b'\n'): new_a+=b'\n'
new_b='\n'.join(keep).encode('utf-8')
open(ARC,'wb').write(new_a)
open(BRD,'wb').write(new_b)
rb=open(BRD,'rb').read(); ra=open(ARC,'rb').read()
assert rb.count(b'\r')==0, rb.count(b'\r')
assert ra.count(b'\r')==2952, ra.count(b'\r')
assert rb.count(b'\n')==lb-cut, (rb.count(b'\n'), lb-cut)
assert ra.startswith(a), 'archive must preserve original bytes as prefix'
assert len(moved_txt.encode('utf-8'))>0
print('AFTER  board LF=%d CR=%d | archive LF=%d CR=%d' % (rb.count(b'\n'),rb.count(b'\r'),ra.count(b'\n'),ra.count(b'\r')))
print('moved lines=%d, board first line=%r' % (cut, keep[0][:60]))
print('OK')
