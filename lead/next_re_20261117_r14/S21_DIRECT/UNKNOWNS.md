# S21-DIRECT · UNKNOWNS

## U1 数据集口径：raw coverage 132 行 vs atlas∩coverage 129 行
⑨ 停机核验采用卡面口径 atlas∩coverage = **129 行**（named 91 / proved 26 / 静态推断 91 / 未证 12，逐字吻合卡面）。
raw coverage.tsv 中 subsystem=S21 共 132 行，其中 3 行无 function_atlas.tsv 条目、不入卡面集：
`0046FC00 CampaignScoreClass::slot1` / `00690C00 ScoreTimeClass::slot3` / `00690D60 ScorePrintClass::slot3`（均 [静态推断]、虚槽名）。
本卡不动这 3 行；如 Lead 口径改回 raw，需另裁。

## U2 既非 direct 亦非 virtual 的未升格行（4 行）
S21 非 proved 共 103 行 = 35 direct 升格 + 64 VIRTUAL_SKIPPED + 4 行两者皆无：
`00596300` / `00597380` / `005C97B0` / `0063A4B0`（均 [静态推断]，源文件模块线索）。
此 4 行保留原 grade。

## U3 ⑬ 风险（入口已证 ≠ 语义已证）—— 卡面唯一判据仍为 direct call
35 行中 34 行为 sub_ 占位名、one_line_semantics 为字符串/模块/弱信号线索；direct call 只证明「入口真实、被真调用」，
**不证明 name/semantics 已证**。本卡按卡面「只动 grade、不动名字/语义」执行，names/sem 与 coverage.tsv 逐字一致（0 差异）。
审计若按四环要求 ③ 体内语义锚，以下 5 行自述含弱/未证信号，最易被降级（如实标注、不预裁）：
`00539760` / `0053AB50` / `00558790` / `00595740`（"弱信号"）、`004C3E30`（"语义[未证]"）。
唯一具名行 `0053AF40 PsyDom::Update` 语义完整，direct caller `0053A742`。

## U4 ⑱ 按地址查全库（只报不改名）
扫描 618 文件（docs/re + re_atlas/{kb,evidence} + COVERAGE + 台账），35 地址共 **190 处命中**。
绝大多数为本行自身证据（模块/字符串线索 r036_r13_deliverable.txt、ini_keyindex.txt、所在函数引用）与 coverage.tsv 本行，
属同源自记（§8.5 主条），不构成第二条命名通道、不升格语义。
少量软性语义归属仅报不改：`00686B20` 在 docs/re/ARCHITECTURE_ATLAS.md 记「场景全局更新 / Global_Update」；
`00599650` 在 docs/re/house_team_ai_update.md 被猜为「逐 House 调 Update 循环（可能）」。名字一律未改。

## U5 调用者子系统分布（观察项，非过滤条件）
35 行中 10 行有 S21 自身调用者，25 行仅被跨子系统调用（S01/S04/S06/S07/S09/S10/S13/S14/S16/S18/S19/S22）。
跨子系统直呼在引擎内合法（caller owner 与 entry 分属不同子系统），**不作为排除条件**；
card 三条件（E8 边界 / site+5+rel32==entry / 非自环）已全满足，caller 明细见 EVIDENCE/direct_call_sites_clean.tsv。

## U6 指令数口径（错源 D）
RawSize 全扫 **1,394,186** 条指令（100% 覆盖 4,063,232 B）；VirtualSize 口径 **1,392,592** 条（与项目基准逐字一致）。
两者 E8@边界/真 call 均为 **68,253**。与 S20_DIRECT 审计结论同口径，不影响任何交付站点。