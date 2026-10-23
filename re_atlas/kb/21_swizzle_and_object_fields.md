# R2-1 续：`TEventClass` 接口字段与 `SwizzleManagerClass`（撤回"字段注册表"） [实证]

更新：2026-10-21（RE-ATLAS R-012）

本篇**撤回** `kb/11_class_layouts.md` §2.1 的一条结论，并把 L-6 / L-14 / L-16 三项结清或推进。

---

## 0. 必须先看的撤回

### 撤回 4：`0xB0C110` 不是"字段注册表根"，是 `SwizzleManagerClass::Instance`

前轮据"`lea [obj+off]` + `push 0xB0C110` + `call 0x6CF240`"这一模式在 `.text` 出现 489 次，
判它为"引擎级字段注册表的根，各处构造函数把字段地址交给统一 helper 完成元数据登记"。
**这个解读是错的。**

证据链（三源一致）：

1. **静态初始化器** `0x006CF0C8` 直接往 `0xB0C110` 写虚表指针：
   ```text
   0x006CF0C8  C7 05 10 C1 B0 00 08 41 7F 00   mov dword ptr [0xB0C110], 0x7F4108
   ```
   一个"注册表根"不会自身带 vtable；带 vtable 说明它**是一个对象**。
2. **虚表 `0x7F4108` 经 RTTI 反查 = `SwizzleManagerClass`**
   （基类 `SwizzleManagerClass, ISwizzle, IUnknown`，10 槽）。
3. **`0x6CF240` 就是该虚表的槽 4**：
   ```text
   0x007F4108 slot[0]=0x006CF430  slot[4]=0x006CF240  slot[6]=0x006CF2C0
   ```
4. **社区源独立佐证**：`YRpp/SwizzleManagerClass.h:26`
   `static constexpr reference<SwizzleManagerClass, 0xB0C110u> const Instance{};`

⇒ 489 处调用是"把某个指针字段登记到 swizzle 管理器，供存档时做指针重定位"。

### 0.0b 489 处的精确拆分

| 分类 | 处数 | 说明 |
|:---|---:|:---|
| 紧接 `call 0x6CF240`（槽 4 `Here_I_Am`） | 473 | 主体 |
| 紧接 `call 0x6CF2C0`（槽 6） | 5 | 三参数版本 |
| 紧接 `call 0x6CF230` | 4 | 槽 3 `Reset` 的封装（`mov ecx,[esp+4]; call 0x6CF350`） |
| 紧接 `call 0x6CF430`（槽 0 `QueryInterface`） | 1 | |
| `push` 与 `call` 之间有 1–2 条**无关指令**插队 | 2 | `0x0055AB16`（`mov [esi+0x14],ebx` 插队）、`0x0070BF74`（`mov [esi+0x514],ebx` 插队），**最终都到达 `0x6CF240`** |
| **字面量出现在指令立即数内部（假命中）** | **4** | `0x006CF0CA` / `0x006CF0F2` / `0x006CF0F8`（都在静态初始化器自身编码里）、`0x00465208`（`push` 后转去算 `[eax+eax*2]` 的索引，不是 swizzle 调用） |

⇒ **真调用 485 处，假命中 4 处**。
"用 `push <literal>` 判 swizzle 调用"这条判据要允许 1–2 条插队指令，
并要排除静态初始化器自身那三个站点。

### 0.1 `0x6CF240` 的真实语义（槽 4）

