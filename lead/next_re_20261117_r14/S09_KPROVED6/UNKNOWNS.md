# S09-KPROVED6 · UNKNOWNS

## U1 · 2 行依赖 D-42 细则#1（loose 档），严格口径下四环齐全数 8→6

- `0069DE00`（ShapeButtonClass::slot34）、`005576A0`（ListClass::slot34）的 ③b① 依据 D-42 操作化细则#1「≥3 道互斥闸且各闸动作不同」（实证：0069DE00 四闸=释放旧串/设串解析坐标/覆盖X/覆盖Y，写目标 [esi+0x58] vs [esi+0x14] vs [esi+0x18] 互异、被调 0x7C8B3D 仅首闸；005576A0 四闸=空输入早退/虚扩容 [edx+8]/写元素+计数/两路不同虚通知 [eax+0x48] 与 [edx+0x8c] 与 [eax+0x88]）。
- 两行体内无跳表、无回边循环、无 GetLastError/-1 错误码返回约定、无 ≥10 字段形状断言 ⇒ 若审计采用「③b① 只认跳表/循环/错误码/形状」的更严口径，这两行落 ③a，四环齐全数由 8 降为 6；按现行 D-42（Lead 已采纳细则#1）计 ③b①，本卡记 8。
- 依据：`lead\PENDING_DECISIONS.md` D-42 细则#1；`R14_COMMON.md` §8.6 条 3；`EVIDENCE/RINGS_0069DE00.txt`；`EVIDENCE/RINGS_005576A0.txt`。

## U2 · ③b 基率检测器是操作化代理，非穷举

- 本卡 `EVIDENCE/baseline_3b.json` 的 strict/loose 两档由 `work/baseline.py` 的确定性检测器给出（池 = 当前盘上 S09 grade=[静态推断] 且落在 .text 的 657 行；seed 20261119、2000 次不放回抽 8）：strict K=113/p=0.171994/E[8]=1.375951/MC=1.358500；loose K=152/p=0.231355/E[8]=1.850837/MC=1.839500（以 baseline_3b.json 为准，口算四舍五入）。
- 检测器口径：strict = 规模索引间接 jmp ∨ -1/HRESULT 返回常量/可证伪哨兵 ∨ ≥2 张 vt 写或 ≥10 字段写 ∨ 回边+边界 cmp+动作(调用或非栈内存写) 的循环；loose = strict ∨ 细则#1（≥3 闸且 ≥3 个互异臂动作）。它是「宽松代理口径」，与逐行人工 ③b 判定同源（同一操作化），但不等价于审计员独立 D-42 实现；审计若用更严实现会得到更低基率（方向对本卡有利：基率高估=压低自身显著性）。
- 与 SURVEY_RING24 的 629 行差 28：SURVEY 用 `classification.tsv`（21 子系统 4,444 行，S09 ②∧④ 静态池 629）且过滤 atlas；本卡池直接用当前盘上 `COVERAGE\coverage.tsv` 的 S09 `[静态推断]`（657 行，含 M44 并表后 grade 变动），口径不同、各自自洽，不混用。
- `K = 行数 × 均值` 与 `E[8] = 8p` 是恒等式，非校验（M3）；本卡未把它们当证据。

## U3 · 004F4240 的 ② 归属层级

- 该 entry 在 9 张 RTTI 表同 slot0（Mouse/Display/GScreen/Map/Tab/Power/Radar/Scroll/Sidebar），按错源⑯（M1）归共同基类 GScreenClass；name 栏写 `GScreenClass::slot0` 与 ② 一致（M2）。盘上原名 `MouseClass::slot0` 被 ⑯ 更正，非改名增 named。
- ④ 为全 S09 A 集合唯一合法 livevt：g=0x87F7E8、vt=0x7E1964、slot=0、构造器 0x5BDA40 在 +0x0A(`0x5BDA4A`) 以 `mov [esi],0x7E1964` 装表、派发点 0x42933E。注意 install_site 0x40D1B2 是 atexit 析构器 0x40D1B0 内的绝对地址重写（`push 0x40D1B0; call 0x7C978A` @0x40D19A），属死表写；活 vptr 来自构造器 0x5BDA4A，满足错源㉓/纪律 10。

## U4 · 未纳入本卡的严格档候选

- `004E1530`/`004E1550`/`004E2580`/`00652E90`/`00653010`/`006D03A0` 等在本卡代理检测器下判 strict，但人工复核其 ③b 依赖字段写/栈槽/位压缩等机械可述或造型边界，未达 D-42 整体合同门槛，故未选入 8 行；不属「已判不成立」黑名单，仅为本卡取舍。
