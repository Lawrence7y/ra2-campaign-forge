# S12-Q2 DISAGREE

| # | 与谁的分歧 | 内容 | 本卡判定 / 证据 |
|---|---|---|---|
| D1 | `PROBE_TABLE.md`(W176) L7/L21 | 原假设 `obj+0x520` 指向 `MapClass`，据此由 obj 求 cell | **本卡不支持该假设**（真机已否证）。静态独立复核：`+0x520` 的 RTTI 类为 BuildingTypeClass（vtable `0x7E4570`），非 MapClass（`0x87F7E8`）。取格改走本卡 §2/§3 两路径。证据 `EVIDENCE\rtti_check.txt`、`CELL_PATH.md` §0 |
| D2 | 台账 §675（已由 R14_COMMON §1 作废） | §675 称 `0x43BCF0` 是 BuildingClass 构造函数、`+0x520` 来自"全局池 POP" | 本卡**遵守作废索引**：不引用 §675 的构造器结论；采用 §911/W152 的 `0x43B740` 为构造器（写 `[esi+0x520]=type` 参数）。`+0x520`=TypeClass 由 §678 + RTTI 支撑，与"池条目"叙事无关。证据 `EVIDENCE\w520_43B756.txt`、`R14_COMMON.md` §1 |
| D3 | `cellclass_offsets_evidence.md`（docs/re，含勘误） | 该文档 §四把 `(Y<<9)+X` 挂钩点前提（0x655D38 处 EAX=CellClass\*）已被其自身勘误 E1 推翻 | 本卡**不引用该挂钩点结论**，仅采用其勘误中"维持成立"的 `CellClass.MapCoords=+0x24/+0x26`（且标 `[静态推断]`，仅作自检）；取格公式 `(Y<<9)+X` 由 `0x5657A0` 独立反汇编证明，不依赖该文档。证据 `EVIDENCE\getcell_5657A0.txt` |
| D4 | 无（本卡内部一致） | — | 两条路径（A 内存重算 / B EIP 捕获）共用 GetCellAt `0x5657A0` 与 GetMapCoords `0x41BEA0`，但获取方式不同，均为静态可证；不互相否定。 |
