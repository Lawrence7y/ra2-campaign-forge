#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R204 p1：四件套写入（wx 独占备份 -> 断言旧 sha256 与 CR -> 一次性写入 -> 回读校验）。
R14_COMMON 新增 ## 2.209（CR 保持 1081）
GOAL_THREE_TARGETS_20261018 新增 ## §1259（CR 保持 337）
lead/LEAD_LOCK 新增 QG 段（CR 保持 137）
STATUS_BOARD 新增第 204 轮（CR 保持 0）
"""
import hashlib, os, time
ROOT = '/home/t628/projects/ra2-campaign-forge'
D = ROOT + '/lead/next_re_20261117_r14'
BASE = ROOT + '/R17_LEAD_BASELINE'
os.makedirs(BASE, exist_ok=True)
def sha(b): return hashlib.sha256(b).hexdigest()
STAMP = time.strftime('%Y%m%d_%H%M%S')

SEC2209 = """
## 2.209 R17 第 204 轮（2026-11-28）· MSVC RTTI 三张表（COL / CHD / BCD）字节布局首次实证；两条独立判据给出同一 partition；CHD.attributes bit0 与 mdisp==0 两条充要律

**一、🔴 布局实证（三张表的字段与步长，全部逐条实测，非抽样）.** COL 记录 5 个 dword：`+0 signature(0/1/2)`、`+4 mdisp`、`+8 pdisp`、`+12 pTypeDescriptor`、`+16 pClassHierarchyDescriptor`。CHD 至少 4 个有效字段：`+0`（954/954 恒 0）、`+4 attributes（取值集合 {0,1,5}，分布 0:855 / 1:66 / 5:33）`、`+8 numBaseClasses（16 种取值，max 18，全部 <= 200）`、`+12 pBaseClassArray（954/954 落 .rdata，954 个互异）`。BCD 定长 **24 字节**六字段：`+0 pTypeDescriptor`、`+4 numContainedBases`、`+8 mdisp`、`+12 pdisp`、`+16 vdisp`、`+20 attributes`；全 1002 条 BCA 引用去重后 **1002 个不同 BCD**，`pdisp` 恒 **-1**（1002/1002）⇒ **本镜像无任何虚基类**，`vdisp` 恒 **0**（1002/1002），BCD.attributes 分布 **0:991 / 2:7 / 9:4**。

**二、🔴 交付一：两条互不依赖的判据给出同一个 partition.** R203 的 954 组是靠「槽流遇同组头类名 COL ⇒ 新视图」这个**名字判据**得到的。本轮改用**纯指针判据**：只按 COL 的 `+16 pClassHierarchyDescriptor` 分组，完全不读类名，也得 **954 组**，组大小分布 **1:860 / 2:10 / 3:6 / 4:76 / 5:1 / 7:1**，与 R203 的视图数分布**逐桶相等**。更强：两个关系**互为细化**（每个 pCHD 块只落 1 个名字块 954/954，每个名字块只落 1 个 pCHD 954/954），块数相同 ⇒ **同一 partition**（`_r204/m1_chd.py` C2c/C2d/C2e、`m6_verify.py` X1c）。⇒ R203 的 954 不再依赖类名判据的正确性，它有了一条同族但不同算法的独立见证。

**三、🔴 交付二：强区分力判据「自有 pTD ⊆ BCA 的 pTD 集合」.** 对每张 CHD，取该组所有 COL 的 pTypeDescriptor 构成自有集合，要求它 ⊆ 该 CHD 的 BCA 中全部 BCD 的 pTD 集合：**954/954 成立**。反控两档：① 抽样换用「同长度其它 CHD 的 BCA」⇒ **0/954**；② 更严的穷举反控（n>=4 的 123 张 CHD，全部同长候选对）⇒ **0/123**。另在 200 次「随机 .rdata 数组」上跑同一判据 ⇒ **0/200**。这条判据反过来证明 BCA 不是任意指针数组，而是与该类身份绑定的继承路径表（`m5_pool.py` P3a/P3b、`m10_final2.py` W3c/W3d/W4d、`m11_ctl.py` V1d）。**R204 首版反控出现过 2/954 的命中，经 `m11_ctl.py` 定位为「无同长候选时回退自选」的脚本缺陷，不是数据反例**（已订正门限与实现）。

