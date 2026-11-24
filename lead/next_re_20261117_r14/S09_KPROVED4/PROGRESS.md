# S09-KPROVED4 · PROGRESS

> 卡号 S09-KPROVED4｜目标 `ra2youli\gamemd.exe` 只读，SHA-256 全值 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（前缀 73201CC0/后缀 F67476，本卡 Get-FileHash 现场复核）｜ImageBase 0x400000。
> 开工 2026-11-19T14:36:05+08:00（Asia/Shanghai）；前 10 分钟硬规矩已满足：先落骨架 ≥5 行，再取数。
> 写域：仅 `S09_KPROVED4\` 与 `_ghidra\S09_KPROVED4\`（本卡用自建 capstone+pefile 只读复算，未生成 Ghidra 数据库、-noanalysis 约束未触发）。未建 venv、未 pip install、未改游戏文件/台账/coverage.tsv、未 git commit。

## 0. 开工前必读（已完成）
R14_COMMON.md §1/§6/§7/§8.1/§8.5/§8.6 六条；PENDING_DECISIONS D-40/D-41/D-42（含 D-42 操作化细则#1/#2/#3）；SURVEY_RING24\PROGRESS.md。逐条落实审计教训 M1–M7 与纪律 1–15。

## 1. 行源与 8 行选定
- 行源 = S09 A 集合（②仅RTTI ∧ ④严格档，SURVEY 主口径）尚未并入部分。**S09 A 集合总行数 = 103**（本卡复算 ②RTTI 命中 601、④direct 体外 128、②∩④direct=102 + livevt 1 行 `004F4240` = 103；与 SURVEY MATRIX S09 A=103 同值）。
- 已并入 18 行（K1 8 + K2 6 + K3 4）全排除；已判不成立 `00654320`(③a)、`0069DEB0` 排除；K3 审计已否的 4 行 `0048E5A0/0048E620/004A8960/004AAD20`（③a）亦不选。剩余 83 行。
- 按 entry 升序选定 8 行：`004E2830` `00557830` `00565B00` `00577920` `006568A0` `006A7D70` `00723EC0` `006D02B0`。

## 2. 核心数字
- **8 行中四环齐全数 = 8**（①②④ 全成立 + ③b 硬档）；**delta 行数 = 8**，两者一致（M6）。
- **③b 基率**（不是 ②∧④ 入选率）：population=S09 629 行；seed 20261119；2000 次；每次同子系统内无放回随机取 8 行。strict：123/629=0.195548，总命中 3188/16000，K=1.594/试次，均值=0.19925/行。loose：144/629=0.228935，总命中 3734/16000，K=1.867/试次，均值=0.233375/行。**K=8×均值是恒等式，不作校验**；A 率 103/629 是挑选谓词，非基线（M3）。
- RTTI 枚举 1214 表/14044 槽，与 §8.1 基线逐位吻合；全 .text skipdata 扫 1,392,592 指令/68,253 E8@边界；capstone `op.index` 陷阱自检通过（`0x4386AB` index=0≠None，错源⑲）。
- ④：13 站点全 E8@边界 + site+5+rel32==entry + 体外（自写 CFG 函数区间包含，非 entry_at_or_before）+ 非自环；8 行 CFG extent 与 atlas size 精确一致 8/8（独立双通道）。

## 3. 四环明细（全量见 EVIDENCE）
- ② 全持有表 `VTABLES_ALL8.tsv`：004E2830→GaugeClass(2表)、00557830→ListClass(2表)、00565B00→MapClass(8表)、00577920→MapClass(8表)、006568A0→RadarClass(2表)、006A7D70→SidebarClass(1表)、00723EC0→ToggleClass(3表)、006D02B0→TabClass(3表)。①②③ 多表同槽按 M1/错源⑯归最派生共同基类（CHD BaseClassArray 传递闭包）；name 栏同类（M2）。
- ③b `CONTRACT_3B.tsv`：③b④ 有界循环读写 5 行（体内显式堆/成员写，非栈累加，M7）、③b② 错误码/哨兵、`③b①【细则#1级】` 多闸 2 行（00557830/00723EC0：各闸写字段与 helper 各异，非仅参数不同汇同一 call，M4 已证）。全部入口相对 +0xNN，逐条与自家 DISASM 同数（M5）。
- ④ `DIRECT_SITES_8.tsv`：13 站点。② 第二通道：8 entry 的 4B VA 出现数 = 持有表数，全在 .rdata（与 RTTI 同源自洽）。

## 4. 自校验与边界
- `work\s7_selfcheck.py` 对 delta 逐行核 M1/M2/M5/M6/M14/M15 + ②/④/③b 一致：`EVIDENCE\SELFCHECK.txt` OVERALL PASS（69/69）。
- 冲突：开工 grep 主台账：`006A7D70` 命中 1 处，为 Ghidra 占位名 `FUN_006a7d70`（非语义名，不构成命名冲突，见 DISAGREE D1）；其余 7 entry 0 命中。③b 基率检测器口径见 UNKNOWNS U1。

## 5. 交付
PROGRESS.md｜UNKNOWNS.md｜DISAGREE.md｜coverage_delta.tsv（8 行）｜EVIDENCE\（VTABLES_ALL.tsv、VTABLES_ALL8.tsv、CLASS_ATTRIB.tsv、CLASS_ATTRIB8.tsv、CONTRACT_3B.tsv、DIRECT_SITES_8.tsv、BASELINE_3B.json/txt/BASELINE_3B_FEATURES.tsv、DISASM_*.txt×8、SELFCHECK.txt）｜work\（s09lib.py + s1–s7 脚本 + JSON）。
