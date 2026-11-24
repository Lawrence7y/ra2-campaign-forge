# Q1 · 成本中心 C1（寻路 / 避障重搜）静态定量分析报告

> 目标：对 `gamemd.exe` 1.001 寻路单例 `0x0087E8B8` 与 Dijkstra 主循环执行完整的字节级函数体反汇编核实，给出节点数真值、每节点指令数估计、1200 单位极端并发重寻路的理论上界与实测 166.8ms 预算的数量级比对，并解析重寻路触发与退避状态机。  
> 执纪原则：凡「A 调用 B ⇒ A 具有 B 的性质」，必须进 B 的函数体核实字节。

---

## 1. 节点数上限逆向核实：2000 是否属实？（**不属实，以字节为准**）

既有文档（如 `docs/re/pathfinding_deep_dive.md`）曾根据外层调用点的 `push 0x7d0` 推断「最大展开深度被硬编码为 2000 个节点」。经对函数链 `FootClass::UpdatePathfinding` → `FootClass::CallFindPath` → `PathFinder::FindPath` → `PathFinder::SearchCore` 逐层进入函数体内核实字节，**该结论被推翻**。

### 1.1 参数传递链追踪（0x7D0 的丢失）

1. **外层调用点**：`FootClass::UpdatePathfinding` (`0x004D3920`)
   - 位于 `0x004D3E3B`：
     ```asm
     0x004D3E37: push  ecx                           ; arg5: flags
     0x004D3E38: push  ebx                           ; arg4: pathIndexOffset
     0x004D3E39: push  0                             ; arg3: 0
     0x004D3E3B: push  0x7d0                         ; arg2: 0x7D0 (十进制 2000)
     0x004D3E40: lea   eax, [esp + 0x1fc0]
     0x004D3E47: push  edx                           ; arg1: pOutDirections
     0x004D3E48: push  eax                           ; arg0: pDestCell
     0x004D3E49: mov   ecx, ebp                      ; this = FootClass*
     0x004D3E4B: call  0x004CBBA0                    ; FootClass::CallFindPath
     ```
   - 此处确实将常数 `0x7D0` (2000) 压入栈作为 `arg2`（偏移 `ESP + 0x0C`）。

2. **中间桥接层**：`FootClass::CallFindPath` (`0x004CBBA0`)
   - 进入函数体（`0x004CBBA0`，大小 155 字节，清栈 `ret 0x18`）：
     ```asm
     0x004CBBA0: sub   esp, 0x14
     0x004CBBA3: push  esi
     0x004CBBA4: mov   esi, ecx
     0x004CBBA6: push  edi
     ```
     此时调用者传入的 `arg2`（0x7D0）位于栈偏移 `[esp + 0x28]`。
   - **字节核实**：在 `0x004CBBA0` 从 `0x004CBBA0` 至 `0x004CBC3B` 的全部指令中，**没有任何一条指令读取或传递 `[esp + 0x28]`**！
   - 反之，在调用底层寻路单例主入口 `PathFinder::FindPath` (`0x0042C900`) 前：
     ```asm
     0x004CBC13: mov   eax, dword ptr [esp + 0x34]   ; flags
     0x004CBC17: mov   ecx, dword ptr [esp + 0x20]   ; pDestCell
     0x004CBC1B: push  eax                           ; arg6: flags
     0x004CBC1C: push  -1                            ; arg5: -1 (硬编码 0xFFFFFFFF)
     0x004CBC1E: push  -1                            ; arg4: -1 (硬编码 0xFFFFFFFF)
     0x004CBC20: mov   dword ptr [esp + 0x14], edx
     0x004CBC24: push  edi                           ; arg3: pOutDirections
     0x004CBC25: push  esi                           ; arg2: FootClass*
     0x004CBC26: lea   edx, [esp + 0x1c]
     0x004CBC2A: push  ecx                           ; arg1: pDestCell
     0x004CBC2B: push  edx                           ; arg0: pStartCoord
     0x004CBC2C: mov   ecx, 0x87e8b8                 ; this = PathFinder 单例
     0x004CBC31: call  0x0042C900                    ; PathFinder::FindPath (ret 0x1c)
     ```
   - **结论**：`0x7D0` 在 `0x004CBBA0` 中被完全丢弃，传给底层 `FindPath` 的 `arg4` 与 `arg5` 是常量 `-1`！

### 1.2 底层寻路单例中节点上限的真实取值

