# M29 · 并入 `a-S08-K1` 认证的 **2 行**（**只升 grade，名字一律不动**）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M29\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M29.bak`。

## 审计裁定（`a-S08-K1` = CONDITIONAL PASS）
- **`Draw_Fog` 这个名字不算两通道 ⇒ 名字降级**：`docs/re` 只是线索，按 R14-R17「双通道不得同源」，docs/台账是同项目读同一 exe 的自记，给不出二进制的独立信息；YRpp 对 `0x47F250`/`Draw_Fog` **0 命中**；`re_atlas\evidence\symbol_map.json` 自证该地址所有 names 的 srcs 均为 `docs/re`。
- ⇒ **`0047F250` 的名字回退为 `sub_0047F250`**（delta 里写的 `Draw_Fog` **不得采纳**），**只升 grade**。
- 先例：前卡 docs 名 `MapClass::DrawShroudFogLayer` 至今未并入（`COVERAGE/CONFLICTS.tsv:392` OPEN，盘上仍 `sub_0047EFE0`）。

## 唯一任务：2 行，**只改第 5 列（grade）**
| entry | 盘上 name（**保持不动**）| 盘上 grade → 新 grade |
|---|---|---|
| `004309D0` | `sub_004309D0` | `[静态推断]` → `[已证]` |
| `0047F250` | `sub_0047F250` | `[未证]` → `[已证]` |

⚠️ **第 2/3/4 列（name / one_line_semantics / 任何其它）一律不动**。本卡**只改第 5 列**。
⚠️ 语义栏若原本是「引用 FOG.SHP → 迷雾/可见性/雷达（字符串线索）」，**保持原样**，不要替换成 delta 里的新语义（避免顺手引入未经审计的名字）。

## 硬要求
1. 合并后数据行仍 **18,431**。
2. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M29\MERGE_LOG.tsv`：2 行 + 一句「按 a-S08-K1 裁定，Draw_Fog 名字不采纳」。
3. 更新 `COVERAGE\PANEL.md`（S08 段）。

## 预期（自行核对，不符先停）
- `[已证]` **1,456 → 1,458**（+2）｜`[静态推断]` 5,948 **→ 5,947**（−1）｜`[未证]` **11,027 → 11,026**（−1）；和 = 18,431
- **S08：proved 1 → 3**（门槛 11，差 8）｜**named 保持 19/22**（名字一个都没加）｜`conflict=1` 保持 254

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M29\PROGRESS.md`：前后直方图 / 2 行改动 / coverage 前后 SHA / 明确写「named 未变（19）」
完成后只回复：并入行数 / `[已证]` 前后值 / S08 proved 与 named 前后值 / coverage 前后 SHA。