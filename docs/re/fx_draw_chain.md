# 特效 / 非单位对象绘制链 —— 地址级逆向（Bullet/Anim/Particle/Wave/VoxelAnim/LaserDraw/EBolt/RadBeam）

> 目标：`gamemd.exe`（尤里的复仇 1.001）ImageBase `0x400000`，偏移 = VA − `0x400000`。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 本文为纯逆向产出（无代码补丁），不修改总档案 `REVERSE_ENGINEERING_AND_PATCHES.md` 与 `ra2render` 源码/dll。
> 证据来源：**[实证]** = capstone 反汇编取证（`out/re_work/fx_draw_re*.py` + `*_out.txt`）；**[YRpp]** = 社区 ABI 头；**[推演]** = 字段序/行为链推导。
> 用途：为迷雾剔除（敌方可见性）与渲染性能优化提供 **Hook 点表**。确定性红线与 `visibility_gap_spysat.md` §5 一致：**只拦绘制，绝不写逻辑状态**。

---

## 0. 结论速览

| 问题 | 结论 |
|---|---|
| 有没有统一 `Object::Draw` 门？ | **没有单一入口**。真正统一的是 **`ObjectClass::DrawIfVisible`（v[65]）**，它做视口裁剪后 **`call [vtable+0x114]`（v[69] Draw）**。各类 FX 的 Draw 是被 DrawIfVisible 间接调的。 |
| 每帧谁在遍历并画 FX？ | 战术视图主绘制函数 **`Tactical/Map DrawIt = 0x006D3D10`**（被 `0x4F44DF/0x4F44F4/0x4F4515` 调用）。其内 **FX 绘制枢纽序列** 固定为：`0x6D8DB0`（Object DrawIfVisible 簇）→ `0x5FFFA0`（Spotlight DrawAll）→ `0x550240`（**LaserDraw::DrawAll**）→ `0x4C2830`（**EBolt::DrawAll**）→ `0x556D40`（线迹/杂项）→ `0x6591B0`（**RadBeam::DrawAll**）→ `0x6DBE20`。 |
| Object 系 FX 的 v[69] | Bullet `0x468090`、Anim `0x422CA0`、Particle `0x62CEC0`、ParticleSystem `0x62E280`、Wave `0x75F9F0`、VoxelAnim `0x749B70`。签名均为 `void __thiscall Draw(Point2D* pLocation, RectangleStruct* pBounds)`，出口 `ret 8`。 |
| 非 Object 系绘制入口 | **LaserDraw::DrawAll `0x550240`**（向量 `0xABC878`，Items `0xABC87C`，Count `0xABC888`）；**EBolt::DrawAll `0x4C2830`**（`0x8A0E88` / Items `0x8A0E8C` / Count `0x8A0E98`）；**RadBeam::DrawAll `0x6591B0`**（`0xB04A60` / Items `0xB04A64` / Count `0xB04A70`）；**Spotlight::DrawAll `0x5FFFA0`**（`0xAC1678` / Items `0xAC167C` / Count `0xAC1688`）。 |
| ParticleSystem 与 Anim 更新/绘制是否分离？ | **是**。粒子系统 Update（`0x62DF20` / `0x62E070`）在逻辑/对象 Update 路径；Draw（`0x62E280`）在渲染路径。**高密度爆炸成本中心 = N × `ParticleClass::Draw` + 每个 ParticleSystem 的 Spotlight 构造/绘制 + AnimClass::Draw 内的坐标变换与 Blit**。 |
| 哪些该受迷雾剔除？ | **敌方**弹道/爆炸 Anim/粒子/波/VoxelAnim/激光/EBolt/RadBeam：应按 `s_visionGrid`（+ 可选 `IsCellShrouded`）剔除。**己方与盟友**恒画。屏幕/全屏特效（部分 Anim 类型、光标、UI）不剔。 |
| 与 Blit 的关系 | FX **不直接调 Blitter 虚表**，而是经 **`ConvertClass`/`DSurface` 形状绘制族**（反复出现 `0x4AED70`、`0x4A35A0/0x4A35F0/0x4A3840`、`0x4BBC90`、`0x5AF980` 等），最终落到 L1 已 Hook 的 Blit 家族（`BlitTrans*` / `RLEBlitTrans*`）。**特效与单位共享同一 Blit 族**；在 Blit 层做剔除会误伤地形/单位，**应在 DrawIfVisible / 各 DrawAll 入口短路**。 |
| Hook 方案 | 按类装 **vtable 槽 65（DrawIfVisible）或槽 69（Draw）钩**；非 Object 三件套在 **DrawAll 循环内按元素短路**。全部为绘制层，联机确定性风险低。 |

---

## 1. 虚表槽位与调用约定

### 1.1 ObjectClass 绘制虚表（与 YRpp 对齐）[实证 + YRpp]

| 槽 | 偏移 | 名称 | ObjectClass 默认 | 多数 FX 类 |
|---|---|---|---|---|
| **65** | `+0x104` | **DrawIfVisible** | `0x005F4B10` | Anim 覆写 `0x422C70`（先查 `+0x184` 再转发）；VoxelAnim 覆写 `0x749B20`；Unit 覆写 `0x73B0B0` |
| 66 | `+0x108` | GetFoundationData | `0x005F5B90` | — |
| 67 | `+0x10C` | **DrawBehind** | — | 由绘制协调层调用 |
| 68 | `+0x110` | **DrawExtras** | — | 血条/对话泡等 |
| **69** | `+0x114` | **Draw** | `0x005B3A50`（空） | 各类独立实现（见下表） |
| 70 | `+0x118` | DrawAgain | `0x005F65D0` | 转发到 Draw |

**DrawIfVisible（`0x5F4B10`）内部链** [实证]：

```
005F4B13  mov al, [0xA8ED6B]          ; 全局「跳过裁剪」开关
005F4B34  mov al, [esi+0x80]          ; 本帧已画/隐藏标志
005F4B3E  mov al, [esi+0x81]          ; 另一隐藏标志
005F4B5D  call [edx+0xAC]             ; 槽43 GetPosition → 屏幕矩形
005F4B6A  call 0x6D2140               ; 视口相交测试（Tactical 裁剪）
005F4B77  call [edx+0x2C]             ; WhatAmI；==0x18(24) 特例直接画
...
005F4CFD  call [eax+0x114]            ; ★ 槽69 Draw
005F4D0C  ret 0xC                     ; __stdcall 3 参
```

签名：`bool __stdcall DrawIfVisible(RectangleStruct* pBounds, bool EvenIfCloaked, DWORD dwUnk3)`，**返回是否绘制**。这是**统一视口门**，比在每个 Draw 里做裁剪更早、更省。

### 1.2 各类 Draw（槽 69）入口与签名 [实证]

| 类 | vtable | 槽 69 | 签名 | 出口 | 原版迷雾门 |
|---|---|---|---|---|---|
| BulletClass | `0x007E46E4` | **`0x00468090`** | `thiscall Draw(Point2D*, RectangleStruct*)` | `ret 8`（`0x468255`/`0x468428`） | `Scenario.Flags&0x1000` → `MapClass::IsCellShrouded(0x5865E0)` |
| AnimClass | `0x007E3354` | **`0x00422CA0`** | 同上 | 多出口，大函数至 `0x4238B0` | 无 Shroud 门；有 `0x8A0DF0`/`0x887644` 全局开关 |
| ParticleClass | `0x007EF954` | **`0x0062CEC0`** | 同上 | — | 同 Bullet 的 `IsCellShrouded`（`0x62CF58`） |
| ParticleSystemClass | `0x007EFB9C` | **`0x0062E280`** | 同上 | — | 无 Shroud 门（Type 标志 `+0x30C`） |
| WaveClass | `0x007F6BF4` | **`0x0075F9F0`** | 同上 | `ret 8` | **双点** `IsCellShrouded`：`+0xB4` 与 `+0xC0`，**两端都黑才跳过** |
| VoxelAnimClass | `0x007F6318` | **`0x00749B70`** | 同上 | — | `IsCellShrouded`（`0x749BAF`） |
| BuildingClass | `0x007E3EBC` | `0x0043D290` | 同上 | `ret 8` | `Type+0x1701` 隐藏门；`IsShrouded` 只清灯 |
| ObjectClass 默认 | — | `0x005B3A50` | 空实现 | — | — |

