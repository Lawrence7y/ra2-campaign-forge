#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 p2：C16_FLOORS 钉入 §2.205/§2.206/§2.207 并重算 C16_FLOORS_SHA256。
下界 = 实测字节 // 2（与该表既有全部条目的建表规则一致）。写前 wx 备份 + 回读校验。"""
import re,hashlib,os,time,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
CD=ROOT+'/lead/next_re_20261117_r14/check_disc.py'
R14=ROOT+'/lead/next_re_20261117_r14/R14_COMMON.md'
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
s=open(R14,'rb').read().decode('utf-8')
hs=[(m.start(),m.group(0)) for m in re.finditer(r'(?m)^## .*$',s)]
sizes={}
for i,(p,h) in enumerate(hs):
    m=re.findall(r'\d+\.(\d+)',h)
    if not m: continue
    num=int(m[0]); end=hs[i+1][0] if i+1<len(hs) else len(s)
    sizes[num]=len(s[p:end].encode('utf-8'))
for n in (205,206,207):
    ck('SIZE_%d 实测字节 > 0'%n, sizes.get(n,0)>0, sizes.get(n))
src=open(CD,'rb').read().decode('utf-8')
sha_old=hashlib.sha256(src.encode('utf-8')).hexdigest()

STAMP=time.strftime('%Y%m%d_%H%M%S')
bak='%s/lead/next_re_20261117_r14/R17_LEAD_BASELINE/check_disc.py.before_r202_c16pin_%s.bak'%(ROOT,STAMP)
with open(bak,'xb') as f: f.write(open(CD,'rb').read())
ck('BAK check_disc wx 独占', os.path.exists(bak), os.path.basename(bak))
# 1) 定位表并追加三条
if all(re.search(r'\n    %d: %d,'%(n,sizes[n]//2),src) for n in (205,206,207)):
    print('ALREADY PINNED - abort'); sys.exit(0)
i=src.index('C16_FLOORS = {')
j=src.index('\n}',i)
tbl=src[i:j]
new_entries=''.join('\n    %d: %d,'%(n,sizes[n]//2) for n in (205,206,207))
tbl2=tbl+new_entries
src2=src[:i]+tbl2+src[j:]
# 2) 重算 sha
m=re.search(r'C16_FLOORS_SHA256 = \'([0-9a-f]{64})\'',src2)
ck('找到 C16_FLOORS_SHA256 常量', m is not None, m.group(1)[:16] if m else None)
ns={}
exec(compile(tbl2+'\n}','<t>','exec'),ns)
T=ns['C16_FLOORS']
norm='\n'.join('%d:%d'%(k,T[k]) for k in sorted(T))
sha_new=hashlib.sha256(norm.encode('utf-8')).hexdigest()
src3=src2[:m.start(1)]+sha_new+src2[m.end(1):]
ck('表条目 201 -> 204', len(T)==204, len(T))
ck('三条已入表', all(n in T for n in (205,206,207)), [(n,T.get(n)) for n in (205,206,207)])
ck('下界 == 实测//2', all(T[n]==sizes[n]//2 for n in (205,206,207)),
   [(n,T[n],sizes[n]) for n in (205,206,207)])
ck('新 sha != 旧 sha', sha_new!=m.group(1), sha_new[:16])
open(CD,'w').write(src3)
back=open(CD,'rb').read().decode('utf-8')
ck('回读 表含 205/206/207', all(re.search(r'\n    %d: %d,'%(n,sizes[n]//2),back) for n in (205,206,207)), '')
ck('回读 sha 常量已更新', sha_new in back, sha_new[:16])
ck('回读 旧 sha 已不在', m.group(1) not in back, '')
ck('回读 文件 CR 未变', open(CD,'rb').read().count(b'\r')==src.encode('utf-8').count(b'\r'), '')
print('   check_disc.py sha %s -> %s'%(sha_old[:16],hashlib.sha256(open(CD,'rb').read()).hexdigest()[:16]))
print('\nSUMMARY fails=%d %s'%(len(fails),fails))
if fails: sys.exit(1)
