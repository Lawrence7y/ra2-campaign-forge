# M31 · 降级 **19 行**（`[已证]` → `[静态推断]`）+ 登记 2 处子系统归属争议

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M31\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M31.bak`。

## 背景（两次独立审计的结论）
`AUDIT-PROVED-UNNAMED`（第一审）判 43 行「`[已证]` 但无名」：**P1=23 / P2=20**，建议降 20 行。
`a-AUDIT-PROVED-UNNAMED`（第二审，独立复算）**只同意降 19 行**，并**救回 1 行**：
- **`00508F60` 不同意降级** —— 体内用立即数把 `MapClass` 单例 `0x87F7E8` 放入 ecx，直接调 `MapClass::Reshroud`(`0x577AB0`) 与 `MapClass::Reveal`(`0x577D90`)；随后与 `[0xA83D4C]`(PlayerHouse) 比较，翻转 `[esi+0x577A]`，并调 `VocClass::PlayGlobal` ⇒ **完整的迷雾开关合同**，属 P1。
**⇒ 本卡按第二审执行：降 19 行，`00508F60` 保持 `[已证]`。**

## 要降级的 19 行（**只改第 5 列 grade，其余列一律不动**）
`00402040` `00402190` `004024A0` `00405B50` `00407860` `00411DF0` `0048EBF0` `00490490` `004A1DE0`
`005865E0` `0054AC40` `00635F20` `00636120` `00638840` `00638A80` `00639740` `00639800` `0065CA80` `007B8730`

（共 19 个。**`00508F60` 不在其中**，保持 `[已证]`。）

## 降级理由（审计原文摘要，供你填 MERGE_LOG）
- 语义栏自陈「**整体语义未定**」（S05 那批 `写 ObjectClass+0x94 层字段 = reg X（该写点已证；整体语义未定）`）⇒ 环③ 不成立，只证了单写点不等于证了函数语义。
- 三条「体内字节 ⇄ 语义栏硬矛盾」（两审均独立复现 3/3）：
  - `0054AC40`：三张 vt 全属 `JumpjetLocomotionClass`，`+0x94` 写入**常数 0**（非 ObjectClass、非 edx）
  - `0065CA80`：对应 `RawFileClass`（文件类 ctor，**非音频/EVA**）
  - `007B8730`：对应 `Mouse`/`WWMouseClass`，且 `00635F20` 的 edx 为 **−1**

## 第二件事：`CONFLICTS.tsv` 追加 **2 行**（子系统归属争议）
当前 **470 行**，追加后应 **472 行**。按该文件**现有列格式**：
1. **`0065CA80`** — 盘上 subsystem 为 `S19`，体内装 `0x7F0904` = `RawFileClass`（文件类 ctor）⇒ **疑似应归 S03（文件系统）**，非 S19（音频）。标注 `OPEN:疑似子系统归属错误`，来源 `AUDIT_PROVED_UNNAMED\_audit\VERDICT.md`。
2. **`007B8730`** — 体内为 `Mouse`/`WWMouseClass` ⇒ 与盘上子系统不符（**请从 coverage 读出它的现 subsystem 并写进备注**）。标注 `OPEN:疑似子系统归属错误`。
- ⚠️ **不要改 coverage.tsv 里这两行的 `subsystem`**（D-37 未裁，只登记不裁）。

## 硬要求
1. **只改这 19 行的第 5 列**（`[已证]` → `[静态推断]`）；`name` / `semantics` / `subsystem` / 其余列一律不动。
2. 合并后数据行仍 **18,431**。
3. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M31\MERGE_LOG.tsv`：19 行 `entry / old_grade / new_grade / reason`；另 **单列一段**说明 `00508F60` **为何不降**（第二审救回）。
4. 更新 `COVERAGE\PANEL.md`。

## 预期（自行核对，不符先停）
- `[已证]` **1,458 → 1,439**（−19）｜`[静态推断]` **5,947 → 5,966**（+19）｜`[未证]` 11,026 不变；和 = 18,431
- 受影响：**S05 170→154**｜S04 92→91｜S07 68→67｜S19 21→20｜S06 **不变 128**
- `CONFLICTS.tsv` **470 → 472**

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M31\PROGRESS.md`：前后直方图 / 19 行清单 / `00508F60` 不降的理由 / CONFLICTS 前后行数 / 各子系统 proved 前后 / coverage 前后 SHA。
完成后只回复：降级行数 / `[已证]` 前后 / 各子系统 proved 前后 / CONFLICTS 行数 / coverage 前后 SHA。