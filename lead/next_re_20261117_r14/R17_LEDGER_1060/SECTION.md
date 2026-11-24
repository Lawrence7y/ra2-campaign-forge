## §1060 · 书记员覆盖 R17 第 7–8 轮（vtable 定名 + slot73 全映射 + 两审 + GLM 两卡）：九事项草稿

> 书记员只起草本节，不写主台账、不改控制文件、不改 coverage.tsv。全部数字已按盘面复算，逐项细目见同目录 numbers.tsv；与卡面不符者并列报出，取不到者直书「未取得」。
> 复算发现两处卡面数字与盘面不一致：事项 3 的 0x7E22A4 slot0、事项 7 的 0x4264C0 命门类数。两处均在正文中并列给出卡面值与复算值，不擅自择一。

### 1 · R12 首个「定偏移虚派发」扫描：形态海量、调用方链为零，且报告自含一处算术错

R17_R12_VT_OFFSET（hy4）第一次把尺子从 `[reg+reg*4]` 索引型换成 `call [reg+disp32]` 定偏移型，扫描 .text raw 全 4063232 B/类。盘上 `hits.tsv` 数据行复算为 **354**，分类逐项复算：`call [reg+0x124]` 181 + `[reg+0x1AC]` 86 = **267**；`jmp` 两类全表计数为 **0**；`mov reg,[reg+disp32]` 55 + 15 = **70**；另 `stack_ff5424` **9**、`other_test_imm` **7**、`other_cmp` **1**。分解回加：267+70+9+7+1 = **354**，与数据行数自洽。判定列复算为 NO_CALLER_LINK 290 / NON_TARGET(base from stack) 64，合计亦 354。

🔴 报告表格「附带 push/cmp/test 等」行写作 `16 | 0 | 8`：0x124 单元格 16 是算术错。本机从 `hits.tsv` 复算该格 = `other_cmp` 1 + `other_test_imm` 7 = **8**，合计栏 8 本身正确；故并列报出「卡面/实测应然值 8」与「报告原写 16」，差 8。此错由 GLM 卡2 #5 发现、Lead 从原始数据复核，此处为第三次独立复算。

结论边界：形态大量存在，但 354 条无一处能把基址寄存器钉成目标类对象，全判 NO_CALLER_LINK（栈基址者另判 NON_TARGET）；这不等于该槽从不被派发，仅说明本尺子不能证明调用方。

证据路径：`lead\next_re_20261117_r14\R17_R12_VT_OFFSET\REPORT.md`；`lead\next_re_20261117_r14\R17_R12_VT_OFFSET\hits.tsv`；`lead\next_re_20261117_r14\R17_R12_VT_OFFSET\controls.tsv`。

判定理由（与其余事项不同）：本事项的价值在于首次换尺子后的「海量命中 vs 零调用方链」反差，并额外承担一次表内算术自检，不与后续定名或语义判定混同。

### 2 · R13 用 RTTI 链给九个 vtable 定名；988 是分散内联名而非一张总表

R17_R13_NAME_TABLE（hy4，本轮 headline）走 `vtable[-4]` → COL → `+12` pTD → `+8` 内联名四跳定名：`0x7E3EBC`/`0x7E3EA0`/`0x7E3E98`/`0x7E3E90` = `.?AVBuildingClass@@`；`0x7F4960`/`0x7F4944`/`0x7F493C`/`0x7F4934` = `.?AVTechnoClass@@`；`0x7E4E78` = `.?AV?$DynamicVectorClass@H@@`。Q3 独立检验：TechnoClass 组与 R14_COMMON §2.6 一致。

名称表复算：`names.tsv` 数据行 **988**，前缀 `.?AV` **962** / `.?AU` **26** / `.?AW` **0** / 其它 **0**，段列 988/988 全为 `.data`。这 988 个是各自独立的 TypeDescriptor 内联 name 字段，不是一张 988 项指针总表；等距结构只有 3 段 stride `0x18` 数组、共 17 项。

强度限定（本事项即卡面指定的限定落点）：这些类名的来源是二进制内 RTTI 自证，属于从对象布局侧推得；按 `R17_R16_SLOT73_SEM\REPORT.md` 的分界，**不得**把「BuildingClass 覆写 TechnoClass 槽 73」写成已证——该读法只是推断，`edi` 是否全程承载同一 this 保持未字节证实。类名链条本身的可信度另见事项 3 的跨家族审计。

