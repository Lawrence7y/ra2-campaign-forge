# R2-2：INI 子系统 —— `INIClass` / `CCINIClass` 骨架 [实证]

更新：2026-10-22（R-015 初版 / R-016 重写 §1、§5 并新增 §9 / … / R-028 §19 / **R-029 §20 结题总览**）

R2-2 的第一篇。目标：给 `ra2forge` 战役编译器一条可查询的 INI 读取链骨架。
**R-029 起结题（见 §20）：核心闭环完成，此后只按需补充，不再开 INI 新轮。**

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
| **`RulesClass` 实例尺寸** | **`0x18C0`** | `push 0x18C0`@`0x0052BABE` → `new` → 构造器 `0x665650`；字段上界 `+0x18BC` + 4B 尾隙（§15.2） |
| **`[MultiplayerDialogSettings]` 27 键字段表** | `+0x1480` 起 11 dword，`+0x14AC` 起 16 byte，**60 字节无空洞** | 双向一致 27/27（§15.1） |
| **载入后镜像到全局** | **18 个字段**有镜像全局；**9 个没有** | 18 条 `mov [全局],reg`@`0x52D149..0x52D22C`（§15.3） |
| **`ShadowGrow`** | 27 键里**唯一读点为 0**（区间 `[0,0]`，两口径皆零） | disp32 在 `.text` 只出现 3 次（构造器 1 + 读取器 2）（§15.4） |
| **`[AudioVisual]` 字段布局** | **151/152 键已解出**（`Smoke` 一键两字段） | 双向一致 151/151（§16） |
| **`[General]` 字段布局** | **268 标量字段**（279 键，零凭空多出，12 个列表型） | 双向一致；函数体 18,782 字节（§17） |
| **全引擎键索引** | **2,426 调用点 / 2,305 键 / 1,893 不同键**（旧值 478/473/427 **作废**） | `E8` 字节扫描与指令扫描逐址相等（§12.0） |
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

> **R-020 异族核验更新**：八条结论已交多通道独立复核（见 §7.1），
> **确认 3 票 / 推翻 0 票 / 无法核 0 票**，无一条翻案。
> 但见 §7.2 的边界说明 —— 有效票只来自 2 个模型家族，且任务书含锚定，
> 不能当作最强证据等级。

| 结论 | 通道 | 状态 |
|:---|:---|:---|
| `0x7EA5F4` = `INIClass` / `0x7E1AF4` = `CCINIClass`（COL 反查） | 字节 | 单通道字节 |
| 两 RTTI 表各 1 槽（都是标量删除析构） | 字节 | 单通道字节 |
| `CCINIClass` ctor `0x535AA0` 写 `List<INISection*>` @ `+0x0C` + 两哨兵 | 字节（逐指令）+ COL 名 | ✅ 双通道 |
| **`INIClass` 不继承 `VectorClass<GraphicMenuItem*>`**（撤回 R-015） | 字节（ctor 写 `0x7EA5F4` + dtor 判据） | ✅ **已核验**（3 票确认，**推翻 R-015**） |
| `INISection` = `0x44` / `INIEntry` = `0x28` | 字节（`push 0x44` @`0x525DEA` / `push 0x28` @`0x526039`） | ✅ **已核验**（3 票确认，见 §7.1） |
| 节查找 = CRC32 排序数组 + 二分 | 字节（`0x81F7B4` 256 项全等标准表 + `0x52B750` 二分 + `0x52B720` 只比首 dword） | ✅ **已核验**（3 票确认，见 §7.1） |
| 节名/键名**大小写敏感** | 字节（查找路径无折大小写）+ 上一条 | ✅ **已核验**（3 票确认，见 §7.1） |
| `0x887180` = `INI_Art`（**不是** rulesmd） | 字节（是 CCINIClass 全局）+ **YRpp `CCINIClass.h:288-296`** | ✅ 双通道，**推翻语料注释** |
| `0x887048` = `INI_Rules` 且是**指针** | YRpp | 社区源（本线未独立复核解引用层级） |
| `0x4F2B60` 是**析构函数**，非构造函数（`ret 4` + 条件 `free(this)`） | 字节 + 3 票异族复核 | ✅ **已核验** |
| `0x526B00` 是 `Reset()`，清 `+0x04`/`+0x08` 两缓存（非"节名预处理"） | 字节 + 3 票异族复核 | ✅ **已核验** |
| 节未命中返回**哨兵 `0xB7882C`** 而非 NULL | 字节（19 处引用）+ 3 票异族复核 | ✅ **已核验** |

---

### 7.1 异族复核记录（R-020）

跑次 `dwfrun-3a210def-635b-42dd-bbd4-d6b60447e0bb`（前身 `dwfrun-b287db93`，
因两条 dfmodel 通道反复重连而 amend 剔除，已完成部分全部从缓存取回）。

**任务书**：每个通道独立跑 python + capstone 直读 `gamemd.exe`，逐条判定八条结论，
用纯文本协议 `VERDICT <n>: <CONFIRMED|REFUTED|UNVERIFIABLE> -- <证据>` 作答，
脚本侧正则解析。

| 通道 | 模型家族 | 解析到的判定数 |
|:---|:---|---:|
| `new-provider-3/qoder-cn:qfmodel` | 千问 | **8** |
| `new-provider-3/wb-global:deepseek-v4.1-flash` | DeepSeek | **8** |
| `new-provider-3/wb-cn:deepseek-v4.1-flash` | DeepSeek | **8** |
| `new-provider-3/qoder-global:qfmodel` | 千问 | **0（未按协议作答）** |
| `new-provider-3/qoder-global:dfmodel` | DeepSeek | 剔除（反复重连） |
| `new-provider-3/qoder-cn:dfmodel` | DeepSeek | 剔除（反复重连） |

**计票（八条全部）**：确认 **3** / 推翻 **0** / 无法核 **0**。

**确定性闸门**：脚本先本地跑 `python re_atlas/tools/dump_ini_nodes.py`，
退出码 **0**，且正对照 `control OK` 命中 —— 这一项是机器判定，不靠模型自述。

**报告产物**：`artifact "verification"`（《R-016 异族复核报告》，964 B）。

### 7.2 ⚠ 这次核验的边界（不得夸大）

必须记清楚三条限制，否则会把"3 票确认"当成比它实际更强的证据：

1. **只有 2 个模型家族，不是 4 个。** 有效票来自千问 ×1 与 DeepSeek ×2，
   同一家族内的两条通道共享训练分布，**不构成家族间互证**。
2. **任务书把"预期证据"写进去了。** 例如第 1 条的说明里直接给了
   "应在 `0x525DD0-0x5261FF` 找 `push 0x44`"，这是**锚定**。
   模型据此去验证很自然会确认 —— 它证明的是"这些字节确实在那里"，
   而**不是**"我给的解读是唯一合理解读"。
3. **一个通道协议失败（0 条判定），两条通道未参与。**
   六条通道里只有三条产出了可用票。

⇒ 结论的等级：**"字节可复现性得到了异族独立确认"**，不是
"解读的穷尽性得到了独立证明"。凡涉及"这条路径之外还有没有别的情况"
（例如 §3.3 的哈希碰撞是否真的会发生），本轮核验**没有覆盖**。

