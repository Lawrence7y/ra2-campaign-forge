# S09-KPROVED3 · PROGRESS

卡号 S09-KPROVED3。开工 2026-11-19T14:05+08:00；前 10 分钟已落骨架（含 8 候选与首候选 ② 证据）。目标 `ra2youli\gamemd.exe` 只读：SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（前缀 73201CC0/后缀 F67476），ImageBase 0x400000。
已读 R14_COMMON §1/§6/§7/§8.1（错源13/14/15/16/17/23）/§8.5/§8.6 六条；PENDING_DECISIONS D-40/D-41/D-42（含细则#1/#2/#3）；SURVEY_RING24\PROGRESS.md；S09_KPROVED2 审计教训 L1–L5。未建 venv、未 pip install、未改游戏文件/台账/coverage.tsv、未 git commit。
写域仅 `lead\next_re_20261117_r14\S09_KPROVED3\`；未创建/写入 `_ghidra\S09_KPROVED3\`（本卡用 capstone+pefile 只读复算，-noanalysis 约束未触发）。
## 1. 行源与 8 候选
行源 = S09 A 集合（②仅RTTI ∧ ④严格档）未并入部分。已排除 14 行：004AAE90 005BDF70 006A5310 004AB9B0 0063FEA0 006A7780 004ACE70 006ABD30 006A5840 006D0680 0063FB20 005BE6D0 004E2690 00557730；另排除已判不成立 00654320、0069DEB0。
选定并按 entry 升序处理 8 行：0048E5A0、0048E620、004A8960、004A9840、004A9DD0、004AA050、004AAD20、004AAD30。前两张同族卡教训逐条落实：L1 全表枚举、L2 类名一致、L3 报 ③b 基率、L4 细则#1 明示、L5 偏移写入口相对。
首候选 0048E5A0 的 ②：全 1214 张 RTTI 可解表恰 1 张命中 vt=`0x7E528C` slot=`31`（槽址 0x7E5308）；COL=`0x7FD308`→COL+0xC=TD=`0x81D0F0`→TD+8 内联 ASCII 逐字符 `.?AVControlClass@@`；vt[31]=entry，name 栏 ControlClass 一致。
## 2. 核心数字
- **8 行中四环齐全数 = 4**：004A9840、004A9DD0、004AA050、004AAD30。四行 ①②④ 均成立；③b 分别为硬档②、硬档④、硬档④、细则#1 级边际。其余 4 行 ③a，不进 delta，理由见 UNKNOWNS.md U1–U4。
- **S09 A 集合总行数 = 103（自数）**：全 exe 复算 ②RTTI 命中 601、④direct 体外站点命中 128、②∩④direct=102；A_strict=102+1 行 livevt `004F4240`（livevt 标志沿用 SURVEY classification，未入本卡候选/delta）。A_loose=111。
- **全 `.text` 扫描**：VirtualSize 4,060,045 B，capstone skipdata 1,392,592 条指令，68,253 个 E8@指令边界；8 候选全部 direct 站点 byte=E8、site+5+rel32==entry、体外（自写 CFG 函数区间包含）、非自环。EVIDENCE\DIRECT_SITES_8.tsv 共 38 条，全部 ok_external=1。
- **③b 基率（不是 ②∧④ 入选率）**：population=S09 629 行；seed=20261119；2000 次；每次同子系统内随机取 8 行（无放回）。strict：39/629=0.062003，总命中 1007/16000，K=0.5035/试次，均值=0.0629375/行。loose：40/629=0.063593，总命中 1035/16000，K=0.5175/试次，均值=0.0646875/行。K=8×均值是恒等式，不作校验；A 率 103/629=0.163752 是挑选谓词，不能冒充基线。
## 3. 四环明细
- ②：L1 全表枚举结果在 EVIDENCE\VTABLES_ALL8.tsv；0048E5A0/0048E620 归 ControlClass；004A8960/9840/9DD0/A050/AD20/AD30 被多张派生类表以同一 slot 持有，按 L1/⑯归最派生共同基类 DisplayClass（CLASS_ATTRIB.tsv 给完整类链），delta name 栏已同步，L2 合规。
- ③b：逐条全量反汇编（EVIDENCE\DISASM_*.txt，偏移均 +0xNN）与档位/证据见 EVIDENCE\CONTRACT_3B.tsv；004AAD30 已按 L4 标「细则#1级」并证明 7 个真支 helper 调用各异，非仅参数不同汇入同一 call。
- ④：direct 站点逐条 rel32/体外/非自环见 EVIDENCE\DIRECT_SITES_8.tsv；extent 由自写 CFG 计算，不依赖 function_atlas.tsv entry+size；cfg/linear 双通道 0 差异（EXTENTS_8.tsv）。
## 4. 自校验
- `work\s5_selfcheck.py` 对 delta 逐行核对 name=基类、全部持有表 vt/TD 名、direct 站点集合、delta 偏移必须在自家 DISASM 中出现、契约放行集合一致、L4 标签；最终 `EVIDENCE\SELFCHECK.txt` OVERALL PASS（30/30）。
- 命名冲突：开工 grep `lead\GOAL_THREE_TARGETS_20261018.md` 中 8 entry 均 0 命中；未写台账、未改 coverage.tsv。
## 5. 交付
PROGRESS.md（本文件）｜UNKNOWNS.md（U1–U8）｜DISAGREE.md（D1–D6）｜coverage_delta.tsv（4 行）｜EVIDENCE\（VTABLES_ALL.tsv、VTABLES_ALL8.tsv、CLASS_ATTRIB.tsv、A_RECOMPUTE.tsv、A_RECOMPUTE_SUMMARY.txt、E8_SWEEP_SUMMARY.txt、DIRECT_SITES_8.tsv、EXTENTS_8.tsv、CONTRACT_3B.tsv、BASELINE_3B.json/txt/features.tsv、DISASM_*.txt×8、SELFCHECK.txt）｜work\（k3lib.py、s1_collect.py、s2_attrib.py、s3_baseline.py、s5_selfcheck.py）。
