# S12-Q2 UNKNOWNS（未闭合项）

| # | 项 | 状态 | 说明 / 证据 |
|---|---|---|---|
| U1 | 多格建筑 foundation 偏移的完整语义 | `[静态推断]` | 挂链包装 `0x5683C0` 用槽 `+0x108` 取 foundation CellStruct 数组并逐项叠加 base（`0x568446..0x568468`）；但"哪些 building type 有几格、槽 +0x108 返回值在各朝向下的确切内容"未逐类型枚举。纯单格建筑路径 A 不依赖它。证据 `W176_place81\EVIDENCE\T2_callee_5683C0_head.txt` |
| U2 | `CellClass.MapCoords`(+0x24/+0x26) 作为坐标自检的可靠性 | `[静态推断]` | `docs/re/cellclass_offsets_evidence.md` §二有实证但该文档含勘误 E1（挂钩点 EAX 语义被证伪）；+0x24/+0x26 本身在其勘误中"维持成立"，本卡未独立逐字节复现该偏移（取格公式已由 `0x5657A0` 独立证）。 |
| U3 | 13 个 +0x520 写点中 6 个"其它 Techno 族同偏移"的类归属 | `[静态推断]` | `0x44EA5A`/`0x4DC823` 抽样见 `EVIDENCE\other_520_writes.txt`；另 `0x6679AE`/`0x710EC7`/`0x7594C3`/`0x759EC3` 未在 BuildingClass vtable 上下文；可能是 Unit/其它 TechnoClass 的同偏移字段（纪律 16：偏移不能定语义）。不影响 BuildingClass 结论。证据 `EVIDENCE\q1_520_writes.txt` |
| U4 | `GetCell()`（直接返回 CellClass\* 的虚槽）精确槽号 | `[未证]` | 本卡两条路径用 GetMapCoords(槽 +0x1B8)+GetCellAt(0x5657A0)，未单独定名 YRpp 中 `GetCell()` 的槽号；slot +0x68(0x4544A0)/+0xF0 等带参函数经 GetCellAt 但不是无参 GetCell。探针用路径 A/B 已够。 |
| U5 | 真机验证 | `[未证]` | 本卡是静态卡，无真机授权/未启游戏；配方待后续真机卡执行（②-b C1/C2 链展开）。 |
| U6 | `0x5657E0`（相邻 `setne al` 变体）精确命名 | `[静态推断]` | 同索引公式但返回 bool（是否占用/有效），可能是 `MapClass::IsCellPresent` 类；未定名，未纳入配方主路径。证据 `EVIDENCE\getcell_5657A0.txt` |
