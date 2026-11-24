# R16-AUDIT-SLOTN-B3 · 机械证据附录

> 由 `verify.py` + `gen_tables.py` 从只读 `gamemd.exe` / `coverage.tsv` / `delta.tsv` / `slotN43.tsv` 生成。
> `gamemd.exe` SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`（4825360 B）
> `coverage.tsv`（本审计快照）SHA-256 `C269720F59C07845250A81CA8C6562F62260C1C9ECFC99F160E72F80F58144A5`（4026555 B，18498 数据行）
> `delta.tsv` SHA-256 `B1C9E6DFA8FCC884812D91F3E93A4C0CEC288FE0EC1BCE5D4DB7F72771BD48F8`（11774 B）

## §A 最小改动与原文保全（逐行）

| # | entry | cov 行号 | 原第4列字节长 | 原句末字符 | 追加段字节长 | 追加段首字符 | 连接处 | 原第4列已含④ | 第1/2/3/5/6/7/8 列 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 005B3060 | 6120 | 325 | `。` | 475 | `；` | `。；` | 否 | 逐字节相同 |
| 2 | 005B3570 | 6121 | 354 | `。` | 483 | `；` | `。；` | 否 | 逐字节相同 |
| 3 | 005B35E0 | 6122 | 348 | `。` | 483 | `；` | `。；` | 否 | 逐字节相同 |
| 4 | 005B3650 | 6123 | 337 | `。` | 479 | `；` | `。；` | 否 | 逐字节相同 |
| 5 | 005B36B0 | 6124 | 322 | `。` | 479 | `；` | `。；` | 否 | 逐字节相同 |
| 6 | 005B4630 | 6149 | 237 | `。` | 471 | `；` | `。；` | 否 | 逐字节相同 |
| 7 | 00653100 | 7889 | 177 | `。` | 467 | `；` | `。；` | 否 | 逐字节相同 |
| 8 | 0065CBF0 | 8067 | 233 | `。` | 471 | `；` | `。；` | 否 | 逐字节相同 |
| 9 | 006B1850 | 8877 | 313 | `。` | 595 | `；` | `。；` | 否 | 逐字节相同 |
| 10 | 006B1900 | 8878 | 297 | `。` | 595 | `；` | `。；` | 否 | 逐字节相同 |
| 11 | 006B8660 | 8983 | 311 | `。` | 595 | `；` | `。；` | 否 | 逐字节相同 |
| 12 | 006B8710 | 8984 | 272 | `。` | 595 | `；` | `。；` | 否 | 逐字节相同 |
| 13 | 006F9E50 | 10037 | 206 | `。` | 471 | `；` | `。；` | 否 | 逐字节相同 |

前缀判定：`delta_col4.startswith(cov_col4)` **13/13 True**；7 列 × 13 行 = **91 次比较，0 不同**；`grade` 列 13/13 == `[已证]`。

## §B 六项字节事实（逐行实测值，本审计独立复算）

| # | entry | ①u32(vt+slot*4) | ②u32(vt-4)=COL | ③u32(COL+4)=off | ④u32(COL+12)=TD | ⑤cstr(TD+8) | ⑥装表点解码 |
|---|---|---|---|---|---|---|---|
| 1 | 005B3060 | `0x005B3060` | `0x00805D28` | `0` | `0x00817B18` | `.?AVMissionClass@@` | `mov dword ptr [esi], 0x7edcc0` |
| 2 | 005B3570 | `0x005B3570` | `0x008033B8` | `0` | `0x00825508` | `.?AVInfantryClass@@` | `mov dword ptr [esi], 0x7eb058` |
| 3 | 005B35E0 | `0x005B35E0` | `0x008033B8` | `0` | `0x00825508` | `.?AVInfantryClass@@` | `mov dword ptr [esi], 0x7eb058` |
| 4 | 005B3650 | `0x005B3650` | `0x00805D28` | `0` | `0x00817B18` | `.?AVMissionClass@@` | `mov dword ptr [esi], 0x7edcc0` |
| 5 | 005B36B0 | `0x005B36B0` | `0x00805D28` | `0` | `0x00817B18` | `.?AVMissionClass@@` | `mov dword ptr [esi], 0x7edcc0` |
| 6 | 005B4630 | `0x005B4630` | `0x00805DE0` | `0` | `0x0082C318` | `.?AVMixFileClass@@` | `mov dword ptr [esi], 0x7edf50` |
| 7 | 00653100 | `0x00653100` | `0x008083C0` | `0` | `0x00816BF8` | `.?AVRadarClass@@` | `mov dword ptr [esi], 0x7f0344` |
| 8 | 0065CBF0 | `0x0065CBF0` | `0x00808790` | `0` | `0x00815DF8` | `.?AVRawFileClass@@` | `mov dword ptr [esi], 0x7f0904` |
| 9 | 006B1850 | `0x006B1850` | `0x00809620` | `0` | `0x0083FCD0` | `.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@` | `mov dword ptr [0xb0b5f0], 0x7f315c` |
| 10 | 006B1900 | `0x006B1900` | `0x00809620` | `0` | `0x0083FCD0` | `.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@` | `mov dword ptr [0xb0b5f0], 0x7f315c` |
| 11 | 006B8660 | `0x006B8660` | `0x00809A08` | `0` | `0x008400E0` | `.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@` | `mov dword ptr [0xb0b880], 0x7f35e4` |
| 12 | 006B8710 | `0x006B8710` | `0x00809A08` | `0` | `0x008400E0` | `.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@` | `mov dword ptr [0xb0b880], 0x7f35e4` |
| 13 | 006F9E50 | `0x006F9E50` | `0x0080C058` | `0` | `0x00817B58` | `.?AVTechnoClass@@` | `mov dword ptr [esi], 0x7f4960` |

六项 × 13 行 = **78 项全部成立**（c1–c6 各自不合格行数：0/0/0/0/0/0）。

## §B 附 · 原始字节 dump（本审计直接读盘，非执行器产物）

```text
# row 1  005B3060  (slot 23)
  007EDD1C (vt+23*4 = 007EDD1C) : 60 30 5B 00   -> 0x005B3060
  007EDCBC (vt-4)            : 28 5D 80 00   -> 0x00805D28
  00805D28 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 18 7B 81 00
  00817B20 (TD+8 内联串)     : ".?AVMissionClass@@"
  005B2DE9 (装表点)          : mov dword ptr [esi], 0x7edcc0

