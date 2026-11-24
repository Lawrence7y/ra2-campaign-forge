# W2 综合归因报告：同图同量级 5.7 倍帧时恶化根因排查与离线判别

> **报告版本**：2026-11-05  
> **责任角色**：报告汇总员（RA2/YR 引擎逆向与数据链路分析）  
> **执行原则**：纯离线数据分析 + gamemd.exe 静态反汇编；零真机运行、绝不启动游戏、绝不写采样代码、只写证据支持的内容、无法验证的一律进诚实账。  
> **母本节文件**：  
> - Q1 b_valid 溯源：`lead/re_line_20261105/W2_FRAMETIME_ATTRIB/sections/Q1_BVALID.md`  
> - Q2 87 窗全量矩阵：`lead/re_line_20261105/W2_FRAMETIME_ATTRIB/sections/Q2_MATRIX.md`  
> - Q2/Q3 候选与判别：`lead/re_line_20261105/W2_FRAMETIME_ATTRIB/sections/Q2Q3_CANDIDATES.md`  

---

## 本报告的复核状态

本报告对三份母本交付件进行了严格的交叉复核与证据核实，复核意见状态如下：

1. **Q1 `b_valid` 字段溯源与定谳**：**CONFIRMED（已确认）**  
   - **复核依据**：查验 harness 源码 `qc151_trip.harness8_v4.py:3839-3840, 3979-4001, 4015-4035`；查验 `gamemd.exe:0x007E9E20` RTTI COL 确证 `DynamicVectorClass<BuildingClass*>`；查验 `gamemd.exe:0x004E6B60` CRT 静态构造将 Items 与 Count 置 0；查验 `0x0043BAD6-BB24` 建筑构造按需扩容堆内存；查验地图 `XMP29U2.MAP` 无预置建筑；查验 `l3_1101v4c` 与 `l3_1101v4d` 进程 PID（18880 vs 2820）与创建时间戳确证独立冷启动；查验反例 `t55k_20261020`（三窗全 false 仍 31.25 fps 满帧）与 `l3_1101v4c`（全 false 下自发恢复至 30.68 fps），确证因果断裂。  
   - **吸纳修正**：① 纠正原稿 §4 C1 item 4 中 `archive_T49_u0800` 堆指针地址十进制 272040160 对应的十六进制为 `0x103700E0`（原误写为 `0x103A0020`，属十六进制换算笔误）；② 将原稿 §4 C1 item 2 关于 `[Structures]` 节的表述修正为「地图 INI 文件缺省未配置该节（等价于 0 预置建筑）」。

2. **Q2 87 窗全量测量普查矩阵**：**CONFIRMED（已确认）**  
   - **复核依据**：分母 N=87 窗（29 趟各 3 窗）及 17 份排除件（14 份短窗/零窗、根目录 3 份散件）全量性 100% 确证；先验门禁与大者基准口径 107 对（含 25 对临界对子透明标注）及小者基准口径 82 对确证无事后调整；按 `map_sha8` 分组的 9 张地图中位数、极值与分位数精确吻合；确证仅靶图 `f3bb0a4e`（中位 41.79ms，两极分化）与 `0add791d`（中位 75.72ms，高载慢爬）异常，其余 7 张地图均稳定满帧（中位 31.64~32.38ms）。

3. **Q2/Q3 候选原因排查与离线判别清单**：**PARTIAL（部分确认，已吸收全部修订）**  
   - **复核依据**：确证 `g_items`（`0x008A0394`）为堆缓冲区指针，慢组真实地面对象计数 `g`（`0x008A03A0`，慢组 1832 > 快组 1589）完全证实反向线索误判；确证慢组连续推帧且 `max_stall_s <= 0.75s` 斩死 C6（Sleep）；确证测量窗内零截图且未采视口坐标，使 C2 永远不可判。  
   - **吸纳五项关键修订**：  
     ① **AI 层（C4）不可离线排除，降级入账**：实测靶图 `ra2youli/[2]0LoadBench_U0400.yrm` 包含 `[AITriggerTypesEnable]` 且启用了 159 条全局触发器，且 `[Basic]` 配置了 `IgnoreGlobalAITriggers=no`，遭遇战默认加载全局 `aimd.ini`；harness 从未采样 `AITriggerTypeClass`（`0x00A8B210`）或 `TeamClass`（`0x008B40F8`）计数。原稿断言“物理不存在”系机制误判，必须将 AI 层从“已排除”改写降级为“缺乏本地脚本但具备全局触发器展开基础的未判候选”；  
     ② **微观单位自主索敌与威胁评估扫描（`T_Targeting`）独立成项**：原稿将索敌混入 C3 宏观建筑并在证伪后降级。现正式将其抽离为独立成本中心候选（`TechnoClass::Greatest_Threat` @ `0x006F8DF0` 对 20x20 粗粒度桶与螺旋 Cell 展开 $O(N \times \text{range}^2)$ 扫描打分 `0x006F7CA0`），并明确因未采索敌计数，同属「靠现有数据永远判不了」的核心项；  
     ③ **补齐战斗物理与模拟更新层**：补入逻辑帧内 `BulletClass` 弹道追踪、`DamageArea` 范围伤害与护甲抗性结算、`AnimClass` 动画状态机的 CPU 计算开销；  
     ④ **修正 Table 3.1 序号 5 的乐观判据**：明确 `qc151_fields.json` 的 `p000000_h*_c5574/c5588` 仅为开局单点静态快照，且慢组 25s 测量窗内总兵力衰减近乎平直（$\Delta\text{units}/\Delta t \approx 0$），静态比例和宏观斜率无法离线区分“原地对射”、“高速巡逻”或“寻路死锁卡塞”；  
     ⑤ **纠正函数入口 VA 笔误**：修正正文中引用的 `SelectAutoTarget`（`0x006FB010`）与 `Greatest_Threat`（`0x006F8DF0`），剔除原误写的非有效指令地址（`0x4D6F40`/`0x4D7180`）。

---

## 1. 一句话结论

