# quotes.md · R17-GLM-TXT-3 引证集（文件:行号 → 原文）

## 第 1 项
- R17_R15_SLOT73\slot73_107.tsv:6 — `.?AVAircraftClass@@	0x007E22A4	341	0x004D3780	0x004196B0	NO / NO`
- R17_R17_SLOT73_MAP\four_classes.tsv:2 — `.?AVAircraftClass@@	0x007E22A4	341	0x004D3780	0x004196B0	0x007E23C8`
- （同法对 Infantry :4/:4=343/343、Unit :5/:5=344/344）

## 第 2 项
- slot73_107.tsv:2-6 — Building 0x007E3EBC / Techno 0x007F4960 / Infantry 0x007EB058 / Unit 0x007F5C70 / Aircraft 0x007E22A4
- four_classes.tsv:3 — `.?AVFootClass@@	0x007E8C94	341	…	0x007E8DB8`

## 第 3 项（逐行）
- four_classes.tsv:2 — 0x007E22A4 + 0x124 = 0x007E23C8（列值 0x007E23C8 ✓）
- four_classes.tsv:3 — 0x007E8C94 + 0x124 = 0x007E8DB8（列值 0x007E8DB8 ✓）
- four_classes.tsv:4 — 0x007EB058 + 0x124 = 0x007EB17C（列值 0x007EB17C ✓）
- four_classes.tsv:5 — 0x007F5C70 + 0x124 = 0x007F5D94（列值 0x007F5D94 ✓）

## 第 4 项
- hits.tsv:1 表头 — `site	class	disp	bytes	host	fn_end	base_reg	position_assert	disasm	base_source	verdict`
- 实测：数据行 354（:2 首行 `0x403CAC	stack_ff5424	…`；:355 末行 `0x7C34F6	mov	disp=0x124	…`）
- 分组实测：call=267 / mov=70 / stack_ff5424=9 / other_test_imm=7 / other_cmp=1（和 354）

## 第 5 项
- R17_R12_VT_OFFSET\REPORT.md:14 — `| 类别 | 0x124 | 0x1AC | 合计 | 扫描字节数/类 |`
- R17_R12_VT_OFFSET\REPORT.md:19 — `| 附带 push/cmp/test 等 | 16 | 0 | 8 | 4063232 |`
- R17_R12_VT_OFFSET\REPORT.md:23 — `- other_cmp: 0x124=1, 0x1AC=0`
- R17_R12_VT_OFFSET\REPORT.md:27 — `- other_test_imm: 0x124=7, 0x1AC=0`
- 对照自洽行：:16 `call [reg+disp32] | 181 | 86 | 267`（181+86=267）、:18 `mov reg,[reg+disp32] | 55 | 15 | 70`（55+15=70）、:20 `stack … | - | - | 9`

## 第 6 项
- R17_R14_VT_STRUCT\REPORT.md:16 — `- 槽数：322；不同值：322；重复值种类：0。`
- R17_R14_VT_STRUCT\REPORT.md:19 — `- 全部重复值已写入 `dups.tsv`（0 种）；下表为按次数降序前 0 项。`
- R17_R14_VT_STRUCT\dups.tsv — 实测 0 字节、0 行（连表头亦无）

## 第 7 项
- R17_R16_SLOT73_SEM\REPORT.md:21 — `- 整体判定：BuildingClass 槽 73 覆写为 0x43F180，并在其体内显式调用 TechnoClass 槽 73 实现 0x6F4A70 —— 推断（非字节证实）。`
- R17_R16_SLOT73_SEM\REPORT.md:20 — `- 同一对象判定：强推断，未取得全区间字节证实。`
- R17_R16_SLOT73_SEM\REPORT.md:32 — `- 若必须标注推断强度：弱推断（仅形态），像一个带标志门控的布尔判定或通知路径；不命名、不断言。`

## 第 8 项
- R17_AUDIT_R13\VERDICT.md:153 — `## 必改项（共 3 条；第 1 条为事实底座级）`
- :155 `### 必改 1（高）· 屏蔽执行方的 `data_va_refs = 0`，或补上"仅数据节/不含指令立即数"的限定`；:167-168 修法为列名/表述级
- :170 `### 必改 2（中）· `names.tsv` 的 `addr` 列名与内容不符`；:174-175 修法为改名/口径统一
- :177 `### 必改 3（低）· REPORT 缺正控/反控，按 §2.8 规则 A 退回`；:180-182 修法为补写 REPORT
- 类名链结论未被推翻：:19 A1 AGREE、:43 A2 AGREE、:62 A3 AGREE、:89 A4 AGREE、:115 A5 AGREE

## 额外：类名逐字比对
- 三串在 R17_R15_SLOT73 / R17_R17_SLOT73_MAP / R17_AUDIT_R13 的出现数：Building 8/11/13，Techno 8/7/14，Foot 4/15/5；全部逐字 `.?AVBuildingClass@@` / `.?AVTechnoClass@@` / `.?AVFootClass@@`。
- R17_R15_SLOT73\REPORT.md:45 — `全部有 #73/#107 的索引 vtable 中命中目标函数的条目数：1；明细：.?AVBuildingClass@@@0x007E3EBC。`（第三个 `@` 为名字@地址分隔符，名字本身完整）
- R17_R15_SLOT73\class_index.tsv:107/:127/:190/:230/:342/:470/:490/:554/:594 — 含 BuildingClass/FootClass/TechnoClass 的模板类 RTTI 名（如 `.?AV?$DynamicVectorClass@PAVBuildingClass@@@@`），属其它类名，非目标串变体。
