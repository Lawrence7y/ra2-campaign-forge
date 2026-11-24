### §A–§E 逐行结果（15 行全做，无抽样）

| # | entry | name | slot | A 最小改动 | B 字节 6 项 | C 文本一致 | D 合先例 | E 反抄袭 | 行判 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | `T_DynamicVectorClass_PAVInfantryClass__::slot2` | 2 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 2 | 0045A610 | `T_DynamicVectorClass_PAVInfantryClass__::slot4` | 4 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 3 | 0045A680 | `T_DynamicVectorClass_PAVFoggedObjectClass__::slot2` | 2 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 4 | 0045A730 | `T_DynamicVectorClass_PAVFoggedObjectClass__::slot4` | 4 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 5 | 00473BA0 | `CCFileClass::slot10` | 10 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 6 | 00473C50 | `CCFileClass::slot5` | 5 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 7 | 00473D10 | `CCFileClass::slot7` | 7 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 8 | 004A9890 | `DisplayClass::slot36` | 36 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 9 | 004D24A0 | `FoggedObjectClass::slot6` | 6 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 10 | 004D2510 | `FoggedObjectClass::slot5` | 5 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 11 | 004D27D0 | `FoggedObjectClass::slot3` | 3 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 12 | 004D2810 | `FoggedObjectClass::slot13` | 13 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 13 | 004D4200 | `FootClass::slot139` | 139 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 14 | 004D4280 | `FootClass::slot151` | 151 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |
| 15 | 004D4B20 | `AircraftClass::slot133` | 133 | PASS | PASS 6/6 | PASS | PASS | PASS（entry 归一后唯一） | PASS |

### §A 最小改动证据（原第 4 列是否为严格前缀 + 其余 6 列逐字节比较）

| # | entry | coverage 行号 | 原第4列字节长 | 原句末字符 | 追加段字节长 | 追加段首字符 | 连接处 | 第1/2/3/5/6/7/8 列 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | 1388 | 188 | `。` | 407 | `；` | `。；` | 逐字节相同 |
| 2 | 0045A610 | 1389 | 171 | `。` | 407 | `；` | `。；` | 逐字节相同 |
| 3 | 0045A680 | 1391 | 199 | `）` | 423 | `；` | `）；` | 逐字节相同 |
| 4 | 0045A730 | 1392 | 171 | `）` | 423 | `；` | `）；` | 逐字节相同 |
| 5 | 00473BA0 | 1633 | 214 | `。` | 299 | `；` | `。；` | 逐字节相同 |
| 6 | 00473C50 | 1635 | 194 | `。` | 295 | `；` | `。；` | 逐字节相同 |
| 7 | 00473D10 | 1638 | 126 | `。` | 295 | `；` | `。；` | 逐字节相同 |
| 8 | 004A9890 | 2638 | 122 | `。` | 303 | `；` | `。；` | 逐字节相同 |
| 9 | 004D24A0 | 3109 | 153 | `）` | 319 | `；` | `）；` | 逐字节相同 |
| 10 | 004D2510 | 3110 | 133 | `）` | 319 | `；` | `）；` | 逐字节相同 |
| 11 | 004D27D0 | 3114 | 192 | `）` | 319 | `；` | `）；` | 逐字节相同 |
| 12 | 004D2810 | 3115 | 163 | `）` | 323 | `；` | `）；` | 逐字节相同 |
| 13 | 004D4200 | 3141 | 185 | `。` | 295 | `；` | `。；` | 逐字节相同 |
| 14 | 004D4280 | 3142 | 169 | `。` | 295 | `；` | `。；` | 逐字节相同 |
| 15 | 004D4B20 | 3143 | 174 | `。` | 311 | `；` | `。；` | 逐字节相同 |

### §B 六项实测值（本脚本从 `ra2youli\gamemd.exe` 字节独立复算）

| # | entry | ①u32(vt+slot*4) | ②u32(vt-4)=COL | ③u32(COL+4)=off | ④u32(COL+12)=TD | ⑤cstr(TD+8) | ⑥装表点解码 |
|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | `0045A560` | `007FC298` | `0` | `00818D28` | `.?AV?$DynamicVectorClass@PAVInfantryClass@@@@` | `mov dword ptr [esi + 0x66c], 0x7e43c8` |
| 2 | 0045A610 | `0045A610` | `007FC298` | `0` | `00818D28` | `.?AV?$DynamicVectorClass@PAVInfantryClass@@@@` | `mov dword ptr [esi + 0x66c], 0x7e43c8` |
| 3 | 0045A680 | `0045A680` | `007FC528` | `0` | `00819230` | `.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@` | `mov dword ptr [eax], 0x7e44f4` |
| 4 | 0045A730 | `0045A730` | `007FC528` | `0` | `00819230` | `.?AV?$DynamicVectorClass@PAVFoggedObjectClass@@@@` | `mov dword ptr [eax], 0x7e44f4` |
| 5 | 00473BA0 | `00473BA0` | `007FA590` | `0` | `00815E58` | `.?AVCCFileClass@@` | `mov dword ptr [esp + 0x20], 0x7e16b0` |
| 6 | 00473C50 | `00473C50` | `007FA590` | `0` | `00815E58` | `.?AVCCFileClass@@` | `mov dword ptr [esp + 0x20], 0x7e16b0` |
| 7 | 00473D10 | `00473D10` | `007FA590` | `0` | `00815E58` | `.?AVCCFileClass@@` | `mov dword ptr [esp + 0x20], 0x7e16b0` |
| 8 | 004A9890 | `004A9890` | `007FFCB8` | `0` | `00816BD8` | `.?AVDisplayClass@@` | `mov dword ptr [esi], 0x7e6114` |
| 9 | 004D24A0 | `004D24A0` | `00800768` | `0` | `00822438` | `.?AVFoggedObjectClass@@` | `mov dword ptr [esi], 0x7e8b38` |
| 10 | 004D2510 | `004D2510` | `00800768` | `0` | `00822438` | `.?AVFoggedObjectClass@@` | `mov dword ptr [esi], 0x7e8b38` |
| 11 | 004D27D0 | `004D27D0` | `00800768` | `0` | `00822438` | `.?AVFoggedObjectClass@@` | `mov dword ptr [esi], 0x7e8b38` |
| 12 | 004D2810 | `004D2810` | `00800768` | `0` | `00822438` | `.?AVFoggedObjectClass@@` | `mov dword ptr [esi], 0x7e8b38` |
| 13 | 004D4200 | `004D4200` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` |
| 14 | 004D4280 | `004D4280` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` |
| 15 | 004D4B20 | `004D4B20` | `007FB4C0` | `0` | `00817B90` | `.?AVAircraftClass@@` | `mov dword ptr [esi], 0x7e22a4` |

