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

### G-19 · 本线自纠三次：`RulesClass` 节名恢复的三个连锁判据错

`tools/dump_rules_sections.py` 首版到第三版各有一次判据错，每次都是**静默产出**
（不报错、跑得通），最危险的是第三次 —— 它产出的是**看起来合理的假答案**。

| 版 | 判据 | 产出 | 为什么错 |
|:--|:---|:---|:---|
| 1 | `op_str.startswith("dword ptr [")` | **0/37** | capstone 把目标操作数写在**逗号之后**：`'eax, dword ptr [0x7f0c94]'`。前缀匹配必然全落空 |
| 2 | 首个可打印字符串 | 34/38，但 3 个错 | `Read_Difficulty` 解成 `'FirePower'`、`Read_LandCharacteristics` 解成 `'Hover'` —— 都是**键名** |
| 3 | 上一条 + 节名表白名单 | 17/38 | 直压型节名（`Animations`/`VoxelAnims`/`Particles`/`Warheads`）**不在**指针表里，被全砍；且扫描器**回退到相邻的、恰好在表里的字符串**，产出更隐蔽的假答案 |
| 4（定稿） | 锚定 `GetSection`/`GetKeyCount` 调用，取前一个可解析串；`min_len=2` | **36/38**，2 个结构性未恢复 | — |

**第 3 版是最该记的教训**：白名单看似"提高精度"，实际把判据倒过来了 ——
先固定"答案必须在这个集合里"，再去找，找不到就退而求其次。
**正确的顺序是先用独立判据定位（这里是 `GetSection` 的实参），再拿结果去核对集合**，
而不是用集合当过滤器。

**另一个沉默点**：`min_len` 取 3 会让 `AI`、`IQ` 两个**真实**节名永远找不到，
表现为"这两个函数没节名"，而不是任何报错。

**纪律 #17（新增）**：**白色名单只能用来核对，不能用来定位。**
用白名单过滤候选时，一旦候选不在名单内，必须区分"判据找错了"与"名单不全"——
默认应假定后者，并把未命中项单独列出，而不是丢弃。

### G-20 · 「第一个 X」当「职责」：`Read_File` 被我读成只处理一个节

工具 `dump_rules_sections.py` 对每个 `Read_*` 返回"**体内第一个**节名引用"。
对 `Read_File` 我据此写成了「`Read_File` → `ColorAdd`，但它不只读这一节」，
并在 KB 里标为 `[首引用]`。**这个表述仍然把实现细节当成了职责。**

再读一遍字节（到第一个 `ret` 为止）才发现 `Read_File` 实际枚举 **7 个节**：

```text
ColorAdd / Countries / OverlayTypes / SuperWeaponTypes / Warheads /
SmudgeTypes / TerrainTypes          （外加 Easy / Normal / Difficult 三个键名）
```

而且它的第一个动作不是碰 `ColorAdd`，是 `call 0x66D3A0`（`Read_Colors`）：

```text
0x00668BFD  push esi
0x00668BFE  call 0x66D3A0        ; Read_Colors
0x00668C03  mov eax,[0x7F0C98]   ; 之后才用 ColorAdd
```

**判据缺陷**：工具回答的是「体内第一个节名引用在哪个地址」，
我问的是「这个函数负责哪些节」。前者是实现细节，后者是职责 —
一个函数可以转调别的 loaders、可以循环枚举多个节、可以两者兼有。
**"第一个"永远不足以回答"负责哪些"。**

**修正**：§13.4 已重写为实测的 7 节表 + 转调说明；§13.2 中该行加注
"首个 `GetSection` 用的节，非职责范围"。

**纪律 #18（新增）**：凡工具只返回「第一个 / 首个 / 最近一个」命中时，
不得据此断言该对象的**范围或职责**。要断言职责，必须枚举完整函数体
（到 `ret` 为止）并说明其中是否有转调与循环。

