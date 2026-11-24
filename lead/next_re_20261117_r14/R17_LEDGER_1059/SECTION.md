## §1059 · 书记员覆盖 D-53(A) 裁决与 ②-b 收口成文（2026-11-21）：七事项草稿

> 书记员只起草本节，不写主台账、不改控制文件、不改 coverage.tsv。全部数字已按盘面复算；细目见 numbers.tsv。取不到者直书「未取得」。

### 1 · D-53 已裁 (A)：定谳句与书面限制 a–e 同框

**定谳句（D-53(A)，用户 2026-11-21，R17 第 5 轮收尾）**：②-b（占格闸两路径行为层不可区分）永久以 [静态推断] 收口，不再投卡。

**书面限制（与上一句同框；引用定谳句必须连本 a–e 一并引用，禁止拆分）**：
- a. 两条路径在闸核内共用同一个 0x47C620，行为层不可区分。
- b. 三函数体内非栈写 = 0：0x449440 为 1 写/0 非栈，0x47C620 为 0/0，0x47C3D0 为 8/0。
- c. 最具区分力的用例（bit0 = 0 的可放置对象）物理不存在；bit0 恒 1 的唯一写点是 0x6F322F。
- d. 「虚派发」仅为推断，依赖 §2.6 对 0x6F2B40 为 TechnoClass ctor 的记录，不是字节证实。
- e. 动态硬件读断点未做；该项需要真机授权复核。

未选 (B)：撤销 D-36(A) 的「不写线程上下文」单条、改走硬件断点确定性取证这条路没有被采纳，故真机授权范围不变。

判定理由（与其余事项不同）：本事项是用户裁决的效力边界，重点是把 grade 与书面限制锁成不可拆的引用单元。

证据路径：lead\next_re_20261117_r14\R14_COMMON.md（§2.6、§2.7、§2.9）；lead\PENDING_DECISIONS.md。

### 2 · 定谳依据：三条路径均为「已排除」，不是「未尝试」

① **逐槽立即数装载：已排除。** #73 = 0x7E3FE0，#107 = 0x7E4068；连邻槽共 12 个候选 VA（0x7E3FDC / 0x7E3FE0 / 0x7E3FE4 / 0x7E3FE8 / 0x7E4050 / 0x7E4054 / 0x7E4058 / 0x7E405C / 0x7E4060 / 0x7E4064 / 0x7E4068 / 0x7E406C）在 .text 的 4 字节小端立即数命中数各自为 0。本机从 gamemd.exe 的 .text raw 独立扫描复得同样 12 个 0。R17_AUDIT_R9 B1 为 AGREE，且给出正控（E8→0x47C620 = 10 处）与反控（对齐、首尾注入、截断、文件边界）。

② **E8 / E9 直接调用：已排除。** 对 0x43F180 与 0x449440，E8 rel32 = 0、E9 rel32 = 0；同一解码链对正控 0x47C620 给出 E8 = 10（首位 0x43F2AE），证明零结果不是尺子失效。

③ **运行期索引派发：已排除。** 窄口径 call [reg+reg*4] = 0；jmp [reg*4+disp32] = 387，逐项均为 switch 跳表，表地址真值 0x4059D0..0x87D44E（386 处 .text、1 处 .data），落在槽段 [0x7E3EBC,0x7E43C4) 内者为 0，故不能触达 #73/#107。并列说明：R17_R10_DISPATCH\REPORT.md 旧写 0x8069D0..0xC7E44E；R17_AUDIT_R10\VERDICT.md 与盘上 raw_results.json 的真值为 0x4059D0..0x87D44E，卡面采用后者，故不构成与卡面不一致。

证据路径：lead\next_re_20261117_r14\R17_R8_RESIDUAL\REPORT.md；lead\next_re_20261117_r14\R17_R8_RESIDUAL\sites.tsv；lead\next_re_20261117_r14\R17_AUDIT_R9\VERDICT.md；lead\next_re_20261117_r14\R17_AUDIT_R9\raw_results.json；lead\next_re_20261117_r14\R17_R10_DISPATCH\REPORT.md；lead\next_re_20261117_r14\R17_AUDIT_R10\VERDICT.md；lead\next_re_20261117_r14\R17_AUDIT_R10\raw_results.json。

