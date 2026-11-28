#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 台账：V587 -> V588，按写入纪律「新版本目录先写、再改指针、再同步 runner」。
只改 F01 一行（RTTI 布局宿主事实行），其余 55 行逐字节不变（G2b 硬闸）。
"""
import os,shutil,hashlib,json,time
G='/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14'
BL='/home/t628/projects/ra2-campaign-forge/R17_LEAD_BASELINE'
SRC=G+'/R17_R131_FACTINDEX_V587/FACT_INDEX.tsv'
DST=V588=G+'/R17_R131_FACTINDEX_V588'
stamp=time.strftime('%Y%m%d_%H%M%S')
def sha(p): return hashlib.sha256(open(p,'rb').read()).hexdigest()
fails=[]
def ck(nm,c,d=''):
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))

ck('K0 V588 目录尚不存在（不覆盖）',not os.path.exists(DST),DST)
src=open(SRC,'rb').read()
pre=hashlib.sha256(src).hexdigest()
ck('K1 V587 sha == 062111ba...',pre.startswith('062111ba'),pre[:16])
lines=src.split(b'\n')
ck('K2 V587 行数',len(lines)>50,len(lines))
hdr=lines[0]
rows=[l for l in lines[1:] if l.strip()]
ck('K3 数据行数',len(rows),len(rows))

R205_ADD=(
'⑫**R205 交付（主会话 m7_final.py 22 断言仅 1 FAIL 且为自身断言过强、m12_ctl2.py 14、m16_final_vti.py 15、m17_runs.py 10、m18_e8.py 18 断言全 0 FAIL；执行员 #518 独立复算 7 项逐数一致、审计员 #519 见 R14_COMMON §2.210 第八节）**：'
'**CHD 记录实为 40 字节，R204 的 16 字节是截断（取得 R204 未取得项④）**。'
'① **40 字节头逐字段实证 954/954**：`+0` 恒 **0**；`+4` attributes `{0:855, 1:66, 5:33}`（与 R204 一致）；`+8` numBaseClasses **恒等于 len(BCA)**（分布 1:256/2:455/3:120/4:11/5:12/6:6/7:6/8:2/9:33/10:26，max 18）；`+12` pBCA 全在 `.rdata`（954/954 互异）；**`+16` 起 20 字节是一条完整 COL 记录**：`sig==0`、`mdisp==0`、`cdOffset==0`、`pTD` 全在 `.data`、**`pCHD` 等于该 CHD 自身地址 954/954**；`+24` 恒 0；`+36` 是本条记录终点。'
'② **判据强度分级（反控口径订正后）**：六条判据逐级累加在 954 真值上恒 **954/954**；在**剔除 954 个真 CHD 后**的 20,000 个 `.rdata` 随机地址上假阳为 `+0==0` **5,056** → `+0 且 +24==0` **3,536** → **`+32==自身` 0** → `+16 是 COL` 0 → `+pTD 属 954 自有` 0 → `+pBCA 在 .rdata` 0 ⇒ **自指判据 `dw(a+32)==a` 单条即充分**，其余四条是全余加固。七档错位反控（-4/+4/+8/+12/+20/+36/+40）在 954 真值上命中 **0**；`.data` 段 20,000 随机地址六元判据假阳 **0**。'
'③ **两个 954 不是同一批（消除 R203 混同风险）**：R203 的「954 组头」是组内 **mdisp 最大的首视图**，R205 的「954 内嵌主对象 COL」是 **mdisp==0 的末视图**；两者**交集仅 860**，差的 **94** 恰是多视图（MI）类。每 CHD 组内 `mdisp==0` 的视图**唯一**且**就是** `CHD+16`（954/954）；954 组头与 954 CHD **一一映射**。计数复核全部复现 R203：vftable 起点 **1214**（`vt` 地址口径）/组头 **954**/被吞伪起点 **260**/视图 **1214**，视图数分布 `1:860/2:10/3:6/4:76/5:1/7:1`；**每个 COL 恰被 1 个 vt 以 `vt-4` 引用（1214/1214）**。'
'④ **978 条 `mdisp==0` 三分解（R204 只报了 954 自有部分）**：**956** 条 pTD 属 954 个类的自有 pTD（覆盖 **954** 个互异 TD；`INoticeSource` 与 `VectorClass<H>` 各有 2 条记录）+ **22** 条 pTD **不属于**任何 954 类，覆盖 **21** 个互异 TD（`UIUnknown` 2 条：`0x7fa9e8` / `0x7fb080`，后者 attributes==2）。22 条逐条实测：pTD 名**全不在** 954 类名集内；**17 条 `.?AU` 接口前缀 + 5 条 `.?AV`**（DiskSwap / Node<INIEntry@INIClass> / Node<MixFileClass> / DynamicVectorClass<DiskID> / CDownloadEventSink）；**其 pTD 从不出现在任何 COL 的 pTD 字段** ⇒ 它们**没有 vftable 视图**，却在 BCA 中被引用 **474** 次，且**从不出现在 BCA[0]**（BCA[0] 恒为本类自有 BCD）。被继承次数 top5：`UIUnknown` 98 / `UIUnknown` 91 / `UIPersist` 90 / `UIPersistStream` 90 / `UIClassFactory` 78。'
'⇒ **R204 的充要律 2「`BCD.mdisp==0` ⟺ pTD 属本类自有」只在 954 类内部成立**；放宽到全 BCD 池后有 **22 条**反例，它们是**纯接口基类**（有类型描述符、无 vftable 视图）。'
'⑤ **取得 R204 未取得项③（段长恰 8 的 79 段成因）**：用**原序**（继承路径序，非地址序）切段复现 R204 全部数字 —— 相邻对 **1661**、`-24` 占 **973**、段数 **1642**、段长 `{1:1252,2:259,3:31,4:8,5:6,6:3,7:1,8:79,10:1,11:1,12:1}`、单元素段 **76.2%**。79 个 8 长段：地址跨度**恒 168 字节**（7×24）；**78 个**首元素 pTD 是 **`.?AVAbstractClass@@`** 且这 78 段的 pTD 名序列**完全一致**（`AbstractClass/UIPersistStream/UIPersist/UIUnknown/UIRTTITypeInfo/UIUnknown/INoticeSink/INoticeSource`），`mdisp` 序列恒 `(0,0,0,0,4,4,8,12)`；唯一例外是 **`.?AVSidebarClass@@`** 段（`SidebarClass/PowerClass/RadarClass/DisplayClass/MapClass/GScreenClass/UIGameMap/UIUnknown`，mdisp 全 0）。79 段中 **68 个是该类 BCA 的最后一个段**，其余 11 个后续段长 `{2:5,1:4,4:1,6:1}`；长度阈值敏感性 6/7/8/9/10 → **3/1/79/0/1** ⇒ 8 是**内容产物**（AbstractClass 那条单继承链恰好 8 个基点）而非网格产物。'
'⑥ **否定结果（进结论）**：`COL.sig` 字段在本镜像**无判别力** —— 1214 条 COL 的 sig **全部为 0**（内嵌 954 条与外层 260 条无差别）。R203/R204 沿用 `sig in (0,1,2)` 作为形态约束是保守的、**非充分条件**，不得作为区分主/子视图的依据。'
'⑦ **自错 14 组（0 条进结论）**，关键 8 条：(a) 把 R204「954 条为每类自有」误读为「每张 BCA 恰 1 条 mdisp==0」；(b) 断言「类级 COL 与 1214 视图 COL 不相交」方向写反（实测 954 个类级 COL **全部是**视图 COL 的元素）；(c) `cname` 取 `TD` 而非 `TD+8`，且把 `CHD+8`（numBaseClasses）当 cdOffset（应取 `+24`）；(d) 假设 `COL.sig ∈ {0,1,2}` 有区分力，被「1214 全 0」砸掉，反开 ⑥；`claimed` 集合混装 COL 地址与 vftable 地址致 1214 全被当组头；(e) 视图分隔位置存的是 `vt-4` 而 VTI 的键是 `vt`，用 `p in VTI` 判恒假得「组头 1214/被吞 0/视图 1729」，改判 `p+4` 后 954/260/1214；(f) 用**三元**判据在 5,000 个随机 `.rdata` 地址上报「0 命中」实测 **90 命中**，逐条核实**全部是真 CHD**（反控池未剔除真值），修正后 20,000 池假阳 0；(g) 用 `sorted(BCA)` 切段得 **1610** 段 / 1217 单元素，与 R204 的 1642/1252 **口径不等价**（原序才是继承路径序）；(h) 把「vftable 槽 0 的内容」当 vftable 起点得 **891**（正确口径是存放 COL 指针的那个 dword 的**地址**，得 **1214**）；**执行员 #518 的 X2=891 是同一错误**，已双向订正。'
'⑧ **另撤回一条过强表述**：R203 原述「组内 `mdisp` **递减**」若读作「**严格**递减」则不成立 —— 260 个组内相邻对中有 **3** 个非严格递减：`.?AVOverlayClass@@`(0x807598) `[12,4,8,0]`、`.?AVSmudgeClass@@`(0x809848) `[12,4,8,0]`、`.?AVTerrainClass@@`(0x80c370) `[4,12,8,0]`。R203 原述「**末端**视图恒 `mdisp==0`」仍成立（954/954）。'
)

new_rows=[]
hit=0
for r in rows:
    parts=r.split(b'\t')
    if parts[0]==b'F01':
        hit+=1
        old=parts[1].decode('utf-8')
        parts[1]=(old+R205_ADD).encode('utf-8')
        print('   F01: %d B -> %d B（+%d）'%(len(old.encode()),len(parts[1]),len(parts[1])-len(old.encode())))
        # 补 evidence_paths
        ev=parts[3].decode('utf-8') if len(parts)>3 else ''
        addp='_r205/m7_final.py,_r205/m12_ctl2.py,_r205/m16_final_vti.py,_r205/m17_runs.py,_r205/m18_e8.py'
        parts[3]=(ev+(';' if ev else '')+addp).encode('utf-8')
        print('   F01 evidence_paths +%d B'%(len(addp)+ (1 if ev else 0)))
    new_rows.append(b'\t'.join(parts))
ck('K4 F01 恰被改 1 次',hit==1,hit)
other_changed=[i for i,(a,b) in enumerate(zip(rows,new_rows)) if a!=b and not a.startswith(b'F01\t')]
ck('K5 除 F01 外其余行逐字节不变',len(other_changed)==0,other_changed[:3])
ck('K6 行数不变',len(new_rows)==len(rows),len(new_rows))

os.makedirs(DST)
new=b'\n'.join([hdr]+new_rows)+b'\n'
open(DST+'/FACT_INDEX.tsv','wb').write(new)
post=sha(DST+'/FACT_INDEX.tsv')
ck('K7 新文件字节 = 旧 + 增量',len(new)-len(src)>0,len(new)-len(src))
ck('K8 新文件 56 行数据',len(new.split(b'\n'))-2==len(rows),len(new.split(b'\n'))-2)
# 复算校验：旧常量复算旧 MASTER 必须命中旧 pin（硬闸）
old_master=hashlib.sha256(src).hexdigest()
ck('K9 硬闸：旧文件 sha == 旧 pin 062111ba...',old_master.startswith('062111ba'),old_master[:16])
print('V588: sha %s bytes %d'%(post[:16],len(new)))
print('\nFAILS:',fails)
json.dump(dict(fails=fails,v588_sha=post,v588_bytes=len(new),
               src_sha=pre,src_bytes=len(src)),open('/home/t628/projects/ra2-campaign-forge/_r205/p4_ledger.json','w'),indent=1)
