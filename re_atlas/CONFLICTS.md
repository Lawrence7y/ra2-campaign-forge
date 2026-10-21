# RE-ATLAS · 语料冲突清单 (CONFLICTS)

> 只登记"同一对象、不同说法"的冲突，并给出**本线按字节的裁定**。
> 不修改 `docs/re/` 下任何文件；对外的勘误建议只体现在本文件与本线交接件里。
>
> 生成器：`tools/extract_symbols.py`（地址→名字）、`tools/classify_conflicts.py`（冲突分级）。
> 原始数据：`out/symbol_map.json`、`out/conflicts.json`、`out/conflicts.txt`。

## 统计总览（2026-10-21 首轮）

| 类别 | 数量 | 含义 |
|:---|---:|:---|
| 语料命名点（.text 内） | 1,304 | 全部经段表校验，排除 RVA 列与十六进制噪声 |
| 单一名字的 VA | 923 | 无冲突 |
| 多名冲突 | 381 | 见下 |
| └ NOISE | 14 | 其余名字是结构描述（`return 0`、`v[52]`、`BSS`） |
| └ ALIAS | 400 | 同一实体的不同粒度叫法（`X::Y` vs `XClass::Y_Cell`） |
| └ **REAL** | **5** | 实质分歧，逐条裁定于下 |

---

## 一、实质冲突裁定（5 条）

### R-1 · `0x004134A0` — `SpatialGrid::AddObject` ✅ 已裁定

- 语料 A：`SpatialGrid::AddObject`（`targeting_deep_dive.md`、ATLAS §4）
- 语料 B：`DynamicVectorClass::AddItem`（被错误绑定的行）
- **字节证据**：入口 `51 53 8B 5C 24 0C 55 8B E9 8B 03 8D 4C 24 08 56`
  → `push ecx; push ebx; mov ebx,[esp+0xC]; push ebp; mov ebp,ecx; mov eax,[ebx]`，
  随后 `0x004134B3: FF 90 B8 01 00 00` = `call [eax+0x1B8]` —— 这是一个**虚调用取坐标**，
  典型的 `AddObject` 形态，不是向量追加。
- **裁定**：`SpatialGrid::AddObject` 正确。`DynamicVectorClass::AddItem` 的真实地址是
  **`0x006C6400`**（ATLAS §10 及 `crt_memory_pool_deep_dive.md` 均如此记），
  冲突来自表格相邻单元格的错误绑定。
- 附带实证：动态向量扩容缺陷在 `0x006C6400`，与本地址无关。

### R-2 · `0x0050B6F0` — `HouseClass::IsPlayerControl` ✅ 已裁定

- 语料并存三名：`House::RadarVisible`、`HouseClass::RadarVisible`、`HouseClass::IsPlayerControl`
- **字节证据**（全函数，24 字节）：
  ```
  0x0050B6F0  A1 38 B2 A8 00     mov eax,[0x00A8B238]      ; 游戏模式
  0x0050B6F5  85 C0              test eax,eax
  0x0050B6F7  75 1D              jne 0x0050B716            ; 联机分支
  0x0050B6F9  8A 81 EC 01 00 00  mov al,[ecx+0x1EC]
  0x0050B6FF  84 C0              test al,al
  0x0050B701  75 0D              jne 0x0050B710
  0x0050B703  8A 81 ED 01 00 00  mov al,[ecx+0x1ED]
  0x0050B709  84 C0              test al,al
  0x0050B70B  75 03              jne 0x0050B710
  0x0050B70D  33 C0              xor eax,eax
  0x0050B70F  C3                 ret
  0x0050B710  B8 01 00 00 00     mov eax,1
  0x0050B715  C3                 ret
  0x0050B716  8B 15 4C 3D A8 00  mov edx,[0x00A83D4C]      ; HouseClass::Player
  0x0050B71C  33 C0              xor eax,eax
  0x0050B71E  3B CA              cmp ecx,edx
  0x0050B720  0F 94 C0           sete al
  0x0050B723  C3                 ret
  ```