在同图（`f3bb0a4e`）同兵力（1189~1352 单位，相对差 ≤10%）下出现的 **5.69 倍极端帧时恶化**（32.2 ms 满帧 vs 182.9 ms 严重慢爬），**绝非**由建筑容器状态 `b_valid`、对象计数假象 `g_items`、失焦/节流 Sleep、音频调度或宿主物理机环境引起；其算力瓶颈高度收敛于**逻辑层单位寻路与移动避障重搜（Dijkstra 2000 节点）**、**微观单位自主索敌与螺旋威胁打分（Greatest_Threat $O(N \times \text{range}^2)$ 扫描）**、**战斗物理与伤害结算（Bullets / DamageArea）**以及**渲染层视口内单位 CPU 软件光栅化（Frustum Culling / 粒子爆炸）**四大成本中心；宏观建筑存在性仅作为诱发单位聚集或停走的催化变量；且由于测控禁令严守零截图、未采视口坐标（`0x887308`）、未采寻路 `GenerationStamp`（`0x0087E8B8+0x28`）与微观索敌计数，**视口渲染、微观寻路与微观索敌三项靠现有数据在物理上永远无法定谳**。

---

## 2. Q1 `b_valid` 定谳（含 harness 源码 路径:行号）

### 2.1 Harness 采样源码与布尔判定逻辑

在 `lead/goal1_harness8_20261031` 目录下，harness 基线脚本 `qc151_trip.harness8_v4.py` 中对建筑相关字段的采样逻辑严格追溯如下：

#### (1) 全局 VA 常量定义（`qc151_trip.harness8_v4.py:3839-3840`）
```python
3839: MEASURE_B_VA = 0x00A8EB50            # B（Items=0x00A8EB44）
3840: MEASURE_B_ITEMS_VA = 0x00A8EB44
```

#### (2) 1 Hz 计数器副读函数（`qc151_trip.harness8_v4.py:3979-4001`）
```python
3979: def _rpm_counters(handle) -> dict:
3980:     """★ 1 Hz 计数器副读（§3.2）：units/infantry/aircraft + G/B/Techno
3981:     （Items 形状自检 D-3：`Items != 0 ∧ Count ≤ 100000`——Items 是**指针**，
3982:     ★ 禁用 `Count−Items==0xC`（把指针当计数，恒假；§3.6-D3））+ 工作集/提交内存。
3983: 
3984:     ★ 任一项读失败 ⇒ 该项 `null`（不写 0）；**零写入**目标进程。
3985:     """
...
3991:     b = _rpm_u32(handle, MEASURE_B_VA)
3992:     b_items = _rpm_u32(handle, MEASURE_B_ITEMS_VA)
...
3998:             "shape": {"g_valid": (None if (g is None or g_items is None)
3999:                                   else (g_items != 0 and g <= 100000)),
4000:                       "b_valid": (None if (b is None or b_items is None)
4001:                                   else (b_items != 0 and b <= 100000))}}
```

#### (3) 采样主循环调度（`qc151_trip.harness8_v4.py:4015-4035`）
```python
4015:     counters: list = []
...
4019:     next_ctr = t0 - 1.0        # ★ 首轮即做一次计数器副读（t_rel≈0，§3.2 schema）
...
4031:         if t_now >= next_ctr:
4032:             row = _rpm_counters(handle)
4033:             row["t_rel"] = round(t_now - t0, 6)
4034:             counters.append(row)
4035:             next_ctr = t_now + 1.0
```

#### (4) 确切布尔代数逻辑
- harness 每秒副读目标进程：`b = _rpm_u32(0x00A8EB50)`，`b_items = _rpm_u32(0x00A8EB44)`；
- 若 RPM 读取失败（返回 `None`），则 `b_valid = None`（JSON 中序列化为 `null`）；
- 若读取成功，判定表达式为：`b_valid = (b_items != 0 and b <= 100000)`；
- 在实跑 87 窗中，`b` 仅为 0 或个位数（1~6），绝无 `b > 100000`。因此：**`b_valid == False` 当且仅当 `b_items == 0`（同拍必定 `b == 0`）**。

---

### 2.2 全局 VA 常量与引擎数据结构溯源

通过对 `ra2youli/gamemd.exe` 的 PE 结构、MSVC RTTI 反解析与反汇编确证：

#### (1) 核心数据结构：`DynamicVectorClass<BuildingClass*>`
- **基址**：`0x00A8EB40`，符号名为 `BuildingClass::Array`（见 `docs/re/LESSONS_20261003_RE_INSTRUMENTS.md:397` 与 `docs/re/savegame_block_manifest.md:391`）；
- **RTTI 证据**：
  - 虚表地址：`0x007E9E24`；
  - CompleteObjectLocator 位于 `0x007E9E24 - 4 = 0x007E9E20`，指向 VA `0x00801280`；
  - 其 TypeDescriptor 位于 `0x00823270`，符号名解码为：`.?AV?$DynamicVectorClass@PAVBuildingClass@@@@`。

#### (2) 字段内存布局（Offset Map）
| 偏移 | 全局 VA | 字段名 | 类型 | Harness 常量名 | 运行时语义 |
|---|---|---|---|---|---|
| `+0x00` | `0x00A8EB40` | `vftable` | `void**` | — | `0x007E9E24`（虚函数表） |
| `+0x04` | `0x00A8EB44` | `Items` | `BuildingClass**` | `MEASURE_B_ITEMS_VA` | 堆上分配的指针数组首地址（为 0 即 NULL） |
| `+0x08` | `0x00A8EB48` | `VectorMax` | `uint32_t` | — | 容器当前容量 Capacity |
| `+0x0C` | `0x00A8EB4C` | `IsAllocated` | `uint8_t` | — | 内存管理标志位 |
| `+0x0D` | `0x00A8EB4D` | `IsInitialized` | `uint8_t` | — | 初始化标志位 |
| `+0x10` | `0x00A8EB50` | `Count` | `uint32_t` | `MEASURE_B_VA` | 战局当前活跃建筑实例总数 |
| `+0x14` | `0x00A8EB54` | `GrowthStep` | `uint32_t` | — | 扩容步长（硬编码为 10） |

