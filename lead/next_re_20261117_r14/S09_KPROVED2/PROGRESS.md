# S09-KPROVED2 · PROGRESS

卡号 S09-KPROVED2。开工 2026-11-19T13:36:18+08:00。写域仅 S09_KPROVED2\（Ghidra 未用，未建 _ghidra\S09_KPROVED2\）。目标 `ra2youli\gamemd.exe` 只读：SHA-256 `73201CC0…F67476`（现场全值复算 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`），ImageBase 0x400000。Python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26；未建 venv、未 pip install、未改游戏文件、未改 coverage.tsv、未写台账、未 git commit。
已读：R14_COMMON §1/§6/§7/§8.1(13/14/15/16/17/23)/§8.5/§8.6 六条；PENDING_DECISIONS D-40/41/42（含 D-42 细则#1/2/3）；SURVEY_RING24\PROGRESS.md（口径）。

## 1. 行源与 8 候选（S09 A 集合 ②仅RTTI∧④严格档，剔除上卡已并 8 entry）
必须排除（已剔除）：004AAE90 005BDF70 006A5310 004AB9B0 0063FEA0 006A7780 004ACE70 006ABD30。
选定 8 行（全部从 exe 复算确认，非仅信 classification.tsv）：
`006A5840` SidebarClass::slot53｜`006D0680` TabClass::slot10｜`0063FB20` PowerClass::slot16｜`005BE6D0` MouseClass::slot31｜`004E2690` GaugeClass::slot27｜`00654320` RadarClass::slot34｜`0069DEB0` ShapeButtonClass::slot27｜`00557730` ListClass::slot42。

## 2. 第一个候选 006A5840 的 ② 证据（全表枚举，L1/L2 合规）
全 1214 张 RTTI 可解表中**恰 1 张**命中：vt=`0x7F3058`，slot=`53`；vt-4=COL `0x8095B8` → COL+0xC=TD `0x816C38` → TD+8 内联 ASCII 逐字符 `.?AVSidebarClass@@`；vt[53]=0x006A5840=entry。②类名与 name 栏 SidebarClass 一致（L2 合规），非"单表断言名不符"。

## 3. 核心数字
- **8 行中四环齐全数 = 7**（①②③④齐全；004E2690、0069DEB0 的③b 为 D-42 细则#1 级边际，已按 L4 明说并给敏感性；00654320 仅③a，不进 delta）。交付 `coverage_delta.tsv` 7 行。
- **A 集合 S09 总行数 = 103**（自己数：exe 复算 ②RTTI 槽命中 601 行、④direct 站点体外 128 行、交集 102 行 direct + 1 行 livevt `004F4240` = 103；与 SURVEY_RING24 的 S09 A=103、④dir/lv=102/1 及 classification.tsv 一致。见 EVIDENCE\A_recompute.tsv）。
- **基线（seed 20261119，2,000 次，S09 内随机取 8 行）**：
  - 严格档：总命中 2647/16000；**K=1.3235/试次，均值=0.1654375/行**（K=8×均值 ✅）。
  - loose 档：总命中 2879/16000；**K=1.4395/试次，均值=0.1799375/行**（K=8×均值 ✅）。
  - 两档并列；总体 A 率 strict=103/629=0.163752、loose=111/629=0.176471。

## 4. 四环复核要点（逐行证据见 EVIDENCE\）
- ②：全 1214 张 RTTI 表按真实 slot 枚举，8 行各恰 1 张命中；通道2 全文件 VA 出现点各恰 1 处（伪命中按表区间排除，见 DISAGREE D1）。
- ③b：006A5840/0063FB20/005BE6D0/00557730 为真循环/错误码（硬档）；006D0680 switch 状多路分派+真循环兜底；004E2690/0069DEB0 细则#1 级边际；00654320 ③a（不进）。
- ④：全 `.text` 100% 扫描 68,253 个 E8@边界；8 行全部站点 `byte=E8 ∧ site+5+rel32==entry ∧ 体外 ∧ 非自环`（EVIDENCE\direct_sites.txt）。无 livevt 行（8 候选皆 direct 命中）。

## 5. 交付
PROGRESS.md（本文件，≤60 行）｜UNKNOWNS.md（U1–U5）｜DISAGREE.md（D1–D5）｜coverage_delta.tsv（7 行）｜EVIDENCE\（rtti_all8.txt / analy3b_all8.txt / direct_sites.txt / A_recompute.tsv / A_recompute_log.txt / occurrences_xcheck_and_baseline.txt / baseline.json / dis_*.txt×8）｜work\（enum_vtables.py / dump_dis.py / analyze_features.py / verify_direct.py / occurrences_baseline.py / recompute_A.py）。
