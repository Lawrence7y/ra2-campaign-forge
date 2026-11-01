# RE-ATLAS · 地址总表 (INDEX)

> 以 VA 为主键的可查询索引。每行：VA → 名称 → 作用 → 证据 → 置信度。
> 置信度：**实证**（本线字节复算）/ **语料实证**（他线做过字节复算且未翻案）/
> **推演** / **社区**。
> 生成口径与校验器见 `tools/`；数据快照见 `evidence/`。

**目标二进制**：`ra2youli/gamemd.exe`
sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`
ImageBase `0x00400000`，入口 `0x007CD80F`。

**规模**：语料命名点 1,304 个（.text 内）；递归遍历发现函数入口 15,224 个；
命名覆盖率 **3.62%**（551/15,224，保守下界）。

---

## A. 全局单例与标量

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x00887324` | `TacticalClass*` | 战术主视口单例指针（一级解引用） | ATLAS §11.1 | 社区 |
| `0x0087F7E8` | `MapClass` 实例 | 全图网格/瓦片/迷雾宿主 | ATLAS §11.1；`0x0072A0AE mov ecx,0x87F7E8` | 实证（旁证） |
| `0x00A8B230` | `ScenarioClass*` | 局内剧本、航点、触发器、RNG(+0x218) | ATLAS §11.1 | 社区 |
| `0x008871E0` | `RulesClass*` | rulesmd.ini 全局规则单例；**实例尺寸 `0x18C0`**（`push 0x18C0`@`0x0052BABE` → `operator new` `0x7C8E17` → 构造器 `0x665650`）；构造器最高字段止于 `+0x18BC` | YRpp `RulesClass.h:85`；kb/30 §15.2 | **实证**（分配立即数 + 字段上界 + 4 字节尾隙三重吻合） |
| `0x00887048` | `INI_Rules` | **指针**，指向 rulesmd.ini 的 `CCINIClass` | YRpp `CCINIClass.h:290` | 社区 |
| `0x00887180` | `INI_Art` | artmd.ini 的 `CCINIClass`（**对象**，非指针） | YRpp `:293`；`c7 05 80 71 88 00 f4 1a 7e 00` | 实证（写入点）+ 社区（命名） |
| `0x00887128` | `INI_AI` | aimd.ini 的 `CCINIClass` | YRpp `:292`；`c7 05 28 71 88 00 f4 1a 7e 00` | 实证（写入点）+ 社区 |
| `0x00887208` | `INI_UIMD` | uimd.ini 的 `CCINIClass` | YRpp `:294`；`c7 05 08 72 88 00 f4 1a 7e 00` | 实证（写入点）+ 社区 |
| `0x008870C0` | `INI_RA2MD` | ra2md.ini 的 `CCINIClass` | YRpp `:295`；`c7 05 c0 70 88 00 f4 1a 7e 00` | 实证（写入点）+ 社区 |
| `0x00887058` | 未命名 `CCINIClass` | 第 6 个静态实例 | `c7 05 58 70 88 00 f4 1a 7e 00` | 实证（写入点） |
| `0x0089F518` | 未命名 `CCINIClass` | 第 7 个静态实例 | `c7 05 18 f5 89 00 f4 1a 7e 00` | 实证（写入点） |
| `0x00B7882C` | INI "未找到"哨兵 | `GetSection`/键查找未命中时返回的共享空对象（**不是 NULL**），19 处 `.text` 引用 | `0x0052690C` / `0x00526A01` / `0x00528B60` / `0x0052B4A8` | **实证** |
| `0x0081F7B4` | CRC32 表 | 256 项，与 `0xEDB88320` 标准反射多项式生成表**逐项相等** | `tools/dump_ini_nodes.py`（全 256 项比对） | **实证** |
| `0x00A83D4C` | `HouseClass::Player` | 本地人类玩家阵营指针 | ATLAS §11.1；`0x0050B71A` 读后严格比对 | **实证** |
| `0x00A80228` | `HouseClass::Array` | 参战阵营动态向量 | ATLAS §11.1 | 社区 |
| `0x0087E8B8` | `PathFinder` | 寻路工作区（生成戳 +0x28） | ATLAS §11.1 | 社区 |
| `0x00887888` | `SpatialGrid` | 20×20 粗空间网格，400 桶×24B | ATLAS §11.1 | 社区 |
| `0x00A8ED84` | `CurrentFrame` | 全局逻辑帧计数器 | claims `0x0055DE73/79/81` 三处字节断言 | **实证** |
| `0x008464AC` | `VoicesEnabled` | 音频主开关 | ATLAS §11.1 | 社区 |
| `0x00A8B238` | 游戏模式标志 | 非 0 ⇒ 联机/多人；0 ⇒ 单人 | 本线 `0x0050B6F0`：`a1 38 b2 a8 00` + `85 c0` + `75 1d` | **实证**（本线新增） |
| `0x00A8B262` | `ShortGame` 全局镜像 | 载入后从 `RulesClass+0x14B6` 拷贝；**50 处取值引用** | kb/30 §15.3；拷贝 `0x0052D1F5` | **实证** |
| `0x00A8B25C` | `Money` 全局镜像 | 从 `RulesClass+0x1484` 拷贝；38 处取值引用 | kb/30 §15.3；拷贝 `0x0052D159` | **实证** |
| `0x00A8B270` | `UnitCount` 全局镜像 | 从 `RulesClass+0x1494` 拷贝；40 处取值引用 | kb/30 §15.3；拷贝 `0x0052D165` | **实证** |
| `0x00A8B268` | `GameSpeed` 全局镜像 | 从 `RulesClass+0x14A0` 拷贝；43 处取值引用 | kb/30 §15.3；拷贝 `0x0052D17D` | **实证** |
| `0x00A8B320` | `MCVRedeploys` 全局镜像 | 从 `RulesClass+0x14B8` 拷贝；44 处取值引用 | kb/30 §15.3；拷贝 `0x0052D22C` | **实证** |
| `0x00A8B31F` | `FogOfWar` 全局镜像 | 从 `RulesClass+0x14B7` 拷贝；22 处取值引用 | kb/30 §15.3；拷贝 `0x0052D219` | **实证** |
| `0x00A8B260` | `BridgeDestruction` 全局镜像 | 从 `RulesClass+0x14AC` 拷贝；27 处取值引用 | kb/30 §15.3；拷贝 `0x0052D1A1` | **实证** |
| `0x00A8B258` | `Bases` 全局镜像 | 从 `RulesClass+0x14AF` 拷贝；39 处取值引用 | kb/30 §15.3；拷贝 `0x0052D1AD` | **实证** |
| `0x00A8B261` | `Crates` 全局镜像 | 从 `RulesClass+0x14B1` 拷贝；41 处取值引用 | kb/30 §15.3；拷贝 `0x0052D1B9` | **实证** |
| `0x00A8B31E` | `CaptureTheFlag` 全局镜像 | 从 `RulesClass+0x14B2` 拷贝；4 处取值引用 | kb/30 §15.3；拷贝 `0x0052D1C5` | **实证** |
| `0x00A8B31D` | `HarvesterTruce` 全局镜像 | 从 `RulesClass+0x14B3` 拷贝；23 处取值引用 | kb/30 §15.3；拷贝 `0x0052D1D1` | **实证** |
| `0x00A8B26C` | `MultiEngineer` 全局镜像 | 从 `RulesClass+0x14B4` 拷贝；21 处取值引用 | kb/30 §15.3；拷贝 `0x0052D1DD` | **实证** |
| `0x00A8B31C` | `AlliesAllowed` 全局镜像 | 从 `RulesClass+0x14B5` 拷贝；12 处取值 + 4 处取址 | kb/30 §15.3；拷贝 `0x0052D1E9` | **实证** |
| `0x00A8B263` | `SuperWeaponsAllowed` 全局镜像 | 从 `RulesClass+0x14B9` 拷贝；41 处取值引用 | kb/30 §15.3；拷贝 `0x0052D201` | **实证** |
| `0x00A8B264` | `BuildOffAlly` 全局镜像 | 从 `RulesClass+0x14BA` 拷贝；35 处取值引用 | kb/30 §15.3；拷贝 `0x0052D20D` | **实证** |
| `0x00A8B278` | `AIDifficulty` 全局镜像 | 从 `RulesClass+0x14A4` 拷贝；17 处取值引用 | kb/30 §15.3；拷贝 `0x0052D189` | **实证** |
| `0x00A8B274` | `AIPlayers` 全局镜像 | 从 `RulesClass+0x14A8` 拷贝；36 处取值引用 | kb/30 §15.3；拷贝 `0x0052D195` | **实证** |
| `0x00822CF4` | `TechLevel` 全局镜像 | 从 `RulesClass+0x149C` 拷贝；20 处取值 + 5 处取址（**非 `.data` 常规区**） | kb/30 §15.3；拷贝 `0x0052D171` | **实证** |
| `0x00AC51FC` | `CurrentFrameCRC` | 当前帧混合 CRC | ATLAS §11.1 | 社区 |
| `0x00B04474` | `LatestFramesCRC[256]` | 过去 256 帧 CRC 环 | ATLAS §11.1 | 社区 |
| `0x008B4204` | `NetworkQueue[16384]` | 网络指令环形队列 | ATLAS §11.1 | 社区 |
| `0x0087E2A8` | `VoicePool[300]` | 音效通道池 | ATLAS §11.1 | 社区 |

---

## B. 类虚表与实例尺寸（RTTI 独立复算）

> 虚表地址 **20/20 与 ATLAS 一致、0 不一致**（`evidence/vtable_xcheck.txt`）。
> **槽位契约（R-012）**：`vtable[11]` = `WhatAmI()`（`AbstractType` 类型 ID），
> `vtable[12]` = `GetSize()`（实例尺寸），**两者成对**。**69 类**逐一命中、ID 冲突 0，
> 与引擎名字表 `0x816EE0`（74 项）及 YRpp `AbstractType` 三方一致。
> 详见 `kb/20_vtable_contract.md`、完整表 `evidence/class_ids.txt`。
> **判据**：先验槽 11 是合法类型 ID（`0x00..0x49`），成立才认槽 12 是尺寸。
> **⚠ 作用域（R-037）**：分母是 **78** 个 `AbstractClass` 后代，不是 954/988；
> 9 个抽象中间基类不符合（槽 11/12 是抽象桩），见 **C.16b**。

| 类 | 虚表 VA | 类型 ID | 实例尺寸 | 置信度 | 备注 |
|:---|:---|---:|---:|:---|:---|
| `AbstractClass` | `0x007E1F50` | `0x34` Abstract | — | 实证（VT） | 抽象桩 `xor eax,eax`，两槽同址 `0x004C9150` |
| `UnitClass` | `0x007F5C70` | `0x01` Unit | 2280 (`0x8E8`) | **实证** | 双槽命中 |
| `AircraftClass` | `0x007E22A4` | `0x02` Aircraft | 1752 (`0x6D8`) | **实证** | |
| `AircraftTypeClass` | `0x007E2868` | `0x03` AircraftType | 3600 (`0xE10`) | **实证** | |
| `AnimClass` | `0x007E3354` | `0x04` Anim | 456 (`0x1C8`) | **实证** | |
| `AnimTypeClass` | `0x007E3608` | `0x05` AnimType | 888 (`0x378`) | **实证** | |
| `BuildingClass` | `0x007E3EBC` | `0x06` Building | 1824 (`0x720`) | **实证** | |
| `BuildingTypeClass` | `0x007E4570` | `0x07` BuildingType | 6040 (`0x1798`) | **实证** | |
| `BulletClass` | `0x007E46E4` | `0x08` Bullet | 352 (`0x160`) | **实证** | |
| `BulletTypeClass` | `0x007E4948` | `0x09` BulletType | 760 (`0x2F8`) | **实证** | |
| `HouseClass` | `0x007EA8A0` | `0x0D` House | 90296 (`0x160B8`) | **实证** | 最大尺寸类 |
| `CellClass` | `0x007E4EEC` | `0x0B` Cell | 328 (`0x148`) | **实证** | |
| `InfantryClass` | `0x007EB058` | `0x0F` Infantry | 1776 (`0x6F0`) | **实证** | |
| `ParticleClass` | `0x007EF954` | `0x16` Particle | 312 (`0x138`) | **实证** | |
| `ParticleSystemClass` | `0x007EFB9C` | `0x18` ParticleSystem | 256 (`0x100`) | **实证** | |
| `SuperClass` | `0x007F3FE8` | `0x39` SuperWeapon | 128 (`0x80`) | **实证** | |
| `TeamClass` | `0x007F4730` | `0x22` Team | 160 (`0xA0`) | **实证** | |
| `TeamTypeClass` | `0x007F47D0` | `0x23` TeamType | **248 (`0xF8`)** | **已核验** | ATLAS 记 288 **错**；异族双通道 |
| `AITriggerTypeClass` | `0x007E2A50` | `0x3B` AITriggerType | **272 (`0x110`)** | **已核验** | ATLAS 记 256 **错**；异族双通道 |
| `MapClass` | `0x007ED404` | 未命中 | — | 实证（VT） | 继承 `GScreenClass` |
| `RadarClass` | `0x007F0344` | 未命中 | —（`v[12]` 非 GetSize） | 实证（VT） | 见 CONFLICTS G-4/G-9 |
| `WWMouseClass` | `0x007F7B2C` | 未命中 | —（`v[12]` 非 GetSize） | 实证（VT） | 见 CONFLICTS G-5/G-9 |

触发器族 8 类全部双槽命中：`Script` 48 (`0x1A`) / `ScriptType` 564 (`0x1B`) /
`Tag` 56 (`0x2C`) / `Trigger` 72 (`0x26`) / `TEvent` 88 (`0x30`) /
`TAction` 148 (`0x2F`) / `TaskForce` 212 (`0x21`) / `Team` 160 (`0x22`)。

完整 988 类清单：`evidence/rtti/hierarchy.txt`（继承链）与 `evidence/rtti/classes_meta.json`（每类 vtable / 槽数 / 基类链）。
69 类 ID+尺寸双命中表：`evidence/class_ids.txt`（工具 `tools/dump_class_ids.py`）。

---

## C. 关键函数（按子系统）

### C.0 `AbstractClass` 主虚表槽位契约（`0x007E1F50`，24 槽）

> 全表与逐槽字节见 `kb/22_abstractclass_vtable_slots.md`、`evidence/vtable_slots.txt`
> （工具 `tools/dump_vtable_slots.py`）。槽 24 不是函数，是下一个表的 COL 指针。

| 槽 | `+0x` | 名称 | 备注 |
|---:|---:|:---|:---|
| 0 | `00` | `QueryInterface` | `E_POINTER` 守卫 |
| 1 | `04` | `AddRef` | 恒 `ret 1` |
| 2 | `08` | `Release` | 恒 `ret 1` |
| 3 | `0C` | `GetClassID` | 基类抽象桩；派生类写 CLSID |
| 4 | `10` | **`IsDirty`** | **返回 `!Dirty`（读 `+0x20`）**，不是 Load |
| 5 | `14` | `Load` | 派生类覆写，体首调 `0x410380` |
| 6 | `18` | `Save`（COM） | 派生类覆写，体首调 `0x410320` |
| 7 | `1C` | `GetSizeMax` | `ret 8` |
| 8 | `20` | 析构（标量删除） | 写 4 vptr，`test al,1` |
| 9 | `24` | `Init` | 空 |
| 10 | `28` | `PointerExpired` | 空，`ret 8` |
| 11 | `2C` | **`WhatAmI`** | 派生类返 `AbstractType` ID |
| 12 | `30` | **`Size`** | 派生类返实例尺寸 |
| 13 | `34` | `AbstractClass::Save`（基类序列化块） | 只写 `+0x10`/`+0x20` |
| 14 | `38` | （存疑） | `or eax,-1; ret` |
| 15 | `3C` | （存疑） | `xor eax,eax; ret` |
| 16 | `40` | `GetOwningHouse` → null | |
| 17 | `44` | `IsDead` → true | |
| 18 | `48` | `GetCoords`（默认） | 写 12 B（3 dword） |
| 19 | `4C` | `GetDestination` | 转发槽 18，`ret 8` |
| 20 | `50` | `IsOnFloor` → false | |
| 21 | `54` | `IsInAir` → false | |
| 22 | `58` | `GetAltCoords` | 转发槽 18，`ret 4` |
| 23 | `5C` | `Update` | 空 |

**`+0x10` = `UniqueID`、`+0x20` = `Dirty`（bool）** —— 由槽 13 的序列化 + YRpp 属性表双通道确认。

### C.1 时钟

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x004093B0` | `Clock::Now` | 间接分发入口：读 `[0x0087E848]` 函数指针后 `jmp eax` | claims `0x004093B0/B5/B9` | 语料实证 |
| `0x00409360` | `Clock::Init` | QPF 初始化 | claims `0x00409360` | 语料实证 |
| `0x004093C0` | `Clock::ReadQPC` / `Clock::NowQpc` | 读高精计时器 | claims `0x004093C0` | 语料实证 |
| `0x00409320` | `Stream::Get_Unread_Bytes` | `[ecx+0x34] − [ecx+0x38]` | claims `0x00409320` | 语料实证 |

### C.2 空间索引

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x004134A0` | `SpatialGrid::AddObject` | 读对象坐标 → 换算桶坐标 → 压入对应桶 | ATLAS §4；`0x004134B3 call [eax+0x1B8]` 取坐标 | 语料实证 |
| `0x004135D0` | `SpatialGrid::RemoveObject` | 从桶移除 | 语料 | 社区 |
| `0x004137A0` | `SpatialBucket::Next` / `SpatialGrid::NextCandidate` | 桶内迭代器；`test [ecx+0x2590]` 空即返回 0 | 本线反汇编 | **实证（新增）** |
| `0x00412B40` | `SpatialGrid::InitQuery` | 查询初始化 | 语料 | 社区 |