```text
0x006CF240  push ebx / push edi
0x006CF242  mov edi, [esp+0x10]        ; arg2 = void** ppField
0x006CF246  test edi, edi
0x006CF248  jne  0x6CF254
0x006CF24A  pop edi
0x006CF24B  mov  eax, 0x80004003       ; E_POINTER
0x006CF250  pop  ebx
0x006CF251  ret  8
0x006CF254  mov  ebx, [edi]            ; value = *ppField
0x006CF256  test ebx, ebx
0x006CF258  jne  0x006CF261
0x006CF25A  pop edi
0x006CF25B  xor  eax, eax              ; value == 0  ⇒ 直接返回 S_OK，不登记
0x006CF25D  pop  ebx
0x006CF25E  ret  8
0x006CF261  mov  eax, [esp+0xc]        ; arg1 = this (SwizzleManagerClass*)
...
0x006CF285  mov  edx, [esi]            ; 向量 vtable
0x006CF289  push 0
0x006CF28B  push eax
0x006CF28C  mov  ecx, esi
0x006CF28E  call [edx+8]               ; 向量扩容
0x006CF295  mov  eax, [esi+0x10]       ; Count
0x006CF298  mov  edx, [esi+4]          ; Items
0x006CF29B  lea  ecx, [eax+1]
0x006CF29E  mov  [esi+0x10], ecx       ; ++Count
0x006CF2A1  mov  [edx+eax*8], ebx      ; Items[n].unknown_0 = value
0x006CF2A4  mov  [edx+eax*8+4], edi    ; Items[n].pAnything = ppField
0x006CF2A8  mov  dword ptr [edi], 0     ; ★ 把原字段清零
0x006CF2AE  pop esi / pop edi
0x006CF2B0  xor  eax, eax              ; S_OK
0x006CF2B2  pop  ebx
0x006CF2B3  ret  8
```

**关键语义**：登记后**原字段被置 0**。对照 YRpp 的
`SwizzlePointerClass { DWORD unknown_0; void* pAnything; }`（8 字节），
数组元素正好是 `{原始指针值, 字段地址}`。

⇒ 编译期含义：一个字段被 `Here_I_Am` 过之后，直接读它拿到的是 **0**；
真实值要去 swizzle 表查。**这是补丁必须知道的行为**，前轮的"注册表"解读会让人以为
字段仍然有效。

### 0.2 `0x6CF2C0`（槽 6）的语义

```text
0x006CF2CA  mov ecx, [eax+0x2c]   ; eax = 传入对象
0x006CF2CD  lea esi, [eax+0x1c]   ; ★ 第二个向量在 +0x1C
0x006CF2D5  mov eax, [esi+8]      ; 容量
0x006CF2D8  cmp ecx, eax
0x006CF2DA  jl  0x6CF2FE          ; 未满 ⇒ 直接追加
...
0x006CF2FE  mov eax, [esi+0x10]   ; Count
0x006CF301  mov edx, [esi+4]      ; Items
0x006CF30A  mov [edx+eax*8], ebx
0x006CF30D  mov [edx+eax*8+4], edi
0x006CF316  ret 0xc               ; 3 参数
```

与 `YRpp/SwizzleManagerClass.h:62-63` 的两个成员
`DynamicVectorClass<SwizzlePointerClass> Swizzles_Old / Swizzles_New;` 吻合：
`+0x04` 与 `+0x1C` 各 0x18 字节（`VectorClass` 0x10 + `Count` + `CapInc`），
实例尺寸 0x34 = 52；`SwizzleManagerClass` 不在 69 类 ID 表内（它不是 `AbstractClass` 派生，无 `WhatAmI`）。

---

## 1. L-6 结清：`TEventClass` 的三个接口字段

前轮记"`+0x30` 与 `+0x54` 两个接口对象"。**实际是三个**，且 `Save` 序列化 4 项
（前轮记 3 项，漏了 `+0x28`）。

### 1.1 构造函数（虚表槽 5 = `0x0071F8C0`）

