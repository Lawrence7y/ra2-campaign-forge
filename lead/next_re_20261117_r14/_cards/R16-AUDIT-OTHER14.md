> 卡号：R16-AUDIT-OTHER14
> 角色：**审计员**（`work/cn:deepseek-v4.1-flash`；执行器 `hy4flash-free`，异族 ✓）
> 写域：`lead\next_re_20261117_r14\R16_AUDIT_OTHER14\`（只写自己的产物目录）
> 日期：2026-11-21（R16 第 18 轮）· **14 行全做（≤18）**

# 任务：审计那 14 行「真·无 ④」补写的 ④

## 0. 绝对边界

1. `R16_F1_OTHER14\` 下产物**只读**；不改 `coverage.tsv`、不改 `gamemd.exe`、不改任何卡目录。
2. 只写 `R16_AUDIT_OTHER14\`。
3. **必须自己跑只读 capstone 独立复算**（这是判 PASS 的硬手段）。
4. 判 PASS 给自测字节证据；判 FAIL 点名哪行哪项。不许编造。

## 1. 被审对象

`lead\next_re_20261117_r14\R16_F1_OTHER14\`：`delta.tsv`（14 行）、`fields.tsv`、`REPORT.md`（+ `scan.py`/`gen_products.py`/`verify_delta.py` 等）。

执行器自述：
- **14 行全 OK / 0 SKIP**；`same_source=yes` **0 行**；
- **2 行 direct call 形态成立**：站点字节 `E8 EF B4 DE FF`→`004AF540`、`E8 5F 11 DF FF`→`004B5AB0`，四项判据（`E8` 边界 / `site+5+rel32==entry` / capstone 目标 / 体外非自环）全过；
- **12 行槽位 12/12 解出**（9 行 slot0、`RadSiteClass`/`WarheadTypeClass` slot8、`AnimClass::Draw` slot69），六项字节复核 12/12×6 全 True；
- 7 行装表点在 **CRT 静态初始化函数**（atlas 未收录），宿主经 `nop`/`CC` 填充定界反推；
- 改前 14 行第 4 列**均不含 `④`**（净增 14）；
- 行行不同：完整 14/14，entry 归一后 14/14。

## 2. 本批的两种形态（不要混判）

| 形态 | 行数 | ④ 该长什么样 |
|---|---:|---|
| `direct call`（形态 1） | 2 | 写**调用站点地址 + 站点指令字节 + `site+5+rel32==entry`**；**不得**写成槽位见证 |
| `slot_witness` | 12 | 照既有 121 行「`④ 活表槽位见证`」先例的骨架（vt/slot/COL/RTTI/装表点/宿主） |

## 3. 逐行审计项（14 行全做）

### A · 最小改动与原文保全
- `delta.tsv` 第 4 列必须以盘上 `coverage.tsv` 该 entry 的**原第 4 列为严格前缀**。
- 第 1/2/3/5/6/7/8 列与盘上**逐字节相同**。
- 注意：`coverage.tsv` 被多轮并发并表改过；以**你开卡时盘上实值**为准，若与 delta 不符先判断是不是并发写者动了该 entry，写进报告。

### B · 字节事实（独立复算）

**对 2 行 direct call**：
1. 站点处 capstone 解码确为 `call rel32`（`E8`），且 `site+5+rel32 == entry`；
2. 站点**不在**该 entry 自身函数体内（非自环）；
3. 该站点所属函数 ≠ entry。

**对 12 行槽位见证**（6 项）：
1. `u32(vt + slot*4) == entry`
2. `u32(vt - 4) == COL`
3. `u32(COL + 4) == offset`
4. `u32(COL + 12) == TD`
5. `cstr(TD + 8) == mangled`（`TD+8` 是**内联串**）
6. 装表点处为 `mov <mem>, imm32` 且 `imm32 == vt`

> `pTD`/`pCHD` 存**绝对 VA**。`gamemd.exe` 只读打开。

### C · **重点：7 行「宿主靠填充定界反推」是否可靠**

执行器自述有 **7 行**的装表点落在 **atlas 未收录的 CRT 静态初始化函数**，宿主是用 `nop`/`CC` 填充分界**反推**出来的。请逐行核：

1. 该装表点地址确实在 `.text` 内、且其前面最近的函数边界确实由填充字节隔开（给出字节实证）；
2. 反推出的宿主**不是** entry 自身（否则「entry 体外」不成立）；
3. 反推的宿主与 `④` 文本里写的宿主**一致**；
4. 若某行的反推不成立 ⇒ 该行判 **FAIL**（这类「靠填充反推」是本批最脆的一环）。

### D · 文本与事实一致
- ④ 文本里每个地址与你 B 项实测一致；
- `slot_witness` 行须含 vt/slot/COL/RTTI/装表点 五要素（缺一即 FAIL，或若该字段写 `未取得` 则记 NIT）；
- `direct_call` 行须含站点地址与 entry，且**不出现**「活表槽位见证」字样；
- **必须含 D-47 披露指针且指向 `§12.6`**（写 `§12.4` ⇒ FAIL）。

### E · `same_source` 判定是否可信
执行器报 `same_source=yes` **0 行**，即 14 行的 ④ 都独立于 ②。请独立核：
- `slot_witness` 行的 ④ 证据（`.text` 装表点）与 ② 的类身份证据（RTTI）是否真的是两条链；
- `direct_call` 行的 ④（`E8` 站点）是否独立于 ②。

若你发现某行其实同源，判 **FAIL** 并说明。

### F · 反抄袭
14 行两两比较；entry 归一后仍须两两不同。

## 4. 产物（`R16_AUDIT_OTHER14\`）

1. `VERDICT.md` —— 首段总体判定；§A–§F 逐项；**§C 的 7 行逐行结论**；必改清单
2. `verify.py` —— 可复跑（含 capstone）
3. `check14.tsv` —— 14 行 × 各项实测值

## 5. 回复里给什么

只给：总体 PASS/FAIL 行数、§A–§F 各项不合格行数、**7 行填充定界反推是否 7/7 成立**、2 行 direct call 是否成立、`same_source=yes` 是否真为 0、§12.6 指针是否 14/14、必改条数、产物路径。**不要贴全表**。