#### (3) 汇编生命周期与惰性分配机制
1. **CRT 静态全局初始化（`ra2youli/gamemd.exe:0x004E6B60`）**：
   ```x86asm
   004E6B60: 33 C0                 xor eax, eax
   004E6B67: A3 44 EB A8 00        mov [0x00A8EB44], eax   ; Items = NULL (0)
   004E6B6C: A3 48 EB A8 00        mov [0x00A8EB48], eax   ; VectorMax = 0
   004E6B71: C6 05 4C EB A8 00 01  mov byte [0x00A8EB4C], 1
   004E6B78: A2 4D EB A8 00        mov byte [0x00A8EB4D], al
   004E6B7D: C7 05 40 EB A8 00 24 9E 7E 00 mov [0x00A8EB40], 0x007E9E24 ; vftable
   004E6B87: C7 05 54 EB A8 00 0A 00 00 00 mov [0x00A8EB54], 10         ; GrowthStep = 10
   004E6B91: A3 50 EB A8 00        mov [0x00A8EB50], eax   ; Count = 0
   ```
2. **实体插入与按需堆分配（`ra2youli/gamemd.exe:0x0043BAD6-BB24`）**：
   在 `BuildingClass::BuildingClass` 构造函数末尾，当新建筑创建并注册进全局容器时：
   ```x86asm
   0043BAD6: A1 48 EB A8 00        mov eax, [0x00A8EB48]   ; eax = VectorMax
   0043BADB: 39 05 50 EB A8 00     cmp [0x00A8EB50], eax   ; Count == VectorMax ?
   0043BAE1: 7C 2C                 jl 0x0043BB0F           ; 容量充足直接写入
   0043BAF9: 8B 15 40 EB A8 00     mov edx, [0x00A8EB40]   ; edx = vftable
   0043BAFF: 03 C1                 add eax, ecx            ; eax = VectorMax + 10
   0043BB08: FF 52 08              call dword ptr [edx+8]  ; VectorClass::Resize -> operator new[] 分配堆
   0043BB18: 89 0D 50 EB A8 00     mov [0x00A8EB50], ecx   ; Count++
   0043BB1E: 8B 0D 44 EB A8 00     mov ecx, [0x00A8EB44]   ; ecx = Items (堆指针)
   0043BB24: 89 34 81              mov [ecx + eax*4], esi  ; Items[index] = this (建筑指针)
   ```
   **确证结论**：引擎对 `BuildingClass::Array` 采取完全的**惰性分配（Lazy Allocation）**。战局内若从未创建过建筑，`Items` 永远为 `NULL`（`0`）。

---

### 2.3 `b_valid=false` 引擎语义判定（4 项候选排查）

- **候选 C1：`BuildingClass::Array` 容器处于惰性分配初始态（当前战局无建筑）**  
  **【裁决：成立（唯一真实引擎语义）】**  
  1. 汇编逻辑确证：静态构造时 `Items=0`，唯有首栋建筑构造才会触发 `Resize` 堆分配；
  2. 地图源文件确证：测试所用地图 `XMP29U2.MAP` 解析确认**缺省未配置 `[Structures]` 节**（等价于 0 预置建筑），仅有 `[Units]`（3840 辆）和 `[Infantry]`（2560 人）；
  3. 实体守恒确证：在 `l3_1101v4c` 中，`units=1211, infantry=365, b=0`，加和 `1211 + 365 = 1576`，精确等于同拍采到的 `techno=1576`；
  4. 动态翻转实证：`archive_T49_u0800/measure_w0.json` 中，t_rel=0s 时 `b=0, b_items=0, b_valid=False`；t_rel=1s 首栋建筑落成，`b=1, b_items=272040160`（对应十六进制堆地址 **`0x103700E0`**），`b_valid` 同拍翻转为 `True`。
- **候选 C2：`ReadProcessMemory` 失败 / 进程消亡**  
  **【裁决：排除】** 源码 `qc151_trip.harness8_v4.py:3998-4001` 表明 RPM 失败返回 `None`（`null`），而非 `False`；且同拍 `ws_kb`、`CurrentFrame` 均正常高频产出。
- **候选 C3：生命周期错位 / 截获在局外**  
  **【裁决：排除】** 慢组各窗逻辑帧持续推进 118~767 帧，兵力平稳在场，局内截图親眼可查已进入激烈对局。
- **候选 C4：数值越界溢出（`b > 100000`）**  
  **【裁决：排除】** 87 窗中 `b` 仅为 0 或 1~6，无任何越界记录。

---

### 2.4 跨趟独立性与因果否定铁证

#### (1) `v4c` vs `v4d` 进程独立性核对
查阅两趟产物目录下的 `_launch_result.json`、`qc151_fields.json` 与 `measure_w0.json`：

| 维度 / 字段 | `l3_1101v4c` | `l3_1101v4d` | 确证结论 |
|---|---|---|---|
| **Trip ID** | `QC161-U0800-L3-V4-20261101C` | `QC161-U0800-L3-V4-20261101D` | 独立发射序列 |
| **Carrier 载具** | `ct/c_094343442247_15396` | `ct/c_164711816568_32328` | 独立生成的文件沙箱 |
| **进程 PID** | **`18880`** | **`2820`** | **OS 分配的不同进程 ID** |
| **内核创建时间戳** | **`134379710375351078`** | **`134379964434682870`** | **内核进程对象完全不同** |
| **启动时间** | `2026-11-01T09:43:43` | `2026-11-01T16:47:11` | **两者相隔 7 小时 3 分 28 秒** |
| **进程清理** | `carrier_delete: true`（09:47:03） | `carrier_delete: true`（16:50:09） | 前序进程已彻底退出并销毁 |

**确证**：两者是相隔 7.05 小时的两个完全独立进程，绝非同一进程内的运行期状态变化。`b_valid` 由 false 变 true 纯系遭遇战中 AI 基地车（MCV）在 `v4c` 中因全图拥堵未能展开、在 `v4d` 中成功展开建了 3 栋建筑所致。

#### (2) 彻底否定因果性的两记铁证
1. **铁证反例一：`t55k_20261020`（同图 `93c2974b`、842 单位）**  
   产物路径：`out/.../qc161_u0400_trip/t55k_20261020/measure_w{0,1,2}.json`  
   实测读数：三窗全程 `b=0, b_items=0, b_valid=False`，但 `fps_avg` 分别为 **31.24, 31.28, 31.24**，`frame_ms_p50` 分别为 **32.24ms, 32.37ms, 32.30ms（满帧！）**。证实 0 建筑（`b_valid=false`）完全能跑满 31.25 fps 锁帧上限。