**四、🔴 交付三：CHD.attributes bit0 与「存在 mdisp!=0 的 BCD」互为充要（954/954 双向）.** 交叉表：`(attributes, 有mdisp!=0, 多视图)` = **{(0,F,F):855, (1,T,T):61, (1,T,F):5, (5,T,T):33}**。⇒ ① `attributes bit0 == 1` ⟺ 该类有 mdisp!=0 的基类 BCD，双向零例外（`m8_laws.py` Z3a）；② `attributes == 5` 的 33 张全部也是 MI 类（Z3b）；③ 5 与 1 的区别**只在是否有 0 以外的结构量**上未找到（7 个候选量里唯一强区分的是 `last_md` 均值 1025.5 vs 67.0，但该量受个别极大 mdisp 拉动，不足以定性），如实登记为**未取得**。⇒ 「attributes == 0 ⇔ 单继承无语义标记」这一半是硬的。

**五、🔴 交付四：BCD 池结构与 24 字节步长的替代证据.** 1002 个 BCD 全部 **8 字节对齐**，但**不是 24 字节统一网格**（地址 mod 24 三态 {0:340, 8:320, 16:342}）。按「相邻差恰为 24」切成 run：**708 个 run**，且 **run 内 mod 24 恒定 708/708**，run 基址 mod 24 = {0:235, 8:233, 16:240} ⇒ 三态来自**不同 24 字节数组的起始模不同**，不是没有定长。24 字节步长的直接证据换成两条可复算的：① `b-24` 也是 BCD 的 **294** 条中，`dw(b-16) == mdisp(b-24)` 成立 **294/294**；② 708 条孤立记录中 `dw(b-16) == 0` 成立 **708/708**（`m12_audit.py` A3d/A3e）。反控：随机 1002 个 .rdata 地址里 `b-16==0` 的 **308** 个，显著低于 708 ⇒ 该证据不是恒真。**审计员原提的「hist(b-16) == hist(mdisp)」判定力不足**：两者键数虽都 14 且 0 的计数都 978，但**逐 BCD 只有 975/1002 相等**（27 处不等），且直方图近乎恒定；偏移扫描进一步显示 `hist` 相等的偏移是 **{-16, +8}**，而 +8 是 mdisp 自身，故真正有效的替代只剩 -16 一条（`m12_audit.py` A3a/A3b/A3c）。

**六、🔴 交付五：mdisp==0 ⟺ 该 BCD 的 pTD 属于本类自有（充要律）.** BCA 元素共 2615 条：`mdisp==0` **2228** 条，其中自有 pTD **954**（每类恰 1 条主对象 BCD）；`mdisp!=0` **387** 条，其中自有 pTD **0**（反向零反例）。反控：把字段换成 `+12 pdisp`（恒 -1）后无一为 0，律整体塌掉（`m12_audit.py` A4a-A4f）。⇒ 「mdisp==0」可以当「这是类自身而不是基类子对象」的机械判据用，与 R201/QE6 的 11 条 mdisp==0 装表定性互相印证。

**七、🔴 交付六：BCA 的段结构与它的两个边界.** 每张 CHD 的 BCA 相邻差分：**-24 占 973/1661**，其余为跨段大跳（-31104:78、-248:29、-776:21、-1312:20、-19864:12、+19888:12 等，全部是 8 的倍数，且跳转目标 100% 落 1002 条 BCD 池内）。按 -24 切段：**段数 1642**，段长分布 `{1:1252, 2:259, 3:31, 4:8, 5:6, 6:3, 7:1, 8:79, 10:1, 11:1, 12:1}`，**单元素段 1252/1642 = 76.2%**。等差（全 -24）CHD **490/954**，其中含 MI 的仅 **4** 个；非等差 464 个里含 MI **95** 个 ⇒ 大跳集中在多重继承类。段边界处 mdisp 变化：**平 652 / 升 33 / 降 3**，降的 3 例全部是 ATL `CComObject`/`CNetUtilEventSink` 家族（`m8_laws.py` Z2、`m12_audit.py` A1/A2）。

**八、🔴 交付七：视图 mdisp 集合 vs BCA mdisp 集合的等式边界.** 939/954 张 CHD 上两者**集合相等**；15 张不等，且**方向单一**（BCA 只多不少，无任何视图 mdisp 缺失）。多出的 mdisp 全是 172/240/248/36 这类大基类偏移。**mdisp!=0 的类 99 个 vs 多视图类 94 个，差 5 个**，5 个逐条定位为 ATL 模板/事件 sink 类（`0x80e680`、`0x80e740`、`0x80e780`、`0x80e7c0`、`0x80e998`），形态是「BCA 里有 mdisp=4 的 `CComObjectRootEx`/`CComObjectRootBase` 基类，但只有一张 vftable」⇒ **有基类子对象 ≠ 有第二张 vftable**，R203 的「94 类有 MI」是「有多视图」的口径，不是「有非零 mdisp 基类」的口径，两者不可混引（`m5_pool.py` P4、`m6_verify.py` X8）。

