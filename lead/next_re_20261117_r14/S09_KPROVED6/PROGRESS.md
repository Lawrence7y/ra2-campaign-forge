# S09-KPROVED6 PROGRESS

- Card S09-KPROVED6 (RA2 reverse execution). Root D:\Project\ra2-campaign-forge.
- Target ra2youli\gamemd.exe READ-ONLY (SHA-256 73201CC0…F67476, 复核 4,825,360B/ImageBase 0x400000).
- Write scope only S09_KPROVED6\ and _ghidra\S09_KPROVED6\ (-noanalysis); nothing else touched. No venv/pip/git commit.
- Task: 8 rows from S09 A set (A=103) remaining gap; 4 rings (② tables+⑯ / ③b / ④ site) each proven.

## 必读已核
- R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条/§8.7 九条判据；PENDING D-40/41/42（含细则#1/2/3）；SURVEY_RING24\PROGRESS.md；prior deltas S09_KPROVED/2/3/4/5 + SEMFIX_SLOTS3。

## 行源与排除集
- 源：`SURVEY_RING24\EVIDENCE\classification.tsv` 的 S09 ∧ has2_rtti=1 ∧ has4_strict=1 = **103** 行（与 SURVEY_RING24 PROGRESS §2 S09 A=103 逐字吻合）。
- 排除：KPROVED(8)+K2(7)+K3(4)+K4(8)+K5(8)=35 行；SEMFIX_SLOTS3 在处理的 8 行 = K5 同 8 行（其 PROGRESS §5 明写 S09_KPROVED5 全部 8 行）；黑名单 00654320(③a)、0069DEB0(细则#1 亦不达) 中后者已在 K2。distinct 排除 36；余 67 候选。

## 8 行与四环（全部成立）
| entry | ② 持有表数→name(⑯基类) | ③b 档 | ④ |
|---|---|---|---|
| 004F4240 | 9→GScreenClass::slot0 | ② HRESULT | livevt g=87F7E8 vt=7E1964 构造器装表 |
| 004E25A0 | 2→GaugeClass::slot35 | ② bool 返回 | E8@6B1E69 |
| 0056BBE0 | 8→MapClass::slot27 | ④+② 有界循环+哨兵 | E8@55B65A |
| 00656AC0 | 2→RadarClass::slot31 | ②+④ 错误码+双循环 | E8@6AC5E5 |
| 006A5030 | 3→SidebarClass::slot7 | ④ 4次有界循环 | E8@5BDF53 |
| 0069DE00 | 1→ShapeButtonClass::slot34 | ①【细则#1级】 | E8@65307B 等 12 |
| 005BDC80 | 1→vt7E1964 MouseClass::slot19 | ②+① 哨兵+魔数闸 | E8@4AC4DA 等 11 |
| 005576A0 | 1→ListClass::slot34 | ①【细则#1级】 | E8@48832E 等 3 |

- 四环齐全数 = **8**（6 strict / 2 细则#1级）；delta 行数 = **8**（=自报，M6/判据7）。
- ② 类名全部与 name 栏一致（M2）；全部表枚举见各 EVIDENCE/RINGS_*.txt；2 表以上同 slot 归基类（错源⑯/M1）。
- ③b 整体合同语义按修正契约写入第 4 列：保留类名+槽位+子系统、替换占位模板、四要素、无「未证/未定/弱信号/线索」；66 个入口相对锚经 `work/anchor_check.py` 与 EVIDENCE 逐字核对、0 处不符（M5）。
- ④ 7 行 direct call E8@指令边界+site+5+rel32==entry+体外+非自环；1 行(004F4240) livevt 构造器装表（非 atexit，D6）。

## 核心数字
- S09 A 集合总行数 = **103**；本卡取 8；四环齐全 = **8**（严格四硬档口径 = 6，见 UNKNOWNS U1）。
- ③b 基率（seed 20261119, 2000 次, 池 N=657 当前盘上 S09 [静态推断]）：strict K=113/p=0.171994/E[8]=1.375951/MC=1.358500；loose K=152/p=0.231355/E[8]=1.850837/MC=1.839500。定义见 EVIDENCE/baseline_3b.json、UNKNOWNS U2。`K=N·p` 为恒等式非校验（M3）。

## 排除/已判不成立
- 00654320（③a）、0069DEB0（细则#1 两档皆不达）未选；理由在 DISAGREE D3 与 prior 审计。

## 交付
- PROGRESS.md（本文件，<60 行）| UNKNOWNS.md | DISAGREE.md | coverage_delta.tsv（8 行 6 列）| EVIDENCE/（RINGS_*.txt 8 + baseline_3b.json + ANCHORS.tsv）| work/（脚本+JSON）。
- 未改 coverage.tsv / 台账 / R14_COMMON.md / STATUS_BOARD.md / ra2youli\ / _audit\ / 其它卡目录。
