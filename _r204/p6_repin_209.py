#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 p6：C16_FLOORS 209 重钉（2.209 从 10626 增到 12819），并重算 C16_FLOORS_SHA256。
floor = 12819 // 2 = 6409。
"""
import hashlib, os, re, time
P='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/check_disc.py'
BASE='/home/t628/projects/ra2-campaign-forge/R17_LEAD_BASELINE'
src=open(P,'rb').read(); old_sha=hashlib.sha256(src).hexdigest()
b=src.decode('utf-8')
OLD="""    208: 3885,
    209: 5313,
}"""
NEW="""    208: 3885,
    209: 6409,
}"""
assert b.count(OLD)==1
m=re.search(r'C16_FLOORS = \{(.*?)\n\}',b,re.S)
floors={}
for line in m.group(1).split('\n'):
    line=line.strip()
    if not line or line.startswith('#'): continue
    k,v=line.rstrip(',').split(':'); floors[int(k)]=int(v)
assert floors[209]==5313
b2=b.replace(OLD,NEW)
m2=re.search(r'C16_FLOORS = \{(.*?)\n\}',b2,re.S)
f2={}
for line in m2.group(1).split('\n'):
    line=line.strip()
    if not line or line.startswith('#'): continue
    k,v=line.rstrip(',').split(':'); f2[int(k)]=int(v)
norm='\n'.join('%d:%d'%(k,f2[k]) for k in sorted(f2))
newsha=hashlib.sha256(norm.encode()).hexdigest()
olds=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",b2).group(1)
assert b2.count(olds)==1
b2=b2.replace(olds,newsha)
assert f2[209]==6409 and len(f2)==len(floors)==201
STAMP=time.strftime('%Y%m%d_%H%M%S')
bak='%s/check_disc.py.%s.bak'%(BASE,STAMP)
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,src); os.close(fd)
assert hashlib.sha256(open(bak,'rb').read()).hexdigest()==old_sha
open(P,'wb').write(b2.encode('utf-8'))
rb=open(P,'rb').read()
assert hashlib.sha256(rb)!=old_sha
print('209 pin 5313 -> 6409 ; C16 sha %s -> %s ; floors=%d' % (olds[:16], newsha[:16], len(f2)))
print('OK')