**九、📌 自错（当场抓出，0 条进结论）.** ① `m1` A1e 期望 CHD+4 恒 1，实测 {0,1,5}；② `m1` B2a/B2b/B2c 把 BCA 间距符号写反（实为 -24 主导），并误设「每个 BCD 的 ±24 都在池内」；③ `m1` B3c 期望 BCD.attributes 恒 0，实测 0/2/9；④ `m1` D1a/D2b/F1a/F3a 用「多重集相等」判据，前提就错（BCA 含无 vftable 的基类、且按路径计重数），四条整体作废；⑤ `m2` S2a 期望「±24 命中 > 55%」，实测各 294/1002（池是按 8 字节粒度交错的）；⑥ `m2` R2a 反控失效（子集律在随机数组上仍 866/954 ⇒ mdisp 大量取 0，子集律本身区分力弱），由 `m5` 换 pTD 判据后才有了强区分力；⑦ `m3` T2 的期望式把 pBCA 当数组首元素（实测 pBCA 指向的是「装 BCD 指针的数组」，其值不与 pBCA 相等），T2c 反控因此 261/954 反而「成立」；⑧ `m3` T4 的 `sig(shift=0)` 读成 pTD 而非 mdisp（应为 +8），致「真 BCA 0/84」的假 FAIL；⑨ `m4` B1a/C1b/C1c/D1a 四条期望都预设了「24 连续数组」，被 mod 24 三态与「数组尾 -8/-4」砸掉；⑩ `m4` E1b/E1c 反控失败（mdisp 子集律换 BCA 后仍 74/84）⇒ 该判据无区分力，已弃用；⑪ `m6` X5a 把我自己的严格基址判据当成执行员的判据（执行员的 490 是「组内等差」，两者数值一致但我标错了名字）；⑫ `m7` Y1c「短 BCA 全是等差」实测 478 等差 / 353 非等差；Y5a「attributes==2 落在 TClassFactory」实测 pTD 只有一个 `.?AUIUnknown@@`（7 条 BCD 分散在 7 个不同类里）；⑬ `m8` Z2c「段边界 mdisp 不减」实测 33 升 / 3 降 / 652 平；Z3d「属性 5 与 mdisp 重复相关」实测两组都是 100%；⑭ `m10` W3d 反控 2/954 是「无同长候选回退自选」的脚本缺陷（`m11_ctl.py` 定位并订正）；⑮ `m12` A3c 断言「偏移扫描唯一性为 {0,-16}」，实测集合是 {-16,+8}（+8 即 mdisp 自身偏移，我误写成 0）。

**十、🟡 跨家族与落盘.** 执行员 **#515**（hy4，12 回合 / 2.5 分 / 7 项独立复核）与审计员 **#516**（deepseek，28 回合 / 3.98 分 / 受控 10 项，自报 PASS 10 / FAIL 0）均无 OVERTIME。执行员 7 项里 5 项主会话逐数一致，2 项（24 网格、BCA 严格降序「绝大多数」）**正确指出卡面预期写错**，直接促成第五节与第七节的表述订正。审计员 10 条全部由主会话 `_r204/m6_verify.py`（20 断言）、`m10_final2.py`（18 断言）、`m11_ctl.py`（4 断言）、`m12_audit.py`（20 断言）亲跑复算；采纳其 4 条加强（708 run 结构、段长分布、b-16 判别力不足、mdisp==0 ⇔ 自有 pTD），**不采纳**其「mdisp 子集律可作证据」的取向（主会话 m4 已实测该判据换 BCA 后仍 74/84，无区分力）。落盘：R14_COMMON §2.209 CR 保持 **1081**；GOAL §1259 CR 保持 **337**；LEAD_LOCK QG 段 CR 保持 **137**；STATUS_BOARD 第 204 轮 CR 保持 **0**（开局 295 行 >= 260，已归档最早 2 段至 BOARD_ARCHIVE，归档后 248 行，收口 2xx 行，BOARD_ARCHIVE CR 保持 2952）。

