# 联机确定性基础设施逆向档案（帧同步 / RNG / Checksum / 命令队列 / 存档）

> 逆向对象：`ra2youli/gamemd.exe`（YR 1.001，ImageBase `0x400000`，文件偏移 = VA − `0x400000`）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 目标：为「哪些优化可动、哪些会破坏联机」提供**地址级红线**。
> 方法：Capstone 5.x 全文扫描 + `out/reverse/symbols.json` vfunc 命名 + YRpp 头交叉对照 + `.rdata` 串实锤。
> 工作产物：`out/re_work/net_sync/`（`analyze_net_sync.py` / `analyze_pass2.py` / `rng_classify.py` / `dump_kind_table.py` / `dump_jumptabs.py` 与各 `fn_*/event_*/xrefs_*` 文本）。
> 约束：只读逆向；不改总档案 `REVERSE_ENGINEERING_AND_PATCHES.md` 与任何源码/dll。
> 前置文档：`docs/re/clock_frame_loop.md`（帧链与 `CurrentFrame++`）、`docs/re/targeting_spatial.md`（枚举序敏感）、`docs/re/pathfinding_locomotion.md`、`docs/re/house_team_ai_update.md`。

---

## 0. 结论速览

| # | 命题 | 结论 | 热度/风险 |
|---|---|---|---|
| 1 | **联机模型 = 确定性锁步（lockstep）** | 所有客户端在**同一逻辑帧**执行**同一条排好序的命令队列**；本地输入只进「待发队列」，经网络回环后才生效。任何「本地立即生效」的优化都会分叉 | 核心 |
| 2 | **每帧同步入口** | `MainLogicFrame 0x55D360` 尾部 `0x55DE40 call 0x647260`（唯一调用点）。职责：收包 → 校验 CRC → 执行到期命令 → 算帧 CRC → 发包/补发 FrameSync | **真热** |
| 3 | **命令执行器** | `0x4C6CB0`（6192B）：`Kind-1` 跳表 `@0x4C8114`，Kind `1..0x2E`。`0x64C380` 在 CRC 比对通过后、且 `event.Timestamp == CurrentFrame` 时调用它 | **真热 / 红线** |
| 4 | **两套 CRC，勿混** | ① **帧 CRC** `0x64DAB0`→`CurrentFrameCRC@0xAC51FC`（量化坐标+RNG，轻量 desync 探针）② **对象 CRC** `AbstractClass::CalculateChecksum`（v[13]）→`Checksummer`（全字段 CRC-32，只进 SYNC*.TXT 诊断档） | 红线 |
| 5 | **desync 检出** | `0x64C6E2–0x64C6F2`：`LatestFramesCRC[(Timestamp−Delay)&0xFF]` vs `event.Checksum`；不等 → `0x64CC61` 写 `SYNC*.TXT` + 弹 `TXT_OUT_OF_SYNC`/`TXT_STOP` | — |
| 6 | **RNG 两套** | 局内唯一：`ScenarioClass::Random`（`ScenarioInstance+0x218`，`0xA8B230` 指向的实例）；局外/RMG：`Randomizer::Global@0x886B88`。**每帧 `0x650A90` 固定吃掉 1 次局内 Random**（进帧 CRC） | **红线** |
| 7 | **乱序/丢包** | 不重排逻辑帧；靠 **FrameSync 心跳 + FrameSendRate 对齐 + 等待**。`0x64C380` 对 `Timestamp > CurrentFrame` 的事件**挂起**，到帧才执行；丢的是包不是帧——`Resending framesync` / `Sent FrameSync only packet` 串可证 | — |
| 8 | **存档范围 = 全量逻辑状态** | `0x67D300`（Save）/ `0x67CEF0`（Load），版本魔数 `Savegame_Magic@0x83D560 = 0x2B898`；约 **35 个子系统块**（`0x67FDF0..0x680EF0` 每 0x80 一个）+ `Save_Sides 0x6805F0`。`CurrentFrame` 在读档路径被整体回填 | 红线 |
| 9 | **纯绘制可改** | Blit / RLE / dirty-rect / 迷雾**显示** / 雷达点 / FPS 档位 / `Sleep` 节拍：不进帧 CRC、不进 CalculateChecksum、不进存档 → **可动** | 可动 |
| 10 | **空间哈希/时间片** | 只允许改「候选枚举的**实现**」，必须保持 **弹出顺序 = 原枚举序**，且重建时机是 `CurrentFrame` 的纯函数（`frame % N == 0`）。禁止渲染帧/墙钟/指针哈希参与 | 见 §6 |

---

## 1. 同步管线（命令收集 → 排序 → 执行）

### 1.1 帧链中的位置

```
GameRunner 0x48CCC0
  ├─ 0x69BAB0                          SessionClass 状态推进
  ├─ call 0x55D360  MainLogicFrame     ← 每逻辑帧
  │     ├─ …世界/对象/触发器/寻路/AI 更新…
  │     ├─ 0x55DE40  call 0x647260     ★联机同步驱动（唯一调用点）★
  │     │     ├─ 0x64DAB0  Compute_Frame_CRC → CurrentFrameCRC
  │     │     ├─ LatestFramesCRC[CurrentFrame & 0xFF] = CurrentFrameCRC
  │     │     ├─ 0x650A90  从 ScenarioClass::Random 抽数（同步消费）
  │     │     ├─ 收包：0x64A0C0 Receive（解压/解码进 Queue ring）
  │     │     ├─ 0x64C380  Validate+Execute（CRC 比对 + 到期命令 → 0x4C6CB0）
  │     │     ├─ 0x64BDD0  Send/Build（打包本地 QueuedEvents）
  │     │     ├─ 0x649CA0  Build_FrameInfo（Timestamp/Checksum=帧CRC）
  │     │     └─ 必要时 0x64DEA0 / 0x6516F0  写 SYNC*.TXT
  │     └─ 0x55DE73–0x55DE81  CurrentFrame++   ★唯一 inc★
  ├─ call 0x55CFD0                     会话/每 1024 帧维护（test eax,0x3FF）
  ├─ call 0x48C8B0                     ★本地 UI→命令入队（下一帧才发）★
  └─ call 0x55CFD0                     再次
```

**关键时序事实**（`0x48CE8A–0x48CEA8`）：
1. `MainLogicFrame`（含同步驱动 + `CurrentFrame++`）**先于** UI 命令收集；
2. `0x48C8B0` 收集的本地命令进 `QueuedEvents`，**本帧不执行**，随下一帧的 Send 发出，再随回环在**未来某帧**（`Timestamp == CurrentFrame`）执行；
3. 这就是原版固有的 **≥1 帧指令延迟**。任何「点击立即建造/立即开火」的优化都会造成本地与远端分叉。

### 1.2 三张队列（勿混）

| 队列 | 全局 | 容量/步长 | 角色 |
|---|---|---|---|
| **本地待发** `QueuedEvents` | `0xA802D4`（YRpp `Networking.h`） | 128 × 111B，索引 `LastEventIndex@0xA802C8` / `NextPacketIndex@0xA802D0`，时间戳 `0xA83A54` | UI/逻辑产生的原始 `NetworkEvent`，尚未排序 |
| **网络命令环** `Queue`（源文件名 `D:\ra2mdpost\Queue.CPP`） | 基址 `0x8B4204`，计数 `0x8B41F8`，读游标 `0x8B41FC` | 0x4000 × 111B（`index & 0x3FFF`） | 收包解码后的**已排序**命令流；`0x64C380` 按 `Timestamp` 消费 |
| **MegaMission 暂存** | `0xA83EDC`，计数 `0xA83ED0`（上限 0x100）/ 游标 `0xA83ED8` | 111B | Kind=4/5（MegaMission/F）专用二级缓冲 |

`NetworkEvent` 布局（YRpp `NetworkEvents.h`，`#pragma pack(1)`，**111 = 0x6F 字节**）：

| 偏移 | 类型 | 字段 | 用途 |
|---|---|---|---|
| +0 | u8 | `Kind` | 见 §1.4 分发表 |
| +1 | u8 | `Unused` | 位 0 常被 `0x64C56B` 测试（「已执行/已调整」标志） |
| +2 | i8 | `HouseIndex` | 玩家槽位 |
| +3 | u32 | `Timestamp` | **逻辑帧号**（排序键） |
| +7 | u32 | `Checksum` | FrameInfo 专用：发送方帧 CRC |
| +0xB | u16 | `CommandCount` | |
| +0xD | u8 | `Delay` | FrameInfo 的 CRC 帧偏移（见 §4.3） |
| +0xE | u8[0x61] | `ExtraData` | 载荷（NetID 打包坐标/类型索引等） |

### 1.3 排序与到期语义（`0x64C380`）

```
for each event e in Queue ring:
    if e.Kind == FrameInfo(0x1C):
        idx = (e.Timestamp - e.Delay) & 0xFF
        if LatestFramesCRC[idx] != e.Checksum:  → DESYNC (0x64CC61)
        continue                    # FrameInfo 不进游戏逻辑
    if e.Kind == Exit(0x13):  ...  # 标记 house+0x248=1，做退出/踢人
    if e.Kind in {MegaMission(4), MegaMissionF(5)}:  转入 0xA83EDC 二级缓冲
    # 时间戳调整（0x64C3A3–0x64C4C6）：
    #   对 Kind==0x1C/0x13 之外的事件，若 Timestamp 落在 [0xA8B1F8, 0xA8B1DC)
    #   则把 Timestamp 重写为 0xA8B1DC（延迟补偿/迟到命令追帧）
    if e.Timestamp > CurrentFrame:  挂起，跳过（不重排、不丢弃）
    if e.Timestamp == CurrentFrame: 调 0x4C6CB0 执行
    # 额外：0x64C6A5 用 e.Delay 校验 <0x100；0x64C685 有「时间戳落后」的丢弃路径
```

- **乱序**：事件按 `Timestamp` 排队等待，**不改变逻辑帧推进**。迟到命令若仍能赶上（在追帧窗口内）会被改时间戳后补执行；否则被日志/丢弃。
- **丢包**：不重传逻辑命令本身（命令在可靠通道里由 Conn 层负责），丢的是同步包时靠 `FrameSync`（Kind=0x19）心跳对齐：`.rdata` 串 `Resending framesync` / `Sent FrameSync only packet` / `Received FRAMESYNC packet from %s. Frame = %d` / `Frame sync stalls: %d`。
- **踢人**：`Kicking player %d from the game - Frame is %d`；Exit 事件处理里 `0x5E2BE0` 判定后可能 `0x6C8820/0x6C6F50` 走结束流程。
- **延迟微调**：Kind `0x24 LatencyFudge` → `0x4C7F35`（串 `Executing LATENCYFUDGE event. Frame is %d`）；`FrameSendRate` 存 `0xA8B554`（`FrameSendRate=%d` / `FrameSendRate is %d`）。

### 1.4 命令分发表（`0x4C6CB0`，跳表 `0x4C8114`）

> `mov al,[esi]; dec eax; cmp eax,0x2d; ja default; jmp [eax*4 + 0x4C8114]`
> 索引 = Kind−1（Empty=0 不进表）。完整表：`out/re_work/net_sync/event_dispatch_table.txt`。

| Kind | 名 | 处理器 | 是否改逻辑状态 |
|---|---|---|---|
| 0x01/0x02 | PowerOn/Off | `0x4C6CF0` / `0x4C6D4D` | **是**（建筑电力） |
| 0x03 | Ally | `0x4C6DEE` | **是**（`HouseClass` 0x4F9A50/0x4F9F70/0x4F9B50） |
| 0x04/0x05 | MegaMission/F | `0x4C71CA` | **是**（编队任务，最大载荷） |
| 0x06 | Idle | `0x4C74CB` | **是** |
| 0x07 | Scatter | `0x4C7859` | **是** |
| 0x08 | Destruct | `0x4C7BDF` | **是** |
| 0x09 | Deploy | `0x4C76BC` | **是** |
| 0x0A | Detonate | `0x4C7823` | **是** |
| 0x0B | Place | `0x4C70E1` | **是**（放置建筑/单位） |
| 0x0C/0x0D | Options/GameSpeed | `0x4C7929` / `0x4C794B` | **是**（对所有端生效） |
| 0x0E–0x11 | Produce/Suspend/Abandon/Primary | `0x4C711B/140/163/18C` | **是**（生产队列） |
| 0x12 | SpecialPlace | `0x4C78D6` | **是** |
| 0x13 | Exit | `0x4C7903` + `0x64C7B6` | **是**（退出/踢人） |
| 0x14 | Animation | `0x4C6FDE` | **是** |
| 0x15/0x16/0x17 | Repair/Sell/SellCell | `0x4C6ED2/6F12/6FB3` | **是** |
| 0x18 | Special（超武） | `0x4C6E48` | **是** |
| 0x19 | FrameSync | **no-op**（`0x4C8109`） | 否（传输层） |
| 0x1A | Message | no-op | 否（聊天） |
| 0x1B | ResponseTime | `0x4C79FF` | 否（计时） |
| 0x1C | FrameInfo | **no-op**（CRC 在 `0x64C380` 处理） | 否 |
| 0x1D | SaveGame | `0x4C7A14` → `0x67CEF0` | **是**（触发存档） |
| 0x1E | Archive | `0x4C6DAA` | **是**（NetID→Techno 归档） |
| 0x1F/0x23 | AddPlayer/RemovePlayer | `0x4C7B4D` / `0x4C7B73` | **是** |
| 0x20/0x21/0x26 | Timing/ProcessTime/PacketTiming | `0x4C800C/80B1` / no-op | 否 |
| 0x22 | PageUser | `0x4C80F6` | 否 |
| 0x24 | LatencyFudge | `0x4C7F35` | 否（延迟调节） |
| 0x25 | MegaFrameInfo | no-op | 否 |
| 0x27–0x29 | AboutToExit/FallbackHost/AddressChange | `0x4C7CF5/7BF1/7C12` | 会话级 |
| 0x2A–0x2C | PlanConnect/Commit/NodeDelete | `0x4C6CDE` | **是**（计划模式） |
| 0x2D | AllCheer | `0x4C6E2E` | 否（表现） |
| 0x2E | AbandonAll | `0x4C7188` | **是** |

