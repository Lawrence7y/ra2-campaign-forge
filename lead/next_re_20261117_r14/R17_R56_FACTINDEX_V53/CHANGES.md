# CHANGES.md — FACT_INDEX v5.2 → v5.3

基底：`lead\next_re_20261117_r14\R17_R51_FACTINDEX_V52\FACT_INDEX.tsv`（v5.2，54 条）。本目录为新增产物，未修改任何既有 FACT_INDEX 目录。

总条数不变：**54**（F01–F54）。改动只落在 **7 行**（F29/F49/F50/F51/F52/F53/F54），其余 47 行与 v5.2 **逐字节一致**（含表头共 48 行完全相同）。

## 1. 失效指针修复：D-4 已裁，`口径待裁` 必须作废

依据：`lead\next_re_20261117_r14\R17_R52_ADJ_D4\VERDICT.md`（2026-11-21，deepseek 跨家族，判定 ① 两者可并存）。

| fact_id | 改了什么 | 依据 |
|---|---|---|
| F29 | `limitations` 删除「两种读法并列 / 口径待裁，不得单引其一」，改为记录 D-4 定谳：语义级判据、带 `imm32==1` 前置条件，与 F49 形态级全称否定作用域不相交；`statement` 同步改用裁决规范措辞（不再用同词异义的「常量桩」，改为直述 `B8 01 00 00 00 C2 04 00` 形态 + 返回恒 1 + 不改状态 + 反例点名）；`evidence_paths` 增列裁决书 | `R17_R52_ADJ_D4\VERDICT.md` §3/§4 |
| F49 | 同上：`limitations` 删除「口径待裁」，改记 D-4 ① 并补「全文件另有 32 处 `b8 imm32 c2 04 00` 的 imm≠1，故本条在任意 imm 层面成立、不得反推槽级语义」；`statement` 改用裁决规范措辞；`evidence_paths` 增列裁决书 | 同上 |

## 2. 字节层精度修正与锚修复

| fact_id | 改了什么 | 依据 |
|---|---|---|
| F50 | **机制表述改写**：原句「va−ImageBase 在 .data/.rsrc 会读到错节」不准确。实为：`.rsrc`/`.detour` 的 `VirtualAddress≠PointerToRawData`（0x77A000 vs 0x47E000、0x793000 vs 0x497000）⇒ 朴素换算必错；而 `.data` 的 **VA==PointerToRawData** ⇒ 两法数值相同，是 `.data` 的 **vsize 0x367BE4 ≫ rsize 0x6C000** 使 RVA 0x47F7E8 落在**无文件映射的尾段**、读到 `.rsrc` 原始窗口字节。**第二证据锚由 `R14_COMMON.md(§13.1)`（该节实为 F30/F54 主题）换为本目录 `lead_byte_checks.tsv`** | 本目录 `lead_byte_checks.tsv` |
| F51 | `limitations` 补双源声明：Lead 已独立复算 336/68/1439 全部命中（严格形态按「紧邻 `push imm32` + `E8`→`0x7C978A`」判据复现 68）；并补交叉引用「与 F27 部分重叠」 | `lead_byte_checks.tsv`；`GOAL_THREE_TARGETS_20261018.md` §1049 第 2 行口径定义 |
| F52 | `statement` 对齐 `R14_COMMON §13.3` 判据2：原行内「三件」与所引判据2 的「三件事」是两份不同清单。改为：调用侧**紧邻** `push 1` 后 `call [vt+0x20]`；体内同时具备**重装 vptr + `test byte ptr [esp+X],1` + `call 0x7C8B3D`** 三件事，并以 **`ret 4` 收尾**；并明写「单一 test 形态本身不构成证据」 | `R14_COMMON.md` §13.3 判据2 |
| F53 | **第二证据锚修复**：原锚 `STATUS_BOARD.md(R17 第 16 轮 段)` 实不含 `0x007E88D0` 材料（实测该段无此地址），换为本目录 `lead_byte_checks.tsv`；`limitations` 补字节复核结论：4 处写点均为 vptr 安装，`0x4CA778` 位于 `0x4CA770` 体内，该函数具备 `test byte ptr [esp+X],1`(+255) + `call 0x7C8B3D`(+263) + `ret 4`(+275) 三件 ⇒ 属删除析构器侧写、**「成对写」成立**；并补交叉引用「与 F28 部分重叠」 | `lead_byte_checks.tsv`；`R14_COMMON.md` §13.5 边界段 |
| F54 | `statement` 补四个 RTTI 名与结构值（按 `COL=u32(vt−4)` 正确读法，四表 COL 全 `sig=0`、`pTD`/`pCHD` 均指向镜像内，解出 `.?AVFactoryClass@@` / `.?AVWarheadTypeClass@@` / `.?AV?$TClassFactory@VFactoryClass@@@@` / `.?AVMouseClass@@`）；`limitations` 补「与 F30 部分重叠」 | `lead_byte_checks.tsv` |

## 3. 未改动项（可证）

- `F01`–`F28`、`F30`–`F48` 共 **47 行**与 v5.2 逐字节一致；
- `grade` 列**未改任何一行**：仍为 `[已证]` 27 / `[静态推断]` 1 / `[流程]` 24 / `未取得` 2 = 54；
- 总条数仍 54，`fact_id` 连续 F01–F54，无新增条目、无删除条目。

## 4. 本轮不采纳的两条审计意见（如实记）

字节层审计（`R17_R54_AUDIT_FI52`）另提两条，经 Lead 复算**均不成立**，故未据此改表：

- 审计称「四处写点全是构造器、无析构器写，`0x4CA770` 不是删除析构器」⇒ **不成立**。该函数在 `+255` 有 `test byte ptr [esp+X],1`、`+263` 有 `call 0x7C8B3D`、`+275` 有 `ret 4`，三件齐（正控 `0x6DC470` 同法可检出，`test@+45` / `call@+53`）。审计只看了函数前 200 字节且把函数起点误定到 `0x4CA766`（该处是 10 个 `0x90` 填充）。
- 审计称「`E8`→`0x7C8B3D` 直接 call 站点 = 0」⇒ **不成立**，实为 **4,499** 处。审计脚本原始输出即 4499，其自行「修正」为 0 反而错了。

Lead 自己也有一次自查错：首次只扫 `0x4CA770` 前 200 字节便一度认同「不是删除析构器」，扩大窗口并加正控后才纠正。**教训：函数体判定的窗口必须覆盖到该函数的第一个 ret，且必须带正控。**
