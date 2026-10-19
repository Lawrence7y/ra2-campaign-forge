# VXL 缓存 / 阴影绘制 —— 可落地规格（R-VXL-CACHE）

> **卡号**：`R-VXL-CACHE` · **性质**：静态逆向落地规格（不是再证明缓存存在）  
> **目标文件**：`gamemd.exe` 1.001 · SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` · MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000` · `file_off = VA − 0x00400000`  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **上游**：`docs/re/vxl_cache_layout.md`（Q1–Q8 布局结论）· `docs/re/vxl_render_sort.md`（绘制链/Hook 表）  
> **取证**：`out/re_work/re_sprint/R_vxl_cache/`（字节报告 + 链/xref 报告，全静态，已 MATCH）  
> **证据档**：**[实证]** = Capstone 反汇编 + 硬字节（本 sprint 产出）；**[ABI]** = 既有文档/YRpp 交叉；**[推演]** = 由调用关系推出的落地语义。  
> **红线**：只拦绘制 / 只改 `.text` 等长字节；不写逻辑状态、不改 Z 语义、不动 `ra2render/**`。

---

## 0. 一句话

VXL 缓存是 `ObjectTypeClass.VoxelCaches[4]` 上的 **Key→Data 排序数组 + MRU**；阴影有 **两条互不相同的链**（SHP 影 vs VXL 炮塔影），前者可直接等长字节剔除、后者已带缓存。Top3 落地点：**缓存预热扩容**、**SHP 影强制跳过**、**VXL 影缓存强制启用**；收益只给插桩口径，不给百分比。

---

## 1. VXL 缓存结构 ABI（条目 / 失效 / 命中 / VA 锚点）

### 1.1 宿主与条目 [实证 + ABI]

```cpp
// ObjectTypeClass（宿主是 Type 不是实例 —— 同型号共享）
// +0x258  SomeVoxelCache VoxelCaches[0]  主车体
// +0x26C  SomeVoxelCache VoxelCaches[1]  主车体阴影/变体
// +0x280  SomeVoxelCache VoxelCaches[2]  炮塔
// +0x294  SomeVoxelCache VoxelCaches[3]  炮管/充能炮塔
// stride 0x14，四元组合计 0x50

struct SomeVoxelCache {          // sizeof 0x14
    VoxelCacheEntry* Buffer;     // +0x00  条目数组（operator new[] @ 0x7C8E17）
    int32_t          Count;      // +0x04  有效条目数
    int32_t          Capacity;   // +0x08  已分配容量（条目数）
    uint8_t          IsSorted;   // +0x0C  1=可二分；0=脏，下次 Find 先 qsort
    uint8_t          Pad[3];
    VoxelCacheEntry* LastFoundEntry; // +0x10  MRU（L1 探测）
};

struct VoxelCacheEntry {         // sizeof 8
    uint32_t Key;                // +0x00  复合渲染键
    void*    Data;               // +0x04  预渲染矩阵/光栅结果
};
```

### 1.2 键格式 [实证]

| 用途 | 键构造 | VA |
|---|---|---|
| 车体/炮塔 VXL | `(Z阶梯<<5) \| (facing&0x1F)`，`Type+0x720==0` 时清 Z 桶（`and esi, 0xFFFFFC1F`）；再 OR HVA 帧相关字节 | `0x0073B74C`–`0x0073B79F` |
| 阴影 | `(((ShadowIndex<<6) + SlopeFacing) << 5) \| (Facing&0x1F)` —— **绝不含 Z 桶** | `0x0055A86D`–`0x0055A8A0` |

> 阴影键剥离 Z 的原因：阴影形态只取决于朝向 + 地表坡度 + 阴影模型索引，与绝对高程无关 → 同坡度多单位高命中。

### 1.3 命中路径（两级）

