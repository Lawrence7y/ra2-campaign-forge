# S03-C5 PROGRESS — S03 A 集合未并入部分：8 行四环取证

# 状态：完成（2026-11-19T13:4x+08:00）。目标 ra2youli\gamemd.exe 只读（SHA-256 73201CC0…F67476 现场复算全值吻合，ImageBase 0x400000）；仅写 S03_C5\ 与 _ghidra\S03_C5\；未建 venv / 未 pip install / 未 import 他卡 work / 未改游戏文件 / 未写台账 / 未改 coverage.tsv / 未 git commit。
# 必读已核：R14_COMMON §1/§6/§7/§8.1/§8.5/§8.6 六条；PENDING D-40/D-42（含细则1/2/3）；SURVEY_RING24\PROGRESS.md。
# S03 A 集合自数 = 31（classification.tsv subsystem=S03 ∧ has4_strict=1），与 SURVEY_RING24 记 S03 A=31 一致；排除上卡 C4 已并 7 entry（0065CAC0 004324B0 00552490 006C9890 00631CC0 0065D150 00431E80）后余 24，本卡只做 8 行不扩。
# 本卡 8 候选：0055C7C0 0065CF00 00431F10 0065CB50 00473B10 00473AE0 0047AF10 0065CCE0（首行 0055C7C0 ② 骨架证据见 work/verify_rtti.py + EVIDENCE/rtti_verify.json）。
# 工具：python 3.12.10 + capstone 5.0.7(skipdata=True,detail=True) + pefile 2024.8.26；.text 全扫 1,392,592 指令 / 68,253 E8@边界 / 81,715 raw E8；extent 用自写 CFG（来自 classification ext_lo/ext_hi，非 atlas entry+size）。

## 结论表（①②③④ 四环 + ③b 档位；现场为入口相对偏移 +0xNN，见 EVIDENCE/THREE_B_DETERMINATION.md）
| entry | name(盘上不动) | ② RTTI(vt/slot/名) | ③b 档位 | ④ direct站点 | 四环 | 处置 |
|---|---|---|---|---|---|---|
| 0055C7C0 | LZOStraw::slot2 | 7ED394/2/.?AVLZOStraw@@ | ④ 完整I/O解压循环(头==4+短读) | 12 | ✅ | delta |
| 0065CF00 | RawFileClass::slot10 | 7F0904/10/.?AVRawFileClass@@ | ①+② origin三路+(-1)错误码 | 14 | ✅ | delta |
| 00431F10 | CDFileClass::vslot5 | 7E1668/5/.?AVCDFileClass@@ | ③a 8指令getter | 29 | ❌③ | UNKNOWNS U1 |
| 0065CB50 | RawFileClass::slot7 | 7F0904/7/.?AVRawFileClass@@ | ①+② open三路模式开关+句柄约定 | 9 | ✅ | delta |
| 00473B10 | CCFileClass::slot9 | 7E16B0/9/.?AVCCFileClass@@ | ①【细则#1级·边际】5道互斥闸 | 44 | ✅ | delta(敏感) |
| 00473AE0 | CCFileClass::slot12 | 7E16B0/12/.?AVCCFileClass@@ | ③a 薄壳 | 11 | ❌③ | UNKNOWNS U2 |
| 0047AF10 | CDFileClass::slot8 | 7E1668/8/.?AVCDFileClass@@ | ③a 二路委托(OR汇合) | 21 | ❌③ | UNKNOWNS U3 |
| 0065CCE0 | RawFileClass::slot9 | 7F0904/9/.?AVRawFileClass@@ | ④ 完整I/O读循环(夹紧+abort) | 15 | ✅ | delta |

## 核心数字
1. **四环齐全数 = 5**（0055C7C0 / 0065CF00 / 0065CB50 / 00473B10 / 0065CCE0；coverage_delta.tsv 仅此 5 行）。③ 环不成立 3（U1/U2/U3）。
2. **S03 A 集合行数 = 31**（自数，与 SURVEY_RING24 一致）；本卡取 8，余 16 未动。
3. **② 成立数 = 8/8**（RTTI 链全读通、vt[slot]==entry；fail-closed 未触发）；**④ 成立数 = 8/8**（direct 站点，双通道逐行一致）；**③b 成立 = 5/8**。
4. **④ direct 站点合计 = 12+14+29+9+44+11+21+15 = 155**（5 行 delta 站点 = 12+14+9+44+15 = 94）。
5. **两档随机基线**（池 N=102=S03∧[静态推断]∧有extent；seed 20261119，2,000 次无放回取 8 行；detector 见 work/baselines.py）：
   - loose（细则#1 记 ③b①）：池命中 39、N=102、均值(命中率) p=39/102=0.382353、**K=E[8]=8×p=3.058824**、MC 实测均值 3.0625。
   - strict（①只认跳表/循环/错误码）：池命中 22、N=102、均值 p=22/102=0.215686、**K=E[8]=8×p=1.725490**、MC 实测均值 1.73。
   - **恒等式 K = 行数 × 均值**（行数=8=本卡行数，均值=p=命中率）：3.058824=8×0.382353 ✅、1.725490=8×0.215686 ✅；等价地池命中 K_pool=N×p=102×0.382353=39 ✅ / 102×0.215686=22 ✅。两档算术自洽。
   - 本卡 5 行 > 两档 K（3.06/1.73），非随机可解释。

## P1–P4 敏感点落实
- **P1**：00473B10 ③b① 明标「细则#1 级·边际」并给敏感性（严格口径下 5→4）；详见 DISAGREE D2。上卡两边际行 006C9890/00631CC0 作为同型先例引用。
- **P2**：两档 K/均值并列，K=N×p、E[8]=8×p 算术自洽（见核心数字5、EVIDENCE/baselines.json）。
- **P3**：表长约束（槽位 < 连续 .text 指针表长）显式挡住「下一张表 COL 当自表槽」伪 (vt,slot)：无约束 18~29 个 → 加约束后 1（00431F10 双链 2），见 EVIDENCE/p3_table_constraint.json；与上卡 616/566→9/8 同机制（本卡被测 entry 多为单类，故基数小）。
- **P4**：全文偏移均 entry 相对 +0xNN，无绝对/相对混用（③b 现场见 THREE_B_DETERMINATION.md）。

## 复算方法（命令）
- ② `python work/verify_rtti.py` → EVIDENCE/rtti_verify.json；④ `python work/scan_sites_card8.py` → EVIDENCE/direct_sites_card8.json（双通道一致）。
- ③b `python work/dump_dis2.py` → EVIDENCE/dis2/*.txt（正确 CFG extent，入口相对偏移）→ 逐条判读见 THREE_B_DETERMINATION.md。
- 基线 `python work/baselines.py` → EVIDENCE/baselines.json；P3 `python work/p3_table_constraint.py` → EVIDENCE/p3_table_constraint.json；liveness `python work/liveness.py`。

## 交付
PROGRESS.md（本文件，≤60 行）/ UNKNOWNS.md / DISAGREE.md / coverage_delta.tsv（5 行）/ EVIDENCE\ / work\。
