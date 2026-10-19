# VXL 载具体素渲染 / 阴影 / Z 序 —— 地址级逆向

> 目标：`gamemd.exe`（尤里的复仇 1.001）ImageBase `0x400000`，偏移 = VA − `0x400000`。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 本文为纯逆向产出（无代码补丁），不修改总档案 `REVERSE_ENGINEERING_AND_PATCHES.md` 与 `ra2render` 源码/dll。
> 证据来源：**[实证]** = capstone 反汇编取证（`out/re_work/vxl_re*.py` + `*_out.txt`）；**[YRpp]** = 社区 ABI 头；**[推演]** = 字段序/行为链推导。
> 用途：为性能优化（缓存 / LOD / 限频）与迷雾剔除提供 **Hook 点表**。确定性红线与 `fx_draw_chain.md` §6 一致：**只拦绘制，绝不写逻辑状态**。

---

## 0. 结论速览

| 问题 | 结论 |
|---|---|
| VXL 绘制入口在哪？ | **`UnitClass::Draw`（v[69] `0x0073CEC0`）** 按 `UnitType+0x236`（IsVoxel）分流：**`DrawAsVXL`（v[341] `0x0073B470`）** 或 `DrawAsSHP`（v[342] `0x0073C5F0`）。两者经 FootClass 虚表槽 **324 / 323** 调 **`Draw_A_VXL` / `Draw_A_SHP`**。 |
| `Draw_A_VXL` 真身？ | FootClass 默认体 **`0x004DAF10`**（薄封装：拷 Matrix + 用 Locomotor `Draw_Point` 修正中心）→ **`TechnoClass` 核心 `0x00706640`**（拼 BlitterFlags、选 Convert/Blitter）→ **`0x00707480`**（体素光栅 + Blit）。炮塔/炮管走 **`0x00706BD0` / `0x00706ED0` / `0x00707280`** 旁路，最终同样进 `0x753C70` + `0x707480`。 |
| 旋转矩阵谁给？ | **`ILocomotion::Draw_Matrix` / `Shadow_Matrix`**（v[9]/v[10]）。默认 `0x0055A730` / `0x0055A7D0`；Drive `0x4AFF60`/`0x4B0410`、Fly `0x4CF610`/`0x4CFB00`、Hover `0x513F40`/`0x5142A0`、Ship `0x69F670`/`0x69FB20`、Tunnel `0x729B40` 等覆写。矩阵为 `Matrix3DStruct`（12×f32）。阴影矩阵查 **全局表 `0xB45188`**（每向 0x30 字节）。 |
| 缩放怎么进？ | 矩阵由 Loco 按朝向/速度构造；`UnitType+0x720`（`fild` 后乘 `0xB1D008`）作整体缩放/倾角；`DrawAsVXL` 内 `0x5AE980`/`0x5AE610`/`0x5AF1A0` 做矩阵合成。**没有独立 Scale 参数**——缩放编在 3×4 矩阵里。 |
| 调色 / 光照怎么进 Blit？ | `ConvertClass`（`FileSystem::UNITx_PAL` @ `0x87F6B4` 等）→ **`SelectRLEBlitter(BlitterFlags)` `0x00490E50`**（VXL 走 RLE 族）/ `SelectPlainBlitter` `0x00490B90`。Blitter 的 `Data` 指向 LightConvert 调色缓冲。VXL 光照在 `0x753E00` / `0x753F90` / `0x7542F0` 算完再进 Blit。 |
| Voxel 缓存是什么？ | **`SomeVoxelCache`**（YRpp `GeneralStructures.h:342`：`ptr, f_4, f_8, f_C, ptr_10`）。`ObjectTypeClass` 持 **`VoxelCaches[4]`**；`DrawAsVXL` 用 **`Type+0x258`（主车体）与 `Type+0x280`（炮塔）** 两份。查找 **`0x007107E0`**（key 命中则 `ptr_10=cached`）、探测 **`0x00746EA0`**。命中后**跳过矩阵重算**，直接复用缓存矩阵/光栅结果。`TechnoTypeClass.DisableVoxelCache` / `DisableShadowCache` 可关。 |
| HVA 帧号怎么用？ | `Draw_A_VXL(VXL, HVAFrameIndex, …)`。`DrawAsVXL` 用 `Unit+0x538` / `Unit+0x148` **对 `VoxLib` 尾块的 `+8`（帧数）取模**得到 HVA 帧；炮塔帧单独取模。**同帧号 + 同朝向 = 同缓存键**，可命中。 |
| 阴影路径？ | 车体阴影在 `UnitClass::Draw` **主体之前**（`0x73D0E3` 起，`Type+0xE0E` NoShadow / `Unit+0x6D2` 门）：Loco **`Shadow_Matrix`** → `0x7559B0` 取阴影投影矩阵 → **Darken 族 Blit**（`BlitTransDarken*` / `RLEBlitTransDarken*`，`DarkenMask=0x7BEF`）。SHP 炮塔影子走 `0x4AED70` + flags `0xA00`。与 `blitter_microkernel_deep_dive.md` 的 Darken 微内核直接衔接。 |
| Z 序谁维护？ | **两层**：① **对象遍历序** = `Map DrawIt 0x6D3D10` → **`0x6D8DB0`** 按绘制协调层列表顺序 `DrawBehind → DrawExtras → DrawIfVisible`（**不是深度排序**，是列表序）；② **逐像素 Z** = Blit 族的 **ZRead / ZReadWrite** 比较/写入 **`ZBuffer`（全局 `0x887644`）**。`Draw_Matrix` 的 `key` 输出打包 **`(Z阶梯<<5) | (facing&0x1F)`**；阴影键另含 `ShadowIndex`。 |
| 乱序会怎样？ | 若两单位重叠且都走 **ZRead/ZReadWrite**：后画的按 Z 比较被拒像素 → **遮挡仍正确**。若走 **Flat（flags `0x2000`）无 Z**：后画覆盖先画 → **遮挡错误**。阴影若在本体之后用 Darken 且无 Z 测试 → **把自己压黑**。原版顺序是「先影后体」，改序必坏。 |
| VXL vs SHP 成本？ | SHP = 8-bit 帧 + RLE Blit（帧已预渲染）。VXL = **每帧软件体素光栅**（`0x437A10` 跨步填充 + 光照 `0x753E*`）+ Blit。同屏 N 辆坦克：VXL ≈ N×(矩阵合成 + 体素遍历 + Blit)；SHP ≈ N×(帧查找 + RLE Blit)。**缓存命中时 VXL 退化为接近 SHP**。 |
| 迷雾中还算矩阵吗？ | **不算**。矩阵只在 `DrawAsVXL`（被 `Draw` 调）里合成，而 `Draw` 只在 `DrawIfVisible` 通过后才跑。`0x6D8DB0` 协调层在调 `DrawIfVisible` **之前**已做 `IsCellShrouded(0x5865E0)`。**在 `DrawIfVisible` / 协调层短路即可省掉全部矩阵/光栅**。 |
| Hook 方案 | 见 §6。优先 **`UnitClass::DrawIfVisible` `0x73B0B0` / 共享体 `0x5F4B10`** 与 **`DrawAsVXL` `0x73B470`**；缓存/性能在 `0x7107E0` 与 `0x707480`；阴影在 `Shadow_Matrix` 与 Darken Blit。 |

