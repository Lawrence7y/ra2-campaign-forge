# S16-N2 · DISAGREE

| # | 事项 | 本卡立场 | 依据 |
|---|---|---|---|
| D1 | 卡面写「S16 named 73、并入 N1 后 81」 | 盘上已是 81/90；卡面为 N1 并入前截面 | coverage.tsv ∩ function_atlas.tsv 自算：S16 全表 92、atlas 内 90、named_L 81、proved 46；N1 8 行已在盘上为 LightningStorm::Start 等真名。按 ⑨ 以盘上为准，不自造差异。 |
| D2 | docs/re 把 0065E660 与 SpawnAircraftEdge 关联 | 不同意据此定名 | 同一名字在 radar_sweep:64 指 0x4AA440，YRpp MapClass.h:287 定 0x4AA440=PickCellOnEdge、HouseClass.h:428 定 0x65EAB0=SendSpyPlanes；0x65E660 本身 YRpp 0 绑定 ⇒ 名字归属冲突，按 ⑱ fail-closed。 |
| D3 | S16-K2/K3 的 Class::sub_ 占位算不算 named | 本卡不采用 | a-S16-K2 VERDICT ★A / a-S16-K3 VERDICT ★C / 台账 32607：该形式全表先例 0、语义上是占位，且本卡硬禁令 1 明确禁止。 |
| D4 | 调用者名（如 caller=SuperClass::Launch）能否当被调函数名 | 否 | 0053DDA0/006CE240/006CE320 的异源记录只给 caller 名；调用者语义不能转嫁给被调函数，且同码 18 命中不特异。 |
| D5 | 被调者名（如 0x71ABC0=LetGo）能否当调用者名 | 否 | 0071AB60 体内 call 0x71ABC0，YRpp 只绑被调者；调用者 0x71AB60 本身 0 绑定。 |
