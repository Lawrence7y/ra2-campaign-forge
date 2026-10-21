# R2-2：INI 子系统 —— `INIClass` / `CCINIClass` 骨架 [实证]

更新：2026-10-21（RE-ATLAS R-015 初版 / R-016 重写 §1、§5 并新增 §9 `INISection`/`INIEntry`）

R2-2 的第一篇。目标：给 `ra2forge` 战役编译器一条可查询的 INI 读取链骨架。

> **⚠ R-016 撤回 R-015 的两条核心结构结论**（§1 与 §5），留痕见 §8.3、§8.4。
> R-015 写的「`INIClass : VectorClass<GraphicMenuItem*>`、`CCINIClass` 三基类多继承」
> **不成立**：那三个 vptr 是**一个 `List<INISection>` 成员**（自带 vptr + 首尾两个哨兵节点）。
> 根因是同一条纪律反复被违反：**`.rdata` 表首尾相接，地址相邻 ≠ 同类**。
> 本篇 §1 已按字节重写，旧结论保留在 §8 留痕。

---

## 0. 结论先行

| 事实 | 值 | 证据 |
|:---|:---|:---|
| `INIClass` RTTI 主虚表 | `0x007EA5F4`（`[vt-4]` → `.?AVINIClass@@`） | COL 反查 |
| `CCINIClass` RTTI 主虚表 | `0x007E1AF4`（`[vt-4]` → `.?AVCCINIClass@@`） | COL 反查 |
| 两类的 RTTI 表各只有 **1 槽**（都是标量删除析构） | `0x004F2810` / `0x0040E4A0` | 槽值 + 槽体 |
| `CCINIClass` 构造函数 `0x00535AA0` 写的表 | `+0x00`→`0x7EA5F4`(INIClass)、`+0x0C`→`0x7E1AFC`(`List<INISection*>`) | 逐指令 |
| `INIClass` 实例尺寸 | **`0x40`** | `+0x28..+0x40` 是最后字段（§2） |
| `INISection` 实例尺寸 | **`0x44`** | `0x00525DEA push 0x44` |
| `INIEntry` 实例尺寸 | **`0x28`** | `0x00526039 push 0x28` |
| 节查找机制 | **排序数组 + CRC32 二分**，不是链表遍历 | §3 |
| 节名/键名比较 | **大小写敏感**（CRC32 原文，无折大小写） | §3.3 |
| `CCINIClass` 静态全局实例 | `0x887180`=**`INI_Art`** / `0x887208`=**`INI_UIMD`** / `0x887128`=**`INI_AI`** / `0x8870C0`=**`INI_RA2MD`** / `0x887048`=`INI_Rules`(指针) / `0x887058` 与 `0x89F518` 两个未命名 | 字节 + YRpp `CCINIClass.h` 静态声明 |

**最重要的一条（对编译器）**：`INI_Art` 是 `0x887180`，**不是** `RULESMD.INI`。
`RULESMD.INI` 走 `0x887048`（**指针**，不是对象）。
两者**不能混**；直接把 `0x887180` 当 rules 用会改到美术定义。

**第二重要的一条（对编译器）**：节名与键名**大小写敏感**。
`[InfantryTypes]` 与 `[infantrytypes]` 是两个不同的节，`Name` 与 `name` 是两个不同的键。
编译器生成 INI 时不能指望引擎做大小写归一。

---

## 1. `INIClass` / `CCINIClass` 的真实结构（R-016 重写，撤回 R-015 §1）

### 1.1 字节

`CCINIClass` 构造函数 `0x00535AA0`（YRpp 记 `THISCALL(0x535AA0)`，确为**构造函数**，
末尾 `0x00535B27 mov [eax], 0x7EA5F4` 写的是**本类的 RTTI 表**）：

```text
0x00535AA6  lea ecx, [eax+0x10]        ; List 的首哨兵节点
0x00535AAC  mov [eax+4],  0            ; List+4 (GraphicMenu? 见 §1.4)
0x00535AAF  mov [eax+8],  0            ; List+8
0x00535AB2  mov [ecx+4],  0            ; 首哨兵.Next
0x00535AB5  mov [ecx+8],  0            ; 首哨兵.Prev
0x00535AB8  mov dword [ecx], 0x7E1B0C  ; 首哨兵 vptr = GenericNode
0x00535AC4  mov dword [edx], 0x7E1B0C  ; 尾哨兵 vptr = GenericNode  (edx=[eax+0x1C])
0x00535ACD  mov dword [eax+0xC], 0x7E1B04 ; List vptr = GenericList
0x00535B0C  mov dword [eax+0xC], 0x7E1AFC ; ★ List vptr 改写成 List<INISection*>
0x00535B27  mov dword [eax],   0x7EA5F4   ; ★ 本类 RTTI 表
```

两次写 `+0x0C` 不是笔误：`0x7E1B04`（`GenericList`）是**基类子对象**的表，
`0x7E1AFC`（`List<INISection*>`，即模板派生）是**完整对象**的表。
这与 `0x52ACE0` 的 `GenericList` 构造函数一致（它把 `+0`/`+4`/`+0x10` 三处都写 `0x7E1B04`/`0x7E1B0C`）。

### 1.2 结构

```text
INIClass            (+0x00 vptr = 0x7EA5F4)
  +0x04  unknown_4  (DWORD, 上一节的缓存值；见 §3.2)
  +0x08  unknown_8  (DWORD, 上一节的 INISection* 缓存)
  +0x0C  List<INISection> Sections        ← 30 字节：vptr + First + Last
           +0x0C vptr = 0x7E1AFC (List<INISection*>)
           +0x10 First (GenericNode, 12B)  vptr=0x7E1B0C, Next=+0x14, Prev=+0x18
           +0x1C Last  (GenericNode, 12B)  vptr=0x7E1B0C, Next=+0x20, Prev=+0x24
  +0x28  INISection**  SectionsByHash (排序数组)   ← §3
  +0x2C  int           SectionCount
  +0x30  int           SectionCapacity
  +0x34  bool          SectionIndexDirty     (排序失效标志)
  +0x38  INISection**  SectionIndex          (二分命中缓存)
  +0x3C  DWORD         (析构清零，语义未定 L-24)
  +0x40  bool          Digested   ← 见 §1.3
  +0x41  byte[20]      Digest      ← 见 §1.3

CCINIClass : INIClass     (+0x00 vptr = 0x7E1AF4，单继承，仅覆写表首)
```