- **裁定**：函数语义是"**该 House 是否由本地玩家控制**"——
  联机分支严格 `cmp ecx,[Player]`；单人分支读两个布尔位。
  采纳 **`HouseClass::IsPlayerControl`** 为正式名。
  另两名是把"雷达可见性判定"的**调用语境**误当作函数名（该函数确实被雷达与框选当闸用）。
  分类：ALIAS 性质的名字过窄，功能上不冲突。

### R-3 · `0x00656EC0` — `RadarClass::Refresh` ✅ 已裁定

- 语料 A：`RadarClass::Refresh`（`radar_fix_report.md`、`radar_crash_static_analysis.md`）
- 语料 B：`RadarClass::DrawMap`（`re_sprint_S10_report.md`、`radar_minimap_dots.md`）
- **字节证据**：入口 `83 EC 48 53 55 56 8B F1 57 8D 9E 0C 12 00 00`
  → 栈帧 0x48；`lea ebx,[esi+0x120C]`（视口/缓存矩形基址）。
  函数内含调用点 `0x006574C3: E8 88 E7 FF FF` = `call 0x00655C50`，
  即 `RadarClass::DrawCell`。
- **裁定**：**`RadarClass::Refresh`**。理由：它是 `vtable[16]` 的**每帧刷新入口**
  （ATLAS §21 给出完整虚派发链 `Mouse→Sidebar 0x6A6C30→Power 0x63FB20→Radar 0x653100`），
  "画全图"只是它的一步。`DrawMap` 描述的是行为而非角色，与 R-Next 类命名习惯不符。
- 影响面：`docs/re/v160_acceptance.md` 已用 `Refresh` 口径，保持一致。

### R-4 · `0x006DA380` — `TacticalClass::GetObjectAt` ✅ 已裁定

- 语料 A：`TacticalClass::GetObjectAt`（ATLAS §21）
- 语料 B：`TacticalClass::ObjectUnderCursor`（`re_sprint_S10_report.md`、`radar_minimap_dots.md`）
- **字节证据**：入口 `83 EC 28 55 56 8B 74 24 34 8B E9 57 33 C9`，
  `mov esi,[esp+0x34]`（出参指针），`mov ebp,ecx`（this），
  `mov eax,[ebp+0xB0]`…，随后线性扫 `0x00B0CEC8`。
  调用点唯一性：`0x00692515: E8 66 7E 04 00`，来自 `ProcessClickCoords`。
- **裁定**：**`TacticalClass::GetObjectAt`**。理由是它符合 `Get*` 一族"出参 + 返回"的签名
  （第二参数是 `ObjectClass**`），`ObjectUnderCursor` 是描述性同义。
- 分类：**ALIAS**（同一函数、不同命名风格）。

### R-5 · `0x0072A090` — `TunnelLocomotion::Can_Enter_Cell` ✅ 已裁定

- 语料 A：`TunnelLocomotion::Can_Enter_Cell`（`pathfinding_locomotion.md`）
- 语料 B：`Tunnel::Can_Enter`（`re_sprint_S7_report.md`）
- **字节证据**：入口 `51 A0 6B ED A8 00 84 C0 75 37 66 8B 4C 24 0E …`
  → `push ecx; mov al,[0xA8ED6B]; test al,al; jne …`；
  取参用 `mov cx,[esp+0xE]` / `mov ax,[esp+0xC]`（**两个 16 位坐标**），
  再 `mov ecx, 0x0087F7E8`（`MapClass` 实例）后 `call 0x005657A0`。
- **裁定**：**`TunnelLocomotion::Can_Enter_Cell`**。两个 16 位坐标参数 +
  以 `MapClass` 为 this 调 `CellClass` 查询，是 locomotion 的 `Can_Enter_Cell` 签名；
  **RTTI 里没有裸 `Tunnel` 类**（988 类中只存在 `TunnelLocomotionClass`，
  精确集合比对 `'Tunnel' in names` = **False**）。`Tunnel::Can_Enter` 写法把
  类名截短了。
- 分类：**ALIAS**。

---

## 二、实例尺寸缺陷（2 条，均为 ATLAS §11.2 错）

