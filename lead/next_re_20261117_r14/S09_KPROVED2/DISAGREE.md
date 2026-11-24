# S09-KPROVED2 · DISAGREE.md

卡号 S09-KPROVED2。记录本卡与盘面 / 上卡 / 口径的潜在分歧及消解。未改 coverage.tsv。

## D1 · L1「不得只用单张 vt 断言盘面名与类不符」—— 本卡无此类分歧（上卡 D1 前提在本卡不成立）
- **上卡翻车形态**：7 张表命中只引 1 张 ⇒ 误判"盘面名与类不符"。本卡 8 候选的 `rtti_classes` 全是**单类**（SidebarClass / TabClass / PowerClass / MouseClass / GaugeClass / RadarClass / ShapeButtonClass / ListClass），name 栏类与唯一命中表的 TD+8 名**逐字一致**，本就不存在"名不符"命题。
- **全表枚举（通道1）**：`work\enum_vtables.py` 从 `.rdata` 扫出**全部 1214 张** RTTI 可解表（vt-4=COL→COL+0xC=TD→TD+8 以 .?AV/.?AU 开头），逐表按真实 slot 走到首个非 .text 终止；8 行各**恰 1 张**命中（EVIDENCE\rtti_all8.txt）。
- **全文件出现点复算（通道2，不依赖 function_atlas entry+size）**：`work\occurrences_baseline.py` 扫全 exe 4 字节 VA，8 行各**恰 1 个原始出现地址 O**（如 006A5840→O=7F312C），且 O 正是通道1命中表的对应 slot（`7F3058+53*4=7F312C`）。两通道互证。
- **被拒的伪命中**：反向扫"任意前置合法 COL"会对同一 O 报出多个 `vt/slot`（如 006A5840 的 O=7F312C 被 7F2FCC[88] SelectClass、7F2F44[122] SBGadgetClass 等 9 个前置 COL 误纳）。这些**不是真实表**：那些 vt 起始的实际 slot 数到不了 O（下一张表的 COL 先到，slot 已终止）。按错源⑯「同址多表且同 slot ⇒ 归基类那一级」在此不适用（8 行无两表同 slot 真命中）。全部伪命中已按表区间排除，不写进 ② 栏。
- **结论**：8 行 ② 栏类名 == name 栏类名（L2 合规），无 DISAGREE 类属分歧；这是上卡 D1 的正面消解，不是"用单张 vt 断言"。

## D2 · 004E2690 GaugeClass::slot27 —— ③b 仅在细则#1 口径成立（细则#1 级边际，已并入）
- 盘面该行 grade `[静态推断]`；本卡并入 `[已证]`，依据是 ①②④ 齐全 + ③b①（线性化 switch 状多路分派，≥3 互斥闸各走不同绘制/取数动作）。
- **分歧点**：若只认 D-42 ③b 的"跳表 / 循环 / 错误码"三档（不认细则#1 的多路守卫链），本函数无 jmp 表、无循环、错误码仅 `call 48E620 → je 返回0` 一处弱约定 ⇒ ③b 不成立 ⇒ 不应并入。
- **处置**：按 L4 明说依赖 D-42 细则#1、标"细则#1 级边际"、给敏感性说明（coverage_delta.tsv 该行 one_line_semantics + EVIDENCE\analy3b_all8.txt）。若审计收紧细则#1，本行应首先回退。

## D3 · 0069DEB0 ShapeButtonClass::slot27 —— ③b 仅在细则#1 口径成立（细则#1 级边际，已并入）
- 盘面该行 grade `[静态推断]`；本卡并入 `[已证]`，依据是 ①②④ 齐全 + ③b①（互斥模式分派，模式 ebx∈{0,1,2,3,4} 各由不同 flag 组合决定）。
- **分歧点**：各"动作"差异仅体现为传给 4AED70 的模式值，弱于"各闸调不同函数"；无 jmp 表、无循环、错误码弱。若只认跳表/循环/错误码三档，本行 ③b 不成立。
- **处置**：按 L4 标"细则#1 级边际"并给敏感性说明；若审计收紧细则#1，本行应首先回退。

## D4 · L3 基线算术自洽（K = 行数 × 均值）—— 已双档自洽，无上卡 41/44 类错误
- 基线（seed 20261119，2000 次，S09 内随机取 8 行，EVIDENCE\baseline.json）：
  - **严格档**：总命中 2647 / 16000 抽样行；K(每试次均值)=**1.3235**；均值(每行)=**0.1654375**；校验 `8 × 0.1654375 = 1.3235 = K` ✅。
  - **loose 档**：总命中 2879 / 16000；K=**1.4395**；均值=**0.1799375**；校验 `8 × 0.1799375 = 1.4395 = K` ✅。
- 上卡 K=41/44 反解应≈43.2/46.2 的错误在本卡不复发：K 与均值由同一总数导出，算术恒等。
- 两档并列报告，未把 loose 当严格、也未把严格当 loose（SURVEY_RING24 口径：严格=②仅RTTI×④严格档，loose=④宽松含槽号歧义 livevt）。

## D5 · ④ direct 站点自证（错源㉖ / 纪律 4）
- 全 `.text`（0x401000..0x7E038D，100% VirtualSize）capstone skipdata 扫描 = 1,394,186 指令 / **68,253 个 E8@边界**（与 SURVEY_RING24 的 E8 数逐字相同）。
- 8 行每个交付站点都落在自报覆盖范围内，且逐站验证 `byte==E8`、`site+5+rel32==entry`、`in_body==False`、`selfloop==False`（EVIDENCE\direct_sites.txt）。
- 双通道：通道1=全 E8@边界 sweep 反查 target；通道2=classification.tsv 的 ring4_direct_sites 列表交叉。两者对 8 行交集非空且一致（本卡 8 行通道1命中站点数 ≥ 通道2列表数，多出的站点同样满足四条件）。无"最近 E8"启发式。