**命令产生端**（`FillEvent_*`，YRpp `NetworkEvents.h` 地址）：

| 函数 | 地址 | 主要调用方 |
|---|---|---|
| `FillEvent_ProduceAbandonSuspend` | `0x4C6970` | 侧边栏生产 `0x6AA600` / `SelectClass@StripClass 0x6AAD00` |
| `FillEvent_SellCell` | `0x4C6650` | `DisplayClass::v[48] 0x4AB9B0` |
| `FillEvent_Noopt` | `0x4C66C0` | UI 泵 `0x48C8B0`、`0x55CFD0`、若干开关类 |
| `FillEvent_PlayerBased` | `0x4C6720` | Options/GameSpeed/Ally |
| `FillEvent_Waypoints` | `0x4C6780` | `BuildingClass::v[81]`、MegaMission 路径 |
| `FillEvent_Place` / `SWPlace` | `0x4C6AE0` / `0x4C6B60` | `DisplayClass::v[48]`、侧边栏 |
| `CreateClickedMissionEvent` | `0x646E90` | `BuildingClass::v[222]`（点击命令，YRpp 注释） |

---

## 2. RNG（随机数）

### 2.1 算法（`Randomizer`，YRpp `Randomizer.h` 已核对）

布局（`sizeof = 0x4 + 0x4 + 0x4 + 0xFA*4 = 0x3F4`）：

| 偏移 | 字段 | 说明 |
|---|---|---|
| +0 | `bool unknown_00` | **非 0 则 `Random()` 恒返回 0**（禁用开关） |
| +4 | `Next1` | 表游标 A |
| +8 | `Next2` | 表游标 B，初值 `0x67`（103） |
| +0xC | `Table[0xFA]` | 250 × DWORD |

**`Random@0x65C780`**（滞后 Fibonacci / 双游标异或）：

```
if (flag) return 0;
r = Table[Next1] ^ Table[Next2];
Table[Next1] = r;
Next1 = (Next1+1) % 250;  Next2 = (Next2+1) % 250;
return r;
```

**`RandomRanged@0x65C7E0`**：取 `[min,max]`（自动交换），按最高位做**拒绝采样**（`test edi, 1<<bit` 循环），消耗的 `Random()` 次数**依赖值域与抽样结果**——即「一次 RandomRanged 可能吃掉 1..N 次 Random」。

**`ctor@0x65C6D0(seed)`**：`Next1=0; Next2=0x67`；用 `.rdata` 常量
`A@0x839644 = {0xBAA96887, 0x1E17D32C, 0x03BCDC3C, 0x0F33D1B2}`、
`B@0x839690 = {0x48AAD7E4, 0x4B0F3B58, 0xE874F0C3, 0x6955C5A6}`
做 4 轮混合 × 250 次填表。种子同则表同，序列同。

### 2.2 两套实例（**绝不可互换**）

| 实例 | 地址 | 用途 | ctor 调用点 |
|---|---|---|---|
| **局内** `ScenarioClass::Random` | `*(0xA8B230) + 0x218` | **一切影响对局结果的随机**：残骸/箱子/暴击/散开/AI/生成单位… | `ScenarioClass` ctor `0x6832C0`（由 `GameStart 0x52BA60` 调） |
| **局外** `Randomizer::Global` | `0x886B88` | RMG 随机地图、音频延迟、UI 花絮、WOL 等 | `0x40D9F7`、`0x52FC20`×4、`0x58B070`、`0x598960` 等 9 处 |

`.rdata` 实锤：`Setup Rematch: Random Seed = %d`、`Creating %d units - Random seed is %08x`、`Random Number:%d`（SYNC 报告里打印 RNG 值）、`Scen->IsRandom = true/false`。

### 2.3 谁在吃 RNG（静态分类，682 处调用）

| 目标 | 归属 | 调用数（约） |
|---|---|---|
| `RandomRanged 0x65C7E0` | 局内（`+0x218` / `ScenarioInstance`） | **335** |
| `RandomRanged` | Global `0x886B88` | 78 |
| `Random 0x65C780` | 局内 | **89** |
| `Random 0x65C780` | Global | 18 |
| `Random 0x65C780` | MapSeedClass::v[8] `0x597FE0` 等地图生成 | 151（RMG，局外） |
| ctor | 各处初始化 | 9 |

局内高频消费者（`out/re_work/net_sync/rng_consumers.txt`）：`AnimClass::v[23]`、`AircraftClass::v[23/138/139/143/151]`、`InfantryClass::v[99]`、`UnitClass::v[99]`、`BuildingClass::v[91/148/315]`、`TechnoClass::v[91]`、`FootClass::v[23]`、`BombClass::v[8]`、`DropPodLocomotionClass::v[16]`、`0x58BDC0/0x58C2C0/0x58C6F0/0x58C800`（地图/触发器簇）、`0x53A140/0x53A300`、`0x6886B0`（开局单位生成）等。

**每帧固定消费点**：`0x650A90`（挂在 `Compute_Frame_CRC 0x64DAB0` 末尾）——

```
if (!ExtraSyncInfo(0xB04880))
    0xAFA26C = ScenarioClass::Random.Random();     // 吃 1 次，结果进侧信道
else
    sync_snap[i] = { CurrentFrameCRC, Random(), CurrentFrame, per-house names… }
```

> **红线**：任何新增的「局内随机」必须走 `ScenarioClass::Random`，且**消费次数与顺序**在所有客户端逐帧一致。用 `Randomizer::Global`、`rand()`、`GetTickCount`、指针地址哈希、渲染帧号做局内随机 = 必炸联机。
> **RandomRanged 的拒绝采样**使「值域」也成为同步契约——改 `RandomRanged(min,max)` 的参数就是改随机流。

---

## 3. Checksum（两套，勿混）

### 3.1 `Checksummer`（对象级，CRC-32）

YRpp `Checksummer.h` 与镜像一致：

- 表：`CRC_Table @ 0x81F7B4`，标准 **CRC-32**（`[0]=0, [1]=0x77073096, …`，反射多项式 0xEDB88320）；
- 核心：`Process(data,len,init)` = 逐字节 `ret = T[b ^ (ret&0xFF)] ^ (ret>>8)`，首尾取反（`~init` / `~ret`）；
- `Add` 按 4 字节块调 `Process`，尾部进 `Bytes[4]` 缓冲，`GetValue/Commit` 时 `Fill()` 补齐再投影（原版 `Fill` 缺边界检查会越界写，`SafeChecksummer` 多 1 字节 padding 就是为此）；
- 实现簇：`0x4A1C10`（bulk `Add(void*,size_t)`）/ `0x4A1CA0`、`0x4A1D50`、`0x4A1D70`、`0x4A1D90`（标量重载）/ `0x4A1DE0`（Process 循环）/ `0x4A1FB0`（GetValue/Commit）。

**进档口 = `AbstractClass::CalculateChecksum(Checksummer&) const`**（YRpp `AbstractClass.h:104`，vtable 槽 v[13]）：

| 类 | v[13] 地址 | Checksummer 调用 |
|---|---|---|
| AbstractClass | `0x410410` | `Add` 少量 |
| ObjectClass | `0x5F6250` | 多次 |
| FootClass | `0x4DBAD0` | 多次 |
| TechnoClass | `0x70C270` | `0x4A1C10`×1 + `0x4A1CA0`×15 + `0x4A1D50`×18 + … + 基类 `RadioClass::v[13] 0x65AB10`；**引用 `CurrentFrame`×4**（Timer 字段） |
| Building/Infantry/Unit/Aircraft/House/Team/Trigger/Tag/Script/… | 各类 v[13] | **331 处** `0x4A1CA0` 直呼，全部在 `*Class::v[13]` 内 |

`SYNC*.TXT` 报告（`0x64DEA0` / `0x6516F0`）按类打印全量 CRC，`.rdata` 类目串实锤覆盖范围（`0x837FAA–0x83883A`）：

> Em Pulse / Tiberium / Sides / Tube / Building Light / Light Source / Overlay Type / Smudge Type / Waypoint Path / Bullet / Particle System(Type) / Particle(Type) / Weapon / Warhead / VoxelAnim(Type) / Factory / **Event** / Action / Trigger(Type) / Tag(Type) / Script(Type) / Team(Type) / Task Force / Anim(Type) / Aircraft(Type) / Building(Type) / Infantry(Type) / Unit(Type) / House(Type)

即：**几乎全部逻辑对象与类型对象的字段都会进 CalculateChecksum**。它**不**用于逐帧联机比对（太重），而用于 desync 后的诊断归因。

### 3.2 帧 CRC（联机比对用，轻量）

`Compute_Frame_CRC @ 0x64DAB0`（被 `0x647260` 与 `0x6475F0` 调用）：

```
CurrentFrameCRC = 0
for each Infantry i:            // 数组 0xA83DEC / 计数 0xA83DF8
    mix( quant(i+0x9C..0xA4 坐标 ÷10,  0x4C93D0(i+0x388) 量化 8bit) )
for each Unit:                  // 0x8B410C / 0x8B4118
    mix( 同上  +  0x4C93D0(obj+0x3A0) )
for each Building:              // 0xA8EB44 / 0xA8EB50
    mix( 同上 )
for each Aircraft:              // 0xA8022C / 0xA80238
    mix( byte at obj+0x241 )
for each in 0x8A0370/-0xC 簇:   // 疑似 Terrain/Overlay/Anim 补充
    mix( vcall[0](obj) )
for each 0x8A03E8 簇:  mix(...)
mix( ScenarioClass::Random.Random() )     // 经 0x650A90
// 混合式：acc = acc*2 + sign(acc) + term   （0x64DB33–0x64DB4A）
```

> **[task-11 最小勘误标记 · v1.5.35]**（不改写上方伪码正文）`Compute_Frame_CRC` 第 4 个循环的数组字段语义已定谳 [实证]：
> `0xA8022C` = **Items**、`0xA80238` = **Count**（`Count − Items = 0xC`）；写侧 `0x67D4C2 = 8B 15 38 02 A8 00`（读 Count）、`0x67D4EC = 8B 15 2C 02 A8 00`（读 Items 基址）；
> 同族三元组口径：`0xA8ECA4` = Items / `0xA8ECA8` = Capacity / `0xA8ECB0` = Count（证据 `0x6F085C`：`89 0D B0 EC A8 00` → `8B 0D A4 EC A8 00` → `89 34 81`）；
> **未闭环**：该数组的**类归属**（Aircraft vs House）仍二义，保持 `[待复核]`。详见 `docs/re/savegame_block_manifest.md §8.4-bis`。

坐标量化：`0x66666667` 乘法 = **÷10**，再拼 `(Y/10)<<16 | q8 | (X/10)` 一类 32 位项。因此：

- 帧 CRC **对「格内亚像素/微小浮点漂移」不敏感**，但对**格坐标/朝向字节/RNG 值**敏感；
- 它**不是**全状态哈希——纯表现层（绘制、迷雾显示、动画播放头）不在内；
- `CurrentFrame` 本身不直接进 CRC（但 RNG 与位置隐含帧序）。

存储：`LatestFramesCRC[256] @ 0xB04474`，索引 `CurrentFrame & 0xFF`（`0x64732F–0x647334`）。

