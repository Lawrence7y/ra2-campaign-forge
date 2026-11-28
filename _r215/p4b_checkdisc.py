# -*- coding: utf-8 -*-
"""R215 p4b：check_disc C16_FLOORS 纳入 §2.223（gate_runner LEDGER 已由 p4 首次运行改好）。"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
CD=TIER+'/check_disc.py'
src=open(TIER+'/R14_COMMON.md','r',encoding='utf-8').read()
m=re.search(r"^## 2\.223 .*?(?=^## 2\.|\Z)",src,re.S|re.M)
assert m,'§2.223 not found'
n=len(m.group(0).encode('utf-8')); lo=int(n*0.75)
print('§2.223 bytes=%d floor=%d'%(n,lo))
ts=open(CD,'r',encoding='utf-8').read()
cb=open(CD,'rb').read()
bak2=BASE+'/check_disc.py.before_r215_c16_20261128.bak'
if not os.path.exists(bak2):
    fd=os.open(bak2,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,cb); os.close(fd)
    assert open(bak2,'rb').read()==cb
    print('backup written')
else:
    print('backup already exists (p4 first run)')
blk=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',ts,re.S).group(0)
pairs=re.findall(r'^    (\d+): (\d+),$',blk,re.M)
print('pins before:',len(pairs),'last:',pairs[-1])
assert not any(k=='223' for k,v in pairs)
nb=ts.replace(blk, blk.replace('\n}', '\n    223: %d,\n}'%lo))
assert nb!=ts
blk2=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',nb,re.S).group(1)
pairs2=re.findall(r'^    (\d+): (\d+),$',blk2,re.M)
norm='\n'.join('%s:%s'%p for p in pairs2)
sha=hashlib.sha256(norm.encode()).hexdigest()
oldsha=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",nb).group(1)
nb=nb.replace(oldsha,sha)
tmp=CD+'.r215tmp'; open(tmp,'w',encoding='utf-8').write(nb); os.replace(tmp,CD)
assert open(CD,'rb').read()==nb.encode('utf-8')
print('pins after:',len(pairs2),'sha',oldsha[:12],'->',sha[:12])
