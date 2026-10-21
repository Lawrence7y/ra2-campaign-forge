# R1/R2 通用：`AbstractClass` 主虚表逐槽定名 [实证]

更新：2026-10-21（RE-ATLAS R-014）

本篇把 `AbstractClass` 主虚表（`0x007E1F50`）的 26 个槽逐一定名，
并**撤回** `kb/11_class_layouts.md` §6 里"槽 4 = Load"的标注。

**为什么值得做**：`kb/20_vtable_contract.md` 只定了槽 11/12。
但任何"遍历/克隆/存档"补丁都会碰到 0–7 这一段的 COM 槽，
槽号错一位就等于调用语义完全不同的函数。

---

## 0. 槽位全表

`AbstractClass` 主虚表 `0x007E1F50`。RTTI 记 24 槽；实测第 25 项（`+0x60`）**不是函数**，
是 `INoticeSource` 接口子表的 **RTTI COL 指针**（见 §4.1）。

| 槽 | `+0x` | 地址 | 体首 | 定名 | 依据 |
|---:|---:|:---|:---|:---|:---|
| 0 | `00` | `0x00410260` | `mov eax,[esp+0xC]; push ebx; test eax,eax; jne; mov eax,0x80004003` | **`QueryInterface`** | 三参数 `ret`、`E_POINTER` 守卫、写 `[arg]` |
| 1 | `04` | `0x00410300` | `mov eax,1; ret 4` | **`AddRef`** | 恒返 1（`this` 参数） |
| 2 | `08` | `0x00410310` | `mov eax,1; ret 4` | **`Release`** | 恒返 1 |
| 3 | `0C` | `0x004C9150` | `xor eax,eax; ret` | **`GetClassID`**（抽象桩） | 基类不实现；派生类逐个覆写成写 CLSID 的版本 |
| 4 | `10` | `0x00410450` | `mov dl,[ecx+0x20]; test dl,dl; sete al; ret 4` | **`IsDirty`** | ★ **返回 `!Dirty`**，见 §1 |
| 5 | `14` | `0x004C9150` | `xor eax,eax; ret` | **`Load`**（抽象桩） | 派生类覆写 |
| 6 | `18` | `0x004C9150` | `xor eax,eax; ret` | **`Save`**（抽象桩） | 派生类覆写 |
| 7 | `1C` | `0x004103E0` | `push esi; mov esi,[esp+0xC]; test esi,esi; jne; mov eax,0x80004003` | **`GetSizeMax`** | 两参数 `ret 8`、`E_POINTER` 守卫 |
| 8 | `20` | `0x004105A0` | 写 4 个 vptr + `test al,1` + `call 0x7C8B3D` | **析构**（虚表指向它，非 deleter） | 标量删除析构；见 §2 |
| 9 | `24` | `0x00410470` | `ret` | `Init`（空） | 无体 |
| 10 | `28` | `0x00410480` | `ret 8` | `PointerExpired`（空） | 两参数 |
| 11 | `2C` | `0x004C9150` | `xor eax,eax; ret` | **`WhatAmI`**（抽象桩） | 派生类返类型 ID，见 `kb/20` |
| 12 | `30` | `0x004C9150` | `xor eax,eax; ret` | **`Size`/`GetSize`**（抽象桩） | 派生类返尺寸 |
| 13 | `34` | `0x00410410` | 写 `+0x10` dword、写 `+0x20` bool | **`AbstractClass::Save`** | 见 §3 |
| 14 | `38` | `0x00410490` | `or eax,-1; ret` | `CalculateChecksum` | 恒返 −1 |
| 15 | `3C` | `0x004104A0` | `xor eax,eax; ret` | `GetOwningHouseIndex` → −1? 实为 0 | 见 §4 存疑 |
| 16 | `40` | `0x004104B0` | `xor eax,eax; ret` | `GetOwningHouse` → nullptr | |
| 17 | `44` | `0x00410440` | `mov al,1; ret` | `IsDead` → true | |
| 18 | `48` | `0x004104C0` | 从 `0x887680/+0x84/+0x88` 拷 3 个 dword 到 `[arg]` | `GetCoords`（默认实现） | 写 12 字节；源是 `.data` 模板，非类内字段 |
| 19 | `4C` | `0x004104F0` | `mov eax,[ecx]; sub esp,0xC; push …; call [eax+0x48]` | `GetDestination` | **转发槽 18**，再拷 12 字节（3 dword） |
| 20 | `50` | `0x00410520` | `xor al,al; ret` | `IsOnFloor` → false | |
| 21 | `54` | `0x00410530` | `xor al,al; ret` | `IsInAir` → false | |
| 22 | `58` | `0x00410540` | 与槽 19 同构（`call [eax+0x48]`） | `GetAltCoords` | **转发槽 18**，仅 `ret` 差别（`ret 4` vs `ret 8`） |
| 23 | `5C` | `0x00410570` | `ret` | `Update`（空） | |
| 24 | `60` | `0x007FB160`（`.rdata`） | — | **不是函数**：RTTI COL 指针 | 见 §4.1 |

