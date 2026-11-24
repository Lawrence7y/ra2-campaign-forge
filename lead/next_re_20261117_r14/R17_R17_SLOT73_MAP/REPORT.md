D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe | sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# R17-R17-SLOT73-MAP · 报告

## 范围与读取

- SHA256 前缀 `73201CC0` 与期望 `73201CC0` 一致。
- 类名只读沿用 `R17_R15_SLOT73\class_index.tsv`；本次未修改该目录。
- 索引中槽数≥108的vtable共 `21` 个；槽#73/#107共 `42` 个4字节值 = `168` bytes。
- 槽值数据读取限于 `.rdata`：RVA `0x003E1000`，raw字节数 `200704`；所有槽地址均落在该节。整文件sha256只用于身份校验。
- 不建进程、不调试、不启动gamemd；未做大范围反汇编。

## Q1 · 全量反向映射

42/42 个槽读取均有值；按值分成 18 组。四个指定函数完整清单：

| 函数值 | 命中数 | 完整反向清单（类名来自索引） |
|---|---:|---|
| `0x0043F180` | 1 | .?AVBuildingClass@@ @ 0x007E3EBC 槽73 |
| `0x00449440` | 1 | .?AVBuildingClass@@ @ 0x007E3EBC 槽107 |
| `0x004D3780` | 4 | .?AVAircraftClass@@ @ 0x007E22A4 槽73<br>.?AVFootClass@@ @ 0x007E8C94 槽73<br>.?AVInfantryClass@@ @ 0x007EB058 槽73<br>.?AVUnitClass@@ @ 0x007F5C70 槽73 |
| `0x006F4A70` | 1 | .?AVTechnoClass@@ @ 0x007F4960 槽73 |

### 全部值分组

### `0x004196B0`（1 项）
- `.?AVAircraftClass@@` @ `0x007E22A4` 槽 107

### `0x004238B0`（1 项）
- `.?AVAnimClass@@` @ `0x007E3354` 槽 73

### `0x004264C0`（15 项）
- `.?AVAnimClass@@` @ `0x007E3354` 槽 107
- `.?AVBuildingLightClass@@` @ `0x007E3AD0` 槽 107
- `.?AVBulletClass@@` @ `0x007E46E4` 槽 107
- `.?AVIsometricTileClass@@` @ `0x007EC258` 槽 107
- `.?AVMissionClass@@` @ `0x007EDCC0` 槽 107
- `.?AVObjectClass@@` @ `0x007EF060` 槽 107
- `.?AVOverlayClass@@` @ `0x007EF3D4` 槽 107
- `.?AVParticleClass@@` @ `0x007EF954` 槽 107
- `.?AVParticleSystemClass@@` @ `0x007EFB9C` 槽 107
- `.?AVRadioClass@@` @ `0x007F0508` 槽 107
- `.?AVSmudgeClass@@` @ `0x007F32FC` 槽 107
- `.?AVTechnoClass@@` @ `0x007F4960` 槽 107
- `.?AVVoxelAnimClass@@` @ `0x007F6318` 槽 107
- `.?AVVeinholeMonsterClass@@` @ `0x007F66A8` 槽 107
- `.?AVWaveClass@@` @ `0x007F6BF4` 槽 107

### `0x0043F180`（1 项）
- `.?AVBuildingClass@@` @ `0x007E3EBC` 槽 73

### `0x00449440`（1 项）
- `.?AVBuildingClass@@` @ `0x007E3EBC` 槽 107

### `0x004666C0`（1 项）
- `.?AVBulletClass@@` @ `0x007E46E4` 槽 73

### `0x004D3780`（4 项）
- `.?AVAircraftClass@@` @ `0x007E22A4` 槽 73
- `.?AVFootClass@@` @ `0x007E8C94` 槽 73
- `.?AVInfantryClass@@` @ `0x007EB058` 槽 73
- `.?AVUnitClass@@` @ `0x007F5C70` 槽 73

### `0x004D9C10`（1 项）
- `.?AVFootClass@@` @ `0x007E8C94` 槽 107

### `0x0051BF90`（1 项）
- `.?AVInfantryClass@@` @ `0x007EB058` 槽 107

### `0x00543330`（1 项）
- `.?AVIsometricTileClass@@` @ `0x007EC258` 槽 73

### `0x005F5850`（8 项）
- `.?AVBuildingLightClass@@` @ `0x007E3AD0` 槽 73
- `.?AVMissionClass@@` @ `0x007EDCC0` 槽 73
- `.?AVObjectClass@@` @ `0x007EF060` 槽 73
- `.?AVParticleSystemClass@@` @ `0x007EFB9C` 槽 73
- `.?AVRadioClass@@` @ `0x007F0508` 槽 73
- `.?AVVoxelAnimClass@@` @ `0x007F6318` 槽 73
- `.?AVVeinholeMonsterClass@@` @ `0x007F66A8` 槽 73
- `.?AVWaveClass@@` @ `0x007F6BF4` 槽 73