> 这两条不是"两文档互相矛盾"，而是 **ATLAS 单侧与字节矛盾**。
> 其中 G-2 语料内已有独立勘误 `E-AIT-1`（`trigger_tag_abi_deep_dive.md`），
> 本线独立复算得到同一结果 —— 属**双通道一致**。G-1 为首报。

### G-1 · `TeamTypeClass` 实例尺寸：288 → **248** ⚠ ATLAS 错（首报）

| 项 | ATLAS §11.2 记 | 本线字节复算 |
|:---|:---|:---|
| 虚表 | `0x007F47D0` | `0x007F47D0`（一致） |
| 虚函数数 | 27 | 27（一致） |
| 尺寸 | 288 / `0x120` | **248 / `0xF8`** |
| 取证 VA | `0x6F29C0` | `0x006F20B0` |
| 取证指令 | `mov eax, 0x120; ret` | `B8 F8 00 00 00 C3` = `mov eax,0xF8; ret` |

**推导链**（可复跑）：
1. `xcheck_sizes.py` 解析 ATLAS §11.2 行 → 得 `vtable=0x7F47D0`。
2. 读 `vtable[12]`（`0x7F47D0 + 12*4`）→ `0x006F20B0`。
3. `0x006F20B0` 字节 `B8 F8 00 00 00 C3` ⇒ `mov eax,0xF8; ret` ⇒ 尺寸 **248**。
4. 反向核 ATLAS 的取证 VA `0x6F29C0`：
   `1C 24 E8 19 84 DD FF DD 1D 68 EA B0 00 83 C4 08 C3`
   → 这是一段**浮点函数的尾部**（`sbb al,0x24; call …; fstp qword [0xB0EA68]; add esp,8; ret`），
   既不是函数头、也没有 `mov eax,0x120`。
5. `0x6F29C0` 也不在 `TeamTypeClass` 的 27 个虚表槽里（全槽集合比对为空）。

**结论**：ATLAS 该行的"尺寸"与"取证"双错。取证 VA 疑似与相邻函数
（`0x006F29A0` 一带的浮点例程）混淆。
**给 Lead 的建议**：出 ATLAS §11.2 勘误块，`TeamTypeClass` 尺寸改 `0x120`→`0xF8`，
取证改 `0x006F20B0: B8 F8 00 00 00 C3`。

**核验状态**：✅ **已核验（异族双通道，2026-10-21）**。
`dwfrun-7cee3752` 两族独立复算：
- GLM 5.3 → `CONFIRMED`（248 / 272），注"按段表 VA 换算，两 GetSize 均为 B8 imm32+C3，独立复算与参考一致"。
- DeepSeek v4.1-flash → `CONFIRMED`（248 / 272），注"两处 GetSize 均为 NOP 填充后的函数头"。

（首轮 `dwfrun-4cc83e74` / `dwfrun-c318607d` 均因限流失败零落盘，已按 §7 冷却后重派。
本轮改用纯文本四行协议取代 typed `ask`，因两模型都不会主动调 `submit_result`。）

### G-2 · `AITriggerTypeClass` 实例尺寸：256 → **272** ⚠ ATLAS 错（语料内已有 E-AIT-1）

| 项 | ATLAS §11.2 记 | 语料 E-AIT-1 | 本线字节复算 |
|:---|:---|:---|:---|
| 尺寸 | 256 / `0x100` | `0x110` = 272 | **272 / `0x110`** |
| 取证 VA | `0x420990` | `0x41FFE0` | `0x0041FFE0` |
| 取证指令 | `mov eax,0x100; ret` | `B8 10 01 00 00 C3` | `B8 10 01 00 00 C3` |

- `vtable[12]` of `0x007E2A50` = `0x0041FFE0`；字节 `B8 10 01 00 00 C3` ⇒ `0x110`。
- ATLAS 记的 `0x420990` 实测为 `C7 46 0C 78 32 7E 00` = `mov [esi+0xC], 0x7E3278`
  （**写 vtable 字面量**，构造序言的一部分），不是 GetSize。
- **结论**：与 `docs/re/trigger_tag_abi_deep_dive.md:21,191,211` 的 E-AIT-1 完全一致。

