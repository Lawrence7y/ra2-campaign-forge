# DISAGREE · S08-K1
- D1 卡面预警「19 行 slot 语义大概率 direct=0」成立；但实测全 22 行有 3 个 strict direct 入口（其中 2 个可升），不是 0。证据见 `DIRECT_ONLY.tsv`。
- D2 优先候选 `004309D0` 只满足二进制通道，不满足「YRpp CALL/JMP 原文行或既有独立真名记录」；按卡面 fallback 到 `0047F250`，未编名。
- D3 命名冲突按 ⑱ 只报不改：`0047EFE0` 前卡名 `MapClass::DrawShroudFogLayer` 与 `docs/re/ARCHITECTURE_ATLAS.md:4336` 的 `Draw_Shroud` 不一致；本卡未改该行。
- D4 卡面 n=22 与盘上原始 S08=23 的差异来自分母口径：`0065B800` 不在 atlas，`atlas∩coverage` 复算恰为 22。
- D5 目标 B 未达 10 行，按卡面如实报「最多 2 行」，未放宽到 atexit 析构器表、槽号匹配、slot-baseline 或 P=R=100% 自证。
