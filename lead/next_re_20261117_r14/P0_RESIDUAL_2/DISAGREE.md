# DISAGREE.md — P0-RESIDUAL-2 与看板/PANEL 的冲突与引节

## D1 · gap 数字：改"估计值"为"枚举清单"（结论 (c)）
- **引节**：`COVERAGE\coverage_unresolved.md` §"三个数"/"性质说明"（"≈222 是估计值非枚举清单，逐地址裁定需另立卡"）；`COVERAGE\PANEL.md` §"三分母"行"剩余未裁定缺口 ≈222（222–820）"；`STATUS_BOARD.md` §"P0 分母修订" 待办（"另约 222 条需补通道"）。
- **本卡结果**：本卡即该"另立卡"。ENUM.tsv 给出 **5,656** 地址的逐地址裁定（FUNC 20 / NOT_FUNC 38 / UNDECIDABLE 5,598），把模糊的 ≈222 变成**枚举清单**。
- **不冲突之处**：本卡**不推翻** 14,715 混合模型本身（那是审计已入账 `[已证]`）；但证明"≈222 是通道不完备上限"这一性质**仍未闭合**——独立 oracle `0x7775C0` 与 2,026 个 FPU 叶函数证明通道仍漏，故真实缺口**不小于**本卡枚举的 UNDECIDABLE 集，222–820 区间的"上界 820"缺乏枚举支撑。

## D2 · coverage.tsv 截面 14,493 → 14,495（并发并表）
- **引节**：`R14_COMMON.md` §7 "coverage.tsv 实测（W180）=14,493"；`PANEL.md` §三分母=14,493；任务卡 §2 现状表=14,493；`STATUS_BOARD.md` §P0 分母修订=13,397/14,493。
- **冲突**：会话期间 M2 合并员把 coverage.tsv 改为 **14,495**（+`005B3740`/`006C41D0`）。Lead 已裁定（消息 2026-11-17）改用当前截面 14,495。
- **处理**：本卡所有对 coverage 的比对用当场重读的 14,495（元数据见 UNKNOWNS U3 / EVIDENCE/stats.json）。**未修改 coverage.tsv**。请 PANEL 维护者据 M2 并表同步 PANEL 三分母表的 14,493→14,495（本卡不写台账/COVERAGE）。

## D3 · 通道完备性（与"P0 已收口"表述的限定）
- **引节**：`STATUS_BOARD.md` §"P0 出口闸验收"结论"P0 入口集合闭合达成——但仅就当时已知的 476 个"；§"P0 分母修订" 证据要点 1（"`0x7775C0` 漏检 ⇒ 通道不完备，1,096 只是下界"）。
- **本卡结果**：一致但更进一步——新通道 F/G/H 仍漏 `0x7775C0`（首字节 0x51）与 FPU 叶函数族。⇒ "通道不完备"从"已知 476 之外"延伸到"新通道之后仍不完备"。结论取 (c)，不是 (b)（缺口非空）。

## D4 · N_pool 7,228 vs 审计 7,229
- **引节**：P0-RESIDUAL `_audit\a13_mixture.json`（N_pool=7,229）。
- **本卡**：7,228（边界差 1，见 UNKNOWNS U4）。属边界细节，非口径冲突；已在 PROGRESS 披露，不凑数改为 7,229。

## D5 · 负对照 B_RAIL 标签歧义
- **引节**：`P0_GATE\EVIDENCE\B_RAIL_C5_EXCLUDED.tsv`（5 条标 R14-R10 B NOT_FUNC）vs `P0_GATE\ENTRY_ADJUDICATION.tsv`（同 5 条 verdict=FUNC/source=true_entry）。
- **本卡**：如实报两者；按审计主表口径判 FUNC 不算假阳性。见 UNKNOWNS U6 / COUNTERFACTUAL §3。

## D6 · 未使用/不可用的 PE 结构
- **引节**：任务卡 §T1 通道 H（"异常/SEH 目录 `.pdata` 若有、增量链接 ILT/thunk"）。
- **本卡**：PE 实测无 EXCEPTION/LOAD_CONFIG(SafeSEH)/TLS 目录，`.pdata`/ILT/SafeSEH 子源为空。通道 H 退化为仅 `jmp_abs`/detour/内联 SEH 扫描，零新增。如实记录，不臆造不存在的结构。
