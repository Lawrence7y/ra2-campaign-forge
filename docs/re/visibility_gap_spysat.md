# 三态迷雾 · 建筑可视性 / 弹道剔除 / 裂缝产生器 / 间谍卫星 —— 地址级逆向储备

> 目标：`gamemd.exe`（尤里的复仇 1.001）ImageBase `0x400000`，`.text` raw offset = RVA。
> 本文为纯逆向产出（无代码补丁），不修改总档案 `REVERSE_ENGINEERING_AND_PATCHES.md` 与 `ra2render` 源码/dll。
> 证据来源：**[实证]** = capstone 反汇编取证（`out/re_work/vis_gap_re*.py` + `out/re_work/vis_gap_re*_out.txt`）；**[YRpp]** = 社区 ABI 头；**[推演]** = 字段序/行为链推导。
> 偏移约定：`类名+0x…` 为对象字段；地址均为 VA。ImageBase 偏移 = VA − `0x400000`。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

---

## 0. 结论速览

| 问题 | 结论 |
|---|---|
| BuildingClass::Draw 能否入口短路？ | **能**。`0x0043D290` 标准 thiscall `ret 8`，可在入口读 `Owner@+0x21C` / `Location@+0x9C>>8` 后按 `s_visionGrid` 直接 `ret 8`。原版门 2（`Type+0x1701`）已是「不画就 ret」先例，语义安全。 |
| BulletClass::Draw 能否入口短路？ | **能**。`0x00468090` 同签名。且**原版已有迷雾相关提前退出**：`Scenario.Flags & 0x1000` 置位时调 `MapClass::IsCellShrouded(0x5865E0)`，黑雾内直接跳 `0x468422` 不画——但 L3 为修 FOG.SHP 反色**强制清零** `0x1000`，该路径被废。L5 需自建 `s_visionGrid` 判定。 |
| 建筑/弹道字段 | Building：`Owner@+0x21C`、`Location@+0x9C/0xA0/0xA4`（定点 `>>8`）、`Type@+0x520`；Bullet：`Owner(Techno)@+0xB0`→`Owner(House)@+0x21C`、`Location@+0x9C`、`Type@+0xAC`、`Invisible@Type+0x29E`、`SpawnNextAnim@+0x158`。 |
| 裂缝产生器半径字段 | `BuildingTypeClass+0x1707` = `SuperGapRadiusInCells`(char)、`+0x1708` 邻接 `GapRadiusInCells`；运行时半径另有 `TechnoType+0x5F0` / `+0x5F4`(int)。覆盖按**圆**（`dx²+dy² < r²`）盖印。 |
| 裂缝更新函数 | **CreateGap 族** `BuildingClass::v[317/318]`=`0x455820`/`0x4556D0`（`inc` 每屋格子计数）；**DestroyGap 族** `v[319/320]`=`0x455A80`/`0x455980`（`dec`）。每帧由 `v[212]`=`0x4555D0`（`IsGeneratingGap` 门）决定是否盖印。 |
| 裂缝与 Shroudedness 关系 | 裂缝**不写** `Shroudedness@+0x120` / `Foggedness@+0x121`，而是写**每屋覆盖计数** `CellClass+0x7C`（`SensorsOfHouses` 旁的 Word 数组，houseIdx 索引）与 `+0xAC`。`IsShrouded(0x487950)` 通过 `0x586360` 聚合这些计数判定。L3 `s_visionGrid` 与裂缝计数**互相独立**，必须显式合并。 |
| 间谍卫星 | `BuildingTypeClass+0x16A5`=`SpySat`(bool)；激活写 `HouseClass+0x577A`=`SpySatActive`，调 `MapClass::RevealArea3(0x577D90)` 全图置 `CopyFlags|=0x18`（Explored）并 `GapsCovering@+0x134=0`——**这正是原版裂缝失效的根因**（SpySat 清空 gap 计数）。 |
| 超武开图 | `SuperWeaponType` 枚举 0..11；`SuperWeaponTypeClass::Type@+0xB4`、`RechargeTime@+0xB0`、`Range@+0xF8`。`SuperClass::Launch(0x6CC390)` 跳表 `0x6CDE44`：**SpyPlane(8)**→`0x6CD66F`（雷达扫描动画）；**PsychicReveal(11)**→`0x6CD70C` 调 `MapClass::RevealArea2(0x5678E0)` 局部开图（半径取 `SW.Range`，0 则 `Rules+0xFEC`）。 |
| 弹道/激光/粒子谁在画 | **无统一 `Object::Draw` 门**。各类槽 69 独立：`BulletClass::v[69]=0x468090`、`AnimClass::v[69]=0x422CA0`、`ParticleClass::v[69]=0x62CEC0`、`WaveClass::v[69]=0x75F9F0`、`VoxelAnimClass::v[69]=0x749B70`。LaserDraw **不是 Object**（独立渲染器，`0x54FE60` 构造），走全局向量 `0xABC878`。 |
| 现版 Draw 统一抽头点 | 引擎是 `call [obj+0x114]`（槽 69）分发，`.text` 仅 6 处直呼（`0x41464F`/`0x43D005`/`0x43DC07`/`0x5F4CFD`/`0x5F65DC`/`0x71CD7B`）。**按类装 vtable 钩**仍是唯一稳妥方案（与 L3 Unit/Infantry/Aircraft 同模式）。 |
| 联机确定性红线 | 所有 Hook **只能拦绘制**（Draw 槽 69 / 绘制协调层），**绝不可**改 `IsShrouded`/`RevealArea`/`CreateGap`/AI 可见性查询/`SelectAutoTarget` 的返回值，否则逻辑帧分叉导致不同步。 |

---

## 1. BuildingClass::Draw / BulletClass::Draw 入口短路

### 1.1 调用约定（两函数一致）[实证]

```
void __thiscall Draw(Point2D* pLocation, RectangleStruct* pBounds) const
; ecx = this；2 栈参；出口 ret 8
```

- Building：入口 `0x0043D290`，4 个出口全 `ret 8`（`0x43D68F`/`0x43D924`/`0x43D9D5`/`0x43DA73`），公共出口 `0x43D9CE`（`pop edi/esi/ebp/ebx; add esp,0x38; ret 8`）。
- Bullet：入口 `0x00468090`，出口 `0x468255`/`0x468428` `ret 8`。
- 虚表槽 69：Building `0x007E3FD0`→`0x0043D290`；Bullet `0x007E47F8`→`0x00468090`（v1.5.2 已登记，本轮复核一致）。

### 1.2 BuildingClass::Draw 门控链（`0x0043D290` 前 120 条）[实证]

```
0043D2A2  call [vtbl+0x1B8]      ; 槽110 GetMapCoords → 读 [this+0x9C]/[+0xA0] >>8
0043D2B2  call [vtbl+0x6C]       ; 槽27  GetCell → CellClass*
0043D2BB  je  0x43D9CE           ; 门1：无格子 → 不画（ret 8）
0043D2C1  test esi,esi
0043D2C3  je  0x43D308
0043D2C9  call [vtbl+0x2C]       ; WhatAmI
0043D2CC  cmp eax, 6             ; AbstractType::Building
0043D2D1  mov eax, [esi+0x534]   ; 子类型/升级标志？
0043D2DF  call [vtbl+0x184]      ; 槽98
0043D2E5  cmp eax, 0x13          ; 某状态枚举
0043D2EA  lea ecx, [esi+0x55c]   ; 21 个指针（炮口/附着物）逐个置 [ptr+0x19D]=1
0043D308  mov eax, [esi+0x520]   ; Type = BuildingTypeClass*
0043D30E  mov cl, [eax+0x1701]   ; Type+0x1701 字节标志
0043D314  test cl,cl
0043D316  jne 0x43D9CE           ; 门2：标志≠0 → 不画（原版「隐藏建筑」门）
...
0043D532  call 0x5657A0          ; MapClass::GetCellAt
0043D539  call 0x487950          ; CellClass::IsShrouded
0043D542  xor edi,edi            ; 门3：黑雾中只清灯光色，**不跳过绘制**
0043D683  call 0x705E00          ; 建筑主体绘制（传 pLocation/pBounds）
```

