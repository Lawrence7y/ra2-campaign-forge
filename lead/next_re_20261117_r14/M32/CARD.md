# M32 · 按 **D-40** 回退 **66 行** direct-only 升格（`[已证]` → `[静态推断]`）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M32\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M32.bak`。

## 背景：D-40 裁定（`lead\PENDING_DECISIONS.md` 已立）
`S03-CRITERION` 独立裁定：**「有 direct call」不能单独支撑 `[已证]`**。三条证据：
1. **方向相反**：`[未证]` 批 direct 命中率 **83.82%** > `[静态推断]` 批 **28.70%**（差 2.9 倍）；
2. **真差异在 ② 环**：`[静态推断]` 108/108 有 RTTI 类属、`[未证]` 仅 6/68 = 8.82%（**11.3 倍**）；而 ③ 语义合同**两批都是 0**；
3. **批内也无效**：direct 把 108 行劈成 31+77，两半 ② 都是 100% ⇒ 劈法与任何证据环无关。

**⇒ `[已证]` 最小环集 = ① 入口 + ② 类属 + ③ 整体合同 + ④ 使用见证，任一缺不得升。**

## 本卡任务：回退 66 行（三张已并入的 direct-only 卡）

### ① `S20_KPROVED` 的 **28 行**（`M24` 并入的）
白名单 28 行 = 21 direct + 7 exact。**7 行 exact 保留**（活 vtable + `vt[slot]==entry` + 写点在本行外，是合法 ④），**只回退 21 行 direct**。
21 行清单（`S20_KPROVED\coverage_delta.tsv` 里 `direct` 型）：
`0045A270` `005251C0` `005F3E30` `005F42C0` `005F4520` `005F5280` `005F5320` `005F5390` `005F5930` `005F5940` `005F5FA0` `005F65A0` `005F6A70` `005F6B60` `005F6BD0` `005F6C70` `005F6C80` `005F6DA0` `005F9970` `0067ABE0` `0075F8B0`
⚠️ 若你从 delta 里核出这 21 个的 `direct`/`exact` 归属与我列的不同，**以 `M24\MERGE_LOG.tsv` 与 `S20_KPROVED\_audit\VERDICT.md` 为准**，并在 MERGE_LOG 注明差异。

### ② `S10_KPROVED` 的 **34 行**（`M25` 并入的）
28 direct + 6 exact（`0045A560` `0045A610` `006B1850` `006B1900` `006B8660` `006B8710`）。
**6 行 exact 保留**，**只回退 28 行 direct**。
28 行清单以 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_KPROVED\_audit\VERDICT.md` §2 的 direct 清单为准（逐条抄）。

### ③ `S20_DIRECT` 的 **4 行**（`M28` 并入的）
`0070F1D0` `0070FD70` `00739AC0` `00739CD0` —— **全部回退**（纯 direct）。

**合计：21 + 28 + 4 = 53 行**（不是 66 —— 66 是「direct 相关总数」，其中 13 行 exact 保留）。
⚠️ **若你算出的回退数不是 53，先停下报告**，不要凑。

## 硬要求
1. **只改回退行的第 5 列**（`[已证]` → `[静态推断]`）；其余列一律不动。
2. 合并后数据行仍 **18,431**。
3. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M32\MERGE_LOG.tsv`：53 行 `entry / old / new / 依据(D-40)`；另**单列一节**列出**保留的 13 行 exact**并给理由。
4. 更新 `COVERAGE\PANEL.md`（S10 / S20 段）。

## 预期（自行核对，不符先停）
- `[已证]` **1,439 → 1,386**（−53）｜`[静态推断]` **5,966 → 6,019**（+53）｜`[未证]` 11,026；和 = 18,431
- **S10：proved 151 → 123**（回退 28）｜**S20：proved 72 → 47**（回退 21+4 = 25）
- `conflict=1` 保持 254（本卡不新增 conflict）

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M32\PROGRESS.md`：前后直方图 / 53 行清单 / 保留 13 行 exact 的理由 / S10 与 S20 proved 前后 / coverage 前后 SHA。
完成后只回复：回退行数 / 保留行数 / `[已证]` 前后 / S10 与 S20 proved 前后 / coverage 前后 SHA。