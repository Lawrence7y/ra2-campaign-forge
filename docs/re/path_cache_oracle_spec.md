# 路径缓存 Oracle 规格（R-PATH-ORACLE）

> 逆向对象：`gamemd.exe` 1.001（尤里的复仇），ImageBase=`0x400000`，FO = VA − `0x400000`。
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 任务：把「路径缓存落地前必须有的 oracle」写死，并给出可全静态落地的部分。
> 配套工作区：`out/re_work/re_sprint/R_path_oracle/`（`verify_anchors.py`、`scan_callers.py`、`claims.txt`、`zero_behavior_hooks.md`）。
> 前作：`docs/re/pathfinding_deep_dive.md`、`docs/re/pathfinding_locomotion.md`（含 S7 离线仿真，**非真机**）。
>
> **证据三档**：`[实证]` = VA/文件偏移/机器码本轮可复算；`[推演]` = 由实证链 + ABI/同步契约推导；`[待实测]` = 必须真机探针。

---

## 0. 任务卡交付对照

| 目标 | 本卡落点 | 状态 |
| :--- | :--- | :--- |
| 1. 寻路主循环/缓存结构 ABI、失效条件、关键 VA | §1–§3 + `claims.txt` | 静态闭环 |
| 2. **Oracle 规格**（探针/比对/样本量/失败判据） | §4 | 规格写死；执行 `[待实测]` |
| 3. 无 oracle 也可先做的：纯缓存结构/统计计数钩 | §5 + `zero_behavior_hooks.md` | 可落地 |
| 4. 确定性：RNG / SP·MP 分叉 | §6 | 静态闭环（缓存行为本身 `[待实测]`） |

---

## 1. 寻路主循环 ABI（原版，无跨单位缓存）

### 1.1 调用漏斗（本轮 `.text` 全扫 E8 rel32）[实证]

```
UpdatePathfinding 0x004D3920   ← 12 个调用点（Walk/Drive/Infantry/…）
        │
        └─唯一出口─► CallFindPath 0x004CBBA0   ← 仅 1 个调用点：0x004D3E4B
                          │
                          └─► PathFinder::FindPath 0x0042C900  (this = 0x0087E8B8)
                                    │
                                    ├─ ResetWorkspace 0x0042A5B0  (GenerationStamp++)
                                    ├─ ExpandNeighbors 0x0042CCD0 / Relax 0x0042CF80
                                    └─ BacktracePath 0x0042AA90 → g_PathResult 0x0089A2D8

旁路：0x00504DAE  直接 call FindPath（多航点/规划路径，结果+8 > 0x19 视为过长）
     —— 不经过 CallFindPath，**缓存钩 0x004D3E4B 覆盖不到**。[实证]
```

| 符号 | VA | 本轮字节锚（前 8B hex） | 等级 |
| :--- | :--- | :--- | :--- |
| `FootClass::UpdatePathfinding` | `0x004D3920` | `b89c1f0000e8266d` | [实证] |
| `FootClass::CallFindPath` | `0x004CBBA0` | `83ec14568bf1578d` | [实证] |
| **钩点 `call CallFindPath`** | **`0x004D3E4B`** | **`e8507dffff`** = `E8 50 7D FF FF` | [实证] |
| `PathFinder::FindPath` | `0x0042C900` | `83ec2053558be956` | [实证] |
| `PathFinder::ResetWorkspace` | `0x0042A5B0` | `8b410c83ec085633` | [实证] |
| `GenerationStamp++` | `0x0042A5FB..0x0042A602` | `8b4128 40 894128 0f8580000000` | [实证] |
| `IsNodeVisited` | `0x0042A690` | `8a44240884c07415` | [实证] |
| `BacktracePath` | `0x0042AA90` | `a000a3890083ec0c` | [实证] |
| `ExpandNeighbors` | `0x0042CCD0` | `83ec28538bd95556` | [实证] |
| `RelaxNeighbor` | `0x0042CF80` | `83ec145355568b74` | [实证] |
| `MarkOccupation` v[73] | `0x004D3780` | `5156578b7c24108b` | [实证] |
| `IsCellReachable` v[179] | `0x004D3810` | `83ec1453568bf18b` | [实证] |
| Walk 内层 `Process` | `0x0075AEC0` | `83ec38a1e85bb400` | [实证] |
| Drive `Process` | `0x004B0500` | `83ec105355568b74` | [实证] |
| `PathFinder` 单例 | `0x0087E8B8` | data | [实证] |
| `g_PathResult` | `0x0089A2D8` | BSS（文件未映射） | [实证] |
| 3×3 方向表 | `0x00818760` | `…03 04 05 02 -1 06 01 00 07` | [实证] |
| 8 方向步进表 | `0x0089F688` | BSS/运行期写 | [实证] |
| `CurrentFrame` | `0x00A8ED84` | data | [实证] |

