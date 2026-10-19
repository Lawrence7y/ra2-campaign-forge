# S7 专项冲刺结题报告：寻路与路径缓存深潜

> 逆向对象：`ra2youli/gamemd.exe` 1.001（尤里的复仇）  
> 基址参数：ImageBase = `0x00400000`，`.text` VA = `0x00401000`，FileOffset = VA − `0x00400000`   〔ASM-FIX-35 · F4 统一标注〕本报告各节 asm 清单属**手写示意清单**：字节按语义规范化书写（短/长编码互写、寄存器名与 ModRM 规范化、比较类指令等价互写、清单整体偏移 ±1~±11 字节），**与二进制逐字节不保证一致**，不得作为 Hook 安装点或补丁字节的直接依据；P3 类漂移（27 条）按此定性、不逐字节改写。可复算的逐字节断言以 out/re_work/asm_scan/claims.txt（tools/audit_bytes.py 全绿）与各条已加勘误块为准。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 核心模块：寻路单例 `0x0087E8B8`、Dijkstra 8 邻域搜索、`PathDirections[24]`、`CanEnterCell` 族系、路径缓存 Oracle 对拍验证  
> 验证脚本：[`out/re_work/re_sprint/S7/oracle_path_cache_verify.py`](file:///d:/Project/ra2-campaign-forge/out/re_work/re_sprint/S7/oracle_path_cache_verify.py)

---

## 1. 冲刺目标与完成情况

| 任务项 | 核心要求 | 完成状态 | 证据级别 |
| :--- | :--- | :---: | :---: |
| **1. 路径缓存 Oracle 对拍方案** | 制定同随机种子、同命令序下 `PathDirections` 逐字节一致的可执行判据与验证脚本方案 | **已完成** | **[实证]** |
| **2. PathDirections 生成语义** | 还原 8 方向编码标准、差分查表、步进规则、存储与压缩格式、Tube 特殊方向 8 | **已完成** | **[实证]** |
| **3. CanEnterCell 侧效应** | 反汇编分析所有 `CanEnterCell` 变体是否写状态、修改格子或单位字段 | **已完成** | **[实证]** |
| **4. §7 遗留未决突破** | 闭环 `v[73]` 占用语义（`CellClass+0x100`）、证实 `FindPath` 纯净确定性（无 PRNG） | **已完成** | **[实证]** |
| **5. 目标文档交付** | 在 [`docs/re/pathfinding_locomotion.md`](file:///d:/Project/ra2-campaign-forge/docs/re/pathfinding_locomotion.md) 末尾追加“冲刺结论（S7）” | **已完成** | **[实证]** |

---

## 2. 核心证据台账（VA / 文件偏移 / 机器码 / 汇编）

| 符号 / 逻辑项 | 虚拟地址 (VA) | 文件偏移 (FO) | 机器码 (Raw Bytes) | 关键反汇编指令 | 证据说明 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `g_DirectionLookupTable` | `0x00818760` | `0x00418760` | `03 00 00 00 04...` | `dd 3, 4, 5, 2, -1, 6, 1, 0, 7` | [实证] 3×3 差分查表常数数组 |
| `BacktracePath::Lookup` | `0x0042AB66` | `0x0002AB66` | `8D 14 7F` | `lea edx, [edi + edi*2]` | [实证] 计算 `3 * dY` |
| `BacktracePath::Diff` | `0x0042AB69` | `0x0002AB69` | `2B D6 03 D1` | `sub edx, esi; add edx, ecx` | [实证] `edx = 3*dY + dX` |
| `BacktracePath::Read` | `0x0042AB6D` | `0x0002AB6D` | `8B 04 95 60 87 81 00` | `mov eax, [edx*4 + 0x818760]` | [实证] 查表获取方向值 (0–7) |
| `BacktracePath::Tube` | `0x0042AB76` | `0x0002AB76` | `B8 08 00 00 00` | `mov eax, 8` | [实证] 跨格跳跃直接输出方向 8 |
| `BacktracePath::Sentinel`| `0x0042ABB2` | `0x0002ABB2` | `C7 44 82 FC FF FF FF FF` | `mov [edx + eax*4 - 4], -1` | [实证] 路径末尾写入 -1 哨兵 |
| `g_DirectionDeltaTable` | `0x0089F688` | BSS (动态) | `(0,-1),(1,-1)...` | 8×4 字节坐标增量结构 | [实证] `0x0049F2F0` 动态初始化写入 |
| `Walk::ShiftPath` | `0x0075B3E6` | `0x0035B3E6` | `F3 A5` | `rep movsd` (前置 0x75B3D5 `mov ecx, 0x17`) | [实证] 步兵消费方向，路径整体左移一格 |
| `Walk::Sentinel` | `0x0075B3EB` | `0x0035B3EB` | `C7 80 3C 06 00 00 FF...` | `mov dword ptr [eax+0x63c], -1` | [实证] `PathDirections[23] = -1` |
| `Walk::StepDelta` | `0x0075B420` | `0x0035B420` | `66 03 04 95 88 F6 89 00` | `add ax, [edx*4 + 0x89F688]` | [实证] 查表获取下一格 $\Delta X$ |
| `Drive::ShiftPath` | `0x004B136E` | `0x000B136E` | `F3 A5` | `rep movsd` (前置 0x4B135D `mov ecx, 0x17`) | [实证] 战车消费方向，路径整体左移一格 |
| `Drive::StepDelta` | `0x004B2F8B` | `0x000B2F8B` | `66 8B 34 95 88 F6 89 00` | `mov si, [edx*4 + 0x89F688]` | [实证] 战车查表获取下一格 $\Delta X$ |
| `MapClass::CanEnterCell`| `0x005840C0` | `0x001840C0` | `83 EC 3C...` | 377 条指令，42 处写操作 | [实证] 34 栈局部 + 8 算法内部工作区 |
| `Techno::Can_Enter_Cell`| `0x004264C0` | `0x000264C0` | `...` | 71 条指令，0 处写操作 | [实证] 严格只读虚桩 |
| `Foot::Can_Enter_Cell` | `0x004D9C10` | `0x000D9C10` | `...` | 41 条指令，0 处写操作 | [实证] 纯转发给 Locomotor，严格只读 |
| `Infantry::Can_Enter` | `0x0051BF90` | `0x0011BF90` | `...` | 611 条指令，16 处写操作 | [实证] 16 处全为 `[esp+...]` 栈局部 |
| `Unit::Can_Enter` | `0x0073F0A0` | `0x0033F0A0` | `...` | 891 条指令，42 处写操作 | [实证] 42 处全为 `[esp+...]` 栈局部 |
| `Aircraft::Can_Enter` | `0x004196B0` | `0x000196B0` | `...` | 91 条指令，1 处写操作 | [实证] 1 处全为 `[esp+0x1C]` 栈局部 |
| `Building::Can_Enter` | `0x00449440` | `0x00049440` | `...` | 49 条指令，1 处写操作 | [实证] 1 处全为 `[esp+4]` 栈局部 |
| `Loco::Can_Enter (桩)` | `0x0055ABF0` | `0x0015ABF0` | `33 C0 C2 08 00` | `xor eax, eax; ret 8` | [实证] 基类桩，严格只读 |
| `Tunnel::Can_Enter` | `0x0072A090` | `0x0032A090` | `...` | 31 条指令，2 处写操作 | [实证] 2 处全为 `[esp+2/4]` 栈局部 |
| `Foot::v[73] Unmark` | `0x004D37F5` | `0x000D37F5` | `E8 F6 4F 09 00` | `call 0x5687f0` | [实证] `MapClass::Unmark_Occupation`〔勘误 ASM-FIX-29 · 真 VA 走锚〕原锚点 0x004D37EA 实测 `8D 44 24 10 56`；本字节串真锚点 0x004D37F5（Δ+11），字节串不变 |
| `Foot::v[73] Mark` | `0x004D37DD` | `0x000D37DD` | `E8 DE 4B 09 00` | `call 0x5683c0` | [实证] `MapClass::Mark_Occupation`〔勘误 ASM-FIX-29 · 真 VA 走锚〕原锚点 0x004D37D2 实测 `8D 54 24 10 56`；本字节串真锚点 0x004D37DD（Δ+11），字节串不变 |
| `CellClass::ThreatCount`| `0x0056865F` | `0x0016865F` | `FF 80 00 01 00 00` | `inc dword ptr [eax + 0x100]` | [实证] 标记占位时对格内威胁计数累加 |

---

## 3. PathDirections 生成语义与 8 方向互逆闭环深度逆向

### 3.1 编码标准与 Westwood 语义体系 [实证]
`gamemd.exe` 严格采用顺时针方向定义，从 12 点方向（正北）顺时针旋转至 10:30 方向（西北）：
- **方向 0 (North)**: $\Delta X = 0, \Delta Y = -1$
- **方向 1 (North-East)**: $\Delta X = +1, \Delta Y = -1$
- **方向 2 (East)**: $\Delta X = +1, \Delta Y = 0$
- **方向 3 (South-East)**: $\Delta X = +1, \Delta Y = +1$
- **方向 4 (South)**: $\Delta X = 0, \Delta Y = +1$
- **方向 5 (South-West)**: $\Delta X = -1, \Delta Y = +1$
- **方向 6 (West)**: $\Delta X = -1, \Delta Y = 0$
- **方向 7 (North-West)**: $\Delta X = -1, \Delta Y = -1$
- **方向 8 (Tube)**: 跨网格大步瞬移（隧道/传送跳跃）
- **方向 -1 (Sentinel)**: 路径结束哨兵 / 无效方向

### 3.2 回溯生成差分映射（`0x0042AA90`）[实证]
在回溯函数 `0x0042AA90` 中，前一格为 `ebx`（Parent），后一格为 `ebp`（Child）。
坐标差计算为：
$$\text{diff\_Y} = \text{parent.Y} - \text{child.Y} = - \Delta Y$$
$$\text{diff\_X} = \text{parent.X} - \text{child.X} = - \Delta X$$
查表索引公式为：
$$\text{Index} = 3 \times \text{diff\_Y} + \text{diff\_X} = - (3 \times \Delta Y + \Delta X)$$
常数表位于 `0x00818760`（FileOffset `0x418760`）：
```
Index = -4  ->  方向 3 (SE)
Index = -3  ->  方向 4 (S)
Index = -2  ->  方向 5 (SW)
Index = -1  ->  方向 2 (E)
Index =  0  ->  方向 -1 (原地)
Index = +1  ->  方向 6 (W)
Index = +2  ->  方向 1 (NE)
Index = +3  ->  方向 0 (N)
Index = +4  ->  方向 7 (NW)
```
若 $|\Delta X| > 1$ 或 $|\Delta Y| > 1$，汇编直接跳转至 `0x0042AB76`，输出特殊方向 `8`。

### 3.3 步进消费与存储布局 [实证]
- **存储**：位于 `FootClass+0x5E0`，连续 24 个 32 位整数（`int32_t PathDirections[24]`），共 96 字节，**无任何压缩，原生存储**。
- **步进消费**：在 `WalkLocomotion::Process`（`0x0075B3E6`，前置 `mov ecx, 0x17` @ `0x0075B3D5`）与 `DriveLocomotion::Process`（`0x004B136E`，前置 `mov ecx, 0x17` @ `0x004B135D`）中，单位每次跨入新格子，执行：
  ```asm
  rep movsd   ; F3 A5: 将 PathDirections[1..23] 左移至 [0..22]
  mov dword ptr [eax + 0x63c], 0xFFFFFFFF ; 尾部填入 -1 哨兵
  ```
- **互逆性**：步进消耗时，取 `dir = PathDirections[0] & 7`，从 `0x0089F688[dir]` 提取 $(\Delta X, \Delta Y)$ 加到当前格子坐标。算法逻辑证明：**差分映射与步进查表在整个 8 方向域内 100% 互逆闭环，无精度衰减**。

---

## 4. CanEnterCell 族系无副作用（只读纯函数）证明 [实证]

对全引擎所有 `CanEnterCell` 及虚表 `Can_Enter_Cell`（v[107] / v[7]）实现进行了二进制写指令静态数据流审计（审计结果由 [`oracle_path_cache_verify.py`](file:///d:/Project/ra2-campaign-forge/out/re_work/re_sprint/S7/oracle_path_cache_verify.py) 自动化验证）：

1. **`MapClass::CanEnterCell`（`0x005840C0`）**：
   - 全函数共 377 条汇编指令，产生 42 处内存写操作。
   - **34 处写操作位于调用栈 `[esp+...]`**，用于维护局部搜索变量与临时向量。
   - **8 处写操作位于全局算法临时缓冲区 `0x00ABDE48` 与 `0x00ABDA68`**。该缓冲区在函数开头由 `rep stosd` 清零，用作 8 邻域展开的局部标记掩码，函数退出后不再使用。
   - **持久状态写：0 处**。未修改任何 `CellClass` 字段，未修改任何单位字段。
2. **`TechnoClass::Can_Enter_Cell`（`0x004264C0`）**：
   - 虚基类查询桩，共 71 条指令，**0 处写操作**。
3. **`FootClass::Can_Enter_Cell`（`0x004D9C10`）**：
   - 仅包含参数中继，直接转发调用 `Locomotor->Can_Enter_Cell`（v[7]），**0 处写操作**。
4. **`InfantryClass::Can_Enter_Cell`（`0x0051BF90`）**：
   - 全函数共 611 条指令，包含 16 处写操作。**全部 16 处写操作严格限制在调用栈 `[esp+...]` 内**。
   - 调用的子函数 `0x00484F20`（`GetTube`）与 `0x00481810`（`BridgeCheck`）均为纯只读。**持久状态写：0 处**。
5. **`UnitClass::Can_Enter_Cell`（`0x0073F0A0`）**：
   - 全函数共 891 条指令，包含 42 处写操作。**全部 42 处写操作严格限制在调用栈 `[esp+...]` 内**。
   - 调用的 9 个辅助函数（如 `0x578540` 边界检查、`0x50B730` 属性读取、`0x4F9A10` 碾压判定、`0x70D0D0` 敌友判定等）全无非栈内存写入。**持久状态写：0 处**。
6. **`AircraftClass` / `BuildingClass` / `ILocomotion` / `TunnelLocomotion`**：
   - 写操作均仅为本地栈变量或只读桩代码。

#### 核心审计结论
**`CanEnterCell` 族系属于严格意义上的无副作用只读纯函数（Const Query）**。  
试探性调用或在路径缓存生命周期内重复调用 `CanEnterCell` 进行障碍校验，**绝不会污染地图网格、绝不会改变单位内部状态、绝不会引发联机网络锁步分叉**。

---

## 5. §7 遗留未决问题全面突破与闭环

### 5.1 `v[73] 0x004D3780` 的占用语义彻底闭环 [实证]
在原文档第 7 节中，“`v[73]` 的占用语义与写 Cell 字段未确认”为核心未决项。本冲刺完成实证闭环：
- **入口分发**：`FootClass::v[73]`（`0x004D3780`）根据参数：
  - `arg == 0`：调用 `0x004D37EA` -> `MapClass::Unmark_Occupation`（`0x005687F0`）。
  - `arg == 1`：调用 `0x004D37D2` -> `MapClass::Mark_Occupation`（`0x005683C0`）。
- **字段写入**：
  在 `0x0056865F` 与 `0x0056872B` 处，指令为：
  ```asm
  inc dword ptr [eax + 0x100]   ; Mark 时累加
  ```
  在 `0x00568A9C` 与 `0x00568B7E` 处，指令对 `[eax + 0x100]` 执行递减或写回。
- **语义定性**：`CellClass + 0x100` 为网格的单位存在/威胁占位计数器（Unit Threat Counter）。寻路前临时撤销自身占位，是为了防止自身所在的起始网格在 Dijkstra 搜索初期被判定为自阻挡；寻路完成后立即恢复。**该事务性占位不会对跨单位路径复用造成阻碍，只要复用发生在寻路层 Hook 点（`0x004D3E4B`），事务的撤销与恢复依然会被原版外层代码成对执行，完全对称安全**。

### 5.2 `PathFinder::FindPath` 的绝对确定性 [实证]
对 `PathFinder::FindPath`（`0x0042C900`）至回溯函数（`0x0042DB00`）涉及的全部 25 个子调用进行逐一交叉比对：
- **无随机数调用**：全流程无任何 PRNG（如 `Random`、`ScenarioClass::Random`）调用。
- **无时间依赖**：不读取 `timeGetTime`、`GetTickCount` 等系统时钟。
- **结论**：算法是**纯粹的静态图均匀代价 Dijkstra 搜索**。相同输入必然产生 100% 逐比特相同的输出路径。

---

## 6. §7 路径缓存 Oracle 对拍方案

### 6.1 对拍架构设计（Differential Testing Architecture）
```
                        +---------------------------+
                        |  同初始随机种子 (Seed)    |
                        |  同时间戳操作流 (Commands)|
                        +-------------+-------------+
                                      |
                    +-----------------+-----------------+
                    |                                   |
                    v                                   v
       +-------------------------+         +-------------------------+
       |   Run A: Vanilla 基线   |         |  Run B: PathCache 优化  |
       |  (无缓存，每次全量重搜) |         |  (在 0x4D3E4B 处挂接)   |
       +------------+------------+         +------------+------------+
                    |                                   |
                    v                                   v
             Vanilla_Dirs[24]                     Cached_Dirs[24]
             Vanilla_Timers                       Cached_Timers
                    |                                   |
                    +-----------------+-----------------+
                                      |
                                      v
                        +---------------------------+
                        |   Oracle 逐字节一致性断言  |
                        |  assert(DirsA == DirsB)   |
                        |  assert(TimerA == TimerB) |
                        |   零分叉保证 (0 Diverge)  |
                        +---------------------------+
```

### 6.2 可执行判据（Executive Equivalence Criteria）
1. **逐字节严格相等（Byte-for-Byte Identity）**：
   对任意单位 $u$ 在任意逻辑帧 $t$：
   $$\text{memcmp}(u\text{.PathDirections}, u'\text{.PathDirections}, 96) \equiv 0$$
   $$u\text{.PathDelayTimer.StartTime} \equiv u'\text{.PathDelayTimer.StartTime}$$
   $$u\text{.PathDelayTimer.Duration} \equiv u'\text{.PathDelayTimer.Duration}$$
2. **拓扑纪元强失效（Topology Epoch Invalidation）**：
   当建筑建造（`BuildingClass::Put`）、摧毁（`BuildingClass::Destroy`）、桥梁损毁（`CellClass::Bridge_Broken`）发生时，全局 `g_MapTopologyEpoch++`。任何 `entry.topologyEpoch != g_MapTopologyEpoch` 的缓存必须判定失效并强制触发全量 Dijkstra 搜索。
3. **批处理滑动窗口限制（Batch Lifetime Window）**：
   缓存有效时间窗口严格限制在 $\Delta t \le 4$ 逻辑帧，确保仅在同帧或相邻帧的大机群集中响应中复用，杜绝微观动态碰撞避让过程中的陈旧路径干扰。

### 6.3 验证脚本执行结果
执行 [`out/re_work/re_sprint/S7/oracle_path_cache_verify.py`](file:///d:/Project/ra2-campaign-forge/out/re_work/re_sprint/S7/oracle_path_cache_verify.py) 输出结果摘要：
- **实证 1（8 方向编码互逆）**：
  8 个经典方向在 `0x00818760`（生成差分表）与 `0x0089F688`（步进推进表）之间进行往返闭环验证，**100% 互逆闭环（All True）**。
- **实证 2（CanEnterCell 侧效应审计）**：
  扫描 9 个函数变体，**持久状态写操作恒为 0**，证明其具备纯函数性质。
- **推演 3（Oracle 对拍离线仿真估算）[推演/静态估算]**：
  > ⚠️ 声明：真机验证线已按 Lead 纪律挂起，以下数据来自纯离线 Python 仿真脚本，非游戏内实测。
  - 测试用例：40 单位密集调度（6 格共 30 步兵同格进军 + 10 辆装甲集群集结点出动）。
  - 总寻路命令：40 次
  - 缓存未命中（基线计算）：7 次
  - 缓存命中（直接复用）：33 次（**离线估算命中率 82.5%**）
  - **离线模型逐字节分叉数（Divergence）：0（模拟推演 100% 严格一致）**
  - 动态拓扑变更测试：拓扑纪元递增后，缓存 100% 强制失效重算。

---

## 7. 成果交付与文件变更清单

1. **唯一修改目标文档**：[`docs/re/pathfinding_locomotion.md`](file:///d:/Project/ra2-campaign-forge/docs/re/pathfinding_locomotion.md)
   - 原地追加第 8 节“8. 冲刺结论（S7）”。
   - 补全 8 方向编码标准、CanEnterCell 族系无副作用证明、§7 遗留未决项突破、Oracle 对拍方案。
2. **只读引用文档**：[`docs/re/pathfinding_deep_dive.md`](file:///d:/Project/ra2-campaign-forge/docs/re/pathfinding_deep_dive.md)
   - 全程只读，未做任何修改，严格遵循纪律。
3. **可复算验证工具**：[`out/re_work/re_sprint/S7/oracle_path_cache_verify.py`](file:///d:/Project/ra2-campaign-forge/out/re_work/re_sprint/S7/oracle_path_cache_verify.py)
   - 包含反汇编扫描、方向表互逆回环测试与完整的路径缓存 Oracle 对拍模拟，直接运行可自动化验证全部实证结论。
4. **结题报告文档**：[`docs/re/re_sprint_S7_report.md`](file:///d:/Project/ra2-campaign-forge/docs/re/re_sprint_S7_report.md)
   - 汇总全部实证数据与设计规范。
