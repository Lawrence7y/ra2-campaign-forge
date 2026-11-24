# S05-KPROVED2 · PROGRESS

卡号 S05-KPROVED2；任务：只做 8 行，S05 的 A 集合（②∧④ 结构齐备），只加 proved 不改 named。开工骨架在 10 分钟内落地。

目标 `ra2youli\gamemd.exe` 只读；SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（前缀 73201CC0/后缀 F67476，现场复核一致）；ImageBase 0x400000。Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未建 venv、未 pip install、未用 Ghidra、未改游戏文件/台账/coverage.tsv、未 git commit。

写域仅 `lead\next_re_20261117_r14\S05_KPROVED2\` 与 `_ghidra\S05_KPROVED2\`（-noanalysis）；禁写 COVERAGE\、台账、R14_COMMON.md、STATUS_BOARD.md、ra2youli\、其它卡目录、_audit\。

必读已核：R14_COMMON §1/§6/§7/§8.1（错源⑬⑭⑮⑯⑰⑲⑳㉑㉒㉓）/§8.5/§8.6 六条；PENDING D-40/D-41/D-42（含细则#1/#2/#3）；SURVEY_RING24\PROGRESS.md。

## 核心数字（全部自算复现）
- **8 行中四环齐全数 = 8**（①②③④全齐，③b 全为 strict 档，不依赖 D-42 细则#1）。交付 `coverage_delta.tsv` **8 行**。
- **S05 A 集合行数（自数）= 41**：`has2_rtti=1 ∧ has4_strict=1`（单看 has4_strict=1 是 70，其中 29 行无 RTTI②），与 SURVEY S05 A=41 一致。已用 exe 字节独立复算（41 行 entry 的 .rdata 原始命中数 == 有效 RTTI 持有表数）。
- **S05 盘面**：coverage.tsv S05 n=643 = 150 `[已证]` + 395 `[静态推断]` + 98 `[未证]`；门槛 `ceil(0.5×643)=322`。本卡只加 proved 8 行，不改 named。
- **③b 基率**（S05 `[静态推断]` 池 N=395，seed 20261119，2000 次抽8不放回）：strict K=103/p=0.260759/E[8]=2.086076/MC=2.109500；loose K=157/p=0.397468/E[8]=3.179747/MC=3.182500。见 EVIDENCE/baselines.json。
- **「K = 行数 × 均值」是恒等式不是校验**：8×p ≡ E[8]（实测差 0.0e+00）；真校验是逐行字节证据。
- 全 `.text` 扫 1,392,592 指令 / 68,253 E8@边界 / 6,728 distinct target，与 SURVEY 基准逐字相同（§8.6 条1/4 双通道）。

## 8 行交付（entry / name / ②持有表 / ③b档 / ④站点数）
| entry | name | ② vt[slot] TD+8 | ③b (strict) | ④direct |
|---|---|---|---|---|
| 00413F80 | AircraftClass::vslot9 | 7E22A4[9] .?AVAircraftClass@@ | ②-1哨兵回退+④查表循环 | 1 |
| 006F4AB0 | TechnoClass::slot101 | 7F4960[101] .?AVTechnoClass@@ | ①物理跳表(11项/byte索引29项) | 8 |
| 006F6AC0 | TechnoClass::slot53 | 7F4960[53] .?AVTechnoClass@@ | ④链表遍历循环 | 2 |
| 0070C270 | TechnoClass::slot13 | 7F4960[13] .?AVTechnoClass@@ | ②-1哨兵4处+④数组循环 | 2 |
| 007077C0 | TechnoClass::slot10 | 7F4960[10] .?AVTechnoClass@@ | ②-1哨兵4处+④有界循环5段 | 2 |
| 00716DC0 | TechnoTypeClass::slot6 | 7F4ED8[6] .?AVTechnoTypeClass@@ | ④数组循环9段 | 4 |
| 007162F0 | TechnoTypeClass::slot5 | 7F4ED8[5] .?AVTechnoTypeClass@@ | ④数组循环29回跳 | 4 |
| 00700600 | TechnoClass::slot28 | 7F4960[28] .?AVTechnoClass@@ | ②-1哨兵3处+④有界循环 | 3 |

## 环成立判据（逐行见 EVIDENCE/ROW_*.txt）
- ① entry 16B 对齐；② 全 .rdata 原始命中穷举，8 行均 holders=1、类名与 name 栏逐字一致、无 DV/V 同slot别名（错源⑯ 不触发）；
- ③b 全部 strict 档：物理跳表（006F4AB0，逐项目标全在体内）/ -1 哨兵可证伪约定 / 有界循环（inc→cmp→jl 回跳）；偏移全部入口相对 +0xNN。
- ④ E8 指令边界（capstone skipdata 全扫）+ site+5+rel32==entry + 站点在 CFG 体外 + 非自环；逐站点字节见 EVIDENCE/ROW_*.txt。
- 无一行依赖 D-42 细则#1；无 livevt 行（S05 A=41 全 direct）。

## 交付与自检
- `coverage_delta.tsv`：8 行，6 列（entry/subsystem/name/one_line_semantics/grade/evidence_path），②栏类名与 name 栏一致 ✅。
- `EVIDENCE/`：ROW_00413F80.txt…ROW_00700600.txt（8 份，含②全表/④全站点逐字节/③b特征/全文反汇编）、ROW_SUMMARY.json、baselines.json。
- `work/`：pe_helpers.py / build_sweep.py / rtti_enumerate.py / cfg_analyze.py / gen_evidence.py / baselines.py / build_delta.py / categorize.py + 中间件（*.pkl/json）。
- `UNKNOWNS.md` U1–U7；`DISAGREE.md` D1–D5。
- 自检：delta 8 行 == 自报 8 行 == EVIDENCE ROW_* 8 份；地址集三者一致；偏移一律 +0xNN；③b 基率已报（非入选率）。

进度：完成。
