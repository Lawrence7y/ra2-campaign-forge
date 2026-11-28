# -*- coding: utf-8 -*-
"""R221 p5：把 R14_COMMON 新增节 229 钉进 C16_FLOORS 并重钉 C16_FLOORS_SHA256。
正控：重算旧表 sha 必须等于现钉值 30effae0…"""
import os, hashlib, re
ROOT='/home/t628/projects/ra2-campaign-forge'; BASE=ROOT+'/R17_LEAD_BASELINE'
G=ROOT+'/lead/next_re_20261117_r14/check_disc.py'
RC=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
def bak(path,tag):
    b=open(path,'rb').read()
    base='%s/%s.before_r221_%s'%(BASE,os.path.basename(path),tag)
    for i in range(10):
        dst=base+(('_%d'%i) if i else '')+'_20261128.bak'
        if os.path.exists(dst):
            if open(dst,'rb').read()==b: return b
            continue
        fd=os.open(dst,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
        with os.fdopen(fd,'wb') as f: f.write(b)
        return b
    raise SystemExit('bak exhausted')
txt=open(RC,'rb').read().decode('utf-8')
secs=[];cur=None;buf=[]
for l in txt.split('\n'):
    m=re.match(r'^## (2\.(\d+))\b',l)
    if m:
        if cur is not None: secs.append((cur,len('\n'.join(buf).encode('utf-8'))))
        cur=int(m.group(2)); buf=[l]
    elif cur is not None: buf.append(l)
if cur is not None: secs.append((cur,len('\n'.join(buf).encode('utf-8'))))
d=dict(secs); print('[实测] R14 节数=%d 末三节=%s'%(len(secs),secs[-3:]))
assert secs[-1][0]==229, secs[-1]
b0=bak(G,'DISC'); s0=b0.decode(); h0=hashlib.sha256(b0).hexdigest()
m=re.search(r'C16_FLOORS = \{(.*?)\n\}',s0,re.S); tbl={}
for ln in m.group(1).split('\n'):
    ln=ln.strip()
    if not ln: continue
    k,v=ln.split(':'); tbl[int(k)]=int(v.strip().rstrip(','))
print('[前态] 已钉=%d 最大 id=%d 229in=%s'%(len(tbl),max(tbl),229 in tbl))
assert 229 not in tbl
oldsha=hashlib.sha256('\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl)).encode()).hexdigest()
pinned=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",s0).group(1)
print('[正控] 旧表重算=%s 现钉=%s 一致=%s'%(oldsha[:16],pinned[:16],oldsha==pinned))
assert oldsha==pinned
anchor='    %d: %d,\n}'%(max(tbl),tbl[max(tbl)])
assert s0.count(anchor)==1
s1=s0.replace(anchor,'    %d: %d,\n    %d: %d,\n}'%(max(tbl),tbl[max(tbl)],229,d[229]))
m2=re.search(r'C16_FLOORS = \{(.*?)\n\}',s1,re.S); t2={}
for ln in m2.group(1).split('\n'):
    ln=ln.strip()
    if not ln: continue
    k,v=ln.split(':'); t2[int(k)]=int(v.strip().rstrip(','))
assert len(t2)==len(tbl)+1 and t2[229]==d[229]
sha=hashlib.sha256('\n'.join('%d:%d'%(k,t2[k]) for k in sorted(t2)).encode()).hexdigest()
assert s1.count(pinned)==1
s2=s1.replace(pinned,sha)
open(G,'wb').write(s2.encode('utf-8'))
r=open(G,'rb').read(); assert sha in r.decode()
print('[写入] C16_FLOORS %d -> %d 节，新增 229:%d'%(len(tbl),len(t2),d[229]))
print('        SHA256 %s -> %s'%(oldsha[:16],sha[:16]))
print('        check_disc %d -> %d B sha %s -> %s'%(len(b0),len(r),h0[:16],hashlib.sha256(r).hexdigest()[:16]))