### 1.3 为什么 `Digested` 落在 `+0x40`

R-015 按 YRpp 声明顺序算出 `Digested` 在 `+0x40`、`Digest[20]` 在 `+0x41..+0x54`。
R-016 用两个独立事实复核：

1. `CCINIClass` 的析构 `0x0040E4A0` 调 `0x5256F0`（`INIClass` 析构体），后者清到 `+0x3C` 为止；
2. YRpp `CCINIClass()` 内联体第二句是 `Digested = false;`，第三句 `*this = 0x7E1AF4`。

⇒ `+0x40 = bool Digested`、`+0x41 = byte[20] Digest` 与声明顺序自洽。
**但本线未在字节里直接观测到对 `+0x40` 的读写**（构造函数只清到 `+0x3C`，
说明 `Digested` 的清零发生在外面的内联代码里）。故此条标 **推演**，不是实证。

### 1.4 `+0x04/+0x08` 的语义

`GetSection` 把它们当**缓存**用（§3.2）：`+0x08` 存上一次命中的 `INISection*`，
`+0x04` 存上一次查询的哈希。YRpp 命名为 `unknown_4` / `unknown_8`，本线给出用途。
**注意**：这两个 dword 与 `List` 的 `First`/`Last` **无关** —— R-015 把它们读成
「`+0x04`/`+0x08` 是普通 dword（清零）」是对的，但把 `+0x0C` 起的三个 vptr
读成三个独立基类则是错的。

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
- 想动 **`artmd.ini`** ⇒ 用 `0x887180`（直接是对象，`&` 即 this）；
- 两者**不能混**。直接把 `0x887180` 当 rules 用会改到美术定义。

---

## 3. 节查找：CRC32 排序数组 + 二分（R-016 新增）

`GetSection`（`0x526810`）**不遍历** `Sections` 链表。它查的是一个
**按哈希排序的 `{u32 hash, INISection*}` 数组**。

### 3.1 结构

```text
INIClass+0x28  INISection** 或 {hash,ptr} 数组基址
INIClass+0x2C  int            元素个数
INIClass+0x30  int            容量
INIClass+0x34  bool           排序失效（dirty）标志
INIClass+0x38  缓存指针       上一次命中的元素地址
```

每个元素 **8 字节**：`+0x00 = u32 sectionHash`、`+0x04 = INISection*`。
证据：`0x0052B430` 的二分里 `lea edi,[edx+8]` / `lea ecx,[edx+8]`（步长 8），
命中后 `add eax,4` 再 `mov eax,[eax]`（取 `+0x04` 的指针）。

### 3.2 流程

```text
0x00526844  call 0x4A1DE0          ; CRC32(节名) -> edi
0x00526849  mov ecx,[esi+0x2c]     ; count        <- esi = this
0x0052685a  mov eax,[esi+0x38]     ; 缓存元素
0x00526861  cmp [eax],edi          ; 缓存命中？
0x00526865  cmp byte [esi+0x34],bl ; dirty？
0x00526876  call 0x7C8B48          ; 重新 qsort（比较器 0x52B720）
0x00526881  mov byte [esi+0x34],1  ; 标 dirty=1（下次仍需排？见 L-27）
0x00526894  call 0x52B750          ; 二分查找
0x00526921  mov [esi+0x38],edx     ; 更新缓存
0x00526927  add esi,4 ; mov eax,[esi]  ; 返回 section 指针
0x0052690C  mov esi,0xB7882C       ; 未命中的空对象
```

**未命中时返回 `0xB7882C`**（BSS 里的一个共享空对象），不是 NULL。
`0xB7882C` 被 19 处 `.text` 引用，是本类族的**通用"空结果"哨兵**。
⇒ 调用方**不需要判空**，但**需要判"是不是哨兵"**才能区分"节不存在"。

### 3.3 哈希 = 标准 CRC32，**无大小写折叠**

`0x4A1FB0` 是 CRC32 更新步（`not eax` … 查表 … `not eax`），
索引表在 `0x0081F7B4`。本线逐项比对 **全部 256 项**，与标准反射多项式
`0xEDB88320` 生成的表**完全一致**。

`0x4A1DE0` 是它的**分块版本**（先按 4 字节尾数处理，再一次 4 字节一组），
但数学上是同一个 CRC32。

**关键判据**：`0x52B720` 这个比较器**只比首 dword**：

```text
0x0052B720  mov eax,[esp+4]
0x0052B724  mov ecx,[esp+8]
0x0052B728  mov eax,[eax]        ; 元素 A 的 hash
0x0052B72A  mov ecx,[ecx]        ; 元素 B 的 hash
0x0052B72C  cmp eax,ecx
0x0052B72E  jne +3
0x0052B730  xor eax,eax
```

它**不比较节名本身**。而 `GetSection` 命中后**也不做字符串复核**
（`0x00526924` 直接取 `[edi+4]` 返回）。

⇒ **节名比较是大小写敏感的**。`[InfantryTypes]` 与 `[infantrytypes]` 是两个不同的节。

> ⚠ 这是一个**哈希碰撞即误命中**的设计：CRC32 是 32 位，两张不同名字的节
> 若 CRC32 相同，`GetSection` 会把后者的内容当成前者返回。本线**未观察到**
> 引擎对名字做二次复核（`ReadString` 的键查找只比哈希，见 §9.3）。
> 对编译器的意义：**不要依赖碰撞概率**，但也不要假设引擎会帮你消歧。

