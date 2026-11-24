# 卡 S13-K8RECHK —— 执行 RULING-R15 的 D-39(C)

项目根 `D:\Project\ra2-campaign-forge`。目标 `ra2youli\gamemd.exe` 只读（SHA-256 前缀 73201CC0、后缀 F67476，ImageBase 0x400000）。
环境：系统 Python 3.12 + capstone 5.0.7（必须 skipdata=True）+ pefile。禁建 venv、禁 pip install。
不改台账、不改 R14_COMMON.md、不改 COVERAGE\、不 git commit。

**必读**：R14_COMMON.md 新增的 **§8.8**（RULING-R15 成文规则，含 D-39/D-41/D-42 可执行判据）、§8.1 错源 ㉓（活 vptr vs atexit 析构器表）、§8.6 六条。

写域：仅 `lead\next_re_20261117_r14\S13_K8RECHK\` 与 `_ghidra\S13_K8RECHK\`（-noanalysis）。禁止写其它卡目录，尤其禁止写 `lead\next_re_20261117_r14\_audit\`。

## 任务背景（裁决原文）

D-39 裁 **(C)**：③④物理同源时，用「审计逐条复算 + 检出力反证」替代环④。裁决附三个条件，第 3 条是：

> **K8 的 18 行须过 ㉓ 陷阱检查（基类死表 + 派生活表）后逐行复核** —— 实测只有 **11 行可辩护**，9 对是错源 ㉓ 的典型形态。预期收益 **+11**（非 +18）：S13 proved 89 → **100/240 = 41.67%**，**仍远低于门槛 120**。

## 任务

1. 读 `S13_K8\coverage_delta.tsv` 与 `S13_K8\_audit\VERDICT.md`，取那 18 行的 entry 清单。若实际行数不是 18，如实报告。

2. **㉓ 检查（本卡的全部重点）**，每行判环④绑定是否成立：
   - **活表** = 由**构造器**写入的 vtable（构造器本身由 `.data` 初值表指向）；
   - **死表** = 由 `push <dtor>; call 0x7C978A`（atexit 注册的析构器）写入的 vtable，**不算活 vptr**；
   - 容器族（VectorClass / DynamicVectorClass）通常**只有 2 个 vptr 写点**：构造器装**派生** `DynamicVectorClass<*>`、析构器装**基类** `VectorClass<*>`。取错那张 ⇒ `vt[slot]==entry` 也会凑上，但该表**从不是任何 global 的终态活 vptr**；
   - **成对判据**：同一 `(site, slot)` 若被「1 活表行 + 1 析构表行」争抢 ⇒ **必有一行是假**。

3. 每行给出：
   - (a) entry 所在 vt 地址、slot 号、COL 与 TD 名（RTTI 链 fail-closed，`TD+8` 是内联名串不是指针）；
   - (b) 该 vt 的**装点地址与宿主函数**，并判宿主是**构造器**还是 **atexit 析构器**（给 `push <dtor>` 与 `call 0x7C978A` 的地址，或证明没有）；
   - (c) 该 global 的**全部** vptr 写点，判它是否会由基类表变终态活表；
   - (d) 结论：**可辩护** / **不可辩护**（成对争抢 / 死表）。

4. **检出力反证**（§8.8 条 1 要求）：把同一 ㉓ 判据施于 **S13 全池的 [静态推断] 行**（约 126 行），报告「恰命中 N 行 / 误报 M 行 / 随机 16B 对齐起点的误报基线 X%」。

5. **正负对照**：已知的成对争抢样本；以及裁决要求「补同一注」的 5 条已接受先例（`004393F0` `0046B5C0` `0046C890` `0062AF70` `007730F0`）——请核实它们是否也过 ㉓ 检查。

## 核心数字

18 行（或实际行数）里的可辩护 / 不可辩护数；期望 11 / 7。**若你算出与裁决的「9 对」不一致，如实报告差异**（可能裁决把「对」与「行」混算，9 对 = 18 行）。检出力反证的 N / M / X；5 条先例是否过 ㉓。

## 交付 `S13_K8RECHK\`

- `PROGRESS.md`（≤60 行：18 行逐行结论表 + ㉓ 三问答案 + 检出力反证 + 先例核查 + 核心数字）
- `RECHECK_18.tsv`（每行：entry / vt / slot / 宿主函数 / 构造器还是析构器 / global 全部写点 / 结论）
- `coverage_delta.tsv`：**只放「可辩护」的行**，grade 列写 `[已证]`；第 4 列语义栏**必须注明「无直接调用者，仅虚派发见证」**；格式 `entry(hex8) TAB subsystem TAB name TAB one_line_semantics TAB grade TAB evidence_path`
- `EVIDENCE\`（逐行反汇编与写点清单，不截断）、`work\`、`UNKNOWNS.md`、`DISAGREE.md`

完成后只回复：卡号 + 可辩护行数 / 不可辩护行数 + 检出力反证 N 与 M + 5 条先例是否过 ㉓ + delta 行数。
