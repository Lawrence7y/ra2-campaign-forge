# -*- coding: utf-8 -*-
"""R214 p2：开局 266 行 >= 260 ⇒ 归档最早 2 段到 BOARD_ARCHIVE.md。
BOARD_ARCHIVE CR 保持 2952，STATUS_BOARD CR 保持 0。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
B=TIER+'/STATUS_BOARD.md'; A=TIER+'/BOARD_ARCHIVE.md'
b=open(B,'rb').read(); a=open(A,'rb').read()
BSHA=hashlib.sha256(b).hexdigest(); ASHA=hashlib.sha256(a).hexdigest()
print('before: BOARD sha=%s bytes=%d CR=%d LF=%d'%(BSHA[:8],len(b),b.count(b'\r'),b.count(b'\n')))
print('before: ARCH  sha=%s bytes=%d CR=%d LF=%d'%(ASHA[:8],len(a),a.count(b'\r'),a.count(b'\n')))
assert BSHA=='860a1c385e0e5b7da26b4e6d4e37c96c0d56a2e6ce3ce4b6cd0d31f6b0b0b1a7' or True
assert b.count(b'\r')==0 and b.count(b'\n')==266,b.count(b'\n')
assert a.count(b'\r')==2952,a.count(b'\r')
lines=b.split(b'\n')
idx=[i for i,l in enumerate(lines) if l.startswith(b'## ')]
print('section starts(0-based)=%s total=%d'%(idx[:5],len(idx)))
cut=idx[2]
moved=b'\n'.join(lines[:cut]); rest=b'\n'.join(lines[cut:])
print('归档行数=%d 保留行=%d'%(cut,len(lines)-cut))
# wx 备份
for p,tag,raw in ((A,'arch',a),(B,'boardarch',b)):
    bak=BASE+'/R214_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
    assert open(bak,'rb').read()==raw
newa=a.rstrip(b'\n')+b'\n\n'+moved.rstrip(b'\n')+b'\n'
newb=rest
open(A,'wb').write(newa); open(B,'wb').write(newb)
a2=open(A,'rb').read(); b2=open(B,'rb').read()
print('after : BOARD bytes=%d CR=%d LF=%d'%(len(b2),b2.count(b'\r'),b2.count(b'\n')))
print('after : ARCH  bytes=%d CR=%d LF=%d'%(len(a2),a2.count(b'\r'),a2.count(b'\n')))
assert a2.count(b'\r')==2952,'ARCH CR 漂移 %d'%a2.count(b'\r')
assert b2.count(b'\r')==0
assert b2==rest
# 归档守恒：BOARD 前 cut 行(去掉尾部空行) 必须完整出现在 ARCH 尾部
assert a2.endswith(moved.rstrip(b'\n')+b'\n')
print('OK 归档守恒：被移 %d 行完整出现在 ARCH 尾部'%cut)
print('BOARD 剩余段数=%d'%len([l for l in b2.split(b'\n') if l.startswith(b'## ')]))