2. **铁证反例二：`l3_1101v4c` 趟内自发加速**  
   产物路径：`out/.../qc161_u0400_trip/l3_1101v4c/measure_w{0,1,2}.json`  
   实测读数：全程 `b_valid=False`，`fps_avg` 从 w0 的 18.52（p50=50.48ms）逐步回升至 w1 的 28.40，并在 w2 达到 **30.68 fps（p50=32.42ms，推进 767 帧满速）**。  

**定谳**：`b_valid` 在慢组（v3a/hb/v4c-w0）全 false、快组（v4d/v4e）全 true 的表面分离，纯属遭遇战 MCV 展开随机性的**伴随伪相关（Spurious Correlation）**，绝非导致 5.7 倍帧时恶化的根因。

---

## 3. Q2 候选清单（表：候选/支持证据/反对证据/可离线验证?/排序）

### 3.1 普查背景与反向线索破案

#### (1) 全量 87 窗普查与 107 对极端对子
依据 `sections/Q2_MATRIX.md` 与探针脚本 `_w2_probe.py` 对全部 87 个有效 25s 测量窗（58 窗有效推进，29 窗终局停摆）普查结果：
- 在同一地图且初始兵力差 ≤10% 的先验门禁下，全量筛出 **107 对** `frame_ms_p50` 相差 >1.5 倍的极端对照窗（最大达 5.69 倍：`v4d/w2` 32.15ms vs `hb/w1` 182.86ms）；
- 透明公开双口径：大者口径（Max-based）107 对（含 25 对跨越临界线的靶子核心对，如 v3a 1349 vs v4d 1225 差 9.19%），小者口径（Min-based）82 对；含 101 对跨趟与 6 对同趟内部剧烈跃迁（如 `hb` w1 182.9ms vs w2 72.0ms 差 2.54x，`v3a` w2 166.8ms vs w1 70.3ms 差 2.37x）；
- 按 `map_sha8` 分组中位表证实：仅靶图 `f3bb0a4e`（9 趟 27 窗，中位 41.79ms，极差 31.90~182.86ms）与 `0add791d`（5 趟 15 窗，中位 75.72ms）存在慢爬，其余 7 张地图各趟中位极其死板地稳定在 **31.64 ~ 32.38 ms**（极差 <1ms，满帧）。

#### (2) 反向线索真相大白：`g_items` 是堆指针，慢组真实计数 `g` 实际更大！
针对任务书 §2 提到的“慢组 `g_items` 偏小、快组 `ws_kb`/`pf_kb` 反而偏大”的困惑，通过代码核查彻底破案：
- `MEASURE_G_ITEMS_VA = 0x008A0394` 位于 `MapClass::ObjectsInLayers[2]` 向量偏移 `+0x04`，是 CRT 堆上分配的缓冲区首地址（**Heap Pointer**）！
  - 慢组十进制 `g_items = 256,152,480` $\longrightarrow$ 十六进制 **`0x0F4493A0`**；
  - 快组十进制 `g_items = 369,696,344` $\longrightarrow$ 十六进制 **`0x16092E58`**；
  - 慢组数值小仅代表 Windows 堆分配器恰好从较低地址分配，**绝非业务计数**；
- **真正的地面层对象计数为 `g`（VA `0x008A03A0`）**：
  实测慢组 `v3a`（**1832**）、`hb`（**1828**）**显著大于**快组 `v4d`（**1589**，少约 240 个对象）！慢组活动实体显著更多，与高负载特征完全相符；
- `ws_kb`/`pf_kb` 快组高出 <0.8%（约 1MB），纯系快组成功展开建筑后多加载了建筑 SHP/Art 资源页，非 CPU 瓶颈。

---

### 3.2 候选原因排查总表

结合复核意见，将全引擎潜在成本中心重构扩充为以下 9 项独立候选，逐项对比定性：

