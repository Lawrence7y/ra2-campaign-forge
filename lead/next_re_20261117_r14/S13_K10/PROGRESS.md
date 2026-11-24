# S13-K10 PROGRESS · 最终（每 3–5 行增量落盘已满足）

状态: 完成。S13_K8 106 行 [静态推断] 中 **43 行**升 [已证]，目标 ≥16 达成。
硬约束: 名字侧净变化 0 损 0 增（占位名→非 sub_ 具名）；未碰 00773030；未用 slot-baseline；未 dual-count 同源。
exe SHA-256 73201CC0…F67476 现场复算一致（4,825,360 B，只读）。

## 逐行结论表（43 行升 [已证]；全表 + 语义见 coverage_delta.tsv）
| 合同名 | 行数 | entry |
|---|---|---|
| Clear | 15 | 0040B640, 0040B7F0, 0040F730, 0040FBB0, 0040FD00, 0046B5E0, 0046B750, 0048AD10, 0048AE60, 0054E890, 0054E9E0, 0062B070, 0062B1C0, 0065BEF0, 0065C040 |
| FindItemIndex | 3 | 0040F870, 0048AFA0, 0054EB20 |
| GetItem | 2 | 0040F630, 0040FC00 |
| GetItemIndex | 16 | 0040B670, 0040B860, 0040F610, 0040F7A0, 0040FBE0, 0040FD70, 0046B610, 0046B7C0, 0048AD40, 0048AED0, 0054E8C0, 0054EA50, 0062B0A0, 0062B230, 0065BF20, 0065C0B0 |
| operator== | 7 | 0040B700, 0040F640, 0040FC10, 0046B660, 0054E8F0, 0062B0D0, 0065BF50 |
| **合计** | **43** | 全部 ∈ K8 106 行；新地址 0 |

## 核心数字（审计复算）
① 升 [已证]: **43**（≥16 达标）
② 仍 [静态推断]: **63**；[未证]: **0**（本卡不新增 [未证]）
③ 检出力基线: 合同单判据 393/19,484 = 2.02%（seed=20261118）；合取判据（合同+RTTI+槽位一致+vptr安装）在 106 行内 0 误命中（44/44 合同/槽号一致，剔除 0040F5E0 幽灵被调后 43）
④ 与 K8 106 行重合: **43/43 = 100%**，新地址 **0**
⑤ 名字侧净变化: 0 损 0 增（原占位名非 sub_ → 新语义名非 sub_；00773030 未出现）

## 方法与复算
- 环③: `work/contract_full.py`（系统 python3.12 + capstone5.0.7 skipdata）逐入口解码 400B，按哨兵字节序列判合同；`EVIDENCE/analysis_recheck.json` 为 106 行逐行结果。
- 合同↔虚序核对: `YRpp/ArrayClasses.h:52-153`（slot1=operator==,3=Clear,4=FindItemIndex,5=GetItemIndex,6=GetItem）+ K9 `VERDICT_EVIDENCE.md` 已证 slot2=SetCapacity/4=FindItemIndex/6=GetItem 锚点。
- 环①②④: K8 `analysis_full.json` 的 RTTI 类属、vt-slot 安装点（C7 05 活 vptr 写全局）、r4=true；`work/exact_callers.py` 交叉验证 K9 的三处 exact 站点（0x43864A/0x4386AB/0x43942B）。
- 基线: `work/baseline_noncand.py`，同判据随机 .text 16B 对齐非候选起点。
- 字节级代表体全文 + 双通道说明: `EVIDENCE/CONTRACT_PROOFS.md`。
- 冲突/分歧: 018 扫描发现 K6 同名（其判据 FAIL，本卡独立复证）；0040F5E0 因 KICKOFF 幽灵被调剔除，见 `DISAGREE.md`。

## 剩余（见 UNKNOWNS.md）
- 63 行留 [静态推断]：多为具体类业务槽（Load/Save 族）缺配对键名；0040F5E0 因 ④误绑保留；Vec 版 slot2=SetCapacity 因 exact 绑定未覆盖保留。D-37 归属未改。
