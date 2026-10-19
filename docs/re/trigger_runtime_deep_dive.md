# 触发器（Trigger / Tag）运行时语义与联机确定性专章深潜

> **目标二进制**：`ra2youli\gamemd.exe`（官方 1.001，MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x400000`，.text VA `0x401000`，FileOffset = VA − 0x400000）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据分级**：**[实证]** = VA + 文件偏移 + 原始机器码 + Capstone 反汇编，可用 `python tools/audit_bytes.py out/re_work/triggers_deep/claims.txt` 复算；**[推演]** = 由相邻实证按 x86 / MSVC 代码生成惯例推导；**[待实测]** = 需真机运行验证。
> **与前作的边界**：`trigger_system_manifest.md`（89 KB）解决了**事件/动作全表与派发跳表**（"有哪些 kind、跳到哪"）；本专章只解决**运行时语义与确定性**（"什么时候被遍历、按什么顺序、烧不烧随机数、生命周期与存档怎么走"）。
> **只读引用**：`trigger_system_manifest.md`（全表）、`net_sync_checksum.md`（RNG / Checksum / 红线表）、`savegame_block_manifest.md`（存档块）、`clock_frame_loop.md`（帧主循环）、`house_team_ai_update.md`（AITrigger / Team 每帧循环）、`audio_engine_deep_dive.md`（EVA / VocClass）。
> **可机读断言**：`out/re_work/triggers_deep/claims.txt`（**174 条**，`audit_bytes.py` 全 OK）
> **反汇编全量 dump**：`out/re_work/triggers_deep/dumps/`（19 个文件）

---

## 0. 结论速览（6 条硬结论）

| # | 结论 | 等级 |
|---|---|---|
| **C1** | **每逻辑帧遍历触发器的唯一位置**是 `LogicClass` 的自触发轮询器 **`0x55AFB0`**，由 `MainLogicFrame` `0x55D360` 在 **`0x55DC9E` 无条件调用一次/逻辑帧**（全镜像仅此 1 个调用点）。它**不遍历触发器**，而是遍历一个专用向量 `0x8B40C8`（元素 = **TagClass\***），对每个 Tag 依序抛 10 个"自求值/计时器"事件。 | [实证] |
| **C2** | **触发器自身不在任何每帧循环中被遍历**：`TriggerClass::Array`（`0xA8EAE8`）与 `TagClass::Array`（`0xB0E720`）的直引**只有"构造函数追加 / 析构函数摘除"**，没有任何每帧迭代点。触发器是**事件驱动**的：条件求值入口 `TriggerClass::RegisterEvent 0x7264C0` 全镜像**只有 1 个调用点**（`0x6E5414`，在 `TagClass::RaiseEvent` 内）。 | [实证] |
| **C3** | **求值顺序三层全为"插入序"**：① 每帧 Tag 向量 = **下标升序**，该顺序在**任务初始化时按 `TagTypeClass::Array` 下标顺序一次性建立**（`0x684CB7` 段），存档按原序还原；② Tag → Trigger 为**单链表头插**（`TagClass::AddTrigger 0x6E55C0` 是标准 head-insert），故为**创建序的逆序**；③ Trigger → Event/Action 为单链表尾接（按 INI/加载序）。**全链路无任何按指针值排序 / 按地址哈希 / 按 House 重排的指令**。 | [实证] |
| **C4** | **局内 PRNG = `ScenarioClass::Random`（`[0xA8B230]+0x218`）**。整个触发器子系统对该实例的消费点**恰好 4 个函数 / 9 条指令**：① `TriggerClass::ResetTimers 0x726400`（RandomDelay 条件计时器）；② 动作 `0x3A MeteorShower` 内联体（4 次 `Random()`）；③ 动作 `0x62 PlaySoundEffectRandom` 内联体（1 次 `RandomRanged`）；④ `AITrigger 0x6F0AB0` / `0x6F0C9C`（2 次 `RandomRanged`）。**事件判定链 `0x71E940–0x71F700`（62 个 kind 的全部条件逻辑）零 PRNG 消费**。 | [实证] |
| **C5** | **帧 CRC `0x64DAB0` 也会消费一次 `ScenarioClass::Random`**（`0x64DE3F`），并把结果折进 `CurrentFrameCRC`（`0xAC51FC`：`acc = acc*2 + rand`）。CRC **不读取** Random 的 `Table[0xFA]`/`Next1`/`Next2`（该区段无 `[reg+0x218..]` 访存）。因此「RNG 状态是否进 CRC」的准确表述是：**CRC 进的是 RNG 的一次输出值，而不是 RNG 的内部状态**。 | [实证] |
| **C6** | **AITrigger 与普通触发器是两套独立机制**：AITrigger `0x6F0AB0` 不属于 Tag/Trigger 体系、不挂 Tag，由 `HouseClass` AI 簇（`HouseClass::v[23]=0x4F8440`）经 **TeamDelayTimer** 门控调用，判据是"房级 Team 计数 vs 上限"+"`RandomRanged(1,100) <= Probability`"，随后在 `TeamClass::Array` 内按权重挑一支队伍创建；普通触发器由**对象/世界事件**自底向上冒泡驱动。 | [实证]（门控语义 [推演]，见 §5） |

---

## 1. Q1 触发器求值入口与节拍（每逻辑帧在哪里遍历？）

### 1.1 类与实例链（vtable 与静态数组实证）

| 类 | vtable VA | `Size()` | 全局数组（`DynamicVectorClass`） | 数组用途 |
|---|---|---|---|---|
| `TagClass` | `0x7F44E0`（`0x6E4F69: C7 07 E0 44 7F 00`） | `0x38`（`TagClass::GetInstance` 的 `operator new(0x38)`，`0x6E52C5: 6A 38`） | `0xB0E720`（Items `0xB0E724`，Count `0xB0E730`） | **全部** Tag 实例（仅创建/销毁用） |
| `TagClass`（**每帧子集**） | — | — | **`0x8B40C8`（Items `0x8B40CC`，Capacity `0x8B40D0`，Count `0x8B40D8`，增长步长 `0x8B40DC = 0x0A`，vtable `0x7EA5A4`）** | **每帧自触发轮询名单**（本专章核心） |
| `TagClass`（次子集） | — | — | `0x8B41A8`（Items `0x8B41AC`，Count `0x8B41B8`） | `AnyEvent(0x08)` / `ZoneEntryBy(0x18)` 专用名单 |
| `TriggerClass` | `0x7F5858`（`0x725FCE: C7 06 58 58 7F 00`） | `0x48`（`0x726930: B8 48 00 00 00 C3`） | `0xA8EAE8`（Items `0xA8EAEC`，Count `0xA8EAF8`）；另有 `0xB0F670`、`0xB0F708` 两个同类向量 | 全部触发器（仅创建/销毁用）；后两者用于"含线穿越类事件"的快速筛选 |
| `TriggerTypeClass` | `0x7F5904` | — | `0x8B4178` | INI 触发器类型表 |
| `TagTypeClass` | `0x7F45C4` | — | `0xB0E780`（Items `0xB0E784`，Count `0xB0E790`） | INI Tag 类型表 |
| `TEventClass` / `TActionClass` | `0x7F5578` / `0x7F443C` | `0x94`（`0x6E4630`） | —（挂在 `TriggerTypeClass+0xAC/+0xB0` 链表上） | — |

> **布局自证**：`TagClass` 的 `Type@+0x24 / FirstTrigger@+0x28 / InstanceCount@+0x2C / Destroyed@+0x34 / IsExecuting@+0x35` 与 `TriggerClass` 的 `Type@+0x24 / NextTrigger@+0x28 / House@+0x2C / Destroyed@+0x30 / Timer@+0x34(12B) / OccuredEvents@+0x40 / Enabled@+0x44` 由 §7 的 174 条字节断言逐字段钉住（`Size()=0x48` 与 `0x34+12+4+1(+3 pad)=0x48` 算术完全吻合）。

### 1.2 每逻辑帧的唯一遍历器：`LogicClass` 自触发轮询器 `0x55AFB0`

**节拍（beat）**：

```
MainLogicFrame 0x55D360  (每逻辑帧，CurrentFrame++ @ 0x55DE73–0x55DE81)
  …
  0x55DC99  mov ecx, 0x87F778        ; this = LogicClass::Logics（YRpp MapClass.h:149）
  0x55DC9E  call 0x55AFB0            ; ★ 全镜像唯一调用点；位于 0x55DBCD 条件块之后的汇合点 → 无条件
  …
  0x55DE9F  call 0x725C70            ; 延迟析构队列抽干（见 §4.4）
```

- `0x55DBCD: 39 3D 38 B2 A8 00`（`cmp [0xA8B238],edi`，游戏状态）后的条件块在 `0x55DC99` **汇合**，因此轮询器**不受该条件影响**，每逻辑帧必达一次。[实证]
- 轮询器**早于** `CurrentFrame++`（`0x55DE73`）执行，故它抛事件时 `CurrentFrame` 仍是**本帧之前的值**；而 `ResetTimers` 读的是 `[0xA8ED84]`（`CurrentFrame`）——这两点共同决定计时器相位。[实证]

**轮询器主体骨架（`0x55AFB0`–`0x55B1A0`）**：

```
0055AFB0  sub esp,0x28
0055AFB3  mov edx,[0xABCD40]              ; 自触发 pass 计数器
0055AFB9  mov [esp],ecx                   ; this = LogicClass
0055AFBD  mov ecx,[0x8B40D8]              ; Count = 每帧 Tag 向量长度
0055AFC6  inc edx
0055AFCD  mov edi,[0xA8B230]              ; edi = ScenarioClass* Instance
0055AFD3  mov [0xABCD40],edx
0055AFDB  mov [0xA83CDC],eax              ; 复入游标归零（eax=0）
0055AFE0  jle 0x55B17D                    ; Count<=0 → 跳到尾巴
0055AFE6  mov ecx,[0x8B40CC]              ; Items
0055AFEC  mov esi,[ecx+eax*4]             ; esi = TagClass*  ← 下标升序
   … 10 次 TagClass::RaiseEvent（条件表见下） …