**核验状态**：✅ **三通道一致**：本线字节复算 + 语料 `E-AIT-1` +
2026-10-21 异族模型双通道（`dwfrun-7cee3752`：GLM 5.3 与 DeepSeek v4.1-flash 均 `CONFIRMED` 272）。

---

## 三、口径类问题（不是错，但会误导）

### G-4 / G-5 · `vtable[12] == GetSize` 不是普适前提

| 类 | ATLAS 记尺寸 | `vtable[12]` 体 | 实情 |
|:---|---:|:---|:---|
| `RadarClass` | 4864 | `mov eax,[ecx]` | 该槽是**访问器**，返回成员而非尺寸 |
| `WWMouseClass` | 96 | `mov eax,[ecx+0x20]` | 同上 |

⇒ 凡用 §11.2 尺寸者，必须先验"体首是 `mov eax,imm`"。
`tools/xcheck_sizes.py` 的 `NO-IMM` 分支就是这个门禁；本次 16 行里
**12 行 SIZE-OK、2 行 SIZE-DIFF（G-1/G-2）、2 行 NO-IMM（G-4/G-5）**。

### G-6 · 语料里同时存在 `VA` 列与 `RVA−ImageBase` 列

`re_sprint_S7_report.md` 等表把 `0x0042AB66`（VA）与 `0x0002AB66`（RVA）
并排列出。用正则直接捞 `0x…` 会把 RVA 当成 VA，制造 45 个假地址。
本线 `extract_symbols.py` 强制过 PE 段表校验，这类全部拒收。

### G-7 · 虚表全表无缺陷

20/20 一致。另 14 条"缺 RTTI 对应"是 §11.1 的**全局变量表**被同一正则捞到
（`CurrentFrame`、`VoicesEnabled` 等），不是虚表，不算冲突。

### G-8 · 本线自撤回：`0xB0C110` 不是"字段注册表根"而是 `SwizzleManagerClass::Instance`

| 项 | 前轮（错） | 本轮（实证） |
|:---|:---|:---|
| 身份 | 引擎级字段注册表的根 | **`SwizzleManagerClass::Instance`**（单例对象） |
| 为何有 vtable | 未解释 | 对象当然有：`0x006CF0C8` 静态写入 `0x7F4108` |
| `0x6CF240` 语义 | 元数据登记 | 虚表**槽 4** `Here_I_Am`：追加 `{原指针, 字段地址}` 并把**原字段清零** |
| 489 处调用 | "各处构造函数注册字段元数据" | 各处把**指针字段**登记进 swizzle 表，供存档重定位 |

**独立佐证**：`YRpp/SwizzleManagerClass.h:26`
`static constexpr reference<SwizzleManagerClass, 0xB0C110u> const Instance{};`

**影响**：任何"读了 `+0x28`/`+0x30`/`+0x54` 拿到有效指针"的假设都可能错——
登记过的字段读出来是 **0**。这是**给 ③ 安全改动能力的一条实质警告**，已转 H-007。

### G-9 · `vtable[11]` 才是身份槽，`vtable[12]` 不是"永远 GetSize"

G-4/G-5 说"槽 12 可能是访问器"。正确的一般化是：**槽 11 = `WhatAmI()`（类型 ID），
槽 12 = `GetSize()`**，两者成对。判据改为"先取槽 11 验是否是合法 `AbstractType`"，
而不是"看槽 12 体首是不是 `mov eax,imm`"。
详见 `kb/20_vtable_contract.md`；**69 个类**逐一命中，ID 冲突 0。

### G-10 · 本线工具缺陷：两个静默空集陷阱导致 10 个核心类被漏掉

`dump_class_ids.py` 第一版只报出 59 类，把 `Unit`/`Aircraft`/`Anim`/`Building`/`Bullet`
及其 `TypeClass` 全部漏掉，并把这 15 项记成"待查覆盖缺口"。**实际是工具 bug，不是数据特性**：

