# M41 · PROGRESS

- 合并员 M41；开工 2026-11-19；合并 S09_KPROVED3（4 行）+ S10_KPROVED2（8 行）共 12 行，`[静态推断]`→`[已证]`，evidence_path 改指对应 `_audit/VERDICT.md#行号`（S09 #19–#22、S10 #15–#22）。仅改第 5/6 列；004DB690/004DF040 另按审计改第 4 列 ③b 口径。name / subsystem / n_sources / conflict 逐字节不动。未建 venv、未 pip、未 git commit；未改台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli。

## 004D74E0 处置结论：并入（第 8 行）
- 成文 name `FootClass::slot81` 可由 S10_KPROVED2 `_audit/VERDICT.md` §2 line15、`PROGRESS.md` §8 行表、`EVIDENCE/per_row/004D74E0.txt` 取得；② 持有表 0x7E8C94/slot81、③b① 跳表 +0x5C（13 体，重映射 71 索引全<13）、④ 3 站点，审计判成立。
- 按「成文 name 可得」条件并入，MERGE_LOG 来源记「来源=审计 VERDICT §2，delta 缺失」。核盘发现 delta.tsv 实际已含该行（任务前提「delta 缺失」为陈旧描述），但成文 name 条件仍成立 ⇒ 结论并入，CONFLICTS 不登记待补。

## 004D85D0 与 ③b 口径
- 004D85D0：审计 §3 要求去掉未证 "MissionState" 字样；因 [vt+0x184] 槽语义仍 `[静态推断]`、无法确证新名，按规则保留盘上 name 不动并在 MERGE_LOG 记「name 收窄待裁」；CONFLICTS.tsv 追加 1 行 supersede（field=verdict，status=SUPERSEDE_BY_M41）。
- 004DB690：语义栏改写为「③b② 可证伪错误码（cmp edi,0x80004002 + jl）」（体内循环无显式写）。
- 004DF040：语义栏明写「累加器写」口径（其「写」是栈累加槽），否则按 D-42④ 字面应退 ③a。

## 必做自检（全部通过）
- (a) 行数：coverage.tsv 改前/改后均 18,431 数据行（含表头 18,432 行），entry 增删 0。
- (b) grade 直方图：改前 [已证] 1,398 / [静态推断] 6,009 / [未证] 11,024；改后 [已证] 1,410 / [静态推断] 5,997 / [未证] 11,024；和 18,431。
- (c) conflict==1：254 → 254，不变（CONFLICTS 追加 1 行不改 coverage 第 8 列）。
- (d) 12 行逐行 grep：grade 全 `[已证]`；name / subsystem / n_sources / conflict 与改前逐字节相同（004D85D0 保留含 MissionState 的 name，见上）。
- (e) SHA-256：
  - coverage.tsv 前 `7364b87f44764a3617cfaa5b0efc5b546a2300ce2a7d0dcde48a848cd2834cd4` → 后 `08403cef279a209ce81a546835d364194c442aac4f9e9fcd2f5679c8a31b008a`。
  - CONFLICTS.tsv 前 `9a8ca7b9e1805a9d7444f2b4fcca7c376b39b6b9093c216254e366ffaf1adb49` → 后 `97768645d1a11d358f44c79ad8cbf3c65a65ad64fa246b146926864d2164bf6a`。
  - 备份 `_hygiene\coverage.M41.bak` / `_hygiene\CONFLICTS.M41.bak` / `_hygiene\PANEL.M41.bak`（SHA 与改前逐字一致）。

## 其它
- 核盘：12 个 entry 改前 grade 全 `[静态推断]`，逐行唯一命中；12 行全在 atlas，atlas 内 [已证] 1,393→1,405；S09 proved 83→87/1051=8.28%、S10 proved 115→123/526=23.38%。PANEL 标题 / 两个量纲 / 三分母 / S09 / S10 / TOTAL 行已更新并新增 M41 段，其余子系统行一字不动。
- S09 VERDICT 的 5 处偏移误引在 delta 语义栏，未传播到 coverage（coverage 语义栏未动）。004AAD30 细则#1 弱行按 VERDICT 并入。