---

## 1. 数据结构与 ABI

### 1.1 VXL / HVA 资源

```cpp
// YRpp FileSystem.h:17
struct VoxelStruct { VoxLib* VXL; MotLib* HVA; };

// YRpp FileFormats/VXL.h
class VoxLib {
    bool Initialized; DWORD CountHeaders, CountTailers, TotalSize;
    VoxelSectionHeader* HeaderData;
    VoxelSectionTailer* TailerData;
    byte* BodyData;
    VoxLib(CCFileClass*, bool)   // 0x755CD0
    ~VoxLib()                    // 0x755D10
    ReadFile(...)                // 0x755DB0
    leaSectionHeader(int)        // 0x7564A0
    leaSectionTailer(int,int)    // 0x7564B0
};
// SectionTailer: span_start/end/data_off, HVAMultiplier, TransformMatrix(3×Vector4),
//                MinBounds, MaxBounds, size_X/Y/Z, NormalsMode
```

`ObjectTypeClass`（YRpp:73–112）持有：

| 字段 | 含义 |
|---|---|
| `MainVoxel / TurretVoxel / BarrelVoxel` | `VoxelStruct{VXL,HVA}` 三件套 |
| `ChargerTurrets[0x12] / ChargerBarrels[0x12]` | 充能炮管变体 |
| `VoxelCaches[4]` | **`SomeVoxelCache`**（见 §3） |

### 1.2 矩阵