# row 2  005B3570  (slot 123)
  007EB244 (vt+123*4 = 007EB244) : 70 35 5B 00   -> 0x005B3570
  007EB054 (vt-4)            : B8 33 80 00   -> 0x008033B8
  008033B8 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 08 55 82 00
  00825510 (TD+8 内联串)     : ".?AVInfantryClass@@"
  00517D9D (装表点)          : mov dword ptr [esi], 0x7eb058

# row 3  005B35E0  (slot 122)
  007EB240 (vt+122*4 = 007EB240) : E0 35 5B 00   -> 0x005B35E0
  007EB054 (vt-4)            : B8 33 80 00   -> 0x008033B8
  008033B8 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 08 55 82 00
  00825510 (TD+8 内联串)     : ".?AVInfantryClass@@"
  00521A11 (装表点)          : mov dword ptr [esi], 0x7eb058

# row 4  005B3650  (slot 125)
  007EDEB4 (vt+125*4 = 007EDEB4) : 50 36 5B 00   -> 0x005B3650
  007EDCBC (vt-4)            : 28 5D 80 00   -> 0x00805D28
  00805D28 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 18 7B 81 00
  00817B20 (TD+8 内联串)     : ".?AVMissionClass@@"
  005B2DE9 (装表点)          : mov dword ptr [esi], 0x7edcc0

# row 5  005B36B0  (slot 126)
  007EDEB8 (vt+126*4 = 007EDEB8) : B0 36 5B 00   -> 0x005B36B0
  007EDCBC (vt-4)            : 28 5D 80 00   -> 0x00805D28
  00805D28 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 18 7B 81 00
  00817B20 (TD+8 内联串)     : ".?AVMissionClass@@"
  005B2DE9 (装表点)          : mov dword ptr [esi], 0x7edcc0

# row 6  005B4630  (slot 0)
  007EDF50 (vt+0*4 = 007EDF50) : 30 46 5B 00   -> 0x005B4630
  007EDF4C (vt-4)            : E0 5D 80 00   -> 0x00805DE0
  00805DE0 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 18 C3 82 00
  0082C320 (TD+8 内联串)     : ".?AVMixFileClass@@"
  005B3C52 (装表点)          : mov dword ptr [esi], 0x7edf50