### G-21 · 最危险的一类：`read_va` 越段读，把 `.detour` 字节当成 BSS 数据

本线所有工具都用 `fo = VA - 0x400000` 做 VA→文件偏移映射。
这个映射**在 `.data` 的 raw 尾部之后仍然"成立"**，因为文件比 `.data`
的 raw backing 长（`.rsrc` 与 `.detour` 还在后面）。

实测：`0x00885780` 是 **BSS**（VA ≥ `0x87E000`，磁盘无字节），
但 `0x885780 - 0x400000 = 0x485780`，而这个偏移**落在文件内**（文件长 `0x49A110`），
于是 `read_va` 返回 `.detour` 段的真实字节，`cstr` 把它解码成
`'ostMessageA'` —— 一个看起来像字符串、实际是 Win32 导入名的假值。

**它差点造成什么**：`Read_Colors` 的节名表里因此多出一项 `ostMessageA`，
`RulesClass` 节表的交叉核对里多出一个 `'�'` 垃圾项。
两者都不报错，只是**凭空多出一条结论**。

**修法**：`read_va` 改为**逐段边界校验**，只承认 `.text`/`.rdata`/`.data`
（这三段的 delta 恰为 `0x400000`），越界或超出 `raw_size`（BSS）一律返回 `b""`。

```python
SECTIONS = [
    (".text",  0x001000, 0x3DF38D, 0x001000, 0x3E0000),
    (".rdata", 0x3E1000, 0x030074, 0x3E1000, 0x031000),
    (".data",  0x412000, 0x367BE4, 0x412000, 0x06C000),
]
# 命中段后还要查 d >= raw_size -> BSS -> b""
```

**纪律 #19（新增）**：**VA→文件偏移不能只做减法。**
必须按 PE 段表逐段校验，且对每段区分 `vsize` 与 `raw_size`：
`d >= raw_size` 即 BSS，必须返回空。
**"BSS 无字节"这条规则靠减法本身是证明不了的** —— 文件比 `.data` 长，
减法会把后面的段错位读进来。本线此前每次口头引用"BSS 无字节"时，
实际用的都是这个未校验的减法；本轮才第一次把它变成代码约束。

### G-22 · 窗口式扫描把相邻函数吞进来：`Init` 与 `Read_File` 的边界

`RulesClass::Init` 在 `0x6686C0`，`Read_File` 在 `0x668BF0` —— **相距仅 0x530**，
而 `Read_File` 有 328 条指令、到 `0x668F8D` 才 `ret 4`。

工具第一版用 `disasm(read_va(INIT, 0x1600), INIT)` 扫 `Init`，
**窗口 0x1600 远大于 `Init` 的真实长度 `0x526`**，于是把 `Read_File` 里的
24 个 `Read_*` 调用全算进了 `Init`。产出：

```text
Init 内 32 个内部调用 → Read_Colors / Read_Sides / Read_BuildingTypes / …
```

这份"载入顺序"读起来完全合理，**且与 YRpp 注释不矛盾**（注释只说
`Init` 对第一份 INI 调一次、`Read_File` 对后续调），
所以单看输出**看不出错**。按 `ret` 边界重划后真实结构是：

| 函数 | 真实范围 | 内容 |
|:---|:---|:---|
| `Init` | `0x6686C0`–`0x668BE5`（`ret 4`） | **只调 `Read_File` ×3**，不直接调任何 `Read_*` |
| `Read_File` | `0x668BF0`–`0x668F8D`（`ret 4`） | **28 个 `Read_*` 调用**，才是 loaders 的容器 |

**修法**：扫描函数体一律用**显式 `[lo, hi)` 区间**，区间由"扫到第一个 `ret`"确定，
不再用"窗口大小"。

