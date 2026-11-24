# S06-K2 PROGRESS（卡号 S06-K2）

目标 `ra2youli\gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（自算一致）｜静态卡，未跑真机｜写域仅 `S06-K2\`。

## 结论表
| 项 | 结论 | 级 | 证据 |
|---|---|---|---|
| T1 CellClass 字段数 | **63**（§958 一致；主表 24 槽+4 COL；`+0xB8` 本类写=0 已删；补 `+0x6C/70/74`） | 已证 | `EVIDENCE/t1_fields.txt`、`core_numbers.txt`、`foundation.txt` |
| T1 逐字段双支撑 | **17/63** 双支撑（本类写点全集+读点）；显式剔除虚调用 `call [reg+disp]`：方法集 51 处 / 全扫 4790 处 | 已证 | `t1_FINAL.txt`、`t1_field_table.txt`、`t1_reads_complete.txt` |
| T1 关键锚点 | `+0x24/26`=MapCoords、`+0x38`=地形类型、`+0x44`=覆盖物/矿类型、`+0x11B`=高度level、`+0x11E`=矿密度、`+0x12C/140`=位标志；均本类双支撑 | 已证/静态推断 | `t1_FINAL.txt`；PROBE_OFFSETS.md |
| T2 GetSize 双向核对 | **闭合**：v[12]=`0x487E70`=`B8 48 01 00 00 C3`→0x148；`push 0x148`@`0x5663C3/0x566B96`→new `0x7C8E17`→ctor `0x47BBF0` | 已证 | `t2_getsize.txt` |
| T2 基线（先测） | `.text` B8/C3 裸候选 666（非 slot12 597）；§969 记 ~837/543（口径差，见 D1）⇒ 必须叠加 vtable slot12 | 已证 | `t2_getsize.txt`、`DISAGREE.md` |
| T3 MapClass 定界 | **30 槽**（COL `0x8054C8`→vt `0x7ED404`，终止符 `0x7ED47C`=0x8055E0）；v[18-21]=共享桩；无 GetSize | 已证 | `foundation.txt`、`method_sets.txt`、`t3_map.txt` |
| T3 格数组 | `0x87F924`=MapClass+0x13C 指针字段（399 绝对读/0 绝对写）；stride=4 字节证据 `0x5657C1 8B 04 81`；`idx=(Y<<9)+X∈[0,0x40000)` | 已证 | `t3_map.txt`、`map_getcellat.txt`、`t3f_arraybase_dataflow.txt` |
| T4 两链读写点 | HEAD A(+0xE4) W4/R7（含 can-place `0x47C620` 扫描）；HEAD B(+0xE8) W3/R2；元素 `+0x30`=ObjectClass::NextObject | 已证 | `t4_lists.txt`、`t4_wrappers.txt` |
| T4 语义 | **+0xE4=FirstObject（占格对象链/ground）；+0xE8=AltObject（桥上对象链）**；选择键 `[obj+0x8C]=OnBridge` | 已证/静态推断 | `t4_wrappers.txt`、`cell_methods.txt` |
| T4 vs S12-K2 | **独立验证一致**（`0x47C620` 只扫 head A；`0x47E8A0` 按 `[+0x8C]` 选头），未采信其结论 | — | `DISAGREE.md` D2 |

## 给审计员的 3 个核心数字（可独立复算）
1. **双支撑字段数 = 17/63；字段总数 63**。复算：`python work/t1_fields.py`（输出 distinct offsets=63）+ `python work/t1d_reads_complete.py`（读点，不因早退 ret 截断）+ `python work/core_numbers.py`（报 17 及写覆盖规则）。63 的构成：direct-write 60 + `+0x26`(dword@+0x24 覆盖) + `+0x7C`/`+0xAC`(rep stosd 区)；`+0xB8` 写=0。
2. **虚调用剔除数 = 51（CellClass 方法集）/ 4790（含 1439 GetCellAt 窗口全扫）**。复算：`python work/t1_final.py` 与 `work/t1d_reads_complete.py`；规则=`call/jmp` 带内存操作数为 vtable 槽调用，非数据读（§969）。
3. **两链 W/R 点数**：`+0xE4` W4/R7、`+0xE8` W3/R2。复算：`python work/t4_lists.py`；地址见核心数字表；onBridge 选择 `0x5684B1`/`0x5688E1`。

## 交付
`LAYOUT.md`（T1–T4）、`PROBE_OFFSETS.md`（T5，可直接转真机卡）、`UNKNOWNS.md`、`DISAGREE.md`、`EVIDENCE/`（未截断，19 文件）、`work/`（20 脚本，可复跑）、`coverage_delta.tsv`（13 条，未改主 coverage）。未写台账、未改游戏文件、未 git commit、未跑真机、未建 Ghidra 副本。
