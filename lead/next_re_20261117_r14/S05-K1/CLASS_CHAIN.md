# S05-K1 · CLASS_CHAIN.md — 对象模型核心继承链全量恢复（T1）

> 卡号 S05-K1｜2026-11-17｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读）
> 类名只认 RTTI TypeDescriptor：链 `vtable[-1]=COL → COL+0xC=TD → TD+8=name`。读不到即 fail-closed，不猜名。
> 槽数**从 `.rdata` 定界**（表尾首个非 `.text` 槽值），不用 atlas 边界反推；与 `classes_meta.json` 槽数 10/10 吻合（独立复算见 `work/recover_class_chain.py`）。
> 父类从 CHD（ClassHierarchyDescriptor，`COL+0x10`）的 `base[1]` 读，非按名猜测。base[0]=自身、base[1]=直接主基类、其后为接口/次基类。

## 0. 类名/继承链结论表（10 类，RTTI 全命中）

| 类名(RTTI) | TD | COL | vtable 基址 | 槽数(.rdata) | 父类(CHD base[1]) | GetSize(imm) | WhatAmI | 构造器地址 | 初始化点(写 vptr 指令) | 分级 |
|---|---|---|---|---:|---|---|---|---|---|---|
| `AbstractClass` | 0x8177C8 | 0x7FB118 | 0x7E1F50 | 24 | (根；base[1]=`IPersistStream` 接口) | 桩 0x4C9150→0 | 桩→0 | 0x410170 / 0x4101C0 / 0x4101F0 / 0x4105A0(析构) | 0x410198,0x4101D0,0x4101F0,0x4105A9,0x6E803F | [已证] |
| `ObjectClass` | 0x817AF8 | 0x807448 | 0x7EF060 | 122 | `AbstractClass` | 桩 0x4C9150→0 | 桩→0 | 0x5F3900 / 0x5F3B50 / 0x5F3B80 | 0x5F39BA,0x5F3B5D,0x5F3B87 | [已证] |
| `MissionClass` | 0x817B18 | 0x805D28 | 0x7EDCC0 | 157 | `ObjectClass` | 桩 0x4C9150→0 | 桩→0 | (本卡未逐条定位；抽象基类) | — | [已证]链/[静态推断]ctor |
| `RadioClass` | 0x817B38 | 0x808590 | 0x7F0508 | 161 | `MissionClass` | 桩 0x4C9150→0 | 桩→0 | (本卡未逐条定位；抽象基类) | — | [已证]链/[静态推断]ctor |
| `TechnoClass` | 0x817B58 | 0x80C058 | 0x7F4960 | 309 | `RadioClass` | 桩 0x4C9150→0 | 桩→0 | 0x6F2B40 / 0x6F4300 / 0x6F4500 | 0x6F3130,0x6F4413,0x6F450D | [已证] |
| `FootClass` | 0x817B78 | 0x800948 | 0x7E8C94 | 341 | `TechnoClass` | 桩 0x4C9150→0 | 桩→0 | 0x4D31E0 / 0x4D3540 / 0x4D3590 | 0x4D345D,0x4D3568,0x4D359D | [已证] |
| `BuildingClass` | 0x818D60 | 0x7FC360 | 0x7E3EBC | 322 | `TechnoClass` | **0x720 (1824)** | 0x6 `Building` | 0x43B740（分配点 0x44FAF8 `push 0x720`） | 0x43B71F,0x43B9FA,0x43BCFD | [已证] |
| `UnitClass` | 0x842D80 | 0x80CC68 | 0x7F5C70 | 344 | `FootClass` | **0x8E8 (2280)** | 0x1 `Unit` | 0x7353C0（分配点 0x449E16 `push 0x8E8`） | 0x73543A,0x735794,0x744521 | [已证] |
| `InfantryClass` | 0x825508 | 0x8033B8 | 0x7EB058 | 343 | `FootClass` | **0x6F0 (1776)** | 0xF `Infantry` | 0x517A50（分配点 0x4430C2 `push 0x6F0`） | 0x517ACC,0x517D9D,0x521A11 | [已证] |
| `AircraftClass` | 0x817B90 | 0x7FB4C0 | 0x7E22A4 | 341 | `FootClass` | **0x6D8 (1752)** | 0x2 `Aircraft` | 0x413D20（分配点 0x41B1B4 `push 0x6D8`） | 0x413D87,0x41408A,0x41B4E1 | [已证] |

**继承链（RTTI CHD 实测，非任务书中的名义链）**：
`AbstractClass → ObjectClass → MissionClass → RadioClass → TechnoClass → {BuildingClass | FootClass → {UnitClass, InfantryClass, AircraftClass}}`
⚠️ 任务书骨架写 `ObjectClass → TechnoClass`，实际 CHD 显示中间还有 `MissionClass` 与 `RadioClass` 两层——本卡按 RTTI 实测插入，不按名字猜（纪律 §8.1④）。

## 1. 槽数定界证据（`.rdata`，10/10）

