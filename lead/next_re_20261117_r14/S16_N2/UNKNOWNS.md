# S16-N2 · UNKNOWNS

| # | 项 | 状态 | 已试通道与证据 |
|---|---|---|---|
| U1 | 9 条 sub_ 的真实语义名 | [未证] | 全部 YRpp 2188 文件按 6/8 位地址大小写全扫 0 绑定；docs/re 403 文件仅 0065E660 一处带名字记录且归属冲突；re_atlas/kb 8 文件 0；台账 + S16-K1/K2/K3/N1 VERDICT/UNKNOWNS 只给语义不给名；全镜像 dword 指针扫描 0 个 vtable 引用；CONFLICT_CLASS2 仅 Class::sub_ 占位（违禁令 1）。逐条见 PROGRESS.md ②。 |
| U2 | 0065E660 名字归属冲突 | [未证] | superweapon_re.md:783-784 与 re_sprint_S2:139-140 写 SpawnAircraftEdge(0x65E660 -> 0x4AA440)；radar_sweep_sw_deep_dive.md:64 把 SpawnAircraftEdge 给 0x4AA440；YRpp MapClass.h:287 定 0x4AA440=PickCellOnEdge、HouseClass.h:428 定 0x65EAB0=SendSpyPlanes。0x65E660 YRpp 全库 0 绑定 ⇒ fail-closed 不命名。 |
| U3 | 0053D8E0 螺旋坐标分解的 edx 语义 | [未证] | 台账 32165 U4 明记「语义未追全，本卡未命名交付」；本卡复算十六进制分解正确但无异源名字。 |
| U4 | grade 变动 | [已证] | 9 行逐行读盘确认，盘上现 grade → 交付 grade 全部相同；proved 前后各算 46/90，无虚报「未动」。 |
| U5 | 卡面基线 73/46 vs 盘上 81/46 | [已证] | 卡面为 N1 并入前截面；盘上 coverage.tsv ∩ atlas 实测 named 81/proved 46；按 ⑨ 以盘上为准并如实记录。 |
| U6 | 真机 DoD #5 / KB S16 | 缺 | 本卡只做攒名字，按令不碰。 |
