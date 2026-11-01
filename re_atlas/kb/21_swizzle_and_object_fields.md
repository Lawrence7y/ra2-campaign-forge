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
>
> **R-047 检验（2026-10-24）：上面「或由 TriggerClass 的存档负责」这一候选被证伪。**
> `TriggerClass::Save`（主表 `0x7F5858` slot13 @`0x726790`）整窗 0x86 字节逐字节钉死：
> 窗内 disp 普查 **+0x54 = 0 处**（阳性对照=同解析器看得见 +0x24/28/30/34/3c/40/44 七字段），
> 直接 call 集恰={基类 Save, 两族字段 writer}（T4），无任何被调方可序列化事件 +0x54；
> handler `0x71E940`（+0x54 唯一存活写入者）的全镜像 E8 入口 `{0x726540}` 不在 Save 路径（T5）。
> ⇒ 「+0x54 由 TriggerClass 存档」**不成立**；R-042 的**运行时缓存假说**又多一条负证据。
> **但 L-20 不关闭**：证伪一条点名候选 ≠ 定谳「谁存档」——完整答案要裁决读侧容器宿主类
> （L-30 域），静态到此为止。门禁 5/5、变异 12/12，`evidence/r047_l20_triggersave.md`。
>
> **R-048（2026-10-24）：读侧宿主定谳 = TriggerClass，「容器」证伪为标量字段，机制升级为
> 正面假说（仍未闭）**。收割函数 `0x7264C0` 的 this 字段集与 TriggerClass ctor `0x725FA0`
> 初始化集双向吻合（恰 {+0x24,+0x2C,+0x30,+0x34,+0x40,+0x44} ⊆ ctor 集，含 vptr
> `0x7F5858` 与 detach/Save 虚法同域双证，门禁 10/10+变异 13/13，
> `evidence/r048_triggerclass_host.md`）；`+0x2C` 有 setter/getter/detach 三件套（标量），
> 整条「写 +0x54 → 读 +0x54 → 存 this+0x2C」链都在这一个 TriggerClass 成员函数内 ⇒
> **运行时缓存假说获得正面机制**：载入后重算使能趟（非「谁存档」而是「无需存档、可重算」）。
> L-20 仍开放：「载入后必跑该趟」需动态序证据（调用方 `0x6E53A0` 有 72 个 E8 入口，
> 静态无法定序）。

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

### 1.4 ★ L-29 定谳（R-042，2026-10-24）：`+0x54` = 事件挂接对端对象的运行时缓存

`evidence/r042_l29_field54.md`（门禁 9/9、变异 10/10）。字节事实四条：

1. **成员字段**：ctor `0x71E6BE` 在装 vptr 前清零 `[esi+0x54]`（G1）；
   `0x71F91B` `add esi,0x54` 把地址交 swizzle（G2）——与 +0x28/+0x30 并列第三接口字段。
2. **不进 Save**：`0x71F820..0x71F87A` 整窗 0x5B 字节逐字节钉死，四项
   `+0x28/+0x2C/+0x30/+0x34` 之外无任何 `[reg+0x54]`（G3）。L-20 的「由谁存档」
   就此给出现象解释（运行时缓存 ⇒ 无需存档），**但非证明**，L-20 保持开放。
3. **写入点**：存活写入 = handler `0x71E940` 内 `0x71F209`
   （`mov [ebp+0x54],eax`，ebp=this；值来自传入对象 vtable slot15(+0x3c) 的返回值；
   门：`[this+0x34]==-1` 跳过，否则 slot14(+0x38) 结果参与比对）。
   **setter `0x71FA44` 是死代码**：E8/E9/立即数三面普查全镜像零引用（G9）。
   主表 slot15=`0x4104A0`=`xor eax,eax; ret` ⇒ 对裸 TEvent 恒 NULL（引擎共享桩，72 表）。
