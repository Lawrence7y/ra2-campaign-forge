# -*- coding: utf-8 -*-
"""R212 p5：四件套（R14 §2.220 / GOAL §1270 / LEAD_LOCK QU / BOARD 第 212 轮）。
每处：wx 独占备份 -> 断言旧 CR -> 纯 LF 追加 -> 回读校验 -> 原前缀逐字节不变。
"""
import os,hashlib
ROOT='/home/t628/projects/ra2-campaign-forge'
LEAD=ROOT+'/lead'; TIER=LEAD+'/next_re_20261117_r14'; BASE=LEAD+'/R17_LEAD_BASELINE'
R14=TIER+'/R14_COMMON.md'; GOAL=LEAD+'/GOAL_THREE_TARGETS_20261018.md'
LOCK=LEAD+'/LEAD_LOCK'; BOARD=TIER+'/STATUS_BOARD.md'

def commit(path,newtext,exp_cr,tag):
    b=open(path,'rb').read()
    bak=BASE+'/'+os.path.basename(path)+'.before_r212_%s_20261128.bak'%tag
    fd=os.open(bak,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o644); os.write(fd,b); os.close(fd)
    assert open(bak,'rb').read()==b
    old_cr=b.count(b'\r')
    assert old_cr==exp_cr,(path,old_cr,exp_cr)
    add=newtext.encode('utf-8')
    assert b'\r' not in add,'new section must be pure LF'
    nb=b+add
    if not nb.endswith(b'\n'): nb=nb+b'\n'
    tmp=path+'.r212tmp'; open(tmp,'wb').write(nb); os.replace(tmp,path)
    chk=open(path,'rb').read()
    assert chk==nb
    assert chk[:len(b)]==b,'original bytes changed'
    assert chk.count(b'\r')==exp_cr,('CR drifted',chk.count(b'\r'))
    print('OK %-26s %d -> %d B  CR %d (kept)  sha %s'%(
        os.path.basename(path),len(b),len(chk),chk.count(b'\r'),hashlib.sha256(chk).hexdigest()[:16]))
    return chk