**仍未核验的**：~~§10 的 `ReadBool`/`ReadInteger` 解析规则（R-017）~~
**已闭（R-030，见 §10.6：异族盲验 + 机器门禁，1 子句推翻已更正）**；
§11 的键→字段映射（R-018）、§12 的键索引（R-019）尚未派复核。

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
0x00527851  cmp byte [edx], 0x24         ; ★ 首字符 '$' 先判（R-030 新证）
0x00527861  call 0x7CA530                ; $ 分支：sscanf(value, "$%x", &out)
0x00527877  mov edi,edx
0x00527879  or ecx,-1 / xor eax,eax / repne scasb   ; strlen
0x00527882  dec ecx
0x00527883  movsx edx, byte [ecx+edx-1]  ; ★ 取最后一个字节
0x00527889  call 0x7CAFF4                ; tolower（'A'..'Z' -> 加 0x20）
0x00527891  cmp eax, 0x68                ; == 'h' ?
0x00527894  jne 0x5278BA                 ; 否 -> 十进制回退
0x0052789E  push 0x825BB4 ; "%xh"        ; 是 -> sscanf(value, "%xh", ...)
0x005278BE  call 0x7C9BFD                ; 1 参转发 -> 0x7C9B72 = **atoi**
```

⇒ **`Key=100h` 是十六进制 0x100，不是 100**。后缀判定**大小写不敏感**
（tolower 后比 `'h'`），`100H` 同样生效。

**R-030 更正（异族盲验 + 字节复算，见 §10.6）**：

| 原表述 | 更正 | 依据 |
|:---|:---|:---|
| "`Key=0x100` 也能被 `%xh` 接受" | **错**。`0x100` 末字节是 `'0'` 不是 `'h'`，走不进 `%xh` 分支 | `D4/D12` @0x527891/0x527894 |
| 回退"走 `strtol`" | **`atoi` 语义**：`0x7C9B72` 单参（无 base/无 endptr），体是 `and 4` 判数字 + `lea ebx,[esi+eax*2-0x30]` 的 10 倍累加 + `-` 取负；体内**无** `'x'/'X'` 比较 ⇒ **认不出 `0x` 前缀** | `D8/D11/D12` |
| 无 | 新证：**首字符 `$` ⇒ 十六进制**（`sscanf` 格式串 `"$%x"` @`0x825BB8`），先于 h 后缀判定 | `D9/D10` @0x527851–0x527861 |

⇒ 编译器口径修正：`Key=0x100` **解析成 0**（atoi 在 `'x'` 处停），
`Key=$100` 与 `Key=100h` 才是 256。这是 R-017 唯一被推翻的子句。

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

### 10.6 §10 的核验状态（R-030）

- **机器门禁**：`tools/verify_r017_claims.py` —— sha256 门禁 G0 +
  **53 条断言全过**（A: 9 入口头/ret/六读者共用 `+4/+8` 缓存；
  B: ReadBool 首字符链 10 断言；C: WriteBool 词汇表；D: ReadInteger 三链 12 断言；
  E: 哈希路 `0x4A1DE0`；NEG: 类表翻转/跳转表改指/无关函数前缀/**sha 门禁活性**）。
  证据表 `evidence/r017_verify.txt`。
- **异族盲验**：千问（qfmodel，先独立 capstone 推导、后读断言集）
  **18 CONFIRMED / 0 REFUTED / 1 UNVERIFIABLE**，
  报告 `evidence/r017_crosscheck_qwen.md`。那 1 条 UNVERIFIABLE（"`0x100` 也接受"）
  由本线字节判定**推翻并就地更正**（见 §10.3 表；机制静态可判：末字节非 `'h'`）。
- 附带新证（两族独立见到）：`$` 前缀分支、`0x7CAFF4` 是 **tolower**
  （`dump_ini_readers.py` 旧 docstring 误写 toupper，正文 §10.3 原就正确）。
- 陷阱入册 **G-36**（见 CONFLICTS）。

⇒ **§10 定为「已核验」**（执行者 R-017，核验者=千问 qfmodel 异族盲验 + 本线机器门禁，
家族不同）。子句级更正 1 条已施加。

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

### 11.5 §11 的核验状态（R-031，进行中）

- **机器门禁已绿**：新增 `tools/verify_r018_claims.py` —— sha 门禁 +
  **21 断言全过**（负控 5 组：dst 改位 / cap 改位 / 键字面量改指 / 无关站点 /
  sha 活性），证据 `evidence/r018_verify.txt`。§11.1/11.2/11.3 全部字节钉死。
- **异族盲验在飞**：GLM 5.3 独立推导 §11 后打分（报告
  `evidence/r018_r019_crosscheck_glm.md`，运行中）。
- ⇒ 本节**暂标「机器门禁 PASS，异族待回」**；异族回来后升「已核验」或按判定更正。

---

## 12. 全引擎 键 → 读取点 索引（R-019，R-023 全面重算；R-031 定稿）

> **⚠ R-031 定稿：本节的「键」列换了口径（2026-10-22）**
>
> 下面 12.0–12.5 的 2,305 / 1,893 / 164 / 121 是 **M1** 口径的产物：
> M1 = 「调用点之前最近的一条可打印字符串字面量 push」。它回答的是
> **「这个调用附近有没有字符串字面量」**，不是 **「这个调用传的键是什么」**。
>
> 按 ABI 事实（键固定占参数槽：六个读取器取**倒数第 2 个** push，
> `GetSection` 取**最后 1 个**）重算，另用栈模型（`pop` / `add esp,N` /
> `leave` / `mov esp,X` 回收槽位后该 push 作废）独立复算；**两条规则在
> 2,426 个站点上零分歧**。定稿数字见 **§12.7**。M1 的老数字保留在
> 12.0–12.5，但只作「字面量出现在范围内的站点数」使用，
> **不得再当作键数引用**。
>
> 一次实质语义更正：**全引擎 2,023 个字面量键里没有一个含 `%`**；
> 所有 `%` 串都是**模板**（见 §12.3、§12.7）。

### 12.0 整节被重算 —— 旧数字全部作废

本节 R-019 公布的「478 个调用点 / 473 个恢复键 / 427 个不同键」**是错的**，
成因不是方法论失误而是**工具静默截断**：

> `md.disasm(.text 全段)` 在 `0x46F5A0` 停止。那里是一张**跳转表**
> （`49 00 c5 e4 46 00 04 e6 46 00 …`，前面是一整片 `04` 字节表），
> capstone 拒绝把它解成指令，于是**一次调用只覆盖了 `.text` 的前 9%**
> （155,215 条 / 全段 138 万余条），却返回成功、不报错。
>
> 我把同一段代码当成"线性全扫"写进了上一版 KB。**这是本轮最严重的一次自纠**：
> 结论的数字不是偏小，而是判据本身只在 9% 的样本上成立。

修法与验收见 §15。新旧对比：

| 项 | 旧（截断） | 新（全段 + 审计重同步） |
|:---|---:|---:|
| 读取器调用点 | 478 | **2,426** |
| 恢复出键字面量的点 | 473 | **2,305** |
| 不同键 | 427 | **1,893** |

**独立复核**：另外写了一个**纯字节 `E8` 扫描**（不解码任何指令，只按
`e8 rel32` 算目标地址），得到 **2,426** 个调用点，与指令扫描**逐址相等、
零差异**。这条对账现在是工具的硬正对照，两侧任何一侧漏检都会红。
（旧的正对照要求 `Name`/`UIName`「恰好 1 处」—— 那个 1 处恰是截断后剩下的唯一
一处，等于**把 bug 校准成了正确答案**。已改判据。）

### 12.1 各读取器的调用点数（全段实测）

| 读取器 | 调用点数 |
|:---|---:|
| `ReadInteger` `0x5276D0` | 757 |
| `ReadBool` `0x5295F0` | 651 |
| `ReadString` `0x528A10` | 650 |
| `ReadDouble` `0x5283D0` | 306 |
| `GetSection` `0x526810` | 54 |
| `ReadUnicodeString` `0x528F00` | 5 |
| `ReadStringtableEntry` `0x529160` | 3 |
| **合计** | **2,426** |

`ReadUnicodeString` 旧记录是「零调用点」，**已推翻**：实际有 5 处。
它确实是 `CCINIClass` 的公开方法，但引擎自己也在用。

### 12.2 未恢复键字面量的点（121 处）

> **⚠ R-031 定稿废止本小节的数字**：下面的 `121 = register 55 / bss_key 59 /
> unknown 7` 来自 M1 口径，三个桶不对应任何 ABI 量。键槽口径下**真值是 217**
> （寄存器/缓冲 210 + 空槽 7），见 §12.7.2。本节保留作过程记录，
> 三类**成因**的描述（键在寄存器 / 键在 BSS / 键是字段地址）仍然成立。

2,426 − 2,305 = 121 处调用点没恢复出键。当前分档（`evidence/ini_keyindex.txt`）：
`register` 55 / `bss_key` 59 / `unknown` 7。原因分三类，全部是**结构性不可还原**：

| 类型 | 说明 |
|:---|:---|
| 键在寄存器 | 先 `call 0x526CC0`（`GetKeyName`）取键名，再读值 —— 按变量名查键 |
| 键在 BSS | 键名本身由运行期写进 BSS 缓冲（如 `0x889F64`） |
| 键是字段地址 | `lea ebp,[ebx+0x24]`（`ID` 字段地址）当键名传 |

静态分析无法把这三类还原成字面量。**编译器不能假设「索引里没有 = 引擎不读」。**

> **⚠ R-031 补**：还有一**反方向**的问题 —— M1 归属规则（"函数起点到调用点之间
> 最后一个 `.rdata` 字面量 push"）有两面：
> 1. **模板键**（键槽=寄存器指向 sprintf/CString 构造缓冲）：M1 记的格式串
>    （`'%d'`@`0x691908`、`'Tile%02dAnim'`@`0x546524`…）归属**成立**，但键名是
>    运行期拼的 —— 本质属上面「键在寄存器」类，只是 M1 把模板记成了"键"。
>    实证链：`0x5464F5 lea eax,[esp+0x18C]`→sprintf→`0x546505 lea edx,[esp+0x188]`
>    （esp 平移后**同一绝对地址**）→`push edx` 进键槽。
> 2. **真误归属**：`'D:\ra2mdpost\Scenario.CPP'`@`0x686ED0` —— NAME 槽是
>    `push eax`（`[0xA8B230]+0x125C` 运行期缓冲），而断言串 `0x83D838` 在
>    **51 条指令前被 `0x734E60`（CSF/断言助手，带行号 `0xC5F`）消费掉**，
>    被 M1 错挂到本调用 ⇒ 该点被**错记为已恢复**，真身是类「键在 BSS」。
> ⇒ **「121 处未恢复」是下界**（每坐实一处类 2，+1）；模板键在 2,305 里合法。
> 样本与机制全录 `evidence/r031_pctkey_mechanism.md`；全量 M2 清点由异族
> 盲验对照（GLM，进行中，报告 `evidence/r018_r019_crosscheck_glm.md`）。

### 12.3 格式化的键：`PowerUp%01dYSort`

键名带 `%` 的项在全段索引里仍只有这一处（6 个读取点，同一函数 ~`0x0045FE50`）：

```text
Key = sprintf("PowerUp%01dYSort", n)   ; n = 0..9
```

⇒ INI 里写作 `PowerUp0YSort` … `PowerUp9YSort` 十个实键。
**编译器不能按字面量写 `PowerUp%01dYSort`。**

> **⚠ R-031 更正（本条"只有一处"被推翻）**：当前证据文件里**含 `%` 的"键"有
> 21 个不同键 / 34 个站点**，两类（详见 §12.2 补注与
> `evidence/r031_pctkey_mechanism.md`）：
> 1. **模板键**（多数）：归属成立、但**不是可照抄的字面量** —— 键名运行期拼，
>    静态段须展开（`PowerUp%01dYSort` 的同类还有 `Tile%02dAnim`×5、
>    `EliteStage%d`、`EliteWeapon%d`、`%sBarrelLength` 等 15+ 个）。
> 2. **真误归属**（确证 1 处）：`'D:\ra2mdpost\Scenario.CPP'` 属 §12.2「键在 BSS」
>    被 M1 错挂；全量清点进行中。
> ⇒ 模板键现象**远比"只有一处"广**；`PowerUp%01dYSort` 本身仍成立。
> **编译器不能按字面量写任何含 `%` 的键。**

> **★★ R-031 定稿（2026-10-22，本条最终结论）**：上一段仍把模板叫「键」，
> 措辞保留但**结论收紧**。按 ABI 键槽口径复算：
> **2,023 个不同字面量键里，含 `%` 的有 0 个。**
> 21 个 `%` 串 / 34 个站点**全部落在「键槽是寄存器」那一档**（§12.7 的
> (1a) 类）—— 也就是说：它们无一例外都是**运行期拼键用的格式模板**，
> 而 M1 把模板记成了键。
>
> ⇒ 对编译器的规则简化成一句：**这个索引里任何含 `%` 的串都不许当键写进 INI。**
> 不是「21 个特殊」，而是**全部都是模板**。
> `PowerUp%01dYSort` 的十个真键是 `PowerUp0YSort`…`PowerUp9YSort`；原结论成立。
> 复跑：`python re_atlas/tools/r031_authoritative_numbers.py`（断言
> `no literal KEY contains '%'`，17/17 PASS）。

### 12.4 被多处读取的键

> **⚠ R-031 定稿：本小节数字与结论双双翻案。** 键槽口径下是 **137** 个
> 键被多处读取（不是 164），而头部高频项**不是** `Name`/`UIName`/`Armor`
> 那些 —— 它们只有 3–7 处；多读的本质是**多个不同 loader 共用键名**，
> 不是「每个 `TypeClass` 派生各读一遍」。见 §12.7.5。

全段重算后是 **164 个**键被多处读取（旧记录 10 个）。完整清单在
`evidence/ini_keyindex.txt` 的「汇总」段。头部高频项为
`Name` / `UIName` / `Image` / `Cameo` / `Armor` / `Cost` / `Strength` /
`TechLevel` / `Range` / `ROF` / `Speed` / `Power` 等 —— 这些是**每个
`TypeClass` 派生类各自读一遍**，改一处不影响另一处。

### 12.5 复跑与判据

```bash
python re_atlas/tools/dump_ini_keyindex.py     # evidence/ini_keyindex.txt
```

正对照（三项全过才算可信）：
1. **`E8` 字节扫描 == 指令扫描，逐址相等**（当前 2426 == 2426，零差异）；
2. `Name` / `UIName` 的读取点里各至少 1 处属 `LoadFromINI`（`0x00410A60`）；
3. 调用点总数 ≥ 2000（防再次静默截断）。

### 12.6 工具方法论（本轮踩过并修好的三件事）

1. **函数起点**必须来自一次带审计重同步的全段扫描，边扫边记录「上一条 `ret`
   之后第一个非 nop 指令」。从 `call_va - N` 这种任意偏移起反汇编会产出伪指令。
2. **段扫描不能只调一次 `disasm`**。必须分块或重同步，且**每一处跳过都要打印**。
3. **正对照不能拿被怀疑对象自身校准**。「恰好 1 处」这种期望值若来自截断结果，
   它校验的是 bug 而不是实现。

### 12.7 ★ R-031 定稿：按 ABI 键槽重算的权威数字（2026-10-22）

本节是 §12 的**结论口径**。12.0–12.6 的数字是 M1 口径的过程记录，
保留可追溯，但对外引用一律用本节。

**判据**：七个读取器的键占固定参数槽 —— 六个读取器**倒数第 2 个 push**、
`GetSection` **最后 1 个 push**。两种独立实现必须一致：

- **规则 B（位置法）**：函数头以来的全部 push 里取该槽；
- **规则 C（栈模型）**：逐条跟踪 `esp`，`pop` / `add esp,N` / `leave` /
  `mov/lea esp,X` 回收槽位后，该槽的 push 作废。

⇒ **B 与 C 在 2,426 个站点上零分歧**（`r031_authoritative_numbers.py`
断言 `rule B == rule C at every site`，17/17 PASS，EXIT=0）。
这是本节所有数字的内部双算。

#### 12.7.1 键槽性质（替代 §12.1 的「恢复键」栏）

| 读取器 | 站点 | 键是字面量 | 键在寄存器/缓冲 | 无活动槽 |
|:--|--:|--:|--:|--:|
| `ReadInteger` `0x5276D0` | 757 | 732 | 23 | 2 |
| `ReadBool` `0x5295F0` | 651 | 647 | 4 | 0 |
| `ReadString` `0x528A10` | 650 | 514 | 131 | 5 |
| `ReadDouble` `0x5283D0` | 306 | 305 | 1 | 0 |
| `GetSection` `0x526810` | 54 | 3 | 51 | 0 |
| `ReadUnicodeString` `0x528F00` | 5 | 5 | 0 | 0 |
| `ReadStringtableEntry` `0x529160` | 3 | 3 | 0 | 0 |
| **合计** | **2,426** | **2,209** | **210** | **7** |

字面量键总体：**2,209 站点 / 2,023 不同键 / 137 个键被多处读取**。

#### 12.7.2 「未恢复」的真值 = 217，不是 121

`210 + 7 = 217` 个站点的键不是字面量（寄存器/缓冲，或槽内根本没有 push）。
§12.2 的 `121 = register 55 + bss_key 59 + unknown 7` 及其「是下界」的措辞
**作废** —— 那三个桶不对应任何 ABI 量。真正的结构性边界是 **217**，
且它不是下界而是键槽口径下的定值（字面量就是没有，运行期才有）。

#### 12.7.3 「含 `%` 的键」= 0 个（语义新发现）

2,023 个字面量键里**含 `%` 的有 0 个**。21 个 `%` 串 / 34 个站点
**全部**属于上面「键在寄存器」档，是**运行期拼键的格式模板**，被 M1 记成键。
详见 §12.3 的 R-031 定稿段。

#### 12.7.4 M1 的 340 个错站，按成因拆开

| 成因 | 站点 | 含义 |
|:--|--:|:--|
| (1a) 键槽是寄存器 | **91** | 键真在运行期拼；M1 记下的是附近模板或更早被消费的串 |
| (1b) 键槽空 | **5** | M1 记的串在此调用根本不是参数 |
| (2) 键槽是**另一个**字面量 | **244** | M1 抓到的是**节名/文件名**（比键更靠近调用）|

成因 (2) 的高频项正是节名 —— `General` 57、`Basic` 38、`MultiPlayer` 21、
`RandomMap` 20、`Lighting` 20、`Header` 12、`Options` 11、`Video` 10、
`SerialDefaults` 10、`WOnline` 9。这是「节名在键之后压栈」的指纹，
与异族盲验独立得到的结论一致。

⇒ 读 M1 索引时必须先过这一条：**若某键的「读取点」里节名占了多数，
那些点是 M1 抓错，不是引擎真在读该键。**

#### 12.7.5 §12.4「164 个多处读取」→ 137，且结论翻转

多读键的真实高频是普通共享键，不是「每个 `TypeClass` 派生各读一遍」：
`Name` 7、`Height` 5、`Description` 5、`Type` 5、`Normalized` 4、`Damage` 4、
`Warhead` 4、`Image` 4、`TechLevel` 4。`Name`/`UIName` 只有 3–7 处，
**不是**每派生类一处 —— 因为 §11.1 的「记录 ID 当节名」机制替代了它。

#### 12.7.6 `ReadDouble` 的「1 vs 68」已撤回

LEDGER §4b 记的「本线 1 / GLM 68 ⇒ def64 占位口径分歧」**是误读，已撤回**。
两个数出自**同一份报告的两条规则**：1 = 规则 B（全部 push 取槽），
68 = 规则 A（只取**尾部连续** push 串取槽，中间任何 `mov` 都打断参数列表）。
`r031_finalise_rules.py` 一次跑出两者：`ReadDouble` B 字面 305/寄存器 1，
A 字面 235/寄存器 68。⇒ **跨家族在 ReadDouble 上根本没有分歧**，
A 是弱规则，不需要统一 def64 口径。

#### 12.7.7 2,305 vs 2,275（30 站点差）为何不裁胜负

三种窗口起点都测过：跳过 `nop` 与跳过 `nop/int3/null` **结果字节级相同**
（均 2,305）⇒ padding 集不是成因；「最近**已校验** `ret` + 前向解码必须落在
本调用」得 1,960（159 站点压根锚不上，太严）。而不校验的 `C3` 字节扫描更糟：
**2,426 个站点里有 2,071 个**在函数头到调用之间的**非指令边界**上存在
`C3`/`CB` 字节（共 81,743 个），例如 `0x41CC5C` 处的那个字节其实是
`mov ecx,ebx` 的 modrm 尾字节。

⇒ **30 站点差是窗口起点的算法产物，两个数都不是语义量。**
这正是本节必须改用 2,209/2,023/137 的理由；M1 的 2,305/2,275 只可说成
「范围内存在可打印字面量 push 的站点数」。

#### 12.7.8 复跑与负控

```bash
python re_atlas/tools/r031_authoritative_numbers.py   # 17/17 PASS, EXIT=0
python re_atlas/tools/r031_finalise_rules.py          # 11/11 PASS, EXIT=0
python re_atlas/tools/r031_esp_slot_adjudicate.py     # 6/7（唯一红是我写错的断言）
python re_atlas/tools/r031_m1_window_diag.py          # padding 集对照
python re_atlas/tools/r031_origin_adjudicate.py       # 窗口起点对照
python re_atlas/tools/r031_ret_boundary_test.py       # 伪 ret 普查
```

负控：sha 门禁活性（原版副本哈希不同）；真键站点 `0x410AA0` = `Name`
在每条规则下都仍是字面量；已知误归属 `0x686ED0` 在任何规则下都**不**成为
字面量；把槽号强改成 `-3`，`ReadBool` 计数立刻变；`GetSection` 用错槽号
从 3 掉到 0。

证据全文：`evidence/r031_section12_restatement.md`。

#### 12.7.9 诚实边界

- 7 个「无活动槽」站点已计数，但未逐个解释。
- 规则 C 只跟 `push/pop/add/sub/leave/mov/lea`。用 `enter` 建帧、或
  `mov esp,<寄存器>` 会按「帧重置」处理 —— 对**槽位存活**判断正确，
  但绝对深度值此时只是近似；本批没有站点依赖绝对深度。
- 21 个 `%` 模板是**本索引里 M1 归过字面量的那批**，因此是模板数的**下界**，
  不是全引擎格式化键的普查。
- `PowerUp%01dYSort` 的 `n = 0..9` 循环上界仍未追（异族判 UNVERIFIABLE）。

---

## 13. `RulesClass` 的节表与载入顺序（R-021）

R2-2 的下一块：`rulesmd.ini` 由谁读、按什么顺序读。这两件事都在字节里。

### 13.1 节名指针表 `0x007F0C78`

一张 4 字节步长的 `const char*` 表，31 项：

```text
0x7F0C78 SpecialWeapons      0x7F0C8C ElevationModel   0x7F0CA0 MultiplayerDialogSettings
0x7F0C7C AudioVisual         0x7F0C90 WallModel        0x7F0CA4 Maximums
0x7F0C80 CrateRules          0x7F0C94 Colors           0x7F0CA8 InfantryTypes
0x7F0C84 CombatDamage        0x7F0C98 ColorAdd         0x7F0CAC Countries
0x7F0C88 Radiation           0x7F0C9C General          0x7F0CB0 VehicleTypes
...（0x7F0CB4 AircraftTypes / 0x7F0CB8 Sides / 0x7F0CBC SuperWeaponTypes /
0x7F0CC0 BuildingTypes / 0x7F0CC4 TerrainTypes / 0x7F0CC8 Teams /
0x7F0CCC SmudgeTypes / 0x7F0CD0 OverlayTypes / 0x7F0CD4 AI / 0x7F0CD8 Powerups /
0x7F0CDC IQ / 0x7F0CE0 JumpjetControls / 0x7F0CE4 Movies /
0x7F0CE8 AdvancedCommandBar / 0x7F0CEC MultiplayerAdvancedCommandBar /
0x7F0CF0 ButtonList）
```

### 13.2 函数 → 节名（36/38 恢复）

**从代码里读出来**，不按函数名推断。三种存储形态：

| 形态 | 例 | 含义 |
|:---|:---|:---|
| `indirect` | `mov eax,[0x7F0C94]` | 节名指针存在上表里 |
| `direct` | `push 0x83D0DC` | 节名字符串地址直接压栈 |
| `table-base` | `mov esi,0x839D68; mov eax,[esi]` | 指标组数组，取 `[0]` |

| 函数 | 节名 | 形态 |
|:---|:---|:---|
| `Read_SpecialWeapons` | `SpecialWeapons` | indirect |
| `Read_AudioVisual` | `AudioVisual` | indirect |
| `Read_CrateRules` | `CrateRules` | indirect |
| `Read_CombatDamage` | `CombatDamage` | indirect |
| `Read_Radiation` | `Radiation` | indirect |
| `Read_ElevationModel` | `ElevationModel` | indirect |
| `Read_WallModel` | `WallModel` | indirect |
| `Read_Colors` | `Colors` | indirect |
| `Read_ColorAdd` | `ColorAdd` | indirect |
| `Read_General` | `General` | indirect |
| `Read_MultiplayerDialogSettings` | `MultiplayerDialogSettings` | indirect |
| `Read_Maximums` | `Maximums` | indirect |
| `Read_InfantryTypes` | `InfantryTypes` | indirect |
| `Read_Countries` | `Countries` | indirect |
| `Read_VehicleTypes` | `VehicleTypes` | indirect |
| `Read_AircraftTypes` | `AircraftTypes` | indirect |
| `Read_Sides` | `Sides` | indirect |
| `Read_SuperWeaponTypes` | `SuperWeaponTypes` | indirect |
| `Read_BuildingTypes` | `BuildingTypes` | indirect |
| `Read_TerrainTypes` | `TerrainTypes` | indirect |
| `Read_Teams_obsolete` | `Teams` | indirect |
| `Read_SmudgeTypes` | `SmudgeTypes` | indirect |
| `Read_OverlayTypes` | `OverlayTypes` | indirect |
| `Read_Animations` | `Animations` | **direct** |
| `Read_VoxelAnims` | `VoxelAnims` | **direct** |
| `Read_Warheads` | `Warheads` | **direct** |
| `Read_Particles` | `Particles` | **direct** |
| `Read_ParticleSystems` | `ParticleSystems` | **direct** |
| `Read_AI` | `AI` | indirect |
| `Read_Powerups` | `Powerups` | indirect |
| `Read_LandCharacteristics` | `Clear` | table-base |
| `Read_IQ` | `IQ` | indirect |
| `Read_JumpjetControls` | `JumpjetControls` | indirect |
| `Read_Movies` | `Movies` | indirect |
| `Read_AdvancedCommandBar` | `AdvancedCommandBar` | indirect |
| `Read_File` | `ColorAdd`（**见 §13.4**） | indirect |

**两个未恢复（结构性，非工具缺陷）**：

- `Read_Difficulty`（`0x66D270`）：节名是**参数**（`edx`），体内没有字符串，直接进 `GetSection`。
  它由 `Read_Difficulties` 用 `Easy` / `Normal` / `Hard` 三个键名各调一次。
- `Read_Difficulties`（`0x674500`）：本身不含 `GetSection`/`GetKeyCount` 调用，
  只是把三个键名转发给 `Read_Difficulty`。

### 13.3 ⚠ `Read_AdvancedCommandBar` 读的是 `AdvancedCommandBar`，但同表还有一项

> **★★ R-021 核验（2026-10-22）：本小节结论被推翻一半，且更重要的那半是反的。**
> 字节事实：`0x7F0CEC` 在全镜像里**恰有 1 处引用**，
> `0x0067465E mov edi,[0x7f0cec]` —— 就在 `Read_AdvancedCommandBar`（`0x674650`）体内，
> 与 `0x00674666 mov edi,[0x7f0ce8]` 成对，由**一个布尔参数**选择：
>
> | 参数 | 用哪个节 | 调用点 |
> |--:|:--|:--|
> | `1` | `MultiplayerAdvancedCommandBar` | `0x00668F81` |
> | `0` | `AdvancedCommandBar` | `0x00668F96` |
>
> ⇒ ❶ 「MP 那项没被任何 `Read_*` 当**首节名**」这个**字面**说法成立；
> ❷ 但「它因此没被用」**不成立** —— 它是该 reader 的**第二个**节，靠参数选。
> ❸ **分支条件与结果**（`0x668F6A` 起，`[0xA8B238]` = `GameMode`）：
>
> | `GameMode` | 含义 | 参数 | 读的节 |
> |--:|:--|--:|:--|
> | 0 | Campaign | 0 | **`AdvancedCommandBar`** |
> | 3 | LAN | 1 | `MultiplayerAdvancedCommandBar` |
> | 4 | Internet | 1 | `MultiplayerAdvancedCommandBar` |
> | 5 | Skirmish | 0 | **`AdvancedCommandBar`** |
>
> ⇒ **单机（战役 / 遭遇战）读的是 `AdvancedCommandBar`；联机（LAN/Internet）
> 才读 `MultiplayerAdvancedCommandBar`。**
> 即「MP 节是联机专用」这个直觉**成立** —— 但它是**字节推出来的**，
> 不是靠"函数名/节名"猜的；而且 §13.3 原文把它说成"没人用"是错的
> （它被读，只是不在单机路径上）。
>
> **本条自纠**：本节首次追记时我把方向写反了（说"战役/遭遇战读 MP 节"）。
> 错误来源：只看两条 `je` 都跳向 `0x668F90` 就下了结论，**没有把
> `0x668F90` 那条路径的参数（`xor eax,eax` → `push 0`）与 F3 的判据
> （`test al,al / jne` → **参数非 0 才用 MP 节**）串起来**。
> 是异族盲验抓到的，本地门禁当时只断言"存在门控"（断言太弱）。
> 现 `verify_r021_claims.py` 按 GameMode 逐个断言映射，防止回潮。
>
> 边界：本节只证「**读**了」，未证读入的值**是否在单机被应用**。

指针表里 `0x7F0CE8 = "AdvancedCommandBar"`、`0x7F0CEC = "MultiplayerAdvancedCommandBar"`。
`Read_AdvancedCommandBar` 的首节用的是 **`0x7F0CE8`（`AdvancedCommandBar`）**。
`MultiplayerAdvancedCommandBar` 这一项**没有被任何 `Read_*` 当作首个节名** ——
但它不是没人用：见上面的核验框，它由参数选为第二个节（联机路径）。

⇒ 函数名里的 "CommandBar" 与节名不完全对应，**不要按函数名猜节名**。

### 13.4 `Read_File` 真正枚举的 7 个节（R-021 实测，非"首引用"）

`Read_File`（`0x668BF0`）不是只处理一个节。到它的第一个 `ret` 为止，
体内引用 **7 个节名 + 3 个难度键名**：

| 顺序 | 节 | 引用地址 |
|---:|:---|:---|
| 1 | `ColorAdd` | `0x7F0C98`（**但先 `call Read_Colors`**，见下） |
| 2 | `Countries` | `0x7F0CAC` |
| 3 | `OverlayTypes` | `0x7F0CD0` |
| 4 | `SuperWeaponTypes` | `0x7F0CBC` |
| 5 | `Warheads` | `0x83A0D0`（direct） |
| 6 | `SmudgeTypes` | `0x7F0CCC` |
| 7 | `TerrainTypes` | `0x7F0CC4` |
| — | `Easy` / `Normal` / `Difficult` | `0x818134` / `0x81BB60` / `0x83A0C4`（**键名**，非节名） |

**`Read_File` 的第一个动作是 `call 0x66D3A0`（即 `Read_Colors`）**：

```text
0x00668BFD  push esi
0x00668BFE  call 0x66D3A0      ; Read_Colors
0x00668C03  mov eax,[0x7F0C98] ; 之后才用 ColorAdd
```

⇒ `Read_File` **不是**"只读 ColorAdd"；它先转调 `Read_Colors`，
再逐个枚举上表 7 个节，末尾处理三档难度。
本表 §13.2 里 `Read_File → ColorAdd` 那一行应读作"首个 `GetSection` 用的节"，
**不是**"它的全部职责"。

**方法学**：这一条是"第一个 X"型判据的典型翻车点 ——
工具返回的是"体内第一个节名引用"，而我最初把它当成了"这个函数处理哪个节"。
两者不是一回事：前者是**实现细节**，后者是**职责**。

### 13.5 载入顺序（R-021 二次更正）

**⚠ 本节第一版是错的，已撤回。** 第一版把 `Init` 用 0x1600 的窗口扫描，
越界读进了紧邻的 `Read_File`，于是把 28 个 `Read_*` 调用全算到 `Init` 头上。
按 `ret` 边界重划后真实结构如下。

**`Init`（`0x6686C0`–`0x668BE5`，`ret 4`）只做三件事**：

```text
0x00668A27  call Read_File      ; 第 1 份 INI
0x00668B05  call Read_File      ; 第 2 份
0x00668BAA  call Read_File      ; 第 3 份
```

⇒ 与 YRpp 的注释吻合：**`Init` 对第一份 INI 调一次，`Read_File` 对后续
（gamemode / map）再调两次**。`Init` **不直接调任何 `Read_*`**。

**`Read_File`（`0x668BF0`–`0x668F8D`，`ret 4`）才是那 28 个 loaders 的容器**，
顺序如下（后读覆盖先读）：

> **★★ R-021 核验（2026-10-22）：上句的范围与「28」都要改。**
> `Read_File` 有**分离冷块**：体内两条 `je` 跳出首 `ret` 的边界 ——
> `0x00668F71 je 0x668F90`、`0x00668F76 je 0x668F90`；冷块从 `0x668F90` 起，
> 到 `0x00668FA2 c2 04 00`（`ret 4`）结束，紧接 `Read_SpecialWeapons`（`0x668FB0`）。
> ⇒ **真范围 `0x668BF0–0x668FA3`**，不是到 `0x668F8D`。
> ⇒ 下表「28 个 loader 调用」里第 28 项 `Read_AdvancedCommandBar`（`0x668F81`）
> 是**主路径**那次；冷块里还有**第 29 次调用**（`0x00668F96`，参数 `0`）。
> 即 **29 次调用 / 28 个不同 loader**（`Read_AdvancedCommandBar` 调两次）。
> 方法学教训见 §13.7 第 5 条：**函数范围不能用「首个 `ret`」定**。

| # | 调用点 | loader |
|--:|:---|:---|
| 1 | `0x00668BFE` | `Read_Colors` |
| 2 | `0x00668CDE` | `Read_Sides` |
| 3 | `0x00668E78` | `Read_BuildingTypes` |
| 4 | `0x00668E80` | `Read_VehicleTypes` |
| 5 | `0x00668E88` | `Read_AircraftTypes` |
| 6 | `0x00668E90` | `Read_InfantryTypes` |
| 7 | `0x00668E98` | `Read_Animations` |
| 8 | `0x00668EA0` | `Read_VoxelAnims` |
| 9 | `0x00668EA8` | `Read_Particles` |
| 10 | `0x00668EB0` | `Read_ParticleSystems` |
| 11 | `0x00668EB8` | `Read_JumpjetControls` |
| 12 | `0x00668EC0` | `Read_MultiplayerDialogSettings` |
| 13 | `0x00668EC8` | `Read_AI` |
| 14 | `0x00668ED0` | `Read_Powerups` |
| 15 | `0x00668ED8` | `Read_LandCharacteristics` |
| 16 | `0x00668EE0` | `Read_IQ` |
| 17 | `0x00668EE8` | `Read_General` |
| 18–20 | `0x00668F02` / `0x00668F14` / `0x00668F26` | `Read_Difficulty` **×3** |
| 21 | `0x00668F2E` | `Read_CrateRules` |
| 22 | `0x00668F36` | `Read_CombatDamage` |
| 23 | `0x00668F3E` | `Read_Radiation` |
| 24 | `0x00668F46` | `Read_ElevationModel` |
| 25 | `0x00668F4E` | `Read_WallModel` |
| 26 | `0x00668F56` | `Read_AudioVisual` |
| 27 | `0x00668F5E` | `Read_SpecialWeapons` |
| 28 | `0x00668F81` | `Read_AdvancedCommandBar`（参数 `1` → MP 节，**联机** GameMode 3/4）|
| 29 | `0x00668F96` | `Read_AdvancedCommandBar`（参数 `0` → `AdvancedCommandBar`，**冷块内**，单机 GameMode 0/5）|

**对编译器有实际意义的两点**：

1. **`Read_File` 会被调三次**（`Init` 里）。所以同一套节会被解析三遍，
   后一遍覆盖前一遍 ⇒ **想覆盖某个值，可以放到后面的 gamemode/map INI 里**。
2. **`Read_General` 在 `Read_Difficulty`（×3）之前**，
   而 `Read_Difficulty` 的三次调用对应三个难度档位。

### 13.6 复跑

`python re_atlas/tools/dump_rules_sections.py`（`evidence/rules_sections.txt`）。
正对照四项：`Read_Colors→Colors`、`Read_General→General`、`Init` 头 6 字节
`81 EC D0 00 00 00`、指针表非空项 ≥28。任一不成立即判不可信。

**本轮工具自纠四次**（全部留痕）：
1. 首版 `op_str.startswith("dword ptr [")` —— capstone 把目标操作数写在**逗号之后**
   （`'eax, dword ptr [0x7f0c94]'`），于是 0/37 命中。
2. 次版只认"首个可打印字符串" —— `Read_Difficulty` 解成 `'FirePower'`、
   `Read_LandCharacteristics` 解成 `'Hover'`，两者都是**键名**不是节名。
3. 三版加白名单过滤 —— 直压型节名（`Animations` 等）不在指针表里，被白名单全砍掉，
   且让扫描器**回退到相邻的、恰好在表里的字符串**，产出更隐蔽的假答案。

4. **四版：窗口 0x1600 扫 `Init`，把紧邻的 `Read_File` 整个吞了** ——
   `Init` 真实长度只有 `0x526`，窗口是它的三倍。产出的"载入顺序"读起来完全合理
   且不违反 YRpp 注释，**单看输出看不出错**；只有数 `ret` 才发现
   `Init` 其实只调 `Read_File` ×3。改为显式 `[lo, hi)` 区间（见 §13.5）。

最终判据：**锚定 `GetSection`/`GetKeyCount` 调用，取其前最后一个可解析字符串**；
`min_len` 从 3 降到 **2**（否则 `AI`/`IQ` 两个两字符节名永远找不到）；
函数体用**由 `ret` 确定的显式区间**，不用窗口大小。

### 13.7 R-021 机器核验（2026-10-22）：30/30 PASS，推翻 2 条 + 纠正 1 条

`python re_atlas/tools/verify_r021_claims.py`（EXIT=0）。
确认 12 条、推翻 2 条、纠 1 条交接件错误；证据
`evidence/r021_section13_verification.md`。要点：

1. **确认面**：指针表 31 项、28 调用序列逐位、`Init` 只调 `Read_File`×3、
   `Read_File` 首动作是 `call Read_Colors`、`Read_General` 在三个
   `Read_Difficulty` 之前、两处结构性未恢复、`Warheads` 直压 —— 全成立。
2. **推翻「`Read_File` 到 `0x668F8D`」**：有分离冷块，真范围到 `0x668FA3`（§13.5 框）。
3. **推翻「MP 节没人用」**：`0x7F0CEC` 有 1 处引用，且由
   `GameMode∈{0,5}` 门控 —— **单机/遭遇战读的就是它**（§13.3 框）。
4. **纠正交接件 H-014**：第三个难度键是 **`Difficult`**（`0x83A0C4`），不是 `Hard`。
   H-014 还留着已撤回的「`Init` 的 32 个内部调用」。**两处都已就地追记。**
5. **方法学教训（本线第 39 条坑）**：
   - **函数范围不能用「首个 `ret`」定** —— 分离冷块会让首 `ret` 提前收边界；
     必须**把体内所有跳出边界的跳转都列出来**，再据跳转目标补解。
   - **补解冷块时不能从「首 `ret` 的下一字节」起**：`0x668F8D` 处解码会把
     `c2 04 00` 当成冷块的 `ret`，于是**正好复现旧错误边界**。
     必须**从跳转目标（`0x668F90`）起**解。这一坑让首版核验器自证"通过"。
   - **「没有被当作首节名」≠「没有被用」**。首节名是一个位置，职责是另一个
     问题 —— 与 §13.4 记的"第一个 X"是同一类错误，这次栽在"唯一一个"上。
   - **全段 `md.disasm` 的截断坑在本节又犯了一次**：核验器里对全 `.text`
     查 `0x7F0CEC` 引用，用单次 `disasm` 只解 155,215 条 ⇒ 假报 0 引用。
     修法：跨度 > 0x10000 一律走 `text_sweep.sweep()`。

---

## 14. 逐 loader 的键清单（R-022，R-023 重算）

`Read_File` 那 38 个 loader 各自读哪些键 —— 这是"要生成一份合法 rulesmd.ini，
每个节必须写什么"的直接答案。

### 14.0 整节被重算 —— 旧数字作废

R-022 公布的 **306 键**是错的，两处系统性低估叠加：

| 缺陷 | 影响 |
|:---|:---|
| **窗口 `0x1000` 太窄** | 4 个 loader 的函数体长达 6–10 KB，键清单被腰斩且**无任何提示**：`Read_AI`、`Read_AudioVisual`（`0x6691E0`→首个 `ret` 在 `0x66B8EE`，**10 KB**）、`Read_CombatDamage`、`Read_General` |
| **键提取口径错** | 原实现收集函数体内**所有**字面量 `push`，既不区分哪次调用，也把参数、节名、委托节名一并算进键 |

修正后的口径：**每次读调用取它自己那个键**（`push 默认值; push KEY; push 节; call`），
且只认参数表已知的 6 个读取器。

| 指标 | 旧（R-022） | 新（R-023） |
|:---|---:|---:|
| 恢复到的字面量键 | 306 | **651** |
| `Read_General` 一个 loader | 14 | **279** |
| `Read_AudioVisual` | （截断） | **152** |
| `Read_AI` | （截断） | **52** |

**最强的一条交叉验证**：`Read_MultiplayerDialogSettings` 用**完全不同的两种方法**
各解一遍 —— 本工具的「读调用实参」与 §15 的「结构体存回偏移」——
**27 个键名逐名相等**。这条现在是硬正对照。

### 14.1 总量与两种形态

| 指标 | 值 |
|:---|---:|
| 恢复到的字面量键 | **651** |
| 有字面量键的 loader | 19 |
| **枚举键名 / 按键名注册**的 loader | **20** |
| **无字面量键**的 loader | **19** |

**关键认知**：**大多数 loader 不读固定键**。
它们先用 `GetKeyCount`（`0x5295F0` 附近）数出节里有多少键，
再用 `GetKeyName`（`0x526CC0`）逐个取**键名**，把键名本身当作数据
（类型名 / 阵营名 / 动画名）。所以：

> **`[VehicleTypes]`、`[BuildingTypes]`、`[Sides]` 等节的内容就是名字列表，
> 键名即数据，没有"字段"可言。**

⇒ 对编译器：这些节要生成成 `名字=值` 或 `名字=`（值可空）的列表，
**键名必须是合法的类型/阵营标识**，值的内容大多被忽略。

### 14.2 读固定键的 15 个 loader（全表）

| loader | 键数 |
|:---|---:|
| `Read_General` | **279** |
| `Read_AudioVisual` | **152** |
| `Read_CombatDamage` | 71 |
| `Read_AI` | 52 |
| `Read_MultiplayerDialogSettings` | 27 |
| `Read_Difficulty` | 12 |
| `Read_IQ` | 11 |
| `Read_CrateRules` | 10 |
| `Read_Radiation` | 9 |
| `Read_LandCharacteristics` | 8 |
| `Read_SpecialWeapons` | 7 |
| `Read_JumpjetControls` | 7 |
| `Read_ElevationModel` | 3 |
| `Read_WallModel` | 2 |
| `Read_Maximums` | 1 |
| **合计** | **651** |

**`[General]` 一个节就占 279 个键**（43%）—— 它是 rulesmd.ini 里最大的节，
不是"边角设置"。`[AudioVisual]` 152 个次之。**编译器必须优先覆盖这两个节。**

**`Read_MultiplayerDialogSettings` 的 27 个键**（遭遇战设置，完整，与 §15 的
结构偏移表**逐名相等**）：

```text
MinMoney / Money / MaxMoney / MoneyIncrement      ← 起始资金
MinUnitCount / UnitCount / MaxUnitCount           ← 单位数
TechLevel / GameSpeed / AIDifficulty / AIPlayers
BridgeDestruction / ShadowGrow / Shroud / Bases / TiberiumGrows / Crates
CaptureTheFlag / HarvesterTruce / MultiEngineer
AlliesAllowed / AllyChangeAllowed / ShortGame / SuperWeaponsAllowed
BuildOffAlly / FogOfWar / MCVRedeploys
```

> **`ShortGame` 在列表里**，读取点 `0x671EA0`，载入后镜像到全局 `0x00A8B262`（§15.3）。

### 14.3 无字面量键的 loader（生成的 INI 必须按社区文档补全）

19 个，其中 14 个是"列出类型名"型（`[VehicleTypes]` 等），另 5 个是
`Read_AdvancedCommandBar` / `Read_Colors` / `Read_ColorAdd` /
`Read_ParticleSystems` / `Read_Particles` 等按键名注册型。

⇒ **工具只覆盖字面量键**。凡需要"某节里有哪些合法键"的完整清单，
必须结合社区文档（rulesmd.ini 注释 / ModEnc），本表只保证
"这些键确实被这个函数读"。

### 14.4 复跑

`python re_atlas/tools/dump_rules_keys.py`（`evidence/rules_keys.txt`）。
三项正对照：`Read_AI` 的字面量键含 `BuildConst`、
`Read_Sides` 被判为"枚举键名"形态、字面量键总数 ≥100。

**一处判据修正**：初版把**节名本身**也当成了键
（`Read_VoxelAnims` 列出 `VoxelAnims`、`Read_Warheads` 列出 `Warheads`）——
因为这两个函数把节名以字面量压栈给 `GetKeyCount`。
已按"字符串 == 本节节名则排除"过滤（只做全等，不做包含），
键数 311 → **306**。

---

## 15. `RulesClass` 字段布局与镜像全局（R-023）

这是编译器把 `[MultiplayerDialogSettings]` 写对位置的最后一环。

### 15.1 27 个键 → 结构偏移（双向一致）

每个键在读取器里出现**两次**：一次作为默认值载入（`mov reg,[esi+off]`），
一次作为结果存回（`mov [esi+off],eax/al`）。两者必须相等 —— 这是**免费的内部
一致性检查**，不一致就说明解析错位。27/27 全部一致。

| 键 | 偏移 | 读法 | 构造器默认值 |
|:---|:---|:---|---:|
| `MinMoney` | `+0x1480` | ReadInteger | `0x9C4` (2500) |
| `Money` | `+0x1484` | ReadInteger | `0x2710` (10000) |
| `MaxMoney` | `+0x1488` | ReadInteger | `0x2710` (10000) |
| `MoneyIncrement` | `+0x148C` | ReadInteger | `0x64` (100) |
| `MinUnitCount` | `+0x1490` | ReadInteger | `1` |
| `UnitCount` | `+0x1494` | ReadInteger | `10` |
| `MaxUnitCount` | `+0x1498` | ReadInteger | `0x14` (20) |
| `TechLevel` | `+0x149C` | ReadInteger | `10` |
| `GameSpeed` | `+0x14A0` | ReadInteger | `6` |
| `AIDifficulty` | `+0x14A4` | ReadInteger | `1` |
| `AIPlayers` | `+0x14A8` | ReadInteger | `1` |
| `BridgeDestruction` | `+0x14AC` | ReadBool | `1` |
| `ShadowGrow` | `+0x14AD` | ReadBool | `0` |
| `Shroud` | `+0x14AE` | ReadBool | `1` |
| `Bases` | `+0x14AF` | ReadBool | `1` |
| `TiberiumGrows` | `+0x14B0` | ReadBool | `1` |
| `Crates` | `+0x14B1` | ReadBool | `1` |
| `CaptureTheFlag` | `+0x14B2` | ReadBool | `0` |
| `HarvesterTruce` | `+0x14B3` | ReadBool | `0` |
| `MultiEngineer` | `+0x14B4` | ReadBool | `0` |
| `AlliesAllowed` | `+0x14B5` | ReadBool | `0` |
| `ShortGame` | `+0x14B6` | ReadBool | `0` |
| `FogOfWar` | `+0x14B7` | ReadBool | `0` |
| `MCVRedeploys` | `+0x14B8` | ReadBool | `1` |
| `SuperWeaponsAllowed` | `+0x14B9` | ReadBool | `1` |
| `BuildOffAlly` | `+0x14BA` | ReadBool | `1` |
| `AllyChangeAllowed` | `+0x14BB` | ReadBool | `1` |

**布局**：`+0x1480..+0x14AB` 是连续 11 个 dword（11 keys × 4 = 44 字节），
`+0x14AC..+0x14BB` 是连续 16 个 byte（16 keys × 1 = 16 字节），
合计 **60 字节，无空洞**。

**注意 `+0x1494` 与 `+0x1498` 之间不存在「`MaxUnitCount` 是 `+0x1499`」的
变体** —— 三个 unit 相关键（`MinUnitCount`/`UnitCount`/`MaxUnitCount`）
是三个独立 dword，不是打包结构。

### 15.2 构造器与实例尺寸

- **构造器**：`0x00665650`，`ret` 在 `0x00667A26`（1,621 条指令、986 个不同偏移）
- **实例尺寸**：`0x18C0`（6,336 字节）
  - 分配点在 `0x0052BABE`：`push 0x18C0` → `call 0x7C8E17`（`operator new`）
    → `call 0x665650`（构造器）→ `mov [0x8871E0], eax`
  - **构造器最高字段止于 `+0x18BC`**（`+0x18B8` 起 4 字节）；`0x18C0 − 0x18BC = 4`
    字节尾隙，符合 4 字节对齐
- **`0x008871E0`** 就是这个 `RulesClass*` 全局（1,423 处引用）

⇒ 尺寸、构造器、全局三者互相钉死，任何一项单独看都可能是巧合。

### 15.3 载入后镜像到全局（★ 编译器必须知道）

`Read_MultiplayerDialogSettings` 返回后，同一个函数立刻把 **18 个字段拷贝到
独立全局变量**，而游戏其余部分**大多读全局，不读 `RulesClass` 字段**。

> **★★ R-023 核验（2026-10-22）：本节三条要改，一条要加。**
>
> 1. **函数边界太短**：本节原写「载入函数 `0x52CD70` 到 `0x52D30C`，最后 `ret` 在
>    `0x52D30B`」。实际 `0x52D277: jle 0x52d30c` 从函数内部**跳过尾部冷块**，
>    冷块（`0x52D30C..0x52D42F`，仍在读 `[0x8871E0]`）属同一函数，
>    真尾是 `0x52D42F` 的 `ret`，函数止于 **`0x52D430`**（比原记长 **292 字节**）。
>    判据只能是**从入口做跳转闭包**，不能是「找最后一条 `ret`」。
> 2. **「载入后只写一次」不成立**：排除载入块与 ModemGst 块后，18 个全局**每一个**
>    仍被别处写入，最少 2 处、合计 **208 处**。它们是**可被运行期覆写的工作变量**，
>    不是冻结的镜像。⇒ 想稳定改，必须改**源头**（INI 或那份设置结构），
>    只改全局会在下一次 UI/会话刷新时被写回。
> 3. **存在第二个成批写入点**（原文完全没提）：`ModemGst.cpp` 的函数 **`0x5B67F0..0x5B6CC6`**
>    内，`0x005B69E4` 一带写同一组全局中的 **17 个**（缺 `CaptureTheFlag`），
>    源结构在 `[ebx+0x7E]..[ebx+0xA3]`，紧邻调试字符串
>    `Decoding game options\n`（`0x82C7A4`）与 `Scenario has changed\n`（`0x82C78C`）。
>    这是**会话/网络房间设置包**的解码路径，与 `RulesClass` 无关。
> 4. **`0x463Axx` 的 `[ebp+0x1488..]` 写入不是 `RulesClass`**：该区引 `0x887180`（`INI_Art`）、
>    不引 `0x8871E0`，是 artmd 侧 TypeClass 字段。按 disp 撞库会误归因。
> 5. **本节的函数起点曾经报错**：原报 `0x5B6011`，真值是 **`0x5B67F0`**。错因是拿
>    「`ret` 之后必须是填充」回退找函数头，而 `0x5B69E1` 是提前退出的 `ret 4`、
>    **后面紧跟代码**，于是回退跨过它退到前一函数的 `int3`。
>    **这与第 1 点是同一类错误的两个方向**：第 1 点切太短（遇 `ret` 就停），
>    这里退太远（要求 `ret` 后有填充）。**边界要从分支图推，不能从"长什么样"推。**
>
> 27 键表、18/9 划分、三条具体映射、`ShadowGrow` 零消费**全部维持**。
> 门禁 `tools/verify_r023_claims.py` **22/22，EXIT=0**（含 P3c / P13b）；异族盲验已返回，
> 6 项对账中 5 项独立一致、1 项**纠正了本节的函数起点**（见上第 5 点）；
> 记录见 `evidence/r023_rulesclass_mirror_verification.md`。

> **这组计数为什么可信（与 §15.4 的区别）**：镜像全局是**唯一地址**
> （如 `0x00A8B25C`），不存在"偏移碰撞"问题 —— 扫到那个地址就是那个变量。
> §15.4 的字段读点靠 `[reg+off]` 匹配，任何对象撞上同一偏移都会误计，
> 所以那边只能给区间。**两个口径可靠性不同，不要混用。**

| 键 | 结构偏移 | 镜像全局 | 取值引用 | 取址引用 |
|:---|:---|:---|---:|---:|
| `Money` | `+0x1484` | `0x00A8B25C` | 38 | 0 |
| `UnitCount` | `+0x1494` | `0x00A8B270` | 40 | 0 |
| `TechLevel` | `+0x149C` | `0x00822CF4` | 20 | 5 |
| `GameSpeed` | `+0x14A0` | `0x00A8B268` | 43 | 0 |
| `AIDifficulty` | `+0x14A4` | `0x00A8B278` | 17 | 0 |
| `AIPlayers` | `+0x14A8` | `0x00A8B274` | 36 | 0 |
| `BridgeDestruction` | `+0x14AC` | `0x00A8B260` | 27 | 0 |
| `Bases` | `+0x14AF` | `0x00A8B258` | 39 | 0 |
| `Crates` | `+0x14B1` | `0x00A8B261` | 41 | 0 |
| `CaptureTheFlag` | `+0x14B2` | `0x00A8B31E` | 4 | 0 |
| `HarvesterTruce` | `+0x14B3` | `0x00A8B31D` | 23 | 0 |
| `MultiEngineer` | `+0x14B4` | `0x00A8B26C` | 21 | 0 |
| `AlliesAllowed` | `+0x14B5` | `0x00A8B31C` | 12 | 4 |
| `ShortGame` | `+0x14B6` | `0x00A8B262` | 50 | 0 |
| `FogOfWar` | `+0x14B7` | `0x00A8B31F` | 22 | 0 |
| `MCVRedeploys` | `+0x14B8` | `0x00A8B320` | 44 | 0 |
| `SuperWeaponsAllowed` | `+0x14B9` | `0x00A8B263` | 41 | 0 |
| `BuildOffAlly` | `+0x14BA` | `0x00A8B264` | 35 | 0 |

**未镜像的 9 个**：`MinMoney` `+0x1480`、`MaxMoney` `+0x1488`、
`MoneyIncrement` `+0x148C`、`MinUnitCount` `+0x1490`、`MaxUnitCount` `+0x1498`、
`ShadowGrow` `+0x14AD`、`Shroud` `+0x14AE`、`TiberiumGrows` `+0x14B0`、
`AllyChangeAllowed` `+0x14BB`。

这些字段**只留存在 `RulesClass` 里**，读取方直接拿 `[RulesClass+off]`。
不是死配置 —— 只是消费路径不同（见 §15.4 的读点数）。

**镜像块位置**：`0x0052D149`（`call Read_MultiplayerDialogSettings` 之后）
到 `0x0052D22C`，**恰好 18 条** `mov [全局], reg` 拷贝，一条字段对一条全局，
无重复、无遗漏。

> ⚠ 这段代码所在的函数**从 `0x0052CD70` 开始**，不是从 `0x0052D0B4` 开始。
> `0x0052D032` 和 `0x0052D0B3` 是两个**提前退出路径**（`ARTMD.INI` 加载失败的
> 两个分支），不是函数边界。把任一 `ret` 当函数结尾会把镜像块切成两半 ——
> 我第一版就是这么错的，得出的结论是"18 个字段里有 16 个零消费"。

### 15.4 读点分布（**区间口径**，不是单值）

⚠ **R-024 更正**：本节原先给的是单一数字（"`MaxMoney` 33 点"等），那是
**未归因的宽松计数** —— 任何 `[reg+off]` 只要偏移撞上就算，与 `RulesClass`
无关。已改为**区间**：

| 键 | 区间（下界=可追溯到 `RulesClass` 全局；上界=任意 `[reg+off]`） |
|:---|:---|
| `MinMoney` | [4, 10] |
| `Money` | **[3, 3]** |
| `MaxMoney` | [4, 33] |
| `MoneyIncrement` | [2, 5] |
| `MinUnitCount` | [4, 18] |
| `UnitCount` | **[3, 3]** |
| `MaxUnitCount` | [4, 21] |
| `TechLevel` | [1, 16] |
| `GameSpeed` | [2, 20] |
| `AIDifficulty` | [1, 9] |
| `AIPlayers` | [1, 7] |
| `BridgeDestruction` | [2, 30] |
| **`ShadowGrow`** | **[0, 0]** |
| `Shroud` | **[1, 1]** |
| `Bases` | **[2, 2]** |
| `TiberiumGrows` | [0, 18] |
| `Crates` | **[3, 3]** |
| `CaptureTheFlag` | **[2, 2]** |
| `HarvesterTruce` | **[1, 1]** |
| `MultiEngineer` | [1, 8] |
| `AlliesAllowed` | **[5, 5]** |
| `ShortGame` | **[2, 2]** |
| `FogOfWar` | **[1, 1]** |
| `MCVRedeploys` | [2, 6] |
| `SuperWeaponsAllowed` | **[3, 3]** |
| `BuildOffAlly` | **[3, 3]** |
| `AllyChangeAllowed` | **[2, 2]** |

**加粗的 13 个上下界相等 ⇒ 归因确证**（宽松计数与根追踪一致，没有模糊空间）。

**为什么不能给单值**：
- 下界只认「基址寄存器可追溯到 `mov reg,[0x8871E0]`」的读取。但很多函数把
  `RulesClass*` 当**参数**收下（`mov ecx,[ebp+0x1488]`，`ebp` 由调用方给），
  这类下界**看不见**。
- 上界把任何 `[reg+off]` 都算，于是**恰好同偏移的异类对象**会被误计
  （`[ecx+0]` 这种小偏移曾报出 56,820 点）。

⇒ 真值在区间内。**单看一个数字会同时高估和低估。**

**`ShadowGrow` 是 [0, 0]** —— 上下界都为零，这是**唯一能说"零消费"的键**，
因为它不是"上界很小时下界为零"，而是**两个口径都找不到任何读取**，
且纯字节扫描复核：`+0x14AD` 的 disp32 在 `.text` 只出现 3 次
（构造器写 1 + 读取器读/写 2）。

⇒ **对编译器：`[MultiplayerDialogSettings]` 里写 `ShadowGrow=` 对引擎行为无影响。**
其余 26 个键都有真实读点。

### 15.5 复跑与判据

```bash
python re_atlas/tools/dump_rules_fields.py      # evidence/rules_fields.txt
python re_atlas/tools/dump_rules_consumers.py   # evidence/rules_consumers.txt
```

`dump_rules_fields.py` 的三重自检：
1. 每个键的「默认载入偏移」必须等于「存回偏移」（27/27）；
2. 4 字节字段必须落在 4 字节网格上；
3. 任意两个键不得共享字节，覆盖区间必须无空洞。

`dump_rules_consumers.py` 的对账正对照：
每个镜像全局的**字节扫描出现次数**必须等于**指令扫描的 (取值 + 取址) 次数**。
（`TechLevel` 20 + 5 = 25，`AlliesAllowed` 12 + 4 = 16，其余 16 个全部相等。）
这条对账能抓到解码器漏扫 —— 只统计"引用数"而不分类，就无法和字节扫描对上。

`dump_rules_fields.py` 的消费点**必须按区间读**（§15.4）。工具同时打印
`[下界, 上界]`，任何一处把区间当单值引用都会失真。

### 15.6 本轮自纠（4 条）

1. **整节 R-019 数字作废**（§12.0）：`md.disasm` 单次调用在 `0x46F5A0`
   静默截断，只覆盖 `.text` 前 9%。这是本会话最严重的一次错误 ——
   错误不在结论，在**样本**。
2. **`mov` 双形态**：字段解析器首版用 `if/elif`，`mov` 被"载入"分支独占，
   "存回"分支永远走不到，输出 0 行。两形态必须互斥判断。
3. **寄存器别名**：构造器把 bool 存成 `mov byte [esi+off], al`，而 `al` 来自
   很久以前的 `mov eax,1`。跟踪器按原始寄存器 id 记账 ⇒ 16 个 bool 全 `None`。
   需要把 `al/bl/cl/dl` 规范化到 `eax/ebx/ecx/edx`，且 capstone 的
   `reg_name` 返回**小写**，拿大写表匹配会静默全部失配。
4. **寄存器不被 `call` 全清**：MSVC 的被调用者保存集（`ebx/esi/edi/ebp`）
   跨调用存活。首版每次 `call` 清空全部 ⇒ `ebx`（构造器的零常量）变未知。
5. **（R-024）单值消费点是假的**：见 §15.4。`[reg+off]` 计数既漏（参数形式的
   `RulesClass*` 看不见）又误（异类对象同偏移命中）。已改区间。
6. **（R-024）`consumers()` 里写死了 MPD 的偏移区间**：`0x1480 <= d < 0x14BC`
   是调用方 A 的区间，被硬编码成函数体内的字面量，于是调用方 B
   （`[AudioVisual]`）的每个字段都报 0 消费点。已由传入的 `offsets` 集合派生。

---

## 16. `[AudioVisual]` 字段布局（R-024，R-025 补全到 151/152）

`[AudioVisual]` 是 rulesmd.ini **第二大节（152 键）**，仅次于 `[General]`（279）。
本线已解出 **151 个键的字段偏移**（151 行，一键一字段）。

### 16.1 总量

| 指标 | 值 |
|:---|---:|
| 声明键（`dump_rules_keys` 口径） | 152 |
| **解出字段** | **151**（R-024 首版 130） |
| 双向一致（默认载入偏移 == 存回偏移） | **151/151** |
| 未解出 | **1**（`OnFire`，见 §16.6b） |

读取器：`0x006691E0`，函数体 `[0x006691E0, 0x0066B8F1)`，**10,001 字节**
（全引擎最长的 loader 之一）。

### 16.2 字段表（151 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `DetailMinFrameRateNormal` | `+0x0000` | ReadInteger | 4 |
| `DetailMinFrameRateMovie` | `+0x0004` | ReadInteger | 4 |
| `DetailBufferZoneWidth` | `+0x0008` | ReadInteger | 4 |
| `PoseDir` | `+0x0044` | ReadInteger | 4 |
| `DeployDir` | `+0x0048` | ReadInteger | 4 |
| `DropPodPuff` | `+0x004C` | ReadString | 4 |
| `WaypointAnimationSpeed` | `+0x0050` | ReadInteger | 4 |
| `VeinAttack` | `+0x00E8` | ReadString | 4 |
| `DigSound` | `+0x0174` | ReadString | 4 |
| `GUIMainButtonSound` | `+0x0188` | ReadString | 4 |
| `GUIBuildSound` | `+0x018C` | ReadString | 4 |
| `GUITabSound` | `+0x0190` | ReadString | 4 |
| `GUIOpenSound` | `+0x0194` | ReadString | 4 |
| `GUICloseSound` | `+0x0198` | ReadString | 4 |
| `GUIMoveOutSound` | `+0x019C` | ReadString | 4 |
| `GUIMoveInSound` | `+0x01A0` | ReadString | 4 |
| `GUIComboOpenSound` | `+0x01A4` | ReadString | 4 |
| `GUIComboCloseSound` | `+0x01A8` | ReadString | 4 |
| `GUICheckboxSound` | `+0x01AC` | ReadString | 4 |
| `ScoreAnimSound` | `+0x01B0` | ReadString | 4 |
| `CheerSound` | `+0x01C8` | ReadString | 4 |
| `DefaultChronoSound` | `+0x01D0` | ReadString | 4 |
| `StartPlanningModeSound` | `+0x01D4` | ReadString | 4 |
| `EndPlanningModeSound` | `+0x01E0` | ReadString | 4 |
| `CrateMoneySound` | `+0x01E4` | ReadString | 4 |
| `CrateRevealSound` | `+0x01E8` | ReadString | 4 |
| `CrateFireSound` | `+0x01EC` | ReadString | 4 |
| `CrateArmourSound` | `+0x01F0` | ReadString | 4 |
| `CrateSpeedSound` | `+0x01F4` | ReadString | 4 |
| `CrateUnitSound` | `+0x01F8` | ReadString | 4 |
| `CratePromoteSound` | `+0x01FC` | ReadString | 4 |
| `ImpactWaterSound` | `+0x0200` | ReadString | 4 |
| `ImpactLandSound` | `+0x0204` | ReadString | 4 |
| `SinkingSound` | `+0x0208` | ReadString | 4 |
| `ChronoInSound` | `+0x0218` | ReadString | 4 |
| `ChronoOutSound` | `+0x021C` | ReadString | 4 |
| `BombTickingSound` | `+0x020C` | ReadString | 4 |
| `BombAttachSound` | `+0x0210` | ReadString | 4 |
| `YuriMindControlSound` | `+0x0214` | ReadString | 4 |
| `AddPlanningModeCommandSound` | `+0x01D8` | ReadString | 4 |
| `ExecutePlanSound` | `+0x01DC` | ReadString | 4 |
| `PlaceBeaconSound` | `+0x01CC` | ReadString | 4 |
| `BuildingGarrisonedSound` | `+0x01BC` | ReadString | 4 |
| `BuildingAbandonedSound` | `+0x01C0` | ReadString | 4 |
| `BuildingRepairedSound` | `+0x01C4` | ReadString | 4 |
| `BaseUnderAttackSound` | `+0x0184` | ReadString | 4 |
| `UpgradeVeteranSound` | `+0x0228` | ReadString | 4 |
| `UpgradeEliteSound` | `+0x022C` | ReadString | 4 |
| `VoiceIFVRepair` | `+0x0230` | ReadString | 4 |
| `SlavesFreeSound` | `+0x0234` | ReadString | 4 |
| `SlaveMinerDeploySound` | `+0x0238` | ReadString | 4 |
| `SlaveMinerUndeploySound` | `+0x023C` | ReadString | 4 |
| `BunkerWallsUpSound` | `+0x0240` | ReadString | 4 |
| `BunkerWallsDownSound` | `+0x0244` | ReadString | 4 |
| `RepairBridgeSound` | `+0x0248` | ReadString | 4 |
| `PsychicDominatorActivateSound` | `+0x024C` | ReadString | 4 |
| `GeneticMutatorActivateSound` | `+0x0250` | ReadString | 4 |
| `PsychicRevealActivateSound` | `+0x0254` | ReadString | 4 |
| `MasterMindOverloadDeathSound` | `+0x0258` | ReadString | 4 |
| `AirstrikeAbortSound` | `+0x025C` | ReadString | 4 |
| `AirstrikeAttackVoice` | `+0x0260` | ReadString | 4 |
| `MindClearedSound` | `+0x0264` | ReadString | 4 |
| `EnterGrinderSound` | `+0x0268` | ReadString | 4 |
| `LeaveGrinderSound` | `+0x026C` | ReadString | 4 |
| `EnterBioReactorSound` | `+0x0270` | ReadString | 4 |
| `LeaveBioReactorSound` | `+0x0274` | ReadString | 4 |
| `ActivateSound` | `+0x0278` | ReadString | 4 |
| `DeactivateSound` | `+0x027C` | ReadString | 4 |
| `SpyPlaneCamera` | `+0x0280` | ReadString | 4 |
| `LetsDoTheTimeWarpOutAgain` | `+0x0284` | ReadString | 4 |
| `LetsDoTheTimeWarpInAgain` | `+0x0288` | ReadString | 4 |
| `DiskLaserChargeUp` | `+0x028C` | ReadString | 4 |
| `SpyPlaneCameraFrames` | `+0x0290` | ReadInteger | 4 |
| `CreateUnitSound` | `+0x0178` | ReadString | 4 |
| `CreateInfantrySound` | `+0x017C` | ReadString | 4 |
| `CreateAircraftSound` | `+0x0180` | ReadString | 4 |
| `IFVTransformSound` | `+0x01B4` | ReadString | 4 |
| `PsychicSensorDetectSound` | `+0x01B8` | ReadString | 4 |
| `SpySatActivationSound` | `+0x0220` | ReadString | 4 |
| `SpySatDeactivationSound` | `+0x0224` | ReadString | 4 |
| `Dig` | `+0x0294` | ReadString | 4 |
| `AtmosphereEntry` | `+0x0354` | ReadString | 4 |
| `GateUp` | `+0x0404` | ReadString | 4 |
| `GateDown` | `+0x0408` | ReadString | 4 |
| `ShroudGrow` | `+0x17F0` | ReadBool | 1 |
| `ScrollMultiplier` | `+0x05B8` | ReadDouble | 8 |
| `ShakeScreen` | `+0x05C8` | ReadInteger | 4 |
| `CloakSound` | `+0x06A0` | ReadString | 4 |
| `SellSound` | `+0x06A4` | ReadString | 4 |
| `GameClosed` | `+0x06A8` | ReadString | 4 |
| `IncomingMessage` | `+0x06AC` | ReadString | 4 |
| `MessageCharTyped` | `+0x06C4` | ReadString | 4 |
| `SystemError` | `+0x06B0` | ReadString | 4 |
| `OptionsChanged` | `+0x06B4` | ReadString | 4 |
| `GameForming` | `+0x06B8` | ReadString | 4 |
| `PlayerLeft` | `+0x06BC` | ReadString | 4 |
| `PlayerJoined` | `+0x06C0` | ReadString | 4 |
| `Construction` | `+0x06C8` | ReadString | 4 |
| `BuildingDieSound` | `+0x06E8` | ReadString | 4 |
| `BuildingSlam` | `+0x06EC` | ReadString | 4 |
| `RadarOn` | `+0x06F0` | ReadString | 4 |
| `RadarOff` | `+0x06F4` | ReadString | 4 |
| `MovieOn` | `+0x06F8` | ReadString | 4 |
| `MovieOff` | `+0x06FC` | ReadString | 4 |
| `ScoldSound` | `+0x0700` | ReadString | 4 |
| `TeslaCharge` | `+0x0704` | ReadString | 4 |
| `TeslaZap` | `+0x0708` | ReadString | 4 |
| `BuildingDamageSound` | `+0x0714` | ReadString | 4 |
| `ChuteSound` | `+0x071C` | ReadString | 4 |
| `GenericClick` | `+0x070C` | ReadString | 4 |
| `GenericBeep` | `+0x0710` | ReadString | 4 |
| `BuildingDrop` | `+0x07C0` | ReadString | 4 |
| `StopSound` | `+0x0720` | ReadString | 4 |
| `GuardSound` | `+0x0724` | ReadString | 4 |
| `ScatterSound` | `+0x0728` | ReadString | 4 |
| `StormSound` | `+0x0730` | ReadString | 4 |
| `ShellButtonSlideSound` | `+0x0750` | ReadString | 4 |
| `Smoke` | `+0x0BAC` | ReadString | 4 |
| `Smoke` | `+0x0BB0` | ReadString | 4 |
| `EliteFlashTimer` | `+0x0BE8` | ReadInteger | 4 |
| `SmallFire` | `+0x0BDC` | ReadString | 4 |
| `LargeFire` | `+0x0BE0` | ReadString | 4 |
| `AllyReveal` | `+0x17E7` | ReadBool | 1 |
| `ConditionRed` | `+0x1708` | ReadDouble | 8 |
| `ConditionYellow` | `+0x1700` | ReadDouble | 8 |
| `EnemyHealth` | `+0x17E6` | ReadBool | 1 |
| `Gravity` | `+0x16B8` | ReadInteger | 4 |
| `IdleActionFrequency` | `+0x1710` | ReadDouble | 8 |
| `MessageDelay` | `+0x14C0` | ReadDouble | 8 |
| `MovieTime` | `+0x1770` | ReadDouble | 8 |
| `NamedCivilians` | `+0x17EA` | ReadBool | 1 |
| `SavourDelay` | `+0x14C8` | ReadDouble | 8 |
| `ShroudRate` | `+0x1640` | ReadDouble | 8 |
| `FogRate` | `+0x1648` | ReadDouble | 8 |
| `VeinGrowthRate` | `+0x1658` | ReadDouble | 8 |
| `IceGrowthRate` | `+0x1650` | ReadDouble | 8 |
| `IceSolidifyFrameTime` | `+0x1660` | ReadInteger | 4 |
| `AmbientChangeRate` | `+0x1668` | ReadDouble | 8 |
| `AmbientChangeStep` | `+0x1670` | ReadDouble | 8 |
| `SpeakDelay` | `+0x16A8` | ReadDouble | 8 |
| `TimerWarning` | `+0x1680` | ReadDouble | 8 |
| `ExtraUnitLight` | `+0x17D4` | ReadDouble | 4 |
| `ExtraInfantryLight` | `+0x17D8` | ReadDouble | 4 |
| `ExtraAircraftLight` | `+0x17DC` | ReadDouble | 4 |
| `OreTwinkleChance` | `+0x186C` | ReadInteger | 4 |
| `LaserTargetColor` | `+0x18A4` | ReadInteger | 4 |
| `IronCurtainColor` | `+0x18A8` | ReadInteger | 4 |
| `BerserkColor` | `+0x18AC` | ReadInteger | 4 |
| `ForceShieldColor` | `+0x18B0` | ReadInteger | 4 |
| `DirectRockingCoefficient` | `+0x18B4` | ReadDouble | 4 |
| `FallBackCoefficient` | `+0x18B8` | ReadDouble | 4 |

### 16.3 三种存回形态（首版漏掉后两种）

| 读法 | 存回指令 | 宽 | 例 |
|:---|:---|---:|:---|
| `ReadInteger`/`ReadBool`/`ReadString` | `mov [esi+off], eax/al` | 4 / 1 / 4 | 绝大多数 |
| `ReadDouble` → double 字段 | **`fstp qword [esi+off]`** | 8 | `ConditionRed` `+0x1708` |
| `ReadDouble` → float 字段 | **`fstp dword [esi+off]`** | 4 | `DirectRockingCoefficient` `+0x18B4` |
| `ReadDouble` → int 字段（经 `imul`/`sar` 换算） | `mov [esi+off], eax` | 4 | `ExtraUnitLight` `+0x17D4` |

**宽度一律取自存回指令，不取自读取器** —— `ReadDouble` 三种宽度都用。
这是首版 22 个键"解不出"的真正原因：不是键的字面量找不到（它们都在 `.data`，
各出现一次），而是**存回不是 `mov`**。

### 16.4 三个必须跟踪的隐藏基址

1. **`add esi,0x18B8`** —— 函数尾部改了对象基址，之后 `[esi]` 等价于 `[原基址+0x18B8]`。
   不跟踪会把 `FallBackCoefficient` 记成 `+0x0000`（真值 `+0x18B8`）。
2. **`fstp qword [esp]`** 只是把默认值放上栈给调用用，**不是字段存回**。
   当成存回会给 4 字节字段记 8 字节宽，并让三个相邻字段看起来重叠。
3. **`fld dword [esi+off]`** 是浮点字段的默认值载入，不是 `mov`。
   只认 `mov` 会让两个字段报"默认值未知"。

### 16.5 `Smoke` 一键两字段

`Smoke` 出现在 `+0x0BAC` 与 `+0x0BB0`，两处推同一字面量 `0x00836F0C`，
**不是工具缺陷**：引擎用一个 `Smoke=` 值填两个槽。⇒ 编译器只写一次。

### 16.6 `YuriMindControlSound` `+0x0214` 无构造器默认值

构造器未在该偏移写入（`+0x210` 与 `+0x218` 各写 4 字节，中间空着），
但读取器确实读它。**这是引擎的真实状态，不是解析错误** ——
该字段依赖其他初始化路径。对编译器：**必须显式写这个键**，不要依赖默认值。

### 16.6b `OnFire` 不是标量字段（唯一未解出项）

`OnFire` 的读法与其他键相同（`push 键; push 节; call ReadString`），但结果
**不落到 `[esi+off]`**：它先读进栈缓冲，再经 `0x7C9CC2`（`strtok` 形态，
分隔符 `0x817F70`）逐段切分，`0x5253B0` 追加进一个栈上的容器对象，
最后整体交给另一个对象。

⇒ `OnFire` 是**列表型配置**（可写多个动画名），不是单值字段。
**它不是解析失败，是形态不同**：本线只解 `[this+off]` 标量字段，故计为未解出。
对编译器：`OnFire=` 可写多个以分隔符隔开的名字，行为与标量键不同。

### 16.7 复跑

```bash
python re_atlas/tools/dump_rules_fields.py 0x006691E0
```

自检：151/151 双向一致 / 宽度取自存回指令 / 双精度按相邻双 dword 校验 /
无偏移重叠 / 构造器逐字段宽度吻合（8 字节字段允许由两条 4 字节 `mov` 组成）。
**消费点只看区间**（§15.4 与 `CONFLICTS` G-26）。

---

## 17. `[General]` 字段布局（R-025）

`[General]` 是 rulesmd.ini **最大的节（279 键）**，占全部字面量键的 43%。

### 17.1 总量

| 指标 | 值 |
|:---|---:|
| 声明键（`dump_rules_keys` 口径） | 279 |
| **解出标量字段** | **268**（267 个不同键，有一键两槽） |
| 未映射 | **12**（全部是列表型，见 §17.3） |
| 凭空多出的字段 | **0** |

读取器：`0x0066D530`，函数体 `[0x0066D530, 0x00671E8E)`，**5,062 条指令**。

> ⚠ **边界陷阱**：`Read_General` 的真实首个 `ret` 在 `0x00671E8B`（`ret 4`），
> 距离入口 18,782 字节。我用过的 `0x0066E52F` 是**错的**（那是函数体中部），
> 用它截断只解出 33 个键。**边界必须由工具 `find_ret` 给出，不能手估。**

### 17.2 字段表（268 行，完整）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `OreTwinkle` | `+0x1870` | ReadString | 4 |
| `BarrelExplode` | `+0x0054` | ReadString | 4 |
| `BarrelParticle` | `+0x0074` | ReadString | 4 |
| `NukeTakeOff` | `+0x0098` | ReadString | 4 |
| `Wake` | `+0x0094` | ReadString | 4 |
| `IonBlast` | `+0x0298` | ReadString | 4 |
| `IonBeam` | `+0x029C` | ReadString | 4 |
| `WeatherConBoltExplosion` | `+0x02F4` | ReadString | 4 |
| `DominatorWarhead` | `+0x02F8` | ReadString | 4 |
| `DominatorFirstAnim` | `+0x02FC` | ReadString | 4 |
| `DominatorSecondAnim` | `+0x0300` | ReadString | 4 |
| `DominatorFireAtPercentage` | `+0x0304` | ReadInteger | 4 |
| `DominatorCaptureRange` | `+0x0308` | ReadInteger | 4 |
| `DominatorDamage` | `+0x030C` | ReadInteger | 4 |
| `ChronoPlacement` | `+0x0330` | ReadString | 4 |
| `ChronoBeam` | `+0x0334` | ReadString | 4 |
| `ChronoBlast` | `+0x0328` | ReadString | 4 |
| `ChronoBlastDest` | `+0x032C` | ReadString | 4 |
| `WarpIn` | `+0x0338` | ReadString | 4 |
| `WarpOut` | `+0x033C` | ReadString | 4 |
| `WarpAway` | `+0x0340` | ReadString | 4 |
| `IronCurtainInvokeAnim` | `+0x0348` | ReadString | 4 |
| `ForceShieldInvokeAnim` | `+0x034C` | ReadString | 4 |
| `WeaponNullifyAnim` | `+0x0350` | ReadString | 4 |
| `ChronoSparkle1` | `+0x0344` | ReadString | 4 |
| `InfantryExplode` | `+0x009C` | ReadString | 4 |
| `FlamingInfantry` | `+0x00A0` | ReadString | 4 |
| `InfantryHeadPop` | `+0x00A4` | ReadString | 4 |
| `InfantryNuked` | `+0x00A8` | ReadString | 4 |
| `InfantryVirus` | `+0x00AC` | ReadString | 4 |
| `InfantryBrute` | `+0x00B0` | ReadString | 4 |
| `InfantryMutate` | `+0x00B4` | ReadString | 4 |
| `Behind` | `+0x00B8` | ReadString | 4 |
| `MoveFlash` | `+0x0BB4` | ReadString | 4 |
| `Parachute` | `+0x0BBC` | ReadString | 4 |
| `BombParachute` | `+0x0BB8` | ReadString | 4 |
| `DropZoneAnim` | `+0x147C` | ReadString | 4 |
| `EMPulseSparkles` | `+0x17F4` | ReadString | 4 |
| `LargeVisceroid` | `+0x0010` | ReadString | 4 |
| `SmallVisceroid` | `+0x0014` | ReadString | 4 |
| `TiberiumHeal` | `+0x0028` | ReadDouble | 8 |
| `SelfHealInfantryFrames` | `+0x0030` | ReadInteger | 4 |
| `SelfHealInfantryAmount` | `+0x0034` | ReadInteger | 4 |
| `SelfHealUnitFrames` | `+0x0038` | ReadInteger | 4 |
| `SelfHealUnitAmount` | `+0x003C` | ReadInteger | 4 |
| `ZoomInFactor` | `+0x0550` | ReadDouble | 8 |
| `RevealByHeight` | `+0x17EE` | ReadBool | 1 |
| `AllowShroudedSubteranneanMoves` | `+0x17EF` | ReadBool | 1 |
| `AircraftFogReveal` | `+0x00F4` | ReadInteger | 4 |
| `MinLowPowerProductionSpeed` | `+0x0570` | ReadDouble | 4 |
| `MaxLowPowerProductionSpeed` | `+0x0574` | ReadDouble | 4 |
| `LowPowerPenaltyModifier` | `+0x0578` | ReadDouble | 4 |
| `MultipleFactory` | `+0x057C` | ReadDouble | 4 |
| `MaximumCheerRate` | `+0x0580` | ReadInteger | 4 |
| `TreeFlammability` | `+0x0588` | ReadDouble | 8 |
| `MissileROTVar` | `+0x0598` | ReadDouble | 8 |
| `MissileSafetyAltitude` | `+0x05A0` | ReadInteger | 4 |
| `MissileSpeedVar` | `+0x0590` | ReadDouble | 8 |
| `DropPodWeapon` | `+0x05A4` | ReadString | 4 |
| `DropPodHeight` | `+0x05A8` | ReadInteger | 4 |
| `DropPodSpeed` | `+0x05AC` | ReadInteger | 4 |
| `DropPodAngle` | `+0x05B0` | ReadDouble | 8 |
| `CrewEscape` | `+0x05C0` | ReadDouble | 8 |
| `TunnelSpeed` | `+0x0020` | ReadDouble | 8 |
| `HoverDampen` | `+0x05F0` | ReadDouble | 8 |
| `HoverBob` | `+0x05D0` | ReadDouble | 8 |
| `HoverHeight` | `+0x05CC` | ReadInteger | 4 |
| `HoverBoost` | `+0x05D8` | ReadDouble | 8 |
| `HoverAcceleration` | `+0x05E0` | ReadDouble | 8 |
| `HoverBrake` | `+0x05E8` | ReadDouble | 8 |
| `VeteranRatio` | `+0x0668` | ReadDouble | 8 |
| `VeteranCombat` | `+0x0670` | ReadDouble | 8 |
| `VeteranSpeed` | `+0x0678` | ReadDouble | 8 |
| `VeteranSight` | `+0x0680` | ReadDouble | 8 |
| `VeteranArmor` | `+0x0688` | ReadDouble | 8 |
| `VeteranROF` | `+0x0690` | ReadDouble | 8 |
| `VeteranCap` | `+0x0698` | ReadDouble | 8 |
| `BridgeVoxelMax` | `+0x0624` | ReadInteger | 4 |
| `TireVoxelDebris` | `+0x061C` | ReadString | 4 |
| `ScrapVoxelDebris` | `+0x0620` | ReadString | 4 |
| `CloakingStages` | `+0x0628` | ReadInteger | 4 |
| `ShipSinkingWeight` | `+0x0630` | ReadDouble | 8 |
| `IceCrackingWeight` | `+0x0638` | ReadDouble | 8 |
| `IceBreakingWeight` | `+0x0640` | ReadDouble | 8 |
| `CliffBackImpassability` | `+0x0664` | ReadInteger | 1 |
| `PlacementDelay` | `+0x05F8` | ReadDouble | 8 |
| `TrackedUphill` | `+0x0768` | ReadDouble | 8 |
| `TrackedDownhill` | `+0x0770` | ReadDouble | 8 |
| `WheeledUphill` | `+0x0778` | ReadDouble | 8 |
| `WheeledDownhill` | `+0x0780` | ReadDouble | 8 |
| `WindDirection` | `+0x07AC` | ReadInteger | 4 |
| `FlightLevel` | `+0x07B4` | ReadInteger | 4 |
| `ParachuteMaxFallRate` | `+0x07B8` | ReadInteger | 4 |
| `NoParachuteMaxFallRate` | `+0x07BC` | ReadInteger | 4 |
| `GDIGateOne` | `+0x086C` | ReadString | 4 |
| `GDIGateTwo` | `+0x0870` | ReadString | 4 |
| `NodGateOne` | `+0x0874` | ReadString | 4 |
| `NodGateTwo` | `+0x0878` | ReadString | 4 |
| `WallTower` | `+0x087C` | ReadString | 4 |
| `GDIPowerPlant` | `+0x089C` | ReadString | 4 |
| `NodRegularPower` | `+0x08A0` | ReadString | 4 |
| `NodAdvancedPower` | `+0x08A4` | ReadString | 4 |
| `ThirdPowerPlant` | `+0x08A8` | ReadString | 4 |
| `PrerequisiteProcAlternate` | `+0x0400` | ReadString | 4 |
| `HarvesterUnit` | `+0x0BE4` | ReadString | 4 |
| `ChronoDelay` | `+0x0BEC` | ReadInteger | 4 |
| `ChronoReinfDelay` | `+0x0BF0` | ReadInteger | 4 |
| `ChronoDistanceFactor` | `+0x0BF4` | ReadInteger | 4 |
| `ChronoTrigger` | `+0x0BF8` | ReadBool | 1 |
| `ChronoMinimumDelay` | `+0x0BFC` | ReadInteger | 4 |
| `ChronoRangeMinimum` | `+0x0C00` | ReadInteger | 4 |
| `SpyPowerBlackout` | `+0x0D64` | ReadInteger | 4 |
| `SpyMoneyStealPercent` | `+0x0D68` | ReadDouble | 4 |
| `AttackCursorOnDisguise` | `+0x0D6C` | ReadBool | 1 |
| `PurifierBonus` | `+0x0F3C` | ReadDouble | 4 |
| `CurleyShuffle` | `+0x17E1` | ReadBool | 1 |
| `FineDiffControl` | `+0x17E4` | ReadBool | 1 |
| `AIAlternateProductionCreditCutoff` | `+0x1300` | ReadInteger | 4 |
| `AIUseTurbineUpgradeProbability` | `+0x13E8` | ReadDouble | 8 |
| `NodAIBuildsWalls` | `+0x17F1` | ReadBool | 1 |
| `AIBuildsWalls` | `+0x17F2` | ReadBool | 1 |
| `UseMinDefenseRule` | `+0x17F3` | ReadBool | 1 |
| `DissolveUnfilledTeamDelay` | `+0x1190` | ReadInteger | 4 |
| `AISafeDistance` | `+0x0D74` | ReadInteger | 4 |
| `AIMinorSuperReadyPercent` | `+0x0D70` | ReadDouble | 4 |
| `HarvesterTooFarDistance` | `+0x0D78` | ReadInteger | 4 |
| `ChronoHarvTooFarDistance` | `+0x0D7C` | ReadInteger | 4 |
| `AIRestrictReplaceTime` | `+0x0DF0` | ReadInteger | 4 |
| `ThreatPerOccupant` | `+0x0DF4` | ReadInteger | 4 |
| `ApproachTargetResetMultiplier` | `+0x0DF8` | ReadInteger | 4 |
| `CampaignMoneyDeltaEasy` | `+0x0DFC` | ReadInteger | 4 |
| `CampaignMoneyDeltaHard` | `+0x0E00` | ReadInteger | 4 |
| `GuardAreaTargetingDelay` | `+0x0E04` | ReadInteger | 4 |
| `NormalTargetingDelay` | `+0x0E08` | ReadInteger | 4 |
| `AINavalYardAdjacency` | `+0x0E0C` | ReadInteger | 4 |
| `MaximumBuildingPlacementFailures` | `+0x0E48` | ReadInteger | 4 |
| `SlaveMinerKickFrameDelay` | `+0x1790` | ReadInteger | 4 |
| `AISuperDefenseFrames` | `+0x0EE0` | ReadInteger | 4 |
| `AICaptureLowMoneyMark` | `+0x0EBC` | ReadInteger | 4 |
| `AICaptureWoundedMark` | `+0x0EC0` | ReadDouble | 4 |
| `CloakDelay` | `+0x1410` | ReadDouble | 8 |
| `GameSpeedBias` | `+0x1418` | ReadDouble | 8 |
| `BaseBias` | `+0x1420` | ReadDouble | 8 |
| `SeparateAircraft` | `+0x17E8` | ReadBool | 1 |
| `BaseDefenseDelay` | `+0x14D8` | ReadDouble | 8 |
| `SuspendPriority` | `+0x14E0` | ReadInteger | 4 |
| `SuspendDelay` | `+0x14E8` | ReadDouble | 8 |
| `SurvivorRate` | `+0x14F0` | ReadDouble | 8 |
| `AlliedSurvivorDivisor` | `+0x14F8` | ReadInteger | 4 |
| `SovietSurvivorDivisor` | `+0x14FC` | ReadInteger | 4 |
| `ThirdSurvivorDivisor` | `+0x1500` | ReadInteger | 4 |
| `ReloadRate` | `+0x1508` | ReadDouble | 8 |
| `BuildupTime` | `+0x1518` | ReadDouble | 8 |
| `HarvesterDumpRate` | `+0x1528` | ReadDouble | 8 |
| `HarvesterLoadRate` | `+0x1520` | ReadInteger | 4 |
| `BuildSpeed` | `+0x1748` | ReadDouble | 8 |
| `DamageDelay` | `+0x16B0` | ReadDouble | 8 |
| `GrowthRate` | `+0x1638` | ReadDouble | 8 |
| `RefundPercent` | `+0x1738` | ReadDouble | 8 |
| `RepairPercent` | `+0x16D0` | ReadDouble | 8 |
| `RepairStep` | `+0x16CC` | ReadInteger | 4 |
| `IRepairStep` | `+0x16D8` | ReadInteger | 4 |
| `RepairRate` | `+0x16E0` | ReadDouble | 8 |
| `URepairRate` | `+0x16E8` | ReadDouble | 8 |
| `IRepairRate` | `+0x16F0` | ReadDouble | 8 |
| `BlendedFog` | `+0x17E2` | ReadBool | 1 |
| `AttackingAircraftSightRange` | `+0x0018` | ReadInteger | 4 |
| `LeptonsPerSightIncrease` | `+0x16BC` | ReadInteger | 4 |
| `TiberiumTransmogrify` | `+0x1688` | ReadInteger | 4 |
| `LightningDeferment` | `+0x1794` | ReadInteger | 4 |
| `LightningDamage` | `+0x1798` | ReadInteger | 4 |
| `LightningStormDuration` | `+0x179C` | ReadInteger | 4 |
| `LightningHitDelay` | `+0x17A0` | ReadInteger | 4 |
| `LightningScatterDelay` | `+0x17A4` | ReadInteger | 4 |
| `LightningCellSpread` | `+0x17A8` | ReadInteger | 4 |
| `LightningSeparation` | `+0x17AC` | ReadInteger | 4 |
| `LightningPrintText` | `+0x17B0` | ReadBool | 1 |
| `ForceShieldRadius` | `+0x17B8` | ReadInteger | 4 |
| `ForceShieldDuration` | `+0x17BC` | ReadInteger | 4 |
| `ForceShieldBlackoutDuration` | `+0x17C0` | ReadInteger | 4 |
| `ForceShieldPlayFadeSoundTime` | `+0x17C4` | ReadInteger | 4 |
| `MutateExplosion` | `+0x17C8` | ReadBool | 1 |
| `PrismSupportModifier` | `+0x049C` | ReadDouble | 4 |
| `PrismSupportMax` | `+0x04A0` | ReadInteger | 4 |
| `PrismSupportDelay` | `+0x04A4` | ReadInteger | 4 |
| `PrismSupportDuration` | `+0x04A8` | ReadInteger | 4 |
| `PrismSupportHeight` | `+0x04AC` | ReadInteger | 4 |
| `V3RocketPauseFrames` | `+0x04B0` | ReadInteger | 4 |
| `V3RocketTiltFrames` | `+0x04B4` | ReadInteger | 4 |
| `V3RocketPitchInitial` | `+0x04B8` | ReadDouble | 4 |
| `V3RocketPitchFinal` | `+0x04BC` | ReadDouble | 4 |
| `V3RocketTurnRate` | `+0x04C0` | ReadDouble | 4 |
| `V3RocketRaiseRate` | `+0x04C4` | ReadDouble | 4 |
| `V3RocketAcceleration` | `+0x04C8` | ReadDouble | 4 |
| `V3RocketAltitude` | `+0x04CC` | ReadInteger | 4 |
| `V3RocketDamage` | `+0x04D0` | ReadInteger | 4 |
| `V3RocketEliteDamage` | `+0x04D4` | ReadInteger | 4 |
| `V3RocketBodyLength` | `+0x04D8` | ReadInteger | 4 |
| `V3RocketLazyCurve` | `+0x04DC` | ReadBool | 1 |
| `DMislPauseFrames` | `+0x04E4` | ReadInteger | 4 |
| `DMislTiltFrames` | `+0x04E8` | ReadInteger | 4 |
| `DMislPitchInitial` | `+0x04EC` | ReadDouble | 4 |
| `DMislPitchFinal` | `+0x04F0` | ReadDouble | 4 |
| `DMislTurnRate` | `+0x04F4` | ReadDouble | 4 |
| `DMislRaiseRate` | `+0x04F8` | ReadDouble | 4 |
| `DMislAcceleration` | `+0x04FC` | ReadDouble | 4 |
| `DMislAltitude` | `+0x0500` | ReadInteger | 4 |
| `DMislDamage` | `+0x0504` | ReadInteger | 4 |
| `DMislEliteDamage` | `+0x0508` | ReadInteger | 4 |
| `DMislBodyLength` | `+0x050C` | ReadInteger | 4 |
| `DMislLazyCurve` | `+0x0510` | ReadBool | 1 |
| `CMislPauseFrames` | `+0x0518` | ReadInteger | 4 |
| `CMislTiltFrames` | `+0x051C` | ReadInteger | 4 |
| `CMislPitchInitial` | `+0x0520` | ReadDouble | 4 |
| `CMislPitchFinal` | `+0x0524` | ReadDouble | 4 |
| `CMislTurnRate` | `+0x0528` | ReadDouble | 4 |
| `CMislRaiseRate` | `+0x052C` | ReadDouble | 4 |
| `CMislAcceleration` | `+0x0530` | ReadDouble | 4 |
| `CMislAltitude` | `+0x0534` | ReadInteger | 4 |
| `CMislDamage` | `+0x0538` | ReadInteger | 4 |
| `CMislEliteDamage` | `+0x053C` | ReadInteger | 4 |
| `CMislBodyLength` | `+0x0540` | ReadInteger | 4 |
| `CMislLazyCurve` | `+0x0544` | ReadBool | 1 |
| `ParadropRadius` | `+0x054C` | ReadInteger | 4 |
| `SpotlightMovementRadius` | `+0x0788` | ReadInteger | 4 |
| `SpotlightLocationRadius` | `+0x078C` | ReadInteger | 4 |
| `SpotlightSpeed` | `+0x0790` | ReadDouble | 8 |
| `SpotlightAcceleration` | `+0x0798` | ReadDouble | 8 |
| `SpotlightAngle` | `+0x07A0` | ReadDouble | 8 |
| `SpotlightRadius` | `+0x07A8` | ReadInteger | 4 |
| `RevealTriggerRadius` | `+0x062C` | ReadInteger | 4 |
| `ChargeToDrainRatio` | `+0x0760` | ReadDouble | 8 |
| `WallBuildSpeedCoefficient` | `+0x0758` | ReadDouble | 8 |
| `ConditionYellowSparkingProbability` | `+0x0560` | ReadDouble | 8 |
| `ConditionRedSparkingProbability` | `+0x0558` | ReadDouble | 8 |
| `AITriggerSuccessWeightDelta` | `+0x00C0` | ReadDouble | 8 |
| `AITriggerFailureWeightDelta` | `+0x00C8` | ReadDouble | 8 |
| `AITriggerTrackRecordCoefficient` | `+0x00D0` | ReadDouble | 8 |
| `WeedCapacity` | `+0x17D0` | ReadInteger | 4 |
| `FlashFrameTime` | `+0x0088` | ReadInteger | 4 |
| `RadarCombatFlashTime` | `+0x008C` | ReadInteger | 4 |
| `RadarEventSpeed` | `+0x0080` | ReadDouble | 4 |
| `RadarEventRotationSpeed` | `+0x0084` | ReadDouble | 4 |
| `RadarEventMinRadius` | `+0x007C` | ReadInteger | 4 |
| `RadarEventColorSpeed` | `+0x0078` | ReadDouble | 4 |
| `MyEffectivenessCoefficientDefault` | `+0x1040` | ReadDouble | 8 |
| `TargetEffectivenessCoefficientDefault` | `+0x1048` | ReadDouble | 8 |
| `TargetSpecialThreatCoefficientDefault` | `+0x1050` | ReadDouble | 8 |
| `TargetStrengthCoefficientDefault` | `+0x1058` | ReadDouble | 8 |
| `TargetDistanceCoefficientDefault` | `+0x1060` | ReadDouble | 8 |
| `DumbMyEffectivenessCoefficient` | `+0x1068` | ReadDouble | 8 |
| `DumbTargetEffectivenessCoefficient` | `+0x1070` | ReadDouble | 8 |
| `DumbTargetSpecialThreatCoefficient` | `+0x1078` | ReadDouble | 8 |
| `DumbTargetStrengthCoefficient` | `+0x1080` | ReadDouble | 8 |
| `DumbTargetDistanceCoefficient` | `+0x1088` | ReadDouble | 8 |
| `EnemyHouseThreatBonus` | `+0x1090` | ReadDouble | 8 |
| `VeinholeMonsterStrength` | `+0x00D8` | ReadInteger | 4 |
| `MaxVeinholeGrowth` | `+0x00DC` | ReadInteger | 4 |
| `VeinholeGrowthRate` | `+0x00E0` | ReadInteger | 4 |
| `VeinholeShrinkRate` | `+0x00E4` | ReadInteger | 4 |
| `VeinDamage` | `+0x00EC` | ReadInteger | 4 |
| `InfantryBlinkDisguiseTime` | `+0x1014` | ReadInteger | 4 |
| `MaximumQueuedObjects` | `+0x00F0` | ReadInteger | 4 |
| `MaxWaypointPathLength` | `+0x0090` | ReadInteger | 4 |
| `TreeStrength` | `+0x1144` | ReadInteger | 4 |
| `EngineerCaptureLevel` | `+0x17F8` | ReadDouble | 4 |
| `EngineerCaptureLevel` | `+0x17FC` | ReadDouble | 4 |
| `TalkBubbleTime` | `+0x1800` | ReadDouble | 4 |

### 17.3 未映射的 12 个键 —— 全是列表型

`BarrelDebris` `BaseUnit` `BridgeExplosions` `DamageFireTypes` `DeadBodies`
`DropPod` `ExplosiveVoxelDebris` `MetallicDebris` `RepairBay` `Shipyard`
`WeatherConBolts` `WeatherConClouds`

形态完全一致（以 `DeadBodies` @`0x0066D9A2` 为例）：

```text
push <key>; push <section>; call ReadString
test eax,eax; je <skip>
push 0; push 0              ; 两个空参数 -> 默认分隔符
... -> 切分 -> 逐项追加进容器
```

⇒ 这些是**列表型配置**（可写多个名字），不是单值字段。本线只解 `[this+off]`
标量字段，故计为未映射。**这不是解析失败。**
对编译器：这类键可写多个以逗号分隔的名字，行为与标量键不同。

### 17.4 跨字段默认值（R-026 已定性：是引擎行为，不是解析错误）

R-025 报告的"7 处偏移错位"已降到 **1 处**，且**成因是引擎设计而非工具缺陷**：

| 键 | 默认取自 | 存回 | 说明 |
|:---|:---|:---|:---|
| `CMislAcceleration` | `+0x04FC`（`DMislAcceleration`） | `+0x0530` | **引擎用对面阵营的同名值作默认** |

`DMislAcceleration` 在 `+0x4FC`、`CMislAcceleration` 在 `+0x530`，两者都是
独立字段；引擎在解析 `CMislAcceleration` 时把 `DMislAcceleration` 的**当前值**
当默认参数传进去。这是刻意的（敌方导弹加速沿用己方设定），不是结构错位。

其余 6 处已由工具修复，成因分别是：
- **`fild dword [esi+off]`** 默认值载入没识别（`PrismSupportModifier` 等 5 处）；
- **`movsx`/`movzx`** 默认值载入没识别（`CliffBackImpassability`）。

**对使用者的判据**：行内标注
- `一致` = 默认载入与存回同一偏移；
- `跨字段默认(from +0xXXXX)` = 引擎刻意用另一字段作默认值，**以「存回」列为准**；
- `!! 默认载入=None` = 标量读者却没有默认载入（这才是真缺陷）。

### 17.4b 构造器「未直接写」的 3 个字段

`AICaptureLowMoneyMark` `+0x0EBC`、`AICaptureWoundedMark` `+0x0EC0`、
`TiberiumTransmogrify` `+0x1688` 在 `RulesClass` 构造器里没有直接写入。
`+0x0EC4` 紧邻是一个 vtable 指针 ⇒ 这几个字段属**内嵌子对象**，
由子对象自己的构造器初始化。**不是解析缺陷**；对编译器意味着这些键的默认值
不该假设为 0，必须显式写。

### 17.5 复跑

```bash
python re_atlas/tools/dump_rules_fields.py 0x0066D530
```

证据：`evidence/rules_fields_general.txt`（554 行，含 268 字段 + 消费点区间）。

---

## 18. 其余小节字段布局（R-027）

`Read_File` 会调用的另外 10 个节，本节一次给全。全部 10 个 loader 的正对照
均通过（见 `evidence/rules_fields_<小写节名>.txt`）。

### 18.1 汇总

| 节 | 读取器 | 键数 | 形态 |
|:---|:---|---:|:---|
| `[CrateRules]` | `0x0066B900` | 10 | 标量，`this=esi` |
| `[IQ]` | `0x00674240` | 11 | 标量，`this=esi` |
| `[Radiation]` | `0x0066CF70` | 9 | 标量，`this=esi` |
| `[SpecialWeapons]` | `0x00668FB0` | 7 | 标量，`this=esi` |
| `[JumpjetControls]` | `0x006743D0` | 7 | 标量，`this=esi` |
| `[ElevationModel]` | `0x0066D150` | 3 | 标量，`this=esi` |
| `[WallModel]` | `0x0066D1F0` | 2 | 标量，`this=esi` |
| `[Maximums]` | `0x00672230` | 1 | 标量，`this=esi` |
| `[Easy/Normal/Difficult]` | `0x0066D270` | 12 | **外部对象**（`edi` 基址） |
| （三个难度子对象） | `0x00674500` | 0 | **纯分派器**，调 `Read_Difficulty` ×3 |
| `[Clear/…]`（地形） | `0x00674000` | 0 | 写入**全局表** `0x89EA44` |

### 18.2 字段表

#### `[CrateRules]` @ `0x0066B900`（10 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `FreeMCV` | `+0x0040` | ReadBool | 1 |
| `WoodCrateImg` | `+0x00F8` | ReadString | 4 |
| `CrateImg` | `+0x00FC` | ReadString | 4 |
| `WaterCrateImg` | `+0x0100` | ReadString | 4 |
| `HealCrateSound` | `+0x0718` | ReadString | 4 |
| `CrateMinimum` | `+0x1470` | ReadInteger | 4 |
| `CrateMaximum` | `+0x1474` | ReadInteger | 4 |
| `CrateRegen` | `+0x1678` | ReadDouble | 8 |
| `UnitCrateType` | `+0x1148` | ReadString | 4 |
| `SoloCrateMoney` | `+0x1140` | ReadInteger | 4 |

#### `[IQ]` @ `0x00674240`（11 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `MaxIQLevels` | `+0x1434` | ReadInteger | 4 |
| `SuperWeapons` | `+0x1438` | ReadInteger | 4 |
| `Production` | `+0x143C` | ReadInteger | 4 |
| `GuardArea` | `+0x1440` | ReadInteger | 4 |
| `RepairSell` | `+0x1444` | ReadInteger | 4 |
| `AutoCrush` | `+0x1448` | ReadInteger | 4 |
| `Scatter` | `+0x144C` | ReadInteger | 4 |
| `ContentScan` | `+0x1450` | ReadInteger | 4 |
| `Aircraft` | `+0x1454` | ReadInteger | 4 |
| `Harvester` | `+0x1458` | ReadInteger | 4 |
| `SellBack` | `+0x145C` | ReadInteger | 4 |

#### `[Radiation]` @ `0x0066CF70`（9 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `RadDurationMultiple` | `+0x1804` | ReadInteger | 4 |
| `RadApplicationDelay` | `+0x1808` | ReadInteger | 4 |
| `RadLevelMax` | `+0x180C` | ReadInteger | 4 |
| `RadLevelDelay` | `+0x1810` | ReadInteger | 4 |
| `RadLightDelay` | `+0x1814` | ReadInteger | 4 |
| `RadLevelFactor` | `+0x1818` | ReadDouble | 8 |
| `RadLightFactor` | `+0x1820` | ReadDouble | 8 |
| `RadTintFactor` | `+0x1828` | ReadDouble | 8 |
| `RadSiteWarhead` | `+0x1834` | ReadString | 4 |

#### `[SpecialWeapons]` @ `0x00668FB0`（7 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `NukeWarhead` | `+0x0F8C` | ReadString | 4 |
| `NukeProjectile` | `+0x0F90` | ReadString | 4 |
| `NukeDown` | `+0x0F94` | ReadString | 4 |
| `MutateWarhead` | `+0x0F98` | ReadString | 4 |
| `MutateExplosionWarhead` | `+0x0F9C` | ReadString | 4 |
| `EMPulseWarhead` | `+0x0FA0` | ReadString | 4 |
| `EMPulseProjectile` | `+0x0FA4` | ReadString | 4 |

#### `[JumpjetControls]` @ `0x006743D0`（7 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `TurnRate` | `+0x040C` | ReadInteger | 4 |
| `Speed` | `+0x0410` | ReadInteger | 4 |
| `Climb` | `+0x0418` | ReadDouble | 8 |
| `CruiseHeight` | `+0x0420` | ReadInteger | 4 |
| `Acceleration` | `+0x0428` | ReadDouble | 8 |
| `WobblesPerSecond` | `+0x0430` | ReadDouble | 8 |
| `WobbleDeviation` | `+0x0438` | ReadInteger | 4 |

#### `[ElevationModel]` @ `0x0066D150`（3 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `ElevationIncrement` | `+0x1838` | ReadInteger | 4 |
| `ElevationIncrementBonus` | `+0x1840` | ReadDouble | 8 |
| `ElevationBonusCap` | `+0x1848` | ReadDouble | 8 |

#### `[WallModel]` @ `0x0066D1F0`（2 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `AlliedWallTransparency` | `+0x1850` | ReadBool | 1 |
| `WallPenetratorThreshold` | `+0x1858` | ReadDouble | 8 |

#### `[Maximums]` @ `0x00672230`（1 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `Players` | `+0x14D0` | ReadInteger | 4 |

#### `[Difficulty]` @ `0x0066D270`（12 键）

| 键 | 偏移 | 读法 | 宽 |
|:---|:---|:---|---:|
| `FirePower` | `+0x0000` | ReadDouble | 8 |
| `Groundspeed` | `+0x0008` | ReadDouble | 8 |
| `Airspeed` | `+0x0010` | ReadDouble | 8 |
| `Armor` | `+0x0018` | ReadDouble | 8 |
| `ROF` | `+0x0020` | ReadDouble | 8 |
| `Cost` | `+0x0028` | ReadDouble | 8 |
| `RepairDelay` | `+0x0038` | ReadDouble | 8 |
| `BuildDelay` | `+0x0040` | ReadDouble | 8 |
| `BuildSlowdown` | `+0x0048` | ReadBool | 1 |
| `BuildTime` | `+0x0030` | ReadDouble | 8 |
| `DestroyWalls` | `+0x0049` | ReadBool | 1 |
| `ContentScan` | `+0x004A` | ReadBool | 1 |

### 18.3 三种非标准形态（本轮新识别）

| 形态 | 特征 | 例 |
|:---|:---|:---|
| **外部对象** | `mov edi,edx`，字段写在 `[edi+off]`；默认值是**立即数**（`push 0x3FF00000; push 0` = 1.0），不从字段载入 | `Read_Difficulty` |
| **纯分派器** | 函数体只有三次 `call Read_Difficulty`，各传不同子对象（`lea edx,[esi+0x1538]` / `+0x1588` / `+0x15D8`） | `Read_Difficulties` |
| **写全局表** | 无对象基址；字段写进常量地址（`mov ebx,0x89EA44` 后 `[ebx+8]`），且带范围钳制（`fcomp` + `fnstsw` + `test ah,1`） | `Read_LandCharacteristics` |

`Read_Difficulty` 的 12 字段布局（`0x4B` 字节结构，每难度一份）：

```text
+0x00 FirePower   +0x08 Groundspeed  +0x10 Airspeed   +0x18 Armor
+0x20 ROF         +0x28 Cost         +0x30 BuildTime  +0x38 RepairDelay
+0x40 BuildDelay  +0x48 BuildSlowdown(bool)  +0x49 DestroyWalls(bool)
+0x4A ContentScan(bool)
```

⇒ **`[Easy]` / `[Normal]` / `[Difficult]` 三个节结构完全相同**，
各自由 `Read_Difficulties` 分派给同一段代码，只是目标子对象不同。

### 18.4 复跑

```bash
python re_atlas/tools/dump_rules_fields.py 0x0066B900   # 以及其余 9 个入口
```

**正对照按目标类型分档**：
- 普通节：双向一致 + 读者在登记表内 + 无偏移重叠；
- 外部对象（`0x0066D270`）：**改用"字段跨度不重叠"**（默认值是立即数，
  "默认载入 == 存回"这条不适用）；
- 分派器/写全局（`0x00674500` / `0x00674000`）：**空结果不计为失败**。


---

## 19. `TypeClass` 继承链与逐类字段布局（R-028）

> §11–§18 全部是 `RulesClass` 自己的字段。本节换到**另一棵继承树**：
> `[InfantryTypes]` / `[VehicleTypes]` / `[AircraftTypes]` / `[BuildingTypes]`
> 里列出的每个名字，各自指向一个 `TypeClass` 实例，那才是 `rulesmd.ini`
> 和 `artmd.ini` 里 90% 内容的落点。对战役编译器而言，这一层比
> `RulesClass` 更直接 —— 生成一张新单位/建筑，写的就是这些键。

### 19.1 继承链（按 vtable 的 CompleteObjectLocator 读出类名，非按函数名推测）

| 层 | vtable | COL 类名 | 槽 25（`LoadFromINI`） | 槽 12（`GetSize`） |
|:---|:---|:---|:---|:---|
| 1 | `0x007E2000` | `.?AVAbstractTypeClass@@` | `0x00410A60` | 0（桩） |
| 2 | `0x007EF2D8` | `.?AVObjectTypeClass@@` | `0x005F92D0` | 0（桩） |
| 3 | `0x007F4ED8` | `.?AVTechnoTypeClass@@` | `0x00712170` | 0（桩） |
| 4a | `0x007EB610` | `.?AVInfantryTypeClass@@` | `0x005240A0` | **0x0ED0** |
| 4b | `0x007F6218` | `.?AVUnitTypeClass@@` | `0x00747620` | **0x0E78** |
| 4c | `0x007E2868` | `.?AVAircraftTypeClass@@` | `0x0041CC20` | **0x0E10** |
| 4d | `0x007E4570` | `.?AVBuildingTypeClass@@` | `0x0045FE50` | **0x1798** |

**逐层委托是实测的，不是按名字推的**：七层 loader 各自的前 20 条指令里
都有一个 `call` 指向**上一层**的 `LoadFromINI`：

```
AbstractType   0x00410A60  （不再下探）
ObjectType     0x005F92D0  → 0x00410A60
TechnoType     0x00712170  → 0x005F92D0
InfantryType   0x005240A0  → 0x00712170
UnitType       0x00747620  → 0x00712170
AircraftType   0x0041CC20  → 0x00712170
BuildingType   0x0045FE50  → 0x00712170
```

⇒ **一个字段的偏移归属哪一层，由哪一层的 loader 写它决定**，
而不是由"读这个键的函数属于哪个类"决定。派生类的 loader 会**重复读**
少量继承字段（见 19.5），那些不是派生类的新字段。

### 19.2 每类字段规模 → **644 键（核验更正，原 613 作废）**

> **⚠ 2026-10-22 核验更正（R-028 核验）**：本条原报 **613 键 / 270+119** 等数字
> **已作废**。真值 **644 键（rules 446 / art 198）**。根因：工具把
> `fstp [ebp+off]` 当成「栈暂存默认值」而跳过，但 `TechnoTypeClass` 与
> `BuildingTypeClass` 的 `this` 恰好是 **EBP** ⇒ 这两个类的全部 `ReadDouble`
> 字段被静默丢弃（TechnoType 缺 **24**、BuildingType 缺 **7**，共 **31**）。
> 判据见 §19.11。正文保留旧值以供追溯，**引用请用"真值"列**。

| 类 | 旧键数 | **真值** | 旧 rules | **真 rules** | 旧 art | **真 art** |
|:---|---:|---:|---:|---:|---:|---:|
| `AbstractTypeClass` | 1 | **1** | 1 | **1** | 0 | **0** |
| `ObjectTypeClass` | 20 | **20** | 15 | **15** | 5 | **5** |
| `TechnoTypeClass` | 252 | **276** | 230 | **255** | 22 | **21** |
| `InfantryTypeClass` | 33 | **33** | 28 | **28** | 5 | **5** |
| `UnitTypeClass` | 27 | **27** | 15 | **15** | 12 | **12** |
| `AircraftTypeClass` | 10 | **10** | 6 | **6** | 4 | **4** |
| `BuildingTypeClass` | 270 | **277** | 119 | **126** | 151 | **151** |
| **合计** | **613** | **644** | **414** | **446** | **199** | **198** |

最高偏移与枚举包装器数不变（`+0x0DCC` / `+0x1780`；25 个）。

两处 rules/art 变化同源，都落在 `MovementZone`（`+0x05B4`）：
旧表标 **artmd**，真值 **rulesmd**。它的 `ecx` 从 `[esp+0x388]` 装载，
该栈槽与序言 `mov esi,[esp+0x37C]`（唯一的 INIClass 形参）是**同一槽**
⇒ 调用方传入的 `rulesmd`。旧表误标源于 `cur_ini` 只写不复位，继承了
前一条 `mov ecx,0x887180`（`0x716044`）的 ART。见 §19.11。

**31 个新增键里 0 个"未定"**：全部有偏移、宽度、读取器，且每个偏移都被
**本类构造器**在同一偏移写过默认值（24/24、7/7，见 §19.11 P12）。

### 19.3 ★ 同一个 loader 同时读两个 INI 文件

这是对编译器最要紧的一条，也是这批 loader 与 `RulesClass` 自己的
loader 最大的结构差异。

四个派生类的 `LoadFromINI` **都**在函数体里出现
`mov ecx, 0x887180` —— `0x887180` 是 **`CCINIClass` 全局实例 `INI_Art`**：

- 依据一（字节，**2026-10-22 核验后修正**）：`0x887180` 落在 `.data` 的
  **BSS 尾部**（`.data` raw 只覆盖 VA `0x812000..0x87E000`），**静态读 4 字节得空**，
  所以"直读它的 vptr"这条证据**不成立**。真正成立的是**写入点**：
  `0x0040E031` 处 `mov dword ptr [0x887180], 0x7E1AF4`（全 `.text` 唯一一处），
  而 `0x7E1AF4` 的 COL 解出的类名是 `.?AVCCINIClass@@`；
- 依据二（YRpp）：`CCINIClass.h` 静态成员 `INI_Art{0x887180}`；
- 依据三（本文 §0）：该结论在 R-015 已双通道核验。

而函数的 `this`（TC）之外的另一个 INIClass 来自**调用方压栈的参数**
（`mov esi,[esp+0x37C]` 之类），那是 `rulesmd.ini`。

⇒ **同一个 `HTNK` 节，其 `Strength` 必须写进 `rulesmd.ini`，
其 `TurretAnimX` 必须写进 `artmd.ini`。** 写错文件时引擎**不会报错**，
只是那个键永远读到默认值。这正是 `BuildingTypeClass` 里
**151/270 个键属于 artmd** 的原因 —— 建筑的动画/帧偏移几乎全在美术文件里。
（核验后分母为 **277**，artmd 侧仍为 **151**，见 §19.2。）

工具输出的 `INI` 列即此归属，逐行可查。

### 19.4 两个节名缓冲：`+0x24` 与 `+0x1F8`

派生 loader 的 `section` 实参不总是字面量，而是 `lea reg,[this+0x24]`
或 `lea reg,[this+0x1F8]` 得到的两个**缓冲区**：

| 偏移 | 内容 | 语义 |
|:---|:---|:---|
| `+0x24` | 类型自身名（`HTNK` / `MTNK` …） | 该名字在**两个文件里都可能是节名** |
| `+0x1F8` | 被 `Image=` 改写后的名字 | **artmd 专用节名** |

据此得到一条**单向不变量**，实测 **613 行里 0 违反**：

> `+0x1F8` 作为 section 的读取，**从不**走 `rulesmd` 的 INIClass。

反向不成立：`+0x24` 既可以配 rulesmd 也可以配 artmd
（3 个键实测走 artmd），因为类型名在 artmd 里同样是一个节。
第一版把这条写成双向的，产出 20 条假"节/INI不符"（见 CONFLICTS G-33 的邻条）。

### 19.5 派生类的 loader 会重复读继承字段

`UnitTypeClass` 在 `+0x67C` 读 `SpeedType` —— 那是 `TechnoTypeClass` 的字段。
这类"继承字段重读"共 1 处（UnitType），不计入派生类自有字段。
`BuildingTypeClass` 另有 1 处 `+0x67C` 读 **`WaterBound`** ——
**同名偏移、不同键、不同属性**：建筑不移动，于是基类的 `SpeedType` 槽
被复用为 `WaterBound`（`WaterBound=yes` → 存 5，`no` → 存 -1，
见 `0x0045FF85..0x0045FFA9` 的 `cmp eax,5 / sete / and 6 / dec`）。
这是**真实的引擎复用**，不是解错：`TechnoTypeClass` 的 loader 不写 `+0x67C` 的那个键，
`BuildingTypeClass` 的 ctor 也不通过 `esi` 直接写它（由 19.7 的指针环覆盖）。

### 19.6 枚举包装器：25 个键不经过裸 `Read*`

`PipScale`、`Armor`、`Foundation`、`SpeedType`、`BuildCat`、`Owner`、
`GuardRange`、`Category`、`VHPScan`、`MovementRestrictedTo`、`SuperWeapon`…
这些键走的是一个 **cdecl 小助手**，签名与 `Read*` 相同
`(section, key, default)`：内部先调真 reader 拿到字符串，再映射成枚举值。

判据是机械的，不是手写清单：

> 函数体里**直接调用**五个 `Read*` 之一，**且**它自己的 `ret` 带
> ≥ 8 字节的立即数参数（cdecl 由被调方清栈）。

25 个键命中该判据。`0x00428B80`（`char*` → 对象指针）与
`0x007514D0`（解析器）虽然也出现在这些站点，但因体内不调 reader 而被排除 ——
它们是**转换步骤**，其后那次 store 属于更早的那个键。

### 19.7 构造器链独立交叉核对（另一条证据线）

字段表和构造器来自完全不同的函数、不同的调用点，
所以两者一致**不可能是同一次解析错误的产物**。逐类对账：

| 类 | loader 写偏移 | 本类 ctor | 基类 ctor | 指针环清零 | 未解 |
|:---|---:|---:|---:|---:|---:|
| `InfantryTypeClass` | 33 | 33 | 0 | 0 | **0** |
| `UnitTypeClass` | 27 | 26 | 1 | 0 | **0** |
| `AircraftTypeClass` | 10 | 10 | 0 | 0 | **0** |
| `BuildingTypeClass` | 269 | 136 | 1 | 132 | **0** |

`BuildingTypeClass` 的 132 个不是漏洞，而是**指针环清零**：

```
lea  eax, [esi + 0xF5C] ; mov ecx, 0x15 ; mov [eax],edi ; ... ; add eax,0x44
```

21 项 × 0x44 字节 = 1428 字节，罩住 `+0x0F5C..+0x14DF` 的 132 个动画字段
（17 组 × 8 个：`ActiveAnimX/Y/ZAdjust/YSort/Powered/…` 到
`SuperLowPowerPoweredSpecial`）。**按 `[esi+off]` 扫构造器永远扫不到。**

构造器链本身也是实测的：`BuildingType 0x0045DD90` 的首个 `call` 是
`TechnoType 0x00710AF0`，后者首个 `call` 是 `ObjectType 0x005F7320`，
再下一个是 `Abstract 0x00410960`。

### 19.8 默认值的三类形态（0 真缺失）

| 形态 | 例 | 标记 |
|:---|:---|:---|
| 字段自读（默认 = 该字段当前值） | 绝大多数 | `一致` |
| 立即数默认 | `Speed` 前有 `push -1` | `立即数默认(-1)` |
| 跨键默认 | `EliteAirstrikeRechargeTime` 前有 `push eax`（= `EliteAirstrikeTeam` 的新值） | `跨字段(+0x…)` |
| 栈缓冲默认 | `ReadString` 的默认是 `lea reg,[esp+…]` 缓冲，不是字段 | `栈缓冲默认` |

修完这四类后**"默认缺失"为 0**（第一版报 31 行，全部是上述后三类被误记）。

**`Speed = -1` 是唯一的立即数默认** —— 键缺席时速度取 -1，
即"无速度类型"，是引擎设计而非缺失。

### 19.9 工具与证据

- 工具：`re_atlas/tools/dump_typeclass_fields.py`（EXIT=0，逐类"全部通过"）
- 证据：`re_atlas/evidence/typeclass_fields.txt`（688 行，613 键）
- 复跑：`python re_atlas/tools/dump_typeclass_fields.py`
- 输出逐字节可复现（仅 CRLF/LF 差异，与 R-027 同）

### 19.10 余项

| 编号 | 内容 |
|:---|:---|
| A-40 | `SuperWeaponTypeClass` / `WeaponTypeClass` / `WarheadTypeClass` / `BulletTypeClass` / `AnimTypeClass` / `OverlayTypeClass` / `TerrainTypeClass` / `SmudgeTypeClass` / `VoxelAnimTypeClass` 等**其余 15 个 TypeClass** 尚未接入本工具 |
| A-41 | `BuildingTypeClass` 的 132 个动画字段已定位到 `+0x44` 步长的结构，但该**子结构的字段名表**未解 |
| A-42 | 枚举包装器的 25 个键其**枚举值表**（字符串 → 整数）未解，只解出落点偏移 |
| A-43 | 联机会话 loader `0x6980C0`（15 键，`RA2MD.INI` 的 `[MultiPlayer]`/`[SerialDefaults]`）已由爆炸半径普查发现，**未接入任何工具**；属 R2-9 只读范围。见 §19.11(g) |

### 19.11 R-028 核验（2026-10-22）—— 三条推翻 + 一条新增事实

核验方式：**另写一个解析器**（`tools/verify_r028_claims.py`，锚定"读者调用点"，
不复用原工具的 `pending` 状态机），两边逐行对账；再以异族盲验独立复核。
门禁 **49/49 PASS、EXIT=0、两次运行逐字节相同**。

#### (a) 推翻：这两个类的 `ReadDouble` 字段整批丢失（31 条）

原工具 `dump_typeclass_fields.py` 的 `fstp` 分支有这条规则：

```python
if op2.mem.base in (X86_REG_ESP, X86_REG_EBP):
    continue          # staging the default argument, not a field
