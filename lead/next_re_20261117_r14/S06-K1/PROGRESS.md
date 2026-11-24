# S06-K1 PROGRESS（卡号 S06-K1）

## 结论表

| 项 | 结论 | 级 | 证据 |
|---|---|---|---|
| CellClass RTTI/vft/ctor/GetSize | TD `81CD70`(.?AVCellClass@@)，主 vft `7E4EEC`(COL off0)，ctor `47BBF0`；GetSize v[12]=`487E70`→`0x148`(328)，WhatAmI v[11]=11 | 已证 | `EVIDENCE/core_numbers.txt`, `find_vtables` 输出 |
| CellClass 字段数 | **61**（distinct offset `0x24..0x147`，write+read 双支撑）；max `0x140+4=0x144 ≤ 0x148` | 已证 | `EVIDENCE/cell_fields_raw.txt`, `core_numbers.txt` |
| 已知锚点核对 | `+0x30`=next ✓、`+0xE4/+0xE8`=链头 ✓；`+0xFC..0x100`=格坐标候选 **证伪**（实为附属对象指针/保留，MapCoords 在 `+0x24/+0x26`） | 已证 | `EVIDENCE/cell_ctor_disasm.txt`, `cell_methods_disasm.txt`; `DISAGREE.md` |
| 重点字段 | 地形类型 `+0x38`[静态推断]；高度 level `+0x11B`[已证]；覆盖物/矿类型 `+0x44`[已证]；矿密度 `+0x11E`[已证]；占用经链头无独立 bool[机制已证]；可见性位图 [未证]；旗标 `+0x12C`[部分] | 分级见 LAYOUT §2 | `EVIDENCE/cell_fields_raw.txt`, `ore_func_disasm.txt` |
| MapClass RTTI/vft/ctor | TD `816BC0`(.?AVMapClass@@)，主 vft `7ED404`(COL off0)，ctor `565090`；单例 `87F7E8` 最终动态类型 PowerClass(vft `7EFF54`)，经 DisplayClass(:MapClass) 链派生 | 已证 | `EVIDENCE/core_numbers.txt`, `EVIDENCE/vt_7e6114.txt`, `EVIDENCE/outer_vft_rtti.txt` |
| MapClass 字段数 | **17**（基 ctor + GetCellAt/init 关键字段 distinct offset）；`+0x13C` 格数组基址(399 abs refs)、`+0x14C`宽512、`+0x150`高512、`+0x154`格数0x40000 | 已证 | `EVIDENCE/map_field_access.txt`, `core_numbers.txt` |
| MapClass GetSize | **无**（vtable 179 槽全扫 B8/C3=0；非 AbstractClass 派生，基类 ctor `4F4220`≠`410170`）；与卡面预设不符，见 DISAGREE | 已证 | `EVIDENCE/core_numbers.txt`, `DISAGREE.md` |
| MapClass size | **0x1174 (4468)** 派生边界法：基 ctor 末写 `+0x1170`(4B)，DisplayClass ctor `4A8730` 首写 `+0x1174` | 已证 | `EVIDENCE/core_numbers.txt`, `EVIDENCE/map_ctor3_output.txt` |
| GetSize 一致性 | CellClass 两处独立对上（v[12]=0x148；`push 0x148`@`5663C3/566B96/6BF9BC`→new→ctor）；MapClass N/A | 已证 | `EVIDENCE/core_numbers.txt`, `size_alloc` 输出 |
| 越界写数 | **0**（CellClass 96 writes / MapClass 17 fields 全查 disp+width ≤ size） | 已证 | `EVIDENCE/core_numbers.txt` |
| 0x485020 逻辑 | `this`=CellClass*；读 `+0x44`(typeID)→`5FDD20`→`DVC<TiberiumClass*>` Items `B0F4EC`；读 `+0x11E`(density)，返回 `[tib+0xB8]×(density+1)`，无矿=0 | 已证 | `EVIDENCE/ore_func_disasm.txt` |
| 0x485020 调用者数 | **20**（capstone-linear 20 == raw-byte 20；§923 列 5 处是子集）；每点 ecx 溯源 GetCellAt(MapClass单例,CellStruct)→CellClass* | 已证 | `EVIDENCE/ore_callers.txt` |
| 每格每帧调用计数 | 静态结构（20 点均按格取值循环/邻格扫描）；动态次数未测，不用 EIP 权重 | 静态推断 | `EVIDENCE/ore_callers.txt`; `UNKNOWNS.md` |
| 坐标↔索引 | CellStruct{short X@0,short Y@2}；`idx=(short)Y<<9+(short)X`；valid `0≤idx<0x40000`；`cell=[[0x87F7E8+0x13C]+idx*4]`；逆 `X=idx&0x1FF,Y=idx>>9` | 已证 | `EVIDENCE/core_numbers.txt` |
| 双通道 | A=atlas `entry+size`（方法边界）；B=capstone 全 `.text` E8 rel32 裸扫 + RTTI COL/vtable 静态链；两通道不同源 | 已证 | `EVIDENCE/core_numbers.txt`, `EVIDENCE/ore_callers.txt` |

## 核心数字（复算方法）

1. **CellClass 字段数=61；GetSize=0x148；越界写=0**。复算：`python work/core_numbers.py`（§2/§4 段）。distinct offset 来自 62 个方法（主 vtable 槽+ctor/dtor+link/ore）的 `[this+disp]` 访问，`0x24≤disp<0x148` 去重；写数=disp+width>0x148 计数。
2. **MapClass 字段数=17；size=0x1174；GetSize=无**。复算：同脚本 §3 段（基 ctor `565090` 内 `[esi+disp]` 写 + 5 关键字段；扫 vtable `7ED404` 全槽 B8/C3）。
3. **0x485020 调用者=20**。复算：`python work/ore_callers.py`，capstone E8 rel32 与 raw-byte 两通道交叉（均 20、集合相同）。

## 交付与写域

- `LAYOUT.md`（≤200 行，本文件 ≤60 行）、`UNKNOWNS.md`、`DISAGREE.md`、`EVIDENCE/`（未截断）、`work/`（可复跑）、`coverage_delta.tsv`。
- 未改游戏文件、未写台账、未改 `COVERAGE\coverage.tsv`、未 git commit。Ghidra 未使用（capstone/pefile 已足够，副本未建）。
