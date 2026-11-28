# -*- coding: utf-8 -*-
"""R218 p7：把 R14_COMMON 新增节 225（R217）与 226（R218）钉进 check_disc.C16_FLOORS，并重钉 C16_FLOORS_SHA256。
理由：C16 实测 unpinned 2 == C16_UNPINNED_MAX，已到上限；下轮再新增一节即 FAIL。
"""
import os,hashlib,re
ROOT='/home/t628/projects/ra2-campaign-forge'
G=ROOT+'/lead/next_re_20261117_r14/check_disc.py'
RC=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
txt=open(RC,'rb').read().decode('utf-8')
secs=[];cur=None;buf=[]
for l in txt.split('\n'):
    m=re.match(r'^## (2\.(\d+))\b',l)
    if m:
        if cur is not None: secs.append((cur,len('\n'.join(buf).encode('utf-8'))))
        cur=int(m.group(2)); buf=[l]
    elif cur is not None: buf.append(l)
if cur is not None: secs.append((cur,len('\n'.join(buf).encode('utf-8'))))
d=dict(secs)
print('[实测] 节数=%d 末两节=%s'%(len(secs),secs[-2:]))
assert secs[-1][0]==226 and 225 in d
b0=open(G,'rb').read(); s0=b0.decode(); h0=hashlib.sha256(b0).hexdigest()
m=re.search(r'C16_FLOORS = \{(.*?)\n\}',s0,re.S)
tbl={}
for ln in m.group(1).split('\n'):
    ln=ln.strip()
    if not ln: continue
    k,v=ln.split(':'); tbl[int(k)]=int(v.strip().rstrip(','))
print('[前态] 已钉=%d 最大 id=%d 225in=%s 226in=%s'%(len(tbl),max(tbl),225 in tbl,226 in tbl))
assert 225 not in tbl and 226 not in tbl
anchor='    %d: %d,\n}'%(max(tbl),tbl[max(tbl)])
assert s0.count(anchor)==1, s0.count(anchor)
s1=s0.replace(anchor,'    %d: %d,\n    %d: %d,\n    %d: %d,\n}'%(max(tbl),tbl[max(tbl)],225,d[225],226,d[226]))
m2=re.search(r'C16_FLOORS = \{(.*?)\n\}',s1,re.S)
t2={}
for ln in m2.group(1).split('\n'):
    ln=ln.strip()
    if not ln: continue
    k,v=ln.split(':'); t2[int(k)]=int(v.strip().rstrip(','))
assert t2[225]==d[225] and t2[226]==d[226] and len(t2)==len(tbl)+2
sha=hashlib.sha256('\n'.join('%d:%d'%(k,t2[k]) for k in sorted(t2)).encode()).hexdigest()
oldsha='e2840adea33d01da5cc97aa1b2c5a2c395adbda56c58aa522d2b53085be4d95c'
assert s1.count(oldsha)==1
s2=s1.replace(oldsha,sha)
open(G,'wb').write(s2.encode('utf-8'))
r=open(G,'rb').read()
assert sha in r.decode()
print('[写入] C16_FLOORS %d -> %d 节；新增 225:%d / 226:%d'%(len(tbl),len(t2),d[225],d[226]))
print('        SHA256 %s -> %s'%(oldsha[:16],sha[:16]))
print('        check_disc bytes %d -> %d sha %s -> %s'%(len(b0),len(r),h0[:16],hashlib.sha256(r).hexdigest()[:16]))
