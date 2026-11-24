# UNKNOWNS.md — P0-RESIDUAL-2 未决项与不可判说明

## U1 · ENUM.tsv 的 5,598 条 UNDECIDABLE
ENUM 全集 5,656 = pool\coverage(当前 14,495)。裁定分布：FUNC 20 / NOT_FUNC 38 / **UNDECIDABLE 5,598**。
不可判原因（逐地址见 ENUM.tsv 的 `undecidable_reason` 列）：
- **5,569 条** `fails_form_filter(c4a|leaf)`：16B 对齐、前驱 TERM、非 JCC、不在 atlas、不在 body，但首字节形态不属于 operational form(c4a∨leaf)。**为什么不可判**：通不过形态过滤器**不等于不是函数**——正对照 oracle `0x7775C0`（push ecx）与 2,026 个 FPU 叶函数（fld/fadd/…/ret，完整函数体）都是反例，证明形态过滤器召回不足；同时这些地址也无引用（call/dataptr）可佐证。硬判 FUNC 会把跳表/数据/对齐填充误收，硬判 NOT_FUNC 会重演漏检。故保持 UNDECIDABLE。
- **29 条** `fails_form_filter;first_byte_E8_E9_EB`：首字节为 call/jmp 类，属任务四项判据明确排除项，但 gate476 中有 10 条真入口首字节=E8，故也不硬判 NOT_FUNC。

## U2 · 2,026 个 FPU 叶函数（真实但无引用）的归属
首字节 0xDD/0xDB（如 `0x403CE0`、`0x403D10`），逐条反汇编为完整浮点计算函数（`fld qword ptr [const]; fdiv; fstp [global]; ret`，nop 填充、16B 对齐），**不在 atlas、不在 coverage、0 直接 call 引用、0 数据指针引用**。它们是"无人引用但真存在"的入口（与 `0x7775C0` 同类）。
- **为什么不可判/未并入**：它们说明通道确实不完备，但（i）数量 2,026 远超卡面 gap 估计 222–820；（ii）无法在本卡内逐一证明每个都是独立函数而非数据/编译器常量折叠片段；（iii）并入会使分母跳到 ~16,500，与已入账 14,715 冲突（纪律 9）。留 P1 专项裁定，本卡只枚举+标记（`EVIDENCE/gap_candidates.tsv` 的 fpu 列、ENUM.tsv 的 `FPU-leaf` channel 标签）。
- 复算：`work/inspectfpu.py` / `work/examine_fpu_region.py`。

## U3 · concurrent coverage.tsv 改动（Lead 已裁定）
会话期间 `COVERAGE\coverage.tsv` 由合并员 M2 从 **14,493 → 14,495**（新增 `005B3740` S10 / `006C41D0` S11）。Lead 裁定改用当前截面 14,495。
- 比对基线元数据：`rows_data=14,495`、`mtime=2026-11-17T17:47:09.019262`、`size_bytes=2,813,399`、`sha256=3BF8A5BF...C99`（`EVIDENCE/stats.json` 的 cov_meta；快照 `EVIDENCE/coverage_snapshot_14495.tsv`）。
- 收尾稳定性复核：`FINAL coverage stability check: rows=14495 ... STABLE=True`。
- 交叉校验：2 条已知新增 `in_cov=True`、`reported_as_new=False`（未误报为新入口，`EVIDENCE/oracle_and_crosscheck.tsv`）。
- ENUM 全集 5,656 即基于当前 14,495，与记录的基线行数一致。

## U4 · N_pool 差 1
本卡 N_pool=7,228；P0-RESIDUAL 审计 a13 记 7,229。差 1 来自 `.text` 末端 `0x7E038D` 的对齐边界处理（末个对齐点 0x7E0380 的前驱/可解码判定）。不影响 5,656 / 20 / 38 / 5,598 的量级与结论。

## U5 · 20 条 FUNC 的语义级映射
20 条新 FUNC（`coverage_delta.tsv`）多为 `push imm32; call [...]; ...; ret` 形态——静态初始化/`atexit` 注册 thunk（如 `0x40A210 push 0x87e880; call [0x7e11e8]`）。本卡只做入口裁定，按纪律 4「字段偏移不能定语义」不臆造具体类名/语义，name=`sub_XXXXXXXX`、subsystem=S22、grade=[未证]，留 P1。

## U6 · B_RAIL 5 条负对照标签歧义
5 条 B_RAIL 在 `B_RAIL_C5_EXCLUDED.tsv` 标 NOT_FUNC（R14-R10 B 抑制口径），但主表 `ENTRY_ADJUDICATION.tsv` verdict=FUNC/source=true_entry（审计 overrule）。本卡如实报"原始 5/6 过判据"，同时给出"真实假阳性 0/1"的更正解读，不掩盖歧义。
