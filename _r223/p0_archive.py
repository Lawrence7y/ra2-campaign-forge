# -*- coding: utf-8 -*-
"""R223 p0：STATUS_BOARD 272 行 >= 260，归档最早 2 段到 BOARD_ARCHIVE（ARCH CR 保持 2952，BOARD CR 保持 0）。"""
import os, hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/R17_LEAD_BASELINE'
BOARD=TIER+'/STATUS_BOARD.md'; ARCH=TIER+'/BOARD_ARCHIVE.md'
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r223_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b,dst
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b,dst
    raise SystemExit('bak exhausted')
bb=open(BOARD,'rb').read(); ab=open(ARCH,'rb').read()
ck('A1 BOARD CR=0', bb.count(b'\r')==0, bb.count(b'\r'))
ck('A2 ARCH CR=2952', ab.count(b'\r')==2952, ab.count(b'\r'))
nl=bb.count(b'\n')
ck('A3 BOARD 272 行 >= 260 触发归档', nl==272, nl)
s=bb.decode('utf-8')
lines=s.split('\n')
ck('A4 末行为空', lines[-1]=='')
# 段边界：以 '## ' 开头
idx=[i for i,l in enumerate(lines) if l.startswith('## ')]
ck('A5 至少 3 个段', len(idx)>=3, len(idx))
cut=idx[2]
head=lines[:cut]; tail=lines[cut:]
ck('A6 归档段数=2 且首段为 206 轮', '第 206 轮' in head[0], head[0][:40])
ck('A7 剩余首段为 208 轮', '第 208 轮' in tail[0], tail[0][:40])
arch_add='\n'+'\n'.join(head).rstrip('\n')+'\n'
ck('A8 归档追加段无 CR', '\r' not in arch_add)
new_board='\n'.join(tail)
nb=new_board.encode('utf-8')
ck('A9 新 BOARD CR=0', nb.count(b'\r')==0)
ck('A10 新 BOARD 行数 < 260', nb.count(b'\n')<260, nb.count(b'\n'))
na=(ab.decode('utf-8')+arch_add).encode('utf-8')
ck('A11 新 ARCH CR 仍 2952', na.count(b'\r')==2952, na.count(b'\r'))
ck('A12 新 ARCH 净增 == 追加段长度', len(na)-len(ab)==len(arch_add.encode()), (len(ab),len(na)))
if fails:
    print('[ABORT]',fails); raise SystemExit(1)
b1,d1=bak(BOARD,'BOARDARCH'); b2,d2=bak(ARCH,'ARCHADD')
ck('A13 两份备份独占创建', os.path.exists(d1) and os.path.exists(d2), (d1,d2))
open(ARCH,'wb').write(na); open(BOARD,'wb').write(nb)
ck('A14 ARCH 回读一致', open(ARCH,'rb').read()==na)
ck('A15 BOARD 回读一致', open(BOARD,'rb').read()==nb)
print('[OK] BOARD %d -> %d 行 ; ARCH %d -> %d B (CR %d)'%(nl, nb.count(b'\n'), len(ab), len(na), na.count(b'\r')))
