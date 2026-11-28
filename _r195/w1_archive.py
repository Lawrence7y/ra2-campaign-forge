#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R195 归档：把 STATUS_BOARD.md 最早的 R184、R185 两段搬到 BOARD_ARCHIVE.md 末尾。
纪律：断言旧 sha/CR -> 一次性写 -> 回读校验。
BOARD_ARCHIVE CR 必须保持 2952；STATUS_BOARD CR 必须保持 0。
"""
import hashlib,os
ROOT='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
SB=os.path.join(ROOT,'STATUS_BOARD.md'); AR=os.path.join(ROOT,'BOARD_ARCHIVE.md')
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
sb=open(SB,'rb').read(); ar=open(AR,'rb').read()
ck('A1 旧 STATUS_BOARD = 59,375 B / CR 0 / 277 行 / sha 14511b7d',
   len(sb)==59375 and sb.count(b'\r')==0 and sb.count(b'\n')==277 and hashlib.sha256(sb).hexdigest().startswith('14511b7d'),
   (len(sb),sb.count(b'\r'),sb.count(b'\n')))
ck('A2 旧 BOARD_ARCHIVE = 1,419,491 B / CR 2952 / sha 32b9ae7f',
   len(ar)==1419491 and ar.count(b'\r')==2952 and hashlib.sha256(ar).hexdigest().startswith('32b9ae7f'),
   (len(ar),ar.count(b'\r')))
L=sb.decode('utf-8').split('\n')
ck('A3 文件末行为非空（无尾随换行）', L[-1]!='', repr(L[-1][:20]))
# 段边界：第 1 行是 R184 标题；R186 标题在第 54 行（index 53）
idx=[i for i,l in enumerate(L) if l.startswith('## 🟢 R17 第 18') or l.startswith('## 🟢 R17 第 19')]
ck('A4 段标题共 11 个（R184..R194）', len(idx)==11, len(idx))
cut=idx[2]           # R186 起点
seg=L[:cut]; rest=L[cut:]
ck('A5 搬走段含 R184 与 R185 两个标题', seg[0].startswith('## 🟢 R17 第 184') and any(x.startswith('## 🟢 R17 第 185') for x in seg), (seg[0][:40],cut))
ck('A6 剩余段首行是 R186', rest[0].startswith('## 🟢 R17 第 186'), rest[0][:40])
ck('A7 搬走行数 53', len(seg)==53, len(seg))
ck('A8 剩余分片数 225 / 将成 224 条换行', len(rest)==225, len(rest))
# BOARD_ARCHIVE 追加：保持原有 CR 数不变（原文全 CRLF？先探明）
ar_txt=ar.decode('utf-8')
ck('A9 归档末行非空（追加需先补换行）或空', True, repr(ar_txt[-3:]))
seg_txt='\n'.join(seg)+'\n'          # 53 条 + 其后的换行
ck('A9b 归档以换行结尾（可直接追加）', ar_txt.endswith('\n'), repr(ar_txt[-2:]))
new_ar=(ar_txt+seg_txt).encode('utf-8')
new_sb=('\n'.join(rest)).encode('utf-8')
ck('A9c 切分无损：seg_txt + new_sb == 旧看板', (seg_txt+new_sb.decode('utf-8'))==sb.decode('utf-8'), True)
ck('A10 新归档 CR 保持 2952', new_ar.count(b'\r')==2952, new_ar.count(b'\r'))
ck('A11 新看板 CR 保持 0', new_sb.count(b'\r')==0, new_sb.count(b'\r'))
ck('A12 新看板换行 224 / 行数 225 <= 300', new_sb.count(b'\n')==224 and new_sb.count(b'\n')+1<=300, new_sb.count(b'\n'))
ck('A13 归档精确追加：new_ar == 旧归档 + 搬迁段', new_ar==ar+seg_txt.encode('utf-8'),
   (len(ar),len(new_ar)))
if fails:
    print('ABORT: %d FAIL，不写盘'%len(fails)); raise SystemExit(1)
open(AR,'wb').write(new_ar)
open(SB,'wb').write(new_sb)
# 回读
r_ar=open(AR,'rb').read(); r_sb=open(SB,'rb').read()
ck('A14 回读归档一致', r_ar==new_ar, (len(r_ar),r_ar.count(b'\r')))
ck('A15 回读看板一致', r_sb==new_sb, (len(r_sb),r_sb.count(b'\n')))
print('ARCHIVE  %d -> %d B (CR %d), SB %d -> %d B (CR %d, %d 行)'%(
  len(ar),len(new_ar),new_ar.count(b'\r'),len(sb),len(new_sb),new_sb.count(b'\r'),new_sb.count(b'\n')))
print('FAILS=%d'%len(fails))
