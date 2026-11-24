# S10-KPROVED4 · PROGRESS

> 卡号 S10-KPROVED4｜开工 2026-11-19T16:12+08:00｜目标 `ra2youli\gamemd.exe` 只读，SHA-256 `73201CC0…F67476` 现场复核一致 · ImageBase 0x400000。Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26；未建 venv、未 pip install。写域仅本目录 + `_ghidra\S10_KPROVED4\`（未跑）。前 10 分钟先落本骨架（≥5 行）——已完成。

## 开工必读（已读）
R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条/§8.7 九判据；PENDING_DECISIONS D-40/D-41/D-42（含操作化细则#1/2/3）；SURVEY_RING24\PROGRESS.md。

## 行源与排除集
S10 A 集合 = **49**（②RTTI∧④strict，自数 50 has4 减 004CBBA0 无②，与 SURVEY S10 A=49 一致）。排除集合并去重 = 16：KPROVED2 8 + KPROVED3 8（含被否的 004DDDE0）+ SEMFIX_SLOTS2 7（全部是 KPROVED3 子集）。余 33。本卡按「最接近 ③b 的形态」取 8 行深查（给最大善意）：004D55C0/004D55F0/004D9C10/00517CC0/004DBAD0/006F3AD0/006FBDC0/006FBC90。

## 逐环结论（①入口 / ②全持有表+⑯ / ③b档+入口相对锚 / ④站点）
8 行 **① 全成立**（E8 直调目标，各 1–6 站点，E8 边界+rel32==entry+体外+非自环）；**② 全成立**（全 RTTI 持有表枚举，2+ 表同 slot 按⑯归基类：006F3AD0→TechnoClass/006FBDC0→TechnoClass/006FBC90→TechnoClass/004D55C0·55F0→FootClass）；**③b 全部不成立（落 ③a）**，逐行锚与失败理由见 UNKNOWNS U2 + EVIDENCE/per_row；④ 全成立。`coverage_delta.tsv` 表头 1 行、**0 数据行**。

## 核心数字
- **8 行中四环齐全数 = 0 / 8**（①8 ②8 ③b**0** ④8；③b 是唯一缺环）。
- **delta 行数 = 0**（= 自报行数，M6/M15）；8 行 grade 保持 `[静态推断]`，盘上未改一行。
- **S10 A 集合总行数 = 49**。
- **③b 基率**（seed 20261119，2000 次取 8，池 S10 `[静态推断]` 398 行）：strict **0.138191**（55/398，E[8]=1.105528，MC=1.1140）/ loose **0.163317**（65/398，E[8]=1.306533，MC=1.3300）。K=N·p 与 E[8]=8p 为恒等式非校验（M3）；报的是 ③b 基率非 ②∧④ 入选率（§8.7 判据4）。

## 方法与纪律
- 扫描 100% `.text`：1,394,186 指令 / 68,253 `E8`@边界 / 6,728 distinct target；RTTI census **1216 COL / 1214 vt / 14,044 槽**（COL=vt−4→TD=COL+0xC→TD+8 内联名逐字符读，fail-closed；修正了 KPROVED3 审计指出的 0x7E4960→0x7F4960、BuildingClass COL/TD 错误）。
- ③b 检测器经 **15 行已并入行阳性对照**（跳表 jt=1 / 循环写 nw≥1 / HRESULT 0x80004002 全命中，15/15）与**基率谓词交叉验证**（已并入 14/15 strict=True、004DDDE0 False 与审计一致、本卡 33 行 0 strict）双重自证非漏检（UNKNOWNS U3）。
- 函数区间包含判④归属（非 entry_at_or_before）；② 全持有表枚举+上层同 slot 值验证引入层；守卫链逐闸打到 ret 核对动作（纪律2/3）；偏移与自家 EVIDENCE 同源（M5）；语义栏遵守 M8 整体合同写法（本卡 delta 0 行，无语义栏需落笔）。
- 未写台账/COVERAGE/R14_COMMON/STATUS_BOARD/ra2youli/其它卡/`_audit/`；未改 coverage.tsv（只交 coverage_delta.tsv，纪律11）；未 git commit；未用「最近 E8/最大函数/无调用者」启发式；atexit 析构器虚表不计活 vptr。

## 交付
`PROGRESS.md` | `UNKNOWNS.md`(U1–U6) | `DISAGREE.md`(D1–D6) | `coverage_delta.tsv`(表头+0 行) | `EVIDENCE/`(holding_tables.tsv / ring4_verified.tsv / per_row\8 / disasm\21 / candidate_analysis*.json / b3_classification.json / guard_shape_check.json / baseline_3b.json / function_extents.json) | `work/`(core + s1–s8 自写脚本，未 import 它卡)。
