# S11-K5 · DISAGREE

| # | 对象 | 本卡结果与处理 | 依据 |
|---|---|---|---|
| D1 | 卡面“不要低于 15 行就不做” | 方法已跑通但合法候选不足：11 条真语义重证、0 条 grade 升级、0 条非已证可升。按硬规矩不凑数，并在 UNKNOWNS U1 明写 | EVIDENCE/candidate_census.txt；EVIDENCE/validate_delta.txt |
| D2 | K4 审计 FAIL：331 行语义已证 0 | 接受裁决；未把 RTTI+vtable 槽直指当语义，未把 Class::slotN 当结论。331 行原级保留 | S11_K4/_audit/VERDICT.md；EVIDENCE/candidate_census.txt |
| D3 | K4 审计脚本把 9 行写成 “const_return(B8 imm32 C3)” | 逐字节复核：004B4820 等 9 行为 `b8 imm32 c2 04 00`（ret 4），不是 `c3`。本卡将其列为人形反例，不计入允许类型 | EVIDENCE/candidate_census.txt；EVIDENCE/entry_shapes.txt |
| D4 | K2/K4 已把 11 个 GetSize 行升为 `[已证]` | 一致，无重复计数；本卡只重证并加固证据，delta 明写 grade 不变，合入后 proved 不增加。11 行中 10 行在 atlas、1 行表外 | EVIDENCE/validate_delta.txt；coverage_delta.tsv |
| D5 | 全 RTTI 69 类 WhatAmI 契约（kb/20） | 独立复算：enum 74 项、off0 slot11 语义匹配 69 类、slot11/slot12 同形态 69 类（取错槽风险成立）；但这些 entry 不在 S11 覆盖集，故 0 升级 | EVIDENCE/abstract_type_enum.txt；EVIDENCE/whatami_candidates.txt |
| D6 | 盘上覆盖数字 | 现场复算与卡面一致：S11 379、∩atlas 368、proved 29、named 358、门槛 184；未触发纪律 9 停机 | EVIDENCE/baseline_recompute.txt |