### 1.2 `CallFindPath` ABI（钩点契约）[实证]

```text
VA 0x004D3E37..0x004D3E4B  (UpdatePathfinding 内)
  push ecx                      ; arg6 flags
  push ebx                      ; arg5 pathIndexOffset
  push 0                        ; arg4
  push 0x7D0                    ; arg3 maxNodes = 2000
  lea eax, [esp+0x1FC0]         ; arg2 pDestCell
  push edx                      ; arg1 pOutDirs  (= esp+0x6C 局部缓冲)
  push eax                      ; arg0 pDestCell  (与 deep_dive 命名一致时以栈序为准)
  mov ecx, ebp                  ; this = FootClass*
  call 0x004CBBA0               ; <<< HOOK 5 字节等长替换
  mov edi, eax                  ; PathResult* (期望 0x0089A2D8)
  test edi, edi
  mov [esp+0x14], edi
  je  fail
```

- 调用约定：`__thiscall`，`ecx=FootClass*`，栈参 6×DWORD，**callee `ret 0x18`**。[实证]
- 返回：`eax = PathResultClass*`；`+0x00 Cost`、`+0x04 Success`、`+0x08 StepCount`、`+0x0C pDirs`。[实证]
- 钩点之前 `v[73](0)` 已撤自身占位；之后 `rep movsd` 拷入 `Foot+0x5E0`，再 `v[73](1)` 恢复占位、写 `PathDelayTimer`。[实证]
- **命中缓存时**必须：填 `pOutDirs[0..23]`、置 `PathResult+0x04=1`、`+0x08=stepCount`、`+0x0C=pOutDirs`；**不得**跳过 `v[73]` 与 Timer 写（那些在钩点外）。[推演]

### 1.3 `UpdatePathfinding` 12 调用点（oracle 覆盖矩阵）[实证]

| 调用点 VA | 归属簇 `[推演]` | 备注 |
| :--- | :--- | :--- |
| `0x004B28A3` | Drive | 栈帧 cell 从 `>>8` 取 |
| `0x004B3A0E` | Drive | `push edx; push 0; push eax` |
| `0x004B3F37` | Drive | |
| `0x004D3FD4` | Foot 内层 | 经 `MapClass::TryGetCellAt 0x005657A0` + `v[0x480/4]` |
| `0x0051667E` | Infantry | |
| `0x005B02DC` | 地图/脚本簇 | |
| `0x005B0C99` | 地图/脚本簇 | `flags = setne+inc`（1 或 2） |
| `0x006A1EF3` | AI/队伍簇 | |
| `0x006A305D` | AI/队伍簇 | |
| `0x006A3586` | AI/队伍簇 | |
| `0x0075AFC5` | **Walk 重寻路** | `PathDelayTimer` 到期路径 |
| `0x0075B979` | **Walk 阻挡重试** | `OnBlocked` 附近 |

> **对 oracle 的含义**：缓存等价性必须在这 12 条触发路径上采样，**不能只测 Walk 框选**；否则 AI/Drive/Infantry 侧命中语义未验证。[推演]

---

## 2. 原版「缓存」实为工作区，无跨单位路径缓存

### 2.1 `PathFinder` 单例（`0x0087E8B8`，`0xC90` 字节）字段 ABI [实证]