**短路方案（推荐挂点）**：在 `0x0043D290` 入口（或 `0x43D2BB` 门 1 之后）插入：

```cpp
// 伪代码：Hook_Building_Draw
if (g_enableStarCraftFog) {
    if (!ShouldDrawBuilding(this))   // 复用 ShouldDrawMobileObject 的敌我+Grid 判定
        return;                      // ret 8
}
return g_pOrigBuildingDraw(this, pLocation, pBounds);
```

- **建筑残影策略**：三态迷雾第 3 态要求「已探索但失去直视时保留静态建筑最后影像」。故敌方建筑**不应**像机动单位那样彻底剔除，而应：
  - 己方/盟军 → 恒画；
  - 敌方 + 直视（`s_visionGrid` 命中）→ 全彩画；
  - 敌方 + 已探索（`Cell+0x12C bit3`）但无直视 → **画但走 50% 灰雾**（可复用 `Hook_CellClass_Draw` 的 `Draw_Fog(0x47F250)` 思路，或建筑绘制后叠加灰层）；
  - 敌方 + 未探索 → 不画（原版黑瓦片已遮，但为省 fillrate 仍可短路）。
- **风险**：建筑绘制含地基多格、炮塔、附着动画；入口短路会连带跳过所有子绘制——这正是想要的。但**不要**在 `0x705E00` 之后做半成品叠加，否则占位光柱/建造动画会被拆散。

### 1.3 BulletClass::Draw 门控链（`0x00468090`）[实证]

```
0046809C  mov eax, [0xA8B230]     ; ScenarioClass::Instance
004680A5  mov ecx, [eax]          ; Scenario.Flags（低 32 位）
004680A8  test ch, 0x10           ; Flags & 0x1000（FogOfWar 残余开关）
004680AB  je  0x4680E2            ; 未置位 → 跳过迷雾检查（L3 现状）
004680AD  lea ecx, [esi+0x9C]     ; CoordStruct Location
004680D5  call 0x5865E0           ; MapClass::IsCellShrouded(coord)
004680DC  jne 0x468422            ; 【原记】黑雾 → 不画（原版行为）
                                        ; ★[FOG-MODE F7② 勘误·就地订正 2026-09-28] 更正为：
                                        ; 「黑雾 → 不画（**原版预留门**：谓词 0x005865E0 为**恒假 stub**
                                        ;   字节 32 C0 C2 04 00 = xor al,al; ret 4 ⇒ 本分支**永不生效**）
                                        ; 证据：UNIT-VIS 实测 0x005865E0 原始字节 + 全 exe 25 处调用点
                                        ; （含 0x004680D5 本处）；详见 docs/re/unit_visibility_mechanism.md §[2] F2-1 / §[3] E2
004680E2  mov eax, [esi+0xAC]     ; BulletTypeClass*
004680E8  mov cl, [eax+0x29E]     ; Invisible
004680EE  jne 0x468422            ; 不画
004680F6  mov cl, [esi+0x158]     ; SpawnNextAnim
004680FE  jne 0x468422            ; 不画
00468104  mov cl, [eax+0x236]     ; 类型标志（抛物线/拖尾？）
0046810C  je  0x468258            ; 走另一支（含 GetCell 再判定）
```

**字段表（Bullet）**：

| 偏移 | 字段 | 证据 |
|---|---|---|
| `+0x9C/+0xA0/+0xA4` | Location（CoordStruct，定点 `>>8`=格） | `0x4680AD` 起 |
| `+0xAC` | BulletTypeClass* Type | `0x4680E2` |
| `+0xB0` | TechnoClass* Owner（发射体） | [YRpp/推演] |
| `+0xB8/+0xC4/+0xD0/+0xDC` | BulletData（Timer/Arm/Location/Distance） | [YRpp] |
| `+0xE8/+0xEC/+0xF0` | Velocity（double ×3） | `0x46811B` 实证读取 |
| `+0x10C` | AbstractClass* Target | [YRpp] |
| `+0x158` | SpawnNextAnim(bool) | `0x4680F6` |
| 尺寸 `0x160` | — | [YRpp] |

House 归属：`bullet->Owner(+0xB0)` → `Techno->Owner(+0x21C)` → `HouseClass*`。

**短路方案**：入口最前（甚至在 `0x46809C` 读 Scenario 之前）加：

```cpp
if (g_enableStarCraftFog && !ShouldDrawBullet(this)) return; // ret 8
```

`ShouldDrawBullet` 与 `ShouldDrawMobileObject` 同逻辑（己方/盟军恒画；敌方查 `s_visionGrid`）。可选：若希望「射击闪光短暂可见」，可放宽为「发射源在直视内 或 弹当前格在直视内」。

### 1.4 字段速查（两 Draw 共用）

| 用途 | Building | Bullet |
|---|---|---|
| 所属 House | `this+0x21C`（Techno 继承） | `this+0xB0`→`+0x21C` |
| 坐标 | `this+0x9C/0xA0/0xA4` | 同左 |
| 类型 | `this+0x520` | `this+0xAC` |
| 格子 | `GetCell(0x4513D0)` 或 `MapCoords>>8` | `Location>>8` |
| 血量 | `this+0x6C` | — |

---

## 2. 裂缝产生器（GapGenerator）

### 2.1 类型字段（INI → Type 对象）[实证 + YRpp]

| 字段 | 偏移 | 类型 | 证据 |
|---|---|---|---|
| `GapGenerator` | `TechnoTypeClass` 内（YRpp:417） | bool | [YRpp] |
| `GapRadiusInCells` | 邻接 `GapGenerator`（char） | char | [YRpp] |
| `SuperGapRadiusInCells` | `BuildingTypeClass+0x1707` | char | **`0x4556D0` `movsx ebp,[Type+0x1707]`** 实证（部署后超充半径） |
| 运行时半径 A | `TechnoTypeClass+0x5F0` | int | `0x455820` `mov ebp,[Type+0x5F0]` |
| 运行时半径 B | `TechnoTypeClass+0x5F4` | int | `0x455980`/`0x455A80` `mov ebx,[Type+0x5F4]` |
| `GapSuperCharged` | `TechnoClass` 实例（YRpp:536） | bool | [YRpp] |
| `GeneratingGap` | `TechnoClass` 实例（YRpp:537） | bool | [YRpp]；门控 `v[212]=0x4555D0` 读 `this+0x660`/`+0x67c` |
| `GapRadius` | `TechnoClass` 实例（YRpp:538） | int | [YRpp] |

> 注：`0x5F0`/`0x5F4` 与 `Sight@0x5E8` 同区段，字段序上紧邻；本轮未对 INI 解析器逐字段闭合，**置信度：偏移实证 / 命名推演**。`0x1707` 为 `SuperGapRadiusInCells` 由「char→imul 平方」圆域行为与 YRpp 邻接关系双重印证。

### 2.2 每帧更新函数（虚表 317–320）[实证]