### 3.3 desync 检出与报告

**比对点**（`0x64C6E2–0x64C6F2`，在 `0x64C380` 内）：

```
idx = (event.Timestamp - event.Delay) & 0xFF
local = LatestFramesCRC[idx]
if (local != event.Checksum) goto DESYNC@0x64CC61
```

发送端（`0x649CA0 Build_FrameInfo`）：`event.Kind=0x1C; event.Timestamp=…; event.Checksum=CurrentFrameCRC; event.HouseIndex=…; event.Delay=…`。

**DESYNC 处理 `0x64CC61`**：

1. 若 `ExtraSyncInfo@0xB04880`（`MultiplayerSyncCommandClass::v[8] 0x537AF0` 切换，串 `Extra sync info ON/OFF`）：
   循环 0x100 次调 `0x6516F0` → 每事件一份 `SYNC%01d_%03d.TXT`；
2. 否则调 `0x64DEA0` → 单份 `SYNC%01d.TXT`（内容：`Frame: %d` / `CRC[%d]=%x` / `Random Number:%d` / `Frames: %d` / `FrameSendRate: %d` / 各类 `*** XXX CRCs ***` 明细）；
3. 再 `0x734E60` 取 `TXT_OUT_OF_SYNC` / `TXT_STOP` 文本，`0x734E60` UI 弹出；`0xA8DAB4++` 计数。

**包级 CRC**（与游戏 CRC 无关）：`Serial packet failed CRC check`、`Error in Winsock packet CRC`——是传输层校验，坏了只导致丢包/重传，不直接判 desync。

---

## 4. 存档 / 读档

### 4.1 入口与魔数

| 角色 | 地址 | 说明 |
|---|---|---|
| 版本魔数 | `Game::Savegame_Magic @ 0x83D560` | 当前值 **`0x2B898`**；`LoadOptionsClass::v[4] 0x559ED0` 与 `0x67CEF0` 校验 |
| 存档主函数 | `0x67D300` | 4416B，顺序调用约 35 个子系统 Save |
| 读档/装载 | `0x67CEF0` | 校验魔数后调 `0x680F70..0x6812E0` 一串 Load（与 Save 一一对应） |
| `Game::Save_Sides` | `0x6805F0`（YRpp `Unsorted.h`） | 由 `0x67D300` 调；被 `0x67D300` 的唯一外部调用者 `0x67E0AF` 间接覆盖 |
| 联机触发 | `NetworkEvent` Kind `0x1D SaveGame` → `0x4C7A14` → `0x67CEF0` | 对局内保存是**命令**，全体客户端同帧执行 |

### 4.2 序列化范围

`0x67D300` 的 Save 块序列（`0x67FDF0, 0x67FE70, …, 0x680EF0`，步长 `0x80`，共约 35 块）+ 外围：

- `0x6607D0`、`0x674730`、`0x67F7E0`、`0x6805F0`(Sides)、`0x689310`；
- 每块内部大量 `[ebx+disp]` 字段直写（`0x67D42A` 被引用 **92 次**，是字段打包热点）。

结合 CalculateChecksum 类目与 `CurrentFrame` 的写点（`out/re_work/clock_frame/currentframe_writes.txt`），**进档的全局/准全局**至少包括：

| 状态 | 证据 |
|---|---|
| `CurrentFrame` | 读档回填点：`0x5BB20C`（`0x5BAC60` 装载簇）、`0x5E550F`、`0x686765`、`0x79758C`；清零点 `0x5B7329`、`0x5E747C`、`0x795234` |
| `ScenarioClass`（含 **`Random` 整个 0x3F4 字节**、UniqueID、Elapsed/Pause/Mission/Shroud/Fog/Ice/Ambient 各 Timer、全局/局部变量表、光照目标） | `ScenarioClass::Load` 系；`Random` 是成员必进档 |
| 全部对象数组：Infantry/Units/Buildings/Aircraft/Terrain/Overlay/Smudge/Bullet/Anim/Particle… | 各 `*Class::IPersistStream::Save/Load`；CalculateChecksum 同覆盖 |
| House（资金、电力、科技、生产、AI 触发器状态、`Team/Script/Trigger/Tag` 链） | `HouseClass` + `Save_Sides` |
| Map/Cell（通行、矿、桥、tube、shroud 数据） | Map/Cell 序列化块 |
| 命令队列与会话 | `Queue` ring、`QueuedEvents`、`SessionClass`、`0xA8B238` 状态 |
| 计时器一律是 `CurrentFrame` 相对量 | `TimerStruct {StartTime, Duration}` + `CurrentFrame` 比较（寻路/触发器/动画文档已证） |

**不进档**（表现层）：`Clock::Now` 墙钟、`FPSCounter`、dirty-rect 队列、音频播放头、`LatestFramesCRC` 历史（可重建）、渲染插值、`Sleep` 节拍、`0x4068E0` 日志桩。

### 4.3 读档与联机

- 读档把 `CurrentFrame` 与 `Random` 状态整体还原——**同档位读档后应能继续锁步**；
- 但 `LatestFramesCRC` 是环形近史，读档后旧 CRC 不可比；`0xA8E30C`（帧阈值，见 `0x64733B`）控制何时开始比对/写报告；
- 联机存档（Kind=0x1D）本身是同步命令：**所有端同帧触发各自的 `0x67CEF0`**，若序列化实现不一致会直接分叉。

---

## 5. 红线表（地址级）

> 图例：**禁改** = 改了必破坏联机 bit 级一致；**慎改** = 可改但必须保持确定性契约；**可动** = 不进同步契约。

### 5.1 必须 bit 级一致（禁改语义/顺序/次数）

| 域 | 地址/符号 | 为什么 | 允许的优化形态 |
|---|---|---|---|
| **逻辑帧号** | `CurrentFrame@0xA8ED84`；唯一 inc `0x55DE73–0x55DE81` | 所有 Timer/触发器/寻路延迟/AI 轮询的时基；也是存档字段 | 不改增量语义；不可并行化 `MainLogicFrame` 内的顺序 |
| **命令队列序** | `Queue@0x8B4204` + `0x64C380` 消费序；`QueuedEvents@0xA802D4` 入队序 | 锁步的「同一命令流」；排序键 = `Timestamp`，同帧内按 ring 下标 | 可改 ring 实现（容量/内存），**不可改同帧执行序** |
| **命令执行器** | `0x4C6CB0` 跳表 `0x4C8114` 与各 handler | 直接改状态 | 可把 handler 内部实现换成等价快版，**副作用与 RNG 消耗必须逐位相同** |
| **RNG** | `ScenarioClass::Random`（`*(0xA8B230)+0x218`）；`Random 0x65C780` / `RandomRanged 0x65C7E0`；每帧 `0x650A90` | 随机流是同步契约；次数/顺序/值域都算 | 不可插拔新调用；不可改 `RandomRanged` 参数；不可用 Global/墙钟/rand |
| **帧 CRC** | `0x64DAB0`、`CurrentFrameCRC@0xAC51FC`、`LatestFramesCRC@0xB04474`、比对 `0x64C6E2` | desync 判据本身 | 不可改混合式/量化除数（÷10、>>7）；否则全员假 desync 或漏报 |
| **CalculateChecksum** | 全部 `*Class::v[13]` + `Checksummer 0x4A1C10` 簇 | 存档一致性与 SYNC 诊断归因；字段增减=改存档格式 | 只能**追加**新字段到新版本魔数；不可重排已有字段 |
| **寻路** | `MapClass::Cost 0x583180` / `CanEnterCell 0x5840C0` / `Passability 0x56D230`；`FootClass` 寻路；`PathDelayTimer` 用 `CurrentFrame` | 路径不同 → 位置不同 → 帧 CRC 不同 | 可加缓存，但缓存命中/未命中必须同帧同结果；键必须是逻辑态 |
| **寻敌** | `Greatest_Threat 0x6F8DF0` 三路枚举；`SelectAutoTarget 0x6FB080`；空间桶 `0x887888` | **枚举序敏感**（同分保留先到者，`targeting_spatial.md` §6） | 见 §6 |
| **生产/建造** | Kind 0x0E–0x11 handler；`FactoryClass`；`HouseClass::CanBuild` | 出兵序列影响战局 | 队列算法可提速，顺序不可变 |
| **AI** | `AITriggerArray`/`TeamTypeArray`/`HouseArray` 遍历序；`ConditionMet` 短路序；`Weight_Current` 浮点序（`house_team_ai_update.md` §全局禁改） | 同权重优先级 | 只允许「跳过整帧」式降频，且跳过条件是 `CurrentFrame` 纯函数 |
| **伤害/武器** | `Warhead/Weapon` 展开；暴击/幸存 RNG；`TechnoClass::ReceiveDamage` 一带 | 直接改血量/死亡时机 | 数值公式禁动；可动纯特效 |
| **触发器/脚本** | `TriggerClass`/`ScriptClass`/`TeamClass` 步进序 | 顺序=优先级 | 不可改遍历序 |
| **Timer 语义** | `TimerStruct` 与 `CurrentFrame` 的比较/重置（`0x75AF80` 等） | 全是帧相对量 | 不可换成墙钟 |
| **存档布局** | `0x67D300`/`0x67CEF0` 块序；魔数 `0x83D560` | 跨版本/跨端可读性 | 追加字段必须 bump 魔数 `0x2B898` |

### 5.2 慎改（保持确定性契约即可）

| 项 | 地址 | 契约 |
|---|---|---|
| 空间哈希/时间片 | `0x887888` 桶、`0x412B40`/`0x4137A0` | 弹出序 = 原枚举序；重建 = `frame % N == 0`（见 §6） |
| 寻路缓存 | PathFinder 簇 | 失效必须是逻辑事件（挡路/开火）驱动，不能 TTL 墙钟 |
| AI 节流 | `0x55D360` 内 `CurrentFrame % 8/100` 分支 | 降频可以；**跳过 vs 执行的判定**必须全员一致 |
| 命令批处理/合并 | Send 路径 `0x64BDD0`/`0x649CA0` | 合并后 `Timestamp` 语义与执行序不变 |
| `RandomRanged` 实现 | `0x65C7E0` | 可换更快拒绝采样，但**输出序列必须逐次相同**（含消耗次数） |
| MegaMission 二级缓冲 | `0xA83EDC` | 可改容量，顺序不可变 |

### 5.3 可动（纯表现，不进同步契约）

| 项 | 证据 |
|---|---|
| **Blit / RLE / NonRLE**（`rle_blit_family.md`、`nonrle_blit_and_named_hotspots.md`、`blitter_microkernel_deep_dive.md`） | 纯像素，无状态回写 |
| **dirty-rect**（`dirty_rect_deep_dive.md`、`dirty_rect_l4.md`） | 只影响重绘范围；`cell+0x5C` 去重用 `CurrentFrame` 但只读 |
| **迷雾/黑幕显示**（`visibility_gap_spysat.md` 的可见性**展示**层） | 注意：可见性**判定**本身影响寻敌！只动绘制不动 `Is可见` 查询 |
| **雷达小点**（`radar_minimap_dots.md`） | 绘制 |
| **音频**（`audio_engine_deep_dive.md`、`audio_input_hotspots.md`） | 用 `Clock::Now` 墙钟，不进 RNG/CRC |
| **FPS/Detail 档位** `0x55AF60`、`Sleep(10)` 节拍、`timeBeginPeriod` | `clock_frame_loop.md`：与 `CurrentFrame` 解耦 |
| **FX/绘制链**（`fx_draw_chain.md`） | 粒子表现若不改 `ParticleSystemClass` 逻辑状态则安全；**注意** Particle 类进 CalculateChecksum 与存档——只动绘制参数层 |
| **UI 控件、鼠标、侧边栏滚动、字体、分辨率** | 无逻辑回写 |
| **日志桩 `0x4068E0`** | 1 字节 `ret`，nop/换遥测不影响语义（`clock_frame_loop.md` §2） |

---

## 6. 空间哈希 / 时间片如何避免改枚举序

（承接 `targeting_spatial.md` §6「必须保持的行为」，此处只补联机视角）

