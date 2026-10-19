# R7 锚定补丁交付：§18 VXL 体素渲染与缓存 / §19 特效与弹丸绘制链归属 / §20 裂缝与间谍卫星可见性分裂

> **执行方**：Agent Teams 成员 `atlas-r7-vxl-fx`（DSH 子代理，任务卡 `task-9`）
> **快照时点**：2026-09-29（本文件全部结论基于该时点工作区）
> **基线二进制**：`ra2youli/gamemd.exe`（MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`，4,825,360 B，ImageBase `0x400000`，FileOffset = VA − `0x400000`）【只读，未改动】
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **字节断言**：`out/re_work/atlas_rev/R7/claims_R7.txt`（**445 条**，`tools/audit_bytes.py` **全 OK**）
> **写作用域**：仅 `docs/re/atlas_rev/R7_vxl_fx_gap.md`、`out/re_work/atlas_rev/R7/**`。**未触碰** `docs/re/ARCHITECTURE_ATLAS.md`（Lead 唯一写者）、其他 R# 文件、`ra2render/**`、`ra2youli/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`。
> **证据标签**：[实证] = VA + FileOffset + 原始字节 + Capstone（可复算）；[ABI] = YRpp/symbols 交叉；[推演] = 字段序/行为链推理；[待实测] = 需真机断点/遥测。

---

## A. 锚点唯一性与实跑证据（补丁块前置条件）

实跑命令：`python out\re_work\atlas_rev\R7\anchor_probe.py`（脚本与输出留档 `out/re_work/atlas_rev/R7/anchor_evidence.txt`）。原文输出：

```text
--- ANCHOR-A: ^## 附录 DA1 : 1 hit(s)
  L1981 | first40='## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09'
     full: ## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09-27）
--- ANCHOR-B: §7.6 末行 NOP 句 : 1 hit(s)
  L1280 | first40='  将上述三处 6 字节指令全部替换为 `90 90 90 90 90 90`（'
     full:   将上述三处 6 字节指令全部替换为 `90 90 90 90 90 90`（6B NOP），完全消除清零副作用，彻底保护裂缝建筑的遮蔽状态机。
--- TOC: ^## 目录 (仅供 Lead 重建参考，不进补丁) : 1 hit(s)
  L17 | first40='## 目录'
--- total lines = 2002
```

- **ANCHOR-A（L1981，前 40 字符 `## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09`）**：唯一命中 1 处，用作 PATCH-R7-01/02/03 的 `APPEND_SECTION` 锚点（新章按 Lead 分配插在 DA1 之前）。
- **ANCHOR-B（L1280，前 40 字符 = 「  将上述三处 6 字节指令全部替换为 90 90 90 90 90 90（」）**：唯一命中 1 处，用作 PATCH-R7-04 的 `INSERT_AFTER` 锚点。
- 本流**不提交任何修改「## 目录」（L17）的补丁块** —— TOC 由 Lead 统一重建。

---

## B. 补丁块

### PATCH-R7-01  新增 §18「VXL 体素渲染与缓存布局」专章

- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md` **L1981**，该行前 40 字符 = `## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09`（实跑 grep 唯一命中，原文见 §A ANCHOR-A）
- **动作**：`APPEND_SECTION`（在 L1981 之前插入；Lead 按流号顺序排版，插入后行号漂移不影响本块）
- **现状问题**：atlas 现有 §0–§12 **全库 0 命中** `VXL` / `voxel` / `0x73B470` / `0x7107E0` / `0x707480`（本流实跑 grep 复核），即**载具体素渲染与体素缓存子系统在 atlas 中完全缺席**：§1 只到 Blitter 微内核族，§2.5 只到「槽 69 视距剔除」，§11 速查表无 `SomeVoxelCache`、Z 梯度表 `0x817710`、Loco `Draw_Matrix/Shadow_Matrix` 族。缺失后果：① 载具性能改造（缓存/朝向量化/LOD）无契约依据；② 阴影顺序不变量（先影后体）未入册，误重排即坏遮挡；③ `DisableVoxelCache/DisableShadowCache` 参与类型层 `v[13]` 序列化这一跨子系统耦合无人知晓。
- **替换文本**：

````markdown
## 18. §18 VXL 体素渲染与缓存布局 (VXL Voxel Rendering & Cache Layout)

> **本章定位**：架构级（类/虚表槽 + 关键 VA 表 + 与其他子系统契约 + 未闭环项），不搬运源文档算法细节。
> **事实来源**：`docs/re/vxl_render_sort.md`（25 KB）与 `docs/re/vxl_cache_layout.md`（23 KB）。
> **二次复核**：本章关键地址已编译为字节断言（`out/re_work/atlas_rev/R7/claims_R7.txt`，445 条中约 130 条属本章，`tools/audit_bytes.py` 全 OK）。
> **红线**：本章为**只读理解**；任何剔除/限频只允许落在绘制层（§18.9），严禁改 `IsShrouded` / `IsCellShrouded` / `RevealArea*` / Loco `Update` / ZBuffer 语义。

### 18.1 双腔分流拓扑：DrawAsVXL 与 DrawAsSHP [实证]

载具绘制由 `UnitClass::Draw`（v[69]）按 `UnitType+0x236`（`IsVoxel`）一分为二：

| 槽位 | 偏移 | 虚表表项 VA | 实现入口 (VA) | 职责 |
|:---|:---:|:---:|:---:|:---|
| `ObjectClass` **v[65]** DrawIfVisible | `+0x104` | 共享体 **`0x005F4B10`** | `0x005F4B10` | 统一视口门：裁剪 → `call v[69]`，出口 `ret 0xC` |
| `UnitClass` **v[65]** | `+0x104` | `0x0073B0B0` | `0x0073B0B0` | Unit 覆写（附加 Gap/隐身检查） |
| **`UnitClass` v[69] Draw** | `+0x114` | `0x007F5D84` | **`0x0073CEC0`** | 载具绘制总入口（阴影段 + 分流） |
| `ObjectClass` v[69] 默认 | `+0x114` | — | `0x005B3A50` | 空实现 |
| **`FootClass` v[323] Draw_A_SHP** | `+0x50C` | — | **`0x0041C090`** | SHP 载具/建筑共用形状绘制（→ `0x705E00`） |
| **`FootClass` v[324] Draw_A_VXL** | `+0x510` | — | **`0x004DAF10`** | 薄封装（Foot/Unit/Aircraft 共用） |
| **`UnitClass` v[341] DrawAsVXL** | `+0x554` | — | **`0x0073B470`** | 体素路径（HVA 帧 + 缓存 + 矩阵） |
| **`UnitClass` v[342] DrawAsSHP** | `+0x558` | — | **`0x0073C5F0`** | SHP 路径 |

分流判定汇编（`0x73D317`–`0x73D38F`）[实证，本流字节复算]：

```asm
0073D317  mov  al, [edi+0x236]    ; UnitType.IsVoxel          8A 87 36 02 00 00
0073D31D  test al, al
0073D31F  je   0x73d361           ; → DrawAsSHP 路径           74 40
0073D321  mov  eax, [edi+0xb0]    ; MainVoxel.VXL 非空?        8B 87 B0 00 00 00
0073D359  call [edx+0x554]        ; ★ v[341] DrawAsVXL
0073D38F  call [edx+0x558]        ; ★ v[342] DrawAsSHP
```

总链（架构口径）：

```text
Tactical/Map DrawIt 0x006D3D10
  └─ Object 绘制协调层 0x006D8DB0
       ├─ v[67] DrawBehind (+0x10C) / v[68] DrawExtras (+0x110)
       └─ v[65] DrawIfVisible 0x005F4B10 ──(call [eax+0x114] @0x5F4CFD)──► v[69] Draw
            └─ UnitClass::Draw 0x0073CEC0
                 ├─[阴影先行, 0x73D0E3] Loco v[10] Shadow_Matrix → 0x7559B0 表 0xB45188 → Darken Blit
                 └─[主体, 0x73D3xx]
                      ├─ IsVoxel=1 → DrawAsVXL 0x73B470
                      │     ├─ Loco v[9] Draw_Matrix (+ key)
                      │     ├─ SomeVoxelCache 两级查找 (0x746EA0 L1 → 0x7107E0 L2)
                      │     ├─ miss → 矩阵合成 0x5AE980 / 0x5AF980 / 0x4C93D0
                      │     └─ Draw_A_VXL v[324] 0x4DAF10 → 0x706640 → 0x707480 (光栅+Blit)
                      └─ IsVoxel=0 → DrawAsSHP 0x73C5F0 → Draw_A_SHP v[323] 0x41C090 → 0x705E00
                 └─[炮塔/炮管旁路] 0x706BD0 / 0x706ED0 / 0x707280 → 0x753C70 → 0x707480
```

### 18.2 Draw_A_VXL 三层与三路部件旁路 [实证]

| 层 | VA | 入口字节 | 职责 |
|:---|:---:|:---|:---|
| 薄封装（v[324]） | **`0x004DAF10`** | `83 EC 40`（`sub esp,0x40`） | `rep movsd` 拷 12-float 矩阵；若 `Foot+0x674`（Loco）非空则 `call [edx+0x2C]` 取 `Draw_Point` 修正中心；`ret 0x28` |
| 标志/Convert 核 | **`0x00706640`** | `83 EC 40` | 起始 `mov esi,0x2000`（Flat，`0x70664F`）；按 `WhatAmI` 跳表装 `0x200A/0x200C/0x2002/0x2004`；恒 `OR 0x800`（Alpha，`0x70674D`）；取 LightConvert；末尾 `call 0x707480` |
| 光栅+Blit 核 | **`0x00707480`** | `83 EC 50` | 求包围盒 `0x4AEC60`；临时缓冲 `0x43AD00`；`SelectRLEBlitter 0x490E50`（flags 去 `0x10`）；跨步体素光栅 **`0x437A10`**（Z 梯度表 `0x817710`）；脏矩形并入 `0xB1CFC0..0xB1CFCC` |

**三路部件旁路**（均收束到 `0x753C70` 体素切片裁剪 + `0x707480`）[实证]：

| 部件核 | VA | 入口字节 | 矩阵级联 | 备注 |
|:---|:---:|:---|:---|:---|
| 炮塔/附加体素顶层 | `0x00706BD0` | `83 EC 3C` | — | 在 `0x706D27` 调炮管核 |
| 主炮塔 + HVA 骨骼 | `0x00706ED0` | `8B 44 24 0C` | `M_turret_world = M_body_world × M_hva_bone`（`0x706F81`–`0x706FAF` 调 `0x5AF980`） | HVA 帧取自 `MotLib` |
| 炮管/充能炮塔 | `0x00707280` | `81 EC D8 00 00 00` | `M_barrel = M_turret × M_recoil`（`0x5AE860` 单位阵 → `0x5AEA10` 后坐力平移 → `0x5AF980` 级联） | 收束 `0x753C70` + `SelectPlainBlitter 0x490B90` |

> **来源口径差异（未闭环，标 [待实测]）**：`vxl_render_sort.md` §2.4/§2.5 记光照核为 `0x753E00 / 0x753F90 / 0x7542F0`（并称 VoxelAnim 走 `SelectPlainBlitter`）；`vxl_cache_layout.md` 记炮塔链为 `0x753E00 / 0x7540F0 / 0x754510`。两来源对 `0x7540F0 / 0x7542F0 / 0x754510` 的配对不一致 ⇒ 本章只断言「同属 `0x753E00` 光照族并最终进 `0x753C70 → 0x707480`」，精确配对列入 §18.10 Q2。

### 18.3 `SomeVoxelCache`：结构 / 两级查找 / 扩容 [实证]

**宿主布局**（`ObjectTypeClass.VoxelCaches[4]`，基址 `Type+0x258`，元素步长 `0x14`）[实证 + ABI]：

| 槽 | Type 偏移 | 载体 | 查询函数 |
|:---:|:---:|:---|:---|
| `[0]` | `+0x258` | 主车体 MainVoxel | `0x746EA0`（L1 探测）→ `0x7107E0`（L2 装填） |
| `[1]` | `+0x26C` | 主车体阴影/特殊变体 | 同上 |
| `[2]` | `+0x280` | 炮塔 TurretVoxel | 同上 |
| `[3]` | `+0x294` | 炮管/充能炮塔 | 同上 |

**结构体与条目**（`sizeof = 0x14`；条目 `sizeof = 8`）[实证 + ABI]：

| 偏移 | 字段 | 语义与实证点 |
|:---:|:---|:---|
| `+0x00` | `VoxelCacheEntry* Buffer` | 动态条目数组（`operator new[] 0x7C8E17`） |
| `+0x04` | `int32_t Count` | 有效条目数（为 0 即必然 miss） |
| `+0x08` | `int32_t Capacity` | 容量上限（**初始 10：`0x706D78 = BB 0A 00 00 00`**） |
| `+0x0C` | `uint8_t IsSorted` | 1=已排序；插入新条目置 0（脏） |
| `+0x10` | `VoxelCacheEntry* LastFoundEntry` | **L1 MRU 单条快命中**（`0x746EA0 = 8B 41 10`） |
| 条目 `+0x00` | `uint32_t Key` | 32 位复合渲染键（§18.4） |
| 条目 `+0x04` | `void* Data` | 预渲染体素栅格指针（命中后直接送 `0x707480`） |

**两级查找与扩容** [实证]：

1. **L1**（`0x746EA0`，`mov eax,[ecx+0x10]` 起）：`LastFoundEntry` 为空或 `Key` 不等 → miss；相等 → `mov al,1; ret 4`（极速命中）。
2. **L2**（`0x7107E0`）：`Count==0` → miss；`IsSorted==0` → 先 `qsort`（`0x7C8B48`，条目 8 字节，比较函数 `0x710860`），随后复位 `LastFoundEntry=null`、`IsSorted=1`；再二分查找（`0x710890`）。
3. **扩容**（Miss 插入，`0x706D65`–`0x706DC7`）：`Count+1 > Capacity` 时空容量取 **10**，否则增量 = 当前容量（**约 2×**）；`new_size = new_cap * 8`；`call 0x7C8E17`；循环拷贝旧条目。
4. **命中跳过路径**：`DrawAsVXL` 于 `0x73BA26`（`mov ecx,0xc` + `rep movsd`）复用缓存矩阵，`0x73BA47` `jmp 0x73BC1D` **跳过 `0x73BA4C` 起的矩阵重合成**；`0x706640` 于 `0x70683B`（取 `LastFoundEntry+4` 的 `Data`）后 `0x706866 call 0x707480` **直接 Blit，跳过 3D 体素光栅与光照**。

**架构级推论（性能契约）** [实证 + 推演]：
- 缓存宿主在 **Type（类型）而非实例** ⇒ **同型号、同朝向、同帧号、同 Z 桶的 N 辆坦克只光栅化 1 次**（原版「静止同朝向」天然免算）。
- **无 LRU 淘汰**；原版扩容步长仅 10 且每次插入使 `IsSorted=0`，大步队异朝向场景会反复 `qsort` [推演，源自 `vxl_cache_layout.md` §三.1]。
- 车体在动（朝向变）⇒ 键变 ⇒ 必然 miss ⇒ **原版 VXL 旋转代价的根因**。

**INI 门控与类型层序列化（跨子系统耦合，必读）** [实证]：

| 项 | INI 键（串 VA） | 类型存储偏移 | 解析写点 | 渲染读点 | 构造初值 |
|:---|:---|:---:|:---:|:---:|:---:|
| 关闭体素缓存 | `DisableVoxelCache`（`0x0084336C`） | `TechnoTypeClass+0xDBE` | `0x71596C` | **`0x706806`**（`jne 0x706875` 强制软件光栅） | `0x711658` |
| 关闭阴影缓存 | `DisableShadowCache`（`0x00843358`） | `TechnoTypeClass+0xDBF` | `0x7159A6` | **`0x706C33`**（`jne 0x706CE1` 跳过阴影缓存查找） | `0x71165E` |
| 炮塔影开关 | `UseTurretShadow`（`0x00845DA0`） | — | — | `UnitTypeClass.UseTurretShadow` | — |

> **契约 C-18-1（硬）**：`+0xDBE / +0xDBF` 在 `TechnoTypeClass` **v[13] 打包（存档与网络同步，读点 `0x717767` / `0x717775`）** 中被读取 ⇒ 属**类型层持久化属性**。任何体素/阴影缓存改造**必须尊重** `DisableVoxelCache` / `DisableShadowCache`（原版语义：对特殊单位强制无缓存光栅），否则构成「类型层属性被渲染层绕过」的契约破坏。

### 18.4 缓存键构造：车体键含 Z 桶，阴影键**不含** [实证]

| 字段位 | 车体 VXL 键（`DrawAsVXL`，`0x73B74C`–`0x73B79F`） | 阴影缓存键（`Shadow_Matrix`，`0x55A86D`–`0x55A89E`） |
|:---|:---|:---|
| bits 0..4 | 朝向桶 `facing & 0x1F`（32 向） | 朝向桶 `facing & 0x1F` |
| bits 5..9 | **Z 桶 / 俯仰阶梯**（`Type+0x720==0` 时以 `and esi,0xFFFFFC1F` 清除） | **地表坡度朝向 `SlopeFacing`** |
| bits 10..15 | 扩展标志位 | `ShadowIndex` 低位 |
| bits 16..23 | **HVA 骨骼动画帧号**（`or esi, extraByte<<0x10`） | `ShadowIndex` 高位/变体 |
| **Z 桶** | **包含**（受 `Type+0x720` 控制） | **绝不包含** |

阴影键合成（`0x55A86D` 起 `shl eax,6` → `add eax,ebp` → `shl eax,5` → `or ecx,eax`（`0x55A89E`））[实证]：

```text
ShadowCacheKey = ((((ShadowIndex << 6) + SlopeFacing) << 5) | (Facing & 0x1F))
```

> **架构推论**：阴影形态只取决于「载具自身朝向 + 地形投射坡度 + 阴影模型索引」，与载具世界 Z 高度无关 ⇒ 阴影键剥离 Z 桶，**多单位同坡度下阴影缓存命中率显著高于车体键**。

### 18.5 阴影链、Darken 微内核与顺序不变量 [实证]

| 形态 | Blitter | 入口 VA | 虚表条目 |
|:---|:---|:---:|:---|
| 载具/建筑 VXL·SHP 影（带 Z） | **`BlitTransDarkenZRead@G`** | **`0x00492D20`** | `0x007E5948` |
| 非 Z Darken | `BlitTransDarken@G` | `0x00492670` | `0x007E59F0` |
| 步兵影（RLE） | `RLEBlitTransDarken@G` | `0x00496250` | `0x007E55A0` |
| 步兵影 + Z | `RLEBlitTransDarkenZRead@G` | `0x00496820` | `0x007E5540` |

- **共同语义**：`*dst = (*dst >> 1) & this->DarkenMask`，`DarkenMask` 典型 `0x7BEF`（RGB565 减半并清溢出位）。
- **高危认知**：`this+0x04` 是**数值掩码**，**不是** Xlat 调色板指针；误当指针解引用即 `0xC0000005`（与 §1 Darken 微内核结论衔接）。
- 阴影投影矩阵表：全局 **`0x00B45188`**（`.bss`，**无文件数据 ⇒ 不可字节断言**），32 向 × 48 B = 1536 B，由 **`0x00754CB0`** 运行期生成；查表函数 **`0x007559B0`**（`lea esi,[edx+edx*2]; shl esi,4; add esi,0xB45188; mov ecx,0xC; rep movsd`）。
- 阴影门：`Type.NoShadow(+0xE0E)`（`0x73D0DB`）与单位阴影开关 `Unit+0x6D2`（`0x73D0E9`）；Loco `v[0x80] Is_To_Have_Shadow`；`TechnoTypeClass.ShadowIndex`。

> **顺序不变量 I-VXL-1（硬）**：**先影后体**（阴影段 `0x73D0E3` 严格早于主体 `0x73D3xx`）。Darken 是「压暗已有像素」：一旦颠倒，影子落到本体上 ⇒ 车体被压黑、两车影叠加错乱。带 `ZRead` 的 Darken 可按 Z 拒绝「盖在更近物体上的影」，但原版 VXL 影多数仍依赖绘制序。

### 18.6 Z 序两层模型与 Z 梯度 [实证 + 推演]

| 层 | 维护者 | 依据 | 乱序后果 |
|:---|:---|:---|:---|
| **对象间遍历序** | `0x006D8DB0` 绘制协调层列表 | 列表插入序（≈ 地图对象序），**非严格深度排序** | 无 Z 的 Flat/半透明叠加错序 |
| **逐像素深度** | Blit `ZRead(0x3000)` / `ZReadWrite(0x4000)` + `ZBuffer`（`0x00887644` 描述符，环形回卷） | `Draw_Matrix` 出参 `key` = `(zBucket<<5) | (facing&0x1F)` | Z 正确则遮挡仍对；Z 缺失则「后画胜出」 |

- `zBucket = ((raw>>10)+1)>>1 & 0x1F` 再 `-8`（Draw）/ 混入 `ShadowIndex`（Shadow）[推演：源自 `vxl_render_sort.md` §1.2，本流未逐指令复算该移位链]。
- **Z 梯度表 `0x00817710`**（`.rdata`，4 项 × 24 B = 96 B）[实证，本流已整表字节复算]：

| 索引 | `ZGradient` | StepX | StepY | ZDivisor | ZStride | ZOffset | ModeFlag | 语义 |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| 0 | `Ground` | 1 | 1 | 1 | 1 | −1 | 1 | 平地等轴步进 |
| 1 | `Deg45` | 2 | 3 | 2 | 3 | −1 | 1 | 斜坡 |
| 2 | `Deg90` | 1 | 3 | 1 | 3 | +1 | **0** | 垂直侧立面（正投影） |
| 3 | `Deg135` | 1 | 1 | −1 | −1 | −1 | 1 | 反向斜坡 |

  索引公式：`lea eax,[eax+eax*2]`（`0x43742F`）→ `lea edx,[eax*8+0x817710]`（`0x437A95`），即 `ZGradient*24 + 0x817710`。
  分支消费：**`ModeFlag==0`** 走 `0x437C39` 正投影 `idiv`（立面不拉伸）；**`ModeFlag==1`** 走 `0x437B70` 等轴步进，按 `ZStride`/`ZOffset` 在每扫描行末补偿梯级深度（保证桥/悬崖/坡道上 ZBuffer 与高度场贴合，不刺穿不闪烁）。
- `ILocomotion::Z_Gradient` = **v[14]（`+0x38`）**：`DriveLocomotion 0x4B4870`（`xor eax,eax; ret 4`）、`ShipLocomotion 0x6A3EA0`、`Fly/Hover/Walk/DropPod 0x55ABA0` **均恒返 0（Ground）**；**全游戏唯一真正实现非零动态梯度的类是 `TunnelLocomotionClass::Z_Gradient 0x729E50`**（基于屏幕投影与高程差，5 路跳表 `0x72A000`，本流已字节复算：`0x729F74 / 0x729FCC / 0x729F40 / 0x729FDE / 0x729F52`）。
- 矩阵提供者：`ILocomotion::Draw_Matrix`（v[9]，默认 `0x55A730`）/ `Shadow_Matrix`（v[10]，默认 `0x55A7D0`）= `Matrix3DStruct{float Data[12]}`；覆写分布 Drive `0x4AFF60`/`0x4B0410`、Fly `0x4CF610`/`0x4CFB00`、Hover `0x513F40`/`0x5142A0`、Ship `0x69F670`/`0x69FB20`、Tunnel `0x729B40` 等 14 处。
- 缩放/倾角：`Type+0x720`（`fild` 后乘 `0xB1D008`）编入 3×4 矩阵，**不存在独立 Scale 参数**。

> **顺序不变量 I-VXL-2（硬）**：**性能优化若重排对象绘制序，必须全量 `ZReadWrite`（或保持原列表序）**；否则桥上/桥下、重叠坦克的遮挡立即错乱。

### 18.7 `UnitClass+0x6D3` 字段定性：纯绘制期标志 [实证]

| 类别 | VA / 指令 | 语义 |
|:---|:---|:---|
| 写 | `0x73B586`（DrawAsVXL 入口置 1）、`0x73C1F5`（退出置 0）、`0x73C7F2`/`0x73CDF9`（DrawAsSHP 同构）、`0x73540A`（ctor 置 0） | `InDrawingLoop` |
| 读 | `0x705F6B` / `0x706156` / `0x706183`（`0x705E00` SHP 核）、`0x7066BA` / `0x706731`（`0x706640` VXL 核）、`0x70717D`（炮塔核）、**`0x7074F0`**（`0x707480`：非 0 则切 `0xB1D140` 离屏/脏矩形暂存缓冲） | 全在绘制调用链 |

> **定谳**：全二进制 17 处读写**全部局限于绘制上下文**，**无任何逻辑/Update/碰撞/同步函数读取** ⇒ 可安全作为绘制层判据（多线程渲染提取、视锥剔除统计）。`AircraftClass` 的同名偏移是**另一语义的独立字段**，禁止跨类套用。

### 18.8 迷雾短路位置（与 §2.5 / §19 / §20 的接口）[实证 + 勘误提示]

- [实证] 矩阵仅在 `DrawAsVXL`（被 `Draw` 调）内合成，而 `Draw` 只经 `DrawIfVisible`（v[65]）通过后才跑 ⇒ **在 v[65] 或协调层短路可省掉矩阵合成 + 缓存查询 + 光栅 + Blit 全链**。
- [实证] 协调层 `0x6D8DB0` 内已有 `IsCellShrouded 0x5865E0` 调用；`UnitClass::DrawIfVisible 0x73B0B0` 另有 Gap/隐身检查。
- ⚠️ **口径冲突（须 Lead 裁决，见 [9]）**：atlas **§2.5** 明令「视距门控**必须且只能收口在槽 69**，严禁在基类 `DrawIfVisible` 槽 65 短路」；而 `vxl_render_sort.md` §7 的 `H-VXL1` 建议钩 **`0x005F4B10`（v[65] 共享体）**。本章立场：**维持 §2.5 纪律**，把 v[65] 方案降级为「待逐类 v[65] 表项取证后的可选优化」，理由：① 建筑走三态残影（非布尔剔除），语义不同；② `Unit/Anim/VoxelAnim` 各自覆写/包装 v[65]（`0x73B0B0` / `0x422C70` / `0x749B20`），共享体并非「一处覆盖全部」。与 §19.7 同一裁决。

### 18.9 落地 Hook 面（**仅纸面规格**，未落地）与确定性红线

| 组 | 目标 | VA / 槽 | 建议改动 | 风险 |
|:---|:---|:---|:---|:---:|
| H-VXL-A | `UnitClass::Draw` / `DrawAsVXL` | `0x73CEC0`（v[69]）/ **`0x73B470`**（v[341]） | 迷雾/LOD 总开关、缓存命中统计（入口短路） | 低（纯绘制） |
| H-VXL-B | `Draw_A_VXL` 薄封装 / 标志核 / **光栅核** | `0x4DAF10` / `0x706640` / **`0x707480`** | 多态覆盖点、LOD flags、降分辨率光栅、性能计数 | 低 |
| H-VXL-C | 两级缓存 | `0x746EA0` / `0x7107E0` | 命中率遥测；`Capacity` 预置 64（32 朝向×2 帧）、插入排序替代整表 `qsort` | 低（须尊重 `+0xDBE`/`+0xDBF`） |
| H-VXL-D | Loco 矩阵提供 | v[9] `Draw_Matrix`（默认 `0x55A730`）/ v[10] `Shadow_Matrix`（默认 `0x55A7D0`） | 雾中/远景跳过阴影（须与主体剔除谓词一致） | 低 |
| H-VXL-E | Z 写入光栅 / 对象协调序 | `0x437A10`（表 `0x817710`）/ `0x6D8DB0` | **只读理解**；协调层仅可加剔除，**勿重排**（除非全量 ZReadWrite） | **中**（改 Z/序即坏遮挡） |
| H-VXL-F | Darken Blit | `0x492D20`（vt `0x7E5948`）/ `0x496250` / `0x496820` | 已属 §1 L1 微内核；SSE2 化 | 低 |

**确定性红线（重申）**：① 可改 = 绘制层（`DrawIfVisible` / `Draw` / `DrawAsVXL` / `Draw_A_VXL` / `0x707480` / 缓存 / Blit / 私有 `s_visionGrid`）；② **不可改** = `IsShrouded 0x487950` / `IsCellShrouded 0x5865E0` / `RevealArea*` / Loco `Process``Move_To` / `Update` 的寿命·位置写 / Z 语义（除非全客户端一致）；③ 先影后体保持；④ 单机/战役绘制 Hook 不进存档，联机仅保留红线内 Hook；**禁止在 `Update` 内限频/跳帧**（确定性高危）。

### 18.10 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证 | 级别 |
|:---:|:---|:---|:---|:---:|
| Q1 | `SomeVoxelCache.Buffer/f_4/f_8` 语义边界（池是否跨 Type 共享） | 只见查找/装填调用，未见池分配器 | 断点 `0x7107E0` / `0x746EA0` 双路径，观察 `Buffer` 指针是否跨 Type 复用 | P2 |
| Q2 | 光照核精确配对（`0x753F90`/`0x7542F0` vs `0x7540F0`/`0x754510`） | 两来源文档口径不一致 | 逐个 dump `0x706ED0` / `0x707280` / `0x749B70` 的 `call` 序列并比对参数来源 | P2 |
| Q3 | `0x817710` 各字段对 ZBuffer 步进的精确作用（`ZDivisor` 与 `ZStride` 耦合） | 需内层循环全量反汇编 + 数值复算 | 反汇编 `0x437A10`–`0x437D00`，构造 Z 桶→像素深度映射表 | P2 |
| Q4 | 同屏超大编队缓存 miss 率与 `qsort` 频次 | 需真机遥测 | 钩 `0x7107E0` 计数 miss / `IsSorted=0` 次数随 N 变化 | P1 |
| Q5 | `Tunnel Z_Gradient` 5 路 case 与 `0x844A98`/`0x844A9C` 精确语义（常量地址已复算，数值用途未复算） | 需结合地形高程字段 | 断点 `0x729E50` 观察 5 路分支触发条件 | P2 |
| Q6 | 阴影缓存键是否含 Z 桶 | **已闭环：不含**（§18.4 实证） | — | — |
| Q7 | `Unit+0x6D3` 是否被逻辑读 | **已闭环：不读**（§18.7 实证） | — | — |
| Q8 | 缓存驱逐/竞争（无 LRU）在极高密度下的表现 | 需真机 | 同 Q4 遥测 + 帧时间剖面 | P2 |

### 18.11 关键 VA 速查表

| VA | 名称/职责 | 证据等级 | 来源 |
|:---:|:---|:---:|:---|
| `0x0073CEC0` | `UnitClass::Draw`（v[69]）载具绘制总入口 | [实证] | `vxl_render_sort.md:14,141` |
| `0x0073B470` | `UnitClass::DrawAsVXL`（v[341]） | [实证] | `vxl_render_sort.md:14,171` |
| `0x0073C5F0` | `UnitClass::DrawAsSHP`（v[342]） | [实证] | `vxl_render_sort.md:14` |
| `0x0041C090` | `FootClass::Draw_A_SHP`（v[323]） | [实证] | `vxl_render_sort.md:14` |
| `0x004DAF10` | `FootClass::Draw_A_VXL` 薄封装（v[324]） | [实证] | `vxl_render_sort.md:15,188` |
| `0x00706640` | `TechnoClass::Draw_A_VXL` 标志/Convert 核 | [实证] | `vxl_render_sort.md:15,189` |
| `0x00707480` | VXL 光栅 + Blit 核 | [实证] | `vxl_render_sort.md:190` |
| `0x00706BD0` / `0x00706ED0` / `0x00707280` | 炮塔顶层 / 主炮塔+HVA / 炮管后坐力 | [实证] | `vxl_cache_layout.md:17,177` |
| `0x007107E0` / `0x00746EA0` | `SomeVoxelCache` L2 查找 / L1 MRU 探测 | [实证] | `vxl_cache_layout.md:14,21` |
| `0x00710860` / `0x00710890` / `0x007C8B48` / `0x007C8E17` | 比较函数 / 二分 / `qsort` / `operator new[]` | [实证] | `vxl_cache_layout.md:21,405` |
| `0x00817710` | Z 梯度表（4×24 B，本流整表复算） | [实证] | `vxl_cache_layout.md:16,140` |
| `0x00437A10` | 跨步体素光栅核（ZBuffer 步进） | [实证] | `vxl_render_sort.md:190,309` |
| `0x0055A730` / `0x0055A7D0` | `ILocomotion::Draw_Matrix` / `Shadow_Matrix` 默认实现 | [实证] | `vxl_render_sort.md:16,75` |
| `0x007559B0` / `0x00B45188` | 阴影投影矩阵查表 / 表本体（`.bss` 无文件数据） | [实证] | `vxl_cache_layout.md:18,214` |
| `0x00492D20` / `0x00492670` / `0x00496250` / `0x00496820` | Darken 族 Blit 入口 | [实证] | `vxl_render_sort.md:258` |
| `0x00729E50` | `TunnelLocomotionClass::Z_Gradient`（唯一非零动态梯度） | [实证] | `vxl_cache_layout.md:20,299` |
| `0x0084336C` / `0x00843358` | INI 键 `DisableVoxelCache` / `DisableShadowCache` | [实证] | `vxl_cache_layout.md:15,88` |
| `0x00706806` / `0x00706C33` | 缓存门控渲染读点（`+0xDBE` / `+0xDBF`） | [实证] | `vxl_cache_layout.md:15,123` |
| `0x0071596C` / `0x007159A6` / `0x00717767` / `0x00717775` | 类型层 INI 写点 / 序列化读点 | [实证] | `vxl_cache_layout.md:15,136` |
````

- **证据**：
  - 等级 **[实证]** —— 本章约 130 条地址已落 `out/re_work/atlas_rev/R7/claims_R7.txt`（445 条断言全 OK，`python tools/audit_bytes.py` 原文见 [6] 节）；来源 `docs/re/vxl_render_sort.md:14-26,141-196,200-247,250-323,361-389` 与 `docs/re/vxl_cache_layout.md:14-21,29-81,87-136,140-173,196-208,214-255,261-283,289-323,327-378`。
  - 等级 **[推演]**：容量瓶颈/命中率推论、`zBucket` 移位链、阴影键命中率对比。
  - 等级 **[待实测]**：§18.2 光照核配对、§18.10 Q1–Q5/Q8。
- **影响面**：
  - **§11 速查表**：新增约 25 行（VXL 族 VA + 字段偏移）—— Lead 需并入 §11.1/§11.2/§11.3（本节 §18.11 表即为待并入底稿）。
  - **§12 契约**：新增 **C-18-1**（`+0xDBE`/`+0xDBF` 属类型层持久化属性，缓存改造必须尊重）、**I-VXL-1**（先影后体）、**I-VXL-2**（重排绘制序须全量 ZReadWrite），落 §12.1/§12.2 名下。
  - **§0 准则**：不改动 §0.2/§0.3 任何裁决；为 §2.5「门控只收口槽 69」提供 VXL 侧支持证据（§18.8）。
  - **§2.5 / §19**：明确 v[65] 方案降级（同一裁决见 §19.7）。


---

### PATCH-R7-02  新增 §19「特效与弹丸绘制链归属」专章

- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md` **L1981**，该行前 40 字符 = `## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09`（实跑 grep 唯一命中，见 §A ANCHOR-A）
- **动作**：`APPEND_SECTION`
- **现状问题**：atlas 现有内容**全库 0 命中** `0x468090` / `0x62CEC0` / `0x62E280` / `0x75F9F0` / `0x749B70` / `0x550240` / `0x4C2830` / `0x6591B0` / `0x5FFFA0` / `0x5F4B10`（本流实跑 grep 复核）。§2 只有一句「Pass 7：动态粒子、投射物与全域特效（Bullet / Particle / Laser）」，且该 Pass 表已被 U3-P1 勘误为「次序与归属均错」；§2.5 只列 Bullet/Particle 两类的槽 69 表项。结果：**FX 侧 6 类 Object + 4 个非 Object 渲染器的归属、Update/Draw 分离性、以及「EBolt 寿命在 DrawAll 内衰减」这一结构性陷阱，在 atlas 中完全无记录**，任何 L5 剔除实现都可能踩雷。
- **替换文本**：

````markdown
## 19. §19 特效与弹丸绘制链归属 (FX & Projectile Draw-Chain Attribution)

> **事实来源**：`docs/re/fx_draw_chain.md`（48 KB）与 `docs/re/bullet_particle_fog_deep_dive.md`（37 KB）。
> **二次复核**：本章约 120 条地址已落 `out/re_work/atlas_rev/R7/claims_R7.txt`（445 条断言全 OK）。
> **红线**：只拦绘制。禁止改 `IsShrouded` / `IsCellShrouded` / `RevealArea*` / 任何 Update、以及 **EBolt Lifetime 推进语义**（除非同端补衰减）。

### 19.1 归属总图：DrawIt 的固定枢纽序列 [实证]

战术主绘制 **`MapClass/Tactical::DrawIt`（`0x006D3D10`，入口 `81 EC F4 00 00 00`）** 内部对 FX 采用**固定顺序的枢纽直呼**（不是 Pass 编号，而是可复核的调用序）：

| 序 | 枢纽 | VA | 职责 |
|:---:|:---|:---:|:---|
| 1 | 地形/覆盖物+雾层 | `0x004801F0`（在 `0x6D448B` 被调） | `CellClass::Draw`（含 `Draw_Fog 0x47F250` / 瓦片层 `0x47EFE0`） |
| 2 | **Object 绘制协调层** | **`0x006D8DB0`**（在 `0x6D465F` 被调） | v[67] DrawBehind → v[68] DrawExtras → v[65] DrawIfVisible（→ v[69] Draw） |
| 3 | Spotlight | `0x005FFFA0` | `SpotlightClass::DrawAll` |
| 4 | 激光 | `0x00550240` | `LaserDraw::DrawAll` |
| 5 | 电弧 | `0x004C2830` | `EBolt::DrawAll` |
| 6 | 尾迹线 | `0x00556D40`（在 `0x6D4673` 被调） | `LineTrail::DrawAll`（单实例 `0x556C00`；清理时于 `0x556E14` 解绑 `ObjectClass+0xA8 LineTrailer`） |
| 7 | 辐射光束 | `0x006591B0` | `RadBeam::DrawAll` |
| 8 | 收尾 | `0x006DBE20` | 阴影/叠加收束 |

> **与 §2.1 的勘误关系**：§2.1 的 8-Pass 表已被 U3-P1 勘误（layer_order_fog_vs_objects.md）—— 迷雾/覆盖物层在**对象层之前**。本章采用「枢纽调用序」口径，避免 Pass 编号漂移。
> **数据源定谳**：`0x8A0394`（Items）/ `0x8A03A0`（Count）= **`MapClass::ObjectsInLayers[2]（Ground 地面层）`** 动态向量（图层基址 `0x8A0360 + Layer*0x18`，入队处 `0x4A9752`：`lea ecx,[edx*8+0x8a0360]`）；`0x6D97D0` / `0x6D9920` 是**视口局部脏矩形补绘**（非小地图/雷达路径）—— 与 §2.1 的『小地图』旧表述相反。

### 19.2 Object 系 FX：槽 69 逐类归属与「自带雾门」的失效 [实证]

| 类 | 主虚表 | v[69] 表项 | 实现入口 | 自带雾门 | 结论 |
|:---|:---:|:---:|:---:|:---|:---|
| `BulletClass` | `0x007E46E4` | `0x007E47F8` | `0x00468090` | `Flags&0x1000` → `0x5865E0` | 门**已废**（见下），需自建剔除 |
| `AnimClass` | `0x007E3354` | `0x007E3468` | `0x00422CA0` | 无 Shroud 硬切；`+0x19D` / `+0x199` 门 | 需自建剔除（§19.5） |
| `ParticleClass` | `0x007EF954` | `0x007EFA68` | `0x0062CEC0` | 同构 `Flags&0x1000` 门 | 门**已废** |
| `ParticleSystemClass` | `0x007EFB9C` | `0x007EFCB0` | `0x0062E280` | 无（仅 `Type+0x30C` Laser 门） | 需自建剔除 |
| `WaveClass` | `0x007F6BF4` | `0x007F6D08` | `0x0075F9F0` | **双端点** `Flags&0x1000` → `0x5865E0` | 门**已废**；谓词须两端 OR |
| `VoxelAnimClass` | `0x007F6318` | `0x007F642C` | `0x00749B70` | `Flags&0x1000` → `0x5865E0` | 门**已废** |
| `OverlayClass` | — | `0x007EF4E8` | `0x005FDF60` = `C2 08 00`（**空桩 ret 8**） | — | **无需在槽 69 剔除**（矿石/围墙由 `CellClass::Draw` 内联） |
| `BuildingClass` | `0x007E3EBC` | `0x007E3FD0` | `0x0043D290` | `Type+0x1701`（InvisibleInGame）门 | 三态残影，**非布尔剔除** |

**「自带雾门全废」的因果链（本章核心结论）** [实证]：

1. 所有 FX 的雾门都形如 `test ch,0x10`（`Scenario.Flags & 0x1000`，例：Bullet `0x4680A8`、Particle `0x62CF2B`、Wave `0x75F9FA`、VoxelAnim `0x749B81`）；未置位即**直接跳过**雾检查；
2. 该位在现代联机/战役/自建渲染器下被**强制清零**（为规避 `FOG.SHP` 反色/崩溃历史缺陷）；
3. 即使置位，被调用的 **`MapClass::IsCellShrouded 0x005865E0` 是恒假桩**：本流字节复算前 2 字节 = `32 C0`（`xor al,al`），全指令 `xor al,al; ret 4` ⇒ 永远返回「未被遮蔽」。
⇒ **原版迷雾对弹道/爆炸/粒子/波/碎片完全无门**。这就是「黑雾中飞出的 V3 火箭与尾影可见」的根因（`bullet_particle_fog_deep_dive.md` §1.2 的「双重致命缺陷」），且**不依赖任何补丁** —— 原版即如此。

### 19.3 非 Object 渲染器四件套 [实证]

| 渲染器 | 全局容器（vptr / Items / Count） | DrawAll | 单实例 Draw | 关键字段 |
|:---|:---|:---:|:---:|:---|
| `LaserDraw` | `0xABC878` / `0xABC87C` / `0xABC888` | **`0x00550240`** | `0x00550260`（旁路 `0x5509F0`） | `this+0x4C` 剩余时长；`this+0x20` 闪烁标志；**无 Owner 字段** |
| `EBolt` | `0x8A0E88` / `0x8A0E8C` / `0x8A0E98` | **`0x004C2830`** | 循环内联（`0x4C2856` 取 `Owner(+0x20)`） | `Point1` / `Point2` / `Owner` / **`Lifetime`** |
| `RadBeam` | `0xB04A60` / `0xB04A64` / `0xB04A70` | **`0x006591B0`** | 循环内联 | `Owner(+4)` / `Type(+0x10)` / Source·Target |
| `Spotlight` | `0xAC1678` / `0xAC167C` / `0xAC1688` | **`0x005FFFA0`** | `0x005FF850` | 半径 → 光锥表 `0x83358C` |

容器布局 = YRpp `VectorClass`：`vptr@0 / Items@+4 / Capacity@+8 / IsAllocated@+0xC / IsInitialized@+0xD / Count@+0x10 / CapacityIncrement@+0x14`。[实证：`0x550240` 入口第一条即读 `0xABC888`（Count），`0x5FFFA0` 同样读 `0xAC1688`，与布局吻合]

> ⚠️ **结构性陷阱 T-FX-1（硬）**：**`EBolt` 的 `Lifetime` 在 `DrawAll` 内衰减（右移一位），到 0 才析构** —— 绘制函数**承担逻辑副作用**。若在 `0x4C2830` 入口整函数短路，**电弧将永不消失（视觉残留）**。正确短路位置 = **循环体内 `continue`**，或短路前手动补衰减。此为本章唯一「Update/Draw 半耦合」点。

### 19.4 Update / Draw 分离性矩阵 [实证]

| 对象 | Update（逻辑帧） | Draw（渲染帧） | 分离性 |
|:---|:---|:---|:---:|
| `AnimClass` | `0x422720` / `0x4228E0` + v[23] `0x423AC0` | `0x422CA0` | 分离 |
| `ParticleClass` | `0x62B5E0` / `0x62BB20` / `0x62D9A0` | `0x62CEC0` | 分离 |
| `ParticleSystemClass` | **`0x62DF20` / `0x62E070`** | `0x62E280`（只画 Spotlight） | **分离（关键）** |
| `BulletClass` | `0x4664C0` 族 / `0x4666E0` | `0x468090` | 分离 |
| `WaveClass` | `0x762AF0` | `0x75F9F0` | 分离 |
| `LaserDraw` | `0x550150` / `0x550000` | `0x550240` | 分离 |
| `EBolt` | Fire `0x4C2A60` 创建 | `0x4C2830` | **半耦合**（T-FX-1） |

> **归属定谳**：`ParticleSystemClass::Draw` **不画粒子**，只维护/绘制 Spotlight（`Type+0x30C` 为 Laser 时另走激光支路，否则于 `0x62E376` 附近直接早退）；真正粒子像素由每个 `ParticleClass::Draw` 独立走完整链（Convert → `0x4AED70` → Blit）⇒ **同帧 N 次独立 Blit，无批处理**。这是高密度爆炸的成本中心。

### 19.5 `AnimClass` 雾语义定谳（含对源文档的勘误）[实证]

**（a）`AnimClass+0x184` = `int DelayTimer`，不是布尔隐藏位**

| # | VA | 指令 | 语义 |
|:---:|:---:|:---|:---|
| 1 | `0x421FC2` | `mov [esi+0x184],ecx` | ctor 写入初始延迟（第 3 参 `LoopDelay`） |
| 2 | `0x4226F6` | `mov eax,[esi+0x184]` | 构造尾判定：为 0 立即 `call 0x424CE0` 启动 |
| 3 | `0x422809` | `mov [esi+0x184],ebx` | 第二初始化函数清零 |
| 4 | `0x422C70` | `mov eax,[ecx+0x184]` | **`DrawIfVisible` 门**：非 0 → 跳绘制（`ret 0xC`） |
| 5 | `0x424386` / `0x424390` / `0x424393` | `mov / dec eax / mov` | **`Update` 每帧递减**，仍 >0 则跳出（不推帧、不造成伤害） |
| 6 | `0x4243A1` | `call 0x424CE0` | 恰好减至 0 → **触发音效与初始逻辑** |
| 7 | `0x4247E5` | `mov [esi+0x184],eax` | 单次循环结束按 `AnimType+0x2E0 RandomLoopDelay` 随机重挂 |
| 8 | `0x425472` | `mov eax,[esi+0x184]` | `Save`（IPersistStream）序列化 |

> 🔺 **归属裁决**：该字段**同时门控 Draw 与 Update**（#4 与 #5），且其归零会触发音效/初始逻辑（#6）⇒ **它不是「纯绘制开关」**。`fx_draw_chain.md` §6 的 `H-FX13`（「在 `+0x184` 写 1 让引擎跳过绘制」，风险记 [中]）**风险等级上调为 [高]（确定性）**：写入该字段会推迟动画起始音效与逻辑推进，联机/回放下帧序分叉。**建议：禁止**用该字段做剔除开关。

**（b）`IsFogged` / 不可见门与「无淡出公式」**

| 门 | 写点 | 读点与行为 |
|:---|:---|:---|
| `+0x199 IsFogged` | `0x4519B2`（建筑创建附属动画时读宿主 `Building+0x6E7`（`0x4519A8`）后置 1） | `0x423014` → 若再叠 `AnimType+0x374`（`ShouldFogRemove`）为真 → 硬切剔除（`jne 0x4238A3`） |
| `+0x19D` 地表不可见 | `0x423B5C`（`AnimClass::AI` 内调 `CellClass::IsVisibleTo` 的结果置位） | `0x422FEC` → `jne 0x4238A3`（**硬切剔除**） |
| 黑雾压暗 | — | `0x423621 call 0x487950`（`CellClass::IsShrouded`）→ `0x42362C` 把 16 位环境光置 0（**只影响灯色**，仍照原 Translucency 走 Blitter） |

> 🔺 **勘误（源文档）**：`fx_draw_chain.md` §2.2/§7-Q2 曾推测「`IsFogged` 半透明淡出公式未闭环」。反汇编定谳：**原版不存在任何非平凡渐变淡出公式**，只有「布尔硬剔除」+「黑雾调色归零」两种处理。三态迷雾若要淡出残影，必须在绘制层自行实现。

### 19.6 FX → Blit 归属：**禁止**在 Blit 层按来源剔除 [实证]

FX 的 Draw **不直接 call Blitter 虚表**，而是经 Convert / DSurface 形状族：

```text
AnimClass::Draw / ParticleClass::Draw / BulletClass::Draw / …
  → 0x55AF60（取 Convert/调色板）
  → 0x4AED70（TacticalClass::Draw_SHP）/ 0x4BBC90 / 0x4A35A0 / 0x4A35F0 / 0x4A3840 / 0x5AF980
  → Blitter::BlitTrans* / RLEBlitTrans*（§1 L1 已 Hook 的同一族）
```

⇒ **特效与单位/地形共享同一 Blit 族**。在 Blit 层按像素/来源做迷雾剔除会 ① 误伤地形与单位、② 破坏 §1 已向量化的 L1 Hook。**唯一允许的剔除位置 = v[65] / 各类 v[69] / 各 DrawAll 入口**（与 §2.5 纪律一致）。
补充：LaserDraw / EBolt / RadBeam 走**逐点/逐段矢量写表面**（单实例 Draw 内），**不走 SHP RLE Blit**，成本在线段长度与分段数。

### 19.7 v[65] vs v[69]：归属裁决（与 §2.5 的口径冲突，需 Lead 定谳）

全 .text 内 call [reg+0x104]（v[65] DrawIfVisible）**仅 7 处** [实证]：

| 调用点 | 所在路径 |
|:---:|:---|
| `0x6D909E` / `0x6D916C` / `0x6D93FA` | 主视图对象层 `0x6D8DB0`（三条支路） |
| `0x6D98E9` / `0x6D9A21` | 脏矩形补绘 `0x6D97D0` / `0x6D9920` |
| `0x43E6B7` / `0x43E788` | 建筑子部件自绘 |
| （`0x5F4CFD`，非外部调用点） | `0x5F4B10` 内部转 `call [eax+0x114]`（v[69]），出口 `ret 0xC` |

**雷达/小地图 RadarClass 零调用 v[65]** [实证]（与 `fx_draw_chain.md` §10.1 Q6 勘误一致）。

| 方案 | 内容 | 优点 | 风险/反证 | 裁决建议 |
|:---|:---|:---|:---|:---|
| **甲（与 §2.5 一致）** | Object 系 FX 逐类在**各自 v[69]** 短路；非 Object 四件套在 **DrawAll 循环体内** continue | 语义分区清晰；建筑残影不被破坏；与已落地 L3 Unit/Infantry/Aircraft 同模式 | 需逐类装钩（6+4 处） | **推荐** |
| 乙（H-FX1 / H-VXL1 原案） | 钩 ObjectClass::DrawIfVisible 共享体 `0x005F4B10`，「一处覆盖全部 Object 系」 | 钩点最少 | ① 直接违反 atlas §2.5 明令；② 共享体并非「一处覆盖全部」：Unit `0x73B0B0` / Anim `0x422C70` / VoxelAnim `0x749B20` 各自覆写或包装 v[65]；③ 建筑需三态残影而非布尔剔除；④ 本流**未逐类取证 v[65] 表项归属** | **暂不采用**；列为「待逐类 v[65] 表项取证后的可选优化」 |

⇒ **本流立场：维持 §2.5 纪律（方案甲）**；乙案需先补 §19.10 Q1 取证并经 Lead 裁决（见 [9]）。


### 19.8 成本中心与仅绘制层限频点 [实证 + 推演]

| 成本项 | 量级与证据 |
|:---|:---|
| Spotlight 包围盒 | `0x5FF916`（宽写点 = 255）、`0x5FF91E`（高写点，此处置 `edi=127`）⇒ 256×128 = 32,768 px；800×600 下**单灯占全屏 6.8%** |
| 同帧 10 个 ParticleSystem | 仅 Spotlight 遍历即 327,680 px（全屏 68.3%）[推演] |
| AnimClass::Draw | 体量大（坐标变换 + 多次 `0x4AED70` / `0x4BBC90` 形状绘制 + 灯色 IsShrouded）[实证 + 推演] |
| 双路径重复绘制 | `0x6D8DB0` 与 `0x6D97D0`/`0x6D9920` 可能对同一对象各画一次 ⇒ 谓词必须**幂等** [实证 + 推演] |

**允许的限频位置**：v[69] / DrawAll 循环体内 / Spotlight 半径内无直视时 continue / 同 ParticleSystem 子粒子按调色板·Translucency 分桶。**禁止**：在 Update 路径限频（改动画/粒子寿命与伤害时序 → 确定性高危）。

### 19.9 归因红线

- `IsShrouded(0x487950)`、`IsCellShrouded(0x5865E0)`、`RevealArea*`、`CreateGap/DestroyGap`、AI 可见性输入、任何 Update 的寿命/位置写 —— **不可改**。
- `EBolt` 短路必须保留 Lifetime 衰减（T-FX-1）。
- 单机/战役：绘制 Hook 不进存档；联机：仅保留红线内 Hook，且**回放两端必须同补丁**。

### 19.10 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证 | 级别 |
|:---:|:---|:---|:---|:---:|
| Q1 | 各类的 **v[65] 表项归属**（哪些类真用共享体 `0x5F4B10`） | 需逐类虚表扫描 + 调用点 xref | 对 6 类 FX + Building/Unit/Infantry/Aircraft 的 vtbl+0x104 表项逐个 dump；再统计 `0x5F4B10` 的 IMM 直呼数 | **P0**（决定 §19.7 裁决能否翻案） |
| Q2 | 单帧双路径重复绘制率 | 需运行时计数 | 钩 `0x5F4B10`，统计返回地址落入 `0x6D8DB0..0x6D9410` / `0x6D97D0..0x6D9A50` 的次数 | P1 |
| Q3 | LaserDraw/EBolt/RadBeam/Spotlight 容器的 Items·Count 落在 .data 未初始化区（**无文件数据，不可字节断言**） | 静态镜像无初值 | 真机读 Items 指针；或以 DrawAll 内的读取指令字节替代断言 | P2 |
| Q4 | ParticleSystem 的 Spotlight 触发条件（`+0xFA SpotlightRadius` 之外的开关） | 只在 `0x62E280` 内见读取 | 反汇编 `0x62E280` 全函数 + 对照 ParticleSystemTypeClass 字段 | P2 |
| Q5 | 各 FX Draw 的 ret 8 出口完整性（已抽 Bullet `0x468428` / Overlay `0x5FDF60`） | 需逐函数尾部扫描 | 对 6 类 Draw 做尾部出口枚举（Building 4 出口可作范式） | P2 |
| Q6 | `0x6D97D0` / `0x6D9920` 触发时机（与 §2.2/§2.3 打脏链的关系） | 需与 TacticalClass 重绘标志交叉 | 断点两者入口，记录调用栈与帧内序号 | P2 |
| Q7 | `0x556D40` 内 LineTrail 的线段栅格化是否与 LaserDraw 单实例 Draw 共用内外核 | 需全函数反汇编比对 | dump 两函数并做结构相似度比对 | P2 |

### 19.11 关键 VA 速查表

| VA | 名称/职责 | 证据等级 | 来源 |
|:---:|:---|:---:|:---|
| `0x006D3D10` | MapClass/Tactical::DrawIt 战术主绘制总函数 | [实证] | `fx_draw_chain.md:15,75` |
| `0x006D8DB0` | Object 绘制协调层（v[67]/v[68]/v[65] 序列） | [实证] | `fx_draw_chain.md:78-81` |
| `0x005F4B10` | ObjectClass::DrawIfVisible 共享体（v[65]），出口 ret 0xC | [实证] | `fx_draw_chain.md:38-52` |
| `0x00468090` | BulletClass::Draw（v[69]，vtable 0x007E46E4） | [实证] | `fx_draw_chain.md:16,58,117` |
| `0x00422CA0` | AnimClass::Draw（v[69]） | [实证] | `fx_draw_chain.md:16,138` |
| `0x0062CEC0` | ParticleClass::Draw（v[69]） | [实证] | `fx_draw_chain.md:16,160` |
| `0x0062E280` | ParticleSystemClass::Draw（v[69]，只画 Spotlight） | [实证] | `fx_draw_chain.md:16,175` |
| `0x0075F9F0` | WaveClass::Draw（v[69]，双端点 Shroud） | [实证] | `fx_draw_chain.md:16,190` |
| `0x00749B70` | VoxelAnimClass::Draw（v[69]） | [实证] | `fx_draw_chain.md:16,208` |
| `0x005FDF60` | OverlayClass::Draw 空桩（ret 8） | [实证] | `visibility_gap_spysat.md:463` |
| `0x00550240` / `0x00550260` | LaserDraw::DrawAll / 单实例 Draw | [实证] | `fx_draw_chain.md:234,235` |
| `0x004C2830` | EBolt::DrawAll（**Lifetime 在循环内衰减**） | [实证] | `fx_draw_chain.md:266,340-343` |
| `0x006591B0` | RadBeam::DrawAll | [实证] | `fx_draw_chain.md:290` |
| `0x005FFFA0` / `0x005FF850` | SpotlightClass::DrawAll / 单实例 Draw | [实证] | `fx_draw_chain.md:311-312` |
| `0x00556D40` | LineTrail::DrawAll（旧稿曾误标「杂项」） | [实证] | `fx_draw_chain.md:517,643-655` |
| `0x005865E0` | MapClass::IsCellShrouded —— **恒假桩（32 C0 / xor al,al; ret 4）** | [实证] | `bullet_particle_fog_deep_dive.md:67-73` |
| `0x004AED70` / `0x004BBC90` / `0x0055AF60` | FX 形状绘制 / 绘制核心 / 取 Convert（进 Blit 族） | [实证] | `fx_draw_chain.md:374-380` |
| `0x006D97D0` / `0x006D9920` | 脏矩形补绘 v[65] 支路（非小地图） | [实证] | `fx_draw_chain.md:91,516,634` |
| `0x004519B2` / `0x00423B5C` | AnimClass+0x199 IsFogged / +0x19D 写点 | [实证] | `fx_draw_chain.md:562,571` |
| `0x00421FC2` / `0x00424386` / `0x00424393` / `0x004247E5` | AnimClass+0x184 DelayTimer 写/递减/重挂 | [实证] | `fx_draw_chain.md:528-554` |
````

- **证据**：
  - 等级 **[实证]** —— 约 120 条地址落 `claims_R7.txt`（445 条全 OK，[6] 节贴原文）；来源 `docs/re/fx_draw_chain.md:14-113,117-221,227-324,328-384,388-455,501-741`、`docs/re/bullet_particle_fog_deep_dive.md:49-89,92-234,238-261,265-291,324-378,672-735`。
  - 等级 **[推演]**：Spotlight fillrate 量级、双路径重复绘制影响、线段栅格化内核共用性。
  - 等级 **[待实测]**：§19.10 Q2/Q3/Q4/Q6/Q7。
- **影响面**：
  - **§11 速查表**：新增约 25 行（FX 族 VA + vtable 表项 + 全局容器）。
  - **§12 契约**：新增 **T-FX-1**（EBolt Lifetime 在 DrawAll 内衰减 → 绘制函数带逻辑副作用，剔除位置受限）、**C-19-1**（FX 剔除只允许落 v[69]/DrawAll 循环体内，禁止 Blit 层与 v[65] 共享体）、**C-19-2**（AnimClass+0x184 禁作剔除开关）。建议挂 §12.1/§12.2。
  - **§2.1**：以「枢纽调用序」替代 Pass 编号表述，避免与 U3-P1 勘误冲突（不重复提交勘误）。
  - **§2.5**：v[65] 方案降级裁决（与 §18.8 同一立场），需 Lead 采纳或驳回（[9]）。
  - **§0 准则**：不改变既有裁决；为「只拦绘制」红线补充 EBolt 例外说明。


---

### PATCH-R7-03  新增 §20「裂缝与间谍卫星可见性分裂」专章

- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md` **L1981**，该行前 40 字符 = `## 附录 DA1 · 勘误登记（雷达挂钩地址与 G-10 覆盖，2026-09`（实跑 grep 唯一命中，见 §A ANCHOR-A）
- **动作**：`APPEND_SECTION`
- **现状问题**：atlas 现有内容**全库 0 命中** `CreateGap` / `DestroyGap` / `GapGenerator` / `0x6FB170` / `0x4555D0` / `0x508F60` / `0x5678E0` / `0x577D90` / `0x487690` / `0x1707` / `0x1701`（本流实跑 grep 复核）；§7.6 只登记了 3×6B NOP 的**改写方案**，未登记 ① 因果链（ShroudCounter 被 GapsCoveringThisCell 钳位）② 落地状态 ③ 超武/间谍卫星两条开图路径的差异。同时既有专题文档内部存在**两代口径**（旧稿把 BuildingTypeClass+0x1707 当 SuperGapRadiusInCells、把 TechnoType+0x5F0/+0x5F4 当裂缝半径、把 BuildingClass 槽 317–320 当 CreateGap/DestroyGap），若不收口进 atlas，后续实现会按错误偏移施工。
- **替换文本**：

````markdown
## 20. §20 裂缝与间谍卫星可见性分裂 (Gap Generator & SpySat Visibility Split)

> **事实来源**：`docs/re/gap_generator_spysat_deep_dive.md`（36 KB）与 `docs/re/visibility_gap_spysat.md`（44 KB，含 §9 冲刺定谳）。
> **二次复核**：本章约 130 条地址已落 `out/re_work/atlas_rev/R7/claims_R7.txt`（445 条断言全 OK）；其中**超武 12 路跳表逐项复算**（见 §20.5）。
> **口径纪律**：同一文档内部两代结论冲突时，**以 S1/深潜冲刺的定谳表为准**（`visibility_gap_spysat.md` §9.1 ERR-1…ERR-7、`gap_generator_spysat_deep_dive.md` §2.1/§6）。

### 20.1 「可见性分裂」的定义：两套权威并存 [实证]

尤里复仇引擎中，地面可见性由**两套彼此独立的状态权威**共同决定，二者无任何自动同步通道：

| 权威 | 载体 | 字段与语义 | 谁写 | 谁读 |
|:---|:---|:---|:---|:---|
| **A. 引擎 Cell 状态**（原版） | `CellClass`（`sizeof=0x148`，vtable `0x007E4EEC`） | `+0x12C CopyFlags`（bit3 `0x08` Explored、bit4 `0x10` Mapped）；`+0x130 ShroudCounter`；**`+0x134 GapsCoveringThisCell`**；`+0x140 RedrawFlags`（bit5 `0x20` 迷雾重绘）；`+0x120 Shroudedness` / `+0x121 Foggedness`；`+0x7C SensorsOfHouses[24]` / `+0xAC DisguiseSensorsOfHouses[24]` | `CreateGap/DestroyGap`、`RevealArea2/3`、`Reshroud`、`ReshroudCell` | `Draw_Shroud 0x47EFE0`、`Draw_Fog 0x47F250`、`CellClass::IsShrouded 0x487950`（经 `0x586360` 聚合每屋计数） |
| **B. 渲染层私有网格** | `ra2render` 的 `s_visionGrid[512*512] + s_visionToken` | 逐帧令牌：命中 = 本帧有己方/盟友直视 | `UpdateVisionGrid()`（按 Buildings/Units/Infantry/Aircraft 盖 `StampVisionCircle`） | 全部绘制层剔除谓词（§18.8/§19） |

**裂缝只走权威 A 的通道**：`CreateGap` 只碰 `+0x134`、`+0x12C` 与（经 `0x48716x` 族）`+0x7C` / `+0xAC`；**权威 B 完全不感知裂缝**。

> **契约 C-20-1（硬，缝合规则）**：绘制谓词必须显式合成两者：
> `ShouldDrawObject = 己方/盟友 ∨ ( s_visionGrid[idx] == s_visionToken ∧ ¬被敌方裂缝覆盖 )`
> 其中「被敌方裂缝覆盖」= **只读** `Cell+0x134 > 0`。依据：`CreateGap` 对玩家与盟友的裂缝**直接跳过盖印**（`0x6FB2D6 call 0x4F9A50` / `0x6FB2DD jne 0x6FB3C1`）⇒ 该计数**严格代表「对本地玩家敌对的裂缝数量」**，可直接当谓词用。
> **否定后果（与原版一致）**：缝内**己方单位/特效也不可见**。若只查权威 B，则「缝内己方直视格」会错误显形 —— 这是分裂的第一类危害。


### 20.2 裂缝生命周期管线 [实证]

```text
BuildingClass::Update 0x004549B0（每逻辑帧）
  └─ v[212] IsGeneratingGap 0x004555D0（七级门控）
       ├─ true  ∧ GeneratingGap==false → v[261] TechnoClass::CreateGap  0x006FB170 → GeneratingGap=1
       └─ false ∧ GeneratingGap==true  → v[262] TechnoClass::DestroyGap 0x006FB470 → GeneratingGap=0
            ├─ 逐格 Cell+0x134++ / --（0x6FB365 inc / 0x6FB5FB dec）
            ├─ CreateGap 还清 CopyFlags bit3/bit4（0x6FB399 清 0x10、0x6FB3B8 清 0x08）
            └─ DestroyGap 在 House+0x577A(SpySatActive) 且计数归零时恢复 bit3/bit4（0x6FB67A / 0x6FB699）
```

- **虚表归属（两代口径收口）**：`BuildingClass` 主虚表 `0x007E3EBC` 的表项 **`0x7E42D0` → `0x006FB170`（v[261] CreateGap）**、**`0x7E42D4` → `0x006FB470`（v[262] DestroyGap）** 已由本流**字节复算**（表项字节 `70 B1 6F 00` / `70 B4 6F 00`）。旧稿「槽 317–320 即 CreateGap/DestroyGap」**为误**，实际是 Sensor/DisguiseSensor 盖印族（见 §20.3）。
- **七级门控**（`0x4555D0`，任一失败即 `xor al,al` 返回）：

| # | 门控 | VA | 判据 |
|:---:|:---|:---:|:---|
| 1 | 超充/最小半径 | `0x4555DA` / `0x4555E4` | `GapSuperCharged(+0x660)` 或 `GapRadius(+0x67C) ≥ 2` |
| 2 | 吸取/超时空冻结/EMP | `0x4555F0` | `+0x504` 计数 > 0 → false |
| 3 | 存活 | `0x4555FE` | `Health(+0x6C) == 0` → false |
| 4 | 电力充足 | `0x45560F` / `0x455619` / `0x455623` / `0x455629` | `Type+0x1573 Powered` / `Type+0xEE4 PowerDrain` / `call 0x4FCE30 HasSufficientPower` |
| 5 | 间谍停电 | `0x455682` | `House+0x577B PowerBlackoutTimer` 非 0 → false |
| 6 | 手动断电 | `0x455686` / `0x455690` | `Type+0x1552 TogglePower` 且 `IsOnline(+0x6CC)==0` → false |
| 7 | 变卖/建造中 | `0x45569E` | `GetMission()` 为 `0x12 Selling` 或 `0x13 Construction` → false |

- **半径派发**（`BuildingClass::GetGapRadius 0x4566B0`）：`Type+0x170C` 升级覆盖优先；否则 `Type+0xCD1 GapGenerator` 为真时，按 `TechnoClass+0x268 GapSuperCharged` 选 **`Type+0xCD3 SuperGapRadiusInCells`** 或 **`Type+0xCD2 GapRadiusInCells`**。
- **INI 字段与字符串**（`TechnoTypeClass::Read_INI 0x713F80` 族）[实证，字符串内容已字节复算]：

| INI 键 | 字符串 VA | 存储偏移 | 读取点 |
|:---|:---:|:---:|:---:|
| `GapGenerator` | `0x00843E98` | `TechnoTypeClass+0xCD1` | `0x713F99` |
| `GapRadiusInCells` | `0x00843E84` | `TechnoTypeClass+0xCD2` | `0x713FB6` |
| `SuperGapRadiusInCells` | `0x00843E6C` | `TechnoTypeClass+0xCD3` | `0x713FD1` |


### 20.3 【勘误】两代口径收口表（以冲刺定谳为准）

| 编号 | 旧口径（错/过时） | 定谳（生效） | 本流复算状态 |
|:---:|:---|:---|:---|
| ERR-1 | BuildingClass 槽 317–320 = CreateGap/DestroyGap | 实为 **Sensor / DisguiseSensor 盖印族**：317 `0x455820`、318 `0x4556D0`、319 `0x455A80`、320 `0x455980` | 采纳（未逐表项复算） |
| ERR-2 | 同上槽位 | 真正 CreateGap/DestroyGap = **TechnoClass v[261]/v[262] = `0x006FB170` / `0x006FB470`** | **本流字节复算通过**（`0x7E42D0` / `0x7E42D4` 表项） |
| ERR-3 | TechnoType+0x5F0/+0x5F4 = 裂缝半径 A/B | 实为 **SensorsSight**（`0x7142EE` push `0x843D50`）/ **DetectDisguiseRange**（`0x714308` push `0x843D3C`） | 采纳（字符串内容已复算） |
| ERR-4 | 裂缝 INI 字段位置未定 | 位于 **TechnoTypeClass+0xCD1..+0xCD3** | **本流复算通过**（三处字符串 + 三处 push） |
| ERR-5 | BuildingTypeClass+0x1707 = SuperGapRadiusInCells | 实为 **CloakRadiusInCells**（char，默认 20）：`0x460C21` push `0x81A978`，ctor `0x45E22B` 赋 `0x14` | **本流复算通过**（字符串内容 = CloakRadiusInCells） |
| ERR-6 | BuildingTypeClass+0x1701 门 2 语义未决 | 实为 **InvisibleInGame**：`0x460DF2` push `0x81A8CC`；置位时 `BuildingClass::Draw` 于 `0x43D316` 提前 `ret 8` | **本流复算通过**（字符串内容 = InvisibleInGame） |
| ERR-7 | PerCell「三兄弟」`0x487160` / `0x487170` / `0x487180` | 实为**四兄弟**：`0x487150`（`inc word` 于 `+0x7C+house*2`）、`0x487160`（`dec` 同址）、`0x487170`（`inc` 于 `+0xAC+house*2`）、`0x487180`（`dec` 同址） | 采纳（四入口均可读） |

> **补强**：ERR-2 原为单来源（冲刺定谳表的字节描述）；本流以**虚表表项字节**独立复核，使其升级为「字节可复核」。ERR-4/5/6 由字符串 VA + 内容双重复核（例如 `47 61 70 47 65 6E 65 72 61 74 6F 72` 即 GapGenerator）。
> **遗留语义分歧（未闭环）**：`Cell+0x7C`（gap 族读作每屋覆盖计数）与已落地渲染层 `ShouldDrawMobileObject` 读的 `Cell+0xAC`（传感器 Word 数组）**同址但语义可能不同**（`visibility_gap_spysat.md` §6 已提示「衔接时必须统一命名并加注释」）⇒ 见 §20.9 Q3。

### 20.4 永久废缝因果链：引用计数被清零 + ReshroudCell 钳位 [实证]

**三处硬编码清零写点**（`.text`，字节已复算；替换为 6B NOP 即 M-10 P-2 方案 A）：

```asm
; [1] MapClass::RevealArea2 内层循环（PsychicReveal 距离开图）      文件偏移 0x168273
00568273  89 99 34 01 00 00   mov dword ptr [ecx+0x134], ebx   ; ebx = 0
; [2] MapClass::RevealArea3（SpySat 全图开图）                     文件偏移 0x177EC5
00577EC5  89 B8 34 01 00 00   mov dword ptr [eax+0x134], edi   ; edi = 0
; [3] MapClass::Reshroud（SpySat 离线重遮蔽）                      文件偏移 0x177B60
00577B60  89 98 34 01 00 00   mov dword ptr [eax+0x134], ebx   ; ebx = 0
```

**钳位机制**（`CellClass::ReshroudCell 0x00487690`）：

```asm
00487691  mov esi, [ecx+0x130]   ; 保存旧 ShroudCounter
004876A6  mov eax, [ecx+0x130]   ; 读 ShroudCounter
004876AC  inc eax               ; ShroudCounter++
004876AD  mov [ecx+0x130], eax
004876B5  mov eax, [ecx+0x134]   ; eax = GapsCoveringThisCell
004876BB  cmp edx, eax           ; ShroudCounter 与 GapsCovering 比较
004876BD  jle 0x4876C5
004876BF  mov [ecx+0x130], eax   ; 截断：ShroudCounter = GapsCovering（可为 0）
004876D4  or  byte [ecx+0x140], 0x20  ; 置迷雾重绘脏位
```

> **不变量 I-GAP-1（硬）**：`ShroudCounter` 被 `GapsCoveringThisCell` **钳位为下界**。若 `+0x134 == 0`，则任何重遮蔽尝试都被截断为 0 ⇒ **该格永远不可能回到黑雾**。
> **死锁闭环**：`CreateGap` 只在 `GeneratingGap` 由 false 变 true 的**跳变**时被调用（`0x6FB180` 的自身去重检查早退）⇒ 计数被清零后，建筑**不会**重新盖印（它以为仍在生效）⇒ **裂缝永久失能**，直到建筑被打爆/断电/变卖使七级门控翻假（§20.2 门控 3/4/5/6/7）。
> **危害等级**：这是「分裂」最严重的一阶后果 —— **权威 A 内部自毁，而权威 B 无感**（`s_visionGrid` 照旧只反映己方/盟友直视），表现层不会给出任何异常信号，属**静默失能**。


### 20.5 间谍卫星与超武开图链 [实证]

**（a）SpySat 状态机 `HouseClass::UpdateSpySat 0x00508F60`**

| 步骤 | VA | 行为 |
|:---|:---:|:---|
| 遍历本阵营建筑，判 BuildingType+0x16A5 SpySat | `0x508F88` | `cmp byte [eax+0x16a5],0` |
| 存活/有电过滤 | `0x508F91` | `IsAlive(+0x81)` / `HasPower(+0x74)` |
| 上线（SpySatActive 置 1） | `0x509069` + `call 0x577D90` | **MapClass::RevealArea3 全图开图** |
| 离线（SpySatActive 清 0） | `0x509017` + `call 0x577AB0` | **MapClass::Reshroud 全图重遮蔽** |
| 建筑摧毁收尾 | `0x50BD10` | `if (SpySatActive) Reshroud` |

**（b）超武分发 `SuperClass::Launch 0x006CC390`**

```asm
006CC3A3  mov eax, [ebp+0xB4]              ; SuperWeaponTypeClass::Type（枚举 0..11）
006CC3A9  cmp eax, 0xB
006CC3AC  ja  0x6CDE36                    ; 越界退出
006CC3B2  jmp dword ptr [eax*4+0x6CDE44]  ; 12 路无条件跳表
```

**12 路跳表逐项字节复算**（`0x006CDE44`，本流输出，与来源文档逐项一致）：

| 索引 | 枚举 | Case 入口 | 索引 | 枚举 | Case 入口 |
|:---:|:---|:---:|:---:|:---|:---:|
| 0 | Nuke | `0x006CDA67` | 6 | AmerParaDrop | `0x006CD537` |
| 1 | IronCurtain | `0x006CCE64` | 7 | PsychicDominator | `0x006CCDBD` |
| 2 | LightningStorm | `0x006CCD3F` | **8** | **SpyPlane** | **`0x006CD66F`** |
| 3 | ChronoSphere | `0x006CC3B9` | 9 | GeneticMutator | `0x006CD7E7` |
| 4 | ChronoWarp | `0x006CC4B2` | 10 | ForceShield | `0x006CD072` |
| 5 | ParaDrop | `0x006CD2EE` | **11** | **PsychicReveal** | **`0x006CD70C`** |

**（c）两条开图路径对权威 A 的写入差异（本章关键对比）**

| 路径 | 入口 | 对细胞状态的写入 | 是否清 +0x134 |
|:---|:---|:---|:---:|
| **PsychicReveal**（索引 11） | `0x6CD70C` → **两次** `MapClass::RevealArea2 0x5678E0`（`0x6CD773` SkipReveal=0 开雾 / `0x6CD79C` SkipReveal=1 记探索）→ `0x6CD7BF call 0x750E20`（雷达事件/音效） | 圆域每格：`CopyFlags |= 0x18`、`ShroudCounter=0`、**GapsCovering=0**、`+0x140` 标志；半径取 `SW+0xF8 Range`，为 0 则 `Rules+0xFEC`；夹紧 `min(10, radius)`（`0x567A4A`） | **是（废缝）** |
| **SpyPlane**（索引 8） | `0x6CD66F` | 遍历雷达点播扫描线动画；**不改 Shroud 字段**，靠机体视距实时盖印 | 否 |
| **SpySat 上线** | `0x577D90`（RevealArea3） | 全图每格 `CopyFlags |= 0x18`、`ShroudCounter=0`、**GapsCovering=0** | **是（废缝）** |
| **SpySat 离线 / 建筑摧毁** | `0x577AB0`（Reshroud） | 每格 `ShroudCounter=1`、**GapsCovering=0**、`CopyFlags &= ~0x18`；并 `House+0x240=0` + `0x657CE0` 刷新 | **是（废缝）** |


### 20.6 交叉引用与**落地状态**（与 §7.6 的关系）[实证 + 待实测]

- atlas **§7.6** 已登记 3×6B NOP 的**改写方案**；本章补三点：① 因果链（§20.4）② 落地状态（本小节）③ 两条开图路径差异（§20.5c）。
- **落地状态（本流快照 2026-09-29）**：
  - `ra2render/**` 全库检索 `568273` / `577EC5` / `577B60` ⇒ **0 命中**，即 **3×6B NOP 未由渲染 DLL 安装**；与 `docs/re/mp_landing_consistency.md:19` 的「政策已定 ≠ 已落地」口径一致。
  - 现网 DLL 走的是**另一条路线**：`PatchSpySatBuildingTypes()`（`ra2render/blitter_hooks.cpp:1370-1429`，只读引用）把 `BuildingType+0x16A5` 置 false、把 `+0x16F0` 绑到 `PsychicReveal` 超武索引、并改 `SW+0xB0`（CD）与 `SW+0xF8`（Range）；同时在 `UpdateVisionGrid()` 内每帧写 `pPlayer+0x577A = 0`（`ra2render/blitter_hooks.cpp:1532`）并强制清 `Scenario.Flags & 0x1000`（同文件 `:1528`）。
  - **后果（P1 产品级缺口）**：`House+0x577A = 0` 恒写只封住 **SpySat 路线**（`0x508F60` 的 `0x509064` / `0x509012` 分支）；**PsychicReveal 路线仍会经 `RevealArea2` 清 +0x134（`0x568273`）** ⇒ 只要对局中出现 PsychicReveal/超能雷达，废缝 bug 依然可复现。
  - **[待实测]**：真机断点读 `0x568273` 首字节——`89` = 未打补丁（原版清零），`90` = 已打 6B NOP。本流**未启动游戏、未改动任何二进制**，故不下达「已落地」结论。

### 20.7 确定性红线与联机门控 [实证 + 推演]

| 项 | 目标 / VA | 建议 | 确定性风险 |
|:---|:---|:---|:---|
| H-20-A（方案 A） | `0x568273` / `0x577EC5` / `0x577B60` 三处 6B 等长 NOP | 保护裂缝引用计数；`EnableGapProtection` 开关 + 逐字节还原 | **触及 ①同步语义 ③存档结构**（`CellClass+0x134` 随存档/校验演进，见 `docs/re/execution_runbook.md:56`）⇒ **必须 MP 门控矩阵 + 真机对拍验收，严禁混端联机** |
| H-20-B（只读合成） | 绘制谓词追加只读 gap 判定（`Cell+0x134 > 0`） | 与 §18.8 / §19.7 同一谓词，幂等 | 低（纯绘制） |
| H-20-C（雷达开窗） | PsychicReveal 扫描结果写私有 `s_radarSweepExpireFrame[512*512]`（600 帧窗口），**不写引擎 `+0x134`** | 实现「透缝扫描后缝仍在」的产品语义 | 中（[推演]；若误走 `RevealArea2` 则回到废缝） |
| H-20-D（禁改） | `SuperClass::Launch 0x6CC390`、`RevealArea2/3 0x5678E0/0x577D90`、`Reshroud 0x577AB0`、`CreateGap/DestroyGap 0x6FB170/0x6FB470` | **禁止 Hook 改写** | **极高**（逻辑帧路径，直接改 Cell 状态 → 帧校验/Desync） |

**红线重申**：可改 = 绘制层（`Draw` / `CellClass::Draw` 挂载的 `Draw_Fog` / 私有网格）；不可改 = `IsShrouded 0x487950` / `IsCellShrouded 0x5865E0` / `RevealArea*` / `CreateGap` / `DestroyGap` / AI 可见性输入 / `SelectAutoTarget` 族。**单机/战役的绘制 Hook 不进存档；但方案 A 是代码段静态改写，会改变 Cell 状态演进，属联机门控项。**

### 20.8 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证 | 级别 |
|:---:|:---|:---|:---|:---:|
| Q1 | 3×NOP 是否已由**外部补丁器/加载器**安装 | 本流只读 `ra2render/**`；不排除其他安装路径 | 真机读 `0x568273` 首字节（`89` / `90`）；或检查加载器安装清单 | **P0** |
| Q2 | `+0x134` / `+0x130` / `+0x12C` 是否进 `.SAV` 与帧 CRC | 需复算存档块与校验链（超出本流来源范围） | 对照 `savegame_block_manifest.md` / `net_sync_checksum.md`；真机对拍 | **P1** |
| Q3 | `Cell+0x7C` 与 `Cell+0xAC` 的**语义归属**（SensorsOfHouses vs gap 计数 vs 渲染层传感器读点） | 两代文档同址异名；需运行时对照 | 打日志对比同格两计数随裂缝/传感器的变化 | **P1** |
| Q4 | `RevealArea2/3`、`Reshroud` 内是否还有**第 4 处** `+0x134` 写入 | 本流只复核了 3 处已知写点 | 对三函数做全函数 `0x134` 立即数/寄存器扫描 | P1 |
| Q5 | PsychicReveal「透缝扫描」产品语义（方案 A/B/C 已定谳 A，但未落地） | 属产品决策 + 落地状态 | 由 Lead 确认后再按 §20.7 门控实施 | P1 |

### 20.9 关键 VA 速查表

| VA | 名称/职责 | 证据等级 | 来源 |
|:---:|:---|:---:|:---|
| `0x0043D290` | BuildingClass::Draw（v[69]），门 2 于 `0x43D316`（`Type+0x1701` InvisibleInGame） | [实证] | `visibility_gap_spysat.md:14,37-58` |
| `0x004549B0` | BuildingClass::Update（每帧驱动裂缝门控） | [实证] | `gap_generator_spysat_deep_dive.md:201` |
| `0x004555D0` | BuildingClass::IsGeneratingGap（v[212]，七级门控） | [实证] | `gap_generator_spysat_deep_dive.md:119-195` |
| `0x004566B0` | BuildingClass::GetGapRadius（半径派发） | [实证] | `gap_generator_spysat_deep_dive.md:93-115` |
| `0x006FB170` / `0x006FB470` | TechnoClass::CreateGap / DestroyGap（v[261]/v[262]） | [实证] | `gap_generator_spysat_deep_dive.md:205-281` |
| `0x00487690` | CellClass::ReshroudCell（钳位截断点 `0x4876BF`） | [实证] | `gap_generator_spysat_deep_dive.md:313-339` |
| `0x00487150` / `0x487160` / `0x487170` / `0x487180` | PerCell 四兄弟（Sensor/DisguiseSensor 计数增删） | [实证] | `visibility_gap_spysat.md:444,450` |
| `0x00568273` / `0x00577EC5` / `0x00577B60` | 三处 `+0x134` 强制清零写点（**Bug 面**） | [实证] | `visibility_gap_spysat.md:472-475` |
| `0x005678E0` / `0x00577D90` / `0x00577AB0` | RevealArea2 / RevealArea3 / Reshroud | [实证] | `visibility_gap_spysat.md:428` |
| `0x00508F60` | HouseClass::UpdateSpySat（SpySat 状态机） | [实证] | `gap_generator_spysat_deep_dive.md:440-470` |
| `0x006CC390` / `0x006CDE44` | SuperClass::Launch / 超武 12 路跳表（本流逐项复算） | [实证] | `gap_generator_spysat_deep_dive.md:345-354` |
| `0x006CD70C` / `0x006CD66F` | PsychicReveal（Case 11）/ SpyPlane（Case 8） | [实证] | `gap_generator_spysat_deep_dive.md:369,366` |
| `0x00750E20` | 雷达事件/音效播发 | 推演（来源仅行为描述） | `gap_generator_spysat_deep_dive.md:393` |
| `0x005865E0` | MapClass::IsCellShrouded（**恒假桩**） | [实证] | `bullet_particle_fog_deep_dive.md:65-73` |
| `0x00487950` / `0x00586360` | CellClass::IsShrouded / 每屋计数聚合内核 | [实证] | `visibility_gap_spysat.md:204` |
| `0x0047EFE0` / `0x0047F250` / `0x004801F0` | Draw_Shroud / Draw_Fog / CellClass::Draw | [实证] | `visibility_gap_spysat.md:198-199` |
| `0x00843E98` / `0x00843E84` / `0x00843E6C` | INI 键 GapGenerator / GapRadiusInCells / SuperGapRadiusInCells | [实证] | `visibility_gap_spysat.md:447` |
| `0x00713F99` / `0x00713FB6` / `0x00713FD1` | 上述三键的 Read_INI 读取点（写入 `+0xCD1..+0xCD3`） | [实证] | `visibility_gap_spysat.md:447` |
| `0x0081A978` / `0x00460C21` / `0x0045E22B` | CloakRadiusInCells 串 / 读取点 / ctor 默认 0x14 | [实证] | `visibility_gap_spysat.md:448` |
| `0x0081A8CC` / `0x00460DF2` | InvisibleInGame 串 / 读取点 | [实证] | `visibility_gap_spysat.md:449` |
| `0x00843D50` / `0x007142EE` / `0x00843D3C` / `0x00714308` | SensorsSight / DetectDisguiseRange 串与读取点 | [实证] | `visibility_gap_spysat.md:446` |
| `0x007E42D0` / `0x007E42D4` | BuildingClass v[261]/v[262] 表项 = CreateGap/DestroyGap | **本流字节复算** | `visibility_gap_spysat.md:445` |

````

- **证据**：
  - 等级 **[实证]** —— 约 130 条地址落 `claims_R7.txt`（445 条全 OK，[6] 节贴原文）；其中超武 12 路跳表、三处清零字节、`CloakRadiusInCells` / `InvisibleInGame` / `GapGenerator` 等字符串内容、PerCell 四兄弟入口、PerCell 表项指针均**逐字节复算通过**。来源 `docs/re/gap_generator_spysat_deep_dive.md:14-21,73-115,119-195,201-281,289-311,313-339,345-394,402-419,440-470,685-691`、`docs/re/visibility_gap_spysat.md:14-24,30-140,145-216,222-284,295-301,307-355,361-384,438-516`。
  - 等级 **[推演]**：600 帧雷达开窗窗口设计、`+0x134` 的存档/CRC 影响面。
  - 等级 **[待实测]**：§20.6 落地状态确认（`0x568273` 首字节）、§20.8 Q1–Q4。
- **影响面**：
  - **§11 速查表**：新增约 30 行（裂缝/视野族 VA + 字段 + INI 串）。
  - **§12 契约**：新增 **C-20-1**（两权威合成规则：`s_visionGrid ∧ ¬Cell+0x134>0`）、**I-GAP-1**（`ShroudCounter` 钳位不变量，任何清零即永久废缝）；建议挂 §12.1/§12.2，并点名 §12.2 联机红线（方案 A 属门控项）。
  - **§7.6**：不重复提交改写（PATCH-R7-04 仅追加落地状态与跨引，见下）。
  - **§2.4 / §2.5**：三态迷雾的「缝内不可见」规则为 §2.4 三态定义的**前置条件**（否则三态与裂缝语义冲突）。
  - **§0 准则**：为「只拦绘制」红线补充「代码段静态改写属联机门控项」的边界说明。


---

### PATCH-R7-04  §7.6 追加「因果链 + 落地状态 + 跨引」（小补丁 / 非新章）

- **目标锚点**：`docs/re/ARCHITECTURE_ATLAS.md` **L1280**，该行前 40 字符 = 「  将上述三处 6 字节指令全部替换为 90 90 90 90 90 90（」（实跑 grep 唯一命中，见 §A ANCHOR-B）
- **动作**：`INSERT_AFTER`
- **现状问题**：§7.6 只给出 3×6B NOP 的**改写方案**，未记录 ① 为什么清零会造成**永久**废缝（`ReshroudCell` 的钳位截断）② 该补丁的**落地状态**（本流快照下 `ra2render/**` 0 命中，未安装）③ 与超武/间谍卫星两条开图路径的关系。缺此三者，读者会误以为「清零一次 = 漏一次雾」，从而低估危害并可能误判已闭环。
- **替换文本**：

````markdown
**补记（R7 流，2026-09-29；不改变本节上述改写方案）**：

1. **为什么是「永久」废缝**：`CellClass::ReshroudCell`（`0x00487690`）在 `0x4876BF` 处执行 `mov [ecx+0x130], eax`，把 `ShroudCounter(+0x130)` **截断钳位**到 `GapsCoveringThisCell(+0x134)`。一旦后者被清零，该格的重遮蔽结果恒为 0 —— **永远无法回到黑雾**。
2. **为什么不会自愈**：`TechnoClass::CreateGap`（`0x006FB170`）在 `0x6FB180` 做「已生成则早退」去重，只响应 `GeneratingGap` 的 false→true **跳变**；计数被清零后建筑仍认为自己在生效，**不会重新盖印**。
3. **落地状态（快照口径）**：`ra2render/**` 全库检索 `568273` / `577EC5` / `577B60` 为 **0 命中** ⇒ 该 6B NOP **尚未由渲染 DLL 安装**；现网 DLL 走的是「关 `BuildingType+0x16A5` + 绑 `PsychicReveal` + 恒写 `House+0x577A=0`」路线，只封住 SpySat 路线，**PsychicReveal 经 `RevealArea2` 清计数（`0x568273`）的路径未封**。
4. **完整拓扑与判定规则见新增 §20**（两套可见性权威 + 契约 C-20-1 + 不变量 I-GAP-1），确定性门控见该章 §20.7。
````

- **证据**：[实证] 三处 6B 字节（`0x568273` = `89 99 34 01 00 00`、`0x577EC5` = `89 B8 34 01 00 00`、`0x577B60` = `89 98 34 01 00 00`）、`0x4876BF` = `89 81 30 01 00 00`、`0x6FB365` = `41 89`（`inc ecx`）、`0x6FB5FB` = `4A 89`（`dec edx`）均落 `out/re_work/atlas_rev/R7/claims_R7.txt`；来源 `docs/re/gap_generator_spysat_deep_dive.md:313-339,398-436`、`docs/re/visibility_gap_spysat.md:468-484,505-515`；[待实测] 落地状态确认为真机读 `0x568273` 首字节。
- **影响面**：仅补强 §7.6 可读性与危害定级，**不改动其结论**；若 R3 流已在同位置提交插入，请 Lead 以「先到优先 + 合并要点」处理或直接丢弃本块（本块不承载独有事实，独有事实均已写入 §20）。


---

## C. 十节回执（AGENT_DELIVERY_FORMAT.md 骨架）

```text
[META]
task=task-9（流 R7：补写 atlas 新章 §18 / §19 / §20）
executor=atlas-r7-vxl-fx（DSH 子代理 / Agent Teams 成员）
elapsed≈2600s（自评，未精确计时）  mode=read-only（仅写本流作用域；基线二进制只读）
scope_declared=docs/re/atlas_rev/R7_vxl_fx_gap.md、out/re_work/atlas_rev/R7/**
snapshot=2026-09-29；baseline ra2youli/gamemd.exe MD5 4F37486E5B0DBE2AE5F45AEEE0F98367（4,825,360 B）
```

### [0] 结论摘要

1. **产出 4 个锚定补丁块**（3 个 APPEND_SECTION 新章 + 1 个 §7.6 INSERT_AFTER），全部锚点经实跑 grep 唯一命中（L1981 / L1280），**未触碰** `docs/re/ARCHITECTURE_ATLAS.md` 与其他 R# 文件。
2. §18 建立 **VXL 体素渲染的三层链路 + `SomeVoxelCache` 两级查找/扩容 + 阴影键不含 Z 桶** 三条架构事实，并给出两条顺序不变量（先影后体 / 重排绘制序须全量 ZReadWrite）与一项跨子系统契约（`+0xDBE/+0xDBF` 属类型层持久化属性）。
3. §19 收口 FX 归属：**「自带雾门全废」因果链**（`Flags&0x1000` 被清 + `IsCellShrouded` 为恒假桩），并把 **EBolt Lifetime 在 DrawAll 内衰减** 立为结构性陷阱（T-FX-1）；同时给出 **v[65] vs v[69] 归属裁决建议（维持 §2.5 纪律）**。
4. §20 定义**可见性分裂**（引擎 Cell 状态 vs 渲染层私有网格两权威），给出 **不变量 I-GAP-1**（`ShroudCounter` 被 `GapsCoveringThisCell` 钳位 ⇒ 清零即永久废缝）与**落地状态实证**（3×6B NOP 未由渲染 DLL 安装）。
5. **最大风险**：§20.6 揭示的 **P1 产品级缺口** —— 现网只封 SpySat 路线，PsychicReveal 仍可经 `0x568273` 清计数导致裂缝永久失能；方案 A 属代码段静态改写，**触及同步语义与存档结构，必须走 MP 门控矩阵 + 真机对拍验收**。

### [1] 逐条必答项结论表

| # | 问题 | 结论 | 证据等级 | 证据锚点 |
|:---:|:---|:---|:---:|:---|
| 1 | 载具体素绘制入口与分流 | `UnitClass::Draw 0x73CEC0` 按 `UnitType+0x236` 分流至 v[341] `DrawAsVXL 0x73B470` / v[342] `DrawAsSHP 0x73C5F0` | [实证] | `vxl_render_sort.md:14`；claims `0x73D317/0x73D31F` |
| 2 | `Draw_A_VXL` 拓扑 | v[324] `0x4DAF10` → `0x706640`（flags/Convert，恒 OR `0x800`）→ `0x707480`（光栅+Blit） | [实证] | `vxl_render_sort.md:188-190`；claims `0x4DAF10/0x706640/0x70674D/0x707480` |
| 3 | 体素缓存结构与查找 | `SomeVoxelCache` = `0x14` 字节；`VoxelCaches[4]` 基址 `Type+0x258`；条目 8 B（Key/Data）；L1 `0x746EA0` MRU → L2 `0x7107E0`（脏则 `qsort 0x7C8B48` + 二分 `0x710890`） | [实证] | `vxl_cache_layout.md:14,29-56`；claims `0x746EA0/0x7107E0/0x706D78/0x7C8B48` |
| 4 | 缓存键是否含 Z 桶 | 车体键**含**（`Type+0x720==0` 时清除）；**阴影键不含** Z 桶，格式 `(((ShadowIndex<<6)+SlopeFacing)<<5) | (facing&0x1F)` | [实证] | `vxl_cache_layout.md:18,244-255`；claims `0x55A86D/0x55A89E` |
| 5 | 缓存与存档/同步的耦合 | `DisableVoxelCache/DisableShadowCache`（`+0xDBE/+0xDBF`）在类型层 `v[13]` 打包（`0x717767/0x717775`）⇒ 属持久化属性，改造必须尊重 | [实证] | `vxl_cache_layout.md:15,120-136`；claims `0x717767/0x717775` |
| 6 | Z 梯度表数值 | `0x817710` 4 项 × 24 B，本流**整表字节复算**与来源一致（Ground/Deg45/Deg90/Deg135，Deg90 的 `ModeFlag=0`） | [实证] | `vxl_cache_layout.md:163-173`；claims `0x817710`（96 B） |
| 7 | 哪些 Loco 有非零动态 Z 梯度 | 仅 `TunnelLocomotionClass 0x729E50`；其余（Drive `0x4B4870` 等）恒返 0 | [实证] | `vxl_cache_layout.md:20,289-316`；claims `0x729E50/0x4B4870/0x72A000` |
| 8 | FX 是否有统一 Draw 门 | **没有**；统一的是 `DrawIfVisible 0x5F4B10`（v[65]）→ `call [eax+0x114]`（v[69]）；`.text` 内 v[65] 调用点全量 7 处 | [实证] | `fx_draw_chain.md:14,38-52`；claims `0x5F4B10/0x5F4CFD/0x5F4D0C` |
| 9 | 为什么敌方弹道在黑雾中可见 | 双重失效：`Flags&0x1000` 被强制清零（`0x4680AB` 直接跳过）+ `IsCellShrouded 0x5865E0` 是恒假桩（`32 C0` / `xor al,al; ret 4`） | [实证] | `bullet_particle_fog_deep_dive.md:49-88`；claims `0x5865E0/0x4680A8` |
| 10 | 非 Object 渲染器归属 | `LaserDraw 0x550240` / `EBolt 0x4C2830` / `RadBeam 0x6591B0` / `Spotlight 0x5FFFA0`；均由 DrawIt 固定时序调用 | [实证] | `fx_draw_chain.md:15,17,239-313`；claims `0x550240/0x4C2830/0x6591B0/0x5FFFA0` |
| 11 | EBolt 剔除的最大陷阱 | `Lifetime` 在 `DrawAll` 内衰减到 0 才析构 ⇒ 整函数短路会使电弧永生；必须在循环体内 `continue` | [实证] | `fx_draw_chain.md:340-343`；claims `0x4C2830/0x4C2856` |
| 12 | `AnimClass+0x184` 能否当剔除开关 | **不能**：它同时门控 Draw 与 Update，且归零触发音效/逻辑（`0x4243A1 call 0x424CE0`）与随机重挂（`0x4247E5` 消费 RNG）⇒ 会改变 RNG 消费序 | [实证] | `fx_draw_chain.md:524-555`；claims `0x421FC2/0x424386/0x424390/0x424393/0x4247E5` |
| 13 | 是否可在 Blit 层按来源剔除 FX | **不可**：FX 与单位/地形共享同一 Blit 族（经 `0x55AF60/0x4AED70/0x4BBC90` 等）⇒ 剔除点只能是 v[65]/v[69]/DrawAll | [实证] | `fx_draw_chain.md:370-384`；claims `0x4AED70/0x4BBC90/0x55AF60` |
| 14 | 裂缝 INI 字段在哪 | `TechnoTypeClass+0xCD1 GapGenerator` / `+0xCD2 GapRadiusInCells` / `+0xCD3 SuperGapRadiusInCells`（字符串 VA 已复算） | [实证] | `visibility_gap_spysat.md:447`；claims `0x843E98/0x843E84/0x843E6C/0x713F99` |
| 15 | `BuildingTypeClass+0x1707` 是裂缝超充半径吗 | **否**，是 `CloakRadiusInCells`（默认 `0x14`）；`+0x1701` 是 `InvisibleInGame`（BuildingClass::Draw 门 2，`0x43D316`） | [实证] | `visibility_gap_spysat.md:448-449,508`；claims `0x81A978/0x81A8CC/0x45E22B` |
| 16 | 真正的 CreateGap/DestroyGap 在哪 | `TechnoClass` v[261] `0x6FB170` / v[262] `0x6FB470`；BuildingClass vtable 表项 `0x7E42D0/0x7E42D4` **本流字节复算通过** | [实证] | `visibility_gap_spysat.md:445`；claims `0x7E42D0/0x7E42D4/0x6FB365/0x6FB5FB` |
| 17 | 裂缝为什么会永久失效 | 三处清零（`0x568273/0x577EC5/0x577B60`）破坏 `+0x134`；`0x4876BF` 把 `+0x130` 钳位截断 ⇒ 永不可重遮蔽；且 `CreateGap` 仅在跳变时调用 ⇒ 不自愈 | [实证] | `gap_generator_spysat_deep_dive.md:313-339,421-436`；claims `0x568273/0x577EC5/0x577B60/0x4876BF` |
| 18 | 间谍卫星与超武如何开图 | `SpySat` → `RevealArea3 0x577D90` / `Reshroud 0x577AB0`；`SuperClass::Launch 0x6CC390` → 12 路跳表 `0x6CDE44`（**逐项复算**）：Case 11 `0x6CD70C` → 双调 `RevealArea2 0x5678E0` | [实证] | `gap_generator_spysat_deep_dive.md:345-394,440-470`；claims `0x6CDE44`（48 B）/`0x509069/0x509017` |
| 19 | 3×6B NOP 是否已落地 | **未落地**：`ra2render/**` 0 命中三处地址；现网走 `PatchSpySatBuildingTypes`（`blitter_hooks.cpp:1370-1429`）+ 恒写 `pPlayer+0x577A=0`（~B:~1532`） | [实证]（代码检索）+ [待实测]（真机字节） | `docs/re/mp_landing_consistency.md:19`；本流 §20.6 |
| 20 | 两套可见性权威如何缝合 | 谓词 = 己方/盟友 ∨ (私有网格命中 ∧ ¬(`Cell+0x134>0`))；缝内己方亦不可见（与原版一致） | [实证] | `gap_generator_spysat_deep_dive.md:641-643`；`visibility_gap_spysat.md:398`；本流 §20.1 |

### [2] 关键证据块

- **机器可读断言**：`out/re_work/atlas_rev/R7/claims_R7.txt` —— **445 条**，格式 `0xVA = HEXBYTES    # 注释 | 反汇编`，由 `out/re_work/atlas_rev/R7/gen_claims_r7.py` 从基线二进制直读生成（非手抄）。
- 代表性断言（原始字节，全部经 `tools/audit_bytes.py` 复算 = OK）：
  - `0x73CEC0 = A0 9C CF B1 00`（`UnitClass::Draw` 入口第一条）
  - `0x73B470 = 81 EC B4 01 00 00`（`DrawAsVXL` 入口 `sub esp,0x1B4`）
  - `0x707480 = 83 EC 50`（VXL 光栅核入口）
  - `0x706D78 = BB 0A 00 00 00`（缓存初始容量 = 10）
  - `0x817710 = 01 00 00 00 01 00 00 00 01 00 00 00 01 00 00 00 FF FF FF FF 01 00 00 00 …`（Z 梯度表 96 B 全量）
  - `0x55A89E = 0B C8`（`or ecx,eax`，阴影键合成）
  - `0x5865E0 = 32 C0`（`IsCellShrouded` 恒假桩）
  - `0x5F4D0C = C2 0C 00`（`DrawIfVisible` 出口 `ret 0xC`）
  - `0x422C70 = 8B 81 84 01 00 00`（`AnimClass` DelayTimer 门）
  - `0x6D3D10 = 81 EC F4 00 00 00`（DrawIt 入口）
  - `0x6CDE44`（48 B）= 12 路超武跳表，逐项 = `0x6CDA67/0x6CCE64/0x6CCD3F/0x6CC3B9/0x6CC4B2/0x6CD2EE/0x6CD537/0x6CCDBD/0x6CD66F/0x6CD7E7/0x6CD072/0x6CD70C`
  - `0x568273 = 89 99 34 01 00 00` ／ `0x577EC5 = 89 B8 34 01 00 00` ／ `0x577B60 = 89 98 34 01 00 00`（三处 `+0x134` 清零）
  - `0x4876BF = 89 81 30 01 00 00`（`ShroudCounter` 钳位截断）
  - `0x72A000`（20 B）= Tunnel Z_Gradient 5 路跳表 = `0x729F74/0x729FCC/0x729F40/0x729FDE/0x729F52`
  - INI 字符串（内容级复算）：`0x843E98` = "GapGenerator"、`0x81A978` = "CloakRadiusInCells"、`0x81A8CC` = "InvisibleInGame"、`0x843D50` = "SensorsSight"、`0x84336C` = "DisableVoxelCache"
- **xref/来源**：每条断言的来源文档与行号见各补丁块「证据」段与 §D 覆盖度自证表；函数入口级 xref 沿用来源文档（本流未重跑 xref，**未以本流名义声称 xref 复算**）。
- **不可字节断言者（已显式标注，不入 claims）**：`0x00B45188`（阴影投影矩阵表）、`0xA8ED6B`、`0xA8B230`、`0xABC87C/0xABC888`、`0x8A0E8C/0x8A0E98`、`0xB04A64/0xB04A70`、`0xAC167C/0xAC1688`、`0xA83D4C`、`0x87F7E8`、`0xA8ED84`、`0x8871E0`、`0x8A0394/0x8A03A0` —— 均落在 `.data` 未初始化区（`.bss` 语义），**文件内无数据**，故只能标 [待实测]。

### [3] 勘误（对既有文档/结论的更正，逐条给）

> 本流**不直接改任何既有文档**（写作用域限制），以下勘误**以补丁块/本条清单形式**交 Lead 处置。

| # | 目标文件:行号 | 改前原文（要点摘录） | 改后文本（定谳） | 理由 | 影响面 |
|:---:|:---|:---|:---|:---|:---|
| E1 | `docs/re/fx_draw_chain.md:446`（§6 H-FX13） | 「H-FX13 … 可在 `+0x184` 写 1（**注意**：该字段可能被 Update 读，**先只读验证**） | **中**：若 Update 也读 `+0x184` 则会影响逻辑 → 先查写点」 | 风险等级上调 **中 → 高（确定性）**；已逐条闭环 8 处读写：`+0x184` 是 `int DelayTimer`，同时门控 Draw（`0x422C70`）与 Update（`0x424386/0x424390/0x424393`），归零触发 `call 0x424CE0`（音效/初始逻辑），循环末 `0x4247E5` 消费 RNG（`0x65C7E0`）重挂延迟 ⇒ **禁止**用作剔除开关 | 反汇编定谳（本流 claims 复算） | **影响产品决策**（L5 剔除实现方案）；不波及其他文档 |
| E2 | `docs/re/fx_draw_chain.md:463-464`（§7 Q2） | 「`AnimClass IsFogged` 淡出公式与写点」标未闭环，并推测存在半透明淡出 | 原版**不存在任何非平凡渐变淡出公式**；只有布尔硬剔除（`0x422FF4` / `0x423026` → `0x4238A3`）与黑雾调色归零（`0x42362C`） | 反汇编定谳（S3 冲刺已给，本流收入 atlas §19.5b） | 三态迷雾「灰雾残影淡出」必须由绘制层自行实现（产品决策） |
| E3 | `docs/re/visibility_gap_spysat.md:151-158`（§2.1） | `SuperGapRadiusInCells` = `BuildingTypeClass+0x1707`；`TechnoType+0x5F0/+0x5F4` = 运行时半径 A/B | `+0x1707` = `CloakRadiusInCells`（默认 0x14）；`+0x5F0` = `SensorsSight`；`+0x5F4` = `DetectDisguiseRange`；裂缝半径在 `+0xCD1..+0xCD3` | 该文档自身 §9.1 ERR-3/ERR-5 已定谳；本流以字符串内容二次复核 | **影响产品决策**（施工偏移）；建议 Lead 决定是否在 §2.1 就地加订正注记 |
| E4 | `docs/re/visibility_gap_spysat.md:167-170`（§2.2） | BuildingClass 槽 317–320 = `CreateGap/DestroyGap` 族 | 槽 317–320 = Sensor/DisguiseSensor 盖印族（PerCell 四兄弟 `0x487150/0x487160/0x487170/0x487180`）；真正 CreateGap/DestroyGap = TechnoClass v[261]/v[262] `0x6FB170/0x6FB470`（表项 `0x7E42D0/0x7E42D4` **本流复算通过**） | 同文档 §9.1 ERR-1/ERR-2 + 本流字节复算 | **影响产品决策**（钩点选择） |
| E5 | `docs/re/ARCHITECTURE_ATLAS.md:1267-1280`（§7.6） | 只登记 3×6B NOP 改写方案，未记因果链与落地状态 | 追加：钳位截断机制（`0x4876BF`）⇒ 「永久」废缝 + 不自愈（`0x6FB180` 去重）+ 落地状态（`ra2render/**` 0 命中） | 本流 §20.4/§20.6 | **影响产品决策**（是否判为已闭环）；以 PATCH-R7-04 提交（可由 Lead 丢弃） |
| — | 其余既有文档 | — | — | — | **本流未发现其他需勘误项** |

### [4] 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证（可直接执行） | 级别 |
|:---:|:---|:---|:---|:---:|
| U1 | 3×6B NOP 落地与否 | 本流只读渲染 DLL 源码；不排除外部补丁器/加载器安装 | 真机断点读 `0x568273` 首字节：`89` = 未打、`90` = 已打；或查加载器安装清单 | **P0** |
| U2 | 各类 v[65] 表项归属（决定能否改用共享体钩） | 需逐类虚表扫描 + 调用点 xref，本流未跑 | dump 6 类 FX + Building/Unit/Infantry/Aircraft 的 `vtbl+0x104` 表项；统计 `0x5F4B10` 的 IMM 直呼数 | **P0** |
| U3 | `Cell+0x134` / `+0x130` / `+0x12C` 是否进 `.SAV` 与帧 CRC | 需复算存档块与校验链（本流来源未覆盖） | 对照 `docs/re/savegame_block_manifest.md` / `net_sync_checksum.md`；真机对拍存档差异 | **P1** |
| U4 | `Cell+0x7C` 与 `Cell+0xAC` 语义归属（gap 计数 vs 传感器数组） | 两代文档同址异名，需运行时对照 | 打日志跟踪同格两计数随裂缝开关/传感器上线变化 | **P1** |
| U5 | PsychicReveal 路线下的废缝是否可复现（现网未封） | 需真机 | 真机发射 PsychicReveal 后断点 `0x4876BF`，观察 `+0x134` 是否为 0 | **P1** |
| U6 | 光照核精确配对（`0x753F90/0x7542F0` vs `0x7540F0/0x754510`） | 两来源口径不一致 | 逐个 dump `0x706ED0/0x707280/0x749B70` 的 call 序列 | P2 |
| U7 | 同屏编队缓存 miss 率与 `qsort` 频次（无 LRU） | 需遥测 | 钩 `0x7107E0` 计数 | P2 |
| U8 | `RevealArea2/3`、`Reshroud` 是否还有第 4 处 `+0x134` 写入 | 本流只复核 3 处已知写点 | 三函数全函数扫描 `0x134` 立即数/寄存器写 | P1 |
| U9 | `0x6D97D0/0x6D9920` 触发时机与 `TacticalClass+0xD7D` 打脏链关系 | 需断点调用栈 | 断点两入口记录帧内调用序 | P2 |
| U10 | 非 Object 四件套容器地址不可字节断言 | 落在 `.data` 未初始化区 | 真机读 Items 指针；或以 DrawAll 内读取指令字节替代断言 | P2 |

### [5] 写作用域合规声明

**改动文件清单**（全部在授权作用域内；均为本流自建文件）：

| 路径 | 性质 |
|:---|:---|
| `docs/re/atlas_rev/R7_vxl_fx_gap.md` | 交付物 1（锚定补丁块 + 十节回执 + 覆盖度自证表） |
| `out/re_work/atlas_rev/R7/claims_R7.txt` | 交付物 2（445 条字节断言） |
| `out/re_work/atlas_rev/R7/gen_claims_r7.py` | 脚本（由二进制直读生成 claims） |
| `out/re_work/atlas_rev/R7/anchor_probe.py` | 脚本（锚点唯一性实跑） |
| `out/re_work/atlas_rev/R7/anchor_evidence.txt` | dump（锚点 grep 原文） |
| `out/re_work/atlas_rev/R7/gate_verify_anchors.txt` / `gate_audit_bytes.txt` | dump（门禁原文） |
| `out/re_work/atlas_rev/R7/parts/*.md` | 组装用中间件（同作用域） |

**未触碰清单（明确声明）**：`docs/re/ARCHITECTURE_ATLAS.md`（Lead 唯一写者）、其他 R# 流文件（`atlas_rev/R1_*`…）、`ra2render/**`（**只读引用**：本流仅 grep 读取 `blitter_hooks.cpp`，未改一字节）、`ra2youli/**`（**只读**）、`REVERSE_ENGINEERING_AND_PATCHES.md`、任何既有 `docs/re/*.md`。

**目标二进制只读证明**：`ra2youli/gamemd.exe` MD5 = `4F37486E5B0DBE2AE5F45AEEE0F98367`，大小 4,825,360 B；`tools/verify_anchors.py` 基线审计报 `.text` raw SHA-256 = `c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738`（与黄金常数一致）+ `.detour` 原生签名 `40 00 00 00 44 74 72 00` ⇒ 二进制未污染。**本流未启动游戏、未注入、未改二进制。**

### [6] 门禁实跑输出（原文粘贴）

**（1）`python tools\verify_anchors.py`** → 须 323/323 PASS（**实测通过**，原文）：

```text
===================================================================================================================
  RA2/YR 二进制决定性锚点自动化回归测试套件 (verify_anchors.py)
===================================================================================================================
目标文件 : D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe (大小: 4,825,360 字节, ImageBase: 0x400000)
断言文件 : D:\Project\ra2-campaign-forge\docs\re\anchor_claims.txt
反汇编器 : Capstone x86-32 引擎已就绪
-------------------------------------------------------------------------------------------------------------------
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
-------------------------------------------------------------------------------------------------------------------
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
===================================================================================================================
```

**（2）`python tools\audit_bytes.py out/re_work/atlas_rev/R7/claims_R7.txt`** → 须全部 OK（**实测通过**，原文节选；全文留档 `out/re_work/atlas_rev/R7/gate_audit_bytes.txt`）：

```text
 ec 74               OK     FlyLocomotionClass::Shadow_Matrix 覆写 | sub esp, 0x74 | sub esp, 0x74
0x5142a0   8b 54 24 04                8b 54 24 04            OK     HoverLocomotionClass::Shadow_Matrix 覆写 | mov edx, dword ptr [esp + 4] | mov edx, dword ptr [esp + 4]
0x69fb20   83 ec 34                   83 ec 34               OK     ShipLocomotionClass::Shadow_Matrix 覆写 | sub esp, 0x34 | sub esp, 0x34
0x492d20   8b 54 24 0c                8b 54 24 0c            OK     BlitTransDarkenZRead@G 入口 (载具/建筑阴影 Z 测试) | mov edx, dword ptr [esp + 0xc] | mov edx, dword ptr [esp + 0xc]
0x492670   8b 44 24 0c                8b 44 24 0c            OK     BlitTransDarken@G 入口 (非 Z Darken) | mov eax, dword ptr [esp + 0xc] | mov eax, dword ptr [esp + 0xc]
0x496250   8b 54 24 10                8b 54 24 10            OK     RLEBlitTransDarken@G 入口 (步兵影) | mov edx, dword ptr [esp + 0x10] | mov edx, dword ptr [esp + 0x10]
0x496820   51 8b                      51 8b                  OK     RLEBlitTransDarkenZRead@G 入口 (步兵影+Z) | push ecx | push ecx
0x7e5948   40 a0 49 00                40 a0 49 00            OK     虚表条目 ?$BlitTransDarkenZRead@G 指针 | inc eax
   …（中间 364 行逐条 OK，略）…
0x73d0e3   0f 84 af 01 00 00          0f 84 af 01 00 00      OK     ├─[阴影先行, 0x73D0E3] Loco v[10] Shadow_Matrix → 0x7559B0 表 0xB45188 → Darken Blit | je 0x73d298 | je 0x73d298
0x73d0e9   8a 86 d2 06 00 00          8a 86 d2 06 00 00      OK     - 阴影门：`Type.NoShadow(+0xE0E)`（`0x73D0DB`）与单位阴影开关 `Unit+0x6D2`（`0x73D0E9`）；Loco `v[0x80] Is | mov al, byte ptr [esi + 0x6d2] | mov al, byte ptr [esi + 0x6d2]
0x73d361   6a 00                      6a 00                  OK     0073D31F je 0x73d361 ; → DrawAsSHP 路径 74 40 | push 0 | push 0
0x7ef4e8   60 df                      60 df                  OK     | `OverlayClass` | — | `0x007EF4E8` | `0x005FDF60` = `C2 08 00`（**空桩 ret 8**） | — | **无需在槽 | pushal | pushal 
0x7f5d84   c0 ce 73                   c0 ce 73               OK     | **`UnitClass` v[69] Draw** | `+0x114` | `0x007F5D84` | **`0x0073CEC0`** | 载具绘制总入口（阴影段 +  | ror dh, 0x73 | ror dh, 0x73
--------------------------------------------------------------------------------------------------------------
合计 445 条：OK=445  MISMATCH/NOREAD=0
```

**（3）本流自建附加校验（非 Lead 门禁，供抽验提速）**：`out/re_work/atlas_rev/R7/va_cover.py` —— 把本文档内出现的全部 in-range VA 与 `claims_R7.txt` 做覆盖交叉：**376 个 VA token 中 366 个已有字节断言**；余 10 个（`0x400000` / `0x87F7E8` / `0x8871E0` / `0x887644` / `0x8A0360` / `0x8A0394` / `0x8A03A0` / `0x8A0E88` / `0x8A0E8C` / `0x8A0E98`）落在 `.data` 未初始化区（**文件内无数据**，物理上不可字节断言），已在 [2] 节显式登记。`0x00ABCxxx / 0x00B04xxx / 0x00AC1xxx` 已超出 `atlas_va_crosscheck.py` 的地址判定上界（`0x00A00000`），计入 noise 而非 dangling。

### [7] 风险与红线提示

| 维度 | 是否触及 | 说明 |
|:---|:---:|:---|
| ① 同步语义 / 命令序 | **触及** | §20 的 3×6B NOP（方案 A）改写 `RevealArea2/3/Reshroud` 对 `Cell+0x134` 的写入 ⇒ 改变引擎视野状态演进；`execution_runbook.md:56` 已明示该字段进入**存档与同步校验**。**必须走 MP 门控矩阵 + 真机对拍验收，严禁混端联机** |
| ② 随机数消费序 | **触及（条件性）** | 本流自身不改任何 RNG 路径；但 §19.5 证明 `AnimClass+0x184` 的重挂会消费 `0x65C7E0` ⇒ 若按旧稿 H-FX13 写该字段，将**间接改变 RNG 消费序**（联机 Desync 风险）。故结论是「**禁止**用该字段剔除」 |
| ③ 存档结构 | **触及（待复算）** | `CellClass+0x134/+0x130/+0x12C` 疑似进档（U3 未复算）；`TechnoTypeClass+0xDBE/+0xDBF` **已证实**进 `v[13]` 打包。方案 A 落地前必须完成 U3 |
| ④ 渲染像素等价性 | **触及（绘制层）** | §18/§19 的缓存/阴影/剔除建议全部落在绘制层：不改逻辑，但会改变像素输出 ⇒ 需截图级视觉验收（VXL 阴影「先影后体」不变量、遮挡关系、缝内可见性） |

**禁止宣称「零风险 / 零 Desync」**：本流仅做静态取证，所有落地项一律 **需 MP 门控矩阵 / 真机对拍验收**。

### [8] 交付物清单

| 类型 | 路径 | 规模 |
|:---|:---|:---|
| 文档 | `docs/re/atlas_rev/R7_vxl_fx_gap.md` | 见文末行数（含 4 个补丁块 + 十节回执 + 覆盖度自证表） |
| 断言 | `out/re_work/atlas_rev/R7/claims_R7.txt` | **445 条**（全部 OK） |
| 脚本 | `out/re_work/atlas_rev/R7/gen_claims_r7.py`、`anchor_probe.py` | 2 个 |
| dump | `out/re_work/atlas_rev/R7/anchor_evidence.txt`、`gate_verify_anchors.txt`、`gate_audit_bytes.txt` | 3 个 |
| 补丁块 | PATCH-R7-01（§18）/ -02（§19）/ -03（§20）/ -04（§7.6 补记） | 4 个 |

### [9] 待裁决项（需 Lead/人决定的分叉，附建议）

| # | 分叉 | 选项 | 建议 | 理由 |
|:---:|:---|:---|:---|:---|
| D1 | **FX 剔除落点：v[65] 共享体 vs 各 v[69]** | 甲：保持 atlas §2.5「只收口槽 69」；乙：采纳 `fx_draw_chain.md` H-FX1 / `vxl_render_sort.md` H-VXL1（钩 `0x5F4B10`，一处覆盖） | **甲**（§18.8/§19.7） | 乙案与 §2.5 明令冲突，且共享体并非「一处覆盖全部」（Unit/Anim/VoxelAnim 各自覆写或包装 v[65]），建筑需三态残影而非布尔剔除；若仍想翻案，先做 U2 取证 |
| D2 | **PATCH-R7-04（§7.6 补记）是否采纳** | 采纳 / 丢弃（若 R3 已占同位置） | 若 §7.6 位置空闲则**采纳**，否则丢弃 | 该块不承载独有事实（独有事实已在 §20），仅为可读性与危害定级补强 |
| D3 | **方案 A（3×6B NOP）联机门控口径** | ① 联机全员强制同值（`EnableGapProtection` 入握手）；② 仅单机/战役启用 | **①**（与 `landing_pack_gap_spysat.md` MP 覆盖口径一致） | `Cell+0x134` 进档 ⇒ 混端必 Desync；且需先完成 U3 |
| D4 | **PsychicReveal 产品语义** | ① 透缝扫描（私有 600 帧窗口，不写引擎 `+0x134`）；② 维持原版 RevealArea2（接受废缝） | **①** | ② 会使裂缝被永久阉割，破坏平衡（§20.5c/§20.7） |
| D5 | **是否把 §20.3 勘误表回写进 `visibility_gap_spysat.md` 正文** | ① 就地加订正注记；② 仅保留其 §9 定谳，靠 atlas §20 收口 | **②**（由 atlas 收口） | 该文档 §9.1 已自证勘误；就地改写会增加多写者冲突面（该文件非本流作用域） |
| D6 | **§2.4 三态迷雾与裂缝规则的关系表述** | ① 在 §2.4 补一句前置条件；② 仅由 §20 承载 | **①**（Lead 落 §2.4 时顺带一行） | 「缝内不可见」是三态定义的前置条件，否则 §2.4 与 §20 语义冲突（本流未提交该块以避免与其他流冲突） |

---

## D. 覆盖度自证表（来源文档 §小节 → 命中补丁块）

> 口径：本流**逐份全文阅读** 6 份来源文档；下表按「来源小节」逐一列出落点。标「不入 atlas」者给出理由。

| 来源文档 | 来源小节 | 落点 |
|:---|:---|:---|
| `docs/re/vxl_render_sort.md` | §0 结论速览（12 问） | PATCH-R7-01 §18.1/18.2/18.3/18.4/18.5/18.6/18.8 |
| | §1.1 VXL/HVA 资源、§1.2 矩阵、§1.3 BlitterFlags | §18.1/18.4/18.5/18.6 |
| | §2.1 总链、§2.2 UnitClass::Draw、§2.3 DrawAsVXL、§2.4 Draw_A_VXL 三层、§2.5 VoxelAnim 对照 | §18.1/18.2（+ §19.2 交叉） |
| | §3.1 缓存结构、§3.2 键与失效、§3.3 HVA 帧 | §18.3/18.4 |
| | §4.1 Blit 族关系、§4.2 VXL 阴影链、§4.3 顺序不变量 | §18.5（I-VXL-1） |
| | §5.1–5.4 Z 序两层模型 / ZGradient / ZBuffer / 乱序推演 | §18.6（I-VXL-2） |
| | §6.1 成本对比、§6.2 可缓存/限频点、§6.3 迷雾 | §18.3（性能契约）/§18.8/§18.9 |
| | §7 Hook 点表（H-VXL1..16） | §18.9（含 H-VXL1 的 D1 裁决） |
| | §8 未决 Q1–Q8 | §18.10（Q6/Q7 标「已闭环」） |
| | §9 取证索引（脚本/输出路径） | **不入 atlas**（工程索引，非架构事实） |
| | §10 与既有 Hook 衔接 | §18.9 / §19.7 |
| `docs/re/vxl_cache_layout.md` | 一、Q1–Q8 总表 | §18.3–18.7 |
| | 二 Q1 结构/扩容、Q2 INI 门控、Q3 Z 梯度表 | §18.3 / §18.3 表 / §18.6 表（**整表字节复算**） |
| | Q4 部件划分与矩阵、Q5 阴影键与表 | §18.2（+ §18.10 Q2 记口径冲突）/§18.4（阴影键不含 Z 桶） |
| | Q6 +0x6D3、Q7 跨高程 Z 梯度、Q8 命中/Miss | §18.7 / §18.6 / §18.3 |
| | 三、工程落地与 Hook 建议 | §18.9（明确标「仅纸面规格」） |
| | 四、取证原始文件索引 | **不入 atlas**（索引） |
| `docs/re/fx_draw_chain.md` | §0 结论速览 | §19.1/19.2/19.3/19.7 |
| | §1.1 虚表槽位与 DrawIfVisible 内部链、§1.2 各类 Draw 入口、§1.3 每帧调用来源、§1.4 全局数组 | §19.2/19.7 / §19.2 / §19.1 / §19.3 |
| | §2.1–2.6 逐类门控（Bullet/Anim/Particle/PSys/Wave/VoxelAnim） | §19.2（雾门全废因果链）/§19.4/§19.5 |
| | §3.1–3.5 LaserDraw/EBolt/RadBeam/Spotlight/清空时机 | §19.3（T-FX-1） |
| | §4.1 Update/Draw 分离、§4.2 成本中心、§4.3 与 Blit 关系 | §19.4 / §19.8 / §19.6 |
| | §5.1–5.3 迷雾判定谓词与分类表、与 gap 的合并 | §19.2 / §20.1（C-20-1） |
| | §6 Hook 点表（H-FX1..15） | §19.7（H-FX1 裁决）+ [3] E1（H-FX13 风险上调） |
| | §7 未决 Q1–Q7 | §19.10（Q1 升级为 P0；Q2/Q3 勘误定谳） |
| | §8 取证索引 | **不入 atlas**（索引） |
| | §9 与 L3 代码衔接 | §19.7 |
| | §10 S3 冲刺勘误（Q1–Q7 定谳） | §19.5（DelayTimer / IsFogged）、§19.1（0x8A0394 归属、双重路径=脏矩形而非小地图） |
| `docs/re/bullet_particle_fog_deep_dive.md` | §1.1 弹药/微粒渲染链架构 | §19.1/19.2 |
| | §1.2 视觉泄露三缺陷（**核心**） | §19.2（含恒假桩字节复算） |
| | §2.1 Bullet Draw 全剖析、§2.2 lepton→cell、§2.3 Owner 寻址树、§2.4 抛物线字段 | §19.2 / §20.1（cell idx = Y*512+X）/ §19.2 表 / §20.8 Q（字段未全量入册，仅取归属相关项） |
| | §3.1 ParticleClass::Draw、§3.2 ParticleSystemClass::Draw | §19.2/19.3 / §19.4（只画 Spotlight） |
| | §4.1–4.3 剔除 Hook 与红线、代码原型 | §19.7/19.9（红线）；**代码原型不入 atlas**（属实现，非架构） |
| | §5.1–5.2 地址与字段速查 | §19.11（速查表）+ §11 待并入底稿 |
| `docs/re/gap_generator_spysat_deep_dive.md` | §1 总体调用拓扑 | §20.2/§20.5 |
| | §2.1 INI 字段布局 + 历史文献勘误（+0x1707） | §20.2/§20.3（E3） |
| | §2.2 七级门控、§2.3 CreateGap/DestroyGap、§2.4 CellClass 字段 + ReshroudCell 截断 | §20.2 / §20.2/20.4 / §20.4（I-GAP-1） |
| | §3.1 超武 12 路跳表、§3.2 PsychicReveal 链、§3.3 根因溯源、§3.4 UpdateSpySat | §20.5b（**逐项复算**）/§20.5c / §20.4 / §20.5a |
| | §4.1 三态视野矩阵、§4.2 雷达开窗算法、§4.3 NOP 补丁表 | §20.1（C-20-1）/§20.7（H-20-C）/§20.4+§20.6 |
| | §5 C++ Hook 原型 | §20.7（纸面规格）；**原型代码不入 atlas** |
| | §6 最终实证结论汇总（5 条） | §20.2/20.4/20.5/20.7 全覆盖 |
| `docs/re/visibility_gap_spysat.md` | §0 结论速览 | §20.1/20.2/20.5 |
| | §1.1–1.4 Building/Bullet Draw 短路、门控链、字段速查 | §19.2/§20.1（含 `Type+0x1701` 门 2 = InvisibleInGame） |
| | §2.1 类型字段、§2.2 每帧函数（317–320）、§2.3 与 Shroud/Fog 关系、§2.4 反制 | §20.3（E3/E4）/§20.2/§20.1（C-20-1）/§20.7 |
| | §3.1 超武跳表、§3.2 SWType 字段、§3.3 激活写入、§3.4 PatchSpySat 对应、§3.5 冲突三方案 | §20.5 / §20.6（`+0x16A5/+0x16F0/+0xB0/+0xF8`）/§20.5c / §20.6 / §20.7（D4） |
| | §4.1 谁在画（槽 69 表）、§4.2 有无统一门、§4.3 统一策略 | §19.2 / §19.7 / §20.1 |
| | §5 Hook 点表 H1–H13 + 红线 | §19.7 / §20.7 |
| | §6 与 L3 代码衔接 | §20.1 / §20.3（遗留语义分歧 → U4） |
| | §7 未决 Q1–Q8 | §20.8（由该文档 §9.4 闭环者标「已闭环」） |
| | §8 取证索引 | **不入 atlas**（索引） |
| | §9.1 勘误 ERR-1…ERR-7（**核心**） | §20.3 全表（含本流二次复算标注） |
| | §9.2 五类对象 Draw 定谳表 | §19.2 |
| | §9.3 方案 A/B/C 对比与裁决 | §20.6/§20.7 |
| | §9.4 11 条未决全面闭环 | §20.5/§20.8 |

---

*本文件由 R7 流（atlas-r7-vxl-fx）产出，供 Lead 机械套用；套用后请由 Lead 亲跑门禁并做抽验（本流门禁见 [6] 节）。*