```cpp
// YRpp BasicStructures.h:124
struct Matrix3DStruct { float Data[12]; };   // 3×4 行主序，含平移列

// YRpp Interfaces.h:150 / LocomotionClass.h:77
Matrix3DStruct* __stdcall Draw_Matrix(Matrix3DStruct* pMatrix, int* key);   // v[9]
Matrix3DStruct* __stdcall Shadow_Matrix(Matrix3DStruct* pMatrix, int* key); // v[10]
Point2D*        __stdcall Shadow_Point(Point2D*);                           // v[12]
ZGradient       __stdcall Z_Gradient();                                     // v[14]
```

**`key` 出参**（实证 `0x55A730` 尾部）：`*key = (zBucket << 5) | (facing & 0x1F)`，其中 `zBucket = ((raw>>10)+1)>>1 & 0x1F` 再 `-8`（Draw）或混入 `ShadowIndex`（Shadow：`((raw<<6)+shadowIdx)<<5 | facing`）。这是 **ZBuffer 写入用的深度键**，不是对象排序键。

阴影投影矩阵来自 **全局表 `0xB45188`**：

```asm
; 0x7559B0 — 按朝向索引拷贝 0x30 字节矩阵
lea esi, [edx+edx*2]; shl esi, 4        ; esi = facing * 48
add esi, 0xB45188
mov ecx, 0xC; rep movsd                 ; 12 float
```

调用点遍布 Loco 覆写（Drive `0x4AFF60`、Fly `0x4CFB00`、Hover `0x513F40`、Ship `0x69F670`、Tunnel `0x729B40` 等 14 处）。

### 1.3 BlitterFlags（进 Blit 的最终编码）

YRpp `GeneralDefinitions.h:1319`：

| 位 | 名 | VXL 路径中的用法 [实证] |
|---|---|---|
| `0x1` | Darken | **阴影**（`& DarkenMask 0x7BEF`） |
| `0x2/0x4/0x6` | TransLucent25/50/75 | 叠加/半透明 |
| `0x8` | Warp | 倾斜/水下扭曲 |
| `0x10` | ZRemap | 深度重映射 |
| `0x20` | Plain | 无透明 |
| `0x800` | Alpha | VXL 核心 **恒 OR `0x800`**（`0x70674D`） |
| `0x2000` | Flat | VXL 起始标志（`0x70664F mov esi, 0x2000`） |
| `0x3000` | ZRead | 深度测试 |
| `0x4000` | ZReadWrite | 深度测试+写 |

`0x706640` 中按 `WhatAmI` 跳表（`0x706BB8`）装入 `0x200A / 0x200C / 0x2002 / 0x2004` 等组合，再按隐身/建筑状态 OR `0x2006 / 0x2004`。

---

## 2. 绘制管线

### 2.1 总链

```
Map DrawIt  0x006D3D10
  └─ Object 协调  0x006D8DB0
       ├─ IsCellShrouded 0x5865E0          ← 迷雾门（协调层，绘制前）
       ├─ DrawBehind   v[67] +0x10C
       ├─ DrawExtras   v[68] +0x110
       └─ DrawIfVisible v[65] +0x104
            └─ 视口裁剪 0x6D2140
                 └─ Draw v[69] +0x114
                      │
                      ├─ UnitClass::Draw  0x73CEC0
                      │    ├─ [阴影] Type+0xE0E / +0x6D2 门
                      │    │    └─ Loco Shadow_Matrix → 0x7559B0 → Darken Blit
                      │    ├─ Type+0x236 ?
                      │    │    ├─ 1 → DrawAsVXL  v[341] 0x73B470
                      │    │    │      ├─ Loco Draw_Matrix (+ key)
                      │    │    │      ├─ SomeVoxelCache 命中?  0x7107E0
                      │    │    │      ├─ 否 → 矩阵合成 0x5AE980/0x5AF1A0
                      │    │    │      └─ Draw_A_VXL  v[324] 0x4DAF10
                      │    │    │           └─ 0x706640  (flags + Convert)
                      │    │    │                └─ 0x707480  (光栅 + Blit)
                      │    │    └─ 0 → DrawAsSHP  v[342] 0x73C5F0
                      │    │           └─ Draw_A_SHP v[323] 0x41C090 → 0x705E00
                      │    └─ [炮塔/炮管 VXL] 0x706BD0 / 0x706ED0 / 0x707280
                      │         └─ 0x753C70 + 0x707480
                      │
                      └─ 其他 Object（Bullet/Anim/… 见 fx_draw_chain.md）
```

### 2.2 `UnitClass::Draw` `0x0073CEC0` [实证]

关键分支（尾部 `0x73D2D0`–`0x73D395`）：

