# Trigger / Tag 生命周期 ABI 补全（R-08）

> **目标二进制**：`ra2bench\gamemd.exe`（YR 1.001，MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x400000`，FileOffset = VA − 0x400000）
> 【W3 勘误 E-W3-01】原句 `FileOffset = VA − 0x400000` 仅在 `.text/.rdata/.data` 成立；
> 通用式为 `FileOffset = 段.PointerToRawData + (VA − 段.VirtualAddress)`，
> 本镜像 `.rsrc`/`.detour` 为 `VA − 0x6FC000`。依据：out/re_work/_lead_baseline/W3/LEAD_ERRATUM_E-W3-01_fileoffset_rule.md；分级：[实证]
> **证据分级**：`[实证]` VA+FileOffset+机器码+反汇编，`claims.txt` 可用 `python tools/audit_bytes.py` 复算（**55/55 OK**）；`[推演]` 由相邻实证按 x86/MSVC 惯例推导；`[待实测]` 需真机。
> **对照源**：`YRpp/TriggerClass.h`、`TagClass.h`、`TriggerTypeClass.h`、`TagTypeClass.h`、`AITriggerTypeClass.h`、`AbstractClass.h`、`AbstractTypeClass.h`、`GeneralStructures.h`（只读）
> **上位**：`trigger_runtime_deep_dive.md`（运行时语义）、`trigger_system_manifest.md`（派发表）、`ARCHITECTURE_ATLAS.md` §14；本文只补 **结构体 ABI + 锚点字节**，不改上述已定谳语义。
> **产物**：`out/re_work/re_sprint/trigger_tag_abi/{claims.txt,abi_bytes.json,abi_bytes.txt,abi_disasm.txt,dump_abi*.py}`

---

## 0. 结论速览

| # | 结论 | 等级 |
|---|---|---|
| **A1** | `TriggerClass` **Size=0x48**（`0x726930: B8 48 00 00 00 C3`），字段布局与 YRpp **完全一致**：`Type@+0x24 / NextTrigger@+0x28 / House@+0x2C / Destroyed@+0x30 / Timer@+0x34(12B) / OccuredEvents@+0x40 / Enabled@+0x44`。`+0x44=Enabled`、`+0x30=Destroyed` 定谳成立。 | [实证] |
| **A2** | `TagClass` **Size=0x38**（`0x6E5890: B8 38 00 00 00 C3`；`new(0x38)`@`0x6E52C5`），与 YRpp 一致：`Type@+0x24 / FirstTrigger@+0x28 / InstanceCount@+0x2C / DefaultCoords@+0x30 / Destroyed@+0x34 / IsExecuting@+0x35`。**TagClass 无 +0x44**；`+0x44` 属 TriggerClass::Enabled，勿混。 | [实证] |
| **A3** | `TimerStruct` 三字段钉死：`StartTime@+0x34`、**匿名 @+0x38**（ResetTimers 会写、CalculateChecksum **不读**）、`TimeLeft@+0x3C`。YRpp `int :32` 匿名位与此吻合。 | [实证] |
| **A4** | `AITriggerTypeClass` **Size=0x110**（`0x41FFE0: B8 10 01 00 00 C3`）。**勘误 E-AIT-1**：Atlas §11 记 `0x420990: mov eax,0x100; ret` 与实测冲突——`0x420990` 实为 `mov [esi+0xc],0x7E3278`（vtable 写），Size 脚注 VA/返回值双错。ctor 写点覆盖至 `+0x108`，`+0x10C` 为尾部未知 dword。 | [实证] |
| **A5** | 事件判定链 `0x71E940–0x71F700` **零 PRNG**（对 `0x65C000–0x65D000` 的 `E8` 相对调用 0 命中）[负证]。PRNG 消费点与任务已知清单**逐条一致**：T1 `0x72646A`、T2 `0x6E2CEB/4E/5A/B0`(**4× Random**)、T3 `0x6DE80F`、T4/T5 `0x6F0B01/0x6F0CEE`。 | [实证] |
| **A6** | ctor/LoadFromINI/dtor/GetInstance 锚点已齐；`TriggerClass` 的 **虚析构入口未定位**（vtable 多重继承 4 vptr，槽位映射未闭环）→ [待实测]。 | [实证]+[待实测] |

---

## 1. TriggerClass ABI（对照 YRpp）

### 1.1 字段布局（Size 0x48）

| 偏移 | 大小 | 字段 | YRpp | 取证 |
|---|---|---|---|---|
| 0x00/04/08/0C | 16 | 4× vptr（`0x7F5858 / 0x7F583C / 0x7F5834 / 0x7F582C`） | AbstractClass 多继承 | ctor `0x725FCE` |
| 0x10..0x23 | 20 | AbstractClass 基：`UniqueID / AbstractFlags / unknown_18 / RefCount / Dirty+pad` | 一致 | YRpp `AbstractClass.h:162-167` |
| **0x24** | 4 | `Type` (TriggerTypeClass*) | `Type` | ctor `0x725FAF: 89 46 24` |
| **0x28** | 4 | `NextTrigger` | `NextTrigger` | ctor `0x725FB2: 89 5E 28`；链步进 `[x+0x28]` |
| **0x2C** | 4 | `House` | `House` | ctor `0x725FB5`；`GetHouse 0x726910: 8B 41 2C` |
| **0x30** | 1 | `Destroyed` | `Destroyed` | ctor `0x725FB8: 88 5E 30`；Destroy `0x726723: C6 46 30 01`；门 `0x7264CF` |
| 0x31 | 3 | pad | `align_31[3]` | — |
| **0x34** | 4 | `Timer.StartTime` | `TimerStruct.StartTime` | ctor `0x725FC4: 89 4E 34`（=CurrentFrame `0xA8ED84`） |
| **0x38** | 4 | `Timer.<匿名>` | `int :32` | ResetTimers 写 `0x72643A/0x72648E: 89 xx 04`；**checksum 跳过** |
| **0x3C** | 4 | `Timer.TimeLeft` | `TimerStruct.TimeLeft` | ctor `0x725FC1: 89 5E 3C=0`；checksum `0x7267E4: 8B 46 3C` |
| **0x40** | 4 | `OccuredEvents` 位图 | `DWORD` | ctor `0x725FC7: 89 5E 40=0`；位操作 `0x7266C0/0x7266E0/0x726700` |
| **0x44** | 1 | `Enabled` | `bool` | ctor `0x725FCA: C6 46 44 01`；门 `0x7264C4: 8A 46 44` |
| 0x45 | 3 | pad | `padding_45[3]` | Size 闭合 `0x34+12+4+1+3=0x48` |

**门控语义（双点一致）[实证]**：
- `RegisterEvent 0x7264C0`：`Enabled==0 → ret0`（`0x7264C4`），`Destroyed!=0 → ret0`（`0x7264CF`）
- `FireActions 0x7265C0`：同序同义（`0x7265C3/0x7265CA`）
- `Enable 0x7268F0`：`[ecx+0x44]=1` 后 **tail-jmp** `ResetTimers`（启用即重置计时器，可能烧 PRNG）
- `Disable 0x726900`：`[ecx+0x44]=0`

### 1.2 方法锚点（VA + 首字节）

| 方法 | VA | FileOffset | 首字节 / 要点 |
|---|---|---|---|
| ctor | `0x725FA0` | `0x325FA0` | `53 56 8B F1 E8 C7 A1 CE FF` → `AbstractClass::ctor 0x410170` |
| GetInstance | `0x726630` | `0x326630` | 扫 `Array 0xA8EAE8` 比 `[t+0x24]==pType`；未命中 `push 0x48; call 0x7C8E17`（CRT `_new`）→ ctor |
| PointerExpired | `0x726690` | `0x326690` | 清 `Type@+0x24` / 头摘 `NextTrigger@+0x28` / 清 `House@+0x2C` |
| MarkEventAsOccured | `0x7266C0` | `0x3266C0` | `or [eax+0x40], 1<<idx` |
| MarkEventAsNotOccured | `0x7266E0` | `0x3266E0` | `and [eax+0x40], ~(1<<idx)` |
| HasEventOccured | `0x726700` | `0x326700` | 测试 `+0x40` |
| Destroy | `0x726720` | `0x326720` | `[esi+0x30]=1` → 尾接延迟队列 `0xB0F698` |
| HasBeenDestroyed | `0x726780` | `0x326780` | `mov al,[ecx+0x30]` |
| CalculateChecksum | `0x726790` | `0x326790` | 校验 Type/NextTrigger/Destroyed/Enabled/Timer.Remaining/OccuredEvents |
| GetClassID | `0x726820` | `0x326820` | CLSID ← `0x7E97E0` |
| **Load** | `0x726860` | `0x326860` | `ret 8`；重置 4 vptr；`0x6CF240` 读 `+0x24/+0x28/+0x2C` |
| **Save** | `0x7268D0` | `0x3268D0` | `ret 0xC`；仅 `call 0x410320`（基类）——**标量是否入档见 §5 U-1** |
| Enable / Disable | `0x7268F0 / 0x726900` | — | 见上 |
| GetHouse / SetHouse | `0x726910 / 0x726920` | — | `[ecx+0x2C]` |
| Size | `0x726930` | `0x326930` | `B8 48 00 00 00 C3` |
| WhatAmI | `0x726940` | `0x326940` | `mov eax,0x26`（`AbstractType::Trigger=0x26`） |
| ResetTimers | `0x726400` | — | PRNG 装填（§4） |
| RegisterEvent | `0x7264C0` | — | 条件求值唯一入口 |
| FireActions | `0x7265C0` | — | `FirstAction = [Type+0xB0]`；`call 0x6DD8B0` |
| **虚析构** | **未定位** | — | [待实测]；vtable 0x7F5858 为 4 重继承，槽位含 dtor complete/deleting，映射未闭环 |

### 1.3 TriggerTypeClass（基类 `AbstractTypeClass` 0x98 字节）

ctor `0x726C80` 写点 [实证]：`ArrayIndex@+0x98=-1`；`Difficulty[3]@+0x9C..0x9E=1,1,1`；`Enabled@+0x9F=1`；`MustTransfer@+0xA0=0`；`House@+0xA4=0`；`NextTrigger@+0xA8=0`；`FirstEvent@+0xAC=0`；`FirstAction@+0xB0=0`。与 YRpp **逐字段一致**。
`LoadFromINIList 0x7275D0`：枚举 `TriggerTypeClass::Array 0x8B4178`（Count `0x8B4188`），名字串 `0x817474`/`0x817694` 过滤 `<none>`。

---

## 2. TagClass ABI（对照 YRpp）

### 2.1 字段布局（Size 0x38）

| 偏移 | 大小 | 字段 | YRpp | 取证 |
|---|---|---|---|---|
| 0x00..0x23 | 36 | 4× vptr + AbstractClass 基 | 一致 | ctor `0x6E4E07` |
| **0x24** | 4 | `Type` (TagTypeClass*) | `Type` | ctor `0x6E4DF0: 89 7E 24`；RaiseEvent `0x6E53D2` |
| **0x28** | 4 | `FirstTrigger` 链表头 | `FirstTrigger` | ctor `0x6E4DF3: 89 5E 28=0`；**头插** `0x6E55C0` |
| **0x2C** | 4 | `InstanceCount` | `int` | ctor `0x6E4DF6: 89 5E 2C=0` |
| **0x30** | 4 | `DefaultCoords` (CellStruct) | `CellStruct` | ctor `0x6E4DF9/0x6E4DFE`：**初值 = 全局 `[0xB0E700]`**（非 0,0） |
| **0x34** | 1 | `Destroyed` | `bool` | ctor `0x6E4E01: 88 5E 34=0`；Destroy `0x6E5233: C6 46 34 01` |
| **0x35** | 1 | `IsExecuting` 重入锁 | `bool` | ctor `0x6E4E04: 88 5E 35=0`；RaiseEvent `0x6E53BC: 8A 45 35` |
| 0x36 | 2 | pad | `padding_36[2]` | Size 闭合 0x38 |

### 2.2 关键方法

| 方法 | VA | 字节要点 |
|---|---|---|
| ctor | `0x6E4DE0` | 见上；4 vptr `0x7F44E0..`；尾接 `TagClass::Array 0xB0E720` |
| GetInstance | `0x6E52A0` | 线性扫 Array 比 `[tag+0x24]==pType`；`push 0x38; call 0x7C8E17` → ctor |
| Destroy | `0x6E5230` | `[esi+0x34]=1` → 尾接延迟队列 `0xB0F698` |
| **AddTrigger** | `0x6E55C0` | `8B 44 24 04 / 8B 51 28 / 89 50 28 / 89 41 28 / C2 04 00` ⇒ `p->Next=FirstTrigger; FirstTrigger=p` **头插** |
| RemoveTrigger | `0x6E55D0` | （YRpp；链表摘除） |
| RaiseEvent | `0x6E53A0` | `IsExecuting@+0x35` / `Destroyed@+0x34` / `Type@+0x24` 三重 early-out；`esi=[ebp+0x28]` 走链 |
| PointerExpired | `0x6E5610` | 清 Type、头摘 FirstTrigger；Type 空则 `Destroyed=1` + 入延迟队列 |
| ShouldReplace | `0x6E57C0` | 走 `[x+0x28]` 链查 `TriggerType+0xA0`（MustTransfer） |
| Load / Save | `0x6E5730 / 0x6E57A0` | Load 重置 4 vptr + 读 `+0x24/+0x28`；Save 仅基类 `0x410320` |
| Size / WhatAmI | `0x6E5890 / 0x6E58A0` | `B8 38 00 00 00 C3` / `mov eax,0x2C` |
| dtor | `0x6E4F60` | 重置 vptr → `AnnounceExpiredPointer` → 按 `GetFlags` 从 `0x8B40C8`/`0x8B41A8` 摘除 |

**`AddTrigger` 头插字节（定谳）**：
```
006E55C0  8B 44 24 04    mov eax, [esp+4]     ; pTrigger
006E55C4  8B 51 28       mov edx, [ecx+0x28]  ; FirstTrigger
006E55C7  89 50 28       mov [eax+0x28], edx  ; p->Next = head
006E55CA  89 41 28       mov [ecx+0x28], eax  ; head = p
006E55CD  C2 04 00       ret 4
```

### 2.3 TagTypeClass

ctor YRpp 声明 `0x5447C0` —— **冲突**：该址写 `+0x294` 级字段并 `call 0x5F7090`，尺寸与 `HouseTypeClass` 同族，**不是** TagTypeClass。[实证·反证] 真 ctor **[待实测]**。
已定字段（由使用点反推 + YRpp）：`ArrayIndex@+0x98`、`Persistence@+0x9C`（RaiseEvent `0x6E5408: cmp edx,2`）、`FirstTrigger@+0xA0`。
`LoadFromINIList 0x6E5ED0`：枚举 `TagTypeClass::Array 0xB0E780`（Count `0xB0E790`），Section 名全局 `0x7F4550`。

---

## 3. AITriggerTypeClass 关键字段（P2 补全）

基类 `AbstractTypeClass` **0x98**。Size **0x110**（`0x41FFE0`）。ctor `0x41E350` 写点逐字段 [实证]：

| 偏移 | 类型 | 字段 | ctor 初值 | 写点 |
|---|---|---|---|---|
| 0x98 | int | `ConditionType` | **-1** | `0x41E363` |
| 0x9C | int | `IsGlobal` | 0 | `0x41E3B9` |
| 0xA0 | int | `OwnerHouseType` | 0 | `0x41E3BF` |
| 0xA4 | bool | `IsEnabled` | 0 | `0x41E3C5` |
| 0xA8 | int | `HouseIndex` | **-1** | `0x41E369` |
| 0xAC | int | `SideIndex` | 0 | `0x41E3CB` |
| 0xB0 | int | `TechLevel` | 0 | `0x41E3D1` |
| 0xB4 | int | `unknown_B4` | （ctor 不写） | YRpp 命名吻合 |
| 0xB8 | double | `Weight_Current` | **1.0** | `0x41E374/0x41E386`（hi=`0x3FF00000`） |
| 0xC0 | double | `Weight_Minimum` | **1.0** | 同上 |
| 0xC8 | double | `Weight_Maximum` | **1.0** | 同上 |
| 0xD0 | bool | `IsForSkirmish` | 0 | `0x41E3D7` |
| 0xD1 | bool | `IsForBaseDefense` | 0 | `0x41E3DD` |
| 0xD2..D4 | bool×3 | `Enabled_Easy/Normal/Hard` | **1,1,1** | `0x41E39A` |
| 0xD8 | ptr | `ConditionObject` | 0 | `0x41E3E3` |
| 0xDC | ptr | `Team1` | 0 | `0x41E3E9`；ConditionMet `0x41E726: 8B 8E DC 00 00 00` |
| 0xE0 | ptr | `Team2` | 0 | `0x41E3EF`；ConditionMet `0x41E73A: 8B 86 E0 00 00 00` |
| 0xE4 | 4×8B | `Conditions[4]` | 清零 `rep stosd ecx=8` | `0x41E3B3` lea / `0x41E41C` |
| 0x104 | int | `TimesExecuted` | 0 | `0x41E3F5` |
| 0x108 | int | `TimesCompleted` | 0 | `0x41E3FB` |
| 0x10C | int | `unknown_10C` | （ctor 不写） | Size 0x110 容器内尾部 |

**浮点扫描**（`fmul/fld/fstp/fild/movsd/fdiv/...`，覆盖 `0x41E000–0x41F500`）：权重字段以 **double 1.0** 字面量初始化（非浮点运算路径）；`0x41E160–0x41E2E5` 为独立常量表计算（写 `0x88A0xx` 全局），**不读写 Weight_* 字段**；`0x41E94C/0x41E986/0x41F056…` 为 `fild` 整数转浮点，属条件比较。⇒ Weight 消费点在 `0x6F0AB0` 簇的加权挑选（T5），不在 ConditionMet。[实证]

---

## 4. PRNG 消费点字节级复核（与 trigger_runtime_deep_dive 对齐）

| # | 点 | 指令 VA | 机器码 | 目标 | 次数 | 与 deep_dive |
|---|---|---|---|---|---|---|
| T1 | ResetTimers RandomDelay 装填 | `0x726464/0x72646A` | `8D 88 18 02 00 00 / E8 71 63 F3 FF` | `0x65C7E0` RandomRanged | 1/事件 | 一致 |
| T2a | MeteorShower | `0x6E2CE5/0x6E2CEB` | `8D 88 18 02 00 00 / E8 90 9A F7 FF` | **`0x65C780` Random()** | 4 | 一致 |
| T2b | 同上 | `0x6E2D48/0x6E2D4E` | `8B CE / E8 2D 9A F7 FF` | `0x65C780` | | 一致 |
| T2c | 同上 | `0x6E2D5A` | `E8 …` | `0x65C780` | | 一致 |
| T2d | 同上 | `0x6E2DAA/0x6E2DB0` | `8D 88 18 02 00 00 / E8 CB 99 F7 FF` | `0x65C780` | | 一致 |
| T3 | PlaySoundEffectRandom | `0x6DE809/0x6DE80F` | `8D 88 18 02 00 00 / E8 CC DF F7 FF` | `0x65C7E0` | 1 | 一致 |
| T4 | AITrigger 概率门 | `0x6F0AFB/0x6F0B01` | `8D 88 18 02 00 00 / E8 DA BC F6 FF` | `0x65C7E0` | 1 | 一致 |
| T5 | AITrigger 加权挑选 | `0x6F0CE8/0x6F0CEE` | `81 C1 18 02 00 00 / E8 ED BA F6 FF` | `0x65C7E0` | 1 | 一致 |
| — | **事件判定链** `0x71E940–0x71F700` | — | — | — | **0** | 一致（负证） |

细节校准：
- 全部实例均为 `ScenarioClass::Random = [0xA8B230]+0x218`（`lea ecx,[reg+0x218]` / `add ecx,0x218` 紧邻）。
- **T2 走 `Random()`（`0x65C780`），T1/T3/T4/T5 走 `RandomRanged()`（`0x65C7E0`）** —— deep_dive 表 T2 写「4 次 Random()」准确；T1 行的「RandomRanged」准确。
- 装填时长公式复核：`Duration = 15 × ((arg>>1) + RandomRanged(0,arg))`，指令 `0x726471–0x726494`（`cdq/sar 1/add/lea *3/lea *5`）与 deep_dive §3.3 **逐字一致**。
- `CalculateChecksum 0x726790` 读 `Timer` 时只用 `StartTime@+0x34` 与 `TimeLeft@+0x3C`，**跳过 +0x38**（`0x7267E1/0x7267E4`）——匿名 dword 不进校验和，与 YRpp `int :32` 一致。

---

## 5. 未闭环 / 冲突登记

| ID | 项 | 现状 | 下一步 |
|---|---|---|---|
| **E-AIT-1** | Atlas §11 `AITriggerTypeClass Size=0x100 @ 0x420990` | **实测 Size=0x110 @ 0x41FFE0**；`0x420990` 是 vtable 字面量写 | 请 Lead 出 Atlas 勘误补丁块（R 不代写 Atlas） |
| **U-1** | `TriggerClass::Save 0x7268D0` / `TagClass::Save 0x6E57A0` 只调基类 `0x410320`，未见标量/指针写出 | 与 Load 不对称（Load 读 `+0x24/+0x28/+0x2C`） | 读 `0x410320` 体或真机 dump 存档块；`[待实测]` |
| **U-2** | `TriggerClass` 虚析构 VA | vtable 4 vptr，槽位含 MSVC complete/deleting dtor，映射未钉 | 从 `0x726950` 邻域或 RTTI 链解槽位 |
| **U-3** | YRpp `TagTypeClass::ctor 0x5447C0` 与字节冲突 | 该址为 HouseTypeClass 尺寸函数 | 真 ctor 定位；YRpp 头文件勘误建议 |
| **U-4** | `TagClass.DefaultCoords` 初值取全局 `[0xB0E700]` | 该全局写点/语义未查 | 查 `0xB0E700` 的写者（地图默认格？） |
| **U-5** | `Timer+0x38` 匿名 dword 的运行时语义 | ResetTimers 写入（值=栈上 arg），checksum 跳过 | 动态观察；联机是否敏感 `[待实测]` |

---

## 6. 与 YRpp 对照总表

| 结构 | YRpp | 实测 | 判定 |
|---|---|---|---|
| TriggerClass Size | （无常量；字段到 `padding_45`） | `0x48` | **一致** |
| TriggerClass 字段 | Type/NextTrigger/House/Destroyed/Timer/OccuredEvents/Enabled | 同左，偏移全钉 | **一致** |
| TagClass Size | （字段到 `padding_36`） | `0x38` | **一致** |
| TagClass 字段 | Type/FirstTrigger/InstanceCount/DefaultCoords/Destroyed/IsExecuting | 同左；DefaultCoords 初值全局 | **一致**（初值语义为新知） |
| TriggerTypeClass 字段 | ArrayIndex/Difficulty[3]/Enabled/MustTransfer/House/NextTrigger/FirstEvent/FirstAction | ctor 写点全钉 | **一致** |
| TagTypeClass 字段 | ArrayIndex/Persistence/FirstTrigger | 使用点反推一致；ctor VA 冲突 | **字段一致 / ctor VA 冲突** |
| AITriggerTypeClass 字段 | 22 项至 `unknown_10C` | ctor 写点全钉 | **一致** |
| AITriggerTypeClass Size | （无） | `0x110` | Atlas 0x100 **冲突（E-AIT-1）** |
| TimerStruct | StartTime / :32 / TimeLeft | +0x34/+0x38/+0x3C | **一致** |

---

## 7. 产物与复算

```
out/re_work/re_sprint/trigger_tag_abi/
  claims.txt        55 条字节断言
  abi_bytes.json    25 站点原始字节 + 反汇编 + PRNG/浮点扫描
  abi_bytes.txt     人类可读 dump
  abi_disasm.txt    vtable 槽位 + 全量反汇编（ctor/dtor/Load/AITrigger）
  dump_abi.py       站点抓取 + PRNG/浮点扫描
  dump_abi2.py      vtable + 深 dump
  dump_abi3.py      Size/dtor/SaveLoad
  dump_abi4.py      Size thunk 扫描
  mkclaims.py       claims 生成
```

门禁：
```
python tools/audit_bytes.py out/re_work/re_sprint/trigger_tag_abi/claims.txt
# 合计 55 条：OK=55  MISMATCH/NOREAD=0
```

> 本文为 **R-08 交付**，写域仅限本文件与 `out/re_work/re_sprint/trigger_tag_abi/**`；未改动 `trigger_runtime_deep_dive.md` / `trigger_system_manifest.md` / Atlas / 台账 / ra2render。
