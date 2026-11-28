# -*- coding: utf-8 -*-
import sys,hashlib
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r211')
import wr
B='STATUS_BOARD.md'; A='BOARD_ARCHIVE.md'
bsha='4d26900a17441dcb3ae6cf9ef67ffd57ec7dbb59ee474cdf855b8d21e7313c02'
asha='18e1e6836848935b35345a0e367dace29cb946c05fbaff0375328e3d835132e1'
bp='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/'+B
b=open(bp,'rb').read()
assert hashlib.sha256(b).hexdigest()==bsha
lines=b.split(b'\n')
# find section starts
idx=[i for i,l in enumerate(lines) if l.startswith(b'## ')]
print('section starts (0-based) =',idx[:5],'total',len(idx))
cut=idx[2]                      # 第三段起点
moved=b'\n'.join(lines[:cut])   # 前两段（含尾部空行）
rest=b'\n'.join(lines[cut:])
assert len(lines[:cut])+len(lines[cut:])==len(lines)
print('moved lines=%d rest lines=%d'%(cut,len(lines)-cut))
# archive: append moved (ensure blank line separator)
ap='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/'+A
a=open(ap,'rb').read()
assert hashlib.sha256(a).hexdigest()==asha
sepa=b'\n'
add=moved.rstrip(b'\n')
newa=a.rstrip(b'\n')+b'\n\n'+add+b'\n'
wr.write(A,'arch',lambda _:newa,asha,2952)
wr.write(B,'arch',lambda _:rest,bsha,0)
# verify
a2=open(ap,'rb').read(); b2=open(bp,'rb').read()
print('ARCH CR=%d (expect 2952) LF=%d'%(a2.count(b'\r'),a2.count(b'\n')))
print('BOARD CR=%d LF=%d (expect 0 / %d)'%(b2.count(b'\r'),b2.count(b'\n'),len(lines)-cut))
assert a2.count(b'\r')==2952 and b2.count(b'\r')==0
assert b2==rest
print('OK archive done')