| 偏移 | 类型 | 语义 |
| :--- | :--- | :--- |
| `+0x0C` / `+0x10` | `void*` | pBufferA / pBufferB（重置只清头部哨兵） |
| `+0x14` / `+0x68` | `DynamicVector` | 活跃节点索引向量 |
| `+0x18` / `+0x1C` | `DWORD*` | 访问戳 A/B（`MapTotalCells` 级） |
| `+0x20` / `+0x24` | `DWORD*` | 代价数组 B / A（g-score） |
| **`+0x28`** | **`DWORD`** | **`GenerationStamp`**，每次 FindPath `inc`；回绕才全清 |
| `+0x2C` | `int` | UnitSpeed |
| `+0x30` / `+0x34` | `int` | Start/Target 高度 |
| `+0x38` | `BYTE` | `bIsBusy`（入口 1 / 出口 0） |
| `+0x3C` | `int` | MaxNodeBudget（调用方传 `0x7D0`） |
| `+0x74/+0x8C/+0xA4` | 3×`0x18` | 开放集队列 |
| `+0xBC…` / `+0xC74` | word 表 / 计数 | 邻域分组 |

**无 `(start,dest) → path` 结果表**。多单位同目标 = 多次全量 Dijkstra。[实证]

### 2.2 单位私有路径状态 [实证]

| 字段 | 偏移 | 写点 |
| :--- | :--- | :--- |
| `PathDirections[24]` | `Foot+0x5E0` | UpdatePathfinding `0x004D3E94..0x004D3E9F` `rep movsd` |
| 尾哨兵 | `Foot+0x63C` | Walk `0x0075B3EB` / Drive `0x004B1373` 写 `-1` |
| `PathDelayTimer` | `Foot+0x640`（Start）/`+0x644`/`+0x648`（Duration） | Walk `0x0075AF8A..0x0075AF8F`；公式 `[0x008871E0]+0x1760` × 常量 `0x007E27F8` → `0x007C5F00` 取整 |
| 左移消费 | Walk `0x0075B3D5` / Drive `0x004B135D` | `ecx=0x17; lea esi,[+0x5E4]; lea edi,[+0x5E0]; rep movsd` |

### 2.3 原版路径结果失效条件（触发重算）[实证]+[推演]

| # | 条件 | 机制 | 等级 |
| :--- | :--- | :--- | :--- |
| V1 | `PathDirections[0] == -1` 且 `PathDelayTimer` 到期 | Walk `Process` 调 `UpdatePathfinding` | [实证] |
| V2 | 行进中 `Can_Enter_Cell` 拒绝 | `PathDirections[0]=-1`，Timer 重置退避 | [实证] |
| V3 | 路径队列走完（尾 `-1`） | 回到 V1 | [实证] |
| V4 | 目标改变（新 `MoveTo`） | Locomotor 写 `MovingDestination`，旧队列消费完/被清 | [实证] |
| V5 | 预检失败（已在原地 / 区域不可达） | `v[179] 0x004D3810` 短路，**不进搜索** | [实证] |
| V6 | 24 步截断 | 长路径每 ≤24 格必再搜 | [实证] |

---

## 3. 拟议跨单位路径缓存 ABI（落地契约）

> 原版**没有**该结构；下列为 S7/`pathfinding_deep_dive.md` 方案的**写死规格**，供 oracle 与实现共用。

### 3.1 键 / 项 [推演]（结构由我们定义）

```cpp
struct PathCacheKey {          // 8 字节紧凑 + 对齐
    int16_t  startX, startY;   // Foot+0x544 CurrentMapCoords（不是 leptons）
    int16_t  targetX, targetY; // pDestCell / MovingDestination>>8
    uint8_t  movementZone;     // TechnoTypeClass+0x5B4
    uint8_t  speedType;        // TechnoTypeClass+0x5B0
    uint16_t flags;            // UpdatePathfinding flags（1/2 会影响是否清路径）
};
struct PathCacheEntry {
    PathCacheKey key;
    uint32_t createFrame;      // CurrentFrame 0x00A8ED84
    uint32_t topologyEpoch;    // 失效纪元
    int32_t  stepCount;
    int32_t  directions[24];   // 与 Foot+0x5E0 同构
    uint8_t  isValid;
};
```

