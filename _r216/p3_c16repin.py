# -*- coding: utf-8 -*-
"""R216 p3：把 R14_COMMON 新节 224 钉进 check_disc.C16_FLOORS（值取实测字节数），并重钉 C16_FLOORS_SHA256。
注意：本脚本必须在 R14_COMMON 追加 §2.224 之后运行（先写节，后钉）。"""
import os,hashlib,json
ROOT='/home/t628/projects/ra2-campaign-forge'
G=ROOT+'/lead/next_re_20261117_r14/check_disc.py'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
b0=open(G,'rb').read(); h0=hashlib.sha256(b0).hexdigest(); s0=b0.decode('utf-8')
dst=BASE+'/check_disc.py.before_r216_c16_20261128.bak'
assert not os.path.exists(dst); open(dst,'wb').write(b0)
print('check_disc 旧 sha=%s bytes=%d'%(h0[:16],len(b0)))
# 实测 R14_COMMON 末节字节
RC=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
txt=open(RC,'rb').read().decode('utf-8')
lines=txt.split('\n')
import re
secs=[];cur=None;buf=[]
for l in lines:
    m=re.match(r'^## (2\.(\d+))\b',l)
    if m:
        if cur is not None: secs.append((cur,len('\n'.join(buf).encode('utf-8'))))
        cur=int(m.group(2)); buf=[l]
    elif cur is not None: buf.append(l)
if cur is not None: secs.append((cur,len('\n'.join(buf).encode('utf-8'))))
print('R14_COMMON 节数=%d 末节=%s'%(len(secs),secs[-1]))
last_id,last_b=secs[-1]
assert last_id==224, '末节不是 224（先写 §2.224 再跑本脚本）'
assert s0.count('    223: 6631,\n}')==1
s1=s0.replace('    223: 6631,\n}','    223: 6631,\n    %d: %d,\n}'%(last_id,last_b))
assert s1!=s0
# 重算 sha
m=re.search(r'C16_FLOORS = \{(.*?)\n\}',s1,re.S)
tbl={}
for ln in m.group(1).split('\n'):
    ln=ln.strip()
    if not ln: continue
    k,v=ln.split(':'); tbl[int(k)]=int(v.strip().rstrip(','))
norm='\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl))
sha=hashlib.sha256(norm.encode()).hexdigest()
old='d1d2aa6ed3f09a2496709de7a9f9f14b413b5df7eb06a2a33eda635159b76b26'
assert s1.count(old)==1, s1.count(old)
s2=s1.replace(old,sha)
open(G,'wb').write(s2.encode('utf-8'))
r=open(G,'rb').read()
assert sha in r.decode(); assert ('    %d: %d,'%(last_id,last_b)) in r.decode()
print('C16_FLOORS 新增 %d:%d ; 节数=%d ; 新 sha=%s'%(last_id,last_b,len(tbl),sha[:16]))
print('check_disc 新 sha=%s bytes=%d'%(hashlib.sha256(r).hexdigest()[:16],len(r)))
json.dump({'cd_old':h0,'cd_new':hashlib.sha256(r).hexdigest(),'c16_sha':sha,
 'c16_sections':len(tbl),'new_sec':[last_id,last_b]},open(ROOT+'/_r216/p3.json','w'),indent=1)