**槽 0–7 与 YRpp `AbstractClass` 的虚函数声明顺序逐一对应**
（`YRpp/AbstractClass.h:71,72,73,76,79,80,81,83`）：
`QueryInterface / AddRef / Release / GetClassID / IsDirty / Load / Save / GetSizeMax`。

> ⚠ **YRpp 的注释把 `IsDirty` 排在 `GetClassID` 之后，槽位一致；
> 但它把 `~AbstractClass` 标在接口组之后（行 97）——实测析构在槽 8（`+0x20`），
> 正好是 8 个接口槽之后的第一个。两者吻合，前提是"接口组占 0–7"。**

---

## 1. ★ 撤回：槽 4 是 `IsDirty`，不是 `Load`

`kb/11_class_layouts.md` §6 的槽位表写：

```text
| 4 | 0x00410450 | mov dl,[ecx+0x20] | 读 AbstractClass 的 +0x20 bool |
```

这行**描述是对的，但没定名**。`kb/20_vtable_contract.md` §7 的未闭合表里
我把它写成 "`vtable[4]` = `Load`"——**这是错的**。

**字节证据**（`0x00410450` 全函数，仅 6 条）：

```text
0x00410450  8B 4C 24 04         mov  ecx, [esp+4]      ; this
0x00410454  33 C0               xor  eax, eax
0x00410456  8A 51 20            mov  dl, [ecx+0x20]    ; Dirty 标志
0x00410459  84 D2               test dl, dl
0x0041045B  0F 94 C0            sete al                ; ★ al = (Dirty == 0)
0x0041045E  C2 04 00            ret  4
```

**返回 `!Dirty`** —— 这是 `IsDirty()` 的定义，不是 `Load`。
`Load` 的语义是"从流里读"，必然有流参数与写操作，这个函数两者都没有。

三个独立佐证：
1. `AbstractClass::Save`（槽 13）末尾**不清 Dirty**（见 §3），
   所以 `IsDirty` 必须由别处清——符合 COM 的 `IPersistStream` 契约。
2. YRpp `AbstractClass.h:79` 把 `IsDirty()` 声明在 `Load` 之前，
   与之对应的槽号正好是 4（`Load` 是 5）。
3. 真正的 `Load` 在槽 5：派生类覆写它，且**体首先调 `0x410380`**
   （`TEventClass` 的槽 5 `0x0071F8C0` 起点即 `call 0x410380`），
   `0x410380` 才是有流参数的那一族。

### 1.1 槽 5 / 槽 6 与槽 13 的分工

这三槽容易混，明确一下：

| 槽 | 名字 | 做什么 | 谁调 |
|---:|---|---|---|
| 5 | `Load(IStream*)` | 从流反序列化 | 引擎读档 |
| 6 | `Save(IStream*, BOOL)` | 写流，**并且**按 `BOOL` 决定是否清 Dirty | 引擎存档 |
| 13 | `AbstractClass::Save` | **只写 `+0x10` 与 `+0x20` 两个字段**，是槽 6 的被调者 | 各类自己的 `Save` 调用 |

`TEventClass` 的例子把三层串起来：

```text
slot 6 = 0x0071F930  -> call 0x410320  （Save 包装，E_POINTER 守卫）
slot 5 = 0x0071F8C0  -> call 0x410380  （Load 包装，E_POINTER 守卫）
slot13 = 0x0071F820  -> call 0x410410  （AbstractClass::Save）
```