---

## 4. 读取链

```text
CCINIClass（单份 INI）
  └─ ReadString(节, 键, buf, def, cap)     ; 0x528A10, ret 0x14
        ├─ 0x526810 GetSection(节)          ; CRC32 + 二分
        └─ 在 section->Entries 里线性找键   ; §9
```

`AbstractTypeClass::LoadFromINI`（`0x00410A60`）的 `ecx` 是 **`CCINIClass*`**：

```text
0x00410A69  mov esi, [esp+0x444]   ; 参数 = CCINIClass*
0x00410A72  mov ecx, esi
0x00410A74  call 0x526B00          ; ★ 不是"节名预处理"，是 Reset()（§4.1）
0x00410A9E  mov ecx, esi
0x00410AA0  call 0x528A10          ; ReadString
```

与 R-012 的 `push 0x31 = Name[0x31]`、`push 0x20 = UINameLabel[0x20]` 接得上。

### 4.1 更正：`0x526B00` 是 `Reset()`，不是"节名预处理"

R-015 把它读成"节名预处理"。字节只有三条指令：

```text
0x00526B00  33 C0        xor eax, eax
0x00526B02  89 41 04     mov dword ptr [ecx+4], eax    ; 清 +0x04 缓存
0x00526B05  89 41 08     mov dword ptr [ecx+8], eax    ; 清 +0x08 缓存
0x00526B08  C3           ret
```

YRpp `CCINIClass.h` 记 `Reset() { JMP_THIS(0x526B00); }`。
它是**清空两个查询缓存**（§1.4 / §3.2），不是处理节名。

---

## 5. ⚠ 撤回：`0x7EA624` 不是 `INIClass` 的表（R-016）

R-015 把 `0x7EA624`（`VectorClass<GraphicMenuItem*>`）当成 `INIClass` 实例实际使用的表，
并据此写出 §5 的 7 槽表与「`INIClass : VectorClass<GraphicMenuItem*>`」。

**这条不成立。** 逐条否证：

1. `0x7EA624` 的 `[vt-4]` = COL `0x00802638` → TD `0x00824100` →
   `.?AV?$VectorClass@PAVGraphicMenuItem@@@@`，是**别的类**。
2. `INIClass` 自己的表 `0x7EA5F4` 的 `[vt-4]` = COL `0x00802510` → `.?AVINIClass@@`，
   唯一槽是 `0x004F2810`。**构造函数 `0x535AA0` 末尾写的正是 `0x7EA5F4`**。
3. R-015 引的"构造点 `0x004F2B66`"其实是 **`0x004F2B60` 这个析构函数**
   在卸载 `+0x0C` 标志、释放 `+0x04` 缓冲**之后**恢复基类 vptr 的那一句 ——
   这是析构函数的**回退写**，不是构造函数的**建立写**。
   `0x004F2B60` 的体首就是 `mov eax,[esi+4]` / `test eax,eax` / 按 `+0xD` 标志
   `call 0x7C8B3D`（free）/ 清 `+0xD`,`+8` / `test byte [esp+8],1` 决定是否 free(this) / `ret 4`
   —— 标准**标量删除析构**形态。
4. `INIClass` 的表只有 **1 槽**，`CCINIClass` 的也只有 1 槽。两者都是标量删除析构。
   `.rdata` 里紧邻的下一张表是 `GraphicMenu`，再下一张是
   `DynamicVectorClass<GraphicMenuItem*>`，再下一张才是 `VectorClass<GraphicMenuItem*>` ——
   **4 张表首尾相接**（`0x7EA5F0..0x7EA648`）。

⇒ R-015 §5 的整张表必须作废。**`INIClass` 没有 `VectorClass` 基类**，
它的方法**不是虚函数**（YRpp 里 `GetSection`/`ReadString` 等全是 `JMP_THIS` 普通成员）。

**判据（纪律 #9 的再次应用）**：看到 `mov [reg], <vtable>` 先判**这是构造函数还是析构函数**。
构造函数的特征：后面跟着一串字段清零 + 最后写本类 vptr；
析构函数的特征：前面有字段释放，写 vptr 后紧跟 `test [esp+8],1` / `free(this)`。
两者写 vptr 的动作**字节相同，语义相反**。

---

## 6. 未闭合

| # | 悬项 |
|:--|:---|
| I-1 | ✅ **已闭（R-016）**：`0x526B00` = `Reset()`（§4.1）；`0x526810` = `GetSection()`，CRC32+二分（§3） |
| I-2 | ✅ **部分闭（R-016）**：`INISection` = `0x44`、`INIEntry` = `0x28`（push 立即数实证）；`INIClass` 尾部字段到 `+0x40`；`CCINIClass` 自身**不新增字段** ⇒ 尺寸应 ≥ `0x55`，语料 `0x58` 与之相容但**仍未独立实证**（L-25） |
| I-3 | `0x0089F518` 这个第 6 个静态 `CCINIClass` 是什么 |
| I-4 | ✅ **已闭（R-016）**：见 §9 —— `+0x10`/`+0x1C` 是 `List<INISection>` 的首尾哨兵，不是独立子对象 |
| I-5 | ✅ **已闭（R-016）**：`INIClass` **不继承** `GraphicMenu`（§5 撤回）；`GraphicMenu` 的 7 槽表 `0x7EA5FC` 与本类无关 |
| L-24 | `INIClass+0x3C` 的语义（析构清零，未被本节任何函数读） |
| L-25 | `CCINIClass` 的**独立**实例尺寸实证（需要找 `new(0x58)` 或栈分配点） |
| L-26 | `0x528A10` 的键查找为何走 `0x52B390`（而非 `0x52B430`）；两者差异未定 |

---

## 7. 核验状态

