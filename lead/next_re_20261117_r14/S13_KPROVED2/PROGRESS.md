# S13-KPROVED2 PROGRESS

- 卡号: S13-KPROVED2；目标 `ra2youli\gamemd.exe` 只读，SHA-256 `73201CC0…FCF67476` 现场复算一致。
- 写域: 仅本目录与 `_ghidra\S13_KPROVED2\`；未改 coverage.tsv / 台账 / STATUS_BOARD / _audit / 游戏文件；未 git commit。
- 开工 10 分钟内落本骨架；python 3.12.10 + capstone 5.0.7 + pefile 2024.8.26；未建 venv、未 pip install。

## 必读已核
R14_COMMON §1/§6/§7/§8.1/§8.4/§8.5/§8.6/§8.7；D-37/39/40/41/42 原文；S13_K12 与 S13_K9 的 `_audit/VERDICT.md`。

## 核心数字
| 项 | 值 |
|---|---|
| 候选行数 | **46**（126 静态池 − K8 18 行 − 容器 slot1–6 62 行；3 M26 + 11 K9 本就非静态池）|
| 四环齐全数 | **0** |
| delta 行数 | **0**（coverage_delta.tsv 仅表头，= 自报行数）|
| S13 proved 240 口径 | **89/240 = 37.0833%** |
| S13 proved 148 口径 | **75/148 = 50.6757%**（剔 92 容器模板行及其 14 行已证）|
| ③b 基率 (126) | strict K=18/p=0.142857/E[8]=1.142857/MC=1.105；loose K=43/p=0.341270/E[8]=2.730159/MC=2.692 |
| ③b 基率 (46) | strict K=8/p=0.173913/E[8]=1.391304/MC=1.433；loose K=15/p=0.326087/E[8]=2.608696/MC=2.619 |
（seed 20261119 / 2000 次 / 抽 8；K=N·p、E[8]=8p 为恒等式非校验，§8.7 判据 3）

## 为何 0 行（决定性环 = ④）
- ② 46/46 PASS（RTTI 可解虚表槽）；③b 部分行可过，但任一环缺即不升。
- ④ 46/46 FAIL，两条独立通道 + 等价形式：
  - 通道 A capstone 全 `.text` 线性反汇编 1,392,592 指令 → 命中候选的 E8 direct 目标 **0**（全镜像 distinct E8 目标 6,728，扫描有效）。
  - 通道 B 纯字节扫 `E8 rel32` 81,715 处 + 1,392,592 边界集 → 命中候选 **0**；A==B。不依赖 atlas entry+size。
  - 活 vtable 派发全条款：46 行 `has4_strict=0`/`has4_loose=0`；VA 均仅落一张虚表槽（与 ② 同源，D-39），无静态 global 接收者 exact 派发。
  - E9 尾跳仅中 0046AFD0/0046AFF0，站点为 `sub [esp+4],4; jmp` thunk（候选→候选别名），非 E8 direct / 非虚表派发，D-40 ④ 不成立；EB 命中 0。
- 与 SURVEY_RING24「S13 A=0/126 严格档，④ dir/lv=0/0」及 S13_K12 审计（14 行为 atexit 析构器基类虚表、非活 vptr）一致。

## 交付物
`coverage_delta.tsv`（0 数据行）｜`UNKNOWNS.md`（U1–U4）｜`DISAGREE.md`（D1–D5）｜
`EVIDENCE/`：`core_numbers.json` / `baselines.json` / `candidate_pool.tsv`｜
`work/`：`s13lib.py` / `w1..w7.py` / `pool.json` / `ring4_scan.json` / `ring4_equiv.json` / `dword_va_scan.json`。

## 纪律自检
1 寄存器/thiscall：本卡未作需此判断的升格；2 分支穷举：E9 thunk 逐条打完；3 门控：未下覆盖结论；
4 穷举双通道且通道 B 不依赖 atlas；5 站点归属用函数区间/边界；6 不存在 ④ 查 direct+livevt+E9/EB 等价形式；
7 写值逐字核对（SHA/数字与 EVIDENCE 同源）；8 未用最近 E8/最大函数/无调用者启发式；10 atexit 表不算活 vptr；
11 未改 coverage.tsv；12 未升格故无 ② 栏/偏移契约冲突；13 报 strict+loose 双档并述操作化；14 容器族按 §8.4 + 错源⑯ 归基类；
15 delta 行数 0 = 自报；16 无 delta 行故无 one_line_semantics；17 未判"各闸动作不同"。
