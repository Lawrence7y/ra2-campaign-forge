# R1/R2 通用：`AbstractClass` 虚表契约与 `AbstractType` 类型 ID [实证]

更新：2026-10-21（RE-ATLAS R-012）

本篇解两件事，两者此前都只有零散记载：

1. **虚表槽位的固定契约**：`vtable[11]` = `WhatAmI()`（类型 ID），`vtable[12]` = `GetSize()`。
   此前 KB 只记了 `vtable[12]`，并且已经发现它**不是全局通用**（`RadarClass`/`WWMouseClass`
   在槽 12 放访问器）。本篇给出正确的一般化：**槽 11 才是身份槽，槽 12 是尺寸槽，两者是一对**。
2. **`AbstractType` 的 74 项类型 ID 全表**，由引擎自己的名字表 `0x816EE0` 直接读出，
   并与 59 个类的 `vtable[11]` 逐一对照。

---

## 0. 结论先行

| 事实 | 值 | 证据 |
|:---|:---|:---|
| 类型 ID 名字表 | `0x00816EE0`，**74 项**，元素 `{char* name, u32 value}` 各 8 字节 | 逐项解引用读出 74 个非空名字 |
| ID 值域 | `0x00..0x49`（`<none>` .. `DiskLaser`） | 表内 `value` 字段 |
| `vtable[11]` = `WhatAmI()` | `mov eax, imm8; ret` | 59 个类全部命中，imm 与名字表 `value` 一一对应 |
| `vtable[12]` = `GetSize()` | `mov eax, imm32; ret` | 59 个类全部命中 |
| ID 冲突数 | **0**（59 个 ID，59 个不同类） | 见 `evidence/class_ids.txt` |
| 名称一致率 | 52/59 字面一致，7 条为已知别名 | 见 §3 |

**载荷**：任何 `AbstractClass*` 都能用 `vtable[11]` 识别真实类型，不需要 RTTI、
不需要 `dynamic_cast`。这是写"按类型分派"补丁的正确入口。

---

## 1. 名字表 `0x816EE0` 的读法

```text
0x00816EE0 + 8*i   -> { char* name; u32 value; }
```

- 表在 **`.data`（可写）**，不在 `.rdata`。**但其中的 `name` 指针全部指向 `.rdata`**，
  所以字符串本身是只读常量（与 `LEDGER` 纪律 #4 一致：先验段属性再引字符串）。
- 74 项，`value` 严格递增 `0x00..0x49`，**没有空洞**。
  这排除了"表里有占位项"的可能，也说明 ID 是连续枚举。

抽样（首项）：

```text
0x00816EE0  pointer 0x00817474  ->  "<none>"
0x00816EE8  value   0x00000000
```

`GetClassName(AbstractType)` 的实现（YRpp 记 `AbstractClass::GetClassName`）就是线性扫这张表。

---

## 2. `vtable[11]` / `vtable[12]` 的字节形态

以 `TEventClass` 为例（虚表 `0x007F5578`）：

```text
vtable[11] @ 0x007F55A4 -> 0x0071FA60
    0x0071FA60  B8 30 00 00 00   mov eax, 0x30        ; AbstractType::Event
    0x0071FA65  C3               ret
vtable[12] @ 0x007F55A8 -> 0x0071FA50
    0x0071FA50  B8 58 00 00 00   mov eax, 0x58        ; 88 字节
    0x0071FA55  C3               ret
```

**注意槽序**：`0x71FA60`（ID 0x30=48）在 `0x71FA50`（尺寸 0x58）**之后**，
即 `GetSize` 函数体在前、`WhatAmI` 在后，但**槽位是 12 → 11 倒序**。
这条顺序关系在 11 个触发器族类上全部成立（见 §4），可作为"是否读错相邻槽"的
交叉校验。

---

## 3. 59 个类的 ID / 尺寸对照表

完整表见 `re_atlas/evidence/class_ids.txt`（工具 `re_atlas/tools/dump_class_ids.py`）。
与三条目标相关的行：