**键完备性红线**[推演]：键**不得**含指针、渲染帧、墙钟、`Randomizer::Global`、单位实例地址。单位尺寸/子位若影响 `Can_Enter_Cell`，必须升入键（当前方案未含 → **oracle 必须测步兵子位 vs 车辆同键碰撞**，见 §4.4 F5）。

### 3.2 缓存失效条件（相对原版 V1–V6 的超集）[推演]

| # | 失效事件 | 挂接建议（逻辑事件，禁墙钟） |
| :--- | :--- | :--- |
| C1 | `topologyEpoch` 不等 | 建筑 `Put`/`Destroy`/变卖、桥梁断/修、`RegisterGain/Loss` 占位翻转 |
| C2 | TTL 窗 `Δframe ≤ 4` | 仅同批集结复用；**TTL 用 `CurrentFrame` 逻辑帧，禁 `GetTickCount`** |
| C3 | 键不完全相等 | 含 flags/zone/speedType |
| C4 | 原版 V2 阻挡 | 复用结果被 `Can_Enter_Cell` 拒时，与原版同路径废弃剩余队列 |
| C5 | 第二调用方旁路 | `0x00504DAE` **不进本缓存**（或独立键空间），禁止错误复用 |

**禁止**：失效只挂在本地可见事件/渲染打脏（会 SP/MP 分叉）。[推演]（对齐 `net_sync_checksum.md` 寻路缓存行）

---

## 4. Oracle 规格（真机探针）

### 4.1 目标命题

> **H_eq**：在同种子、同命令流下，对每一次寻路请求 R，`Cached(R) ≡ Vanilla(R)`  
> 比较面：**PathDirections[24] 全 96 字节 + PathResult.StepCount/Success + PathDelayTimer(Start,Duration)**。

原版基线必须用**干净零售 1.001**（现有 `ra2youli/gamemd.exe` 含 `.detour`/第三方 dll，只可做静态，不可当运行基线）。[推演]（对齐 REWRITE_RESEARCH）

### 4.2 架构

```
同 Seed + 同命令流 (save / 自动驾驶脚本)
        │
        ├─ Run A: 干净原版（无钩）
        └─ Run B: 同版本 + PathCache 钩（EnablePathCache=1）
                │
                ▼
        逻辑帧边界对齐采样（每帧每单位）
        assert memcmp(PathDirsA, PathDirsB, 96)==0
        assert TimerA==TimerB && StepCountA==StepCountB
```

### 4.3 探针清单（真机侧，`[待实测]`）

| 探针 ID | 挂点 | 记录内容 | 侵入性 |
| :--- | :--- | :--- | :--- |
| **P0** | `0x004D3E4B` 钩**旁路日志**（先只读） | 每次寻路：`foot*`、start/dest cell、zone/speed/flags、`stepCount`、dirs 24、frame | L0 观测 |
| **P1** | 同上，双跑序列化 | Run A/B 的 P0 流 → 二进制 diff | L0 |
| **P2** | `0x0042A5B0` 之后 | `GenerationStamp`、搜索展开节点数（读 `+0x3C` 预算与活跃计数） | L0 |
| **P3** | 失效事件点（`BuildingClass::Put/Destroy`、桥、`Mark/Unmark_Occupation`） | `topologyEpoch++` 时的 frame + 原因码 | L0 |
| **P4** | `PathDelayTimer` 写点 `0x0075AF8A` | Start/Duration 与 `Rules.PathDelay` | L0 |
| **P5** | 每帧尾 | 单位坐标量化（对齐帧 CRC 输入面）抽查 | L0 |

> 探针**禁止**调用 `Random/RandomRanged`、禁止改写 `PathDirections`/Timer、禁止跳过 `v[73]`。日志走本地缓冲，不进网络事件。

### 4.4 比对什么 / 样本量 / 失败判据

#### 比对对象（每个寻路请求 R）

| 代号 | 字段 | 相等判据 |
| :--- | :--- | :--- |
| **M1** | `PathDirections[24]` | `memcmp == 0`（含 `-1` 尾） |
| **M2** | `PathResult.StepCount` / `Success` | 整型相等 |
| **M3** | `PathDelayTimer.StartTime/Duration` | 整型相等 |
| **M4** | `Can_Enter_Cell` 实际准入序列（行进 24 步） | 每步允许/拒绝布尔串一致 |
| **M5** | 帧 CRC（`CurrentFrameCRC 0x00AC51FC`） | 抽样帧相等（间接位姿） |

