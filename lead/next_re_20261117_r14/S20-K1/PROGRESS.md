# S20-K1 PROGRESS（卡号 S20-K1）

目标文件 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（本卡全值复核一致）·ImageBase 0x400000·只读未写入。
写域仅 `lead\next_re_20261117_r14\S20-K1\`（`work/` + `EVIDENCE/` + 本文件组）。capstone 全 `skipdata=True`。

## 结论表

| 项 | 结论 | 分级 | 证据路径 |
|---|---|:---|---|
| RTTI 类清单 | 8 类实测：Anim/Particle/ParticleSystem/VoxelAnim + 4 Type 类；名/TD/COL/vtable/槽数 | `[已证]` | `EVIDENCE/T1_rtti_vtables.tsv` |
| 总量校验 | TD 988 / COL 1214 / 表 1214 / **槽 14,044** —— 复现 R14 §8.1 审计基线，未受害于 vtables_v2.json 错 | `[已证]` | `EVIDENCE/T1_rtti_summary.txt` |
| GetSize 双向 | 4 实例类通道A(imm32)+通道B(分配对)全闭合 | `[已证]` | `EVIDENCE/T2_getsize_channelA.txt`、`T2_getsize_channelB_v3.txt` |
| GetSize 值 | Anim 0x1C8 / Particle 0x138 / PSys 0x100 / VoxelAnim 0x148 | `[已证]` | `EVIDENCE/T2_getsize_channelA.tsv` |
| Type 类 GetSize | 4 类通道A imm32（0x378/0x318/0x310/0x308），通道B 未闭合 | 通道A `[已证]` | `EVIDENCE/T2_getsize_channelA.tsv` |
| 字段布局 | 214 条偏移读写普查；4 类关键字段写者+读者双支撑 | 见 LAYOUT | `EVIDENCE/T3_field_census.tsv`、`T3_field_semantic_functions.txt` |
| Anim +0x184 | DelayTimer：ctor 写/Update dec/DrawIfVisible 门/减至0触发 0x424CE0 | `[已证]` | `EVIDENCE/T3_field_semantic_windows.txt` |
| 虚表关键槽 | 槽11 WhatAmI、槽12 GetSize、槽65 DrawIfVisible、槽69 Draw | `[已证]` | `EVIDENCE/T4_vtable_slots.tsv` |
| 更新入口 | Anim v23=0x423AC0；PSys Update 0x62DF20(<0x6C59CF)/0x62E070(<0x630233)；Draw 0 直接调用者 | `[已证]` | `EVIDENCE/T4_update_callsites.tsv` |
| T5 S07 接口 | DrawIt 0x6D3D10→0x6D8DB0→v65→v69（仅接口定位） | `[已证]` | `EVIDENCE/T4_update_callsites.tsv` |

## 给审计员的核心数字（可独立复算）

1. **AnimClass GetSize 立即数 = `0x1C8` (456)**，地址 `0x426530` 字节 `B8 C8 01 00 00 C3`。
   复算：`python work/t2_getsize.py`；独立复核 `mov eax,0x1c8;ret` + `EVIDENCE/T2_getsize_channelB_v3.tsv` 中 AnimClass 155 条 `push 0x1C8;call 0x7C8E17`→ctor 对。
2. **vtable 总量 = 1,214 表 / 14,044 槽**（R14 §8.1 基线值）。
   复算：`python work/t1_rtti.py`，判据 = `.rdata` 中 `sig=0 ∧ TD∈.data ∧ CHD∈.rdata` 的 COL 数（1214）+ 每个 `vt[-1]∈COL` 的表从 vt 起连续 `.text` 指针数；勿用 atlas。
3. **AnimClass +0x184 访问点 = 3 写 + 3 读**（写：ctor `0x421FC2`、Update dec 回写 `0x424393`、循环重挂 `0x4247E5`；读：Update `0x424386`、Save `0x425472`、DrawIfVisible 门 `0x422C70`）。
   复算：`python work/t3_anim184_exact.py`；`EVIDENCE/T3_anim184_exact.txt` 逐条指令（capstone detail W/R 位）。

## 纪律自检

- 双通道：T2 通道B（`push imm`/new）不依赖 function_atlas.tsv ✓
- 类名只认 `COL+0xC→TD+8`，读不到 fail-closed（本卡 COL 名全部 ASCII，无 `?`）✓
- 槽数从 `.rdata` 连续 `.text` 指针定界，未用 atlas ✓；vftable 槽值即函数（6B `mov eax,imm;ret` 已计入）✓
- 字段语义须写者+读者双支撑；`+0x94` 类跨类反例未套用 ✓
- 写值逐字符核对（`+0x184` dec、`+0xF4`=0x1d=29）✓；未改台账/游戏文件/未 git commit ✓
- 核心数字先测基线：slot 数对照审计 14,044/1214 ✓（无 N/N 空判据）。