1. **`PathFinder::FindPath` (`0x0042C900`) 的重试循环控制**：
   - 读取传入的 `arg4`（`[esp + 0x44]`）：
     ```asm
     0x0042CB8B: mov   eax, dword ptr [esp + 0x44]   ; eax = -1
     0x0042CB8F: mov   dword ptr [esp + 0x3c], 0
     0x0042CB97: inc   eax                           ; eax = 0
     0x0042CB98: neg   eax                           ; eax = 0, CF = 0
     0x0042CB9A: sbb   eax, eax                      ; eax = 0
     0x0042CB9C: and   al, 0xfc                      ; eax = 0
     0x0042CB9E: add   eax, 5                        ; eax = 5
     0x0042CBA1: mov   dword ptr [esp + 0x1c], eax   ; 循环上限设为 5
     ```
     当 `arg4 == -1` 时，外层重试轮数上限为 5 次（`0x0042CC91: cmp edi, ecx`）。
   - 随后在 `0x0042CBEA`: `mov edx, dword ptr [esp + 0x44]`（依然为 `-1`），并在 `0x0042CBFB` 处 `push edx`（作为 `arg4`）调用核心搜索函数 `PathFinder::SearchCore` (`0x00429A90`)。

2. **Dijkstra 主循环入口与预算重写**：`PathFinder::SearchCore` (`0x00429A90`)
   - 检查传入的 `arg4`（`[esp + 0x70]`）：
     ```asm
     0x00429D51: mov   eax, dword ptr [esp + 0x70]   ; 读取 arg4 (-1)
     0x00429D55: test  eax, eax
     0x00429D57: jge   0x00429D61                    ; 若 >= 0 则保持原值
     0x00429D59: mov   dword ptr [esp + 0x70], 0xfff7 ; 若 < 0，强制重写为 0xFFF7 (65527)！
     ```
   - **循环推进条件（0x00429D6D）**：
     ```asm
     0x00429D6D: mov   ecx, dword ptr [esp + 0x70]   ; ecx = 65527
     0x00429D71: mov   eax, dword ptr [esp + 0x28]   ; 已展开节点数计数器（初值 0）
     0x00429D75: xor   edx, edx
     0x00429D77: cmp   eax, ecx
     0x00429D79: jge   0x0042A3DE                    ; 达到 65527 节点跳出
     ```
   - **循环退出判据（0x0042A3DE）**：
     ```asm
     0x0042A3DE: mov   ecx, dword ptr [esp + 0x28]   ; 实际展开节点数
     0x0042A3E2: cmp   ecx, 0x2710                   ; 0x2710 = 十进制 10,000！
     0x0042A3E8: je    0x0042A43E                    ; 若达到 10000 判定为寻路失败！
     0x0042A3EA: mov   eax, dword ptr [esp + 0x14]
     0x0042A3EE: test  eax, eax
     0x0042A3F0: je    0x0042A43E                    ; 目标节点为空判定失败
     0x0042A3F2: cmp   ecx, dword ptr [esp + 0x70]   ; 是否达到预算上限 65527
     0x0042A3F6: je    0x0042A43E                    ; 达到预算亦判定失败
     0x0042A3F8: cmp   dword ptr [eax + 0xc], 2
     0x0042A3FC: jl    0x0042A43E
     0x0042A3FE: mov   ecx, dword ptr [esp + 0x6c]
     0x0042A402: push  ecx
     0x0042A403: push  eax
     0x0042A404: mov   ecx, esi
     0x0042A406: call  0x0042AA90                    ; 成功：回溯生成方向序列
     ```

### 1.3 核心结论
- **2000 节点上限属不属实**：**不属实（FALSE）**。`0x7D0` (2000) 仅为上层接口传入的无用死参数，在中间层 `0x004CBBA0` 被完全抛弃。
- **真实节点数上限**：
  - 核心循环的迭代硬上限为 **`0xFFF7`（65,527 个节点）**；
  - 寻路成功校验硬上限为 **`0x2710`（10,000 个节点）**，凡展开节点数达 10,000 或 65,527 均被强行裁定为寻路失败。

---

## 2. 单节点展开的指令数估计

Dijkstra 展开主循环（`0x00429D6D .. 0x0042A3D8`）共 **544 条汇编指令，二进制长度 1,645 字节**。展开 1 个节点时经历以下核心流程：

1. **堆顶出队与目标判决（0x00429D7F .. 0x00429DB0）**：
   - 提取当前最小代价值节点；比对当前坐标与高度是否到达终点（`0x00429D8B: cmp eax, edi` 与 `0x00429D99: cmp ecx, edi`）。耗时约 **25 ~ 35 条指令**。
