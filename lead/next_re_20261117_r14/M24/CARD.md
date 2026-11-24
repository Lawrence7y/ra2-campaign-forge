# M24 · 合并员（COVERAGE\ 唯一写者）—— 只并入 `a-S20-KPROVED` 认证的 **28 行**

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + 本卡目录 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M24\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。系统 python 3.12 够用。
⚠️ **coverage.tsv 格式陷阱**：**表头行用逗号、数据行用 TAB**（8 列）。按逗号切会毁表。**改前先备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M24.bak`。

## 唯一输入：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED\coverage_delta.tsv`（40 行），但**只并入白名单 28 行**
审计 `a-S20-KPROVED` 裁决 **PARTIAL**：40 行里 **12 行不成立**（exact 通道判据退化为槽号匹配）。

### ✅ 白名单 28 行（`[静态推断]` → `[已证]`）
**直呼 21 行**：`0045A270` `005251C0` `005F3E30` `005F42C0` `005F4520` `005F5280` `005F5320` `005F5390` `005F5930` `005F5940` `005F5FA0` `005F65A0` `005F6A70` `005F6B60` `005F6BD0` `005F6C70` `005F6C80` `005F6DA0` `005F9970` `0067ABE0` `0075F8B0`
**exact 7 行**：`0040F0A0` `0040F150` `0053C6A0` `005514B0` `00551560` `00557090` `00557140`

⚠️ `0075F8B0` 的 subsystem（S20 vs S07）是 **CONFLICTS 里 OPEN 的争议项** ⇒ **照卡面要求：只并入 grade，不改 subsystem、不裁决归属**，并在 MERGE_LOG 注明。

### ❌ 黑名单 12 行（**整行不得改动**，保持盘上 `[静态推断]`）
`0040EF60` `0040F040` `0053C560` `00551370` `00551450` `00556F50` `00557030` `00422BE0` `00423930` `004253B0` `00425530` `004A7C10`
（理由：7 行只有 atexit **析构器**装的虚表、5 行接收者是运行时寄存器/工厂返回值无静态归属。**整行不改**，连名字也不动——保持原样即可。）

## 硬要求
1. **不得新增/删除 entry**：合并后数据行必须仍为 **18,431**（改前先实测确认；不符即**停下报告**）。
2. **不改 `subsystem`**（D-37 未裁；含 `0075F8B0`）。**不改 name / one_line_semantics**（本卡只动 grade）。
3. 幂等：同 entry 只落一次；若某行盘上已是 `[已证]` ⇒ **停下报告**（白名单全是 `[静态推断]`）。
4. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M24\MERGE_LOG.tsv`：逐行 `entry action(old_grade→new_grade) note`；另列 12 行 rejected 段（附审计理由摘要）。
5. 更新 `COVERAGE\PANEL.md`（S20 的 proved 与总计）。

## 预期（改完自行核对，不符先停）
- grade 直方图：`[已证]` 1,387 → **1,415**（+28）｜`[静态推断]` 6,013 → **5,985**（−28）｜`[未证]` 11,031（不变）；**和 = 18,431**
- S20：proved 40 → **68/410 = 16.59%**（门槛 205，仍差 137）｜named 399 不变
- `conflict=1` 保持 **254**（本卡不新增冲突）

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M24\PROGRESS.md`：改动前后 grade 直方图、applied 28 / rejected 12 计数、coverage.tsv 前后 **SHA-256 与行数**、PANEL 更新确认。
完成后只回复：并入行数 / rejected 数 / `[已证]` 前后值 / coverage 前后 SHA / PANEL 路径。