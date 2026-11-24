# S09-K1 PROGRESS — 类布局与虚表字节级取证

目标 `ra2youli\gamemd.exe`（SHA-256 `73201CC0…F67476` 已验）. 静态卡，未跑真机。capstone 全程 `skipdata=True`。
写域：本卡目录 + `_ghidra\S09-K1`（未使用 Ghidra）.

## 结论表

| 项 | 结论 | 级 | 证据 |
|---|---|---|---|
| RTTI 表自建 | 988 TD / 1214 COL；链 `COL+0xC→TD`, `TD+8` 内联 name；读 `COL+8` 会得 0/name='?' 已 fail-closed 拒绝 | [已证] | E00; work/re_lib.py |
| 虚表定界基线 | **1214 表 / 14,044 槽**，与审计 §8.1 基线逐位吻合（不信 vtables_v2.json 的 13,351） | [已证] | E01; work/t1_vtable_enum_v2.py |
| S09 类清单 | 21 个主要类 + ~40 CommandClass 子类：RTTI 名/TD/COL/vtable/槽数/父类 CHD 全表 | [已证] | T1_all_classes.tsv; E00 |
| 继承链(IGameMap) | IGameMap→GScreen→Map→Display→Radar→Power→Sidebar→Tab→Scroll→Mouse；父类由 CHD 实测 | [已证] | E00; work/t1_class_table.py |
| RTTI 权威名 | `Tactical`（无 Class 后缀）、`Mouse`（WWMouseClass 父类）——按字符串，不按头文件名 | [已证] | E00 |
| Tactical::GetSize | slot12 `B8 18 0E…C3`=0xE18 + `push 0xE18/call new` 构造器两处独立对上 → 闭合 | [已证] | E02 |
| Tactical::WhatAmI | slot11 `B8 38…C3`=0x38 | [已证] | E02 |
| 槽语义 12 条 | Sidebar/Select/Display/Mouse/Command 的 12 个槽函数指针逐条重读，全部 OK | [已证] | E03 |
| 侧栏 4×75 / stride 0x34 | S09-F1 已坐实（§950），本卡 RTTI+槽位对齐、未重做 | [已证](复用) | LAYOUT T5; S09-F1 VERDICT §2 |
| S09 UI 主类 GetSize | slot11/12 非 `B8 imm C3`（IGameMap 层次共享复杂函数），按纪律 9 报冲突+[未证]，不臆造 | [未证] | LAYOUT T2 |
| DisplayClass 字段 | +0x11CF/+0x11D0/+0x11B3/+0x11A4 写点+读点双支撑（语义多依赖 clue doc，故 [静态推断]） | [静态推断] | T3_field_scan_output.txt |
| CommandClass v[8] | 0x4C9150 抽象桩（46 子类各自覆写）；按基类 hook 会误伤 | [已证] | E03; R8 §21.1 |

## 给审计员的核心数字（含独立复算方法）

1. **1214 表 / 14,044 槽**（本卡最重要数字，直接对账 §8.1 基线）
   复算：`work/t1_vtable_enum_v2.py`。原理：`.rdata` 内 `dword==合法COL`（COL 定义 `sig=0` 且 `COL+0xC→TD` 且 TD+8 为 `.?AV…@@` 字符串）的位置 P 共 1214；vtable=P+4；从 vtable 逐 dword 读，值 ∈ `.text[0x401000,0x7E1000)` 记 1 槽，遇非代码值停，下一 P 为硬上界；求和 = 14,044。**不依赖 atlas entry+size**（纪律 3 的双通道要求：本卡通道=字节 RTTI/定界，与 S09-F1 的调用图通道不同源）.

2. **Tactical::GetSize = 0xE18（3608）双向闭合**
   复算：`work/t2_ctor_scan.py` + `E02`。判据A：`u32(0x7F4348+12*4)=0x6DC460`，`read(0x6DC460,6)=B8 18 0E 00 00 C3`。判据B：全 `.text` 扫 `push 0xE18` 紧接 `call 0x7C8E17`，命中 5 处；`0x6BF83C` 后继 `call 0x6D1C20(ctor)` 内 `0x6D1D54: mov [esi],0x7F4348`。两路独立对上 0xE18。**基线**：该 `B8 imm C3` 形态全镜像 ~638 个、仅 71 落在真 slot12（≈11%）⇒ 必须叠加槽位校验，本卡已叠加（纪律 1）.

3. **12 条槽语义槽值逐条 OK**
   复算：`work/t4_slot_verify.py` / `E03`。例：`u32(0x7F3058+16*4)=0x6A6C30`(SidebarClass Draw)、`u32(0x7F2FCC+31*4)=0x6AAD00`(SelectClass v31)、`u32(0x7EBE3C+8*4)=0x4C9150`(CommandClass 抽象桩)。期望值来源 R8_ui_crt.md §21.1，本卡独立重读现值对照.

## 边界与纪律
- 双通道：本卡通道=`.rdata/.data` RTTI 字节 + 虚表定界 + `B8 imm C3`/push 立即数；S09-F1 通道=全 `.text` 调用图/sweep。两者不同源（数据表 vs 代码引用图）.
- 不用 `function_atlas` entry+size 反推虚表；槽值即函数（含 6 字节 GetSize）不再做"像不像函数"二次筛选.
- 未对 `+0x80/+0x94/+0x184` 下跨类语义；未用 `ret 0xC`/最近 E8/E9/最大函数/无调用者启发式.
- 写"新发现"前 Select-String 过主台账/PANEL；未写台账、未改游戏文件、未 git commit/push.
- 与 S09-F1/台账/kb11 冲突处见 DISAGREE.md；未决见 UNKNOWNS.md.