4. **读侧**：getter `0x71FA30` 唯二调用者 `0x726551/0x72655c`（消费方 `0x7264C0`
   的事件循环内），非空即存入 `[esi+0x2C]`（G6/G7）。
   【勘误 R-048】原文此处称「收割进**容器** `[esi+0x2C]`」为措辞误导：V8 三件套
   （setter `0x726920`/getter `0x726910`/detach 等值摘除 `0x726690`）证其为
   **TriggerClass 标量对端字段**；R-043 证据件同词挂同一勘误指针（站点与值不变）。

普查新坑：`modrm rm==4` 是 SIB（`[esp+disp]`）不是 `[esi+disp]`——首轮把 0x44 当 esi
双向失真；capstone `op.size` 单位=字节（dword 判据 `==4` 非 `==32`，否则全镜像 0 命中，
G-60 假阴性第二次复发形态）。handler 参数对象类归属记 **L-30**。

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
| L-20 | `TEventClass+0x54` 被 swizzle 登记但不在 `Save` 里，由谁存档（**R-047：TriggerClass::Save 候选已证伪**，见 §1.2 横幅；**R-048：正面机制成立——`+0x54` 与 TriggerClass`+0x2C` 由同一使能收割趟（`0x7264C0`）重算，「无需存档、可重建」取代「谁存档」**；仍开放：「载入后必跑该趟」需动态序证据） |
| L-23 | `0x528A10` 的节名缓存快速路径（`[esp+0x1c]` vs `[ebp+4]`） |
| L-30 | `0x71E940` 参数对象（slot15 派发宿主）与容器 `[esi+0x2C]` 的类归属（R-042 遗留）。**R-043 进展**：门查询的注册表已定谳 = `DynamicVectorClass<HouseClass*>` @`0xA80228`（finder `0x502D30` 整函数钉死，RTTI TD 名双证）；且 **arg2 不是裸 HouseClass**（其 slot15 是 `xor eax,eax` 桩⇒若 arg2=House 则 +0x54 恒 NULL 自相矛盾，G-62 反证），arg2 具体类仍未定谳。**R-048 消费侧收口**：消费函数 `0x7264C0` 宿主 = TriggerClass（字段签名互校+虚法同域，10/10+13/13）；「容器」证伪为标量字段（三件套，V8）；arg2 = `[T+0x24](owner)+0xA4 → +0xB4` 运行期对端（R-043 Y5 链在册）。**R-050 实例容器定谳**：TriggerClass 对象的持有容器 = `DynamicVectorClass<AbstractClass*>` @`0xB0F670`（引擎级共享注册表；安装/降级双 pattern 全段唯一、RTTI 链解名 + House 阳性对照 + TriggerClass 名串反证对照，7/7+12/12，`evidence/r050_trigger_registry.md`）；入册值=ctor this（esi 保全普查唯一写点=头部）。**【R-051 推翻·部分】** 本条曾断言「**非** `<TriggerClass*>`、不存在专用 trigger 向量」——**不成立**：ctor 实际向**三**个容器注册（`0xB0F670`、`0xB0F708` 皆 AbstractClass*；**`0xA8EAE8` = `DynamicVector<TriggerClass*>` 专用表**，vptr `0x7E9BE4`），R-050 只看到一条腿就外推到总体（变种 F「样本当总体」复发）。**GOAL-3T 遍历全部 trigger 的静态入口 = 直接遍历 `0xA8EAE8`**（`[+4]`data/`[+0x10]`count/`[+8]`cap），**无需** WhatAmI 过滤（表名与元素类型自洽）；见 `evidence/r051_trigger_three_registries.md`（8/8+12/12）。**【R-052 定谳残余②】** 调用方
`0x6E53A0`（73 E8 入口）宿主类 = **TagClass 非虚成员**：体内 `[ebp+disp]` 集恰 `{24,28,2C,34,35}`、
+0x34/+0x35 字节重入旗标=Tag ctor `0x6E4DE0` 五字段签名；反证非 TriggerClass（其 +0x34 是 dword）；
链路=Tag ctor 造 TriggerClass（rel32=0x725FA0）头插 `[esi+0x28]` 链、`0x6E53A0` 逐成员调 `0x7264C0`；
this 来源=`DynamicVector<TagClass*>`（`[0x8B40CC]`，vptr `0x7EA5A4` 安装唯一站 `0x4E7FCD`）；
RTTI `.?AVTagClass@@`+WhatAmI 0x2C 双证（10/10+13/13，`evidence/r052_tagclass_host.md`）。
**副产物**：TagClass ctor 亦三注册腿（专用 `0xB0E720`=DynamicVector<TagClass*> + 共享
`0xB0F670`/`0xB0F708`，ctor 跨度尾存 `893481` 恰 3）；**第四共享 Abstract 表 `0xB0F698`**
（vptr 同 `0x7E91EC`；`0x6E53A0` 尾段自报入它，登记不定谳）。**残余①重述**：旧「attach 工厂
`0x6E4EC0..`」地址**落在 TagClass ctor 本体跨度内**（非独立工厂）；所谓「arg1 列表驱动构造」实为
Tag ctor 的 `[[arg1+0xA0]→+0xA8]` 节点链（0x6E4F19 起，Y5 在册）；新残量=Tag ctor arg1 类归属
（调用点 `0x6C20CE`/`0x6E52D6`/`0x6E8D90` 待追），且 Trigger+0x24 实存**链节点**而非 arg1 原值
（0x6E4F35 `push edi`）。**【R-053 定谳残余①·L-30 全闭】** TagClass ctor `0x6E4DE0` 的 arg1 =
**`TagTypeClass*` 或 NULL**：构造点精确集合恰 3（E9 尾跳 0）——`0x6C20CE`（`TClassFactory<TagClass>`
虚表 `0x7F3A80` slot3，arg1=`push 0` ⇒ **NULL** 无主 Tag）、`0x6E52D6`（find-or-create `0x6E52A0`
**按 `[tag+0x24]==arg1` 去重**；调用者经 `0x6E5E70` 取 `DynamicVector<TagTypeClass*>`
@`[0xB0E784]`（vptr `0x7F4558`，安装站 `0x6E5AFD`）的元素）、`0x6E8D90`（TeamClass ctor 三参，
arg1=`[[TeamClass+0x24]+0xD0]`；`TeamTypeClass+0xD0` 写入者精确集合恰 3、值来自 `0x6E6310` 的
`push 0xA4`（=TagTypeClass GetSize）+`call 0x6E5B60`（TagTypeClass ctor））。arg1 落 `Tag+0x24`，
沿 `[arg1+0xA0]→[+0xA8]` 逐节点 `push 0x48`+`call 0x725FA0` 派生 TriggerClass 头插 `Tag+0x28`；
`+0xA0` 链头归 TagTypeClass（其 ctor `0x6E5B73` 清零、dtor `0x6E5CA0` 沿链释放、`0x6E5E50` 按值摘链）；
`+0xA8`/`+0x9C` 为同簇链指针。六类 RTTI/WhatAmI/GetSize 同钉（Tag `2C/38`、TagType `2D/A4`、
Trigger `26/48`、TriggerType `27/B4`、Team `22/A0`、TeamType `23/F8`）。门禁 10/10 + 变异 16/16，
见 `evidence/r053_tag_arg1.md`。 |

**关闭**：L-15（§4.5 全解）、L-16（§2 全解）、L-22（§2.3.1 结清 —— 是**本线误读**，YRpp 无误）、
**L-21（R-041 §1.3 定谳横幅：`+0x28`=前一个 `TEventClass`、`+0x30`=`TeamTypeClass*`）**、
**L-29（R-042 §1.4 横幅：`+0x54` 归属——事件挂接对端对象的运行时缓存；写入点 `0x71E940`@`0x71F209`；setter `0x71FA44` 死代码；读侧 getter `0x71FA30` 唯二调用者 `0x726551/5c` 收割进 `[esi+0x2C]`——原文「容器」措辞已由 R-048 勘误为标量字段，见 §1.4 第 4 条勘误注）**。

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
