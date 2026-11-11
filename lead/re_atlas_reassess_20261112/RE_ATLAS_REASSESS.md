# RE-ATLAS 复评 · 2026-11-12（受限执行方报告）

执行环境：D:\Project\ra2-campaign-forge（Windows/PowerShell）。**零真机**（未启动 gamemd.exe/ra2loader/YURI.exe，未 attach、未读活进程内存）；除写域 `lead\re_atlas_reassess_20261112\` 外一律只读；未做任何 git 操作；所有脚本以 `python -I -X utf8 <绝对路径>` 运行；指纹全部 hashlib/Get-FileHash 实算。
写域内产物：`RE_ATLAS_REASSESS.md`（本件）、`step1_fingerprint.py`、`step1_re_atlas_manifest.tsv`（498 文件）、`step1_manifest_baseline.tsv`（首跑基线副本）、`step1_fingerprint.stdout.txt`、`step2_r036_rerun.py`、`step2_r036_rerun.stdout.md`、`step2_r036_rerun.stderr.txt`、`step2_verify_r035.stdout.txt`、`step2_verify_r035.stderr.txt`。

---

## STEP 1 · 停摆事实核实（全部实算，不转引）

### 1.1 关键文件指纹（实跑：`python -I -X utf8 step1_fingerprint.py`，全量 498 文件见 step1_re_atlas_manifest.tsv）

| 文件 | 字节 | mtime（本地） | sha256 |
|:--|--:|:--|:--|
| re_atlas\STATUS.md | 89,528 | 2026-10-30 07:09:08 | dc2df84d1a75dbac30019d65800d67c2914998ef2ba05e1be1753b8344212f53 |
| re_atlas\LEDGER.md | 397,746 | 2026-10-30 07:09:08 | 3a20921958131b776f4920ab104f3d1d5006aa6758067f4f1f01a8422faefd2d |
| re_atlas\INDEX.md | 116,281 | 2026-10-29 19:25:30 | a080bc246ea09006ebd1b02d39a95a9b572a29644bdf5930d24166247105bc67 |
| re_atlas\HANDOFF_TO_GOAL3T.md | 127,332 | 2026-10-29 19:16:32 | 00fbe2383bb4059c9e07ec0b84cdca3f84a117e775395e7f704eae0283a6f219 |
| re_atlas\kb\00_global_skeleton.md | 10,125 | 2026-10-21 22:08:49 | 29a579889a12c3bdfd577e8eba1801c2d04d1b7dc392399aad85a3903af45587 |
| re_atlas\kb\10_map_triggers.md | 15,665 | 2026-10-21 22:08:49 | 702b80b28b5e9ce089f3547a2727497655d4c47fc1333cc169a89426d4c26510 |
| re_atlas\kb\11_class_layouts.md | 48,978 | 2026-10-25 22:31:03 | 3b0b70a40d9f4bef64728d5fa157acdbe3d4b130ffa247761e13c5ea72d22d25 |
| re_atlas\kb\20_vtable_contract.md | 14,171 | 2026-10-23 23:56:02 | 600965b9c7a4a3bf892dac3c1df2db5b5df8cc8124c6789b5aa6ecc1c04c196a |
| re_atlas\kb\21_swizzle_and_object_fields.md | 28,739 | 2026-10-25 22:31:03 | 4764eca67e2ee5e11e307fa4c3535fd3f56ae17517189f4b5eeda5c7c0dfec62 |
| re_atlas\kb\22_abstractclass_vtable_slots.md | 14,597 | 2026-10-21 22:08:49 | e48c2122eb608646a1cfa602e98f7e7afcb8e0873af23bedece096968c5dd767 |
| re_atlas\kb\30_ini_subsystem.md | 169,077 | 2026-10-26 01:51:39 | 977a29fd95d05e7612f6909d6f0517b10612a9894e0dc3f368fd1d44e26953c9 |

目录分布（实跑分组统计）：`evidence/` 169 件、`tools/` 169 件、`.mimosa/` 136、`tmp_qwen_grade/` 11、`kb/` 7 卷、顶层登记件 6（STATUS/LEDGER/INDEX/HANDOFF/CONFLICTS/ADJUDICATION_REQUEST）。

### 1.2 最后轮次与停摆时长（实跑 `Select-String '^## R-\d+'`）

- LEDGER.md 轮次标题总数 = **73**（实测计数），末轮标题 = **R-064 · 2026-10-30 — INIClass/GenericList 定名仲裁**（LEDGER.md:6771，节尾 :6798-6801 含「R-064 为单甄别员同族上下文自查裁定（未过异族）」的诚实账）。
- re_atlas/ 内最晚 mtime = `tools\_r064rev_probe7.py` **2026-10-30 12:39:53**（R-064 收口后的复核探针）；次晚为 LEDGER/STATUS 2026-10-30 07:09:08。
- **对转引的一处订正**：RE_PROGRESS_20261111.md §1-4/§2 写「STATUS/LEDGER 文件 mtime 2026-10-29」——实测为 **2026-10-30 07:09:08**（mtime 10-29 的是 INDEX.md 与 HANDOFF）。停摆时长按最晚活动（10-30）算到本报告时点（11-12）约 **12.5 天**，「停摆 12 天」的量级成立，但依据日期应更正为 10-30 而非 10-29。

### 1.3 STATUS 头部登记（转引自文件，本人已读过原文）

- 覆盖率口径（STATUS.md:3-13）：对齐族 **12,792 / 13,683 ⇒ 4.28%…4.07%**（推荐引用），上界族 13,352/14,242 ⇒ 4.10%…3.91%；R-060 勘误 13,682→13,683。
- 欠账登记（STATUS.md:59-62、:259、:712）：**R-035 §六 761 合计可复现、分列不可复现**；**R-035 §2「426,741 / 40% 重叠」完全不可复现（实测 523,181 / 48.7%）**；「两项待 C 会话独立复算」。

---

## STEP 2 · 两条登记欠账的可复算性（核心）

### 2.1 欠账 B：「426,741 / 40% 重叠」→ 实测 523,181 / 48.7%

**依据件链**：
- 原始声称：LEDGER.md R-035 条目 :3755-3756（「归属结果里有大量站点被多个闭包同时认领（426,741 个地址，40% 重叠）」——**无落盘脚本**，是 R-035 轮内叙事）；
- 复测在案：`evidence/r036_r13_deliverable.md` §「同源的第二个不可复现量」:152-161（flat|T2 → Σ1,596,441 / ∪1,073,260 / **523,181** / **48.7%** / >1 所有者 228,884；flat → 1,529,944 / 1,019,137 / 510,807 / 50.1% / 222,419）；
- 登记横幅：`evidence/r035_denominator_both_directions.md`:3-15（「§二的重叠统计…均无法复现…重叠实测 523,181/48.7%」）；STATUS.md:62/259、INDEX.md:873、HANDOFF_TO_GOAL3T.md:1405/1423。

**a) 复算脚本在盘吗？**
- 独立的重叠计算脚本**不在盘**（在 `re_atlas/tools/` 全文检索 `523181|1073260|1596441|510807|426741` 零命中）。
- 但产生该数的**闭包引擎与入口集构造完整在盘**：`tools/r036_r13_deliverable.py`（sha256 007DBF5E6BE855DFD8A873248CF81970A679E44CD9E90C409F81B15C0E327B1A）内建 `CL = {e: closure(e) for e in flatT2}`（:411），其 P1 门禁钉镜像 sha256、P2 门禁钉 T2=886/flat|T2=16,110；读数定义（Σ闭包/并集/超出/超出占比/>1 所有者）在依据件表头逐列写明。
- **注意【未证】**：原始 523,181 当初是否恰好用盘上这个 `closure()`（cap=8000）算出，无法证明（原始脚本没落盘）。

**b) 写域内复制重跑能否复现 523,181/48.7%？——能，逐位精确复现。**
做法：`Copy-Item` 原脚本到写域（复制前后 sha256 相等），唯一改动是在 `CL/OWN` 构建之后追加 8 行**只读数**增量块（REGISTER OVERLAP 两行，不新增/修改任何 `check()` 门禁），`python -I -X utf8` 重跑：
- 门禁 **8/8 PASS**（P1 镜像 73201cc0…、P2 T2=886/flat|T2=16,110、P3 四分类 1,299/351/939/3,688=6,277、P3b 幻影 1 个 0x5BA0CE/对齐 6,276、P4 名字面量 5/30/21/35、P5 17 函数、P6 74/69 文件、P7 debug 2,589）；
- **REGISTER OVERLAP：flat|T2 (16,110)：Σ闭包 1,596,441 / 并集 1,073,260 / 超出 523,181（48.7%）/ >1 所有者地址 228,884**；flat (15,224)：1,529,944 / 1,019,137 / 510,807（50.1%）/ 222,419 —— **两行与 evidence/r036_r13_deliverable.md:156-157 在案值逐位一致**（stdout/stderr 已落写域 `step2_r036_rerun.stdout.md`（6,029 行交付件全文）/`step2_r036_rerun.stderr.txt`）。

**结论（欠账 B）**：可以闭合。该数不依赖丢失的脚本——闭包引擎在盘且带门禁，读数定义在案，重算复现。STATUS/HANDOFF 里「引用时必须重算，不能照抄」的禁令可解除为「可引用复算值」。

### 2.2 欠账 A：R-035 §六 761 的「分列」

**依据件链**：原表 `evidence/r035_denominator_both_directions.md` §六 :253-272（path 425 / format 147 / text 289 / ident 277 / debug **761**）；复测 `evidence/r036_r13_deliverable.md` §3.1 :110-140 与 LEDGER R-036b :4178-4222（地址类规则 `roots_call|T2`=14,238 +「最近前驱且闭包包含」→ 合计 **761** 命中且删 100 入口仍 752–756，四列 **418/149/290/289** ≠ 425/147/289/277 ⇒ 判「合计可复现、分列不可复现」，不采用）；STATUS.md:59-62。

**a) 复算脚本在盘吗？**
- 闭包类口径：在盘可跑（同一 `r036_r13_deliverable.py`，N1 REGISTER 行输出 761 欠账文本）。
- R-036b **地址类规则**：**不在盘**。LEDGER:4221-4222 明文记载——「**工具：探针已跑完即删（一次性）**，结论记于此条与 evidence/r036_r13_deliverable.md §3.1」。
- 闭包类「12 种组合落在 730…838」的扫描脚本同样不在盘；盘上脚本只算「最早入口优先」单口径。

**b) 能否复现？**
- 已复现（闭包类单口径）：重跑 N1 = 「最早入口优先得 **758**（差 -3），其中 path **425** 精确等于 R-035」——与原跑留档 `evidence/r036_verify.txt`:9 **逐字一致**。
- **未复现（地址类四列 418/149/290/289）**：脚本已删，按任务规则 6c **不另造替代算法**。

**c) 如实说缺什么**：缺「地址类规则」的实现（入口集 `roots_call|T2`=14,238 + 按地址取最近前驱且闭包包含的归属函数）与「随机删 T2/roots_call 入口 → 稳定性 752–756」实验脚本。这两件被显式声明为一次性丢弃，重得它们需要**按 LEDGER:4185-4208 记载的口径重新实现探针**（属新探针开发，非复算），本报告不做。

**旁证（顺带闭合）**：R-035 主结论的门禁 `tools/verify_r035_claims.py` 在盘、只读（仅 open EXE/RTTI/symbol_map 三个读句柄），重跑 **23/23 PASS, exit 0**（`step2_verify_r035.stdout.txt`）——LOWER 13,352 / 对齐 12,792 / UPPER 13,683 / 覆盖率 4.28%…4.07% / E9 虚高 1,445 / 幻影 563/560 / 锚点 0x403A80 四路零引用 全部复算成立。即「欠账不影响 R-035 主结论」这句话的门禁依据今日仍在盘、仍绿。

---

## STEP 3 · kb 卷与 lead 线 6 探针交叉对照

方法：逐探针提取其依据的 VA/类布局/字段偏移，然后在 `re_atlas/`（kb 七卷 + LEDGER + INDEX + CONFLICTS + HANDOFF + evidence/）做定点检索（列出所用模式），kb 有登记的给文件:行与该处结论，无登记的如实报「检索无命中」。

### 六行对照表

| # | 探针（写域外依据件） | kb 是否已覆盖 | kb 证据位置与该处结论 | 判定 |
|:--|:--|:--|:--|:--|
| 1 | 虚表 slot2 调用面 0x54A4F0/0x54A630（`lead/slot2_fullscan_20261111/`） | **部分重叠（登记面仅 RTTI 原料）** | 有：`evidence/rtti/symbols.json:1774-1793`（DynamicVectorClass\<PAUTileInsertType@IsometricTileTypeClass\>，vtable 0x7ECBDC，vfuncs 第 3 项=0054A630）与 `:8785-8798`（VectorClass 同族，vtable 0x7ECBFC，第 3 项=0054A4F0）；`classes_meta.json:822-827/4047-4051`。kb/20、kb/22 两卷虚表契约均**无**该族 slot2/Capacity 条目，`call [reg+8]` 全 .text 普查（1,714 站）、唯一派发点 0x546069、唯一实例 0xAA1078、初始化/析构对 0x543E70/0x543EB0 在 re_atlas **检索无命中**（模式：`54A4F0|54A630|7ECBFC|7ECBDC|AA1078|546069`、`slot2|call \[reg\+8\]`） | **新增为主**：kb 只有机器 dump 的类名/虚表/槽函数清单，无语义；lead 的调用面普查与唯一性证明 kb 没有 |
| 2 | 0x0054A56E 数据依赖链（`lead/re_crashwriter_static_20261110/`） | **部分重叠** | 有：同上 symbols.json 两处 RTTI 行；DynamicVectorClass 字段布局家族在案：`evidence/class_contract.json:871-872`（vptr[+0] data[+4] capacity[+8] grow[+0xC] flag[+0xD] count[+0x10]，`call [edx+8]` 虚 Add）、`evidence/r043_l30_housevec.py:16-21`（0xA80228 init/degrade vptr、Count/CapacityIncrement 布局注记）；free 原语 `0x7C8B3D`/`0x7C8E17` 已登记 `INDEX.md:187-188`；「按 [esi+0xD] 调 0x7C8B3D 释放→清 +0xD/+8」同族形态在案 `CONFLICTS.md:324-326`（G-15，INIClass 析构）。0x54A56E 本位点、0xAA1078 生命周期与 normal/post-atexit/corruption 三态可达性 **检索无命中**（含 `84F2BA` 无命中） | **新增为主**：free-then-null 家族形态 kb 有同类例证，但该链路本体（含崩点语境解释）是 kb 之外的新知识 |
| 3 | HouseClass owner 归属（`lead/re_orphan_owners_20261110/`） | **部分重叠（kb 已有注册表定谳，无 ctor/字段表）** | 有：`HouseClass::Array`=0x00A80228 `kb/00_global_skeleton.md:145`（标注社区/待复算）+ R-043 定谳「注册表=DynamicVectorClass\<HouseClass*\>、finder 0x502D30 整函数钉死、元素写入 0x4F61EC」`LEDGER.md:4794-4817`、`STATUS.md:499`、`kb/21_swizzle_and_object_fields.md:405`、`INDEX.md:959`；HouseClass 尺寸 0x160B8=90,296 `kb/20_vtable_contract.md:113`、`evidence/class_ids.txt:19`、vtable 0x7EA8A0 `evidence/size_indep.txt:5`；`HouseClass::Player` 0xA83D4C `kb/00:144`。无：ctor 0x4F54A0 本体与 span、Type@+0x34/ID@+0x30、Name@+0x15FF4、12×CounterClass +0x5500..+0x55DC、big-zero +0x57E4、HouseTypes 0xA83C98、NoInit ctor 0x4F7140、parser 用的 `INIClass::Get_Int 0x475540`——**检索无命中**（模式：`(?i)4F54A0|A83C98|15FF4|4F7140|5009B0|4F61EC|F54A0`、`(?i)475540`）；0x5009B0 仅作为「Houses/Country ident 归属宿主」出现在 `evidence/r036_r13_deliverable.txt:2996-2999` 与 `evidence/ebp_this_census.txt:12`（DISPATCH，未命名） | **部分重叠**：数组/finder/尺寸/自注册站点 kb 已钉（R-043 直接复用价值最高）；ctor 全解码+字段偏移表+HouseTypes 是 lead 新增 |
| 4 | 地图预置槽位解码（`lead/re_map_preset_decode_20261110/`） | **kb 无（属 kb 职责面外的知识类型）** | kb 十卷无地图文件实体表（[Units]/[Infantry] 逐 house 槽位、per-house 240+160、型号分布）知识；kb/10_map_triggers.md 只覆盖触发器族引擎结构；`evidence/ini_keyindex.txt` 是 **exe 侧 INI 键普查**，非地图文件解析。检索无命中（`Units|Infantry` 预置语义类）。探针④本身也不依赖 exe 类布局（纯文件侧 INI 解析，XMP29U2.MAP sha256 0add791d…df60bc 实算在案 `_md_parse_out.txt:7`） | **新增**（但注意：这不是 kb 的缺口——kb 定位是 gamemd.exe 静态知识库，地图文件谱系本不在其范围） |
| 5 | LoadBench 逐维比对（`lead/re_loadbench_diff_20261110/`） | **kb 无（同上，职责面外）** | kb 无任何 LoadBench 地图谱系条目；探针⑤产出为六维文件比对+谱系锁定（`_ld_diff_out.txt`），不涉及 exe VA | **新增**（职责面外，非 kb 缺口） |
| 6 | PlayerControl / PercentBuilt 语义（`lead/playerctrl_semantics_20261111/`） | **部分重叠（键级已有，字段/写入点/消费者没有）** | 有：`HouseClass::IsPlayerControl 0x0050B6F0` 全函数反汇编已裁定、单人读 `+0x1EC/+0x1ED` `CONFLICTS.md:37-63`、`kb/00_global_skeleton.md:156-165`、`INDEX.md:169`；INI 键级归属在案：`evidence/ini_keyindex.txt:4142-4143`（'PlayerControl' ReadBool 0x00500BD6 @~0x00500B40）、`:4091-4092`（'PercentBuilt' ReadInteger 0x0042EC0C @~0x0042EBE0）、`:3872-3873`（'NodeCount' 0x0042EC1E）、`:3782-3783`（'MultiplayPassive' 0x00511A8A）、`:338/:549`（TechLevel/Credits @0x500B40）；INIClass 读取器 VA `kb/30_ini_subsystem.md:713-714/1686-1691`（ReadInteger 0x5276D0/ReadBool 0x5295F0/GetKeyCount 0x526960/GetKeyName 0x526CC0）。**且 kb 自己挂了账**：`CONFLICTS.md:274` P-4「HouseClass 尺寸 90,296 与 +0x1EC/+0x1ED **字段语义待 HouseClass 模块**」。无：Read_INI **写入侧**（PlayerControl→+0x1ED 存储点 0x500BDD、TechLevel→+0x1D4、Credits→+0x1DC）、PercentBuilt→BaseClass+0x1C=HouseClass+0x571C、读/写函数对 0x42EBE0/0x42ED60 语义、运行期消费者 0x4F6EC0/0x50A5C0、场景加载派发 0x686B20 vs 0x687F10（0x686B20 本身有符号条目 `evidence/symbol_map.json:18127`，语义无）——检索无命中（模式：`500B40|42EBE0|42ED60|571C|4F6EC0|50A5C0|687F10|PercentBuilt|NodeCount|PlayerControl` 等） | **部分重叠**：键→函数归属 kb 已有；**写入点/字段偏移正是 CONFLICTS P-4 的挂账**，lead 探针补的是 kb 明示待补的东西 |
| 3b | （附）HouseClass 计数问题 kb 侧在案相关性 | 事实 | LEDGER.md:581-582/1887/2115/2356 反复登记「GOAL-3T 在飞 units0/HouseClass 衰减线与本线零交集」——即 RE-ATLAS 当初**主动让出** HouseClass 计数线（禁区协调），不是漏做 | 判定修正依据：不能把「HouseClass 细节 kb 没有」读成「RE-ATLAS 失职」，这是双方约好的分工边界（文件在案） |

**六行小结**：0 行「纯重复造轮子」；2 行「新增」（探针④⑤，且属 kb 职责面外）；4 行「部分重叠」（探针①②③⑥——RTTI 原料/注册表定谳/键级归属/读取面 kb 已有，语义层与写入侧 kb 没有）。RE_PROGRESS §6-5「避免重复造轮子」的建议方向成立但表述过强：**lead 线不是在 kb 已有结论上重复，而是在 kb 的原料层之上补语义层**；真正可省的重复只有一处形态——探针①②重复解码了 kb RTTI dump 已含的类名/虚表（可改为先查 `evidence/rtti/symbols.json` 再决定是否写探针）。

---

## STEP 4 · 复活条件判断（明确区分判断与既有结论）

### 4.1 文件里的既有结论（转引，标出处）

- 「RE-ATLAS 已停摆 12 天、最后轮 R-064=2026-10-30」——RE_PROGRESS §1-4/§2（日期细节本报告已订正为 mtime 10-30，见 STEP1.2）。
- 「两条欠账待 C 会话独立复算」「不影响 R-035 主结论」——STATUS.md:62/259、r036_r13_deliverable.md §六 :222-223。
- 「R-036b 地址类探针已跑完即删」——LEDGER.md:4221-4222。
- 「761/426,741 对 GOAL-3T 的影响：**无**；引用过请改用实测值」——HANDOFF_TO_GOAL3T.md:1423。
- 「让 RE-ATLAS 重新接上：VA 反查走 kb/ 已有卷」——RE_PROGRESS §6-5。
- 「RE-ATLAS 主动让出 HouseClass/units0 线（禁区协调）」——LEDGER.md:581-582 等。

### 4.2 本报告的判断（以下是我从 STEP1–3 读数推出的，不是文件既有）

1. **断供对 ①/② 的实际影响：中低，且被 HANDOFF 的「影响：无」基本说中。**
   依据（事实面）：①「为什么慢」的硬卡点是 D-13 采集授权（RE_PROGRESS §5-3），② 的硬卡点是观测实现缺陷（§3）——都不是 kb 内容能供给的；六探针里 exe 侧反查需求 kb 只能**部分**供给（六行表：4 行部分重叠里 kb 供给的是 RTTI 原料、注册表定谳、尺寸、键级归属、读取面），缺的语义层（ctor 字段、slot2 面、写入点）kb 也确实没有。所以「停摆」没有直接卡死 ①/② 的当下推进，但持续停摆会让 lead 线在「类布局/字段偏移」这类可沉淀知识上持续自造探针，口径分裂风险随轮数累积。
2. **「重复造轮子」的修正判断：六探针 0 行纯重复。** lead 线实际在 kb 原料层之上补语义层；RE_PROGRESS §6-5 若执行，应表述为「先查 kb/RTTI 原料，再写探针」而不是「直接走 kb 卷」——因为 kb 卷里根本没有探针①②⑥要查的语义条目。
3. **复活的最小动作（判断，按性价比排序）：**
   - **动作一（最小，纯追加）**：把本次写域复算结果按 §7 追加进 LEDGER 新开一轮（如 R-065）：欠账 B（523,181/48.7%）**闭合**（附 step2 stderr 两行 REGISTER + 引擎与门禁 8/8）；欠账 A 登记「闭包类单口径已复算（758/path=425 与原跑逐字一致），地址类四列脚本在案声明已删、未复算」。两条「待 C 会话独立复算」挂账即可结一条、改写一条。
   - **动作二（把 lead 读数升格为 kb 登记）**：六探针的 `_out` 读数按卷归位——kb/11 补 HouseClass 字段表（+0x30/+0x34/+0x15FF4/+0x5500 段/+0x57E4、HouseTypes 0xA83C98）、kb/20 或 kb/22 加 slot2 调用面注记（0x54A4F0/0x54A630/0xAA1078/0x546069）、kb/30 或 kb/00 补 Read_INI 写入链（0x500B40→+0x1D4/+0x1DC/+0x1ED），并在 CONFLICTS P-4 落「+0x1ED=PlayerControl 存储位、+0x1EC 待查」——这是把「未交付原始读数」变成知识库存量的最短路径。
   - **动作三（可选）**：若要闭合 761 分列，按 LEDGER:4185-4208 记载口径重写地址类探针并走门禁+变异流程；不做也不阻塞其余复活工作（该分列已被判定「不采用」）。
   - **复活无技术阻塞**：RE-ATLAS 的门禁套件今日重跑全绿（verify_r035 23/23、r036 8/8），停摆形态是「无人开轮」而非「跑不动」。
4. **【未证】边界**：上述第 1、2 条判断只针对**登记面覆盖**，不背书 lead 六探针读数本身的正确性——它们无门禁/变异/盲验（RE_PROGRESS §4 已定性为「未交付的原始读数」）；本报告未验证任何「机制/因果」主张（如 0x54A56E 可达性对崩溃的解释、HouseClass 计数与卡顿的因果），一律不在本报告下结论。

---

## 边界与未验（诚实账）

1. **本报告未验的项**：
   - R-036b 地址类规则四列 418/149/290/289——脚本在案声明已删（LEDGER:4221-4222），未复算，未重实现。
   - R-036 闭包类「12 种组合 730…838」扫描——扫描脚本不在盘，本次只复算了盘上单口径（758）。
   - 原始 523,181 测量当时所用闭包参数与盘上 `closure()`（cap=8000）是否逐参一致——不可证（原脚本未落盘）；本次是「盘上引擎+在案定义」的复算，结果逐位吻合。
   - INDEX.md/STATUS.md/LEDGER.md 6,801 行未逐行读——只做定点检索、头部/欠账节/R-036b/R-064 节读取；「kb 无登记」类结论的检索模式与范围已逐条列出，但不排除同义表述（如用别名指称同一 VA）在未读段落存在的可能。
   - lead 六探针 `_out` 读数的技术正确性未复核（本次只取其登记面做 kb 对照）。
   - `evidence/r036_r13_deliverable.txt` §D 5,882 行逐站点明细未逐行抽查（其生成门禁已复算 PASS）。
2. **只读边界执行情况**：
   - 既有件零改动：`step1_fingerprint.py` 首跑与末跑两次全量指纹 diff = **498/498 文件 path/bytes/mtime/sha256 全等**（step1_manifest_baseline.tsv vs step1_re_atlas_manifest.tsv，Compare-Object 空）。首跑基线取于两次复算脚本执行**之前**，故该 diff 同时证明复算执行未改任何既有件。
   - 全部写操作仅落在 `lead\re_atlas_reassess_20261112\`；未 git commit/push/reset/checkout；未启动任何游戏进程、未 attach、未读活进程内存、未写 hook/采样类代码。
   - gamemd.exe 指纹重算 = sha256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`、4,825,360 B（与 re_atlas 交付锚一致；只读打开）。