证据路径：`lead\next_re_20261117_r14\R17_R13_NAME_TABLE\REPORT.md`；`lead\next_re_20261117_r14\R17_R13_NAME_TABLE\names.tsv`；`lead\next_re_20261117_r14\R17_R13_NAME_TABLE\vtable_owner.tsv`；`lead\next_re_20261117_r14\R17_R16_SLOT73_SEM\REPORT.md`（仅用于强度限定）。

判定理由（与其余事项不同）：本事项确立的是「名字从哪来」的命名通道，并在此处先把语义外推堵死，与事项 3 的独立复核、事项 5 的槽归属刻意分工。

### 3 · AUDIT-R13 跨家族审计：A1–A5 全 AGREE + 全表闭环，但一条 slot0 数字并列报出

AUDIT-R13（deepseek，跨家族、独立实现、未 import 执行方逻辑）对 A1–A5 全判 **AGREE**。全表闭环复算：`.data` 内 TD 记录 **988** 条且名字互异；`.rdata` 内 COL **1201** 条，其 pTD 全部命中这 988 个 TD（1201/1201 = **100%**）；1201 条 COL 全部能被某 vtable 以 `[-4]` 指回；**954** 个 offset=0 主 COL 的 pSelf 恰为 COL−0x10；`.text` 内各有 3 处连续 `C7 06/46 04/46 08/46 0C` 立即数写入作独立旁证。分布 863/13/78（1/2/4 条 COL）呈多重继承子 vtable 形态。

**类名结论的证据强度（必须同写）**：类名结论**已过跨家族审计且 A1–A5 全 AGREE、链条字节证实 + 全表闭环**；但「哪张 vtable 属于哪个类」是**由 COL→TD 推得**，不是从代码调用推得。A4 分辨力进一步支持这一点：自选 `0x7E22A4`→AircraftClass、`0x7E4EEC`→CellClass、`0x7E8C94`→FootClass（另 `0x7EA8A0`→HouseClass、`0x7E3278`→AlphaShapeClass），五种结果互异，认证据不被槽内容带偏。必改 3 条均属报告表述、非结论：列名 `data_va_refs` 需限定为仅数据节、`names.tsv` 的 `addr` 应改名 `name_va`、REPORT Q2 缺正控/反控。

⚠️ 数字并列报出：卡面称 `0x7E22A4` 与 `0x7E8C94` 的 slot0「同为 0x410260」；本机从 `R17_AUDIT_R13\_audit_extract.json` 复算 `a4[0].slot0 = 4276880 = 0x414290`（Aircraft）、`a4[2].slot0 = 4260448 = 0x410260`（Foot），二者**不同**；审计 `VERDICT.md` 的 A4 表自身也列 Aircraft=0x414290、Foot=0x410260，真正同为 0x410260 的是 CellClass(`0x7E4EEC`) 与 FootClass(`0x7E8C94`)。故并列记「卡面 0x410260（同值断言）」与「实测 0x414290 / 0x410260」，不改写任一方。分辨力结论本身不受影响——不同类名仍由 COL→TD 决定，只是同槽值那一对的举例有误。

证据路径：`lead\next_re_20261117_r14\R17_AUDIT_R13\VERDICT.md`；`lead\next_re_20261117_r14\R17_AUDIT_R13\chain.tsv`；`lead\next_re_20261117_r14\R17_AUDIT_R13\_audit_extract.json`；`lead\next_re_20261117_r14\R17_AUDIT_R13\controls.tsv`。

判定理由（与其余事项不同）：本事项核的是第三方独立审计的闭环与分辨力，并第一次触发「卡面数字 vs 盘面数字」的并列报出，既不重复事项 2 的命名推导，也不进入事项 5 的槽归属。

### 4 · R14 结构判定：322 槽全唯一，守「零类名」边界

R17_R14_VT_STRUCT（hy4）读 `[0x007E3EBC, 0x007E43C4)` 共 1288 B / 322 槽。复算 `slots.tsv` 数据行 **322**、不同值 **322**、重复值种类 **0**；`0x43F180` 全表仅出现在 #73、`0x449440` 全表仅出现在 #107；三张小表 T0/T1/T2 分别 **2/2/7** 槽（11 = 2+2+7），与主表同值交集 **0** 种。结构判定「更像一个类的正常 vtable」仅按字节结构判据。