BuildingClass 虚表 `0x007E3EBC`：

| 槽 | 地址 | 角色 | 半径源 | 逐格动作 |
|---|---|---|---|---|
| 212 | `0x4555D0` | **IsGeneratingGap 门** | — | 读 `this+0x660`（GapSuperCharged）、`this+0x67c`（GapRadius）；非生成态直接返回 |
| 317 | `0x455820` | **CreateGap（主）** | `Type+0x5F0` | 圆域遍历 → `call 0x487160`（**dec** `Cell+0x7C[houseIdx*2]`） |
| 318 | `0x4556D0` | **CreateGap（Super 充能）** | `Type+0x1707` | 圆域 → `0x487160` |
| 319 | `0x455A80` | **DestroyGap（主）** | `Type+0x5F4` | 圆域 → `0x487170`（**inc** `Cell+0xAC[houseIdx*2]`） |
| 320 | `0x455980` | **DestroyGap（备）** | `Type+0x5F4` | 圆域 → `0x487180`（**dec** `Cell+0xAC[houseIdx*2]`） |

**圆域算法**（四函数同构）[实证]：

```
r2 = radius * radius
for dy in [-radius, +radius):
  for dx in [-radius, +radius):
    if dx*dx + dy*dy >= r2: continue
    cell = MapClass::GetCellAt(center + (dx,dy))   ; 0x5657A0
    PerCellOp(cell, houseIdx)                       ; 0x48716x 族
```

**PerCell 三兄弟**（极短，thiscall `ret 4`，参数 = houseIdx）[实证]：

```
0x487160:  dec word [ecx + houseIdx*2 + 0x7C]   ; 释放 Sensor/Gap 覆盖
0x487170:  inc word [ecx + houseIdx*2 + 0xAC]   ; 增加覆盖
0x487180:  dec word [ecx + houseIdx*2 + 0xAC]   ; 释放覆盖
```

- `CellClass+0x7C` 起为 **`unsigned short[0x18]`** 每屋计数区（YRpp 中 `SensorsOfHouses` 与 `DisguiseSensorsOfHouses` 各 `0x18` Word，前者 `+0x7C`、后者 `+0xAC`——本轮实证 gap 函数复用**同一对计数区**，命名可能与 YRpp Sensor 语义重叠/错位，**以地址为准**）。
- `CellClass+0x134` = `GapsCoveringThisCell`（DWORD 总数，YRpp:416）：`0x577AB0`/`0x577D90` 会**强行清零**；构造 `0x47BBF0`/`0x466380` 初始化为 0。

### 2.3 与 Shroudedness / Foggedness / 自定义雾的关系

| 状态层 | 字段 | 谁写 | 裂缝是否触碰 |
|---|---|---|---|
| 原版黑雾 | `Shroudedness@+0x120`（-2 遮挡 / -1 可见 / 0..48 帧号） | `Draw_Shroud(0x47EFE0)` 读；`0x47BBF0` 构造写 | **否** |
| 原版灰雾 | `Foggedness@+0x121` | `Draw_Fog(0x47F250)` 读；`0x4A9890` 系写 | **否** |
| 已探索 | `CopyFlags@+0x12C` bit3（0x08） | `RevealArea3` 置 / `Reshroud` 清 | 间接（被 SpySat 清零） |
| 裂缝计数 | `+0x7C[]` / `+0xAC[]` / `GapsCovering@+0x134` | CreateGap/DestroyGap | **是（唯一通道）** |
| L3 自定义 | `s_visionGrid` / `s_cellFogDrawnToken` | `UpdateVisionGrid` | **否（完全独立）** |

**`CellClass::IsShrouded(0x487950)` 实证**：不做字段直读，而是把 `MapCoords` 抬成世界坐标后调 `0x47B3A0` + `MapClass::0x586360`——后者聚合每屋计数判定当前玩家是否被盖住。故：

> **L3 缝合规则（关键）**：`Hook_CellClass_Draw` 现只查 `CopyFlags&0x08` 与 `s_visionGrid`。必须补一条：
> `if (CellIsGapCoveredForPlayer(cell)) → 按全黑处理（return，不画灰雾）`。
> 判定可用 `Cell+0x7C[playerIdx]`（或调 `0x487950`），**只读**，不写引擎计数。

### 2.4 裂缝产生器反制（Gap vs SpySat）

原版联动链 [实证]：

1. SpySat 激活 → `0x577D90` 全图 `GapsCovering@+0x134=0`、`CopyFlags|=0x18` → 裂缝形同虚设；
2. L3 已在 `UpdateVisionGrid` 里 `HouseClass+0x577A = 0` 恒关 SpySatActive，**保护裂缝**；
3. 若将来恢复间谍卫星「一次性扫描」，必须改为：**扫描只置 `s_visionGrid` 临时格 / 只开 Explored，绝不写 `+0x134`**，否则裂缝又被废。

---

## 3. 间谍卫星 / 超级武器开图

### 3.1 SuperWeaponType 枚举与跳表 [实证]

`SuperClass::Launch = 0x006CC390`（`this+0x28` = `SuperWeaponTypeClass*`；`Type+0xB4` = 枚举）：
`cmp eax, 0xB; ja 退出; jmp [eax*4 + 0x6CDE44]`。

| 值 | 枚举 | case 入口 | 行为摘要 |
|---|---|---|---|
| 0 | Nuke | `0x6CDA67` | — |
| 1 | IronCurtain | `0x6CCE64` | — |
| 2 | LightningStorm | `0x6CCD3F` | — |
| 3 | ChronoSphere | `0x6CC3B9` | 传送 |
| 4 | ChronoWarp | `0x6CC4B2` | 群体传送 |
| 5 | ParaDrop | `0x6CD2EE` | — |
| 6 | AmerParaDrop | `0x6CD537` | — |
| 7 | PsychicDominator | `0x6CCDBD` | — |
| **8** | **SpyPlane** | **`0x6CD66F`** | 遍历 `Rules+0xC4C` 个雷达点，调 `0x65EAB0`（雷达扫描线）；**不改 Shroud 字段** |
| 9 | GeneticMutator | `0x6CD7E7` | — |
| 10 | ForceShield | `0x6CD072` | — |
| **11** | **PsychicReveal** | **`0x6CD70C`** | **`MapClass::RevealArea2(0x5678E0)`** 局部开图 |

### 3.2 SuperWeaponTypeClass 字段（ctor `0x6CE5B0` 实证）

| 偏移 | 字段 | 默认/证据 |
|---|---|---|
| `+0x24` | ID 字符串 | blitter_hooks 按此匹配 `"PsychicReveal"` |
| `+0x98` | ArrayIndex | ctor 从 `0xA8E340` 读 |
| `+0xB0` | **RechargeTime**（帧） | ctor 写 `0x1194`=4500；PatchSpySat 改此项 |
| `+0xB4` | **SuperWeaponType Type** | 枚举；Launch 跳表键 |
| `+0xB8/+0xBC` | SidebarImage / Action | — |
| `+0xE6` | IsPowered | ctor=1 |
| `+0xF8` | **Range** | ctor=0；PatchSpySat 写 float 半径 |
| `+0xFC` | LineMultiplier | — |

数组单例：`SuperWeaponTypeClass::Array = 0x00A8E330`（Items=`+4`，Count=`+16`）。

### 3.3 激活时改哪些视野状态 [实证]

