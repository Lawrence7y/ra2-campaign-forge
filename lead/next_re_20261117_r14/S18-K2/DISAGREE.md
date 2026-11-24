# S18-K2 · DISAGREE.md —— 与卡面前提/已入账值的分歧（纪律 9：不凑数）

## D1（硬分歧）· S18 分母：卡面 660 vs 盘上 659
- **卡面**：`PANEL.md` atlas **660**、named 496(**75.15%**)、proved 53(**8.03%**)。
- **盘上实测**（本卡 `work/t1_targets.py`，`python 3.12.10`）：
  - `coverage.tsv` 数据行 **18,431**；`function_atlas.tsv` **12,916**；
  - S18 总行 **663**、S18∩atlas **659**；
  - named_L **496 / 659 = 75.27%**；named_S **496 / 659 = 75.27%**（S18 无 `Class::sub_` 占位）；
  - proved **53 / 659 = 8.04%**；grade 分布 `[已证]53/[静态推断]552/[未证]54`。
- **盘上 PANEL.md L50**：`| S18 | 659 | 496 | 75.27 | 75.27 | 53 | 8.04 | 491 |` —— 与本卡自算逐格一致。
- **根因**：卡面用 660 作分母（496/660=75.15%、53/660=8.03%），而权威 atlas 分母为 659。属派卡口径警告（STATUS_BOARD「Lead 传子代理的数字可能是错的」）。
- **处置**：本卡一律用 **659 / 496(75.27%) / 53(8.04%)**；**未**改 `coverage.tsv`、**未**凑到 660。50% 门槛 ceil(0.5×659)=330，差 **277** 项 proved。**请审计复核 659 并请 Lead 更正派卡文。**

## D2（口径澄清，非事实分歧）· 「CRC 46 项」
- 卡面：「111 B / 46 项」「把 46 项逐项落地：每项 = 哪个对象/哪个字段、读宽度、在 CRC 串里的偏移」。
- 事实：F1 入账 **111 B**=`NetworkEvent` 结构大小；**46 项**=EventType 跳表项数（Kind 1..0x2E）。两者都是**事件**属性，不是 CRC 字段数。帧 CRC 每对象仅读 ~4–6 字段（CRC.md §3.2），无 46 字段结构；Checksummer 是全字段 CRC32，Add 调用 331 处（非 46）。
- **处置**：不编造"46 个 CRC 字段"。CRC.md §3.1 按权威口径落地 46 个 EventType，§3.2 给真实 CRC 字段表，§3.3 给标准 CRC32 本体。**请 Lead 澄清是否本意为「46 个 EventType 的事件串字段」**。

## D3（前序卡已纠正，本卡复核确认）· CRC 第 4 集合
- F1 PROGRESS N3 曾写「Aircraft」；a-S18-F1 VERDICT §5 更正为 **HouseClass**。
- 本卡独立复核：容器 `0xA8022C` vt→COL→TD = `.?AV?$DynamicVectorClass@PAVHouseClass@@@@`（`EVIDENCE/rtti_container_types.txt`）⇒ **HouseClass 成立**，与审计一致。已入账值无误。

## D4（精度瑕疵，已修）· desync 边界对齐点
- F1 正文曾写「真边界 `0x64C6AA`」；a-S18-F1 §4 更正为 **`0x64C6AC`**。
- 本卡复核：`0x64C6CC mov dl,[...+0x8B4211]` 是 7 字节指令，`0x64C6AA` 落其 disp32 内（伪 `inc edx`），`0x64C6AC` 才是边界。CRC.md §2.4 用 `0x64C6AC`。已入账更正无误。