> **注意**：`.text` 内 **直接 `call [reg+0x114]` 仅 6 处**（`0x41464F`/`0x43D005`/`0x43DC07`/`0x5F4CFD`/`0x5F65DC`/`0x71CD7B`）——其中 **`0x5F4CFD` 就是 DrawIfVisible 内的统一转发**；其余是建筑/航空器画子对象。  
> **对 Draw 入口零 IMM 直呼**（`call 0x422CA0` 等 nrefs=0），全部经虚表。Hook 虚表槽是唯一稳妥方案。

### 1.3 每帧调用来源（谁遍历、谁 call）[实证]

```
GScreen/Display 绘制
  └─ 0x4F44DF / 0x4F44F4 / 0x4F4515
       └─ Tactical/Map DrawIt  0x006D3D10   (end 0x6D4B50)
            ├─ …地形/覆盖物/层绘制 helpers (0x6D2B60 / 0x6D3660 / 0x6D2DE0 / …)
            ├─ 0x53D850          表面/调色板准备
            ├─ ★ 0x6D8DB0        Object 绘制协调：对列表内对象
            │      call [obj_vt+0x10C]  DrawBehind
            │      call [obj_vt+0x110]  DrawExtras
            │      call [obj_vt+0x104]  DrawIfVisible → (内部) Draw v[69]
            ├─ ★ 0x5FFFA0        SpotlightClass::DrawAll
            ├─ ★ 0x550240        LaserDraw::DrawAll
            ├─ ★ 0x4C2830        EBolt::DrawAll
            ├─ 0x556D40          线迹/杂项（LineTrail 等）
            ├─ ★ 0x6591B0        RadBeam::DrawAll
            └─ 0x6DBE20          收尾（阴影/叠加）
```

`0x6D8DB0` 的 `call [r+0x104]` 站点：`0x6D909E`、`0x6D916C`、`0x6D93FA`（三条支路，对应不同层/是否 Extras）。  
另有 **`0x6D97D0` / `0x6D9920`** 两条 **`call [r+0x104]`** 小循环（遍历 `0x8A0394` Items / `0x8A03A0` Count，过滤 `WhatAmI==0x24`），被 `0x6D39xx/0x6D3Cxx` 多次调用——**第二遍绘制/小地图/重绘路径**，Hook 时两处都要覆盖。
> 【W3 勘误 · W3-A6/ISSUE-FX-FILTER-REVERSED】改前：0x6D97D0` / `0x6D9920`** 两条 **`call [r+0x104]`** 小循环（遍历 `0x8A0394` Items / `0x8A03A0` Count，过滤 `WhatAmI==0x24；改后：0x6D9920 滤 Building(6)；0x6D97D0 滤 Terrain(0x24)；依据：ra2youli/gamemd.exe:0x2D997C, 0x2D982A; errata_sync_master_table.md:20 (R-E05)；分级：P1

> 【勘误 2026-09-30 · R-E05 · errata_sync】原文「0x6D97D0 / 0x6D9920 … 过滤 WhatAmI==0x24」过滤对象写反。实测：0x6D9920 滤 Building(6)（cmp eax,6 @ 0x6D997C = 83 F8 06）；0x6D97D0 滤 Terrain(0x24)（cmp eax,0x24 @ 0x6D982A = 83 F8 24）。两处并非同一过滤对象。权威：render_second_pass_deep_dive.md:93-95,237。原文保留不删字。

### 1.4 全局数组一览 [实证 + YRpp]

| 集合 | 基址（DynamicVectorClass 对象） | Items | Count | 绘制入口 |
|---|---|---|---|---|
| BulletClass::Array | `0x00A8ED40` | `0xA8ED44` | `0xA8ED50` | 经 Object 簇 `0x6D8DB0` |
| AnimClass::Array | `0x00A8E9A8` | `0xA8E9AC` | `0xA8E9B8` | 同上 |
| ParticleClass::Array | `0x00A83DC8` | `0xA83DCC` | `0xA83DD8` | 同上 |
| ParticleSystemClass::Array | `0x00A80208` | `0xA8020C` | `0xA80218` | 同上 |
| WaveClass::Array | `0x00A8EC38` | `0xA8EC3C` | `0xA8EC48` | 同上 |
| VoxelAnimClass::Array | `0x00887388` | `0x88738C` | `0x887398` | 同上 |
| **LaserDraw 向量** | **`0x00ABC878`** | **`0xABC87C`** | **`0xABC888`** | **`0x550240` DrawAll** |
| **EBolt::Array** | **`0x008A0E88`** | **`0x8A0E8C`** | **`0x8A0E98`** | **`0x4C2830` DrawAll** |
| **RadBeam::Array** | **`0x00B04A60`** | **`0xB04A64`** | **`0xB04A70`** | **`0x6591B0` DrawAll** |
| SpotlightClass::Array | `0x00AC1678` | `0xAC167C` | `0xAC1688` | **`0x5FFFA0` DrawAll** |
| DiskLaserClass::Array | `0x008A0208` | — | — | 磁盘激光（浮空圆盘紫光） |
| AlphaShapeClass::Array | `0x0088A0F0` | — | — | 半透明叠层 |
| BulletClass::ScalableBullets | `0x0089DE18` | — | — | 缩放弹体辅助表 |

> 布局 = YRpp `VectorClass`：`vptr@0, Items@4, Capacity@8, IsAllocated@0xC, IsInitialized@0xD, Count@0x10, CapacityIncrement@0x14`。LaserDraw DrawAll 读 `0xABC888`（+0x10）与 `0xABC87C`（+4）**实证吻合**。

---

## 2. 逐类 Draw 门控链（迷雾相关）

### 2.1 BulletClass::Draw `0x00468090` [实证]

```
0046809C  mov eax, [0xA8B230]        ; ScenarioClass::Instance
004680A5  mov ecx, [eax]             ; Scenario.Flags
004680A8  test ch, 0x10              ; Flags & 0x1000
004680AB  je  0x4680E2               ; 未置位 → 跳过迷雾检查（L3 已强制清 0x1000）
004680AD  lea ecx, [esi+0x9C]        ; Location CoordStruct
004680D5  call 0x5865E0              ; MapClass::IsCellShrouded
004680DC  jne 0x468422               ; 黑雾 → 不画
004680E2  mov eax, [esi+0xAC]        ; BulletTypeClass*
004680E8  mov cl, [eax+0x29E]        ; Invisible
004680EE  jne 0x468422
004680F6  mov cl, [esi+0x158]        ; SpawnNextAnim
004680FE  jne 0x468422
00468104  mov cl, [eax+0x236]        ; 类型标志（抛物线/拖尾分支）
```

字段：`Location@+0x9C/0xA0/0xA4`（定点 `>>8`=格）、`Type@+0xAC`、`Owner(Techno)@+0xB0`→`Owner(House)@+0x21C`、`Velocity@+0xE8/0xEC/0xF0`（double×3）。  
**L5 建议**：在入口最前加 `ShouldDrawEffect` 短路（不要依赖已被 L3 废掉的 `Flags&0x1000`）。

### 2.2 AnimClass::Draw `0x00422CA0` [实证]

```
00422CA0  mov al, [0x8A0DF0]         ; 全局绘制总开关（与 GScreen Draw_It 同源）
00422CB9  mov eax, [0x887644]        ; ZBuffer/表面
00422CC6  push 0x8182F0              ; 名字/图集键
00422CCB  call 0x5F3E50              ; 资源查找
00422CD8  读 +0xB4/+0xAC/+0xC0/+0xBC ; 动画进度/帧号
00422D14  call [eax+0x1EC]           ; 槽123（Anim 自身扩展）
... 中间大量 0x4A35A0/0x4A35F0/0x4A3840（颜色矩阵/光照）...
00422FCC  call 0x55AF60              ; 取 Convert/调色板
0042341B  call 0x47C520              ; 形状绘制
0042347B  call 0x4BBC90              ; ★ 绘制核心（进 Blit）
00423621  call 0x487950              ; CellClass::IsShrouded（局部灯色，非硬切）
0042364F  call 0x69E7E0              ; 灯光/叠层
```

