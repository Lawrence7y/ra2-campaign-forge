# 卡 R17-GLM-TXT-4 · 纯文本/表内算术第二意见（限 8 项，不做字节判定）

## 〇、边界（超界整卡作废）
只判断：① 同一事实在不同文件里的文字表述是否一致；② 表内数字加减是否自洽。
**严禁**：字节级、装配形态、宿主身份、函数边界、类名正确性判定。**严禁**超过 8 项。

## 一、要核的 8 项（逐项 AGREE / DISAGREE / 无法判定 + 一句原文引证，注明文件与行号）
1. `R17_R19_RTTI_XCHECK\reconcile.tsv` 的三桶计数是否与同目录 `REPORT.md` 所报数字一致（BOTH 209 / COVERAGE_ONLY 220 / RTTI_ONLY 779）？请按 tsv 的 `bucket` 列逐值计数核实。
2. 该 `reconcile.tsv` 的数据行总数是否为 1208（不含表头）？且 209+220+779 是否等于 1208？
3. `COVERAGE_ONLY` 里是否存在以 `AV` 开头、且去掉 `AV` 后能在 `BOTH` 里找到同名的条目？（只做字符串比对，给出条数）
4. `COVERAGE_ONLY` 里是否存在以 `PAV` 开头的条目？（给出条数）
5. `R17_R17_SLOT73_MAP\four_classes.tsv` 的 `main_plus_0x124` 是否逐行等于 `main_vtable + 0x124`？（逐行算）
6. `R17_R16_SLOT73_SEM\vtable_hits.tsv` 是否显示 `0x6F4A70` 在 TechnoClass 表出现 1 次、BuildingClass 表 0 次？
7. `R17_R18_EDI_GAP\edi_writes.tsv` 的数据行数是否为 4（不含表头）？地址是否恰为 `0x43F1DA`/`0x43F387`/`0x43F3DA`/`0x43F5C9`？
8. `lead\LEAD_LOCK` 的 `AB8` 段是否如实写了「GLM 三卡共抓出 2 处真实缺陷」以及「仍不用于字节级判定」这一边界？

## 二、额外一条只读检查（不计入 8 项）
`lead\GOAL_THREE_TARGETS_20261018.md` 的 `§1061` 里关于 R19 的那一句，是否把 `COVERAGE_ONLY 220` 与三条限制**写在同一处**（即未被拆开引用）？
只回答「同处/不同处」，不要评价数字对错。

## 三、输出
- 每项一行：`#n` + 结论 + 一句原文引证。
- 最后一行：`OVERALL: CONSISTENT` 或 `OVERALL: 有冲突（列项号）`。

## 四、铁律
1. 只读；**不得修改任何文件**。
2. 产物只写 `lead\next_re_20261117_r14\R17_GLM_TXT_4\` 下 `VERDICT.md`、`quotes.md`。
3. `VERDICT.md` 开头**如实写明你自报的 provider 与 model id 原始字符串**。
4. 严格 **5 分钟**。