```asm
0073D317  mov  al, [edi+0x236]     ; UnitType.IsVoxel
0073D31D  test al, al
0073D31F  je   0x73d361            ; → DrawAsSHP
0073D321  mov  eax, [edi+0xb0]     ; MainVoxel.VXL 非空?
0073D329  je   0x73d395            ; 空则跳过
        … 拷 RectangleStruct / Point2D …
0073D359  call [edx+0x554]         ; ★ DrawAsVXL (v[341])
0073D35F  jmp  0x73d395
0073D38F  call [edx+0x558]         ; DrawAsSHP (v[342])
```

阴影段（**先于** VXL/SHP 主体，在 `0x73D0E3`）：

```asm
0073D0DB  mov  al, [edx+0xe0e]     ; Type.NoShadow
0073D0E1  je   0x73d298            ; NoShadow → 跳过阴影
0073D0E9  mov  al, [esi+0x6d2]     ; 单位阴影开关
0073D0F1  je   0x73d298
0073D0F7  mov  eax, [esi+0x674]    ; Locomotor (ILocomotion*)
0073D114  call [ecx+0x80]          ; Is_To_Have_Shadow
… 0x4C93D0 取朝向 → Z 键打包 → Shadow_Matrix / Shadow_Point …
```

炮塔影子/附加在 `0x73D3CC push 0xA00` + `call 0x4AED70`（SHP 形状绘制，flags 含 Alpha）。

### 2.3 `DrawAsVXL` `0x0073B470` [实证]

1. 读 `Unit+0x6C4`（`UnitTypeClass*`），可被 `+0x6E0`/`Type+0x6B8` 覆盖（变形单位）。
2. **HVA 帧**：`Unit+0x538` / `Unit+0x148` 对 `Type+0xB4` / `Type+0xBC`（HVA）的 `+8` **取模**。
3. 换全局绘制状态 `0x887314`，置 `Unit+0x6D3=1`（绘制中标志）。
4. **Loco Draw_Matrix**（`this+0x674`，`call [edx+0x2C]`）→ 矩阵拷入栈。
5. **缓存查询**（§3）：`Type+0x258` / `Type+0x280` → `0x746EA0` / `0x7107E0`。
   - 命中：`rep movsd` 复用缓存矩阵，**跳过** `0x73BA4C` 起的合成。
   - 未命中：`0x5AE980`（缩放/倾角，`fild [Type+0x720] * 0xB1D008`）+ `0x4C93D0`（朝向）→ 重算。
6. 组装参数，**`call [edi+0x510]` = Draw_A_VXL**（本体 `MainVoxel`，`Type+0xB0`）。
7. Z 键二次打包（`and esi, 0x1F; or esi, facing`）+ `Type+0x720==0` 时 `and esi, 0xFFFFFC1F`（清 Z 桶）。
8. 炮塔/炮管重复 5–7（`Type+0xC0/0xC4` 等）。

### 2.4 `Draw_A_VXL` 三层

| 层 | 地址 | 职责 |
|---|---|---|
| 薄封装 | **`0x004DAF10`**（Foot/Unit/Aircraft 共用，v[324]） | `rep movsd` 拷 12-float 矩阵；若 `Foot+0x674`（Loco）非空，`call [edx+0x2C]` 取 **`Draw_Point`** 修正 `CenterPoint`；`ret 0x28` |
| 标志/Convert | **`0x00706640`** | 初始 `esi=0x2000`（Flat）；`WhatAmI` 跳表装 `0x200A/0x200C/0x2002/0x2004`；隐身/建筑再 OR；`OR 0x800`；`Type+0x21C → 0x50B6F0`；`v[0x43C]` 混色；`v[0x464]` 取 LightConvert；缓存对象 `0x7107E0`；最终 **`call 0x707480`** |
| 光栅+Blit | **`0x00707480`** | `0x4AEC60` 求包围盒；`0x43AD00` 分配临时缓冲；**`SelectRLEBlitter 0x490E50`**（flags 去 `0x10`）；WhatAmI==1 且 `+0x6D3` 用全局 `0xB1D140`；脏矩形并入 `0xB1CFC0..0xB1CFCC`；`v[0x2F0]/v[0x2EC]` 后 **`0x437A10`**（跨步光栅，查表 `0x817710`） |

> `0x706640` 的 `fn_end` 就是 **`0x706BD0`**（下一个函数）——后者是炮塔/第二件 VXL 路径，同样收束到 `0x707480` 与 `0x753C70`（`0x706A06/0x706AF2/0x706D47/0x706E46`）。

### 2.5 VoxelAnim（弹片）对照