**纪律 #20（新增）**：**不许用"窗口大小"扫函数体。**
窗口必须由函数自身的边界（`ret` / 下一个函数头）确定；
窗口大于真实函数体时，产出的是**相邻函数的调用序列**，
而它在语法与语义上都完全合理 —— 这是最难发现的一类错。
用显式区间，并加一条边界正对照（如"`Init` 内 `call Read_File` 恰 3 次"）。

---

### G-23 · capstone 单次 `md.disasm` 在 `.text` 的 `0x46F5A0` 静默截断

**发现（R-023）**：`md.disasm(整段 .text 字节)` 在 `0x46F5A0` 停止解码并**正常返回**。
该处是一张跳转表（`49 00 c5 e4 46 00 04 e6 46 00 …`，前面是一整片 `04` 字节表），
capstone 拒绝把它解成指令，于是**一次调用只覆盖 `.text` 的前 9%**：

| 口径 | 指令数 | 覆盖终点 |
|:---|---:|:---|
| 单次 `md.disasm` | **155,215** | `0x0046F5A0` |
| 分块扫描（64KB 块） | 1,150,117 | 段尾 |
| 带审计重同步的扫描 | **1,389,579** | `0x007E0FFF` |

**影响面**：任何"扫 `.text` 求全部引用/全部调用点"的工具，只要写成
`for insn in md.disasm(read_va(TEXT_LO, TEXT_SIZE), TEXT_LO)` 就**只看了 9%**，
而且**不会报错**。已确认受害：`dump_ini_keyindex.py`（R-019）、
`dump_rules_fields.py` 首版消费者扫描、`dump_rules_consumers.py` 首版。

**判别**：跑完打印**最后一条指令的地址**。若它远小于段尾（本件 `0x7E1000`），
就是截断了。仅凭"没报错 + 结果看起来合理"无法发现。

**修法**：`tools/text_sweep.py` —— 分块 + 在停点处按 CALL 密度重同步
（代码每几十字节有一条 `e8` 调用；跳转表/字面量表一条都没有），
并**返回每一处跳过的审计记录**供打印。

**独立对账**：纯字节 `E8` 扫描（不解码任何指令）找 INI 读取器调用点，
得到 2,426 处，与指令扫描**逐址相等、零差异**。这条对账现在是硬正对照。

**纪律 #21（新增）**：**扫整段 `.text` 时禁止单次 `md.disasm`,必须分块或重同步,
且必须打印"最后一条指令地址"和"每一处跳过"。**
"没报错"不是覆盖率证据;覆盖率只能用「最后指令地址 == 段尾」或
「与独立方法逐址相等」来证明。

**纪律 #22（新增）**：**正对照的期望值不能取自被怀疑对象自身的输出。**
R-019 的正对照写的是「`Name`/`UIName` 各恰 1 处」—— 那个 1 处正是截断后
剩下的唯一一处，等于**把 bug 校准成了正确答案**。
正对照的期望值必须来自**独立方法**（如字节扫描）或**独立事实**（如已知函数边界）。

---

### G-24 · 窗口 `0x1000` 腰斩长函数，且**无任何提示**

**发现（R-023）**：`dump_rules_keys.py` 用 `WINDOW = 0x1000` 解 loader 函数体，
但 4 个 loader 长达 6–10 KB：

| loader | 函数体 |
|:---|---:|
| `Read_AudioVisual` | **0x2710（10 KB）** |
| `Read_AI` | 0x1389 |
| `Read_CombatDamage` | 0x0FFD |
| `Read_General` | 0x0FFF |

工具的行为是"解到 `ret` 就停"——**窗口用完也照样返回**，于是这 4 个 loader
的键清单被腰斩，而输出看起来完全正常。`Read_General` 因此从 14 键变成 **279 键**，
总数 306 → **651**。

**这是 G-22（窗口吞相邻函数）的镜像错误**：G-22 是窗口**太大**把邻居读进来，
本条是窗口**太小**把自己的后半截丢掉。两者都属"窗口大小 ≠ 函数边界"。