| 结论 | 通道 | 状态 |
|:---|:---|:---|
| `0x7EA5F4` = `INIClass` / `0x7E1AF4` = `CCINIClass`（COL 反查） | 字节 | 单通道字节 |
| 两 RTTI 表各 1 槽（都是标量删除析构） | 字节 | 单通道字节 |
| `CCINIClass` ctor `0x535AA0` 写 `List<INISection*>` @ `+0x0C` + 两哨兵 | 字节（逐指令）+ COL 名 | ✅ 双通道 |
| **`INIClass` 不继承 `VectorClass<GraphicMenuItem*>`**（撤回 R-015） | 字节（ctor 写 `0x7EA5F4` + dtor 判据） | ✅ 双通道，**推翻 R-015** |
| `INISection` = `0x44` / `INIEntry` = `0x28` | 字节（`push 0x44` @`0x525DEA` / `push 0x28` @`0x526039`） | 单通道字节 |
| 节查找 = CRC32 排序数组 + 二分 | 字节（`0x81F7B4` 256 项全等标准表 + `0x52B750` 二分 + `0x52B720` 只比首 dword） | ✅ 双通道 |
| 节名/键名**大小写敏感** | 字节（查找路径无折大小写）+ 上一条 | ✅ 双通道 |
| `0x887180` = `INI_Art`（**不是** rulesmd） | 字节（是 CCINIClass 全局）+ **YRpp `CCINIClass.h:288-296`** | ✅ 双通道，**推翻语料注释** |
| `0x887048` = `INI_Rules` 且是**指针** | YRpp | 社区源（本线未独立复核解引用层级） |

---

## 8. 自纠留痕

（R-015 两次 / R-016 两次，全部保留）

**自纠 1（R-015）：把邻居表当成自己的方法表。**
初稿写"`0x7E1B44` 是 `CCINIClass` 的 7 槽方法表"。
验 `[vt-4]` → COL → `.?AV?$VectorClass@PAVScriptClass@@@@`，与 INI 无关。
错因：我从 RTTI 表头往后找"第一段连续 ≥4 个 `.text` 指针"的 run，
那段 run 恰好紧跟其后，我就默认是同类延续。**没验 COL。**

**自纠 2（R-015）：`0x887180` 是 `INI_Art` 不是 `RULESMD.INI`。**
初稿沿用了语料 `vxl_cache_layout.md:102` 的注释。
YRpp 明确列出 `INI_Art{0x887180}`，`INI_Rules` 是 `0x887048` 且为**指针**。
语料那行注释是推断且错。

**自纠 3（R-016）：撤回「`INIClass : VectorClass<GraphicMenuItem*>`」。**
这是**同一个错误的第三次** —— R-015 §2.3 自己写了纪律 #9
（"`.rdata` 表首尾相接，地址相邻 ≠ 同类"），紧接着在 §5 又犯了。
区别只在于这次错的是**上一张**表（`0x7EA624` 在 `0x7EA5F4` **后面**第三张），
而自纠 1 错的是**下一张**。判据本身没错，是**没有执行**。

**自纠 4（R-016）：撤回「`CCINIClass` 三基类多继承」。**
`+0x0C`/`+0x10`/`+0x1C` 不是三个基类子对象，而是**一个 `List<INISection>` 成员**：
成员自己的 vptr + 首哨兵 + 尾哨兵。判据是 `0x52ACE0`（`GenericList` 构造函数）
对**同一个 30 字节区域**做了完全相同的三次写。
⇒ "看到 3 个 vptr" 不等于 "3 个基类"；必须先问**这块内存属于哪个成员**。

**自纠 5（R-016）：`0x526B00` 不是"节名预处理"，是 `Reset()`。**
R-015 §4 的注释写错了。字节是三条指令（清 `+0x04`/`+0x08`），YRpp 记 `Reset()`。

**纪律 #9**：RTTI 的 `slots` 是记账值，**并且** `.rdata` 里多张表首尾相接。
按槽号遍历必须配"值落 `.text`"判据，且判断归属必须验 `[vt-4]` 的 COL 名。

**纪律 #10**：**社区源（YRpp）与语料注释冲突时，先查 YRpp 的静态地址声明**。
两处地址归属都是 YRpp 对、语料注释错。

**纪律 #11（R-016 新增）**：`mov [reg], <vtable>` 在**构造函数**和**析构函数**里
字节相同、语义相反。判据：
- 构造：后面跟一串字段清零，**最后**写本类 vptr；
- 析构：前面有字段释放，写 vptr 后紧跟 `test byte [esp+8],1` + `free(this)` + `ret 4`。
不判这一步，就会把析构的"vnptr 回退写"读成"构造的建立写"，
进而推出一个根本不存在的继承关系。

**纪律 #12（R-016 新增）**：**"N 个 vptr" ≠ "N 个基类"**。
模板容器（`List<T>`）的实例里就含 1 个容器 vptr + 2 个哨兵节点的 vptr。
归属判据：找该容器的**构造函数**，看它对哪块内存做了同一组写。
`GenericList` = `0x52ACE0`，`List<T>` 沿用同一构造。

**纪律 #13（R-016 新增）**：判"节/键是否存在"时，**命中返回值不是 NULL 而是哨兵**
（`0xB7882C`）。任何"`if (p == NULL)` 判不存在"的写法在本子系统里是**错的**。

---

## 9. `INISection` / `INIEntry` 节点布局（R-016 新增，闭 I-4）

### 9.1 `INISection`（`0x44` = 68 字节）

构造函数在 `0x525DD0`–`0x5261FF` 一带（`0x00525DEA push 0x44` 后 `call 0x7C8E17` 分配）。
vptr `0x7EB73C`，`[vt-4]` → COL `0x00803708` → `.?AUINISection@INIClass@@`。