### §C 文本与事实一致（各项均以实测值比对）

| # | entry | name 的 slot | 文本「槽 N 值」 | 槽内值==entry | COL/offset/RTTI/装表点 与实测 | <Class>==name 前缀 | <Class>↔TD+8 装饰名 | D-47 披露句 |
|---|---|---|---|---|---|---|---|---|
| 1 | 0045A560 | 2 | `0045A560` | PASS | PASS | PASS（`T_DynamicVectorClass_PAVInfantryClass__`） | PASS | PASS 在位 |
| 2 | 0045A610 | 4 | `0045A610` | PASS | PASS | PASS（`T_DynamicVectorClass_PAVInfantryClass__`） | PASS | PASS 在位 |
| 3 | 0045A680 | 2 | `0045A680` | PASS | PASS | PASS（`T_DynamicVectorClass_PAVFoggedObjectClass__`） | PASS | PASS 在位 |
| 4 | 0045A730 | 4 | `0045A730` | PASS | PASS | PASS（`T_DynamicVectorClass_PAVFoggedObjectClass__`） | PASS | PASS 在位 |
| 5 | 00473BA0 | 10 | `00473BA0` | PASS | PASS | PASS（`CCFileClass`） | PASS | PASS 在位 |
| 6 | 00473C50 | 5 | `00473C50` | PASS | PASS | PASS（`CCFileClass`） | PASS | PASS 在位 |
| 7 | 00473D10 | 7 | `00473D10` | PASS | PASS | PASS（`CCFileClass`） | PASS | PASS 在位 |
| 8 | 004A9890 | 36 | `004A9890` | PASS | PASS | PASS（`DisplayClass`） | PASS | PASS 在位 |
| 9 | 004D24A0 | 6 | `004D24A0` | PASS | PASS | PASS（`FoggedObjectClass`） | PASS | PASS 在位 |
| 10 | 004D2510 | 5 | `004D2510` | PASS | PASS | PASS（`FoggedObjectClass`） | PASS | PASS 在位 |
| 11 | 004D27D0 | 3 | `004D27D0` | PASS | PASS | PASS（`FoggedObjectClass`） | PASS | PASS 在位 |
| 12 | 004D2810 | 13 | `004D2810` | PASS | PASS | PASS（`FoggedObjectClass`） | PASS | PASS 在位 |
| 13 | 004D4200 | 139 | `004D4200` | PASS | PASS | PASS（`FootClass`） | PASS | PASS 在位 |
| 14 | 004D4280 | 151 | `004D4280` | PASS | PASS | PASS（`FootClass`） | PASS | PASS 在位 |
| 15 | 004D4B20 | 133 | `004D4B20` | PASS | PASS | PASS（`AircraftClass`） | PASS | PASS 在位 |

### §D 骨架与先例逐字符比对（先例 3 条归一后为同一骨架）

先例骨架（`00464AC0/004DE630/004F42F0`）：

```text
④ 活表槽位见证：<CLS>::slot<N>（vt=<H>，槽 <N> 值=<H>，COL=<H> offset=<N>，RTTI=<H>→<MAN>；装表点 <H> 位于 <H> 体内，entry 体外） ④升级句：<CLS>::slot<N>（④ 表属类与行名类一致，均为 <CLS>；该槽即其 vt=<H> 表 slot<N>，无归属歧义）
```

| # | entry | core 与先例逐字符相等 | 尾部额外括注 |
|---|---|---|---|
| 1 | 0045A560 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 2 | 0045A610 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 3 | 0045A680 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 4 | 0045A730 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 5 | 00473BA0 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 6 | 00473C50 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 7 | 00473D10 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 8 | 004A9890 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 9 | 004D24A0 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 10 | 004D2510 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 11 | 004D27D0 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 12 | 004D2810 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 13 | 004D4200 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 14 | 004D4280 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |
| 15 | 004D4B20 | PASS | `（D-47(A) 裁决：槽位占用即 ④，§12.3 对该形态让位，见 R14_COMMON §12.4 与 PANEL 对应披露）` |

### §E 归一化分组（同组=同 vt 同 class 的行，属「事实相同」）

- 0045A560, 0045A610
- 0045A680, 0045A730
- 00473BA0, 00473C50, 00473D10
- 004D24A0, 004D2510, 004D27D0, 004D2810
- 004D4200, 004D4280

（entry 归一化后重复组：无）
