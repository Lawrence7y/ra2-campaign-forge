# -*- coding: utf-8 -*-
"""R209 p6（重做）：C16_FLOORS 纳入 §2.217 并重钉 sha。不 import check_disc（避免执行副作用），纯文本解析。
"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
CD=TIER+'/check_disc.py'
t=open(CD,'rb').read().decode('utf-8')
m=re.search(r'^C16_FLOORS = \{\n(.*?)\n\}\n',t,re.S|re.M)
assert m
body=m.group(1)
F={int(k):int(v) for k,v in re.findall(r'^    (\d+): (\d+),$',body,re.M)}
print('现有节数=%d 最大 id=%d'%(len(F),max(F)))
assert max(F)==216 and 217 not in F
R14=open(TIER+'/R14_COMMON.md','rb').read().decode('utf-8')
i=R14.find('## 2.217 ·'); assert i>=0
j=R14.find('\n## ',i+10)
sec=R14[i:(j+1 if j>0 else len(R14))]
b=len(sec.encode('utf-8'))
floor=int(b*0.5)
print('§2.217 实测 %d B -> floor %d'%(b,floor))
F[217]=floor
lines='\n'.join('    %d: %d,'%(k,F[k]) for k in sorted(F))
norm='\n'.join('%d:%d'%(k,F[k]) for k in sorted(F))
sha=hashlib.sha256(norm.encode()).hexdigest()
print('新 sha =',sha)
raw=open(CD,'rb').read()
bak=BASE+'/check_disc.py.before_r209_c16_20261128.bak'
if not os.path.exists(bak):
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
assert open(bak,'rb').read()==raw
new_body=lines
t2=t[:m.start(1)]+new_body+t[m.end(1):]
oldsha=re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'",t2,re.M).group(1)
assert oldsha!=sha
t2=t2.replace(oldsha,sha)
nb=t2.encode('utf-8')
tmp=CD+'.r209tmp'; open(tmp,'wb').write(nb); os.replace(tmp,CD)
assert open(CD,'rb').read()==nb
# 回读校验：表项数与 sha 自洽
t3=open(CD,'rb').read().decode('utf-8')
b3=re.search(r'^C16_FLOORS = \{\n(.*?)\n\}\n',t3,re.S|re.M).group(1)
F3={int(k):int(v) for k,v in re.findall(r'^    (\d+): (\d+),$',b3,re.M)}
n3='\n'.join('%d:%d'%(k,F3[k]) for k in sorted(F3))
sha3=hashlib.sha256(n3.encode()).hexdigest()
s3=re.search(r"^C16_FLOORS_SHA256 = '([0-9a-f]{64})'",t3,re.M).group(1)
assert len(F3)==209 and max(F3)==217 and sha3==s3
print('OK check_disc.py %d -> %d B ; 209 节 / max 217 / sha 自洽 %s'%(len(raw),len(nb),sha3[:16]))