```text
0x0071F8CB  call 0x410380                  ; AbstractClass::Load 或初始化
0x0071F8E4  mov [esi+0x00], 0x7F5578       ; 主 vptr
0x0071F8EA  mov [esi+0x04], 0x7F555C       ; IPersistStream
0x0071F8F1  mov [esi+0x08], 0x7F5554       ; IRTTITypeInfo
0x0071F8F8  mov [esi+0x0C], 0x7F554C       ; INoticeSink/INoticeSource
0x0071F8FF  lea edx, [esi+0x28]            ; ★ 字段 1
0x0071F902  push edx
0x0071F903  push 0xB0C110                  ; SwizzleManager::Instance
0x0071F908  call 0x6CF240                  ; Here_I_Am(&flag)
0x0071F90D  lea eax, [esi+0x30]            ; ★ 字段 2
0x0071F910  push eax
0x0071F911  push 0xB0C110
0x0071F916  call 0x6CF240
0x0071F91B  add esi, 0x54                  ; ★ 字段 3
0x0071F91E  push esi
0x0071F91F  push 0xB0C110
0x0071F924  call 0x6CF240
```

**三个字段**：`+0x28`、`+0x30`、`+0x54`。全部登记进 swizzle 管理器，
即全部是**会被指针重定位的指针字段**。

### 1.2 `Save`（虚表槽 13 = `0x0071F820`）序列化 4 项

```text
0x0071F820  push esi / push edi
0x0071F822  mov edi, [esp+0xc]             ; 流对象
0x0071F826  mov esi, ecx                   ; this
0x0071F828  push edi
0x0071F829  call 0x410410                  ; AbstractClass::Save  ← 先基类
0x0071F82E  mov eax, [esi+0x28]            ; ★ 项 1
0x0071F831  test eax, eax
0x0071F833  je   0x71F847
0x0071F835  mov ecx, [eax+4]               ; 接口 vtable
0x0071F838  add eax, 4                     ; 接口子对象 this
0x0071F83B  push eax
0x0071F83C  call [ecx+0x10]                ; 接口槽 4 → 取值
0x0071F83F  push eax
0x0071F840  mov ecx, edi
0x0071F842  call 0x4A1D50                  ; 写 dword
0x0071F847  mov edx, [esi+0x2C]            ; ★ 项 2（事件 Kind）
0x0071F84C  push edx
0x0071F84D  call 0x4A1D50
0x0071F852  mov eax, [esi+0x30]            ; ★ 项 3
0x0071F859  mov ecx, [eax+4]
0x0071F85C  add eax, 4
0x0071F860  call [ecx+0x10]
0x0071F866  call 0x4A1D50
0x0071F86B  mov edx, [esi+0x34]            ; ★ 项 4
0x0071F871  call 0x4A1D50
0x0071F878  ret 4
```

**存档顺序（`TEventClass`）**：
`AbstractClass 基类 → +0x28 接口 → +0x2C Kind → +0x30 接口 → +0x34 dword`

> `+0x54` 虽然也被 swizzle 登记，但**不在 `Save` 里**。
> ⇒ 它是纯运行时字段，或由别处（如 `TriggerClass` 的存档）负责。
> 这是本轮**没解完**的一点，记 L-20。

### 1.3 `+0x28` / `+0x30` 的结构（同构）

两者在 `Save` 里走**完全相同的三步**：

```text
p = *(obj + off)
if p:
    vt = *(p + 4)        ; 接口子对象在 +4
    call [vt + 0x10](p + 4)
```

`+4` 取 vtable、`+0x10` 是槽 4 —— 与 `AbstractClass` 的 `IPersistStream` 子对象
（`+0x04` 挂 `0x7F555C`）**同一形态**。⇒ `+0x28` / `+0x30` 指向**外部接口对象**，
不是普通子结构。

**真实类名仍未定**（L-6 部分闭合）：两个字段被 swizzle 登记说明是引擎对象指针，
但本轮没有抓到给它们赋值的站点。记 **L-21**。

