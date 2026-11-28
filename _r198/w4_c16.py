#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 把 §2.203（8,796 B ⇒ floor 4,398）钉进 check_disc 的 C16_FLOORS（202 -> 203），重算 sha256。
fail-closed + wx 独占备份 + 回读校验。
"""
import os,re,sys,time,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
T=os.path.join(ROOT,'lead/next_re_20261117_r14')
CD=os.path.join(T,'check_disc.py')
BL=os.path.join(T,'R17_LEAD_BASELINE')
SEC=int(open('/tmp/r198_sec203_len').read())
print('§2.203 =',SEC,'B -> floor',SEC//2)
fails=[];n=0
def ck(nm,c,d=''):
    global n;n+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def sha(b): return hashlib.sha256(b).hexdigest()
raw=open(CD,'rb').read()
ck('C0a 旧 check_disc sha', True, sha(raw)[:16])
src=raw.decode('utf-8')
m=re.search(r"C16_FLOORS = \{(.*?)\n\}", src, re.S)
body=m.group(1)
ids=[int(x) for x in re.findall(r'^\s*(\d+):',body,re.M)]
ck('C1a 现盘 194 条且末条 202', (len(ids),ids[-1])==(194,202), (len(ids),ids[-1]))
ck('C1b 无 203', 203 not in ids, 203 in ids)
ck('C1c 202 floor == 4333', re.search(r'^\s*202: (\d+),',body,re.M).group(1)=='4333',
   re.search(r'^\s*202: (\d+),',body,re.M).group(1))
FL = SEC//2
newbody = body.rstrip('\n') + '\n    203: %d,\n' % FL
ns = src[:m.start(1)] + newbody + src[m.end(1):]
# 重算 sha
def c16_norm(txt):
    mm=re.search(r"C16_FLOORS = \{(.*?)\n\}",txt,re.S).group(1)
    d={}
    for line in mm.split('\n'):
        mm2=re.match(r'\s*(\d+):\s*(\d+),',line)
        if mm2: d[int(mm2.group(1))]=int(mm2.group(2))
    return '\n'.join('%d:%d'%(k,d[k]) for k in sorted(d)), len(d)
norm,cnt = c16_norm(ns)
NEWSHA=hashlib.sha256(norm.encode()).hexdigest()
old=re.search(r"^C16_FLOORS_SHA256 = '(\w+)'",ns,re.M)
ck('C2a 找到旧 sha 定义', old is not None)
ns2 = ns[:old.start()] + "C16_FLOORS_SHA256 = '%s'"%NEWSHA + ns[old.end():]
norm2,cnt2 = c16_norm(ns2)
ck('C2b 新表 195 条且末条 203', (cnt2,203 in [int(x) for x in re.findall(r'^\s*(\d+):',re.search(r"C16_FLOORS = \{(.*?)\n\}",ns2,re.S).group(1),re.M)])==(195,True),cnt2)
ck('C2c 新 sha 回算自洽', hashlib.sha256(norm2.encode()).hexdigest()==NEWSHA)
ck('C2d 旧 sha 已不在文件', old.group(1) not in ns2)
ck('C3a 反控：203 floor +1 ⇒ sha 变',
   hashlib.sha256(norm2.replace('203:%d'%FL,'203:%d'%(FL+1)).encode()).hexdigest()!=NEWSHA)
ck('C3b CR 保持 0', ns2.count('\r')==0, ns2.count('\r'))
if fails:
    print('ABORT: %s'%fails); sys.exit(1)
stamp=time.strftime('%Y%m%d_%H%M%S')
bak=os.path.join(BL,'check_disc.before_r198_c16_%s.bak'%stamp)
fd=os.open(bak,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
with os.fdopen(fd,'wb') as f: f.write(raw)
ck('W1 备份 sha 一致', sha(open(bak,'rb').read())==sha(raw))
assert open(CD,'rb').read()==raw
open(CD,'wb').write(ns2.encode('utf-8'))
ck('W2 回读一致', sha(open(CD,'rb').read())==sha(ns2.encode('utf-8')))
print('C16_FLOORS 194 -> 195，钉 203: %d；sha 0edaca3d… -> %s…'%(FL,NEWSHA[:16]))
print('FAILS=%d'%len(fails))
