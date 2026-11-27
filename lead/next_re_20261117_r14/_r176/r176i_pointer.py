# -*- coding: utf-8 -*-
"""R176 指针 FACT_INDEX_CURRENT.md -> V559（声明式，全部断言在写盘之前）。"""
import os,sys,hashlib,time,csv,io
T='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
PTR=os.path.join(T,'FACT_INDEX_CURRENT.md')
NEWTSV=os.path.join(T,'R17_R128_FACTINDEX_V559/FACT_INDEX.tsv')
BASE=os.path.join(T,'R17_LEAD_BASELINE')
P=F=0
def ck(n,c,d=''):
    global P,F
    if c: P+=1; print('PASS',n,d)
    else: F+=1; print('FAIL',n,d)
raw=open(NEWTSV,'rb').read(); sha=hashlib.sha256(raw).hexdigest()
ck('A1 sha',sha.startswith('e4642d554d8ba9f1'),sha[:16])
ck('A2 bytes',len(raw)==129405)
cur=open(PTR,encoding='utf-8').read()
# S-636: 目录名在指针里出现 TWO 次（版本目录 + 相对路径），原断言写 1 是假 FAIL
ck('B1 ptr currently V558 twice (dir + relpath)',cur.count('R17_R128_FACTINDEX_V558')==2,'%d'%cur.count('R17_R128_FACTINDEX_V558'))
ck('B2 ptr old sha once',cur.count('157996aa5da193d3ac254c9d6026343050b23f969793f83433469d5520bd8aa5')==1)
ck('B3 ptr old bytes once',cur.count('| 字节数 | 128835 |')==1)
ck('B4 ptr declares R175',cur.count('| 声明轮次 | R175 |')==1)
# 版本目录实况（不预估）
dirs=[d for d in os.listdir(T) if d.startswith('R17_R') and '_FACTINDEX_V' in d]
vers=sorted(int(d.split('_V')[-1]) for d in dirs)
ck('C1 version count matches on-disk',len(vers)==len(dirs),'%d'%len(dirs))
ck('C2 max version is 559',max(vers)==559,'%d'%max(vers))
ck('C3 contiguous 530..559',vers[-30:]==list(range(530,560)),repr(vers[-3:]))
ck('C4 R128 holds 4 dirs now',sorted(d for d in dirs if '_R128_' in d)==['R17_R128_FACTINDEX_V556','R17_R128_FACTINDEX_V557','R17_R128_FACTINDEX_V558','R17_R128_FACTINDEX_V559'],repr(sorted(d for d in dirs if '_R128_' in d)))
new=cur
new=new.replace('R17_R128_FACTINDEX_V558','R17_R128_FACTINDEX_V559')
new=new.replace('157996aa5da193d3ac254c9d6026343050b23f969793f83433469d5520bd8aa5',sha)
new=new.replace('| 字节数 | 128835 |','| 字节数 | 129405 |')
new=new.replace('| 声明轮次 | R175 |','| 声明轮次 | R176 |')
OLD_BASIS='版本号 530..558 连续无缺；V558 是「版本号最大」。**R175 再订正**：R175 当日已在 R128 下产生 V556/V557/V558 **三份**，故原「R128 下只有这一个目录」彻底失效；现依据改为「版本号最大 + 该目录内文件 sha256 与 facts_floors.py 的 D0 一致」两条同时成立'
NEW_BASIS='版本号 530..559 连续无缺；V559 是「版本号最大」。**R176 三次订正**：R128 下现已有 V556/V557/V558/V559 **四份**（同一轮内可生成多版），故「R128 下只有这一个目录」与「R128 下三份」两种写法都已失效；现依据固定为「版本号最大（现盘 530..559 连续 30 份）+ 该目录内文件 sha256 与 facts_floors.py 的 D0 一致」两条同时成立'
ck('C5 basis sentence present once',cur.count(OLD_BASIS)==1,'%d'%cur.count(OLD_BASIS))
new=new.replace(OLD_BASIS,NEW_BASIS)
new=new.replace('V530..V557 是 28 个可独立复核的快照','V530..V559 是 30 个可独立复核的快照')
ck('D1 new dir twice',new.count('R17_R128_FACTINDEX_V559')==2,'%d'%new.count('R17_R128_FACTINDEX_V559'))
ck('D2 old dir zero',new.count('R17_R128_FACTINDEX_V558')==0)
ck('D3 new bytes str',new.count('| 字节数 | 129405 |')==1)
ck('D4 R176 declared',new.count('| 声明轮次 | R176 |')==1)
ck('D5 old 三份 wording gone',new.count('R128 下三份')==1 and new.count('V556/V557/V558 **三份**')==0,'三份=%d'%new.count('三份'))
ck('D6 V556/V557/V558/V559 四份 written',new.count('V556/V557/V558/V559 **四份**')==1)
if F: print('ABORT'); sys.exit(1)
ts=time.strftime('%Y%m%d_%H%M%S')
bp=os.path.join(BASE,'FACT_INDEX_CURRENT.md.before_r176_%s.bak'%ts)
with open(bp,'xb') as f: f.write(cur.encode())
ck('E1 backup',open(bp,'rb').read()==cur.encode())
with open(PTR,'wb') as f: f.write(new.encode())
ck('F1 readback',open(PTR,encoding='utf-8').read()==new)
ck('F2 CR=0',b'\r' not in open(PTR,'rb').read())
print('---- %d PASS / %d FAIL ----'%(P,F))
sys.exit(1 if F else 0)
