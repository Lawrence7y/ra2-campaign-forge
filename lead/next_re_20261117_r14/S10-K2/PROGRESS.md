# S10-K2 · PROGRESS（结论表 / 三级分级 / 证据 / 核心数字）

> 卡号 S10-K2｜Mission 系统｜2026-11-17。只读目标，未改游戏文件，未写台账，未 git commit。无 Ghidra 副本（capstone+pefile 双通道足够）。全部脚本 `work/*.py` 可复跑；原始证据 `EVIDENCE/` 不截断。

## 结论表

| # | 问题 | 结论 | 级 | 证据 |
|---|---|---|---|---|
| 1 | MissionClass 主 vtable | `0x7EDCC0`，**157 槽**（`.rdata` 定界，COL `0x805D28`→TD `0x817B18`）；Mission 处理槽 = v[129..156]（28 槽，disp `0x204..0x270`） | [已证] | `EVIDENCE/t2_rtti_vtables.txt`,`t2_mission_slots.txt` |
| 2 | 派发映射（mission→槽） | 表 `0x5B34E8` 32 项→stub `call [vptr+disp]`；逐项解出 32 mission→v129..v156，disp/4=槽 | [已证] | `EVIDENCE/t2_dispatch.txt` |
| 3 | 全桩槽/Mission | **6 全桩槽**（v129/130/131/141/142/154）⇒ **8 全桩 Mission**（Sleep/QMove/Return/Stop/Ambush/Harmless/Wait/Attack Move） | [已证] | `EVIDENCE/t2_final_slots.txt` |
| 4 | 有实现槽/Mission | **22/28 槽有实现**，**24/32 Mission 有实现**；43 是非桩入口地址数（不是"有实现 Mission 数"） | [已证] | `EVIDENCE/t2_final_slots.txt`,`verify_counts2.txt` |
| 5 | GetSize 双点闭合 | 5/5 具体类（Aircraft `0x6D8`/Building `0x720`/Infantry `0x6F0`/Unit `0x8E8`/Fogged `0x78`）v[12] imm == 工厂 push size→new `0x7C8E17`→ctor 写 VT；抽象基类 v[12]=`0x4C9150` 桩非真 GetSize | [已证] | `EVIDENCE/t3_getsize_final.txt`,`t3_getsize_closure.txt` |
| 6 | 字段增量 | +0xB8 补 1 字节读点（`0x74431F` mission 上下文，派生类方法）；+0xCC/+0x6C 补不出可归属本类另一侧 | [未证]/候选 | `EVIDENCE/t4_fields.txt`,`t4_fields_broad.txt` |
| 7 | proved 对账 | 卡面 28（5.46%）**过期**；盘上真值 **55/513=10.72%**；本卡交 37 条 `[静态推断]→[已证]` delta | [已证] | `EVIDENCE/t1_targets_report.txt`,`DOD.md` |

## 给审计员的核心数字（可独立复算）

1. **Mission vtable 已定槽数 = 157**（MissionClass `0x7EDCC0`，end `0x7EDF34` noncode 定界）。复算：`work/t2_rtti_vtables.py` 从 `.rdata` 扫 `vtable[-1]∈COL` + `slot0 code` + 逐槽 code/COL/SEP 截断；不读 atlas。
2. **桩/实现 = 6 全桩槽 / 22 有实现槽；8 全桩 Mission / 24 有实现 Mission**。复算：`work/t2_final_slots.py`（classify 跟随 jmp thunk）+ `work/t2_dispatch.py`（32 项派发表→stub disp/4）；基线已测（裸形态无鉴别力）。
3. **proved 28(卡面)→盘上 55→本卡交 37 条升级**。复算：`work/t1_targets.py`（coverage.tsv S10 grade 自数）+ `work/build_delta.py`（37 行 `[静态推断]→[已证]`，均带证据路径）。**S10 远未达 50%**（门槛 257，差 187~229）。

## 纪律自检 / 分级

- 类名只认 RTTI `COL+0xC→TD+8`（未读 `COL[+8]`=CD 猜名）；无 `noinit_t` 误用。
- vtable 定界从 `.rdata`；`vtables_v2.json` 槽数未引用。基桩步长 0x10（纠正 S10-K1 的 0x10B）。
- 字段偏移不定语义：+0xB8 读点在派生类 ⇒ 只标候选不升 [已证]；+0xCC/+0x6C 跨类读/写全剔除；`call [reg+disp]` 虚槽调用显式剔除 34 处。
- 「不存在 X」查等价形式（jmp thunk/共用桩/B8 同形）；未用最近 E8/E9、最大函数、无调用者、entry_at_or_before；站点归属用函数区间。
- 停机核验：24/32、22/28、8 全桩、11 字段 8+3、196/144/52/43（用 RadioClass 七表）全部自算吻合；**唯一不符 = proved 28（卡面过期）→ 已上报不凑数**（见 DISAGREE D1）。
- 写「新发现」前已 `Select-String` 主台账/STATUS_BOARD；未写台账、未改游戏文件、未 git commit/push。

## 交付 / 复跑

- 结论：`LAYOUT.md`（T2–T4）、`DOD.md`（六条）、`UNKNOWNS.md`、`DISAGREE.md`、`TARGETS.tsv`（515 行）。
- 证据：`EVIDENCE/*.txt/.json`（不截断）、`work/*.py`（可复跑；Python 3.12.10 + capstone 5.0.7 skipdata=True + pefile 2024.8.26）。
- 增量：`coverage_delta.tsv`（37 行 `[静态推断]→[已证]`，已校验结构）；**未改** `COVERAGE\coverage.tsv`。
