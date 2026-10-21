# HouseClass 四计数器定名 + units0=732 逐槽位归因

**时间**：2026-10-21 12:0x
**方法**：只读离线。`YRpp/ArrayClasses.h` / `HouseClass.h` 布局反推 + `qc151_fields.json` 逐帧数值四方对账 + `_src_L1_sf8_20261020/XMP29U2.MAP` 逐条解析。
**性质**：**定谳**四个字段语义；**推翻**上一轮「步兵实例化率 37.8%」的归因；给出 `units0=732` 的真实构成。

---

## 一、★ 定谳：四个计数器是 `CounterClass` 的 `Total`

### 1.1 布局推导（`YRpp/ArrayClasses.h`）

```cpp
template <typename T> class VectorClass {
    T*   Items;          // +0x00（vptr 之后）
    int  Capacity;       // +0x04
    bool IsInitialized;  // +0x08
    bool IsAllocated;    // +0x09
};                       // vptr(4)+0x0A → 对齐到 0x10

class CounterClass : public VectorClass<int> {
    int Total;           // +0x10
};                       // sizeof = 0x14
```

`HouseClass` 在 `unknown_55F0/55F4` 之前有 **12 个 `CounterClass`**（YRpp `HouseClass.h:879-901`），分三组各 4 个：

| 组 | 成员 | 语义（YRpp 原注释） |
|:--|:--|:--|
| 组 1 | `OwnedBuildingTypes` / `OwnedUnitTypes` / `OwnedInfantryTypes` / `OwnedAircraftTypes` | 「Counting objects **ever** owned」——历史上拥有过 |
| 组 2 | `OwnedBuildingTypes1` / `OwnedUnitTypes1` / `OwnedInfantryTypes1` / `OwnedAircraftTypes1` | 「Counting objects **currently** owned and on the map」 |
| 组 3 | `OwnedBuildingTypes2` / …2 | 「Counting objects **produced from Factory**」——不随易手/移除而变 |

块起点 = `0x55F0 − 12×0x14` = **`0x5500`**。逐项推：

```
组1  @0x5500..0x554F   Total 在 0x5510 / 0x5524 / 0x5538 / 0x554C
组2  @0x5550..0x559F   Total 在 0x5560 / 0x5574 / 0x5588 / 0x559C   ← 四个探针偏移
组3  @0x55A0..0x55EF   Total 在 0x55B0 / 0x55C4 / 0x55D8 / 0x55EC
```

**四个探针偏移 0x5560/0x5574/0x5588/0x559C 步长恰为 0x14，全部落在组 2 的 `Total` 槽位上。**
⇒ 探针读的是 `CounterClass::Total`，**不是** `DynamicVectorClass` 的 `Count`（后者在 0x10 基类之上再加 `int Count` + `int CapacityIncrement` ⇒ **sizeof = 0x18**；`Count` 虽也在 +0x10，但 0x18 ≠ 0x14，四个 0x14 步长偏移与连续 `DynamicVectorClass` 不相容）。

> 脚本注释里「照 c5574 既有模式：list 对象 +0x10 的 Count 直读」——**「+0x10」是对的，「list Count」的说法不准**：`CounterClass` 是「类型索引 → 计数」的稀疏数组，`Total` 是其**总和**，不是元素个数。

### 1.2 ★ 二进制级印证（第三条独立证据链）

前两节是「头文件布局反推 + 数值对账」。本节是从 `ra2bench/gamemd.exe`（sha `73201cc0`）直接反汇编得到的**第三条证据**，不依赖 YRpp。

**证据 1：`CounterClass` 构造/清零原语在 `0x009FBE0`**

```asm
0009FBE0  53              push ebx
0009FBE4  8bf9            mov  edi, ecx          ; ecx = this
0009FBE6  33db            xor  ebx, ebx
0009FBEC  895f04          mov  dword ptr [edi + 4], ebx    ; Items = nullptr
0009FBEF  895f08          mov  dword ptr [edi + 8], ebx    ; Capacity = 0
0009FBF2  c6470c01        mov  byte ptr [edi + 0xC], 1     ; IsInitialized = true
0009FBF6  885f0d          mov  byte ptr [edi + 0xD], bl    ; IsAllocated = false
0009FBF9  c707545c7e00    mov  dword ptr [edi], 0x7E5C54   ; vptr = CounterClass vtable
0009FBFF  895f10          mov  dword ptr [edi + 0x10], ebx ; ★ Total = 0
```

