# -*- coding: utf-8 -*-
"""R216 p3b：§2.224 正文加长后重钉 C16_FLOORS[224] 与其 sha（p3 已跑过一次，备份已存在故另起脚本）。"""
import os,hashlib,json,re
ROOT='/home/t628/projects/ra2-campaign-forge'
G=ROOT+'/lead/next_re_20261117_r14/check_disc.py'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
b0=open(G,'rb').read(); h0=hashlib.sha256(b0).hexdigest(); s0=b0.decode('utf-8')
dst=BASE+'/check_disc.py.before_r216_c16b_20261128.bak'
assert not os.path.exists(dst); open(dst,'wb').write(b0)
print('check_disc 旧 sha=%s'%h0[:16])
RC=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
lines=open(RC,'rb').read().decode('utf-8').split('\n')
cur=None;buf=[];secs=[]
for l in lines:
    m=re.match(r'^## (2\.(\d+))\b',l)
    if m:
        if cur is not None: secs.append((cur,len('\n'.join(buf).encode('utf-8'))))
        cur=int(m.group(2)); buf=[l]
    elif cur is not None: buf.append(l)
if cur is not None: secs.append((cur,len('\n'.join(buf).encode('utf-8'))))
print('末节=%s'%(secs[-1],))
lid,lb=secs[-1]; assert lid==224
assert s0.count('    224: 8692,')==1
s1=s0.replace('    224: 8692,','    224: %d,'%lb)
m=re.search(r'C16_FLOORS = \{(.*?)\n\}',s1,re.S)
tbl={}
for ln in m.group(1).split('\n'):
    ln=ln.strip()
    if not ln: continue
    k,v=ln.split(':'); tbl[int(k)]=int(v.strip().rstrip(','))
norm='\n'.join('%d:%d'%(k,tbl[k]) for k in sorted(tbl))
sha=hashlib.sha256(norm.encode()).hexdigest()
oldsha='89193ad409e94b0d'
import re as _re
cur_sha=_re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",s1).group(1)
assert s1.count(cur_sha)==1
s2=s1.replace(cur_sha,sha)
open(G,'wb').write(s2.encode('utf-8'))
r=open(G,'rb').read()
assert sha in r.decode() and ('    224: %d,'%lb) in r.decode()
print('C16_FLOORS[224]=%d ; 节数=%d ; sha %s -> %s'%(lb,len(tbl),cur_sha[:16],sha[:16]))
json.dump({'cd_old':h0,'cd_new':hashlib.sha256(r).hexdigest(),'c16_sha_old':cur_sha,'c16_sha_new':sha,
 'sec224':lb,'sections':len(tbl)},open(ROOT+'/_r216/p3b.json','w'),indent=1)
