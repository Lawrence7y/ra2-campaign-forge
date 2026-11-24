# P0-GATE-FIX · atlas 之外 476 个入口裁定（审计 R14-R10 四项修正）

> 卡号 P0-GATE-FIX｜目标 `ra2youli\gamemd.exe`，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`，ImageBase 0x400000，只读未改。
> 写域仅 `lead\next_re_20261117_r14\P0_GATE\`；未改 `ra2youli\`、`COVERAGE\` 或台账。
> capstone 5.0.7 `skipdata=True`；`.text=[00401000,007E038D)`；不读 `vtables_v2.json`。复跑：`adjudicate_r10.py` → `verify.py` → `make_reports.py`。

## 一、审计条件逐条落实

1. **ALREADY_IN_COVERAGE = 2**：`004F8440`（`HouseClass::Update`, S16）与 `00535E50`（`SetDefenseTabCommand::Execute`, S09）。`VT_DIRECT_ENTRIES.tsv` 有 **413** distinct target，**413 − 2（已入 coverage）= 411**；这两条不属于本次 476 池，见 `EVIDENCE\ALREADY_IN_COVERAGE.tsv`。
2. **B 轨按 R14-R10 报 60**：65 条候选中有 5 条上游 `TRUE_ENTRY_UNIFIED.tsv` verdict=FALSE（c5 粗距离抑制）。R14-R10 口径 B = **60 FUNC / 5 NOT_FUNC**；5 条见 `EVIDENCE\B_RAIL_C5_EXCLUDED.tsv`。主表仍保留审计维持的 65 条 FUNC，但不再声称「c1–c6 全过导出 65」。
3. **A2 已换**：撤下 `linear-sweep-start` 作为证据；A2 = 前驱∈{`nop`,`int3`,`ret`,`jmp`}。实测 nop 409 / ret 2，共 411。审计基线：**34.7%** 的 4B 对齐地址、**36.5%** 的 16B 对齐地址是 sweep 起点；对齐起点中 **78.6%** 的前驱是函数中部指令 ⇒ 旧 A2 无区分力，已废弃。
4. **分级对齐**：逐行与 SUMMARY 统一为：`[已证] slot value`（槽值指向 `.text`）、`[已证] predecessor-form`（前驱形态）、`[已证] table-boundary-input-restatement`（A3 表界，仅重述同源输入）；`[静态推断] slot-value-as-function-entry`（语义原则）。B 轨字节/判据为 `[已证]`，c4b 语义 bucket 为 `[静态推断]`。

## 二、分轨账

| 轨 | 池 | R14-R10 口径 | 主表裁定 |
|---|---:|---:|---:|
| A `vt_direct` | 411 | FUNC **411** / NOT_FUNC **0** | 411 FUNC |
| B `true_entry` | 65 | FUNC **60** / NOT_FUNC **5** | 65 FUNC（5 条 c5 覆盖已披露） |
| 合计 | 476 | 471 baseline FUNC / 5 baseline NOT_FUNC | 476 FUNC / 0 NOT_FUNC / 0 UNDECIDABLE |

A 轨逐条 A1–A4 全过，NOT_FUNC 失败项：**无**。顶点证据为前驱形态而非 sweep 起点；A3 仍为自定界 1214 表输入，按 `[已证] 重述` 标注，不作独立第二通道。

B 轨 5 条 R14-R10 基线排除：`00632A20`, `00632B20`, `00632B70`, `00690AE0`, `00796ED0`。审计给出填充隔离证据，故主表维持 FUNC；此改判已显式登记，不再默认通过。

## 三、集合与形态

- ∩ `coverage.tsv` = **0**（本 476 池）；∩ `probe_and_data_entries.tsv` = **0**；atlas 区间包含命中 = **0**。
- A 轨 tiny(<16B)=**144**，首字节 `E8/E9/EB`=**10**；均只作形态注记，不作否定理由。
- A 轨数据交叉命中 = **0**（跳表 dword / probe 精确命中 / Items 区）；审计扩至全部 switch 表/标签后仍为 0。
- B 轨 c4a=65，c4b=4，both=4；c4b 旧「体长≥16B」作废。

## 四、分级
- `[已证]`：PE 段归属、槽值、前驱形态、A3 表界重述、B 字节/判据、集合交集、计数。
- `[静态推断]`：槽值即函数入口的语义原则、B c4b 语义 bucket。
- `[未证]`：无；UNDECIDABLE=0。

## 五、P0 出口闸结论

**P0 出口闸 (b)：有条件满足。** 476 条已全部裁定且无一为 `NOT_FUNC`；但支撑判据已按审计 R14-R10 修正（A2 换为前驱形态、A/B 轨分级对齐、`ALREADY_IN_COVERAGE` = 2、B 轨 60）。**待 Lead 验收这 4 项修正后方可标记为满足。**

## 六、证据与复算
- `ENTRY_ADJUDICATION.tsv`：476 行主表；A 轨 c1..c6=`NA`，A1–A4/分级在 evidence。
- `EVIDENCE\ENTRY_ADJUDICATION_FULL.tsv`、`A_RAIL_DETAILS.tsv`：不截断逐条证据与分级列。
- `EVIDENCE\ALREADY_IN_COVERAGE.tsv`、`B_RAIL_C5_EXCLUDED.tsv`、`R14_R10_NOT_FUNC_DETAILS.txt`、`counts.json`、`VERIFY.txt`、`_audit\VERDICT.md`。
