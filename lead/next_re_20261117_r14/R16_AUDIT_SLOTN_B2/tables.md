# R16-AUDIT-SLOTN-B2 · 机械生成的逐行证据表

> 由 `verify.py` 生成，勿手改。所有数值均来自脚本对 `gamemd.exe` / `coverage.tsv` / `delta.tsv` 的只读实测。

## 基线

| 对象 | 实测 |
|---|---|
| `ra2youli\gamemd.exe` | 4825360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` |
| `COVERAGE\coverage.tsv` | 4026555 B，SHA-256 `C269720F59C07845250A81CA8C6562F62260C1C9ECFC99F160E72F80F58144A5` |
| `R16_SLOTN_B2\delta.tsv` | 13254 B，SHA-256 `DC2E8A87468F3ED52FCFEE37D726F2E05F1EF19504B64E2F959811BA0E2775E2` |

## §A 最小改动（原第 4 列严格前缀 + 其余 6 列逐字节）

| # | entry | coverage 行号 | 原第4列 B | 原句末 | 追加 B | 追加首字符 | 严格前缀 | 其余6列 | 判 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 004D4CB0 | 3144 | 301 | 。 | 483 | ； | True | True | PASS |
| 2 | 004D4DC0 | 3145 | 318 | 。 | 467 | ； | True | True | PASS |
| 3 | 004D5070 | 3146 | 323 | 。 | 467 | ； | True | True | PASS |
| 4 | 004D5350 | 3147 | 317 | 。 | 467 | ； | True | True | PASS |
| 5 | 004D6AA0 | 3152 | 335 | 。 | 467 | ； | True | True | PASS |
| 6 | 004D9290 | 3163 | 310 | 。 | 467 | ； | True | True | PASS |
| 7 | 004DA2C0 | 3185 | 313 | 。 | 467 | ； | True | True | PASS |
| 8 | 004DDF90 | 3226 | 303 | 。 | 483 | ； | True | True | PASS |
| 9 | 0051F3E0 | 4446 | 322 | 。 | 483 | ； | True | True | PASS |
| 10 | 0053C6A0 | 4982 | 189 | 。 | 563 | ； | True | True | PASS |
| 11 | 005514B0 | 5286 | 188 | 。 | 583 | ； | True | True | PASS |
| 12 | 00551560 | 5287 | 161 | 。 | 583 | ； | True | True | PASS |
| 13 | 00557090 | 5387 | 170 | 。 | 563 | ； | True | True | PASS |
| 14 | 00557140 | 5388 | 150 | 。 | 563 | ； | True | True | PASS |
| 15 | 005B2FD0 | 6118 | 405 | 。 | 483 | ； | True | True | PASS |

## §B 六项实测值

| # | entry | slot | ①u32(vt+slot*4) | ②u32(vt-4)=COL | ③u32(COL+4)=offset | ④u32(COL+12)=TD | ⑤cstr(TD+8) | ⑥装表点解码 | 6/6 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 004D4CB0 | 134 | `004D4CB0` | `007FB4C0` | `0` | `00817B90` | `.?AVAircraftClass@@` | `mov dword ptr [esi], 0x7e22a4` | 6 |
| 2 | 004D4DC0 | 132 | `004D4DC0` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` | 6 |
| 3 | 004D5070 | 135 | `004D5070` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` | 6 |
| 4 | 004D5350 | 138 | `004D5350` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` | 6 |
| 5 | 004D6AA0 | 136 | `004D6AA0` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` | 6 |
| 6 | 004D9290 | 144 | `004D9290` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` | 6 |
| 7 | 004DA2C0 | 140 | `004DA2C0` | `00800948` | `0` | `00817B78` | `.?AVFootClass@@` | `mov dword ptr [esi], 0x7e8c94` | 6 |
| 8 | 004DDF90 | 150 | `004DDF90` | `007FB4C0` | `0` | `00817B90` | `.?AVAircraftClass@@` | `mov dword ptr [esi], 0x7e22a4` | 6 |
| 9 | 0051F3E0 | 132 | `0051F3E0` | `008033B8` | `0` | `00825508` | `.?AVInfantryClass@@` | `mov dword ptr [esi], 0x7eb058` | 6 |
| 10 | 0053C6A0 | 2 | `0053C6A0` | `008047B8` | `0` | `00828000` | `.?AV?$DynamicVectorClass@PBVAnimClass@@@@` | `mov dword ptr [0xa9fa60], 0x7ebfcc` | 6 |
| 11 | 005514B0 | 2 | `005514B0` | `00804DF0` | `0` | `00829710` | `.?AV?$DynamicVectorClass@PAVLaserDrawClass@@@@` | `mov dword ptr [0xabc878], 0x7ecedc` | 6 |
| 12 | 00551560 | 4 | `00551560` | `00804DF0` | `0` | `00829710` | `.?AV?$DynamicVectorClass@PAVLaserDrawClass@@@@` | `mov dword ptr [0xabc878], 0x7ecedc` | 6 |
| 13 | 00557090 | 2 | `00557090` | `008051A8` | `0` | `00829D78` | `.?AV?$DynamicVectorClass@PAVLineTrail@@@@` | `mov dword ptr [0xabcb78], 0x7ed0cc` | 6 |
| 14 | 00557140 | 4 | `00557140` | `008051A8` | `0` | `00829D78` | `.?AV?$DynamicVectorClass@PAVLineTrail@@@@` | `mov dword ptr [0xabcb78], 0x7ed0cc` | 6 |
| 15 | 005B2FD0 | 124 | `005B2FD0` | `008033B8` | `0` | `00825508` | `.?AVInfantryClass@@` | `mov dword ptr [esi], 0x7eb058` | 6 |

