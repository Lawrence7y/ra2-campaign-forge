# M37 · 并入 `a-S08-KPROVED2` 白名单 **6 行** + 登记 1 处 docs 命名冲突

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M37\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M37.bak`。

## 审计裁定（`a-S08-KPROVED2` = **FAIL（部分成立）**）
12 行交 8 行 → **6 行成立、2 行降级**。

### ✅ 白名单 6 行（`[静态推断]` → `[已证]`）
`0045A680` `0045A730` `004D24A0` `004D2510` `004D27D0` `004D2810`

### ❌ 黑名单 2 行（**整行不得改动**，保持 `[静态推断]`）
| entry | 审计理由 |
|---|---|
| `0045AB50` | **槽位虚构**：卡称 `007E44F4` slot10 @`007E451C` —— **该槽不存在**（该表仅 7 槽 0..6，slot7 @`007E4510` = `007FC558` 是**下一张表的 COL**）。且卡内偏移全错（free 在 `+0x76` 非 `+0x66`、false 在 `+0x3F` 非 `+0xCE`）。**④ 无**：该表唯一构造器写点 `00488098` 被 `00483A5C` 直调后，`00483A61` 立即把 vptr 覆写为 `007E44F4` ⇒ 非终态活 vptr；其余写点全是 dtor/atexit。direct E8=0 |
| `0045AC30` | 同上（`007E4524` = `007E4514` slot4，非卡称的 `007E44F4` slot12）；偏移整体错位；**④ 无** |

⚠️ 这两行是 `SURVEY-RING24` 警告的 **livevt 歧义 111/112** 的实例：`DV slot(7+k) ≡ V slot k`（k=0..6）⇒ 把「下一张表的 COL」当成自己表的槽位。

## 硬要求
1. **只改这 6 行的第 4/5 列**（semantics / grade）；**name 必须与盘上逐字相同**；`subsystem` 不动。
   ⚠️ 这 6 行的 name 仍是 `::slotN` 占位名 —— **本卡不改名**（命名另有卡）。
2. 合并后数据行仍 **18,431**；`conflict=1` 保持 **254**。
3. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M37\MERGE_LOG.tsv`：6 行改动 + 2 行 rejected（附审计理由）。

## 第二件事：`CONFLICTS.tsv` 追加 **1 行**（470 → 473）
当前 **472** 行，追加后应 **473**。按现有列格式追加：
- entry：**`004D2510`**
- 内容：**docs 侧命名冲突** —— `0x004D2510` 在 3 份 docs 被记作 **`FoggedObjectClass::Draw`**（`atlas_rev/R2_fog_l4.md`、`building_fog_residual_deep_dive.md`、`re_sprint_S12_report.md`），而盘上名为 `FoggedObjectClass::slot5`。
- 标注 `OPEN:docs 命名 vs 盘上占位名`；**不改 grade、不改名**（审计判「反汇编支持卡侧语义、docs 非名字通道（§8.5），故不改 grade，只登记」）。

## 预期（自行核对，不符先停）
- `[已证]` **1,366 → 1,372**（+6）｜`[静态推断]` **6,041 → 6,035**（−6）｜`[未证]` 11,024；和 = 18,431
- **S08：proved 3 → 9/22**（门槛 11，**差 2 ⇒ 仍不达标**）｜named **L 20/22 不变**
- `CONFLICTS.tsv` **472 → 473**

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M37\PROGRESS.md`：前后直方图 / 6 行 applied / 2 行 rejected / CONFLICTS 前后行数 / **S08 proved 前后并明确写「S08 仍不达标（9/11）」** / coverage 前后 SHA。
完成后只回复：并入行数 / rejected 数 / `[已证]` 前后 / S08 proved 前后 + 是否达标 / CONFLICTS 行数 / coverage 前后 SHA。