# row 7  00653100  (slot 16)
  007F0384 (vt+16*4 = 007F0384) : 00 31 65 00   -> 0x00653100
  007F0340 (vt-4)            : C0 83 80 00   -> 0x008083C0
  008083C0 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 F8 6B 81 00
  00816C00 (TD+8 内联串)     : ".?AVRadarClass@@"
  00652B45 (装表点)          : mov dword ptr [esi], 0x7f0344

# row 8  0065CBF0  (slot 5)
  007F0918 (vt+5*4 = 007F0918) : F0 CB 65 00   -> 0x0065CBF0
  007F0900 (vt-4)            : 90 87 80 00   -> 0x00808790
  00808790 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 F8 5D 81 00
  00815E00 (TD+8 内联串)     : ".?AVRawFileClass@@"
  0065CA03 (装表点)          : mov dword ptr [esi], 0x7f0904

# row 9  006B1850  (slot 2)
  007F3164 (vt+2*4 = 007F3164) : 50 18 6B 00   -> 0x006B1850
  007F3158 (vt-4)            : 20 96 80 00   -> 0x00809620
  00809620 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 D0 FC 83 00
  0083FCD8 (TD+8 内联串)     : ".?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@"
  006AF13D (装表点)          : mov dword ptr [0xb0b5f0], 0x7f315c

# row 10 006B1900  (slot 4)
  007F316C (vt+4*4 = 007F316C) : 00 19 6B 00   -> 0x006B1900
  007F3158 (vt-4)            : 20 96 80 00   -> 0x00809620
  00809620 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 D0 FC 83 00
  0083FCD8 (TD+8 内联串)     : ".?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@"
  006AF13D (装表点)          : mov dword ptr [0xb0b5f0], 0x7f315c

# row 11 006B8660  (slot 2)
  007F35EC (vt+2*4 = 007F35EC) : 60 86 6B 00   -> 0x006B8660
  007F35E0 (vt-4)            : 08 9A 80 00   -> 0x00809A08
  00809A08 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 E0 00 84 00
  008400E8 (TD+8 内联串)     : ".?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@"
  006B6C2D (装表点)          : mov dword ptr [0xb0b880], 0x7f35e4

# row 12 006B8710  (slot 4)
  007F35F4 (vt+4*4 = 007F35F4) : 10 87 6B 00   -> 0x006B8710
  007F35E0 (vt-4)            : 08 9A 80 00   -> 0x00809A08
  00809A08 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 E0 00 84 00
  008400E8 (TD+8 内联串)     : ".?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@"
  006B6C2D (装表点)          : mov dword ptr [0xb0b880], 0x7f35e4

# row 13 006F9E50  (slot 23)
  007F49BC (vt+23*4 = 007F49BC) : 50 9E 6F 00   -> 0x006F9E50
  007F495C (vt-4)            : 58 C0 80 00   -> 0x0080C058
  0080C058 (COL)            : 00 00 00 00 00 00 00 00 00 00 00 00 58 7B 81 00
  00817B60 (TD+8 内联串)     : ".?AVTechnoClass@@"
  006F3130 (装表点)          : mov dword ptr [esi], 0x7f4960