3. **环境**：python 3.12.10、capstone 5.0.7（`python -I -X utf8 -c "import capstone"` 实测）；两个复算脚本运行时长各约 4–9 分钟（后台执行，exit 0）。

---

## 收尾回执

**改了哪些文件**（全部为写域内新建，零既有件改动）：
`lead\re_atlas_reassess_20261112\` 下 — RE_ATLAS_REASSESS.md（本件）、step1_fingerprint.py、step1_re_atlas_manifest.tsv、step1_manifest_baseline.tsv、step1_fingerprint.stdout.txt、step2_r036_rerun.py（= 盘上 r036_r13_deliverable.py 的逐字节副本 + 明示标注的 8 行 OVERLAP 读数增量块）、step2_r036_rerun.stdout.md、step2_r036_rerun.stderr.txt、step2_verify_r035.stdout.txt、step2_verify_r035.stderr.txt。

**跑了哪些命令**（关键项）：
1. `python -I -X utf8 ...\step1_fingerprint.py`（×2，首跑=基线、末跑=收尾核验，diff 空）；
2. `Copy-Item re_atlas\tools\r036_r13_deliverable.py <写域>\step2_r036_rerun.py` + 双侧 Get-FileHash 相等（007DBF5E…27B1A）+ edit 插入标注增量块；
3. `python -I -X utf8 <写域>\step2_r036_rerun.py` → **8/8 PASS** + REGISTER OVERLAP 两行（523,181/48.7% 与 510,807/50.1% 逐位复现）；
4. `python -I -X utf8 re_atlas\tools\verify_r035_claims.py` → **23/23 PASS, exit 0**；
5. `Get-FileHash gamemd.exe`（=73201CC0…F67476，4,825,360 B）；
6. `Select-String '^## R-\d+' LEDGER.md`（73 个轮次标题，末轮 R-064@2026-10-30）；
7. re_atlas 全目录清单与分组计数（step1 TSV + Get-ChildItem）；
8. 对 re_atlas 的十余组定点 grep（模式逐条列于 STEP3 表内）。

**结论一句话**：RE-ATLAS 停摆属实（末轮 R-064=2026-10-30，73 轮，最晚件 mtime 10-30 12:39），两条挂账欠账中「523,181/48.7% 重叠」已在写域用盘上门禁引擎**逐位复算闭合**、「761 分列」的闭包类口径可复跑（758/path=425）而地址类脚本在案声明已删不可复算；lead 六探针对照 kb 为「0 重复 / 2 新增 / 4 部分重叠」，故断供对 ①/② 当下影响有限（中低），复活最小动作 = LEDGER 追加一轮结账 + 把六探针读数按卷归位（均无技术阻塞）。

**遗留未验项**：R-036b 地址类四列（脚本已删）；闭包类 12 组合扫描（脚本不在盘）；原始 523,181 所用闭包参数与盘上引擎逐参一致性（【未证】，仅结果级吻合）；INDEX/LEDGER 未逐行通读（「无登记」结论以列出的检索模式为界）；lead 六探针读数本身未经门禁化复核。