1. **弹出序 = 原序**：`Greatest_Threat` 三路（桶 `0x887888` → 螺旋 Cell 链 → 数组）用 `>` 严格大于择优，同分保留**先被枚举**者。任何哈希桶必须复刻「桶序 → 桶内索引 → swap-with-last 弹出」的同一序列；做不到就**不要用哈希替换枚举**，只做**预过滤短接**（短接条件 = 原函数「找不到」语义的逐位超集，且短接前后返回值相同）。
2. **重建时机必须是 `CurrentFrame` 的纯函数**：`if (CurrentFrame % N == 0) Rebuild();`。禁用渲染帧、`Clock::Now`、`timeGetTime`、线程调度、指针哈希。`house_team_ai_update.md` 已给范例：轮转用 `CurrentFrame % 3` 而非本地计数器。
3. **跨帧缓存要写进同步契约**：若缓存「上帧结果」，所有端必须在同一帧、以同一输入失效。推荐「跳过整帧」而非「复用旧结果」；脏标记在 `RegisterGain/Loss`、`TransactMoney`、SW 充能完成等**逻辑事件**处强制置位。
4. **时间片（分帧更新）**：允许把 `0x55D360` 内某段昂贵扫描拆成 `k` 帧轮询，但必须满足：
   - 分片规则 = `(CurrentFrame + index) % k`（确定性）；
   - **不改变「本帧哪些对象被考虑」对命令执行的影响**——若某对象本帧未扫到而导致未开火/未寻路，则所有端都未扫到（同规则）即安全；若只有一端提前扫到 = desync。
   - 与帧 CRC 的耦合：位置一旦变化就会进 `0x64DAB0`；分片导致的「晚一帧开火」会让双方晚得一致 → CRC 仍相等。**分片不会被 CRC 抓到，但不一致的分片会**。
5. **枚举序自检**：打补丁后跑回放对拍，把 `(this, ret, frame)` 落日志与未打补丁对比（`targeting_spatial.md` §6 已建议）；联机场景再加 `LatestFramesCRC` 逐帧对拍。
6. **不要动 `TargetFlags` 位重映射**（`0x6F7CA0` 内 `[esp+0x14]` 的 `0x8042` 等）——按位测试，「整理」位定义会改分支。

---

## 7. 未决问题

1. **`0x4C93D0`**（帧 CRC 取值 helper，对 `obj+0x388` / `obj+0x3A0`）的字段语义未逐字段命名——疑似「当前速度/朝向/血量档」，需对照 `TechnoClass` 布局确认量化前的物理量。
2. **`0x64DAB0` 尾部两个簇** `0x8A0370/-0xC` 与 `0x8A03E8` 的对象类型（Terrain? Overlay? Anim?）未确认；影响「哪些对象位置会进帧 CRC」的完整清单。
3. **`0xA8E30C`**（`0x64733B`：`CurrentFrame >= 此值` 才走 CRC 报告/比对分支）的写入者未找到——疑似「开始比对的帧阈值」或「desync怀凝帧」，需查 `0x6475F0`/`0x652230` 一带。
4. **`event.Timestamp` 与 `Delay` 的精确换算**（`0x649CA0` 两条路径：`((CurrentFrame+ecx-1)/FrameSendRate)*FrameSendRate` 与 `CurrentFrame+ecx`）中 `ecx` 参数来源（本机延迟估计？`0xA8B554`？）未逐指令确认。
5. **追帧/迟到命令的时间戳重写窗口** `0xA8B1F8..0xA8B1DC`（`0x64C3CC–0x64C3D8`）的确切含义（延迟补偿上下界？）未命名。
6. **`0x64A0C0` 收包解压**（串 `Receive packet uncompressed into %d commmands`）的压缩格式与序号/ACK 机制未展开——决定「丢包重传」在 Conn 层如何保证命令不丢不重。
7. **35 个存档块**（`0x67FDF0..0x680EF0`）与 35 个装载块（`0x680F70..0x6812E0`）的**一一对应名表**未逐个命名（需对每块 prologue 的字段引用反推）。
8. **`0xB04874/0xB04878/0xB04884/0xB0488C`** 一族（`0x6475F0`/`0x648710`/`0x64AD10` 引用）的会话/同步控制块布局未完整还原。
9. **`MPCooperative::v[43] 0x5C46E0`**（`Setup Rematch: Random Seed = %d`）与合作模式特有同步（`0x5E7460` 清 `CurrentFrame`）的关系——合作任务脚本是否走同一条锁步。
10. **单机 vs 联机**下 `0x647260` 早退路径（`0xA8D5F8` 位 2/位 4）：单机是否完全跳过 CRC 与 Queue 消费（若是，单机优化可更激进，但必须仍保持可联机行为）。
11. **`FrameSync`（0x19）/`MegaFrameInfo`（0x25）** 在 `0x64A0C0/0x64BDD0` 的具体封包格式与 `LatestFramesCRC` 的交换频率（每帧？每 `FrameSendRate` 帧？）。
12. **CalculateChecksum 是否在非诊断路径被调用**（例如存档前自检）——目前只见于 `SYNC*.TXT` 与 v[13] 自身；若有隐藏调用点，则改字段会更早炸。

---

## 8. 附：关键地址速查

| 地址 | 名 | 角色 |
|---|---|---|
| `0xA8ED84` | `CurrentFrame` | 逻辑帧号，唯一 inc `0x55DE81` |
| `0x55D360` | `MainLogicFrame` | 每逻辑帧；`0x55DE40` 调同步驱动 |
| `0x48CCC0` | `GameRunner` | 外环；`0x48CE8A` 调 MainLogicFrame，`0x48CE9C` 调 UI 泵 |
| `0x647260` | `NetFrameSync` | 联机同步驱动（唯一被 `0x55DE40` 调） |
| `0x64DAB0` | `Compute_Frame_CRC` | 帧 CRC |
| `0xAC51FC` | `CurrentFrameCRC` | 当前帧 CRC |
| `0xB04474` | `LatestFramesCRC[256]` | 近史 CRC 环 |
| `0x64C380` | `Queue_ValidateExecute` | CRC 比对 + 到期执行 |
| `0x4C6CB0` | `NetworkEvent::Execute` | Kind 跳表 `0x4C8114` |
| `0x649CA0` | `Build_FrameInfo` | 发帧 CRC |
| `0x64A0C0` | `Receive_Packet` | 收包解码 |
| `0x64BDD0` | `Build_SendPacket` | 发包 |
| `0x64DEA0` / `0x6516F0` | `SyncReport` / `SyncDump` | `SYNC*.TXT` |
| `0x8B4204` / `0x8B41F8` / `0x8B41FC` | `Queue` ring | 网络命令环（111B × 0x4000） |
| `0xA802D4` / `0xA802C8` / `0xA802D0` | `QueuedEvents` | 本地待发（128 × 111B） |
| `0x65C6D0` / `0x65C780` / `0x65C7E0` | `Randomizer` ctor / `Random` / `RandomRanged` | |
| `0x886B88` | `Randomizer::Global` | 局外 |
| `*(0xA8B230)+0x218` | `ScenarioClass::Random` | **局内** |
| `0x650A90` | `SyncSnapshot` | 每帧抽 1 次局内 RNG |
| `0x81F7B4` | `CRC_Table` | CRC-32 |
| `0x4A1C10` 簇 | `Checksummer` | 对象 CRC |
| `*::v[13]` | `CalculateChecksum` | 进档口 |
| `0x67D300` / `0x67CEF0` | Save / Load | |
| `0x83D560` | `Savegame_Magic` | `0x2B898` |
| `0x837DE8` / `0x837DF8` | `TXT_OUT_OF_SYNC` / `TXT_STOP` | desync UI |
| `0xB04880` | `ExtraSyncInfo` | `0x537AF0` 切换 |
| `0xA8B554` | `FrameSendRate` | |
| `0xA8D5F8` | 联机会话标志（位 2/位 4） | `0x647260` 入口测试 |
| `0x887888` | 全局空间桶枚举器 | 寻敌路 A，见 `targeting_spatial.md` |

---

## 9. 事件填充序（place / swplace / anim / waypoints / playerbased / sellcell / produce）

> 证据源：`out/re_work/net_sync/event_fill_*.txt`（Capstone 全文）+ `YRpp/NetworkEvents.h` 签名 + `event_dispatch_table.txt`（跳表 `0x4C8114`）。
> 约定：`NetworkEvent` 布局见 §1.2（`#pragma pack(1)`，111B）。`FillEvent_*` 为 **`this`=`NetworkEvent*` 的 `__thiscall`**（YRpp `JMP_THIS`），栈参从 `arg1` 起。
> 读栈注意：多数 Fill 入口先 `call 0x4068E0`（`DebugLogStub`）且 **`add esp, N` 在读参之后**——反汇编里的 `[esp+disp]` 必须按「含日志临时压栈」还原，下文已按此折算到 `argN`。

### 9.0 总规律（全部 Fill 共用，地址级）

| 序 | 动作 | 典型指令 | 说明 |
|---|---|---|---|
| 0 | 入口日志 | `push 0x820BF0; push kind_name_table[0x82091C + (eventKind&0xFF)*4]; call 0x4068E0` | **`eventKind` 参数本身**须已是合法小枚举（供名字表下标）；不写事件体 |
| 1 | 校验 `arg1`（PlayerNumber / house） | `test eax,eax; jl err`（`arg1` 有符号 ≥0） | **必须最先**；失败走错误支 |
| 2 | 写 `HouseIndex`（`+2`） | `mov byte [esi+2], al` | 成功支：`arg1&0xFF` |
| 3 | 写 `Kind`（`+0`） | `mov byte [esi], bl`（`bl`=`eventKind`） | **必须在 HouseIndex 之后**；错误支会覆盖为 0 |
| 4 | 写载荷（`+7` 起） | `mov [esi+7/0xB/0xF/…], …` | 各 Fill 不同，见下表 |
| 5 | **末写** `Timestamp`（`+3`） | `mov [esi+3], CurrentFrame@0xA8ED84` | **成功/错误支都最后写**；`0xA8ED84` 直引为证 |
| E | 错误支 | `HouseIndex=0xFF; Kind=0; Timestamp=CurrentFrame` | 例：`0x4C6B49–0x4C6B5B`（Place）、`0x4C6701–0x4C6714`（Noopt） |

**顺序依赖（结论）**：

1. **`HouseIndex(+2)` 必须先于 `Kind(+0)` 写入**——`arg1` 的 `jl` 门控在前，错误支靠覆盖 `Kind=0` 把事件打成 Empty；若先写 Kind 再失败，错误支虽能改回，但任何「Kind 非 0 即有效」的旁路读取会踩半成品。
2. **`Timestamp(+3)` 必须最后写**——它是 `0x64C380` 的排序/到期键；先写 Timestamp 会让事件提前变为「可到期」，而载荷未齐。
3. 载荷字段之间除下列标注外**无强制互序**（同帧单线程填充）；但 **`loc`/指针参数的解引用（`[eax]`/`[eax+2]`）必须在指针仍存活的填充栈帧内完成**，禁止先存指针、延后解引用。

### 9.1 Place — `FillEvent_Place 0x4C6AE0`（Kind 参数化，典型 `0x0B` → handler `0x4C70E1`）

- YRpp：`FillEvent_Place(int a2, NetworkEvents eventKind, int a4, int a5, int a6, CellStruct *loc)`，`ret 0x18`（6 栈参）。
- 反汇编：`out/re_work/net_sync/event_fill_place.txt`（50 行全文）。

| 序 | 字段 | 写入指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C6B14  mov [esi+2], al` | `a2`（`[esp+0x14]` 日志后窗，= arg1） |
| 2 | `+0xB` dword | `0x4C6B1B  mov [esi+0xb], eax` | `a5`（arg4） |
| 3 | `Kind +0` | `0x4C6B22  mov [esi], bl` | `eventKind`（arg2） |
| 4 | `+7` dword | `0x4C6B24  mov [esi+7], edx` | `a4`（arg3） |
| 5 | `+0xF` dword | `0x4C6B27  mov [esi+0xf], ecx` | `a6`（arg5） |
| 6 | `+0x13` word | `0x4C6B2D  mov [esi+0x13], dx` | `loc->X`（`0x4C6B2A  mov dx,[eax]`，`eax`=arg6） |
| 7 | `+0x15` word | `0x4C6B35  mov [esi+0x15], ax` | `loc->Y`（`0x4C6B31  mov ax,[eax+2]`） |
| 8 | `Timestamp +3` | `0x4C6B3F  mov [esi+3], ecx` | `CurrentFrame@0xA8ED84`（`0x4C6B39`） |

- 错误支：`0x4C6B49  HouseIndex=0xFF` → `0x4C6B4D  Kind=0` → `0x4C6B58  Timestamp=CurrentFrame`。
- **顺序依赖**：`a2≥0` 门控 → HouseIndex →（+0xB）→ Kind → 载荷 → loc 解引用字 → **Timestamp**。`+0xB` 在 Kind 前是实际序，非契约强制。
- 主要调用方：`DisplayClass::v[48] 0x4AB9B0`、侧边栏（§1.4）。

### 9.2 SWPlace — `FillEvent_SWPlace 0x4C6B60`（Kind 参数化，典型 `0x12 SpecialPlace` → `0x4C78D6`；亦可能 `0x18`）

- YRpp：`FillEvent_SWPlace(int PlayerNumber, NetworkEvents eventKind, int swTypeIdx, CellStruct *loc)`，`ret 0x10`（4 栈参）。
- 反汇编：`event_fill_swplace.txt`。文件内含**两个填充体**（`0x4C6B60` 与 `0x4C6BE0`，中间 nop 对齐）。

**体 A `0x4C6B60`（Cell 拆双 word）**：

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C6B90` | `PlayerNumber`（arg1） |
| 2 | `Kind +0` | `0x4C6B97` | `eventKind`（arg2） |
| 3 | `+7` dword | `0x4C6B99  mov [esi+7], edx` | `swTypeIdx`（arg3） |
| 4 | `+0xB` word | `0x4C6B9F  mov [esi+0xb], cx` | `loc->X`（`0x4C6B9C`） |
| 5 | `+0xD` word | `0x4C6BA7  mov [esi+0xd], dx` | `loc->Y`（`0x4C6BA3`） |
| 6 | `Timestamp +3` | `0x4C6BB0` | `CurrentFrame`（`0x4C6BAB`） |