⇒ **槽 13 不是 COM `Save`，它是"基类字段的序列化块"**，
派生类的槽 6 会调用它。前轮把槽 13 直接叫 "`Save`" 会与槽 6 撞名，
本篇统一称 **`AbstractClass::Save`（基类序列化块）**。

---

## 2. 槽 8 是析构，不是标量删除析构

`0x004105A0` 写 4 个 vptr：

```text
0x004105A0  8A 44 24 04         mov  al, [esp+4]
0x004105A5  8B F1               mov  esi, ecx
0x004105A7  A8 01               test al, 1
0x004105A9  C7 06 50 1F 7E 00   mov  [esi+0x00], 0x7E1F50
0x004105AF  C7 46 04 ...        mov  [esi+0x04], 0x7E1F34
0x004105B6  C7 46 08 ...        mov  [esi+0x08], 0x7E1F2C
0x004105BD  C7 46 0C ...        mov  [esi+0x0C], 0x7E1F24
0x004105C4  74 09               je   0x4105CF
0x004105C6  56                  push esi
0x004105C7  E8 71 85 3B 00      call 0x7C8B3D          ; operator delete
0x004105CF  8B C6               mov  eax, esi
0x004105D1  5E                  pop  esi
0x004105D2  C2 04 00            ret  4
```

**`ret 4` + 返回 `esi`（this）** ⇒ 这是**标量删除析构**的完整形态
（`test al,1` 决定是否 `operator delete`，但无论如何返回 `this`）。
所以 YRpp 行 97 的 `virtual ~AbstractClass()` 就是它。

（YRpp 同时声明了一个普通析构与一个标量删除析构，MSVC 会把二者合并成一个槽。）

---

## 3. `AbstractClass::Save`（槽 13）全解

```text
0x00410410  56                push esi
0x00410411  8B F1             mov  esi, ecx
0x00410413  57                push edi
0x00410414  8B 7C 24 0C       mov  edi, [esp+0xC]     ; IStream*
0x00410418  8B 46 10          mov  eax, [esi+0x10]    ; ★ 字段 1
0x0041041B  8B CF             mov  ecx, edi
0x0041041D  50                push eax
0x0041041E  E8 2D 19 09 00    call 0x4A1D50           ; Write dword
0x00410423  8A 4E 20          mov  cl, [esi+0x20]     ; ★ 字段 2
0x00410426  51                push ecx
0x00410427  8B CF             mov  ecx, edi
0x00410429  E8 72 18 09 00    call 0x4A1CA0           ; Write bool（setne 归一化）
0x0041042E  5F                pop edi
0x0041042F  5E                pop esi
0x00410430  C2 04 00          ret 4
```

**基类只写两个字段**：`+0x10`（dword）与 `+0x20`（bool）。

与 YRpp `AbstractClass` 属性表对照（`YRpp/AbstractClass.h` 的 `Properties` 段）：

```text
+0x10 DWORD UniqueID          <- Save 字段 1
+0x14 AbstractFlags
+0x18 DWORD unknown_18
+0x1C LONG  RefCount
+0x20 bool  Dirty             <- Save 字段 2
+0x21 BYTE  padding_21[3]
```

⇒ **`+0x10` = `UniqueID`，`+0x20` = `Dirty`，两者被序列化；其余五个不序列化。**
这与"`RefCount` 是运行时态、`AbstractFlags` 可重建"一致。

`0x4A1CA0` 的归一化（`cmp bl,dl; setne bl; mov [eax+ecx+8],bl`）
说明写入时把任意非零值折叠成 1 —— **`Dirty` 的语义是 bool，不是 count**。

---

## 4. 存疑项（不强行定名）

| 槽 | 现象 | 为什么不给定名 |
|---:|---|---|
| 15 | `xor eax,eax; ret` | `GetOwningHouseIndex` 通常以 −1 表示"无主人"，这里是 0。可能是 `return 0` 即合法的"第 0 阵营"，也可能我对应的 YRpp 行错位 |
| 14 | `or eax,-1; ret` | 标成 `CalculateChecksum` 是根据 YRpp 顺序推的，没有行为证据 |

**不作裁定**，保留为待核。这两条不影响 0–7 的结论（那 8 个槽有独立字节证据）。

### 4.1 槽 24 不是槽 —— 是 `INoticeSource` 子表的 COL 指针