判定理由（与其余事项不同）：本事项逐项否定的是取证通道本身，而非裁决结论或文件治理状态。

### 3 · 类身份维度也已排除

三个装表 host 为 0x43B680 / 0x43B740 / 0x43BCF0，类名均为「未取得」。全文件对装饰名字符串 VA 的 4 字节 raw 命中 6 处；逐点锚点/操作数复核后有效立即数引用 0 处；host 体内及所列 0x43A680..0x43C0CA 窗口内均为 0。口径并列：.?A 真值为 988 处且 988/988 在 .data，.text 为 0；旧「989 且都在 .text」不是本条依据。

因此「先定类名再反查调用者」这条路不再走。

证据路径：lead\next_re_20261117_r14\R17_R10_DISPATCH\REPORT.md；lead\next_re_20261117_r14\R17_R10_DISPATCH\residual.md；lead\next_re_20261117_r14\R17_AUDIT_R10\VERDICT.md；lead\next_re_20261117_r14\R17_AUDIT_R10\name_refs.tsv；lead\next_re_20261117_r14\R17_AUDIT_R10\names_by_section.tsv；lead\next_re_20261117_r14\R17_AUDIT_R10\raw_results.json。

判定理由（与其余事项不同）：本事项排除的是类身份命名通道，不是调用形态通道或 coverage 判据。

### 4 · R14_COMMON §2.9 已成文，且唯一权威

节名为 ## 2.9 【D-53(A) 裁决，2026-11-21】②-b 永久以 [静态推断] 收口 + 书面限制。结构上，定谳句与书面限制 a–e 在同一小节同框；随后才是三条已排除路径、类身份排除、已成立事实与引用纪律。不得只引定谳句而漏引 a–e。

复算数字：R14_COMMON.md 236,380 → 241,825 B，差 5,445 B；LF 1,648 → 1,704；CR 1,081 → 1,081 未变。写盘前旧长度前缀 sha256 PASS；备份 R14_COMMON.before_2.9.md 与改前 full-file sha256 相同（E7253E44CBEFC446FE8C86519406012FADF10359B212AF5F13BD87EA6325CC5D），本机复算 after 前 236,380 字节 sha256 与该备份一致；after full-file sha256 = 5543CD991E2FEF28AB3EB12A15E2D4414A196E7A343067A854C011003F0DB500。追加段 5,445 B、CR 0、LF 56。

引用纪律：凡引用 ②-b，必须写 [静态推断] 并同引 R14_COMMON §2.9；不得写成「已证」，不得只引 §2.6 而不引 §2.9。§2.7 只负责两处表述更正，§2.8 只负责取证方法论，均不替代 §2.9 的权威表述。

证据路径：lead\next_re_20261117_r14\R14_COMMON.md（§2.6 / §2.7 / §2.8 / §2.9）；lead\next_re_20261117_r14\R17_COMMON_2_9\REPORT.md；lead\next_re_20261117_r14\R17_COMMON_2_9\R14_COMMON.before_2.9.md；lead\next_re_20261117_r14\R17_COMMON_2_9\verify.py。

判定理由（与其余事项不同）：本事项核的是成文载体的字节完整性与引用唯一性，而不是某条静态判据的真假。

### 5 · PENDING_DECISIONS.md 已按纪律处置，且未改 coverage grade

现盘 lead\PENDING_DECISIONS.md 为 81,251 B。删除 D-53 待裁块、插入裁决条后的中间态 81,112 可由本机复算：81,251 − 139（现「当前无待裁项」一行 138 B + LF）= 81,112；改前 82,591 B 与 sha256 前缀 006283afe1e2e6d8… 只可由备份缺口说明读到，改动前文件未落盘，故这两项的逐字节复核值为「未取得」，不得伪称已复算。原第 61–75 行也是执行时断言/说明记录，当前文件无法回读原状，记为「未取得」。