全文零类名、未越界：报告明确「类名/继承层级/函数语义：未取得」，不写任何 `.?AV…@@`，因此不与事项 2 的定名结论冲突——这里是刻意留白，不是否定定名。

证据路径：`lead\next_re_20261117_r14\R17_R14_VT_STRUCT\REPORT.md`；`lead\next_re_20261117_r14\R17_R14_VT_STRUCT\slots.tsv`；`lead\next_re_20261117_r14\R17_R14_VT_STRUCT\dups.tsv`（0 B，与重复 0 种一致）。

判定理由（与其余事项不同）：本事项只做形状统计并主动放弃命名，是全套里唯一以「不取」为结论的一节，边界功能与其余各节相反。

### 5 · R15 槽归属排他性：1211 索引里两函数仅 BuildingClass 主表命中

R17_R15_SLOT73（hy4）索引规模复算：`class_index.tsv` **1211** 个 vtable / distinct class_name **951** 个（仅 `.?AV*` 类 RTTI；TD 候选 961、其中 951 有 vtable 引用）。五类主表槽数与槽值复算：BuildingClass `0x7E3EBC` 322 槽，#73 `0x43F180`、#107 `0x449440`；TechnoClass `0x7F4960` 309 槽，#73 `0x6F4A70`、#107 `0x4264C0`；InfantryClass `0x7EB058` 343 槽、UnitClass `0x7F5C70` 344 槽、AircraftClass `0x7E22A4` 341 槽，三者 #73 **均 `0x4D3780`**。

判定：全部有 #73/#107 的索引 vtable 中命中目标函数的条目数为 1，即 `.?AVBuildingClass@@@0x007E3EBC`；未取得项 0，五个主表槽数均 ≥108，不存在「槽不存在」。故 `0x43F180` 与 `0x449440` 判 **BuildingClass 专有**。R14_COMMON §2.6 的「所有 TechnoClass 派生可放置对象共用」只针对 `+0x14` 的 bit0 与唯一写点 `0x6F322F`，不外推到这两个槽；Infantry/Unit/Aircraft 的 #73 同为 `0x4D3780` 也不是 `0x43F180`，不得写成「共用本函数」。

证据路径：`lead\next_re_20261117_r14\R17_R15_SLOT73\REPORT.md`；`lead\next_re_20261117_r14\R17_R15_SLOT73\class_index.tsv`；`lead\next_re_20261117_r14\R17_R15_SLOT73\slot73_107.tsv`。

判定理由（与其余事项不同）：本事项用的是「类名→全部 vtable」的正向索引做排他性归属判定，与事项 7 的反向全量枚举方向相反，也不同于事项 4 的无名统计。

### 6 · 三重印证：coverage 的 004D3780 [已证] 行被四条 +0x124 独立字节算址印证

`COVERAGE\coverage.tsv` 中 `entry=004D3780` 恰 1 行，语义称 slot73 位于 `0x7E23C8`/`0x7E8DB8`/`0x7EB17C`/`0x7F5D94`，grade `[已证]`。本机四条加法逐条复算：Aircraft `0x7E22A4 + 0x124 = 0x7E23C8`、Foot `0x7E8C94 + 0x124 = 0x7E8DB8`、Infantry `0x7EB058 + 0x124 = 0x7EB17C`、Unit `0x7F5C70 + 0x124 = 0x7F5D94`——**四条全等**。entry 按格式要求写作大写 8 位 `004D3780`（无 `0x`），地址一律带 `0x`。

⇒ 该 `[已证]` 行被独立字节分析印证；本事项只做算址对账，不改动 coverage 行的 grade、不改 coverage.tsv 任何字节，也不把它与事项 5 的 BuildingClass #73 混为一谈。

证据路径：`lead\next_re_20261117_r14\COVERAGE\coverage.tsv`；`lead\next_re_20261117_r14\COVERAGE\coverage_README.md`；`lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\four_classes.tsv`。

判定理由（与其余事项不同）：本事项是唯一把外部台账既有 `[已证]` 行拿来与本地字节算式对账的一节，方向是「验证已有结论」而非「产生新结论」。

### 7 · R17 反向映射：0x4D3780 四族共用，0x4264C0 基类整族继承，且一处数字并列报出