`0x7E1F50 + 0x60 = 0x7E1FB0`，该 dword 的值是 `0x007FB160`。这不是代码地址，
而是一个 **CompleteObjectLocator**：

```text
COL @0x007FB160
  +0x00 signature       = 0
  +0x04 offset          = 0
  +0x08 cdOffset        = 0
  +0x0C pTypeDescriptor = 0x008177E8
  +0x10 pClassDescriptor= 0x007FB150

TypeDescriptor @0x008177E8
  +0x00 pVFTable = 0x007F9594
  +0x08 name     = ".?AVINoticeSource@@"
```

**这是 `INoticeSource` 接口子表的开头**：MSVC 在 vtable 起点之前放 `vtable[-1] = COL`。
`AbstractClass` 主表在 `0x007E1F50`，占 24 槽（`0x60` 字节）到 `0x7E1FB0` 结束；
下一个结构从 `0x7E1FB0` 开始，前 4 字节正是上面这个 COL 指针，
**函数槽从 `0x7E1FB4` 起**。

验证：`u32(0x7E1FB4) = 0x004C9150`（`xor eax,eax; ret`）—— 是代码。

### 4.1.1 可复跑的判据

`tools/dump_vtable_slots.py` 把这条做成机器判据：**槽值落在 `.rdata` ⇒ 是 COL 指针**。
它对两个类都给出正确终止：

```text
AbstractClass [24] 0x007FB160 COLPTR  COL -> .?AVINoticeSource@@
TEventClass   [24] 0x0080C638 COLPTR  COL -> .?AVTextButtonClass@@
```

两个类都是 24 个函数槽 + 1 个 COL。

**注意段边界**：`.rdata` 是 `0x7E1000..0x811074`（rva `0x3E1000` + vsize `0x30074`），
**COL 在 `.rdata`，但它指向的 TypeDescriptor 在 `.data`（`0x812000..0xB79BE4`）**。
查名字时两段都要接受，否则 `describe_col` 只会输出 `?`。
这是本线第一版工具的实际错误（用 `0x812000` 当 `.rdata` 上界），已修。

### 4.1.2 `TEventClass` 的 COL 为何指向 `TextButtonClass`

`TEventClass` 主表之后紧跟的是**无关的** `TextButtonClass` 表 —— 说明
`.rdata` 里 vtable 的排布**不保证按继承关系相邻**。
⇒ 不能用"下一个 COL 是哪个类"来推断当前类的接口列表。
`AbstractClass` 那条能对上 `INoticeSource` 是巧合（也可能是链接器按编译单元排的），
**不作为证据使用**。本条结论只依赖"`.rdata` 值 ⇒ 非函数"这一点。

⇒ **不要用"槽数是 24 还是 25"来判断布局**。`mangled names` 里的 `INoticeSource`
子表紧贴主表尾部，按槽号扫过去会把它当第 25 个虚函数。
判据：**槽值若落在 `.rdata`（`0x7E1000..0x812000`），它不是函数**，
而是一个 COL 指针，表示"这里换了一张表"。

这条也解释了为什么 `classes_meta.json` 里 `AbstractClass` 记 24 槽
（RTTI 只数到主表末尾），而朴素按指针扫描会数出 25 个。

---

## 5. 核验状态

| 结论 | 通道 | 状态 |
|:---|:---|:---|
| 槽 0–7 = COM 8 槽，顺序与 YRpp 一致 | 字节 + 社区源 | ✅ 双通道 |
| **槽 4 = `IsDirty`（返回 `!Dirty`）** | 字节 6 条全函数 | 单通道字节（强） |
| 槽 5 = `Load`、槽 6 = COM `Save`、槽 13 = 基类序列化块 | 字节（三族调用链） | 单通道字节 |
| 槽 8 = 标量删除析构 | 字节（`ret 4` + 返回 this） | 单通道字节 |
| `+0x10` = `UniqueID`、`+0x20` = `Dirty`（bool） | 字节 + YRpp 属性表 | ✅ 双通道 |
| 槽 11/12 = `WhatAmI`/`Size` | 见 `kb/20_vtable_contract.md`（69 类 + 三方一致） | ✅ 已核验 |
| 槽 4 在全引擎 77 个类上同址 | `slot[4]` 直方图 | 单通道字节（旁证：基类几乎无人覆写） |