## §B 辅助：体内/体外、独立枚举活表、装表点全集

| # | entry | 宿主 body | site 体内/entry 体外 | 同槽活表（独立枚举） | 该 vt 装表点全集 | 宿主内唯一写入 |
|---|---|---|---|---|---|---|
| 1 | 004D4CB0 | `[00413D20,00413EB1)` | True | 007F5C70/UnitClass,007EB058/InfantryClass,007E8C94/FootClass,007E22A4/AircraftClass | 00413D87, 0041408A, 0041B4E1 | True |
| 2 | 004D4DC0 | `[004D31E0,004D353C)` | True | 007E8C94/FootClass | 004D345D, 004D3568, 004D359D | True |
| 3 | 004D5070 | `[004D31E0,004D353C)` | True | 007E8C94/FootClass | 004D345D, 004D3568, 004D359D | True |
| 4 | 004D5350 | `[004D31E0,004D353C)` | True | 007E8C94/FootClass | 004D345D, 004D3568, 004D359D | True |
| 5 | 004D6AA0 | `[004D31E0,004D353C)` | True | 007E8C94/FootClass | 004D345D, 004D3568, 004D359D | True |
| 6 | 004D9290 | `[004D31E0,004D353C)` | True | 007F5C70/UnitClass,007EB058/InfantryClass,007E8C94/FootClass | 004D345D, 004D3568, 004D359D | True |
| 7 | 004DA2C0 | `[004D31E0,004D353C)` | True | 007F5C70/UnitClass,007EB058/InfantryClass,007E8C94/FootClass | 004D345D, 004D3568, 004D359D | True |
| 8 | 004DDF90 | `[00413D20,00413EB1)` | True | 007F5C70/UnitClass,007EB058/InfantryClass,007E8C94/FootClass,007E22A4/AircraftClass | 00413D87, 0041408A, 0041B4E1 | True |
| 9 | 0051F3E0 | `[00517A50,00517BF7)` | True | 007EB058/InfantryClass | 00517ACC, 00517D9D, 00521A11 | True |
| 10 | 0053C6A0 | `[00539580,005395BD)` | True | 007EBFCC/?$DynamicVectorClass@PBVAnimClass@@ | 0053959D, 0053963D, 005396DD | True |
| 11 | 005514B0 | `[0054FDC0,0054FDFD)` | True | 007ECEDC/?$DynamicVectorClass@PAVLaserDrawClass@@ | 0054FDDD | True |
| 12 | 00551560 | `[0054FDC0,0054FDFD)` | True | 007ECEDC/?$DynamicVectorClass@PAVLaserDrawClass@@ | 0054FDDD | True |
| 13 | 00557090 | `[005569A0,005569DD)` | True | 007ED0CC/?$DynamicVectorClass@PAVLineTrail@@ | 005569BD | True |
| 14 | 00557140 | `[005569A0,005569DD)` | True | 007ED0CC/?$DynamicVectorClass@PAVLineTrail@@ | 005569BD | True |
| 15 | 005B2FD0 | `[00517D90,00517F95)` | True | 007F5C70/UnitClass,007F4960/TechnoClass,007F0508/RadioClass,007EDCC0/MissionClass,007EB058/InfantryClass,007E8C94/FootClass,007E3EBC/BuildingClass | 00517ACC, 00517D9D, 00521A11 | True |

