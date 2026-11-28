#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 落盘：四件套追加（写入纪律：wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验）。"""
import os,sys,hashlib,shutil,time,json
B='/home/t628/projects/ra2-campaign-forge'
G=B+'/lead/next_re_20261117_r14'
BL=B+'/R17_LEAD_BASELINE'
os.makedirs(BL,exist_ok=True)
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
def crc(p): return open(p,'rb').read().count(b'\r')
def backup(p,tag):
    d,b=os.path.split(p)
    bp=os.path.join(BL,'%s.before_r205_%s_%s.bak'%(b,tag,stamp))
    fd=os.open(bp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o644)
    with os.fdopen(fd,'wb') as f: f.write(open(p,'rb').read())
    return bp
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

print('='*70)
# ---------------- 1. R14_COMMON.md 追加 ## 2.210 ----------------
p=G+'/R14_COMMON.md'
pre_sha=sha(p); pre_cr=crc(p); pre_lf=len(open(p,'rb').read().split(b'\n'))-1
ck('W0 R14_COMMON 旧 sha/CR/LF',True,(pre_sha[:16],pre_cr,pre_lf))
ck('W1 R14_COMMON 旧 CR == 1081',pre_cr==1081,pre_cr)
b1=backup(p,'R14_COMMON')
ck('W2 备份写入且内容一致',sha(b1)==pre_sha,os.path.basename(b1))