**DrawIfVisible 包装 `0x422C70`**：`if (this+0x184) return false;` 否则 `call 0x5F4B10`。  
`+0x184` 在构造 `0x422720` 中清零；**语义：置位则整只 Anim 跳过绘制**（[推演] 可能对应 Invisible/已完成/附加隐藏）。YRpp 另有 `IsFogged`、`Invisible`（`AnimClass.h`）——**写点未在本轮闭合**，见 §7 未决。

无 Shroud 硬切门；`IsShrouded` 只影响灯色。**敌方爆炸烟雾在迷雾中仍会画** → L5 必须自建剔除。

### 2.3 ParticleClass::Draw `0x0062CEC0` [实证]

```
0062CEC9  call 0x55AF60              ; Convert
0062CF58  call 0x5865E0              ; IsCellShrouded（同 Bullet 门）
0062CF87  call [eax+0x1D0]           ; 槽116
0062D01D  call 0x4AED70              ; ★ 形状/点绘制（进 Blit）
0062D058  call 0x6D2140              ; 视口测试
0062D0AF  call 0x4114B0              ; 辅助
0062D112  call 0x7BD130              ; 数学/随机
```

字段（YRpp `ParticleClass`）：`Type@+0xAC`、`Velocity`、`ParticleSystem@+0x124` 附近、`Translucency`、`RemainingEC/RemainingDC`。  
Array 全局 `0xA83DC8`。

### 2.4 ParticleSystemClass::Draw `0x0062E280` [实证]

```
0062E314  call 0x7C5F00              ; CRT 浮点取整
0062E31D  call 0x7C8E17              ; 分配
0062E347  call 0x5FF250              ; Spotlight 相关
0062E35D  call 0x5FF850              ; SpotlightClass::Draw
0062E368  call 0x5FF2D0              ; Spotlight 更新/收尾
```

**要点**：ParticleSystem 的 Draw **不直接画粒子点**，而是 **维护/绘制 Spotlight（光照锥）**；真正的粒子像素由子对象 `ParticleClass::Draw` 画。  
Update 路径：`0x62DF20`（调用自 `0x6C59CF`）、`0x62E070`（调用自 `0x630233`）——**与 Draw 完全分离**（逻辑帧 vs 渲染帧）。

YRpp 字段：`Particles`（`DynamicVectorClass<ParticleClass*>`）、`Owner`、`OwnerHouse`、`Lifetime`、`TimeToDie`、`SpotlightRadius`（默认 29）。

### 2.5 WaveClass::Draw `0x0075F9F0` [实证]

```
0075F9FA  test ch, 0x10              ; Scenario.Flags & 0x1000
0075FA0B  call 0x5865E0              ; IsCellShrouded(this+0xB4)  起点
0075FA20  call 0x5865E0              ; IsCellShrouded(this+0xC0)  终点
0075FA27  jne 0x75FA76               ; 两端都黑 → 不画
0075FA29  mov eax, [esi+0xB0]        ; WaveType 0..3
0075FA34  jmp [eax*4 + 0x75FA7C]     ; 跳表
    case0: call 0x75FA90             ; 磁暴/磁力
    case1: call 0x7602E0
    case2: call 0x7609E0
    case3: …
```

YRpp：`Draw_Magnetic 0x762070`、`Draw_NonMagnetic 0x761640`、`Update_Wave 0x762AF0`。  
**两端点判定**：只要有一端在可视格就画——L5 剔除时应对 **两端 OR**，不能只查中心。

### 2.6 VoxelAnimClass::Draw `0x00749B70` [实证]

```
00749BAF  call 0x5865E0              ; IsCellShrouded
00749BF6  call 0x578080              ; 变换
00749C09  call 0x565730              ; 坐标
00749C76  call 0x6D2140              ; 视口
00749CAC  call 0x4399E0              ; Voxel 绘制族
00749CBE  call 0x753E00 / 0x753F90 / 0x7542F0  ; 体素/光照
00749D2A  call 0x6D20E0              ; 裁剪
00749D42  call 0x490B90              ; 混合
```

Array `0x887388`。`Invisible` 字段在头文件存在（同 Anim 语义）。

---

## 3. 非 Object 系：LaserDraw / EBolt / RadBeam / Spotlight

### 3.1 LaserDraw（全局向量 `0xABC878`）[实证]

| 项 | 地址 / 布局 |
|---|---|
| 向量对象 | `0xABC878`（vptr）、**Items `0xABC87C`**、Capacity `0xABC880`、**Count `0xABC888`**、CapInc `0xABC88C` |
| 构造 `LaserDrawClass::ctor` | **`0x0054FE60`**（YRpp `JMP_THIS(0x54FE60)`） |
| 析构 | `0x0054FFB0` |
| **DrawAll** | **`0x00550240`** |
| 单实例 Draw | **`0x00550260`**（`this+0x4C`=剩余时长；`this+0x20` 置位则走 `0x5509F0` 旁路） |
| 更新/回收 | `0x550150`（被 `0x55B5C3` Logic 区调用）、`0x550000`（被 `0x534949` 调用） |
| 清空时机 | 析构/RemoveItem 族：`0x54FF7A`/`0x54FFB1` 写 Items/Count；每帧 `0x550240` **倒序遍历**，时长耗尽由 `0x550260`/`0x5509F0` 负责删除 |

**DrawAll 循环** [实证]：

```
00550240  mov eax, [0xABC888]        ; Count
00550246  lea esi, [eax-1]
0055024D  mov ecx, [0xABC87C]        ; Items
00550253  mov ecx, [ecx+esi*4]       ; Items[i]
00550256  call 0x550260              ; LaserDraw::Draw(this)
0055025B  dec esi
0055025C  jns 0x55024D
0055025F  ret
```

单实例 Draw 内：`this+0x4C`（Duration 剩余）`<=0` 则不画；`this+0x20` 为「闪烁/特殊」标志；`0xABC8B8` 为全局混合状态位。

构造调用点（谁创建激光）：`0x44AC9E`（建筑武器）、`0x4A7691/0x4A7804/0x4A78DF`（**DiskLaser 磁盘激光**）、`0x62F940`、`0x6FD42B`（Techno 开火）。  
**LaserDraw 不是 Object，无 Owner 字段**——YRpp 仅有 Source/Target CoordStruct、颜色、Duration。迷雾剔除只能按 **线段两端格子** 查 `s_visionGrid`。

### 3.2 EBolt（电弧，`0x8A0E88`）[实证 + YRpp]

| 项 | 地址 |
|---|---|
| Array | `0x8A0E88` / Items `0x8A0E8C` / Count `0x8A0E98` |
| ctor | `0x4C1E10` |
| dtor | `0x4C2C10` |
| Fire | `0x4C2A60`（写入 Array） |
| SetOwner / ClearOwner | `0x4C2BD0` / `0x4C1E50` |
| **DrawAll** | **`0x004C2830`** |
| DeleteAll | `0x4C2930`（YRpp 注释） |

**DrawAll 循环** [实证]：

```
004C2833  mov eax, [0x8A0E98]        ; Count
004C2839  dec eax
004C2849  mov ecx, [0x8A0E8C]        ; Items
004C284F  mov eax, [ecx+eax*4]
004C2856  mov ecx, [eax+0x20]        ; Owner (TechnoClass*)
004C287C  call [ebx+0xB0]            ; Owner->GetFLH / GetSourceCoords
... 用 Point1(+0)/Point2(+0xC)、Random、AlternateColor 画折线闪电 ...
```

YRpp 字段：`Point1`、`Point2`、`Owner`、`WeaponSlot`、`Lifetime`（**DrawAll 时 `>>=1`，0 则 dtor**——「每画一次寿命减半」）、`AlternateColor`。  
**迷雾**：有 `Owner`，可 `Owner→House` 判敌我；两端点坐标在 `Point1/Point2`。

### 3.3 RadBeam（辐射光束，`0xB04A60`）[实证 + YRpp]