`VoxelAnimClass::Draw 0x00749B70`（`fx_draw_chain.md` §2.6）：`IsCellShrouded → 0x4399E0（矩阵）→ 0x753E00/0x753F90/0x7542F0（光照）→ 0x6D20E0 → SelectPlainBlitter 0x490B90(flags=0x2001) → 0x753C70 → 0x4AF2A0`。**与载具 VXL 共享 `0x753C70` 绘制核**，但用 **Plain** 而非 RLE（弹片体素更碎）。

---

## 3. Voxel 缓存（SomeVoxelCache / HVA 帧）

### 3.1 结构 [YRpp + 实证]

```cpp
struct SomeVoxelCache {   // YRpp GeneralStructures.h:342，0x14 字节
    void*  ptr;      // +0  缓存池/描述
    DWORD  f_4;      // +4  非空才继续查
    DWORD  f_8;
    BYTE   f_C;
    DWORD* ptr_10;   // +10 命中后的条目（后续 +4 读位图/矩阵）
};
```

| 用途 | 宿主偏移 | 查询函数 |
|---|---|---|
| 主车体 | `ObjectTypeClass+0x258` | `0x746EA0`（探测）→ `0x7107E0`（命中装填） |
| 炮塔 | `ObjectTypeClass+0x280` | 同上 |
| `Draw_A_VXL` 内 | 参数 `SomeVoxelCache*` | `0x7107E0`（`0x70682F`） |

`0x7107E0` 极短：`if (!cache->f_4) return 0;` 否则 `call 0x7C8B48`（键比较/查表），命中写 `cache->ptr_10 = entry`。返回入口地址，调用方 `add eax, 4` 后取内容。

### 3.2 缓存键与失效

**键 = HVA 帧号 + 朝向桶 + 阴影标志**（实证 `0x73B74C`–`0x73B79F`）：

```asm
… and esi, 0x1F; or esi, facing_bucket
… Type+0x720==0 ? and esi, 0xFFFFFC1F
… or esi, (extraByte << 0x10)
```

- **同帧号 + 同朝向 + 同缩放开关** → 命中，**不重复软件渲染**。
- 车体在动（朝向变）→ 键变 → 必然 miss（原版 VXL 旋转代价所在）。
- `TechnoTypeClass.DisableVoxelCache` / **`DisableShadowCache`**（YRpp:502–503）可对特殊单位关闭。
- 缓存宿主在 **Type（类型）** 而非实例：**同型号多辆坦克共享缓存**——静止同朝向的 N 辆车只有 1 次光栅。

### 3.3 HVA 帧

`Draw_A_VXL(..., HVAFrameIndex, ...)`。`DrawAsVXL` 计算：

```
frame = Unit+0x538  % (MainHVA+8)          ; 车体
frame = Unit+0x148  % (TurretHVA+8)        ; 炮塔（仅当 Main 帧==0 时）
```

`VoxLib` 的 `HVAMultiplier`（SectionTailer）参与矩阵缩放（`0x55A730` 中 `fild * 0x7E4408`）。

---

## 4. 阴影绘制路径（Darken Blit）

### 4.1 与 Blit 族的关系

| 形态 | Blitter | 入口 | 文档 |
|---|---|---|---|
| SHP 步兵影（RLE） | `RLEBlitTransDarken@G` | `0x00496250`（vt `0x7E55A0`） | `blitter_microkernel_deep_dive.md` §3.3 |
| SHP 步兵影+Z | `RLEBlitTransDarkenZRead@G` | `0x00496820`（vt `0x7E5540`） | 同上 §3.2 |
| **载具/建筑 VXL·SHP 影** | **`BlitTransDarkenZRead@G`** | **`0x00492D20`**（vt `0x7E5948`） | 同上 §3.6 |
| 非 Z Darken | `BlitTransDarken@G` | `0x00492670`（vt `0x7E59F0`） | 同上 |

**共同语义**：`*dst = (*dst >> 1) & this->DarkenMask`，`DarkenMask` 典型 `0x7BEF`（RGB565 减半并清溢出位）。**`this+0x04` 是数值掩码，不是 Xlat 指针**（误用即 `0xC0000005`）。

### 4.2 VXL 阴影链

