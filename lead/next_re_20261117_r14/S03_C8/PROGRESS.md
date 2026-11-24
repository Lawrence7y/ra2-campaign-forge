# S03-C8 PROGRESS

- Card: S03-C8 | Operator: RA2 逆向执行员 | Started: 2026-11-19 (Asia/Shanghai)
- Target: ra2youli\gamemd.exe (READ-ONLY; SHA-256 73201CC0…F67476) — 现场复核一致
- Write domain: lead\next_re_20261117_r14\S03_C8\ and _ghidra\S03_C8\ (-noanalysis) ONLY
- Task: 只做 8 行（上限），不得扩；行源 = S03 A 集合(A=31) 尚未并入部分。
- Deliverables: PROGRESS.md(<=60行), UNKNOWNS.md, DISAGREE.md, coverage_delta.tsv, EVIDENCE\, work\.

## 必读已核（开工前）
- R14_COMMON §1 作废索引 / §6 纪律21条 / §7 环境 / §8.1 错源(含⑯共享vt) / §8.5 三口径 / §8.6 六条(D-40/41/42) / §8.7 九条(M1-M8).
- PENDING_DECISIONS D-40/41/42 原文(含细则1/2/3); SURVEY_RING24/PROGRESS.md.
- 环境: py3.12.10 + capstone 5.0.7(skipdata) + pefile 2024.8.26; 未建 venv / 未 pip install.

## A 集合与排除集（核心数字）
- S03 A 集合总行数 = **31**（A_strict ∩ classification subsystem=S03，与 MATRIX S03 A=31 一致）。
- 排除唯一 26 = C4(7) ∪ C5(5) ∪ C6(7) ∪ C7(3) [=22 互不相交] ∪ SEMFIX_SLOTS2 S03(4,全落C6内无新增) ∪ 已判不成立(00431F10/00473AE0/0047AF10/00432050/0065D240，00432050已在C6，另4新增).
- **A 剩余 = 31−26 = 5 行**（00473C00/00473CE0/00473FC0/0047AAB0/00631D30）。「只做 8 行」为上限，池实际 5 行，不扩面凑数。

## 方法（全部自写脚本，未 import 它卡 work/）
- work/common.py: 自写 PE/hash/disasm 助手（SHA 断言、va2off、md/md_detail）。
- work/disasm5.py: 5 行入口相对 +0xNN 反汇编 → EVIDENCE/dis_*.txt（与 C7 逐字一致）。
- work/scan_rtti.py: 全 .rdata 4 对齐枚举 1,205 张 RTTI 表，② 全持有表 → rtti_holders.json.
- work/scan_sites.py: 全 .text skipdata 扫 1,394,186 指令，④ direct 站点 → direct_sites.json.
- work/detector.py: D-42 strict/loose ③b 检测器 + 基率(seed 20261119/2000) → baselines.json.

## 逐行结果（详见 EVIDENCE/THREE_B_DETERMINATION.md）
- 00473C00 CCFileClass::slot11: ②1表(⑯=CCFileClass) ④26站点 ③a(2闸,getter) ⇒ 不进.
- 00473CE0 CCFileClass::slot13: ②1表 ④42站点 ③a(死分支+单次构造/清零/委托) ⇒ 不进.
- 00473FC0 CCFileClass::slot2: ②1表 ④14站点 ③a(清零+单调用) ⇒ 不进.
- 0047AAB0 CDFileClass::slot7: ②1表(⑯=CDFileClass) ④2站点 ③a(纯转发桩) ⇒ 不进.
- 00631D30 FilePipe::slot1: ②5表同slot(⑯=Pipe基类) ④6站点 ③a(纯转发桩+NULL哨兵) ⇒ 不进.

## 交付核心数字
- 作业面 5 行；② 成立 5/5；④ 成立 5/5（direct 合计 90 站点）；③b 成立 **0/5**（全 ③a）。
- **四环齐全 = 0/5**；**coverage_delta.tsv 数据行 = 0 行**（=自报 0 行，M6/M7）。
- ③b 基率（池=当前盘上 S03 [静态推断] ∩ extent = 88 行，seed 20261119，2000 次取8不放回）：strict K=17/88=19.32% E[8]=1.5455 MC=1.5285；loose K=27/88=30.68% E[8]=2.4545 MC=2.4510。K=N·p 恒等式不作校验(M3)。
- 池/检测器与 C7(N=91/18/32) 差异已在 EVIDENCE/UNKNOWNS/DISAGREE 披露，两口径并列不声称同值。

## 状态
- [DONE] 0 行交付，5 行全列 UNKNOWNS（每行缺 ③b 可证伪判据）。
- 未做真机 / 未改 grade / 未改 coverage.tsv / 未写禁写目录（含 _audit\）。
