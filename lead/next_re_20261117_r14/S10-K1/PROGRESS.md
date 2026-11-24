# S10-K1 · PROGRESS（结论表 / 分级 / 证据 / 核心数字）

> 卡号 S10-K1｜Mission 系统｜2026-11-17。只读目标，未改游戏文件，未写台账，未 git commit。Ghidra 副本曾复制自 W150（`-noanalysis` 预案）但未启用；capstone+pefile 双通道足够，副本已删除。

## 结论表

| # | 问题 | 结论 | 级 | 证据 |
|---:|---|---|---|---|
| 1 | Mission 枚举表 | 指针表 `0x816CAC`（exclusive end `0x816D2C`），**32 项**，索引→名见 LAYOUT §1 | 已证 | `EVIDENCE/dump_ptr_table.txt`,`find_mission_xrefs.txt` |
| 2 | MissionClass 字段 | **11 字段**（`+AC,+B0,+B4,+B8,+BC,+C0,+C4,+C8,+CC,+D0,+6C`）；9 项双支撑，2 项静态推断 | 已证/静态推断 | `EVIDENCE/field_trace.txt` |
| 3 | 派发机制 | **两级混合**：`jmp [eax*4+0x5B34E8]`（32 项跳表）→ stub → `call [vptr+v129..v156]`；非纯跳表亦非每 Mission 独立入口函数 | 已证 | `EVIDENCE/dump_ai_dispatch.txt`,`mission_dispatch_map.txt` |
| 4 | Mission_* 实现 | **43 个**非桩实现（7 vtable 去重）；核心 13 Mission 见 LAYOUT §4 | 已证 | `EVIDENCE/rtti_and_counts.txt`,`disasm_mission_handlers.txt` |
| 5 | Guard→Attack | 判据 `[+0xAC]∈{2,0xA,5}`+目标链 `0x709290`；切换调用点 `QueueMission(1,0)` @ **`0x414B9E`** → `[+0xB4]=1` → `[+0xAC]` @ `0x5B357F` | 已证(切换)/静态推断(敌对判据位) | `EVIDENCE/ga_final.txt`,`mission_call_sites.txt` |
| 6 | 与 FootClass::AI 关系 | `FootClass::AI(0x4DA530)` 首段 `call 0x6F9E50`@`0x4DA539` → `call 0x5B3060`@`0x6FA655` → 派发 @`0x5B30C1`；**每帧**（不在 frame%N 门控的 60 条内） | 已证 | `EVIDENCE/footai_tail.txt`,`mission_call_sites.txt` |

## 核心数字（给审计）

| 数字 | 值 | 复算 |
|---|---|---|
| Mission 枚举项数 | **32** | 通道 A：`(0x816D2C−0x816CAC)/4`；通道 B：`0x5B3934 cmp esi,0x816d2c` 循环 32 次（`work/dump_ptr_table.py`,`find_mission_xrefs.py`） |
| 字段数 | **11** | LAYOUT §2 表逐一计；写点 `work/field_trace.py`，读点序列化块 `0x5B397E..0x5B3A26` |
| 派发表地址/项数 | **`0x5B34E8` / 32** | `work/dump_ai_dispatch.py` 读 32 dword，第 33 项起为 `90909090`；派发指令 `cmp eax,0x1F@5B30B8` |
| Mission_* 实现数 | **43** | `work/rtti_and_counts.py`：7 vtable×v[129..156] 去重，排除 28 个 `0x5B2E10..0x5B2FD0` 空桩 |
| 派发点地址 | **`0x5B30C1`** | `jmp dword ptr [eax*4+0x5B34E8]`（`EVIDENCE/find_mission_dispatch.txt`） |

## 双通道声明（纪律 1）

- 枚举项数：通道 A＝**数据表结构边界**（指针表 + 前后哨兵）完全不依赖 function_atlas；通道 B＝**代码循环上界**（`0x5B3910`）。两条不同源（数据 vs 代码），均未数 E8 站点。
- 派发表项数：通道 A＝**数据表尾部填充检测**（`0x5B3568` 起 `90`）；通道 B＝**派发函数边界比较**（`cmp eax,0x1f`）。不同源。

## 分级与纪律自检

- 类名只认 RTTI TD：MissionClass vtable `0x7EDCC0`→COL `0x805D28`→TD `0x817B18`→name `.?AVMissionClass@@`@`0x817B24`（逐字符核对）；未用 `noinit_t` 式推断。
- 字段语义须写者+读者双支撑：+AC/+B0/+B4/+BC/+C0/+C4/+C8/+D0 满足；+B8/+CC 读者未定 → 仅静态推断。
- thiscall 追 ecx：所有 Mission 方法 `mov esi,ecx`/`mov edi,ecx` 已核对；`0x6FA655` 的 `ecx=esi` 来自 `0x6FA63E`。
- 站点归属用函数区间（atlas `0x4DA530` size 2520 止于 `0x4DAF08`），未用 entry_at_or_before。
- 未用"最近 E8/E9 目标"/"无调用者=死代码"/"最大函数=热点"；所有穷举用 capstone skipdata=True 全 .text 扫。
- 停机核验：枚举 32、派发表 32、字段 11、实现 43 均与脚本输出一致，无凑数。

## 证据路径 / 复跑

- 结论文档：`lead\next_re_20261117_r14\S10-K1\LAYOUT.md`
- 原始证据（不截断）：`EVIDENCE\*.txt`（21 份，含全量反汇编/表 dump）
- 可复跑脚本：`work\*.py`（22 份，Python 3.12 + capstone 5.0.7 skipdata=True + pefile 2024.8.26）
- 未知/分歧：`UNKNOWNS.md`,`DISAGREE.md`；增量覆盖：`coverage_delta.tsv`（**未改** `COVERAGE\coverage.tsv`）
- Ghidra 副本 `_ghidra\S10-K1`：已删除（未启用）。