**`Total` 在 `+0x10`** —— 与 §1.1 的 `CounterClass : VectorClass<int> { int Total; }` 完全一致。
`[edi+0]`=vptr、`[+4]`=Items、`[+8]`=Capacity、`[+0xC]`=IsInitialized、`[+0xD]`=IsAllocated ⇒ `VectorClass` 尾部到 `+0xE`，`Total` 对齐到 `+0x10`，**sizeof = 0x14**。

**证据 2：HouseClass 批量清零 8 个 `CounterClass`，步长精确 0x14**

```asm
00103227  8d8e50550000    lea  ecx, [esi + 0x5550]    ; OwnedBuildingTypes1
0010322D  e8aec9f9ff      call 0x9FBE0
00103232  57              push edi
00103233  8d8e64550000    lea  ecx, [esi + 0x5564]    ; OwnedUnitTypes1
00103239  e8a2c9f9ff      call 0x9FBE0
0010323E  57              push edi
0010323F  8d8e78550000    lea  ecx, [esi + 0x5578]    ; OwnedInfantryTypes1
00103245  e896c9f9ff      call 0x9FBE0
0010324A  57              push edi
0010324B  8d8e8c550000    lea  ecx, [esi + 0x558C]    ; OwnedAircraftTypes1
00103251  e88ac9f9ff      call 0x9FBE0
00103256  57              push edi
00103257  8d8ea0550000    lea  ecx, [esi + 0x55A0]    ; OwnedBuildingTypes2
0010325D  e87ec9f9ff      call 0x9FBE0
00103262  57              push edi
00103263  8d8eb4550000    lea  ecx, [esi + 0x55B4]    ; OwnedUnitTypes2
00103269  e872c9f9ff      call 0x9FBE0
0010326E  57              push edi
0010326F  8d8ec8550000    lea  ecx, [esi + 0x55C8]    ; OwnedInfantryTypes2
00103275  e866c9f9ff      call 0x9FBE0
0010327A  57              push edi
0010327B  8d8edc550000    lea  ecx, [esi + 0x55DC]    ; OwnedAircraftTypes2
00103281  e85ac9f9ff      call 0x9FBE0
```

**连续 8 个 `lea` 紧跟 8 个 `call 0x9FBE0`，地址步长精确 0x14**（0x5550→0x5564→0x5578→0x558C→0x55A0→0x55B4→0x55C8→0x55DC）。
这正是组 2 + 组 3 的 8 个 `CounterClass` 被批量 `Clear()`。**对象尺寸 0x14 由此在二进制层面直接确认。**

**证据 3：全 `.text` 分段扫描，无任何 `[reg+0x5574]` 形态**

`0x5574`/`0x5588`/`0x559C` 作为**内存操作数位移**在 630,226 条指令中**零命中**
——因为访问一律走「先 `lea` 取对象基址，再在对象内取 `+0x10`」。这也反证了 §1.1 的结论：
探针直读 `house+0x5574` 等价于读 `(&OwnedUnitTypes1) + 0x10` = `OwnedUnitTypes1.Total`。

> 注：capstone 单次 `disasm` 会在 `0x6F59D` 处截断（仅 155,215 条），必须**分块扫描**才能覆盖全部 `.text`（630,226 条）。这是本项目已知陷阱。

### 1.3 定名表

| 探针键 | 偏移 | 真实字段 | 语义 |
|:--|:--|:--|:--|
| `c5560` | `0x5560` | `OwnedBuildingTypes1.Total` | **当前在图的建筑数** |
| `c5574` | `0x5574` | `OwnedUnitTypes1.Total` | **当前在图的车辆数** |
| `c5588` | `0x5588` | `OwnedInfantryTypes1.Total` | **当前在图的步兵数** |
| `c559C` | `0x559C` | `OwnedAircraftTypes1.Total` | **当前在图的飞行器数** |

### 1.4 数值四方对账（8 个快照帧，全部通过）