R17_R17_SLOT73_MAP（hy4）从 21 个槽数≥108 的 vtable 取 #73/#107 共 42 个值，`reverse_map.tsv` 数据行复算 **42**，分 18 组。四个指定函数复算：0x43F180 **1**（BuildingClass #73）、0x449440 **1**（BuildingClass #107）、0x4D3780 **4**（Aircraft/Foot/Infantry/Unit 的 #73）、0x6F4A70 **1**（TechnoClass #73）。FootClass 补齐：`0x7E8C94` 341 槽，#73 `0x4D3780`、#107 `0x4D9C10`，与 Aircraft/Infantry/Unit 并排得到事项 6 的四个 +0x124 地址。

⚠️ 数字并列报出：卡面称 `0x4264C0` 出现在 **17** 个类的 #107；本机从 `reverse_map.tsv` 复算 `function_value=0x004264C0` 且 `slot=107` 的行数为 **15**，`R17_R17_SLOT73_MAP\REPORT.md` Q1 的「0x004264C0（15 项）」分组亦为 15。故并列记「卡面 17」与「实测 15」，差 2，不擅自择一。无论 15 还是 17，「典型基类方法整族继承」的定性不变；该项只影响数量陈述。

证据路径：`lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\REPORT.md`；`lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\reverse_map.tsv`；`lead\next_re_20261117_r14\R17_R17_SLOT73_MAP\four_classes.tsv`。

判定理由（与其余事项不同）：本事项是唯一从「函数值→类」反向全量枚举的一节，用途是暴露整族继承而非排他归属，并因此成为第二处卡面数字的并列报出点。

### 8 · GLM 两卡：纯文本第二意见有实效，但不用于字节级判定

卡1（R17_GLM_TXT_1，自报 `bigmodel-api/GLM-5.3-Flash`）8 项全 AGREE、`OVERALL: CONSISTENT`，额外一条判「无」——现势表述中未发现把 ②-b 写成「已证」。卡2（R17_GLM_TXT_2，同一自报身份）7 项 AGREE、**#5 DISAGREE**，正是事项 1 的 R12 表格算术错（`| 附带 push/cmp/test 等 | 16 | 0 | 8 |`，16+0≠8，而细分 1+7=8）。本机复算确认 #5 的 DISAGREE 成立。

⇒ 两卡证明 GLM 在「≤8 行纯文本/表内算术」上有实效（能抓出人写的 16/8 不自洽）；但按卡面纪律，仍**不用于字节级判定**，其所有 AGREE 只作文字一致性意见，不替代 AUDIT-R13 的独立字节复核。

证据路径：`lead\next_re_20261117_r14\R17_GLM_TXT_1\VERDICT.md`；`lead\next_re_20261117_r14\R17_GLM_TXT_1\quotes.md`；`lead\next_re_20261117_r14\R17_GLM_TXT_2\VERDICT.md`；`lead\next_re_20261117_r14\R17_GLM_TXT_2\quotes.md`。

判定理由（与其余事项不同）：本事项评的是外部模型作为第二意见的能力边界，既非字节证据也非台账结论，只界定「可用到哪一层」。

### 9 · R7 勘误：三处只增不改，哈希与 mtime 写前写后一致

新建 `R17_R7_REJECT_LAYER\ERRATA.md`（独占创建、未覆盖），三处勘误全部写入：① `jne` 起始 `0x47C73D` → `0x47C73F`（跳目标 `0x47C853` 正确）；② `0x47C853` = `5F`（pop edi）、`xor al,al` 在 `0x47C856`；③ `0x47C615` = `5E`（pop esi）、`C2 08 00` 在 `0x47C616`。每处含①原文片段②权威值③字节依据④定谳出处，格式齐备。

`R17_R7_REJECT_LAYER\REPORT.md` 的 sha256 与 mtime 写前写后完全一致（sha256 `0EB3D37B41C8777BB9EA2FF7C645D6000D4F05B533AE5E5EC27E0D4FD7E4FB72`；mtimeMs `1795239104954.8674`），报告全文 11694 B，未改动一字节——勘误只落在新文件，不回改原状。

证据路径：`lead\next_re_20261117_r14\R17_R7_ERRATA\REPORT.md`；`lead\next_re_20261117_r14\R17_R7_REJECT_LAYER\ERRATA.md`；`lead\next_re_20261117_r14\R17_R7_REJECT_LAYER\REPORT.md`。

判定理由（与其余事项不同）：本事项是文件治理型事项，判据是「新增载体的完整性 + 原载体零改动」的哈希/mtime 证明，与任何字节语义或类名判定无关。

---

本草为 §1060 草稿，由 Lead 逐字追加；书记员未自行改动台账。