2. **8 邻域展开循环（0x00429DC2 .. 0x0042A1AD）**：
   - 循环展开 0..7 八个邻域方向（Tube 格点检查第 8 方向）。
   - 对每个邻域：
     - 坐标转换与索引哈希（`0x00429E85: call 0x0056D3F0`）：约 **20 条指令**。
     - 阻挡与通行性检查（`0x00429F54: call dword ptr [edx + 0x1ac]` 即 `TechnoClass::Can_Enter_Cell`）：沿格子 `CellClass+0xE4` 物体单链表遍历，并检测 `+0x124/+0x128` 占位掩码，视格内单位与建筑物数量，耗时约 **50 ~ 150 条指令**。
     - 地形与坡度代价值计算（`0x00429830: call 0x00429830`）：约 **30 条指令**。
     - 开放集更新与优先队列入队（`0x0042A030: call 0x0042A460` 及二叉堆上浮）：约 **30 ~ 60 条指令**。
   - 单个邻居平均开销约 100 ~ 180 条指令，8 个邻域合计：`8 × (100 ~ 180) ≈ 800 ~ 1,440 条指令`。
3. **优先队列二叉堆下沉调整（0x0042A1CB .. 0x0042A3AF）**：
   - 对活动节点列表执行二叉堆堆序维护，平均耗时约 **80 ~ 150 条指令**。

### 指令数汇总
- **单节点平均指令数**：约为 **500 ~ 1,500 条指令 / 节点**（典型平原开阔地形中位数约为 **800 ~ 1,000 条指令 / 节点**）。

---

## 3. 数量级论证：1200 单位极端并发重寻路 vs 166.8ms 预算

### 3.1 理论上界计算

假设现代 CPU（单核主频 2.5 GHz ~ 3.0 GHz，平均 IPC ≈ 1.0 ~ 1.5），单条指令平均耗时约为 $0.35 \sim 0.4 \text{ ns}$（即每 $10^6$ 条指令约耗时 $0.35 \sim 0.4 \text{ ms}$）。

| 场景模型 | 节点数上限 | 每节点指令数 | 单次寻路指令数 | 单次寻路耗时 | 1200 单位同帧并发理论总耗时 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **模型 A**（假想 2,000 节点） | 2,000 | 800 | $1.6 \times 10^6$ | $\approx 0.56 \text{ ms}$ | **$672 \text{ ms}$** |
| **模型 B**（实测 10,000 节点硬限） | 10,000 | 800 | $8.0 \times 10^6$ | $\approx 2.80 \text{ ms}$ | **$3,360 \text{ ms}$（3.36 秒）** |
| **模型 C**（实测 65,527 节点耗尽） | 65,527 | 800 | $5.2 \times 10^7$ | $\approx 18.2 \text{ ms}$ | **$21,840 \text{ ms}$（21.8 秒）** |

### 3.2 与实测 166.8ms 慢窗预算对比

- **实测慢窗帧时预算**：$166.8 \text{ ms}$。
- **数量级差距**：
  - 模型 A（2,000 节点）上界 $672 \text{ ms}$：约为实测预算的 **4.0 倍**（处于同一数量级）。
  - 模型 B（10,000 节点）上界 $3,360 \text{ ms}$：约为实测预算的 **20.1 倍**（**高出 1 个数量级**）。
  - 模型 C（65,527 节点）上界 $21,840 \text{ ms}$：约为实测预算的 **130.9 倍**（**高出 2 个数量级**）。
- **推论**：
  - **理论上界远大于实测预算**。这意味着：在极端拥堵或全图无法通达的场景下，**只需约 60 个单位（按 10,000 节点）或 300 个单位（按 2,000 节点）在同一帧触发寻路，就能直接把整帧耗时打满到 166.8ms！**
  - 因此，从纯计算能力的上界来看，**C1 在静态数量级上无法被排除（NOT statically excludable）**。

---

## 4. 重寻路触发条件与形态学矛盾分析

虽然纯计算力上界无法排除 C1，但进一步进状态机代码核实其**触发与限频机制**后，发现了其与慢窗形态学的重大矛盾。

### 4.1 `WalkLocomotion::Process`（`0x0075AEC0`）完整触发条件

1. **正常推进（零寻路开销）**：
   - `0x0075AF1D: cmp dword ptr [ecx + 0x5e0], -1`。
   - 若 `PathDirections[0] != -1`，说明此前生成的 24 步路径依然有效，直接跳转 `0x0075B2FF`。
   - 每帧仅执行 `rep movsd 0x17` 将路径方向数组整体左移 1 格（`0x0075B3D5`），并调用 `Can_Enter_Cell` 驱动位移。**此时寻路单例完全不被调用，CPU 耗时微秒级**。