- 错误支：`0x4C6BBA–0x4C6BC9`（`0xFF` / `Kind=0` / `Timestamp`）。
- **顺序依赖**：同 9.0；`swTypeIdx`（+7）与 `loc` 字无互序，但都在 Timestamp 前。

**体 B `0x4C6BE0`（YRpp 未单列，相邻填充体；`ret 0x10`）**：

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C6C10` | arg1 |
| 2 | `Kind +0` | `0x4C6C17` | `eventKind`（arg2） |
| 3 | `+7` dword | `0x4C6C19` | arg3 |
| 4 | `+0xB` dword | `0x4C6C1C` | arg4（**整 dword**，非拆 word） |
| 5 | `Timestamp +3` | `0x4C6C25` | `CurrentFrame`（`0x4C6C1F`） |

- 证据序号：`event_fill_swplace.txt:63–96`。与体 A 的差异仅在载荷打包（dword vs word×2）。**是否为 SWPlace 的 naval/bridge 变体待实证**。

### 9.3 Animation — `FillEvent_Animation 0x4C6800`（**Kind 硬编码 `0x14`** → handler `0x4C6FDE`）

- YRpp：`FillEvent_Animation(int PlayerNumber, NetworkEvents eventKind, int a4, int a5)`，`ret 0x10`。
- 反汇编：`event_fill_anim.txt`。**注意：`eventKind` 参数不写入 `Kind` 字段**，`Kind` 固定 `0x14`（`0x4C6823  mov byte [esi], 0x14`）。

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C681C` | `PlayerNumber`（arg1，`jl` 门控 `0x4C6816`） |
| 2 | `Kind +0` | `0x4C6823  mov byte [esi], 0x14` | **立即数** |
| 3 | `+7` dword | `0x4C6826  mov [esi+7], eax` | `PlayerNumber`（arg1，与 HouseIndex 同源） |
| 4 | `+0xB` dword | `0x4C682D  mov [esi+0xb], ecx` | `eventKind` 参数（arg2，**进载荷不进 Kind**） |
| 5 | `+0xF` dword | `0x4C6832  mov [esi+0xf], edx` | `*(int*)a4`（`0x4C6830  mov edx,[eax]`，`eax`=arg3） |
| 6 | `+0x13` dword | `0x4C6838  mov [esi+0x13], eax` | `*(int*)(a4+4)`（`0x4C6835`） |
| 7 | `Timestamp +3` | `0x4C6841` | `CurrentFrame`（`0x4C683B`） |

- **顺序依赖**：HouseIndex 门控 → Kind(常量) → 载荷（含 `a4` 解引用）→ Timestamp。`a5`（arg4）在本体**未被读取**——YRpp 签名第 4 参疑似冗余/变体用，**待实证**。
- YRpp 把 `a4` 标 `int`，汇编按**指针解引用**（2×dword）——**以汇编为准**（与 `targeting_spatial.md` §1.4 同类签名偏差）。

### 9.4 Waypoints — `FillEvent_Waypoints 0x4C6780`（Kind 参数化：MegaMission 路径 / `BuildingClass::v[81]`）

- YRpp：`FillEvent_Waypoints(int PlayerNumber, NetworkEvents eventKind, int a4, char a5, int a6, char a7)`，`ret 0x18`（6 栈参）。
- 反汇编：`event_fill_waypoints.txt`。

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C67B0` | `PlayerNumber`（arg1） |
| 2 | `Kind +0` | `0x4C67BA  mov [esi], bl` | `eventKind`（arg2） |
| 3 | `+7` dword | `0x4C67BC  mov [edx], eax`（`edx=esi+7`） | `a4`（arg3） |
| 4 | `+0xB` byte | `0x4C67C2  mov [edx+4], cl` | `a5`（arg4，char） |
| 5 | `+0xC` dword | `0x4C67CC  mov [esi+0xc], eax` | `a6`（arg5） |
| 6 | `+0x10` byte | `0x4C67D1  mov [edx+4], cl`（`edx=esi+0xc`） | `a7`（arg6，char） |
| 7 | `Timestamp +3` | `0x4C67DA` | `CurrentFrame`（`0x4C67D4`） |

- 错误支：`0x4C67E2–0x4C67EE`。
- **顺序依赖**：`+0xB` 字节与 `+0xC` dword **不重叠**（+0xB=1B，+0xC..+0xF）；HouseIndex → Kind → a4/a5/a6/a7 → Timestamp。
- 文件内 `0x4C6800` 起为 Animation 体（共用反汇编窗口），见 9.3。

### 9.5 PlayerBased — `FillEvent_PlayerBased 0x4C6720`（Kind 参数化：`0x0C Options` / `0x0D GameSpeed` / `0x03 Ally`）

- YRpp：`FillEvent_PlayerBased(int a2, NetworkEvents eventKind, int a4)`，`ret 0x0c`。
- 反汇编：`event_fill_playerbased.txt`。**最简三字段填充**。

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C6750` | `a2`（arg1，`jl` 门控 `0x4C674A`） |
| 2 | `Kind +0` | `0x4C6753  mov [esi], bl` | `eventKind`（arg2） |
| 3 | `+7` dword | `0x4C6755  mov [esi+7], edx` | `a4`（arg3） |
| 4 | `Timestamp +3` | `0x4C675D` | `CurrentFrame`（`0x4C6758`） |

- 错误支：`0x4C6767–0x4C6774`。
- **顺序依赖**：仅「HouseIndex 先于 Kind」「Timestamp 最后」；`a4` 无互序。
- Handler 对应：`0x0C→0x4C7929`、`0x0D→0x4C794B`、`0x03→0x4C6DEE`（`event_dispatch_table.txt`）。

### 9.6 SellCell — `FillEvent_SellCell 0x4C6650`（Kind 参数化，典型 `0x17` → handler `0x4C6FB3`）

- YRpp：`FillEvent_SellCell(int dwUnk, NetworkEvents eventKind, CellStruct *Coords)`，`ret 0x0c`。
- 反汇编：`event_fill_sellcell.txt`。

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C667C  mov [esi+2], al` | `dwUnk`（arg1，`jl` 门控 `0x4C667A`；YRpp 名 `dwUnk` 但汇编按 **有符号 house 序号** 用） |
| 2 | `Kind +0` | `0x4C6683  mov [esi], bl` | `eventKind`（arg2） |
| 3 | `+7` word | `0x4C6688  mov [esi+7], dx` | `Coords->X`（`0x4C6685  mov dx,[eax]`） |
| 4 | `+9` word | `0x4C6690  mov [esi+9], ax` | `Coords->Y`（`0x4C668C  mov ax,[eax+2]`） |
| 5 | `Timestamp +3` | `0x4C669A` | `CurrentFrame`（`0x4C6694`） |

- 错误支：`0x4C66A4–0x4C66B1`。
- **顺序依赖**：同 9.0；`Coords` **无空指针检查**（`jl` 只测 arg1），指针无效直接崩——填充前调用方须保证 `Coords` 有效（`DisplayClass::v[48] 0x4AB9B0`）。
- 与 Place 的差别：SellCell 只打包 Cell 双 word 到 `+7/+9`，无 NetID/类型 dword。

### 9.7 Produce 族 — `FillEvent_ProduceAbandonSuspend 0x4C6970`（Kind `0x0E/0x0F/0x10` → `0x4C711B/0x4C7140/0x4C7163`）

- YRpp：`FillEvent_ProduceAbandonSuspend(int PlayerNumber, NetworkEvents eventKind, AbstractType abstractId, int idx, int isNaval)`，`ret 0x14`（5 栈参）。
- 反汇编：`event_fill_produce.txt`（`0x4C6970–0x4C6AE0` 含 **3 个填充体**）。

**体 1 `0x4C6970`（通用 Produce/Abandon/Suspend）**：

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C69A4` | `PlayerNumber`（arg1） |
| 2 | `Kind +0` | `0x4C69AB  mov [esi], bl` | `eventKind`（arg2） |
| 3 | `+7` dword | `0x4C69AD  mov [esi+7], edx` | `abstractId`（arg3） |
| 4 | `+0xB` dword | `0x4C69B0  mov [esi+0xb], eax` | `idx`（arg4） |
| 5 | `+0xF` dword | `0x4C69B3  mov [esi+0xf], ecx` | `isNaval`（arg5） |
| 6 | `Timestamp +3` | `0x4C69BE` | `CurrentFrame`（`0x4C69B6`） |