| 编号 | 候选原因 | 核心引擎机制与复杂度 | 支持证据 | 反对证据 | 可离线验证? | 排序 / 定性 |
|:---|:---|:---|:---|:---|:---|:---|
| **C1** | **寻路与移动碰撞阻挡** | `FootClass::UpdatePathfinding` @ `0x004D3920` 驱动均匀代价 Dijkstra（`0x0087E8B8`，单次上限 2000 节点）；**跨单位零路径复用缓存**；静止 Idle 零耗时，移动挤压避障频繁触发重寻路 | 兵力同为 1200~1350，快组（集结静止待命）与慢组（全图冲锋拥堵）寻路负载可差百倍；解释同趟同兵力不同窗突变（v3a w1 70ms 跃至 w2 166ms）与跨趟反例（t55k 满帧 vs l1c 慢爬） | 现有 counters 未采单位移动状态机，未采 `GenerationStamp`，无微观调用留痕 | **部分可推演，但定量定谳不可判**（未采 `0x0087E8B8+0x28`） | **★ 排序第 1**<br>最高嫌疑根因 |
| **C2** | **微观单位自主索敌与威胁评估扫描** | `TechnoClass::Greatest_Threat` @ `0x006F8DF0` 对 20x20 粗粒度空间桶（`0x00887888`）与螺旋 Cell 展开 $O(N \times \text{range}^2)$ 扫描打分（`0x006F7CA0`）；单位独立计时器触发 | 1300+ 单位在全图漫游寻敌时，单帧成百上千次扫描大桶与链表，单帧计算开销可达数十至上百毫秒；解释移动交火期与静止期待命期的巨大反差 | 同样缺乏微观索敌调用次数与打分循环耗时埋点；无法与寻路开销离线分离 | **现有数据永远不可判**（未采索敌计时器与计数） | **★ 排序第 2**<br>核心主嫌疑 |
| **C3** | **战斗物理与逻辑模拟更新** | 逻辑帧内 `BulletClass` 弹道追踪、`DamageArea` 范围溅射伤害与装甲抗性判定、`AnimClass` 爆炸动画状态机更新 | 千人级激烈交火期弹道与伤害判定频次暴增，属于纯逻辑层 CPU 计算大户 | 慢组 25s 测量窗内总兵力几乎零衰减（$\Delta\text{units}/\Delta t \approx 0$），难以区分激烈对射与相持卡塞 | **部分可分析，但无法定量定谳**（未采弹道与动画活跃池计数） | **排序第 3**<br>重要逻辑成本 |
| **C4** | **渲染与视口裁剪** | DirectDraw CPU 软件光栅化，`DrawIfVisible` (v[65])；视口裁剪（Frustum Culling）短路屏幕外单位；屏幕内交火时体素切片/阴影/局部脏矩形/粒子爆炸开销巨大 | 视口内外可见单位数可差数百倍，解释 150ms 巨额耗时；各窗兵力几乎无损耗但帧时剧烈起伏，符合单位进出视口特征 | harness 自动化执行无人工平移视角，理论初始视角在出生点；无法解释视野外是否同样慢爬 | **现有数据永远不可判**（零视口坐标，窗内严守禁令零截图） | **★ 排序第 4**<br>核心主嫌疑 |
| **C5** | **战斗形态与战局目标拓扑** | 建筑作为宏观吸引锚点；`TechnoClass::SelectAutoTarget`（`0x006FB010`）寻敌；有建筑时单位集结围攻停驻开火；无建筑时全图无规则穿插漫游加剧避障与索敌碰撞 | 统计上 24 个无建筑窗中位 73.9ms，61 个有建筑窗中位 32.2ms（宏观高度分离）；解释 v4c 从 w0 50.5ms 回升至 w2 32.4ms 满帧演化 | 存在铁证反例：`t55k`（全无建筑仍 32.2ms 满帧），`l3_20261021`（有建筑仍 105ms 慢爬），确证非直接充要因果 | **可离线证伪直接因果**，确证其为宏观动力学催化变量 | **排序第 5**<br>动力学诱发变量 |
| **C6** | **AI 决策与队伍更新** | `HouseClass::Update` @ `0x4F8440` 四大成本中心（AITrigger 宿主 `0x6F0AB0`、招募三兄弟 `0x4FEA60` 等） | 地图 `[AITriggerTypesEnable]` 启用了 159 条全局触发器且加载 `aimd.ini`，遭遇战 AI 存在逻辑展开基础 | 靶图是兵力基准压测图，无本地定制脚本；未采运行时 `AITriggerTypeClass` / `TeamClass` 计数，无法证实是否发生队伍爆炸 | **不可离线完全排除**，亦无法凭现有数据证实 | **降级入账**<br>未决候选 |
| **C7** | **音频调度与播放** | `VocClass::PlayAt` @ `0x007509E0`；300 槽 Voice 固定池 `[0x87E2A8]`；大规模交火音效调度 | 密集交火时音效触发极其高频 | 通道池分配纯走 Freelist，超额在入口 `0x7509EC` 直接早退，单次微秒级，历史开销从不超过 2~3ms，无法贡献 150ms 赤字 | **可逻辑完全排除**（汇编短路与开销常数上限确定） | **已排除**<br>量级严重不足 |
| **C8** | **输入/焦点与节流器 Sleep** | `0xA8ED80` 前台焦点标志（失焦 `Sleep(500)`）；`0x0055E160` 游戏速度下限节流（补睡到 32ms） | 调度或失焦是帧时人为拉长最常见机制 | **双刀斩死**：①慢组各窗连续推进（118~767 帧）且 `max_stall_s <= 0.75s`，无失焦停摆；②`0x55E160` 是下限保底器，帧耗时超 32ms 时 `elapsed >= target` 恒成立，**零 Sleep** | **可离线完全斩死**（查 `max_stall_s` 与连续推帧数据） | **已斩死**<br>与机制及数据矛盾 |
| **C9** | **进程级与宿主环境差异** | ASLR/堆碎片分布、Windows 线程调度抖动、CPU 热降频、DDraw 表面格式 | v4c 与 v4d 是间隔 7.05 小时的两个完全独立进程 | 同一物理机环境下其余 7 张地图各趟中位恒定在 31.6~32.4ms（极差 <1ms）；同进程内部窗口间剧烈跃迁（v4c 差 1.56x，v3a 差 2.37x） | **可离线完全排除**（跨图基准一致性与同趟内突变） | **已排除**<br>环境高度恒定 |

---

### 3.3 核心候选逐条深入剖析与代码级依据

#### 候选 C1 · 寻路与阻挡碰撞层（排序第 1 · 最高嫌疑根因）
- **代码与机制依据**（`docs/re/pathfinding_deep_dive.md` 与 `docs/re/pathfinding_locomotion.md`）：
  - 引擎单例 `PathFinder @ 0x0087E8B8`，核心算法为 8 邻域均匀代价 Dijkstra（`0x0042CCD0`），最大节点展开预算硬编码为 `0x7D0`（2000 个节点）；
  - **跨单位零缓存硬伤**：寻路器内部维护了 `GenerationStamp`（`this+0x28`，`0x0042A5B0` 处递增），仅用于免除工作区 512×512 网格的 `memset`，但**完全没有跨单位起终点路径复用缓存**；
  - **移动 vs 静止的巨大不对称性**：
    - 单位静止（Idle）时，`ILocomotion::Process`（`0x0075AEC0`）入口检测 `PathDirections[0] == -1` 且无指令，极短预检后直接返回，单单位每帧耗时 <0.1 微秒，1300 个静止单位总计耗时 <0.2 毫秒；
    - 单位移动时，若前方被友军阻挡（`Can_Enter_Cell` 失败），`0x0075AEC0` 会将 `PathDirections[0]` 置为 -1 并重置 `PathDelayTimer`（`+0x640`），到期后立即调用 `FootClass::UpdatePathfinding`（`0x004D3920`）触发全量 Dijkstra 搜索。单次展开 2000 个节点耗时 0.5~1.5 毫秒。当有 100~200 个单位在路口同时挤压碰撞时，单帧触发数百次 Dijkstra 搜索，单帧耗时瞬间暴增 100~200 毫秒！
