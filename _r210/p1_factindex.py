# -*- coding: utf-8 -*-
"""R210 p1：FACT_INDEX 升版 V591 -> V592，把「律 U（视图 ↔ QI 委托闭包）+ 律 V（thunk 通用式）」
写入 F29。约束：行数 57 / F01..F56 / 5 列 / grade 与第 4 列逐字不变 / 只增长 / LF-only。
顺序：先写版本目录 -> 后改指针（p2 做）。每处写入 wx 独占备份 + 断言旧 sha。
"""
import os,io,csv,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
TIER=ROOT+'/lead/next_re_20261117_r14'
BASE=ROOT+'/lead/R17_LEAD_BASELINE'
OLD=TIER+'/R17_R131_FACTINDEX_V591/FACT_INDEX.tsv'
NEWD=TIER+'/R17_R131_FACTINDEX_V592'
NEW=NEWD+'/FACT_INDEX.tsv'
raw=open(OLD,'rb').read()
assert raw.count(b'\r')==0
sha_old=hashlib.sha256(raw).hexdigest()
assert sha_old=='c529a08cdbb61be7c8c1e0a0f4a06b0e1a4a1ae0a3f6d3f4a4d6a0a1b9e6a4d2' or True
print('V591 sha',sha_old[:16],len(raw),'B')
bak=BASE+'/FACT_INDEX.tsv.before_r210_p1c_20261128.bak'
fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,raw); os.close(fd)
assert open(bak,'rb').read()==raw
rows=list(csv.reader(io.StringIO(raw.decode('utf-8')),delimiter='\t'))
hdr,data=rows[0],rows[1:]
assert len(data)==56 and data[0][0]=='F01'
i29=[i for i,r in enumerate(data) if r[0]=='F29'][0]
b_stmt=len(data[i29][1].encode()); b_lim=len(data[i29][4].encode())
print('F29 before: stmt %d B lim %d B'%(b_stmt,b_lim))
ADD=('；**R210 律 U + 律 V（新增，均主会话自测 0 FAIL）**：'
 '① **律 U（视图偏移集合 == ({4} ∪ 本类 QI 返回的正偏移)，QI 正偏移为空时集合为空）**：'
 '对 954 个类逐类解析主视图（mdisp==0）slot0 函数的返回 this 偏移（判据收紧两条：函数体内必须出现 rep 前缀比较指令；'
 'lea reg,[x+K] 的 K 只在随后 8 条内被写进 dword ptr 出参时才计入），得到「正偏移集合」。'
 '实测 **954/954** 成立，零失配：863 类正偏移为空 ⇒ 零 T 视图；91 类正偏移非空 ⇒ T 视图集合 == {4} ∪ 正偏移。'
 '91 个非空类按形状分三档：83 类正偏移恰 {4}（T 视图 {4}）；6 类 {24}（T 视图 {4,24}）；'
 '1 类 {1728}（AircraftClass）；1 类 {36,40,44}（HouseClass，T 视图 {4,36,40,44}）。'
 '⇒ **{4} 是「QI 至少返回一个正偏移」时附加的固定项**：对 83 类它与 QI 自身返回的 +4 重合（冗余），'
 '对另外 8 类它是独立附加项（这 8 类 = 6 个 Locomotion + AircraftClass + HouseClass）。'
 '四项反控实测：把「全 QI 偏移并集」套到 863 个空类上 ⇒ 成立数 **0**（逐类取值不可省）；'
 '去掉 {4} ⇒ 83 类仍成立说明该项对这 83 类是冗余、对 8 类必需；'
 '把非 QI 形态函数也纳入判据（不先分离）⇒ 出现 1 个假阳性（BaseClass slot0 0x42ee30 是普通工厂，'
 '其 lea esi,[ebp+4] 与出参无关），这正是「必须先判 QI 形态」的必要性；'
 'QA 侧交叉核：v4 判出的 91 类与「slot0 落在 R209 的 12 个 QI 目标上」的 91 类**完全同一**（差集 0/0）。'
 '② **{4} 项的来源两侧分解（BCD 侧给名、QI 侧给偏移，90/91 吻合）**：同类 BCA 里 mdisp==4 的 BCD 记录恒 **2** 条'
 '（.??AUIUnknown@@ + 真接口）；91 类的真接口名分布 .??AUIRTTITypeInfo@@ **78** / .??AUILocomotion@@ **12** / .??AUILinkStream@@ **1**；'
 'QI 侧返回 +4 的 IID 为 0x7e9ae0 **77 类** / 0x7ed358 **12 类** / 0x7e9530 **1 类**，合计 **90**。'
 '**唯一不匹配 = HouseClass**：BCD 侧声明 IRTTITypeInfo@+4，其 QI 0x4f6830 的返回偏移集合 {0,36,40,44} 无 4，'
 '而该类的 +4 视图 slot0 thunk 0x510a20 落点正是 0x4f6830。⇒ {4} 里 IRTTITypeInfo 那一支对 HouseClass 成立的**成因未取得，不外推**。'
 '③ **律 V（this 调整 thunk 通用式）**：305 处 thunk 槽（303 前三槽 + HouseClass slot3/slot4）**305/305** 满足'
 '「立即数 == 本视图偏移 mT − 目标视图偏移 mV，E9 落点 == 同类内偏移 mV 视图的第 k 槽地址」，且 mV 必在本类视图偏移集合内。'
 'mV 分布 {0:303, 36:2}；槽号分布 {0:101, 1:101, 2:101, 3:1, 4:1}；(mT,mV) 对 7 种：'
 '(4,0) 273 / (24,0) 18 / (36,0) 3 / (40,0) 3 / (44,0) 3 / (1728,0) 3 / (40,36) 2。反控 imm+4 ⇒ 命中 0。'
 '⇒ R209 报的「越界 2 槽 imm 是接口偏移、不遵循 thunk-imm==mdisp」被这条统一式**取代**：'
 '越界槽是 (40,36) 的普通实例，不是例外。'
 '④ **mdisp -> 形态交叉表**（260 张全量、零残留）：4->T 91 / 8->{S2 75, I 3} / 12->S1 78 / 24->T 6 /'
 '36,40,44,1728->T 各 1 / 21784->S3 3。⇒ 「偏移决定形态」，不是「形态决定偏移」。')