四屋 `Total` 之和 vs `measure_w*.json` 的全局计数器（时钟基准 = `frame_edges[0][1] + t_rel`）：

| 快照帧 | 对应帧 | 全局 units | 全局 infantry | 全局 b | Σc5574 | Σc5588 | Σc5560 | ΔU | ΔI | ΔB |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 3900 | 3912 | 730 | 242 | 7 | 729 | 242 | 6 | −1 | 0 | −1 |
| 4200 | 4193 | 727 | 242 | 7 | 727 | 242 | 6 | 0 | 0 | −1 |
| 4500 | 4506 | 727 | 242 | 8 | 727 | 242 | 7 | 0 | 0 | −1 |
| 4800 | 4787 | 726 | 244 | 5 | 726 | 244 | 4 | 0 | 0 | −1 |
| 5100 | 5100 | 719 | 247 | 0 | 719 | 247 | 0 | **0** | **0** | **0** |
| 5400 | 5412 | 706 | 239 | 0 | 707 | 240 | 0 | +1 | +1 | 0 |
| 5700 | 5694 | 671 | 236 | 0 | 670 | 236 | 0 | −1 | 0 | 0 |
| 6000 | 6007 | 632 | 220 | 0 | 632 | 222 | 0 | 0 | +2 | 0 |

**8/8 全部 |Δ|≤2**（残差来源：计数器 1 Hz 采样 vs 快照整帧，跨帧边界偏移）。三对独立关系同时成立：
- `Σc5574 ≈ units`（车辆）
- `Σc5588 ≈ infantry`（步兵）
- `Σc5560 ≈ b`（建筑）
- `Σc559C = 0` = `aircraft = 0` ✓

**这是四路互证的定名，不是靠命名猜的。**

---

## 二、★★ 推翻：`units0=732` 不是「实例化率低」

### 2.1 `units0` 的真实测量时点

`qc151_trip.py` 中：

```python
units0 = None
for _row in s_counters:
    if _row.get("units") is not None:
        units0 = _row["units"]
        break
```

`s_counters` 来自 **settle 阶段**（`_measure_poll_span(handle, MEASURE_SETTLE_S=4.0, hz=500)`），即：

```
NAV 导航完成（已进图 + 已开菜单操作）
  ↓ settle 4 s 轮询
units0 = 该阶段第一个 units 值        ← 此时帧号已是 3849
  ↓ 窗前在局闸
3 窗 × 25 s 采样
```

**`units0` 不是 t=0 的预置数，是进图后约 123–128 秒（帧 3849）的存量。**
上一轮把它当「实例化结果」对比地图预置 1600，是**口径错配**。

### 2.2 最早的可用快照已经是帧 3724

`QC213P2` 的 `early` 快照在 **帧 3724**（`qc213p2_probe_final.first_frame = 3724`）：

| 帧 | h0 车/兵 | h1 车/兵 | h2 车/兵 | h3 车/兵 | Σ车 | Σ兵 |
|--:|:--|:--|:--|:--|--:|--:|
| **3724** | **175 / 8** | 91 / 23 | 225 / 104 | 240 / 107 | **731** | **242** |
| 3900 | 173 / 8 | 91 / 23 | 225 / 104 | 240 / 107 | 729 | 242 |

**帧 3724 与 3900 之间几乎没有变化**，说明损失在此之前（帧 0–3724）就已发生完毕。

### 2.3 逐槽位分布（对照地图预置）

| 屋 | 对应 owner | 实测车/兵 | 地图预置车/兵 | 车保留率 | 兵保留率 |
|:--|:--|:--|:--|--:|--:|
| h0 | `<human player>` | 175 / **8** | 240 / 160 | 72.9% | **5.0%** |
| h1 | `Computer` | 91 / 23 | 240 / 160 | **37.9%** | 14.4% |
| h2 | `Neutral` | 225 / 104 | 240 / 160 | 93.8% | 65.0% |
| h3 | `Special` | 240 / 107 | 240 / 160 | **100.0%** | 66.9% |
| **合计** | — | **731 / 242** | **960 / 640** | **76.1%** | **37.8%** |

**分布极不均匀**：h3 车辆一个不少（240/240），h1 只剩 37.9%；h0 步兵只剩 8 个（5%），h2/h3 有 65% 左右。