**十一、⚪ 未取得（不粉饰）.** ① CHD.attributes == 5 与 == 1 的语义差别（7 个候选结构量都不足以定性）；② 非等差 BCA 的 464 张中 111 张是「短 BCA（n<=3）却非等差」，其跨段成因未逐个定性；③ 段长恰为 8 的 79 个段的成因（异常聚集）；④ CHD `+16` 之后是否还有字段（本轮只验了前 4 个 dword，未验证结构总长）；⑤ BCD 池中 9579 个非 BCD 的 8 字节槽内容语义（zero 6069 / .rdata 2534 / other 976）；⑥ 5 个 ATL 类的 `CComObjectRootEx` 基类为何不产生第二张 vftable；⑦ R203 遗留 260 个被吞候选归类、94 个 MI 类基类名链；⑧ R200 (c)(d)(f)(g)；⑨ F23/F35 grade；⑩ coverage.tsv/function_atlas.tsv 仍不可读；⑪ 86.19% 仍不可重算；⑫ C7 三死分支各 0 行；⑬ C11 十二个 ID 未动。
"""

SEC1259 = """
## §1259 R17 第 204 轮（2026-11-28）· MSVC RTTI 三表字节布局实证：CHD 4 字段 / BCD 24 字节 6 字段 / BCA 指针数组；两条独立判据同一 partition；两条充要律

**一、布局.** COL 5 dword（signature / mdisp / pdisp / pTD / pCHD）。CHD `+0` 恒 0、`+4` attributes `{0:855,1:66,5:33}`、`+8` numBaseClasses（max 18）、`+12` pBaseClassArray（全 .rdata，954 互异）。BCD **定长 24** 六字段（pTD / numContainedBases / mdisp / pdisp / vdisp / attributes）；1002 条去重 BCD 中 `pdisp` 恒 **-1**、`vdisp` 恒 **0** ⇒ **无虚基类**；BCD.attributes `{0:991,2:7,9:4}`。

**二、两条独立判据同一 partition.** 只用 `COL+16 pCHD` 分组、完全不读类名，得 **954 组**，组大小 **1:860/2:10/3:6/4:76/5:1/7:1**，与 R203 名字判据的视图数分布逐桶相等；两关系互为细化且块数相同 ⇒ **同一 partition**。R203 的 954 因此有了不同算法的独立见证。

**三、强区分力判据.** 「自有 pTD ⊆ BCA pTD 集合」**954/954**；反控：换同长其它 CHD 的 BCA **0/954**、n>=4 穷举 **0/123**、随机 .rdata 数组 **0/200**。

**四、充要律 1.** CHD.attributes bit0 == 1 ⟺ 该类存在 mdisp!=0 的 BCD，**双向 954/954**；交叉表 `{(0,F,F):855,(1,T,T):61,(1,T,F):5,(5,T,T):33}`。attributes==5 与 ==1 的语义差别**未取得**。

**五、充要律 2.** BCD 的 `mdisp==0` ⟺ 该 BCD 的 pTD 是本类自有：BCA 2615 条元素中 mdisp==0 **2228**（自有 954）、mdisp!=0 **387**（自有 **0**）；换字段反控（用恒 -1 的 pdisp）律整体塌掉。

**六、BCD 池与 24 步长.** 1002 条全 8 字节对齐，mod 24 三态 `{0:340,8:320,16:342}` ⇒ 非统一网格。按相邻差 24 切 run：**708 run**，run 内 mod24 恒定 **708/708**，run 基址 mod24 `{0:235,8:233,16:240}`，三态来自不同数组起点。24 步长替代证据：`b-24∈池` 的 294 条中 `dw(b-16)==mdisp(b-24)` **294/294**；孤立 708 条中 `dw(b-16)==0` **708/708**；反控随机 1002 地址 zero 仅 308。审计原提的 `hist(b-16)==hist(mdisp)` **判别力不足**（逐 BCD 仅 975/1002 相等）。

**七、BCA 段结构.** 组内差分 **-24 占 973/1661**，其余为 8 的倍数大跳（-31104:78 等），跳转目标 100% 落 BCD 池；段数 **1642**，段长 `{1:1252,2:259,3:31,4:8,5:6,6:3,7:1,8:79,10:1,11:1,12:1}`，**单元素段 76.2%**；等差 CHD **490/954**（含 MI 仅 4 个），非等差 464 个（含 MI 95 个）；段边界 mdisp **平 652 / 升 33 / 降 3**，降的 3 例全为 ATL 事件 sink 家族。

**八、视图集合等式边界.** 939/954 张 CHD 上「视图 mdisp 集合 == BCA mdisp 集合」；15 张不等且方向单一（BCA 只多不少）。mdisp!=0 的类 **99** vs 多视图类 **94**，差的 5 个逐条定位为 ATL `CComObject`/事件 sink（0x80e680/0x80e740/0x80e780/0x80e7c0/0x80e998）：**有基类子对象 ≠ 有第二张 vftable**，两个口径不可混引。