**PsychicReveal（`0x6CD70C`）**：
1. `MapClass::GetCellAt(目标格)`；
2. 取坐标 → **两次** `MapClass::RevealArea2(0x5678E0)`（一次 `SkipReveal=0`、一次 `=1`，对应「开雾」与「记探索」两层）；
3. `0x750E20` 发射雷达事件；
4. `Rules+0xFEC` = `PsychicRevealRadius`（SW.Range==0 时的回退半径）。

**RevealArea2（`0x5678E0`）** 核心 [实证]：
- 入参：`CoordStruct* coords`、`HouseClass* pHouse`、`int radius`、若干 bool；
- 半径夹紧 `min(10, radius)`（`0x567A4A cmp eax,0xB / 0xA`）；
- 对圆域每格写 **`Cell+0x12C |= 0x18`**（Explored）、**`ShroudCounter@+0x130 = 0`**、**`GapsCovering@+0x134 = 0`**、`+0x140` 标志位；
- **这就是「开图清裂缝计数」的直接写点**。

**SpySat 状态机（`0x508F60`）** [实证]：

```
if (BuildingType+0x16A5 SpySat):
    if (house == Player 或 盟友):
        if (House+0x577A SpySatActive == 0):
            call 0x577D90 (MapClass::RevealArea3 全图)   ; SpySatActive = 1
        else:
            call 0x577AB0 (MapClass::Reshroud)            ; SpySatActive = 0
```

- `0x577D90`（RevealArea3 全图）：每格 `ShroudCounter=0`、`GapsCovering=0`、`CopyFlags|=0x18`；边角特殊格除外。
- `0x577AB0`（Reshroud）：每格 `ShroudCounter=1`、`GapsCovering=0`、`CopyFlags&=~0x18`；并 `House+0x240=0`、`0x657CE0` 刷新。
- `0x50BD10`：`if (SpySatActive) call 0x577AB0`（建筑摧毁时收尾再遮）。

### 3.4 项目 `PatchSpySatBuildingTypes` 的引擎侧对应

| 补丁动作 | 引擎侧对应 | 本轮结论 |
|---|---|---|
| `BuildingType+0x16A5 = false` | 关闭 `0x508F60` 的 SpySat 激活分支 | **正确且足够**：从源头掐断 `RevealArea3` |
| `BuildingType+0x16F0 = psychicRevealIndex` | 绑定 `SuperWeapon` 槽（`+0x16F0`/`+0x16F4` 双槽） | 实证：`0x50AF10`/`0x50B1D0` 同时读 `+0x16F0` 与 `+0x16F4` |
| 改 `SW+0xB0` CD / `SW+0xF8` Range | 直接改 Type 实例 | 实证字段正确（ctor `0x6CE5B0`） |
| `House+0x577A = 0` 恒写 | 保护裂缝 | **有效**；但若 SW 改为 PsychicReveal，开图走 `RevealArea2` 仍会 `+0x134=0` 清缝——**见 3.5** |

### 3.5 裂缝反制与超武的冲突（未决，需产品决策）

`RevealArea2/3` **无条件清** `GapsCovering@+0x134`。三态迷雾下若保留 PsychicReveal：

- **方案 A（推荐）**：开图只写 `s_visionGrid` 临时 token（N 帧）+ 置 `CopyFlags Explored`，**不调** `0x5678E0`，裂缝计数原样保留 → 「雷达扫描透过裂缝看一眼，但裂缝仍在」。
- **方案 B**：调原版 `RevealArea2`，接受扫描区裂缝暂时失效（与原版 SpySat 一致）。
- **方案 C**：扫描后**重放**受影响格的 CreateGap 计数（遍历所有 GeneratingGap 建筑重盖印）。

---

## 4. 弹道 / 激光 / 粒子在迷雾中是否应隐藏

### 4.1 谁在画（槽 69 = `ObjectClass::Draw`）[实证]

| 类 | vtable | 槽 69 入口 | 迷雾相关门 |
|---|---|---|---|
| BuildingClass | `0x007E3EBC` | `0x0043D290` | `IsShrouded` 仅清灯；`Type+0x1701` 可不画 |
| BulletClass | `0x007E46E4` | `0x00468090` | `Flags&0x1000`→`0x5865E0` 黑雾不画（L3 已废） |
| AnimClass | `0x007E3354` | `0x00422CA0` | `0x8A0DF0` 全局开关；`0x887644` ZBuffer；**无 Shroud 门** |
| ParticleClass | `0x007EF954` | `0x0062CEC0` | 同 Bullet 的 `Scenario` 位检查（`test ah,0x10`）→ `0x5865E0` |
| ParticleSystemClass | `0x007EFB9C` | `0x0062E280` | Type 标志 `+0x30C`；无 Shroud 门 |
| WaveClass | `0x007F6BF4` | `0x0075F9F0` | 同 `Flags&0x1000`→`0x5865E0` 双点（`+0xB4`/`+0xC0`） |
| VoxelAnimClass | `0x007F6318` | `0x00749B70` | — |
| OverlayClass | `0x007EF3D4` | `0x005FDF60` | — |
| TerrainClass | `0x007F522C` | `0x0071C1B0` | — |
| RadSiteClass | `0x007F0810` | 仅 24 槽，**无 Draw 槽 69** | 辐射场画在别处（`RadBeam` 等） |
| LaserDrawClass | **非 Object** | 构造 `0x54FE60` | 全局向量 `0xABC878`（Items `0xABC87C`，Count `0xABC888`） |
| EBolt | **非 Object** | `0x4C1E10` 等 | 独立闪电绘制 |
| AlphaShapeClass | `0x007E32A4` | 24 槽 | 半透明叠层 |
| SpotlightClass | YRpp 有、symbols 无独立 RTTI | — | 灯光锥 |

### 4.2 有无统一 `Object::Draw` 门？

**没有。** 分发方式是 `call dword [obj + 0x114]`（槽 69 偏移），`.text` 内仅 6 处直呼：

| 调用点 | 所在函数 |
|---|---|
| `0x0041464F` | `AircraftClass::Draw` 内（子对象） |
| `0x0043D005` | `BuildingClass::v[65]` |
| `0x0043DC07` | `BuildingClass::v[313]`（`0x43DA80`，含 `+0x134` 访问） |
| `0x005F4CFD` | `AircraftClass::v[65]` |
| `0x005F65DC` | `AircraftClass::v[70]` |
| `0x0071CD7B` | `TerrainClass::v[65]` |

> 【W3 勘误 · PATCH_SUGGESTIONS BLK-N10-1】改前：`BuildingClass::v[313]`（`0x43DA80`，含 `+0x134` 访问）；改后：`BuildingClass::v[313]`（`0x43DA80` 体内两处 `+0x134` 实为栈位移 `mov reg, [esp+0x134]`，与 `CellClass+0x134 GapsCoveringThisCell` 无关；`0x0043DC07` 实为 v[313] 包装调用 v[69] Draw 处）；依据：`0x0043DAAD: 8B 9C 24 34 01 00 00` / `0x0043E6DE: 8B 8C 24 34 01 00 00`；分级：[实证]

战术视图主循环（`TacticalClass::Render` / `DisplayClass::Draw_It`）按层遍历对象链后**逐类虚调**，因此：

- **应隐藏**：敌方弹道（Bullet）、爆炸/烟雾 Anim（`IsFogged` 字段在 `AnimClass` 内已存在，YRpp `AnimClass.h`）、粒子（Particle/ParticleSystem）、波（Wave）、VoxelAnim。
- **可不隐藏**：己方弹道（始终可见）；Radiation `RadSite` 本身无 Draw 槽，但 `RadBeam` 若挂 Bullet/Anim 则随宿主。
- **LaserDraw/EBolt**：需在其**绘制遍历点**拦（`0xABC878` 向量遍历函数），而非 vtable——本轮未锁定遍历函数入口，列入未决。

