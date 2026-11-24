# S20-KPROVED UNKNOWNS

| # | 项 | 状态 / 处理 |
|---|---|---|
| U1 | capstone 5.0.7 的 `op.index` | 派卡纪律写“无 index 返回 0”，本环境实测 x86 operand **无 `op.index` 属性**；已按更保守方式只用 `op.type`/`op.mem.index`，并用 `EVIDENCE/capstone_index_selfcheck.json` 留证。 |
| U2 | D-39 未裁 | 294 行三环齐但只有活 vptr 安装/vt imm32 引用，按卡面保持 `[静态推断]`，只登记不升格。 |
| U3 | 构造器链反推的 global vptr 写 | 19 行 exact 中 5 行依赖构造器链（`EVIDENCE/global_ctor_vptr_writes.tsv`）：vptr 写站点 + caller 把 ecx 设为 global 两段字节证据；18 行有绝对 `C7 05` 写。D-39 裁前不把任何 C2 行并入。 |
| U4 | 25 行额外过 C1 判据 | 目标 40 行已选满；未交付行见 `EVIDENCE/unselected_c1_pass.tsv`，grade 全部保持 `[静态推断]`，不静默扩交。 |
| U5 | `0075F8B0` 冲突 | `COVERAGE/CONFLICTS.tsv:152-153` 有 subsystem（C09_census:S20 vs W174_dirty80:S07）与 name（WaveClass::slot54 vs fn_0075F8B0）OPEN 冲突；本卡只报不改 subsystem/name。 |
| U6 | 未落盘 COVERAGE | 写域只允许本卡目录；`并入后 proved=80` 是内存复算，需合并员落盘。 |
