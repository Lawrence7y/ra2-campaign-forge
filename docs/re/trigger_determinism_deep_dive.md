# 触发器联机确定性深潜（R-TRIG-DET）

> **目标二进制**：`ra2youli\gamemd.exe` 1.001（ImageBase `0x400000`，FileOffset = VA − 0x400000）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据分级**：`[实证]` = VA + 文件偏移 + 机器码（本轮 `out/re_work/re_sprint/R_trig_det/verify_anchors.py` 复算）；
> `[推演]` = 相邻实证 + x86/MSVC 习惯推导；`[待实测]` = 需真机。
> **边界**：本专章收口**确定性残差**；状态机/派发表细节见 `trigger_runtime_deep_dive.md`、`trigger_system_manifest.md`、`trigger_tag_abi_deep_dive.md`；RNG/帧 CRC 红线见 `net_sync_checksum.md`。
> **工作区**：`out/re_work/re_sprint/R_trig_det/`（claims.txt / risk_table.md / verify_anchors.py / scan_rng_sites.py）

---

## 0. 结论速览

1. **TriggerClass/TagClass 状态机在单机与联机下走同一条求值/执行路径**：触发器三簇（`0x6DD000–0x6E5000` 动作、`0x71E000–0x727000` 事件、`0x55AFB0` 轮询器）对 `0xA8D5F8` 的字面量引用为 **0**；`MainLogicFrame` 的 4 个 `0xA8D5F8` 读点全部落在轮询器调用**之前**的网络/命令分支。轮询器 `call 0x55AFB0` 位于 `0x55DBCD` 条件块汇合点之后，**无条件每逻辑帧一次**。[实证]
2. **事件条件体零 PRNG**：`HasOccured 0x71E940–0x71F700` 本轮重同步扫描 0 命中 `Random/RandomRanged`。条件求值本身不消耗随机流。[实证]
3. **求值/执行顺序全为插入序**：每帧 Tag 向量 = `TagTypeClass::Array` 下标升序；Tag→Trigger = 头插 LIFO；Trigger→Event/Action = 尾接 INI 序；每帧 10 个自求值事件为硬编码固定序。全链路无指针比较/地址哈希。[实证]
4. **确定性残差 Top5** 见 `risk_table.md`：本地输入驱动事件、RNG 消费次数、INI 加载序、AITrigger×TeamDelayTimer、0x722xxx 残差 RNG 簇。
5. **产品向（ra2forge）**：`maplib` 把 `[Triggers]` 第 8 字段写死为 `0`，而 `make_trigger(repeating=…)` 只写入 `[Tags]`——Persistence 只有 Tags 生效，字段不一致是语义坑。

---

## 1. 状态机（TriggerClass / TagClass）

### 1.1 每帧节拍与帧时钟耦合

```
MainLogicFrame 0x55D360
  0x55DBCD  cmp [0xA8B238],edi     ; GameMode 条件块
  0x55DC99  mov ecx,0x87F778       ; LogicClass::Logics（汇合点）
  0x55DC9E  call 0x55AFB0          ; ★ 自触发轮询器，唯一调用点，无条件
  …
  0x55DE73  CurrentFrame++         ; 轮询器早于帧号自增
  0x55DE9F  call 0x725C70          ; 延迟析构队列抽干
```

- 轮询器抛事件时 `CurrentFrame` 仍是**本帧自增前**的值；`ResetTimers` 读 `[0xA8ED84]`——两者共同决定 `TimerStruct` 相位。[实证]
- 计时器单位 = **逻辑帧**（`Elapsed/RandomDelay` 分支同用 `*3*5` = 15×arg）。不可换墙钟。[实证]

### 1.2 求值顺序三层

| 层 | 结构 | 插入 | 求值序 |
|---|---|---|---|
| 每帧 Tag 名单 | `DynamicVectorClass` `0x8B40C8` | 尾接 `Items[Count++]=tag` | 下标升序 = 注册序 |
| Tag→Trigger | 单链表 `TagClass+0x28` | **头插** `0x6E55C0` | 创建序逆序（LIFO） |
| Trigger→Event/Action | 单链表（节点 `+0x28`） | 尾接 | INI 声明序；位图位次=链表位次 |