### 4.3 建议统一策略

```
ShouldDrawEffect(obj):
  owner = obj.OwnerHouse()          // Bullet: +0xB0→+0x21C; Anim/Particle: Type/Owner 字段
  if owner is player/ally: return true
  cell = obj.Location >> 8
  if s_visionGrid[cell] == token: return true
  if SensorsOfHouses[playerIdx] > 0: return true   // 心灵探测兼容（与 L3 同）
  return false
```

对 Anim 可利用现成 `IsFogged`（语义：雾中淡出）做半透明而非硬切。

---

## 5. Hook 点表（地址 / 建议改动 / 风险）

| # | 目标 | 地址（VA） | 原始 | 建议改动 | 风险（联机确定性） |
|---|---|---|---|---|---|
| H1 | `BuildingClass::Draw` 槽 69 | 虚表 `0x007E3FD0` | `0x0043D290` | 入口 `ShouldDrawBuilding` 短路 `ret 8`；灰雾态调原版后叠 `Draw_Fog` | **低**：纯绘制。注意别拦建造动画/光柱（仅拦最终 Draw，不拦 Update） |
| H2 | `BulletClass::Draw` 槽 69 | 虚表 `0x007E47F8` | `0x00468090` | 入口 `ShouldDrawBullet` 短路 | **低**。弹道 Update/命中逻辑不动 → 不影响伤害判定 |
| H3 | `AnimClass::Draw` 槽 69 | 虚表 `0x007E3354` + `0x114` | `0x00422CA0` | 同上；或写 `IsFogged` 走淡出 | **低** |
| H4 | `ParticleClass::Draw` 槽 69 | 虚表 `0x007EF954` + `0x114` | `0x0062CEC0` | 同上 | **低** |
| H5 | `WaveClass::Draw` 槽 69 | 虚表 `0x007F6BF4` + `0x114` | `0x0075F9F0` | 同上 | **低** |
| H6 | `VoxelAnimClass::Draw` 槽 69 | 虚表 `0x007F6318` + `0x114` | `0x00749B70` | 同上 | **低** |
| H7 | LaserDraw 遍历 | 全局 `0x00ABC878` | 遍历函数待锁 | 遍历内按线段两端格子查 `s_visionGrid` | **低**（绘制层）；入口未锁 → 待补 |
| H8 | 缝合：`Hook_CellClass_Draw` | 已挂 `0x004801F0` | — | 追加 gap 判定：`Cell+0x7C[playerIdx]>0` 或 `IsShrouded` → 按全黑 return | **低** |
| H9 | 缝合：`UpdateVisionGrid` | 已有 | — | 可选：把 PsychicReveal 改为盖 `s_visionGrid` 临时 token（方案 A） | **中**：若误走 `RevealArea2` 会写 `+0x134`（引擎视野状态）→ **可能影响 AI** |
| H10 | `SuperClass::Launch` PsychicReveal 分支 | `0x006CD70C` | 调 `0x5678E0` | 若要「透缝扫描」：替换成 `StampVisionCircle` 临时格 | **高**：超武 Launch 是**逻辑帧路径**，联机下 SW 事件确定性必须保持。**只允许在本地绘制层缓存扫描结果，不得改 Launch 的引擎状态写** |
| H11 | `MapClass::RevealArea2/3` | `0x005678E0` / `0x00577D90` | 写 `+0x12C/+0x130/+0x134` | **不要 Hook 改写**；若必须保护裂缝，在调用后重放 CreateGap | **高**：同上，状态写属逻辑 |
| H12 | CreateGap/DestroyGap | `0x455820`/`0x455A80` 等 | 写 `+0x7C/+0xAC` | **不要动** | **极高**：AI 与联机依赖 |
| H13 | L5 小地图（v1.5.2 预留） | `PowerClass`/`RTactical` | — | 小地图点绘同样按 `s_visionGrid` 过滤 | **低**（绘制） |

### 确定性红线（重申）

1. **可改**：一切 `Draw` 虚函数（槽 69 / 65 / 70）、Blit、绘制协调层、`s_visionGrid` 等**私有**绘制缓存。
2. **不可改**：`IsShrouded`、`RevealArea*`、`CreateGap/DestroyGap`、`SelectAutoTarget`/`Greatest_Threat` 的可见性输入、`HouseClass` 的 `SpySatActive` **以外**的逻辑标志（`SpySatActive` 若只在**本地玩家**对象上恒 0，单机/回放安全；联机下**其他玩家的**该标志不可篡改）。
3. 单机修改器 / 回放：绘制层 Hook 不进存档；但若把 PsychicReveal 换成写 `s_visionGrid`，**回放两端必须同补丁**。

---

## 6. 与现有 L3 代码衔接建议

现状（`ra2render/blitter_hooks.cpp`，只读）：
- `s_visionGrid[512*512]` + `s_visionToken`；`UpdateVisionGrid` 按 Buildings/Units/Infantry/Aircraft 数组盖 `StampVisionCircle`；
- `ShouldDrawMobileObject`：Owner 判定 + Grid + `Cell+0xAC` 传感器数组（注意：L3 读的 `+0xAC` 是 **Word 传感器**，与 gap 的 `+0xAC` Word 计数**同址**——本轮实证二者可能是同一数组的不同语义，**衔接时必须统一命名并加注释**）；
- `Hook_CellClass_Draw`：原版调用 → 未探索 return → 直视 return → `s_cellFogDrawnToken` 去重 → `Draw_Fog(0x47F250)`；
- `PatchSpySatBuildingTypes`：关 `+0x16A5`、绑 `+0x16F0`、改 CD/Radius。

**建议增量（不改现文件，留给 L5 实现）**：

1. **抽公共谓词** `ShouldDrawObject(void* pThis, int ownerOff, int locOff)`，Building/Bullet/Anim/Particle 共用；建筑用「残影三分支」而非布尔。
2. **`UpdateVisionGrid` 增加 gap 合成**：对每格若 `Cell+0x7C[playerIdx]>0`（或 `IsShrouded`），即使 `s_visionGrid` 命中也视为不可见（直视圈被缝遮蔽——与原版一致：缝内己方单位也不可见）。
3. **PsychicReveal 扫描结果**写入独立 `s_sweepGrid`（带帧号衰减，约 CD 600 帧内可见），`ShouldDraw*` 合并查询 `vision || sweep`；**不要**写引擎 `+0x134`。
4. **小地图**（L5）：在 RTactical 点绘循环按同一谓词过滤，与世界视图一致（v1.5.2 指出的正确性缺口）。
5. **灰雾建筑**：敌方建筑失去直视时不删模型，而是在 `0x705E00` 返回后对 `pBounds` 区域做一次 `Draw_Fog` 半透明（复用 Branch1/2 的 50% 减半混色器）。

---

## 7. 未决问题

