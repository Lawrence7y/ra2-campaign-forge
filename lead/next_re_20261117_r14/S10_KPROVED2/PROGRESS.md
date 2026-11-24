# S10-KPROVED2 · PROGRESS

- 卡号 S10-KPROVED2；开工 2026-11-19T14:05+08:00；目标 `ra2youli\gamemd.exe` 只读 SHA-256 前缀 `73201CC0` 后缀 `F67476`（现场全值 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` 一致）；ImageBase 0x400000。Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26；未建 venv、未 pip install。写域仅本目录 + `_ghidra\S10_KPROVED2`（-noanalysis，未跑）。
- 已读 R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条；PENDING_DECISIONS D-40/D-41/D-42；SURVEY_RING24\PROGRESS.md。
- 行源：classification.tsv 筛 subsystem=S10 ∧ has4_strict=1 得 **50** 行；`004CBBA0` 无 ②（has2_rtti=0）剔除 ⇒ **S10 A 集合 = 49**（自数确认，与 SURVEY 记 S10 A=49 一致）。本卡只做 8 行，不扩。

## 8 行（全部四环齐全，②/③b/④ 逐行证据见 EVIDENCE\per_row\*.txt）
| entry | name | ② 持有表(vt/slot/TD+8) + ⑯归属 | ③b 档 + 入口相对偏移 | ④ 站点(E8 边界/体外) |
|---|---|---|---|---|
| 004D74E0 | FootClass::slot81 | 1 表: 7e8c94/s81/.?AVFootClass@@ ⇒ FootClass | ①跳表 +0x5c（13 目标） | 00417C4E/0051F1EF/00738902 |
| 004D7D50 | FootClass::slot80 | 1 表: 7e8c94/s80/.?AVFootClass@@ ⇒ FootClass | ①跳表 +0x90（11 目标） | 00417C94/0051F2AF/0073895D |
| 004D7170 | FootClass::slot54 | 1 表: 7e8c94/s54/.?AVFootClass@@ ⇒ FootClass | ④循环 +0xeb..+0x13c（8邻格 ++） | 0041439B/0051E0D6/00737BB1 |
| 004D85D0 | FootClass::Mode2CellAndMissionStateRefresh_behavior | 2 表同 slot99: 7e22a4/.?AVAircraftClass@@ + 7e8c94/.?AVFootClass@@ ⇒ 基类 FootClass(⑯) | ④循环 +0xc4..+0x11a（8邻格 --） | 0051A9FC/0073A4FB/0073B0A0 |
| 004DB3C0 | FootClass::slot5 | 1 表: 7e8c94/s5/.?AVFootClass@@ ⇒ FootClass | ④循环 +0x128..+0x18e（追加+边界） | 0041B4BE/005219EE/007444FE |
| 004D9960 | FootClass::slot10 | 1 表: 7e8c94/s10/.?AVFootClass@@ ⇒ FootClass | ④循环 +0x213..+0x229（删除左移） | 0041B66E/0051AA1E/007446EE |
| 004DF040 | FootClass::slot330 | 3 表同 slot330: 7e8c94/Foot + 7eb058/Infantry + 7f5c70/Unit ⇒ 基类 FootClass(⑯) | ④循环 +0x1e..+0x75（最佳查找） | 0041BC17 |
| 004DB690 | FootClass::slot6 | 1 表: 7e8c94/s6/.?AVFootClass@@ ⇒ FootClass | ④循环 +0x4c..+0x6f（有界查询） | 0041B5CF/00521B0F/00744629 |

## 核心数字
- **四环齐全数 = 8 / 8**（①入口 E8 直调目标 ✓ / ② RTTI 持有表 ✓ / ③b 跳表×2+完整循环×6 ✓ / ④ direct 站点 E8 边界+rel32==entry+体外 ✓）。全部进 coverage_delta.tsv（grade [已证] 提议）。
- **S10 A 集合行数 = 49**（50 个 has4_strict=1 减 004CBBA0 无 ②）。
- **③b 基率**（seed 20261119，2000 次，池=S10 全部 398 行，同子系统随机取 8）：strict 档 97/398=24.37%、8 行均值 **1.9945**（24.93%）；loose 档 225/398=56.53%、8 行均值 **4.5710**（57.14%）。`K = 行数×均值` 是恒等式（strict 8×0.2437=1.9497；loose 8×0.5653=4.5226），非校验；基线报的是 ③b 基率，非 ②∧④ 入选率。

## 方法与纪律
- 扫描 100% `.text`：1,394,186 指令 / 68,253 `E8`@边界 / 6,728 distinct target（与 SURVEY 基准逐字同）；全镜像 RTTI census 1,185 表，COL=vt-4→TD=COL+0xC→TD+8 内联名逐字符读，读不到 fail-closed。
- ② 全部持有表枚举（holding_tables.tsv），2+ 表同 slot 按 ⑯ 归基类；name 栏类 = 归属类（FootClass），纪律 12 自洽。③b 偏移一律入口相对 +0xNN。站点用函数区间包含判归属，不用 entry_at_or_before。
- capstone 已知阳性自检：`0x4386AB call [edx+0x10]` 命中；mem index 无索引返 0（⑲）已处理。
- 未写台账/COVERAGE/其它卡/ra2youli；未 git commit；未改 coverage.tsv（只交 coverage_delta.tsv）。未用启发式（最近 E8/最大函数/无调用者）；未复制其它卡 work 代码。

## 交付
PROGRESS.md | UNKNOWNS.md（U1–U9） | DISAGREE.md（D1–D7，D7 为 004D85D0 与台账旧裁决的分歧） | coverage_delta.tsv（8 行） | EVIDENCE\（holding_tables.tsv / ring4_verified.tsv / ring3b.tsv / summary.json / per_row\8 文件 / baseline_3b.txt / jump-table 与 loop dump 经 work\ 脚本） | work\（re_core/call_sweep/func_analyze/baseline/gen_evidence 等自写脚本，未 import 它卡）。