| 项 | 地址 |
|---|---|
| Array | `0xB04A60` / Items `0xB04A64` / Count `0xB04A70` |
| Allocate | `0x659110`（`RadBeamType mode`） |
| **DrawAll** | **`0x006591B0`** |
| 相关 | `0x658DE0`（向量构造/清空，`ret 8`） |

**DrawAll 开头** [实证]：

```
006591B9  mov eax, [0xB04A70]        ; Count
006591DC  mov eax, [0xB04A64]        ; Items
006591E2  mov eax, [edx]             ; beam
006591E4  cmp dword [eax+0x10], 2    ; Type == 2 特殊分支计数
006591EB  cmp byte [eax+9], bl
```

YRpp 字段：`Owner(+4)`、`Type(+0x10)`、`Color`、`SourceLocation`、`TargetLocation`、`Period`、`Amplitude` 等。  
**RadSiteClass 无 Draw 槽 69**（仅 24 槽 Abstract）；辐射场的可见光束走 **RadBeam::DrawAll**，伤害场逻辑在 `RadSite`。

### 3.4 SpotlightClass（探照灯锥，`0xAC1678`）[实证 + YRpp]

```
005FFFA0  mov eax, [0xAC1688]        ; Count
005FFFA6  lea esi, [eax-1]
005FFFB3  mov ecx, [0xAC167C]        ; Items
005FFFB6  call 0x5FF850              ; SpotlightClass::Draw
```

YRpp：`Draw 0x5FF850`、`Update 0x5FF320`。由 **ParticleSystem::Draw** 与建筑灯光创建。与 `AlphaShapeClass`（`0x88A0F0`）同属叠层光效。

### 3.5 非 Object 三件套的清空时机

| 集合 | 何时减员 |
|---|---|
| LaserDraw | 单实例 `0x550260`/`0x5509F0` 发现 Duration 耗尽 → Remove；Logic 区 `0x550150` 定期回收；关卡/重载时 `0x550000` 清空 |
| EBolt | **DrawAll 本身推进 Lifetime**（`>>=1`，到 0 析构）；`DeleteAll 0x4C2930` 全清 |
| RadBeam | Allocate 复用池；`0x658DE0` 构造向量时 `Count=0`；单束结束由 Update 移除 |
| Spotlight | Draw/Update 内衰减；数组随 Light 关闭清空 |

---

## 4. Update vs Draw 分离；高密度爆炸成本中心

### 4.1 分离性 [实证]

| 对象 | Update（逻辑帧） | Draw（渲染帧） | 是否同函数 |
|---|---|---|---|
| AnimClass | `0x422720`/`0x4228E0` 等（Array 注册/销毁）+ 虚表 Update 槽 | `0x422CA0` | **分离** |
| ParticleClass | `0x62B5E0` ctor、`0x62BB20`、`0x62D9A0` | `0x62CEC0` | **分离** |
| ParticleSystemClass | **`0x62DF20`、`0x62E070`**（发射子粒子、推进 Lifetime） | **`0x62E280`**（只画 Spotlight） | **分离（关键）** |
| BulletClass | 飞行/命中逻辑（`0x4664C0` 等） | `0x468090` | **分离** |
| WaveClass | `Update_Wave 0x762AF0` | `0x75F9F0` | **分离** |
| LaserDraw | `0x550150`/`0x550000` | `0x550240`/`0x550260` | **分离** |
| EBolt | Fire 创建；Lifetime 在 **DrawAll 内衰减**（**耦合点**） | `0x4C2830` | **半耦合**（Draw 推进寿命） |

> **EBolt 的 Lifetime 在 DrawAll 里 `>>=1`**：若 L5 在 DrawAll 入口整段跳过（不进入循环），**电弧会永生**。  
> **正确短路位置**：循环体内 `if (!ShouldDraw) continue;` **不要**跳过整个 DrawAll；或短路前先手动衰减 Lifetime。

### 4.2 高密度爆炸的成本中心 [实证 + 推演]

一场 V3/核弹级爆炸典型对象：

1. **1 × AnimClass**（爆炸本体）→ `AnimClass::Draw` ≈ **0xC10 字节** 的坐标变换 + 多次 `0x4AED70/0x4BBC90` 形状绘制 + 灯色 `IsShrouded`。
2. **1 × ParticleSystemClass** → Draw 里 **构造/更新 Spotlight**（`0x5FF250`/`0x5FF850`/`0x5FF2D0`），每个 Spotlight 一次锥面填充。
3. **N × ParticleClass**（N 常达数十～数百）→ **每个独立走 DrawIfVisible + Draw**，各自视口测试 + Convert + Blit。
4. 可能叠加 **VoxelAnim**（弹片）、**Wave**（震波）、**LaserDraw**（若有激光武器）。

**同帧重复绘制**：

- `ParticleSystem::Draw` 的 Spotlight 与 `ParticleClass::Draw` 的点 **不共享批次**，N 次独立 Blit 调用。
- `0x6D8DB0` 与 `0x6D97D0/0x6D9920` **两条绘制路径**可能对同一对象各画一次（主视图 + 重绘/小地图）——若两路径都挂 Hook，要保证谓词幂等。
- Anim 的 `0x4A35A0/0x4A35F0` 光照矩阵在 Draw 内逐帧重算，可缓存。

**可合并 / 限频点**（仅绘制层）：

| 点 | 理由 | 风险 |
|---|---|---|
| 同一 `ParticleSystem` 的子粒子按调色板/Translucency 分桶 | 减少 Convert/Blit 切换 | 低（只合并绘制） |
| `s_visionGrid` 未命中时 **在 DrawIfVisible 直接 return false** | 最早短路，省掉全部子绘制 | 低 |
| Spotlight：半径内无变化时隔帧画 | 锥面填充贵 | 低 |
| Anim：`IsFogged` 半透明淡出而非硬切（可选） | 保留「雾中残影」体验 | 低 |
| **禁止**在 Update 路径限频 | 会改动画/粒子寿命与伤害时序 | **高（确定性）** |

### 4.3 与 Blit 的关系 [实证]

FX Draw **不直接 call Blitter vtable**；调用链：

```
AnimClass::Draw / ParticleClass::Draw / BulletClass::Draw
  → 0x55AF60（Convert/调色板）
  → 0x4AED70 / 0x4BBC90 / 0x4A35A0 / 0x4A35F0 / 0x4A3840 / 0x5AF980
       （DSurface / ConvertClass 形状与点绘制）
  → Blitter::BlitTrans* / RLEBlitTrans*（L1 已 Hook 的同一族）
```

**结论**：特效与单位/地形 **共享 Blit 族**。在 Blit 层按像素剔除无法区分来源，**且会破坏已向量化的 L1 Hook**。迷雾/性能短路必须放在 **DrawIfVisible（槽 65）或各类 Draw/DrawAll 入口**。

LaserDraw/EBolt/RadBeam 的线段/折线绘制走 **逐点/逐段写表面**（`0x550260` 内大量数学 + 表面写），同样最终进像素输出，但 **不走 SHP RLE Blit**——它们是 **矢量线/面填充**，成本在线段长度与分段数。

---

## 5. 迷雾剔除策略（谁该藏、谁不该藏）

### 5.1 判定谓词（与 L3 `ShouldDrawMobileObject` 同构）

```
ShouldDrawEffect(obj, ownerOff, locOff):
  owner = *(obj+ownerOff)           // 可能是 Techno* 或 House*
  if owner == null:                 // 无主特效（中立爆炸残骸）
      return s_visionGrid[cell(loc)] || 已探索
  house = owner(House)
  if house == Player || house == Ally: return true
  cell = (Coord)loc >> 8
  if s_visionGrid[cell] == s_visionToken: return true
  if SensorsOfHouses[playerIdx] > 0: return true   // 心灵探测
  return false
```

### 5.2 分类表