> ### ★ L-21 定谳（R-041，2026-10-24）
> **`+0x28` = 前一个 `TEventClass`**（事件列表回链：loader @`0x7274FD` `call 0x71F4E0`
> 紧接 `mov [esi+0x28],[ebp+0xAC]`；链摘除槽10 @`0x71F800` 按同类同偏移再读——
> 「外部接口对象」的旧措辞就此修正：字段持的是**同类引擎对象**，Save 的三步走的是
> 对象自带的 IPersistStream facet）。
> **`+0x30` = `TeamTypeClass*`**（parse fn @`0x71F4E0` 内唯一取值写入 `call 0x6F0FC0;
> mov [esi+0x30],eax`；解析器按名扫全局注册表向量 `[0xA8ECA4]/[0xA8ECB0]` 比对
> `[item+0x24]` Name 槽与 `[item+0x64]`；注册表持有物经 facet 间距（主表
> `0x7F47D0`−0x24/−0x2C → `0x7F47AC/0x7F47A4`）与 `TeamTypeClass.vfuncs ∋ 0x6F1030`
> 双证；`"TeamTypes"` 节未命中即 `new 0xF8`（=248，G-1 双证尺寸）；转储 @`0x71F3FE`
> push `[对象+0x24]` 名字缓冲独立指向类型类）。
> 全簇存储站点 census 收口 = 门禁 X10；`evidence/r041_l21_eventteam.md`
> （门禁 10/10、变异 10/10）。**L-21 关闭；同函数 `0x72759D` 已归属排除
> （`[edi+0x28]` 属 TActionClass 兄弟链：new 0x94/ctor `0x6DD000`/主 vtable `0x7F443C`）。**

---

## 2. L-16 结清：`push 0x31` = `Name` 字段大小 49

前轮追到 `push 0x31`（=49）但两种解释（"49 项上限"/"缓冲区长度"）都不成立，
如实挂起。**本轮解出：它是传缓冲区容量，而目标是 `AbstractTypeClass::Name[0x31]`。**

### 2.1 调用现场（`0x00410A60`，`AbstractTypeClass::LoadFromINI`）

```text
0x00410A79  lea ebp, [ebx+0x24]        ; 节名 = UINameLabel
0x00410A7F  call 0x526810              ; INI: 该节是否存在
0x00410A86  je   0x410B7D              ; 不存在 ⇒ 走另一分支
0x00410A91  lea edi, [ebx+0x64]        ; ★ 目标缓冲区 = Name
0x00410A94  push 0x31                  ; ★ 容量 49
0x00410A96  push eax                   ; 默认值缓冲（esp+0x44）
0x00410A97  push edi                   ; 目标缓冲
0x00410A98  push 0x817854              ; "Name"    ← .rdata 字符串
0x00410A9D  push ebp                   ; 节名
0x00410A9E  mov ecx, esi               ; INI 对象
0x00410AA0  call 0x528A10              ; ReadString
```

### 2.2 独立佐证：YRpp 的字段声明

`YRpp/AbstractTypeClass.h:76`：

```c
class NOVTABLE AbstractTypeClass : public AbstractClass
{
public:
	char ID [0x18];
	PROTECTED_PROPERTY(BYTE, zero_3C);
	char UINameLabel [0x20];
	const wchar_t* UIName;
	char Name [0x31];     // ★ 49 字节，与 push 0x31 精确相等
};
```

**字节与社区源完全吻合**：`+0x64` 是 `Name`，容量 `0x31`。

### 2.3 同一函数的第二处：`+0x3D` 是另一个 32 字节缓冲区

```text
0x00410AEB  lea ebp, [ebx+0x3d]        ; ★ 目标 = +0x3D
0x00410AEE  push 0x20                  ; ★ 容量 32
0x00410AF0  push edx                   ; 默认值（esp+0x44）
0x00410AF1  push ebp                   ; 目标缓冲
0x00410AF2  lea eax, [ebx+0x24]        ; 节名仍是 +0x24
0x00410AF5  push 0x81784C              ; "UIName"   ← .rdata
0x00410AFA  push eax
0x00410AFB  call 0x528A10              ; ReadString
0x00410B12  push 0x1f                  ; 容量 31
0x00410B1A  call 0x7C91D0              ; 宽字符拷贝（31 wchar = 62 B）
0x00410B2F  mov ecx, 8
0x00410B3A  rep movsd                  ; 拷 8 dword = 32 B 到 [ebp]=+0x3D
```