```
DrawAsVXL 0x73B470
  ├─ L1  SomeVoxelCache::IsCached  0x746EA0     // LastFoundEntry->Key == *key ?
  │      调用点: 0x73B970（车体） / 0x73B9D9（炮塔）
  ├─ L2  SomeVoxelCache::Find      0x7107E0     // IsSorted? qsort(0x7C8B48, cmp 0x710860) : 直接二分 0x710890
  │      调用点: 0x73B980 / 0x73B9E9（DrawAsVXL） / 0x70682F（Draw_A_VXL 核）
  └─ 命中: Entry.Data(+4) → 0x707480 直接 Blit，跳过矩阵重算与体素光栅
     未命中: 矩阵合成 0x5AE980/0x5AF1A0 → 光栅 → 插入缓存
```

**L1 快路径**（`0x746EA0`，16 字节）：`LastFoundEntry` 非空且 Key 相等 → `AL=1`，不碰排序数组。  
**L2 二分**（`0x7107E0`）：`Count==0` 直接 Miss；`IsSorted==0` 则 `qsort`（比较器 `0x710860` 按 Key 有符号比较）后清 `LastFoundEntry`、置 `IsSorted=1`，再二分。

### 1.4 插入 / 扩容 / 失效 [实证]

| 事件 | VA | 语义 |
|---|---|---|
| 插入判定 | `0x00706D65` | `Count+1 > Capacity` → 扩容 |
| 初始容量 | `0x00706D78` | `mov ebx, 0xa`（**10 项**，覆盖不住 32 朝向×帧） |
| 扩容步长 | `0x00706D7F` | `mov ebx, eax`（增量=当前容量，翻倍）；`lea edx,[edi*8]`；`call operator new[] 0x7C8E17` |
| 拷贝旧项 | `0x00706DB0`–`0x00706DD0` | 逐项拷 Key/Data |
| 换 Buffer 后 | `0x00706DF1` | `LastFoundEntry = 0` |
| 追加写入 | `0x00706E02`/`0x00706E0B` | `Buffer[Count].Key/Data = …` |
| **失效（排序脏）** | `0x00706E13` | `IsSorted = 0`（**任何插入都打脏**，下次 Find 付一次 qsort） |
| Count 递增 | `0x00706E17` | `Count++` |

**无 LRU / 无淘汰**：条目只增不减（直到 Type 析构）。同型号静止同朝向 N 辆车共享 1 条；旋转/换帧键变 → 必 Miss 并插入。

### 1.5 渲染门控（必须尊重）[实证]

| 字段 | INI | 解析写入 | 渲染读取 | 语义 |
|---|---|---|---|---|
| `TechnoTypeClass+0xDBE` | `DisableVoxelCache` @ `0x84336C` | `0x0071596C` | `0x00706806`（`test cl,cl; jne 0x706875`） | !=0 → **完全跳过缓存**，强制软件光栅 |
| `TechnoTypeClass+0xDBF` | `DisableShadowCache` @ `0x843358` | `0x007159A6` | `0x00706C33`（`test cl,cl; jne 0x706ce1`） | !=0 → **跳过阴影缓存查找** |

构造初值均为 0（`0x711658` / `0x71165E`）。存档打包读点 `0x717767`/`0x717775`（v[13]）。

---

## 2. 阴影绘制链（降采样 / 缓存 / 剔除）

**关键结论：存在两条互不相同的阴影链，落地点不能混用。**

### 2.1 链 A —— SHP 单位影（`UnitClass::Draw` 内，**先影后体**）

```
UnitClass::Draw 0x73CEC0
  └─ 0x73D0DB  Type+0xE0E ?        ; 非 0 才继续（字段实为"有影/画影"极性）
       └─ 0x73D0E9  Unit+0x6D2 ?   ; 单位影开关
            └─ 0x73D114  Loco v[0x80] Is_To_Have_Shadow
                 └─ AL != 0 → 跳过（0x73D11C jne 0x73D298）
            └─ 朝向/坐标变换 0x4C93D0 / 0x6D2140 …
            └─ 0x73D251  push 0x2A00   ; Flat|Alpha|0x200
            └─ 0x73D283  call 0x4AED70 ; 通用形状/SHP 绘制（全二进制 60+ 调用点）
  └─ 0x73D359  call v[341] DrawAsVXL 0x73B470   ; 主体在后
```