**九、跨家族.** #515（hy4，7 项独立复核，5 项逐数一致、2 项正确指出卡面预期错）与 #516（deepseek，受控 10 项自报全 PASS）结论全部由主会话 `m6_verify.py`（20 断言）/`m10_final2.py`（18）/`m11_ctl.py`（4）/`m12_audit.py`（20）亲跑复算；采纳 4 条加强，不采纳「mdisp 子集律可作证据」。自错 15 组 0 条进结论。

**十、未取得.** ① attributes 5 vs 1 语义；② 111 张「短 BCA 非等差」成因；③ 段长恰 8 的 79 个段成因；④ CHD+16 之后字段；⑤ 9579 个非 BCD 8 字节槽语义；⑥ 5 个 ATL 类为何无第二张 vftable；⑦ R203 遗留 260 被吞候选与 94 MI 基类名链；⑧ R200 (c)(d)(f)(g)；⑨ F23/F35 grade；⑩ coverage.tsv/function_atlas.tsv 不可读；⑪ 86.19% 不可重算；⑫ C7 三死分支 0 行；⑬ C11 十二个 ID 未动。
"""

QG = """
## QG · R17 第 204 轮（2026-11-28）· RTTI 三表布局首次实证；954 组有了第二条独立判据；两条充要律（attributes bit0 / mdisp==0）

**QG1. 🔴 布局（全部逐条实测）.** COL 5 dword：signature / mdisp / pdisp / pTD / pCHD。CHD：`+0` 恒 0（954/954）、`+4` attributes `{0:855,1:66,5:33}`、`+8` numBaseClasses（max 18）、`+12` pBaseClassArray（全 .rdata、954 互异）。BCD **定长 24** 六字段 pTD/numContainedBases/mdisp/pdisp/vdisp/attributes；1002 条去重 BCD 中 `pdisp` 恒 **-1**、`vdisp` 恒 **0** ⇒ **本镜像无虚基类**；BCD.attributes `{0:991,2:7,9:4}`。

**QG2. 🔴 954 组的第二条独立判据（算法级）.** 只用 `COL+16 pCHD` 指针分组、完全不读类名，得 954 组，组大小 **1:860/2:10/3:6/4:76/5:1/7:1**，与 R203 名字判据的视图数分布**逐桶相等**；两关系互为细化、块数相同 ⇒ **同一 partition**。⇒ R203 的 954 不再依赖类名判据的正确性。

**QG3. 🔴 强区分力判据「自有 pTD ⊆ BCA pTD 集合」.** 真 **954/954**；反控三档 **0/954**（换同长其它 CHD 的 BCA）、**0/123**（n>=4 穷举全部同长候选对）、**0/200**（随机 .rdata 数组）。首版反控出现的 2/954 经 `m11_ctl.py` 定位为「无同长候选回退自选」的脚本缺陷，非数据反例。

**QG4. 🔴 充要律 1（CHD.attributes bit0）.** `bit0==1` ⟺ 该类存在 mdisp!=0 的 BCD，**双向零例外 954/954**；交叉表 `{(0,F,F):855,(1,T,T):61,(1,T,F):5,(5,T,T):33}`。attributes==5 的 33 张全为 MI；5 与 1 的语义差别**未取得**（7 个候选结构量都不足以定性）。

**QG5. 🔴 充要律 2（BCD.mdisp==0）.** mdisp==0 ⟺ 该 BCD 的 pTD 属本类自有：BCA 2615 条中 mdisp==0 **2228**（自有 954，每类恰 1 条主对象 BCD）、mdisp!=0 **387**（自有 **0**）；反控换成恒 -1 的 pdisp 后律整体塌掉。

**QG6. 🔴 BCD 池与 24 字节步长.** 1002 条全 8 字节对齐但 mod 24 三态 `{0:340,8:320,16:342}` ⇒ **非统一网格**；按相邻差 24 切 **708 run**，run 内 mod24 恒定 **708/708**，run 基址 mod24 `{0:235,8:233,16:240}`（三态来自不同数组起点）。24 步长替代证据：`b-24∈池` 的 294 条中 `dw(b-16)==mdisp(b-24)` **294/294**；孤立 708 条 `dw(b-16)==0` **708/708**；反控随机 1002 地址 zero 仅 **308**。审计原提 `hist(b-16)==hist(mdisp)` **判别力不足**（逐 BCD 仅 975/1002 相等、27 处不等）。