每帧事件固定 10 步：`0x32 PickupCrate → 0x1B GlobalSet → 0x1C GlobalCleared → 0x24 LocalSet → 0x25 LocalCleared → 0x2D AmbientLightBelow → 0x2E AmbientLightAbove → 0x0D ElapsedTime → 0x33 RandomDelay → 0x0E MissionTimerExpired`。任一事件在该 Tag 上产出动作则跳过该 Tag 余下事件种类（不中止整帧）。[实证]

### 1.3 门控与生命周期

- `TriggerClass::RegisterEvent` 前置：`Enabled@+0x44 != 0` 且 `Destroyed@+0x30 == 0`（DA2-T1 更正后的命名）。ctor 置 `Enabled=1`、`Destroyed=0`。[实证]
- Persistence（`TagTypeClass+0x9C`）：`0` Volatile=命中即 FireActions+Destroy；`1` SemiPersistant=仅 `InstanceCount==1` 时执行并销毁；`2` Persistent=只 FireActions 永不销毁。[实证]
- `Destroyed` 只是标记；真正释放走延迟队列 `0xB0F698`，帧尾 `0x725C70` 统一抽干 → 多端销毁时机一致。[实证]
- `RaiseEvent` 入口 `ArmageddonMode@0xA8ED6B` 置位则整条返回 false——该全局须多端一致。[实证]

### 1.4 与 AITrigger 的分界

AITrigger `0x6F0AB0` 不属于 Tag/Trigger 体系、不挂 Tag、不进每帧向量；由 `HouseClass` AI 簇经 **TeamDelayTimer** 门控调用，判据为房级 Team 计数 + `RandomRanged(1,100)<=Probability`。与普通触发器**零交叉**，但**共享同一条 `ScenarioClass::Random` 流**。[实证；门控语义 [推演]]

---

## 2. 确定性风险点

完整 20 条见 `out/re_work/re_sprint/R_trig_det/risk_table.md`。此处只展开 Top5。

### 2.1 本地输入/可见性驱动事件 [VIOLATION]

事件 `0x21 SelectedByPlayer` / `0x23 EnemyInSpotlight` / `0x31/0x32 PickupCrate*` / `0x04 DiscoveredByPlayer` 依赖本机交互或本机可见性。每帧轮询器读的锁存位 `[Scenario+0x34BE]`(crate)、`0x34AA`(global/local set) 若由拾取木箱等本地动作置位，条件求值结果在多端天然分叉。

**处置**：联机地图禁用这四类事件，或仅挂在「表现层 Tag」（不改逻辑状态的动作）。触发器侧本身无 NetworkEvent 产生（manifest §1.3 负证），分叉发生在条件求值而非命令队列。

### 2.2 RNG 消费次数 [VIOLATION]

| 消费点 | 次数/次调用 | 锚 |
|---|---|---|
| `ResetTimers 0x726400`（RandomDelay 装填） | 1×`RandomRanged(0,arg)` | `0x72646A` |
| 动作 `0x3A MeteorShower` | **4×`Random()`** | `0x6E2CEB/0x6E2D4E/0x6E2D5A/0x6E2DB0` |
| 动作 `0x62 PlaySoundEffectRandom` | 1×`RandomRanged` | `0x6DE80F` |
| `AITrigger 0x6F0AB0` / 姊妹 `0x6F0C9C` | 各 1×`RandomRanged` | `0x6F0B01` 等 |
| 帧 CRC `0x64DAB0` | 1×`Random()` 折入 `CurrentFrameCRC` | `0x64DE3F` |

任何改次数/参数/短路路径的补丁都改 RNG 序列。帧 CRC 会消费一次 Random 并把输出折进累加器（**不**读 `Table/Next1/Next2` 内部状态）→ RNG 分叉**当帧**即被 CRC 打出。

