# -*- coding: utf-8 -*-
"""R211 p4：四件套（R14 §2.219 / GOAL §1269 / LEAD_LOCK QT / BOARD 第 211 轮）。
每处：wx 独占备份 -> 断言旧 CR -> 一次写入 -> 回读校验。
R14/GOAL/LOCK 是 CRLF（CR 数 == CRLF 数），BOARD 全 LF。
"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; TIER=LEAD+'/next_re_20261117_r14'; BASE=LEAD+'/R17_LEAD_BASELINE'
R14=TIER+'/R14_COMMON.md'; GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'
LOCK=LEAD+'/LEAD_LOCK'; BOARD=TIER+'/STATUS_BOARD.md'
def commit(path,newtext,exp_cr,tag,crlf=True):
    b=open(path,'rb').read()
    oldhead=b[:16]
    bak=BASE+'/'+os.path.basename(path)+'.before_r211_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    old_cr=b.count(b'\r')
    assert old_cr==exp_cr,(path,old_cr,exp_cr)
    add=newtext.encode('utf-8')          # 新节一律 LF 写入：CR 不变量只统计原文的 CR
    assert b'\r' not in add, 'new section must be pure LF'
    # 注意：变量 b 是旧文件内容，绝不可被覆盖（R211 事故根因即为 add 覆盖 b）
    sep=b'\n'
    orig=b
    assert orig[:16]==oldhead,('unexpected source content',orig[:16])
    nb=orig+add          # 纯追加：原文件逐字节不变，新节接在其后
    if not nb.endswith(sep): nb=nb+sep
    tmp=path+'.r211tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    chk=open(path,'rb').read()
    assert chk==nb
    # 新段本身按原文件行尾风格写入；校验「原有部分」CR 不变（新段所含 CR 不计入不变量）
    assert chk.startswith(orig), 'prefix changed'
    assert chk[:len(orig)]==orig, 'original bytes changed'
    assert len(chk)==len(orig)+len(add)+(0 if (orig+add).endswith(sep) else len(sep))
    assert b.count(b'\r')==exp_cr, ('orig CR drifted',b.count(b'\r'),exp_cr)
    print('OK %-24s %d -> %d B  CR %d (kept)  sha %s'%(
        os.path.basename(path),len(b),len(chk),chk.count(b'\r'),hashlib.sha256(chk).hexdigest()[:16]))
    return chk

R14_SEC = '''## 2.219 · R211（2026-11-28）· 律 W 定稿：视图偏移集合 V(c) 完全由 BCA 记录决定，954/954 零失配；R210 律 U 的 {4} 归约为接口 BCD 记录；HouseClass 反例是口径问题；V593

**一、🔴 律 W（954/954 零失配，两源同值）.** 定义 INTERFACE = pTD 名字以 .?AU 开头的类型描述符（实测 26 个）；TD_OWN = 954 个 own COL 记录（COL+16 处内嵌）的 pTD 集合。律：
V(c) == { mdisp(r) : r ∈ BCA(c), mdisp(r) != 0, pTD(r) ∈ INTERFACE ∪ TD_OWN }
左侧 V(c) 用**两条独立路径**重建并互校：①vftable 槽扫描（`_r209/q3.json` 的 mdisp 表）；②COL 记录扫描（同 pCHD 下全部 COL 记录的 mdisp 去 0）。两源逐类比对 **失配 0 / 954**，再各自对右侧比对均 **失配 0 / 954**。
等价式（第二判据）：条件可写成「pTD 名字不以 .?AV 开头 ∨ pTD ∈ TD_OWN」，同样 954/954 零失配。

**二、🔴 反控四项（说明判据不是碰巧）.** C0 不加任何 pTD 过滤（全部非零 mdisp）⇒ 失配 **15** 类；C1 只用「pTD ∈ TD_OWN」⇒ 失配 **91**；C2 只用「.?AU 前缀」⇒ 失配 **81**；C3 把全部 954 类 BCA 的非零 mdisp 并集（13 个偏移）套给每个类 ⇒ 成立 **0**。序列错位反控：用相邻 CHD 的 BCA 套本类 ⇒ 成立 0。

**三、🔴 被排除的 5 个 pTD（律 W 的判别力来源）.** C0 多出的 **26** 条 BCD 记录恰好只涉及 5 个 pTD，全部满足「名字以 .?AV 开头 ∧ 无任何 COL 记录引用（onlysec）」：
`0x817ab8 .?AVStageClass@@`（BCD 引用 9 次）、`0x817ad8 .?AVFlasherClass@@`（6）、`0x845e30 .?AVBounceClass@@`（1）、`0x84a838 .?AVCComObjectRootBase@ATL@@`（5）、`0x84a860 .?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL@@`（5）。
⇒ 律 W 的实质是：**只有「接口 pTD」与「有自己类表头的 pTD」才生成第二 vftable**；onlysec 的 .?AV 基类虽然被写进 BCA，但不生成视图。

**四、🔴 域分解与 R210 律 U 的归约（两域并集 == 律 W，零残留）.** 按 mdisp 值分域（沿用 R210 QS5 交叉表）：
T 域 mdisp ∈ {4,24,36,40,44,1728}：V_T(c) == { mdisp(r) : pTD 名 .?AU }，**954/954 零失配**；
S 域 mdisp ∈ {8,12,21784}：V_S(c) == { mdisp(r) : pTD ∈ TD_OWN ∧ 名 .?AV }，**954/954 零失配**；
V_T ∪ V_S == V(c) 逐类，**零残留**；I 域（既非 T 非 S）**0** 个。
⇒ **R210 律 U 的「{4} 是 QI 至少返回一个正偏移时附加的固定项」不再是独立规律**：{4} 就是 BCA 里那条 `mdisp=4` 的**接口** BCD 记录（`.?AUIRTTITypeInfo@@` 78 类 / `.?AUILocomotion@@` 12 类 / `.?AUILinkStream@@` 1 类 = 91 类）与伴记录 `.?AUIUnknown@@`(nc=0, attr=0x2) 的直接结果。mdisp=4 记录按 pTD 组合分组：IRTTITypeInfo+IUnknown **78** / ILocomotion+IUnknown **12** / CComObjectRootEx+CComObjectRootBase **5** / ILinkStream+IUnknown **1**，合计 **96** 类。
**R210「HouseClass 是唯一不匹配反例」是口径问题，不是反例**：HouseClass 的 V = `[4,8,12,36,40,44]`，其中 **8 / 12 属 S 域**（BCD 记录 pTD 为 `.?AVINoticeSink@@` / `.?AVINoticeSource@@`，属 TD_OWN 的 .?AV），不在律 U 的 T 域内；T 域恰为 `{4,36,40,44}`，与律 U 公式逐项一致。R210 把 V_all 当成律 U 的域才产生「唯一例外」。

**五、🟡 数据结构口径实测（供后续轮次复用）.** COL 记录 **1214** 条（`+0` sig∈{0,1,2}、`+4` mdisp、`+8` cdOffset 恒 0、`+12` pTD、`+16` pCHD；COL+16 处内嵌本类 own 记录）；CHD **954** 个（16 B：`+0` sig、`+4` attributes、`+8` numBaseClasses、`+12` pBCA）；BCA 元素 **2615** 条（元素是 **BCD 记录地址**，非 COL）；BCD 24 B 六字段为 `+0` pTD、`+4` numContainedBases、`+8` mdisp、`+12` pdisp、`+16` vdisp、`+20` attributes；BCA 中 mdisp≠0 的记录 **387** 条，COL 记录自身 mdisp≠0 的 **260** 条（两个口径禁互代）。`4∈V` 的类 **91**、`4∈B` 的类 **96**，差集 5 类全为 ATL EventSink（`0x80e680`/`0x80e740`/`0x80e780`/`0x80e7c0`/`0x80e998`）且 V 为空。
本段 X1/X2/X3 复算的**地址口径订正**：正文与卡片里出现的 `0x802a18` 等 8 个地址是 **CHD 键**（∉ COL），各类的 own COL 分别为 `0x802a28`/`0x7fb4c0`/`0x7ffeb0`/`0x8000a8`/`0x804cf0`/`0x809408`/`0x80c1e0`/`0x80d2a8`（= CHD+16）；mdisp=4 的**首记录（BCA 序在前）**是接口（IRTTITypeInfo / ILocomotion），**伴记录在后**是 `.?AUIUnknown@@`。

**六、🟡 跨家族（§2.12 规则 D 全部主会话复算）.** #542（hy4，9 回合 / **2.12'** vs 预算 8.0，无 OVERTIME）12/12 PASS，并独立指出「G1 的两个非零口径」为 387（BCA）/260（COL），主会话 d1 复算确认。#543（deepseek，`audit` 只读，落 `_r211/audit_deepseek.json`）12/12 PASS，另提两条**字面订正**：①8 个地址是 CHD 不是 COL；②「第二记录」按 BCA 物理序应为 IUnknown 而非接口。两条经 d2 复算**全部成立**并已在本段采纳（见五）。主会话 §2.12 规则 D 复算 **29 断言 0 FAIL**（d1 25 条 + d2 4 条）。

**七、📌 自错 5 组（0 条进结论）.** ①`c3` 把 BCA 元素当 COL 记录查 mdisp（实为 BCD 记录地址）⇒ 954 类全报 B 集为空，判定「律 W 不成立」；②`c4` 按 R207 代码沿用 `pCHD=COL+16` 之外又误取 `+12` 为 pCHD（`+12` 是 pTD，`+16` 才是 pCHD）⇒ 首轮读出一堆 `pdisp` 当 mdisp；③`c8` 先验「extras 的 pTD 都不在 TD_OWN」⇒ 律 W'（只筛 TD_OWN）失配 91，说明 mdisp=4 的**接口**记录 pTD 也不在 TD_OWN，该先验作废；④`c9` 机械搜索里把 `tdown` 当独立充分条件期望 PERFECT，实测 91 失配；⑤`p1` 首次把正文追加到第 2 列（[已证] 列）而非第 5 列，且逐行校验基准取被原地改写的 `lines` 而非 `ORIG` ⇒ 两次 AssertionError，已修正。

**八、🟡 落盘与门禁.** R14_COMMON 本段 **§2.219** CR 保持 **1081**；GOAL **§1269** CR 保持 **337**；LEAD_LOCK **QT** CR 保持 **137**；STATUS_BOARD 第 211 轮 CR 保持 **0**（开局 **264 行 >= 260** ⇒ 先把最早 2 段归档到 BOARD_ARCHIVE，归档 CR 保持 **2952**，归档后看板 225 行）。**FACT_INDEX V592→V593**：把律 W 全量写入 F29 第 5 列正文（其余 55 行逐字节不变；57 行 / 5 列 / grade 与第 4 列全同），sha `b3327fd4`→**`1f6fe2af`**、249545→**251275** B（+1730）；指针 + facts_floors（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER `519ee33a`→**`ae756204`**）+ gate_runner LEDGER 同步重钉 V593。C16_FLOORS 纳入 §2.219（unpinned 0 / hollow 0 / missing 0）。
'''

GOAL_SEC = '''## §1269 · R211（2026-11-28）· 律 W：视图偏移集合 V(c) == {BCA 中 pTD 名 .?AU 或 pTD∈TD_OWN 的非零 mdisp}，954/954 零失配；R210 律 U 的 {4} 归约为接口 BCD 记录；HouseClass「唯一反例」为口径问题；FACT_INDEX V593

**一、🔴 律 W 定稿.** INTERFACE = pTD 名以 .?AU 开头的类型描述符（26 个）；TD_OWN = 954 个 own COL 的 pTD 集合。
V(c) == { mdisp(r) : r ∈ BCA(c), mdisp(r)≠0, pTD(r) ∈ INTERFACE ∪ TD_OWN }，**954/954 零失配**。
V 用两条独立路径重建并互校：vftable 槽扫描 与 COL 记录扫描，**两源逐类失配 0**，各自对右侧也失配 0。
等价式「pTD 名不以 .?AV 开头 ∨ pTD ∈ TD_OWN」同样零失配。

**二、🔴 反控.** 无过滤失配 15；仅 TD_OWN 失配 91；仅 .?AU 失配 81；全量并集（13 个偏移）套各类成立 0；相邻 CHD 错位套用成立 0。

**三、🔴 判别力来源 = 5 个 onlysec pTD.** C0 多出的 26 条 BCD 记录只涉及 5 个 pTD，全部是「.?AV 前缀 ∧ 无 COL 引用」：
`0x817ab8 ?AVStageClass`、`0x817ad8 ?AVFlasherClass`、`0x845e30 ?AVBounceClass`、`0x84a838 ?AVCComObjectRootBase@ATL`、`0x84a860 ?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL`。
⇒ 只有「接口 pTD」和「有自己类表头的 pTD」才生成第二 vftable；onlysec 的 .?AV 基类虽写进 BCA 却不生成视图。

**四、🔴 域分解（并集 == 律 W，零残留）.** T 域（mdisp ∈ {4,24,36,40,44,1728}）V_T == {.?AU 记录的 mdisp}，954/954；S 域（{8,12,21784}）V_S == {TD_OWN 且 .?AV 记录的 mdisp}，954/954；I 域 0 个。
⇒ **律 U 的 {4} 归约**：{4} 来自 mdisp=4 的接口 BCD 记录（`?AUIRTTITypeInfo` 78 类 / `?AUILocomotion` 12 / `?AUILinkStream` 1 = 91 类）+ 伴记录 `?AUIUnknown`(nc=0,attr=0x2)。mdisp=4 按 pTD 组合分组 78/12/5/1 = 96 类。
⇒ **HouseClass 不是反例**：其 V=[4,8,12,36,40,44]，8/12 属 S 域（`?AVINoticeSink`/`?AVINoticeSource`），T 域恰 {4,36,40,44}，与律 U 逐项一致；R210 把 V_all 当律 U 域才产生「唯一例外」。

**五、🟡 结构口径与地址订正.** COL 1214（+0 sig / +4 mdisp / +8 cdOffset 恒 0 / +12 pTD / +16 pCHD；COL+16 内嵌 own）；CHD 954（16 B：sig / attributes / numBaseClasses / pBCA）；BCA 元素 2615（是 BCD 记录地址）；BCD 24 B（+0 pTD / +4 nc / +8 mdisp / +12 pdisp / +16 vdisp / +20 attributes）；BCA 非零 mdisp 387 条 vs COL 自身非零 260 条（禁互代）。`4∈V` 91 类、`4∈B` 96 类，差 5 类全为 ATL EventSink 且 V 空。
**订正**：`0x802a18` 等 8 个地址是 **CHD 键**，各类 own COL = CHD+16（`0x802a28`/`0x7fb4c0`/`0x7ffeb0`/`0x8000a8`/`0x804cf0`/`0x809408`/`0x80c1e0`/`0x80d2a8`）；mdisp=4 的 BCA 序首记录是接口、伴记录是 `?AUIUnknown`。

**六、🟡 跨家族与落盘.** #542（hy4，9 回合 / 2.12'，无 OVERTIME）12/12 PASS；#543（deepseek，只读）12/12 PASS 并提两条字面订正（CHD≠COL、伴记录次序），经 d2 复算成立已采纳。主会话 §2.12 规则 D **29 断言 0 FAIL**（d1 25 + d2 4）。FACT_INDEX **V592→V593**（F29 第 5 列写入律 W，sha `b3327fd4`→`1f6fe2af`、249545→**251275** B），指针/facts_floors（MASTER `519ee33a`→`ae756204`）/gate_runner LEDGER 同步重钉；C16_FLOORS 纳入 §2.219。看板开局 264 行 ≥260 ⇒ 归档最早 2 段至 BOARD_ARCHIVE（CR 保持 2952），归档后 225 行。
'''

LOCK_SEC = '''## QT · R211（2026-11-28）· 律 W：视图偏移集合 V(c) == {BCA 中 pTD 名 .?AU ∨ pTD∈TD_OWN 的非零 mdisp}，954/954 零失配（两源互校）；R210 律 U 的 {4} 归约为接口 BCD 记录；HouseClass「唯一反例」= 口径问题（8/12 属 S 域）；V593

**QT1. 🔴 律 W（954/954 零失配）.** INTERFACE = pTD 名 `.?AU` 前缀（26 个）；TD_OWN = 954 个 own COL 的 pTD 集合。
V(c) == { mdisp(r) : r ∈ BCA(c), mdisp(r) ≠ 0, pTD(r) ∈ INTERFACE ∪ TD_OWN }。
V 重建两条独立路径：①`_r209/q3.json` vftable 槽扫描；②同 pCHD 下全部 COL 记录 mdisp 去 0。**两源逐类失配 0/954**，各自对右侧亦失配 0/954。等价式「¬.?AV ∨ TD_OWN」零失配。

**QT2. 🔴 反控四项.** C0 无过滤失配 **15**；C1 仅 TD_OWN 失配 **91**；C2 仅 `.?AU` 失配 **81**；C3 全量并集（13 偏移）套各类成立 **0**；相邻 CHD 错位套用成立 **0**。

**QT3. 🔴 判别力来源 = 5 个 onlysec pTD.** C0 的 26 条多余记录只涉及这 5 个（全 `.?AV` ∧ 无 COL 引用）：
`0x817ab8 .?AVStageClass@@`(BCD 9) / `0x817ad8 .?AVFlasherClass@@`(6) / `0x845e30 .?AVBounceClass@@`(1) / `0x84a838 .?AVCComObjectRootBase@ATL@@`(5) / `0x84a860 .?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL@@`(5)。
⇒ **只有「接口 pTD」与「有自己类表头的 pTD」生成第二 vftable**；onlysec 的 `.?AV` 基类写进 BCA 但不生成视图。

**QT4. 🔴 域分解与律 U 归约.** T 域 mdisp ∈ {4,24,36,40,44,1728}：V_T == {`.?AU` 记录的 mdisp} **954/954**；S 域 {8,12,21784}：V_S == {TD_OWN ∧ `.?AV` 记录的 mdisp} **954/954**；并集 == V 逐类零残留；I 域 **0**。
⇒ **{4} 不是独立附加项**：它来自 mdisp=4 的接口 BCD 记录（`?AUIRTTITypeInfo` 78 / `?AUILocomotion` 12 / `?AUILinkStream` 1 = 91 类）+ 伴记录 `?AUIUnknown`(nc=0,attr=0x2)。mdisp=4 分组：IRTTITypeInfo+IUnknown **78** / ILocomotion+IUnknown **12** / CComObjectRootEx+CComObjectRootBase **5** / ILinkStream+IUnknown **1** = **96** 类。
⇒ **HouseClass 不是反例**：V=[4,8,12,36,40,44]，其中 8/12 属 S 域（`?AVINoticeSink`/`?AVINoticeSource`），T 域恰 `{4,36,40,44}`，与律 U 公式逐项一致。R210 QS3 的「唯一不匹配」措辞本段**订正为口径问题**。

**QT5. 🟡 结构口径实测 + 地址订正.** COL **1214**（+0 sig∈{0,1,2} / +4 mdisp / +8 cdOffset 恒 0 / +12 pTD / +16 pCHD；COL+16 内嵌 own）、CHD **954**（16 B：sig/attributes/numBaseClasses/pBCA）、BCA 元素 **2615**（是 BCD 记录地址）、BCD 24 B（+0 pTD / +4 nc / +8 mdisp / +12 pdisp / +16 vdisp / +20 attributes）；BCA 非零 mdisp **387** vs COL 自身非零 **260**（两口径禁互代）。`4∈V` **91** / `4∈B` **96**，差 5 类全为 ATL EventSink（`0x80e680`/`0x80e740`/`0x80e780`/`0x80e7c0`/`0x80e998`）且 V 空。
**订正两条**：①`0x802a18` 等 8 个地址是 **CHD 键**（∉ COL），own COL = CHD+16：`0x802a28`/`0x7fb4c0`/`0x7ffeb0`/`0x8000a8`/`0x804cf0`/`0x809408`/`0x80c1e0`/`0x80d2a8`；②mdisp=4 的 **BCA 序首记录是接口**、**伴记录在后是 `.?AUIUnknown@@`**（House 索引 5/6、Aircraft 10/11，其余 5/6）。

**QT6. 🟡 跨家族（§2.12 规则 D 全复算）.** #542（hy4，9 回合 / **2.12'** vs 8.0，无 OVERTIME）12/12 PASS，并补「387(BCA) / 260(COL) 两非零口径」。#543（deepseek，`audit` 只读，落 `_r211/audit_deepseek.json`）12/12 PASS，提两条字面订正（CHD≠COL、「第二记录」按 BCA 序应为 IUnknown），经 d2 **全部成立并采纳**。主会话 **29 断言 0 FAIL**（d1 25 / d2 4）。

**QT7. 📌 自错 5 组（0 条进结论）.** ①`c3` 把 BCA 元素当 COL 记录取 mdisp（实为 BCD 地址）⇒ B 集全空、误判律 W 不成立；②`c4` 误取 `COL+12` 当 pCHD（`+12` 是 pTD、`+16` 才是 pCHD）；③`c8` 先验「extras pTD 都不在 TD_OWN ⇒ 只筛 TD_OWN 即 PERFECT」⇒ 实测失配 91，先验作废；④`c9` 把 `tdown` 当独立充分条件期望 PERFECT ⇒ 91 失配；⑤`p1` 正文追加到第 2 列而非第 5 列，且逐行校验基准取被原地改写的 `lines` ⇒ 两次 AssertionError。

**QT8. 🟡 落盘与门禁.** R14_COMMON **§2.219** CR 保持 **1081**；GOAL **§1269** CR 保持 **337**；本段 **QT** CR 保持 **137**；STATUS_BOARD 第 211 轮 CR 保持 **0**（开局 **264 行 ≥ 260** ⇒ 归档最早 2 段，归档后 **225 行**，BOARD_ARCHIVE CR 保持 **2952**）。**FACT_INDEX V592→V593**：F29 第 5 列写入律 W（其余 55 行逐字节不变），sha `b3327fd4`→**`1f6fe2af`**、249545→**251275** B；指针 + facts_floors（MASTER `519ee33a`→**`ae756204`**）+ gate_runner LEDGER 重钉 V593。C16_FLOORS 纳入 §2.219。

**QT9. ⚪ 未取得.** ①37 个 onlysec pTD 里其余 32 个（非 `.?AV` 前缀或未被 BCA 引用者）的生成规则；②`?AUIUnknown` 伴记录 `attr=0x2` 的位义（仍须 win-main 动态）；③S 域 21784（Mouse/Tab/Scroll）的 `0x11c7`/`0x11c8` 语义；④T 域 91 类与 96 类差 5 的 ATL EventSink 为何不生成视图（结构性无 vs 丢失）；⑤主视图 9958 个 slot≥3 槽语义归属；⑥F23/F35 grade（两 tsv 不可读，禁预估回填）；⑦C7 三死分支、C11 十二 ID。
'''

BOARD_SEC = '''## 🟢 R17 第 211 轮（2026-11-28）· 律 W 定稿：视图偏移集合 V(c) 完全由 BCA 记录决定（954/954 零失配，两源互校）；R210 律 U 的 {4} 归约为接口 BCD 记录；HouseClass「唯一反例」= 口径问题；V593

**取得（1 律 + 1 归约 + 2 订正）.** ①🔴 **律 W（954/954 零失配）**：INTERFACE = pTD 名以 `.?AU` 开头的类型描述符（26 个），TD_OWN = 954 个 own COL 的 pTD 集合；**V(c) == { mdisp(r) : r ∈ BCA(c), mdisp≠0, pTD(r) ∈ INTERFACE ∪ TD_OWN }**。V 用两条独立路径重建（`_r209/q3.json` vftable 槽扫描 / 同 pCHD 下全部 COL 记录 mdisp），**两源逐类失配 0**，各自对右侧也失配 0；等价式「¬`.?AV` ∨ TD_OWN」同样零失配。②🔴 **反控**：无过滤失配 **15** / 仅 TD_OWN **91** / 仅 `.?AU` **81** / 全量并集（13 偏移）套各类成立 **0** / 相邻 CHD 错位套用成立 **0**。③🔴 **判别力来源 = 5 个 onlysec pTD**：C0 多出的 **26** 条 BCD 记录只涉及 `0x817ab8 ?AVStageClass`(9) / `0x817ad8 ?AVFlasherClass`(6) / `0x845e30 ?AVBounceClass`(1) / `0x84a838 ?AVCComObjectRootBase@ATL`(5) / `0x84a860 ?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL`(5)，全部「`.?AV` 前缀 ∧ 无 COL 引用」⇒ **只有接口 pTD 与有自己类表头的 pTD 才生成第二 vftable**。④🔴 **域分解 + 律 U 归约（零残留）**：T 域（{4,24,36,40,44,1728}）V_T == {`.?AU` 记录 mdisp} **954/954**；S 域（{8,12,21784}）V_S == {TD_OWN ∧ `.?AV` 记录 mdisp} **954/954**；并集 == V 逐类、I 域 **0**。⇒ **{4} 不是独立附加项**，它来自 mdisp=4 的接口记录（`?AUIRTTITypeInfo` 78 / `?AUILocomotion` 12 / `?AUILinkStream` 1 = 91 类）+ 伴记录 `?AUIUnknown`(nc=0,attr=0x2)；mdisp=4 分组 **78/12/5/1 = 96** 类。⑤🔴 **HouseClass 不是反例**：V=[4,8,12,36,40,44]，8/12 属 S 域（`?AVINoticeSink`/`?AVINoticeSource`），T 域恰 `{4,36,40,44}`，与律 U 逐项一致 —— R210 QS3「唯一不匹配」为**口径问题**。⑥🟡 **结构口径**：COL 1214（+0 sig/+4 mdisp/+8 cdOffset 恒 0/+12 pTD/+16 pCHD；COL+16 内嵌 own）、CHD 954、BCA 元素 2615（是 BCD 记录地址）、BCD 24 B；BCA 非零 mdisp **387** vs COL 自身非零 **260**（禁互代）；`4∈V` 91 / `4∈B` 96，差 5 类全为 ATL EventSink 且 V 空。

**订正两条（跨家族指出，主会话复算成立）.** ①`0x802a18` 等 8 个地址是 **CHD 键**（∉ COL），own COL = CHD+16（`0x802a28`/`0x7fb4c0`/`0x7ffeb0`/`0x8000a8`/`0x804cf0`/`0x809408`/`0x80c1e0`/`0x80d2a8`）；②mdisp=4 的 **BCA 序首记录是接口**、**伴记录是 `.?AUIUnknown@@``**（House 5/6、Aircraft 10/11、其余 5/6）。

**跨家族（§2.12 规则 D 全复算）.** #542（hy4，`audit`，9 回合 / **2.12'** vs 预算 8.0，无 OVERTIME）**12/12 PASS**，并补充「387 / 260 两非零口径」。#543（deepseek，`audit` 只读，落 `_r211/audit_deepseek.json`）**12/12 PASS**，另提两条字面订正（CHD≠COL、「第二记录」按 BCA 序应为 IUnknown），经 d2 复算**全部成立并采纳**。主会话 §2.12 规则 D **29 断言 0 FAIL**（d1 25 / d2 4）。

**自错 5 组（0 条进结论）.** ①`c3` 把 BCA 元素当 COL 记录取 mdisp（实为 BCD 地址）⇒ 954 类 B 集全空、误判律 W 不成立；②`c4` 误取 `COL+12` 当 pCHD（`+12` 是 pTD、`+16` 才是 pCHD）；③`c8` 先验「extras pTD 都不在 TD_OWN ⇒ 只筛 TD_OWN 即 PERFECT」实测失配 91；④`c9` 把 `tdown` 当独立充分条件期望 PERFECT ⇒ 91 失配；⑤`p1` 正文追加到第 2 列而非第 5 列、逐行校验基准取被原地改写的 `lines` ⇒ 两次 AssertionError。

**落盘与门禁.** R14_COMMON **§2.219** CR 保持 **1081**；GOAL **§1269** CR 保持 **337**；LEAD_LOCK **QT** CR 保持 **137**；本段 CR 保持 **0**（开局 **264 行 ≥ 260** ⇒ 先归档最早 2 段至 BOARD_ARCHIVE，归档 CR 保持 **2952**，归档后 **225 行**）。**FACT_INDEX V592→V593**：律 W 写入 F29 第 5 列正文（其余 55 行逐字节不变；57 行 / 5 列），sha `b3327fd4`→**`1f6fe2af`**、249545→**251275** B（+1730）；指针 + facts_floors（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER `519ee33a`→**`ae756204`**）+ gate_runner LEDGER 同步重钉 V593。C16_FLOORS 纳入 §2.219（unpinned 0 / hollow 0 / missing 0）。三门待收口复跑。

**⚪ 未取得.** ①37 个 onlysec pTD 里其余 32 个的生成规则；②`?AUIUnknown` 伴记录 `attr=0x2` 位义（须 win-main）；③S 域 21784（Mouse/Tab/Scroll）的 `0x11c7`/`0x11c8` 语义；④5 个 ATL EventSink 不生成视图是结构性无还是丢失；⑤主视图 9958 个 slot≥3 槽语义归属；⑥F23/F35 grade（两 tsv 不可读）；⑦C7 三死分支、C11 十二 ID。
'''

commit(GOAL,GOAL_SEC,337,'goalc')
commit(LOCK,LOCK_SEC,137,'lockc')
commit(BOARD,BOARD_SEC,0,'boardc',crlf=False)
print('\nall four written')
