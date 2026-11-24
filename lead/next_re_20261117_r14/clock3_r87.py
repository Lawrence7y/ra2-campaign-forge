#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R87：能不能用「产物文件自身的 mtime」当外部时钟，把「真追加一行」与「就地改 at」分开？
原理：一条声称于 at 写入的行，不可能存在于「最后一次写入早于 at」的文件里。
若 at > mtime ⇒ 该行不是在该文件里于 at 时刻写入的（要么 at 是改的，要么文件被搬动）。
先做纯测量：现有 30 行里有多少会被这条判成不一致（若大量误伤则不可用）。只读。"""
import os, io, re, datetime

ROOT='/home/t628/projects/ra2-campaign-forge'
R14=os.path.join(ROOT,'lead','next_re_20261117_r14')
TZ=datetime.timezone(datetime.timedelta(hours=8))
body=[l.split('\t') for l in io.open(os.path.join(R14,'DISC_RECHECK.tsv'),encoding='utf-8').read().split('\n')[1:] if l.strip()]
LN=re.compile(r'^DISC_RECHECK discipline=(\d+) round=(R\d{2,3}) at=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}) anchors=(sha256:[0-9a-f]{64}) conclusion=(\S+)$')

print('%-4s %-26s %-21s %-21s %s'%('id','product','at','mtime','mtime>=at?'))
rows=[]
for r in body:
    prod=os.path.join(ROOT,r[4].strip().replace('\\',os.sep).replace('/',os.sep))
    if not os.path.isfile(prod): print('%-4s %-26s FILE MISSING'%(r[0],os.path.basename(prod))); continue
    txt=io.open(prod,encoding='utf-8',errors='replace').read()
    hits=[m for m in (LN.match(l) for l in txt.splitlines() if l.startswith('DISC_RECHECK '))
          if m and int(m.group(1))==int(r[0])]
    if not hits:
        print('%-4s %-26s (无本纪律自述行)'%(r[0],os.path.basename(prod))); continue
    m=hits[0]
    at=datetime.datetime.strptime(m.group(3),'%Y-%m-%dT%H:%M:%S%z')
    mt=datetime.datetime.fromtimestamp(os.path.getmtime(prod),TZ)
    ok = mt>=at
    rows.append((r[0],ok,mt-at))
    print('%-4s %-26s %-21s %-21s %s'%(r[0],os.path.basename(prod)[:26],
          at.strftime('%H:%M:%S'),mt.strftime('%H:%M:%S.%f')[:12],
          'OK' if ok else '** mtime早于at (差 %s)'%(at-mt)))
print()
print('自述行总数 %d；mtime>=at 成立 %d；不成立 %d'%(len(rows),sum(1 for _,o,_ in rows if o),
      sum(1 for _,o,_ in rows if not o)))
print()
print('⇒ 若「不成立」为 0，则这条断言可在不误伤现状的前提下加入门禁（纯增益）。')