```

## §B 附2 · 装表点宿主函数体（「site 体内 / entry 体外」校验）

| # | entry | 声称 func | 前一字节为对齐填充 | 解码能否精确落到 site | 到达 site 的指令数 | body 区间 | site∈body | entry∉body |
|---|---|---|---|---|---|---|---|---|
| 1 | 005B3060 | `0x005B2DA0` | `0x90` | 是 | 16 | `[0x005B2DA0, 0x005B2E08)` | 是 | 是 |
| 2 | 005B3570 | `0x00517D90` | `0x90` | 是 | 8 | `[0x00517D90, 0x00517F95)` | 是 | 是 |
| 3 | 005B35E0 | `0x00521960` | `0x90` | 是 | 57 | `[0x00521960, 0x00521AF2)` | 是 | 是 |
| 4 | 005B3650 | `0x005B2DA0` | `0x90` | 是 | 16 | `[0x005B2DA0, 0x005B2E08)` | 是 | 是 |
| 5 | 005B36B0 | `0x005B2DA0` | `0x90` | 是 | 16 | `[0x005B2DA0, 0x005B2E08)` | 是 | 是 |
| 6 | 005B4630 | `0x005B3C20` | `0x90` | 是 | 19 | `[0x005B3C20, 0x005B3D4F)` | 是 | 是 |
| 7 | 00653100 | `0x00652960` | `0x90` | 是 | 104 | `[0x00652960, 0x00652BB7)` | 是 | 是 |
| 8 | 0065CBF0 | `0x0065CA00` | `0x90` | 是 | 3 | `[0x0065CA00, 0x0065CA67)` | 是 | 是 |
| 9 | 006B1850 | `0x006AF120` | `0x90` | 是 | 7 | `[0x006AF120, 0x006AF15D)` | 是 | 是 |
| 10 | 006B1900 | `0x006AF120` | `0x90` | 是 | 7 | `[0x006AF120, 0x006AF15D)` | 是 | 是 |
| 11 | 006B8660 | `0x006B6C10` | `0x90` | 是 | 7 | `[0x006B6C10, 0x006B6C4D)` | 是 | 是 |
| 12 | 006B8710 | `0x006B6C10` | `0x90` | 是 | 7 | `[0x006B6C10, 0x006B6C4D)` | 是 | 是 |
| 13 | 006F9E50 | `0x006F2B40` | `0x90` | 是 | 263 | `[0x006F2B40, 0x006F3269)` | 是 | 是 |

> **「entry 体外」不是空约束（实例）**：行 6（`005B4630 MixFileClass::slot0`）的表 `007EDF50` 另有一个装表点 `0x005B4639`，它**落在 entry 自己体内**——`body(005B4630)=[005B4630, 005B46DF)`，`005B4630: 53 56 8B F1 33 DB 8B 46 0C **C7 06 50 DF 7E 00** 3B C3 …`，从 `005B4630` 解码第 6 条即精确命中 `005B4639`（`mov dword ptr [esi], 0x7edf50`，析构器开头回写自身 vptr）。执行器**避开**了它、取体外 `005B3C52`；若照抄 `site_of` 启发式，B⑥ 仍会通过而「entry 体外」会为假。

## §C 行 32/33 表改选四问四答 — 实测依据

### Q1 · `0043B71F` 装的是哪张表、RTTI 解出什么类？

- capstone：`mov dword ptr [esi], 0x7e3ebc` ⇒ `is_mov_mem_imm=True`，`imm32=0x007E3EBC`
- 该表 `COL=0x007FC360` / `offset=0` / `TD=0x00818D60` / `TD+8=".?AVBuildingClass@@"` ⇒ 类 = **BuildingClass**
- 该表槽数（连续指向 .text 的槽）：**322**

### Q2 · entry 在 `007EB058` 的第几槽 / 在 BuildingClass 表里也在某槽吗？

| entry | 表 | vt | 实测所在槽 | 行 slot_no |
|---|---|---|---|---|
| 005B3570 | 007EB058_Infantry | `0x007EB058` | [123] | 123 |
| 005B3570 | BuildingClass | `0x007E3EBC` | [123] | 123 |
| 005B35E0 | 007EB058_Infantry | `0x007EB058` | [122] | 122 |
| 005B35E0 | BuildingClass | `0x007E3EBC` | [122] | 122 |

全表枚举（本审计独立扫全镜像，凡 `T-4` 可解出合法 COL 链者计入）：

| entry | 命中表数 | (vt, 槽, 类) |
|---|---|---|
| 005B3570 | 7 | `0x007E3EBC`#123 BuildingClass；`0x007E8C94`#123 FootClass；`0x007EB058`#123 InfantryClass；`0x007EDCC0`#123 MissionClass；`0x007F0508`#123 RadioClass；`0x007F4960`#123 TechnoClass；`0x007F5C70`#123 UnitClass |
| 005B35E0 | 7 | `0x007E3EBC`#122 BuildingClass；`0x007E8C94`#122 FootClass；`0x007EB058`#122 InfantryClass；`0x007EDCC0`#122 MissionClass；`0x007F0508`#122 RadioClass；`0x007F4960`#122 TechnoClass；`0x007F5C70`#122 UnitClass |

### Q3 · 声称装表点是否 `mov <mem>, imm32` 且 `imm32 == 007EB058`？是否在本 entry 之外的函数体内？

| entry | site | capstone | imm32 | imm==007EB058 | 声称 func | func 起点合法 | body | entry∈body |
|---|---|---|---|---|---|---|---|---|
| 005B3570 | `0x00517D9D` | `mov dword ptr [esi], 0x7eb058` | `0x007EB058` | 是 | `0x00517D90` | 是（前字节 `0x90`） | `[0x00517D90, 0x00517F95)` | 否 |
| 005B35E0 | `0x00521A11` | `mov dword ptr [esi], 0x7eb058` | `0x007EB058` | 是 | `0x00521960` | 是（前字节 `0x90`） | `[0x00521960, 0x00521AF2)` | 否 |

### Q3 附 · 同一张表的全部装表点（0xC7 候选 21940 个逐条 capstone 解码确认）

- `007EB058`（InfantryClass）全部装表点：`0x00517ACC`、`0x00517D9D`、`0x00521A11`
- `0x007E3EBC`（BuildingClass）全部装表点：`0x0043B71F`、`0x0043B9FA`、`0x0043BCFD`

## §C 附2 · 本批 8 张 vt 的装表点全景（证明「同一表多装表点属正常」）

| vt | 涉及行 | 枚举到的装表点数 | 全部装表点 | 本批采用 | 采用点在枚举内 |
|---|---|---|---|---|---|
| `0x007EB058` | 005B3570、005B35E0 | 3 | `0x00517ACC`、`0x00517D9D`、`0x00521A11` | `0x00517D9D`、`0x00521A11` | 是 |
| `0x007EDCC0` | 005B3060、005B3650、005B36B0 | 4 | `0x005B2DE9`、`0x005B3A63`、`0x0065AF12`、`0x006F4775` | `0x005B2DE9` | 是 |
| `0x007EDF50` | 005B4630 | 3 | `0x005B3C52`、`0x005B3F59`、`0x005B4639` | `0x005B3C52` | 是 |
| `0x007F0344` | 00653100 | 4 | `0x00652B45`、`0x00652C0C`、`0x006587AC`、`0x006A4F78` | `0x00652B45` | 是 |
| `0x007F0904` | 0065CBF0 | 4 | `0x0065CA03`、`0x0065CAA8`、`0x0065D3A3`、`0x006C77C7` | `0x0065CA03` | 是 |
| `0x007F315C` | 006B1850、006B1900 | 1 | `0x006AF13D` | `0x006AF13D` | 是 |
| `0x007F35E4` | 006B8660、006B8710 | 1 | `0x006B6C2D` | `0x006B6C2D` | 是 |
| `0x007F4960` | 006F9E50 | 3 | `0x006F3130`、`0x006F4413`、`0x006F450D` | `0x006F3130` | 是 |

## §D 文本与事实一致（以装表点为唯一锚，正向推出全链后比对）

| # | entry | site→imm32(=vt) | →COL | →offset | →TD | →TD+8 装饰名 | 文本↔链 5 字段 | slot 四方一致 | <Class>↔name | <Class>↔装饰名 | D-47 指针 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 005B3060 | `0x007EDCC0` | `0x00805D28` | 0 | `0x00817B18` | `.?AVMissionClass@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 2 | 005B3570 | `0x007EB058` | `0x008033B8` | 0 | `0x00825508` | `.?AVInfantryClass@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 3 | 005B35E0 | `0x007EB058` | `0x008033B8` | 0 | `0x00825508` | `.?AVInfantryClass@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 4 | 005B3650 | `0x007EDCC0` | `0x00805D28` | 0 | `0x00817B18` | `.?AVMissionClass@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 5 | 005B36B0 | `0x007EDCC0` | `0x00805D28` | 0 | `0x00817B18` | `.?AVMissionClass@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 6 | 005B4630 | `0x007EDF50` | `0x00805DE0` | 0 | `0x0082C318` | `.?AVMixFileClass@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 7 | 00653100 | `0x007F0344` | `0x008083C0` | 0 | `0x00816BF8` | `.?AVRadarClass@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 8 | 0065CBF0 | `0x007F0904` | `0x00808790` | 0 | `0x00815DF8` | `.?AVRawFileClass@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 9 | 006B1850 | `0x007F315C` | `0x00809620` | 0 | `0x0083FCD0` | `.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 10 | 006B1900 | `0x007F315C` | `0x00809620` | 0 | `0x0083FCD0` | `.?AV?$DynamicVectorClass@PAVSlaveManagerClass@@@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 11 | 006B8660 | `0x007F35E4` | `0x00809A08` | 0 | `0x008400E0` | `.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 12 | 006B8710 | `0x007F35E4` | `0x00809A08` | 0 | `0x008400E0` | `.?AV?$DynamicVectorClass@PAVSpawnManagerClass@@@@` | 全等 | 是 | 是 | 是 | §12.6 |
| 13 | 006F9E50 | `0x007F4960` | `0x0080C058` | 0 | `0x00817B58` | `.?AVTechnoClass@@` | 全等 | 是 | 是 | 是 | §12.6 |