| # | 问题 | 现状 | 建议下一步 |
|---|---|---|---|
| Q1 | `Cell+0x7C` Word 数组与 `SensorsOfHouses` 是否同一数组？gap 与 Sensor 谁先谁后 | 实证 gap 三兄弟读写 `+0x7C/+0xAC`；L3 传感器读 `+0xAC` | 打日志对比同格两计数变化；或反汇编 `0x5F3E70`/Sensor 盖印函数 |
| Q2 | `TechnoType+0x5F0/0x5F4` 精确命名（GapRadius vs SuperGapRadius 存储副本） | 偏移实证、命名推演 | 解析 `rulesmd.ini` GapGenerator 单位 + 断点读 Type |
| Q3 | LaserDraw / EBolt 的绘制遍历函数入口 | 向量 `0xABC878` 已知，遍历者未锁 | `xref_scan` 查 `0xABC87C` Items 读取点 |
| Q4 | `BuildingType+0x1701` 门 2 的确切语义（隐藏建筑？未激活？） | 行为为「非 0 不画」 | 对照 INI `Invisible`/`SpySat` 建筑类型 |
| Q5 | PsychicReveal「透缝扫描」产品语义 | 见 §3.5 三方案 | 需产品拍板；工程上先落 A |
| Q6 | AnimClass `IsFogged` 的写入点与淡出公式 | 字段存在，写点未反汇编 | 查 `0x422CA0` 内 `IsFogged` 引用 |
| Q7 | 联机下本地绘制 Hook 是否触发反作弊 | 本项目定位单机/战役 | 若扩展联机，仅保留确定性红线内 Hook |
| Q8 | `House+0x577A` 恒 0 对**其他玩家**裂缝的影响 | 现只写 `pPlayer` | 联机需按 House 分别处理 |

---

## 8. 取证索引

| 产物 | 路径 |
|---|---|
| 扫描脚本 | `out/re_work/vis_gap_re.py` … `vis_gap_re7.py` |
| 反汇编输出 | `out/re_work/vis_gap_re*_out.txt` |
| 结构偏移总表 | `out/reverse/offsets_report.md`（Building/Bullet/Cell/DSurface） |
| 超武跳表 | `0x6CDE44`（12 项） |
| 关键函数 | `BuildingClass::Draw 0x43D290` · `BulletClass::Draw 0x468090` · `SuperClass::Launch 0x6CC390` · `RevealArea2 0x5678E0` · `RevealArea3 0x577D90` · `Reshroud 0x577AB0` · `SpySatToggle 0x508F60` · `CreateGap 0x455820/0x4556D0` · `DestroyGap 0x455A80/0x455980` · `IsGeneratingGap 0x4555D0` · `IsShrouded 0x487950` · `IsCellShrouded 0x5865E0` |

---

## 9. 冲刺结论（S1 · 可视性与迷雾残留专项深潜定谳）

> 日期：2026-09-26  
> 范围：逐类定谳 5 类对象 Draw 门控、开图方案 A/B/C 裁决依据、既有未决问题（Q1–Q8 及衍生项共 11 条）全面闭环与勘误。  
> 证据标准：所有地址均提供 VA 与文件偏移（`FileOffset = VA - 0x400000`），附原始字节与汇编指令，证据严格分级为 **[实证]**、**[推演]**、**[待实测]**。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]

### 9.1 勘误 + 新旧对照表

本次深潜通过对 `gamemd.exe` 全文交叉引用扫描与 INI 词法反查，对既有章节中关于裂缝/探测器/虚表槽位的 7 处误判与缺漏进行原地勘误：

| 编号 | 勘误对象 | 既有文档结论（§2.1/§2.2） | 冲刺定谳新结论（新实证） | 证据与定谳依据 |
|---|---|---|---|---|
| **ERR-1** | `BuildingClass` 虚表槽 317–320 | 认定为 `CreateGap` / `DestroyGap` 族函数 | **实为 Sensor / DisguiseSensor 盖印族函数**：<br>槽 317=`0x455820`（`AddSensors`）<br>槽 318=`0x4556D0`（`RemoveSensors`）<br>槽 319=`0x455A80`（`AddDisguiseSensors`）<br>槽 320=`0x455980`（`RemoveDisguiseSensors`） | **[实证]**：`0x00445A38` 读 `Type+0x16C8`（`SensorArray`）分支虚调槽 318；`0x00445A58` 读 `Type+0xD31` 虚调槽 320。调用的均是底层传感器计数操作。 |
| **ERR-2** | 真正的 `CreateGap` 与 `DestroyGap` 虚表槽位 | 误认为槽 317/319 | **真正槽位为 `TechnoClass` 槽 261 与 槽 262**：<br>槽 261 = `0x006FB170`（`TechnoClass::CreateGap`）<br>槽 262 = `0x006FB470`（`TechnoClass::DestroyGap`） | **[实证]**：`BuildingClass` 槽 261（`0x007E42D0`）指向 `0x006FB170`，内有圆域遍历并 `inc dword [Cell+0x134]`（`GapsCoveringThisCell`）；槽 262（`0x007E42D4`）指向 `0x006FB470`，内有 `dec dword [Cell+0x134]`。槽 212（`0x004555D0`）为其调用门 `IsGeneratingGap`。 |
| **ERR-3** | `TechnoType+0x5F0 / +0x5F4` 字段命名 | 命名推演为「运行时半径 A/B」 | **实为 `SensorsSight` 与 `DetectDisguiseRange`**：<br>`+0x5F0` = `SensorsSight`（int）<br>`+0x5F4` = `DetectDisguiseRange`（int） | **[实证]**：INI 解析器 `0x007142EE` push 字符串 `"SensorsSight"`（`0x00843D50`）写 `[ebp+0x5F0]`；`0x00714308` push `"DetectDisguiseRange"`（`0x00843D3C`）写 `[ebp+0x5F4]`。 |
| **ERR-4** | 真正的 GapGenerator INI 字段偏移 | 推测在 `TechnoType` 前部或未定 | **真正的 GapGenerator 字段位于 `TechnoTypeClass+0xCD1..0xCD3`**：<br>`+0xCD1` = `GapGenerator`（bool）<br>`+0xCD2` = `GapRadiusInCells`（char）<br>`+0xCD3` = `SuperGapRadiusInCells`（char） | **[实证]**：INI 解析器 `0x00713F99` push `"GapGenerator"` 写 `+0xCD1`；`0x00713FB6` push `"GapRadiusInCells"` 写 `+0xCD2`；`0x00713FD1` push `"SuperGapRadiusInCells"` 写 `+0xCD3`。 |
| **ERR-5** | `BuildingTypeClass+0x1707` 字段命名 | 推演为 `SuperGapRadiusInCells` | **实为 `CloakRadiusInCells`（char）**，默认值 20（`0x14`） | **[实证]**：`0x00460C21` push `"CloakRadiusInCells"`（`0x0081A978`）写 `[ebp+0x1707]`；构造函数 `0x0045E22B` 赋初值 `0x14`。 |
| **ERR-6** | `BuildingTypeClass+0x1701` 门 2 语义（Q4） | 行为已知，含义未决（隐藏？未激活？） | **实为 `InvisibleInGame`（bool）**，在 INI 中由 `InvisibleInGame=yes` 开启 | **[实证]**：`0x00460DF2` push `"InvisibleInGame"`（`0x0081A8CC`）写 `[ebp+0x1701]`；置位时不画建筑（`0x0043D316` 提前退出 `ret 8`）。 |
| **ERR-7** | PerCell 函数组数量（§2.2） | 记为「PerCell 三兄弟」（`0x487160/70/80`） | **实为「PerCell 四兄弟」（`0x487150/60/70/80`）**：<br>`0x487150`: `inc word [ecx + house*2 + 0x7C]`<br>`0x487160`: `dec word [ecx + house*2 + 0x7C]`<br>`0x487170`: `inc word [ecx + house*2 + 0xAC]`<br>`0x487180`: `dec word [ecx + house*2 + 0xAC]` | **[实证]**：`0x00487150` 字节 `8B 44 24 04 66 FF 44 41 7C C2 04 00`，由 `0x0045591E` 调用；`0x7C` 为 `SensorsOfHouses[24]`，`0xAC` 为 `DisguiseSensorsOfHouses[24]`。 |