```
UnitClass::Draw  0x73D0E3
  └─ Type.NoShadow(+0xE0E)?  Unit+0x6D2?
       └─ Loco->Is_To_Have_Shadow()          v[0x80]
            └─ Loco->Shadow_Matrix()         v[10]  (默认 0x55A7D0)
                 ├─ 0x565730  取场景/朝向
                 ├─ 0x7559B0  ← 表 0xB45188[facing]
                 └─ key 打包: ((raw<<6)+ShadowIndex)<<5 | facing
            └─ Loco->Shadow_Point()          v[12]  (0x55A8C0)
       └─ Draw_A_VXL(VXL, frame, Flags|Darken, ShadowCache, …)
            └─ 0x707480 → SelectRLEBlitter(flags含 Darken)
                 └─ RLEBlitTransDarken* / BlitTransDarken*
```

**ShadowIndex** 来自 `TechnoTypeClass.ShadowIndex`（YRpp:368）；`UnitTypeClass.UseTurretShadow`（YRpp:65）控制炮塔影。

### 4.3 顺序不变量

**先影后体**（`0x73D0xx` 在 `0x73D3xx` 之前）。Darken 是「压暗已有像素」，若颠倒：

- 影子落在本体上 → 车体被压黑；
- 两车影叠车体 → 遮挡关系错乱。

带 `ZRead` 的 Darken 可按 Z 拒绝「盖在更近物体上的影」，但 **原版 VXL 影多数仍依赖绘制序**。

---

## 5. 绘制排序（Z 序）

### 5.1 两层模型

| 层 | 维护者 | 依据 | 乱序后果 |
|---|---|---|---|
| **对象间遍历序** | `0x6D8DB0` 按绘制协调层列表 | 列表插入序 ≈ 地图对象序（**非严格深度排序**） | 无 Z 的 Flat/半透明叠加错序 |
| **像素深度** | Blit ZRead/ZReadWrite + `ZBuffer 0x887644` | `Draw_Matrix` 的 `key` / 每像素 Z 梯度 | Z 正确则遮挡仍对；Z 缺失则后画胜出 |

### 5.2 ZGradient

```cpp
enum class ZGradient : int { None=-1, Ground=0, Deg45=1, Deg90=2, Deg135=3 };
```

- `FootClass::Draw_A_SHP` 显式收 `ZGradient` 参数；`TechnoClass::GetZGradient` 虚表可取。
- `ILocomotion::Z_Gradient()`（v[14]）默认 `Deg90`（`LocomotionClass.h:99`）。
- `0x437A10` 光栅用查表 **`0x817710`**（`eax*8` 索引，3 项阶梯）把 Z 梯度映射为跨步 Z 增量。

### 5.3 ZBuffer

全局 **`*(ZBufferClass**)0x887644`**（YRpp `Drawing.h:86`：`Bounds, Surface, BufferStart/End, BufferSizeInBytes, Width, Height`）。Blit 族读写时做 **环形回卷**（`zBuf >= BufferEnd → zBuf -= BufferSize`）——与 `rle_blit_family.md` §、`blitter_microkernel_deep_dive.md` 一致。

### 5.4 乱序实测推演

| 场景 | 无 Z / Flat | ZRead | ZReadWrite |
|---|---|---|---|
| 两坦克前后重叠，列表反序 | 前车被后车覆盖（**错**） | 后车像素按 Z 被拒（**对**） | 对 |
| 影子画在本体后 | 本体变暗（**错**） | 影 Z 更大可被拒（**多半对**） | 对 |
| 跨高程（桥上/桥下） | 必错 | 依赖 Z 梯度正确 | 对 |

**结论**：原版「列表序 + 逐像素 Z」混合；**性能优化若重排对象绘制序，必须保留 ZReadWrite 或维持先影后体**。

---

## 6. 性能与迷雾

### 6.1 VXL vs SHP 成本（同屏 N 坦克）

| 项 | SHP | VXL（冷缓存） | VXL（热缓存） |
|---|---|---|---|
| 几何 | 已预渲染 8-bit 帧 | **每帧体素遍历 + 光照** | 无 |
| 矩阵 | 无 | `Draw_Matrix` + 合成 | 命中跳过 |
| Blit | RLE 一次 | RLE 一次 | RLE 一次 |
| 相对量级 | 1× | **约 5–20×**（视体素数/分辨率） | ~1.2× |

### 6.2 可缓存 / LOD / 限频点（仅绘制层）