0055B164  mov eax,[0xA83CDC] / inc eax / cmp eax,ecx / mov [0xA83CDC],eax / jl 0x55AFE6
```

**10 个每帧抛出的 EventKind（顺序即求值顺序，全部 [实证]）**：

| 序 | EventKind | 名称 | 前置条件（读 `ScenarioClass*` `edi`） | 调用点 VA | 机器码 |
|---|---|---|---|---|---|
| 1 | `0x32` | PickupCrate_any | `[edi+0x34BE] != 0` | `0x55B00A` | `E8 91 A3 18 00` |
| 2 | `0x1B` | GlobalSet | `[edi+0x34AA] != 0` | `0x55B037` | `E8 64 A3 18 00` |
| 3 | `0x1C` | GlobalCleared | 同上 | `0x55B055` | `E8 46 A3 18 00` |
| 4 | `0x24` | LocalSet | 同上 | `0x55B073` | `E8 28 A3 18 00` |
| 5 | `0x25` | LocalCleared | 同上 | `0x55B090` | `E8 0B A3 18 00` |
| 6 | `0x2D` | AmbientLightBelow | `[edi+0x34AB] != 0` | `0x55B0BE` | `E8 DD A2 18 00` |
| 7 | `0x2E` | AmbientLightAbove | 同上 | `0x55B0DC` | `E8 BF A2 18 00` |
| 8 | `0x0D` | ElapsedTime | **无条件** | `0x55B0F5` | `E8 A6 A2 18 00` |
| 9 | `0x33` | RandomDelay | **无条件** | `0x55B10F` | `E8 8C A2 18 00` |
| 10 | `0x0E` | MissionTimerExpired | 任务计时器 `[Scenario+0x11E8]`（`TimerStruct`）到期（`0x55B11E` 起的三路比较） | `0x55B159` | `E8 42 A2 18 00` |

这 10 项与 `TEventClass::GetFlags` 的 **bit 0x10**（"自求值/计时器事件"位，见 §3.1）**逐项一致**：该位集合为 `{0x08, 0x0D, 0x0E, 0x17, 0x1B, 0x1C, 0x24, 0x25, 0x2D, 0x2E, 0x2F, 0x32, 0x33, 0x3C, 0x3D}`，其中 `0x17` 见 §1.5、`0x08/0x2F/0x3C/0x3D` 见 §8 U-5。

**关键控制流语义 [实证]**：每个 `RaiseEvent` 返回后 `test al,al / jne 0x55B15E`——一旦某个事件在**该 Tag 上**产生"至少一个动作被执行"，就**跳过该 Tag 剩余的事件种类**，直接进入下一个 Tag（`0x55B164` 续循环）。**不是**中止整帧遍历。故"同一帧内多个 Tag 各有触发"是允许且必然按向量序发生的。

**每帧事件携带的坐标**：`RaiseEvent(event, pTagOwner=NULL, location=*(CellStruct*)0xABCCD8, forceAllOccured=0, pSource=0)`——`pTagOwner` 传 **NULL**（自求值事件没有宿主对象）。`0xABCCD8` 是全局 `CellStruct`，全镜像直引 11 处（`0x55AEF2/0x55AEF8` 清零写 + 轮询器 10 处读）。[实证]（setter 语义见 §8 U-2）

### 1.3 事件驱动漏斗：`TagClass::RaiseEvent 0x6E53A0`（73 个调用点）

`0x6E53A0` 是**全系统把"世界上发生了什么"送进触发器系统的唯一闸门**，全镜像 73 个直呼点，按函数聚簇如下（完整清单见 `dumps/xrefs_poller_chain.txt`）：

| 簇 | 代表函数 | 调用点数 | 语义 [推演] |
|---|---|---|---|
| 每帧轮询器 | `LogicClass` `0x55AFB0` | **10** | 自求值/计时器事件（§1.2） |
| 步兵 | `InfantryClass::v[99]` `0x519630`（5）、`0x519E7D/0x51A017/0x51A219/0x51A383`（各 1） | 9 | 进入/踩格/拾取/被选中类 |
| 载具 | `UnitClass::v[99]` `0x739EC0`（2）、`UnitClass::v[56]` `0x744720`（3） | 5 | 同上 |
| 飞行器 | `AircraftClass::v[56]/v[57]`（各 5）、`v[247]`（3）、`v[102]`（1）、`v[83]`（1） | 15 | 同上 |
| 建筑 | `BuildingClass::v[99]` `0x6F5090`（1） | 1 | 同上 |
| 队伍 | `TeamClass::v[23]=TeamClass::AI` `0x6E9140`（1）、`0x6EA467`（1） | 2 | `0x17 TeamLeavesMap`（§1.5） |
| 世界/杂项 | `0x4D8916`（7）、`0x5F55EE`（7）、`0x576059`（3）等 | 41 | 伤害/发现/区域/线穿越等 |

`RaiseEvent` 的骨架 [实证]：

```
006E53A0  push ecx
006E53A1  mov al,[0xA8ED6B]            ; ArmageddonMode 全局：置位则整条 RaiseEvent 直接返回 false
006E53AC  mov ebp,ecx
006E53BC  mov al,[ebp+0x35]  test al,al  jne ret0   ; TagClass::IsExecuting 重入保护
006E53C7  mov al,[ebp+0x34]  test al,al  jne ret0   ; TagClass::Destroyed
006E53D2  mov eax,[ebp+0x24] test eax,eax je ret0   ; TagClass::Type == 0
006E53DE  mov esi,[ebp+0x28]                        ; FirstTrigger 链表头
   … 逐个 TriggerClass …
006E53FE  mov edx,[ecx+0x9C]                        ; TagTypeClass::Persistence
006E5408  cmp edx,2 / sete dl                       ; persistent := (Persistence == Persistent)
006E5414  call 0x7264C0                             ; RegisterEvent(event,pObject,forceFire=arg4,persistent,pSource)
006E5419  test al,al  je next
006E5420  mov eax,[edx+0x9C]                        ; 按 Persistence 分派
            0 → 0x6E5465 FireActions + Destroy
            1 → 0x6E5442 (InstanceCount==1 ? FireActions+Destroy : 只置"已发生"位)
            2 → 0x6E5431 FireActions
