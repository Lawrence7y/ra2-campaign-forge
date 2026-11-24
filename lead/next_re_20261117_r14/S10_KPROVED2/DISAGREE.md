# S10-KPROVED2 · DISAGREE

## D1 · 与 classification.tsv 的 `has4_strict=1` 计数（50 vs SURVEY 的 A=49）
`classification.tsv` 筛 subsystem=S10 ∧ has4_strict=1 得 **50** 行，但 SURVEY_RING24\PROGRESS.md 记 S10 A=49。本卡复算后确认：第 50 行 `004CBBA0` 的 `has2_rtti=0`、`rtti_classes` 空、② 环缺失，不满足 A=②∧④ ⇒ A 真值 **49**。本卡采 49，与 SURVEY 一致；`classification.tsv` 单列 `has4_strict` 不可单独当 A 判据（须再 ∧ has2_rtti=1）。

## D2 · 与 D-40「direct call 不算 ④ 单独证据」的一致性
本卡**未**把 direct call 当升格唯一依据：8 行全部另有 ②（RTTI 持有表）与 ③b（跳表/完整循环）。direct 站点只作 ④ 被使用见证。符合 D-40 / M32 回退口径，无分歧。

## D3 · 错源⑯ "slot 0x18C" 记法
R14_COMMON §8.1 ⑯ 写 004D85D0 在 vt 0x7E8C94/0x7E22A4 的 "slot 0x18C"；本卡实测该 entry 在两表的 **slot 99 = byte offset 0x18C**。判定为同一事实的两种记法（slot 号 vs 字节偏移），非实质分歧；本卡 delta 按 slot 号 99 记录。

## D4 · ③b 基率严格档为上界
自动 strict 检测器把 `push 0x80004xxx` 计为 ③b②，但该常量多数是 `call 0x7dc720`（invalid-parameter 处理器）的**断言参数**而非函数返回约定（U5）。故 strict 基率 24.37%（97/398）为**上界**；loose 基率 56.53%（225/398）不受此影响。8 个入选行无一靠"错误码常量"过 ③b（6×完整循环 + 2×跳表），故本卡 delta 不受此高估影响。

## D5 · ③b④ 行的语义表述
004DB690（slot6）的循环体是「有界向量逐项虚调 + test 结果」，`test eax` 后 `inc ebx` 推进，但循环体内无显式用户态内存写（写由被调虚方法经指针参数完成）。本卡按 D-42 ③b④「循环读写完整 I/O（读→判→写→推进）」判其成立（读 Items 指针→判 test→调用写→推进），但承认这是 8 行中 ③b 证据最弱的一行；若合并员要求"写必须在循环体内显式出现"，该行应退回 `[静态推断]`，delta 其余 7 行不受影响。

## D6 · grade 升级需合并员确认
coverage_delta.tsv 把 8 行从盘上 `[静态推断]` 升为 `[已证]`（四环齐全），属**提议**；本卡不直接改 coverage.tsv（纪律 11）。实际并入与 grade 终裁由 M 卡执行。

## D7 · `004D85D0` 与台账 §1000 / M15 旧裁决的关系（本卡重提，请合并员裁定）
台账 §1000（行 34676–34693）记 `004D85D0` 曾由 `[已证]` 退为 `[静态推断]`，理由三处硬伤：① 编造 `0x816CAC` 环①、`0065C7E0 RandomRanged` 幽灵被调、类归属错（应为 FootClass）。本卡**不复用**那三处依据：④ 站点改用 `0051A9FC/0073A4FB/0073B0A0` 三个真实 E8 直调（E8 边界+rel32==entry+体外全过，见 ring4_verified.tsv），类归属已按 ⑯ 归 FootClass。
- 台账旧裁决的「缺环①」中的①指**外部已证 mission 枚举锚点**，与 D-40 的最小环集①（入口形态）与③（整体合同）编号不同。本卡按派卡明示的 D-40 / D-42 判据，③b④ = 完整循环（8 邻格 `byte[cell+0x122]--` 读改写 + 8 次边界），该循环为台账 L34691 已记录的逐指令事实（并非新发现）。
- 该行 8 邻格循环证据与台账相同，编号框架不同 ⇒ 本卡**重提**其四环齐全。若合并员认为旧裁决优先，我把该行退回 `[静态推断]`，delta 余 7 行不变。特此显式报分歧，不静默改盘。
