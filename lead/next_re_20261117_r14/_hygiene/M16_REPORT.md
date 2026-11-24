# M16_REPORT（≤25 行）
1. 改 name：盘上前名 `AircraftClass::slot99` —— 与卡面所述 K13 名 `AircraftClass::ApplyMode2CellRefreshWithSubcellCounters_behavior` 不符（M15 曾明确排除该行、未并 K13，故从未进阶为 K13 behavioral 名）。依「以盘上为准、如实报告差异」，如实记录该差异；现名改为 K14 `FootClass::Mode2CellAndMissionStateRefresh_behavior`。
2. 改 one_line_semantics：用 S10_K14 语义栏替换原 slot99 占位语义；删去编造的 `0x816CAC` Mission 表与幽灵被调 `0065C7E0`，改为真实 `[vt+0x184]` getter(005B3040) 枚举比较 + `005657A0 MapClass::TryGetCellAt` 环④（K14 仅剩环②③④）。
3. grade：保持 `[静态推断]`，未升 `[已证]`（K14 缺环①，禁止提级）；evidence_path/n_sources/conflict/subsystem 四列均未改。
4. grade 分布 before = after：`[未证]` 11031 / `[静态推断]` 6031 / `[已证]` 1369 —— 逐位相同（唯一自检点通过）。
5. 行数：before=after=18,431（无新增/删除 entry）；逐行比对仅 entry `004D85D0`（物理行 3159）第 3、4 列变化，其余 7 列逐字节一致。
6. PANEL：S10 proved 现值 `114/526 = 21.6730%`（面板列 114 / 21.67），与卡面相符；grade 未变故 proved 无需刷新，PANEL.md 未修改。旁注：name 由 slot99→behavioral 会使 S10 strict 名义计数 78→79，本卡按「只检查 proved / 不要为了对齐而改」未动 PANEL，提请 lead 裁定。
7. PENDING_CORRECTIONS.tsv：+1 行（`M16 / 004D85D0 / name+one_line_semantics`），注明「name+semantics 更正，grade 未变」并附返工卡号 `S10_K14`；数据行 262→263。
8. 快照 `_hygiene/M16_before/`（coverage.tsv / PANEL.md / PENDING_CORRECTIONS.tsv）SHA-256：
   before coverage.tsv  E5F7BF9726D7BF935EC83D10BB64775C7CC069DC0E8797864B9A3FE1CB5B8B81
   before PANEL.md      A8C9D2E438E19CB95C6896AED231C02DFEB8951666F8AF7910D12FB7F718AE6D
   before PENDING       9C3BB325B02F4B57B1383557210C08C4FF6B19C08DE77EADA0979A47BECFD911
   after  coverage.tsv  4B2435804E5CDC55E787486B1F7E4E4FC528224145867210DB0615FF45CC2C4F
   after  PENDING       EF02D7CAA1071FC051F485946E20152ED38EA0BC9B713E7982BDAD8990D5514A
   PANEL.md 未改（SHA 同 before）
