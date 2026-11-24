# S05-KPROVED3 · PROGRESS — S05 A 集合未并入部分补 ②/③b/④（只做 8 行，不扩）

卡号 S05-KPROVED3；开工 2026-11-19T15:44+08:00；骨架 10 分钟内先落（已守）。写域仅 `S05_KPROVED3\` 与 `_ghidra\S05_KPROVED3\`（-noanalysis）；未写 COVERAGE/台账/R14_COMMON/STATUS_BOARD/ra2youli/其它卡/_audit；未建 venv、未 pip install、未改游戏文件、未 git commit。

目标 `ra2youli\gamemd.exe` 只读：SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（前缀 73201CC0/后缀 F67476，现场复核一致）；ImageBase 0x400000。Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra 分析（_ghidra 空目录）。

必读已核：R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条/**§8.7 九条判据**；PENDING D-40/D-41/D-42（含细则#1/#2/#3）；SURVEY_RING24\PROGRESS.md。逐条落实 M1–M8 与纪律 1–16。

行源：classification.tsv `subsystem=S05 ∧ has4_strict=1 ∧ has2_rtti=1`（A 集合）共 41 行，排除 S05_KPROVED2 已并入 8 行（00413F80/006F4AB0/006F6AC0/0070C270/007077C0/00716DC0/007162F0/00700600），余 33 行中选 8。本卡 8 行：006F3330 006F8DF0 006FC0B0 006FFEC0 00704350 0070BF50 00712170 00716150。

## 核心数字（全部自算复现）
- **8 行中四环齐全数 = 8**：①②③④全齐，③b 全为 strict 档（③b② 可证伪错误码 + ③b④ 有界循环），不依赖 D-42 细则#1。交付 `coverage_delta.tsv` **8 行**（= 自报 8 行，M6）。
- **S05 A 集合总行数 = 41**（`has2_rtti=1 ∧ has4_strict=1`），与 SURVEY S05 A=41 逐字一致；`has4_strict=1` 单看是 70（29 行无 RTTI②）。已用 exe 字节独立复算（RTTI crosscheck diffs=0）。
- **③b 基率**（S05 `[静态推断]` 池 N=387，seed 20261119，2000 次抽8不放回，D-42 忠实检测器）：strict K=91/p=0.235142/E[8]=1.881137/MC=1.836500；loose K=147/p=0.379845/E[8]=3.038760/MC=2.997500。见 EVIDENCE/baselines.json。
- **N=387 而非前卡 395**：前卡 8 行已并入 coverage.tsv（现均 `[已证]`），池由 395→387（395-8）。S05 现态 387 静态推断 + 98 未证 + 158 已证 = 643。
- 「K=N·p / E[8]=8p」是恒等式不是校验（M3）；真校验是逐行字节证据。
- 全 `.text` 扫 1,392,592 指令 / 68,253 E8@边界 / 6,728 distinct（SURVEY 基准逐字同，双通道⑩）。

## 8 行交付（entry / name / ②持有表 / ③b / ④站点数 / 错源⑯）
| entry | name | ② holders | ③b (strict) | ④dir | 错源⑯归属 |
|---|---|---|---|---|---|
| 006F3330 | FootClass::slot185 | 4表同slot185 | ②-1哨兵2处 | 2 | 基类级(TechnoClass) |
| 006F8DF0 | TechnoClass::slot241 | 1表 | ④显式对象写有界循环 | 2 | TechnoClass级 |
| 006FC0B0 | FootClass::slot240 | 2表同slot240 | ②-1哨兵4处 | 4 | 基类级(TechnoClass) |
| 006FFEC0 | TechnoClass::slot29 | 1表 | ②-1哨兵+④循环 | 2 | TechnoClass级 |
| 00704350 | TechnoClass::slot187 | 1表 | ②-1哨兵3处+④循环 | 1 | TechnoClass级 |
| 0070BF50 | TechnoClass::slot5 | 1表 | ②负返回约定+④循环 | 2 | TechnoClass级 |
| 00712170 | TechnoTypeClass::slot25 | 1表 | ②-1哨兵35处+④显式写循环 | 4 | TechnoTypeClass级 |
| 00716150 | AircraftTypeClass::slot42 | 4表同slot42 | ④0x7fff哨兵循环(累加器写) | 1 | 基类级(TechnoTypeClass) |

## 环成立判据（逐行见 EVIDENCE/ROW_*.txt）
- ① 8 行 entry 全 16B 对齐；② 全 .rdata 4 对齐原始命中穷举：3 行多持有表（4/2/4）按 M1/错源⑯归基类级、DV/V 同slot别名已查均「无」、name 类逐字出现在 TD+8 持有表中（M2）；5 行单表。
- ③b 全 strict：可证伪 -1/0x7fff 哨兵（读者可预测错路）、负返回约定（jl→ret 负值）、有界循环（显式对象写或明标累加器写口径 + 推进 + 界判）；偏移全部入口相对 +0xNN，与 EVIDENCE 同源。无一行依赖 D-42 细则#1。
- ④ E8 指令边界（capstone skipdata 全扫）+ site+5+rel32==entry + 站点在自写 CFG 体外 + 非自环；thiscall ecx 来源逐站点回溯（多数 `mov ecx,<reg>` 前置）；站点归属按函数区间包含，非 entry_at_or_before。

## 不进 delta 的 25 行（理由见 UNKNOWNS）
③a 薄桩/清零 20 行 + ③b 仅 loose 3 行 + 00703860(假回跳)/005F9720(memset清零) 2 行。

## 交付与自检
- `coverage_delta.tsv` 8 行 6 列；②栏类名与 name 栏一致 ✅；偏移 +0xNN ✅；无自陈未证字样 ✅；行数=自报=8 ✅。
- `EVIDENCE/`：ROW_* 8 份（②全表/④全站点字节/③b特征/全文反汇编）、ROW_SUMMARY.json、baselines.json。
- `work/`：pe_helpers / verify_cache / rtti_enumerate / cfg_analyze / categorize_remaining / detail_candidates / dump_disasm / ctx_extract / ctx2 / loop_body / scan_8df0 / exact_check / site_verify / baselines / gen_evidence / build_delta + 中间件。
- `UNKNOWNS.md` U1–U8；`DISAGREE.md` D1–D6；进度：完成。