| 问题 | 结论 | 证据 |
|---|---|---|
| 可缓存？ | **否**（链 A 不走 `SomeVoxelCache`；`0x4AED70` 是通用 SHP 绘制） | [实证] xref `0x4AED70` 60 调用点，无缓存参数 |
| 可剔除？ | **是**，三道现成门 + 可等长字节强制跳过 | [实证] 三处 jcc 原字节 |
| 可降采样？ | **否**（SHP 影已是 8-bit 预渲染形状，无光栅核可降） | [实证] 路径不含 `0x707480` |
| 顺序不变量 | **先影后体**；Darken/Alpha 压暗已有像素，颠倒必坏 | [ABI] `vxl_render_sort.md §4.3` |

**强制跳过落地（L-VXL-2）**：`0x73D0E3` 的 `0F 84 AF 01 00 00`（`je 0x73D298`）→ `E9 AF 01 00 00 90`（`jmp` 同目标 + nop）等长 6B，无条件跳过整段 SHP 影。

### 2.2 链 B —— VXL 炮塔影（`Draw_A_VXL_Turret` → `0x706BD0`，**带缓存**）

```
FootClass::Draw_A_VXL_Turret 0x4DB0D0
  └─ Loco v[0x20] == 1 才继续（0x4DB0FB）
  └─ Loco v[0x30] Shadow_Point（0x4DB13E）
  └─ call 0x706BD0          ; 调用点仅 2 处: 0x4DB190 / 0x706EBF
       ├─ Type+0xD98 门（0x706BF3）
       ├─ 0x706C33  DisableShadowCache（Type+0xDBF）
       │    !=0 → 0x706CE1 跳过缓存
       ├─ 内联 L1+qsort+bsearch（0x706C41–0x706C91，结构同 SomeVoxelCache）
       │    命中 → Entry.Data → 0x707480  flags=0x2001 (Flat|Darken)
       │    未命中 → 0x706CED 走光栅回填
       └─ 阴影矩阵表 0xB45188（32 向×48B，生成器 0x754CB0，查询 0x7559B0）
```

| 问题 | 结论 | 证据 |
|---|---|---|
| 可缓存？ | **已经缓存**（`SomeVoxelCache` 语义；`DisableShadowCache` 可关） | [实证] `0x706C20` 窗口 |
| 可剔除？ | **是**（`Type+0xD98` / `DisableShadowCache` / 迷雾短路在 `DrawIfVisible`） | [实证] |
| 可降采样？ | **仅**经 `0x707480` 光栅核改分辨率 —— **高风险**，不作首选 | [推演] 全部 VXL/影 Blit 收束于此（xref 仅 2 处 call：`0x706866` 车体 / `0x706CC0` 影） |

### 2.3 降采样总判

| 手段 | 可行性 | 落点 | 风险 |
|---|---|---|---|
| SHP 影降采样 | 不可行（无光栅核） | — | — |
| VXL 影/体素降采样 | 可行但**动 `0x707480`** | 光核入口 `0x707480`（`83 EC 50 53 55 56…`） | **高**：改跨步/尺寸牵动 ZBuffer 写与包围盒，遮挡可能坏 |
| 影距离剔除 | 可行 | 链 A 的 jcc / 链 B 的门 | 中（视觉上远景无影） |
| 影缓存 | **已有**；扩容同 L-VXL-1 | `0x706D78` | 低 |

---

## 3. 落地点表（改哪里 / 原字节 / 开关 / 回滚 / 风险）