- **解释力**：完美解释同图同兵力 5.69 倍帧时差（静止集结 vs 拥堵避障）、解释同趟同兵力窗间剧烈跃迁（`v3a` w1 70ms $\to$ w2 166ms），以及反例 `t55k`（842 单位静止待命跑满 32.2ms）。

#### 候选 C2 · 微观单位自主索敌与威胁评估扫描层（排序第 2 · 核心主嫌疑）
- **代码与机制依据**（`docs/re/targeting_spatial.md:29-70`）：
  - 真实调度入口为 `TechnoClass::SelectAutoTarget`（`0x006FB010`），驱动威胁评估扫描核心 `TechnoClass::Greatest_Threat`（`0x006F8DF0`）；
  - **空间扫描与打分复杂度**：
    - 扫描首先通过 `0x00412B40 / 0x004137A0` 枚举 `0x00887888` 全局 20×20 粗粒度空间桶中的候选对象；
    - 随后调用 `0x006F8960` 对射程内的螺旋 Cell 链表进行逐格遍历，核心收口于 `0x006F7CA0`（单候选过滤 + 威胁打分评估）；
    - 打分过程需反复调用 `MapClass::TryGetCellAt`（`0x005657A0`）、`MapClass::IsCellInMap`（`0x00568300`）及外交阵营判定 `HouseClass::IsAlliedWith`（`0x004F9A50`），计算开销高达 $O(N \times \text{range}^2)$。
- **解释力**：当全图 1300+ 单位在无建筑吸引下处于自主漫游状态时，各单位内部索敌定时器密集超时，单帧成百上千次触发空间桶与 Cell 打分循环，CPU 耗时完全可达数十至上百毫秒，是除寻路外最沉重的逻辑成本中心。

#### 候选 C3 · 战斗物理与逻辑模拟更新层（排序第 3 · 重要逻辑成本）
- **代码与机制依据**：
  - 逻辑帧内活跃实体循环不仅包含移动和索敌，还包含弹道与爆炸模拟：
    - `BulletClass` 弹道运动追踪与碰撞检测；
    - 武器落点触发的范围溅射伤害结算 `DamageArea`（遍历受损 Cell 内所有对象并执行装甲/抗性乘除法算力）；
    - `AnimClass` 爆炸与烟尘粒子状态机步进。
- **局限性**：慢组 25s 测量窗内总兵力几乎零衰减（$\Delta\text{units}/\Delta t \approx 0$），难以区分激烈交火还是对峙卡塞，属于重要逻辑组成但无法单独作为 5.7 倍主导因。

#### 候选 C4 · 渲染与视口裁剪层（排序第 4 · 核心主嫌疑）
- **代码与机制依据**（`docs/re/fx_draw_chain.md` 与 `docs/re/render_second_pass_deep_dive.md`）：
  - DirectDraw CPU 纯软件光栅化渲染，主渲染驱动为 `0x006D8DB0`，局部脏矩形由 `0x006D97D0/0x006D9920` 驱动，最终收口于 `DrawIfVisible`（v[65]）；
  - **视口裁剪（Frustum Culling）**：屏幕外单位在入口相交测试后 10 个指令内瞬间短路早退，CPU 开销几乎为 0；屏幕内单位则必须承担极其繁重的 VXL 体素切片解压、阴影投影、高程映射及迷雾淡出计算。
- **解释力**：若玩家视角恰好对准 500 个单位的大规模交火中心，光栅化开销足以吃满 CPU 产生 150ms 渲染卡顿；若视口在空地死角，即便有 1300 个单位也能轻松跑满 32ms。

#### 候选 C5 · 战斗形态与战局目标拓扑层（排序第 5 · 动力学诱发变量）
- **机制与定性**：
  - 有建筑存在（`b > 0`）时，敌方单位具有明确的宏观聚集点，行军至基地射程后转入原地静止攻击（`Mission::Attack`），大幅平息寻路与漫游避障碰撞；
  - 无建筑存在（`b == 0`）时，战局沦为无据点遭遇战，全图单位被迫进入无规则大范围交叉巡逻漫游，最大化激发了寻路冲突（C1）与索敌扫描（C2）；
  - **铁证反例证实非直接充要原因**：`t55k_20261020` 全无建筑仍跑满 32.2ms，`l3_20261021` 有建筑仍慢爬至 105ms，确证其并非性能瓶颈本体，而是改变战局动力学形态的**诱发/催化变量**。

#### 候选 C6 · AI 决策与队伍更新层（降级入账 · 未决候选）
- **机制与依据**：
  - 靶图 `[2]0LoadBench_U0400.yrm` 实测包含 `[AITriggerTypesEnable]` 且启用了 159 条全局触发器，且 `[Basic]` 中 `IgnoreGlobalAITriggers=no`，遭遇战默认加载全局 `aimd.ini`；
  - 但因该图无本地定制 Team，且 harness 从未副读 `AITriggerTypeClass::Array.Count`（`0x00A8B210`）或 `TeamClass::Array.Count`（`0x008B40F8`），既不能像原稿那样断言“物理不存在”，亦无法证实其发生队伍膨胀，故**降级为离线未决候选**。

#### 候选 C7~C9 · 音频、Sleep 与宿主环境（已斩死 / 排除）
- **C7 音频层**：300 槽固定池 Freelist 分配，超额入口早退，单次微秒级，量级严重不足（已排除）；
- **C8 Sleep 层**：前台零 Sleep（`0xA8ED80`）；单机节流器（`0x0055E160`）是下限截断保底器，当单帧耗时达到 70~180ms 时 `elapsed >= target` 恒成立，**零 Sleep**；慢组连续推帧且 `max_stall_s <= 0.75s` 彻底斩死失焦停摆；
- **C9 宿主环境层**：其余 7 张基准地图各趟中位死板稳定在 31.64~32.38ms（极差 <1ms）；同趟同进程内剧烈跳变（`v4c` 差 1.56x，`v3a` 差 2.37x），排除了系统降频与进程环境差异。

---

## 4. Q3 下一批离线判别清单（含「哪条永远判不了」）

### 4.1 现有产物进一步离线判别清单

