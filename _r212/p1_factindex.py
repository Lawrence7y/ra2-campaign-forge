# -*- coding: utf-8 -*-
"""R212 p1：FACT_INDEX V593 -> V594，把 R212 两项新事实写入 F29。
纪律：wx 独占备份 + 旧 sha/CR 断言 + 一次性写入 + 回读校验 + 逐行不变。
"""
import os,shutil,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
OLDV=TIER+'/R17_R131_FACTINDEX_V593/FACT_INDEX.tsv'
NEWDIR=TIER+'/R17_R131_FACTINDEX_V594'
raw=open(OLDV,'rb').read()
OLD_SHA=hashlib.sha256(raw).hexdigest(); OLD_B=len(raw)
print('V593 sha %s bytes %d'%(OLD_SHA,OLD_B))
assert OLD_SHA=='1f6fe2af208c29b1a1ed0183f6c3853c7ed0c7cf20d058a8595bd2a850f5d43f',OLD_SHA
assert OLD_B==251275,OLD_B
lines=raw.decode('utf-8').split('\n')
ORIG=list(lines)
print('rows(split)=%d trailing_empty=%s'%(len(lines),lines[-1]==''))
idx=[i for i,l in enumerate(lines) if l.startswith('F29\t')]
assert len(idx)==1,idx
i=idx[0]; cols=lines[i].split('\t')
assert len(cols)==5,len(cols)
print('F29 列数 5 OK；改前 stmt=%d lim=%d'%(len(cols[1]),len(cols[2])))
ADD=('【S 域 8/12 接口身份 · R212】BCA 记录按 BCD 24B 结构解析后实测：mdisp==8 的 BCA 记录恰 78 条、'
 'pTD 全部为 .?AVINoticeSink@@（TD 址 0x816b50）；mdisp==12 恰 78 条、pTD 全部为 .?AVINoticeSource@@（TD 址 0x8177e8）。'
 '二者均属 TD_OWN（954 个 own COL 的 pTD 集合）且均不属 INTERFACE（26 个 .?AU 类型描述符），'
 '即 S 域两偏移来自「本类自己的类 TD」，与 T 域的接口 BCD 来源不同源。两偏移的出现类集合完全相同（78 类，差集 0/0）。'
 '78 条记录的 (nc,pdisp,vdisp,attributes) 全为 (0,-1,0,0)，无一条例外。'
 'BCA 中的相对位置：8 记录索引恒等于 12 记录索引 − 1（78/78，即 8 紧邻 12 之前）；'
 '但绝对索引不固定（8 在 6..12、12 在 7..13，随继承深度变化），距 BCA 末尾的记录数分布 {1:67, 2:4, 3:5, 5:1, 7:1}，'
 '故两条记录不占据固定的首部或尾部槽位。反控：索引 0 记录 mdisp 恒 0（954/954），8/12 恒不在索引 0。'
 '【S 域 8/12 视图的 vftable 字节侧复算 · R212】不经 mdisp 推导，直读槽表：78 类中 8 与 12 的视图 slot0 落点全部异址（同 0 / 异 78），'
 '两视图槽数均为 1（单槽接口表，78/78）。8 视图 slot0 落点分布 {0x410580:75, 0x41bc30:1, 0x522a60:1, 0x746100:1}，'
 '12 视图 slot0 落点 0x410590 被 78 类全部共享。字节级函数体：0x410580 = xor al,al ; ret 8（2 条指令，无条件返回 false、清 2 个 dword 参数），'
 '0x410590 = ret 4（首指令即 ret，清 1 个 dword 参数，其后为 nop 填充与独立函数 0x4105a0，非本函数体）。'
 '两地址在全 .text 线性扫描下被直接 call/jmp 命中 0 次（纯虚调用入口，无静态直调路径）。'
 '⇒ 8 域 75 类共享同一个「恒返回 false」的桩，另 3 类（AircraftClass 0x41bc30 / InfantryClass 0x522a60 / UnitClass 0x746100）'
 '为真函数体，体内均含 lea esi,[edi-8] 的 this 调整与 cmp ebx,0x117b，即 R208 已证的 I 域三形态——'
 '此处从 S 域视角再得一次独立确认：mdisp=8 槽在 3 个 I 域类里由真实现取代共享桩。'
 '【ATL EventSink V 空 = 律 W 全过滤 · R212】5 个 EventSink（CHD 0x80e680 / 0x80e740 / 0x80e780 / 0x80e7c0 / 0x80e998）'
 '的 BCA 各含 5-6 条记录，其中非零 mdisp 记录各 2 条，pTD 恒为 .?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL@@ (mdisp=4, nc=1) '
 '与 .?AVCComObjectRootBase@ATL@@ (mdisp=4, nc=0)；两者均为 onlysec（既 ∉ INTERFACE 亦 ∉ TD_OWN），'
 '故律 W 对其得空集，与实测空视图逐类一致（5/5）。⇒ V 为空是律 W 过滤的结构性后果，不是视图丢失；'
 '判定依据：其 BCA 确实存在非零 mdisp 记录（各 2 条），若不做 pTD 过滤会得 {4}（反控实测 5/5 非空），'
 '说明判别力来自 pTD 归属而非「记录缺失」。'
 '【S3 与 S2 同 pTD 交叉 · R212】mdisp==21784 的 3 条记录 pTD 亦为 .?AVINoticeSink@@（与 mdisp=8 同源），'
 'attributes 恒 9（区别于 mdisp=8 的 0），对应类为 MouseClass(0x7fab28, idx=11) / TabClass(0x805e90, idx=9) / ScrollClass(0x809050, idx=10)，'
 '三类均不含 mdisp=8/12 记录。⇒ 同一个类 TD ?AVINoticeSink@@ 在不同类里被以 8 或 21784 两种偏移引用，'
 '且 21784 记录带 attributes=9 而 8 记录带 0，两者不可互代。'
 '【判据订正 · R212】INTERFACE 集合必须由 pTD 所指向 TD 的内联名（TD+8）判定（全域得 26 个），'
 '不可由 COL 记录自带的名字判定（那样只得 2 个，且使律 W 失配 91 类）——本轮实测该错判据的失配数恰为 91，与 R211 c8/c9 的 91 同值。')