> 全部 **等长字节替换**，禁 trampoline、禁动 `.detour`。安装前校验 SHA-256 与原字节。

### 3.1 L-VXL-1 缓存初始扩容（P1，首选）

| 项 | 值 |
|---|---|
| **ID** | `L-VXL-1` |
| **VA / off** | `0x00706D78` / `0x00306D78` |
| **函数** | 缓存 Miss 插入扩容（`Draw_A_VXL` 核 `0x706640` 内） |
| **原字节（5B）** | `BB 0A 00 00 00` |
| **原指令** | `mov ebx, 0xa`（初始容量 = 10） |
| **新字节（5B）** | `BB 40 00 00 00` |
| **新指令** | `mov ebx, 0x40`（初始容量 = 64 ≈ 32 朝向 × 2 帧） |
| **语义** | 只改**首次**分配粒度；扩容步长（翻倍）与插入逻辑不动 |
| **开关键** | `EnableVxlCachePrewarm`（`[Render]`，默认 `0`=不装） |
| **回滚** | 软：键置 0 + 重启；硬：还原 `BB 0A 00 00 00` |
| **风险** | **低**。每 Type 每缓存多占 `54×8=432B`（4 缓存 ≈ 1.7KB/Type）；不影响命中语义与渲染正确性 |
| **邻接约束** | `0x706D7D` 为 `EB 0A`（jmp 跳过 growstep）；`0x706D7F` 为 `8B D8`（growstep）—— **只许动 `0x0A→0x40` 一字节**，禁改 EB/8B |

### 3.2 L-VXL-2 SHP 单位影强制跳过（P1）

| 项 | 值 |
|---|---|
| **ID** | `L-VXL-2` |
| **VA / off** | `0x0073D0E3` / `0x0033D0E3` |
| **函数** | `UnitClass::Draw` `0x0073CEC0` 阴影段 |
| **原字节（6B）** | `0F 84 AF 01 00 00` |
| **原指令** | `je 0x73D298`（`Type+0xE0E==0` 时跳过影） |
| **新字节（6B）** | `E9 AF 01 00 00 90` |
| **新指令** | `jmp 0x73D298` + `nop`（**无条件跳过 SHP 影**） |
| **语义** | 链 A 整段不画；链 B（VXL 炮塔影）与主体 `DrawAsVXL` **不受影响** |
| **开关键** | `EnableVxlShadowSkip`（`[Render]`，默认 `0`） |
| **回滚** | 软：键置 0 + 重启；硬：还原 `0F 84 AF 01 00 00` |
| **风险** | **中**（渲染正确性观感）：单位脚下影消失/变浅，属可见表现变化；不改像素 Z、不改逻辑、不改存档。联机需全端一致（纯绘制，无 DESYNC，但观感分叉） |
| **邻接约束** | `0x73D0DB`=`8A 82 0E 0E 00 00`（读 Type+0xE0E）；`0x73D0E9` 起为 `Unit+0x6D2` 门 —— **不得动**；只改 6B jcc→jmp |

**备选（更保守）**：改 `0x73D0F1`（`0F 84 A1 01 00 00` → `E9 A1 01 00 00 90`）只跳 `Unit+0x6D2` 门之后的影，保留其它门；或改 `0x73D11C`（`0F 85 76 01 00 00` → `E9 76 01 00 00 90`）强制 `Is_To_Have_Shadow` 判否。三者互斥，默认只装 L-VXL-2。

### 3.3 L-VXL-3 VXL 影缓存强制启用（P2）

