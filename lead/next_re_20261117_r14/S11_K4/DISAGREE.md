# S11-K4 · DISAGREE（引用台账节号）

| # | 对象 | 本卡结果与处理 | 依据 |
|---|---|---|---|
| D1 | 派卡写 proved 约 29/368≈7.9% | 一致，无冲突：现场自算 coverage∩atlas=368、proved=29、named=358。没有照抄卡面；baseline_recompute.py 独立复算 | EVIDENCE/baseline_recompute.txt；台账 §981 六 |
| D2 | 台账 §972 的 6A imm8 陷阱 | 复现且遵守：11 个工厂 push 中 6A=10 / 68=1；若只扫 imm32 会漏 10 个。未把 imm32 单边失败当“不闭合” | EVIDENCE/closure.txt；台账 §972 四-1/五-1、§981 二 |
| D3 | 006C41D0 = Jumpjet CI（K2 DISAGREE D4 / §981 九） | 确认旧值错：独立 RTTI 工厂表 0x7F3C90 slot3 指向 006C4190；006C41D0 未在本卡 vtable/CI 闭合中。因该行盘上已 [已证]，本 delta 不改其名，留 UNKNOWNS U6 待合并员裁定 | EVIDENCE/layout.txt；EVIDENCE/closure.txt；台账 §981 九 |
| D4 | §981 IPersistStream slot9 措辞 | 按审计必改措辞执行：写 off0 主表 slot9（0–7=IPersistStream、8=析构、9=Size），不写 IPersistStream 的槽 9 | EVIDENCE/closure.txt；台账 §981 三/九 |
| D5 | §8.1 ① vtables_v2.json 槽数错 / §8.1 ⑧ RTTI 链 | 复现：全 RTTI 自扫 1,214 表/14,044 槽；类名一律 COL+0xC→TD+8 内联串，读不到 fail-closed。未使用 JSON 槽数、未把 TD+8 当指针 | EVIDENCE/shape_counterexamples.txt；EVIDENCE/layout.txt；R14_COMMON §8.1 ①⑧ |
| D6 | 台账 §981 的 WhatAmI/取槽风险 | 方法继承、结论不外推：Locomotor 11 处 B8 imm32 C3 全在 off0 slot9 且双点闭合；off4 slot11/12 不是 size。未把 B8 imm32 C3 裸形态用于 WhatAmI 定名；五类 slot35/36 反例已复现 | EVIDENCE/shape_scan.txt；EVIDENCE/shape_counterexamples.txt；台账 §981 四 |
| D7 | 新升 331 行的语义边界 | 升级依据是 RTTI+.rdata vtable 槽直指（入口/VT/COL/TD/槽字节/首指令字节），只证明结构归属；不把结构归属冒充高层算法语义。高层语义未证者沿原名并在 UNKNOWNS U5 登记 | EVIDENCE/entry_evidence.txt；coverage_delta.tsv；R14_COMMON §8.1 错源“字段偏移不能定语义” |