**实测的三个缓冲区**：

| 偏移 | 容量 | 来源 | 回拷宽度 |
|---:|:---|:---|:---|
| `+0x24` | — | 作为**节名**传给 `0x528A10` / `0x526810`；也是**类型 ID** 串（见 §4.5.3） | — |
| `+0x3D` | `0x20` = 32 | 键 `"UIName"` | `rep movsd` ecx=8 ⇒ 32 B |
| `+0x60` | 4 | **指针**，赋 `0x887734`（默认串）或解析结果 | `mov dword [ebx+0x60], eax` |
| `+0x64` | `0x31` = 49 | 键 `"Name"` | `rep movsd` ecx=0xC + `movsb` ⇒ 49 B |

### 2.3.1 与 YRpp 完全吻合（L-22 结清，**并撤回本线此前的怀疑**）

把 YRpp `AbstractTypeClass` 的字段按"`ID` 起于 `+0x24`"展开：

```text
ID[0x18]            +0x24 .. +0x3B
zero_3C             +0x3C
UINameLabel[0x20]   +0x3D .. +0x5C
pad                 +0x5D .. +0x5F
UIName (wchar_t*)   +0x60 .. +0x63
Name[0x31]          +0x64 .. +0x94
```

**三个实测偏移全部精确命中**：`+0x24`（ID/节名）、`+0x3D`（UIName 标签）、
`+0x64`（Name）、`+0x60`（UIName 指针，`0x410B58`/`0x410B69` 直接写）。
⇒ **YRpp 是对的**。

**前轮记录为 L-22 的"YRpp `UINameLabel` 尺寸注释与实测不符"是我自己的误读**：
我按"`ID` 从 `+0x00` 起"去套 `AbstractTypeClass` 自己的字段表，
忘了那 0x24 字节前缀属于基类 `AbstractClass`。
`AbstractClass` 的属性表（`YRpp/AbstractClass.h`）是
`UniqueID(+0x10) / AbstractFlags(+0x14) / unknown_18(+0x18) / RefCount(+0x1C) /
Dirty(+0x20) / padding_21[3](+0x21..+0x23)`
⇒ 正好 0x24 字节，与 INI 里 `AbstractClass::Save` 只写 `+0x10`（`UniqueID`）与
`+0x20`（`Dirty`，bool）**完全对上**。

**⇒ 撤回 6（本线 R-012）**：L-22 不成立，YRpp 无误。
纪律 #7（新增）：**用一个派生类的字段表去核对基类字段之前，先算清基类占了多少字节。**

### 2.4 结论

`push 0x31` 的语义 = **"读 INI 时 `Name` 字段的缓冲区容量"**，`0x31`=49 即
`char Name[0x31]`。前轮两种猜测都错，正确解释是第三种：**它既不是条目上限，
也不是通用缓冲长度，而是某一个具名字段自己的声明尺寸**。

---

## 3. L-14 推进：`0x528A10` 的实参顺序

前轮只确认"5 参数 + `ret 0x14`"。本轮从两处调用现场定序：

```text
0x528A10(sub_ecx=INI对象, arg1=节名, arg2=键名, arg3=目标缓冲, arg4=默认值, arg5=容量)
          ^ ecx(this)     [+0x04]    [+0x08]    [+0x0C]      [+0x10]     [+0x14]
```

推导入参偏移的依据：

```text
0x00528A10  sub esp, 0xc / push ebx / push ebp / push edi   ; 压 3 寄存器 + 0xc
0x00528A18  mov edi, [esp+0x28]      ; 第 1 个栈参 → 0x28 = 0x0C + 3*4 + 4*4 = ...
0x00528A1C  cmp edi, eax             ; eax=0 ⇒ 空指针检查 → E_POINTER
0x00528A26  cmp [esp+0x2c], 2        ; 第 2 个栈参 与 2 比较 → "至少 2"
0x00528A31  mov ebx, [esp+0x1c]      ; 第 5 个栈参 → 与 [+4] 比较
0x00528A3D  mov edx, [esp+0x20]      ; 第 4 个栈参
```