**纪律 #23（新增）**：**每个需要"函数完整体"的工具，必须内置一条
"是否走到该函数自己的 `ret`"的断言。**
没走到就必须报错，不能返回已解出的部分当结果。
"解到 `ret` 就停"只有在**确实解到了 `ret`** 时才是正确行为。

### G-25 · 键提取按"函数体内所有字面量 push"取，参数与节名混进键表

**发现（R-023）**：`ReadInteger(section, key, default)` 的调用形态是

```text
push <default>      ; 可能本身就是字符串地址
push <KEY>
push <section>
call ReadInteger
```

原实现把函数体内**每一个**可打印字面量 `push` 都当成键，于是：
- 默认值是字符串时被算成键；
- 节名被算成键（`Read_File` 的 `Warheads`/`Easy`/`Normal`/`Difficult` 全是节名）；
- 无法说明某个键属于哪次调用。

已改为**逐调用取 `got[1]`**（倒数第二个 push），并用
`READER_KEYS` 记录每个读取器的栈参数量。

**判据不能按名字过滤**：`Warheads`/`Easy` 这类列表节名**不在** 31 项指针表里
（那张表只有 `Read_File` 直接处理的节），所以"排除已知节名"这条路走不通 ——
必须按**位置**（它在调用参数里的第几位）判定。

---

### G-26 · `[reg+off]` 匹配既漏又误：单值"消费点"是假精度

**发现（R-024）**：统计"某个结构字段被谁读"时，把 `[任意寄存器 + off]` 一律算上
是错的，两个方向同时错：

| 方向 | 机理 | 实例 |
|:---|:---|:---|
| **误计** | 任何对象只要某字段恰好落在同一偏移就算中 | `[ecx+0]` 报了 **56,820** 次（真值个位数） |
| **漏计** | 很多函数把 `RulesClass*` 当**参数**收下，基址寄存器在函数外赋值 | `0x0046399A` 的 `mov ecx,[ebp+0x1488]`，`ebp` 由调用方传入 |

**单值不可得**，只能给区间：下界 = 基址可追溯到 `mov reg,[0x8871E0]`，
上界 = 任意 `[reg+off]`。`[AudioVisual]` 的 `+0x0000` 字段就是
`[0, 56820]` 这种荒谬区间。

**可以确证的只有下界 == 上界的情形**（27 键里有 13 个，如 `Money` `[3,3]`、
`ShortGame` `[2,2]`）。`ShadowGrow` 是 `[0,0]`，双向确证零消费。

**判据**：**唯一地址（全局变量）的引用计数是可靠的**（扫到那个地址就是那个变量）；
**靠偏移匹配的计数不可靠**，必须给区间。两者不要混用。

**纪律 #24（新增）**：**不能用偏移匹配得出的单值当事实。**
要么追踪基址来源（并说明它会漏掉参数形式），要么报区间。
宁可写 `[4, 33]`，也不要写一个看起来很确定的 `33`。

**纪律 #25（新增）**：**不要把某个调用方的参数硬编码进通用函数的函数体。**
`consumers()` 里写死 `0x1480 <= d < 0x14BC`（MultiplayerDialogSettings 的区间）
之后，第二个调用方（`[AudioVisual]`）的每个字段都报 0 消费点 ——
函数仍然是"对的"，只是只对一个场景对。

---

### G-27 · "字符串不在 `.rdata`" 被误当成"键读不到"

**发现（R-025）**：R-024 判定 22 个键"解不出"时，我把原因写成
「`FogRate` 的字面量**不在 `.rdata`**」。实测它**在 `.data`（`0x0083A2EC`）**，
各出现一次、各被引用一次，且引用点全部落在 `Read_AudioVisual` 的函数体内。

**"不在 `.rdata`" 不等于"没有字面量"，更不等于"键读不到"。**
`read_va` 的搜索范围是 `.text`/`.rdata`/`.data` 三段，我当时的核对脚本只查了
`.rdata`，得出"没有"的结论后，就把它当成了原因写进 KB 和 ledger。

