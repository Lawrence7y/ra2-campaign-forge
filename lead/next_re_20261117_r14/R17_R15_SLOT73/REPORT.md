D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe | sha256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476

# 卡 R17-R15-SLOT73 · 报告

## 结论先行

`0x43F180` 与 `0x449440` 为 **BuildingClass 专有**（本卡 RTTI 索引覆盖的 1211 个 `.?AV*` vtable 中，只有 BuildingClass 主表的 #73/#107 命中；未取得项 0）。

R14_COMMON §2.6 的「所有 TechnoClass 派生可放置对象……共用」只针对 `+0x14` 的 **bit0** 与唯一写点 `0x6F322F`，**不适用于这两个 vtable 函数**；本处措辞必须加 BuildingClass 限定。

## 静态范围与方法

- 镜像：D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe
- sha256：73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476（前缀 73201CC0 校验通过）
- 扫描：.rdata raw 0x31000 = 200704 bytes（COL 与 vtable[-4] 引用）；.data raw 0x6c000 = 442368 bytes（TypeDescriptor 内联名）；合计 643072 bytes。
- 只读：未建进程、未调试、未启动 gamemd；仅读 4 字节槽值及 COL/TD 小结构，未做大规模反汇编。
- 索引方法：扫 .data 中 TD+8 内联名 `.?AV*`；扫 .rdata 中 COL(+12→TD, +16→ClassDescriptor)；扫 .rdata 对齐 dword 中指向 COL 的引用，引用地址 +4 即 vtable 基址。槽数 = 从 vtable 基址起连续落在 .text raw VA 区间 `[0x00401000, 0x007E1000)` 的 4 字节函数指针数。

## 第 1 步 · 类名 → 全部 vtable 索引

索引规模：**1211 个 vtable / 951 个不同类名**（仅 `.?AV*` 类 RTTI；TD 候选 961 个，其中 951 个有 vtable 引用）。

5 个目标类名按字节逐字如下（TD 内联名，非转写）：

| 类名（逐字） | 全部 vtable 基址 / 槽数 | 主表 |
|---|---|---|
| `.?AVBuildingClass@@` | 0x007E3E90 (1)<br>0x007E3E98 (1)<br>0x007E3EA0 (6)<br>0x007E3EBC (322) | 0x007E3EBC (322) |
| `.?AVTechnoClass@@` | 0x007F4934 (1)<br>0x007F493C (1)<br>0x007F4944 (6)<br>0x007F4960 (309) | 0x007F4960 (309) |
| `.?AVInfantryClass@@` | 0x007EB02C (1)<br>0x007EB034 (1)<br>0x007EB03C (6)<br>0x007EB058 (343) | 0x007EB058 (343) |
| `.?AVUnitClass@@` | 0x007F5C44 (1)<br>0x007F5C4C (1)<br>0x007F5C54 (6)<br>0x007F5C70 (344) | 0x007F5C70 (344) |
| `.?AVAircraftClass@@` | 0x007E2250 (9)<br>0x007E2278 (1)<br>0x007E2280 (1)<br>0x007E2288 (6)<br>0x007E22A4 (341) | 0x007E22A4 (341) |

完整 1211 行索引见 `class_index.tsv`。

## 第 2 步 · 主 vtable 的 #73 / #107 对比

| 类名 | 主 vtable | 槽数 | slot #73 | slot #107 | 是否等于 0x43F180 / 0x449440 |
|---|---:|---:|---:|---:|---|
| `.?AVBuildingClass@@` | 0x007E3EBC | 322 | 0x0043F180 | 0x00449440 | 是 / 是 |
| `.?AVTechnoClass@@` | 0x007F4960 | 309 | 0x006F4A70 | 0x004264C0 | 否 / 否 |
| `.?AVInfantryClass@@` | 0x007EB058 | 343 | 0x004D3780 | 0x0051BF90 | 否 / 否 |
| `.?AVUnitClass@@` | 0x007F5C70 | 344 | 0x004D3780 | 0x0073F0A0 | 否 / 否 |
| `.?AVAircraftClass@@` | 0x007E22A4 | 341 | 0x004D3780 | 0x004196B0 | 否 / 否 |

全部有 #73/#107 的索引 vtable 中命中目标函数的条目数：1；明细：.?AVBuildingClass@@@0x007E3EBC。

## 第 3 步 · 判定与措辞建议

1. 只有 BuildingClass 主表 `0x7E3EBC` 的 #73 = `0x43F180`、#107 = `0x449440`。
2. TechnoClass / InfantryClass / UnitClass / AircraftClass 的主表这两个槽均不等于目标函数；三者 #73 同为 `0x4D3780`，但不是 `0x43F180`，不得据此写「共用本函数」。
3. 五个目标类的主表槽数均 ≥108，不存在「槽不存在」项；未取得项数 = 0。
4. 建议将本处写成：**`0x43F180` 与 `0x449440` 是 BuildingClass 专有；R14_COMMON §2.6 的「所有 TechnoClass 派生可放置对象共用」仅指 bit0 写点，不可外推到这两个 vtable 槽。**

## 产物

- `REPORT.md`：本报告
- `class_index.tsv`：类名 → 全部 vtable（1211 行）
- `slot73_107.tsv`：5 个目标类主表槽值
- `work.py`：可复跑脚本
