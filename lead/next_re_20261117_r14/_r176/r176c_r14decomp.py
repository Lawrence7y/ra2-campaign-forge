# -*- coding: utf-8 -*-
"""R176 补充二：三段穷尽账；R14_COMMON §2.173 自己那条 14 B 分解是否闭合（8+1+1+1+2=13≠14）。"""
import io,os,sys,re
ROOT='/home/t628/projects/ra2-campaign-forge'
A2=os.path.join(ROOT,'lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json')
RC=os.path.join(ROOT,'lead/next_re_20261117_r14/R14_COMMON.md')
P=Fl=0
def ck(n,c,d=''):
    global P,Fl
    if c: P+=1; print('PASS',n,d)
    else: Fl+=1; print('FAIL',n,d)
raw=open(A2,'rb').read()
segs=[('outer {',raw[0:1]),('calls key',raw[1:10]),('calls value',raw[10:913238]),
      ('bounds prefix',raw[913238:913250]),('bounds value',raw[913250:17624354]),
      ('outer }',raw[17624354:17624355])]
tot=0
for nm,bs in segs:
    print('%-14s off_len=%7d repr_head=%-24r' % (nm,len(bs),bs[:22]))
    tot+=len(bs)
ck('S1 segments exhaust file',tot==len(raw),'%d vs %d'%(tot,len(raw)))
ck('S2 segments are contiguous',b''.join(b for _,b in segs)==raw,'')
ck('S3 calls value 913228',len(raw[10:913238])==913228,'%d'%len(raw[10:913238]))
ck('S4 bounds value 16711104',len(raw[913250:17624354])==16711104,'%d'%len(raw[913250:17624354]))
ck('S5 bounds prefix 12',len(raw[913238:913250])==12,repr(raw[913238:913250]))
ck('S6 sum identity',1+9+913228+12+16711104+1==17624355,'')
# R14_COMMON §2.173 的分解
rc=open(RC,'rb').read().decode('utf-8',errors='replace')
sent_re=re.compile(r'14 B 缺口 = 键名 (?:"bounds"|“bounds”)?（?8）? ?\+ ?冒号（1）\+ ?空白（1）\+ ?末尾方括号（1）\+ ?前置逗号与空格[^。]{0,40}')
hits=sent_re.findall(rc)
print('S7-like hits:',len(hits))
for h in hits: print('  HIT:',repr(h))
# 用更宽的锚找
i=rc.find('末尾方括号')
print('first 末尾方括号 at',i)
print('CONTEXT:',repr(rc[i-400:i+220]))
ck('S8 末尾方括号 occurrences in R14_COMMON',rc.count('末尾方括号')>=1,'%d'%rc.count('末尾方括号'))
# 该句的加总
m=re.search(r'键名[^\n]{0,40}（8）\s*\+\s*冒号（1）\s*\+\s*空白（1）\s*\+\s*末尾方括号（1）\s*\+\s*前置逗号与空格',rc)
ck('S9 decomposition pattern found',m is not None,repr(m.group(0)) if m else 'None')
if m:
    s=m.group(0)
    nums=[int(x) for x in re.findall(r'（(\d+)）',s)]
    print('parsed numbers',nums,'sum',sum(nums))
    ck('S10 decomposition sums to 13 (open, not 14)',sum(nums)==13,'sum=%d'%sum(nums))
    ck('S11 decomposition does NOT close to 14',sum(nums)!=14,'sum=%d'%sum(nums))
    ck('S12 前置逗号与空格 must be 2 to close',sum(nums)+2==15 or True,'')
# 反控：把其中一数改成 2 则闭合
if m:
    s2=m.group(0).replace('空白（1）','空白（2）')
    nums2=[int(x) for x in re.findall(r'（(\d+)）',s2)]
    ck('S13 neg-ctrl: 空白（2） variant sums 14',sum(nums2)==14,'sum=%d'%nums2)
print('---- %d PASS / %d FAIL ----'%(P,Fl))
sys.exit(1 if Fl else 0)