真因是**存回不是 `mov`**（`ReadDouble` 的 `fstp qword`/`fstp dword`）。

**纪律 #26（新增）**：**"找不到 X" 的结论，必须先证明搜索覆盖了全部可能位置。**
说"字符串不存在"之前，先在全文件字节流里搜一次（而不是在某个段里搜），
并打印**它实际在哪一段**。R-023 的 `read_va` 越段读（G-21）是"找到了假的"，
本条是"没找到真的" —— 两者都是**搜索范围定义了结论**。

### G-28 · 正对照绑死在单一输入上，就不是对照

**发现（R-025）**：`dump_rules_fields.py` 的正对照写死了
「`0x7F0CA0` 必须解析成 `MultiplayerDialogSettings`」「首字段 `+0x1480`」
「末字段 `+0x14B8`」—— 这些只对 MPD 成立。把工具指向 `[AudioVisual]`
（`0x006691E0`）时，**151 行全部双向一致**，却报"正对照失败"。

**期望值只对一个输入成立，那是硬编码，不是对照。**
它的问题不是"过严"，而是**它校验的对象根本不是本次运行的结果**。

**纪律 #27（新增）**：**多目标工具的每条正对照，必须声明它的适用范围。**
特定目标的控制写成"当 X 在目标列表里时校验"，另加对**任意**目标成立的通用控制
（如"非空""双向一致 100%""所有读者都在登记表内"）。

---

### G-29 · 为了"修到一致"而抹平引擎语义，会造出伪造的 100%

**发现（R-026）**：`[General]` 有 4 处"自检不通过"：
1 处跨字段默认值、2 个内嵌子对象字段、1 个字符串栈缓冲默认。

它们**全都不是缺陷**：

| 现象 | 真相 | 正确处置 |
|:---|:---|:---|
| `CMislAcceleration` 默认取自 `DMislAcceleration` | 引擎刻意用对面阵营值作默认 | 标注，**不改** |
| 3 个字段构造器未写 | 属内嵌子对象，由子对象构造器初始化（`+0x0EC4` 是 vptr 可作旁证） | 降级为提示 |
| `ReadString` 的 `doff` 为 None | 默认值是**栈缓冲地址**，不是字段 | 不对它算失败 |

如果按"自检必须全绿"去改，最省事的做法就是把这三类都判成通过 ——
**得到 100%，但那个 100% 是伪造的**：它把"引擎这样设计"和"我解析错了"
混成同一类。

**纪律 #28（新增）**：**自检的每一处失败，必须先判定它是「实现缺陷」还是
「被观察对象的真实行为」。**
判据是**换一个独立方法能否复现同一现象**（本轮用 ctor 的双字对、
用 vptr 相邻性、用栈缓冲的 `lea` 形态分别佐证）。
只有确认是实现缺陷才修；确认为真实行为的，**保留标注并单独计数**，
不要为了让检查变绿而放宽判据。
（对照 [[lead-file-stop-order-and-live-write-discipline]] 的"禁删检查项求绿"。）

---

### G-30 · 判据依赖调用方输入的写法，就不可复现

**发现（R-027）**：外部目标的判定写成了
```python
is_external = ... or "0x0066D270" in name or ...
```
其中 `name` 是 `loader_<hex>`，而 `<hex>` 的大小写取决于命令行怎么敲。
于是 **`0x66D270` 通过、`0x66d270` 失败** —— 同一个 loader，两种结论。

这是比"结果错"更糟的一类：**结果随无关输入变化，且两次运行都"有理由"**。
批量跑（`hex(va)` 产出小写）与手工跑（大写）给出的结论不一致，
如果只看其中一次，会得出完全相反的可信度判断。

**纪律 #29（新增）**：**判据只能依赖被观察对象本身，不能依赖调用方怎么写。**
地址按数值查表，不按名字字符串匹配；路径按规范化后的真实路径比较，
不按调用方传入的原始字符串；类型按 RTTI/结构判定，不按变量名。

