# S10-KPROVED UNKNOWNS

| # | 项 | 状态 / 处理 |
|---|---|---|
| U1 | D-39 未裁 | 338 行只有活 vptr 安装/vt imm32 引用，按卡面只登记 `D39_CANDIDATES.tsv`，保持 `[静态推断]`。 |
| U2 | 58 行过 C1 判据但目标 40 | 多出的 18 行列 `EVIDENCE/unselected_c1_pass.tsv`，不扩交、不写 grade。 |
| U3 | capstone op.index 措辞 | 卡面称无 index 返回 0；本环境实测 x86 operand 无 `op.index` 属性而 `op.mem.index=0`。用更保守的 op.type/op.mem.index 判定。 |
| U4 | `004CBBA0` 无 vtable slot | direct-call 环④成立但未找到 slot/RTTI；proof 与 delta 明示 atlas-only，不编类名或槽。 |
| U5 | ⑱ 冲突扫描 | 40 entry 在 docs/re/台账/COVERAGE 共 89 行命中；仅登记地址级命中，未改 name/subsystem。 |
| U6 | 未落盘 COVERAGE | proved=157 为内存复算，待合并员落盘。 |
| U7 | 环①②独立性 | 有 slot 行用 atlas+slot 与 global-vptr；atlas-only 行不声称 RTTI，靠 body 与外部环④。 |