**QG7. 🔴 BCA 段结构.** 组内差分 **-24 占 973/1661**，其余为 8 的倍数跨段大跳（-31104:78 / -248:29 / -776:21 / -1312:20 / ±19864:12），跳转目标 **100%** 落 1002 条 BCD 池内；段数 **1642**，段长 `{1:1252,2:259,3:31,4:8,5:6,6:3,7:1,8:79,10:1,11:1,12:1}`，**单元素段 76.2%**；等差 CHD **490/954**（含 MI 仅 4），非等差 464（含 MI 95）；段边界 mdisp **平 652 / 升 33 / 降 3**，降的 3 例全为 ATL 事件 sink 家族。

**QG8. 🔴 集合等式边界（口径级）.** 939/954 张 CHD 上「视图 mdisp 集合 == BCA mdisp 集合」；15 张不等且方向单一（BCA 只多不少）。mdisp!=0 的类 **99** vs 多视图类 **94**，差的 5 个逐条定位为 ATL `CComObject`/事件 sink（0x80e680 / 0x80e740 / 0x80e780 / 0x80e7c0 / 0x80e998）⇒ **有基类子对象 ≠ 有第二张 vftable**，R203 「94 类有 MI」与「99 类有非零 mdisp 基类」不可混引。

**QG9. 📌 自错（15 组，0 条进结论）.** ① m1 A1e 期望 CHD+4 恒 1（实测 {0,1,5}）；② m1 B2a/B2b/B2c 间距符号写反且误设「每个 BCD 的 ±24 都在池内」；③ m1 B3c 期望 BCD.attributes 恒 0（实测 0/2/9）；④ **m1 D1a/D2b/F1a/F3a 四条「多重集相等」判据整体作废**（前提错：BCA 含无 vftable 的基类且按路径计重数）；⑤ m2 S2a 期望 ±24 命中 >55%（实测各 294/1002，池按 8 字节粒度交错）；⑥ **m2 R2a 反控失效**（mdisp 子集律在随机数组上仍 866/954 ⇒ 该律区分力弱），促使改用 pTD 判据；⑦ m3 T2 期望式把 pBCA 当数组首元素，T2c 反控因此 261/954 反而成立；⑧ m3 T4 `sig(shift=0)` 读成 pTD 而非 mdisp，致「真 BCA 0/84」假 FAIL；⑨ m4 B1a/C1b/C1c/D1a 四条预设「24 连续数组」，被 mod24 三态与「数组尾 -8/-4」砸掉；⑩ **m4 E1b/E1c 反控失败**（mdisp 子集律换 BCA 后仍 74/84）⇒ 判据弃用；⑪ m6 X5a 把自己写的严格基址判据当成执行员的判据（执行员的 490 是「组内等差」，数值一致但标签错）；⑫ m7 Y1c「短 BCA 全等差」实测 478/353；Y5a「attributes==2 落 TClassFactory」实测 pTD 只有 `.?AUIUnknown@@`；⑬ m8 Z2c「段边界 mdisp 不减」实测 33 升 / 3 降 / 652 平；Z3d「属性 5 与 mdisp 重复相关」两组均 100%；⑭ m10 W3d 反控 2/954 是「无同长候选回退自选」缺陷，由 m11_ctl 订正；⑮ m12 A3c 断言偏移扫描唯一集为 {0,-16}，实测 {-16,+8}。

**QG10. 🟡 跨家族与落盘.** #515（hy4，12 回合 / 2.5 分 / 7 项）与 #516（deepseek，28 回合 / 3.98 分 / 受控 10 项，自报 10 PASS / 0 FAIL）**均无 OVERTIME**。执行员 7 项中 5 项逐数一致、**2 项正确指出卡面预期写错**（24 网格、BCA「绝大多数」降序），直接促成 QG6/QG7 表述订正。审计 10 条由主会话 `m6_verify.py`（20 断言）、`m10_final2.py`（18）、`m11_ctl.py`（4）、`m12_audit.py`（20）亲跑复算；**采纳 4 条加强**（708 run、段长分布、b-16 判别力不足、mdisp==0⇔自有 pTD），**不采纳**「mdisp 子集律可作证据」。落盘：R14_COMMON §2.209 CR 保持 **1081**；GOAL §1259 CR 保持 **337**；本段 CR 保持 **137**；STATUS_BOARD 第 204 轮 CR 保持 **0**（开局 295 行 >= 260，归档最早 2 段至 BOARD_ARCHIVE 后 248 行，BOARD_ARCHIVE CR 保持 **2952**）。