现状复核：「D-53 待裁」0 处，「D-53 已裁决」恰 1 条且位于「已裁决记录（最近在上）」顶部，「当前无待裁项」恰 1 行。coverage.tsv 中检索 D-53 与 ②-b 均为 0 行；entry 004D3780 仍为 [已证]；coverage.tsv 的 mtime 早于 PENDING_DECISIONS.md 与 R14_COMMON.md 的本次改动时间。故 grade 影响为 0 行，coverage.tsv 全程未动。

证据路径：lead\PENDING_DECISIONS.md；lead\next_re_20261117_r14\COVERAGE\coverage.tsv；lead\next_re_20261117_r14\R17_LEAD_BASELINE\PENDING_DECISIONS_before_D53_NOTICE.md。

判定理由（与其余事项不同）：本事项核的是待裁项生命周期与下游 grade 不受影响，不涉及排除路径的证据强弱。

### 6 · 防误读：coverage entry 004D3780 与本节 #73 不是同源

coverage.tsv 中 entry 004D3780 仅 1 行，grade 为 [已证]，第 4 列语义含「shared slot73 for RTTI Aircraft/Foot/Infantry/Unit; no 0x47C620 caller」。判定：不是同一槽。经核，该行 slot73 的物理地址是 0x7E23C8 / 0x7E8DB8 / 0x7EB17C / 0x7F5D94，四处 dword 均为 0x004D3780；本节 #73 是 0x7E3FE0，dword 为 0x0043F180。两者仅槽序号 73 与偏移 +0x124（0x124/4 = 73）巧合相同；物理地址、宿主 vtable、槽内函数全不同。

因此不得写「已有一行 [已证] 与本结论互相印证」；该行 grade 不变，也不是本节结论的同源证据。

证据路径：lead\next_re_20261117_r14\COVERAGE\coverage.tsv；lead\next_re_20261117_r14\R17_COMMON_2_9\row_004D3780.md；lead\next_re_20261117_r14\R17_COMMON_2_9\REPORT.md；ra2youli\gamemd.exe。

判定理由（与其余事项不同）：本事项专门拆开「同号槽」造成的表面互证，防止把另一条 RTTI 口径误挂到本节结论上。

### 7 · 流程缺陷 R17-4：before 副本静默跳过

改 PENDING_DECISIONS.md 时，before 副本用了固定名 PENDING_DECISIONS.before_D53.md；该名在更早轮次已存在，if (!exists) write 静默跳过，导致改动前状态未被落盘。旧快照经盘面复算为 79,824 B，现名 PENDING_DECISIONS.before_R17r1_STALE.md；真正的 D-53 before 文件在 R17_LEAD_BASELINE 下不存在。改动前 82,591 B / sha256 006283afe1e2e6d8… 来自 R17_LEAD_BASELINE\PENDING_DECISIONS_before_D53_NOTICE.md 的如实留痕，逐字节复核为「未取得」。

改动本身仍可核：结构完好、D-53 待裁归零、D-53 已裁决恰 1 条；但无法从备份逐字节还原，只能按执行时断言反向重放。处置已落：旧快照改名并标 STALE，缺口说明写入 R17_LEAD_BASELINE\PENDING_DECISIONS_before_D53_NOTICE.md。规则：before 副本文件名必须带轮次与序号，写入前必须显式校验目标不存在或覆盖；if (!exists) 这类静默跳过不得用于备份。

证据路径：lead\next_re_20261117_r14\R17_LEAD_BASELINE\PENDING_DECISIONS.before_R17r1_STALE.md；lead\next_re_20261117_r14\R17_LEAD_BASELINE\PENDING_DECISIONS_before_D53_NOTICE.md；lead\PENDING_DECISIONS.md。

判定理由（与其余事项不同）：本事项登记的是备份控制失败，不改变任何 ②-b 证据分级。

本草为 §1059 草稿，由 Lead 逐字追加；书记员未自行改动台账。