### C.3 归属与可见性闸

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x0050B6F0` | **`HouseClass::IsPlayerControl`** | 单人读 `+0x1EC/+0x1ED`；联机 `cmp ecx, [0xA83D4C]` | 本线全函数反汇编 | **实证（本线裁定）** |
| `0x006DA380` | **`TacticalClass::GetObjectAt`** | 鼠标下对象解析，扫 `0xB0CEC8`，硬拦未探测隐形 | 语料 + 本线入口确认 | 语料实证（本线裁定命名） |
| `0x00656EC0` | **`RadarClass::Refresh`** | 雷达主循环（含地形缓存 + 视口矩形 + 画点） | 语料 | 语料实证（本线裁定命名） |

### C.4 可见性 / 裂缝

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x00568273` | 裂缝隐匿保护 1 | `mov [ecx+0x134], ebx` | claims `0x00568273` | 实证 |
| `0x00577EC5` | 裂缝隐匿保护 2 | `mov [eax+0x134], edi` | claims `0x00577EC5` | 实证 |
| `0x00577B60` | 裂缝隐匿保护 3 | `mov [eax+0x134], ebx` | claims `0x00577B60` | 实证 |
| `0x00508F88` | 间谍卫星状态检查 | `cmp byte [eax+0x16A5], 0` | claims `0x00508F88` | 实证 |
| `0x00508F8F` | 间谍卫星门控短跳 | `je 0x00508FF6`（无卫星跳过揭开黑雾） | claims `0x00508F8F` | 实证 |