| 缺陷 | 表现 | 真因 |
|:---|:---|:---|
| 判据 `op_str.startswith("eax,0x")` | id `0x00..0x09` 全漏 | **capstone 把小立即数渲染成十进制**：`mov eax, 1`，没有 `0x` |
| 尺寸上限 `0 < size < 0x4000` | `HouseClass`（90,296 字节）被滤 | 自以为"类不会那么大" |

修法：用 `insn.operands`（`X86_OP_IMM`）读结构，不比对渲染文本；上界放到 `0x400000`
并按 HRESULT 形状（`0x8000xxxx`）排除失败返回值而非按大小。

**修后 59 → 69 类**，`ids in engine table but no class recovered` 从 15 项降到 5 项，
其余 5 项各有正当原因（`<none>` 哨兵 / `AbstractClass` 抽象桩 / `.rdata` 里根本没有
`SpecialClass`、`AITriggerClass`、`NavyTypeClass` 三个类）。

**教训**：任何"解析指令取常量"的工具，必须同时输出**肯定对照**
（本次即"69 行且 0 冲突"）。空集与全漏在日志上无法区分。
已记为纪律 #8，并在 `dump_class_ids.py` 的 docstring 里写明。

### G-11 · 本线自撤回：`vtable[4]` 是 `IsDirty`，不是 `Load`

| 项 | 前轮（错） | 本轮（实证） |
|:---|:---|:---|
| 槽 4 | `Load` | **`IsDirty`**，返回 `!Dirty` |
| 槽 5 | 未定 | `Load`（体首 `call 0x410380`） |
| 槽 6 | 未定 | COM `Save`（体首 `call 0x410320`） |
| 槽 13 | 泛称 `Save` | `AbstractClass::Save`（**基类序列化块**，只写 `+0x10`/`+0x20`） |

**错因**：按 YRpp 的声明顺序
（`GetClassID / IsDirty / Load / Save`）默对应，把"第 2 个"对成了 `Load`，
**漏掉 `IsDirty` 这一格**。字节只说"读 `+0x20` 返回 bool"，是 `sete al` 定谳它是 `!Dirty`。

**槽 13 与槽 6 撞名**：槽 13 不是 COM `Save`，是"基类字段的序列化块"，
派生类的槽 6 会调用它。日后引用一律写 `AbstractClass::Save`。

### G-12 · 虚表尾部的 `.rdata` 值不是虚函数，是 COL 指针

扫虚表时若某槽值落在 `.rdata`（`0x7E1000..0x811074`），**它不是代码**，
而是 MSVC 的 `vtable[-1]` `CompleteObjectLocator` 指针 —— 说明"这里换了一张表"。

`AbstractClass` 的 `[24] = 0x007FB160` 解出 `.?AVINoticeSource@@`，
`TEventClass` 的 `[24] = 0x0080C638` 解出 `.?AVTextButtonClass@@`（**无关类**）。

⇒ **不能**用"下一个 COL 是哪个类"推断当前类的接口列表 ——
`.rdata` 里 vtable 的排布不按继承关系相邻。`AbstractClass` 那条对上属巧合。
判据只用"`.rdata` 值 ⇒ 非函数"这一点。工具 `tools/dump_vtable_slots.py`。

**附带的段边界坑**：`.rdata` 是 `0x7E1000..0x811074`（不是 `..0x812000`），
而 COL 指向的 TypeDescriptor 在 `.data`（`0x812000..0xB79BE4`）。
查名字时**两段都要接受**，否则只输出 `?`。

---

## 四、待核（本线暂无裁定能力，或需真机）

| # | 事项 | 卡点 |
|:--|:---|:---|
| P-1 | `TacticalClass` 单例 `0x00887324` 的解引用层级（`**` vs `*`） | 需运行时读一次指针值，属三目标禁区边缘，暂不碰 |
| P-2 | `ScenarioClass*` / `RulesClass*` 同上 | 同上 |
| P-3 | `SpatialGrid` 桶数组"每桶 24 字节"的实证 | 可在离线字节内做（`+0x2580/+0x2584/+0x2590` 已在 `0x4137A0` 见到），留待空间索引模块 |
| P-4 | `HouseClass` 尺寸 90,296 与 `+0x1EC/+0x1ED` 字段语义 | 尺寸已实证；字段语义待 `HouseClass` 模块 |