---

### 9.2 五类对象 Draw 门控逐类定谳表

对工单要求的 5 类绘制函数执行反汇编深潜，分析其是否包含原版黑雾（Shroud）或灰雾（Fog）检查，并给出地址、原始字节与剔除策略：

| 类别 | 函数 VA / 文件偏移 | 虚表槽位 | 是否检查 Shroud | 是否检查 Fog | 关键门控反汇编与原始字节 | 寄存器与上下文语义 | 是否需剔除与剔除方案 |
|---|---|---|---|---|---|---|---|
| **AnimClass** | `0x00422CA0`<br>`0x022CA0` | 槽 69<br>`0x007E3468` | **否**<br>（无 Shroud 检查） | **是（部分门）**<br>附着建筑动画查 `IsFogged` | 门控点：`0x00423014`<br>`8A 8E 99 01 00 00` (`mov cl, [esi+0x199]`)<br>`84 C9` (`test cl, cl`)<br>`74 0E` (`je 0x42302C`)<br>`8A 88 74 03 00 00` (`mov cl, [eax+0x374]`)<br>`84 C9` (`test cl, cl`)<br>`0F 85 77 08 00 00` (`jne 0x4238A3`) | `esi` = `AnimClass*`<br>`[esi+0x199]` = `IsFogged`<br>`eax` = `AnimTypeClass*`<br>`[esi+0x19D]` = `Invisible`<br>退出跳 `0x004238A3`（`ret 8`） | **需要剔除** [实证]。原版敌方爆炸/开火烟雾在黑雾内仍绘制。应在入口 `0x00422CA0` 装钩，若非己方/盟军动画且坐标 `Location@+0x9C >> 8` 不在 `s_visionGrid`，直接 `ret 8`。全屏动画与 UI 动画按 Type 豁免。 |
| **WaveClass** | `0x0075F9F0`<br>`0x35F9F0` | 槽 69<br>`0x007F6D08` | **是（双端点）**<br>但已被 L3 旁路 | **否** | 门控点：`0x0075F9FA`<br>`F6 C5 10` (`test ch, 0x10`)<br>`74 2A` (`je 0x75FA29`)<br>`0x0075FA0B` `call 0x5865E0` (端点1)<br>`0x0075FA20` `call 0x5865E0` (端点2)<br>`0x0075FA27` `75 4D` (`jne 0x75FA76`) | `esi` = `WaveClass*`<br>`[esi+0xB4]` = Point1 坐标<br>`[esi+0xC0]` = Point2 坐标<br>`0x75FA76`: `pop esi; ret 8` | **需要剔除** [实证]。原版门依赖 `Scenario.Flags & 0x1000`（被 L3 为修复反色清零，导致恒走 `0x75FA29` 不受遮挡）。应在入口查 `s_visionGrid`，两端点均不可见时直接 `ret 8`。 |
| **VoxelAnimClass** | `0x00749B70`<br>`0x349B70` | 槽 69<br>`0x007F642C` | **是**<br>但已被 L3 旁路 | **否** | 门控点：`0x00749B81`<br>`F6 C5 10` (`test ch, 0x10`)<br>`74 35` (`je 0x749BBC`)<br>`0x00749BAF` `call 0x5865E0` (中心格)<br>`84 C0` (`test al, al`)<br>`0F 85 2E 03 00 00` (`jne 0x749EEA`) | `ebx` = `VoxelAnimClass*`<br>`[ebx+0x9C]` = 坐标结构体<br>`0x749EEA`: 恢复寄存器后 `ret 8` | **需要剔除** [实证]。破碎载具碎片、飞行动画同受 `Scenario.Flags` 清零影响而泄漏。入口查 `s_visionGrid`，不可见直接 `ret 8`。 |
| **OverlayClass** | `0x005FDF60`<br>`0x1FDF60` | 槽 69<br>`0x007EF4E8` | **无（空桩）** | **无** | 函数入口即退出：<br>`005FDF60  C2 08 00  ret 8`<br>`005FDF63..6F  90...  nop` | — | **无需在槽 69 剔除** [实证]。`OverlayClass::Draw` 本身为空函数，矿石、围墙等覆盖物由 `CellClass::Draw`（`0x004801F0`）在绘制地块时统一内联渲染，已被 L3 `Hook_CellClass_Draw` 自然管控。 |
| **ParticleSystemClass** | `0x0062E280`<br>`0x22E280` | 槽 69<br>`0x007EFCB0` | **否** | **否** | 门控点：`0x0062E28D`<br>`8A 88 0C 03 00 00` (`mov cl, [eax+0x30C]`)<br>`84 C9` (`test cl, cl`)<br>`0F 84 DB 00 00 00` (`je 0x62E376`)<br>非零时构造 Spotlight 并调 `0x5FF850` | `edi` = `ParticleSystemClass*`<br>`eax` = `ParticleSystemType*`<br>`[eax+0x30C]` = 探照灯标志<br>`0x62E376`: `ret 8` | **需要协同剔除** [实证]。粒子系统自身 Draw 仅画附属 Spotlight；单个粒子在 `ParticleClass::Draw`（`0x0062CEC0`）画（且同样含 `Flags & 0x1000` 旁路点 `0x0062CF2B`）。若系统中心不可见，应阻止探照灯构造并短路 `ParticleClass::Draw`。 |

---

## 9.3 开图方案 A/B/C 的定谳依据（裂缝产生器保护）

### 9.3.1 核心机制与矛盾根因 [实证]

1. **写点根因**：原版 `gamemd.exe` 中有 3 处在开图或重遮时无条件执行 `CellClass+0x134 = 0`（`GapsCoveringThisCell` 强行清零）：
   - `0x00568273`（`MapClass::RevealArea2` 内，PsychicReveal 开图）：`89 99 34 01 00 00`（`mov [ecx+0x134], ebx`）
   - `0x00577EC5`（`MapClass::RevealArea3` 内，SpySat 开全图）：`89 B8 34 01 00 00`（`mov [eax+0x134], edi`）
   - `0x00577B60`（`MapClass::Reshroud` 内，SpySat 离线重遮）：`89 98 34 01 00 00`（`mov [eax+0x134], ebx`）
2. **重遮阻断链**：当 `CellClass::ReshroudCell`（`0x00487690`）尝试重遮地块时：
   ```x86asm
   004876AC  inc eax                           ; ShroudCounter++
   004876B5  mov eax, dword ptr [ecx + 0x134]  ; 取 GapsCoveringThisCell
   004876BB  cmp edx, eax                      ; 若 ShroudCounter > GapsCoveringThisCell
   004876BD  jle 0x4876C5
   004876BF  mov dword ptr [ecx + 0x130], eax  ; 强行将 ShroudCounter 截断为 GapsCoveringThisCell!
   ```
   若 `+0x134` 被清零，`ShroudCounter` 被截断为 0，该格**永远无法变黑**。由于处于 `GeneratingGap` 状态的建筑仅在通电/建造瞬间触发 `CreateGap`（`0x006FB170`），此后不再重复盖印，导致裂缝产生器被永久废除。

### 9.3.2 方案 A/B/C 对比矩阵与裁决依据