R14_SEC = '''## 2.220 · R212（2026-11-28）· S 域 mdisp 8/12 接口身份定案：?AVINoticeSink@@(8) / ?AVINoticeSource@@(12) 各 78 条、两偏移同批 78 类、8 恒紧邻 12 之前；ATL EventSink 空视图 = 律 W 全过滤（非丢失）；V595

**一、🔴 S 域 mdisp=8 / =12 的接口身份（此前 5 轮列为未取得）.** 按 BCD 24 B 结构（`+0` pTD / `+4` nc / `+8` mdisp / `+12` pdisp / `+16` vdisp / `+20` attributes）解析 BCA 元素后实测：
mdisp==8 的 BCA 记录恰 **78** 条，pTD **全部**为 `.?AVINoticeSink@@`（TD 址 `0x816b50`）；mdisp==12 恰 **78** 条，pTD **全部**为 `.?AVINoticeSource@@`（TD 址 `0x8177e8`）。两者去重名各 **1** 个，无第二个 pTD 混入。
二者均 **∈ TD_OWN**（954 个 own COL 的 pTD 集合）且均 **∉ INTERFACE**（26 个 `.?AU` 类型描述符）⇒ **S 域两偏移来自「本类自己的类 TD」，与 T 域来自接口 BCD 的机制不同源**，这解释了 R211 律 W 分域判据为何要用 `TD_OWN ∧ .?AV`。
78 条记录的 `(nc, pdisp, vdisp, attributes)` **全为 (0, -1, 0, 0)**，78/78 无例外。

**二、🔴 BCA 中的位置规律（相对固定、绝对不固定）.** 含 8 的类集合与含 12 的类集合**完全相同**（各 78 类，对称差 **0/0**）。
相对位置：`idx(8) − idx(12)` 分布恒为 **{−1: 78}** ⇒ **8 记录恒紧邻 12 记录之前**，78/78 无一多值类。
绝对位置**不固定**：8 的 BCA 索引跨度 **6..12**，12 的跨度 **7..13**，随继承深度变化；8 距 BCA 末尾的记录数分布 `{1:67, 2:4, 3:5, 5:1, 7:1}` ⇒ 不占据固定的首部或尾部槽位。
反控：BCA 索引 0 记录的 mdisp **恒 0**（954/954），8/12 恒不在索引 0，即两者恒排在本类 own 记录之后。

**三、🔴 vftable 字节侧独立复算（不经 mdisp 推导）.** 直读槽表：78 类中 8 与 12 的视图 **slot0 落点全部异址**（同 0 / 异 78），两视图**槽数均为 1**（单槽接口表，78/78）。
8 视图 slot0 落点分布 `{0x410580: 75, 0x41bc30: 1, 0x522a60: 1, 0x746100: 1}`；12 视图 slot0 落点 `0x410590` 被 78 类**全部共享**。
函数体字节：`0x410580` = `xor al, al ; ret 8`（共 2 条指令，**无条件返回 false**、清 2 个 dword 参数）；`0x410590` = `ret 4`（首指令即 ret，清 1 个 dword 参数；其后 nop 填充与 `0x4105a0` 起的独立函数，非本函数体）。
两地址在全 `.text` 线性扫描（`disasm_lite`，未开 detail）下被直接 call/jmp 命中 **0** 次 ⇒ 纯虚调用入口，无静态直调路径。

**四、🔴 mdisp=8 槽的双形态：75 类共享桩 + 3 类真实现.** 上述 3 个独占落点 `0x41bc30`（AircraftClass）/ `0x522a60`（InfantryClass）/ `0x746100`（UnitClass）为真函数体，体内均含 `lea esi, [edi-8]` 的 this 调整与 `cmp ebx, 0x117b`。
⇒ 从 S 域视角**再得一次独立确认** R208 已证的 I 域三形态：mdisp=8 槽在这 3 个 I 域类里由真实现取代共享桩，其余 75 类用共享桩。两个口径（T/S/I 互斥的 I 域 = 3，S 域 8 槽的独占落点 = 3）**指向同一批类**。

**五、🔴 5 个 ATL EventSink 空视图 = 律 W 全过滤，非丢失.** CHD `0x80e680` / `0x80e740` / `0x80e780` / `0x80e7c0` / `0x80e998`，NB = 6/6/5/5/6。
其 BCA **非零 mdisp 记录各 2 条**，pTD 恒为 `.?AV?$CComObjectRootEx@VCComMultiThreadModel@ATL@@@ATL@@`(mdisp=4, nc=1) 与 `.?AVCComObjectRootBase@ATL@@`(mdisp=4, nc=0)。两者均 **onlysec**（既 ∉ INTERFACE 亦 ∉ TD_OWN）⇒ 律 W 得空集，与实测空视图**逐类一致 5/5**。
判别力证据：若不做 pTD 过滤，这 5 类会得 `{4}`（反控实测 5/5 非空）⇒ **空视图的成因是 pTD 归属过滤，不是「记录缺失」**；律 W 在此处有真实判别作用而非平凡满足。

**六、🟡 S3(mdisp=21784) 与 S2(mdisp=8) 同 pTD 交叉.** mdisp==21784 的 3 条记录 pTD **亦为** `.?AVINoticeSink@@`（与 mdisp=8 同源），attributes 恒 **9**（区别于 mdisp=8 的 0），对应类 MouseClass(`0x7fab28`, idx=11) / TabClass(`0x805e90`, idx=9) / ScrollClass(`0x809050`, idx=10)，三类均**不含** mdisp=8/12 记录。
⇒ 同一个类 TD 在不同类里被以 8 或 21784 两种偏移引用，且 21784 记录带 attributes=9 而 8 记录带 0，**两口径禁互代**。

**七、🟡 判据订正（本轮自错根因）.** INTERFACE 集合**必须**由 pTD 所指向 TD 的内联名（TD+8）判定（全域得 **26** 个 `.?AU`）；**不可**由 COL 记录自带的名字判定（那样只得 **2** 个，且使律 W 失配 **91** 类）。本轮实测该错判据的失配数恰为 **91**，与 R211 `c8`/`c9` 的 91 同值 —— 同一个 91 有两个不同成因，禁互相引用为证据。

**八、🟡 跨家族（§2.12 规则 D 全部主会话复算）.** #545（deepseek，`audit` 只读，22 回合 / **4.47'** vs 预算 8.0，无 OVERTIME）**12/12 PASS**，并提两条订正与三条口径限制，全部经 `_r212/d1_recheck.py` 复算成立：
①**卡面 A8 括注方向写反**（我写「8 紧跟 12 之后/索引更大」，实测 `idx(8) − idx(12)` 恒 −1，即 8 在 BCA 中**先于** 12）；落盘正文方向一直正确，此条只订正卡面。旁证：78 对的 BCD 地址差 `b8 − b12` 恒 **+24**（78/78），与 R204 S2b「BCA 次序逆序于 BCD 数组次序」一致。
②**「988」与「954」是两把尺**：988 = RTTI TD 全池（`.?AV` 962 / `.?AU` 26），954 = COL 引用 distinct pTD 池，且 **TD_OWN == COL 引用池（954/954 相等）**；律 W 的 INTERFACE 项须取**全池 26**（COL 池里只有 2 个 `.?AU`：`?AUINIEntry@INIClass`/`?AUINISection@INIClass`）。实测三种写法（名字前缀 / 全池 26 / 实载 9）给出**相同失配 0**，反控三数亦同：无过滤 **94** / 仅 TD_OWN **91** / 仅 INTERFACE **81**。
③**律 W 零失配含大量平凡项**：V 空 **860**、载非零记录 **99**；其中 V 空 ∧ 无非零 = **855**（两侧都空、自动一致）、V 空 ∧ 载非零 = **5**、V 非空 ∧ 载非零 = **94**（律 W 真正吃力的部分）、V 非空 ∧ 无非零 = **0**。⇒ 855/954 = **89.6% 平凡满足**，不得当作 954 类强区分力证据。
④全池 2615 条记录 `pdisp` 恒 −1、`vdisp` 恒 0 ⇒ 四元组中实际只有 nc 与 attributes 两位有区分力。
⑤补充数字：`attributes==9` 全局 **6** 条，除 S3 三条外另三条为 `?AV?$VectorClass@H@@`(`0x7ff680`, mdisp=0) / `?AVINoticeSource@@`(`0x808170`, mdisp=0) / `?AVStageClass@@`(`0x800600`, mdisp=36) ⇒ attr=9 **不专属** S3 三表。∈全池但 ∉(INTERFACE∪TD_OWN) 的 TD 共 **10** 个，其中 **5** 个被 BCA 实载共 **26** 条，另 5 个零命中（`?AVDiskSwap` / `?$Node@PAUINIEntry@INIClass@@` / `?$Node@PAVMixFileClass@@` / `?$DynamicVectorClass@W4DiskID@@` / `?AVCDownloadEventSink`）。
主会话 §2.12 规则 D 复算 **12 断言 0 FAIL**。

**九、📌 自错 4 组（0 条进结论）.** ①`c1` 沿用 R211 的 COL 类头判据去解析 **BCA 元素**（元素是 BCD 记录，`+4` 是 nc 不是 mdisp）⇒ 5 个 sink 全部报 MISSING、mdisp=8/12 记录一条不命中，误得「8/12 不在任何 BCA 里」；②`c2` 的 INTERFACE 用「COL 记录自带名字」判 ⇒ 只得 2 个 `.?AU`，律 W 失配 91（同一错型第三次复发）；③`c3` 断言「8 恒紧邻 12 之后（差恒 +1）」方向写反，实测 −1；④`c4`/`d1` 三次类型错（`own[a]['name']` 对 CHD 键取 own 记录、`nz-set(emp)` 对 list 做差、`VS[...]` 返回 dict 却与 set `{0}` 比较）。

**十、🟡 落盘与门禁.** R14_COMMON 本段 **§2.220** CR 保持 **1081**；GOAL **§1270** CR 保持 **337**；LEAD_LOCK **QU** CR 保持 **137**；STATUS_BOARD 第 212 轮 CR 保持 **0**（开局 **238 行 < 260**，**不归档**）。**FACT_INDEX V593→V595**（V594 为 S 域正文本，V595 补入 §八 的五条口径限制与卡面订正）：F29 第 5 列两次追加，其余 **57 行逐字节不变**（57 行 / 5 列），sha `1f6fe2af`→`184e2c74`→**`9ffc56c9`**、251275→254880→**257435** B；指针 + facts_floors（EXPECT_CUR / CUR_SHA256 / TOTAL_BYTES / MASTER `ae756204`→`a692adcc`→**`835e4388`**）同步重钉 V595。
'''