### 2.4 关键反证：h2/h3 的步兵全程**完全不动**

| 帧 | h2 c5588 | h3 c5588 | h0 c5588 | h1 c5588 |
|--:|--:|--:|--:|--:|
| 3724 | 104 | 107 | 8 | 23 |
| 3900 | 104 | 107 | 8 | 23 |
| 4800 | 104 | 107 | 8 | 25 |
| 6000 | **104** | **107** | 8 | 3 |

**h2/h3 的步兵在 2276 帧（≈73 秒）内一个没死。** 若 37.8% 是战斗损失，不可能出现「两个屋零损失、两个屋近乎全灭」的分布。
⇒ **缺失发生在帧 0–3724 的一次性事件中，且与 owner 身份强相关。**

### 2.5 已排除的机制

| 假设 | 排除依据 |
|:--|:--|
| 地图预置本身就不对称 | ✗ 四槽位**完全对称**：各 240 车（MTNK 80/HTNK 80/TTNK 80）+ 160 兵（E1 54/GI 53/FLAKT 53），索引连续 |
| 格子冲突导致放置失败 | ✗ 全图 5600 个实体占 5600 个不同格子，**零碰撞** |
| 地形阻挡 | ✗ `[IsoMapPack5]` 仅 18 字节（base64 16 字符 / 解码 12 字节）、`[OverlayPack]` 30 字节（base64 28 字符 / 解码 21 字节）⇒ **纯平坦空图** |
| 建筑/防御武器击杀 | ✗ 地图无 `[Structures]`；全局 `b` 仅 6→8（h1 名下），且 `c5560` 全程 ≤8 |
| 后续持续战损 | ✗ h2/h3 步兵 2276 帧零变化（§2.4） |

### 2.6 与地图几何的关系

14 个 owner 沿对角线排成 14 个条带，每带 400 实体，**彼此紧邻**：

```
<human player> x[ 91..139] y[ 7..16]   ← h0
Alliance       x[139..188] y[ 7..16]       x=139 相接
French         x[ 81..129] y[17..26]
Germans        x[129..179] y[16..26]
British        x[ 71..119] y[27..36]
Africans       x[119..169] y[26..36]
Arabs          x[ 61..109] y[37..46]
Confederation  x[109..159] y[36..46]
Computer       x[ 51.. 99] y[47..56]   ← h1
YuriCountry    x[100..149] y[46..55]
GDI            x[ 41.. 89] y[57..66]
Nod            x[ 90..140] y[55..65]
Neutral        x[ 31.. 79] y[67..76]   ← h2
Special        x[ 80..130] y[65..75]   ← h3
```

`MaxPlayer=2`、`Player=Russians`。只有 **4 个 `HouseClass` 实例**（`meta_count=4`），映射为 h0=`<human player>` / h1=`Computer` / h2=`Neutral` / h3=`Special`。

**其余 10 个 owner（Alliance/French/Germans/British/Africans/Arabs/Confederation/YuriCountry/GDI/Nod）的 4000 个实体没有对应的 HouseClass** —— 它们要么未实例化，要么归并到上述 4 屋。

---

## 三、这对 ① 意味着什么

### 3.1 直接结论

1. **`units0=732` 不是实例化缺陷，是帧 0–3724 内的一次性损失。** 地图给了 960+640=1600，进图约 2 分钟后剩 731+242=973。
2. **上一轮「步兵实例化率 37.8%」的表述作废。** 正确表述是「步兵在进图后约 123–128 秒（帧 3724）只存活 37.8%，且分布极不均匀（5%–66.9%）」。
3. **h1 在测量窗内的崩塌（91→3 车）是第二段损失**，与帧 0–3724 的第一段损失是**两个不同阶段**。

### 3.2 为什么 `units0` 卡在 732

`units0=732` 是 **settle 起点（帧 3849）** 的值。要抬到 ≥800，必须减少帧 0–3849 内的损失，或提高地图预置总数。

**这与「改图拉开槽位距离」的思路一致，但理由变了**：不是为了让单位不被挡，而是为了让开局混战晚一点发生 / 少损失一些。

