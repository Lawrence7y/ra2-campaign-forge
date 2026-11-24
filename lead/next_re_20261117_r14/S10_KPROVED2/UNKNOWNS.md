# S10-KPROVED2 · UNKNOWNS

## U1 · 候选池口径：50 vs 49
`classification.tsv` 中 subsystem=S10 ∧ has4_strict=1 共 **50** 行；其中 `004CBBA0`（FootClass::CallFindPath）`has2_rtti=0`、`rtti_classes` 空 ⇒ 无 ②，不满足 A=②∧④，**剔除**。故自数 S10 A 集合 = **49**，与 SURVEY_RING24\PROGRESS.md 记 S10 A=49 一致。004CBBA0 的 ④ 站点 004D3E4B 成立但 ② 缺失，不进本卡。

## U2 · 未选的 41 个 A 集合行（49−8）
本卡只做 8 行，其余 41 行**未逐一手工打尽 ③b**，不宣称其四环状态。自动 ③b 探测（work\baseline.py，与 8 行同判据）提示其中 004D55C0/004D55F0/004D94B0/004D9C10/004DA2B0/004DE620/006F3AD0/006F3D60/00702D40/00706640/00708C30 等命中 strict ③b，但：
- **00702D40/00706640/00708C30/006F3AD0/006F3D60/004D5690/004DB260**：name 栏类名（AircraftClass）与 ⑯ 基类归属（FootClass/TechnoClass）不一致，按纪律 12「② 栏类名须与 name 栏类一致」**本卡不纳入 delta**（否则须改名，超出"只做 8 行"范围）。
- **004D94B0/004D9C10/004DA2B0**：strict 命中来自 `0x80004003`（E_POINTER）常量，但该常量是传给 `0x7dc720`（invalid-parameter/assert 处理器）的**参数**，不是函数返回约定 ⇒ **非 ③b② 可证伪错误码**，不进 delta。
- **其余**：③a（机械可述/无关键判据）或未手工验证，不进 delta。
上述 41 行的最终 grading 留给后续卡；本卡不对其下结论。

## U3 · 004DA2B0 / 004DE620 的 ext_hi 异常
`classification.tsv` 中 `004DA2B0`（atlas_size=5）ext_hi=005B2EF6、`004DE620`（atlas_size=5）ext_hi=005F6BB2 —— CFG extent 远大于 atlas_size（SURVEY 自写 CFG 在 5 字节桩后继续跟随落入邻函数）。本卡对这两行的自动扫描按 `min(ext_hi, entry+4000)` 截断；因其未入 delta，不影响 8 行结论。

## U4 · 错源⑯ slot 记法
R14_COMMON §8.1 ⑯ 记 004D85D0 在 vt 0x7E8C94/0x7E22A4 的 "slot 0x18C"；实测该地址为 **byte offset 0x18C = slot 99**（0x18C/4=99）。本卡按 slot 99 记录（holding_tables.tsv），与 ⑯ 的 byte-offset 记法一致，非新事实、非分歧。

## U5 · ③b 基率检测器口径
work\baseline.py 的 strict/loose ③b 检测器为**自动结构判据**（跳表≥3目标 / 完整循环 read+write+advance / ≥2 vt 写或≥10 字段 imm / 错误码常量），池 = 398 S10 行，seed 20261119，2000 次、每次随机取 8 行。8 个入选行的 ③b 已**逐条手工核**（见 EVIDENCE\per_row 与 work\dump_jumptables.py / dump_loops.py）；自动基率只是基线，不替代手工判定。`push 0x80004xxx` 被自动器计为"错误码"会高估 strict 基率（如 004D94B0 实为 assert 参数），故 strict 基率 24.37% 是**上界**。

## U6 · 无 Ghidra decompile 交叉
本卡按 `-noanalysis` 约束未跑 Ghidra 反编译；所有 ③b 结论来自 capstone 线性/范围反汇编的字节证据 + 手工逐条核对，未使用 `function_atlas.tsv` 的 entry+size 作站点归属（用 body 区间包含判定）。`_ghidra\S10_KPROVED2` 目录已建但为空。

## U7 · ④ 站点在体外
8 行全部 direct 站点经 E8 边界 + signed rel32 解析，target==entry，且站点地址均落在函数体 `[entry,ext_hi)` 之外（ring4_verified.tsv `outside_body=True` 全过）。无自环。

## U8 · `004D85D0` 台账旧裁决
grep GOAL_THREE_TARGETS 命中 14 处：台账 §1000 / M15 曾因三处硬伤把该行由 `[已证]` 退 `[静态推断]`，且明示「不计入 S10 proved」。本卡用的是**不同编号框架**（D-40/D-42：③b④完整循环）与**真实** ④ 站点（非旧版幽灵被调），逐条证据见 per_row 与 DISAGREE D7。是否重提由合并员裁定；未静默改盘。

## U9 · 004DB3C0 台账命中
grep 命中 1 处（L13783 仅为函数大小表 `0x004db3c0 | 11 | 708`），无 grade 裁决冲突。