披露句逐字（13/13 相同后缀，仅前段类名/slot 不同）：

```text
（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.6 与 PANEL 对应披露）
```

`§12.4` 出现次数（全 `delta.tsv` 数据行）：**0**；`§12.6` 行数：**13**。

指针落点（本审计核对，非空指）：`R14_COMMON.md` **L1558** 起 = `§12.6 【COMMON-R16 追加】D-47 裁决`；`COVERAGE\PANEL.md` **L161–171** = M74 冲突披露 + **M84 裁决落定**（L171 写明「成文位置：R14_COMMON.md §12.6」）。`R14_COMMON.md` 另有**旧 §12.4**（L1216「三条推进通道的上限量化」），故写成 §12.4 会落到无关条款。

## §E 格式合先例

先例 3 条（`00464AC0` / `004DE630` / `004F42F0`）归一后骨架（三者相同：True）：

```text
④ 活表槽位见证：<CLS>::slot<N>（vt=<H>，槽 <N> 值=<H>，COL=<H> offset=<N>，RTTI=<H>→<MAN>；装表点 <H> 位于 <H> 体内，entry 体外） ④升级句：<CLS>::slot<N>（④ 表属类与行名类一致，均为 <CLS>；该槽即其 vt=<H> 表 slot<N>，无归属歧义）
```

