# S10-KPROVED3 · UNKNOWNS

行源 = S10 A 集合 49 行，已并入 8 行排除后余 41 行；本卡取其中 8 行。逐行四环证据见 `EVIDENCE/per_row/`。

## U1 · 行源与已并入排除
S10 A 集合 = **49**（`has2_rtti=1 ∧ has4_strict=1`，与 SURVEY_RING24 `MATRIX.tsv` S10 A=49 一致）。已并入 8 行（`004D74E0 004D7D50 004D7170 004D85D0 004DB3C0 004D9960 004DF040 004DB690`）全部排除；本卡 8 行 entry 与之无交集。

## U2 · 5 行的类名按错源⑯改为基类级（delta name 与 classification.tsv 原名不同）
下列 5 行的 entry 被 **2 张以上虚表以同一 slot 持有**，按 R14_COMMON §8.1 错源⑯ 归基类级；`coverage_delta.tsv` 的 `name` 栏写归属基类，与 delta ② 栏类名一致（M2/纪律12）。classification.tsv `name` 原名一并列出，供合并员核对：

| entry | classification 原名 | 本卡 name（②归属） | 同 slot 持有表数 |
|---|---|---|---|
| 004D5690 | AircraftClass::slot335 | FootClass::slot335 | 2（Aircraft 22a4 + Foot 8c94）|
| 004DB260 | AircraftClass::slot53 | FootClass::slot53 | 2（Aircraft 22a4 + Foot 8c94）|
| 00702D40 | AircraftClass::slot56 | TechnoClass::slot56 | 5（Aircraft/Building/Foot/Infantry/Techno）|
| 00706640 | AircraftClass::slot273 | TechnoClass::slot273 | 6（上述 + Unit）|
| 00708C30 | AircraftClass::slot174 | TechnoClass::slot174 | 4（Aircraft/Foot/Infantry/Techno）|

这是**类名更正**不是新命名：`slotN` 是占位名，不计入 `named(S)`（§8.1⑬），本批 named 净增 0。若合并员认为应保留盘上原名，则这 5 行的 name 需按 CONFLICTS 流程另裁，grade/四环结论不受影响。

## U3 · ③b 细则#1 级行（严格口径敏感）
- **004DDDE0**（③b①′）完全依赖 D-42 细则#1 的「多路守卫链」解释（6 道互斥闸、三结局 ebx/1/2、五个不同被调、无共同汇入 call）。若审计只认硬四档（跳表/循环/错误码/内存形状），该行落 ③a ⇒ 四环齐全数 8→7、delta 7 行。M4 已逐闸给出不同动作（见 ring3b.tsv）。
- **004D94B0**（③b②）为可证伪返回约定：`call 0x45aea0` 返回值 `>=0` 或 `==0x80004002(E_NOINTERFACE)` 放行、其余负值走 `call 0x7dc720` 断言。该行同时有一串 `cmp/jne` 守卫；③b 成立只依赖 +0xD1..+0xDD 的返回值检视，不依赖守卫链。若审计要求「返回约定须是本函数自己的返回值而非被调返回值的检视」，该行需重判。

## U4 · ③b 基率口径（本卡自算，与前卡不同检测器）
`work/s4_baseline.py` 在 S10 静态推断池（n=398）上自算，seed 20261119、2000 次每次取 8 不放回：
- strict ③b（含 D-42 细则#1 守卫链）：129/398=0.3241；8 行均值 2.6215 ⇒ 基率 **0.3277**；
- core ③b（只 ①②③④ 四硬档）：47/398=0.1181；均值 0.9585 ⇒ 0.1198；
- loose D-42(A)：95/398=0.2387；均值 1.9160 ⇒ **0.2395**。

与前卡 S10_KPROVED2 自报（strict 0.2437/loose 0.5653）不同：本卡 loose 严格按 D-42(A)「出向 call + 分支 + ≥2 字段写」实现，未把「任一后向跳/任一 0x8000xxxx」当 loose（那是前卡 DISAGREE D4 承认的高估）。本卡 strict 129 与前卡审计 117 同量级（差在该检测器把部分守卫链计入）。**K=行数×均值是恒等式不是校验**（M3）。

## U5 · ③b 检测器假阳性已人工剔除
自动 inventory（`work/feature_inventory.txt`）对 5 字节桩 `004DA2B0`/`004DE620` 报出 `+0xBE00` 级 switch/loop 偏移，系 CFG extent 越界落入邻函数；本卡按 `entry+atlas_size` 截断后无硬 ③b，未纳入。同理 `004D82B0` 的 ext_hi=entry（破损），按 atlas_size=679 重扫得到真循环 `+0x104..+0x11A`。

## U6 · ④ 站点 ecx 溯源
全部 24 个 direct 站点经「E8 指令边界 + site+5+rel32==entry + 站点在函数体外 + 非自环」验证（`EVIDENCE/ring4_verified.tsv`）。单站点行：`00702D40`(00744790)、`00706640`(004DAFAB)、`00708C30`(0044D715) 各 1 个，与已并入的 `004DF040` 单站点形态一致。部分站点 ecx 在 -40B 窗口内未见 `mov ecx`，但 ④ 的成立条件是 E8 边界/rel32/体外，thiscall 接收者由类属（②）与虚表槽合同（③b）共同保证；未据此单独升格任何环。

## U7 · 未选的 33 行（41−8）
- 自动 ③b 探测器 strict/core 命中但归属/语义不足硬证的行：`00517CC0`（InfantryClass::slot9，仅守卫链，④ 1 站点）、`006FB010`/`006FBC90`/`006FC030`/`0070E140`/`00707D20`（均仅守卫链、5 表同槽但 ③b 无硬档）。这些留给后续卡判定，本卡不宣称其四环状态。
- 其余 27 行：③a（机械可述/无关键判据）或 ③b 硬特征仅来自 5 字节桩假阳性，不进 delta。
- `004D55C0`/`004D55F0`（FootClass::StopMoving/MoveTo，3 表同 slot，④ 2/1 站点）体内无硬 ③b，本卡不纳入。

## U8 · 纪律/边界合规
未改 `gamemd.exe`/`ra2youli`/coverage.tsv/台账/R14_COMMON/STATUS_BOARD/其它卡/`_audit`；未建 venv、未 pip install；未 git commit；只交 `coverage_delta.tsv`。双通道：② 走自写 RTTI census（不依赖 function_atlas entry+size）+ ④ 走全 `.text` 100% 指令扫描（1,392,592 指令 / 68,253 E8@边界 / 6,728 distinct target，与前卡基准逐字同）；站点归属用函数区间包含，非 entry_at_or_before。