## §D 文本与事实一致

| # | entry | 行名 | addr | slot 自洽 | <Class>=行名前缀 | <Class>↔TD+8 | 有 D-47 句 | 指 §12.6 | 判 | 备注 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 004D4CB0 | AircraftClass::slot134 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 2 | 004D4DC0 | FootClass::slot132 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 3 | 004D5070 | FootClass::slot135 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 4 | 004D5350 | FootClass::slot138 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 5 | 004D6AA0 | FootClass::slot136 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 6 | 004D9290 | FootClass::slot144 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 7 | 004DA2C0 | FootClass::slot140 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 8 | 004DDF90 | AircraftClass::slot150 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 9 | 0051F3E0 | InfantryClass::slot132 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 10 | 0053C6A0 | T_DynamicVectorClass_PBVAnimClass__::slot2 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 11 | 005514B0 | T_DynamicVectorClass_PAVLaserDrawClass__::slot2 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 12 | 00551560 | T_DynamicVectorClass_PAVLaserDrawClass__::slot4 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 13 | 00557090 | T_DynamicVectorClass_PAVLineTrail__::slot2 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 14 | 00557140 | T_DynamicVectorClass_PAVLineTrail__::slot4 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |
| 15 | 005B2FD0 | InfantryClass::slot124 | True | True | True | True | True | False | FAIL | 披露指针未指 §12.6（本行写的是 §12.4，已过时编号） |

## §E 骨架归一（先例 3 条）

```text
④ 活表槽位见证：<CLS>::slot<N>（vt=<H>，槽 <N> 值=<H>，COL=<H> offset=<N>，RTTI=<H>→<MAN>；装表点 <H> 位于 <H> 体内，entry 体外） ④升级句：<CLS>::slot<N>（④ 表属类与行名类一致，均为 <CLS>；该槽即其 vt=<H> 表 slot<N>，无归属歧义）
```

| # | entry | 骨架子=先例 |
|---|---|---|
| 1 | 004D4CB0 | True |
| 2 | 004D4DC0 | True |
| 3 | 004D5070 | True |
| 4 | 004D5350 | True |
| 5 | 004D6AA0 | True |
| 6 | 004D9290 | True |
| 7 | 004DA2C0 | True |
| 8 | 004DDF90 | True |
| 9 | 0051F3E0 | True |
| 10 | 0053C6A0 | True |
| 11 | 005514B0 | True |
| 12 | 00551560 | True |
| 13 | 00557090 | True |
| 14 | 00557140 | True |
| 15 | 005B2FD0 | True |

## §F 归一化分组

- (i) 仅归一 entry：15 条互异，重复组 0
- (ii) 全 8 位十六进制归一：15 条互异，重复组 0
- (iii) 再归一槽号（最严）：同组 5 组
  - [1, 8]
  - [2, 3, 4, 5, 6, 7]
  - [9, 15]
  - [11, 12]
  - [13, 14]
