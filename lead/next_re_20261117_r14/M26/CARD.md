# M26 · 并入 `a-S13-K12` 白名单的 **3 行**（Lead 漏并，补账）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + 本卡目录 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M26\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。
⚠️ **coverage.tsv 表头用逗号、数据行用 TAB**（8 列）。**改前先备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M26.bak`。

## 背景（Lead 的账错，本卡补）
`a-S13-K12` 裁决 **FAIL**，但白名单给了 **3 行**（审计原话：「可并入 3 行：`0040F870`、`0054E890`、`0054EA70`」）。
**Lead 误把它们当成「已并入」，实际一行都没落盘**（盘上这 3 行仍是 `[静态推断]`、名字仍是占位名）。

## 唯一任务：并入这 3 行，**grade + name + semantics 一起**
| entry | 新名（来自 `S13_K12\coverage_delta.tsv`）|
|---|---|
| `0040F870` | `VectorClass<WarheadTypeClass*>::FindItemIndex`（**以 delta 原文为准，逐字抄**）|
| `0054E890` | `VectorClass<KamikazeControl*>::Clear`（同上）|
| `0054EA70` | `VectorClass<KamikazeControl*>::SetCapacity`（同上）|

⚠️ **名字必须逐字取自 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K12\coverage_delta.tsv` 的对应行**，不要自己改写、不要加 `Dynamic` 前缀。
⚠️ 若 delta 里的名字与上表不一致，**以 delta 为准**，并在 MERGE_LOG 注明差异。

## 硬要求
1. **只这 3 行**，其余 14 行（K12 黑名单）**整行不动**。
2. **不得新增/删除 entry**：合并后数据行仍为 **18,431**。
3. 只改这 3 行的 `name` / `one_line_semantics` / `grade` / `evidence_path`（4 列）；`subsystem` 与 `n_sources`/`conflict` 不动。
4. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M26\MERGE_LOG.tsv`：3 行逐行 `entry action(old_grade→new_grade) (name_from → name_to)`。
5. 更新 `COVERAGE\PANEL.md`（S13 段）。

## 预期（自行核对，不符先停）
- `[已证]` **1,449 → 1,452**（+3）｜`[静态推断]` **5,951 → 5,948**（−3）｜`[未证]` 11,031 不变；和 = 18,431
- **S13：proved 86 → 89**（门槛 120，差 31）｜named **216 不变**（这 3 行本是占位名，非 `sub_`，换真名不改计数）
- `conflict=1` 保持 **254**

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M26\PROGRESS.md`：前后 grade 直方图 / 3 行逐行改动 / coverage 前后 SHA-256 与行数 / PANEL 确认。
完成后只回复：并入行数 / `[已证]` 前后值 / S13 proved 前后值 / coverage 前后 SHA。