```text
INISection : Node<INISection*>            ; vptr + Next + Prev = 0x0C
  +0x00  vptr = 0x7EB73C
  +0x04  Node.Next          (GenericNode*)
  +0x08  Node.Prev          (GenericNode*)
  +0x0C  char*              Name           ; 堆副本（0x7D5408 strdup）
  +0x10  List<INIEntry*>    Entries        ; 0x1C: vptr + First(12) + Last(12)
    +0x10  vptr = 0x7EB744
    +0x14  First.vptr = 0x7E1B0C
    +0x18  First.Next
    +0x1C  First.Prev
    +0x20  Last.vptr  = 0x7E1B0C
    +0x24  Last.Next
    +0x28  Last.Prev
  +0x2C  CheckedEntry*      CheckedEntries.Entries   ; 0x14 结构
  +0x30  int                CheckedEntries.Count
  +0x34  int                CheckedEntries.Capacity
  +0x38  byte               CheckedEntries.Unknown_0C
  +0x3C  u32                CheckedEntries.Unknown_10
  +0x40  u32                Unknown_40
  ---   0x44 total
```

| 偏移 | 类型 | 语义 | 证据 |
|:---|:---|:---|:---|
| `+0x00` | vptr | `0x7EB73C` | `0x00525E3E mov [ebx],0x7EB73C` |
| `+0x04` | `GenericNode*` | 继承的 `Node<INISection*>::Next` | `0x00525E16 mov [ebx+4],edi(0)` |
| `+0x08` | `GenericNode*` | `Prev` | `0x00525E19` |
| `+0x0C` | `char*` | `Name`（堆副本，**区分大小写**） | `0x00525E22 mov [ebx+0x0C],eax`，eax=`0x7D5408` 返回 |
| `+0x10` | vptr | `List<INIEntry*>` 成员 vptr = `0x7EB744` | `0x00525E2D mov [esi],0x7EB744`，esi=`ebx+0x10` |
| `+0x14` | vptr | `Entries.First` 哨兵 vptr = `0x7E1B0C` | `0x52ACE0` 同构（`[esi]=0x7E1B0C`，esi=基准+4） |
| `+0x18` | `GenericNode*` | `Entries.First.Next` ← **空表时指向 Last 哨兵** | `0x52ACE0` `[esi+4]=0` |
| `+0x1C` | `GenericNode*` | `Entries.First.Prev` | `0x52ACE0` `[esi+8]=0` |
| `+0x20` | vptr | `Entries.Last` 哨兵 vptr = `0x7E1B0C` | `0x52ACE0`（edx=基准+0x10） |
| `+0x24` | `GenericNode*` | `Entries.Last.Next` | `0x52ACE0` `[edx+4]=0` |
| `+0x28` | `GenericNode*` | `Entries.Last.Prev` | `0x52ACE0` `[edx+8]=0` |
| `+0x2C` | `CheckedEntry*` | `CheckedEntries.Entries` | `0x0052B080`（ecx=`ebx+0x2C`）`[0]=0` |
| `+0x30` | `int` | `CheckedEntries.Count` | `0x0052B080` `[+4]=0`；`GetKeyName` 拿它当上界 |
| `+0x34` | `int` | `CheckedEntries.Capacity` | `0x0052B080` `[+8]=0` |
| `+0x38` | `byte` | `CheckedEntries.Unknown_0C` | `0x0052B080` `byte[+0xC]=0` |
| `+0x3C` | `u32` | `CheckedEntries.Unknown_10` | `0x0052B080` `[+0x10]=0` |
| `+0x40` | `u32` | `Unknown_40` | `0x00525E44 mov [ebx+0x40],ecx` |

**⚠ 内部结构对齐**：`List<INIEntry>` 成员占 `+0x10..+0x27`（vptr 4 + 首哨兵 12 + 尾哨兵 12
= 28 字节 → `0x10+0x1C = 0x2C`）。`CheckedEntryList` 因此**从 `+0x2C` 起**，
与 YRpp 的 `Entries` 后接 `CheckedEntries` 一致。

### 9.2 为什么 `+0x18` 是 `Entries.First.Next`

`GetKeyName`（`0x526CC0`）取键名的路径：

```text
0x00526D40  call 0x52B430        ; 按 hash 取 section（命中返回 section*+0，未命中哨兵）
0x00526D45  mov eax,[eax]        ; 取出 section 指针
0x00526D4F  mov ecx,[eax+0x30]   ; count  = CheckedEntries.Count（键数）
0x00526D52  cmp edx,ecx          ; if (index >= count) return NULL
0x00526D56  mov eax,[eax+0x18]   ; ★ 链表头 = Entries.First.Next
0x00526D5D  mov ecx,[eax+4]      ;   node->Next
0x00526D64  mov esi,[eax+8]      ;   node->Prev
0x00526D78  mov eax,[eax+0x0C]   ; ★ 命中项返回 Key（[node+0x0C]）
```

⇒ **`+0x18` 是 `Entries` 链表的第一个真实节点**（`First.Next`；
空表时指向 `Last` 哨兵 → 循环立即结束）。
**`+0x0C` 就是 `INIEntry::Key`**，与 §9.3 的 `+0x0C = Key` 交叉印证。

`+0x30` 被当作**键总数**上界 ⇒ `CheckedEntries.Count` 与 `Entries` 链表长度同义
（引擎维护两份索引：链表管插入顺序，`CheckedEntries` 管 CRC 校验）。

### 9.3 `INIEntry`（`0x28` = 40 字节）

构造函数在 `0x526039`–`0x5260A8` 一带（`push 0x28` 后 `call 0x7C8E17`）。
vptr `0x7EB734`，`[vt-4]` → COL `0x00803668` → `.?AUINIEntry@INIClass@@`。