**体 2 `0x4C69E0`（`ret 0x10`，4 栈参；载荷带 Cell 双 word）**：

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C6A10` | arg1 |
| 2 | `Kind +0` | `0x4C6A17` | `eventKind`（arg2） |
| 3 | `+7` dword | `0x4C6A19` | arg3（`abstractId`） |
| 4 | `+0xB` dword | `0x4C6A1C  mov dword [esi+0xb], 0xFFFFFFFF` | **常量 −1** |
| 5 | `+0xF` dword | `0x4C6A23  mov dword [esi+0xf], 0` | **常量 0** |
| 6 | `+0x13` word | `0x4C6A2D` | `*(word*)arg4`（Cell X） |
| 7 | `+0x15` word | `0x4C6A35` | `*(word*)(arg4+2)`（Cell Y） |
| 8 | `Timestamp +3` | `0x4C6A3E` | `CurrentFrame`（`0x4C6A39`） |

**体 3 `0x4C6A60`（`ret 0x14`，5 栈参）**：

| 序 | 字段 | 指令（VA） | 来源 |
|---|---|---|---|
| 1 | `HouseIndex +2` | `0x4C6A90` | arg1 |
| 2 | `Kind +0` | `0x4C6A97` | `eventKind`（arg2） |
| 3 | `+0xB` dword | `0x4C6A99` | arg4 |
| 4 | `+7` dword | `0x4C6AA0` | arg3 |
| 5 | `+0xF` dword | `0x4C6AA3  = 0` | **常量** |
| 6 | `+0x13` word | `0x4C6AAD` | `*(word*)arg5` |
| 7 | `+0x15` word | `0x4C6AB5` | `*(word*)(arg5+2)` |
| 8 | `Timestamp +3` | `0x4C6ABE` | `CurrentFrame`（`0x4C6AB9`） |

- 错误支：`0x4C69C6/0x4C6A48/0x4C6AC8` 三处同构。
- **顺序依赖**：体 3 中 `+0xB`（arg4）**先于** `+7`（arg3）写入——非契约强制，但说明「载荷互序不可假定对称」；一律以 Timestamp 收尾。
- 体 2/3 与体 1 的 YRpp 对应关系**待实证**（疑似 Suspend/Abandon 或 naval 变体；`+0xB=−1` 像「无二次索引」哨兵）。
- 侧边栏调用方：`0x6AA600` / `StripClass::SelectClass 0x6AAD00`（§1.4）。

### 9.8 Kind ↔ 填充体 ↔ handler 对照（跳表 `0x4C8114`）

| Kind | 名 | 填充体 | handler | 填充体是否绑定 Kind |
|---|---|---|---|---|
| `0x0B` | Place | `0x4C6AE0` | `0x4C70E1` | 否（参数 `eventKind`） |
| `0x12` | SpecialPlace | `0x4C6B60` / `0x4C6BE0` | `0x4C78D6` | 否 |
| `0x14` | Animation | `0x4C6800` | `0x4C6FDE` | **是（硬编码 0x14）** |
| （路径载荷） | MegaMission 路径 | `0x4C6780` | `0x4C71CA`（Kind `0x04/0x05`） | 否 |
| `0x0C/0x0D/0x03` | Options/GameSpeed/Ally | `0x4C6720` | `0x4C7929/0x4C794B/0x4C6DEE` | 否 |
| `0x17` | SellCell | `0x4C6650` | `0x4C6FB3` | 否 |
| `0x0E/0x0F/0x10` | Produce/Suspend/Abandon | `0x4C6970`（+变体 `0x4C69E0/0x4C6A60`） | `0x4C711B/0x4C7140/0x4C7163` | 否 |
| （开关类） | PowerOn/Off 等 | `0x4C66C0 FillEvent_Noopt` | 各 handler | 否 |

> **契约**：调用方传入的 `eventKind` 必须与目标 handler 跳表项一致；填充函数**不校验** Kind 合法性（除 Animation 自锁 `0x14`）。改填充序/字段布局 = 改命令流字节 = 全端分叉。

---

## 10. 「可安全优化 vs 联机红线」结论表（地址级，扩 §5.1–5.3）

> 判定图例：**安全** = 不进同步契约，可独立优化；**条件安全** = 仅当保持「同帧同结果 / 弹出序不变 / RNG 消耗逐次相同」；**禁止** = 改了必分叉（或全员假 desync）。
> 「进帧 CRC `0x64DAB0`」= 字段会参与 `CurrentFrameCRC` 混合；「进 Checksummer」= 进 `*Class::v[13]` / `0x4A1C10` 簇（`SYNC*.TXT` 与存档）。

| # | 改动类型 | 典型地址或符号 | 进帧 CRC `0x64DAB0` | 进 Checksummer | 判定 | 理由（地址级） |
|---|---|---|---|---|---|---|
| 1 | **Blit / RLE / NonRLE** | `rle_blit_family.md` / `blitter_microkernel_deep_dive.md` 像素核 | 否 | 否 | **安全** | 纯像素、无逻辑状态回写；不进 `0x64DAB0` 对象扫描，也不在 CalculateChecksum 类目（§3.1 `0x837FAA–0x83883A`） |
| 2 | **dirty-rect / 重绘范围** | `dirty_rect_deep_dive.md`、`cell+0x5C`、`MarkForRedraw 0x486E70` | 否（`cell+0x5C` 只读 `CurrentFrame`） | 否 | **安全** | 只影响「画哪些格」；`CurrentFrame` 不进 CRC 显式混合（§3.2），dirty 标记不进档（§4.2 不进档清单） |
| 3 | **迷雾/黑幕「显示」** | `visibility_gap_spysat.md` 展示层；绘制链 | 否 | 否 | **条件安全** | **只动绘制**；`IsShrouded 0x487950` / `IsCellShrouded 0x5865E0` / `RevealArea*` 的**判定**影响寻敌与可见性语义 → 动判定即 **禁止**（红线 §3.2） |
| 4 | **音频 / 流** | `audio_engine_deep_dive.md`、`Clock::Now 0x4093B0`、`AudioFrameUpdate 0x406F70` | 否 | 否 | **安全** | 墙钟时间线（`clock_frame_loop.md` §1.3），不吃局内 RNG、不进 CRC/档 |
| 5 | **Sleep / FPS 档位 / timeBeginPeriod** | `Sleep` 节拍、`0x55AF60`、`0x5D5870/80/90`、`0xA8ED80` 跳 Sleep 标志 | 否 | 否 | **安全** | 与 `CurrentFrame` 解耦（`clock_frame_loop.md` §0.5、§1.3）；`0xA8ED80` 只跳过 Sleep 块 |
| 6 | **日志空桩** | `DebugLogStub 0x4068E0`（1672 直呼） | 否 | 否 | **安全** | 1 字节 `ret`；nop/换遥测零语义变化（`clock_frame_loop.md` §2.1） |
| 7 | **UI / 侧边栏 / 分辨率 / 字体** | 各 UI 簇 | 否 | 否 | **安全** | 无逻辑回写；命令仍走 `0x48C8B0` 入队（§1.1 ≥1 帧延迟契约不受 UI 影响） |
| 8 | **雷达小点 / 纯 FX 绘制参数** | `radar_minimap_dots.md`、`fx_draw_chain.md` 绘制层 | 否 | 否 | **条件安全** | Particle/ParticleSystem **逻辑状态**进 CalculateChecksum 与档（§3.1 类目含 Particle System(Type)/Particle(Type)）→ 只许改绘制参数，不许改寿命/位置/Owner 字段 |
| 9 | **寻路缓存** | `MapClass::Cost 0x583180`、`CanEnterCell 0x5840C0`、`Passability 0x56D230`；PathFinder 簇；`PathDelayTimer` | **是**（路径差 → 位置差 → 坐标进 CRC） | 是（Foot/Techno v[13]） | **条件安全** | 缓存键必须是逻辑态；失效由逻辑事件（挡路/开火/`RegisterGain/Loss`）驱动；**命中/未命中同帧同结果**。TTL 墙钟/渲染帧失效 = **禁止** |
| 10 | **Greatest_Threat 空间哈希** | `0x6F8DF0` 三路枚举；桶 `0x887888`；`0x412B40`/`0x4137A0`；`0x6F7CA0` 打分 | **是**（选目标 → 开火/移动 → 位置） | 是 | **条件安全** | 只许改「候选枚举实现」；**弹出序 = 原枚举序**（`>` 择优、同分保留先到者，`targeting_spatial.md` §6）；重建时机 = `CurrentFrame % N == 0` 纯函数。哈希做不到保序就**禁止替换**，只许原语义超集的预过滤短接 |
| 11 | **寻敌调度器节流（SelectAutoTarget）** | `0x6FB010` / `0x6FB080`；`this+0x2FC` 计数、`+0x1FC/+0x204` 定时器 | 间接是 | 间接是 | **条件安全** | L2 8 帧节流作用在调度器（`targeting_spatial.md` §2.3）；跳过判定必须 `CurrentFrame` 纯函数且全员一致；**不许**只在部分端提前跑 `0x6F8DF0` |
| 12 | **生产队列算法** | Kind `0x0E–0x11` handler `0x4C711B/140/163/18C`；`FactoryClass`；`HouseClass::CanBuild` | **是**（出兵时机/位置） | 是 | **条件安全** | 可改队列内部数据结构；**出兵顺序与帧**不可变；不许并行预计算导致某端提前 `Place` |
| 13 | **AI 时间片 / 降频** | `0x55D360` 内 `CurrentFrame % 8/100` 分支；`AITriggerArray`/`TeamTypeArray` 遍历 | **是**（晚一帧决策 → 晚一帧位置） | 是 | **条件安全** | 允许「跳过整帧」；分片规则 `(CurrentFrame + index) % k`；**禁止** `Weight_Current` 浮点归约序变化、`ConditionMet` 短路序变化（`house_team_ai_update.md`） |
| 14 | **RNG 实现** | `Randomizer::Random 0x65C780` / `RandomRanged 0x65C7E0`；局内 `*(0xA8B230)+0x218`；每帧 `0x650A90` | **是**（`0x650A90` 显式 mix） | 是（Timer/各 v[13]） | **禁止改流** | 输出序列与**拒绝采样消耗次数**必须逐次相同；改 `RandomRanged` 值域/参数 = 改随机流。换 `Randomizer::Global 0x886B88`、`rand()`、`GetTickCount`、指针哈希 = **禁止** |
| 15 | **RNG 消费点增减** | 任意新增 `ScenarioClass::Random` 调用 | **是** | 是 | **禁止** | 消费次数/顺序是同步契约（§2.3）；多抽/少抽一次即全员分叉 |
| 16 | **命令序 / 时间戳** | `Queue@0x8B4204` 消费 `0x64C380`；`QueuedEvents@0xA802D4`；`FillEvent_*`（§9）；`Build_Send 0x64BDD0` | 间接是 | 是（Event 类目） | **禁止改序** | 同帧按 ring 下标序执行；`Timestamp` 是排序键。可改 ring 内存/容量，**不可**改同帧执行序、不可「本地立即生效」 |
| 17 | **命令批处理/合并** | `0x64BDD0` / `0x649CA0` | 否（载荷不变则 CRC 不变） | 否 | **条件安全** | 合并后 `Timestamp` 语义与到期执行序不变；不得吞掉/重排命令 |
| 18 | **帧 CRC 量化/混合** | `0x64DAB0`、÷10（`0x66666667`）、`>>7`、`acc = acc*2 + sign(acc) + term`（`0x64DB33–0x64DB4A`） | 本体 | 否 | **禁止** | 判据本身；改除数/混合式 → 假 desync 或漏报（§5.1） |
| 19 | **CalculateChecksum 字段** | 全部 `*Class::v[13]`、`Checksummer 0x4A1C10` 簇 | 否（不进帧 CRC） | 本体 | **禁止重排/删** | 存档格式 + SYNC 归因；只许新魔数追加字段（`Savegame_Magic 0x83D560` bump） |
| 20 | **Timer 语义** | `TimerStruct` vs `CurrentFrame`；`0x75AF80` 等 | 间接是 | 是 | **禁止换墙钟** | 全是帧相对量；墙钟 → 分叉（§5.1） |
| 21 | **存档块序/魔数** | `0x67D300`/`0x67CEF0`、`0x83D560=0x2B898`、35 块 `0x67FDF0..` | 否 | 是 | **禁止重排** | 跨端可读性；追加必须 bump 魔数 |
| 22 | **Z 序 / VXL 先影后体** | `vxl_render_sort.md`；`ZReadWrite` | 否（显示） | 视对象字段 | **条件安全** | 纯绘制可动；若重排影响逻辑命中/遮挡语义则禁（红线 §3.3）。**迷雾正确性优先**（§3.4，含 17:16 修订：静止零重绘须 `0x006DA7D0` 打脏） |
| 23 | **MegaMission 二级缓冲** | `0xA83EDC`（计数 `0xA83ED0`/游标 `0xA83ED8`） | 否 | 是 | **条件安全** | 可改容量；弹出序不可变（§5.2） |
| 24 | **`0x4068E0` 以外的空桩/短路** | 各「可证明无副作用」桩 | 否 | 否 | **条件安全** | 须逐桩证明无状态回写；有 vtable 引用的桩**禁止** nop |

**一句话裁决**：显示、音频、Sleep、UI、日志 = **安全**；寻路缓存 / 空间哈希 / AI 与生产时间片 / 命令批处理 = **条件安全（保序 + `CurrentFrame` 纯函数）**；RNG 流、命令序、帧 CRC 算法、CalculateChecksum 字段、Timer 语义 = **禁止**。

---

## 11. 修复 Hook 点表（desync 早停 / 诊断增强，只写规格）

> 范围：desync 判据 `0x64C6E2`、`SYNC*.TXT` 生成点、帧 CRC `0x64DAB0` 周边。
> **不改 `ra2render/**`**——本节是给实施方的 Hook 规格（插入点 / 伪码 / 开关 / 回滚 / 风险），落地须走单写者轨道。
> 风险分级：**L0** 纯旁路遥测（零语义）· **L1** 诊断增强（只加写日志/文件）· **L2** 早停/控制流（只影响 desync 处理路径）· **L3** 触碰同步契约（本表**禁止**实施）。

### 11.1 判据与生成点地图

| 角色 | 地址 | 现行为 | 证据 |
|---|---|---|---|
| 帧 CRC 计算 | `0x64DAB0` → `CurrentFrameCRC@0xAC51FC`；写 `LatestFramesCRC[256]@0xB04474`（`CurrentFrame & 0xFF`，`0x64732F–0x647334`） | 每逻辑帧由 `0x647260` / `0x6475F0` 调 | §3.2；`fn_64DAB0_framecrc.txt` |
| 同步驱动 | `0x647260`（`0x55DE40` 唯一调） | 收包 → 校验 → 执行 → 算 CRC → 发包 | §1.1 |
| **desync 判据** | `0x64C6E2  mov edx, [esi*4 + 0xB04474]`<br>`0x64C6E9  mov esi, [eax+eax*2 + 0x8B420B]`<br>`0x64C6F0  cmp edx, esi`<br>`0x64C6F2  jne 0x64CC61` | `local=LatestFramesCRC[(Timestamp-Delay)&0xFF]` vs `event.Checksum`；不等 → DESYNC | `fn_64C380_tail.txt:3–9` |
| DESYNC 处理入口 | `0x64CC61` | ExtraSyncInfo 分支 → 写报告 → 弹 UI | §3.3 |
| SYNC 单份 | `0x64DEA0`（串 `0x838EB0 'SYNC%01d.TXT'`） | `Frame:` / `CRC[]` / `Random Number:` / 各类 `*** CRCs ***` | `fn_64DEA0.txt`；`desync_strings.txt:1` |
| SYNC 多份 | `0x6516F0`（串 `0x839194 'SYNC%01d_%03d.TXT'`） | `ExtraSyncInfo@0xB04880` 时循环 0x100 次 | `desync_strings.txt:4`；§3.3 |
| UI 文本 | `0x734E60` 取 `TXT_OUT_OF_SYNC@0x837DE8` / `TXT_STOP@0x837DF8` | 弹窗 | §3.3 |
| Extra 开关 | `MultiplayerSyncCommandClass::v[8] 0x537AF0` → `0xB04880` | 串 `Extra sync info ON/OFF` | §3.3 |
| 报告阈值 | `0xA8E30C`（`0x64733B`：`CurrentFrame >=` 才比对/写报告） | 开局宽限 | §7.3 **写入者待实证** |
| 每帧 RNG 侧信道 | `0x650A90`（`Compute_Frame_CRC` 尾） | 不 Extra 时写 `0xAFA26C=Random()`；Extra 时 `sync_snap[]` | §2.3 |

### 11.2 Hook 规格

| ID | Hook 点 | 目的 | 伪码（规格） | 开关 / 回滚 | 风险 | 备注 |
|---|---|---|---|---|---|---|
| **H-D1** | `0x64C6F2`（`jne 0x64CC61`）**之前** | **desync 早停日志**（不改分支） | `if (cmp_ne) log("DESYNC_PREDICT frame=%u idx=%u local=%08x remote=%08x house=%d ts=%u delay=%u", CurrentFrame, idx, edx, esi, event.HouseIndex, event.Timestamp, event.Delay);` 然后**落入原 `jne`** | ini `SyncEarlyLog=0/1`；Remove 恢复原 6 字节 `0F 85 69 05 00 00` | **L0** | 纯旁路；必须**不改** `edx/esi/eflags` 以外寄存器契约——建议 `pushfd/pushad` 包裹。回滚 = 还原指令字节 |
| **H-D2** | `0x64CC61` 入口（DESYNC 处理器） | **早停增强**：写报告前先落「现场快照」 | `dump_minimal_sync_state(file);` 含 `CurrentFrame`、`CurrentFrameCRC`、`LatestFramesCRC[256]` 环、`Random` 状态指针值、`Queue` 计数/游标、`event` 原文 111B hex；然后 `jmp` 原逻辑 | `SyncSnapshotOnDesync=0/1`；失败则跳过快照仍进原流程 | **L1** | 只追加文件写；不得占用 `SYNC%01d.TXT` 文件名（用 `SYNC_SNAP_%u.bin`） |
| **H-D3** | `0x64DEA0` / `0x6516F0` 尾部 | **SYNC 报告增强** | 追加一节 `EXTRA: path_hash=… / threat_ret=… / ai_slice=…`（仅诊断哈希，**不进 CRC**） | `SyncExtraSection=0/1` | **L1** | 新节必须是**只读派生**，禁止写回游戏对象 |
| **H-D4** | `0x64DAB0` 入口 | 帧 CRC **计时/计数遥测** | `t0=Clock::Now;` 原函数; `t1=Clock::Now;` 统计进 EMA。**不改返回值** | `FrameCrcProfiling=0/1` | **L0** | 全程 `pushfd/pushad`；禁止改变 `0x650A90` 调用次数 |
| **H-D5** | `0x64DAB0` 出口（`0xAC51FC` 写后） | **逐帧 CRC 镜像**（本地 ring dump） | `if (SyncMirrorEnabled) ring[CurrentFrame & 0xFF] = CurrentFrameCRC;`（独立内存，**不碰** `0xB04474`） | `SyncMirror=0/1` | **L0** | 镜像环与 `LatestFramesCRC` 分离；用于双端对拍 |
| **H-D6** | `0x64C380` 命令执行前（`Timestamp==CurrentFrame` 调 `0x4C6CB0` 处） | **命令流镜像** | `log_cmd(CurrentFrame, kind, house, ts, extra_hex);` 再 `call 0x4C6CB0` | `SyncCmdMirror=0/1` | **L0** | 只读事件；禁止改写 `Timestamp/Kind` |
| **H-D7** | `0x649CA0` `Build_FrameInfo` 写 `event.Checksum` 处 | **本地 CRC 发出前记账** | 记录 `(CurrentFrame, CurrentFrameCRC, Delay, HouseIndex)` 到侧信道 | 随 H-D5 开关 | **L0** | 不改写 `Checksum` 字段 |
| **H-D8** | `0x650A90` | **RNG 侧信道对拍** | 记录抽样值与帧号（ExtraSyncInfo 已有 `sync_snap`；无 Extra 时补本地环） | `RngMirror=0/1` | **L0** | **禁止**多抽/少抽 `Random()` |
| **H-D9** | `0x64733B`（`CurrentFrame >= 0xA8E30C`） | **宽限期可观测** | 日志记录阈值触发帧 | 随 H-D1 | **L0** | 阈值本身 **L3 禁改**（写入者未明，§7.3） |
| **H-D10** | `0x64CC61` **跳过 UI 弹窗**（`0x734E60`/`TXT_OUT_OF_SYNC` 前） | **静默早停**（回归测试用） | `if (SyncSilentDesync) { dump; return; }` else 原弹窗 | `SyncSilentDesync=0/1`；默认 0 | **L2** | 改变客户端交互与结束流程；**仅测试镜像**，发行默认关。不得跳过 `0x64DEA0` 报告写盘 |
| **H-D11** | （反例，**禁止实施**）改 `0x64DAB0` 混合式 / 量化 ÷10 / `0x650A90` 抽样次数 / `0x64C6E2` 比较宽度 | — | — | — | **L3 禁止** | 同步契约本体（§10 #18–19） |
| **H-D12** | （反例，**禁止实施**）在 `0x4C6CB0` handler 内「本地先执行、远端后补」 | — | — | — | **L3 禁止** | 破坏锁步（§0.1、§1.1） |

### 11.3 实施约束（规格级）

1. **先影后体**：H-D* 全部是旁路；任何要写游戏内存的「诊断」一律禁止（只许写独立缓冲/文件）。
2. **开关 + 回滚**：每条独立 ini 键；Install/Remove **对称**（沿 v1.5.3 教训：禁止「装了没生效/卸了没还原」）。Remove 必须还原原指令字节并撤销 trampoline。
3. **寄存器契约**：插入点若在 flag 敏感处（尤其 `0x64C6F2` 的 `jne`），必须 `pushfd/pushad` 保存恢复，保证 `edx/esi/eflags` 与原路径一致。
4. **不改 `ra2render/**`**：本表仅规格；落地归渲染/实施轨道，Hook 地址冲突须先过 `HOOK_POINT_MATRIX.md`（Q2）。
5. **与 §6 的耦合**：若同时启用空间哈希/时间片，H-D5/H-D6 镜像对拍是「保序是否被破坏」的**验收探针**——回放双端 `ring[0xB04474]` 与命令镜像必须逐帧一致。
6. **单机路径**：`0x647260` 在 `0xA8D5F8` 位 2/4 早退（§7.10）；H-D* 在单机可关，避免写无意义 SYNC 文件。

---

## 12. 交叉引用索引（本章新增）

| 主题 | 本文 | 对端 |
|---|---|---|
| 逻辑帧 / Sleep / 墙钟解耦 | §10 #4–6、#20 | `docs/re/clock_frame_loop.md` §0.5、§1.2–1.3、§2.1 |
| `CurrentFrame` 唯一 inc / 节拍 | §1.1、§5.1 | `clock_frame_loop.md` §0.4、§1.3 |
| 枚举序敏感 / 空间哈希保序 | §10 #10–11、§6 | `docs/re/targeting_spatial.md` §0、§1.3、§2.3、§6 |
| `Greatest_Threat` 虚表覆盖缺口 | §10 #10 | `targeting_spatial.md` §1.3（inline hook `0x6F8DF0` 优先于逐类 v[241]） |
| 寻路确定性 | §10 #9 | `docs/re/pathfinding_locomotion.md`、`docs/re/pathfinding_deep_dive.md` |
| AI 遍历/浮点序 | §10 #13 | `docs/re/house_team_ai_update.md` |
| 迷雾显示 vs 判定 | §10 #3 | `docs/re/visibility_gap_spysat.md`；红线 §3.2/§3.4（17:16 修订） |
| Blit/dirty/音频可动 | §10 #1–2、#4–5 | `rle_blit_family.md`、`dirty_rect_deep_dive.md`、`audio_engine_deep_dive.md`、`clock_frame_loop.md` |
| 填充序 vs 命令队列 | §9、§10 #16–17 | 本文 §1.2–1.4 |

---

## 13. 冲刺结论（S8 · 联机确定性与门控收口深潜）

> 专项：S8 · 派工 v19 · 2026-09-26  
> 逆向对象：`ra2youli/gamemd.exe`（ImageBase `0x400000`，`.text` 偏移 `0x1000`，文件偏移 `FileOffset = VA - 0x400000`）  
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> 核心任务：① 帧 CRC 尾部簇类型定谳；② 超武/微粒抽样与校验计算流定谳；③ 缺口 G-03/G-04/G-06/G-07/G-09 字节级实证补强。

### 13.1 帧 CRC 尾部簇类型定谳（彻底闭环 §7.2）

在 `Compute_Frame_CRC`（`0x0064DAB0`，FileOffset `0x24DAB0`）中，既有文档标记为疑似未决的尾部地址簇 `0x8A0370/-0xC` 与 `0x8A03E8` 已完成字节级闭环定谳：

1. **`0x8A0360` 为全局图层数组 `LayerClass LayerClass::Objects[5]` [实证]**：
   - 符号与结构：继承链 `LayerClass` → `DynamicVectorClass<ObjectClass*>` → `VectorClass<ObjectClass*>`，单实例步长 `0x18` 字节。
   - 构造点 `0x004A8630`–`0x004A866B`（FileOffset `0x0A8630`）：
     ```assembly
     0x004A8630: mov eax, 0x8a0368        ; eax = &Objects[0].Capacity
     0x004A8635: mov edx, 5               ; 循环 5 次
     0x004A863C: mov [eax-4], ecx         ; Items = NULL (0x8A0364)
     0x004A863F: mov [eax], ecx           ; Capacity = 0 (0x8A0368)
     0x004A8641: mov byte ptr [eax+4], 1  ; IsAllocated = 1
     0x004A8645: mov byte ptr [eax+5], cl ; IsInitialized = 0
     0x004A8648: mov [eax-8], 0x7e192c    ; VectorClass vftable
     0x004A864F: mov [eax-8], 0x7e4f64    ; DynamicVectorClass vftable
     0x004A8656: mov [eax+0xc], 0xa       ; CapacityIncrement = 10
     0x004A865D: mov [eax+8], ecx         ; Count = 0 (0x8A0370)
     0x004A8660: mov [eax-8], 0x7e6060    ; LayerClass vftable! (0x8A0360)
     0x004A8667: add eax, 0x18            ; 步进到下一图层实例
     0x004A866A: dec edx
     0x004A866B: jne 0x4a863c
     0x004A866D: push 0x4a8680            ; 注册 atexit 析构器 (循环递减 sub esi, 0x18)
     ```
   - 5 个图层枚举及其在 `.data` 的绝对内存布局：
     | 图层索引 | 语义名 | 对象基址 | Items 槽位指针 (`+0x04`) | Count 计数指针 (`+0x10`) |
     |---|---|---|---|---|
     | Layer 0 | `Layer::Underground` | `0x008A0360` | `0x008A0364` | `0x008A0370` |
     | Layer 1 | `Layer::Surface` | `0x008A0378` | `0x008A037C` | `0x008A0388` |
     | Layer 2 | `Layer::Ground` | `0x008A0390` | `0x008A0394` | `0x008A03A0` |
     | Layer 3 | `Layer::Air` | `0x008A03A8` | `0x008A03AC` | `0x008A03B8` |
     | Layer 4 | `Layer::Top` | `0x008A03C0` | `0x008A03C4` | `0x008A03D0` |

2. **`0x8A03E8` 为哨兵指针，非独立对象 [实证]**：
   - 在 `Compute_Frame_CRC` `0x0064DCE4`–`0x0064DD92` 中：
     - 初始 `mov ebp, 0x8A0370`（从第 0 个图层的 Count 字段起算）；
     - 每轮图层内对象遍历完毕后 `add ebp, 0x18`；
     - 循环终止条件 `cmp ebp, 0x8A03E8; jl 0x64DCE9`；
     - `0x8A03D0 + 0x18 == 0x8A03E8`，因此 `0x8A03E8` **纯属图层数组 Count 字段的越界哨兵**（`&LayerClass::Objects[5].Count`），绝非独立数据结构。

3. **`0x0087F778` 为 `LogicClass::Instance` [实证]**：
   - 紧随图层循环之后的 `0x0064DD98`–`0x0064DE33`：
     - 初始检查 `mov eax, [0x87F788]`（Count），取缓冲区 `mov edx, [0x87F77C]`（Items）；
     - 初始化点 `0x0040CB80` 实证：基址 `0x0087F778` 写入虚表 `0x007E18FC`，该虚表在 `symbols.json` RTTI 中明确为 `LogicClass`（继承自 `LayerClass`）。
     - 职责：管理注册在逻辑心跳中的对象集合，逐对象调用 `WhatAmI()` 并量化混入帧 CRC。

4. **图层内对象抽样规则 [实证]**：
   - 在图层遍历（`0x0064DD00`）与 Logic 遍历（`0x0064DDB0`）中，调用虚表 `[eax + 0x2C]` 即 `AbstractClass::WhatAmI()`：
     - 若返回 `4`（`RTTI_ANIM`，`AnimClass`），检查 `esi->Type`（`call [ecx+0x10]`），若返回 `-2` 则 `je 0x64DD79` 跳过不参与 CRC；
     - 其余所有对象均在 `0x0064DD1B` 读取 `esi + 0x9C` 处坐标，经 `0x66666667` 乘法（`X / 10` 与 `Y / 10`）量化后，按 `acc = acc*2 + sign(acc) + (type + (Y/10)<<16 + X/10)` 混合入 `CurrentFrameCRC@0xAC51FC`。

---

### 13.2 超武与微粒在校验计算流中的定谳（彻底闭环）

对照 `Compute_Frame_CRC`、`0x64DE75`、`0x64C911`、`0x64CC0A` 与 `SyncReport` 展开全面取证：

| 对象分类 | 是否进帧 CRC `0x64DAB0` | 是否在命令执行点 `0x64C911/CC0A` 算 CRC | 是否进 SYNC 诊断 `0x64DEA0` (v[13]) | 实证依据与结论 |
|---|---|---|---|---|
| **超级武器** (`SuperClass`) | **否** | **否** | **间接** | `SuperClass`（vtable `0x007F3FE8`）直接继承 `AbstractClass`，**非 `ObjectClass` 子类**；无 `+0x9C` 空间坐标，不挂入 5 个 `LayerClass` 或 `LogicClass`，`0x64DAB0` 零访问。`0x64C911/CC0A` 仅执行 `0x4C6CB0` 命令派发（Kind `0x12/0x18`），不产生 CRC。SYNC 诊断中无独立 Super CRC 节，仅作为 `HouseClass` 状态间接存在 |
| **超武类型** (`SuperWeaponTypeClass`) | **否** | **否** | **否** | 继承 `AbstractTypeClass`，纯静态规则数据，不进帧 CRC；SYNC 报告 42 个分节中无此项 |
| **微粒** (`ParticleClass`) | **否** | **否** | **是**（专用节） | 虽继承 `ObjectClass`，但微粒仅存储在专属数组 `0x00A83DC0`（`Count@0xA83DD8`），未被调用 `Add_Object_To_Layer 0x4A9720`，不进图层与 Logic；`0x64DAB0` 全程未遍历 `0xA83DC0`。在 `0x64DEA0`（`0x650300` 循环）中有独立 `*** Particle CRCs ***` 打印并调用 `v[13] 0x62D980` |
| **微粒系统** (`ParticleSystemClass`) | **否** | **否** | **是**（专用节） | 仅存储在专属数组 `0x00A80200`（`Count@0xA80218`），同样不进图层与 Logic，不进帧 CRC。在 `0x64DEA0`（`0x65038D` 循环）中有独立 `*** Particle System CRCs ***` 打印并调用 `v[13] 0x630210` |

> **定谳裁决**：**超级武器与微粒（系统）均 100% 不被抽样进每帧锁步帧 CRC（`Compute_Frame_CRC`）**。微粒只在发生 desync 后的 `SYNC*.TXT` 离线诊断中由 `Checksummer` 扫描，不构成每帧在线锁步的直接比对约束。超武的状态分叉只通过其产生的次生对象（如爆炸产生的 Anim、被摧毁建筑/单位）间接映射入帧 CRC。

---

### 13.3 缺口表 G-03 / G-04 / G-06 / G-07 / G-09 字节级实证补强

根据派工纪律，对 Lead 未裁定的 5 项缺口提供绝对精确的代码位置与指令级实证：

#### G-03 · L2 Threat Retention 无独立门控键
- **位置与指令 [实证]**：
  - 目标点：`TechnoClass::Greatest_Threat` 入口 VA `0x006F8DF0`（FileOffset `0x2F8DF0`）。
  - 原指令（9B）：`83 EC 5C 8B 15 34 EC A8 00`（`sub esp, 0x5c; mov edx, dword ptr [0xa8ec34]`）。
  - 原版在此递增计数器 `0xA8EC34`，并对全图候选进行三路完整枚举打分；
  - `blitter_hooks.cpp:495-502` 打入 `E9` 补丁后，在 `((unitHash + currentFrame) % interval) != 0` 节流帧短路直接 `return pTarget`（读取 `*(pThis + 0x5D4)` 目标指针）。
- **同步风险补强 [推演]**：
  - 目标保持改变了原版“每帧对当前威胁严格大于重新择优”的语义。若战场环境剧变（原目标出射程或出现近距离高危目标），节流端会粘滞原目标，直到放行帧才切换。
  - 当前无独立键控制 Retention，与 `TargetScanInterval` 强耦合。一旦联机对拍发现因目标粘滞导致开火偏差，必须把 `TargetScanInterval` 设为 1 整体回退，无法单关 Retention。
- **实施补强**：增加 `[Logic] EnableThreatRetention=0/1`（联机自动降级 W2 强制 0），解耦寻敌扫描间隔与目标保持逻辑。

#### G-04 · B1/B2 混色桩与 L4 全量刷补丁无条件安装
- **位置与指令 [实证]**：
  - **B1 桩**：VA `0x0047F40F`（FileOffset `0x07F40F`，49B 原字节 `66 8B 08 66 83 F9 7F 75 07 66 33 C9 8A CB EB 1E 8B 54 24 48 81 E1 FF FF 00 00 81 E2 FF 00 00 00 8D 4C 11 81 33 D2 85 C9 0F 9E C2 4A 23 CA 66 89 08`）。
  - **B2 桩**：VA `0x0047F4AE`（FileOffset `0x07F4AE`，51B 原字节 `66 8B 08 66 83 F9 7F 75 09 66 0F B6 D2 66 89 10 EB 21 8B 54 24 48 81 E1 FF FF 00 00 81 E2 FF 00 00 00 8D 4C 11 81 33 D2 85 C9 0F 9E C2 4A 23 CA 66 89 08`）。
  - **L4 视口全量刷**：VA `0x006D3D99`（FileOffset `0x2D3D99`，6B 原字节 `0F 8D 98 00 00 00` `jge 0x006D3E37`）。
  - 安装点 `blitter_hooks.cpp:1307` 将 `0x006D3D99` 强制改写为 `E9 99 00 00 00 90`（`jmp 0x006D3E37; nop`）。
- **风险补强 [实证]**：
  - `InstallCellClassDrawHook` 中上述三处写入没有任何 `if` 条件门控！即使在 ini 中配置 `EnableStarCraftFog=0`、`FadeFogTransition=0`，代码段依然被强行改写；
  - L4 绕过脏矩形跳跃指令 `jge`，迫使每一帧全屏无条件重绘，不仅彻底破坏“关迷雾回到原版纯净基线”的预期，而且与 Q7 脏矩形调优形成永久冲突。
- **实施补强**：在 `InstallCellClassDrawHook` 中建立装卸门控，若 `EnableStarCraftFog=0` 则跳过这三处补丁写入；新增 `[Render] L4DirtyMode=force-full|off`。
> 【W3 勘误 · W3-A6/ISSUE-SECTION-L4DIRTYMODE】改前：[Render] L4DirtyMode；改后：[FogOfWar] L4DirtyMode=force-full；依据：ra2render/blitter_hooks.cpp:757; ra2render/ra2render.ini:251；分级：P0

#### G-06 · S2 与 S3 全局状态写缺乏独立门控
- **位置与指令 [实证]**：
  - **S2 (`ScenarioClass` 标志 `&= ~0x1000`)**：
    - 读取端点 1：VA `0x006D8FCB`（FileOffset `0x2D8FCB`，`8A 84 24 ... test ah, 0x10`）；
    - 读取端点 2：VA `0x006D9630`（FileOffset `0x2D9630`，`test ah, 0x10`）；
    - 原版若 `ah & 0x10`（即位 `0x1000`）非零，则调用 `MapClass::IsCellShrouded 0x5865E0` 并执行绘制剔除；`blitter_hooks.cpp:747` 强行清零该位以旁路原版黑幕剔除。
  - **S3 (`HouseClass + 0x577A` SpySatActive)**：
    - 写入端点：VA `0x00509054`（FileOffset `0x109054`，`mov al, [esi+0x577a]; test al, al; jne ... mov byte ptr [esi+0x577a], 1`，SpySat 展开全图时置 1）；
    - 消费端点：VA `0x0050BD10`（FileOffset `0x10BD10`，`mov al, [ecx+0x577a]; test al, al; jne 0x50bd25; call 0x577ab0`，若为 1 则阻止裂缝产生器重黑视野）；
    - `blitter_hooks.cpp:753` 每逻辑帧强行写入 `*(uint8_t*)(pPlayer + 0x577A) = 0`，推翻原版 SpySat 判定以允许雷达扫视。
- **同步风险补强 [实证]**：
  - `ScenarioClass` 与 `HouseClass` 均为核心同步状态（进存档与网络契约）。在混联对局中，安装 DLL 的客户端强清两处状态，而原版客户端保持置位，将立即造成黑幕遮蔽状态和裂缝产生器遮盖时机的两端分叉。
  - 目前 S2/S3 无独立开关，只要开启任意 fog 键触发 `UpdateVisionGrid` 就会执行。
- **实施补强**：必须建立 `[Multiplayer] MpStateWrites=0` 开关（或随 `EnableSpySatRadarSweep` 联动），在联机非全员同款构建下严禁任何状态写。

#### G-07 · S1 TYPE 补丁无 Remove 还原逻辑
- **位置与指令 [实证]**：
  - `BuildingTypeClass + 0x16A5`：原版 `SpySat` 布尔标志，在 VA `0x00508F88` 读取（`cmp byte ptr [eax + 0x16a5], 0`）；
  - `BuildingTypeClass + 0x16F0`：超武关联索引，在 VA `0x004516B1` 处校验（`cmp dword ptr [eax + 0x16f0], -1`）；
  - `SuperWeaponTypeClass + 0xB0`（RechargeTime 充能帧数）与 `+0xF8`（Range 范围）。
  - `PatchSpySatBuildingTypes`（`blitter_hooks.cpp:597-623`）直接篡改进程全局单例对象的属性。
- **风险补强 [实证]**：
  - 单例对象的规则数据生命周期贯穿进程始终。当前 `RemoveVTableHooks` 或战局结束（`OnGameEnd`）均无还原逻辑。一旦打上补丁，无论用户后续在 ini 关闭开关，还是退出到主菜单切换单人原版战役，内存中间谍卫星类型数据均保持为被篡改状态（无全图揭示能力，变为心灵感应超武），破坏进程内回滚洁净度。
- **实施补强**：在 DLL 中定义静态变量保存原始 4 项数值，在 `RemoveVTableHooks` 及战局清理时严格对称还原。

#### G-09 · `EnableMinimapFog=1` 时 everSeen 记忆不进档
- **位置与指令 [实证]**：
  - `gamemd.exe` 读写档管线：`CellClass::Save 0x00483C10` 与 `CellClass::Load 0x004839F0` 仅序列化原版格位数据（`CellClass + 0x12C` 迷雾标记等）；
  - `ra2render.dll` 的 `s_everSeenGrid` 为 512×512 字节数组（256 KB），位于 DLL 内部私有未初始化段，完全独立于引擎存档流；
  - 关键代码 `blitter_hooks.cpp:714-721`：
    ```cpp
    if (currentFrame < s_lastFrame - 30) {
        memset(s_everSeenGrid, 0, sizeof(s_everSeenGrid));
        ...
    }
    ```
    当读取存档引发逻辑帧倒退时，DLL 显式执行 `memset` 将 `s_everSeenGrid` 全面清零！
- **同步与体验裁定 [实证]**：
  - `s_everSeenGrid` 纯属客户端表现层网格，完全不参与 `0x64DAB0` 帧 CRC，其清零**绝对不会导致联机锁步 desync**；
  - 现象表现为：读档后，先前侦察过的战争迷雾中建筑暗影全部消失，需单位重新侦察方可再次盖章。此属体验/UX 遗留，而非锁步安全违规，定谳为“已知体验限制”，免除联机安全整改阻断。