### 2.3 `TagTypeClass::Array` 加载序 [VIOLATION·条件·待实测]

每帧 Tag 向量顺序的唯一来源是任务初始化 `0x684CB7` 段对 `TagTypeClass::Array` 的下标升序扫描；存档按原序还原。**没有**按 Tag 名/指针/House 排序的指令。因此「多端顺序一致」的充分条件是 **INI 解析器枚举序一致**——静态无法断言解析器是否用哈希表遍历。这是原 U-1 残差，仍为 [待实测]。

### 2.4 AITrigger × TeamDelayTimer [RISK]

AITrigger 每次评估抽 `RandomRanged(1,100)`（+加权挑选再 1 次）。门控计时器 `this+0x5798/+0x57A0` 若因浮点/帧号/房序在多端不一致，抽数次数立即分叉。普通触发器不经过此路径，但共享 RNG 流。ra2forge 地图若写 `IgnoreGlobalAITriggers=yes` 可整体关掉 AITrigger，消除该面。

### 2.5 残差 RNG 触点（原 U-3） [RISK·待实测]

本轮扫描 `0x71E000–0x727000` 内除 `ResetTimers` 外仍有：

- `0x720ABE` `RandomRanged`
- `0x7224B9 / 0x722B67 / 0x722F75 / 0x72304A / 0x723604` `Random`（5 处，0x722xxx 簇）

以及 `MainLogicFrame` 内 `0x55DE08` `RandomRanged`（位于轮询器调用之后、`CurrentFrame++` 附近）。这些点**是否属于触发器契约面、是否被 MP 同步约束**，上游归属仍未闭环。在归属定谳前，禁止对该区间做任何「优化短路」。

---

## 3. 与 `0xA8D5F8` NetworkManager 门控交叉

| 问题 | 结论 | 证据 |
|---|---|---|
| 触发器求值是否读 SessionFlags？ | **否** | TAction/TEvent/Poller 三簇 `A0/A3/83 3D … F8 D5 A8 00` 字面量 0 命中 |
| 单机/联机是否走不同 trigger 路径？ | **否** | 轮询器在 `0x55DBCD` 条件块**汇合点之后**无条件调用；`RegisterEvent/FireActions` 无 `0xA8D5F8` 分支 |
| `MainLogicFrame` 的 4 个读点在哪？ | `0x55D465` `test [0xA8D5F8],2`；`0x55D87A` `mov ecx,[0xA8D5F8]; test cl,2`；`0x55D8F9`；`0x55DA44` | 本轮扫描；均在 `0x55DC9E` 轮询器**之前** |
| 语义影响面 | 命令队列消费 / 帧 CRC 报告 / 网络事件执行在 MP 才走锁步路径；**触发器状态机两模式同构** | `net_sync_checksum.md` §7#10 |
| 遭遇战 | **不置位** bit1（`[0xA8D5F8]=0x00`，ZCode 真机）→ MP 门控在遭遇战不触发；bench 对局的 L2 节流一直以「单机」跑 | `out/re_work/zcode_live/claims.txt` |

**含义**：产品侧不能靠「联机关掉触发器」来防 desync——触发器在单机也在跑；真正的约束是 **RNG 消耗次数 + 本地输入事件 + INI 加载序**。MP 门控只保护命令/CRC 层。

---

## 4. 产品向：ra2forge 地图触发器语义坑

> 只读 `ra2forge/**`，本节为静态审查，不改代码。

