# M49 PROGRESS — 登记 MEASURE-F3A 两条「既有事实被字节证伪」（只登记不裁决、不改 coverage）
卡号 M49（登记卡，不改 grade）。项目根 D:\Project\ra2-campaign-forge。写域：COVERAGE/CONFLICTS.tsv、COVERAGE/PENDING_CORRECTIONS.tsv、M49\、_hygiene/M49 备份；其余只读。
输入（只读）：MEASURE_F3A/PROGRESS.md、UNKNOWNS.md、F3A_CLASS.tsv。未改 coverage.tsv / PANEL.md / 台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli；未 git commit、未建 venv、未 pip install。

## 实际列名（本卡描述与既有结构不同处）
- CONFLICTS.tsv 实际 5 列：entry, field, source_a(card:value), source_b(card:value), status（表头逗号分隔、数据行 TAB 分隔；无「备注」列，来源注脚并入 status，与既有行同口径）。field 取被证伪事实所在 coverage 列名 one_line_semantics。
- PENDING_CORRECTIONS.tsv 实际 7 列：card, entry, field, current_value, audited_value, source_section, source_verdict（无 issue/target 列：issue→current_value，target→audited_value，来源→source_section+source_verdict）。

## 登记 1 · 004C93D0（S18）
status=OPEN:语义被字节证伪-待重写；source_a=盘上现值「帧CRC量化helper(obj+0x388/0x3A0)…仅被0x64DAB0…字段物理语义[未证]」；source_b=MEASURE-F3A 实测（体内无 0x388 与 0x3A0、187 个 E8 站点含 0064DAF7）；来源注脚=MEASURE_F3A/PROGRESS.md 与 UNKNOWNS.md。
## 登记 2 · 00522340（S10）
current_value=语义栏混入台账坐标片段 ledger S12/[未证]/sub_，[未证]非自陈未证；audited_value=one_line_semantics 措辞清理；语义本身已证（③b 自查锚全部过字节复核）；来源同上。

## 必做自检 (a)-(d)
(a) 行数（表头+数据）：CONFLICTS 478→479（+1，表头1+数据477→478）；PENDING 275→276（+1，表头1+数据274→275）。两表各加 1 行，无多/少。
(b) coverage.tsv SHA-256 改前 e397af8695895c7dce7160c7dfc6cc251a96277babb4929378427bc8090ad48b → 改后 e397af8695895c7dce7160c7dfc6cc251a96277babb4929378427bc8090ad48b，完全相同（未动）。
(c) 两表 SHA-256（全串）与备份路径：
  - CONFLICTS 改前 97768645d1a11d358f44c79ad8cbf3c65a65ad64fa246b146926864d2164bf6a → 改后 d54a2c3c984238d2f4c5b2dc8e0b44ca9070a16fd78192e46900cb17d76d4d60。
  - PENDING 改前 4cb723ccdbc89a6ab9d60a56f7c9ace68f2dafc917baaf993793919d5e1dd3a0 → 改后 0d76f1b152c26a70c4e0de13bc333a679aea0b87847eb6db9b8264739f319dbc。
  - 备份 _hygiene\M49_before\CONFLICTS.tsv、_hygiene\M49_before\PENDING_CORRECTIONS.tsv（备份实测 SHA 与各自改前一致）。
(d) 列数逐行核（表头逗号 / 数据 TAB，两种分隔符同列数）：CONFLICTS 表头 5 列、478 数据行全 5 列，异常 0；PENDING 表头 7 列、275 数据行全 7 列，异常 0。多列/少列 0。
四项全部符合，无停下理由。只登记、不裁决、不改 coverage.tsv。