### G-13 · 语料错注：`0x887180` 是 `INI_Art`（artmd.ini），不是 `RULESMD.INI`

`docs/re/vxl_cache_layout.md:102` 写：

```text
00715962  mov ecx, 0x887180  ; CCINIClass* rulesmd.ini
```

**该注释错。** 三处独立证据：

1. `YRpp/CCINIClass.h:293` — `static constexpr reference<CCINIClass, 0x887180u> const INI_Art{};`
2. 同文件 `:290` — `INI_Rules` 是 **`0x00887048`**，且类型为 **`CCINIClass*`（指针）**
3. 字节侧：`0x0040E031` / `0x0040E0E1` / `0x0040E191` / `0x0040E241` / `0x0040E2F1` /
   `0x0049B40B` 共 6 处 `c7 05 <addr> f4 1a 7e 00`，把 6 个全局写成 `CCINIClass` 对象

**全部 6 个地址落在 BSS**（≥ `0x0087E000`），磁盘上无字节，
所以"对象是否已构造"无法从文件复核；地址→文件名映射本轮以 YRpp 为唯一来源。

**影响**：把 `0x887180` 当 rulesmd 用会**改到 artmd 的定义**。
`INI_Rules` 是**指针**，必须解引用一次（`*[0x887048]`）才是对象 —— 两者形态不同。

### G-14 · 语料/直觉陷阱：`.rdata` 里 vtable 首尾相接，相邻 ≠ 同类

`0x7EA5F0..0x7EA64C` 这一片是 **4 张表**首尾相接：

| 表头 | 前 4 字节（`[vt-4]`）COL → 类名 |
|:---|:---|
| `0x007EA5F4` | `INIClass` |
| `0x007EA5FC` | `GraphicMenu` |
| `0x007EA604` | `DynamicVectorClass<GraphicMenuItem*>` |
| `0x007EA624` | `VectorClass<GraphicMenuItem*>` |

从 `0x7EA5F4` 往后按"连续 `.text` 指针"扫，会把 4 张表读成一张。
本线第二稿就这样把 `VectorClass<ScriptClass*>` 的 7 槽认成了 `CCINIClass` 的方法表。

**判据**：判断表的归属，**先读 `[vt-4]` 的 COL 反查类名**；扫槽时遇 `.rdata` 值即停。

### G-15 · 本线自纠：`INIClass` **不继承** `VectorClass<GraphicMenuItem*>`（撤回 R-015 §5）

R-015 曾写「`INIClass` 的第一个基类是 `VectorClass<GraphicMenuItem*>`」，
依据是 `0x004F2B66 mov [esi], 0x7EA624`。**该结论错，已撤回。**

否证四条：

1. `0x7EA624` 的 `[vt-4]` = COL `0x00802638` → TD `0x00824100`
   → `.?AV?$VectorClass@PAVGraphicMenuItem@@@@`，**是另一个类**。
2. `INIClass` 自己的表 `0x7EA5F4` 的 `[vt-4]` = COL `0x00802510` → `.?AVINIClass@@`，
   唯一槽 `0x004F2810`。**构造函数 `0x535AA0` 末尾 `0x00535B27` 写的正是 `0x7EA5F4`。**
3. `0x004F2B60` 是**析构函数**（体首 `mov eax,[esi+4]` → `test eax,eax` →
   按 `[esi+0xD]` 调 `0x7C8B3D` 释放 → 清 `[esi+0xD]`/`[esi+8]` →
   `test byte [esp+8],1` → 条件 `free(this)` → `ret 4`）。
   它写 `0x7EA624` 是**析构时恢复基类 vptr**，不是构造时建立。
4. `INIClass` 的表只有 1 槽，`CCINIClass` 的也只有 1 槽，都是标量删除析构。
   `0x7EA5F0..0x7EA648` 是 4 张表首尾相接（见 G-14）。