006E5484  mov esi,[esi+0x28]                        ; NextTrigger
```

### 1.4 求值与执行的**唯一性**（确定性分析的基石）

| 函数 | 直呼调用点数 | 调用点 | 结论 |
|---|---|---|---|
| `TriggerClass::RegisterEvent 0x7264C0` | **1** | `0x6E5414`（`RaiseEvent`） | 条件求值**唯一入口** |
| `TEventClass::HasOccured 0x71E940` | **1** | `0x726540`（`RegisterEvent`） | 62 个条件分支**唯一入口** |
| `TriggerClass::FireActions 0x7265C0` | **5** | `0x6E5439 / 0x6E5450 / 0x6E546D`（`RaiseEvent` 三分支）、`0x6DF119`（动作 `0x16 ForceTrigger` 体内）、`0x6E2AD0`（动作辅助簇 `0x6E25xx`，含 `0x35 EnableTrigger` 邻近体） | 动作执行入口极少，好挂钩 |
| `TActionClass::Execute 0x6DD8B0` | **1** | `0x726605`（`FireActions`） | 145 项动作**唯一入口** |
| `TriggerClass::ResetTimers 0x726400` | **5** | `0x7260E7`（ctor）、`0x7263BB`（NotifyGlobalChanged）、`0x7263EB`（NotifyLocalChanged）、`0x7265A4`（RegisterEvent 尾）、`0x7268F4` | **PRNG 消费点集合**（§3） |
| `TriggerClass::Destroy 0x726720` | **4** | `0x6DF07D`（动作 `0x0C DestroyTrigger`）、`0x6E2A3A`（辅助簇）、`0x6E5457 / 0x6E5474`（`RaiseEvent` Volatile/SemiPersistant 分支） | 销毁入口 |

`RegisterEvent` 内部的求值顺序 [实证]：

```
007264F2  mov edi,[eax+0xAC]         ; edi = TriggerTypeClass::FirstEvent
00726501  mov eax,[esi+0x40]         ; eax = TriggerClass::OccuredEvents（位图）
00726504  mov ebp,1 ; mov ecx,ebx ; shl ebp,cl     ; ebp = 1<<eventIndex（下标 = 链表位次）
0072650D  test ebp,eax ; jne 0x72654F                ; 已持久置位的事件跳过
00726533  call 0x502D30                             ; 由 TriggerType+0xA4(HouseType)→[+0xB4] 解析房指针，写入 Trigger+0x2C
00726540  call 0x71E940                             ; TEventClass::HasOccured  ← 条件
00726549  mov byte [esp+0x13],al  (0)               ; "全部事件已发生"累加器清 0
00726551  call 0x71FA30 ×2 → mov [esi+0x2C],eax     ; 房指针回写
0072656E  call 0x71F950 (GetStateA) → 真则 call 0x71F9C0 (GetStateB) → 真则 or [esi+0x40],ebp
00726585  mov edi,[edi+0x28] ; inc ebx               ; 下一个事件，位次 +1
00726591  mov al,[esp+0x13]                          ; 全部事件是否都已发生
0072659A  mov al,[esp+0x20]  (arg4 persistent) ; je 0x7265A9
007265A4  call 0x726400                              ; ★ ResetTimers（PRNG 点）
```

- **`OccuredEvents` 的位序号 = 事件在链表中的位置**（`ebx` 每轮 `inc`，与 kind 数值无关）。`forceFire`（arg3，`0x7264DA–0x7264E7`）为真时**整段事件求值被短路**（直接跳到 `0x72659A`），相当于"全部事件已发生"。 [实证]
- `FireActions`：`esi = TriggerType+0xB0 (FirstAction)` → `call 0x6DD8B0` → `esi=[esi+0x28]`；任一动作返回真则整体返回真（`0x72660E: B3 01`）。前置门 `[edi+0x44] Enabled==1` 且 `[edi+0x30] Destroyed==0`。 [实证]

> **勘误（对 `trigger_system_manifest.md` §1.1 的门控命名）**：该文写"`TriggerClass+0x44`（已过期）与 `0x30`（已禁用）任一为真则整条跳过"。字节级实读为：`+0x44` 是 **`Enabled`**（`RegisterEvent` 要求 **==1** 才继续：`0x7264C4: 8A 46 44 / 84 C0 / JE ret0`），`+0x30` 是 **`Destroyed`**（要求 **==0**）。构造函数 `0x725FCA: C6 46 44 01` 明确置 1，故 `+0x44` 必为 `Enabled`。**"真则跳过"的判定模式成立，但字段名错位**，以本专章为准。

### 1.5 第二个每帧入口：`TeamClass::AI` 抛 `0x17 TeamLeavesMap`

`0x6E92F3` 与 `0x6EA4B1` 两处**遍历同一个 `0x8B40C8` 向量**（`mov eax,[0x8B40CC]` + `mov ecx,[eax+edi*4]`）并向每个 Tag 抛 `EventKind 0x17`（`push 0x17` 后 `call 0x6E53A0`），`pTagOwner` 同样传 NULL、`location` 取自 `[0xB0E948]`。这两处位于 `TeamClass::v[23]=TeamClass::AI 0x6E9140` 及其邻近函数内。[实证]

> 因此"每帧遍历触发器"的**完整答案**是：**每帧遍历的是"含 bit0x10 事件的 Tag 名单"（两个调用方：`LogicClass` 轮询器 + `TeamClass::AI` 的离队判定）**，而不是触发器对象本身。

---

## 2. Q2 求值顺序与锁步确定性

### 2.1 每帧 Tag 向量的建立顺序（任务初始化 `0x684CB7` 段）

该段从 `TagTypeClass::Array` **下标 0 → Count−1** 单向扫描，按位掩码分三次注册：

```
00684D4E  mov eax,[0xB0E790]        ; Count = TagTypeClass::Array
00684D56  mov edx,[0xB0E784]        ; Items
00684D5C  mov esi,[edx+ebx*4]       ; esi = TagType*（ebx = 下标，升序）
00684D61  call 0x6E61F0             ; TagTypeClass::GetFlags() → BYTE 位掩码
00684D66  test al,4                 ; bit2 → 注册进 0x8B41A8（AnyEvent / ZoneEntryBy）
00684D6C  call 0x6E52A0             ; TagClass::GetInstance（无则 new 0x38 + ctor）
00684DC5  mov [ecx+eax*4],edi       ; Items[Count++] = tag
00684DCF  test al,0x10              ; bit4 → 注册进 ★每帧向量 0x8B40C8
00684DD5  call 0x6E52A0 ; 00684E23 ++Count ; 00684E2F Items[Count] = tag
00684EA7  inc ebx ; cmp ebx,[0xB0E790] ; jl 0x684D56   ; 下标升序闭环
```

**结论 [实证]**：每帧向量的插入序 = **`TagTypeClass` 数组下标升序**，而该数组来自 INI（`TagTypeClass::LoadFromINIList 0x6E5ED0`、`TriggerTypeClass::LoadFromINIList 0x7275D0`）的解析顺序。**没有按 Tag 名排序、没有按 House 分组、没有按指针值排序**。

> 附带游戏契约 [推演]：`GetFlags()` 未置 bit4 的 Tag **在任务初始化时连 TagClass 实例都不会被创建**（`GetInstance` 只在对应位命中时调用）；这类 Tag 只在有对象显式引用它时才被实例化，也因此**永远不进每帧向量**——若它同时含 `RandomDelay/ElapsedTime` 事件，该事件在运行时不会按帧求值。这是地图作者可踩的语义陷阱，建议列入地图制作告警。

**存档还原路径**：`0x67FB8A/0x67FB93/0x67FB9D`（`0x67F9C0` 内的载入段）把向量 **按存档中的原始顺序**重新 `Add`，顺序与存前一致（**不是**按 TagType 下标重排）。[实证]

### 2.2 三层插入语义

| 层 | 数据结构 | 插入操作 | 实证 | 求值序 |
|---|---|---|---|---|
| Tag 名单 | `DynamicVectorClass<TagClass*>` `0x8B40C8` | 尾接：`Items[Count++] = tag` | `0x684E2F: 89 3C 81`；`0x67FB9D` | **下标升序 = 注册序** |
| Tag → Trigger | 单链表 `TagClass+0x28` | **头插**：`p->Next = FirstTrigger; FirstTrigger = p` | `0x6E55C0: 8B 44 24 04 / 8B 51 28 / 89 50 28 / 89 41 28 / C2 04 00` | **创建序的逆序（LIFO）** |
| Trigger → Event / Action | 单链表 `TriggerClass+0x28`（节点为 `TEventClass`/`TActionClass`） | 尾接（`TriggerTypeClass` 挂载时按 INI 序） | `0x7264F2`（事件头）、`0x7265D8`（动作头）、遍历 `0x726610 / 0x726585` | **INI 声明序** |
| 每帧事件种类 | 硬编码指令序列 | 固定 10 步 | §1.2 表 | **固定序 0x32→0x1B→…→0x0E** |

**是否存在按指针排序 / 哈希？** 在 `RaiseEvent / RegisterEvent / FireActions / 轮询器` 四段代码里，**全部**遍历都是"向量下标 +1"或"链表 `[x+0x28]` 前进"，**没有任何一处比较两个条目地址大小来决定次序**。[实证，方法论 = 逐指令读 §7 所列 dump]

### 2.3 迭代期安全变更（游标 `0xA83CDC`）

轮询器把"当前下标"放在全局 `0xA83CDC`（`0x55AFDB` 置 0、`0x55B164` 自增）。当迭代中某 Tag 被销毁（`TagClass::Destroy` 会把自己塞进延迟析构队列，§4.4；或 `0x6E4F60` 摘除路径），摘除代码会比较"被摘除下标 vs 游标"并**按需回退游标**（`0x6E4FD0–0x6E4FE8`：`mov ecx,[0xA83CDC] / cmp ecx,eax / jl skip / dec eax / mov [0xA83CDC],eax / jns skip / test edx,edx / jne skip / mov [0xA83CDC],edx`），避免漏求值。这是**顺序稳定性**的保障机制。[实证]

### 2.4 确定性判定

| 命题 | 判定 | 依据 |
|---|---|---|
| 每帧 Tag 遍历顺序在多端一致 | **是**（前提：`TagTypeClass::Array` 的加载顺序一致） | 顺序只依赖 INI 解析序 + 存档序；无指针依赖 |
| 顺序依赖指针对齐 / 分配器行为 | **否** | 无地址比较指令（§2.2） |
| 顺序依赖 House 序 | **否**（每帧路径 `pTagOwner=NULL`，无房维度遍历） | §1.2 调用参数 |
| 遍历中变更是否导致多端步调不同 | **取决于"销毁时机"是否确定**：销毁由延迟队列在 `MainLogicFrame` 尾部统一抽干（`0x55DE9F → 0x725C70`），时机确定 | §4.4 |
| `TagTypeClass::Array` 的加载顺序是否严格等于 INI 文本序 | **[待实测]**：静态无法断言 INI 解析器的枚举/哈希顺序 | §8 U-1 |
| 每帧事件种类序列中的 `[Scenario+0x34AA/0x34AB/0x34BE]` 锁存位 | **多端一致的前提**是这些"本帧发生 Set/Clear/环境光/拾取"锁存位由确定性事件置位；其中 `0x34BE`（crate）与 `0x34AA`（global/local set）若由本机输入（拾取木箱）驱动，则**天然分叉**——与 `trigger_system_manifest.md` §9.3 的高危输入面一致 | [推演] + manifest §9.3 |

---

## 3. Q3 随机数（PRNG）消费

### 3.1 两个 Randomizer 实例与 `GetFlags` 位语义（先把"谁该进名单"钉死）

- **局外 RNG**：`Randomizer::Global` @ `0x886B88`（YRpp `Randomizer.h:10`；全镜像 99 处引用，集中在 `0x4040xx` 等 RMG/菜单路径）——**触发器子系统一处都不用**。[实证]
- **局内 RNG**：`ScenarioClass::Random` @ `[0xA8B230]+0x218`（YRpp `ScenarioClass.h:97`）。触发器子系统的 **4 个消费函数全部使用它**（每处都有 `lea ecx,[reg+0x218]` 紧邻）。[实证]
- **`Randomizer` 布局**（`0x65C6D0` ctor 实证）：`+0x00 bool IsLocked`（`0x65C780: 80 39 00 / 74 03` → 置位则 `Random()` 返回 0）、`+0x04 Next1`、`+0x08 Next2`、`+0x0C Table[0xFA]`（250 个 dword，ctor 用 4 组 XOR/乘法混合预填充）；`Random()` = 经典 lagged-Fibonacci：`Table[Next1] ^= Table[Next2]`，两个游标模 250 递增。[实证]
- **`TEventClass::GetFlags 0x71F680` 位语义**（4 组 selector 字节表 + 跳表解出，全 62 kind 逐项）：

| 位 | 含义 | 置位的 EventKind（实测解出） |
|---|---|---|
| `0x01` | 位置/进入类 | `0x00,0x01,0x04,0x08,0x18,0x19,0x1A,0x1F,0x35,0x36,0x3B` |
| `0x02` | 对象状态类 | `0x00,0x01,0x02,0x04,0x06,0x07,0x08,0x1D,0x21,0x22,0x23,0x26,0x27,0x28,0x29,0x2A,0x2B,0x2C,0x30,0x31` |
| `0x04` | `AnyEvent(0x08)` / `ZoneEntryBy(0x18)` | 仅此 2 项（`0x71F6BD: 83 CE 04`） |
| `0x08` | 房级计数/是否类 | `0x03,0x05,0x08,0x09,0x0A,0x0B,0x0C,0x0F,0x10,0x11,0x12,0x13,0x14,0x15,0x16,0x1E,0x20,0x34,0x37,0x38,0x39,0x3A` |
| **`0x10`** | **自求值/计时器类（= 每帧名单准入位）** | `0x08,0x0D,0x0E,0x17,0x1B,0x1C,0x24,0x25,0x2D,0x2E,0x2F,0x32,0x33,0x3C,0x3D`（`0x71F6F1: 83 CE 10`） |

- `TActionClass::GetFlags 0x6E3EE0` 返回值域实测**只有 {0, 2}**：`2` 的 7 项 = `0x0E ChangeHouse, 0x20 DestroyAttachedObject, 0x3C SellBuilding, 0x3D TurnOffBuilding, 0x3E TurnOnBuilding, 0x5B GoBerzerk, 0x6F EvictOccupiers`（与 `trigger_system_manifest.md` §6.2 的 7 项一致，本节独立复算）。[实证]

### 3.2 PRNG 消费点逐条清单（"调用序编号" = 触发器子系统内的指令级先后，不含其它子系统）

| # | 函数 | 指令 VA | 机器码 | 实例 | 语义 | 消费次数/次调用 |
|---|---|---|---|---|---|---|
| **T1** | `TriggerClass::ResetTimers 0x726400` | `0x726464` / `0x72646A` | `8D 88 18 02 00 00` / `E8 71 63 F3 FF` | `+0x218` | `RandomRanged(0, event->arg)`，用于 `RandomDelay(0x33)` 计时器重新装填 | 每个 `RandomDelay` 事件 **1** |
| **T2** | 动作内联体 `0x3A MeteorShower`（块起始 `0x6DF223`）→ 辅助 `StartMeteorShower 0x6E2C40` | `0x6E2CEB / 0x6E2D4E / 0x6E2D5A / 0x6E2DB0` | `E8 90 9A F7 FF` 等 | `+0x218` | 随机流星落点/数量 | **4** |
| **T3** | 动作内联体 `0x62 PlaySoundEffectRandom`（块起始 `0x6DE7A5`） | `0x6DE809` / `0x6DE80F` | `8D 88 18 02 00 00` / `E8 CC DF F7 FF` | `+0x218` | `RandomRanged(0, Value−1)` 从音效表随机取一条 | **1** |
| **T3′** | YRpp slave `PlayAudioAtRandomWP 0x6E1780`（**同体死副本**，全镜像 0 个直呼点） | `0x6E17D8` / `0x6E17DE` | `8D 8A 18 02 00 00` / `E8 FD AF F7 FF` | `+0x218` | 同上；改 hook 该 slave **不会**生效（与 manifest §2"hook slave 不必然生效"一致） | 1 |
| **T4** | `AITrigger 0x6F0AB0` | `0x6F0AFB` / `0x6F0B01` | `8D 88 18 02 00 00` / `E8 DA BC F6 FF` | `+0x218` | `RandomRanged(1,100)` 概率门 | **1** |
| **T5** | `AITrigger` 姊妹函数 `0x6F0C9C` | `0x6F0CE8` / `0x6F0CEE` | `81 C1 18 02 00 00` / `E8 ED BA F6 FF` | `+0x218` | 加权挑选候选（`RandomRanged(1,n)` 后按权重游走） | 1 |
| **T6** | 帧 CRC `0x64DAB0` | `0x64DE39` / `0x64DE3F` | `8D 8A 18 02 00 00` / `E8 3C E9 00 00` | `+0x218` | 取 1 个随机数折进 `CurrentFrameCRC` | **1 / 每次 CRC** |

**事件判定侧**：`TEventClass::HasOccured 0x71E940` 及其全部辅助（`0x71E940–0x71F700`，重同步线性扫描）**0 条** Randomizer 调用。[实证]

**其它触发器相邻但非本体系的消费点**（供交叉核对，不计入上表）：`0x6EE85C/0x6EE94E/0x6EFADC`（Team 脚本/招募）、`0x6F3254`（AITrigger 类型簇）、`0x702049/0x702572/0x7027F7/0x705860`、`0x707xxx`、`0x71C5B0/0x71C730`、`0x7224AE/0x722AF0/0x722F6A/0x722FF2/0x7235A0`（`0x722xxx` 簇与 `TriggerTypeClass` 同区，**上游归属未闭环**，见 §8 U-3）。全区间 `0x6C0000–0x730000` 共 **65** 条 Randomizer 直呼。[实证]

### 3.3 条件侧（概率型条件）消费的精确结论

`RandomDelay(0x33)` 的计时器公式（`0x726459–0x72649C`，逐指令）：

```
00726459  mov eax,[edi+0x34]              ; eax = TEventClass::arg（INI 的 Value）
00726464  lea ecx,[ScenarioRandom]
0072646A  call 0x65C7E0                  ; eax = RandomRanged(0, arg)
0072646F  mov ecx,eax
00726471  mov eax,[edi+0x34] ; cdq ; sar eax,1   ; eax = arg/2（向零取整）
00726483  add eax,ecx                   ; arg/2 + rand(0,arg)
00726488  mov [esi+0x34],ebx            ; Timer.Start = CurrentFrame
0072648B  lea eax,[eax+eax*2]           ; *3
00726491  lea eax,[eax+eax*4]           ; *5 ⇒ Duration = 15 * (arg/2 + rand(0,arg)) 逻辑帧
00726494  mov [ecx+8],eax               ; Timer.Duration
007264A5  and [esi+0x40],~(1<<eventIdx) ; 清该事件的 OccuredEvents 位
```

- **`15` = 每秒逻辑帧数**：`ElapsedTime(0x0D)` 分支同一处 `0x72642E/0x726437` 也是 `*3 *5`（即 `15 × arg` 帧），两条支路共享同一乘法序列 → `Timer.Duration` 单位 = **逻辑帧**。[实证]
- 重新装填（即**再次消费 PRNG**）的时机：`RegisterEvent` 尾部 `0x726591/0x7265A4`：**"该 Trigger 的全部事件都已发生" 且 `arg4 persistent==1`** 时才调用（`persistent` 由 `RaiseEvent` 用 `Persistence==Persistent(2)` 传入，`0x6E5408: 83 FA 02 / 0F 94 C2`）。其余 4 个调用点为构造 / Enable / `NotifyGlobalChanged` / `NotifyLocalChanged`。 [实证]
- 因此：**条件侧的 PRNG 消费不是"每次判定都抽"，而是"计时器装填瞬间抽一次"**。它在 MP 中的次数 = 各端"装填事件"发生次数；装填由（a）任务初始化（`TriggerClass` 构造，`0x7260E7`，**每张触发器的每个 RandomDelay 事件各 1 次**，确定）、（b）持久触发器的整组事件全部命中（**取决于世界状态，需确定性**）驱动。

### 3.4 帧 CRC 与 RNG 的关系（对 `0x0064DAB0` 的准确表述）

`0x64DAB0` 是"每帧校验混合器"：遍历 `[0xA83DF8]/[0xA83DEC]` 与 `[0x8B4118]/[0x8B410C]` 两个对象数组，把每项的 `[obj+0x9C]` 等字段折进滚动累加器 `[0xAC51FC] = CurrentFrameCRC`（每步 `acc = acc*2 + value`，`0x64DB33–0x64DB4A` 一段可逐字对照），**并在收尾 `0x64DE39/0x64DE3F` 调一次 `Randomizer::Random()`** 再 `acc = acc*2 + rand`（`0x64DE44–0x64DE54`）。[实证]

结论（三条，务必按此引用）：
1. **CRC 会消费局内 RNG**：每次 CRC 计算使 `ScenarioClass::Random` 的两个游标各前进 1。
2. **CRC 不哈希 RNG 状态**：字节级负证——`0x64C000–0x64E100` 区间内对 `+0x218` 的编码引用**只有 1 处**（`0x64DE39` 的 `lea ecx,[edx+0x218]`），即只取输出值；无 `Table/Next1/Next2` 的读取。
3. 由此推论 [推演]：**"RNG 状态分叉"会经由下一次 CRC 立即显形**（因为 CRC 混入了 RNG 的一个输出），比"只依赖后续消费点显形"更早。**这使 `RandomDelay` 类触发器一旦分叉几乎必然在当帧被 CRC 打出。** 亦解释了为什么 `savegame_block_manifest.md` 的禁改表把"RNG 状态（`ScenarioClass::Random`）"列为**禁改**。

### 3.5 对 `trigger_system_manifest.md` §9 的补强与一处**风险升级建议**

- 该文把动作 `0x62` 从"绿"升为"黄（消耗同步 RNG）"——**本专章独立复算成立**（§3.2 T3，实例为 `Scenario+0x218`，非 `Randomizer::Global`）。
- **风险升级建议**：该文 §9.2 把音效类列为"纯表现可优化"面（绿/黄）。逐指令复核后：`0x63 PlaySoundEffectAtWaypoint` 的内联体 `0x6DE845`–`0x6DE871`（`call 0x6E1830`）**不消费 RNG**，**绿判定成立**；其 YRpp slave `PlayAudioAtSpecificWP 0x6E18B0` 与 `PlayAudio 0x6E1760` 亦无 RNG 调用。**结论：只有 `0x62` 一项属于 RNG 契约面，manifest 的"唯一"表述正确。** [实证]
- 另一处需补强：`0x3A MeteorShower` 消费 **4 次** `Random()`（§3.2 T2），manifest 已标"红｜流星雨（生成伤害对象）"但未标 PRNG 次数；**联机改图时若对流星雨做次数削减，会立即改变 RNG 序列 → 分叉**。建议在 manifest 该行补注"RNG×4"。

---

## 4. Q4 Tag/Trigger 生命周期、Destroyed、EVA 与存档

### 4.1 `TagClass` 生命周期

| 阶段 | 入口 | 实证要点 |
|---|---|---|
| **加载/实例化** | `TagClass::GetInstance 0x6E52A0`（`FindByNameOrID 0x6E5E70` 供 INI 名字解析） | 线性扫 `TagClass::Array`（Items `0xB0E724`，Count `0xB0E730`）比较 `[tag+0x24]==pType`（`0x6E52B8`）；未命中则 `operator new(0x38)`（`0x6E52C5: 6A 38 / E8 4B 3B 0E 00`）→ ctor `0x6E4DE0` |
| **构造** | `0x6E4DE0` | 设 4 个 vtable 指针（`0x7F44E0` 起）→ `AnnounceExpiredPointer`（`0x7258D0`）→ 尾接进 `TagClass::Array`（`0x6E4E47/0x6E4E50`） |
| **挂到对象** | 由对象侧写自己的 Tag 指针 | 轮询器/事件路径均通过 `RaiseEvent` 的 `pTagOwner` 传入宿主；`RaiseEvent` 尾部有 `cmp [edi+0x34], ebp`（`0x6E549F`）后 `call 0x5F5B50` 的"清宿主引用"分支 [实证；宿主字段归属 [推演]] |
| **摘除/析构** | `0x6E4F60` | 重置 vtable → `AnnounceExpiredPointer(this,true)`（`0x6E4F84: E8 47 09 04 00`）→ **有条件地**从 `0x8B40C8`（gated by `GetFlags()&0x10`，`0x6E4FA6/0x6E4FAB`）、`0x8B41A8`（`&4`）、以及 Trigger 链摘除，并回退游标 `0xA83CDC` |
| **触发后置位/销毁** | `TagClass::Destroy 0x6E5230` | `mov byte [esi+0x34],1`（Destroyed=1）→ 把自己**尾接进延迟析构向量 `0xB0F698`**（`0x6E5237`–`0x6E5287`） |

### 4.2 `TriggerClass` 生命周期

`TriggerClass::ctor 0x725FA0`（逐指令）[实证]：

```
00725FAF  mov [esi+0x24],eax     ; Type = arg
00725FB2  mov [esi+0x28],ebx     ; NextTrigger = 0
00725FB5  mov [esi+0x2C],ebx     ; House = 0
00725FB8  mov [esi+0x30],bl      ; Destroyed = 0
00725FBB  mov ecx,[0xA8ED84]     ; CurrentFrame
00725FC4  mov [esi+0x34],ecx     ; Timer.Start = CurrentFrame
00725FCA  mov byte [esi+0x44],1  ; Enabled = 1
00725FCE  … 4 个 vtable 指针（0x7F5858 起）
00726037  mov [ecx+eax*4],esi    ; 尾接进向量 0xB0F670
0072608A  mov [ecx+eax*4],esi    ; 尾接进向量 0xB0F708
007260DD  mov [ecx+eax*4],esi    ; 尾接进 TriggerClass::Array 0xA8EAE8
007260E0  cmp [esi+0x24],0 ; je skip
007260E7  call 0x726400          ; ★ ResetTimers（若含 RandomDelay → 此处消费 PRNG）
```

- **触发器创建即可能烧随机数**；同一张地图的触发器实例化顺序若一致，则这段 PRNG 消费一致。[实证]
- `TriggerClass::Destroy 0x726720`、`Enable/Disable`（`+0x44` 直写）、`ResetTimers`、`NotifyGlobalChanged 0x7263A0`、`NotifyLocalChanged 0x7263D0` 构成"启用/禁用/变量重置"控制面（后两者是 `GlobalSet/GlobalCleared/LocalSet/LocalCleared` 事件的**推送侧**：某处写全局/局部变量后会通知相关 Trigger 重置计时器）。

### 4.3 触发后置位（三分支 + 位图 + 指针失效通告）

| Persistence（`TagTypeClass+0x9C`） | 条件 | 行为（`0x6E541D–0x6E5484`） |
|---|---|---|
| `Volatile = 0` | 事件命中 | `FireActions`（`0x6E546D`）→ `TriggerClass::Destroy`（`0x6E5474`） |
| `SemiPersistant = 1` | 事件命中 **且** `InstanceCount==1`（`0x6E5442: 83 7D 2C 01`） | `FireActions` + `Destroy`（`0x6E5450/0x6E5457`），并 `AnnounceExpiredPointer(this,true)`（`0x6E54EF: 8B CD / E8 DC 03 04 00`） |
| `SemiPersistant = 1` | 事件命中 **但** `InstanceCount != 1` | 只置"已发生"位，**不执行动作、不销毁**（`0x6E547F`） |
| `Persistent = 2` | 事件命中 | 仅 `FireActions`，**永不销毁**（`0x6E5431/0x6E5439`） |
| 事件级持久位 | `forceFire`(arg3) 或 `GetStateA/B` 双真 | `or [esi+0x40], 1<<eventIdx`（`0x726582: 09 6E 40`） |

> 位序 = 事件在链表中的位次（§1.4），因此**触发器事件在存档里以位图形式持久化**——这要求 `TriggerClass` 的 `Save/Load`（v[5] `0x726860` / v[6] `0x7268D0`）严格保持链表顺序。

### 4.4 `Destroyed` 与"延迟析构队列"（`0xB0F698`）

- 队列：`DynamicVectorClass<AbstractClass*>` @ `0xB0F698`（Items `0xB0F69C`、Capacity `0xB0F6A0`、Count `0xB0F6A8`、增长 `0xB0F6AC`）。**TagClass::Destroy**（`0x6E5230`）与同族对象（`DiskLaserClass::v[23]`、`BuildingClass::v[62]` 等也向同一向量追加）共用它。[实证]
- 抽干：`0x725C70`——遍历向量 → 调 vfunc 17（`0x725C8F: FF 52 44`，`AbstractClass::IsDead`）→ 从向量移除（`0x725CAA: FF 52 10`，`DynamicVectorClass::RemoveItem`）→ 虚调用 + RTTI `dynamic_cast`（类型描述符 `0x818D60 / 0x842D80`）后释放。[实证]
- 调用时机：`MainLogicFrame` 尾部 **`0x55DE9F`**（另有 `0x534450`、`0x5FD2E0`、`0x68794D` 三处），即"帧内统一收尸"。**这是多端销毁时机一致性的保证点**：销毁不是就地 `delete`，而是排队到帧尾。[实证]
- 与 §2.3 的游标回退机制配合 → 每帧遍历顺序在"遍历中被销毁"时仍稳定。

### 4.5 EVA 播报链路

- 动作 `0x15 PlaySpeech` 内联体（块起始 `0x6DE904`）：

```
006DE904  mov ecx,[esi+0x90]     ; ecx = TActionClass::Value（语音 ID）
006DE90A  push -1                ; 优先级/通道参数
006DE90C  mov edx,2              ; mode = 2（EVA 专属流）
006DE911  call 0x752480          ; EVA 播放入口（audio_engine_deep_dive.md: EVA 专属流 0x752480 / AudioStream [0xB1D4CC]）
```

- 因此 **`PlaySpeech` 是"触发器 → EVA"的唯一动作路径**；`0x13 PlaySoundEffect`（`0x6DE780`）走 `VocClass::PlayGlobal 0x750920`、`0x62/0x63` 走 `PlayGlobal/PlayIndexAtPos`，属普通 Voc 通道（受 `audio_engine_deep_dive.md` 的 300 通道池饥饿问题影响，EVA 因独立流而免疫）。[实证 + 引用]
- **全局性 EVA（如任务计时器到期）**不在触发器动作里，而在 `0x55AFB0` 尾部（`0x55B1C6: 6A 02 / B9 E8 F7 87 00 / E8 1E 91 F9 FF`，在 `MapClass 0x87F7E8` 上调用 `0x4F42F0(2)`）——即"任务计时器到期"这条每帧事件的**表现侧**与动作侧分离。[实证]

### 4.6 与存档的关联点

| 存/取内容 | 实证位置 | 说明 |
|---|---|---|
| **每帧 Tag 向量**（`0x8B40C8` 的 Items 全量，每项 4 字节） | 存 `0x67F8C5`–`0x67F8D6`（`mov edx,[0x8B40CC]` + `lea eax,[edx+edi*4]` + 流写入）；取 `0x67FB8A/0x67FB93/0x67FB9D` | **顺序敏感**：载入按存档序重建 → 顺序与存前一致 |
| `CurrentFrame` | 存 `0x67F819`（`push 0xA8ED84`）；取 `0x67FA19`（与 `savegame_block_manifest.md` §U-3 定谳一致） | 计时器相位依赖 `CurrentFrame`（§3.3） |
| 同批标量（`0xA8ED78`、`0xA83D4C` …） | `0x67F7E3`–`0x67F822` | 帧/局标识 |
| `TriggerClass` 自身 | IPersistStream v[5] `0x726860` / v[6] `0x7268D0` | 读回后重置 4 个 vtable 指针（`0x726884`–`0x726898`） |
| `TagClass` 自身 | IPersistStream v[5] `0x6E5730` / v[6] `0x6E57A0` | 由 `TagClass` vtable `0x7F44E0` 槽位定 |
| **RNG 状态** | `ScenarioClass+0x218` | `savegame_block_manifest.md` 禁改表：**禁改**（联机 desync） |

> **重要提醒（新发现）**：`0xB0F698`（延迟析构队列）与 `0xA83CDC`（轮询游标）是**帧内瞬时状态**，必须在跨帧/存档边界为"空/0"；若存档发生在帧中、在 `0x725C70` 抽干之前，队列内容是否进档需真机验证 → §8 U-4。

---

## 5. Q5 与 AI 的联动：AITrigger `0x6F0AB0` 与普通触发器的调用关系与差异

**调用关系 [实证]**：AITrigger 的**唯一** 2 个直呼点为 `0x4F8A6A` 与 `0x4FA220`，两者都落在 `HouseClass` AI 簇（`HouseClass::v[23] = 0x4F8440`）。与普通触发器**零交叉**：`TagClass::RaiseEvent 0x6E53A0` 的 73 个调用点里没有 AITrigger 相关函数；`AITriggerTypeClass` 也不出现在 `TriggerClass/TagClass` 的任何数组或链表中。

**AITrigger `0x6F0AB0` 骨架**：

```
006F0AB0  sub esp,0x50 ; this=ecx(AITriggerTypeClass*), edx=HouseClass*
006F0AC9  call 0x6F2230                 ; 条件评估上下文准备
006F0ACE  mov eax,[edi+0x5600]          ; AITrigger → 房下标
006F0AE5  mov ecx,[0xA8022C] ; mov edx,[ecx+eax*4]   ; → HouseClass*
006F0AF7  push 0x64 ; push 1
006F0AFB  lea ecx,[eax+0x218]  (ScenarioClass::Random)
006F0B01  call 0x65C7E0                 ; ★ RandomRanged(1,100)
006F0B06  cmp eax,[edi+0x565C] ; jg skip        ; ← Probability 门（> 则放弃）
006F0B12  mov al,[edi+0x1F2] ; je skip           ; ← AITriggersActive 门
006F0B20  mov ebp,[0x8B40F8] ; mov ecx,[0x8B40EC]   ; TeamClass::Array（Count/Items）
006F0B36  cmp [eax+0x2C],edi                     ; team->HouseOwner == house ?
006F0B3F  cmp byte [eax+0xF6],0                  ; team type 标志位
006F0B69  cmp ebx,[edx+ecx]                      ; 该房 Team 数 vs 上限
006F0B77  cmp esi,eax                            ; "达标团队"数 vs 上限一半
006F0B90  … 选 [team+0x50] 最小者作为候选
```

**差异表**：

| 维度 | 普通触发器（Tag/Trigger） | AITrigger（`0x6F0AB0`） |
|---|---|---|
| 宿主数据结构 | `TagClass`→`TriggerClass`→`TEventClass/TActionClass` 链 | `AITriggerTypeClass::Array`（`0xA8B200/0xA8B204/0xA8B210`，见 `house_team_ai_update.md:120`） |
| 求值节拍 | 每逻辑帧（10 个自求值事件，`LogicClass` 轮询器）+ 对象事件冒泡 | `HouseClass` AI 内、**TeamDelayTimer**（`this+0x5798/+0x57A0`）门控，**非每帧**（[推演]；依据：`house_team_ai_update.md` 门控点 `0x4F8A00` 与本次直呼点 `0x4F8A6A` 紧邻） |
| 条件表达 | 62 种 EventKind 逐 kind 编译进 4 层跳表 | 房级 Team 计数 / 上限比较 + 概率门 |
| 概率/随机 | 仅 `RandomDelay`（**装填时**抽 1 次） | **每次评估抽 1 次** `RandomRanged(1,100)`（+姊妹函数 1 次） |
| 结果 | 执行 145 种动作之一（含 `0x04 CreateTeam`） | 选出一支 `TeamClass` 并触发创建（`0x6F09C0 TeamTypeClass::CreateTeam`，见交叉文档） |
| 权重 | 无 | `Weight Current` 由 Team 死亡/成功失败回写（`0x41FD60/0x41FE20`，见交叉文档） |
| 顺序依赖 | 向量下标升序 + 链表序 | AITriggerArray 下标序（同权重下的优先级，见交叉文档 §插入点 A 警告） |
| 是否进每帧 Tag 向量 | 是（若含 bit0x10 事件） | **否** |

**联机含义 [实证 + 推演]**：AITrigger 的 RNG 消费频率与"每帧有几间房通过门控"耦合 → **门控计时器（TeamDelayTimer）必须多端一致**，否则 AITrigger 抽数次数不同 → 立即分叉。这是"AI 节奏 ≠ 触发器节奏、但共享同一条 RNG 流"的关键风险点，建议列入 `net_sync_checksum.md` 红线表。

---

## 6. 逐条结论表（含证据等级）

| # | 结论 | 等级 | 关键证据（VA / 字节 / 反汇编） |
|---|---|---|---|
| Q1-1 | 每帧遍历触发器系统的唯一位置 = `LogicClass` 轮询器 `0x55AFB0` | **[实证]** | `0x55DC9E: E8 0D D3 FF FF`（唯一调用点，在 `MainLogicFrame 0x55D360` 内） |
| Q1-2 | 该调用**无条件**（位于 `0x55DBCD` 条件块汇合点之后） | **[实证]** | `0x55DBCD: 39 3D 38 B2 A8 00 / 0F 85 C0 00 00 00` → 汇合于 `0x55DC99` |
| Q1-3 | 轮询器遍历的是 **Tag 名单向量 `0x8B40C8`**，不是触发器对象 | **[实证]** | `0x55AFE6: 8B 0D CC 40 8B 00`；`0x55AFEC: 8B 34 81` |
| Q1-4 | 每帧抛出固定 **10 个** EventKind（表见 §1.2） | **[实证]** | 10 条 `push imm` + `E8 xx xx xx xx`（claims.txt 逐条） |
| Q1-5 | 轮询器早于 `CurrentFrame++`（`0x55DE73`） | **[实证]** | `0x55DC9E` < `0x55DE73`；与 `clock_frame_loop.md` §3.2 一致 |
| Q1-6 | 一个 Tag 上"任一事件已执行动作"即跳过该 Tag 余下事件种类 | **[实证]** | `0x55B011/0x55B03E/0x55B05C/…: 0F 85 xx xx xx xx` → `0x55B15E` |
| Q1-7 | 条件求值唯一入口 `RegisterEvent 0x7264C0`（1 个调用点） | **[实证]** | 全镜像 `call 0x7264C0` 仅 `0x6E5414` |
| Q1-8 | 动作执行唯一入口 `TActionClass::Execute 0x6DD8B0`（1 个调用点） | **[实证]** | 全镜像仅 `0x726605` |
| Q1-9 | 条件判定 `HasOccured 0x71E940` 唯一调用点 `0x726540` | **[实证]** | — |
| Q1-10 | 第二个每帧入口：`TeamClass::AI` 两处抛 `0x17 TeamLeavesMap` 遍历同一向量 | **[实证]** | `0x6E92F3/0x6E9304`；`0x6EA4B1/0x6EA4C0`（`push 0x17`） |
| Q1-11 | 每帧事件 `location` 恒取全局 `CellStruct 0xABCCD8`；`pTagOwner=NULL` | **[实证]** | 10 处 `push [0xABCCD8]` + `push 0` |
| Q2-1 | 每帧顺序 = 向量下标升序 | **[实证]** | `0x55AFDB` 归零、`0x55B164: 8B 0D DC 3C A8 00 / 40 / 3B C1 / 89 0D … / 7C 9F` |
| Q2-2 | 注册序 = `TagTypeClass::Array` 下标升序（只追加） | **[实证]** | `0x684D4E/0x684D56/0x684D5C/0x684EA7`；追加 `0x684E2F: 89 3C 81` |
| Q2-3 | Tag→Trigger 单链表为**头插**（LIFO） | **[实证]** | `0x6E55C0: 8B 44 24 04 / 8B 51 28 / 89 50 28 / 89 41 28` |
| Q2-4 | Trigger→Event/Action 链表序 = 挂载序；位图位序 = 链表位次 | **[实证]** | `0x7264F2`（`8B B8 AC 00 00 00`）、`0x7265D8`（`8B B0 B0 00 00 00`）、`0x726509: D3 E5` |
| Q2-5 | 全链路**无按指针值排序/哈希** | **[实证]**（负证） | §2.2，四段代码逐指令无地址比较 |
| Q2-6 | 迭代中摘除会回退游标 `0xA83CDC`，保证不漏求值 | **[实证]** | `0x6E4FD0`–`0x6E4FE8` |
| Q2-7 | 存档重建保持原序（不按 TagType 重排） | **[实证]** | `0x67FB8A/0x67FB93/0x67FB9D` |
| Q2-8 | 锁步下顺序稳定 | **[推演]**（条件：INI 加载序一致 + 锁存位确定） | §2.4；`TagTypeClass::Array` 加载序需真机验证 |
| Q3-1 | 局内 PRNG = `ScenarioClass::Random`（`[0xA8B230]+0x218`）；触发器系统**不用** `Randomizer::Global` | **[实证]** | 4 个消费函数全部 `lea ecx,[reg+0x218]`；`0x886B88` 在 `0x6C0000–0x730000` 区间 0 引用 |
| Q3-2 | 事件**条件判定链 0 PRNG 消费** | **[实证]**（负证） | `0x71E940–0x71F700` 重同步扫描 0 命中 |
| Q3-3 | `RandomDelay(0x33)` 装填 = `RandomRanged(0,arg)`，时长 `15*((arg>>1)+rand)` 逻辑帧 | **[实证]** | `0x726464/0x72646A/0x726481/0x72648B/0x726491` |
| Q3-4 | 动作 `0x3A MeteorShower` 消费 **4** 次 `Random()` | **[实证]** | `0x6E2CEB/0x6E2D4E/0x6E2D5A/0x6E2DB0` |
| Q3-5 | 动作 `0x62 PlaySoundEffectRandom` 消费 **1** 次 `RandomRanged`（内联体；slave `0x6E1780` 同体但零引用） | **[实证]** | `0x6DE809/0x6DE80F`；`0x6E17D8/0x6E17DE` |
| Q3-6 | AITrigger 消费 2 次 `RandomRanged`（概率门 + 加权挑选） | **[实证]** | `0x6F0AFB/0x6F0B01`；`0x6F0CE8/0x6F0CEE` |
| Q3-7 | 帧 CRC `0x64DAB0` **消费 1 次** Random 并把值折进 `CurrentFrameCRC` | **[实证]** | `0x64DE39/0x64DE3F/0x64DE44`–`0x64DE54` |
| Q3-8 | 帧 CRC **不**读 RNG 内部状态（`Table/Next1/Next2`） | **[实证]**（负证） | `0x64C000–0x64E100` 区间对 `0x218` 引用仅 1 处（`0x64DE39`） |
| Q3-9 | `TEventClass::GetFlags` bit 0x10 = 每帧名单准入位，与轮询器 10 事件一致 | **[实证]** | `0x71F6F1: 83 CE 10`；selector `0x71F7C0` 全表解出 |
| Q3-10 | manifest §9 对 `0x62` 的"唯一 RNG 契约项"判定成立；建议为 `0x3A` 补注 RNG×4 | **[实证]** | §3.5 |
| Q4-1 | `TriggerClass::Size()=0x48`；`TagClass` 实例 0x38 | **[实证]** | `0x726930: B8 48 00 00 00 C3`；`0x6E52C5: 6A 38` |
| Q4-2 | `Enabled@+0x44` / `Destroyed@+0x30`（manifest 命名勘误） | **[实证]** | `0x7264C4: 8A 46 44 / 84 C0 / 0F 84 …`；`0x725FCA: C6 46 44 01` |
| Q4-3 | 触发后按 `Persistence` 三分支；`Persistent` 永不销毁 | **[实证]** | `0x6E5420/0x6E5426/0x6E542B/0x6E542E` |
| Q4-4 | `Destroyed` 只是标记；真正释放走延迟队列 `0xB0F698`，帧尾 `0x725C70` 抽干 | **[实证]** | `0x6E5233: C6 46 34 01〔勘误 ASM-FIX-4b：原记锚点 0x6E5230 实测 `56 8B F1 C6`（`push esi; mov esi, ecx` 起于 0x6E5230），`mov byte [esi+0x34], 1` 真锚点 = 0x6E5233，Δ+3〕` + `0x6E525E`；`0x55DE9F: E8 CC 7D 1C 00〔勘误 ASM-FIX-4〕原记 rel32 末字节 `02`（解析目标 0x00585C70，该调用点全镜像 0 命中）实测 `1C`（`call 0x00725C70`），与同行「帧尾 `0x725C70` 抽干」自洽` |
| Q4-5 | EVA 播报唯一动作路径 = `0x15 PlaySpeech` → `call 0x752480`（EVA 专属流） | **[实证]**（`0x752480` 身份引用 `audio_engine_deep_dive.md` [推演]） | `0x6DE904/0x6DE90A/0x6DE90C/0x6DE911` |
| Q4-6 | 每帧 Tag 向量整体进存档（4 字节/项）并原序还原；`CurrentFrame` 同批进档 | **[实证]** | `0x67F8C5`…；`0x67F819`；`0x67FB8A`… |
| Q5-1 | AITrigger 唯一 2 个直呼点在 `HouseClass` AI 簇 | **[实证]** | `0x4F8A6A`、`0x4FA220`（`HouseClass::v[23]=0x4F8440`） |
| Q5-2 | AITrigger 与 Tag/Trigger 体系零交叉（无共同数组/链表/事件号） | **[实证]**（负证） | `RaiseEvent` 73 调用点无 AITrigger 函数；`AITriggerTypeClass` 不在 `TagClass/TriggerClass` 数组中 |
| Q5-3 | AITrigger 概率门 `RandomRanged(1,100) <= [this+0x565C]` | **[实证]** | `0x6F0AF7/0x6F0AFB/0x6F0B06` |
| Q5-4 | AITrigger 由 TeamDelayTimer 门控、非每帧 | **[推演]**（依据 `0x4F8A00` 与直呼点 `0x4F8A6A` 相邻 + `house_team_ai_update.md`） | — |
| Q6-1 | 结论均以 `[实证]/[推演]/[待实测]` 标注；174 条字节断言机读通过 | **[实证]** | §9 门禁输出 |

---

## 7. 关键证据（原始机器码 + 反汇编）

以下全部可在 `out/re_work/triggers_deep/claims.txt` 中复算（`audit_bytes.py` → 174/174 OK）。

**(1) 每帧节拍——轮询器调用点与遍历循环**

```
0055DC99  B9 78 F7 87 00        mov ecx,0x87F778        ; LogicClass::Logics
0055DC9E  E8 0D D3 FF FF        call 0x55AFB0           ; ★ 全镜像唯一调用点
00684E29  8B 0D CC 40 8B 00     mov ecx,[0x8B40CC]      ; per-frame Tag vector Items
00684E2F  89 3C 81              mov [ecx+eax*4],edi     ; Items[Count] = tag（尾接）
0055AFE6  8B 0D CC 40 8B 00     mov ecx,[0x8B40CC]
0055AFEC  8B 34 81              mov esi,[ecx+eax*4]     ; esi = TagClass*（下标升序）
0055B164  A1 DC 3C A8 00        mov eax,[0xA83CDC]      ; 迭代游标
0055B169  8B 0D D8 40 8B 00     mov ecx,[0x8B40D8]      ; Count
0055B177  0F 8C 69 FE FF FF     jl 0x55AFE6             ; 下标升序闭环
```

**(2) 条件求值链（1 次调用 = 1 次判定）**

```
006E53DE  8B 75 28              mov esi,[ebp+0x28]      ; TagClass::FirstTrigger
006E5414  E8 A7 10 04 00        call 0x7264C0           ; TriggerClass::RegisterEvent  ← 唯一调用点
007264F2  8B B8 AC 00 00 00     mov edi,[eax+0xAC]      ; TriggerTypeClass::FirstEvent
00726509  D3 E5                 shl ebp,cl              ; 1<<eventIndex
00726540  E8 FB 83 FF FF        call 0x71E940           ; TEventClass::HasOccured  ← 唯一调用点
0072657B  E8 42 94 FF FF        call 0x71F9C0           ; GetStateB
00726582  09 6E 40              or [esi+0x40],ebp       ; OccuredEvents |= bit
007265A4  E8 57 FE FF FF        call 0x726400           ; ResetTimers（PRNG 点）
00726605  E8 A6 72 FB FF        call 0x6DD8B0           ; TActionClass::Execute  ← 唯一调用点
```

**(3) PRNG 消费点（局内实例 `Scenario+0x218`）**

```
0072645D  A1 30 B2 A8 00        mov eax,[0xA8B230]      ; ScenarioClass::Instance
00726464  8D 88 18 02 00 00     lea ecx,[eax+0x218]     ; &ScenarioClass::Random
0072646A  E8 71 63 F3 FF        call 0x65C7E0           ; RandomRanged(0,arg)   [RandomDelay]
006DE809  8D 88 18 02 00 00     lea ecx,[eax+0x218]
006DE80F  E8 CC DF F7 FF        call 0x65C7E0           ; RandomRanged          [Action 0x62]
006E2CE5  8D 88 18 02 00 00     lea ecx,[eax+0x218]
006E2CEB  E8 90 9A F7 FF        call 0x65C780           ; Random() ×4           [Action 0x3A]
006F0AFB  8D 88 18 02 00 00     lea ecx,[eax+0x218]
006F0B01  E8 DA BC F6 FF        call 0x65C7E0           ; RandomRanged(1,100)   [AITrigger]
006F0B06  3B 87 5C 56 00 00     cmp eax,[edi+0x565C]    ; Probability 门
0064DE39  8D 8A 18 02 00 00     lea ecx,[edx+0x218]
0064DE3F  E8 3C E9 00 00        call 0x65C780           ; Random()              [帧 CRC]
0064DE44  8B 15 FC 51 AC 00     mov edx,[0xAC51FC]      ; CurrentFrameCRC
0064DE4F  8D 0C 51              lea ecx,[ecx+edx*2]     ; acc = acc*2 + rand
```

**(4) 顺序与生命周期**

```
006E55C0  8B 44 24 04           mov eax,[esp+4]         ; TagClass::AddTrigger（头插）
006E55C4  8B 51 28              mov edx,[ecx+0x28]      ; FirstTrigger
006E55C7  89 50 28              mov [eax+0x28],edx      ; p->Next = FirstTrigger
006E55CA  89 41 28              mov [ecx+0x28],eax      ; FirstTrigger = p
006E5230  56 / 8B F1 / C6 46 34 01   push esi; mov esi,ecx; mov byte [esi+0x34],1  ; TagClass::Destroy
006E525E  A1 A8 F6 B0 00        mov eax,[0xB0F6A8]      ; 延迟析构向量 Count
006E5287  89 34 81              mov [ecx+eax*4],esi     ; Items[Count] = this
0055DE9F  E8 CC 7D 02 00        call 0x725C70           ; MainLogicFrame 尾部抽干
00725C8F  FF 52 44              call [edx+0x44]         ; IsDead()
00725CAA  FF 52 10              call [edx+0x10]         ; RemoveItem
```

**(5) Flags 位与动作 `0x15` 的 EVA 路径**

```
0071F6F1  83 CE 10              or esi,0x10             ; TEventClass::GetFlags: 自求值/计时器位
0071F6BD  83 CE 04              or esi,4                ; AnyEvent(0x08) / ZoneEntryBy(0x18)
006E3EF9  B8 02 00 00 00        mov eax,2               ; TActionClass::GetFlags 七项返回 2
006DE904  8B 8E 90 00 00 00     mov ecx,[esi+0x90]      ; Action 0x15 PlaySpeech: 语音 ID
006DE90A  6A FF                 push -1
006DE90C  BA 02 00 00 00        mov edx,2
006DE911  E8 6A 3B 07 00        call 0x752480           ; EVA 专属播放入口
```

---

## 8. 未闭环清单（含原因与下一步取证方法）

| # | 未闭环项 | 状态 | 原因 | 下一步取证方法 |
|---|---|---|---|---|
| **U-1** | `TagTypeClass::Array`（`0xB0E784`）的**加载顺序**是否逐字等于 INI 文本序 | **未闭环** | 只静态证明"注册序 = 数组下标序"，未证明"数组下标序 = INI 文本序"（解析器可能按名字哈希/字典序插入） | 反汇编 `TagTypeClass::LoadFromINIList 0x6E5ED0` 全函数，定位其数组 Add 调用点及其上文的键枚举循环；真机侧：同一地图两机各 dump `0xB0E784` 前 N 项做序列比对 |
| **U-2** | 每帧 `location` 全局 `0xABCCD8` 的**有效写入方** | **未闭环** | 全镜像直引 11 处：`0x55AEF2/0x55AEF8` 是**清零写**，其余 10 处是轮询器读；通过寄存器间接写入的点未穷尽 | 对 `0xABCCD8` 做"写点穷尽"扫描：额外扫 `8D 0D D8 CC AB 00` / `8D 15 …` / `B8 D8 CC AB 00` 等取址型指令，再筛 `mov [reg],…`；必要时真机下硬件写断 |
| **U-3** | `0x722xxx` 簇（`0x7224AE / 0x722AF0 / 0x722F6A / 0x722FF2 / 0x7235A0`）5 处 Random 消费点的**上游动作/系统归属** | **未闭环** | 该簇紧邻 `TriggerTypeClass`（`0x726xxx`）但不在本次定义的触发器子区间内；未回溯其调用者 | 对这 5 个函数起点做 `who`，回溯到首个属于已知表的调用者（`TActionClass::Execute` 跳表 / `TeamClass::AI` 跳表 / `AITriggerTypeClass`） |
| **U-4** | 延迟析构队列 `0xB0F698` 与游标 `0xA83CDC` 是否进存档 | **未闭环** | `0x67F7E0` 段只见 `0xA8ED78 / 0xA83D4C / 0xA8ED84 / 0xA8ECC8+数组 / 0x8B40C8 向量`；未逐字节走完全部序列化调用点 | 在 `0x67F7E0–0x67F9C0` 内枚举全部 `call [vtable+0x10]`（Write）实参，列出被写地址全集，与 §4.6 表做差集 |
| **U-5** | `EventKind 0x08 AnyEvent / 0x2F ElapsedScenarioTime / 0x3C / 0x3D` 的抛出点 | **未闭环** | 本次只钉住轮询器的 10 个 kind 与 `0x17` 的 2 个点 | 以"置位 `GetFlags` bit 0x10 的 kind 集合 ∖ 已闭环集合"为差集，机械筛 `dumps/xrefs_poller_chain.txt` 的全部 73 个 `call 0x6E53A0` 点与其前置 `push imm` |
| **U-6** | `RaiseEvent` 尾部 `[edi+0x34]`（宿主）字段归属与 `call 0x5F5B50` 的语义 | **未闭环** | `pTagOwner` 在每帧路径恒为 NULL，只有对象触发路径会走到；`0x5F5B50` 未在本专章反汇编 | 反汇编 `0x5F5B50` 及其调用上下文；对 `ObjectClass/TechnoClass` 布局做偏移核对 |
| **U-7** | 锁存位 `[Scenario+0x34AA / 0x34AB / 0x34BE]` 的置位来源与 MP 确定性 | **未闭环**（MP 风险 [推演]） | 本专章只证"轮询器读它们" | 扫全镜像对这三处的写点（含经 `ecx=[0xA8B230]` 的间接寻址），判定是否含本机输入路径 |
| **U-8** | AITrigger 门控 `TeamDelayTimer` 的精确周期与多端一致性 | **未闭环** | 本专章只证直呼点位置，未反汇编门控比较 | 与 `house_team_ai_update.md` §2.5 交叉，必要时反汇编 `0x4F8A00` 附近的 `TimerStruct` 比较 |

> **本专章不做的推测**：所有"名称/语义"结论都对齐到 YRpp 具名地址或已登记文档；凡无字节证据的字段语义一律停在 [推演]/未闭环，不使用"推测/应有"充当结论。

---

## 9. 改动文件清单 + 门禁命令输出

### 9.1 改动文件清单（全部新建，未改动任何既有文件）

| 路径 | 类型 | 说明 |
|---|---|---|
| `docs/re/trigger_runtime_deep_dive.md` | **新建（本文件）** | 触发器运行时语义与确定性专章 |
| `out/re_work/triggers_deep/claims.txt` | 新建 | **174 条**可机读字节断言（`0xVA = HEXBYTES # 注释`） |
| `out/re_work/triggers_deep/td.py` | 新建 | 反汇编/交叉引用工具（fn/dump/dis/who/abs/vt/ctx/bytes） |
| `out/re_work/triggers_deep/scan_prng2.py` | 新建 | 重同步线性扫描：触发器子系统全部 Randomizer 直呼点 |
| `out/re_work/triggers_deep/decode_flags.py` | 新建 | `TEventClass::GetFlags`/`TActionClass::GetFlags` selector+跳表位语义解码 |
| `out/re_work/triggers_deep/dump_all.py` | 新建 | 批量产出 dumps 与 xref 表 |
| `out/re_work/triggers_deep/mkclaims.py` / `addclaims2.py` / `addclaims3.py` | 新建 | claims 生成脚本（可重跑复现） |
| `out/re_work/triggers_deep/_stats.py` / `_whichaction.py` / `_acthelpers.py` / `_crc2.py` / `_ai_fns.py` / `_scan3.py` / `_calls_6e17.py` / `_fns.py` | 新建 | 调用点统计 / 动作块归属 / 动作→辅助映射 / RNG 状态引用负证 / AI 簇定位 等一次性分析脚本 |
| `out/re_work/triggers_deep/dumps/*.txt` | 新建（19 个） | 原始反汇编与 xref dump |