GOAL_SEC = '''## §1270 · R212（2026-11-28）· S 域 8/12 接口身份：?AVINoticeSink@@ / ?AVINoticeSource@@（各 78 条，8 恒在 12 之前）；空视图 = 律 W 全过滤；S3 与 S2 同 pTD；V595

**一、🔴 S 域 mdisp=8/12 身份定案.** 按 BCD 24 B 结构解析 BCA：mdisp==8 记录 **78** 条、pTD 全为 `.?AVINoticeSink@@`(`0x816b50`)；mdisp==12 **78** 条、pTD 全为 `.?AVINoticeSource@@`(`0x8177e8`)。各仅 **1** 个去重名。
两者 **∈ TD_OWN**、**∉ INTERFACE** ⇒ **来自本类自己的类 TD，与 T 域来自接口 BCD 不同源**。78 条 `(nc,pdisp,vdisp,attributes)` 全为 `(0,-1,0,0)`。

**二、🔴 位置规律.** 含 8 与含 12 的类集合**相同**（各 78，对称差 0/0）。相对：`idx(8) − idx(12)` 恒 **−1**（78/78）⇒ **8 恒紧邻 12 之前**。绝对**不固定**：8 跨度 **6..12**、12 跨度 **7..13**；8 距末尾分布 `{1:67,2:4,3:5,5:1,7:1}`。反控：索引 0 的 mdisp 恒 0（954/954），8/12 恒不在索引 0。

**三、🔴 vftable 字节侧复算.** 78 类的 8 与 12 视图 **slot0 落点全部异址**（同 0 / 异 78），两视图**槽数均为 1**。8 视图落点 `{0x410580:75, 0x41bc30:1, 0x522a60:1, 0x746100:1}`；12 视图落点 `0x410590` 被 78 类全共享。
字节：`0x410580` = `xor al,al ; ret 8`（2 条指令、无条件 false、清 2 dword）；`0x410590` = `ret 4`（首指令即 ret，清 1 dword）。两址被 `.text` 直接 call/jmp 命中 **0** 次（纯虚入口）。

**四、🔴 mdisp=8 双形态.** 独占落点 3 个（`0x41bc30` Aircraft / `0x522a60` Infantry / `0x746100` Unit）为真函数体，体内含 `lea esi,[edi-8]` 与 `cmp ebx,0x117b` ⇒ 从 S 域再证 R208 的 I 域三形态：3 个 I 域类用真实现取代共享桩，其余 75 类共享桩。两口径指向同一批类。

**五、🔴 EventSink 空视图 = 律 W 全过滤.** CHD `0x80e680`/`0x80e740`/`0x80e780`/`0x80e7c0`/`0x80e998`，NB 6/6/5/5/6，非零 mdisp 记录各 **2** 条，pTD 恒为 `?$CComObjectRootEx@VCComMultiThreadModel@ATL@@`(4,nc=1) 与 `CComObjectRootBase@ATL@@`(4,nc=0)，两者均 onlysec ⇒ 律 W 空集，与空视图 **5/5 一致**。反控：不做 pTD 过滤会得 `{4}`（5/5 非空）⇒ 空视图成因是过滤而非记录缺失。

**六、🟡 S3/S2 同 pTD 交叉.** mdisp==21784 的 3 条 pTD **亦为** `?AVINoticeSink@@`，attributes 恒 **9**（8 记录为 0），对应 MouseClass/TabClass/ScrollClass，三类均不含 8/12 ⇒ **同一 TD 在 8 与 21784 两种偏移被引用，禁互代**。

**七、🟡 判据订正.** INTERFACE **必须**由 pTD 所指向 TD 的内联名判定（全域 **26** 个 `.?AU`），**不可**由 COL 记录自带名字判定（只得 **2** 个、律 W 失配 **91**）。该 91 与 R211 `c8`/`c9` 的 91 **成因不同**，禁互为证据。

**八、🟡 跨家族与落盘.** #545（deepseek，audit 只读，22 回合 / 4.47'，无 OVERTIME）**12/12 PASS**，两条订正（卡面 A8 方向写反；988/954 两把尺）与三条口径限制（855/954 平凡满足、pdisp/vdisp 恒定、attr=9 不专属）经 d1 复算**全部成立并采纳**。主会话 §2.12 规则 D **12 断言 0 FAIL**。FACT_INDEX **V593→V595**（S 域正文本 + 口径限制列），sha `1f6fe2af`→**`9ffc56c9`**、251275→**257435** B；指针/facts_floors（MASTER `ae756204`→**`835e4388`**）重钉 V595。看板开局 238 行 < 260 ⇒ **不归档**。
'''

