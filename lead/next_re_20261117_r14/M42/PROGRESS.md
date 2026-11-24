# M42 · PROGRESS

- 合并员 M42；开工 2026-11-19；写域仅 COVERAGE\coverage.tsv、M42\、_hygiene\coverage.M42.bak。未改 CONFLICTS.tsv / PENDING_CORRECTIONS.tsv / 台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli\；未 git commit、未建 venv、未 pip install。
- 任务A：并入 12 行 proved（S05_KPROVED2 8 + S09_KPROVED4 4），grade [静态推断]→[已证]，evidence_path 改指对应 _audit/VERDICT.md#行号。
- 任务B：并入 36 行语义补写（SEMFIX_SLOTS），仅改第 4 列，grade 一律不动。

## 12 行 entry 清单（任务 A）
S05_KPROVED2 delta 全部 8 行（逐行自 delta 读出）：
1 00413F80 → VERDICT#21（PASS）
2 006F4AB0 → VERDICT#22（PASS）
3 006F6AC0 → VERDICT#23（PASS，须补证）
4 0070C270 → VERDICT#24（PASS）
5 007077C0 → VERDICT#25（PASS）
6 00716DC0 → VERDICT#26（PASS）
7 007162F0 → VERDICT#27（PASS）
8 00700600 → VERDICT#28（PASS）
S09_KPROVED4 VERDICT §5 line35「应并入 4 行」白名单 4 行：
9 00557830 → VERDICT#21（白）
10 00577920 → VERDICT#23（白）
11 006568A0 → VERDICT#24（白）
12 006D02B0 → VERDICT#27（白）
S09 其余 4 行 004E2830 / 00565B00 / 006A7D70 / 00723EC0 **未并入**（审计 FAIL：③b 不成立或语义硬错；00723EC0 黑名单）。
审计按「白名单原样取」，4 个 entry 明确列出，无需回退逐行表、无需凑数。

## 按规则处置说明
- 12 行中 11 行盘上第 4 列为占位模板（含「槽语义未证」），按例外改用对应 delta 第 4 列（已核新语义无该字样、name 逐字节不变）；00413F80 盘上第 4 列非该占位模板，未动。
- 4 行 S09 盘上 name 为派生类名（ColorListClass / MouseClass / PowerClass / MouseClass），delta name 为归基类（ListClass / MapClass / RadarClass / TabClass）；按规则 name 不改，保留盘上值。
- A/B 无交集；36 行 SEMFIX grade 逐行核与盘上一致（均 [已证]，应降级 0），name 逐字节一致。

## 必做自检（全部通过）
- (a) 行数：改前 18,431 → 改后 18,431 数据行；entry 增删 0、无重复、全表 8 列合法。
- (b) grade 直方图：改前 [已证] 1,410 / [静态推断] 5,997 / [未证] 11,024；改后 [已证] 1,422 / [静态推断] 5,985 / [未证] 11,024（任务 B 不改 grade）。
- (c) conflict==1：254 → 254，不变。
- (d) 12 行逐行：grade 全 [已证]（12/12）、name 与改前逐字节一致（12/12）、evidence_path 全指 VERDICT.md#行号（12/12）。
- (e) 36 行逐行：新语义不含「槽语义未证」（36/36）、grade 未变（36/36）、name 逐字节未变（36/36）。
- (f) 全表复查 col4 含「槽语义未证」∧ grade=[已证] ∧ subsystem≠S22：改前 36 → 改后 **0**（验收指标达成）。
- (g) coverage.tsv SHA-256：改前 `08403cef279a209ce81a546835d364194c442aac4f9e9fcd2f5679c8a31b008a` → 改后 `abdd594dd0dac330b306d859eceb99d42cd13dc17aa5dc451d24544110c06a0c`；备份 `_hygiene\coverage.M42.bak` SHA 与改前逐字一致。

## 交付
- M42\PROGRESS.md、M42\MERGE_LOG.tsv（1 表头 + 12 A + 36 B = 49 行）。
- 改后 coverage SHA-256 前 8 位：`abdd594d`。