**QG11. ⚪ 未取得（不粉饰）.** ① CHD.attributes 5 与 1 的语义差别；② 464 张非等差 CHD 中 111 张「n<=3 却非等差」的成因；③ 段长恰为 8 的 79 个段成因；④ CHD `+16` 之后是否还有字段；⑤ BCD 池 9579 个非 BCD 的 8 字节槽语义（zero 6069 / .rdata 2534 / other 976）；⑥ 5 个 ATL 类为何不产生第二张 vftable；⑦ R203 遗留 260 被吞候选归类与 94 MI 基类名链；⑧ R200 (c)(d)(f)(g)；⑨ F23/F35 grade；⑩ coverage.tsv/function_atlas.tsv 仍不可读；⑪ 86.19% 仍不可重算；⑫ C7 三死分支各 0 行；⑬ C11 十二个 ID 未动。
"""

BOARD = """
## R204 (2026-11-28) · MSVC RTTI 三表布局首次实证；954 组获得第二条独立判据；两条充要律

**一、布局实证.** COL 5 dword（signature / mdisp / pdisp / pTD / pCHD）。CHD：`+0` 恒 0、`+4` attributes `{0:855,1:66,5:33}`、`+8` numBaseClasses（max 18）、`+12` pBaseClassArray（全 .rdata、954 互异）。BCD **定长 24** 六字段；1002 条去重 BCD 中 `pdisp` 恒 **-1**、`vdisp` 恒 **0** ⇒ **无虚基类**；BCD.attributes `{0:991,2:7,9:4}`。

**二、第二条独立判据.** 只用 `COL+16 pCHD` 指针分组、**完全不读类名**，得 **954 组**，组大小 **1:860/2:10/3:6/4:76/5:1/7:1** 与 R203 名字判据逐桶相等；两关系互为细化、块数相同 ⇒ **同一 partition**。R203 的 954 不再依赖类名判据。

**三、强区分力判据.** 「自有 pTD ⊆ BCA pTD 集合」真 **954/954**；反控 **0/954**（换同长其它 CHD 的 BCA）、**0/123**（n>=4 穷举同长候选对）、**0/200**（随机 .rdata 数组）。首版 2/954 经 `m11_ctl.py` 定位为「无同长候选回退自选」脚本缺陷。

**四、充要律 1.** CHD.attributes `bit0==1` ⟺ 存在 mdisp!=0 的 BCD，**双向 954/954**；交叉表 `{(0,F,F):855,(1,T,T):61,(1,T,F):5,(5,T,T):33}`。attributes 5 vs 1 的语义差别**未取得**。

**五、充要律 2.** `mdisp==0` ⟺ 该 BCD 的 pTD 属本类自有：BCA 2615 条中 mdisp==0 **2228**（自有 954）、mdisp!=0 **387**（自有 **0**）；换恒定 -1 的 pdisp 反控律整体塌掉。

**六、BCD 池与 24 步长.** 1002 条全 8 字节对齐但 mod24 三态 `{0:340,8:320,16:342}` ⇒ **非统一网格**；按差 24 切 **708 run**，run 内 mod24 恒定 **708/708**，run 基址 mod24 `{0:235,8:233,16:240}`。24 步长替代证据：`b-24∈池` 294 条中 `dw(b-16)==mdisp(b-24)` **294/294**；孤立 708 条 `dw(b-16)==0` **708/708**；反控随机 1002 地址 zero 仅 **308**。审计原提 `hist(b-16)==hist(mdisp)` **判别力不足**（逐 BCD 仅 975/1002 相等）。

**七、BCA 段结构.** 组内差分 **-24 占 973/1661**，其余为 8 的倍数大跳（-31104:78 / -248:29 / -776:21 等），跳转目标 **100%** 落 BCD 池；段数 **1642**，段长 `{1:1252,2:259,3:31,4:8,5:6,6:3,7:1,8:79,10:1,11:1,12:1}`，**单元素段 76.2%**；等差 CHD **490/954**（含 MI 仅 4），非等差 464（含 MI 95）；段边界 mdisp **平 652 / 升 33 / 降 3**，降的 3 例全为 ATL 事件 sink 家族。

**八、集合等式边界.** 939/954 张 CHD 上「视图 mdisp 集合 == BCA mdisp 集合」；15 张不等且方向单一（BCA 只多不少）。mdisp!=0 的类 **99** vs 多视图类 **94**，差 5 个逐条定位为 ATL `CComObject`/事件 sink（0x80e680/0x80e740/0x80e780/0x80e7c0/0x80e998）⇒ **有基类子对象 ≠ 有第二张 vftable**，两口径不可混引。