LOCK_SEC = '''## QU · R212（2026-11-28）· S 域 mdisp 8/12 = ?AVINoticeSink@@ / ?AVINoticeSource@@（各 78 条、同批 78 类、8 恒在 12 之前）；ATL EventSink 空视图 = 律 W 全过滤而非丢失；S3 与 S2 同 pTD 禁互代；V595

**QU1. 🔴 mdisp=8/12 接口身份（R207-R211 遗留未取得项结案）.** 按 BCD 24 B（`+0`pTD/`+4`nc/`+8`mdisp/`+12`pdisp/`+16`vdisp/`+20`attributes）解析 BCA 元素：
mdisp==8 → **78** 条，pTD 全 `.?AVINoticeSink@@`(`0x816b50`)；mdisp==12 → **78** 条，pTD 全 `.?AVINoticeSource@@`(`0x8177e8`)。各去重名 **1** 个。
两者 **∈ TD_OWN** 且 **∉ INTERFACE**（26 个 `.?AU`）⇒ **S 域来自本类自己的类 TD**，与 T 域来自接口 BCD **不同源**——这是律 W 分域判据要写成 `TD_OWN ∧ .?AV` 的实质原因。
78 条 `(nc,pdisp,vdisp,attributes)` 全 `(0,-1,0,0)`。

**QU2. 🔴 位置规律.** 含 8 与含 12 类集合**相同**（78/78，对称差 0/0）。相对：`idx(8) − idx(12)` 恒 **−1**（78/78）。绝对**不固定**：8 跨度 **6..12**、12 跨度 **7..13**；8 距末尾 `{1:67,2:4,3:5,5:1,7:1}`。反控：索引 0 mdisp 恒 0（954/954）。

**QU3. 🔴 vftable 字节侧独立复算.** 8 与 12 视图 slot0 落点**全异址**（同 0 / 异 78），**槽数均 1**。
8 落点 `{0x410580:75, 0x41bc30:1, 0x522a60:1, 0x746100:1}`；12 落点 `0x410590` 78 类全共享。
`0x410580` = `xor al,al ; ret 8`（2 条指令、恒返回 false、清 2 dword）；`0x410590` = `ret 4`（首指令即 ret）。两址直接 call/jmp **0** 次。

**QU4. 🔴 mdisp=8 双形态 = I 域三形态的 S 域侧再证.** 3 个独占落点 `0x41bc30`(AircraftClass)/`0x522a60`(InfantryClass)/`0x746100`(UnitClass) 为真函数体，体内含 `lea esi,[edi-8]` 与 `cmp ebx,0x117b`；其余 **75** 类共享桩。⇒ R208 的 I 域 3 类在 S 域 8 槽口径下**独立复现**，两口径同一批类。

**QU5. 🔴 EventSink 空视图 = 律 W 全过滤.** 5 个 CHD（`0x80e680`/`0x80e740`/`0x80e780`/`0x80e7c0`/`0x80e998`），NB 6/6/5/5/6，非零 mdisp 记录各 **2** 条，pTD 恒 `?$CComObjectRootEx@VCComMultiThreadModel@ATL@@`(4,nc=1) + `CComObjectRootBase@ATL@@`(4,nc=0)，两者均 **onlysec** ⇒ 律 W 空集，与空视图 **5/5 一致**。
判据有效的证据：不做 pTD 过滤 ⇒ 5 类全得 `{4}`（反控 5/5 非空）⇒ **成因是过滤，不是记录缺失**。R211 QT9④「结构性无 vs 丢失」**判为结构性无**（过滤所致）。

**QU6. 🟡 S3(21784) 与 S2(8) 同 pTD.** 21784 的 3 条 pTD **亦为** `?AVINoticeSink@@`，attributes 恒 **9**（8 记录为 0），类为 MouseClass(`0x7fab28`,idx=11)/TabClass(`0x805e90`,idx=9)/ScrollClass(`0x809050`,idx=10)，三类**均不含** 8/12。⇒ 同一 TD 以 8 与 21784 两偏移被引用，**两口径禁互代**。

**QU7. 🟡 判据订正（自错根因）.** INTERFACE **必须**取 pTD 所指向 TD 的内联名（全域 **26** 个），**不可**取 COL 记录自带名字（得 **2** 个、律 W 失配 **91**）。该 **91** 与 R211 `c8`/`c9` 的 91 **成因不同**（前者是 INTERFACE 判据错、后者是去掉 INTERFACE 项），禁互为证据。

**QU8. 🟡 跨家族（§2.12 规则 D 全复算）.** #545（deepseek，`audit` 只读，22 回合 / **4.47'** vs 8.0，无 OVERTIME）**12/12 PASS**。
其两条订正：①卡面 A8 括注「8 紧跟 12 之后/索引更大」方向写反（实测 −1，8 在前；落盘正文一直正确）；②「988 全池」与「954 COL 引用池」是两把尺，`TD_OWN == COL 引用池`（954/954），律 W 的 INTERFACE 须取全池 26。
其三**条口径限制：①律 W 零失配含 **855/954 = 89.6%** 平凡项（V 空 ∧ 无非零），真正吃力的是 **94** 类（V 非空 ∧ 载非零）+ **5** 类（V 空 ∧ 载非零）；②全池 `pdisp` 恒 −1、`vdisp` 恒 0，四元组只有 nc/attributes 有区分力；③`attributes==9` 全局 **6** 条，另 3 条为 `?$VectorClass@H@@`(0)/`?AVINoticeSource@@`(0)/`?AVStageClass@@`(36) ⇒ 不专属 S3。
补充：被排除 TD 共 **10** 个，**5** 个被实载 **26** 条、**5** 个零命中。
主会话 §2.12 规则 D 复算 **12 断言 0 FAIL**（`_r212/d1_recheck.py`）。

**QU9. 📌 自错 4 组（0 条进结论）.** ①`c1` 沿用 COL 类头判据解析 **BCA 元素**（元素是 BCD，`+4` 是 nc 不是 mdisp）⇒ sink 全报 MISSING、8/12 零命中；②`c2` 的 INTERFACE 取 COL 记录名 ⇒ 只得 2 个、律 W 失配 91（同错型第三次）；③`c3` 断言方向写反（+1 应为 −1）；④`c4`/`d1` 三次类型错（CHD 键取 own 名、list 差集、dict 与 set 比较）。

**QU10. 🟡 落盘与门禁.** R14_COMMON **§2.220** CR 保持 **1081**；GOAL **§1270** CR 保持 **337**；本段 **QU** CR 保持 **137**；STATUS_BOARD 第 212 轮 CR 保持 **0**（开局 **238 行 < 260**，**不归档**）。**FACT_INDEX V593→V594→V595**（V594 = S 域正文本，V595 补入 QU8 五条口径限制）：F29 第 5 列两次追加，其余 **57 行逐字节不变**，sha `1f6fe2af`→`184e2c74`→**`9ffc56c9`**、251275→254880→**257435** B；指针 + facts_floors（MASTER `ae756204`→`a692adcc`→**`835e4388`**）重钉 V595。

**QU11. ⚪ 未取得.** ①S3 三表（Mouse/Tab/Scroll，21784）的 `0x11c7`/`0x11c8` 语义（仍须 win-main 或静态扫 `[vtable+偏移]` 引用面）；②`?AUIUnknown` 伴记录 `attr=0x2` 与 S3 `attr=9` 的位义（须 win-main 动态）；③`?AVINoticeSink@@` 被以 8 / 21784 两偏移引用的选择规则；④主视图 9958 个 slot≥3 槽语义归属；⑤37 个 onlysec pTD 中其余 32 个的生成规则；⑥F23/F35 grade（两 tsv 不可读，禁预估回填）；⑦C7 三死分支、C11 十二 ID。
'''