**未触碰（只读）**：`ra2youli/**`、`ra2render/**`、`REVERSE_ENGINEERING_AND_PATCHES.md`、`docs/re/*.md` 既有 88 份文档、`YRpp/*.h`、`out/reverse/**`、`tools/**`。

### 9.2 门禁命令与输出（实跑）

**① 全库基线：`python tools/verify_anchors.py`**

```
[基线完整性审计]
  [PASS] .text 原始段哈希: c0368a179f6e1a0f85bf94ebeb3a3e62efc8b1a2000abe164e5e1c61714eb738 (口径: raw(SizeOfRawData=0x3E0000))
  [INFO] PE头特征判定 : RA2OPT_PERF_APPLIED (0xAE=0x20, Stack=4MB, .text未变) (DllChar: 0x20, StackReserve: 0x400000)
  [PASS] .detour 原生签名: 40 00 00 00 44 74 72 00 ('@\0\0\0Dtr\0' @ VA 0xb93000) -> 严禁写入/注入原则确立
回归汇总 : 断言总数 323 条 | PASS: 323 (100.00%) | FAIL: 0 | NOREAD: 0
★ 最终裁决 : [100% ALL PASS] 全库决定性锚点与二进制基线完全一致，生产环境可安全放行！
```

**② 本专章断言：`python tools/audit_bytes.py out/re_work/triggers_deep/claims.txt`**