| 项 | 值 |
|---|---|
| **ID** | `L-VXL-3` |
| **VA / off** | `0x00706C3B` / `0x00306C3B` |
| **函数** | `0x00706BD0` 影缓存门（`DisableShadowCache`） |
| **原字节（6B）** | `0F 85 A0 00 00 00` |
| **原指令** | `jne 0x706CE1`（`Type+0xDBF != 0` 时跳过缓存） |
| **新字节（6B）** | `90 90 90 90 90 90` |
| **新指令** | `nop ×6`（**永不跳过缓存**，强制走缓存查找） |
| **语义** | 忽略 per-Type `DisableShadowCache`；命中直接 `0x707480` flags `0x2001` |
| **开关键** | `EnableVxlShadowCacheForce`（`[Render]`，默认 `0`） |
| **回滚** | 软：键置 0 + 重启；硬：还原 `0F 85 A0 00 00 00` |
| **风险** | **中低**。破坏原版对个别特殊单位的「禁影缓存」语义（若某单位影缓存会花屏/错色则被此键放大）；渲染正确性回归点=花屏/影错位 |
| **约束** | **不得**同时用本键去「修」已知 `DisableShadowCache=yes` 的单位；发现异常先关本键再关 `EnableVxlCachePrewarm` 归因 |

### 3.4 其它锚点（不单独开键，供对照/插桩）

| ID | VA | 原字节 | 用途 |
|---|---|---|---|
| A-CACHE-FIND | `0x007107E0` | `56 8B F1 8B 46 04 …` | L2 入口；插桩计数 |
| A-CACHE-QSORT | `0x00710800` | `E8 43 83 0B 00` | qsort 调用；计数=排序脏频率 |
| A-CACHE-L1 | `0x00746EA0` | `8B 41 10 85 C0 …` | L1 探测；命中率 |
| A-CACHE-INSERT | `0x00706E13` | `C6 45 0C 00` | 插入置脏；扩容计数看 `0x706D78` |
| A-RASTER | `0x00707480` | `83 EC 50 53 55 56 …` | 光栅核；调用次数=Miss 数 |
| A-SHDW-FLAGS | `0x00706CB6` | `68 01 20 00 00` | 影 Blit flags `0x2001` |
| A-DISABLE-VXL | `0x0070680E` | `75 65` | DisableVoxelCache 门（尊重，勿 NOP） |
| A-DISABLE-SHDW | `0x00706C3B` | `0F 85 A0 00 00 00` | DisableShadowCache 门（L-VXL-3 作用点） |

---

## 4. 预期收益 —— 可测口径（**只给插桩点，不写百分比**）

> 旧性能 ROI 作废。以下为**插桩规格**：在下列 VA 处挂只读计数器（或日志采样），用同场景 A/B（键开/关）对比。**禁止**在热路径做字符串/分配。

| 计数器 | 插桩 VA | 语义 | 与落地点关系 |
|---|---|---|---|
| `vxlCacheL1Hits` | `0x746EA0` 返回 `AL=1` 前 | MRU 命中 | L-VXL-1 后应上升（更少扩容/排序） |
| `vxlCacheFindCalls` | `0x7107E0` 入口 | L2 查询次数 | 分母 |
| `vxlCacheFindHits` | `0x7107E0` 命中返回 `0x710851` | 二分命中 | 命中率=Hits/FindCalls |
| `vxlCacheQsortCalls` | `0x710800` 前 | 排序脏触发次数 | L-VXL-1 后应下降（少插入） |
| `vxlCacheInserts` | `0x706E17` 前 | 新条目写入 | Miss 率另一口径 |
| `vxlCacheGrowths` | `0x706D94`（`call new[]`）前 | 扩容次数 | L-VXL-1 直接作用点 |
| `vxlRasterCalls` | `0x707480` 入口 | 软件光栅次数 | ≈ 缓存 Miss + 禁缓存单位 |
| `vxlShadowSHPDraws` | `0x73D283`（`call 0x4AED70`）前 | SHP 影绘制次数 | L-VXL-2 后应为 0 |
| `vxlShadowVxlCacheHits` | `0x706CC0` 前 | VXL 影缓存命中 Blit | L-VXL-3 后应上升 |
| `vxlShadowVxlCacheMiss` | `0x706CED` | VXL 影缓存 Miss | 对照 |
| `frameTimeMs` / `drawCallsPerFrame` | 既有帧循环遥测 | 总帧时间 / Draw 调用数 | 综合口径；与既有 `totalBlitCalls` 同源比对 |

