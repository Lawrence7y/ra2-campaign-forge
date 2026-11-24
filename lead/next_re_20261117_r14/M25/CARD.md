# M25 · 合并员（COVERAGE\ 唯一写者）—— 只并入 `a-S10-KPROVED` 认证的 **34 行**

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + 本卡目录 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M25\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。
⚠️ **coverage.tsv 表头用逗号、数据行用 TAB**（8 列）。**改前先备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M25.bak`。

## 唯一输入：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_KPROVED\coverage_delta.tsv`（40 行），**只并入白名单 34 行**
审计 `a-S10-KPROVED` 裁决 **PARTIAL**：12 行 exact 里 **6 行不成立**（判据退化为「atexit 析构器基类表槽号匹配」，与 a-S20/a-S13-K12 同型，**第三次复发**）。

### ✅ 白名单 34 行（`[静态推断]` → `[已证]`）
**direct 28 行**：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_KPROVED\_audit\VERDICT.md` §2 所列 28 条（**以该 VERDICT 的 §2 清单为准，逐条抄**）
**exact 6 行**：`0045A560` `0045A610` `006B1850` `006B1900` `006B8660` `006B8710`

⚠️ `004CBBA0`（`FootClass::CallFindPath`）在 direct 28 条内：**可并入，但其证据只有 atlas + direct 单通道**，不得在语义栏声称虚表归属（照 delta 原文即可，不要加）。

### ❌ 黑名单 6 行（**整行不得改动**，保持盘上 `[静态推断]`）
`0045A420` `0045A500` `006B1710` `006B17F0` `006B8520` `006B8600`
（理由：这 6 行只在 **atexit 析构器**装的基类 `VectorClass` 表上满足 `vt[K]==entry`；8 个 `(site,slot)` 各被一条活表行与一条析构表行争抢。）

## 硬要求
1. **不得新增/删除 entry**：合并后数据行仍为 **18,431**（改前实测确认；不符即停下报告）。
2. **只动 grade**：不改 name / one_line_semantics / subsystem。
3. 若某行盘上已是 `[已证]` ⇒ **停下报告**（白名单应全为 `[静态推断]`）。
4. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M25\MERGE_LOG.tsv`：逐行 `entry action(old→new) note` + rejected 6 行段（附审计理由）。
5. 更新 `COVERAGE\PANEL.md`。

## 预期（自行核对，不符先停）
- `[已证]` **1,415 → 1,449**（+34）｜`[静态推断]` **5,985 → 5,951**（−34）｜`[未证]` 11,031 不变；和 = 18,431
- S10：proved **117 → 151/526 = 28.71%**（门槛 263，差 112）｜named 513 不变
- `conflict=1` 保持 **254**

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M25\PROGRESS.md`：前后 grade 直方图 / applied 34 / rejected 6 / coverage 前后 SHA-256 与行数 / PANEL 确认。
完成后只回复：并入行数 / rejected 数 / `[已证]` 前后值 / coverage 前后 SHA / PANEL 路径。