| 对象 | 是否迷雾剔除 | Owner 来源 | 坐标来源 | 备注 |
|---|---|---|---|---|
| **己方/盟友** Bullet/Anim/Particle/Wave/VoxelAnim | **否（恒画）** | 同左 | 同左 | 射击反馈必须可见 |
| **敌方** Bullet | **是** | `+0xB0`→`+0x21C` | `+0x9C` | 可放宽为「发射源直视 ∨ 弹当前格直视」 |
| **敌方** 爆炸/烟雾 Anim | **是**（或 `IsFogged` 半透明） | YRpp OwnerObject / Type | `+0x9C` 系 | 硬切省 fillrate；半透明留残影 |
| **敌方** Particle / ParticleSystem | **是** | `OwnerHouse`（PS）/ ParticleSystem 指针 | 各自 Location | PS 剔除后子粒子也应藏 |
| **敌方** Wave | **是**（两端 OR） | `+0x200` 附近 Owner | `+0xB4` 与 `+0xC0` | 只查一端会漏画/多画 |
| **敌方** VoxelAnim | **是** | Owner 字段 | Location | 弹片 |
| **敌方** LaserDraw | **是**（线段两端 OR） | **无 Owner** | Source/Target | 只能按两端格子；己方开火激光建议恒画（可按颜色/Duration 推测） |
| **敌方** EBolt | **是** | `Owner(+0x20)` | Point1/Point2 | Lifetime 衰减不可跳过 |
| **敌方** RadBeam | **是** | `Owner(+4)` | Source/Target | 伤害逻辑在 RadSite，不拦逻辑 |
| Spotlight / AlphaShape | **随宿主**（Particle/建筑） | — | — | 宿主剔除则自然消失 |
| 全屏/UI/光标/雷达扫描线 | **否** | — | — | 屏幕特效 |
| 建筑残影（三态迷雾） | **不硬切** | `+0x21C` | `+0x9C` | 敌方+已探索无直视 → 灰雾叠加（同 `visibility_gap_spysat.md` §1.2） |

### 5.3 与裂缝产生器 / SpySat 的合并

与 `visibility_gap_spysat.md` §2.3 相同：`s_visionGrid` 命中后仍需查 `Cell+0x7C[playerIdx]`（gap 覆盖）——**缝内己方特效也不可见**（与原版一致）。

---

## 6. Hook 点表（地址 / 改动 / 确定性风险）

> 红线：**只拦绘制**。禁止改 `IsShrouded` / `IsCellShrouded` / `RevealArea*` / Update / EBolt Lifetime 推进语义（除非同步补衰减）。

| # | 目标 | 地址（VA） | 原始 | 建议改动 | 确定性风险 |
|---|---|---|---|---|---|
| **H-FX1** | `ObjectClass::DrawIfVisible` | 虚表槽 65，共享体 `0x005F4B10` | 视口裁剪后 `call v[69]` | 入口加 `ShouldDrawEffect`：失败则 `xor al,al; ret 0xC`。**一处钩覆盖 Bullet/Anim/Particle/PS/Wave/VoxelAnim/Overlay/…** | **低**（纯绘制）。注意 Anim/VoxelAnim/Unit 有包装（`0x422C70`/`0x749B20`/`0x73B0B0`），钩共享体即可，包装只加 `+0x184` 门 |
| **H-FX2** | `BulletClass::Draw` 槽 69 | vtable `0x007E47F8` / fn `0x00468090` | 门控链 | 入口短路 `ret 8`（双保险；H-FX1 已盖则可选） | **低** |
| **H-FX3** | `AnimClass::Draw` 槽 69 | `0x007E3354`+`0x114` / `0x00422CA0` | 无 Shroud 硬切 | 入口短路或写 `IsFogged` 走淡出 | **低** |
| **H-FX4** | `ParticleClass::Draw` | `0x007EF954`+`0x114` / `0x0062CEC0` | 有 IsCellShrouded | 入口短路 | **低** |
| **H-FX5** | `ParticleSystemClass::Draw` | `0x007EFB9C`+`0x114` / `0x0062E280` | Spotlight | 入口短路（连带少画 Spotlight） | **低** |
| **H-FX6** | `WaveClass::Draw` | `0x007F6BF4`+`0x114` / `0x0075F9F0` | 两端 Shroud | 入口短路；谓词用两端 OR | **低** |
| **H-FX7** | `VoxelAnimClass::Draw` | `0x007F6318`+`0x114` / `0x00749B70` | — | 入口短路 | **低** |
| **H-FX8** | **LaserDraw::DrawAll** | **`0x00550240`** | 倒序循环 `call 0x550260` | **循环体内**按 Source/Target 格子查 `s_visionGrid`，失败 `continue`（勿短路整个函数） | **低** |
| **H-FX9** | **EBolt::DrawAll** | **`0x004C2830`** | 循环 + Lifetime 衰减 | **循环体内**短路；**必须保留 Lifetime `>>=1`**，否则电弧永生 | **低**（若误跳过循环 → 视觉残留，非同步） |
| **H-FX10** | **RadBeam::DrawAll** | **`0x006591B0`** | 循环 | 循环体内按两端格子短路 | **低** |
| **H-FX11** | Spotlight::DrawAll | `0x005FFFA0` | 循环 `call 0x5FF850` | 可选：半径内无直视时 continue | **低** |
| **H-FX12** | 第二绘制路径 `0x6D97D0` / `0x6D9920` | `call [r+0x104]` | 重绘/小地图 | 与 H-FX1 同谓词（幂等） | **低** |
| **H-FX13** | `AnimClass::DrawIfVisible` 包装 `0x422C70` | `+0x184` 门 | — | 若要用引擎现成「跳过绘制」标志，可在 `+0x184` 写 1（**注意**：该字段可能被 Update 读，**先只读验证**） | **中**：若 Update 也读 `+0x184` 则会影响逻辑 → 先查写点 |
| **H-FX14** | 性能：同帧粒子合并 | Particle Draw 之前按桶批绘 | — | 纯绘制层重排 | **低**；禁止改 Update 顺序 |
| **H-FX15** | 灰雾建筑残影 | `BuildingClass::Draw` 返回后叠 `Draw_Fog` | 见 visibility 文档 H1 | 同文档 | **低** |

### 确定性红线（重申）

1. **可改**：DrawIfVisible / Draw / DrawAll / Blit / `s_visionGrid` 等私有绘制缓存。
2. **不可改**：`IsShrouded(0x487950)`、`IsCellShrouded(0x5865E0)`、`RevealArea*`、CreateGap/DestroyGap、AI 可见性输入、任何 Update 的对象寿命/位置写。
3. **EBolt Lifetime 在 DrawAll 衰减**：短路时要么继续衰减，要么接受「雾中电弧寿命不减」的视觉副作用（单机可接受，回放需两端同补丁）。
4. 单机/战役：绘制 Hook 不进存档。联机：仅保留红线内 Hook。

---

## 7. 未决问题

| # | 问题 | 现状 | 建议下一步 |
|---|---|---|---|
| Q1 | `AnimClass+0x184` 确切语义（Invisible / Done / Attached-hidden） | DrawIfVisible 非 0 即跳过 | 断点写点；对照 YRpp `IsFogged`/`Invisible` 偏移 |
| Q2 | `AnimClass IsFogged` 淡出公式与写点 | 头文件有字段，Draw 内未锁定公式 | 在 `0x422CA0` 内搜 `+0x1A0` 附近字节（Anim 尾部） |
| Q3 | `0x6D8DB0` 与 `0x6D97D0` 列表的精确数据源 | 前者 `esi` 来自绘制协调层参数；后者 `0x8A0394/0x8A03A0` | 对 `0x8A0394` 做 xref，确认是否「当前层对象表」 |
| Q4 | `0x556D40`（EBolt 与 RadBeam 之间） | 在枢纽序列中，疑似 LineTrail/磁盘激光杂项 | 反汇编并对照 DiskLaserArray `0x8A0208` |
| Q5 | LaserDraw 无 Owner，己方激光是否恒画 | 只能按两端格子 | 产品定：己方武器激光建议恒画（Duration 短、反馈关键） |
| Q6 | 同帧双路径（主视图+小地图）是否重复绘制 | `0x6D8DB0` 与 `0x6D97D0` 均 call DrawIfVisible | 加计数器统计 Draw 调用次数/对象 |
| Q7 | ParticleSystem SpotlightRadius 膨胀时的 fillrate | 默认 29，INI 可更大 | 大半径 Spotlight 单独限频 |

---

## 8. 取证索引

