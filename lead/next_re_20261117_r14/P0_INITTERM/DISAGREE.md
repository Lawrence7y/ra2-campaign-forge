# DISAGREE.md — 与审计值 / 台账 / 派卡前提的冲突（逐条引节号）

## D1 · coverage 截面 14,495 vs README 抬头 14,493
- **冲突**：`COVERAGE/coverage_README.md` 抬头写「当前版：14,493 行」；实测 `coverage.tsv` **14,495 数据行**（14,496 行含表头）；`STATUS_BOARD.md` COVERAGE 状态段与 `P0_RESIDUAL_2/_audit/VERDICT.md` §1 均认定 14,495（M2 并表 +2）。
- **处置**：以实测 14,495 为截面；14,493 是 M2 前旧值。本卡分母全部基于 14,495。不改 coverage。

## D2 · 前驱 ∈ TERM 计数 3,928（字节级） vs 审计 3,941
- **冲突**：审计 VERDICT §2 称「3,941 项前驱∈TERM」；本卡 `prev_byte_class` 字节级实测 nop 3,907 / ret(C3) 8 / int3 13 / other 16，TERM 严格字节级 = **3,928**。差 13。
- **根因（已查清，非矛盾）**：16 个 "other" 的 target−1 字节均为 `0x00`，但回看前 16 字节（`EVIDENCE/t2_pred_zero_detail.txt`）显示 **15 个是 `C2 imm16`（ret 4 / ret 8 / ret 0x10 / ret 0x2c）的 imm16 末字节**，按"前一条真实指令"口径它们也是 TERM；仅 `0x42FF80` 前驱是数据指针表（非 TERM）。按指令级口径 TERM≈3,943，与审计 3,941 仍差 2（疑为 4 个首字节跳转 thunk 的前驱口径差异）。
- **处置**：`INITTERM_TABLE.tsv` 的 `prev_byte_class` 列**如实记录字节级分类**（不凑数）；无论哪种口径，都不改变 3,944 全 FUNC 的结论（槽值即函数优先，派卡 T2 明确规定）。

## D3 · 首指令跳转 4（审计）vs 本卡 firstbyte_jmp 标记 5
- **冲突**：审计 §2「仅 4 项首指令是跳转」；本卡 `firstbyte_jmp` 标记 5 项。
- **根因（已查清）**：本卡标记条件是首字节 ∈ {E8,E9,EB}，5 项 = 4×`E9`（`0045B1B0`/`0045C2F0`/`561900`/`5638C0`，纯 jmp thunk）+ 1×`E8`（`5A9C20`，是 `call 0x5A9C40; push 0x5AC190; call 0x7C978A; pop ecx; ret`，首指令是 call 不是 jmp）。审计的"跳转"仅计 4×E9，**一致**。
- **处置**：保留本卡 5 项标记并注明构成；全 5 项均为合法入口（槽值即函数）。

## D4 · 派卡 T3「静态对象构造器（写 vptr / 调 ctor 的 thunk）」vs 实测「全局初始化器为主」
- **冲突**：派卡 T3 要求区分"写 vptr / 调 ctor 的 thunk"；实测 3,944 项**0 项**在限定体内直接 `C7 /0 <.rdata vptr>`（`EVIDENCE/t3_buckets_refined.tsv` A_VPTR_WRITE=0）。主体是 B_CALL_THUNK(1,962，含调 `_ftol`/数学辅助) / C_FP_INIT(1,148) / D_PLAIN_STORE(818)。
- **处置**：不虚构"写 vptr"证据（违纪律 5）。如实按实测分桶（见 SEMANTICS.md §2-3），并把类别语义限定为"静态初始化函数/thunk"——这是 MSVC `_initterm` 的准确术语。

## D5 · 派卡 T1「可能只有一张表」vs 实测 4 张 `_initterm` 表
- **冲突派卡前提**：T1 说"若只有一张，给出只有一张的穷举依据"；实测同一函数内有 **4 处** `_initterm` 调用（4 张表，见 PROGRESS.md T1 表）。
- **处置**：主表（3,944 项）是本卡唯一收编目标（派卡 §2"本卡范围就是这张表"）；另外 3 张小表（5/4/2 槽，共 8 个非空 FUNC）如实列在 EVIDENCE/t1_tables.txt 与 PROGRESS.md，**未并入 coverage_delta.tsv**（避免越界）。若 Lead 要一并收编，另立卡。

## D6 · 分母 18,417（本卡）vs 审计 18,431
- **冲突**：审计 §6 口径 A 报 18,431；本卡干净增量报 18,417。差 14 = P0-RESIDUAL-2 的 20 个新 FUNC 中**不在本表**的 14 个（另 6 个已在本表 3,944 内）。
- **处置**：两个数并列、各自注明口径（见 CALIBER.md §2），不凑成同一个数。

## D7 · 审计 2,026 的 "无人引用" 已被推翻（本卡继承审计结论，不复算冲突）
- 审计 VERDICT §2 已证 2,019/2,026 有数据段指针（`_initterm` 表引用），2,026 ⊂ 3,944 表。本卡不重复裁定，只整表收编 3,944（见 SEMANTICS.md §1）。