| 点 | 机制 | 风险 |
|---|---|---|
| **A. SomeVoxelCache 扩容/预热** | 同型号静止单位共享；预渲染常用朝向 | 低 |
| **B. 朝向量化** | 32 向量化 → 键稳定，命中率↑ | 低（视觉轻微） |
| **C. 远景 LOD** | 小于阈值像素时改画 1/2 分辨率或 SHP 剪影 | 低 |
| **D. 限频** | 静止单位隔帧重光栅（缓存续命） | 低；**禁止改 Update** |
| **E. 阴影降质** | 远景阴影用椭圆 Darken 代替 VXL 影 | 低 |
| **F. 合并 Blit** | 同 Convert/flags 的单位批量 | 低 |
| **禁止** | 在 Update 里限频/跳帧 | **高（确定性）** |

### 6.3 迷雾

| 问题 | 结论 [实证] |
|---|---|
| 雾中是否仍算矩阵？ | **否（只要绘制被短路）**。矩阵仅在 `DrawAsVXL` 内合成；`Draw` 受 `DrawIfVisible` 约束。 |
| 现成迷雾门？ | 协调层 `0x6D8DB0` 调 `IsCellShrouded 0x5865E0`；`UnitClass::DrawIfVisible 0x73B0B0` 另有 Gap/隐身检查（`0x65AD40` + `0x4A5110/5130/51B0/51D0`）。 |
| 能否更早短路？ | **能**。在 `DrawIfVisible`（v[65]）入口或 `0x6D8DB0` 调用点前用 `s_visionGrid` 判定，失败直接跳过 —— 省掉矩阵、缓存查询、光栅、Blit。 |
| 敌方 VXL 在雾中？ | 原版走 `IsCellShrouded`；自建 `s_visionGrid` 谓词与 `fx_draw_chain.md` §5 同构（己方/盟友恒画）。 |

---

## 7. Hook 点表

> 红线：**只拦绘制**。禁止改 `IsShrouded` / `IsCellShrouded` / `RevealArea*` / Update / Loco 逻辑状态。

| # | 目标 | VA / 槽 | 建议改动 | 确定性 |
|---|---|---|---|---|
| **H-VXL1** | `ObjectClass::DrawIfVisible` 共享体 | `0x005F4B10`（v[65]） | 入口 `ShouldDrawObject` 失败 → `xor al,al; ret 0xC` | **低** |
| **H-VXL2** | `UnitClass::DrawIfVisible` | `0x0073B0B0`（Unit v[65]） | 同上（含 Gap 谓词） | **低** |
| **H-VXL3** | `UnitClass::Draw` | `0x0073CEC0`（v[69]） | 迷雾/LOD 总开关；可在此跳阴影段 | **低** |
| **H-VXL4** | **`DrawAsVXL`** | **`0x0073B470`**（v[341]） | 入口短路；或包一层缓存统计 | **低** |
| **H-VXL5** | `Draw_A_VXL` 薄封装 | `0x004DAF10`（v[324]） | 多态覆盖点（Unit/Aircraft 共用） | **低** |
| **H-VXL6** | VXL 标志/Convert 核 | `0x00706640` | 注入 LOD flags / 强制缓存 | **低** |
| **H-VXL7** | **VXL 光栅核** | **`0x00707480`** | 降分辨率光栅；性能计数 | **低** |
| **H-VXL8** | 缓存命中 | `0x007107E0` / `0x00746EA0` | 命中率统计；未命中时预热 | **低** |
| **H-VXL9** | 矩阵提供 | Loco v[9] `Draw_Matrix`（默认 `0x55A730`，Drive `0x4AFF60`，Fly `0x4CF610`…） | 迷雾中跳过（须与 H-VXL1 一致） | **低** |
| **H-VXL10** | 阴影矩阵 | Loco v[10] `Shadow_Matrix`（默认 `0x55A7D0`） | 远景/雾中跳过阴影 | **低** |
| **H-VXL11** | 阴影表 | `0x007559B0`（表 `0xB45188`） | 只读；可做朝向量化索引 | **低** |
| **H-VXL12** | Darken Blit（载具影） | `BlitTransDarkenZRead` `0x00492D20`（vt `0x7E5948`+4） | 已属 L1 微内核；SSE2 化 | **低** |
| **H-VXL13** | RLE Darken | `0x00496250` / `0x00496820` | 同上 | **低** |
| **H-VXL14** | Z 写入光栅 | `0x00437A10`（表 `0x817710`） | 只读理解；勿改 Z 语义 | **中**（改 Z 会坏遮挡） |
| **H-VXL15** | 对象协调序 | `0x006D8DB0` | 仅可加剔除；**勿重排**除非全 ZReadWrite | **中** |
| **H-VXL16** | 第二绘制路径 | `0x6D97D0` / `0x6D9920` | 与 H-VXL1 同谓词（幂等） | **低** |

### 确定性红线

