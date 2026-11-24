# S10-K3 · DISAGREE

| # | 对象 | 本卡结果与处置 | 依据 |
|---|---|---|---|
| D1 | 卡面 88/513≈17.15% | 盘上现值为 S10 ∩atlas **526**、proved **88**（16.73%）；S10 coverage 528 行、表外 2 行。按纪律 9 用盘上值，不沿用 513。 | EVIDENCE/baseline_recompute.txt；COVERAGE/PANEL.md S10=526/88 |
| D2 | DoD 门槛“≥257” | 该数来自 513 分母；526 的 50% 门槛是 ceil(526/2)=**263**。本卡交 23 行，合入 111/526，仍差 152。 | EVIDENCE/validate_delta.txt |
| D3 | named≈97% vs 硬规则 slotN 不计 named(S) | 两者口径不同：PANEL/L 为 511/526；严格排除 slotN/vslotN/sub_ 后为 29/526。未把槽名当语义，也未改共享 PANEL。 | EVIDENCE/validate_delta.txt；PROGRESS 核心数字 |
| D4 | S11-K4 FAIL（331 行 vtable 槽直指） | 完全避开：本卡 23 行均带函数体自身证据（B8 imm + 工厂 push/ctor 写 vptr；或 0x1C2 入口到 ret + dispatch 结果写回），无一行仅凭“在虚表里”。 | EVIDENCE/whatami_s10.txt；EVIDENCE/getsize_s10.txt；EVIDENCE/mission_noop_s10.txt |
| D5 | S10-K2 已交 37 行 | 那 37 行已在盘上 88 中；本卡只挑当前 grade≠[已证] 的 23 行，未重复计数。 | EVIDENCE/validate_delta.txt old_nonproved 检查 |
| D6 | 19 行 no-op 使用同一语义族 | 每行 name 带唯一 entry 后缀，满足“一个 name 只覆盖一个 entry”；接受判据不是 RTTI 槽归属，而是逐函数 body `b8c2010000c3` + 10 NOP + dispatch caller `call [vptr+disp]` 与 `mov [esi+8],eax`。 | EVIDENCE/mission_noop_s10.txt；coverage_delta.tsv |
| D7 | 0x1C2 是否被当 AbstractType | 否。0x1C2=450 不在 enum 0x00..0x49，且未走 WhatAmI 通道；这些行按 Mission 行为型 no-op 证明。 | EVIDENCE/semantic_census_s10.txt；EVIDENCE/whatami_s10.txt |
| D8 | 未升 0x5B3970 / 0x5B3A60 / 0x5F5E80 | 有行为线索但方法名需槽继承推断，超出允许的 1–4 类；按“证不出保留原级”处理。 | EVIDENCE/nonupgraded_candidates.txt |

## 纪律自检
- 双通道：通道 A 为覆盖入口裸字节 + capstone 入口到 ret；通道 B 为全 RTTI/vtable + 工厂 push/ctor 写 vptr 或 dispatch 表/结果写回；至少一条不依赖 atlas entry+size。
- 类名仅认 COL+0xC→TD+8 内联串；读不到 fail-closed。未用 Ghidra、未改游戏文件、未写台账、未 git commit。
