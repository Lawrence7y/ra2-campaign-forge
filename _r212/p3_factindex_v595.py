# -*- coding: utf-8 -*-
"""R212 p3：FACT_INDEX V594 -> V595，把跨家族审计 #545 复算成立的三条口径限制
与一条卡面订正补入 F29 的 limitations 列（第 5 列）。其余 57 行逐字节不变。"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
OLDV=TIER+'/R17_R131_FACTINDEX_V594/FACT_INDEX.tsv'
NEWDIR=TIER+'/R17_R131_FACTINDEX_V595'
raw=open(OLDV,'rb').read()
OLD_SHA=hashlib.sha256(raw).hexdigest(); OLD_B=len(raw)
print('V594 sha %s bytes %d'%(OLD_SHA,OLD_B))
assert OLD_SHA=='184e2c745e4ea72f22c53fe40b9efe81e2e4b9119236278b265d55a4d9d7e591',OLD_SHA
assert OLD_B==254880,OLD_B
lines=raw.decode('utf-8').split('\n'); ORIG=list(lines)
idx=[i for i,l in enumerate(lines) if l.startswith('F29\t')]
assert len(idx)==1,idx
i=idx[0]; cols=lines[i].split('\t'); assert len(cols)==5
ADD=('【口径限制 · R212 跨家族 #545 复算成立】①「988」与「954」是两把尺，禁互代：988 是 RTTI TypeDescriptor 全池'
 '（.data 段 +0 恒 0x7f9594 且名合式，.?AV 962 / .?AU 26），954 是 954 个 own COL 实际引用的 distinct pTD 池，'
 '两者数值相等关系为 TD_OWN == COL 引用池（954/954 相等），而 TD_OWN ⊂ 全池。'
 '律 W 的 INTERFACE 项必须取全池 26 个 .?AU（COL 引用池里只有 2 个：.?AUINIEntry@INIClass@@ / .?AUINISection@INIClass@@）。'
 '实测该口径不影响任何结论：非零 BCA 记录只载 9 个 .?AU 类型（IUnknown/IRTTITypeInfo/IFlyControl/ILinkStream/'
 'IPiggyback/ILocomotion/IConnectionPointContainer/IPublicHouse/IHouse），故「名字前缀判定」「全池 26 集合」「实载 9 集合」'
 '三种写法给出完全相同的失配 0，且反控三数亦同：无过滤 94 / 仅 TD_OWN 91 / 仅 INTERFACE 81。'
 '②律 W 的零失配含大量平凡项，不得当作 954 类强区分力证据：V 空类 860、载非零记录类 99，'
 '其中 V 空 ∧ 无非零记录 = 855（两侧都空，自动一致）、V 空 ∧ 载非零记录 = 5（律 W 必须把它们滤掉）、'
 'V 非空 ∧ 载非零记录 = 94（律 W 真正吃力的部分）、V 非空 ∧ 无非零记录 = 0。'
 '③全池 2615 条 BCA 记录的 pdisp 恒 -1、vdisp 恒 0，四元组 (nc,pdisp,vdisp,attributes) 中实际只有 nc 与 attributes 两位有区分力。'
 '【订正 · R212 卡面措辞】本轮调度卡 A8 括注「8 紧跟 12 之后/索引更大」方向写反，'
 '实测 8 记录索引 = 12 记录索引 − 1（78/78），即 8 在 BCA 中先于 12；落盘正文方向一直正确，此条只订正卡面。'
 '旁证：78 对的 BCD 地址差 b8 − b12 恒为 +24（78/78），与 R204 S2b「BCA 次序逆序于 BCD 数组次序」一致。'
 '【补充数字 · R212 #545 复算成立】attributes==9 全局共 6 条，除 MouseClass(0x7fab28, mdisp=21784) / '
 'TabClass(0x805e90, 21784) / ScrollClass(0x809050, 21784) 三条外，另三条为 '
 '?AV?$VectorClass@H@@(0x7ff680, mdisp=0) / ?AVINoticeSource@@(0x808170, mdisp=0) / ?AVStageClass@@(0x800600, mdisp=36) '
 '⇒ attributes=9 不专属 S3 三表。∈全池但 ∉(INTERFACE∪TD_OWN) 的 TD 共 10 个，其中 5 个被 BCA 实际载入共 26 条记录'
 '（?AVStageClass 9 / ?AVFlasherClass 6 / ?AV?$CComObjectRootEx@VCComMultiThreadModel 5 / ?AVCComObjectRootBase 5 / '
 '?AVBounceClass 1），另 5 个零命中（?AVDiskSwap / ?$Node@PAUINIEntry@INIClass@@ / ?$Node@PAVMixFileClass@@ / '
 '?$DynamicVectorClass@W4DiskID@@ / ?AVCDownloadEventSink）。')
cols[4]=cols[4]+ADD
lines[i]='\t'.join(cols)
nb='\n'.join(lines).encode('utf-8')
nlines=nb.decode('utf-8').split('\n')
assert len(nlines)==len(ORIG)
diff=[j for j in range(len(ORIG)) if ORIG[j]!=nlines[j]]
assert diff==[i],diff
print('仅第 %d 行变化；其余 %d 行逐字节不变'%(i,len(ORIG)-1))
os.makedirs(NEWDIR,exist_ok=True)
out=NEWDIR+'/FACT_INDEX.tsv'
assert not os.path.exists(out),'V595 已存在'
open(out,'wb').write(nb)
assert open(out,'rb').read()==nb
NSHA=hashlib.sha256(nb).hexdigest(); NB=len(nb)
print('V595 sha %s bytes %d (+%d)'%(NSHA,NB,NB-OLD_B))
PTR=TIER+'/FACT_INDEX_CURRENT.md'
b=open(PTR,'rb').read()
bak=BASE+'/FACT_INDEX_CURRENT.md.before_r212_ptr595_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
t=b.decode('utf-8')
for old,new in [('| sha256 | %s |'%OLD_SHA,'| sha256 | %s |'%NSHA),
                ('| 字节数 | %d |'%OLD_B,'| 字节数 | %d |'%NB)]:
    assert t.count(old)==1,(old,t.count(old))
    t=t.replace(old,new)
assert 'V594' in t
t2=t.replace('R17_R131_FACTINDEX_V594','R17_R131_FACTINDEX_V595').replace('V594','V595')
open(PTR,'wb').write(t2.encode('utf-8'))
assert open(PTR,'rb').read()==t2.encode('utf-8')
print('PTR -> V595')
open(ROOT+'/_r212/p3_out.txt','w').write('%s %d %s %d\n'%(OLD_SHA,OLD_B,NSHA,NB))
