#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R206 落盘三：check_disc.py 的 C16_FLOORS 纳入新节 211 并重算 C16_FLOORS_SHA256。
下界口径沿用 R119 建表规则（= 本节实测字节的一半，向下取整）。"""
import os,re,hashlib,time,json
B='/home/t628/projects/ra2-campaign-forge'
P=B+'/lead/next_re_20261117_r14/check_disc.py'
BL=B+'/R17_LEAD_BASELINE'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
fails=[]; NA=0
def ck(nm,c,d=''):
    global NA; NA+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
pre=sha(P)
bp=os.path.join(BL,'check_disc.py.before_r206_pin_%s.bak'%stamp)
fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
with os.fdopen(fd,'wb') as f: f.write(open(P,'rb').read())
ck('K0 备份一致',sha(bp)==pre,os.path.basename(bp))
s=open(P,encoding='utf-8').read()
# 本节实测字节
rc=open(B+'/lead/next_re_20261117_r14/R14_COMMON.md',encoding='utf-8').read()
lines=rc.split('\n'); cur=None; buf=[]
for l in lines:
    m=re.match(r'^##\s+2\.(\d+)\b',l)
    if m:
        if cur==211: break
        cur=int(m.group(1)); buf=[l]
    elif cur==211: buf.append(l)
size=len('\n'.join(buf).encode('utf-8'))
ck('K1 §2.211 实测 %d B'%size,size>4000,size)
floor=size//2
ck('K2 新下界 = size//2 = %d'%floor,True,floor)
m=re.search(r'(    210: 6513,\n)\}',s)
ck('K3 找到 C16_FLOORS 末项 210',m is not None)
s2=s[:m.end(1)]+'    '+('211: %d,\n'%floor)+s[m.end(1):]
# 重算 sha
m2=re.search(r'C16_FLOORS = \{(.*?)\n\}',s2,re.S)
pairs=re.findall(r'(\d+): (\d+)',m2.group(1))
d={int(a):int(b) for a,b in pairs}
norm='\n'.join('%d:%d'%(k,d[k]) for k in sorted(d))
nsha=hashlib.sha256(norm.encode('utf-8')).hexdigest()
oldsha=re.search(r"C16_FLOORS_SHA256 = '([0-9a-f]{64})'",s2).group(1)
s3=s2.replace(oldsha,nsha)
open(P,'w',encoding='utf-8',newline='').write(s3)
chk=open(P,encoding='utf-8').read()
ck('K4 写入后 211 在表内',re.search(r'    211: %d,'%floor,chk) is not None)
ck('K5 C16_FLOORS_SHA256 已更新',nsha in chk and oldsha not in chk)
ck('K6 表项数 203',len(re.findall(r'^    \d+: \d+,$',chk,re.M))==203,len(re.findall(r'^    \d+: \d+,$',chk,re.M)))
ck('K7 其余行逐字节不变（除两处）',len([1 for a,b in zip(s.split('\n'),chk.split('\n')) if a!=b])<=3,
   len([1 for a,b in zip(s.split('\n'),chk.split('\n')) if a!=b]))
print('  old sha %s -> new sha %s'%(oldsha[:16],nsha[:16]))
print('\n%d asserts, %d FAIL %s'%(NA,len(fails),fails))
json.dump(dict(asserts=NA,fails=fails,size211=size,floor211=floor,oldsha=oldsha,newsha=nsha),
  open('_r206/p3_pin_c16.json','w'),indent=1)