配合 `0x00410AA0` 的 push 顺序（逆序入栈）：
`push 节名; push "Name"; push 目标; push 默认值; push 0x31` ⇒
参数从右到左依次是 容量、默认值、目标、键名、节名。

⇒ **`arg5` = 容量**，且 `cmp arg2, 2` 是"键名长度至少 2"的下限检查
（不是前轮猜的"条目数上限"）。

**剩余不确定**：`[esp+0x1c]` 与 `[ebp+4]` 比较的那处（`0x528A31/0x528A4D`）
是"节名与缓存节名相同则跳过重解析"的快速路径，本轮未展开。记 **L-23**。

---

## 4. 本轮新增悬项

| # | 悬项 |
|:--|:---|
| L-20 | `TEventClass+0x54` 被 swizzle 登记但不在 `Save` 里，由谁存档 |
| L-23 | `0x528A10` 的节名缓存快速路径（`[esp+0x1c]` vs `[ebp+4]`） |
| L-29 | `+0x54` 的取值写入点归属（R-041 census 实测 2 处：`0x71F209`/`0x71FA44`；清零站点 ctor `0x71E6BE`） |

**关闭**：L-15（§4.5 全解）、L-16（§2 全解）、L-22（§2.3.1 结清 —— 是**本线误读**，YRpp 无误）、
**L-21（R-041 §1.3 定谳横幅：`+0x28`=前一个 `TEventClass`、`+0x30`=`TeamTypeClass*`）**。

---

## 4.5 L-15 结清：`0x004C4EF0` = 按 `"<type>,<id>"` 查类型对象并填四字对

前轮只得知"清零 `[esi]`/`[esi+4]`，按 `.data` 模板 `0x82085C` 分派"。本轮全解：

```text
0x004C4EF0  sub esp, 0x40
0x004C4EF3  mov edx, [esp+0x44]        ; arg = 源字符串
0x004C4EF7  lea eax, [esp]             ; 本地缓冲
0x004C4EFA  mov esi, ecx               ; this = 输出结构（至少 8 字节）
0x004C4EFE  lea ecx, [esp+0x48]        ; arg 的地址
0x004C4F04  push 0x82085C              ; ★ 格式串 "%d,%s"
0x004C4F0A  mov dword ptr [esi],   0   ; ★ 先清零
0x004C4F10  mov dword ptr [esi+4], 0   ; ★ 再清零
0x004C4F17  call 0x7CA530              ; sscanf 风格：从 arg 按 "%d,%s" 解出
0x004C4F1C  mov eax, [esp+0x58]        ; 解出的整数 d
0x004C4F27  mov [esi], eax             ; ★ 字段 A = 整数
0x004C4F29  call 0x523C90              ; 用解出的字符串查类型表
0x004C4F2E  cmp eax, -1
0x004C4F31  je  0x4C4F48               ; 未找到 ⇒ 只剩 [esi]，[esi+4] 仍为 0
0x004C4F33  mov ecx, [0xA8E34C]        ; 类型表 Items
0x004C4F39  mov edx, [ecx+eax*4]       ; Items[idx]
0x004C4F3E  mov [esi+4], edx           ; ★ 字段 B = 类型对象指针
```

⇒ **参数只有一个（`ret 4`）**，是形如 `"12,GAOREP"` 的标识串；
输出是**两个 dword**：`{ 整数, 类型对象指针 }`。

### 4.5.1 模板 `0x82085C` 是 `.data` 里的 `"%d,%s"`