### G-31 · 三类目标不能共用一套判据

**发现（R-027）**：`dump_rules_fields.py` 原本对每个 loader 都检查
「默认载入偏移 == 存回偏移」。这对写 `[this+off]` 的普通节成立，但对：

- **外部对象**（`Read_Difficulty`，默认值是 `push 0x3FF00000; push 0` 立即数）
  ⇒ 12 行全部判"不一致"；
- **分派器**（`Read_Difficulties` 只调别人）⇒ 判"没解出任何字段"；
- **写全局表**（`Read_LandCharacteristics` 无对象基址）⇒ 同上。

三类假失败共 14 行，占本轮全部失败项的 **100%**。

**处置**：正对照按目标类型分档（KB §18.4）：
普通节用双向一致；外部对象用**字段跨度不重叠**；分派器/写全局**空结果不计失败**。

**纪律 #30（新增）**：**一条判据只对一类结构成立时，必须显式分支，
不能默认它对所有输入都适用。** 与 G-29 同源：
为了"全绿"而放宽是造假；为了"严格"而误杀是失真。两者都源于
**用错了判据，而不是判据太松或太紧**。

---

### G-32 · 同一个"对象寄存器"在七个 loader 里是七个不同寄存器

**发现（R-028）**：TypeClass 继承链上有七个 `LoadFromINI`，全部是 thiscall，
`this` 从 `ecx` 进来，但**保存的寄存器各不相同**：

| 类 | `this` 寄存器 |
|:---|:---|
| `AbstractTypeClass` / `ObjectTypeClass` | `ebx` |
| `TechnoTypeClass` / `BuildingTypeClass` | `ebp` |
| `InfantryTypeClass` / `AircraftTypeClass` | `esi` |
| `UnitTypeClass` | `edi` |

R-023 的 `detect_base()` 只在 `{edi, ebx, esi}` 里挑候选，于是在
**TechnoType（挑中 `esi` = INIClass）**、**BuildingType（挑中 `edi` = INIClass 参数）**
两处选错对象。后果不是报错，而是**给错误的对象解出一整套自洽字段表**：
偏移全部落在这个大对象的前段，行内"默认载入 == 存回"照样 100% 一致。

**处置**：改成位置判据 —— **第一个 `mov reg, ecx` 之前没有 `call` 时，
目的寄存器就是 `this`**。七处全部命中，且与各类 `GetSize` 的槽 12 上界互相印证。

**纪律 #31**：**"多数样本里成立的寄存器约定"不是契约。**
当一个工具要在 N 个函数间通用时，先量出每一处的实际寄存器并打印出来；
打印出来的值本身就是对照 —— 七个函数给出五种寄存器，肉眼立刻可见，
而"全部当成 esi"则永远静默正确。

---

### G-33 · `push eax` 既是"节名缓冲"也是"上一个键的值"，靠位置定夺

**发现（R-028）**：这些 loader 用两个**节名缓冲**（`+0x24` 类型自身名 /
`+0x1F8` 被 `Image=` 改写的美术节名）当 `section` 参数，分别 `lea` 到不同的寄存器。
于是 `push <reg>` 是一个合法的节名传递。但同一个形状也用于另一种语义：

```
call 0x5276d0          ; ReadInteger AirstrikeTeam
push eax               ; ← 它的返回值，作为下一个键的默认值
push 0x843b70          ; EliteAirstrikeTeam
call 0x5276d0
```

`push eax` 到底是哪一种，取决于**上一条指令是不是一次 reader 调用**：
调用之后 `eax` 是返回值，且 `call` 已经破坏了 `eax` 上的任何缓冲租约。

**处置**：两条规则并用 ——
1. 任何 `call` 作废 `eax/ecx/edx` 上的节名缓冲租约（`ebx/esi/edi/ebp` 存活）；
2. `push eax` 紧跟 reader 调用时一律判为"跨键默认"，不当节名。