| # | entry | core 与先例骨架逐字符相等 | 尾部额外括注（长度） |
|---|---|---|---|
| 1 | 005B3060 | PASS | 65 字符 |
| 2 | 005B3570 | PASS | 65 字符 |
| 3 | 005B35E0 | PASS | 65 字符 |
| 4 | 005B3650 | PASS | 65 字符 |
| 5 | 005B36B0 | PASS | 65 字符 |
| 6 | 005B4630 | PASS | 65 字符 |
| 7 | 00653100 | PASS | 65 字符 |
| 8 | 0065CBF0 | PASS | 65 字符 |
| 9 | 006B1850 | PASS | 65 字符 |
| 10 | 006B1900 | PASS | 65 字符 |
| 11 | 006B8660 | PASS | 65 字符 |
| 12 | 006B8710 | PASS | 65 字符 |
| 13 | 006F9E50 | PASS | 65 字符 |

## §F 反抄袭

- 整段 ④ 文本 `set()`：**13/13** 互不相同。
- 8 位十六进制全部归一为 `ENTRY` 后 `set()`：**13/13** 互不相同（= 卡面判据「entry 归一后仍两两不同」）。
- 再收紧（slot 号与 offset 一并归一）后的重复组（属**事实相同**，见 VERDICT §6 判据）：

- 005B3060、005B3650、005B36B0
- 005B3570、005B35E0
- 006B1850、006B1900
- 006B8660、006B8710

- 同 vt 同 site 分组：

- `0x007EDCC0 | 0x005B2DE9` → 005B3060、005B3650、005B36B0
- `0x007F315C | 0x006AF13D` → 006B1850、006B1900
- `0x007F35E4 | 0x006B6C2D` → 006B8660、006B8710

- 字段多样性：vt **8** 种 / slot **10** 种 / class **8** 种 / site **9** 种。

## §E 附 · 全量先例普查（盘上全部含「④ 活表槽位见证」的行，不只 3 条）

