# -*- coding: utf-8 -*-
"""R210 p7：把 §2.218 纳入 C16_FLOORS 重钉（unpinned 0 / hollow 0 / missing 0）+ 重算 C16_FLOORS_SHA256。
C16_FLOORS 是 {小节号: floor} 整数映射，规范化串 = 逐 'k:v' 排序后 '\n' 连接。
"""
import os,re,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'; BASE=ROOT+'/lead/R17_LEAD_BASELINE'
CD=TIER+'/check_disc.py'
src=open(TIER+'/R14_COMMON.md','r',encoding='utf-8').read()
m=re.search(r"^## 2\.218 .*?(?=^## 2\.|\Z)",src,re.S|re.M)
assert m,'§2.218 not found'
n=len(m.group(0).encode('utf-8')); lo=int(n*0.75)
print('§2.218 bytes=%d floor=%d'%(n,lo))
t=open(CD,'r',encoding='utf-8').read()
b=open(CD,'rb').read()
bak=BASE+'/check_disc.py.before_r210_c16b_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
assert open(bak,'rb').read()==b
blk=re.search(r'C16_FLOORS = \{\n(.*?)\n\}',t,re.S).group(0)
pairs=re.findall(r'^    (\d+): (\d+),$',blk,re.M)
print('pins before:',len(pairs),'last:',pairs[-1])
assert not any(k=='218' for k,v in pairs)
lastline='    218: %d,'%lo
nb=t.replace(blk, blk.replace('\n}', '\n'+lastline+'\n}'))
assert nb!=t
pairs2=re.findall(r'^    (\d+): (\d+),$',re.search(r'C16_FLOORS = \{\n(.*?)\n\}',nb,re.S).group(1),re.M)
norm='\n'.join('%s:%s'%p for p in pairs2)
sha=hashlib.sha256(norm.encode()).hexdigest()
nb=nb.replace(re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",nb).group(1), sha)
tmp=CD+'.r210tmp'; open(tmp,'w',encoding='utf-8').write(nb); os.replace(tmp,CD)
print('pins after:',len(pairs2),'sha',sha[:16])