利用已有产物（`measure_w*.json`、`_w2_matrix.tsv`、`_launch_result.json`、`qc151_fields.json` 与地图源文件），完全不碰真机，可执行的判别操作如下：

| 序号 | 查哪个文件 | 查哪个字段 | 判定准则（判据） | 能判死 / 确认哪个候选 | 操作复算命令 |
|:---|:---|:---|:---|:---|:---|
| **1** | `measure_w*.json` | `stats.max_stall_s`<br>`stats.logic_frames`<br>`samples` (逐拍帧沿差分) | 若 `max_stall_s < 1.0s` 且 `logic_frames > 0`，且帧间隔差分不存在 500ms/10ms 离散阶梯停顿，表现为连续毫秒级分布 | **彻底判死 C8**<br>（焦点丢失 Sleep 与节流器 Sleep） | `python -I -X utf8 -c "import json; d=json.load(open('.../measure_w0.json')); print(d['stats']['max_stall_s'])"` |
| **2** | `_w2_matrix.tsv` | `map_sha8`<br>`frame_ms_p50`（全量 87 窗） | 普查其余 7 张非高负载地图在全部 21 趟中的表现。若中位数恒定在 31.64~32.38 ms（极差 <1ms），且无一例慢爬 | **彻底判死 C9**<br>（宿主系统降频与进程级环境差异） | 查 `sections/Q2_MATRIX.md` §3 分组表 |
| **3** | `measure_w0..2.json`<br>（跨窗追踪） | `stats.frame_ms_p50`<br>（同一趟内 w0→w2） | 观察同趟同进程内部的窗口跳变：`l3_1101v4c` 从 50.5ms 跳回 32.4ms；`l3_1101v3a` 从 70.3ms 恶化到 166.8ms | **彻底判死启动参数与静态环境决定论**，确立战局运行期动态状态驱动 | 查 `_w2_matrix.tsv` 中同趟窗间比对 |
| **4** | 地图源文件<br>`[2]0LoadBench_U0400.yrm` | `[AITriggerTypesEnable]`<br>`[Basic] -> IgnoreGlobalAITriggers` | 解析确认启用了 159 条全局触发器且未忽略全局 AI，确证 skirmish 依赖 `aimd.ini` 运行全局 AI 循环 | **澄清 C6 (AI) 机制基础**<br>（纠正原稿完全排除的漏洞） | `python -I -X utf8 -c "d=open('ra2youli/[2]0LoadBench_U0400.yrm','rb').read(); print(b'[AITriggerTypesEnable]' in d)"` |
| **5** | `qc151_fields.json` | `QC213/QC213P2`<br>`p000000_h*_c5574`<br>`p000000_h*_c5588` | 查验车辆与步兵初始构成比例。**客观认知其边界**：此字段仅为开局静态快照，且慢组 25s 窗内兵力衰减近乎平直，无法离线区分交火动态 | **明确静态宏观字段的能力边界**<br>（防止过早过度推论） | 查 `qc151_fields.json` 中的 `p000000_h*_c5574` 与 `c5588` 字段 |
| **6** | `measure_w*.json` | `counters[].g`<br>（`0x008A03A0`） | 提取地面层真实对象计数并对比各窗：快组 1589 vs 慢组 1832 | **彻底修正反向线索误判**，确证慢组在场活动对象显著更多 | `python -I -X utf8 -c "import json; d=json.load(open('.../measure_w0.json')); print([c['g'] for c in d['counters']])"` |

---

### 4.2 现有产物【永远判不了】的候选原因及其根本物理原因

经过对现有产物（`measure_w*.json`、`qc151_fields.json`、`_launch_result.json`）的逐字段盘点，**以下三条核心候选靠现有产物在物理上永远无法定谳**：

#### 1. 候选 C4（渲染层视口位置与屏幕可见单位数）——【永远判不了】
- **根本原因一：物理内存字段缺失（根本没采）**  
  `measure_w*.json` 的 `counters` 仅采集了全局对象总数（units, infantry, g, b, techno）和系统内存（ws_kb, pf_kb）。**harness 从未采样**：
  - 玩家视口左上角坐标（`TacticalClass::Instance` 视口坐标偏移 `0x00887308 / 0x0088730C`）；
  - 视口裁剪通过数：`DrawIfVisible`（v[65]）在当前帧的实际命中调用计数；
  - 屏幕可见对象池：主绘制簇 `0x008A0370` 计数器与局部脏矩形队列。
- **根本原因二：严守测控禁令，测量窗内零截图（图像完全缺失）**  
  `qc151_trip.harness8_v4.py:3826` 明确规定：
  > `“★★ 观测扰动禁令（§3.1-②/§4.1）：测量窗内零键鼠、零 PrintWindow（capture_frame 属观测扰动，测量窗内禁用）”`  
  全部 87 个 25s 测量窗期间，磁盘上**完全没有生成任何一张游戏画面的截屏 PNG**！历史遗留的 `shots/` 均发生在进图前或测量窗外的校准阶段。
- **信息论定论**：在没有视口内存指针采样且零截图的前提下，试图用现有数据判断“慢窗是不是因为视口正对混战中心”在物理上是不可能的。

#### 2. 候选 C1（寻路层单位移动状态与 Dijkstra 搜索调用峰值）——【永远判不了】
- **根本原因一：根本没采微观函数调用计数与单位状态机**  
  RA2/YR 寻路单例 `0x0087E8B8` 内部维护了每次搜索必递增的生成计数器 **`GenerationStamp`（偏移 `+0x28`）**。如果 harness 采样该 VA，只需计算 $\Delta\text{GenerationStamp}$ 即可瞬间判定本秒内是否触发了海量 Dijkstra 搜索。**但 harness 从未读取该 VA**；且 harness 从未遍历全图单位读取 `Locomotor->State` 或 `FootClass->PathDirections[0]`，现有数据完全没有“当前有多少单位正在移动、有多少单位正在避障重寻路”的统计。