S210 = '''
## 2.210 · R17 第 205 轮（2026-11-28）· CHD 记录实为 40 字节，+16 处内嵌本类主对象 COL；954 组头与 954 内嵌 COL 差 94 个 MI 类；978 条 mdisp==0 三分解；79 个 8 长段成因

**一、🔴 结构订正（取得 R204 未取得项④）.** R204 把 CHD 当作 16 字节是**截断**：真跨度 **40 字节**。逐字段实测 954/954 全命中：
`+0` 恒 **0**；`+4` attributes `{0:855, 1:66, 5:33}`（复现 R204）；`+8` numBaseClasses，恒等于 `len(BCA)`，分布 `{1:256,2:455,3:120,4:11,5:12,6:6,7:6,8:2,9:33,10:26,...}` 最大 18；`+12` pBCA 全在 `.rdata`（954/954）；
**`+16` 起 20 字节是一条完整的 COL 记录**：`sig==0`、`mdisp==0`、`cdOffset==0`、`pTD` 全在 `.data`、**`pCHD` 等于该 CHD 自身地址**（954/954）。`+24` 恒 `0`（即内嵌 COL 的 cdOffset）。`+36` 是本条记录终点，`+16` 起点换成 `+36` 后**不再**命中 COL（反控 0/954）。⇒ 每个类的 RTTI 信息是**自包含块**：`[BCD 数组][BCA 数组][40 字节 CHD，其中 +16 内嵌本类主对象 COL]`。

**二、🔴 判据强度分级（反控正确口径）.** 六条判据逐级累加，在 954 真值上恒 **954/954**；在**剔除 954 真 CHD 后的 20,000 个 `.rdata` 随机地址**上假阳逐级为：
`+0==0` 5,056 → `+0 且 +24==0` 3,536 → **`+0 且 +24==0 且 +32==自身` 0** → `+16 是 COL` 0 → `+pTD 属 954 自有` 0 → `+pBCA 在 .rdata` 0。
⇒ **「`+32` 等于自身地址」这一条就足够**（自指判据），后续四条是全余加固。七档错位反控（`-4/+4/+8/+12/+20/+36/+40`）在真值上命中 **0/954**；`.data` 段 20,000 随机地址假阳 **0**（`_r205/m12_ctl2.py`，14 断言 1 FAIL 为我方反控口径写错）。

**三、🔴 两个 954 不是同一批（订正 R203 混同风险）.** R203 的「954 组头」与 R205 的「954 内嵌主对象 COL」**交集仅 860**，差的 **94** 恰是多视图（MI）类：
- **组头 = 组内 `mdisp` 最大的首视图**；**内嵌 COL = `mdisp==0` 的末视图**；
- 单视图类（860）两者重合；多视图类（94）必然分离；
- 每 CHD 组内 `mdisp==0` 的视图**唯一**且**就是** `CHD+16`（954/954）；
- 954 组头 ↔ 954 CHD **一一映射**（`D1a`），954 CHD 各被恰 1 个组头覆盖（`D1b`）。
计数复核：vftable 起点 **1214**（`vt` 地址口径），组头 **954**，被吞伪起点 **260**，视图 **1214**，视图数分布 `1:860/2:10/3:6/4:76/5:1/7:1` 全部复现 R203（`_r205/m16_final_vti.py` A1-B4，15 断言 0 FAIL）。

**四、🔴 978 条 `mdisp==0` 的三分解.** 去重 BCD 的 `mdisp==0` 共 **978**（R204 的 954 是其中自有部分，本轮给出全量分解）：
- **956** 条 pTD 属 954 个类的自有 pTD（覆盖 **954** 个互异 TD；其中 `.?AVINoticeSource@@` 与 `.?AV?$VectorClass@H@@` 各有 **2** 条记录）；
- **22** 条 pTD **不属于**任何 954 类，覆盖 **21** 个互异 TD（`.?AUIUnknown@@` 有 2 条：`0x7fa9e8` / `0x7fb080`）；
- 这 22 条逐条实测：pTD 名**全不在** 954 类名集内；**17 条 `.?AU`** 接口前缀 + 5 条 `.?AV`（`.?AVDiskSwap@@`、`.?AV?$Node@PAUINIEntry@INIClass@@@@`、`.?AV?$Node@PAVMixFileClass@@@@`、`.?AV?$DynamicVectorClass@W4DiskID@@@@`、`.?AVCDownloadEventSink@@`）；
- **其 pTD 从不出现在任何 COL 的 pTD 字段** ⇒ 它们**没有 vftable 视图**，却在 BCA 中被引用 **474** 次，且**从不出现在 BCA[0]**（BCA[0] 恒为本类自有 BCD）；
- 被继承次数 top5：`.?AUIUnknown@@` 98 / `.?AUIUnknown@@` 91 / `.?AUIPersist@@` 90 / `.?AUIPersistStream@@` 90 / `.?AUIClassFactory@@` 78。
⇒ 「`mdisp==0` ⟺ pTD 属本类自有」这条 R204 充要律**只在 954 类内部成立**；放宽到全 BCD 池后有 **22 条**反例，它们是**纯接口基类**（无独立 vftable 视图）。

**五、🔴 取得 R204 未取得项③：段长恰 8 的 79 段成因.** 用**原序**（继承路径序，非地址序）切段复现 R204 全部数字：相邻对 **1661**、`-24` 占 **973**、段数 **1642**、段长 `{1:1252,2:259,3:31,4:8,5:6,6:3,7:1,8:79,10:1,11:1,12:1}`、单元素段 **76.2%**（`_r205/m17_runs.py`，10 断言 0 FAIL）。
79 个 8 长段：地址跨度**恒 168 字节**（`7×24`）；**78 个**首元素 pTD 是 **`.?AVAbstractClass@@`**，且这 78 段的 pTD 名序列**完全一致**：`AbstractClass / UIPersistStream / UIPersist / UIUnknown / UIRTTITypeInfo / UIUnknown / INoticeSink / INoticeSource`，`mdisp` 序列恒 `(0,0,0,0,4,4,8,12)`；唯一例外是 **`.?AVSidebarClass@@`** 段（`SidebarClass / PowerClass / RadarClass / DisplayClass / MapClass / GScreenClass / UIGameMap / UIUnknown`，mdisp 全 0）。
91 个 8 长段里 **68 个是该类 BCA 的最后一个段**（之后无段），其余 11 个后续段长 `{2:5, 1:4, 4:1, 6:1}`。段长阈值敏感性：长度 6/7/8/9/10 的段数分别 **3/1/79/0/1** ⇒ 8 不是网格产物而是**内容产物**（AbstractClass 那一条单继承链恰好 8 个基点）。

**六、📌 自错（当场抓出，0 条进结论）.** 共 **14 组**，关键 6 条：
① `m1` V1 断言「每 CHD 恰 1 条 `mdisp==0` 的 BCD」实测 `{2:455,1:256,3:122,...}` —— R204 QG5 说的是「1002 条去重 BCD 中 954 条为每类自有」，不是「每张 BCA 恰 1 条」；复算 `sum` 计数 **2228** 与 R204 一致。
② `m1` H2b 断言「类级 COL 与 1214 视图 COL 不相交」方向写反，实测 **954 个类级 COL 全部是** 1214 视图 COL 的元素。
③ `m3` `cname` 写成 `P.cstr(P.dw(b))`，TD 名在 `TD+8`，应为 `P.cstr(P.dw(b)+8)`；`C2` 正控把 `CHD+8`（numBaseClasses）当 cdOffset，应取 `+24`。
④ `m5` 假设 `COL.sig ∈ {0,1,2}` 有区分力 —— 实测 **1214 条 sig 全为 0**，该字段在本镜像**无判别力**（否定结果进结论）；`m5` G1f 的 `claimed` 集合混装 COL 地址与 vftable 地址，致 1214 全被当组头。
⑤ `m6/m7` 首跑 `seps` 存的是 COL 指针位置（`vt-4`），而 VTI 的键是 vftable 起点（`vt`），用 `p in VTI` 判恒假得组头 1214/被吞 0/视图 1729；改判 `p+4` 后 954/260/1214。
⑥ `m10` C3 用**三元**判据（`+0==0 / +24==0 / +32==自身`）在 5,000 个随机 `.rdata` 地址上报「0 命中」，实测 **90 命中**，逐条核实**全部是真 CHD**（反控口径错：抽样池未剔除真值）；修正后 20,000 池假阳 **0**。
⑦ `m10` L2c/L2d 用 `sorted(BCA)` 后切段得 1610 段 / 1217 单元素，却拿去与 R204 的 1642/1252 比 —— 口径不等价（`m17` R5/R6）。
⑧ `m14` M2 把「vftable 槽 0 的内容」当 vftable 起点，得 **891**；正确口径 `vt = 存放 COL 指针的那个 dword 的地址`，**1214/1214 每个 COL 恰被 1 个 vt 引用**。**执行员 #518 的 X2=891 是同一错误**，本轮双向订正。
⑨ `m13` D2.5 断言「组内 mdisp 严格递减 954/954」**不成立**，实测 260 个组内相邻对中 **3** 个非严格递减：`.?AVOverlayClass@@`(0x807598) `[12,4,8,0]`、`.?AVSmudgeClass@@`(0x809848) `[12,4,8,0]`、`.?AVTerrainClass@@`(0x80c370) `[4,12,8,0]`。R203 原述「**末端**视图恒 mdisp==0」仍成立（954/954），但「**严格**递减」只能表述为「递减，3 例外」。
⑩ `m18` T2/T6/T9a 三条断言写错（8 长段地址序列实际 2 种、AbstractClass 出现 78 非 79、numBaseClasses 恰 9 的只有 27 非「多数」）。

**七、🟡 跨家族与落盘.** 执行员 **#518**（hy4，X1-X8 全给数）与审计员 **#519**（deepseek）见第八节。执行员独立复算 **X1=1214 / X3=954 / X4=954 / X5=954 / X6=954 / X7={"1":954} / X8={978,956,22} 全部与主会话逐数一致**；其 **X2=891 与 C1=132「假阳」两项被主会话复算订正**（891 是槽 0 内容去重、132 全部是真 CHD）。落盘：本节 R14_COMMON **CR 保持 1081**；GOAL §1260 CR 保持 **337**；LEAD_LOCK QH 段 CR 保持 **137**；STATUS_BOARD 第 205 轮 CR 保持 **0**。

**八、⚪ 未取得（不粉饰）.** ① `COL.sig` 在本镜像恒 0，其原义（是否曾用于区分单/多重继承）无法从本镜像取得；② 3 个非严格递减反例（Overlay/Smudge/Terrain）的**语义**成因未取得，只取得字节事实；③ 22 条无 vftable 接口基类中 5 条 `.?AV`（非接口前缀）为何也无 vftable 视图未定性；④ 2 个 TD 各 2 条 `mdisp==0` 记录（`INoticeSource` / `VectorClass<H>`）的语义未取得；⑤ `.?AUIUnknown@@` 有 2 条非自有 `mdisp==0`（`0x7fa9e8` / `0x7fb080`，后者 attributes==2）的差别未取得；⑥ CHD `+36` 之后（下一条块起点前）的字节语义未取得；⑦ R204 遗留的 464 张非等差 CHD 中 111 张「短 BCA 非等差」成因、`attributes 5 vs 1` 语义仍未动；⑧ 5 个 ATL 类为何不产生第二张 vftable、260 个被吞候选归类、94 个 MI 类基类名链仍未动；⑨ R200 (c)(d)(f)(g)；⑩ F23/F35 grade；⑪ `coverage.tsv`/`function_atlas.tsv` 仍不可读；⑫ 86.19% 仍不可重算；⑬ C7 三死分支各 0 行；⑭ C11 十二个 ID 未动。
'''
data=open(p,'rb').read()
ck('W3 R14_COMMON 末尾是 LF',data.endswith(b'\n'),data[-1:])
new=data+S210.encode('utf-8')
open(p,'wb').write(new)
post=open(p,'rb').read()
ck('W4 R14_COMMON 写入后 CR 仍 1081',crc(p)==1081,crc(p))
ck('W5 R14_COMMON 新增 §2.210',b'## 2.210' in post,None)
ck('W6 R14_COMMON 回读 sha 与预期一致',sha(p)==hashlib.sha256(new).hexdigest(),sha(p)[:16])
ck('W7 R14_COMMON 前缀未变（旧内容逐字节保留）',post[:len(data)]==data,None)

print('='*70)
print('R14_COMMON: %s -> %s, +%d B'%(pre_sha[:16],sha(p)[:16],len(new)-len(data)))
print('\nFAILS:',fails)
json.dump(dict(fails=fails,r14_pre=pre_sha,r14_post=sha(p)),open(B+'/_r205/p1_write.json','w'),indent=1)
