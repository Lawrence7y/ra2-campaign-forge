# -*- coding: utf-8 -*-
"""R212 p6：gate_runner.LEDGER 重钉 V595 + C16_FLOORS 纳入 §2.220。各含 wx 备份与断言。"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
# --- 1) gate_runner LEDGER ---
GR=ROOT+'/_r161/gate_runner.py'
b=open(GR,'rb').read()
fd=os.open(BASE+'/gate_runner.py.before_r212_ledger595_20261128.bak',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644)
os.write(fd,b); os.close(fd); assert open(BASE+'/gate_runner.py.before_r212_ledger595_20261128.bak','rb').read()==b
t=b.decode('utf-8')
old="'R17_R131_FACTINDEX_V593'"
assert t.count(old)==1,t.count(old)
t=t.replace(old,"'R17_R131_FACTINDEX_V595'")
open(GR,'wb').write(t.encode('utf-8')); assert open(GR,'rb').read()==t.encode('utf-8')
print('gate_runner LEDGER -> V595')
# --- 2) C16_FLOORS 纳入 §2.220 ---
CD=TIER+'/check_disc.py'
src=open(TIER+'/R14_COMMON.md','r',encoding='utf-8').read()
m=re.search(r"^## 2\.220 .*?(?=^## 2\.|\Z)",src,re.S|re.M)
assert m,'§2.220 not found'
n=len(m.group(0).encode('utf-8')); lo=int(n*0.75)
print('§2.220 bytes=%d floor=%d'%(n,lo))
ts=open(CD,'r',encoding='utf-8').read()
cb=open(CD,'rb').read()
bak=BASE+'/check_disc.py.before_r212_c16_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,cb); os.close(fd)
assert open(bak,'rb').read()==cb
blk=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',ts,re.S).group(0)
pairs=re.findall(r'^    (\d+): (\d+),$',blk,re.M)
print('pins before:',len(pairs),'last:',pairs[-1])
assert not any(k=='220' for k,v in pairs)
nb=ts.replace(blk, blk.replace('\n}', '\n    220: %d,\n}'%lo))
assert nb!=ts
blk2=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',nb,re.S).group(1)
pairs2=re.findall(r'^    (\d+): (\d+),$',blk2,re.M)
norm='\n'.join('%s:%s'%p for p in pairs2)
sha=hashlib.sha256(norm.encode()).hexdigest()
oldsha=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",nb).group(1)
nb=nb.replace(oldsha,sha)
tmp=CD+'.r212tmp'; open(tmp,'w',encoding='utf-8').write(nb); os.replace(tmp,CD)
assert open(CD,'rb').read()==nb.encode('utf-8')
print('pins after:',len(pairs2),'sha',oldsha[:16],'->',sha[:16])