```

把 **EBP** 和 ESP 一起当成"栈暂存"。但 `this_register()` 对这两个类解出的
对象寄存器**就是 EBP**：

| 类 | `this` | `mov <reg>,ecx` 地址 |
|:---|:---|:---|
| `TechnoTypeClass` | **ebp** | `0x712180` |
| `BuildingTypeClass` | **ebp** | `0x45FE5F` |

⇒ 两个类里所有 `fstp [ebp+off]` 字段写全部被丢弃。

| 类 | 旧 | 真 | 丢失 |
|:---|---:|---:|---:|
| `TechnoTypeClass` | 252 | **276** | **24** |
| `BuildingTypeClass` | 270 | **277** | **7** |

**三条独立证据**：

1. **对账**：两个实现之间 `missing=0`（旧表有的新表全有），
   `extra=31`，且 **31/31 全是 `ReadDouble`**（P11a/P11b）。
2. **构造器交叉**：这 31 个偏移，**每一个**都被本类构造器在同一偏移写过
   默认值（TechnoType 24/24、BuildingType 7/7，P12）。构造器与 loader 是
   不同函数、不同调用点，一致不可能是同一次解析错误。
3. **机制复现**：模拟"跳过 `fstp [ebp+off]`"后，本门禁的计数**精确落回
   252 / 270**（N4）。这是把缺陷归因到原因，而不是猜。

**边界**：`TechnoTypeClass` 另有两处 `fstp [ebp+off]`（`+0x360` `0x7160F6`、
`+0x368` `0x71611D`）是 `fild/fmul/fadd` 的**派生计算值**，不是 INI 键，不计入 31。

#### (b) 推翻：`MovementZone` 属 **rulesmd**，不是 artmd

`+0x05B4`，唯一调用点 `0x716079`，`ecx` 从 `[esp+0x388]` 装载。
该栈槽与序言 `mov esi,[esp+0x37C]`（唯一 INIClass 形参）**是同一槽**：

```
0x712179  mov esi,[esp+0x37C]   ; esp=E-888 -> E+4 = arg0  (rulesmd)
0x716071  mov ecx,[esp+0x388]   ; esp=E-900 -> E+4 = arg0  (同一个)
0x716079  call 0x474E40         ; WRAP，枚举映射
```

旧表标 artmd，是 `cur_ini` **只写不复位**：它继承了 12 条指令前
`0x716044 mov ecx,0x887180`（ART）的状态。修正后 `cur_ini` 遇
`mov ecx,[mem]` / `mov ecx,<其它立即数>` 一律复位为 RULES。

#### (c) 推翻：`0x887180` 的"直读 vptr"证据不成立（结论不变）

`0x887180` 在 BSS，静态读 4 字节得空。成立的证据是**唯一写入点**
`0x40E031: mov dword ptr [0x887180], 0x7E1AF4`，以及 `0x7E1AF4` 的 COL 类名
`.?AVCCINIClass@@`。⇒ `INI_Art` 结论保留，**依据改写**。

#### (d) 新增事实：`ReadDouble` 会静默吃掉 `%`（★ 写 INI 必读）

`ReadDouble`（`0x5283D0`）读完字符串后会：

```
0x528564  push 0x2525             ; "%%"
0x52856E  call 0x7CAF30           ; strstr
0x528578  je   0x528588           ; 没找到 % -> 原值
0x52857E  fmul qword ptr [0x7E3808]   ; = 0.01
```

`0x7E3808` 的 8 字节是 `7b14ae47e17a843f` = **0.01**（已实测解出）。

⇒ **任何走 `ReadDouble` 的键，写成 `50%` 会被静默读成 `0.5`。**
这不是格式错误、不报错、不留痕。对 ③ 的意义：战役编译器生成 rulesmd 时
若沿用人写的百分比写法，一整类数值键会**悄悄差 100 倍**。

已知走 `ReadDouble` 的键共 **35 个**（31 个本轮新增 + 4 个旧表已有的
`LightIntensity` / `LightRedTint` / `LightGreenTint` / `LightBlueTint`），
完整清单见 `evidence/typeclass_fields_v2.txt` 的 `读者` 列（`ReadDouble`）。

#### (e) 广度和诚实边界

- 644 行两实现**逐行一致**（键名 / 偏移 / 宽度 / INI 归属四列全等），
  唯一差异是旧表的上述两处，修正后归零。
- `+0x1F8` 单向不变量复核：**238 个字面量 INIClass 站点 0 违反**；
  另有 **1 个**站点的 INIClass 来自栈参数、静态不可判（`TurretAnimGarrisoned`
  `0x464553`），已如实标注为 unresolved 而不计入断言。
- **口径边界**：两张表都只收"键 → 标量字段"。另有 **153 个**键读进
  **内联 `char[]` 缓冲区**（`read -> lea reg,[this+off] -> rep movsd`），
  如 `TurretAnim` / `TurretAnimDamaged` / `TurretAnimGarrisoned`
  落在 `+0x11B0..+0x11DF`。这些是**真键真偏移**，但不在"标量字段"口径内，
  两张表都未列 ⇒ **644 不是键总数，是标量字段数**（P11d）。
- `SuperWeapon`（`+0x16F0`）仍显示"默认缺失"：它的默认值取自字段自身
  （`mov edx,[ebp+0x16F0]` 紧邻 `push`），是工具的位置式取默认值口径所致，
  不是新事实。

#### (f) 工具与证据

| 件 | sha256（前 16） |
|:---|:---|
| `tools/verify_r028_claims.py` | `5fd1d9e1d0d9c377` |
| `tools/dump_typeclass_fields.py`（已修） | `03135c34a02d40af` |
| `evidence/typeclass_fields_v2.txt`（644 行） | `065ef20c1f458a79` |

复跑：`python re_atlas/tools/verify_r028_claims.py`（EXIT=0，49/49）
`python re_atlas/tools/dump_typeclass_fields.py`（EXIT=0，`小结` 七行全"全部通过"，
仅 BuildingType 的 `SuperWeapon` 一行按上述口径标"默认缺失"）

#### (g) 爆炸半径普查（同轮追加）：这个缺陷还有没有别处？

修好两个类之后必须回答"同一假设还在哪被用过"。
`tools/census_ebp_this_loaders.py`（EXIT=0，6/6，见 `evidence/ebp_this_census.txt`）

| 项 | 数 |
|:---|---:|
| 根（`.text` 内 rel32 E8/E9 + `.rdata` 成组 `.text` 指针） | 15,751 |
| 去重后函数 span / 已覆盖跳过 | 13,193 / 2,525 |
| 解析出 `this` 的函数 | 4,339 |
| **`this`=EBP 且调 `Read*`** | **13** |
| 已覆盖 / **未覆盖** | 2 / **11** |

`tools/classify_ebp_this_candidates.py`（EXIT=0）把 11 个逐个定性：
**`KEY_FIELD` 仅 2 个**，其余是派发器（5）或无紧邻字面量键（4）。

1. `0x6686C0` = **`RulesClass::Init`**（R-021 的 31 节载入顺序），`this` 在 EBP
   （`0x6686CD`），仅 1 键 `Players`→`+0x14D0`。**派发层，不是字段表。**
2. `0x6980C0` = **联机会话/序列号设置 loader**（新，15 键）：
   `PortBase` / `PortPool` / `SendDelay` / `PortNumberOverride` / `PhoneIndex` /
   `CheckHeap` / `WOLLimitResolution` / `LastNickSlot` / `Color` / `ColorEx` /
   `Side` / `SideEx` / `WOLTaunts` / `LANTaunts` / `WOLScrollText` /
   `LANScrollText`；节 = `RA2MD.INI` 的 `[MultiPlayer]` / `[SerialDefaults]`。
   调用方 `0x52E119 mov ecx,0xA8B238`（`GameMode` 全局）⇒ 联机路径。

⇒ **RulesClass 那棵树不在半径内**：`Read_General`(`0x66D530`) 与
`Read_AudioVisual`(`0x6691E0`) 的 `this` 都是 **ESI**（`0x66D547 mov esi,ecx`），
普查 P3 反面对照 PASS。因此 **H-016/H-017/H-018 的 268/279/151 等数字不受
G-41 影响**（已实测，非推断）。

⇒ **③ 的受影响面到此为止**：除已修的 31 条，没有第二个同类漏收；
新增的 `0x6980C0` 属 R2-9 联机（只读），不进 ③ 的配置面。

---

## 20. R2-2 结题总览（R-029，2026-10-22）

R2-2「INI 与规则加载」自 R-015（2026-10-21）至 R-028（2026-10-22）共 **14 轮**。
核心闭环已完成，本篇此后**只按需补充，不再开 INI 新轮**（§3 P0 项结题）。

### 20.1 一图总览：INI 读取栈

```text
CCINIClass（单份 INI 文件，0x58 推定 / 0x55 下界）
  : INIClass（0x40）
      +0x04/+0x08  查询缓存（Reset 0x526B00 清这两个）
      +0x0C        List<INISection*>（+0x10/+0x1C 首尾哨兵）
  ├─ GetSection(节)   0x526810   ; CRC32 排序数组 + 二分（0x52B750/0x52B720）
  │                            ; 未命中 → 哨兵 0xB7882C（不是 NULL）
  ├─ ReadString        0x528A10, ret 0x14（§4）
  ├─ INISection        0x44（push@0x525DEA）  节名 CRC32 可缓存
  ├─ INIEntry          0x28（push@0x526039）  键名→值，节内线性查找
  └─ 读族 ReadBool/ReadInteger/…（§10）
        ReadBool 只认**首字符**；ReadInteger 尾 h 走十六进制

