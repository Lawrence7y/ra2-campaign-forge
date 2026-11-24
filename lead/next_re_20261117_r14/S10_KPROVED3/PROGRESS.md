# S10-KPROVED3 · PROGRESS

> 卡号 S10-KPROVED3｜执行员 agent-30｜开工 2026-11-19T15:14+08:00｜目标 `ra2youli\gamemd.exe` 只读 SHA-256 `73201CC0…F67476`（现场全值 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` ✓）· ImageBase 0x400000。Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26；未建 venv、未 pip install。

## 开工必读（已读）
R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条；PENDING_DECISIONS D-40/D-41/D-42；SURVEY_RING24\PROGRESS.md。前 10 分钟先落本骨架（≥5 行）——已完成。

## 行源
S10 A 集合 = **49** 行（②RTTI ∧ ④strict，与 SURVEY_RING24 S10 A=49 一致）；已并入 8 行（004D74E0/004D7D50/004D7170/004D85D0/004DB3C0/004D9960/004DF040/004DB690）全部排除，余 **41** 候选；本卡取 8 行，不扩。

## 8 行（①入口 ②持有表+⑯归属 ③b+入口相对偏移 ④站点 逐环证据见 EVIDENCE/per_row/）
| entry | name(=②归属) | ② 全部持有表 / 归属 | ③b 档 + 相对偏移 | ④ 站点 |
|---|---|---|---|---|
| 004D82B0 | FootClass::slot289 | 1 表 7e8c94/s289 ⇒ FootClass | ④循环 +0x104..+0x11A | 00417782/0051CBB1/00738983 |
| 004D5690 | FootClass::slot335 | 2 表同 s335(22a4+8c94) ⇒ 基类 FootClass(⑯) | ④循环 +0x3F9..+0x40F | 0052236E/00741689 |
| 004DB260 | FootClass::slot53 | 2 表同 s53(22a4+8c94) ⇒ 基类 FootClass(⑯) | ④循环 +0x38..+0x89 | 00414112/00517E6C/0051DF53/0073584F/007440B4 |
| 00702D40 | TechnoClass::slot56 | 5 表同 s56 ⇒ 基类 TechnoClass(⑯) | ①跳表 +0x2EE | 00744790 |
| 00706640 | TechnoClass::slot273 | 6 表同 s273 ⇒ 基类 TechnoClass(⑯) | ①跳表 +0x24（另 2 循环） | 004DAFAB |
| 00708C30 | TechnoClass::slot174 | 4 表同 s174 ⇒ 基类 TechnoClass(⑯) | ①跳表 +0x1E | 0044D715 |
| 004D94B0 | FootClass::slot288 | 1 表 7e8c94/s288 ⇒ FootClass | ②返回约定 +0xD1..+0xDD | 0041AAA6/0041AD06/0041ADB4/0051B1D2/00742D0B/00743161 |
| 004DDDE0 | FootClass::slot28 | 1 表 7e8c94/s28 ⇒ FootClass | ①′守卫链 +0x70..+0xC3 | 00417FAA/0051F833/007404F6 |

## 核心数字
- **8 行中四环齐全数 = 8/8**（①入口 16B 对齐 + E8 直调目标；② RTTI 全持有表枚举、2+ 表同槽按⑯归基类；③b 跳表×3 + 完整循环×3 + 返回约定×1 + 守卫链×1；④ E8 边界 + site+5+rel32==entry + 体外 + 非自环）。
- **delta 行数 = 8**（= 自报行数，M6/M15）；8 行 grade 提议 `[已证]`。
- **S10 A 集合总行数 = 49**。
- **③b 基率**（seed 20261119，2000 次取 8，池 = S10 静态推断 398 行）：strict **0.3277**（129/398，均值 2.6215）/ loose **0.2395**（95/398，均值 1.9160）；core（四硬档）0.1198。K=行数×均值恒等式，非校验（M3）。

## 方法与纪律
- 扫描 100% `.text`：1,392,592 指令 / 68,253 `E8`@边界 / 6,728 distinct target（与前卡基准逐字同）；RTTI census 经 `COL=vt-4 → TD=COL+0xC → TD+8` 内联名逐字符读，读不到 fail-closed。
- ② 全持有表枚举（holding_tables.tsv）；2+ 表同 slot 归基类，name 栏类名与 ② 一致（M2/纪律12）。③b 偏移一律入口相对 +0xNN，与 ring3b.tsv 一致（M5）；循环均有显式内存写（M7）。④ 站点用函数区间包含判归属，非 entry_at_or_before；24 个站点全 E8 边界+rel32+体外（纪律1/4/5）。
- 细则#1 行（004DDDE0）已逐闸证动作不同（M4）；5 行类名按⑯改基类已显式披露（UNKNOWNS U2/DISAGREE D1）；one_line_semantics 全为 ③b 级整体合同，无自陈未证字样（M8）。
- 未写台账/COVERAGE/R14_COMMON/STATUS_BOARD/ra2youli/其它卡/`_audit`；未改 coverage.tsv（只交 coverage_delta.tsv，纪律11）；未 git commit；未用「最近 E8/最大函数/无调用者」启发式。

## 交付
`PROGRESS.md` | `UNKNOWNS.md`(U1–U8) | `DISAGREE.md`(D1–D7) | `coverage_delta.tsv`(8 行 6 列) | `EVIDENCE/`(holding_tables.tsv / ring3b.tsv / ring4_verified.tsv / baseline_3b.txt / summary.json / per_row\8 文件) | `work/`(s0–s6 自写脚本 + dumps/sites/analysis.json/baseline.json/feature_inventory.txt) | `_ghidra\S10_KPROVED3\`(空，-noanalysis)。