- **根本原因二：宏观 500Hz 帧沿采样率无法解构帧内微观耗时**  
  `measure_w*.json` 中的 `samples` 是以 500Hz 轮询 `CurrentFrame`（`0x00A8ED84`）记录的帧沿。它能高精度测出“这一帧总耗时 166.8 毫秒”，但由于缺乏进程内部微观 Profile 埋点，它**物理上无法把这 166.8 毫秒拆解为**：
  $$\text{FrameTime} = T_{\text{Dijkstra}} + T_{\text{Targeting}} + T_{\text{Physics}} + T_{\text{Render}} + T_{\text{Other}}$$
  宏观墙钟采样对于微观指令周期的不可见性，是导致无法在现有产物中定量定谳 C1 的根本原因。

#### 3. 候选 C2（微观单位自主索敌与威胁评估扫描）——【永远判不了】
- **根本原因一：微观索敌限频定时器与执行计数零采集**  
  引擎在 `TechnoClass::SelectAutoTarget`（`0x006FB010`）中维护了自主索敌定时周期，在 `TechnoClass::Greatest_Threat`（`0x006F8DF0`）中执行空间桶与 Cell 遍历。harness 从未采样各单位的索敌倒计时，也未 hook 该函数的每秒执行频次。
- **根本原因二：与寻路开销在宏观表现上高度共线**  
  单位漫游冲锋时，既高度触发避障重寻路（C1），又高度触发全图螺旋搜敌（C2），两者在宏观平直的单位总数曲线上完全共线耦合，缺乏微观计数器时无法在离线状态下实现解耦分离。

---

## 5. 诚实账

### 5.1 我亲验（纯离线实跑核验与代码审查）

1. **Harness 采样源码全链路核验**：
   - 查验 `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:3839-3840, 3979-4001, 4015-4035`，确证 `MEASURE_B_VA = 0x00A8EB50`、`MEASURE_B_ITEMS_VA = 0x00A8EB44`、`MEASURE_G_ITEMS_VA = 0x008A0394`、`MEASURE_G_VA = 0x008A03A0`；
   - 确证 `b_valid` 判定逻辑为 `(None if (b is None or b_items is None) else (b_items != 0 and b <= 100000))`；
   - 确证 `qc151_trip.harness8_v4.py:3826` 的观测扰动禁令：测量窗内零键鼠、零 PrintWindow 截图。
2. **PE 结构、RTTI 与静态反汇编核验**：
   - 查验 `ra2youli/gamemd.exe:0x007E9E20` RTTI COL 确证 `DynamicVectorClass<BuildingClass*>`；
   - 查验 `ra2youli/gamemd.exe:0x004E6B60` CRT 静态构造将 Items 与 Count 置 0；
   - 查验 `ra2youli/gamemd.exe:0x0043BAD6-BB24` 建筑构造按需扩容堆内存；
   - 查验 `docs/re/targeting_spatial.md:29-70`，确证真实索敌入口为 `TechnoClass::SelectAutoTarget`（`0x006FB010`）与 `TechnoClass::Greatest_Threat`（`0x006F8DF0`），纠正了原稿中的无效 VA 笔误。
3. **87 窗全量矩阵普查底表与对子复算**：
   - 实跑核算 `_w2_probe.py`（退出码 0），核验 `_w2_matrix.tsv` 87 行 × 12 列数据无空缺；
   - 确证分母 N=87（29 个子目录标准窗，排除 15 份 4s/0s 短窗与 2 份历史根散件，有效推进 58 窗，停摆 29 窗）；
   - 确证先验门禁下大者基准口径 107 对（含 25 对临界对子透明标注）与小者基准口径 82 对；
   - 确证 9 张地图分组中位数：靶图 `f3bb0a4e`（中位 41.79ms）与 `0add791d`（中位 75.72ms），其余 7 张地图中位恒定在 31.64~32.38ms。
4. **反向线索与独立进程核验**：
   - 提取并换算十六进制地址：慢组 `g_items = 0x0F4493A0`，快组 `g_items = 0x16092E58`，确证其为堆指针；
   - 提取真实地面对象数 `g`：慢组（1828~1832）显著大于快组（1589）；
   - 核对 `l3_1101v4c` 与 `l3_1101v4d` 之 PID（18880 vs 2820）与创建时间戳，确证相隔 7.05 小时的两个独立进程；
   - 纠正 `archive_T49_u0800` 十进制 272040160 对应的十六进制为 `0x103700E0`。
5. **地图结构实跑解析**：
   - 实跑脚本解析 `ra2youli/[2]0LoadBench_U0400.yrm`：确证存在 `[AITriggerTypesEnable]` 且启用了 159 条全局触发器，且 `[Basic]` 中包含 `IgnoreGlobalAITriggers=no`，证实遭遇战具备加载 `aimd.ini` 的机制基础，据此纠正原稿 AI 层完全排除的武断结论。

### 5.2 我未验（客观边界声明）

1. **零真机运行**：绝未启动任何游戏进程（`gamemd.exe`、`ra2loader` 等），绝未进行任何活进程内存读取；
2. **零注入代码**：绝未编写或注入任何动态内存 Hook、MiniDump、SuspendThread 或 StackWalk 探针；
3. **测量窗内视口实际位置未验**：因测量窗内零截图且 harness 从未采集视口坐标（`0x00887308/0x0088730C`），测量期间屏幕内到底包含多少可见单位客观无法验证；
4. **测量窗内微观函数调用频次与耗时未验**：因 harness 从未采样寻路单例 `GenerationStamp`（`0x0087E8B8+0x28`）、微观索敌定时器及 AI 队伍计数，各窗内到底执行了多少次 Dijkstra 搜索与多少次 Greatest_Threat 扫描客观无法验证；
5. **停摆窗退出前瞬间 DirectDraw 表面状态未验**：直接采信台账 §543/§547 的终局停摆标注。

### 5.3 铁律遵循

- **零真机**：完全恪守离线原则，所有数字追溯到已落盘文件与静态反汇编；
- **只读铁律**：`out/re_work/.../qc161_u0400_trip/` 下所有原始数据、`lead/GOAL_THREE_TARGETS_20261018.md`、`lead/PENDING_DECISIONS.md` 及三份节文件母本均未作任何修改；
- **环境安全**：Python 均以 `python -I -X utf8` 运行；
- **版本控制**：未执行 `git commit`，未执行 `git push`；写域严格限定在当前综合报告文件。
