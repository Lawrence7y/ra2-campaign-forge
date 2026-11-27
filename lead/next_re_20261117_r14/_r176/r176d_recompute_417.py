# -*- coding: utf-8 -*-
"""R176 复算审计员 #417 的附加发现（规则 D：不得直接采信）。
A) LEAD_LOCK 是否真有 1 处「键名 8 + 冒号 1 + 空白 1 + 结构字符」
B) 「空白 2」全库是否 0 处
C) R14_COMMON §2.173 的分解式 8+1+1+1+2 是否 =13≠14
D) 全树扫描这些错误标签的总分布（决定改动面）"""
import io,os,re,sys
ROOT='/home/t628/projects/ra2-campaign-forge'
T=os.path.join(ROOT,'lead/next_re_20261117_r14')
P=F=0
def ck(n,c,d=''):
    global P,F
    if c: P+=1; print('PASS',n,d)
    else: F+=1; print('FAIL',n,d)
def rd(p):
    return open(p,'rb').read().decode('utf-8',errors='replace')
LL=rd(os.path.join(ROOT,'lead/LEAD_LOCK'))
RC=rd(os.path.join(T,'R14_COMMON.md'))
BR=rd(os.path.join(T,'STATUS_BOARD.md'))
AR=rd(os.path.join(T,'BOARD_ARCHIVE.md'))
FI=rd(os.path.join(T,'R17_R128_FACTINDEX_V558/FACT_INDEX.tsv'))

labA='键名 8 + 冒号 1 + 空白 1 + 括号与收尾 4'
labB='键名 8 + 冒号 1 + 空白 1 + 结构字符'
print('LL labA',LL.count(labA),'labB',LL.count(labB))
print('RC labA',RC.count(labA),'labB',RC.count(labB))
print('BR',BR.count(labA),BR.count(labB),'AR',AR.count(labA),AR.count(labB))
print('FI labA',FI.count(labA),'labB',FI.count(labB))
ck('A1 LEAD_LOCK holds labB exactly once',LL.count(labB)==1,'%d'%LL.count(labB))
ck('A2 LEAD_LOCK holds labA zero',LL.count(labA)==0,'%d'%LL.count(labA))
i=LL.find(labB)
print('A-CTX:',repr(LL[i-260:i+120]))
# B) 全库「空白 2」出现?
tot=0
for nm,txt in (('LL',LL),('RC',RC),('BR',BR),('AR',AR),('FI',FI)):
    c=txt.count('空白 2')
    tot+=c
    print('空白 2 in',nm,c)
ck('B1 total 空白 2 == 0 (nobody ever wrote the true value)',tot==0,'%d'%tot)
ck('B2 neg-ctrl: 空白 1 present somewhere',(LL.count('空白 1')+FI.count('空白 1'))>=2,
   '%d'%(LL.count('空白 1')+FI.count('空白 1')))
# C) R14_COMMON 的分解式
m=re.search(r'14 B 缺口 = 键名[^\n]{0,160}',RC)
ck('C1 decomposition sentence found',m is not None,'')
print('C-SENT:',repr(m.group(0)))
nums=[int(x) for x in re.findall(r'（(\d+)）',m.group(0))]
print('C nums',nums,'sum',sum(nums))
ck('C2 four numbered items sum 11',sum(nums)==11,'sum=%d'%sum(nums))
ck('C3 + 前置逗号与空格(2) 得 13',sum(nums)+2==13,'%d'%(sum(nums)+2))
ck('C4 13 != 14 (does not close)',sum(nums)+2!=14,'%d'%(sum(nums)+2))
ck('C5 sentence claims 末尾方括号 which is 0 in the 14 B','末尾方括号' in m.group(0),'')
ck('C6 neg-ctrl: 空白（1） appears in that sentence','空白（1）' in m.group(0),'')
# D) 全树扫描 三个错串
bad=['括号与收尾','末尾方括号','键名加冒号加空白加末尾方括号']
for b in bad:
    print('TREE-SCAN',b,'LL',LL.count(b),'RC',RC.count(b),'FI',FI.count(b),'BR',BR.count(b),'AR',AR.count(b))
print('---- %d PASS / %d FAIL ----'%(P,F))
sys.exit(1 if F else 0)