不加规则 1 时，`BuildingTypeClass` 里 `+0x1F8` 同时租给了 `eax` 和 `edi`，
`OccupyHeight` 的默认值（= `Height`）被当成"push 节名"吃掉；
不加规则 2 时，`EliteAirstrikeRechargeTime` 与 `EliteAirstrikeTeam` 的
默认值关系整条丢失。

**纪律 #32**：**同一形状在同一函数里有两种语义时，判据必须是"上一条指令"级别的，
不是"这个操作数长什么样"级别的。** 形态相似的两行代码可能语义完全无关；
决定语义的是紧邻的上下文，而不是这个 token 本身。

---

### G-34 · "默认值缺失"里有三种完全不同的东西，只有一种算失败

**发现（R-028）**：第一版报出 **31 行"默认载入=None"**。逐个看下去，
它们分属三类，一类是缺陷、两类是引擎事实：

| 类 | 例 | 真相 |
|:---|:---|:---|
| 立即数默认 | `Speed` 前有 `push -1` | 键缺席时的默认值就是 -1，**编译器正需要这个数** |
| 跨键默认 | `EliteAirstrikeRechargeTime` 前有 `push eax` | 默认值 = 上一个键的新值，可精确解析为上一行的存回偏移 |
| 拆栈提升 | `OccupyHeight` 读 `+0xEF4` 后存 `+0xEF8` | 上一个键的 store 被编译器挪到了下一个键的实参之后 |
| **真缺陷** | — | 解析漏读 |

修完后**真缺陷 0 行**，`Speed = -1` 与 `EliteAirstrike*` 的依赖关系被显式还原。

**处置**：三种情况各给一种标记（`立即数默认(N)` / `跨字段(+0xX)` / `一致`），
不合并成"缺失"。

**纪律 #33**：**把三种不同的成因报成同一个 `None`，是最难发现的那类错误 ——
它看起来像"工具能力不足"，实际上是"工具没区分"。**
与 G-31 同源：判据不够细，就会把引擎的真实行为计成自己的失败；
而为了消掉这些失败去放宽判据，又会把真实缺陷一起放走。

---

### G-35 · 构造器"覆盖不到"的偏移，大半是**指针环清零**，不是没初始化

**发现（R-028）**：把每类自己的构造器解出来后，逐偏移对账。
`InfantryType` / `UnitType` / `AircraftType` 三类 **33/33、27/27、10/10 全覆盖**；
`BuildingTypeClass` 却有 **132 个偏移在建器里找不到任何 `[esi+off]` 写**。

这 132 个偏移**不是问题**：构造器把它们清成一个指针推进的环：

```
lea  eax, [esi + 0xF5C]
mov  ecx, 0x15          ; 21 项
...
mov  [eax], edi         ; 经由指针写，操作数里根本没有 esi
add  eax, 0x44          ; 步长 0x44 = 68 字节
```

21 × 0x44 = 1428 字节，正好罩住 `+0x0F5C..+0x14DF` 的 132 个动画字段
（`ActiveAnimX` 起 17 组 × 8 个）。**按偏移扫构造器永远扫不到它们。**

**处置**：`loop_cleared_offsets()` 还原 `(基址, 步长, 项数)` 三元组，
把 132 个"无 ctor 写"折叠成 **1 条有机制的解释**；
最终 `BuildingTypeClass` 269/269 全部归因（本类 ctor 136 + 基类 1 + 指针环 132），
"内嵌子对象/未解" 为 **0**。

**纪律 #34**：**"扫不到"必须再问一句"是不是根本没通过这个寄存器写"。**
与 G-27 同族（"搜的范围里没有 ≠ 不存在"），但更隐蔽：
这里循环确实初始化了那些字节，只是**存取路径绕开了你匹配的那个操作数形状**。
