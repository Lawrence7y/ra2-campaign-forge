# M35 · 合并 **66 行语义栏补写**（`SEMFIX-S10` 25 + `SEMFIX-REST` 41；**grade/name 一律不变**）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M35\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M35.bak`。

## 背景
盘上有 76 行「`[已证]` 但语义栏自陈未证」（S22 10 行不裁 ⇒ 非 S22 **66 行**）。
`AUDIT-SEM-SELF` 判定它们 grade 正确（③b 成立），只是**语义栏是模板语**。两张卡已按审计 `criterion` 列补写。

## 输入（两份 delta，**各 8 列，已核 grade/name 零变更**）
| 卡 | 行数 | 语义长度 | 状态 |
|---|---|---|---|
| `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_S10\coverage_delta.tsv` | **25** | 154–233 字符 | Lead 已核：grade 变更 0、name 变更 0、含弱词 0 |
| `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SEMFIX_REST\coverage_delta.tsv` | **41** | 84–214 字符 | 同上 |

⚠️ 两卡**无重叠**（Lead 已核）。

## 唯一任务：把 66 行的**第 4 列（one_line_semantics）**替换成 delta 里的新语义

## 硬要求
1. **只改第 4 列**。`grade`（第 5 列）必须仍是 `[已证]`；`name`（第 3 列）必须与盘上**逐字相同**；`subsystem` / `entry` / `evidence_path` / `n_sources` / `conflict` **一律不动**。
2. 合并后数据行仍 **18,431**；**grade 直方图必须前后完全相等**：`[已证]` **1,366** / `[静态推断]` 6,041 / `[未证]` 11,024。
3. 若某行盘上 name 与 delta 的 name 不同 ⇒ **停下报告**（不得改 name）。
4. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M35\MERGE_LOG.tsv`：66 行 `entry / old_semantics(前 40 字符) / new_semantics(前 40 字符) / 来源卡`。
5. 更新 `COVERAGE\PANEL.md`（只改说明，不改数字 —— 直方图不变）。

## 预期（自行核对，不符先停）
- **grade 直方图完全不变**（1,366 / 6,041 / 11,024）；行数 18,431；`conflict=1` 254
- **「`[已证]` 且语义栏含「未定/弱信号/线索/槽语义未证」」的行数应从 76 降到 10**（剩余 10 行全是 S22，按 §1 不裁）
  ⇒ 请**实测这个数**（合并前 76、合并后应 10），并在 PROGRESS 里报出来。**这是本卡唯一的实质产出指标。**

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M35\PROGRESS.md`：前后直方图（应相等）/ 66 行改动数 / **「语义自陈未证」行数 76 → ? 实测** / coverage 前后 SHA。
完成后只回复：修改行数 / 直方图前后（应相等）/ 语义自陈未证行数 前→后 / coverage 前后 SHA。