cols[4]=cols[4]+ADD
lines[i]='\t'.join(cols)
nb='\n'.join(lines).encode('utf-8')
nlines=nb.decode('utf-8').split('\n')
assert len(nlines)==len(ORIG)
diff=[j for j in range(len(ORIG)) if ORIG[j]!=nlines[j]]
assert diff==[i],diff
print('仅第 %d 行（F29）变化；其余 %d 行逐字节不变'%(i,len(ORIG)-1))
os.makedirs(NEWDIR,exist_ok=True)
out=NEWDIR+'/FACT_INDEX.tsv'
assert not os.path.exists(out),'V594 已存在，拒绝覆盖'
open(out,'wb').write(nb)
assert open(out,'rb').read()==nb
NSHA=hashlib.sha256(nb).hexdigest(); NB=len(nb)
print('V594 sha %s bytes %d (delta +%d)'%(NSHA,NB,NB-OLD_B))
# 指针：wx 备份 + 断言 + 一次写 + 回读
PTR=TIER+'/FACT_INDEX_CURRENT.md'
b=open(PTR,'rb').read()
bak=BASE+'/FACT_INDEX_CURRENT.md.before_r212_ptr594_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
t=b.decode('utf-8')
for old,new in [('| sha256 | %s |'%OLD_SHA,'| sha256 | %s |'%NSHA),
                ('| 字节数 | %d |'%OLD_B,'| 字节数 | %d |'%NB)]:
    assert t.count(old)==1,(old,t.count(old))
    t=t.replace(old,new)
assert 'V593' in t
t2=t.replace('R17_R131_FACTINDEX_V593','R17_R131_FACTINDEX_V594').replace('V593','V594')
open(PTR,'wb').write(t2.encode('utf-8'))
assert open(PTR,'rb').read()==t2.encode('utf-8')
print('PTR -> V594')
open(ROOT+'/_r212/p1_out.txt','w').write('%s %d %s %d\n'%(OLD_SHA,OLD_B,NSHA,NB))