| 偏移 | 类型 | 语义 | 证据 |
|:---|:---|:---|:---|
| `+0x00` | vptr | `0x7EB734` | `0x005260A2 mov [esi],0x7EB734` |
| `+0x04` | `GenericNode*` | **继承的 `Node<INIEntry*>::Next`** | `0x00526090 mov [esi+4],0` |
| `+0x08` | `GenericNode*` | `Prev` | `0x00526093` |
| `+0x0C` | `char*` | **`Key`** | `0x00526079 mov [esi+0x0C],eax`，eax=`0x7D5408` 返回 |
| `+0x10` | `char*` | **`Value`** | `0x00526087 mov [esi+0x10],eax`（第二个 strdup） |
| `+0x14` | `char*` | `unknown_14` | `0x00526080 mov [esi+0x14],edx` |
| `+0x18` | `char*` | `unknown_18` | `0x00526096 mov [esi+0x18],eax` |
| `+0x1C` | `DWORD` | `unknown_1C` | `0x00526099 mov [esi+0x1C],ebx` |
| `+0x20` | `DWORD` | `unknown_20` | `0x0052609C mov [esi+0x20],edi` |
| `+0x24` | `DWORD` | `unknown_24` | `0x0052609F mov [esi+0x24],edx` |

YRpp 声明 `Key, Value, unknown_14, unknown_18, unknown_1C, unknown_20, unknown_24` ——
**偏移完全一致**，且 `+0x28` 恰好是分配尺寸边界（7 个 dword 字段全用满）。

`INIEntry` 析构 `0x52AD50` 释放 `+0x0C`、`+0x10`、`+0x14`（链表式逐节点 `free`）、`+0x18`
⇒ `+0x0C/+0x10/+0x14/+0x18` **都是堆分配指针**，`+0x1C/+0x20/+0x24` 是标量。

### 9.4 `List<T>` 的尺寸 = `0x1C`，与 YRpp 完全一致（含一次自纠）

**先记一次自纠**：写这一节时我先算错了 `List<T>` 的尺寸（误按 `0x28` 算），
由此得出"YRpp 与 `push 0x44` 矛盾"的结论。**那个结论是错的**，已撤回。
实际核算如下。

`GenericNode` 有虚析构 ⇒ 每节点 `vptr(4) + Next(4) + Prev(4)` = **`0x0C`**。
`GenericList` 有虚析构 + 两个 `GenericNode` 成员 ⇒ `4 + 0x0C + 0x0C` = **`0x1C`**。
`List<T> : GenericList` **不新增字段** ⇒ 同为 **`0x1C`**。

字节侧完全吻合 `0x52ACE0`（`GenericList` 构造函数）：

```text
esi = eax+0x04             ; First
edx = eax+0x10             ; Last
[esi] = 0x7E1B0C           ; First.vptr
[esi+4] = [esi+8] = 0      ; First.Next / First.Prev
[edx] = 0x7E1B0C           ; Last.vptr
[edx+4] = [edx+8] = 0      ; Last.Next / Last.Prev
[eax] = 0x7E1B04           ; GenericList.vptr
```

用 `0x1C` 复算 `INISection`：

| 区段 | 起点 | 长度 | 终点 |
|:---|---:|---:|---:|
| `Node<INISection*>` 基类 | `+0x00` | `0x0C` | `+0x0C` |
| `Name` | `+0x0C` | 4 | `+0x10` |
| `Entries` (`List<INIEntry*>`) | `+0x10` | `0x1C` | `+0x2C` |
| `CheckedEntries` | `+0x2C` | `0x14` | `+0x40` |
| `Unknown_40` | `+0x40` | 4 | `+0x44` |

⇒ **`0x44`，与 `push 0x44` 逐字节一致。YRpp 的 `INISection` 声明是对的。**

> 顺带一条 **YRpp 自身的小不一致**：它写 `List<INISection> Sections`（非指针），
> 但 RTTI 名字是 `.?AV?$List@PAUINISection@INIClass@@@@`（`PAU` = `INISection*`）。
> 以 RTTI 名为准，元素是指针。


---

## 10. 读族逐键语义（R-017）

编译器的真正问题不是"有哪些函数"，而是"**这个键的值会被解析成什么**"。
本节把**解析规则**逐条钉到字节。

### 10.1 读/写族入口

| VA | 名称 | 调用约定 | 头两字节 |
|:---|:---|:---|:---|
| `0x00528A10` | `ReadString` | `ret 0x14`（5 参） | `83 EC 0C`（`sub esp,0xC`） |
| `0x00528F00` | `ReadUnicodeString` | `ret 0x14` | `B8 14 50 00 00`（`mov eax,0x5014`，0x14KB 栈帧） |
| `0x00529160` | `ReadStringtableEntry` | `ret 0x10` | `81 EC 14 04 00 00`（1KB 栈缓冲） |
| `0x005283D0` | `ReadDouble` | 默认值 8 字节压栈 | `83 EC 0C` |
| `0x005276D0` | `ReadInteger` | `ret 0xC` | `83 EC 0C` |
| `0x005295F0` | `ReadBool` | `ret 0xC` | `83 EC 0C` |
| `0x00528660` | `WriteString` | — | `83 EC 38` |
| `0x00529560` | `WriteBool` | `ret 0xC` | `8A 44 24 0C`（无栈帧） |
| `0x00528E00` | `WriteUnicodeString` | — | `51 53 55 56` |

**读族共享同一前段**：先 `cmp` 参数与 `[this+4]`（上次查询的哈希缓存），
命中就走 `[this+8]` 的缓存节；未命中才 `call 0x4A1DE0` 算哈希再查 `+0x28` 排序数组。
⇒ `+0x04`/`+0x08` 这对缓存**六个读函数都在用**，不是 `GetSection` 独有。

### 10.2 `ReadBool`：只取**首字符**，查 0x2A 项表，三元分派

这是本轮最实用的结论。`ReadBool` **不解析整个字符串**，它只：

```text
0x00529764  mov esi,[esi+0x10]     ; INIEntry->Value
0x0052976B  movsx ecx, byte [esi]  ; ★ 只取第一个字节
0x0052976F  call 0x7C97D3          ; toupper（'a'..'z' -> 减 0x20）
0x00529774  add eax, -0x30         ; index = ch - '0'
0x0052977A  cmp eax, 0x29          ; 越界 -> 返回默认值
0x00529781  mov dl, byte [eax+0x5297B4]   ; ★ 3 元分派类
0x00529787  jmp dword [edx*4+0x5297A8]
```