| 产物 | 路径 |
|---|---|
| 扫描脚本 | `out/re_work/fx_draw_re.py` … `fx_draw_re12.py` |
| 反汇编输出 | `out/re_work/fx_draw_re*_out.txt` / `*_clean.txt` |
| 关键函数 | **DrawIfVisible `0x5F4B10`** · **Map DrawIt `0x6D3D10`** · **Object 簇 `0x6D8DB0`** · **LaserDraw::DrawAll `0x550240`** · **EBolt::DrawAll `0x4C2830`** · **RadBeam::DrawAll `0x6591B0`** · **Spotlight::DrawAll `0x5FFFA0`** |
| Draw（槽 69） | Bullet `0x468090` · Anim `0x422CA0` · Particle `0x62CEC0` · ParSys `0x62E280` · Wave `0x75F9F0` · VoxelAnim `0x749B70` |
| Update（分离） | ParSys `0x62DF20`/`0x62E070` · Anim `0x422720`/`0x4228E0` · Wave `0x762AF0` |
| 全局向量 | LaserDraw `0xABC878` · EBolt `0x8A0E88` · RadBeam `0xB04A60` · Spotlight `0xAC1678` |
| 相关文档 | `docs/re/visibility_gap_spysat.md`（迷雾/建筑/弹道门）· `docs/re/rle_blit_family.md`（Blit 族） |

---

## 9. 与 L3 现有代码衔接（只读建议，不改 ra2render）

现状（`ra2render/blitter_hooks.cpp`）：已钩 Unit/Infantry/Aircraft 的 **vtable[69] Draw** + `CellClass::Draw` + L1 Blit。

**L5 增量建议**：

1. 抽 `ShouldDrawEffect(void* p, int ownerOff, int locOff)`，与 `ShouldDrawMobileObject` 共用 `UpdateVisionGrid` / gap 合成。
2. **优先钩 `ObjectClass::DrawIfVisible` 共享体 `0x5F4B10`**（或各 FX 类槽 65）：一处覆盖全部 Object 系 FX；比逐类钩槽 69 更省。
3. 非 Object 三件套 + Spotlight：在 **DrawAll 循环体内** continue；**EBolt 保留 Lifetime 衰减**。
4. 性能：同一 ParticleSystem 子粒子分桶合并；Spotlight 限频；**不改 Update**。
5. 小地图路径 `0x6D97D0/0x6D9920` 使用同一谓词，保证与主视图一致。

---

## 10. 冲刺结论（S3）

> **冲刺任务**：S3 特效绘制链深潜（Q1–Q7 7 条未决逐项闭环）  
> **执行日期**：2026-09-26  
> **基准程序**：`ra2youli/gamemd.exe`（1.001，ImageBase `0x00400000`，`.text` RVA `0x00001000`，`FileOffset = VA - 0x00400000`）  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据等级**：**[实证]**（VA + 文件偏移 + 原始机器码 + 汇编指令）/ **[推演]**（算法结构与调用链分析）/ **[待实测]**（需联机/真机遥测）

### 10.1 既有结论勘误与新旧对照

根据本次 S3 专项指令级反汇编与静态交叉引用结果，对本文前序章节的推测性内容进行单列勘误如下（既有正文保留原状，以本小节定谳为准）：

| 涉及位置 | 既有描述（旧假说/推测） | S3 冲刺定谳（新结论） | 判定依据 |
|---|---|---|:---:|
| §1.1 / §2.2 / §7 Q1 | `AnimClass+0x184` 推演为“Invisible / Done / Attached-hidden 隐藏布尔标志” | **勘误**：实为 **`int DelayTimer`（帧延迟倒计时计数器）**。非布尔值，生命周期贯穿创建延迟与循环延迟，每帧递减，`> 0` 时阻断 `DrawIfVisible` 与 `Update`。 | **[实证]**<br>`0x424386` `dec eax` + `0x421fc2` 写入 |
| §2.2 / §7 Q2 | “`AnimClass IsFogged` 淡出公式与写点未闭环”；推测存在半透明淡出公式 | **勘误**：原版 `gamemd.exe` **不存在渐变半透明淡出公式**。`IsFogged(+0x199)` 与 `AnimType.ShouldFogRemove(+0x374)` 配合执行**布尔硬切剔除（`ret 8`）**；黑雾格仅清零光照强度（`0x42362c`）。 | **[实证]**<br>`0x423014` 硬切 + 全文本无其他 `0x199` 读写 |
| §1.3 / §7 Q3 | `0x8A0394/0x8A03A0` 称为“当前层对象表 / 第二遍绘制 / 小地图路径” | **确证并细化**：实为 **`MapClass::ObjectsInLayers[2]`（`Layer::Ground` 地面层）对象动态向量** 的 `Items` 与 `Count`；`0x6D97D0/0x6D9920` 属于**视口局部脏矩形（Dirty Rect）重绘**，非小地图/雷达路径。 | **[实证]**<br>`0x4a9752` `Layer*24` 寻址 + `0x6d3969` 脏矩形循环 |
| §0 / §1.3 / §7 Q4 | `0x556D40` 归属未定（推测为 EBolt、RadBeam 之间杂项/磁盘激光） | **定谳**：归属于 **`LineTrail::DrawAll`（抛射体/导弹尾迹线全量绘制）**。遍历全局动态向量 `0xABCB78`，单实例绘制为 `0x556C00`。与 EBolt、RadBeam 无派生从属关系。 | **[实证]**<br>`0x556e14` 清空 `ObjectClass+0xA8` (`LineTrailer`) |
| §7 Q6 | 推测主视图与小地图存在双路径重复调用 `DrawIfVisible` | **勘误**：小地图（`RadarClass`）完全不调用 `DrawIfVisible(v[65])`。同帧潜在双路径重复绘制发生在 **主视图全量剔除遍历（0x6D8DB0）与局部脏矩形补绘（0x6D97D0/0x6D9920）** 之间。 | **[实证]**<br>全程序仅 7 处调用 `v[65]`，雷达无调用 |

---

### 10.2 Q1–Q7 逐条实证闭环报告

#### Q1: `AnimClass+0x184` 语义、类型与生命周期闭环 [实证]

- **字段类型**：32 位有符号整型 `int DelayTimer`（或 `RemainingDelay`）。
- **全部读写指令证据链**（全程序 `0x420000 - 0x426000` 仅 8 处指令操作 `[reg + 0x184]`）：
  1. `0x00421FC2`（FO: `0x021FC2`）`89 8E 84 01 00 00`：`mov dword ptr [esi + 0x184], ecx`  
     **语义**：`AnimClass::ctor(0x421EA0)` 提取第 3 个参数（`[ebp + 0x10]` 即 `LoopDelay` 初始延迟值），写入 `+0x184`。
  2. `0x004226F6`（FO: `0x0226F6`）`8B 86 84 01 00 00`：`mov eax, dword ptr [esi + 0x184]`  
     **语义**：构造末尾检查 `cmp eax, ebx`。若延迟初始为 0，立即 `call 0x424ce0` 启动音效与动画；若大于 0 则挂起。
  3. `0x00422809`（FO: `0x022809`）`89 9E 84 01 00 00`：`mov dword ptr [esi + 0x184], ebx`  
     **语义**：第二构造/初始化函数 `0x422720` 中，将该倒计时显式清零。
  4. `0x00422C70`（FO: `0x022C70`）`8B 81 84 01 00 00`：`mov eax, dword ptr [ecx + 0x184]`  
     **语义**：`AnimClass::DrawIfVisible` 门控：`test eax, eax; je 0x422c7f; xor al, al; ret 0xc`。**只要延迟未归零（`Delay > 0`），强制返回 false，跳过本帧全部渲染**。
  5. `0x00424386`（FO: `0x024386`）`8B 86 84 01 00 00`：`mov eax, dword ptr [esi + 0x184]`  
  6. `0x00424393`（FO: `0x024393`）`89 86 84 01 00 00`：`mov dword ptr [esi + 0x184], eax`  
     **语义**：`AnimClass::Update` 核心步进：
     ```asm
     00424386  mov eax, [esi+0x184]
     0042438C  test eax, eax
     0042438E  je 0x4243ae          ; 延迟已为0，执行正常动画进度
     00424390  dec eax              ; 延迟递减 1 帧
     00424391  test eax, eax
     00424393  mov [esi+0x184], eax ; 回写倒计时
     00424399  jne 0x424b42         ; 仍大于0，直接跳出 Update，不推动画帧、不造成伤害
     0042439F  mov ecx, esi
     004243A1  call 0x424ce0        ; 恰好减至0！触发开播音效与初始逻辑
     004243AD  ret
     ```
  7. `0x004247E5`（FO: `0x0247E5`）`89 86 84 01 00 00`：`mov dword ptr [esi + 0x184], eax`  
     **语义**：单次循环结束时，从 `AnimTypeClass+0x2E0`（`RandomLoopDelay`）读取区间，调用随机数生成器 `call 0x65c7e0`，生成下一轮迭代的延迟帧数，写回 `+0x184` 重新挂起。
  8. `0x00425472`（FO: `0x025472`）`8B 86 84 01 00 00`：`mov eax, dword ptr [esi + 0x184]`  
     **语义**：`AnimClass::Save`（`IPersistStream`）持久化序列化，调用 `0x4a1d50` 写入存档流。