**采样协议（建议）**：
1. 同地图、同镜头、同单位编成（推荐 ≥24 辆同型号静止 + 8 辆旋转）；
2. 采样窗口 ≥300 帧，丢弃首 60 帧；
3. 记录上表计数器增量 + 帧时间分布（p50/p95）；
4. 键开/关各跑一遍，**只报告差值方向与调用次数**，不报告百分比承诺。

---

## 5. 安装门禁与回滚

| # | 检查 | 期望 | 失败则 |
|---|---|---|---|
| G0.1 | SHA-256 | `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476` | 拒绝安装 |
| G0.2 | 各点原字节 | 见 §3 表 | 已是新字节→报告「已打」；其它→拒绝 |
| G0.3 | 等长 | 5==5 / 6==6 | 拒绝（禁 trampoline） |
| G0.4 | 开关键 | 显式 `1` 才装 | 默认全 `0`=零行为变化 |
| G0.5 | 联机 | `MpActive` 时 L-VXL-2 强制不装（观感一致要求）；L-VXL-1/3 可装（不进存档） | — |

**回滚矩阵**：
- 软：对应键置 `0` + 重启（安装态 init 读一次）；
- 硬：备份原字节 → `memcpy` 还原（`L-VXL-1: BB 0A 00 00 00` / `L-VXL-2: 0F 84 AF 01 00 00` / `L-VXL-3: 0F 85 A0 00 00 00`）。

---

## 6. 风险总表（对渲染正确性）

| ID | 风险 | 落地点 | 缓解 |
|---|---|---|---|
| R-1 | 单位脚下影消失（可见表现） | L-VXL-2 | 键默认 0；验收截图对比；联机不装 |
| R-2 | 特殊单位影缓存花屏/错色 | L-VXL-3 | 尊重 `DisableShadowCache` 的单位清单；异常先关本键 |
| R-3 | 扩容内存增量 | L-VXL-1 | 仅初始 64，不改翻倍步长 |
| R-4 | 动 Z/光栅核导致遮挡错误 | （降采样未落地） | **本规格不落地 0x707480 改动** |
| R-5 | 先影后体顺序 | — | 不改 `UnitClass::Draw` 内顺序；L-VXL-2 是「跳过」不是「移到后面」 |
| R-6 | 邻接 flags | 全部 | 只许等长 jcc→jmp 或 imm8/imm32 数值替换；禁改 `cmp/test` 前导 |

---

## 7. 交付回执（执行方填）

| 项 | 值 |
|---|---|
| 安装点 | （ ）L-VXL-1 （ ）L-VXL-2 （ ）L-VXL-3 |
| 安装前 SHA-256 | |
| 安装后首字节 | |
| 开关键实际值 | |
| 计数器采样文件 | |
| 验收结论 | |

---

## 8. 取证索引

| 产物 | 路径 |
|---|---|
| 字节/PE/落地点报告 | `out/re_work/re_sprint/R_vxl_cache/vxl_cache_bytes_report.txt`（mismatches=0） |
| 链/xref/门字节报告 | `out/re_work/re_sprint/R_vxl_cache/vxl_cache_chain_report.txt` |
| 复算脚本 | `out/re_work/re_sprint/R_vxl_cache/verify_vxl_cache_bytes.py` · `verify_vxl_cache_chain.py` |
| 上游布局 | `docs/re/vxl_cache_layout.md`（Q1–Q8） |
| 上游绘制链 | `docs/re/vxl_render_sort.md`（Hook 表 H-VXL*） |
| 既有缓存取证 | `out/re_work/vxl_cache/`（q1–q8 系列） |