### `0x005FC570`（1 项）
- `.?AVOverlayClass@@` @ `0x007EF3D4` 槽 73

### `0x0062D6F0`（1 项）
- `.?AVParticleClass@@` @ `0x007EF954` 槽 73

### `0x006B4BE0`（1 项）
- `.?AVSmudgeClass@@` @ `0x007F32FC` 槽 73

### `0x006F4A70`（1 项）
- `.?AVTechnoClass@@` @ `0x007F4960` 槽 73

### `0x0071BFB0`（1 项）
- `.?AVTerrainClass@@` @ `0x007F522C` 槽 73

### `0x0071C4D0`（1 项）
- `.?AVTerrainClass@@` @ `0x007F522C` 槽 107

### `0x0073F0A0`（1 项）
- `.?AVUnitClass@@` @ `0x007F5C70` 槽 107

## Q2 · FootClass 补齐与四类并排

`.?AVFootClass@@` 主vtable `0x007E8C94`（341槽）：**#73 = `0x004D3780`；#107 = `0x004D9C10`**。

| 类名 | 主 vtable | 槽数 | #73 | #107 | 主vtable+0x124 |
|---|---:|---:|---:|---:|---:|
| `.?AVAircraftClass@@` | `0x007E22A4` | 341 | `0x004D3780` | `0x004196B0` | `0x007E23C8` |
| `.?AVFootClass@@` | `0x007E8C94` | 341 | `0x004D3780` | `0x004D9C10` | `0x007E8DB8` |
| `.?AVInfantryClass@@` | `0x007EB058` | 343 | `0x004D3780` | `0x0051BF90` | `0x007EB17C` |
| `.?AVUnitClass@@` | `0x007F5C70` | 344 | `0x004D3780` | `0x0073F0A0` | `0x007F5D94` |

## Q3 · 与外部线索对账

外部线索 D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv：
```text
004D3780	S12	MobileClass::SetOccupation_shared	shared slot73 for RTTI Aircraft/Foot/Infantry/Unit; no 0x47C620 caller	[已证]	S12-K2/EVIDENCE/t4_rtti_getsize.txt;S12-K2/EVIDENCE/t2_all_attach_paths.txt;M82 指针修复：原记 EVIDENCE/t4_rtti_getsize.txt;EVIDENCE/t2_all_attach_paths.txt（缺卡目录），实为 S12-K2/EVIDENCE/t4_rtti_getsize.txt;S12-K2/EVIDENCE/t2_all_attach_paths.txt	2	0
```

| 类名 | 算式 | 外部地址 | 是否相等 |
|---|---|---:|---|
| `.?AVAircraftClass@@` | `0x007E22A4` + 0x124 = `0x007E23C8` | `0x007E23C8` | 相等 |
| `.?AVFootClass@@` | `0x007E8C94` + 0x124 = `0x007E8DB8` | `0x007E8DB8` | 相等 |
| `.?AVInfantryClass@@` | `0x007EB058` + 0x124 = `0x007EB17C` | `0x007EB17C` | 相等 |
| `.?AVUnitClass@@` | `0x007F5C70` + 0x124 = `0x007F5D94` | `0x007F5D94` | 相等 |

结论：**外部线索与本次独立字节分析一致**。

## Q4 · 结论措辞

1. `0x0043F180` 仅命中 `.?AVBuildingClass@@` 主表#73；`0x00449440` 命中该主表#107。
2. `0x004D3780` 仅命中 `.?AVAircraftClass@@`、`.?AVFootClass@@`、`.?AVInfantryClass@@`、`.?AVUnitClass@@` 主表#73，各1项；其余类没有命中。
3. 可直接引用：**在本次索引覆盖且槽数≥108的21个主vtable中，槽73上：`.?AVBuildingClass@@` 使用 `0x0043F180`，`.?AVTechnoClass@@` 使用 `0x006F4A70`，`.?AVAircraftClass@@`、`.?AVFootClass@@`、`.?AVInfantryClass@@`、`.?AVUnitClass@@` 共用 `0x004D3780`。**

> 类名逐字取自索引；索引未给出则写“未取得”。适用范围限于本次索引覆盖且槽数≥108的vtable。

## 产物

- `REPORT.md`
- `reverse_map.tsv`
- `four_classes.tsv`
- `work.py`