- **生命周期总结**：创建阶段由 INI/开火逻辑初始化 $\to$ 挂起阶段在 `Update` 中逐帧 `dec`（同时被 `DrawIfVisible` 隐藏）$\to$ 减至 0 时触发 `0x424ce0` 进入活跃播放 $\to$ 循环时重新随机置位挂起 $\to$ 随动画析构终结。

---

#### Q2: `IsFogged` 写点与淡出公式闭环 [实证]

- **写点 1（建筑附属动画迷雾标记，`+0x199`）**：
  - 地址：`0x004519B2`（FO: `0x0519B2`）`C6 85 99 01 00 00 01`：`mov byte ptr [ebp + 0x199], 1`
  - 上下文：在 `BuildingClass` 为建筑创建附属动画（`0x451970`）时，读取宿主建筑迷雾状态：
    ```asm
    004519A8  mov al, byte ptr [esi + 0x6e7] ; BuildingClass.IsFogged
    004519AE  test al, al
    004519B0  je 0x4519b9
    004519B2  mov byte ptr [ebp + 0x199], 1  ; AnimClass.IsFogged = true
    ```
- **写点 2（地表视野不可见标记，`+0x19d`）**：
  - 地址：`0x00423B5C`（FO: `0x023B5C`）`88 96 9D 01 00 00`：`mov byte ptr [esi + 0x19d], dl`
  - 上下文：在 `AnimClass::AI`（`0x00423AC0`，虚表槽 23）中，读取动画世界坐标并转换格坐标，调用 `CellClass::IsVisibleTo`（`0x0043B4C0`）。若对当前观察方不可见，则 `sete dl`，向 `+0x19d` 写入 1。
- **绘制期门控行为（`AnimClass::Draw` `0x00422CA0`）**：
  - 检查点 1（`+0x19d` 地表不可见）：
    ```asm
    00422FEC  mov al, byte ptr [esi + 0x19d]
    00422FF2  test al, al
    00422FF4  jne 0x4238a3       ; 直接跳至函数末尾 ret 8，硬切剔除！
    ```
  - 检查点 2（`+0x199` 建筑迷雾标记）：
    ```asm
    00423014  mov cl, byte ptr [esi + 0x199] ; IsFogged
    0042301A  test cl, cl
    0042301C  je 0x42302c
    0042301E  mov cl, byte ptr [eax + 0x374] ; AnimTypeClass.ShouldFogRemove (INI: ShouldFogRemove)
    00423024  test cl, cl
    00423026  jne 0x4238a3       ; 若 IsFogged 且 ShouldFogRemove=yes，硬切剔除！
    ```
  - 检查点 3（黑雾环境光压暗，`0x00423621`）：
    ```asm
    0042361F  mov ecx, eax                   ; CellClass*
    00423621  call 0x487950                  ; CellClass::IsShrouded
    00423626  test al, al
    00423628  je 0x423630
    0042362A  xor ebp, ebp
    0042362C  mov dword ptr [esp + 0x1c], ebp ; 环境光 16 位颜色置 0 (全黑)
    ```
- **淡出公式结论**：**原版游戏不存在任何非平凡的平滑渐变淡出数学公式**。原版对迷雾中的动画仅提供两种处理：
  1. 布尔硬剔除（Hard Culled）：满足 `+0x19d` 或 `+0x199 && ShouldFogRemove` 时，一律跳转到 `0x4238A3` 退出，消耗 0 像素填充率；
  2. 黑雾调色降级：若动画未被剔除但地性格处于黑雾（Shroud），其 16 位光照 Tint 颜色被置零（全黑），仍按原始 Translucency 正常走 Blitter。

---

#### Q3: 列表数据源 `0x8A0394` / `0x8A03A0` 交叉引用定谳 [实证]

- **基址与结构识别**：
  - 全局静态基址 `0x008A0360` 映射为 `MapClass::ObjectsInLayers[5]`（5 个连续的 `LayerClass`，每个结构体占用 `0x18` 字节，继承自 `DynamicVectorClass<ObjectClass*>`）。
  - 图层偏移计算公式：`LayerBase = 0x008A0360 + LayerIndex * 0x18`。
  - 各图层地址分布：
    - Layer 0 (`Underground`): `0x008A0360`
    - Layer 1 (`Surface`): `0x008A0378`
    - **Layer 2 (`Ground` 地面层)**: **`0x008A0390`**  
      - `+0x00`: vtable
      - **`+0x04`: Items 指针 (`0x008A0394`)**
      - `+0x08`: Capacity (`0x008A0398`)
      - `+0x0C`: IsAllocated / IsInitialized (`0x008A039C`)
      - **`+0x10`: Count 元素计数 (`0x008A03A0`)**
    - Layer 3 (`Air`): `0x008A03A8`
    - Layer 4 (`Top`): `0x008A03C0`
- **入队证据**（`0x004A9739`）：
  ```asm
  004A9739  mov eax, [esi]
  004A973D  call [eax+0x78]    ; call ObjectClass::InWhichLayer()
  004A9740  mov edi, eax       ; edi = layer
  004A9747  cmp edi, 2         ; 判断是否为地面层
  004A974A  lea edx, [edi+edi*2]
  004A974D  sete cl            ; 若是地面层，设置 sorted=true
  004A9750  push ecx
  004A9751  push esi
  004A9752  lea ecx, [edx*8 + 0x8a0360] ; ecx = 0x8a0360 + layer * 24
  004A9759  call 0x5519b0      ; LayerClass::AddObject
  ```
- **遍历用途确证**：
  1. `0x006D97D0` / `0x006D9920`：在视口局部脏矩形（Dirty Rect）循环中遍历地面层 `0x8A0394`，过滤出建筑物（`WhatAmI == 6`）与地面特殊对象，调用 `DrawIfVisible` 重绘；
  2. `0x004AE00B` / `0x004AE0D3`：在 UI 辅助层遍历地面层对象，调用 `DrawExtras(v[68])` 绘制血条与选取框；
  3. `0x0048286C`：进行地表格子对象距离与空间测试。

---

#### Q4: `0x556D40` 归属实证闭环（既非 EBolt 亦非 RadBeam）[实证]

- **函数入口**：`0x00556D40`（FO: `0x156D40`）。
- **真实身份**：**`LineTrail::DrawAll`（或 `LineTrailClass::DrawAll`，全量抛射体拖尾线迹绘制）**。
- **实证证据链**：
  1. **遍历全局集合**：`0x556D40` 内部循环遍历全局向量 `0x00ABCB78`（`DynamicVectorClass<LineTrail*>`），其元素指针位于 `0x00ABCB7C`，计数位于 `0x00ABCB88`。
  2. **宿主对象字段解绑**：在销毁/清理死线迹时（`0x00556E14`）：
     ```asm
     00556E0D  mov eax, dword ptr [esi + 4]    ; esi 为 LineTrail*，+4 为 Owner (ObjectClass*)
     00556E10  cmp eax, ebx
     00556E12  je 0x556e1d
     00556E14  mov dword ptr [eax + 0xa8], ebx ; 将 Owner+0xA8 置 NULL !
     ```
     根据 YRpp `ObjectClass.h`，`+0xA8` 正是 `LineTrail* LineTrailer` 指针。
  3. **单实例绘制调用**：遍历中活跃的尾迹线在 `0x00556DD2` 调用 `call 0x00556C00`（`LineTrail::Draw`），内部包含将三维轨迹坐标序列转换为连续多边形段写入目标表面的矢量画线微核。
  4. **枢纽调用位置**：在战术绘制总函数 `0x006D3D10`（`MapClass::DrawIt`）中，`0x006D4673` 唯一调用 `call 0x556d40`，严格紧随 `EBolt::DrawAll(0x4C2830)` 之后，位于 `RadBeam::DrawAll(0x6591B0)` 之前。