#### 样本矩阵（最小集 = **N≥2000 次寻路请求** 或 **≥30 局 × ≥5 分钟**，先到为准）

| 场景层 | 必测用例 | 最少次数 |
| :--- | :--- | :--- |
| S1 同键批量 | 30–50 单位同 `MoveTo`（缓存主收益） | ≥200 批 |
| S2 相邻起点 | 起点 1–2 格差、同终点、同 zone | ≥200 |
| S3 键不等 | 同起终点但 **步兵 vs 车辆**（子位/占用差异） | ≥100 对 |
| S4 拓扑变更 | 缓存窗口内造/拆建筑、断桥 | ≥50 次变更 |
| S5 动态阻挡 | 队列对撞、`Can_Enter_Cell` 失败后重寻 | ≥100 |
| S6 长路径 | >24 格截断续算 | ≥50 |
| S7 旁路 | 多航点 `0x00504DAE`（确认**未**被错误命中） | ≥30 |
| S8 多 locomotor | Walk / Drive / Infantry 各簇 12 调用点抽样 | 每调用点 ≥20 |
| S9 Tube | 方向码 8 / `\|dX\|>1` | ≥10（若地图含管） |
| S10 SP/MP | 同剧本单机 vs 双端锁步 | 各 ≥5 局 |

#### 失败判据（任一命中即 **oracle FAIL**，缓存不得合入）

| ID | 判据 | 级别 |
| :--- | :--- | :--- |
| **F1** | 任一请求 M1 不等（PathDirections 字节差） | **硬失败** |
| **F2** | M2/M3 不等 | **硬失败** |
| **F3** | M4 行进准入序列不一致 | **硬失败** |
| **F4** | 抽样帧 CRC 不一致 / MP 双端 SYNC | **硬失败** |
| **F5** | 同键不同单位类型（步兵/车辆）错误复用（S3） | **硬失败** |
| **F6** | 拓扑变更后仍命中陈旧项（S4） | **硬失败** |
| **F7** | `0x00504DAE` 旁路被 0x4D3E4B 缓存错误短接 | **硬失败** |
| **F8** | 命中率 < 30%（S1）或性能无收益 | **非致命**（回滚优化，不阻断等价性结论） |
| **F9** | 探针自身多抽 RNG / 改 Timer | **探针无效**，整轮作废 |

**通过线**：F1–F7 = 0；样本矩阵全部覆盖；双端（若测 MP）零 DESYNC。

### 4.5 离线预演与真机的关系

S7 `oracle_path_cache_verify.py` 的 82.5% 命中 / 0 分叉是 **Python 离线模型 `[推演]`**，**不能**替代 §4.2 真机对拍。真机线按 Lead 纪律可挂起，但规格以本节为准。

---

## 5. 无 oracle 也可先落地：零行为钩（统计/结构）

> 目标：**不改变任何寻路产物与 RNG 消费**，只计数/只读快照。  
> 细节与安装序见 `out/re_work/re_sprint/R_path_oracle/zero_behavior_hooks.md`。

| 钩 | VA | 行为 | 确定性 |
| :--- | :--- | :--- | :--- |
| **H0 计数** | `0x004D3E4B` 调用前后 | `n_FindPathCalls++`，按 zone/speed 直方图 | L0，原样 call |
| **H1 键指纹** | 同上 | 只读算 `(start,dest,zone,speed,flags)` 哈希进本地环 | L0 |
| **H2 命中模拟** | 同上（shadow cache） | **只模拟不短接**：shadow 命中则计 `n_ShadowHit`，仍走原版 | L0 |
| **H3 GenerationStamp** | `0x0042A5FB` 后 | 记 stamp、回绕次数 | L0 |
| **H4 失效事件** | 建筑/桥/占位 | `n_Epoch++` 直方图 | L0 |
| **H5 阻挡率** | Walk `0x0075B6D1` | `n_Blocked++` | L0 |

