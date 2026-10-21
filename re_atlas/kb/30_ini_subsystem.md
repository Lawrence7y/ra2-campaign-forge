# R2-2：INI 子系统 —— `INIClass` / `CCINIClass` 骨架 [实证]

更新：2026-10-21（RE-ATLAS R-015）

R2-2 的第一篇。目标：给 `ra2forge` 战役编译器一条可查询的 INI 读取链骨架。

> **本篇含两次当场自纠**（写完验 COL 才发现），留痕见 §8。
> 初稿把邻居表当成自己的方法表、把 `RULESMD.INI` 认错，都已撤回重写。

---

## 0. 结论先行

| 事实 | 值 | 证据 |
|:---|:---|:---|
| `INIClass` RTTI 主虚表 | `0x007EA5F4`（`[vt-4]` → `.?AVINIClass@@`） | COL 反查 |
| `CCINIClass` RTTI 主虚表 | `0x007E1AF4`（`[vt-4]` → `.?AVCCINIClass@@`） | COL 反查 |
| **但构造函数不写这两张表** | 见 §2 —— 写的是成员子对象各自的表 | 见 §2 |
| `CCINIClass` 静态全局实例 | `0x887180`=**`INI_Art`** / `0x887208`=**`INI_UIMD`** / `0x887128`=**`INI_AI`** / `0x8870C0`=**`INI_RA2MD`** / `0x887048`=`INI_Rules`(指针) / `0x887058` 与 `0x89F518` 两个未命名 | 字节 + YRpp `CCINIClass.h` 静态声明 |

**最重要的一条**：`INI_Art` 是 `0x887180`，**不是** `RULESMD.INI`。
`RULESMD.INI` 走的是 `0x887048`（**指针**，不是对象）。

---

## 1. `INIClass` 是多继承，不是"扁平类 + 一个析构槽"

YRpp 把 `INIClass` 写成没有基类的独立类（`CCINIClass.h:13`），
但**字节证明它有基类**，而且是**多继承**：

`CCINIClass` 构造函数 `0x00535AA0`（YRpp 记 `THISCALL(0x535AA0)`）逐个写子对象 vptr：

```text
0x00535AA5  lea ecx, [eax+0x10]        ; 子对象 1 @ +0x10
0x00535AAC  mov [eax+4],  0            ; +4 清零
0x00535AAF  mov [eax+8],  0            ; +8 清零
0x00535AB2  mov [ecx+4],  0            ; +0x14
0x00535AB5  mov [ecx+8],  0            ; +0x18
0x00535AB8  mov dword [ecx], 0x7E1B0C  ; ★ +0x10 写 GenericNode 表
0x00535AA9  lea edx, [eax+0x1C]        ; 子对象 2 @ +0x1C
0x00535AC4  mov dword [edx], 0x7E1B0C  ; ★ +0x1C 也是 GenericNode 表
0x00535ACD  mov dword [eax+0xC], 0x7E1B04 ; ★ +0x0C 写 GenericList 表
```

COL 反查：

```text
0x007E1B04 -> .?AVGenericList@@
0x007E1B0C -> .?AVGenericNode@@
```

⇒ **`CCINIClass` 有 3 个内嵌子对象**（`+0x0C` 一个 List，`+0x10` 与 `+0x1C` 两个 Node），
不是"一段扁平字段"。`+0x04`/`+0x08` 是普通 dword（清零）。

`INIClass` 的构造函数 `0x004F2B60` 则写 `0x7EA624`
（→ `VectorClass<GraphicMenuItem*>`），见 §2.2。

---

## 2. ⚠ RTTI 表 vs 构造函数写的表：不是同一张

这是本轮最需要记住的结构。

### 2.1 RTTI 表确实各只有 1 槽

```text
0x007EA5F0  COL -> .?AVINIClass@@            ← vtable[-1]
0x007EA5F4  [0] 0x004F2810                   ← 唯一槽（析构）
0x007EA5F8  0x008025C0                       ← 落入 .rdata = 下一张表的 COL
```

`0x007E1AF4`（CCINIClass）同样：`[0] = 0x0040E4A0`，`[1] = 0x007FAC20`（`.rdata`）。

⇒ `classes_meta.json` 记 `slots=1` **是对的**，这次不是记账错。

### 2.2 构造函数写的是**成员子对象的表**

| 对象 | 构造点 | 写入的 vtable | COL 名 |
|:---|:---|:---|:---|
| `INIClass` | `0x004F2B66` | `0x007EA624` | `VectorClass<GraphicMenuItem*>` |
| `CCINIClass` | `0x00535ACD` | `0x007E1B04` | `GenericList` |
| `CCINIClass` | `0x00535AB8` | `0x007E1B0C` | `GenericNode` @ `+0x10` |
| `CCINIClass` | `0x00535AC4` | `0x007E1B0C` | `GenericNode` @ `+0x1C` |