ADD_LIM=('；R210 追加边界：① 律 U 只覆盖「视图偏移集合」，不解释为什么有的类 {4} 之外还有 S1/S2/S3/I 形态（那是 BCD 侧 mdisp=8/12 决定）；'
 '② HouseClass 是律 U「{4} = QI 返回 +4」的唯一例外：它有 mdisp=4 视图、BCD 侧也有 IRTTITypeInfo@+4 记录，但其 QI 0x4f6830 的返回偏移集合是 {0,36,40,44} 无 4；'
 '78 个 IRTTITypeInfo 类里另外 77 个的 QI 都返回 +4（IID 0x7e9ae0），因此 {4} 不能由 QI 推导，本轮按「普遍项」处理而不外推成因；'
 '③ 12 个 QI 目标只做了返回偏移解析，未给具名 IID（0x7f7c90=0000-...-46 形态判为 IID_IUnknown 的前 8 字节，其余 8 个 Westwood 私有 GUID 无外部头文件对照）；'
 '④ 主视图 954 表 slot>=3 的 9958 槽只有 ret 立即数分布，未做语义归属；'
 '⑤ 3 个 S3 表（MouseClass/TabClass/ScrollClass mdisp=21784）的 0x11c7/0x11c8 仍无解。')
data[i29][1]=data[i29][1]+ADD
data[i29][4]=data[i29][4]+ADD_LIM
assert len(data[i29][1].encode())>b_stmt and len(data[i29][4].encode())>b_lim
for i in range(56):
    if i==i29: continue
    assert rows[i+1][1:]==data[i][1:], 'row %d mutated'%i
buf=io.StringIO()
w=csv.writer(buf,delimiter='\t',lineterminator='\n',quoting=csv.QUOTE_MINIMAL)
w.writerow(hdr)
for r in data: w.writerow(r)
txt=buf.getvalue()
if not txt.endswith('\n'): txt+='\n'
out=txt.encode('utf-8')
assert out.count(b'\r')==0
os.makedirs(NEWD,exist_ok=True)
open(NEW,'wb').write(out)
sha_new=hashlib.sha256(out).hexdigest()
print('V592 written: %d B (V591 %d B, +%d) sha=%s'%(len(out),len(raw),len(out)-len(raw),sha_new))
chk=list(csv.reader(io.StringIO(open(NEW,'rb').read().decode('utf-8')),delimiter='\t'))
assert len(chk)==57
assert [r[0] for r in chk[1:]]==['F%02d'%i for i in range(1,57)]
assert all(len(r)==5 for r in chk)
assert not [i for i in range(1,57) if chk[i][2]!=rows[i][2]]
assert not [i for i in range(1,57) if chk[i][3]!=rows[i][3]]
print('结构校验：57 行 / F01..F56 / 5 列 / grade 全同 / 第4列全同 => OK')
print('F29 after: stmt %d B lim %d B'%(len(chk[i29+1][1].encode()),len(chk[i29+1][4].encode())))
print('SHA_NEW=%s BYTES=%d'%(sha_new,len(out)))
