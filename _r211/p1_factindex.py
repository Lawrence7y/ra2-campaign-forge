# -*- coding: utf-8 -*-
"""R211 p1：FACT_INDEX V592 -> V593，把律 W（视图偏移集合由 BCA 记录决定）写入 F29。
纪律：版本目录 + 逐行不变校验 + 指针/facts_floors/gate_runner 同步重钉。
"""
import os,shutil,hashlib,re
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
OLDV=TIER+'/R17_R131_FACTINDEX_V592/FACT_INDEX.tsv'
NEWDIR=TIER+'/R17_R131_FACTINDEX_V593'
raw=open(OLDV,'rb').read()
OLD_SHA=hashlib.sha256(raw).hexdigest(); OLD_B=len(raw)
print('V592 sha %s bytes %d'%(OLD_SHA,OLD_B))
assert OLD_SHA.startswith('b3327fd4'),OLD_SHA
lines=raw.decode('utf-8').split('\n')
ORIG=list(lines)   # 逐行不变校验的基准
print('rows(split)=%d ; trailing empty=%s'%(len(lines),lines[-1]==''))
# 找 F29 行
idx=[i for i,l in enumerate(lines) if l.startswith('F29\t')]
assert len(idx)==1,idx
i=idx[0]; cols=lines[i].split('\t')
print('F29 cols=%d  stmt_len=%d  lim_len=%d'%(len(cols),len(cols[1]),len(cols[2])))
ADD=('【律 W · R211】视图偏移集合由 BCA 记录决定：V(c) == { mdisp(r) : r ∈ BCA(c), mdisp(r) != 0, '
 'pTD(r) ∈ INTERFACE ∪ TD_OWN }，对全部 954 类逐类零失配（判据 COL 记录独立源与 vftable 槽扫描两源同值 954/954）。'
 'INTERFACE = pTD 名字以 .?AU 开头的类型描述符（26 个），TD_OWN = 954 个 own COL 的 pTD 集合。'
 '等价式：pTD 名字不以 .?AV 开头 ∨ pTD ∈ TD_OWN。反控：无过滤失配 15 / 仅 TD_OWN 失配 91 / 仅 .?AU 失配 81 / '
 '全量并集套各类成立 0。被排除的恰 26 条 BCD 记录、涉及 5 个 pTD（0x817ab8 ?AVStageClass / 0x817ad8 ?AVFlasherClass / '
 '0x845e30 ?AVBounceClass / 0x84a838 ?AVCComObjectRootBase / 0x84a860 ?AV?$CComObjectRootEx），全部 onlysec（无 COL 引用）。'
 '域分解：T 域（mdisp ∈ 4,24,36,40,44,1728）偏移集合 == {pTD 名 .?AU 的记录 mdisp}；'
 'S 域（mdisp ∈ 8,12,21784）偏移集合 == {pTD∈TD_OWN 且名 .?AV 的记录 mdisp}；两者并集 == V 逐类（零残留）。'
 '⇒ R210 律 U 的 {4} 不再是独立附加项：它是 mdisp=4 的接口 BCD 记录（.?AUIRTTITypeInfo 78 类 / ?AUILocomotion 12 类 / '
 '?AUILinkStream 1 类）加上伴记录 ?AUIUnknown(nc=0,attr=0x2) 的直接结果；R210「HouseClass 唯一反例」是口径问题——'
 'HouseClass 的 V=[4,8,12,36,40,44]，其中 8/12 属 S 域（?AVINoticeSink/?AVINoticeSource），不在律 U 的 T 域内，'
 'T 域恰为 {4,36,40,44}，与律 U 公式一致。计数：COL 记录 1214 / CHD 954 / BCA 元素 2615 / 非零 mdisp 记录 387 / '
 '4∈V 91 类 / 4∈B 96 类 / 差 5 类全为 ATL EventSink 且 V 为空。跨家族 #542(hy4 12/12) 与 #543(deepseek 12/12) 全 PASS，'
 '主会话 §2.12 规则 D 复算 29 断言 0 FAIL。')
assert len(cols)==5
cols[4]=cols[4]+ADD      # 正文列（第 5 列）追加
lines[i]='\t'.join(cols)
nb='\n'.join(lines).encode('utf-8')
# 逐行不变校验
nlines=nb.decode('utf-8').split('\n')
assert len(nlines)==len(ORIG)
diff=[j for j in range(len(ORIG)) if ORIG[j]!=nlines[j]]
assert diff==[i],diff
print('only line %d changed (F29)'%i)
os.makedirs(NEWDIR,exist_ok=True)
out=NEWDIR+'/FACT_INDEX.tsv'
open(out,'wb').write(nb)
assert open(out,'rb').read()==nb
NSHA=hashlib.sha256(nb).hexdigest(); NB=len(nb)
print('V593 sha %s bytes %d (delta +%d)'%(NSHA,NB,NB-OLD_B))
# 备份并写指针
PTR=TIER+'/FACT_INDEX_CURRENT.md'
b=open(PTR,'rb').read()
bak=BASE+'/FACT_INDEX_CURRENT.md.before_r211_ptr593_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
t=b.decode('utf-8')
for old,new in [('| sha256 | %s |'%OLD_SHA,'| sha256 | %s |'%NSHA),
                ('| 字节数 | %d |'%OLD_B,'| 字节数 | %d |'%NB)]:
    assert t.count(old)==1,(old,t.count(old))
    t=t.replace(old,new)
assert 'V592' in t
t2=t.replace('V592','V593').replace('R17_R131_FACTINDEX_V592','R17_R131_FACTINDEX_V593')
open(PTR,'wb').write(t2.encode('utf-8'))
print('PTR updated V592->V593')
open('/home/t628/projects/ra2-campaign-forge/_r211/p1_out.txt','w').write('%s %d %s %d\n'%(OLD_SHA,OLD_B,NSHA,NB))