**注意**：`INIClass` 自己的构造函数把 **`this+0`** 写成 `VectorClass<GraphicMenuItem*>` ——
也就是说 **`INIClass` 的第一个基类就是 `VectorClass<GraphicMenuItem*>`**，
而不是"独立类"。YRpp 的写法省略了这一层。

⇒ **`INIClass` 的真实继承链**（字节）：

```text
INIClass : VectorClass<GraphicMenuItem*>          （+0x00 起）
CCINIClass : INIClass, GenericList(+0x0C),
             GenericNode(+0x10), GenericNode(+0x1C)
```

### 2.3 `.rdata` 里这些表是**交错排布**的

`0x7EA5F4` 起的 dword 序列：

```text
+0x00  0x004F2810  TEXT   ← INIClass 唯一槽
+0x04  0x008025C0  RDATA  ← GraphicMenu 表的 COL
+0x08  0x004F2830  TEXT   ← GraphicMenu 的槽
+0x0C  0x00802578  RDATA  ← DynamicVectorClass<GraphicMenuItem*> 的 COL
+0x10  0x004F2BB0  TEXT   ← 该表的槽
...
```

⇒ **整片区域是 4 张表首尾相接**，每张前面一个 COL：
`INIClass` / `GraphicMenu` / `DynamicVectorClass<GraphicMenuItem*>` / `VectorClass<GraphicMenuItem*>`。

**判据（纪律 #10）**：任何"这张表属于这个类"的判断，
**必须先验 `[vt-4]` 的 COL 反查出类名**。地址相邻 ≠ 同类。

---

## 3. 6 个静态全局 `CCINIClass` —— 名字来自 YRpp，地址本线复核

字节侧：`c7 05 <addr> f4 1a 7e 00`（`mov dword [<addr>], 0x7E1AF4`）共 **6 处静态写入**：
`0x887058` / `0x8870C0` / `0x887128` / `0x887180` / `0x887208` / `0x89F518`。
（`0x887048` = `INI_Rules` 是**指针**，由别处赋值，不走这个形态。）

YRpp `CCINIClass.h:288-296` 给出对应关系：

| 地址 | 名字 | 类型 |
|:---|:---|:---|
| `0x00887058` | （YRpp 未列） | 第 6 个，本轮未命名 |
| `0x00887048` | `INI_Rules` | **`CCINIClass*`（指针）** |
| `0x00887128` | `INI_AI` | `CCINIClass`（对象） |
| `0x00887180` | `INI_Art` | `CCINIClass`（对象） |
| `0x00887208` | `INI_UIMD` | `CCINIClass`（对象） |
| `0x008870C0` | `INI_RA2MD` | `CCINIClass`（对象） |
| `0x0089F518` | （YRpp 未列） | 第 7 个，本轮未命名 |

可复跑：`python re_atlas/tools/dump_ini_globals.py`（`evidence/ini_globals.txt`）。
工具把「`INI_Rules` 不出现」当作**肯定对照** —— 它是指针、运行期赋值，
不会被 `mov dword [addr], vptr` 戳；若它出现了，说明扫描判据错了。

**⚠ 更正**：初稿据语料 `vxl_cache_layout.md:102` 的注释
（`mov ecx, 0x887180 ; CCINIClass* rulesmd.ini`）把 `0x887180` 当成 `RULESMD.INI`。
**YRpp 明确写它是 `INI_Art`**（artmd.ini）。语料那行注释是推断且错的。

**这 5 个地址全部落在 BSS**（`.data` raw 只到 VA `0x0087E000`，而它们都 ≥ `0x00887048`）
⇒ **磁盘上没有字节，加载时才初始化**。所以我无法从文件里直接读到它们的 vptr 值来独立复核，
只能靠"`c7 05 <addr> f4 1a 7e 00` 这个写入指令"证明它们**被写成 CCINIClass 对象**。
地址→文件名的映射本轮**以 YRpp 为唯一来源**，标 `社区`。

**对编译器的含义**：
- 想动 **`rulesmd.ini`** ⇒ 用 `0x887048`（**一级解引用**：`*[0x887048]` 才是对象）；
- 想动 **`artmd.ini`** ⇒ 用 `0x887180`（直接是对象，`&` 即 `this`）；
- 两者**不能混**。直接把 `0x887180` 当 rules 用会改到美术定义。

---

## 4. 读取链

```text
CCINIClass（单份 INI）
  └─ ReadString(节, 键, buf, def, cap)     ; 0x528A10, ret 0x14
        └─ 写进 AbstractTypeClass +0x24/+0x3D/+0x64
```

`AbstractTypeClass::LoadFromINI`（`0x00410A60`）的 `ecx` 是 **`CCINIClass*`**：