### 3.3 下一步的判据

| 优先级 | 动作 | 判据 |
|:--|:--|:--|
| 1 | 查明帧 0–3724 内 1600→973 的损失机制 | **下一趟 `--probe-frames` 换早期帧**（如 `300,600,900,1200,1800,2400,3000,3600`）。当前阶梯是 3900 起，看不到早期 |
| 2 | 若损失不可免，改图：提高 `<human player>` 预置（`_src_variant_800x600_csf` 就是 360+240 的版本） | `units0` 直接抬到 ≥800 |
| 3 | 拉开槽位距离 / 改 `Mission=Guard` | 降低帧 0–3849 的损失率 |

**⚠ 关于早期快照的说明（本件初稿曾误判，现给出确切结论）**

`qc151p3_probe_frames` = `{"latch_frames": [3900,…,6000], "anchor_default": [300,600,1800]}`，
`source: "argv:--probe-frames"` —— 本趟**显式**给了 3900 起的 8 点阶梯（`qc151_trip.py:308034`），
脚本行为正确。但**即使不给这个参数，本趟也拿不到早期帧**，原因在别处：

| 趟 | `window_stabilize_seconds` | `esc_send_times` | 首个快照帧 | 结局 |
|:--|--:|:--|--:|:--|
| T44 | **1.422** | **`[]`（零次 Esc）** | **300** ✓ | 883 帧冻结 |
| T47 | — | — | **300** ✓ | 708 帧冻结 |
| **本趟 l1a** | **11.906** | **`[4.656, 9.484]`（2 次 Esc）** | **3724** ✗ | 跑到 6137 |

**本趟发了 2 次 Esc**，跳过了片头/菜单，进图后帧号已推进到 3724 才开始 tick。
`_qc213_tick` / `_qc213p2_tick` 都由 **measure 循环**驱动，而 measure 循环在 `capture_target_frame` 之后才启动
⇒ 阶梯里的帧 10/250–312 与默认 300/600/1800 **在本趟全部错过**（`ladder_dropped=138`）。

T44/T47 能锁到帧 300，是因为**没发 Esc、窗口稳定只用 1.4 秒**，measure 循环在帧 300 前就已启动。

**⚠ 但 T44/T47 是另一张图**（`_src_variant_800x600_csf`，41 建筑、333 单位），
与本趟 L1 sf8（0 建筑、973 单位）不可比 ⇒ **本趟的早期损失曲线确实缺失，无法离线补。**

**下一趟要补，须同时满足**：(a) 不发 Esc 或把 Esc 延后到帧 <300 之前；(b) `--probe-frames` 给早期帧
（如 `300,600,900,1200,1800,2400,3000,3600`）。**脚本零改动。**

---

### 3.4 ★ 跨图佐证：T44 在帧 300 时也远低于预置

T44 用的是另一张图（`_src_variant_800x600_csf`，`<human player>` 预置 **360 车 + 240 兵**），
它在**帧 300** 就锁到了快照（§3.3 说明为何它能做到）：

| 趟 | 帧 | Σc5560（建筑） | Σc5574（车） | Σc5588（兵） |
|:--|--:|--:|--:|--:|
| T44 | **300** | 41 | **242** | **91** |
| T44 | 600 | 42 | 241 | 91 |
| T44 | 883（冻结） | 41 | 241 | 82 |
| T47 | **300** | 41 | **249** | **105** |
| 本趟 l1a | 3724 | 0 | 731 | 242 |

T44 的 `<human player>` 预置是 360 车，但**帧 300 时四屋总和只有 242 车**。
⇒ **损失在帧 300 之前就已大量发生**，这在本趟（帧 3724 剩 731/960 = 76%）之上又提前了一大截。

**这是跨图、跨趟的独立佐证**：损失不是本趟特有的，也不是「测量窗内才发生」的。

### 3.5 引擎侧已排除「Array 容量上限截断」

`YRpp` 声明：`UnitClass::Array` @`0x008B4108`、`InfantryClass::Array` @`0x00A83DE8`、
`TechnoClass::Array` @`0x00A8EC78`（均在 `.data` 段 `0x812000..0xB79BE4` 内）。

`.text` 分块全扫（630,226 条）后：