**九、自错 15 组 0 条进结论.** 关键三条：① **m1 的「多重集相等」四条判据整体作废**（BCA 含无 vftable 的基类、按路径计重数）；② **m2 R2a 反控失效**（mdisp 子集律随机数组仍 866/954，无区分力）促使改用 pTD 判据；③ m4 E1b/E1c 反控失败（换 BCA 后仍 74/84）⇒ 判据弃用。其余为期望值写反/字段偏移读错/常量腐烂。

**十、跨家族.** #515（hy4，12 回合 / 2.5 分，7 项独立复核）与 #516（deepseek，28 回合 / 3.98 分，受控 10 项自报 10 PASS / 0 FAIL）**均无 OVERTIME**。执行员 **2 项正确指出卡面预期写错**（24 网格、BCA「绝大多数」降序），直接采纳。审计 10 条全由 `m6_verify.py`（20 断言）/`m10_final2.py`（18）/`m11_ctl.py`（4）/`m12_audit.py`（20）亲跑复算；采纳 4 条加强，**不采纳**「mdisp 子集律可作证据」。落盘：R14_COMMON §2.209 CR 保持 **1081**；GOAL §1259 CR 保持 **337**；LEAD_LOCK QG 段 CR 保持 **137**；看板 CR 保持 **0**（开局 295 行 >= 260，归档最早 2 段后 248 行；BOARD_ARCHIVE CR 保持 **2952**）。

**十一、未取得.** ① CHD.attributes 5 与 1 的语义差别；② 464 张非等差 CHD 中 111 张「n<=3 却非等差」成因；③ 段长恰 8 的 79 个段成因；④ CHD `+16` 之后字段；⑤ 9579 个非 BCD 的 8 字节槽语义（zero 6069 / .rdata 2534 / other 976）；⑥ 5 个 ATL 类为何无第二张 vftable；⑦ R203 遗留 260 被吞候选与 94 MI 基类名链；⑧ R200 (c)(d)(f)(g)；⑨ F23/F35 grade；⑩ coverage.tsv/function_atlas.tsv 不可读；⑪ 86.19% 不可重算；⑫ C7 三死分支 0 行；⑬ C11 十二个 ID 未动。
"""

JOBS = [
    (ROOT + '/lead/GOAL_THREE_TARGETS_20261018.md', SEC1259, 337, '§1258'),
    (ROOT + '/lead/LEAD_LOCK', QG, 137, 'QF'),
    (D + '/STATUS_BOARD.md', BOARD, 0, 'R203'),
]
for path, sec, want_cr, anchor in JOBS:
    old = open(path, 'rb').read()
    oldsha = sha(old); oldcr = old.count(b'\r')
    assert oldcr == want_cr, (path, oldcr, want_cr)
    assert anchor.encode('utf-8') in old, (path, anchor)
    bak = '%s/%s.%s.bak' % (BASE, os.path.basename(path), STAMP)
    fd = os.open(bak, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    os.write(fd, old); os.close(fd)
    assert sha(open(bak, 'rb').read()) == oldsha
    core = sec.replace('\r\n', '\n').strip('\n')
    tail = {'R14_COMMON.md': '\n\n', 'LEAD_LOCK': '\n\n', 'GOAL_THREE_TARGETS_20261018.md': '\n',
            'STATUS_BOARD.md': '\n'}[os.path.basename(path)]
    head = '\n' if old.endswith(b'\n') else '\n\n'
    new = old + (head + core + tail).encode('utf-8')
    with open(path, 'wb') as f: f.write(new)
    rb = open(path, 'rb').read()
    assert rb.count(b'\r') == want_cr, (path, rb.count(b'\r'), want_cr)
    assert sha(rb) != oldsha and rb.startswith(old)
    print('WROTE %-42s CR=%d LF=%d +%d B  %s' % (os.path.basename(path), rb.count(b'\r'),
          rb.count(b'\n'), len(rb) - len(old), os.path.basename(bak)))
    if os.path.basename(path) == 'R14_COMMON.md':
        i = rb.find('## 2.209'.encode())
        seg = rb[i:]
        j = seg.find(b'\n## ', 1)
        seg = seg if j < 0 else seg[:j]
        print('   SEC 2.209 bytes = %d  (floor = %d)' % (len(seg.rstrip(b'\n\n')), len(seg.rstrip(b'\n\n')) // 2))
print('OK')
