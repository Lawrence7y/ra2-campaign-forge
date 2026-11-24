# M34 · 按 `AUDIT-SEM-SELF` 降级 **22 行**（`[已证]` → `[静态推断]`）

写域（绝对路径，唯一）：`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\` + `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M34\`。**其他位置一律只读**。
⚠️ **严禁建 venv / pip install**。**coverage.tsv 表头逗号、数据行 TAB**（8 列）。**改前备份**到 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\_hygiene\coverage.M34.bak`。

## 依据：全表内一致性审查（`AUDIT-SEM-SELF`，只读测量）
盘上有 **105 行 `[已证]` 的语义栏自陈未证**（含 S22 10 行不裁 ⇒ **非 S22 95 行**）。
审计对 95 行逐行独立反汇编、按 D-42 判：**P1 = 73 / P2 = 22 / P3 = 0**。

### 要降级的 22 行（**只改第 5 列 grade**）
`00407B40` `0041BEA0` `0044B760` `0044B770` `00459ED0` `00459EE0` `00473C00` `00486840` `00487E70` `004D55C0`
`004D55F0` `004D9C10` `004DA2B0` `0051F620` `0051F640` `005B2E10` `005B3040` `005C9470` `005CAE10` `005CAEB0`
`005F6940` `0075AC80`

（共 22 个。逐行理由见 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\AUDIT_SEM_SELF\ROW_VERDICTS.tsv` 的 `criterion` / `note` 列。）

## 降级理由摘要（供 MERGE_LOG 用）
- **薄壳 / 转发桩 / 单点推断**（D-42 ③a）：如 `005C9470` `005CAE10` `005CAEB0` 三个构造器薄壳（只 `call 0x5D8C50` + 单张 vt 写、线性无分支）。
- **单点推断不成立**：`00487E70`（0x148 的 10 个分配点**没有一处**写 CellClass 活 vt）、`005B2E10`（0x1c2 无 `push`→`operator new`）⇒ 「常量返回 = 对象大小」不成立。
- **③ 缺**：其余行为「整体语义未定」或只有类级描述（rtti-vftable / 槽语义未证）而无 ③b 四个充分条件之一。

## 硬要求
1. **只改这 22 行的第 5 列**（`[已证]` → `[静态推断]`）；`name` / `semantics` / `subsystem` / 其余列**一律不动**。
2. 合并后数据行仍 **18,431**；`conflict=1` 保持 **254**。
3. 记 `D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M34\MERGE_LOG.tsv`：22 行 `entry / old / new / 理由（一行）`。
4. 更新 `COVERAGE\PANEL.md`。

## 预期（自行核对，不符先停）
- `[已证]` **1,388 → 1,366**（−22）｜`[静态推断]` **6,019 → 6,041**（+22）｜`[未证]` 11,024；和 = 18,431
- 受影响（按子系统）：**S10 −8**（33 行里的 8 行）｜S05 −4｜S18 −3｜S12 −2｜S06 −2｜S03 −1｜S20 −1｜S11 −1
- **无任何子系统状态翻转**（达标仍 S15 / S16 / S17）

## 交付
`D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\M34\PROGRESS.md`：前后直方图 / 22 行清单 / 各子系统 proved 前后 / coverage 前后 SHA / 明确写「达标仍 3 个」。
完成后只回复：降级行数 / `[已证]` 前后 / 各子系统 proved 前后 / 达标数是否变化 / coverage 前后 SHA。