分派表 `0x5297A8` 三个目标：

| 类 | 目标 | 体 | 语义 |
|---:|---|---|:---|
| 0 | `0x0052979A` | `xor al,al` | **false** |
| 1 | `0x0052978E` | `mov al,1` | **true** |
| 2 | `0x0052974B` | `mov al,[esp+0x28]` | **返回调用方给的默认值** |

类表 `0x5297B4`（42 项 = `'0'..'9'` 加 32 个字母/符号）中只有 **6 项非默认**：

| 字符 | 类 | 结果 |
|:---|:---|:---|
| `0` | 0 | false |
| `1` | 1 | true |
| `F` | 0 | false |
| `N` | 0 | false |
| `T` | 1 | true |
| `Y` | 1 | true |

其余 36 项一律返回默认值。

**对编译器的硬结论**：
- `yes` / `no` / `true` / `false` / `1` / `0` / `Y` / `N` 都能识别（**只认首字母**）；
- **大小写不敏感**（`0x7C97D3` 是 toupper）；
- **`2` 及任何其他首字符 = 取默认值，不是 false** —— 写成 `SomeKey=2` 不会报错，
  会**静默回落到默认值**；
- `ReadBool` 只读首字节，所以 `YesPlease` / `Nonsense` 也按 `Y`/`N` 判 ——
  拼错的词不会报错。

`WriteBool`（`0x529560`）写的是字面量 `"yes"`（`0x825BF8`）/ `"no"`（`0x825BF4`）：
⇒ **读写不同词汇表**。引擎自己写出去的是 `yes`/`no`，但读得懂 `1`/`0`/`T`/`F`。

### 10.3 `ReadInteger`：看**末字符**，`h` 后缀 = 十六进制

```text
0x00527877  mov edi,edx
0x00527879  or ecx,-1 / xor eax,eax / repne scasb   ; strlen
0x00527882  dec ecx
0x00527883  movsx edx, byte [ecx+edx-1]  ; ★ 取最后一个字节
0x00527889  call 0x7CAFF4                ; tolower（'A'..'Z' -> 加 0x20）
0x00527891  cmp eax, 0x68                ; == 'h' ?
0x00527894  jne 0x5278BA                 ; 否 -> strtol
0x0052789E  push 0x825BB4 ; "%xh"        ; 是 -> sscanf(value, "%xh", ...)
0x005278BE  call 0x7C9BFD                ; strtol(Value)
```

⇒ **`Key=100h` 是十六进制 0x100，不是 100**。`Key=0x100` 也能被 `%xh` 接受。
后缀判定**大小写不敏感**（tolower 后比 `'h'`），`100H` 同样生效。

### 10.4 `ReadDouble` / Unicodes

- `ReadDouble`（`0x5283D0`）默认值是 8 字节实参，YRpp 用 `PUSH_VAR64` 压栈，返回在 ST0。
- `ReadUnicodeString`（`0x528F00`）**栈帧 0x5014 字节**（约 20KB），比 `ReadString` 大得多
  ⇒ 它内部把整个值缓冲下来做转义解码后再写调用方缓冲。
- `ReadStringtableEntry`（`0x529160`）栈帧 `0x414`（1KB），先读 ANSI 再查
  CSF 字符串表转成宽字符。

### 10.5 复跑

`python re_atlas/tools/dump_ini_readers.py`（`evidence/ini_readers.txt`）。
工具含**正对照**：先验 `ReadString@0x00528A10` 头三字节是 `83 EC 0C`，
不成立就直接判"VA 映射错、以上全部作废"。
`ReadInteger` 的窗口从 `0x527877` 起 —— 那是 `ReadInteger` 体内一个真实跳转目标；
从 `0x527878` 起会从指令中间反汇编出伪指令 `cli`（本轮实测踩到，已改）。

---

## 11. 键 → 字段映射（R-018）：`AbstractTypeClass::LoadFromINI`

编译器最终要回答的是"**这个键写进去，落在哪个字段**"。本节把
`AbstractTypeClass::LoadFromINI`（`0x00410A60`）的映射钉到字节。

### 11.1 ⚠ `+0x24` 既是 `ID` 又是**节名**

这是本节最重要的一条，也是"照着 YRpp 写结构体"会踩到的坑：

```text
0x00410A79  lea ebp, [ebx+0x24]    ; ebp = this->ID
0x00410A7E  push ebp               ; ★ 节名 = this->ID
0x00410A7F  call 0x526810          ; GetSection(this->ID)
```

`+0x24` 是 `char ID[0x18]`（YRpp `AbstractTypeClass.h`），**同时**被当作
`GetSection` 的节名实参。

⇒ **节头与对象 ID 是同一串字节。** 编译器生成 `[MTNK]` 时，
实例化出来的对象 `ID` 就是字符串 `"MTNK"`；**不能**让节头写显示名而另存一个 id。

`+0x60` 的 `UIName`（宽字符指针）才是显示名，由 `UIName` 键经 CSF 解析后填入。

### 11.2 两个键的完整映射

`LoadFromINI` 只读 **2 个键**（`ReadString` 只被调两次，`0x410AA0` / `0x410AFB`）：

| 键 | 目标字段 | 上限 | 证据 |
|:---|:---|:---|:---|
| `Name` | `this+0x64` | **`0x31`（49）** | `0x00410A91 lea edi,[ebx+0x64]` / `0x00410A94 push 0x31` / `0x00410A98 push "Name"` |
| `UIName` | `this+0x3D` | **`0x20`（32）** | `0x00410AEB lea ebp,[ebx+0x3D]` / `0x00410AEE push 0x20` / `0x00410AF5 push "UIName"` |

`UIName` 读完后再经 `0x734E60` 解析成宽字符指针，写入 `this+0x60`：

