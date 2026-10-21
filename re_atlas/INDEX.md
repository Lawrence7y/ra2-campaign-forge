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
| `0x008871E0` | `RulesClass*` | rulesmd.ini 全局规则单例（YRpp `RulesClass.h:85`） | ATLAS §11.1；YRpp | 社区 |
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
### C.11 全引擎 键 → 读取点 索引（R2-2 第五轮，详见 `kb/30_ini_subsystem.md` §12）

**478 个 INI 读取调用点，473 个键字面量恢复，427 个不同键。**

| 读取器 | 调用点 |
|:---|---:|
| `0x005295F0` `ReadBool` | 207 |
| `0x005276D0` `ReadInteger` | 141 |
| `0x00528A10` `ReadString` | 112 |
| `0x005283D0` `ReadDouble` | 16 |
| `0x00526810` `GetSection` | 1 |
| `0x00529160` `ReadStringtableEntry` | 1 |
| `0x00528F00` `ReadUnicodeString` | **0**（引擎自己不用） |

**被多处读取的键（10）**：`Description` / `DoubleThick` / `Elasticity` / `Flat` /
`Image` / `PowerUp%01dYSort` / `Shadow` / `SpawnDelay` / `ToTile` / `Trailer`

**★ 格式化键**：`"PowerUp%01dYSort"`（`0x008194D4`，6 个读取点，全在 ~`0x0045FE50`）
⇒ 运行期 `sprintf` 成 `PowerUp0YSort`…`PowerUp9YSort`，INI 里要展开写 10 个实键。

复跑：`python re_atlas/tools/dump_ini_keyindex.py`（`evidence/ini_keyindex.txt`，
1419 行；正对照 = `Name`/`UIName` 各恰好落在 `0x00410A60`）。

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