1. **可改**：DrawIfVisible / Draw / DrawAsVXL / Draw_A_VXL / `0x707480` / 缓存 / `s_visionGrid` / Blit。
2. **不可改**：`IsShrouded(0x487950)`、`IsCellShrouded(0x5865E0)`、`RevealArea*`、Loco `Process/Move_To`、Update 寿命/位置、Z 语义（除非全客户端一致）。
3. **先影后体** 顺序保持；重排绘制必须全量 ZReadWrite。
4. 单机/战役：绘制 Hook 不进存档。联机：仅保留红线内 Hook。

---

## 8. 未决问题

| # | 问题 | 现状 | 建议下一步 |
|---|---|---|---|
| Q1 | `SomeVoxelCache` 缓存池实际布局（`ptr`/`f_4`/`f_8` 语义） | 仅见查找/装填调用 | 对 `0x7C8B48`、`0x746EA0` 全文反汇编；看 `VoxelCaches` 构造 |
| Q2 | `DisableVoxelCache` 写点与 INI 键名 | YRpp 有字段 | xref `TechnoTypeClass+0x…`；对照 rulesmd |
| Q3 | `0x817710` Z 梯度表精确数值 | 3 项 `*8` 查表 | dump 该只读表；对照 ZGradient 枚举 |
| Q4 | `0x706BD0/0x706ED0/0x707280` 与本体的部件划分 | 均进 `0x753C70` | 逐个 dump 参数来源（Barrel/ChargerTurret） |
| Q5 | 阴影缓存（`DisableShadowCache`）键是否含 Z 桶 | Draw 键含 Z 桶，Shadow 键含 ShadowIndex | 断点 `0x7107E0` 双路径 |
| Q6 | `Unit+0x6D3` 绘制中标志是否被 Update 读 | `0x73B586` 置 1，`0x7066BA` 读 | xref 写点/读点；若 Update 也读则勿当 Hook 开关 |
| Q7 | 跨高程（桥/悬崖）Z 梯度与 `ZGradient` 覆盖 | Loco v[14] 默认 Deg90 | dump Drive/Ship/Tunnel 的 `Z_Gradient` 覆写 |
| Q8 | 同屏超大编队时缓存竞争/驱逐 | 未见 LRU | 统计 `0x7107E0` miss 率随 N 变化 |

---

## 9. 取证索引

| 产物 | 路径 |
|---|---|
| 扫描脚本 | `out/re_work/vxl_re.py` … `vxl_re4.py` |
| 反汇编输出 | `out/re_work/vxl_re*_out.txt`（UTF-16）/ `*.u8` |
| 关键函数 | **DrawAsVXL `0x73B470`** · **Draw_A_VXL `0x4DAF10`→`0x706640`→`0x707480`** · **SomeVoxelCache `0x7107E0`** · **Shadow_Matrix `0x55A7D0`** · **阴影表 `0x7559B0`/`0xB45188`** · **协调 `0x6D8DB0`** |
| 虚表槽 | Unit v[65] `0x73B0B0` · v[69] `0x73CEC0` · v[323] Draw_A_SHP · v[324] Draw_A_VXL · v[341] DrawAsVXL · v[342] DrawAsSHP |
| 相关文档 | `fx_draw_chain.md`（DrawIfVisible/FX）· `rle_blit_family.md` · `blitter_microkernel_deep_dive.md`（Darken/Z）· `visibility_gap_spysat.md`（迷雾） |
| YRpp | `FootClass.h`（Draw_A_VXL 签名）· `UnitClass.h`（DrawAsVXL）· `GeneralStructures.h`（SomeVoxelCache）· `FileFormats/VXL.h` · `LocomotionClass.h` · `ConvertClass.h` · `Drawing.h`（ZBuffer） |

---

## 10. 与既有 Hook 衔接（只读建议）

- **L1 Blit 微内核**（`ra2render/blitter_hooks.cpp`）已覆盖 Darken/Xlat 族 → VXL 阴影直接受益，无需新 Blit Hook。
- **L3 `ShouldDrawMobileObject`** 谓词可直接复用到 H-VXL1/2；VXL 单位坐标取 `Object+0x9C`。
- **L5 FX 剔除**（`fx_draw_chain.md` H-FX*）与本文 H-VXL* 共用 `s_visionGrid`，谓词需幂等。
- 性能顺序建议：① 热缓存/朝向量化（A/B）→ ② H-VXL7 光栅降质（C）→ ③ 阴影降质（E）→ ④ 迷雾短路（H-VXL1）。