### C.5 CRT / 内存

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x007C8E17` | CRT `operator new` 路径 | `push 1; push [esp+8]` | claims | 语料实证 |
| `0x007C8B3D` | CRT `operator delete` 包装 | `push [esp+4]; call free` | claims | 语料实证 |
| `0x006C6400` | `DynamicVectorClass::AddItem` | 线性扩容 +10 缺陷 | ATLAS §10 | 语料实证 |
| `0x004068E0` | Release 空桩 | `ret; nop×3`，1,672 处直调 | claims `0x004068E0` | **实证** |

---

### C.6 触发器 / 队伍脚本派发（R2-1，详见 `kb/10_map_triggers.md`）

| VA | 名称 | 作用 | 证据 | 置信度 |
|:---|:---|:---|:---|:---|
| `0x006DD8B0` | `TActionClass::Execute` | 触发器动作执行；`sub esp,0x240` | 本线入口反汇编 | **实证** |
| `0x006DFDEC` | Action 跳表 | 145 dword，145/145 在 .text，143 唯一 | `dump_trigger_tables.py` | **实证** |
| `0x006DD8E7` | Action 派发点 | `jmp [edx*4+0x6DFDEC]` | 字节 | **实证** |
| `0x006DFDDB` | Action 共享 epilogue | `mov al,1; pop×4; add esp,0x240; ret 0x10` | 字节 | **实证**（动作 38/91/92 共用） |
| `0x006E9050` | `TeamClass::AI` | 队伍脚本执行；`[edi+0x3C]` 状态比较后早退 | 本线入口反汇编 | **实证** |
| `0x006E9F74` | Team 动作跳表 | 65 dword，65/65 在 .text，**65 唯一** | `dump_trigger_tables.py` | **实证** |
| `0x0071E940` | `TEventClass::HasOccured` | 事件判定；`[ebp+0x2C]`=事件 Kind | 本线入口反汇编 | **实证** |
| `0x0071F218` | 事件一级跳表 | **12 dword / 12 唯一目标** | `dump_trigger_tables.py` | **实证** |
| `0x0071F248` | 事件二级选择表 | **49 字节**，值=一级表下标（0..11），`0x0B`=兜底 | `evidence/trigger_tables.txt` 全文 | **实证** |
| `0x0071E964` | 事件派发点 | `jmp [edx*4+0x71F218]` | 字节 | **实证** |
| `0x0071EC63` | 事件兜底 | 既是 `ja` 目标，又是选择值 11 的目标 | 字节 + 机器输出 | **实证** |
| `0x0071F27C` | 事件二级门 | 2 目标门 + 选择表 `0x71F284` | 语料 | 语料实证（未复核） |
| `0x0071F2C0` | 事件三级 | 14 目标 + 选择表 `0x71F2F8` | 语料 | 语料实证（未复核） |
| `0x0071F328` | 事件四级 | 10 目标 + 选择表 `0x71F350` | 语料 | 语料实证（未复核） |

**关键读表规则**：事件是**两级**查表 `table1[table2[kind-0x0D]]`，
不是 `table1[kind-0x0D]`。49 槽中仅 **12 槽**有专属实现，**37 槽**走兜底。
Action / Team 两表是**单级**绝对地址数组。

---

### C.7 触发器族类布局（R2-1 第二轮，详见 `kb/11_class_layouts.md`）

| 类 | 虚表 VA | 槽 | 实例尺寸 | 证据 | 置信度 |
|:---|:---|---:|---:|:---|:---|
| `AbstractClass` | `0x007E1F50` | 24 | **0（桩，非真尺寸）** | `v[12]=0x004C9150` = `33 C0 C3` | **实证** |
| `AbstractTypeClass` | `0x007E2000` | 27 | **0（桩）** | 同槽同址 | **实证** |
| `ScriptClass` | `0x007F0F78` | 24 | **48** (`0x30`) | `v[12]=0x00691ED0` | **实证** |
| `TagClass` | `0x007F44E0` | 24 | **56** (`0x38`) | `v[12]=0x006E5890` | **实证** |
| `TriggerClass` | `0x007F5858` | 24 | **72** (`0x48`) | `v[12]=0x00726930` | **实证** |
| `TEventClass` | `0x007F5578` | 24 | **88** (`0x58`) | `v[12]=0x0071FA50` | **实证** |
| `TActionClass` | `0x007F443C` | 24 | **148** (`0x94`) | `v[12]=0x006E4630` | **实证** |
| `TeamClass` | `0x007F4730` | 24 | **160** (`0xA0`) | `v[12]=0x006F0430` | **实证** |
| `TaskForceClass` | `0x007F4680` | 27 | **212** (`0xD4`) | `v[12]=0x006E87E0` | **实证** |
| `ScriptTypeClass` | `0x007F1008` | 27 | **564** (`0x234`) | `v[12]=0x00691F80` | **实证** |

**★ `AbstractClass` 是多继承：4 个 vtable 指针**（`+0x00/+0x04/+0x08/+0x0C`），
COL.offset 分别 **0/4/8/12**。所有派生类头部都是这个形态。
证据：删除析构 `0x004105A0` 连续四次 `mov dword [esi+N], <vt>`。

**`AbstractClass` 前缀字段**：

| 偏移 | 内容 | 序列化 | 证据 |
|:---|:---|:---|:---|
| `+0x00..+0x0C` | 4 × vptr | 否 | `0x004105A9/AF/B6/BD` |
| `+0x10` | dword | **是**（`Save` 写入） | `0x00410418` → `call 0x4A1D50` |
| `+0x14..+0x1C` | 3 × dword | **否**（纯运行时态） | `Save` 只读两个字段 |
| `+0x20` | **bool** | **是**（归一化 `setne` 后写） | `0x00410423` → `call 0x4A1CA0` |

**派生类已确证字段**：

| 类 | 偏移 | 类型 | 语义 | 证据 |
|:---|:---|:---|:---|:---|
| `TEventClass` | `+0x2C` | `int32` | 事件 Kind（合法域 `0x0D..0x3D`） | `0x0071E94D` 读 / `0x0071F847` 写入存档 |
| `TEventClass` | `+0x30` | **指针** | 指向带接口的从属对象；非空时按 `[vt+0x10]` 序列化 | `0x0071F852..860` |
| `TEventClass` | `+0x34` | `int32` | 第二个数值参数 | `0x0071F86B` |
| `TEventClass` | `+0x54` | 4B | 第二个接口字段（`add esi,0x54` 后再取接口） | `0x0071F91B` |
| `TActionClass` | `+0x90` | **dword** | 最后一个字段，被 `Save` 写入存档 | `0x006E3ECD` |
| `TeamClass` | `+0x3C` | `dword` | 当前脚本步；与入参相同则**早退** | `0x006E9059/5C/5E` |

复跑：`python re_atlas/tools/dump_class_layouts.py`（`evidence/class_layouts.txt`）。

---

### C.8 INI 容器与节点（R2-2 第二轮，详见 `kb/30_ini_subsystem.md`）

| 类 | 虚表 VA | 槽 | 实例尺寸 | 证据 | 置信度 |
|:---|:---|---:|---:|:---|:---|
| `INIClass` | `0x007EA5F4` | 1 | **`0x40`** | `[vt-4]`→COL `0x00802510`；`v[0]=0x004F2810` | **实证** |
| `CCINIClass : INIClass` | `0x007E1AF4` | 1 | ≥`0x55`（语料 `0x58` 未独立复核） | `[vt-4]`→COL `0x007FAC88`；`v[0]=0x0040E4A0` | 实证（结构）/ 推演（尺寸） |
| `INISection` | `0x007EB73C` | 1 | **`0x44`** | `[vt-4]`→COL `0x00803708`；`0x00525DEA push 0x44` | **实证** |
| `INIEntry` | `0x007EB734` | 1 | **`0x28`** | `[vt-4]`→COL `0x00803668`；`0x00526039 push 0x28` | **实证** |
| `List<INISection*>` | `0x007E1AFC` | 1 | **`0x1C`** | `[vt-4]`→COL `0x007FAC20` | **实证** |
| `List<INIEntry*>` | `0x007EB744` | 1 | **`0x1C`** | `[vt-4]`→COL `0x00803600` | **实证** |
| `GenericNode` | `0x007E1B0C` | — | `0x0C`（vptr+Next+Prev） | `[vt-4]`→COL `0x007FACD0` | **实证** |

**`INIClass` 字段（`kb/30` §1.2）**：`+0x04`/`+0x08` = GetSection 缓存（哈希/上次命中）、
`+0x0C` = `List<INISection>`（`0x1C`）、`+0x28` = 哈希排序数组、`+0x2C`/`+0x30` = 数量/容量、
`+0x34` = dirty、`+0x38` = 二分命中缓存、`+0x40` = `Digested`、`+0x41..+0x54` = `Digest[20]`（推演）。

**关键机制函数**：

| VA | 名称 | 作用 | 证据 |
|:---|:---|:---|:---|
| `0x00535AA0` | `CCINIClass::ctor` | 写 `0x7EA5F4`(本类) + `+0x0C` 的 `List` 结构 | 逐指令 |
| `0x005256F0` | `INIClass` dtor 体 | 清 `+0x0C..+0x3C`，释放 `+0x28` | 逐指令 |
| `0x00526B00` | `INIClass::Reset` | 清 `+0x04`/`+0x08` 两缓存（**不是**"节名预处理"） | `33 C0 / 89 41 04 / 89 41 08 / C3` |
| `0x00526810` | `GetSection` | CRC32 → 排序数组二分 → 未命中返 `0xB7882C` | 逐指令 |
| `0x004A1DE0` | CRC32（分块） | 节名/键名哈希 | 与 `0x4A1FB0` 同多项式 |
| `0x004A1FB0` | CRC32（单块） | 同上 | 表 `0x81F7B4` 全 256 项比对 |
| `0x0052B720` | hash 比较器 | **只比首 dword，不复核名字** | `cmp [eax],[ecx]` |
| `0x0052B750` | 二分 | 8 字节步长，命中返元素地址 | `lea [ecx+eax*8]` |
| `0x00528A10` | `ReadString` | 节→键→拷贝（`ret 0x14`） | 逐指令 |
| `0x00526CC0` | `GetKeyName` | `[sec+0x18]` 链表头 / `[sec+0x30]` 键数上界 | 逐指令 |

复跑：`python re_atlas/tools/dump_ini_nodes.py`（`evidence/ini_nodes.txt`；
含 `AbstractClass` COL 正对照 + CRC 表 256 项全比）。

---

### C.9 INI 读族逐键语义（R2-2 第三轮，详见 `kb/30_ini_subsystem.md` §10）

| VA | 名称 | 解析规则（字节实证） | 置信度 |
|:---|:---|:---|:---|
| `0x005295F0` | `ReadBool` | **只取首字符** → `toupper` → 查 `0x5297B4`（0x2A 项）→ 三元分派；`0/F/N`=false，`1/T/Y`=true，**其余取默认值** | **实证** |
| `0x005276D0` | `ReadInteger` | **看末字符** → `tolower` → 等于 `h` 则 `%xh` 十六进制解析，否则 `strtol` | **实证** |
| `0x00529560` | `WriteBool` | 写字面量 `"yes"`(`0x825BF8`) / `"no"`(`0x825BF4`) | **实证** |
| `0x00528A10` | `ReadString` | `ret 0x14`；节→键→拷贝 | **实证** |
| `0x00528F00` | `ReadUnicodeString` | 栈帧 `0x5014`（约 20KB），先缓冲再转义解码 | **实证** |
| `0x00529160` | `ReadStringtableEntry` | 栈帧 `0x414`（1KB），ANSI→CSF 字符串表→宽字符 | **实证** |
| `0x005283D0` | `ReadDouble` | 默认值 8 字节实参，返回 ST0 | **实证** |
| `0x007C97D3` | `toupper` | `'a'..'z'` → 减 `0x20` | **实证** |
| `0x007CAFF4` | `tolower` | `'A'..'Z'` → **加** `0x20`（注意与上一条方向相反） | **实证** |
| `0x005297A8` | `ReadBool` 分派表 | 3 项：class0→`0x52979A`(false) / class1→`0x52978E`(true) / class2→`0x52974B`(默认) | **实证** |
| `0x005297B4` | `ReadBool` 类表 | 0x2A 项，仅 6 项非默认 | **实证** |
| `0x00825BB4` | 十六进制格式串 | `"%xh"` | **实证** |

**读族共享缓存**：六个读函数都先用 `[this+4]`（上次哈希）/`[this+8]`（上次节）做短路，
未命中才 `call 0x4A1DE0` 算哈希查 `+0x28` 排序数组。

复跑：`python re_atlas/tools/dump_ini_readers.py`（`evidence/ini_readers.txt`，
含 `ReadString` 头字节正对照）。

---
### C.10 键 → 字段映射（R2-2 第四轮，详见 `kb/30_ini_subsystem.md` §11）

`AbstractTypeClass::LoadFromINI`（`0x00410A60`）**只读 2 个键**：

| 键 | 目标字段 | 上限 | 证据 |
|:---|:---|:---|:---|
| `Name` | `this+0x64` | `0x31`(49) | `0x00410A91 lea edi,[ebx+0x64]` / `0x00410A94 push 0x31` |
| `UIName` | `this+0x3D` | `0x20`(32) | `0x00410AEB lea ebp,[ebx+0x3D]` / `0x00410AEE push 0x20` |

**★ `+0x24` 既是 `char ID[0x18]` 又是节名**：
`0x00410A79 lea ebp,[ebx+0x24]` → `0x00410A7E push ebp` → `0x00410A7F call 0x526810`(GetSection)。
⇒ 节头字符串与对象 ID 是同一串字节；显示名走 `+0x60` 的 `UIName`（`wchar_t*`）。

**字段边界（含对齐）**：

| 偏移 | 字段 | 尺寸 |
|:---|:---|---:|
| `+0x24` | `ID` | `0x18` |
| `+0x3C` | `zero_3C` | 1 |
| `+0x3D` | `UINameLabel` | `0x20` |
| `+0x5D` | **对齐填充** | **3** |
| `+0x60` | `UIName`(`wchar_t*`) | 4 |
| `+0x64` | `Name` | `0x31` |
| `+0x95` | —（本类结束） | |

| VA | 名称 | 作用 | 置信度 |
|:---|:---|:---|:---|
| `0x00526B00` | `INIClass::Reset` | 清 `+0x04`/`+0x08` 缓存 | **实证** |
| `0x00734E60` | `UIName` 解析 | 查 CSF 表；表未初始化时返回 `0x84583C`（非 NULL） | **实证** |

复跑：`python re_atlas/tools/dump_ini_keymap.py`（`evidence/ini_keymap.txt`，
双正对照 + 算式/字节对齐自检）。

---
### C.11 全引擎 键 → 读取点 索引（R2-2 第五轮，**R-023 全面重算**，详见 `kb/30_ini_subsystem.md` §12）

> ⚠ **旧数字 478 / 473 / 427 作废。** 根因：capstone 单次 `md.disasm(.text)`
> 在 `0x46F5A0`（跳转表）**静默停止**，只覆盖前 9%，见 `CONFLICTS.md` G-23。

**2,426 个 INI 读取调用点，2,305 个键字面量恢复，1,893 个不同键。**

| 读取器 | 调用点 |
|:---|---:|
| `0x005276D0` `ReadInteger` | 757 |
| `0x005295F0` `ReadBool` | 651 |
| `0x00528A10` `ReadString` | 650 |
| `0x005283D0` `ReadDouble` | 306 |
| `0x00526810` `GetSection` | 54 |
| `0x00528F00` `ReadUnicodeString` | **5**（旧记录"0 处"已推翻） |
| `0x00529160` `ReadStringtableEntry` | 3 |

**被多处读取的键：164 个**（旧记录 10 个）。头部高频项 `Name` / `UIName` /
`Image` / `Cameo` / `Armor` / `Cost` / `Strength` / `TechLevel` / `Range` /
`ROF` / `Speed` / `Power` —— 都是各 `TypeClass` 派生类各读一遍。

**未恢复键的 121 处**：键在寄存器（`GetKeyName` 取名）／键在 BSS 缓冲／
键是字段地址（`lea ebp,[ebx+0x24]`）。**静态不可还原，编译器不能假设"索引里没有 = 引擎不读"。**

**★ 格式化键**：`"PowerUp%01dYSort"`（`0x008194D4`，6 个读取点，全在 ~`0x0045FE50`）
⇒ 运行期 `sprintf` 成 `PowerUp0YSort`…`PowerUp9YSort`，INI 里要展开写 10 个实键。

复跑：`python re_atlas/tools/dump_ini_keyindex.py`（`evidence/ini_keyindex.txt`）。
**正对照（三项全过才算可信）**：① 纯 `E8` 字节扫描 == 指令扫描，**逐址相等**
（当前 2426 == 2426 零差异）；② `Name`/`UIName` 各有 ≥1 处属 `LoadFromINI`
（`0x00410A60`）；③ 调用点总数 ≥2000（防再次静默截断）。

---

### C.12 `RulesClass` 节表与载入顺序（R2-2 第六轮，详见 `kb/30_ini_subsystem.md` §13）

**节名指针表 `0x007F0C78`**：31 项 `const char*`（`SpecialWeapons` … `ButtonList`）。

**函数 → 节名 36/38 恢复**（`tools/dump_rules_sections.py`）。三种形态：

| 形态 | 例 |
|:---|:---|
| `indirect`（指针表） | `mov eax,[0x7F0C94]` |
| `direct`（字符串地址直压） | `push 0x83D0DC` |
| `table-base`（数组首项） | `mov esi,0x839D68` |

| 函数 | 节名 |
|:---|:---|
| `0x0066D3A0` `Read_Colors` | `Colors` |
| `0x0066D530` `Read_General` | `General` |
| `0x00672280` `Read_InfantryTypes` | `InfantryTypes` |
| `0x006728B0` `Read_Animations` | `Animations`（direct） |
| `0x00672990` `Read_Warheads` | `Warheads`（direct） |
| `0x00672AE0` `Read_AI` | `AI`（2 字符） |
| `0x00674240` `Read_IQ` | `IQ`（2 字符） |
| `0x00674000` `Read_LandCharacteristics` | `Clear`（数组首项） |
| `0x00674650` `Read_AdvancedCommandBar` | `AdvancedCommandBar`（**非** Multiplayer…） |

**载入顺序**：`Init`(`0x6686C0`) 32 个内部调用，`Read_File ×3` 先建列表节，
其余按序；**后读覆盖先读**。

**结构性未恢复**：`Read_Difficulty`（节名是参数 `edx`）、`Read_Difficulties`（只转发键名）。

复跑：`python re_atlas/tools/dump_rules_sections.py`（`evidence/rules_sections.txt`，
四项正对照）。

---
### C.13 逐 loader 键清单（R2-2 第七轮，详见 `kb/30_ini_subsystem.md` §14）

**651 个字面量键**（R-022 旧值 306 作废：窗口 `0x1000` 腰斩了 4 个 6–10 KB 的 loader，
且键提取把参数/节名一并算进键；见 `kb/30` §14.0）。关键认知：**20 个 loader 是"枚举键名"形态** ——
`GetKeyCount` → `GetKeyName`，**键名即数据**；`[VehicleTypes]`/`[Sides]` 等节
就是名字列表，没有"字段"。

只有 15 个 loader 读固定键（合计 651）：

| loader | 键数 |
|:---|---:|
| `0x0066D530` `Read_General` | **279** |
| `0x006691E0` `Read_AudioVisual` | **152** |
| `0x0066BBB0` `Read_CombatDamage` | 71 |
| `0x00672AE0` `Read_AI` | 52 |
| `0x00671EA0` `Read_MultiplayerDialogSettings` | 27 |
| `0x0066D270` `Read_Difficulty` | 12 |
| `0x00674240` `Read_IQ` | 11 |
| `0x0066B900` `Read_CrateRules` | 10 |
| `0x0066CF70` `Read_Radiation` | 9 |
| `0x00674000` `Read_LandCharacteristics` | 8 |
| `0x00668FB0` `Read_SpecialWeapons` | 7 |
| `0x006743D0` `Read_JumpjetControls` | 7 |
| `0x0066D150` `Read_ElevationModel` | 3 |
| `0x0066D1F0` `Read_WallModel` | 2 |
| `0x00672230` `Read_Maximums` | 1 |

**`[General]` 与 `[AudioVisual]` 两节就占 431/651（66%）** —— 编译器优先覆盖这两个。

`Read_MultiplayerDialogSettings` 的 27 键含 `MinUnitCount`/`UnitCount`/`MaxUnitCount`、
`ShortGame`、`MultiEngineer`、`MCVRedeploys` 等。

复跑：`python re_atlas/tools/dump_rules_keys.py`（`evidence/rules_keys.txt`，
三项正对照）。

---
### C.14 `RulesClass` 字段布局与镜像全局（R-023，详见 `kb/30_ini_subsystem.md` §15）

**`[MultiplayerDialogSettings]` 27 键 → 结构偏移**（双向一致 27/27）：

| 段 | 偏移 | 键 |
|:---|:---|:---|
| 11 × dword | `+0x1480..+0x14AB` | `MinMoney` `Money` `MaxMoney` `MoneyIncrement` `MinUnitCount` `UnitCount` `MaxUnitCount` `TechLevel` `GameSpeed` `AIDifficulty` `AIPlayers` |
| 16 × byte | `+0x14AC..+0x14BB` | `BridgeDestruction` `ShadowGrow` `Shroud` `Bases` `TiberiumGrows` `Crates` `CaptureTheFlag` `HarvesterTruce` `MultiEngineer` `AlliesAllowed` `ShortGame` `FogOfWar` `MCVRedeploys` `SuperWeaponsAllowed` `BuildOffAlly` `AllyChangeAllowed` |

共 **60 字节无空洞**。读法 `ReadInteger`（dword）/ `ReadBool`（byte）；
每键在读取器里出现两次（默认载入 + 结果存回），两处偏移必须相等。
构造器默认值全表见 `evidence/rules_fields.txt`。

**载入后 18 个字段镜像到独立全局**（游戏读全局，不读字段）——
见 §A 的 `0x00A8B25C`…`0x00A8B320` 各行。核心三条：
`ShortGame`→`0x00A8B262`（50 处取值）、`MCVRedeploys`→`0x00A8B320`（44）、
`GameSpeed`→`0x00A8B268`（43）。镜像块 `0x0052D149..0x0052D22C`，恰好 18 条
`mov [全局], reg`，所在函数从 **`0x0052CD70`** 开始（`0x52D032`/`0x52D0B3` 是提前退出路径，不是函数边界）。

**9 个字段不镜像**，只留在 `RulesClass` 里：`MinMoney` `+0x1480`、
`MaxMoney` `+0x1488`、`MoneyIncrement` `+0x148C`、`MinUnitCount` `+0x1490`、
`MaxUnitCount` `+0x1498`、`ShadowGrow` `+0x14AD`、`Shroud` `+0x14AE`、
`TiberiumGrows` `+0x14B0`、`AllyChangeAllowed` `+0x14BB`。

**`ShadowGrow`（`+0x14AD`）是 27 键里唯一读点为 0 的**（纯字节扫描复核：
该 disp32 在 `.text` 只出现 3 次 = 构造器写 1 + 读取器读/写 2）。

复跑：`tools/dump_rules_fields.py`（`evidence/rules_fields.txt`）与
`tools/dump_rules_consumers.py`（`evidence/rules_consumers.txt`）。
判据：27/27 双向一致 + 4 字节字段对齐 + 无偏移重叠；
每个镜像全局的**字节扫描次数 == 指令扫描 (取值+取址) 次数**（18/18 相等）。

---
### C.15 `[AudioVisual]` 字段布局（R-024，详见 `kb/30_ini_subsystem.md` §16）

读取器 `0x006691E0`，函数体 `[0x006691E0, 0x0066B8F1)`，**10,001 字节**。
**151/152 键已解出字段偏移**（`Smoke` 一键两字段），双向一致 151/151。

**R-025 补全**：首版 130 的 22 个"未解出"**判因错误** —— 字符串一直都在 `.data`，
真因是 `ReadDouble` 的存回不是 `mov`（`fstp qword` / `fstp dword`）。
唯一剩余的 `OnFire` 是**列表型**，不是标量字段。

代表项：`DetailMinFrameRateNormal` `+0x0000` / `DetailMinFrameRateMovie` `+0x0004` /
`DetailBufferZoneWidth` `+0x0008` / `PoseDir` `+0x0044` / `DeployDir` `+0x0048` /
`DropPodPuff` `+0x004C`(Str) / `Gravity` `+0x16B8` / `EnemyHealth` `+0x17E6`(Bool) /
`AllyReveal` `+0x17E7`(Bool) / `ShroudGrow` `+0x17F0`(Bool) /
`LaserTargetColor` `+0x18A4` / `IronCurtainColor` `+0x18A8` /
`BerserkColor` `+0x18AC` / `ForceShieldColor` `+0x18B0`。
全表见 `kb/30` §16.2 与 `evidence/rules_fields_av.txt`。

**`Smoke` 是唯一同名两字段的键**（`+0x0BAC` / `+0x0BB0`，同一字面量 `0x00836F0C`）
⇒ 引擎用**一个** `Smoke=` 值填**两个**槽，编译器只写一次。

**未解出 22 个**（`FogRate` 已定性：字面量不在 `.rdata`，不走 `push <imm>` 形态）。

复跑：`python re_atlas/tools/dump_rules_fields.py 0x006691E0`。
判据：131/131 双向一致 + 读者全在登记表内 + 4 字节对齐 + 无偏移重叠。

---
### C.16 `[General]` 字段布局（R-025，详见 `kb/30_ini_subsystem.md` §17）

`[General]` 是 rulesmd.ini **最大节（279 键，占全部字面量键 43%）**。
读取器 `0x0066D530`，函数体 `[0x0066D530, 0x00671E8E)`，5,062 条指令。

**268 个标量字段已解出**，**0 个凭空多出**，12 个未映射的键全是列表型
（`DeadBodies` / `BarrelDebris` / `BaseUnit` 等，形态为
`ReadString` → `push 0; push 0` → 切分 → 追加容器）。

代表项：`PrismSupportModifier` `+0x049C` / `PrismSupportMax` `+0x04A0` /
`PrismSupportDelay` `+0x04A4` / `PrismSupportDuration` `+0x04A8` /
`PrismSupportHeight` `+0x04AC` / `AICaptureLowMoneyMark` `+0x0EBC` /
`TiberiumTransmogrify` `+0x1688`。全表见 `kb/30` §17.2 与
`evidence/rules_fields_general.txt`。

> ⚠ **边界陷阱**：真实首个 `ret` 在 `0x00671E8B`（距入口 18,782 字节）。
> 手估的 `0x0066E52F` 是错的（函数体中部），用它只解出 33 个键。

**已知 7 行偏移错位**（`ReadDouble` 8 字节默认值跨字段），以「存回」列为准。

复跑：`python re_atlas/tools/dump_rules_fields.py 0x0066D530`。

---
### C.17 其余小节字段布局（R-027，详见 `kb/30_ini_subsystem.md` §18）

10 个较小的 rulesmd.ini 节，全部正对照通过：

| 节 | 读取器 | 键数 | 形态 |
|:---|:---|---:|:---|
| `[CrateRules]` | `0x0066B900` | 10 | 标量 `this=esi` |
| `[IQ]` | `0x00674240` | 11 | 标量 `this=esi` |
| `[Radiation]` | `0x0066CF70` | 9 | 标量 `this=esi` |
| `[SpecialWeapons]` | `0x00668FB0` | 7 | 标量 `this=esi` |
| `[JumpjetControls]` | `0x006743D0` | 7 | 标量 `this=esi` |
| `[ElevationModel]` | `0x0066D150` | 3 | 标量 `this=esi` |
| `[WallModel]` | `0x0066D1F0` | 2 | 标量 `this=esi` |
| `[Maximums]` | `0x00672230` | 1 | 标量 `this=esi` |
| `[Easy]`/`[Normal]`/`[Difficult]` | `0x0066D270` | 12 | **外部对象**（`edi` 基址） |
| （三难度分派） | `0x00674500` | 0 | **纯分派器** |
| `[Clear]` 等地形节 | `0x00674000` | 0 | 写**全局表** `0x89EA44` |

**三种非标准形态**（R-027 新识别）：外部对象（默认值是立即数不是字段载入）、
纯分派器（只调别人的函数）、写全局表（无对象基址 + 范围钳制）。

`[Easy]`/`[Normal]`/`[Difficult]` 三节**结构完全相同**（`0x4B` 字节，
`FirePower` `+0x00` / `Groundspeed` `+0x08` / … / `ContentScan` `+0x4A`），
由 `Read_Difficulties` 分派给同一段代码。

复跑：`python re_atlas/tools/dump_rules_fields.py <读取器地址>`。
**正对照按目标类型分档**（普通 / 外部对象 / 分派器），详见 `kb/30` §18.4。

### C.18 `TypeClass` 继承链与逐类字段（R-028，**R-028 核验后为 644 键**，详见 `kb/30_ini_subsystem.md` §19 / §19.11）

> 这是 `rulesmd.ini` / `artmd.ini` 里 **90% 内容**的落点：
> `[InfantryTypes]` / `[VehicleTypes]` / `[AircraftTypes]` / `[BuildingTypes]`
> 里每个名字都指向一个 `TypeClass` 实例。**644 键（rules 446 / art 198），0 未定。**
>
> **⚠ 原报 613 键已作废**：工具把 `fstp [ebp+off]` 当"栈暂存"跳过，而
> `TechnoTypeClass`(0x712180) / `BuildingTypeClass`(0x45FE5F) 的 `this` 就是 EBP
> ⇒ 两类的全部 `ReadDouble` 字段丢失（24+7=31）。三条独立证据见 §19.11。

| 层 | 类 | 虚表 | `LoadFromINI`（槽 25） | 尺寸（槽 12） | 键数 | rulesmd | artmd |
|:---|:---|:---|:---|---:|---:|---:|---:|
| 1 | `AbstractTypeClass` | `0x007E2000` | `0x00410A60` | 0（桩） | 1 | 1 | 0 |
| 2 | `ObjectTypeClass` | `0x007EF2D8` | `0x005F92D0` | 0（桩） | 20 | 15 | 5 |
| 3 | `TechnoTypeClass` | `0x007F4ED8` | `0x00712170` | 0（桩） | **276** | **255** | **21** |
| 4a | `InfantryTypeClass` | `0x007EB610` | `0x005240A0` | **0x0ED0** | 33 | 28 | 5 |
| 4b | `UnitTypeClass` | `0x007F6218` | `0x00747620` | **0x0E78** | 27 | 15 | 12 |
| 4c | `AircraftTypeClass` | `0x007E2868` | `0x0041CC20` | **0x0E10** | 10 | 6 | 4 |
| 4d | `BuildingTypeClass` | `0x007E4570` | `0x0045FE50` | **0x1798** | **277** | **126** | **151** |

**四条对编译器直接可用的事实**：

1. **逐层委托**：每个派生 loader 的前 20 条指令内都有 `call` 指向上一层 loader
   （实测是第 9–12 条，不是第 1 条——第 1 条是 `0x526B00` 的字段复位小助手）。
   字段偏移的归属由**谁写**决定。
2. **同一 loader 同时读两个文件**：`rulesmd`（调用方参数）与
   `artmd`（全局 `CCINIClass` **`0x887180`**）。**写错文件不报错，只是键永远读默认值。**
   Building 有 151/277 键属 artmd。
   - `0x887180` 在 **BSS**，静态读不到 vptr；身份由唯一写入点
     `0x40E031: mov dword ptr [0x887180], 0x7E1AF4` 证实，
     `0x7E1AF4` 的 COL = `.?AVCCINIClass@@`。
3. **两个节名缓冲**：`+0x24` = 类型自身名（两文件通用）；
   `+0x1F8` = `Image=` 改写后的美术节名（**artmd 专用**，
   238 个字面量站点 0 违反；另 1 个站点 INIClass 来自栈参数、不可静态判）。
4. **★ `ReadDouble` 会静默吃掉 `%`**：`0x5283D0` 命中 `%%` 后
   `fmul [0x7E3808]`(=**0.01**)。`50%` → `0.5`，不报错、不留痕。
   已知走 `ReadDouble` 的键 **35 个**。**写 INI 必读。**

**一处归属更正**：`MovementZone`（`+0x05B4`）属 **rulesmd**，非 artmd。
它的 `ecx` 来自 `[esp+0x388]`，与序言 `mov esi,[esp+0x37C]`（唯一 INIClass 形参）
**同一栈槽** ⇒ 调用方传入的 rulesmd。

25 个键经 **cdecl 枚举包装器**读取（`PipScale` / `Armor` / `Foundation` /
`SpeedType` / `BuildCat` / `Owner` …），判据：函数体直接调 `Read*` 且
`ret N`（N≥8）。构造器链独立核对：四类 **33/33、27/27、10/10**，
Building **269/269**（含 132 个 `lea eax,[esi+0xF5C] / 0x15 项 / 步长 0x44`
的指针环清零）。

**`WaterBound` 与 `SpeedType` 共用 `+0x67C`**（建筑不移动，复用该槽；
`yes`→5、`no`→-1）—— **跨类按偏移批量改写会打穿这一格。**

**口径边界（重要）**：**644 不是键总数，是"标量字段"数**。另有 **153 个**键
读进**内联 `char[]` 缓冲区**（`read → lea reg,[this+off] → rep movsd`），
如 `TurretAnim`/`TurretAnimDamaged`/`TurretAnimGarrisoned` 落在
`+0x11B0..+0x11DF`。两张表都未列它们。

复跑：`python re_atlas/tools/dump_typeclass_fields.py`（644 键）；
独立门禁 `python re_atlas/tools/verify_r028_claims.py`（**49/49，EXIT=0**）；
证据 `evidence/typeclass_fields_v2.txt`（644 行，**现行**；
`typeclass_fields.txt` 为旧版已作废）。

### C.18b EBP-this INI loader 普查（G-41 爆炸半径，2026-10-22）

> 回答"`fstp [ebp+off]` 被误排除"这个缺陷**还波及哪些表**。
> 根集合 = `.text` 内 rel32 `E8/E9` 目标 + `.rdata` 成组 `.text` 指针（虚表槽），
> 原始字节取根（一次 `md.disasm` 扫全段会在 `0x46F5A0` 静默停）。

| 项 | 数 |
|:---|---:|
| 根 / 去重 span / 解析出 `this` | 15,751 / 13,193 / 4,339 |
| **`this`=EBP 且调 `Read*`** | **13**（已覆盖 2，未覆盖 11） |
| 定性后 `KEY_FIELD` | **2** |

- **RulesClass 树安全**：`Read_General`(`0x66D530`) / `Read_AudioVisual`(`0x6691E0`)
  的 `this` 是 **ESI**（`0x66D547` / `0x6691F6 mov esi,ecx`）
  ⇒ **H-016/H-017/H-018 的 268/279/151 不受影响**（实测）。
- `0x6686C0` = `RulesClass::Init`（派发层，1 键）。
- `0x6980C0` = **联机会话/序列号 loader**（新发现，15 键，
  `RA2MD.INI` 的 `[MultiPlayer]`/`[SerialDefaults]`；调用方传 `GameMode`）
  ⇒ R2-9 只读，不进 ③ 配置面。

⇒ **③ 无第二个同类漏收。**
复跑：`tools/census_ebp_this_loaders.py`（6/6）、
`tools/classify_ebp_this_candidates.py`；证据 `evidence/ebp_this_{census,classify}.txt`。

### C.15c 逐 loader 字面量键 651（R-024 核验口径，2026-10-23）

> **核验门禁 `tools/verify_r024_claims.py` 15/15 PASS，EXIT=0** + 异族盲验（279/152 独立一致）。
> 记录件 `evidence/r024_rules_keys_fields_verification.md`；正文 `kb/30` §14。

| loader | 键 | loader | 键 |
|:---|---:|:---|---:|
| `Read_General` | **279** | `Read_CrateRules` | 10 |
| `Read_AudioVisual` | **152** | `Read_Radiation` | 9 |
| `Read_CombatDamage` | 71 | `Read_LandCharacteristics` | 8 |
| `Read_AI` | 52 | `Read_SpecialWeapons` | 7 |
| `Read_MultiplayerDialogSettings` | 27 | `Read_JumpjetControls` | 7 |
| `Read_Difficulty` | 12 | `Read_ElevationModel` | 3 |
| `Read_IQ` | 11 | `Read_WallModel` | 2 |
| | | `Read_Maximums` | 1 |

**合计 651，来自 15 个 loader；`[General]`+`[AudioVisual]` = 431/651（66%）。**
另有 **20 个 loader 走「枚举键名 / 按键名注册」** 形态，其键集合**无法**从静态字面量得出。

**★ 边界测量（R-024 新增，交付件未做）**：38 个 loader 里 **18 个**在首个 `ret` 之后
仍有可达代码（17 个失败尾声 `pop…; xor al,al; …; ret`，1 个是容器 `Read_File` 的清理路径），
但**冷块内不含任何键字面量** ⇒ `dump_rules_keys.py` 的「首个 `ret`」边界**没有漏键**。
**但这不使 `first ret` 成为正确判据**——要分析冷块内容必须用跳转闭包。

**两个必须按偏移而非名字统计的表**：`EngineerCaptureLevel`（`+0x17F8`/`+0x17FC`）、
`Smoke`（`+0x0BAC`/`+0x0BB0`）各是**两个合法条目**，按名字去重会假性少一个。

**★ 660 / 651 / 650 三个数的量纲（R-032 核验）**：

| 数 | 数的是什么 |
|--:|:--|
| **660** | 读取**站点**数（同键读两次算两个）|
| **651** | **loader 内**去重（上表口径）|
| **650** | **跨 loader** 去重（`ContentScan` 在 Difficulty/IQ 各读一次）|

站点 − 键 = 9，全部是 loader 内双读：`Read_General` 1 / `Read_AudioVisual` 1 /
`Read_LandCharacteristics` 7。**这三个数混用就是量纲错误。**

### C.15d 字典节的四条机器判据（R-032 核验，2026-10-23）

> 门禁 `tools/verify_r032_claims.py` **13/13 PASS，EXIT=0**（sha16 `84b3f0b8ded6391f`）；
> 证据 `evidence/r032_h015_dictionary_sections_verification.md`；正文 `kb/30` §14.5。

C.15c 里"20 个 loader 枚举键名"这句话，本轮拆成四条**可执行**判据：

1. **★ 族 A（17/20）注册的是「值」，不是「键名」**（16 站点全对）。
   `GetKeyName` 的返回值进的是 `ReadString` 的**键槽**，注册 callee 的 `this`
   是 `ReadString` 的**落盘缓冲** ⇒ **键名是查表的键，值是数据**。
   **编译器写对的一处**：`[VehicleTypes]` 要写 `0=HTNK`（值=类型名），
   **不是** `HTNK=1`（反写不报错，只静默生成叫 `1` 的垃圾条目）。
2. **值取不到就不注册**（17/17）：`test eax,eax / je 跳过注册` ⇒
   **`Key=` 与「不写这个键」完全等价**。
3. **注册端有保留字挡板**：先比 `0x00817474 "<none>"`、再比 `0x00817694 "none"`，
   两个 `je` 都跳 `0x74814E`（`xor eax,eax` 零返回）⇒ 不建条目。
4. **20 个枚举 loader 分两族 —— 只有族 B 是「键名即数据」**：

| 族 | 数量 | 形状 | 谁被当数据 | 值能不能空 |
|:--|--:|:--|:--|:--|
| **A** | 17 | `GetKeyName`→`ReadString`→有值才注册 | **值** | 不能空 |
| **B** | 3 | `Read_ColorAdd`/`Read_Colors`/`Read_Sides`，键名直接进查找/构造 | **键名** | 不读值 |

**参数个数以 `ret imm16` 为准**（P2）：`0x526810`→1 / `0x526960`→1 / `0x526CC0`→2 /
`0x528A10`→**5** / `0x5283D0`→4 / `0x5276D0`→3 / `0x5295F0`→3 / `0x529160`→4。
这更正了 `dump_rules_keys.py` 的 `READER_KEYS`（把 `0x528A10`/`0x528F00` 记作 4、
`0x529160` 记作 3），**但不影响键清单** —— 那里 `want` 只作走步上限，键永远是倒数第二个 push。
机制见 `CONFLICTS.md` **G-52**（编译器调度优化不能当判据）。

### C.15e 函数入口分母的两个界与「调试字符串命名」的天花板（R-035，2026-10-23；R-038 修正定性）

> 门禁 `tools/verify_r035_claims.py` **23/23 PASS，EXIT=0**（R-060 对齐读法转正版，
> 含新增 R1..R6 计数断言；P1 恒真项单列不计 PASS 数，有效断言 22 条；
> R-038 修复版曾为 17/17）；
> 变异 `tools/mutate_r060_gate.py` **14/14 精确集合击杀 + G-79 覆盖 23/23**（区分性对 C11/C12）；
> 证据 `evidence/r035_denominator_both_directions.md`（**取代** r034 件）。
>
> **⚠⚠ R-038（异族盲验 V-001 触发）**：§三 的「LOWER 13,352 是下界」**定性被推翻**
> —— E8 侧同样存在字节扫描幻影（563 源 / 560 个只被幻影指向的目标）。
> 对齐族 **LOWER 12,792 / UPPER 13,683 / 4.28%…4.07%** 为推荐引用口径（R-060 勘误
> 原 13,682：头部须对对齐 CFG 收集，0x40A090 补回）；
> 13,352/14,242 降为「上界族」并列存档。**方向结论不变**（两口径都高于 3.62%）。
> 复现 `tools/r038_e8_phantom.py`；LEDGER R-038 条。


**① 分母两边都错，净效果是偏高。** `fn_walk.py` 的 `raw_rel32_targets()`
把 `E8`（call）与 `E9`（jmp）混成一个根集，并把**每个根都标成函数入口**。
E9 兼作函数内块跳转 ⇒ 假入口。

| 量 | 值 |
|:--|--:|
| E8 目标 | 7,279 |
| E9 目标 | 2,042（与 E8 重叠 138）|
| E9 目标中落在已覆盖代码内部（假入口）| **1,445** |

**② 修正口径（E9 一律当跳转）。**

| 口径 | 定义 | 值 | 覆盖率 |
|:--|:--|--:|--:|
| 上界族 LOWER（~~13,352 是下界~~ 已被 R-038 推翻定性，**只作上界**） | `E8 ∪ 虚表 ∪ PE 入口`，CFG 遍历**零新增** | **13,352** | **4.10%**（547）|
| 上界族 UPPER | 上界 LOWER + 890 个 CFG 到不了但序言完整的头 | **14,242** | **3.91%**（557）|
| **对齐族（推荐）** | 见上方 R-060 勘误行：**12,792 / 13,683 / 4.28%…4.07%** | | |
| ~~公布~~ | ~~扁平根集~~ | ~~15,224~~ | ~~3.62%~~ |

**两个界都高于公布值** ⇒ R-034 的「覆盖率更低」方向**被推翻**。

**③ 补集 ≠ 修正量**（G-56）：R-034 的 3,237 里 **2,352 个**落在已发现函数闭包内，
真正新函数 **885**；独立方法测 **890**；R-034 自己复核 **886** —— 三路收敛。

**④ R1-3 前提证伪**（G-57）：调试字符串能命名的函数上限 **17 个（0.15%）**。

| 来源 | 站点 | 实际是什么 |
|:--|--:|:--|
| 纯 `Class::Method` 字面量 | 5 个串 | 函数名（只有 5 个）|
| 以 `Class::Method` 开头 | 30 串 / **21 方法名** | 函数名 + 尾随文本 |
| push 这些字面量 | **35** | 归属 **17 个函数** |
| `__FILE__` | 1,299 | **源文件名**（91.6% 跟 `call 0x734E60` = `ret 8` 驻留表查找）|
| 裸标识符 | 3,688 | **62.1% 是 INI reader 实参 = 键名** |

**⑤ ~~副产品：去嵌套归属表~~（外层优先，闭包判定）—— ⚠ 函数列已被 R-036 判为不可复现**

> **推翻横幅（2026-10-23，R-036 / R-036b）**：原表「761 / 277」两个函数数在
> R-036 的 12 种**闭包类**口径下**均无法复现**（落在 730…838，最近 758）。
> R-036b 补测**地址类**规则后：入口集 `roots_call|T2`(14,238) + 「最近前驱且闭包包含」
> **合计 761 精确命中且稳定**（删 100 个入口仍 752–756），**但四列为 418/149/290/289**，
> 与 425/147/289/277 不符 ⇒ **合计可复现、分列不可复现**，不采用。
> 站点数 **2,589** 与 **3,688** 精确复现（R-039 注：均为字节扫描口径，对齐口径
> 各为 2,588 / 3,688 —— text 类有 1 个 `cmp ...,0x68` imm8 幻影，不归属任何函数）。
> 处置：函数列作废，改引 R-036 实测值；见 `evidence/r036_r13_deliverable.md` §三。

| 类 | 站点 | 命中函数（R-036 实测，最早入口优先）|
|:--|--:|--:|
| path | 1,299 | 425 |
| format | 351 | 146 |
| text | 939 | 288 |
| **debug 合计** | **2,589** | **758**（~~R-035 报 761~~）|
| ident（不计入命名）| 3,688 | 274（~~R-035 报 277~~）|

未归属 debug 站点 391 / 2,589；四类合计 6,277。

### C.16b 虚表 `vtable[11]/[12]` 契约的**真实作用域**（R-037，2026-10-23）

> 门禁 `tools/verify_r037_scope.py` **8/8 PASS，EXIT=0**；
> 变异 `tools/mutate_r037_gate.py` **3/3 killed（精确集合判定），EXIT=0**；
> 证据 `evidence/r037_vtable_scope.txt`（含 69 个类的 ID/尺寸全表）。

**★ 修正 `kb/20` 的载荷句**：原文「**任何** `AbstractClass*` 都能用 `vtable[11]`
识别真实类型」**范围过宽**。

| 层 | 类数 | 说明 |
|:--|--:|:--|
| RTTI 总类数 | 988 | |
| 带虚表 | 954 | 其余 34 无虚表 |
| 虚表槽数 ≤12 | **804** | `vfunc_count` 独立给出；**槽 11/12 不存在** |
| 虚表槽数 >12 | 150 | |
| **`AbstractClass` 后代** | **78** | **契约真正的作用域** |
| 其中符合 | **69**（88.5%） | 槽 11/12 = `mov eax,imm; ret` |
| 其中不符合 | **9** | 全是抽象中间基类 |

**9 个不符合的类**：`AbstractClass` / `AbstractTypeClass` / `ObjectClass` /
`ObjectTypeClass` / `MissionClass` / `RadioClass` / `TechnoClass` /
`TechnoTypeClass` / `FootClass` —— 槽 11/12 都指向 `0x004C9150`
（`33 C0 C3` = `xor eax,eax; ret`），**返回 0 而非 ID**。

**但契约对实例仍安全**：69 个符合类里**被继承的 = 0**（全是叶子/最派生类），
而真实对象的虚表必是最派生类的那张。⇒ 只有故意拿中间基类的虚表去读才会拿到 0。

**正确表述**：对**具体的（最派生的）**`AbstractClass` 实例，`vtable[11]` 是类型 ID、
`vtable[12]` 是尺寸；69 个叶子类型类全部成立。分母是 **78**，不是 954 也不是 988。

**变异抓到门禁缺陷**：P6 初版只比对「9 类指向同一指针」，改桩字节时**不变红**
（指针没变，改的是指针指向的内容）。补上「该地址字节确为 `33 C0 C3`」才可杀。

### C.16d P1 共享库：机器可读的 `class_contract.json`（R-040，2026-10-23）

> 门禁 `tools/r040_shared_contract.py` **6/6 PASS**（C3/C4/C5/C7 字节可钉；
> C1 恒真、C2/C6 结构性普查具名标注）；变异 `tools/mutate_r040_gate.py`
> **4/4 killed（精确集合）**；交付物 `evidence/class_contract.json`
> （schema `ra2-atlas/class-contract/v1`）。HANDOFF H-027/H-028。

**内容**：69 个最派生叶子类的 `{class, vtable, slots, id, size, id_fn, size_fn,
engine_name}` + 9 个抽象中间基类名单 + 名字表/桩地址 + population 漏斗；
**作用域声明写进 json 的 `scope` 字段**（「对具体实例成立、对中间基类不成立」
随数据交付）。全部数值生成时从字节重读，消费方可逐行复算。

**★ kb/20 §1 勘误（G-59 首例）**：门禁 C4 照搬散文「`value` **严格递增**」首跑变红——
实测名字表**存储顺序非单调**（条目 69=`Temporal(0x46)`、70=`RadSite(0x45)`），
但**值集合 = {0x00..0x49}（74 不同值）无空穴**成立。判据改为集合相等；
「无空穴」不受影响。**形状词不可从散文搬进断言**——红在自家文档措辞上时，
默认怀疑文档而不是改断言迁就它。

**又一记 G-55**：本轮变异目标凭记忆写错两处（GetSize 地址、C5 级联预期），
纠正流程 = 基线 → 逐变异**实测**红集 → 实测值才写进预期；C5 解耦派生集后 4/4 精确。

### C.16c R1-3 交付件：17 个函数名 / 69 个可归属源文件（R-036，2026-10-23）

> 门禁 `tools/r036_r13_deliverable.py` **8/8 PASS，EXIT=0**（含 R-039 P3b 对齐复核）；
> 变异 `tools/mutate_r036_gate.py` **7/7 killed（精确集合判定），EXIT=0**；
> 证据 `evidence/r036_r13_deliverable.md` / `.txt`（含 5,882 行逐站点明细）、
> `evidence/r039_push_aligned.txt`（0x68 对齐复核，1 幻影逐址）。

**D-03 裁决 A 的执行产物。** R1-3 标**已完成，目标下调**。

| 项 | 值 | 口径 |
|:--|--:|:--|
| 可命名的函数 | **17** | 35 个 `push 'Class::Method'` 站点去嵌套归属 |
| 源文件（可归属） | **69** | `__FILE__` 去重 **74** 个 basename，5 个零归属 |
| debug 字符串站点 | **2,589** 字节扫描 / **2,588** 对齐 | path 1,299 + format 351 + text 939/938（R-039：1 个 text 幻影 `0x5BA0CE`=`cmp eax,0x68` 的 imm8，不归属任何函数 ⇒ 17/69 两数不变） |


**三个引用陷阱**：

1. **「69 个源文件」≠「镜像里有 69 个 .cpp」**。文件总数 **74**；69 是「至少一个站点
   能归属到函数」的文件数。零归属的 5 个：`CD.CPP` / `Event.CPP` / `GameDlg.CPP` /
   `Score.CPP` / `stlscore.cpp`。
2. **「17 个函数名」只说明该函数 push 了这个串**，不证明它就是那个方法。
   自洽的只有 `0x652CF3 push 'RadarClass::One_Time()'`（在 `0x652CF0` 体内）。
3. **地址是「最早入口优先」下的入口**。`RadarClass::One_Time` 给 `0x63F7B0`
   （`jmp 0x652CF0` 的尾调用 thunk），本体在 `0x652CF0`；要本体须再跟一次 `jmp`。

**新欠账**：R-035 §六 的 761 —— **合计在地址类规则下可复现且稳定，但四列不符**，
不采用；R-035 §2 的「426,741 / 40% 重叠」完全不可复现（实测 **523,181 / 48.7%**）。
两项待 C 会话独立复算。

### C.14 全引擎 INI 键索引（R-031 定稿口径）

| 项 | 值 | 口径 |
|:--|--:|:--|
| 读取器调用点 | **2,426** | `E8` 字节扫描 == 指令扫描，逐址零差异 |
| 键是字面量 | **2,209 站点 / 2,023 键** | ABI 键槽（6 读取器取倒数第 2 push，`GetSection` 取最后 1 push） |
| 键非字面量 | **217** | 寄存器/缓冲 210 + 空槽 7 |
| 多读键（≥2 站点） | **137** | |
| **含 `%` 的字面量键** | **0** | 21 个 `%` 串全是**运行期拼键模板**，不是键 |

**两条编译器规则**：

1. **任何含 `%` 的串都不能当键写进 INI。** 它们是模板
   （`PowerUp%01dYSort` → 真键 `PowerUp0YSort`…`PowerUp9YSort`）。
2. **同一个键名可能被多个 loader 各读一遍**（137 个实证多读键），
   改一处不保证全局生效。

**M1 旧口径（2,305/1,893/164/121）只作"范围内存在字面量 push 的站点数"**，
M1 在 **340 个站点**上与键槽不一致：91 个键槽是寄存器、5 个空槽、
**244 个是抓到了节名**（`General` 57 / `Basic` 38 / `MultiPlayer` 21 …）。

复跑：`python re_atlas/tools/r031_authoritative_numbers.py`（17/17 PASS, EXIT=0）；
证据 `evidence/r031_section12_restatement.md`；正文 `kb/30` §12.7。

### C.16e L-21 定谳：`TEventClass+0x28`=前驱事件（同类回链）、`+0x30`=`TeamTypeClass*`（R-041，2026-10-24）

> 门禁 `tools/r041_l21_eventteam.py` **10/10 字节断言 PASS**（X0 指纹恒真、
> X6 结构性具名，均不入分母）；变异 `tools/mutate_r041_gate.py`
> **10/10 killed（精确集合）**；证据 `evidence/r041_l21_eventteam.md`。

**结论**：`+0x28` 由事件列表 loader（`0x7274FD` `new 0x58→call 0x71E6A0`、
`call 0x71F4E0; mov [esi+0x28],[ebp+0xAC]`）逐条回链，槽10（`0x71F800`）
按同类同偏移再读=摘链 ⇒ **前一个 `TEventClass`**。`+0x30` 唯一取值写入在
parse fn `0x71F4E0`（`call 0x6F0FC0; mov [esi+0x30],eax`）；resolver 扫全局
注册表向量 `[0xA8ECA4]/[0xA8ECB0]` 比对 `[item+0x24]` Name/`[item+0x64]`，
注册表持有物 facet `0x7F47AC/0x7F47A4`（主表 `0x7F47D0`−0x24/−0x2C 间距）+
`TeamTypeClass.vfuncs ∋ 0x6F1030` 双证 ⇒ **`TeamTypeClass*`**；
`"TeamTypes"` reader 未命中即 `new 0xF8`（248=G-1）。

**抓到两件事**（详见 LEDGER R-041 §3）：
1. **G-60**：census 假阴性（`endswith` 用错操作数侧）产出的「0 处」差点写进交付件——
   否定式断言必须自带阳性对照；纠正后真实簇站点表钉进 X10。
2. **悬项编号先查再发**：首稿新开 L-24，但台账 max=L-28 ⇒ 改 **L-29**（+0x54 归属）。

**作用域**：类名定谳，不宣称任何地址可改写。真机/异族核验欠账同 R-035…R-041。

### C.16f L-29 定谳：`TEventClass+0x54`=事件挂接对端对象的运行时缓存（R-042，2026-10-24）

> 门禁 `tools/r042_l29_field54.py` **9/9 字节断言 PASS**（G0 指纹恒真、S1 结构性
> 具名，均不入分母；S1 红仍非零退出）；变异 `tools/mutate_r042_gate.py`
> **10/10 killed（精确集合）**；证据 `evidence/r042_l29_field54.md`。

**结论**：`+0x54` 是构造即清零（ctor `0x71E6BE`，G1）、swizzle 登记（`0x71F91B`，G2）、
**不进 Save**（`0x71F820..0x71F87A` 整窗 0x5B 字节钉死，G3）的**运行时缓存**。
存活写入=handler `0x71E940`（this=ebp）@`0x71F209`：受 `[this+0x34]==-1` 门控、值=
传入对象 **vtable slot15(+0x3c)** 返回值（主表 slot15=`0x4104A0`=`xor eax,eax;ret`
引擎共享桩 ⇒ 裸 TEvent 恒 NULL）。setter `0x71FA44` 三面普查（E8/E9/立即数）零引用
=**死访问器**（G9）。读侧 getter `0x71FA30` 唯二调用者 `0x726551/5c`，非空收割进
容器 `[esi+0x2C]`（G7）。簇域存储 census 收口恰 {0x71E6BE, 0x71F209, 0x71FA44}（G8）。

**抓到三件事**（详见 LEDGER R-042 §2、CONFLICTS G-61）：
1. **SIB 陷阱**：modrm `rm==4`=SIB 非 esi——首版普查把 `0x44` 当 esi 双向失真。
2. **`op.size` 单位=字节**：dword 判据 `==4` 非 `==32`，否则全镜像 0 命中
   （G-60 假阴性第二次复发形态，阳性对照当场抓到）。
3. **resync 助手地址漂移**：幻影 0x71F216；raw 字节坐实 R-041 登记 `0x71F209` 本就正确。

**作用域**：字段语义定谳，不宣称任何地址可改写。L-20 由此获得现象解释（运行时缓存
⇒ 无需存档）但**非证明**，保持开放。新债 L-30（handler 参数对象/容器类归属）。
真机/异族核验欠账同 R-035…R-042。

### C.16g L-30 进展：`+0x54` 写门查询的注册表定谳 = `DynamicVectorClass<HouseClass*>` @`0xA80228`（R-043，2026-10-24）

> 门禁 `tools/r043_l30_housevec.py` **6/6 字节断言 PASS**（G0 指纹、Y2b 结构性具名
> 不入分母，但**Y2b 已改造为读内存态 ⇒ 可被变异证伪**）；变异 `tools/mutate_r043_gate.py`
> **12/12 killed（精确集合）**；证据 `evidence/r043_l30_housevec.md`。

**结论**：R-042 钉住的写门（handler `0x71E940`@`0x71F209` 前置）调用查找器 `0x502D30`
（整函数 0x30 字节钉死）遍历全局对象 `this=0xA80228` 的向量 `[0xA8022C]`×计数 `[0xA80238]`，
按 `[[item+0x34]+0xB8]==事件参数` 匹配；该对象 vptr 两态 `0x7E9EE4/0x7E9F04` 的 RTTI TD 名
= `?$DynamicVectorClass@PAVHouseClass@@`/`?$VectorClass@PAVHouseClass@@`（镜像串直存）
⇒ **门查询注册表 = `DynamicVectorClass<HouseClass*>`**（元素类型半边定谳）。
存储站 census（全编码 a3/89+r/m/c705/88/a2）：`[0xA8022C]←` 恰 {init 0x4E6CE7,
teardown 0x4E6D47}、`[0xA80238]←` 恰 {init 0x4E6D11, Push 0x4F61E0}；元素写入
0x4F61EC `mov [ecx+eax*4],ebp`。HouseClass 自证：slot11=`mov eax,0xd;ret` 与
AbstractType 名字表（@0x816EE0，实测 word0=nameptr/word1=id）第 0x0D 对 'House'/0x0D
交叉闭合。

**收紧（G-62）**：**不宣称 `+0x54`=House\***——存入的是 arg2.slot15() 返回值；
HouseClass 裸 slot15=`xor eax,eax` 桩 ⇒ arg2 若是裸 HouseClass 则 +0x54 恒 NULL
自相矛盾 ⇒ **arg2 不是 HouseClass**（自带反证）。arg2 具体类/容器 `[esi+0x2C]`
元素类/消费方宿主类未定谳 ⇒ L-30 保持开放（本轮半闭）。miss 路径解引用疑点登记。

**新坑 G-62**：结构性断言首版从磁盘重读⇒变异永不捕（改内存态）；散文把「相等关系」
写成「等于」⇒G-57 的身份等号变体。名字表行序第 69 行起不按 id 排（0x46,0x45…），
已交付「值域 0x00..0x49 无空穴」结论不排序仍成立。
真机/异族核验欠账同 R-035…R-043。

### C.16h L-4 大块半闭：`ScriptTypeClass`(0x234) Save 载荷=计数 +0xA0、数组 +0xA8 步长8=TeamType 注册表索引（R-044，2026-10-24）

> 门禁 `tools/r044_scripttype_block.py` **9/9 字节断言 PASS**（G0 指纹、X10 结构性具名
> 不入分母，X10 红仍非零退出）；变异 `tools/mutate_r044_gate.py` **15/15 killed（精确
> 集合）**（M4 共享字节 Save 窗+X9 阳性对照同被杀）；证据 `evidence/r044_scripttype_block.md`。

**结论**：`ScriptTypeClass::Save`（slot13 `0x691E00`，整窗 0x21 字节钉死）自有载荷仅一个
dword——`mov eax,[esi+0xA0]`（计数）；其余基类 `AbstractTypeClass::Save` `0x410BE0`
（整窗 0x34 字节）序列化三串（Name+0x24/+0x64/+0x3D，全走 `repne scasb` strlen 串 writer
`0x4A1DB0`）。数组 `[+0xA8]`（步长 8，由 fixup slot10 `0x691E30` 管理）**不进 Save**：
门 `call [arg_vt+0x2c]→cmp eax,0x23`（=TeamType，名字表第 0x23 对交叉），数组条目=TeamType
在注册表 `[0xA8ECA4]/[0xA8ECB0]`（R-041 同一对全局）的下标，TeamType 被删时 `dec` 前移
重编号（`add edx,8`@0x691EB2、`488902`@0x691E98 双坐实）。GetSize=0x234/WhatAmI=0x1B
双证。L-4 **半闭**：条目内双 dword 细分转按需。

**新坑 G-63（本轮最大方法论发现，教训分级）**：同一 resync 地址漂移的**机制自诊错了
两次且都写进正式台账**——R-042「忘同步 PC（少推进）」与本轮初稿「16B 窗口截断」。
**消融实验证否两者**：真实机制=双游标（偏移 o 与地址 a）都 +=size、又把 `a+o` 喂 disasm
⇒ 地址 **2× 前进**（win=255 覆盖整段仍漂→窗口大小无关）。判据：**现象有字节坐实才写进
结论；根因未复测只标「待证假设」**（按错的根因去修=完全无效的方向）。事实源纪律更新为
「单次整段 `md.disasm()` 线性解码 + 独立 raw 字节 `find()` 双印证才进断言」，三处产物
（LEDGER §2.3/CONFLICTS G-61 判据3/r042 evidence）就地挂勘误指针（现象保留、机制推翻）。

**作用域**：类布局定谳，不宣称任何地址可改写。真机/异族核验欠账同 R-035…R-044。

### C.16i L-4 细目收口：`+0xA0` 计数生命周期八站全归因（R-045，2026-10-24）

> 门禁 `tools/r045_count_lifecycle.py` **8/8 字节断言 PASS**（G0 指纹不入分母）；
> 变异 `tools/mutate_r045_gate.py` **13/13 killed（精确集合）**；
> 证据 `evidence/r045_count_lifecycle.md`。

**结论**：R-044 留作细目的「census 存储点逐个功能归属」与「条目内双 dword」两项就此收口，
站点集合=R-044 X9 census 集合（无遗漏）：

- **清零两处**：ctor `0x6916C7`/`0x691C8B`（`c7 86 a0…` imm32=0 + 6 字节内主 vptr
  `mov [esi],0x7F1008` 邻接，Z1/Z2）；**解析入口 `0x6918CF`**——`mov [esi+0xA0],edi`
  前 5 字节 `xor edi,edi` ⇒ **edi 恒 0**（Z4+C11 双窗钉死；kb/11 原注「计数清零」成立）。
- **建表循环（Z8）**：元素对写 `mov [esi+eax*8+0xA4],ecx` / `…+0xA8],edx`
  （modrm rm==4=**SIB** base=esi idx=eax scale=8）⇒ **元素=8 字节对 [+0xA4 键,+0xA8 值]**；
  界 imm `0x32`（=50，值语义不宣称）；自增 `read;inc;store` @0x691940..47（Z7）。
- **读侧**：循环上界 `0x691547`（Z5）、界检查 `0x69191F`（`mov eax,[esi+0xA0]; cmp
  eax,0x32`）、Save `0x691E0E`、fixup `0x691E4B/0x691EAB`——后三站字节窗 R-044 X2/X7
  已钉（但当时只列 census 址未标功能），本轮 census 复现（Z6）+ 生命周期归属收口。

**新坑 G-64（本轮最重要，被自家 G-63 纪律当场抓出）**：Z4 首版把「源=寄存器」误标成
「写非常量（非清零）」——复核现场前 5 字节即 `xor edi,edi`，**语义词（非零/初值/累加）
必须锚到现场数据流字节**；翻转后「恒 0」成为可杀断言（C11 专测）。G-57 取值纪律在
语义标注层的推论。其余：手敲 read 长度 vs hex 字节数不符 ×2（G-61 判据 2 第三次现场）、
Z4 边界宣称收敛（槽入口≠体边界）、变异共窗预期实测化 ×2、**LEDGER「待推」重复行删重**
（行级缺陷只有真读才发现）。

**作用域**：字段生命周期归因，不宣称任何地址可改写。真机/异族核验欠账同 R-035…R-045。

### C.16j L-4 残余定谳：双构造现场 = plain ctor `0x6916B0` vs INI find-or-create 工厂 `0x691C00`（R-046，2026-10-24）

> 门禁 `tools/r046_ctor_vs_factory.py` **7/7 字节断言 PASS**（G0/S1 不入分母）；
> 变异 `tools/mutate_r046_gate.py` **13/13 killed（精确集合）**；
> 证据 `evidence/r046_ctor_vs_factory.md`。

**结论**：R-045 登记的「两 ctor 变体（`0x6916C7`/`0x691C8B` 同型双零）归属」定谳——
**同一类 `ScriptTypeClass` 的两个入口，非派生变体**：① **plain ctor `0x6916B0`**：头
`mov esi,ecx(this); call 0x410800`（共享 init 助手，rel32 复算），且 **census：体内 E8
目标集合恰={0x410800}**（唯一调用、无分配器 ⇒ new 在调用方，散文声明落成可杀普查，C1）；
② **工厂 `0x691C00`**（`"ScriptTypes"` 节现场）：双串守卫 `'<none>'/'none'`→`call 0x7C8D20`
（strcmp 形态，rel32）je-fail；按名扫注册表 `[0x8B41CC]`（`add ecx,0x24` Name 槽）；未命中
`push 0x234`（=GetSize）`call 0x7C8E17`（分配包装头钉死）后走**同一 init**（C2）；
③ **共享 init 尾 0x2F 字节两站逐字节相等**（vptr 组全同 ⇒ 同一类，C3）；④ 两站都登记进
ScriptTypes 注册表并写下标 `mov [esi+0x98],eax`（@0x691763/0x691D26，C4/C6 census 恰两处，
**无第三形态**）；⑤ dtor `0x691770`：deleting 标志→重装 vptr→`call 0x7258D0`→
`[0x8B41D8]--`+**SIB 压缩**（后项下移）@0x6917CE/7D1→`call 0x4109C0`（C5）。

**顺带定谳**：`0x691A5B`（R-045「第三形态」疑点）**不是** ctor——只写 [+0xA0],ebx 无
[+0x9C] 伙伴，归因降级为「非 ctor 形态的 +0xA0 写入点」。

**新坑 G-65（判据复发性升格）**：G-61 判据 2（read 长度 vs hex 字节数）**连犯三轮**
（R-044×2/R-045×2/R-046×2）⇒ 登记为独立条目：判据写在文档≠执行，规则必须落成**工序顺序**
（先 print 字节再据此写 N，同轮内不隔回忆）。本轮同时**主动**把 C1「零分配」散文升级为
E8 集合 census（G-57 精神不等质疑再补）；升级过程中第一版踩 G-60 判据 2（切片双偏移混用）
当场 FAIL 修正——登记进诚实账。压缩后 +0x98 是否再修：静态不可见，只钉字节不宣称 bug。

**作用域**：构造路径定谳，不宣称任何地址可改写。真机/异族核验欠账同 R-035…R-046。

### C.16k L-20 候选证伪：`TriggerClass::Save` 不序列化 `event+0x54`（R-047，2026-10-24）

> 门禁 `tools/r047_l20_triggersave.py` **5/5 字节断言 PASS**（G0/S1 不入分母，S1 红仍非零退出）；
> 变异 `tools/mutate_r047_gate.py` **12/12 killed（精确集合；S1=RTTI-JSON 不可杀，如实不列）**；
> 证据 `evidence/r047_l20_triggersave.md`。

**结论（分两层）**：kb/21 §1.2 点名的候选解释「`+0x54` 或由 `TriggerClass` 存档负责」
**证伪**——`TriggerClass::Save`（主表 `0x7F5858` slot13 @`0x726790`）整窗 **0x86 字节**
（53 指令→`ret 4`）逐字节钉死（T2）；窗内 **disp 普查 +0x54 = 0 处**（阳性对照：同解析器
看得见 +0x24/28/30/34/3c/40/44 七字段，T3=G-60 对自身执行）；**直接 call 目标集
（capstone 线性解码取 imm）恰={基类 Save `0x410410`×1, `0x4A1CA0`×2, `0x4A1D50`×4}**
（+2 个 facet 间接 call `[ecx/edx+0x10]` 与 R-042 X2 同形态，T4）；`event+0x54` 唯一存活
写入者 handler `0x71E940` 的全镜像 E8 入口 `{0x726540}` 不在 Save 路径（T5）。类身份闭合
（T1：WhatAmI 0x26、GetSize 0x48=72 台账复证、名字表第 0x26 对='Trigger'）。
⇒ **但 L-20 不关闭**：证伪一条点名候选 ≠ 定谳「谁存档」；完整答案要裁决读侧容器宿主类
（L-30 域）。R-042 运行时缓存假说再多一条负证据。

**新坑 G-66（本轮最重要，登记 CONFLICTS）**：① 探索脚本用回**双游标 `dump()`**（G-63
定谳的漂移形态），其地址表被抄进变异偏移 ⇒ 首跑 8/12 偏差（M3 目标落窗外 rc=0 不红）
才暴露——**交付件里从"另一段脚本打印"抄的字节位置，须与该脚本共用同一解析器**；② 写
诚实账时凭记忆**过度归因**（初稿称 T4 raw 扫描把幻影钉进台账），双解析器对照证伪——
本窗 raw 与 capstone 目标集**逐字节一致**，T4 值本就对、只是**方法脆弱**（bytescan-phantom
在册，此窗 imm 恰无 0xE8 字节）。⇒ **诚实账须区分「值错」与「方法脆弱」**，改 T4 是换
更稳取数方式而非纠错值；落笔前对两版解析器实际输出各跑一遍。**G-65 工序本轮正向生效**：
T1/T2/T4/T5 hex 全部先 print 后贴，一次通过。

**作用域**：候选路径证伪，不宣称任何地址可改写。真机/异族核验欠账同 R-035…R-047。

### C.16l L-30 消费侧收口：收割函数 `0x7264C0` 宿主 = `TriggerClass`；「容器 +0x2C」证伪为标量字段（R-048，2026-10-24）

> 门禁 `tools/r048_triggerclass_host.py` **10/10 字节断言 PASS**（V0 指纹 + S1 结构性不入
> 分母，红仍非零退出）；变异 `tools/mutate_r048_gate.py` **13/13 killed（精确集合）**；
> 证据 `evidence/r048_triggerclass_host.md`。

**结论**：R-042/R-043 遗留的「消费方 `0x7264C0` 宿主类未定谳」收口——this 字段集
**恰** = {`+0x24`,`+0x2C`,`+0x30`,`+0x34`,`+0x40`,`+0x44`}（V2 单点线性解码精确集合），
与 `TriggerClass` ctor `0x725FA0` 初始化集双向吻合（V3）；vtable `0x7F5858` slot10
（detach `0x726690`）/slot13（Save `0x726790`）与消费方操作字段同域（V10）；入口集恰
{`0x6E5414`} 且 V7 内嵌阳性对照（同扫描见 handler 入口 {0x726540}）。
**「容器 `[esi+0x2C]`」证伪为标量对端字段**：setter `0x726920`（ret 4）/getter `0x726910`/
detach 等值摘除（V8 三件套），站点值不变、措辞三处挂【勘误】。整条「写 +0x54（handler
`0x71E940`，arg2 经 `[T+0x24]→+0xA4→+0xB4` 链）→ 读 +0x54（getter `0x71FA30`）→ 存
this+0x2C」链**只经这一个 TriggerClass 成员函数**（V4/V5/V6 字节+rel32 复算）。
⇒ **L-20 升级为正面机制**：`+0x54`/`+0x2C` 是使能收割趟重算的运行时对（无存档需求），
「谁存档」问题改写为「载入后是否必跑」——后者需动态序证据，L-20 仍开放。
L-30 残余：owner 类（`[T+0x24]`=ctor arg1，与 TaskForceClass 容器簇特征吻合，线索非取证）、
调用方 `0x6E53A0` 宿主（72 个 E8 入口）。

**新坑 G-67（登记 CONFLICTS）**：变异偏移心算 5/13 全错（M2/M3/M8/M10/M13），被
「权威窗 hex 全等 + 目标偏移现值==预期」机械前置全数拦下 ⇒ **偏移禁心算，验证脚本
先行**（G-66 教训的工序化闭环）。V7 阳性对照内嵌化后，M6 共享字节如实杀 {V6,V7} 两例。

**作用域**：宿主类定谳，不宣称任何地址可改写。真机/异族核验欠账同 R-035…R-048。

### C.16m D-06 裁决执行：两路 GLM 异族盲验三回合收敛命中 LOWER_ALIGNED=12,792 ⇒ 口径三档定稿（R-049，2026-10-24）

> 实录 `evidence/r049_d06_blind.md`；工作流 run 链 63af8f20→5fb436b8→028e2790
> （`out/_wfb_d06_blind.ts`）；子代理通道 `new-provider-2/glm-5.3-flash$max`×2（章程 §6 异族）。

**Lead 裁决 v8 §2.1 三动作全执行**：① 口径头「暂定」→**三档定稿**（上界族 13,352/14,242、
对齐族 **12,792/13,682 推荐引用**【R-060 勘误：UPPER 实为 13,683——当年把裁决文本
13,683 判成「笔误」读为 13,682 是**判反了**：13,682 = 12,792 + 字节扫描头部 890，
两种读法混算；对齐头部应为 891】、UPPER 敏感度 ≈2× 注记）；
② H-022 标**已交付**；③ **D-06 已删**（本 LEDGER/INDEX 行留痕）。§2.3 同轮落地：契约
`object_fields` 段 + `population_note_R037`（17 锚点逐字节验证）→ H-037。

**三回合方法论实录（新坑 G-68）**：v1 任务书内嵌恒真 oracle ⇒ 两路**一致地错**
（PHANTOM=0，六数逐值相等但全错）；v2 判据修对但「闭包遍历」留实现自由度 ⇒ 两路
**发散地错**（12,321/2,599，权威 563）；v3 方法B 逐字线性规格（主会话预跑出
68,807/68,244/563 后才派发）+ 三路可见性自检（真 call `0x7274FF` + 已知幻影
`0x4077DE`/`0x4094E8`）⇒ 六数全等命中 12,792。**证据力如实分档**：v3=「规格钉死后的
独立实现」级复现；方法论级跨族互证=V-001（自写）+ R-038（自写）早已吻合。被裁值只进
脚本比对逻辑、不进子代理提示词（防泄漏已验）。

**作用域**：口径定稿动作件，不宣称任何地址可改写。R-036b 两挂账（761 分列/426,741）维持不用。

### C.16n L-30 实例容器定谳：TriggerClass 对象由 `DynamicVectorClass<AbstractClass*>` @`0xB0F670` 持有（R-050，2026-10-24）

> 门禁 `tools/r050_trigger_registry.py` **7/7 字节断言 PASS**（S1 结构性不入分母，红仍非零退出）；
> 变异 `tools/mutate_r050_gate.py` **12/12 killed（精确集合；pre-run 现值断言前置）**；
> 证据 `evidence/r050_trigger_registry.md/.txt`；探索件 `tools/_probe_r050_registry.py`。

**结论**：R-048 登记的「谁持有 TriggerClass 实例」收口——注册表全局 `0xB0F670` 装
vptr `0x7E91EC` = **`DynamicVectorClass<AbstractClass*>`**（降级 `0x7E920C`=
`VectorClass<AbstractClass*>`）。**不是 `<TriggerClass*>`**：名串 `PAVTriggerClass` 在
镜像存在但非本场所装 ⇒ **持有≠类型参数**（G-62 同族）。安装/降级 pattern 全 `.text`
各唯一站（W2）⇒ 无第三方改写容器类型；TriggerClass ctor `0x725FA0` 内注册块（W5 整窗
`ff5208` 虚槽 2 Add + 尾 `893481` SIB 存）把 **this 入册**（esi 保全普查唯一写点=头部
`0x725FA2`，W6）；`mov ecx,0xB0F670` 全段 58 站（W7）⇒ **引擎级 AbstractClass 共享注册表**，
House/Radar 等后代都入它。**GOAL-3T 遍历全部 trigger 的静态入口 = 该向量筛
`WhatAmI==0x26`**（S1 引 kb/20 契约 + R-047 T1）。

**残量更新**：L-30 从三问缩到两问——owner 类（`[T+0x24]`=ctor arg1；attach 工厂
`0x6E4EC0..` 的 arg1 列表=全局 `0xB0F708` 向量，线索非取证）、调用方 `0x6E53A0` 宿主
（72 E8 入口）。L-20 不变更（重算趟对象源已有静态入口，「必跑」仍待动态序）。
> **⚠ 两问均已被后续轮处理（R-051/R-052）**：专用 trigger 表存在（C.16o）；`0x6E53A0`
> 宿主=TagClass 非虚成员（C.16p）；「attach 工厂 `0x6E4EC0`」措辞系 Tag ctor 本体误读，
> G-69 勘误见 C.16p 残量①重述段。

**新坑/复发**：G-60 **第三次复发**并入判据 4——普查尺子元组字段序错（存 `(va,vs,rp,rs)`
按 `(vs,va,rp,rs)` 解 ⇒ `fileoff` 拿 VA 比 RVA ⇒ 全局引用假零命中），修=canonical 元组 +
`assert SEC[0]==(0x1000,0x3DF38D,0x1000,0x3E0000)` 钉序 + **控制项**（House `0xA80228` 同扫
得 7 站）；esi 谓词方向错（「写 esi」误写成「内存基址=esi」0 条假绿）修法同。变异偏移
3 处心算错被 G-67 现值前置拒入。

**作用域**：容器类定谳，不宣称任何地址可改写。真机/异族核验欠账同 R-035…R-050。

> **⚠ 部分被推翻（R-051，2026-10-24）**：本节「**不是** `<TriggerClass*>`／不存在专用
> trigger 向量」**不成立**——TriggerClass ctor 向**三**个容器注册（`0xB0F670`、`0xB0F708`
> 皆 AbstractClass*，**`0xA8EAE8` = `DynamicVector<TriggerClass*>` 专用表**）。
> 遍历 trigger 请直接走 `0xA8EAE8`（无需 WhatAmI 过滤）。本节其余内容（`0xB0F670` 类型/布局/
> 入册值=this/58 站）仍成立。见下方 C.16o。

### C.16o **推翻** R-050：TriggerClass 专用注册表 `DynamicVectorClass<TriggerClass*>` @`0xA8EAE8`；ctor 三路注册（R-051，2026-10-24）

> 门禁 `tools/r051_trigger_three_registries.py` **8/8 字节断言 PASS**（S1 结构性不入分母）；
> 变异 `tools/mutate_r051_gate.py` **12/12 killed（精确集合；pre-run 现值前置）**；
> 证据 `evidence/r051_trigger_three_registries.md/.txt`。

**结论**：TriggerClass ctor `0x725FA0..0x726131`（`ret 4`）向**三**个向量注册同一 this：

| 腿 | 地址 | 全局 | 类型 | 引用 |
|:--|:--|:--|:--|--:|
| 1 | `0x725FE9` | `0xB0F670` | `DynamicVector<AbstractClass*>` | 116 |
| 2 | `0x72603A` | `0xB0F708` | `DynamicVector<AbstractClass*>`（同 vptr） | 12 |
| 3 | `0x72608D` | **`0xA8EAE8`** | **`DynamicVector<TriggerClass*>`** | 8 |

三腿逐字节同构；**`893481` 尾存在 ctor 内恰 3 处**（X3 可数控制）；dtor `0x726950`
（vtable slot8）三路对称注销；三容器 vptr 安装/降级 pattern 全段唯一（X5）。
**GOAL-3T**：遍历全部 trigger = 直接遍历 `0xA8EAE8`，无需 WhatAmI 过滤（H-039 取代 H-038）。

**方法论**：R-050 的 7/7+12/12 全绿不假，但结论从**一条腿外推总体**——「样本当总体」
（变种 F）在结构发现层复发。**N/N PASS 只覆盖被测命题**，不覆盖「别处没有第二条路」。

**作用域**：容器定谳，不宣称任何地址可改写。

### C.16p L-30 残余②定谳：收割驱动 `0x6E53A0` 宿主类 = TagClass（R-052，2026-10-24）

> 门禁 `tools/r052_tagclass_host.py` **10/10 字节断言 PASS**（S1 结构性不入分母）；
> 变异 `tools/mutate_r052_gate.py` **13/13 killed（精确集合；pre-run 现值前置）**；
> 证据 `evidence/r052_tagclass_host.md/.txt`。

**结论**：R-050 登记的 L-30 残量两问之②（调用方 `0x6E53A0` 宿主）定谳 = **TagClass 非虚成员**。
判据三路独立互锁，任一单独成立都指向同类：

| 路 | 取证 | 断言 |
|:--|:--|:--|
| 字段签名 | 体内 `[ebp+disp]` 集恰 `{0x24,0x28,0x2C,0x34,0x35}`，+0x34/+0x35 **字节**重入旗标 | Tag ctor `0x6E4DE0` 整窗（Y3）恰初始化同五字段 |
| 排除反证 | TriggerClass ctor 对 +0x34 是 **dword** 写、体内 `c64634`/`c64635` census=0/0 | 宿主≠TriggerClass（Y4，配镜像他处阳性对照） |
| 链路同一性 | Tag ctor 造 TriggerClass（rel32 复算=0x725FA0）头插 `[esi+0x28]`；`0x6E53A0` 从 `[ebp+0x28]` 起步逐成员调 `0x7264C0` | 链成员即宿主对象（Y5/Y6） |
| this 来源 | 调用点取 `[0x8B40CC]`=`DynamicVector<TagClass*>` 数据（vptr `0x7EA5A4` 安装唯一站 `0x4E7FCD`） | 迭代元素=TagClass*（Y9） |
| 类同一性 | RTTI `.?AVTagClass@@`；WhatAmI 槽11 TagClass=0x2C vs TriggerClass=0x26 | 双证（Y10） |
| 非虚成员 | `0x6E53A0` 不在任何 vtable（对齐 dword census=0；阳性对照=slot10 `0x6E5610` 命中 @0x7F4508） | 非虚（Y7） |

**副产物（新事实）**：① TagClass ctor 亦向**三**向量注册（专用 `0xB0E720`=`DynamicVector<TagClass*>`
+ 共享 `0xB0F670`/`0xB0F708`），ctor 跨度尾存 `893481` 恰 3 处（R-051 可数控制法**制度化复用**——
本轮直接把它作为「还有没有第四条腿」的可杀断言）；② **第四共享 Abstract 表 `0xB0F698`**
（vptr 同 `0x7E91EC`；`0x6E53A0` 尾段把本对象经 Add 后 `892c81` 存入，S1 结构性登记不定谳）。

**残量①重述（勘误 R-048/R-050/INDEX C.16n 措辞）**：旧「attach 工厂 `0x6E4EC0..`」地址**落在
TagClass ctor 本体跨度 `0x6E4DE0..0x6E4F59` 内**（非独立工厂，是 Tag ctor 的第 2 注册腿 + 节点链）；
TriggerClass`+0x24` 实存**挂接节点**（0x6E4F35 `push edi`=walked 节点）而非 Tag ctor arg1 原值。
⇒ L-30 残余①缩小为「Tag ctor arg1（`[arg1+0xA0]→+0xA8` 节点链宿主）的类归属」，调用点
`0x6C20CE`/`0x6E52D6`/`0x6E8D90` 在册待追。

**方法论**：宿主判定用**三路独立互锁**（字段签名+排除反证+链路/this 来源）而非单一签名——
单看 `[ebp+disp]` 集与 TriggerClass 部分重叠会误判；字节 vs dword 访问宽度（Y4）+ this 容器类型
（Y9）才是判据。异族盲验：R-051 三注册表结论的两路 GLM 盲验（工作流 `dwfrun-56dd81cd`）另记。

**作用域**：宿主类定谳，不宣称任何地址可改写（`0x6E53A0`/TagClass ctor 仅登记）。真机/动态序欠账同 L-20。

### C.16q L-30 残余①定谳：TagClass ctor `arg1` = `TagTypeClass*`（或 NULL）（R-053，2026-10-24）

> 门禁 `tools/r053_tag_arg1.py` **10/10 字节断言 PASS**（S1 结构性不入分母）；
> 变异 `tools/mutate_r053_gate.py` **16/16 killed（精确集合；G-67 现值前置）**；
> 证据 `evidence/r053_tag_arg1.md/.txt` + `evidence/r053_mutate.txt`。

**结论**：C.16p 残量①收口——TagClass ctor `0x6E4DE0` 的唯一栈参数 `arg1` 是
**`TagTypeClass*`，或 NULL**（工厂路径的无主 Tag）。全镜像 `E8→0x6E4DE0` 构造点**精确集合恰 3**
（`E9` 尾跳 **0**），三点各走一条建 Tag 路径：

| 站点 | 宿主 | arg1 来源 | 归属 |
|:--|:--|:--|:--|
| `0x6C20CE` | `TClassFactory<TagClass>` 虚表 `0x7F3A80` slot3 = `0x6C2090` | `push 0`（`6a00`@0x6C20CA） | **NULL**（无主 Tag） |
| `0x6E52D6` | find-or-create `0x6E52A0`（**按 `cmp [eax+0x24],edi` 去重**） | 调用者 `ecx`：`0x6E5E70` 从 `[0xB0E784]` 取元素 | **TagTypeClass\*** |
| `0x6E8D90` | TeamClass ctor `0x6E8A90`（`ret 0xc` 三参） | `[[esi+0x24]+0xD0]` | **TagTypeClass\*** |

**三路互锁**：

| 路 | 取证 | 断言 |
|:--|:--|:--|
| 站点 B 调用链 | `0x6E5E70` 扫 `[0xB0E784]`（= `DynamicVector<TagTypeClass*>` 的 data；vptr `0x7F4558`，安装站恰 `0x6E5AFD`/降级 `0x6E5B28`）取元素、比 `[elem+0x24]` 名串 | 返回值 ⇒ TagTypeClass* |
| 站点 C 两跳 | `TeamClass+0x24`=TeamTypeClass*（ctor 三参）；`TeamTypeClass+0xD0` 写入者**精确集合恰 3** `{0x6F0799,0x6F1041,0x6F135D}`，其值来自 `0x6E6310`：扫 `[0xB0E780]` 未命中则 `push 0xA4`（**= TagTypeClass GetSize**）+ `call 0x6E5B60`（**TagTypeClass ctor**） | ⇒ TagTypeClass* |
| 链头字段所有者 | TagTypeClass ctor `0x6E5B73` 清 `+0xA0`；dtor `0x6E5CA0` 沿 `[+0xA0]→[+0xA8]` 逐节点 `call [vptr+0x20]` 释放并回写；`0x6E5E50` 按值摘链 | `+0xA0` 归 TagTypeClass |

**arg1 的用途**：落 `Tag+0x24`；`cmp edi,ebx; je`（NULL 跳过）→ `mov edi,[edi+0xA0]` →
循环 `push 0x48; call 0x7C8E17; push edi; call 0x725FA0`（rel32 复算=TriggerClass ctor）→ 头插
`8b5628/895028/894628`（`Tag+0x28` 链）→ 回边 `mov edi,[edi+0xA8]`。
⇒ **`arg1+0xA0` 是 TriggerType 链头、`+0xA8` 是 next**；一个 Tag 实例按**每个** TriggerType
派生一个 TriggerClass 实例。与 R-052 的 `0x6E53A0` 三重门卫自洽：门卫含「owner `[+0x24]` 非空」，
NULL Tag 被自然跳过。

**六类身份同钉**（RTTI 名 + WhatAmI 槽11 + GetSize 槽12 三者）：

| 类 | 主虚表 | WhatAmI | GetSize |
|:--|:--|--:|--:|
| TagClass | `0x7F44E0` | `0x2C` | `0x38` |
| **TagTypeClass** | **`0x7F45C4`** | **`0x2D`** | **`0xA4`** |
| TriggerClass | `0x7F5858` | `0x26` | `0x48` |
| TriggerTypeClass | `0x7F5904` | `0x27` | `0xB4` |
| TeamClass | `0x7F4730` | `0x22` | `0xA0` |
| TeamTypeClass | `0x7F47D0` | `0x23` | `0xF8` |

**排除法**：arg1 在 Tag ctor 内**从不被 WhatAmI 检查、从不经其 vptr 调用**，唯一用途是取
`+0xA0` 链头 ⇒ 与「TagType 是类型描述符」一致。

**方法论（本轮两处门禁真空由变异自己抓出）**：M8 首跑「存活」⇒ Z6 只钉链头 `+0xA0` 与 rel32，
**没钉回边 `+0xA8` 本身**；M16 首跑「存活」⇒ S1 的 stderr 行写成 `S1 OK (...)` 而非
`S1 PASS:/FAIL:`，判别器按 `parts[1]=="FAIL:"` 解析不到。两处均**改门禁不改结论**（G-70 同族：
门禁抓不住变异就补强判据，绝不为通过而放宽断言）。另 M4 首稿**预期侧**写错（预言
`Z4+Z10` 双杀，实测只杀 `Z4`，因 `0x6E8D89` 在 Z10 census 窗之外）——按实测改预期并在脚本头注记。

**作用域**：类归属定谳，不宣称任何地址可改写。未做动态次序验证（同 L-20 欠账口径）。

### C.15 `RulesClass` 载入顺序（R-021 核验口径）

| 项 | 值 |
|:--|:--|
| 节名指针表 | `0x007F0C78`，31 项非空（共 32 槽） |
| `Init` `0x6686C0` | 只做一件事：`Read_File` **×3**（第一份 / gamemode / map） |
| `Read_File` `0x668BF0` | 真范围 **`0x668BF0–0x668FA3`**（有分离冷块，非首 `ret` 的 `0x668F8D`） |
| loader 调用 | **29 次 / 26 个不同 loader**（`Read_Difficulty` ×3、`Read_AdvancedCommandBar` ×2） |
| 难度键 | `Easy` `0x818134` / `Normal` `0x81BB60` / **`Difficult` `0x83A0C4`**（不是 `Hard`） |

**三条对编译器可用的结论**：

1. **同一套节被解析三遍**（`Read_File`×3）⇒ 后一遍覆盖前一遍；
   想覆盖某值就放到后面的 gamemode / map INI 里。
2. **`[AdvancedCommandBar]` 是单机读的节，`[MultiplayerAdvancedCommandBar]` 是联机读的。**
   `Read_AdvancedCommandBar` 按布尔参数选节（`1`→MP，`0`→`Advanced`），
   参数由 `[0xA8B238]`(`GameMode`) 决定：`0/5`（战役/遭遇战）→ 参数 `0`
   → **`AdvancedCommandBar`**；`3/4`（LAN/Internet）→ 参数 `1` → MP 节。
   ⇒ 改单机命令栏请改 `[AdvancedCommandBar]`。
3. **第三个难度键是 `Difficult`**；写 `Hard=` 无效（无读取点）。

复跑：`python re_atlas/tools/verify_r021_claims.py`（34/34 PASS, EXIT=0）；
证据 `evidence/r021_section13_verification.md`；正文 `kb/30` §13 + §13.7。

### C.15b `[MultiplayerDialogSettings]` 字段与镜像全局（R-023 核验口径，2026-10-22）

> **核验门禁 `tools/verify_r023_claims.py` 22/22 PASS，EXIT=0**（含 P3c / P13b）+ 异族盲验。
> 记录件 `evidence/r023_rulesclass_mirror_verification.md`；正文 `kb/30` §15.3。

| 项 | 值 |
|:--|:--|
| 读取器 | `0x00671EA0`，27 键 |
| 字段布局 | `+0x1480..+0x14AB` = 11×dword；`+0x14AC..+0x14BB` = 16×byte；**60 字节零空洞** |
| 载入函数真边界 | **`0x52CD70..0x52D430`**（真尾 `ret` @`0x52D42F`） |
| 镜像块 | `0x52D149..0x52D22C`，**恰 18 条** `mov [全局], reg` |
| 镜像 / 不镜像 | **18 / 9** |
| `ShortGame` / `FogOfWar` / `MCVRedeploys` | `0xA8B262` / `0xA8B31F` / `0xA8B320` |
| `ShadowGrow +0x14AD` | **零消费**：disp32 在 `.text` 出现 3 次（ctor 写 + reader 读/写） |

**★ 三条编译器必须知道（R-023 核验推翻/新增）**：

1. **载入函数边界比原记长 292 字节**。`0x52D277: jle 0x52d30c` 从函数内部跳过尾部冷块，
   冷块仍在读 `[0x8871E0]`。判据只能是**从入口做跳转闭包**，不是「找最后一条 `ret`」。
2. **这些全局不是冻结镜像，是运行期工作变量**。排除载入块与 ModemGst 块后，
   18 个全局**每一个**仍被别处写入（最少 2 处，合计 **208 处**）；
   写入者身份已确认 = 大厅/联机/地图选择 UI
   （`ModemHst.cpp` / `netdlg2.cpp` / `WDTSel.cpp` / `wonline.cpp` / `Skirmish.cpp`）。
   ⇒ **要稳定改，必须改源头（INI / 设置结构）**；只改全局会在下次 UI/会话刷新被写回。
   「读点在全局上」成立（字节 vs 指令对账 18/18），错的是「改一次就够」。
3. **存在第二个成批写入点**：`ModemGst.cpp` 的函数 `0x5B67F0`（块在 `0x5B69E4`，
   `Decoding game options\n`）写同一组全局中的 **17 个**（缺 `CaptureTheFlag`），
   源结构 `[ebx+0x7E]..[ebx+0xA3]`。属会话/网络房间设置包，与 `RulesClass` 无关。
   （起点曾误报 `0x5B6011`，异族盲验纠正；错因是「`ret` 后须有填充」的回退跨过了提前退出。）

**撞库警告**：`0x463Axx` 的 `[ebp+0x1488..]` 写入**不是** `RulesClass.MaxMoney`
（该区引 `0x887180`=`INI_Art`、不引 `0x8871E0`），是 artmd 侧 TypeClass 字段。
`0x652Axx` 集群同样不引用 `0x8871E0`。按 disp 数值统计字段读点必然误计 ——
这就是 §15.4 只能给**区间**的原因。



---
## D. 数据/字符串锚点（claims PART 2–4 摘要）

完整 323 条见 `docs/re/anchor_claims.txt`；本线已全量复算 **323/323 PASS**
（`evidence/claims_verify.txt`）。此处只列高频引用者：

| VA | 内容 | 说明 |
|:---|:---|:---|
| `0x00826444` | `"RA2MD.INI"` | 主配置文件名 |
| `0x00840D4C` | `"LANGUAGE.MIX"` | 语言 MIX |
| `0x00840D5C` | `"LANGMD.MIX"` | 尤复语言 MIX |
| `0x008189C8` | Base64 字母表 | `A`–`Z a`–`z 0`–`9 + /` |
| `0x008108AE` | `hint=0xFD` + `"StgCreateDocfile"` | 导入名表项，确证 `ole32!StgCreateDocfile` |
| `0x00825C08` / `0x00825C14` | `"PrivateKey"` / `"PublicKey"` | 联机加密 |

---

### C.16r L-4 四项残余全闭 + 推翻 R-046「恰两处」（R-054，2026-10-25）

> 门禁 `tools/r054_l4_residuals.py` **26/26 字节断言 PASS**（S1..S3 结构性不入分母）；
> 变异 `tools/mutate_r054_gate.py` **22/22 killed（精确集合；G-67 现值前置）**；
> 证据 `evidence/r054_l4_residuals.md/.txt` + `evidence/r054_mutate.txt`。

**结论一：marker `0x12` 是脚本动作 ID，不是类型标记。**

| 事实 | 字节 |
|:--|:--|
| fixup 比的字段 = 元素键 `+0xA4` | `0x691E60` `lea edx,[ebx+0xA8]`；`0x691E66` `cmp [edx-4],0x12`；步长 `+8` (`0x691EB2`) |
| 键写在 `+0xA4`、值在 `+0xA8`，同 `eax*8` | 写 `0x69192E` `89 8C C6 A4…` / `0x691939` `89 94 C6 A8…`；读 `0x691520` `8B B4 D1 A4…` |
| 动作派发 = ID−1 索引 | `0x6DD8D7` `mov edx,[esi+0x2c]; dec edx; cmp edx,0x90; jmp [edx*4+0x6DFDEC]` |
| 跳表 145 项 / 143 唯一 | 145/145 落 .text；别名下标 `[38,91,92]` |
| ID `0x12` → `0x6DE37B` | 其体 `call 0x6E11C0`；后者 `[0xA83D4C]`+`0x68BCC0` 按**名**查 TeamType |

⇒ `0x12` = "参数是 TeamType 引用"的那个动作；TeamType 删除导致注册表压缩时，只有这些条目
需要 `dec` 重编号。

**结论二：键模板 `%d` = 整数的十进制串，元素对是 (动作ID, 参数)。**

写侧 `0x6918D5` `push 0x817F6C`（机器读出 `25 64 00` = `"%d"`）→ `0x7C8EF4`
（格式类别立即数 `c745ec42000000` 的 `0x42` = `'B'`，printf 族）。
读侧 `0x723CA0` 用 `0x81C000`（`"%d,%d"`）经 `0x7CA530`（类别 `0x49` = `'I'`，sscanf 族）
拆两整数写回 `[esi]`/`[esi+4]`。写入界 `0x691925` `cmp eax,0x32`。

**结论三：`0x691A5B` 是第三个构造现场（★ 推翻 R-046）。**

```
0x691989  xor ebx, ebx          ; 区间内 ebx 唯一写点
0x691A32  push 0x234            ; ScriptTypeClass GetSize
0x691A37  call 0x7C8E17         ; 分配
0x691A50  call 0x410800         ; 共享基类 init（同 ctor 0x6916B8 / factory 0x691C7C）
0x691A55  89 9E 9C 00 00 00     ; [+0x9C] <- ebx (=0)
0x691A5B  89 9E A0 00 00 00     ; [+0xA0] <- ebx (=0)
0x691A61  c7 06 08 10 7F 00     ; 四连 vptr 安装（与另两处 20B 逐字节相等）
```

宿主 `0x691970` = `[ScriptTypes]` 节解析（三处 `push 0x83E728`）。`+0x9C` 写点精确集合
（**全部编码形态**）= `{0x6916BD(C7), 0x691A55(89), 0x691B0D(89, 非零), 0x691C81(C7)}`。
R-046 只匹配 `C7` 形态 ⇒ 漏判（**G-73**）。

**结论四：压缩后 `+0x98` 不修正，是构造时快照。**

dtor `0x691770` 只做向量 SIB 压缩（`0x6917CE` `8B 14 81` / `0x6917D1` `89 54 81 FC`），
`0x691770..0x6917E8` 内位移 `0x98` 访存**空集**。`+0x98` 写点恰三处（各构造现场算一次：
`0x69173F` `893481` push 自己 → 线性查位置 → `-1` 兜底 → `0x691763`/`0x691AEC`/`0x691D26`），
读者唯一 `slot16 0x691F90` `mov eax,[ecx+0x98]; ret`。

**更正清单（推翻类）**：`evidence/r046_ctor_vs_factory.md`（顶部横幅 + C6/§2）、
`kb/11` §8.1 第 471/474 行（就地改写）+ 新增 §8.2、`CONFLICTS.md` G-73、`class_contract.json`
的 `ScriptTypeClass.fields` 四键 + `entry_pair` + 4 条新锚（24→28）。

**方法论**：本轮最重要的一次自我推翻（R-046 的 C6）。教训 = **少命中比零命中更危险**：
口径窄时"集合恰好等于预期的两元素"从内部看完全自洽，反而强化错误结论。

### C.16s INI 四项悬项收口 + 推翻 kb/30 的 L-24 判据（R-055，2026-10-25）

> 门禁 `tools/r055_ini_residuals.py` **18/18 字节断言 PASS**（S1..S3 结构性不入分母）；
> 变异 `tools/mutate_r055_gate.py` **14/14 killed（精确集合；G-67 现值前置）**；
> 证据 `evidence/r055_ini_residuals.md/.txt` + `evidence/r055_mutate.txt`。

**结论一：L-26 闭 —— 四个查找入口、三个职责 + 一个等价副本（初版错一次，盲验更正；R-056 再降一档）。**

| 函数 | 返回 | 关键字节 |
|:--|:--|:--|
| `0x52B4F0` | **条目指针** / NULL | `0x52B53B` `8b34c7` → `0x52B561` `5f5b8bc25e`（`mov eax,edx`） |
| `0x52B390` | **布尔** | 命中 `0x52B3B3` `b001`；未命中 `0x52B411` `32c0` |
| `0x52B430` | **条目+4（值指针）/ 哨兵 `0xB7882C`** | 命中 `0x52B4B8` `8b4310` + `0x52B4BE` `83c004`；未命中 `0x52B4A8` `b82c88b700` |
| `0x52B4D0` | **布尔**（轻量，只查缓存槽） | `0x52B4E1` `b001` / `0x52B4E6` `32c0` |

`0x528A10` 体内 E8 目标 = `{0x4A1DE0, 0x52B390, 0x52B4F0, 0x52B620}`：`0x52B4F0` ×2
（`0x528AA7`/`0x528AD8`，条目向量 `+0x2C`）、`0x52B390` ×1（`0x528B4F`，键向量 `+0x28`）、
**`0x52B430` 零次**。**前 7 条指令完全相同只说明共用查找骨架**（同一比较函数 `0x52B720`、同一哈希 worker
`0x7C8B48`），**不能据此推断语义相同** —— 第 8 条起两者分叉，且命中后的去向不同
（`0x52B390` 就地 `mov al,1;ret`，`0x52B430` 落到 `mov eax,[ebx+0x10]; add eax,4`）。
▶ **初版正是在这里出错**：把"前 7 条相同"读成"语义等价"，并且把 `0x52B4D0`
（独立函数，`0x52B4C2..0x52B4D0` 是 12 字节 nop 填充）的首个 `ret` 当成了 `0x52B430` 的尾。
两路 GLM 盲验各自独立纠正，字节复核证实盲验正确。

**结论二：L-24 证伪 —— `+0x3C` 是"最近命中缓存"，被读。**

```
0x52A51A  8b463c   mov eax,[esi+0x3C]      ; 缓存槽
0x52A51F  7404     je  0x52A525            ; 空 -> 慢路径
0x52A521  3938     cmp [eax],edi           ; 缓存键 == 待查哈希?
0x52A523  743f     je  0x52A564            ; 命中
0x52A53E  895e3c   mov [esi+0x3C],ebx      ; 未命中: 清缓存 (ebx=0)
0x52A541  c6463801 mov byte [esi+0x38],1   ; 脏标志
0x52A561  89463c   mov [esi+0x3C],eax      ; 回填
0x52A5E4  8b763c   mov esi,[esi+0x3C]      ; 取用 (+ add esi,4)
```

清零点精确集合 `{0x52A53E, 0x52A590, 0x52ABCD, 0x52AC14}` + 构造期 `{0x52CC30, 0x52CD19}`。
同一角色在三个 lookup 里由 **`+0x10`** 承担（`0x52B39D` 读 / `0x52B3D3` 清）。
**原判据错因：kb/30 只用 disp32（`8b 86 3c 00 00 00`）找，本族全用 disp8（`8b 46 3c`）**
—— 该窗口 disp32 命中 **0**、disp8 命中 **11**。

**结论三：I-3 闭（部分）—— `0x89F518` 是在用实例。**

`c7 05 <g> f4 1a 7e 00`（vptr `0x7E1AF4`）精确六处：
`{0x887058, 0x8870C0, 0x887128, 0x887180, 0x887208, 0x89F518}`。
引用权重 `0x89F518` = **28**（**19** 处在 `0x5C1500..0x5C4600`）、`0x887058` = **3**
（init `0x40E241` + thunk `0x40E261`）。**仍未定**：各自对应哪个 `.ini`。

**结论四：L-25 仍未闭** —— `CCINIClass` 独立尺寸无 `new(0x58)` 实证，不虚报。

**方法论（新坑 G-74）**：G-73 立的"少命中"仅隔一轮就复发，并新增**纵向**形态——
我首版只解 `0x528A10` 前 0xA0 字节就写「kb 的 L-26 前提是错的」，补读到 `ret` 边界后
发现 `0x528B4F` 确实调用 `0x52B390`。**横向窄 → 假吻合；纵向短 → 假推翻**，
后者更危险，因为它会去改一份本来正确的文档。

### C.16t INI 查找族三条边界收口：孪生重复 / 共享二分核 / 双 +0x3C 宿主（R-056，2026-10-25）

> 门禁 `tools/r056_ini_lookup_family.py` **19/19 字节断言 PASS**（S1..S3 结构性不入分母，红仍非零退出）；
> 变异 `tools/mutate_r056_gate.py` **16/16 精确集合击杀**（G-67 现值前置）；
> **⚠ 本结论初版含三处实证错误，由异族盲验抓出并全部改正**（G-77）：长度 `0x77`→`0x79`、
> `0x52B620` 不是死重（20 调用者）、`+0x2C` 属 `[ebp+8]` 不属 `this`。
> 证据 `evidence/r056_ini_lookup_family.md`。

**结论一：`0x52B620` 是 `0x52B4F0` 的逐字节孪生，不是第四个角色。**

两函数各 **`0x79`（121）字节**、各有三个 `ret 4` 出口、各自以 **7 字节 `nop`** 围栏收尾。
逐字节比较**恰好 4 个字节不同**，且**全在操作数位**：

| 差异 | `0x52B4F0` | `0x52B620` |
|:--|:--|:--|
| 比较器立即数 | `0x52B505 68a0b65200` → `0x52B6A0` | `0x52B635 6820b75200` → `0x52B720` |
| `call 0x7C8B48` 的 rel32 | 起点不同故位移不同 | 同一目标 |

两个比较器体 **34 字节逐字节相同** ⇒ 两份代码语义等价。
⇒ R-055 的「四种用途」应读作 **三种职责 + 一份等价副本**。

**★ 但它是活代码**：`0x52B4F0` 有 **22** 个调用者、`0x52B620` 有 **20** 个
（`.text` 全段对齐线性反汇编 68,249 条 `call`）。初版写「死重」是**分母错位**——
问「这个函数体用了谁」，答成「谁用了这个函数」。

**★ 真容器布局**：`this+0`=数组基址、`this+4`=元素数、`this+0xC`=已排序标志、
`this+0x10`=上次命中缓存；未排序先 `qsort(this+0, this+4, 8, cmp)`（`0x7C8B48`）。
⇒ 这一族是**「按 int key 的排序数组二分查找」容器方法**，不是通用 INI 键查找。
`0x528A10` 里 `esi` 在 `0x528A86` 被 `add esi,0x2c` 改写过，故那里 `esi+0x2C`
是 `[ebp+8]+0x2C`（另一对象），**不是** `this+0x2C`。

**结论二：`0x52B6D0` 是共享二分核，但孪生不调它。**

```
0x52B6D0  5356 85d2 57 8bf2 7e2b 8b442410 8b18
          push ebx/esi; test edx,edx; push edi; mov esi,edx; jle miss
          mov eax,[esp+0x10]; mov ebx,[eax]      ; key 指针解引用一次
