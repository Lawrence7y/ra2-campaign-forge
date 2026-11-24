# 卡 R17-GLM-TXT-3 · 纯文本/表内算术第二意见（限 8 项，不做字节判定）

## 〇、边界（超界整卡作废）
你**只**判断两件事：① 同一事实在不同文件里的文字表述是否一致；② **表内数字的加减是否自洽**。
**严禁**：字节级判定、装配形态判定、宿主身份判定、函数边界判定、类名正确性判定。
**严禁**超过 8 项。本卡恰好 8 项。

## 一、要核的 8 项（逐项 AGREE / DISAGREE / 无法判定 + 一句原文引证）
1. `R17_R15_SLOT73\slot73_107.tsv` 里五类的 `slot_count` 与 `R17_R17_SLOT73_MAP\four_classes.tsv` 里同名类的 `slot_count` 是否**完全一致**？
2. 两张表里 `main_vtable` 是否一致（BuildingClass `0x7E3EBC` / TechnoClass `0x7F4960` / Infantry `0x7EB058` / Unit `0x7F5C70` / Aircraft `0x7E22A4` / Foot `0x7E8C94`）？
3. `R17_R17_SLOT73_MAP\four_classes.tsv` 的 `main_plus_0x124` 列，是否**每个都等于**该行 `main_vtable + 0x124`？（逐行算一遍）
4. `R17_R12_VT_OFFSET\hits.tsv` 的数据行总数是否为 **354**，且按 `class` 列分组是否恰为 `call 267 / mov 70 / stack_ff5424 9 / other_test_imm 7 / other_cmp 1`？
5. 由此，`R17_R12_VT_OFFSET\REPORT.md` 命中数表里「附带 push/cmp/test 等 | 16 | 0 | 8」这一行的 `0x124` 单元格**是否应为 8**？（即 16 是否与 7+1 矛盾）
6. `R17_R14_VT_STRUCT\REPORT.md` 称 322 槽「不同值 322、重复 0 种」——请核该报告是否**同时**给出了重复值表文件（`dups.tsv`）且其为空（只有表头）。
7. `R17_R16_SLOT73_SEM\REPORT.md` 是否明确把「覆写读法」标为**推断**（而不是字节证实）？
8. `R17_AUDIT_R13\VERDICT.md` 的必改项是否为 **3 条**，且三条都属**报告表述**层面（而非推翻类名结论）？

## 二、额外一条只读检查（不计入 8 项）
在 `R17_R15_SLOT73`、`R17_R17_SLOT73_MAP`、`R17_AUDIT_R13` 三个产物里，
三个类名字符串 `.?AVBuildingClass@@` / `.?AVTechnoClass@@` / `.?AVFootClass@@` 是否**逐字一致**（大小写、`@@` 结尾、`?$` 模板形式）？
若有任何拼写变体请指出文件与行。

## 三、输出
- 每项一行：`#n` + 结论 + 一句原文引证（注明文件与行号）。
- 最后一行：`OVERALL: CONSISTENT` 或 `OVERALL: 有冲突（列项号）`。

## 四、铁律
1. 只读；**不得修改任何文件**。
2. 产物只写 `lead\next_re_20261117_r14\R17_GLM_TXT_3\` 下 `VERDICT.md`、`quotes.md`。
3. `VERDICT.md` 开头**如实写明你自报的 provider 与 model id 原始字符串**（看不到写 未回报）。
4. 严格 **5 分钟**。