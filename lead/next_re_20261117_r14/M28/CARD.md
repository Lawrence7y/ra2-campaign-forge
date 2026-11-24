# M28 · 并入 `a-S20-DIRECT` 白名单 **4 行** + 登记 `007C978A` 归属冲突

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + 本卡目录 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M28\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M28.bak`。

## 输入：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_DIRECT\coverage_delta.tsv`（11 行），**只并入白名单 4 行**
审计 `a-S20-DIRECT` 裁决 **PARTIAL**：11 行里 **7 行不合格**。

### ✅ 白名单 4 行（`[未证]` → `[已证]`，**跨两级**，审计已独立复核体锚点）
`0070F1D0` `0070FD70` `00739AC0` `00739CD0`
（审计原话：体内独立复核到 `AnimClass::AnimClass` + `SetOwnerObject` + `VocClass::PlayAt` 锚点。）

### ❌ 黑名单 7 行（**整行不得改动**，保持盘上现值）
| entry | 盘上现值 | 理由（审计）|
|---|---|---|
| `004C54E0` `0062F230` `0075E950` `007610F0` | `[未证]` | 四环不足 |
| `0062DF20` `0062E070` | `[静态推断]` + `ParticleSystemClass::Update_A/_B` | **归属对、名字错**：实为**构造器**与**标量删除析构器**（体内装 4 张 `.?AVParticleSystemClass@@` 表 + `ObjectClass::ObjectClass` / `CRT::_delete` / `AnnounceExpiredPointer` / `Limbo`）；`Update_A/B` 与「reads +0xBC」（实为 `lea ecx,[esi+0xbc]`）均错 |
| `007C978A` | `[未证]` | **MSVC 静态 CRT `atexit` 注册包装**；`0x7C978A % 16 = 10` 违项目入口判据；336 个调用者跨 ≥13 子系统 ⇒ **S20 归属不成立** |

## 第二件事：把 `007C978A` 登记进 `CONFLICTS.tsv`
当前 `CONFLICTS.tsv` **没有** `007C978A` 的记录。请按该文件**现有列格式**追加 **1 行**：
- subsystem 字段：`S20`（盘上现值），并在备注列写明「**疑似子系统归属错误**」
- 备注须含：`MSVC CRT atexit 注册包装`、`336 个 direct 调用者跨 ≥13 子系统（S22 289 / S06 10 / S12 7 / S20 仅 6）`、`0x7C978A % 16 = 10 违入口判据`、来源 `S20_DIRECT\_audit\VERDICT.md`
- **不要改 coverage.tsv 里它的 subsystem**（D-37 未裁，只登记不裁）

## 硬要求
1. **只这 4 行改 grade**；`name` / `one_line_semantics` / `subsystem` 一律不动（白名单 4 行名字本就是 `sub_`）。
2. 合并后数据行仍 **18,431**；`CONFLICTS.tsv` 从 **469** 行 → **470** 行（+1）。
3. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M28\MERGE_LOG.tsv`：4 行 applied + 7 行 rejected（附理由）。
4. 更新 `COVERAGE\PANEL.md`。

## 预期（自行核对，不符先停）
- `[已证]` **1,452 → 1,456**（+4）｜`[未证]` **11,031 → 11,027**（−4）｜`[静态推断]` 5,948 不变；和 = 18,431
- **S20：proved 68 → 72**（门槛 205，差 133）｜named 399 不变
- `coverage.tsv` 的 `conflict=1` 计数：**保持 254**（本卡不新增 `conflict` 标记，只在 CONFLICTS.tsv 追加登记行）

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M28\PROGRESS.md`：前后 grade 直方图 / 4 applied / 7 rejected / CONFLICTS 前后行数 / coverage 前后 SHA。
完成后只回复：并入行数 / rejected 数 / `[已证]` 前后值 / CONFLICTS 行数 / coverage 前后 SHA。