```
0x0082085C  "%d,%s\0"
```
**注意段属性**：`0x82085C` 在 **`.data`（可写）**，不在 `.rdata`。
这与本线 R-006 的撤回是同一条纪律：**引用字符串常量前先验段属性**。
它仍然可用（加载时已初始化），只是"只读常量"的说法不成立。

### 4.5.2 类型表 = `0xA8E34C`（Items）/ `0xA8E358`（Count）

```text
0x004C4F33  mov ecx, [0xA8E34C]   ; Items 指针
0x004C4F39  mov edx, [ecx+eax*4]  ; 元素是指针
```
两者在 `.text` 里分别有 **39 / 41** 处引用，是全局类型数组。

### 4.5.3 `0x523C90` = 按名字查类型表（带两个特殊名短路）

```text
0x00523C94  push 0x817474            ; "<none>"
0x00523C9A  call 0x7C8D20            ; strcmpi
0x00523CA6  push 0x817694            ; "none"
0x00523CAC  call 0x7C8D20
0x00523CB8  mov eax, [0xA8E358]      ; Count
0x00523CC3  mov ecx, [eax+esi*4]     ; Items[i]
0x00523CCC  add ecx, 0x24            ; ★ 比的是每个类型对象的 +0x24
0x00523CD0  call 0x7C8D20            ; strcmpi(Items[i]+0x24, name)
0x00523CE7  or eax, -1               ; 未找到返回 -1
```

**这里 `+0x24` 与 `kb/21` §2.3 的"节名缓冲"是同一字段**：
`AbstractTypeClass+0x24` 就是类型名（与 INI 节名同址）。
⇒ 交叉印证：`0x410A79` 的 `lea ebp,[ebx+0x24]` 拿的**既是节名也是类型名**，
两者是同一个字符串。这条把 L-22 里"`+0x24` 是什么"从猜测变成实证。

### 4.5.4 对 `TaskForceClass` 成员容器的意义

`0x4C4EF0` 的输出是 `{int, void*}` 两个 dword —— 与
`kb/11_class_layouts.md` §10 的 `TaskForceClass` 成员元素 `{id, value}` **同构**，
且同样 8 字节。**但本轮没有证据表明二者是同一个类型**（L-9 已解为
`{dword, dword}`，这里是 `{int, 类型对象指针}`）。
按 R-007 的纪律（同偏移/同尺寸 ≠ 同字段），**不做合并**。

---

## 5. 核验状态

| 结论 | 通道 | 状态 |
|:---|:---|:---|
| `0xB0C110` = `SwizzleManagerClass::Instance` | 字节（静态初始化器 + 虚表 + RTTI）| 单通道字节 |
| 同上 | 社区源 `YRpp/SwizzleManagerClass.h:26` | ✅ 独立佐证 |
| `0x6CF240` 登记后清零原字段 | 字节 `0x006CF2A8` | 单通道字节 |
| 489 处引用 = 485 真调用 + 4 假命中 | 字节逐站核对 | 单通道字节 |
| `TEventClass` 三接口字段 / `Save` 四项 | 字节（ctor + Save 全函数）| 单通道字节 |
| `push 0x31` = `Name[0x31]` | 字节（`0x410A94` + 字段偏移）| 单通道字节 |
| 同上 | 社区源 `YRpp/AbstractTypeClass.h` | ✅ 独立佐证 |
| `0x528A10` 参数顺序 | 字节（两处调用现场 + 栈帧）| 单通道字节，L-23 未闭 |
| `0x4C4EF0` = 解析 `"%d,%s"` 并查类型表填 `{int, ptr}` | 字节（全函数 + 两个 helper）| 单通道字节 |
| `AbstractTypeClass` 字段边界与 YRpp 完全吻合 | 字节（四个偏移全命中）+ 社区源 | ✅ **双通道一致** |
| `AbstractClass::Save` 写 `+0x10`/`+0x20` = `UniqueID`/`Dirty` | 字节 + 社区源 `YRpp/AbstractClass.h` | ✅ **双通道一致** |