```
合计 174 条：OK=174  MISMATCH/NOREAD=0
```

（样例行，含反汇编回显）

```
0x55dc9e   e8 0d d3 ff ff         OK   MainLogicFrame: call 0x55AFB0 ...            | call 0x55afb0
0x72646a   e8 71 63 f3 ff         OK   ResetTimers: call 0x65C7E0 RandomRanged(0,arg) | call 0x65c7e0
0x64de3f   e8 3c e9 00 00         OK   frame CRC 0x64DAB0: call Randomizer::Random() | call 0x65c780
0x6e55c0   8b 44 24 04 8b 51 28   OK   TagClass::AddTrigger: HEAD insert             | mov eax, [esp + 4]
```

---

## 附：`claims.txt` 174 条断言的主题分布

| 主题 | 条数 | 覆盖 |
|---|---|---|
| 每帧节拍与轮询器 | 31 | 调用点、向量字段、10 个事件号、锁存位、游标、早退 |
| 条件求值链 | 27 | `RegisterEvent`/`HasOccured`/`Execute`/`FireActions`/`ResetTimers`/`Destroy` 的调用点 |
| PRNG 消费 | 14 | 4 个函数 9 条指令 + 实例基址 + CRC 折入 |
| 顺序与结构 | 18 | 向量尾接、链表头插、位图位序、游标回退、存档原序 |
| 生命周期 | 26 | ctor / dtor / Destroy / GetInstance / 延迟队列 / 抽干 |
| Flags 位语义 | 12 | `GetFlags` 4 组表 + `TagTypeClass/TriggerTypeClass` 链式 OR + 动作 flags |
| AITrigger | 9 | 两个直呼点、概率门、Team 计数扫描 |
| EVA / 动作 | 3 | 动作 `0x15` → `0x752480` |
| 负证锚点 | 34 | RNG 状态不读、事件链零消费、无地址排序等 |

> 合计 174 条（部分条目同时服务两个主题，故行和大于 174）。