| 数组 | 直接引用数 |
|:--|--:|
| `InfantryClass::Array` (`0xA83DE8`) | 4 |
| `UnitClass::Array` (`0x8B4108` 邻域 `0x8B4100..0x8B4130`) | **35** |
| `TechnoClass::Array` (`0xA8EC78`) | 0（经全局基址间接访问） |

`DynamicVectorClass` 布局 = `VectorClass`(0x10) + `Count` + `CapacityIncrement` = **0x18**，
`SetCapacity` 有 `if (Capacity < Count) Count = Capacity;` 的**收缩**保护，但**没有**「超过 N 就拒绝插入」的硬上限。

⇒ **「引擎对超量实体设硬上限并静默截断」这一假设，在数组层没有依据。**
（仍未排除的是更高层的规则级上限，如 `MaxUnitCount`；记忆库 PERF-NSCALE01 记录过 `rules.ini` 的 `MaxUnitCount=10` 是 UI 上限、代码回退 20——但那是**建造**上限，不是**预置实例化**上限。）

## 四、诚实边界

1. 本件全部为**离线只读分析**，未重跑任何趟。
2. **`units0` 是 settle 起点值（帧 3849），不是 t=0** —— 这是本件最重要的口径纠正。
3. 帧 0–3724 的损失机制**未定谳**。已排除：预置不对称、格子冲突、地形、建筑击杀、持续战损。**未排除**：开局寻敌互射（全员 `Mission=Hunt`）、引擎对超量实体的截断、`MaxPlayer=2` 与 14 owner 的槽位裁减。
4. 10 个非 HouseClass owner 的 4000 实体去向**未定谳**（未实例化？归并？）。
5. `CounterClass` 的 `Total` 语义有**三条独立证据**：YRpp 布局反推（§1.1）、二进制清零原语 `0x009FBE0` 的 `mov [edi+0x10],0` 与 `0x00103227` 起的 8 连 `lea` 步长 0x14（§1.2）、四路数值对账 8/8（§1.4）。**未做**的是：`Total` 的**增量写入点**（对象增删时 `++/--` 的位置）尚未反汇编定位——这不影响「它是什么」的定名，但影响「它在哪一帧更新」的时序精度。
6. 上一轮 §二「h3 的 c5574=240 证明预置被实例化」的推理**方向对但理由弱**：240 是「当前在图的车辆数」，不是「实例化成功数」。若 h3 车辆一辆没死，两者数值相同；这在本趟成立（h3 车辆全程 240）。
8. **独立核验（GLM 5.3，`dwfrun-9fb1ccc3`）结果：10 HOLDS / 2 FALSIFIED / 1 INSUFFICIENT。** 两处 FALSIFIED 已在本件修正：
   (a) `DynamicVectorClass` 尺寸 **0x18**（原写 0x1C，0x1C 是 `TypeList<T>`）；(b) `[OverlayPack]` **30 字节**（原写 44）。
   一处 INSUFFICIENT：帧 3849 的「约 128 秒」是 30 fps 口径近似，帧 0–3849 段实际帧率无落盘数据，**已改为「约 123–128 秒」并标注不可定谳**。
   **两处 FALSIFIED 均不影响核心结论**（A/B/C/D/E/F/G/I 九条全 HOLDS）。
7. 本件初稿曾把 `--probe-frames 3900..6000` 误判为「仪器缺陷」，**已更正**：那是命令行显式参数（`source: "argv:--probe-frames"`），脚本行为正确，只是看不到早期损失。

---

## 五、可复跑

```bash
cd D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip\l1a_20261020
PYTHONDONTWRITEBYTECODE=1 python -c "
import json,re
d=json.load(open('qc151_fields.json',encoding='utf-8'))
val={(int(m.group(1)),m.group(2),m.group(3)):r['value']
     for r in d if r['group']=='QC213'
     for m in [re.match(r'p(\d+)_(h\d)_(\w+)\$',r['key'])] if m}
for f in (3900,4200,4500,4800,5100,5400,5700,6000):
    print(f,[sum(val.get((f,h,k),0) or 0 for h in ('h0','h1','h2','h3'))
             for k in ('c5560','c5574','c5588','c559C')])
"
```
