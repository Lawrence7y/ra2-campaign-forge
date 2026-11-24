# SURVEY-D39 PROGRESS（只读测量，不改 grade / 不交 delta）

## 0. 前提与自证
- 目标只读：`ra2youli\gamemd.exe` SHA-256 现场复算 `73201CC0…F67476` 一致。
- ⑨ 盘上重算通过：S10 n/named(S)/proved/threshold/gap = 526/513/117/263/146；S11 = 368/358/29/184/155；S20 = 410/399/40/205/165；S13 = 240/216/86/120/34。全项目 S01–S21 `[静态推断]`=4,416、proved 缺口=2,736（与卡面 Lead 值一致；S22 按 COMMON §1 不作覆盖/百分比结论）。
- capstone 5.0.7 + `skipdata=True`：.text 解出 1,394,186 条、指令边界 direct call 68,253 处；对齐 dword 命中 3,965，RTTI 可解表命中 3,676。
- ⑲ 自检：已知阳性 `0x4386AB call dword ptr [edx+0x10]` 的 `mem.index=0`；脚本不按 `op.index is None` 筛 call。
- ⑭：C1 的 direct call 目标来自 68,253 个指令边界 call 的 rel32 目标表；exact dispatch 仅计入 `mov reg,[global] + mov ecx,global + call [reg+slot]` 且 global 有安装点、槽值等于 entry。未使用 slot-baseline。

## 1. 四子系统 × 四类计数矩阵（仅 grade=`[静态推断]` 且 coverage∩atlas；共 1,215 行）
| 子系统 | C1 真四环 | C2 D-39 型 | C3 缺②类属 | C4 缺③语义 | 小计 |
|---|---:|---:|---:|---:|---:|
| S10 | 58 | 35 | 82 | 221 | 396 |
| S11 | 8 | 3 | 0 | 320 | 331 |
| S20 | 37 | 25 | 0 | 297 | 359 |
| S13 | 17 | 36 | 0 | 76 | 129 |
| 合计 | 120 | 99 | 82 | 914 | 1,215 |

## 2. 两口径下 proved 与达标（门槛=ceil(n/2)）
| 子系统 | 现 proved | 门槛 | (B)严格四环 = 现+C1 | 差 | 判定 | (A)/(C)三环 = 现+C1+C2 | 差 | 判定 |
|---|---:|---:|---:|---:|---|---:|---:|---|
| S10 | 117 | 263 | 175 | 88 | 未达标 | 210 | 53 | 未达标 |
| S11 | 29 | 184 | 37 | 147 | 未达标 | 40 | 144 | 未达标 |
| S20 | 40 | 205 | 77 | 128 | 未达标 | 102 | 103 | 未达标 |
| S13 | 86 | 120 | 103 | 17 | 未达标 | 139 | 0 | 达标 |

## 3. 全项目汇总
- 严格四环 (B)：四子系统可升 **120** 行；达标 **0/4**。
- 三环可证 (A)/(C)：四子系统可升 **219** 行（C1 120 + C2 99）；达标 **1/4**（仅 S13）。
- C2 仅表示「按 D-39 放宽后可升」，**不表示应该升格**；裁决权在用户。

## 4. 判别力基线（⑳，唯一数）
- C2 判据「有活 vptr 安装且 direct call=0」在随机 100 个 atlas 入口上的命中率：**15/100 = 15.00%**（seed 20261118）。说明该判据单独不够特异，必须配合 RTTI 链与体内合同。

## 5. 抽样佐证
- C1 抽样 10 行：`EVIDENCE/C1_samples.tsv`（direct call 站点 / exact 派发站点 + global + slot）。
- C2 抽样 12 行：`EVIDENCE/C2_samples.tsv`，全部避开 K8/K10 的 61 个 S13 地址；可用非 61 池共 70 行。
- 逐行分类：`EVIDENCE/classification.tsv`；全部 ring4 站点：`EVIDENCE/ring4_sites.tsv`。
- 可复跑脚本：`work/analyze.py`；结果：`work/result.json`；未知/边界：`UNKNOWNS.md`。

## 6. 方法边界
- C1 按卡面环④判据计数；C2 要求 RTTI 链可解、有活安装/imm 见证、direct call=0 且无 exact 派发；体内合同只认强字节形态（vector 族 slot1–6 与 scalar deleting dtor）。
- 未改 coverage/grade/subsystem；未生成 coverage_delta.tsv。