| # | 坑 | 位置 | 引擎语义 | 建议 |
|---|---|---|---|---|
| P1 | `[Triggers]` 第 8 字段（REPEATING）**写死 `0`**，`make_trigger(repeating=…)` 只影响 `[Tags]` | `maplib.py:448-449` vs `triggers.py:32-37` | Persistence 实际由 **Tags 首字段**（`TagTypeClass+0x9C`）决定；Triggers 尾字段与之是否同义需对照官方图 | 以 Tags 为准并在文档声明；或两处同步写 |
| P2 | 默认 `repeating=0` = Volatile（一次即销毁） | `triggers.py:32` | 命中后 FireActions+Destroy | 多波次增援须 `repeating=1/2` |
| P3 | `ElapsedTime(seconds)` → 引擎 `Duration=15*arg` 逻辑帧 | `triggers.py:112-114` | 单位是**秒**（15fps）正确 | 勿改成帧数；文档注明单位 |
| P4 | 房号为 `[Houses]` 数字索引 | `design.HOUSE_INDEX` / `act_winner` 等 | `FindHouseByIndex 0x6E45E0` | 顺序变更会改目标房 |
| P5 | `act_reinforce_at_waypoint` = Action **80** `ReinforcementAt`，P7 为路径点字母 | `triggers.py:59-61` | 表项 `0x50` 存在，读 `TeamType*+0x30` / `Waypoint+0x44` | 字母→Waypoint 号转换 `ord(letter)-ord('A')` 与引擎一致 |
| P6 | `act_reveal_all` = Action 16 `RevealAllMap` | `triggers.py:88-90` | 改地图/可见性状态（manifest 标红 `M`） | 锁步下多端同帧揭示则安全；勿做单端补丁 |
| P7 | `IgnoreGlobalAITriggers=yes` | `maplib.py:230` | 关闭 AITrigger 体系 | **有利确定性**（消除 AITrigger RNG 消费） |
| P8 | CreateTeam/Reinforcement 创建 `TeamClass` | `builder.py:522-542` | 进对象表；后续 `TeamClass::AI` 可能抛 `0x17 TeamLeavesMap` | 队伍脚本步进序进红线（不可改遍历序） |
| P9 | 仅含 `ElapsedTime/RandomDelay/TimerExpired` 的 Tag 若 `GetFlags` 无 bit0x10 则不进每帧向量 | `make_trigger` 未暴露 flags 控制 | 静态：bit0x10 由引擎 `TEventClass::GetFlags` 推导，地图侧无法直接写 | 这些事件本身带 bit0x10，一般成立；自定义事件组合需回归 |

---

## 5. 证据与残差

### 5.1 本轮独立复算（17 条锚）

`verify_anchors.py` 输出与前作逐字一致：轮询器入口/调用、Enabled/Destroyed 门控、头插 `0x6E55C0`、Meteor×4、PlaySndRnd、AITrigger、CRC Random、Armageddon 早退、双派发表基址、ctor/Destroy 置位。[实证]

### 5.2 残差（继承 + 本轮）

| ID | 残差 | 状态 |
|---|---|---|
| U-1 | `TagTypeClass::Array` 加载序是否严格 = INI 文本序 | **仍待实测** |
| U-3 | `0x722xxx` 簇 5×Random + `0x720ABE` RandomRanged + `0x55DE08` 归属 | **仍待实测**（本轮定位精确 VA） |
| U-4 | 延迟析构队列在帧中存档是否进档 | 仍待实测 |
| NEW | `0xA8B238`（GameMode）与 `0x34AA/0x34AB/0x34BE` 锁存位的写入者是否全为确定性事件 | 待实测 |

### 5.3 计数

- 证据等级：**[实证] 19 · [推演] 4 · [待实测] 2**
- 判定：**VIOLATION 5 · RISK 8 · SAFE 12**（合计 25，见 risk_table）
- 产品向坑：**9**（P1–P9）

---

## 6. 只读引用

- `docs/re/trigger_runtime_deep_dive.md`（状态机/PRNG/生命周期）
- `docs/re/trigger_system_manifest.md`（145 动作 / 49+ 事件派发表）
- `docs/re/trigger_tag_abi_deep_dive.md`（ABI）
- `docs/re/net_sync_checksum.md`（RNG/帧 CRC/红线）
- `docs/re/house_team_ai_update.md`（AITrigger/TeamDelayTimer）
- `docs/re/clock_frame_loop.md`（帧时钟）
- `docs/re/mp_autodowngrade_spec.md`（`0xA8D5F8` 门控）
- `ra2forge/triggers.py`、`ra2forge/maplib.py`、`ra2forge/builder.py`（只读）