BOARD_SEC = '''## 🟢 R17 第 212 轮（2026-11-28）· S 域 8/12 结案：?AVINoticeSink@@(8) / ?AVINoticeSource@@(12) 各 78 条、同批 78 类、8 恒在 12 之前；EventSink 空视图 = 律 W 全过滤（结构性无，非丢失）；mdisp=8 双形态再证 I 域三形态；V595

**取得（1 结案 + 3 新事实 + 1 定性）.** ①🔴 **S 域 mdisp=8/12 接口身份定案**（R207-R211 连续列为未取得）：按 **BCD 24 B 结构**（`+0`pTD/`+4`nc/`+8`mdisp/`+12`pdisp/`+16`vdisp/`+20`attributes）解析 BCA 元素 —— mdisp==8 恰 **78** 条、pTD **全部**为 `.?AVINoticeSink@@`(`0x816b50`)；mdisp==12 恰 **78** 条、pTD **全部**为 `.?AVINoticeSource@@`(`0x8177e8`)。各去重名 **1** 个。两者 **∈ TD_OWN** 且 **∉ INTERFACE**（26 个 `.?AU`）⇒ **S 域来自本类自己的类 TD，与 T 域来自接口 BCD 不同源**，这是律 W 分域判据写成 `TD_OWN ∧ .?AV` 的实质原因。78 条 `(nc,pdisp,vdisp,attributes)` **全 `(0,-1,0,0)`**。②🔴 **位置规律**：含 8 与含 12 的类集合**完全相同**（78/78，对称差 **0/0**）；`idx(8) − idx(12)` 恒 **−1**（78/78）⇒ **8 恒紧邻 12 之前**；绝对索引**不固定**（8 跨度 **6..12**、12 跨度 **7..13**，随继承深度变化；8 距末尾 `{1:67, 2:4, 3:5, 5:1, 7:1}`）。反控：BCA 索引 0 的 mdisp **恒 0**（954/954），8/12 恒不在索引 0。③🔴 **vftable 字节侧独立复算**（不经 mdisp 推导）：78 类的 8 与 12 视图 **slot0 落点全部异址**（同 0 / 异 78），两视图**槽数均为 1**；8 落点分布 `{0x410580:75, 0x41bc30:1, 0x522a60:1, 0x746100:1}`，12 落点 `0x410590` 被 78 类**全共享**。函数体：`0x410580` = `xor al,al ; ret 8`（**2 条指令**、无条件返回 false、清 2 dword）；`0x410590` = `ret 4`（首指令即 ret、清 1 dword）。两址被 `.text` 直接 call/jmp 命中 **0** 次（纯虚入口）。④🔴 **mdisp=8 双形态 = I 域三形态的 S 域侧再证**：3 个独占落点 `0x41bc30`(Aircraft)/`0x522a60`(Infantry)/`0x746100`(Unit) 为真函数体，体内含 `lea esi,[edi-8]` 与 `cmp ebx,0x117b`，其余 **75** 类共享桩 ⇒ **R208 的 I 域 3 类在 S 域 8 槽口径下独立复现**，两口径同一批类。⑤🔴 **ATL EventSink 空视图定性 = 律 W 全过滤，不是丢失**：5 个 CHD（`0x80e680`/`0x80e740`/`0x80e780`/`0x80e7c0`/`0x80e998`）NB **6/6/5/5/6**，非零 mdisp 记录**各 2 条**，pTD 恒 `?$CComObjectRootEx@VCComMultiThreadModel@ATL@@`(mdisp=4,nc=1) + `CComObjectRootBase@ATL@@`(mdisp=4,nc=0)，两者均 **onlysec** ⇒ 律 W 空集，与空视图 **5/5 一致**；反控：不做 pTD 过滤则 5 类全得 `{4}`（**5/5 非空**）⇒ **成因是过滤而非记录缺失**，R211 QT9④ 的「结构性无 vs 丢失」**判为结构性无**。⑥🟡 **S3/S2 同 pTD 交叉**：mdisp==21784 的 3 条 pTD **亦为** `?AVINoticeSink@@`，attributes 恒 **9**（8 记录为 0），类为 MouseClass(`0x7fab28`,idx=11)/TabClass(`0x805e90`,idx=9)/ScrollClass(`0x809050`,idx=10)，三类**均不含** 8/12 ⇒ 同一 TD 以 8 与 21784 两偏移被引用，**两口径禁互代**。

**判据订正（自错根因，同错型第三次）.** INTERFACE **必须**由 pTD 所指向 TD 的内联名（TD+8）判定（全域 **26** 个 `.?AU`）；**不可**由 COL 记录自带名字判定 —— 那样只得 **2** 个（`?AUINIEntry@INIClass`/`?AUINISection@INIClass`）且使律 W 失配 **91**。该 **91** 与 R211 `c8`/`c9` 的 91 **成因不同**（前者 INTERFACE 判据错、后者去掉 INTERFACE 项），禁互为证据。

**跨家族（§2.12 规则 D 全复算）.** #545（deepseek，`audit` 只读，22 回合 / **4.47'** vs 预算 8.0，无 OVERTIME）**12/12 PASS**。其两条订正：①**卡面 A8 括注方向写反**（我写「8 紧跟 12 之后/索引更大」，实测 −1 即 8 在前；**落盘正文方向一直正确**，只订卡面），旁证 78 对 `b8 − b12` 恒 **+24**，与 R204 S2b「BCA 次序逆序于 BCD 数组」一致；②「**988** RTTI 全池」与「**954** COL 引用池」是两把尺（`TD_OWN == COL 引用池` 954/954），律 W 的 INTERFACE 须取全池 26；实测三种写法（名字前缀 / 全池 26 / 实载 9）失配**均 0**，反控三数**同值**（无过滤 **94** / 仅 TD_OWN **91** / 仅 INTERFACE **81**）。其三条**口径限制：①律 W 零失配含 **855/954 = 89.6%** 平凡项（V 空 ∧ 无非零），真正吃力的是 **94** 类（V 非空 ∧ 载非零）+ **5** 类（V 空 ∧ 载非零）+ **0** 类（V 非空 ∧ 无非零）；②全池 `pdisp` 恒 −1、`vdisp` 恒 0 ⇒ 四元组只有 nc/attributes 有区分力；③`attributes==9` 全局 **6** 条，另 3 条为 `?$VectorClass@H@@`(`0x7ff680`,0)/`?AVINoticeSource@@`(`0x808170`,0)/`?AVStageClass@@`(`0x800600`,36) ⇒ **不专属** S3。补充：∈全池 ∉(INTERFACE∪TD_OWN) 的 TD 共 **10** 个，**5** 个被实载共 **26** 条、**5** 个零命中（`?AVDiskSwap`/`?$Node@PAUINIEntry@INIClass@@`/`?$Node@PAVMixFileClass@@`/`?$DynamicVectorClass@W4DiskID@@`/`?AVCDownloadEventSink`）。主会话 §2.12 规则 D **12 断言 0 FAIL**。

**自错 4 组（0 条进结论）.** ①`c1` 沿用 COL 类头判据解析 **BCA 元素**（元素是 BCD 记录：`+4` 是 nc 不是 mdisp）⇒ 5 个 sink 全报 MISSING、mdisp=8/12 一条不命中，误得「8/12 不在任何 BCA 里」；②`c2` 的 INTERFACE 取「COL 记录自带名字」⇒ 只得 2 个 `.?AU`、律 W 失配 **91**（同错型第三次复发）；③`c3` 断言「8 恒紧邻 12 之后（差恒 +1）」方向写反，实测 **−1**；④`c4`/`d1` 三次类型错（CHD 键取 own 记录名、`nz−set(emp)` 对 list 做差、`VS[...]` 返回 dict 却与 set `{0}` 比较）。

**落盘与门禁.** R14_COMMON **§2.220** CR 保持 **1081**；GOAL **§1270** CR 保持 **337**；LEAD_LOCK **QU** CR 保持 **137**；本段第 212 轮 CR 保持 **0**（开局 **238 行 < 260**，**不归档**）。**FACT_INDEX V593→V594→V595**（V594 = S 域正文本，V595 补入五条口径限制与卡面订正）：F29 第 5 列两次追加，其余 **57 行逐字节不变**（57 行 / 5 列），sha `1f6fe2af`→`184e2c74`→**`9ffc56c9`**、251275→254880→**257435** B（+6160）；指针 + facts_floors（EXPECT_CUR/CUR_SHA256/TOTAL_BYTES/MASTER `ae756204`→`a692adcc`→**`835e4388`**）重钉 V595。三门待收口复跑。

**⚪ 未取得.** ①S3 三表（Mouse/Tab/Scroll，21784）的 `0x11c7`/`0x11c8` 语义（仍须 win-main 或静态扫 `[vtable+偏移]` 引用面）；②`?AUIUnknown` 伴记录 `attr=0x2` 与 S3 `attr=9` 的位义（须 win-main 动态）；③`?AVINoticeSink@@` 被以 8 / 21784 两偏移引用的选择规则；④主视图 9958 个 slot≥3 槽语义归属；⑤37 个 onlysec pTD 中其余 32 个生成规则；⑥F23/F35 grade（两 tsv 不可读，禁预估回填）；⑦C7 三死分支、C11 十二 ID。
'''

commit(R14,R14_SEC,1081,'r14c')
commit(GOAL,GOAL_SEC,337,'goalc')
commit(LOCK,LOCK_SEC,137,'lockc')
commit(BOARD,BOARD_SEC,0,'boardc')
print('\n四件套全部写入完成')