RulesClass（0x18C0，ctor 0x665650，分配点 push@0x52BABE）
  ├─ 31 个节的载入顺序（§13；Read_File 在解析期驱动）
  ├─ [General] 268 标量字段（279 键、12 列表型）（§17）
  ├─ [AudioVisual] 151/152（§16）
  ├─ 其余 10 小节全解（§18）
  └─ 18 个设置键载入后**镜像到独立全局**（ShortGame→0xA8B262）；9 个无镜像（§15.3）

TypeClass 继承链（§19）——键分在**两个文件**
  AbstractType(1) → ObjectType(20) → TechnoType(252) → {Inf(33), Unit(27), Air(10), Bld(270)}
  合计 613 键，0 未定；rulesmd 414 / artmd(INI_Art 0x887180) 199
  Building 的 151/270 属 artmd —— 写错文件不报错，键永远读默认值
  每层 LoadFromINI = 虚表槽 25；尺寸 = 槽 12；构造器链 269/269 全归因（含 132 指针环）
```

静态全局 `CCINIClass` 共 6 个（§3）：`0x887048`（INI_Rules，指针）/ `0x887180`（INI_Art）
等；第 6 个 `0x0089F518` 身份未定（I-3）。

### 20.2 G 系坑点汇总（按危害分类，编号见 CONFLICTS.md）

14 轮踩出 **34 个坑（G-1…G-35，G-3 编号跳空）**。按可迁移性分六类：

**A. 静默失效（最难防：输出看着正常，实为空/为假）**

| # | 一句话 |
|:--|:---|
| G-23 | capstone 单次 `md.disasm(.text)` 在 `0x46F5A0` **静默停止**，只覆盖 9% ⇒ 键索引旧值 478/473/427 作废，重算 2,426/2,305/1,893 |
| G-24 | 窗口 `0x1000` 腰斩长函数，**无任何提示** ⇒ 键归属跨函数泄漏 |
| G-10 | 两个"0 命中"陷阱：`op_str` 逗号后空格、小立即数渲染成十进制 ⇒ 10 个核心类差点漏掉。兜底 = **肯定对照**（同文件全类命中才算绿） |
| G-21 | `read_va` 越段读把 `.detour` 字节当 BSS 数据 ⇒ 读任何地址先过段表 |
| G-28 | 正对照只绑一个输入就不是对照；绑**无关对象**才算（负控同理，见 §6 铁律） |

**B. 判据错置（结构层面的"相邻 ≠ 同类"家族）**

| # | 一句话 |
|:--|:---|
| G-14 | `.rdata` 虚表首尾相接，**地址相邻 ≠ 同类**（R-015 两条撤回的共同根因） |
| G-9 / G-4 / G-5 | 身份槽是 **vtable[11]**（WhatAmI）；[12]=GetSize 不普适，成对双验证（69 类零冲突）才是安全取法 |
| G-11 | `vtable[4]` 是 `IsDirty` 不是 `Load` —— 槽位语义逐槽定名，不可类推 |
| G-12 | 虚表尾部出现 `.rdata` 值是 **COL 指针**不是虚函数 |

**C. 语义过度解读**

| # | 一句话 |
|:--|:---|
| G-20 | "第一个 X"≠"只处理 X"：`Read_File` 被我读成单节处理 |
| G-25 | 按"函数体内所有字面量 push"取键 ⇒ 参数、节名混进键表 |
| G-26 | `[reg+off]` 匹配**既漏又误**；单值"消费点"是假精度 |
| G-27 | "字符串不在 `.rdata`" ≠ "键读不到"（运行期拼键存在） |
| G-29 | 为"修到一致"抹平引擎语义 ⇒ 伪造 100%（真引擎有跨键默认、字段复用） |
| G-31 | 三类目标（找键/定字段/归属文件）不能共用一套判据 |
| G-33 | `push eax` 既是节名缓冲又是上一键返回值，**只能靠上一条指令定夺** |
| G-34 | "默认值缺失"混三种成因，只有一种算失败；全报 `None` 掩盖真缺陷 |

**D. 可复现性**

| # | 一句话 |
|:--|:---|
| G-30 | 判据依赖调用方输入 ⇒ 不可复现；工具必须自足可跑 |
| G-6 | 语料同时混 `VA` 与 `RVA−ImageBase` 两列 ⇒ 先钉口径 |

**E. 本线自纠（撤回留痕制）**

G-15（`INIClass` 不继承 `VectorClass`）、G-16（`CCINIClass` 非三基类多继承，
是一个 `List` 成员）、G-17（`List<T>` 尺寸算错差点伪造冲突）、
G-18（按声明顺序朴素相加错算尾部偏移）、G-19（节名恢复三个连锁判据错）、
G-8（`0xB0C110` = `SwizzleManagerClass::Instance` 非字段注册表）。
全部保留原文于 §8，**只追加更正不删除**。

**F. 对上游语料/ATLAS 的翻案**

G-1（`TeamTypeClass` 288→**248**）、G-2（`AITriggerTypeClass` 256→**272**）
—— 两案均已异族双通道核验；G-13（语料错注 `0x887180` 是 INI_Art 不是 rulesmd）。

### 20.3 核验台账（如实，不夸大）

| 批次 | 内容 | 异族核验 |
|:---|:---|:---|
| R-016 八条 | INIClass 结构、`0x44/0x28`、CRC32 二分、大小写敏感、`Reset`、哨兵、析构、INI_Art | ✅ 3 票确认（千问×1 + DeepSeek×2；**边界见 §7.2**：有效家族只 2 个、任务书含锚定） |
| G-1 / G-2 | 两条实例尺寸翻案 | ✅ 已核验（双通道） |
| R-017 读族 | 读族规则、`ReadBool`/`ReadInteger` 解析（§10） | ✅ **已核验**（R-030：千问 qfmodel 异族盲验 18C/0R/1U + 机器门禁 53/53；1 子句推翻已更正，见 §10.3/§10.6） |
| R-018 / R-019 | 键→字段、全引擎键索引 | 🟡 **进行中（R-031）**：§11 机器门禁 21/21；GLM 异族盲验在飞；§12.3「% 键只有一处」已本地推翻（见 §12.2/12.3 补注、G-37） |
| R-021 / R-022 / R-023 | RulesClass 节表、651 键清单、字段布局+镜像全局 | ✅ **R-021 ✅ / R-023 ✅ / R-022 ⏳**：R-021 门禁 34/34 + 异族盲验（推翻 3 条，见 §13）；**R-023 门禁 22/22 PASS + 异族盲验**（6 项中 5 项独立一致、1 项纠正我方函数起点），推翻/修正 3 条（边界 292 字节差且切掉唯一成功出口、全局非单次写 208 处、ModemGst 第二镜像块 17/18），见 §15.3 |
| R-024…R-027 | [AV]、[General] 268、其余 10 小节 | ⏳ **未核验**（H-017/018） |
| R-028 | TypeClass 613 键 + 两文件归属 | ✅ **已核验（R-028 核验）**：独立解析器门禁 **49/49**、EXIT=0；**推翻 3 条**（613→**644** 键、`MovementZone`→rulesmd、`INI_Art` 依据改写入点）+ 新增 `%` 语义。见 §19.2 / §19.11 |

⇒ **核验欠账 = R-018 部分 + R-022 + R-024…R-027**（H-015 / H-017 / H-018）。
R-017 于 R-030 闭，**R-028 于 R-028 核验轮闭**（H-019），
**R-021 于 R-021 核验轮闭**（H-014），**R-023 于 R-023 核验轮闭**（H-016），
R-020 是核验轮无新结论。
DeepSeek/千问两个既定通道均报 `provider-not-found`，
异族复核改走可用代理完成（R-023 轮：收窄版 3 问，先独立推导后对断言，
反查出我方一处函数起点错误 —— 见 §15.3 第 5 点）。

### 20.4 证据与工具清点

- 工具 11 个（INI 域）：`dump_ini_nodes` / `dump_ini_readers` / `dump_ini_keymap` /
  `dump_ini_keyindex` / `dump_ini_globals` / `dump_rules_sections` / `dump_rules_keys` /
  `dump_rules_fields` / `dump_rules_consumers` / `dump_typeclass_family` /
  `dump_typeclass_fields` —— 各自可复跑、EXIT=0、带负控。
- 证据：`evidence/ini_*.txt`、`evidence/rules_fields*.txt`（含逐小节分文件）、
  `evidence/typeclass_fields.txt`（688 行 / 613 键）。
- 交接：H-010…H-019 十条（除结构批次外均标未核验）。

### 20.5 结题后边界

- 本支柱转**按需补充**模式：A-40/41/42、I-3、L-24/25/26 挂起，不排新轮。
- 后续若 R2-3（生产建造）等子系统撞进 INI 域，引用本篇结论、不重开轮次。
- **例外**：§20.3 的核验欠账属 §3 P0，不随结题关闭 —— 每轮至多清 1 批，
  直到 R-017…R-028 各批次过异族复核。