```text
0x00410B3C  mov al,[ebp]           ; UINameLabel[0] 非空？
0x00410B42  je 0x410B68            ; 空 -> 跳过
0x00410B50  mov ecx,ebp
0x00410B52  call 0x734E60          ; 解析 CSF
0x00410B58  mov [ebx+0x60],eax     ; ★ UIName = 解析结果
```

`0x734E60` 在**全局 CSF 表未初始化**时返回常量 `0x84583C`（不是 NULL）——
与 §3.3 的哨兵风格一致。

### 11.3 字段边界（含对齐）

按 YRpp 声明顺序**朴素相加**会把 `Name` 算到 `+0x61`，但字节实测是 `+0x64`。
差的 3 字节是 `UINameLabel[0x20]` 结束于 `+0x5D` 之后、`wchar_t*` 的 4 字节对齐填充：

| 偏移 | 字段 | 尺寸 |
|:---|:---|---:|
| `+0x24` | `ID` | `0x18` |
| `+0x3C` | `zero_3C` | 1 |
| `+0x3D` | `UINameLabel` | `0x20` |
| `+0x5D` | **（对齐填充）** | **3** |
| `+0x60` | `UIName`（`wchar_t*`） | 4 |
| `+0x64` | `Name` | `0x31` |
| `+0x95` | —（本类结束） | |

⇒ **`AbstractTypeClass` 尾部到 `+0x95`**。工具用"算式 vs 字节观测"对照做校验，
不一致会直接打印 mismatch。

> 这正是 R-012 纪律 #"派生类核基类先减前缀"的同一类问题：**声明顺序不等于字节偏移**，
> 编译器插入的对齐填充在头文件里看不见。

### 11.4 复跑

`python re_atlas/tools/dump_ini_keymap.py`（`evidence/ini_keymap.txt`）。
双正对照：`LoadFromINI@0x00410A60` 头 6 字节 `81 EC 34 04 00 00`，
以及键字面量 `0x00817854 == "Name"`；任一不成立即判 VA 映射错、结果作废。

---

## 12. 全引擎 键 → 读取点 索引（R-019）

### 12.1 规模

`AbstractTypeClass::LoadFromINI` 只读 2 个键，剩下的钥匙面在别处。
本线把**所有** INI 读取入口的调用点扫了一遍（`.text` 线性全扫）：

| 读取器 | 调用点数 |
|:---|---:|
| `ReadBool` `0x5295F0` | 207 |
| `ReadInteger` `0x5276D0` | 141 |
| `ReadString` `0x528A10` | 112 |
| `ReadDouble` `0x5283D0` | 16 |
| `GetSection` `0x526810` | 1 |
| `ReadStringtableEntry` `0x529160` | 1 |
| `ReadUnicodeString` `0x528F00` | **0** |
| **合计** | **478** |

其中 **473 个**调用点的键字面量被恢复出来，覆盖 **427 个不同键**。

**`ReadUnicodeString` 零调用点** —— 它是 `CCINIClass` 的公开方法但引擎自己不用它。
对编译器的含义：写 `ReadUnicodeString` 风格的转义值（`\uXXXX`）不会天然生效，
除非某个 loader 自己调它。

### 12.2 未恢复的 5 个点（全是真实原因，非工具缺陷）

| 调用点 | 读取器 | 原因 |
|:---|:---|:---|
| `0x00410A7F` | `GetSection` | 键是 `lea ebp,[ebx+0x24]`（`ID` 字段地址），非立即数 |
| `0x0041B164` | `ReadString` | 键在寄存器里（先 `call 0x526CC0` 取键名） |
| `0x0044F88F` | `ReadString` | 同上 |
| `0x0041F4D2` | `ReadString` | 键在 **BSS** 的字符串缓冲（`0x889F64`） |
| `0x0041F5B9` | `ReadString` | 同上 |

⇒ 前三条是**按变量名查键**（先取键名再读值），后两条是**键名本身存在 BSS**。
这两类在静态分析里无法还原成字面量，属**结构性不可还原**，不是漏扫。

### 12.3 格式化的键：`PowerUp%01dYSort`

有 **6 个**读取点共用键字面量 `"PowerUp%01dYSort"`（`0x8194D4`），全在同一个函数
（~`0x0045FE50`）。`%01d` 说明**键名是运行期拼出来的**：

```text
Key = sprintf("PowerUp%01dYSort", n)   ; n = 0..9
```

⇒ 这类键在 INI 里写作 `PowerUp0YSort` … `PowerUp9YSort`。
**编译器生成 INI 时不能按字面量 `PowerUp%01dYSort` 写** —— 要展开成 10 个实键。

同理需要留意任何键名里带 `%` 的项（本索引里只有这一处）。

### 12.4 被多处读取的键（10 个）

`Description` / `DoubleThick` / `Elasticity` / `Flat` / `Image` / `PowerUp%01dYSort` /
`Shadow` / `SpawnDelay` / `ToTile` / `Trailer`

⇒ 这些键**由多个不同 loader 各自读一遍**，改一处不影响另一处。
典型是 `artmd.ini` 与 `rulesmd.ini` 里有同名键、各自由不同类消费。

### 12.5 复跑

`python re_atlas/tools/dump_ini_keyindex.py`（`evidence/ini_keyindex.txt`，1419 行）。
正对照：`Name` / `UIName` 必须各恰好 1 处且落在 `0x00410A60`，
外加字面量 `0x00817854 == "Name"`；任一不成立即判索引不可信。

**工具方法论**（本轮踩过并修好）：函数起点必须来自**一次从 `.text` 首字节开始
的线性扫描**，边扫边记录"上一条 `ret` 之后第一个非 nop 指令"。
从 `call_va - N` 这种任意偏移起反汇编会产出伪指令
（实测 `les edx, ptr [ecx*4 - 0x179bdbb4]`），首版因此丢了 42 个点里的键。