| ID | 尺寸 | 类 | 虚表 |
|---:|---:|:---|:---|
| `0x1A` | 48 | `ScriptClass` | `0x007F0F78` |
| `0x1B` | 564 | `ScriptTypeClass` | `0x007F1008` |
| `0x1C` | 180 | `SideClass` | `0x007F2EC0` |
| `0x21` | 212 | `TaskForceClass` | `0x007F4680` |
| `0x22` | 160 | `TeamClass` | `0x007F4730` |
| `0x23` | **248** | `TeamTypeClass` | `0x007F47D0` |
| `0x26` | 72 | `TriggerClass` | `0x007F5858` |
| `0x27` | 180 | `TriggerTypeClass` | `0x007F5904` |
| `0x2C` | 56 | `TagClass` | `0x007F44E0` |
| `0x2D` | 164 | `TagTypeClass` | `0x007F45C4` |
| `0x2F` | 148 | `TActionClass` | `0x007F443C` |
| `0x30` | 88 | `TEventClass` | `0x007F5578` |
| `0x3B` | **272** | `AITriggerTypeClass` | `0x007E2A50` |

**加粗的两行**正是 ATLAS §11.2 的两条翻案值（ATLAS 记 288 / 256），
本轮获**两族独立复核**（见 §6）。

### 3.1 七条名称"不一致"全部是别名，不是错误

| ID | RTTI 类名 | 引擎表名 | 说明 |
|---:|---|---|---|
| 17 | `IsometricTileClass` | `Isotile` | 缩写 |
| 18 | `IsometricTileTypeClass` | `IsotileType` | 缩写 |
| 19 | `BuildingLightClass` | `Light` | 引擎表更短 |
| 47 | `TActionClass` | `Action` | `T` 前缀是触发器系统命名习惯 |
| 48 | `TEventClass` | `Event` | 同上 |
| 56 | `Tactical` | `TacticalMap` | 引擎表更长 |
| 57 | `SuperClass` | `SuperWeapon` | 引擎表是语义名 |

YRpp 的 `enum class AbstractType`（`YRpp/GeneralDefinitions.h:19`）是第三条独立来源，
74 项与本节完全一致，且用的正是 `Isotile` / `BuildingLight` / `Super` 这些引擎侧名称。

### 3.2 引擎表里有、但本轮没恢复出类的 15 个 ID

`0x00 <none>`、`0x01 Unit`、`0x02 Aircraft`、`0x03 AircraftType`、`0x04 Anim`、
`0x05 AnimType`、`0x06 Building`、`0x07 BuildingType`、`0x08 Bullet`、`0x09 BulletType`、
`0x0D House`、`0x1F Special`、`0x34 Abstract`、`0x3A AITrigger`、`0x40 NavyType`。

**这是本轮的覆盖缺口，不是矛盾**：`dump_class_ids.py` 只认"`vtable[11]` 是单条
`mov eax,imm; ret`"这一种形态。这些类要么 `WhatAmI` 体更长（不是单指令），
要么 RTTI 没找到虚表（954/988 有虚表）。`House`/`Unit`/`Building` 这类高频类
一定存在，只是没命中本工具的模式。

---

## 4. 槽 11/12 的成对性 —— 11 个触发器族类全表

```text
类                     vtable[11]  vtable[12]
ScriptClass            0x1A       0x030
ScriptTypeClass        0x1B       0x234
TActionClass           0x2F       0x094
TEventClass            0x30       0x058
TagClass               0x2C       0x038
TaskForceClass         0x21       0x0D4
TeamClass              0x22       0x0A0
TeamTypeClass          0x23       0x0F8
TriggerClass           0x26       0x048
AITriggerTypeClass     0x3B       0x110
SideClass              0x1C       0x0B4
```

11/11 双槽都是 `B8 imm C3` 形态，且 ID 全部落在名字表的合法值域内、无重复。
**这是"槽 11/12 是固定契约"的正面证据**，而不只是"槽 12 偶尔是 GetSize"。

---

## 4.5 第三条独立证据：`0x410380` 用槽 12 当"流长度"

`AbstractClass` 的一个方法 `0x00410380`（`TEventClass` 构造序言在 `0x0071F8CB` 调它）
在写流时把**槽 12 的返回值**当作要写的字节数：

```text
0x004103B7  call 0x6CF2C0              ; swizzle: Here_I_Am
0x004103BC  mov  eax, [esi]            ; 主 vtable
0x004103BE  mov  ebx, [esi+0x1c]
0x004103C1  mov  ebp, [edi]            ; 流 vtable
0x004103C5  mov  ecx, esi
0x004103C7  call [eax+0x30]            ; ★ 槽 12 = GetSize()
0x004103CA  push eax                   ; ★ 当作长度传下去
0x004103CB  push esi
0x004103CC  push edi
0x004103CD  call [ebp+0xc]             ; 流 Write(ptr, len)
```