**Shadow cache（H2）是 oracle 的前置**：零行为变化地估计真实命中率与键冲突，决定是否值回票价，再进 §4 真机对拍。[推演]

禁止项（即使用于统计）：多抽/少抽 `ScenarioClass::Random`、改 `PathDelayTimer`、改 `PathDirections`、用墙钟做 TTL。[实证]（契约见 `net_sync_checksum.md`）

---

## 6. 确定性结论

### 6.1 寻路是否吃 RNG？

| 命题 | 结论 | 等级 |
| :--- | :--- | :--- |
| `PathFinder` 簇 `0x0042A5B0..0x0042E000` 调用 `Random/RandomRanged` | **0 次** | [实证] 本轮 `verify_anchors.py` §5 |
| `CallFindPath 0x004CBBA0` | **0 次** | [实证] |
| `UpdatePathfinding 0x004D3780..0x004D4200` | **0 次** | [实证] |
| 输入决定输出（Dijkstra 纯函数） | **是** | [实证]（S7 全链扫描一致）+ [推演] |
| `CanEnterCell` 族副作用 | 持久写 = 0 | [实证]（S7） |

⇒ **寻路本体不消费局内 RNG 流**。缓存短接若只替换「重复搜索」，**不增减** `ScenarioClass::Random` 次数。[推演]

### 6.2 缓存是否可能引入 SP/MP 分叉？

| 风险源 | SP | MP 锁步 | 等级 |
| :--- | :--- | :--- | :--- |
| 等价命中（M1 全过） | 无分叉 | 无分叉 | [推演] |
| 键不全（漏尺寸/子位/flags） | 手感变化 | **分叉** | [推演]（F5） |
| 失效滞后（只听本地事件） | 偶发不一致 | **分叉** | [推演] |
| TTL 用墙钟/渲染帧 | 不可复现 | **分叉** | [推演] |
| 限频/帧预算（插入点 B/C） | 节奏变化 | **分叉**（除非双端同算法） | [推演] |
| Shadow 只统计（H2） | 无 | 无 | [推演] |
| `0x00504DAE` 旁路误缓存 | 行为变 | **分叉** | [推演]（F7） |

**总判**：  
- **等价缓存（A 型短接）+ 逻辑事件失效 + 键完备** ⇒ SP/MP **条件安全**（与 `net_sync_checksum.md` 行 9 一致）。  
- **限频/改重寻时机（B/C 型）** ⇒ **禁止进 MP**，除非双端逐帧同队列（高风险，默认不采纳）。  
- 最终裁决以 §4 oracle F1–F7 为准；静态只能证明「无 RNG 污染」与「钩点 ABI 闭合」，**不能**证明字节等价。[推演]

---

## 7. 落地顺序建议

1. **立刻**：H0–H5 零行为钩 + shadow 命中统计（§5）→ 得命中率/键冲突。  
2. **随后**：§4 真机 oracle（干净 1.001 双跑）过 F1–F7。  
3. **通过后**：`0x004D3E4B` 等长短接 + `topologyEpoch` + TTL≤4 逻辑帧（`EnablePathCache=0` 默认关）。  
4. **明确不做**：MP 下的帧预算限频（插入点 B），除非另立锁步契约。

---

## 8. 证据索引

| 内容 | 等级 | 复算 |
| :--- | :--- | :--- |
| 关键 VA 字节锚 / 钩点 `E8 50 7D FF FF` / 生成戳 `inc [ecx+0x28]` | [实证] | `python out/re_work/re_sprint/R_path_oracle/verify_anchors.py` |
| FindPath 2 调用 / CallFindPath 1 调用 / UpdatePathfinding 12 调用 | [实证] | 同上 §4 + `scan_callers.py` |
| PathFinder/UpdatePathfinding 零 RNG | [实证] | 同上 §5 |
| PathDirections/Timer 写点机器码 | [实证] | 同上 §6 |
| 调用点簇归属、键字段完备性、失效挂点 | [推演] | — |
| 命中率、字节等价、MP 零 DESYNC | [待实测] | §4 oracle |

机器可读锚：`out/re_work/re_sprint/R_path_oracle/claims.txt`。