2. **遭遇障碍作废路径（碰撞时刻）**：
   - 当 `Can_Enter_Cell` 判定不可通行时，流程转入 `0x0075B6D1`：
     - `0x0075B6D4: mov dword ptr [edx + 0x5e0], 0xffffffff`（立即将剩余路径作废，置为 -1）；
     - `0x0075B6FA: mov eax, dword ptr [0xa8ed84]`（读取当前逻辑帧号 `CurrentFrame`）；
     - `0x0075B707: mov dword ptr [edx + 0x640], eax`（将 `PathDelayTimer.StartTime` 重置为当前帧）。
3. **退避定时器保护（Anti-Avalanche 防雪崩限频）**：
   - 随后各帧进入 `WalkLocomotion::Process` 时：
     - `0x0075AF1D` 发现 `PathDirections[0] == -1`；
     - `0x0075AF41..0x0075AF49`：
       ```asm
       0x0075AF41: mov   ecx, dword ptr [0xa8ed84]  ; ecx = CurrentFrame
       0x0075AF47: sub   ecx, edx                   ; ecx = CurrentFrame - StartTime
       0x0075AF49: cmp   ecx, eax                   ; 与 PathDelayTimer.Duration 比对
       0x0075AF4B: jge   0x0075AF69                 ; 只有 >= Duration (退避到期) 才重搜！
       ```
     - 若未到期（`Elapsed < Duration`）：
       `0x0075AF57: call dword ptr [eax + 0x548]`（进入原地微调/等待）；
       `0x0075AF66: ret 4`（**直接返回退出，本帧绝对不执行任何寻路**）。
4. **定时器时长配置与计算**：
   - 在 `0x0075AF69..0x0075AF7B` 中：
     `fld qword ptr [Rules + 0x1760]` 读取 `Rules.PathDelay`，乘以常数 `0x007E27F8`（双精度浮点数 **900.0**，即每分钟 900 逻辑帧），转换为整数作为退避帧数 `Duration`。
   - 原版 `rules.ini` 中 `PathDelay` 通常为 `.01` ~ `.02` 分钟，即 **9 ~ 18 逻辑帧**。

### 4.2 与领队慢窗形态学（§1.3）的严重张力

- **领队前提 §1.3**：慢窗是**整窗 25 秒内 147 帧持续平稳慢**（147 个间隔跨 16 个 16ms 桶连续平滑分布，`p50 = 166.8ms`），**绝不是单帧毛刺或整拍跳帧**。
- **C1 的机制特征**：
  - 阻挡后有强行 `PathDelay`（9 ~ 18 帧）退避期。
  - 在退避期间内，单位每帧在 `0x0075AF66` 直接 `ret 4` 返回，寻路耗时为 0；只有当 9 ~ 18 帧后退避集体到期时，才会在该特定帧爆发一次寻路。
  - 这在宏观帧时间上应当表现为**“十几帧极快（~30ms）+ 单帧极慢（几百毫秒）”的周期性跳帧/锯齿波形态**。
  - 能够使 147 帧每一帧都连续稳定在 166.8ms 的唯一可能，是这 1200 个单位在时间轴上被完全均匀地离散化为每帧恰有固定数量的单位退避到期，这在无外力调度的自发碰撞场景下极其罕见。

---

## 5. 结论与未验事项

1. **一句话上界结论**：
   `0x004CBBA0` 静默丢弃了外层的 `0x7D0` (2000) 节点参数，底层 Dijkstra 循环以 `0xFFF7` (65,527) 为迭代硬上限并在 `0x2710` (10,000) 处校验失败；单节点展开约需 500 ~ 1,500 条指令；1200 单位极端并发寻路的理论耗时为 **720 ~ 3,600 ms**，高出实测 166.8ms 预算 4 ~ 20 倍（高出约 1 个数量级），因此**在纯计算力数量级上无法静态排除 C1**。
2. **是否可在不采帧内数据的前提下静态排除**：
   **否（false）**。由于其理论上限远高于实测预算，纯静态分析无法排除「少量单位在慢窗中高频寻路」的可能性。
3. **明确未能验证的部分（Unverified）**：
   - 无法在离线状态下验证慢窗（`f3bb0a4e` / `0add791d`）中活进程每帧实际调用 `0x0042C900`（`PathFinder::FindPath`）的精确次数（`FindPath_Calls_Per_Frame`）。
   - 无法验证在特定拥堵地形下，1200 个单位的 `PathDelayTimer` 是否会发生相干共振或被完全离散化打散。