| 口径 | 行数 | 说明 |
|---|---|---|
| 盘上含「④ 活表槽位见证」的总行数 | 106 | 与卡面「既有 106 行先例」一致 |
| variantA（`④升级句：<CLS>::slotN（④ 表属类与行名类一致，均为 <CLS>；…无归属歧义）`） | 55 | 归一后骨架种类数 **1**，且**全部等于本批骨架**（是） |
| variantB（`④升级句：<CLS>::slotN；类名归属：…`） | 51 | 行名类 ≠ 表类时的既有变体，结构不同故不适用本批 |
| 不可解析 | 0 | — |

⇒ 本批 13 行走的是**多数派 variantA**，且是该变体唯一骨架；本批 13 行的行名类全部等于其所选表的类，故**结构上不可能**落到 variantB。

## 逐行总表（13 行全做，无抽样）

| # | entry | name | slot | vt | 装表点 | §A | §B(6) | §D | §E | §F | 行判 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 005B3060 | `MissionClass::slot23` | 23 | `0x007EDCC0` | `0x005B2DE9` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 2 | 005B3570 | `InfantryClass::slot123` | 123 | `0x007EB058` | `0x00517D9D` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 3 | 005B35E0 | `InfantryClass::slot122` | 122 | `0x007EB058` | `0x00521A11` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 4 | 005B3650 | `MissionClass::slot125` | 125 | `0x007EDCC0` | `0x005B2DE9` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 5 | 005B36B0 | `MissionClass::slot126` | 126 | `0x007EDCC0` | `0x005B2DE9` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 6 | 005B4630 | `MixFileClass::slot0` | 0 | `0x007EDF50` | `0x005B3C52` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 7 | 00653100 | `RadarClass::slot16` | 16 | `0x007F0344` | `0x00652B45` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 8 | 0065CBF0 | `RawFileClass::slot5` | 5 | `0x007F0904` | `0x0065CA03` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 9 | 006B1850 | `T_DynamicVectorClass_PAVSlaveManagerClass__::slot2` | 2 | `0x007F315C` | `0x006AF13D` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 10 | 006B1900 | `T_DynamicVectorClass_PAVSlaveManagerClass__::slot4` | 4 | `0x007F315C` | `0x006AF13D` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 11 | 006B8660 | `T_DynamicVectorClass_PAVSpawnManagerClass__::slot2` | 2 | `0x007F35E4` | `0x006B6C2D` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 12 | 006B8710 | `T_DynamicVectorClass_PAVSpawnManagerClass__::slot4` | 4 | `0x007F35E4` | `0x006B6C2D` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 13 | 006F9E50 | `TechnoClass::slot23` | 23 | `0x007F4960` | `0x006F3130` | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |

### §D 附 · `<Class>` 与 RTTI 装饰名的字面/归一化口径

| # | entry | 行 name 前缀 | RTTI 解出类名 | 字面相等 | 归一口径（probe.py:col_name_match） |
|---|---|---|---|---|---|
| 1 | 005B3060 | `MissionClass` | `MissionClass` | 是 | match |
| 2 | 005B3570 | `InfantryClass` | `InfantryClass` | 是 | match |
| 3 | 005B35E0 | `InfantryClass` | `InfantryClass` | 是 | match |
| 4 | 005B3650 | `MissionClass` | `MissionClass` | 是 | match |
| 5 | 005B36B0 | `MissionClass` | `MissionClass` | 是 | match |
| 6 | 005B4630 | `MixFileClass` | `MixFileClass` | 是 | match |
| 7 | 00653100 | `RadarClass` | `RadarClass` | 是 | match |
| 8 | 0065CBF0 | `RawFileClass` | `RawFileClass` | 是 | match |
| 9 | 006B1850 | `T_DynamicVectorClass_PAVSlaveManagerClass__` | `?$DynamicVectorClass@PAVSlaveManagerClass` | 否（模板伪名） | match |
| 10 | 006B1900 | `T_DynamicVectorClass_PAVSlaveManagerClass__` | `?$DynamicVectorClass@PAVSlaveManagerClass` | 否（模板伪名） | match |
| 11 | 006B8660 | `T_DynamicVectorClass_PAVSpawnManagerClass__` | `?$DynamicVectorClass@PAVSpawnManagerClass` | 否（模板伪名） | match |
| 12 | 006B8710 | `T_DynamicVectorClass_PAVSpawnManagerClass__` | `?$DynamicVectorClass@PAVSpawnManagerClass` | 否（模板伪名） | match |
| 13 | 006F9E50 | `TechnoClass` | `TechnoClass` | 是 | match |

