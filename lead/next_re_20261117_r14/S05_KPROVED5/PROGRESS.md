# S05-KPROVED5 · PROGRESS

卡号 S05-KPROVED5（agent-44）。目标 `ra2youli\gamemd.exe` 只读，SHA-256 `73201CC0…F67476` 现场复核一致（4,825,360 B / ImageBase 0x400000）。
写域仅 `lead\next_re_20261117_r14\S05_KPROVED5\`；未写 COVERAGE/台账/R14_COMMON/STATUS_BOARD/ra2youli/其它卡目录/_audit；未建 venv、未 pip install、未改 coverage.tsv、未 git commit。

## 开工必读（已读）
R14_COMMON §1（作废索引）/§6（21 条纪律）/§7（环境）/§8.1（16+ 错源，含 ⑯）/§8.5（3 条口径）/§8.6（D-40/41/42 六条硬判据）/§8.7（9 条新判据）；PENDING_DECISIONS D-40/D-41/D-42 原文；SURVEY_RING24/PROGRESS.md。

## 行源与排除集
- S05 A 集合 = **41**（SURVEY_RING24 主口径 ②仅RTTI × ④严格档；从 classification.tsv 按 has2_rtti=1 ∧ has4_strict=1 复算恰 41）。
- 排除集合成（先读 delta）：KPROVED2(8) ∪ KPROVED3(8) ∪ KPROVED4(3) = **19 唯一行**；SEMFIX_SLOTS3 的 7 行是 KPROVED3 去 00704350 的子集，无新增。剩 **22** 行。
- 本卡按代表性取 8 行处理：00709A40 / 005F9720 / 006F3F40 / 006F6CA0 / 006F4A70 / 00711F00 / 0070E2B0 / 0040BA50。

## 逐行四环结果（详见 EVIDENCE/ROW_*.txt）
| entry | ②持有表/⑯ | ③档 | ④站点 | delta |
|---|---|---|---|---|
| 00709A40 | 1 表 TechnoClass slot289 | ③a 4jcc/2目标(同型闸,M4) | 004D82D9 | 否 |
| 005F9720 | 1 表 ObjectTypeClass slot5 | ③a 析构清零(有界清零循环) | 10 站点 | 否 |
| 006F3F40 | 2 表 slot9→基类级 TechnoClass | ③a 顺序惰性构造 | 5 站点 | 否 |
| 006F6CA0 | 1 表 TechnoClass slot54 | ③a 线性初始化 | 2 站点 | 否 |
| 006F4A70 | 1 表 TechnoClass slot73 | ③a 2闸布尔谓词 | 3 站点 | 否 |
| 00711F00 | 4 表 slot33→基类级 TechnoTypeClass | ③a 浮点换算单闸 | 0045EDDB | 否 |
| 0070E2B0 | 1 表 TechnoClass slot85 | ③a setter | 2 站点 | 否 |
| 0040BA50 | 1 表 VectorClass<TechnoClass*> slot3 | ③a 容器 Clear | 0063B01A | 否 |

## 核心数字
- **8 行中四环齐全数 = 0**（环①②④全成立，③全为机械可述 ③a，无 ③b）。
- **S05 A 集合总行数 = 41**。
- **③b 基率**（strict/loose，seed 20261119，2000 次，sample_n=8，池=S05 `[静态推断]` ∩ classification extent = 387 行）：
  - strict **0.235142 (91/387)**，E[8]=1.881137，MC 均值 **1.836500**；
  - loose **0.379845 (147/387)**，E[8]=3.038760，MC 均值 **2.997500**。
  - 操作化：strict=跳表①∨错误码②∨内存形状③∨完整I/O循环④；loose=strict∨细则#1 互斥闸链(≥3 distinct jcc 目标)。K=N·p、E[8]=8p 为恒等式非校验（M3）。

## 纪律自检
- ① 8/8 入口 16B 对齐 + 前驱 ret/nop；② 全镜像 4 对齐原始命中 + RTTI 链 COL+0xC→TD+8 fail-closed，枚举 1214 表（R14_COMMON 权威值一致）；多表同槽（006F3F40/00711F00）归基类级（错源⑯/M1），name 栏按基类级写（M2）。
- ③ 偏移一律入口相对 +0xNN，与自家 EVIDENCE/work/disasm 逐字同一数（M5）；④ 全 .text 1,392,592 指令 / 68,253 E8@边界独立扫，站点体外非自环（纪律 7/站点用区间包含）。
- ③b 判定双通道穷举；无"某闸什么都不做"的截断推断（把入口到 ret 全打完）；00709A40 的 jcc distinct target=2 已实测（双通道：capstone + 原始字节）。
- delta 行数 = 自报行数 = **0**（M6/M7）；③b 语义四要素模板已备（见 D3），四环缺一即不进 delta。

## 交付
PROGRESS.md / UNKNOWNS.md(U1–U8) / DISAGREE.md(D1–D4) / coverage_delta.tsv(0 数据行，附说明) / EVIDENCE(ROW_*.txt ×8 + ROW_SUMMARY.json + baselines.json) / work(w0–w5 + ax_lib + disasm/ + 各 JSON)。