```

`ecx` = 有序基址、`edx` = 元素数、`[esp+0x10]` = key 指针。
命中 `0x52B70C 5f5e8bc25bc20400`（`mov eax,edx`）；未命中 `0x52B704 5f5e33c05bc20400`。
**全引擎恰 2 个 E8 调用者**：`{0x526BB2, 0x52A554}` —— **两个孪生都不在其中**，
它们各自**内联**了同一段 12 字节循环核心（`0x52B534` / `0x52B664` 逐字节相同，步长 8 B）。

**结论三：两处额外 `+0x3C` 清零 = 同一 teardown 块跑两遍，宿主头是 `0x52AB80`。**

```
0x52ABC4  895e30895e34885e38895e3c    ; +0x30/+0x34/+0x38/+0x3C 全清零
0x52AC0B  895e30895e34885e38895e3c    ; 同一 10 字节块，相距 0x47
```

宿主 `0x52AB80 53568bf18b460c` 是 dtor 形状：`0x52AB87 c7063cb77e00` 重打 vptr `0x7EB73C`、
`0x52ABB2 6a01ff12` 遍历 `+0x18` 链虚删除（arg=1）、`0x52AC1A c74610041b7e00` 再打第二张
facet 表 `0x7E1B04`。两块之间是 `+0x40` 链的释放。
⇒ **4 个字节级写点，语义上 3 个独立失效位置。**

▶ **自我纠错**：宿主头初写 `0x52AAC0`，门禁 C5 当场打红 —— `0x52AAC0` 是另一个函数
（`test ecx,ecx` … `cmp byte [ecx],0x5b` / `push 0x5d`，即 `'['`/`']'` 匹配器）。

### C.16u 查找容器归属：四字段结构坐实（R-057，2026-10-25；归属项已由 C.16v 闭合）

> 门禁 `tools/r057_container_ownership.py` **22/22 字节断言 PASS**（S1..S3 结构性不入分母）；
> 变异 `tools/mutate_r057_gate.py` **27/27 精确集合击杀**；
> 证据 `evidence/r057_container_ownership.md`。

**结论一：容器是固定四字段结构，出现在四个宿主偏移上。**

| 宿主 | 容器基址 | 相对字段 |
|:--|:--|:--|
| `0x52B4F0` / `0x52B620` | `this+0` | `+0` 基址 / `+4` 元素数 / `+0xC` 标志 / `+0x10` 缓存 |
| `0x52A4D0` | `this+0x2C` | `+0x2C` / `+0x30` / `+0x38` / `+0x3C` |
| `0x528A10` 路径 A | `[arg+8]+0x2C` | `+0x2C` / `+0x30` / `+0x38` / `+0x3C` |
| `0x528A10` 路径 B | `this+0x28` | `+0x28` / `+0x2C` / `+0x34` / `+0x38` |

**结论二：`0x528A10` 的两个容器分属两个不同对象。**
`ebp` 全函数只写一次（`0x528A1E mov ebp,ecx`）⇒ `[ebp+disp]` 就是 `this+disp`。
路径 A 的 `esi` 来自 `0x528A55 mov esi,[ebp+8]`，再被 `0x528A86 add esi,0x2C` 重基址
——**注意 `0x528A83 [esi+0x30]` 在 add 之前**，所以那是 `[arg+8]+0x30`（容器 +4 元素数）。

**结论三：★ 嵌入偏移 `+0x2C` 由活调用者硬证（初版误判为"冲突"，已推翻）。**

```
0x52772C  8b 4e 30      mov ecx,[esi+0x30]   ; 元素数在宿主 +0x30
0x52772F  83 c6 2c      add esi,0x2C         ; 容器基址 = 宿主 +0x2C
0x52773E  8b 4e 10      mov ecx,[esi+0x10]   ; 缓存 = 宿主 +0x3C
0x52774D  8b ce         mov ecx,esi
0x527750  e8 9b 3d 00 00  call 0x52B4F0
```

容器四字段折到宿主后恰好落在 `{0x2C, 0x30, 0x38, 0x3C}` —— 与 `0x52A4D0` **全中**，**零冲突**。

**★ 本轮自我推翻一次**：初版把 `0x528A10` 的 `this+0x28` 与 `0x52A4D0` 的 `this+0x2C`
按绝对偏移叠加，得出"`+0x2C` 既当元素数又当基址 ⇒ 两视图互斥"。
**但那个叠加有一个从未验证的前提：两个 `this` 是同一类。** 千问盲验给出上述活调用者，
直接推翻。错在我把两个不同对象的字段图强行对齐。

**留下的真结论**：同一容器类型在**不同宿主上用不同偏移**（`+0x28` vs `+0x2C`）是正常的，
**不能用"偏移不同"推断"结构不同"或"归属错误"**。归属仍待证：`0x52A4D0`
**三通道全零可达**（E8=0 / E9=0 / dword=0；阳性对照 `0x52B4F0`=22），其 `this` 类型静态不可定；
构造器也帮不上（清零集是并集、清零对称）。

**方法论（新坑 G-78）**：每侧单独看都完全正确，**两侧都对、叠起来错**——
因为中间那座桥（"这两个 `this` 是同一类"）**从未被验证**。
逐条断言的门禁**永远不会因为桥不存在而变红**。

### C.16v 容器归属定谳：RTTI 链钉名 `CCINIClass`（R-058，2026-10-25）

> ⚠ **本条把 C.16u 留的"归属待证"闭合为定谳**（非推翻：R-057 的降级结论方向正确，
> R-058 补上从未验证的那座桥——RTTI 类名）。受影响条目：C.16u 结论段、
> HANDOFF H-044（已加指针 + 新增 H-045）、class_contract `R057_WARNING`
> （已替换为 `r058_ADJUDICATED` + `CCINIClass`/`INISection` 条目）、kb/30（新增 §6.4）。

> 门禁 `tools/r058_container_class_rtti.py` **28/28 字节断言 PASS**；变异
> `tools/mutate_r058_gate.py` **27/27 精确集合击杀 + G-79 覆盖对账内置**；
> 证据 `evidence/r058_container_class_rtti.md` / `.txt`。

**结论**：RTTI 链 `vtable[-1]→COL→TD`（x86 名**内联**在 TD+8）给出
`0x7E1AF4 → '.?AVCCINIClass@@'`、基条目 → `'.?AVINIClass@@'`（mdisp=0）——
**`+0x2C` 容器嵌在 `CCINIClass` 对象内**。构造现场（`"BATTLEMD*.INI"` 工厂
`push 0x58; call new` @`0x52CBFB` → `0x52CC21` 清零块**显式**清容器四槽 →
`0x52CC36` 盖主 vptr）证明它是被初始化的成员，不是字段表巧合。
六个 TD 共享 vfptr `0x7F9594` ⇒ 编译器生成表，非手摆假 vtable。

**连带**：① R-056 匿名 dtor 宿主定名 **`INISection`**（`.?AUINISection@INIClass@@`，
嵌套 struct）；② **L-25 闭合**：堆 new(0x58)（BATTLEMD/RULEMD* 工厂）+
**6 个 `.data` 全局由全局构造器盖 vptr 从不 new**（`0x887180/0x887208/0x887128/
0x887058/0x8870C0` @`0x40DFE0` 簇 + `0x89F518` @`0x49B405`）+ atexit 式析构注册
（`call 0x40E340` + thunk `mov ecx,<全局>; jmp→dtor`）；③ **孪生调用协议不对称**：
twin A 13/22 近端 `add esi,0x2c`（含两活见证）vs twin B 0/20——「可互换」印象作废；
④ 异族盲验两路结论经字节复核**反采纳**（GLM 第二活见证 E2、qwen 构造器可判别性 B5）。

**仍开**：见证函数↔实例一一对应未证；`0x52A4D0` 静态隐身无解释；
`0x528A10` 宿主类未定；`0x89F518` 的 .ini 归属不断言。

**新坑 G-79**：变异套件击杀分母是**用例数**不是**断言数**——24/24 全绿里
A7/A8/D1 实际零杀手，靠「断言→killer 双向清单」才暴露；已把 uncovered 非空⇒红
做成脚本内置门禁（**R-059 已推广到 R-056/R-057 存量套件**，见 C.16w）。

### C.16w G-79 对账落地 + 恒真断言改写 + 见证↔实例普查（R-059，2026-10-25）

> 门禁复跑 R-056 19/19 / R-057 22/22；变异 R-056 **20/20 + 覆盖 19/19**、
> R-057 **32/32 + 覆盖 21/21**（两套件尾部各加机器化 G-79 尾检）；
> 证据 `evidence/r059_g79_reconciliation.md`。

**① 存量套件对账（预判成真）**：AST 双向清单抓出 R-056 零杀手 **B3/B4/C6**、
R-057 零杀手 **C3/C5/D2**——两套件当时都报全绿。全部补齐（红集按实测写死）。
**② 新坑 G-80（恒真式极端形态：断言根本不读镜像字节）**：C6 = 常量地址算术、
D2 = 字面量折叠——对变异天然免疫；已重写为「从字节读值再折叠」。全仓普查
23 条初筛逐条溯源：除已修两处外全数洗白（绑定自 read()/辅助函数的间接读）。
**③ 见证↔实例（否定式）**：13 近端站点 `esi` 首写者零个直取六全局
（4× ecx 跨过程 / 7× `[esi+0x10]` 容器链自遍历 / 2× 栈参）⇒ 需调用图上行。
**④ `0x7E1AF4` 形状定谳**：1 槽 scalar-deleting-dtor 表（与 kb/30 §7 R-020 登记一致，
非推翻）；R-058「主 vptr」措辞修正为「析构专用表」——CCINIClass 全非虚直调
与查找族零虚表槽互证；真析构 `0x5256F0` 释放 +0x28 并清容器区 = 又一条属主证据。

### C.16x D-06 C 案执行轮：对齐读法转正 + UPPER 勘误 13,682→13,683（R-060，2026-10-26）

> ⚠ **本条推翻两项在册口径**（章程 §8 横幅）：① 对齐 UPPER **13,682 作废，改 13,683**
> （当年把 V-001 原报 13,683 判为笔误是**判反了**——13,682 混用了字节扫描头部；
> 头部必须对同一 CFG 收集，`0x40A090` 在对齐覆盖下补回 ⇒ 891）；② `fn_walk` 旧
> 「15,224 入口 / 3.62%」产数路径作废，生产件根集改**对齐 E8 ∪ 虚表 ∪ PE**（E9 不再
> 当入口）。受影响条目：STATUS 口径头/量化面板/横幅注、INDEX C.15e 行、HANDOFF H-022
> 契约表、r035/r049 证据件（追加不删改）、LEDGER 历史两处 ★★ 块。覆盖率 4.28%…4.07%
> **不变**，12,792/6,719/563/560/547/557 全部复现吻合。

> 门禁 `tools/verify_r035_claims.py` **23/23 PASS**（新增 R1..R6 计数断言）；变异
> `tools/mutate_r060_gate.py` **14/14 精确集合击杀 + G-79 覆盖 23/23**；
> `fn_walk`/`fn_census` 修后实测 12,792 / 6,719；证据 `evidence/r060_verify.txt`、
> `evidence/r060_mutate.txt`；LEDGER R-060 节。

**① 区分性对（D-06 判据①的可杀形态）**：C11 位移**干净**幻影（窗全在一条 `mov` 体内，
机器筛 89 个）⇒ 只红字节扫描侧、P2c 绿；C12 提升幻影为对齐边界 ⇒ 只红对齐侧、
P2/P3 绿。⇒ 两读法互相藏不了对方缺陷。新坑 **G-81**：区分性变异的被改窗必须先证
「全在对方读法同一条指令体内」——首轮用旧幻影 `0x4011DB` 时 rel32 跨宿主尾界，
把对齐流带失步误红 P2c（旧 R-038 M11 同坑被子集计分藏了三轮）。
**② 同类扩散（铁律 5 当轮执行）**：`fn_census.py` 单次线性 `disasm_lite` 静默丢
83% call 目标（1,118 vs 6,719）——已修+重生成；其余线性 disasm 全仓搜过均为窗式或带
resync。
**③ 自我误判入册（G-82）**：指控旧 M4「死案例」被 regex 复算否证（methods 21→22
照红 P8；错的是 M4 的注释描述不是 M4）。判测试死活只能跑复算，标签不算证据。
**④ 敏感度转正**：P5b REGISTER → **R4 计数断言**（891/451/352 ≈2.5×），
UPPER 不可单值冻结现在由门禁钉住。

### C.16y 见证 `this` 调用图上行：R-059 §2③ 推翻 + 辅批次 1 收官（R-061，2026-10-26）

> ⚠ **本条推翻 R-059 §2③ 三分归类**（4×`mov esi,ecx`/7×容器自遍历/2×栈参）：那是
> 线性窗口越过函数头读上一函数序言的污染（**G-83**）。分支图闭包重做后 13 近端站点
> **13/13 全部 `mov esi,[reg+8]` 缓存加载**——见证方=包装对象，容器在 `[[this+8]+0x2C]`。

**① 归属表（机器钉值）**：5 宿主 global-direct：`0x5276D0`（Art 119/RA2MD 45，callers
757）、`0x528A10`（80/10，650）、`0x5295F0`（95/23，651）、`0x5283D0`（RA2MD-only 3，
306）、`0x528F00`（RA2MD-only 2，5）；7 小扇出宿主零 global-direct（kind 直方图钉，
this=转参→**UNKNOWN 保留未知**）；每宿主尾段一处 `0xB7882C/0xB78830` 兜底注册表；
堆工厂 `0x52CB90`（new(0x58)×2、盖 `0x7E1AF4`、4 callers 钉）工厂件→见证连线**未证**；
`0x529394` 冷多入口零 E8 入边。R-059 四址病根 `0x5275CC/527B97/528DF2/52A623`=前驱函数
内 `8bf1`（其自报 `8bce` 也是笔误，本件机器纠正）。
**② 门禁与变异**：`tools/r061_witness_this_contract.py` **194/194 PASS**（A27/B51/C17/
D39/E24/F10/G26 全 exact-pin）；round-5 校准 194 例全杀（survived/exc/mismatch/uncovered
=0），清单 `out/_r061_freeze5.json` 机械转录 `tools/mutate_r061_gate.py`（手抄字面量、
STALE 三哈希守卫、splice/full 双路精确比对）——**状态=冻结候选**（异族通道派发失败
降级同族新上下文核验，升格前不作定谳）。新坑 **G-84**（BLOB 快照先于注入⇒raw 断言全盲）、
**G-85**（`>=N` 阈值掩蔽单字节翻转）。
**③ 辅批次 1（G-79→R-053/054/055）**：R-053 **17/17+覆盖 10/10**（补 M17）；R-054
**27/27+覆盖 26/26**（M23–M27 逐址 + D3 负命题→disp32 集合正锚定）；R-055 **20/20+
覆盖 20/20**（根因=bake-before-hoist 缺失，G-84 实锤）。输出
`evidence/r05{3,4,5}_*_r061.txt`。
**④ 辅批次 2/3（G-79 推广收官 R-047..R-055 全口径）**：R-050 **12/12+7/7**、R-047
**12/12+5/5**、R-048 **13/13+10/10**（基线全杀加尾段）；R-051 X7/X8 零 killer→M13/
M14 ⇒ **14/14+8/8**；R-052 Y2/Y4 + **G-84 变体（attestation 在注入后算⇒rc 恒 2）**
修 PRISTINE ⇒ **15/15+10/10**；R-049 **N/A**（无断言套件）。域外 5 件同 pattern 登记
移交零改动（LEDGER §6.6）。输出 `evidence/r0{47,48,50,51,52}_{gate,mutate}_r061.txt`、
`evidence/r061_aux_batch23.md`。XVERIFY 勘误交接件待回执。LEDGER R-061 节。

### C.16y2 见证 `this` 上行一跳收口：88 caller 分类表 + GenericList 栈件（R-062，2026-10-27）

> 落实 R-061 §6.5「上行再一跳仍可查」——本件把 7 SMALL 宿主全部 aligned caller（88 行）
> 分类钉死。**实例归属不升格**：param-slot/unknown-* 只是「this 从更上层线传入」，
> 「是哪个对象」仍是 UNKNOWN。

**① 分类表（门禁 `tools/r062_upward_trace_contract.py` 126/126 PASS，U-chain 88 行
逐 verdict+链字节字面量）**：param-slot 54（入向 cdecl 参数槽——帧内对目标 slot 零写入，
`mov reg,[esp+X]`/`mov ecx,[esp+X]`）、stack-object 17（`lea ecx,[esp+X]` 紧邻 call，
0x528C00 独占）、local-slot 1（`0x770774`）、param1-forward 3（`0x52A760` 三 caller 的
`mov edi,[ebp+8]`＝转发自身第一参数；F=0x689E90 唯一 caller 0x687853、G 帧 edi 又源自
入向参数——链两跳全钉）、unknown-reg 12、unknown-thunk 1。
**② 负命题双对照**：caller-self=0/88（同一 classify_call 在五个直传宿主命中 caller-self
4+31+5+11+0=**51** 行——检测器能看见这形态，0 是真结果不是盲区）；global-load=0 跨
SMALL（直传宿主 U-ctl 复现 **164/90/118/3/2** 与 R-061 E-hist 逐值全等）。
**③ ★ 机制发现**：0x528C00 的 17/67 this 是 caller **栈上 GenericList 临时件**——5 行
帧内构造证据（`mov [esp+X],0x7E1B04` 三窗 8B 钉 `c7442438041b7e00`；RTTI 链
vtable→COL→TD 定名 `.?AVGenericList@@`，控制位 CCINIClass TD vfp `0x7F9594` 同 walk）；
12 行裸传（slot 帧内零 dword 写——构造在 callee 内或帧外，静态不可判，登记未证）。
⇒ 见证协议存在第三种 this 来源（栈件），与六全局/堆工厂并存；R-061 工厂连线未证账不变。
**④ 变异**：round-1 109/112（三处我错：hex 串长 G-86、`.rdata` 注入分流 G-87、
U-set 重言式→冻结字面量 HOST_ROWS）；round-2 **112/112 killed、126 标签全覆盖、
uncovered=0**。清单 `out/_r062_freeze.json`（`1e4e0ba0…`）机械转录
`tools/mutate_r062_gate.py`（`1e8d600d…`，STALE 三守卫+双路精确红集）；
双路全量复跑已收口 **112/112 exact、EXIT=0**（`out/_r062_freeze_run1.txt`）+异族复核未做
⇒ **冻结候选**。
证据 `evidence/r062_upward_trace.md`；LEDGER R-062 节。

### C.16y3 R-061/R-062 升格收口（2026-10-29，异族对账级复核 PASS）

> 异族复核书 `evidence/r061_r062_oof_review_20261029.md`（deepseek-v4.1-flash，用户指定通道；qfmodel
> 本日故障停跑在案）：门禁 194/194+126/126、变异套件全量 194/194+112/112 exact 亲测；同族深度复核
> 书 §10 四落点全 CONFIRMED；红项 4（R-062 书 §2 标题「三分之一」→约 1/4，勘误注已随办理落书）。
> ⇒ R-061/R-062 **状态=已核验（定谳·静态范围）**（对账级非全量重导，随状态登记）。仍开账不变：
> 实例归属 UNKNOWN/12 裸传构造点/51 行 caller-self 再上行/BSS 现值/工厂→见证连线/运行期。LEDGER
> 「升格收口」节 + HANDOFF 升格通报在案。

## 查询方式

```bash
# 按 VA 查语料里所有叫法（含来源文件与出现次数）
python -c "import json;m=json.load(open('re_atlas/evidence/symbol_map.json',encoding='utf-8'))['map'];print(json.dumps(m.get('0x00656EC0'),ensure_ascii=False,indent=1))"

# 取任意 VA 的前 N 条指令 + 原始字节
python re_atlas/tools/disas.py 00656EC0

# 复算 323 条 claims
python re_atlas/tools/verify_claims.py

# 复核某个类的尺寸（含"该槽是否 GetSize"门禁）
python re_atlas/tools/xcheck_sizes.py
```