这条**与"槽 12 是尺寸"完全自洽**：引擎在这里拿它当"这个对象要写多少字节"。
配合 §2 的 `mov eax, imm; ret` 形态，构成两条不同性质的证据
（形态证据 + **使用方式**证据）。

⇒ 这是判据的最佳形态：不看函数体长什么样，而看**引擎自己怎么用它**。

---

## 5. 与 §0.2 多继承前缀的关系
`TEventClass` 的构造函数 `0x0071F8C0` 里，先调 `0x4101C0` 写 4 个 vptr：

```text
0x0071F8E4  mov [esi+0x00], 0x7F5578    ; 主 vptr（本文件分析的这张表）
0x0071F8EA  mov [esi+0x04], 0x7F555C    ; IPersistStream
0x0071F8F1  mov [esi+0x08], 0x7F5554    ; IRTTITypeInfo
0x0071F8F8  mov [esi+0x0C], 0x7F554C    ; INoticeSink / INoticeSource
```

**槽 11/12 只在主表 `+0x00` 上有意义**。接口子表的槽位语义完全不同
（它们是 COM 的 `QueryInterface`/`AddRef`/`Release`/`Save`/`Load`）。
⇒ 编译器/补丁取值时**必须先确认用的是 `[obj]` 这张表**，不能对 `[obj+4]` 之类套同样的槽号。

这条是对 `kb/11_class_layouts.md` §0.2 的补充，不修改该篇。

---

## 6. 核验状态

| 结论 | 通道 | 状态 |
|:---|:---|:---|
| `vtable[12]`=GetSize，59 类，槽 11=WhatAmI | 本线字节直算（`dump_class_ids.py`） | 单通道 |
| 名字表 74 项、值域 0x00..0x49、空穴 0 | 本线直接解引用 | 单通道 |
| 74 项与 YRpp `AbstractType` 完全一致 | 社区源（YRpp `GeneralDefinitions.h:19`） | 交叉佐证 |
| `TeamTypeClass`=248 / `AITriggerTypeClass`=272 | **GLM 5.3 + DeepSeek v4.1-flash 双族独立复算** | ✅ **已核验** |

核验详情（`dwfrun-7cee3752`）：

- GLM：`CONFIRMED`，248 / 272，注"按段表 VA 换算，两 GetSize 均为 B8 imm32+C3，独立复算与参考一致"。
- DeepSeek：`CONFIRMED`，248 / 272，注"两处 GetSize 均为 NOP 填充后的函数头；
  `0x6F29C0`/`0x420990` 落在函数中段，非函数头"（后一条是给核验员的映射自检，与本篇无关）。

⇒ `CONFLICTS.md` 的 G-1 / G-2 可从"待异族核验"升级为"已核验"。

---

## 7. 未闭合

| # | 悬项 | 为什么本轮没解 |
|:--|:---|:---|
| L-17 | 15 个高频类（`House`/`Unit`/`Building`/`Bullet`/`Anim`/`NavyType`…）的 `WhatAmI` 为何不是单指令 | 需放宽模式：允许 `push`/`mov` 后再 `mov eax,imm`，或用 XRTTI 的 `get_this_locator` 反查 |
| L-18 | 名字表 `value` 字段在表里是 `u32`，但 `WhatAmI` 返回 `AbstractType`（也是 4 字节）——是否有注释说的小值优化 | YRpp 记 `AbstractType : unsigned int`，一致；无需再查 |
| L-19 | `vtable[13]` = `Save`、`vtable[4]` = `Load` 的槽号是否也全族固定 | 本轮只验了 11/12；4/13 需另跑一遍 |

---

## 8. 对编译器的可操作结论

```text
类型识别：   type_id  = call [ *(u32**)obj + 11*4 ](obj)      # 或直接读 vtable[11] 的函数
实例尺寸：   size     = call [ *(u32**)obj + 12*4 ](obj)      # 注意不是 12 恒等于 GetSize
             —— 以 vtable[11] 是否为合法 AbstractType 为准来判定"这是主表"
```

**不要**假设槽 12 永远是 `GetSize`：`RadarClass`/`WWMouseClass` 在槽 12 放的是访问器
（见 `re_atlas/evidence/size_xcheck.txt` 的 `NO-IMM` 分支）。
正确判据是**先取槽 11 验类型 ID**，槽 11 合法才认槽 12。