每个 vtable 从 `vt[0]` 逐槽读 dword，连续落在 `.text` 的即函数槽，首个非 `.text` 值即表尾：
- `AbstractClass` vt+0x60=`0x7FB160`（`.rdata` COL 指针）→ 24 槽。与 `kb/22 §4.1` 一致。
- `FootClass` vt+0x554=`0x8009B0`（`.rdata` COL）→ 341 槽。
- `BuildingClass` vt+0x508=`0x7FC298`（`.rdata` COL）→ 322 槽。
- `UnitClass` vt+0x560=`0x0` → 344 槽；`InfantryClass` vt+0x55C=`0x0` → 343 槽；`AircraftClass` vt+0x554=`0x0` → 341 槽。
- `ObjectClass` vt+0x1E8=`0x66666666`（`.rdata` 浮点常量）→ 122 槽；`TechnoClass` vt+0x4D4=`0x3C23D70A`（`.rdata` 浮点常量）→ 309 槽。此二者表尾是常量数据而非 COL，仍是合法表间边界。
- 全部与 `re_atlas/evidence/rtti/classes_meta.json` 的 `slots` 字段 10/10 一致（该字段由同一 `.rdata` 扫描得来，属旁证非独立通道；**独立**证据是本节逐槽字节 + `vtables_v2.json` 已知少末槽错，见 DISAGREE.md）。

## 2. GetSize 双向核对（T2，本卡核心数字）

`v[12]` 取 `B8 <imm32> C3`；第二通道为 `push <size> ; call 0x7C8E17(operator new) ; add esp,4 ; … ; mov ecx,eax ; call <ctor>`。两处独立对上才算闭合。

| 类 | 通道1 v[12] imm | 通道2 `push imm` 分配点 | 构造器（vptr 写入属主） | `ecx=eax` 证据 | 结论 |
|---|---|---|---|---|---|
| BuildingClass | 0x720 | 0x44FAF8 `push 0x720` → 0x7C8E17 | 0x43B740（写 0x7E3EBC @0x43B9FA） | 0x44FB1F `mov ecx,eax` → 0x44FB22 call | **闭合** |
| UnitClass | 0x8E8 | 0x449E16 `push 0x8E8` → 0x7C8E17 | 0x7353C0（写 0x7F5C70 @0x73543A） | 0x449E42 → 0x449E44 call | **闭合** |
| InfantryClass | 0x6F0 | 0x4430C2 `push 0x6F0` → 0x7C8E17 | 0x517A50（写 0x7EB058 @0x517ACC） | 0x430DB → 0x430DD call | **闭合** |
| AircraftClass | 0x6D8 | 0x41B1B4 `push 0x6D8` → 0x7C8E17 | 0x413D20（写 0x7E22A4 @0x413D87） | 0x41B1D6 → 0x41B1D9 call | **闭合** |

**双向核对通过 4/4 具体类。** 6 个抽象中间基类 GetSize=桩 0x4C9150（`xor eax,eax; ret`，字节 `33 C0 C3`），自身从不实例化 ⇒ 无分配点，属"不可比"，不计入失败（与 `kb/20 §0.2 作用域修正` 的 9 个抽象桩类口径一致）。

`operator new=0x7C8E17` 由 41 个不同 `push <size>` 站点的首 call 直方图确定（其余 4 个 `0x4068E0` 是另一分配器、3 个其它）；其体 `push 1; push [esp+8]; call 0x7C9442; pop;pop;ret` 是标准 new 转发。

## 3. 反向一致性检查（继承链 vs GetSize 单调性）

抽象基类 GetSize 恒 0（桩）， concrete 类须各自 > 前缀且随继承加深非递减。实测：
- BuildingClass(直接从 TechnoClass 派生) = 1824 < UnitClass(从 FootClass 派生) = 2280；符合"FootClass 派生链追加 Locomotor/移动字段"预期。
- InfantryClass = 1776、AircraftClass = 1752，均 < UnitClass 2280，符合三者同为 FootClass 直接子类、各自追加不同移动/战斗字段。
- **未发现矛盾**：无"子类 GetSize < 父类已证最大字段"情形（见 LAYOUT.md §T4 自检）；BuildingClass 1824 > TechnoClass 已证最大字段 +0x21C+4=0x220，余量充足。
- 唯一需说明：抽象基类桩返回 0 不是"尺寸 0"，不能用 `派生尺寸-基类尺寸` 算追加区（`kb/11 §0.1` 已警告）。

## 4. 证据文件
- `EVIDENCE/class_chain_core.json`：10 类 RTTI/TD/COL/槽数/v11/v12/CHD 全字段
- `EVIDENCE/vtable_write_sites.json`：C7 05 批量通道 + 基线 + 各 vt 写点
- `EVIDENCE/getsize_alloc_sites.json`：`push <size>` 站点 + 首 call 直方图
- `EVIDENCE/ctor_association.txt` / `alloc_disasm.txt`：逐站反汇编（`ecx=eax → call ctor`）
- `EVIDENCE/trap_verification.txt`：+0x80 / +0x94 两个已知陷阱站点核验
- 复跑：`python work/recover_class_chain.py`（类名一键全量）、`python work/scan_sites.py`、`python work/find_alloc_sites.py`