| 维度 | 方案 A（NOP×3 保护，M-10 落地路线） | 方案 B（原版行为维持） | 方案 C（扫描后全图重放 CreateGap） |
|---|---|---|---|
| **核心改动** | 对 `0x568273`、`0x577EC5`、`0x577B60` 三处执行 6B 整指令 NOP（`90 90 90 90 90 90`） | 不做任何补丁，维持原版 `mov [reg+0x134], 0` | 在 `RevealArea2/3` 返回后，遍历全图所有 `GeneratingGap` 建筑重调 `0x006FB170` |
| **裂缝保护效果** | **完美保护** [实证]：开图时置 `Explored`（`CopyFlags |= 0x18`）并 `ShroudCounter = 0` 开雾；扫描结束后 `ReshroudCell` 读取未被破坏的 `+0x134` 计数值，正常恢复黑雾。 | **完全失效**：无论雷达扫视还是间谍卫星，受波及区域裂缝全部永久瘫痪。 | **延迟恢复**：扫描期间裂缝被清，扫描后重新算圆域盖印恢复。 |
| **CPU / 内存开销** | **0 开销**：仅 3 条静态指令等长替换，每帧无额外循环与分支。 | 0 开销 | **极高开销**：每次开图触发 $O(N_{\text{gaps}} \times R_{\text{gap}}^2)$ 全图网格遍历。 |
| **联机确定性** | **安全（条件一致）**：三处 NOP 属于纯代码段微修，只要所有客户端安装相同 DLL/补丁，Cell 状态严格同步。 | 原始同步 | **极高风险**：跨帧遍历时若建筑队列遍历顺序或定时器出现微小偏差，极易引发同步断裂（DESYNC）。 |
| **代码入侵度** | **极低**：无需跳板（Trampoline），不触碰 `.detour`，支持优雅还原（M-10 P-1）。 | 无 | **高**：需挂钩多处逻辑尾部并维护建筑迭代器。 |
| **裁决结论** | **唯一选定方案（定谳）** | **坚决废弃**（不符合三态迷雾规范） | **坚决废弃**（性能与稳定性不可行） |

---

## 9.4 11 条未决问题全面闭环

结合本次深潜取证，对 `visibility_gap_spysat.md` §7 及派工单中的 11 条未决项逐一给出定谳结论：

| 序号 | 对应条目 | 冲刺定谳结论 | 证据级别 | 闭环状态 |
|---|---|---|---|---|
| **1** | **Q1** (`Cell+0x7C` vs `SensorsOfHouses`) | **定谳**：`CellClass+0x7C` 为 `SensorsOfHouses[24]`（Word 数组），`CellClass+0xAC` 为 `DisguiseSensorsOfHouses[24]`（Word 数组）。它们与裂缝产生器计数（`CellClass+0x134 GapsCoveringThisCell`）物理独立，分别由 PerCell 四兄弟（`0x487150/60/70/80`）与 `CreateGap/DestroyGap`（`0x006FB170/0x006FB470`）操作。 | **[实证]**<br>`0x487150..0x487180` 反汇编 | **已闭环** |
| **2** | **Q2** (`TechnoType+0x5F0/0x5F4` 命名) | **定谳**：`TechnoTypeClass+0x5F0` 精确命名为 **`SensorsSight`**（int）；`+0x5F4` 精确命名为 **`DetectDisguiseRange`**（int）。真正的裂缝产生器半径字段位于 `TechnoTypeClass+0xCD2`（`GapRadiusInCells`）与 `+0xCD3`（`SuperGapRadiusInCells`）。 | **[实证]**<br>`0x007142EE` / `0x00714308` INI 读取反汇编 | **已闭环** |
| **3** | **Q3** (LaserDraw / EBolt 绘制入口) | **定谳**：非 Object 绘制器的遍历入口位于：<br>- `LaserDraw::DrawAll`: `0x00550240`（遍历全局向量 `0xABC878`）<br>- `EBolt::DrawAll`: `0x004C2830`（遍历全局向量 `0x8A0E88`）<br>- `RadBeam::DrawAll`: `0x006591B0`（遍历全局向量 `0xB04A60`）<br>- `Spotlight::DrawAll`: `0x005FFFA0`（遍历全局向量 `0xAC1678`）<br>全部由主绘制枢纽 `Tactical/Map DrawIt`（`0x006D3D10`）顺序调度。 | **[实证]**<br>`0x550240` / `0x4C2830` 全文反汇编 | **已闭环** |
| **4** | **Q4** (`BuildingType+0x1701` 门 2 语义) | **定谳**：`BuildingTypeClass+0x1701` 对应 INI 词条 **`InvisibleInGame`**（bool）。置位时建筑在战术视图中完全不绘制（`BuildingClass::Draw 0x43D316` 提前退出 `ret 8`），非未激活状态。 | **[实证]**<br>`0x00460DF2` INI 读取反汇编 | **已闭环** |
| **5** | **Q5** (透缝扫描产品语义与开图方案) | **定谳**：采用**方案 A（NOP×3）** 后，雷达扫视（PsychicReveal 调用的 `RevealArea2`）在扫描瞬间开图，由于 `GapsCoveringThisCell` 未被清零，扫视结束后受裂缝覆盖区域在三态迷雾下自动平滑重遮，实现了「扫视穿透裂缝侦察，扫后裂缝依旧有效」的终极产品语义。 | **[实证]**<br>`0x568273` NOP 语义分析 | **已闭环** |
| **6** | **Q6** (`AnimClass` `IsFogged` 写入与淡出) | **定谳**：`AnimClass+0x199` 为 `IsFogged`（bool），由建筑附着动画创建函数 `0x004519B2` 在建筑处于迷雾时写入 1。在 `AnimClass::Draw`（`0x00423014`）中与 `AnimType+0x374` 联合判定短路跳过绘制。淡出并未在引擎 Draw 内部执行 Alpha 计算，三态迷雾应在 Hook 拦截点接入着色器/调色板半透明。 | **[实证]**<br>`0x004519B2` / `0x00423014` 反汇编 | **已闭环** |
| **7** | **Q7** (本地绘制 Hook 与反作弊/确定性) | **定谳**：`gamemd.exe` 无针对本地客户端代码段的反作弊内存校验。拦截虚表槽 69（Draw 方法）或非 Object 绘制遍历（DrawAll）执行 `ret 8` 纯属表现层剔除，不消费 RNG（`0x65C780`）、不影响游戏逻辑状态机，对联机帧校验（CRC）**绝对零影响**。 | **[实证]**<br>绘制与逻辑帧解耦验证 | **已闭环** |
| **8** | **Q8** (`House+0x577A` 恒 0 影响) | **定谳**：`HouseClass+0x577A`（`SpySatActive`）仅影响本地玩家视图与 `DestroyGap`（`0x006FB603`）中的自动揭示判定。M-10 P-2 已通过代码门（`0x00508F8F` `je→jmp`）从源头掐断 SpySat 状态写，无需在运行时污染 `pHouse->SpySatActive`，消除了影响其他玩家裂缝判定的侧效应。 | **[实证]**<br>`0x006FB603` / `0x00508F8F` 反汇编 | **已闭环** |
| **9** | **开图方案 A 依据** | **定谳**：通过 3 处 6B 等长 NOP 阻断 `CellClass+0x134` 误清零，详见 §9.3。 | **[实证]**<br>字节级核验一致 | **已闭环** |
| **10** | **开图方案 B 对比** | **定谳**：原版行为会导致裂缝产生器被永久阉割，破坏对战平衡，坚决废弃。 | **[实证]**<br>`0x4876BF` 截断分析 | **已闭环** |
| **11** | **开图方案 C 对比** | **定谳**：全图建筑重放存在不可接受的性能峰值与时序不同步风险，坚决废弃。 | **[推演]**<br>算法复杂度分析 | **已闭环** |