```text
0x00410A69  mov esi, [esp+0x444]   ; 参数 = CCINIClass*
0x00410A72  mov ecx, esi
0x00410A74  call 0x526B00          ; 节名预处理
0x00410A9E  mov ecx, esi
0x00410AA0  call 0x528A10          ; ReadString
```

与 R-012 的 `push 0x31 = Name[0x31]`、`push 0x20 = UINameLabel[0x20]` 接得上。

---

## 5. 实测方法体（`INIClass` = `VectorClass<GraphicMenuItem*>` 一族）

`0x007EA624` 的 7 个槽体，**这确实是 `INIClass` 实例实际用的表**（构造函数写的就是它）：

| 槽 | 地址 | 体首 | 判读 |
|---:|---|---|---|
| 0 | `0x004F2B60` | 写 vtable、`+4` 判空、`+0xD` 判后释放、清 `+0xD`/`+8` | 析构 / 标量删除 |
| 1 | `0x004F28E0` | `mov esi,[ecx+8]` 后与 `[edi+8]` 比较 | `operator==` |
| 2 | `0x004F2920` | 分配路径 | `SetCapacity` |
| 3 | `0x004F29D0` | `+4` 释放路径 | `Clear` |
| 4 | `0x004F2A00` | `mov al,[ecx+0xC]` | `IsAllocated` |
| 5 | `0x004F2A40` | 同上变体 | |
| 6 | `0x004F28A0` | `mov eax,[ecx+4]; mov eax,[eax+ecx*4]` | `operator[]`，**4 字节步长 ⇒ 元素是指针** |

字段偏移（`INIClass` 实例）：`+0x04` Items / `+0x08` Count / `+0x0C` 标志 /
`+0x0D` 释放标志。
注意 **`ParticleClass` 等 `AbstractClass` 的 `+0x04` 是 vptr，这里的 `+0x04` 是数据** ——
`INIClass` 不是 `AbstractClass` 派生，不能套用 `kb/22` 的槽位契约。

---

## 6. 未闭合

| # | 悬项 |
|:--|:---|
| I-1 | `0x526B00`（节名预处理）/ `0x526810`（节存在判定）的语义 |
| I-2 | `INIClass` / `CCINIClass` 的实例尺寸（语料记 `CCINIClass` = `new(0x58)`，本线未独立复核） |
| I-3 | `0x0089F518` 这个第 6 个静态 `CCINIClass` 是什么 |
| I-4 | `INISection` / `INIEntry` 节点布局（`+0x10`/`+0x1C` 两个 Node 挂什么） |
| I-5 | `GraphicMenu` 基类的作用（`INIClass` 继承它，但 YRpp 未记载） |

---

## 7. 核验状态

| 结论 | 通道 | 状态 |
|:---|:---|:---|
| `0x7EA5F4` = `INIClass` / `0x7E1AF4` = `CCINIClass`（COL 反查） | 字节 | 单通道字节 |
| 两 RTTI 表各 1 槽 | 字节 | 单通道字节 |
| 构造函数写的是成员子对象表（`3` 个 vptr for `CCINIClass`） | 字节（`0x535AA0` 逐指令） | 单通道字节 |
| `INIClass : VectorClass<GraphicMenuItem*>` | 字节（ctor 写 `0x7EA624`）+ COL 名 | ✅ 双通道 |
| `0x887180` = `INI_Art`（**不是** rulesmd） | 字节（是 CCINIClass 全局）+ **YRpp `CCINIClass.h:288-296`** | ✅ 双通道，**推翻语料注释** |
| `0x887048` = `INI_Rules` 且是**指针** | YRpp | 社区源（本线未独立复核解引用层级） |

---

## 8. 本轮自纠留痕（两次）

**自纠 1：把邻居表当成自己的方法表。**
初稿写"`0x7E1B44` 是 `CCINIClass` 的 7 槽方法表"。
验 `[vt-4]` → COL → `.?AV?$VectorClass@PAVScriptClass@@@@`，与 INI 无关。
错因：我从 RTTI 表头往后找"第一段连续 ≥4 个 `.text` 指针"的 run，
那段 run 恰好紧跟其后，我就默认是同类延续。**没验 COL。**

**自纠 2：`0x887180` 是 `INI_Art` 不是 `RULESMD.INI`。**
初稿沿用了语料 `vxl_cache_layout.md:102` 的注释。
YRpp 明确列出 `INI_Art{0x887180}`，`INI_Rules` 是 `0x887048` 且为**指针**。
语料那行注释是推断且错。

**纪律 #9（新增）**：RTTI 的 `slots` 是记账值，**并且** `.rdata` 里多张表首尾相接。
按槽号遍历必须配"值落 `.text`"判据，且判断归属必须验 `[vt-4]` 的 COL 名。

**纪律 #10（新增）**：**社区源（YRpp）与语料注释冲突时，先查 YRpp 的静态地址声明**。
本轮两处地址归属都是 YRpp 对、语料注释错。