**教训（纪律 #11）**：`mov [reg], <vtable>` 在构造函数和析构函数里**字节相同、语义相反**。
构造：一串字段清零 + **最后**写本类 vptr；
析构：前面有字段释放，写 vptr 后紧跟 `test byte [esp+8],1` + `free(this)` + `ret 4`。

### G-16 · 本线自纠：`CCINIClass+0x0C/+0x10/+0x1C` 是**一个 `List` 成员**，不是三个基类

R-015 把这三个 vptr 读成「`GenericList` + 两个 `GenericNode` 基类子对象」。
**错。** 它们是**一个成员** `List<INISection>` 的内部结构：

```text
+0x0C  List vptr        = 0x7E1AFC  (List<INISection*>)
+0x10  First 哨兵 vptr  = 0x7E1B0C  (GenericNode)
+0x1C  Last  哨兵 vptr  = 0x7E1B0C  (GenericNode)
```

判据：`0x52ACE0`（`GenericList` 构造函数）对**同一块 0x1C 字节**做了完全相同的
`[+0]`/`[+4]`/`[+0x10]` 三次 vptr 写。`CCINIClass` ctor 只是在做同一件事。

**纪律 #12**：**"N 个 vptr" ≠ "N 个基类"**。模板容器实例自带 1 个容器 vptr
+ 2 个哨兵节点 vptr。归属判据是找该容器的构造函数。

### G-17 · 本线自纠：写 §9.4 时把 `List<T>` 尺寸算错，差点伪造一条 YRpp 冲突

R-016 初稿按「`YList = GenericList(0x10) + First(0x0C) + Last(0x0C) = 0x28`」算，
得出 `INISection` 应为 `0x50`，与 `push 0x44` 矛盾，遂准备登记一条"YRpp 结构尺寸错"。

**该结论错，已撤回。** 正确核算：

- `GenericNode`（虚析构）= `vptr(4) + Next(4) + Prev(4)` = **`0x0C`**
- `GenericList`（虚析构 + 两个 `GenericNode` 成员）= `4 + 0x0C + 0x0C` = **`0x1C`**
- `List<T> : GenericList` **不新增字段** ⇒ **`0x1C`**

用 `0x1C` 复算 `INISection` = `0x0C(Node) + 4(Name) + 0x1C(Entries) + 0x14(Checked) + 4` = **`0x44`** ✅
与 `0x00525DEA push 0x44` 逐字节一致。**YRpp 的 `INISection` 声明是对的。**

**教训**：算结构尺寸时，"基类占多少"必须先数**基类自己的虚表指针和成员**，
不能用"看起来像几个字段"的直觉。这次的错法和 G-16 同源 —— 都是把
"容器"当成"若干独立子对象"来算。

### G-18 · 本线自纠：按 YRpp 声明顺序朴素相加会算错 `AbstractTypeClass` 尾部偏移

`AbstractTypeClass` 按声明顺序朴素相加：

```text
+0x24 ID[0x18]  -> +0x3C
+0x3C zero_3C   -> +0x3D
+0x3D UINameLabel[0x20] -> +0x5D
+0x5D UIName (wchar_t*, 4) -> +0x61     ← 错
+0x61 Name[0x31]                        ← 错
```

**字节实测 `Name` 在 `+0x64`**：`0x00410A91 lea edi,[ebx+0x64]`。

差的 3 字节是 `wchar_t*` 的 4 字节对齐填充（`+0x5D` → `+0x60`）。
正确布局：

```text
+0x5D  填充 3
+0x60  UIName (wchar_t*)   ← 0x00410B58 mov [ebx+0x60],eax
+0x64  Name[0x31]          ← 0x00410A91 lea edi,[ebx+0x64]
+0x95  AbstractTypeClass 结束
```

**判据**：任何"声明顺序 = 字节偏移"的推算都必须**逐字段验对齐**，
并在算出结果后与至少一个字节观测点对照。`tools/dump_ini_keymap.py`
把这条做成了自检：算式与观测不一致就打印 mismatch。

**影响**：算错这 3 字节会让所有 `AbstractTypeClass` 派生类的字段偏移整体偏 3，
而偏移错 3 在生产/战斗类里通常表现为"读到相邻字段"而非崩溃 —— 静默错误。