---

#### Q5: 己方激光是否恒画决策分析 [实证 + 推演]

- **原版二进制行为 [实证]**：
  - `LaserDraw::DrawAll`（`0x00550240`）对 `0x00ABC878` 向量实施无条件倒序遍历绘制，不查阵营、不查迷雾，原版中**所有激光无差别恒画**；
  - `LaserDrawClass` 实例内存尺寸仅 `0x5C`（92 字节），包含起点/终点坐标（`+0x24`/`+0x30`）、颜色通道、粗细、时长等，**类内部无任何 Owner 或 House 成员指针**。
- **剔除策略定谳 [推演]**：
  - **推荐基线方案（两端点双向 OR）**：
    $$\text{ShouldDrawLaser} = s\_visionGrid[\text{cell}(Source)] \lor s\_visionGrid[\text{cell}(Target)]$$
    - **己方激光必然恒画**：己方单位/建筑开火时，发射源点（$Source$）必然位于玩家本方视野覆盖格内，判定恒为 true；
    - **受击反馈必然可见**：敌方从黑雾中向我方单位/建筑射击时，目标点（$Target$）位于我方视野格内，判定为 true，玩家能看清被攻击的激光来向；
    - **仅黑雾暗算被裁撤**：敌方在完全未探索或裂缝覆盖的黑暗区域内自相交火或摧毁中立目标时，$Source$ 与 $Target$ 均无直视，激光被精准剔除，杜绝全图声光泄密。
  - **备选极致方案（开火挂钩登记）**：若需在极端被盲目（己方被裂缝完全屏蔽）状态下依然强制绘制己方开火激光，可在武器开火点（`0x006FD42B` 及 `0x0044AC9E`）挂钩，在 `LaserDrawClass::ctor` 执行完毕后将其 `this` 地址记录于 DLL 内部的 `s_friendlyLasers` 集合；在 `0x550240` 循环体内直接放行集合内的激光指针。

---

#### Q6: 主视图与局部脏矩形双路径重复绘制计数方案 [实证 + 推演]

- **路径归属反查 [实证]**：
  全可执行文件 `.text` 节区仅有 7 处调用虚表槽 65（`call [edx+0x104]` 即 `DrawIfVisible`）：
  - **主视图主绘制流**：`0x006D8DB0` 内 3 处（`0x006D909E`、`0x006D916C`、`0x006D93FA`）；
  - **视口脏矩形重绘流**：`0x006D97D0`（`0x006D98E9`）与 `0x006D9920`（`0x006D9A21`）；
  - **建筑子部件自绘**：`0x0043E6B7` 与 `0x0043E788`。
  - 小地图（`RadarClass`）**零调用** `DrawIfVisible`。
- **重复绘制计数与遥测监控方案 [推演]**：
  在 `ra2render` 内部设计无锁帧期位图统计，架构如下：
  ```cpp
  struct ObjectDrawStats {
      uint32_t frameId = 0;
      uint32_t totalDrawCalls = 0;
      uint32_t uniqueObjects = 0;
      uint32_t duplicateCalls = 0;
      uint32_t pathMainCalls = 0;     // 来自 0x6D8DB0
      uint32_t pathDirtyCalls = 0;    // 来自 0x6D97D0 / 0x6D9920
      uint32_t pathSubCalls = 0;      // 来自 0x43E6B7 等
  };

  // 挂钩 0x005F4B10 (ObjectClass::DrawIfVisible 共享入口)
  bool __stdcall Hook_DrawIfVisible(RectangleStruct* pBounds, bool EvenIfCloaked, DWORD dwUnk3) {
      ObjectClass* pThis = ...; // 获取 ecx / this 指针
      void* callerEIP = _ReturnAddress();

      g_stats.totalDrawCalls++;
      if (callerEIP >= (void*)0x6D8DB0 && callerEIP < (void*)0x6D9410) {
          g_stats.pathMainCalls++;
      } else if (callerEIP >= (void*)0x6D97D0 && callerEIP < (void*)0x6D9A50) {
          g_stats.pathDirtyCalls++;
      } else {
          g_stats.pathSubCalls++;
      }

      // 幂等重复检测
      if (s_drawnObjectsFrameSet.find(pThis) != s_drawnObjectsFrameSet.end()) {
          g_stats.duplicateCalls++;
      } else {
          s_drawnObjectsFrameSet.insert(pThis);
          g_stats.uniqueObjects++;
      }

      return Original_DrawIfVisible(pBounds, EvenIfCloaked, dwUnk3);
  }
  ```
  在帧循环起点 `0x006D3D10` 清空 `s_drawnObjectsFrameSet`，在帧末尾输出遥测日志，可精确验证双路径重复率。

---

#### Q7: `ParticleSystem SpotlightRadius` 填充率分析与抗爆炸雪崩策略 [实证 + 推演]

- **微核执行链路 [实证]**：
  1. `ParticleSystemClass::Draw`（`0x0062E280`）从 `[edi + 0xF4]` 提取 `SpotlightRadius`（默认 29），写入临时 `SpotlightClass+0xC`，调用 `SpotlightClass::Draw(0x005FF850)`；
  2. `0x005FF850` 根据半径查表 `0x83358c` 计算光锥多边形，裁剪到屏幕后设定最大包围盒尺寸为 **$W=255, H=127$**（`0x5ff916` 宽 255，`0x5ff91e` 高 127，等价于 $256 \times 128$ 像素矩形）；
  3. 软件光栅化核（如 `0x007DF191`）执行双层像素循环：
     - 外层高 $H$，内层宽 $W$；
     - 对掩码中非零像素，从 `[edi]` 读取 16 位目标色彩，拆分 RGB565/555 三通道，执行 32 位整数乘法 `imul ebx, [ebp - 0x18]`，进行饱和截断相加后写回目标表面。
- **定量 Fillrate 与 CPU 负载模型 [推演]**：
  - 单个聚光灯包围盒总采样点：$256 \times 128 = 32,768$ 像素；
  - 800×600 分辨率总像素量为 480,000 像素，单个聚光灯占全屏面积的 **6.8%**；
  - 密集爆炸场景下（例如基洛夫/V3齐射、核弹、闪电风暴引发的连续粒子系统），若同屏活跃 10 个 `ParticleSystem`，仅 Spotlight 遍历量就达 **327,680 像素（占全屏 68.3% 的总填充率）**；
  - 每个非零混合像素需消耗约 30 条 CPU 指令（无 SIMD 加速的纯软件循环）。10 个聚光灯每帧消耗 **500 万～660 万条 CPU 指令**，在 60 FPS 下每秒耗费超过 3 亿次 CPU 周期，是造成特效卡顿的核心瓶颈。
- **优化与防雪崩方案 [推演]**：
  1. **迷雾硬短路**：在 `0x0062E280` 调用 `0x005FF850` 前，检测宿主粒子系统所在世界格是否位于 `s_visionGrid`，若无直视视野直接跳过光照锥创建与绘制，节省 100% 雾中聚光灯填充率；
  2. **最大同屏限频**：限制单帧绘制的聚光灯上限（如 $\le 4$ 个），超出部分仅画粒子本体跳过 Spotlight 锥面叠加；
  3. **SIMD 矢量化替换**：将 `0x7DF191` 等 6 种软件混合微核使用 SSE2/AVX2 重写为 8 像素并行饱和加法，可将光栅化开销降低 80% 以上。

