# KB · `11_class_layouts` — 触发器族类布局与 `AbstractClass` 多继承前缀

> R2-1 第二轮。目标：给战役编译器提供**可用的类尺寸与头部布局**，
> 让 `TagClass` / `TriggerClass` / `TEventClass` / `TActionClass` / `TeamClass` /
> `TaskForceClass` / `ScriptClass` 能按字节偏移读写。
> 置信度：**实证**（本线字节复算）/ 语料实证 / 推演。

---

## 0. 结论速览

### 0.1 实例尺寸（全部字节实证，`vtable[12]` 体首 `mov eax,imm32`）

| 类 | 虚表 VA | 槽数 | **实例尺寸** | 十六进制 | GetSize VA | 基类 |
|:---|:---|---:|---:|:---:|:---|:---|
| `ScriptClass` | `0x007F0F78` | 24 | **48** | `0x30` | `0x00691ED0` | `AbstractClass` |
| `TagClass` | `0x007F44E0` | 24 | **56** | `0x38` | `0x006E5890` | `AbstractClass` |
| `TriggerClass` | `0x007F5858` | 24 | **72** | `0x48` | `0x00726930` | `AbstractClass` |
| `TEventClass` | `0x007F5578` | 24 | **88** | `0x58` | `0x0071FA50` | `AbstractClass` |
| `TActionClass` | `0x007F443C` | 24 | **148** | `0x94` | `0x006E4630` | `AbstractClass` |
| `TeamClass` | `0x007F4730` | 24 | **160** | `0xA0` | `0x006F0430` | `AbstractClass` |
| `TaskForceClass` | `0x007F4680` | 27 | **212** | `0xD4` | `0x006E87E0` | `AbstractTypeClass` |
| `ScriptTypeClass` | `0x007F1008` | 27 | **564** | `0x234` | `0x00691F80` | `AbstractTypeClass` |
| `AbstractClass` | `0x007E1F50` | 24 | **0（桩）** | `0x0` | `0x004C9150` | 根 |
| `AbstractTypeClass` | `0x007E2000` | 27 | **0（桩）** | `0x0` | `0x004C9150` | `AbstractClass` |

**⚠ `AbstractClass::GetSize` 返回 0**：字节为 `33 C0 C3`（`xor eax,eax; ret`）。
这是**纯虚/抽象占位**，不是"尺寸为 0"。任何"用基类尺寸算派生类"的做法都会得到 0；
尺寸必须逐类取自己的 `vtable[12]`。`AbstractTypeClass` 同槽同址同体，也是桩。

### 0.2 ★ `AbstractClass` 头部是多继承：4 个 vtable 指针

这是本轮最重要的结构性发现，它决定了**所有派生类的头部布局**。

**证据**：`AbstractClass` 的标量删除析构函数 `0x004105A0` 完整反汇编：

```
0x004105A0  8A 44 24 04         mov  al, [esp+4]          ; 删除标志
0x004105A4  56                  push esi
0x004105A5  8B F1               mov  esi, ecx
0x004105A7  A8 01               test al, 1                ; bit0 = 是否释放内存
0x004105A9  C7 06 50 1F 7E 00   mov  [esi+0x00], 0x7E1F50 ; ★ vtable #0（主类）
0x004105AF  C7 46 04 34 1F 7E 00 mov [esi+0x04], 0x7E1F34 ; ★ vtable #1
0x004105B6  C7 46 08 2C 1F 7E 00 mov [esi+0x08], 0x7E1F2C ; ★ vtable #2
0x004105BD  C7 46 0C 24 1F 7E 00 mov [esi+0x0C], 0x7E1F24 ; ★ vtable #3
0x004105C4  74 09               je   0x4105CF
0x004105C6  56                  push esi
0x004105C7  E8 71 85 3B 00      call 0x7C8B3D            ; operator delete
0x004105CC  83 C4 04            add  esp, 4
0x004105CF  8B C6               mov  eax, esi
0x004105D1  5E                  pop  esi
0x004105D2  C2 04 00            ret  4
```

**四个 vtable 各自的 COL 与 this 调整量** [实证]（`vtable-4` 指向 CompleteObjectLocator）：

| 偏移 | vtable | COL | **COL.offset** | 对应接口 |
|---:|---|---:|---:|:---|
| `+0x00` | `0x007E1F50` | `0x007FB118` | **0** | 主类 `AbstractClass` |
| `+0x04` | `0x007E1F34` | `0x007FB008` | **4** | 接口 1 |
| `+0x08` | `0x007E1F2C` | `0x007FAFF0` | **8** | 接口 2 |
| `+0x0C` | `0x007E1F24` | `0x007FAFD8` | **12** | 接口 3 |

`COL.offset` 正是"从对象首地址到该子对象起点的字节距离"，且等于 vtable 指针自身的
偏移 —— 这是多继承布局的铁证（单继承时只有 offset=0 一项）。

**接口的 this 调整跳板** [实证]：

```
0x004105E0  83 6C 24 04 04      sub [esp+4], 4      ; 把 this 从子对象退回首地址
0x004105E5  E9 76 FC FF FF      jmp 0x00410260      ; 转发到主类实现 slot0
0x004105EA  CC CC CC            int3
0x004105F0  83 6C 24 04 04      sub [esp+4], 4
0x004105F5  E9 06 FD FF FF      jmp 0x00410300      ; slot1
```

⇒ 接口 vtable 的槽里放的是"减法跳板"，不是独立实现。

### 0.3 由此确定的 `AbstractClass` 前缀布局

| 偏移 | 大小 | 内容 | 证据 |
|:---|---:|:---|:---|
| `+0x00` | 4 | vptr #0（主类） | `0x4105A9` 字面写 |
| `+0x04` | 4 | vptr #1（接口 1） | `0x4105AF` |
| `+0x08` | 4 | vptr #2（接口 2） | `0x4105B6` |
| `+0x0C` | 4 | vptr #3（接口 3） | `0x4105BD` |
| `+0x10` | 4 | **指针**，被 `Save` 序列化 | `0x00410418: mov eax,[esi+0x10]` → `push` → `call 0x4A1D50` |
| `+0x14`…`+0x1C` | 12 | 未知（3 dword） | 待定 |
| `+0x20` | 1 | **bool**（写入时被归一化为 0/1） | `0x00410423: mov cl,[esi+0x20]` → `call 0x4A1CA0` |

**`Save` 方法本体** `0x00410410`（只读到两个字段，说明 `AbstractClass` 自身只序列化 2 项）：

```
0x00410410  56                  push esi
0x00410411  8B F1               mov  esi, ecx
0x00410413  57                  push edi
0x00410414  8B 7C 24 0C         mov  edi, [esp+0xC]      ; 流对象
0x00410418  8B 46 10            mov  eax, [esi+0x10]     ; ★ 字段 +0x10
0x0041041B  8B CF               mov  ecx, edi
0x0041041D  50                  push eax
0x0041041E  E8 2D 19 09 00      call 0x4A1D50            ; WriteDWord
0x00410423  8A 4E 20            mov  cl, [esi+0x20]      ; ★ 字段 +0x20
0x00410426  51                  push ecx
0x00410427  8B CF               mov  ecx, edi
0x00410429  E8 72 18 09 00      call 0x4A1CA0            ; WriteByte
```

**序列化助手识别** [实证]：

| VA | 语义 | 证据 |
|:---|:---|:---|
| `0x004A1D50` | 写 4 字节到流 | 包装 `push 4` → `call 0x4A1DE0`（流写入核心） |
| `0x004A1CA0` | **写 bool**（先归一化 `setne` 再写 1 字节） | `0x004A1CB1: cmp bl,dl` → `0x004A1CB4: setne bl` → `0x004A1CB7: mov [eax+ecx+8], bl` |

⇒ `AbstractClass::Save` 只序列化两项：`+0x10`（dword）与 `+0x20`（bool）。
`+0x14..+0x1C` 三个 dword **不在存档里**，说明它们是纯运行时态（缓存/临时指针）。

---

## 1. 派生类尺寸与基类的关系 [实证]

`AbstractClass` 前缀到 `+0x20` 至少 33 字节。派生类尺寸**远大于**此前缀：

| 类 | 总尺寸 | 减去前缀 0x21≈33 | 派生追加区 |
|:---|---:|---:|---:|
| `ScriptClass` | 48 | 15 | 极小，符合"脚本 = 指令数组"的轻量设计 |
| `TagClass` | 56 | 23 | 含名字指针/引用计数类字段 |
| `TriggerClass` | 72 | 39 | 含 Tag 指针 + Event/Action 链头 |
| `TEventClass` | 88 | 55 | 已知 `+0x2C` = 事件 Kind（见 `10_map_triggers.md` §3.1） |
| `TActionClass` | 148 | 115 | 已知 `+0x90` 有标志字节（见 §2） |
| `TeamClass` | 160 | 127 | 已知 `+0x3C` = 当前脚本状态（见 §2） |
| `TaskForceClass` | 212 | — | 29×7 或结构数组（待核） |

> 注："派生追加区"一列是**差值**，不是实测字段表；只用于验证"尺寸够装下已知字段"。

---

## 2. 已确证的派生字段

### 2.1 `TEventClass` — `Save` 完整解码 [实证]

`TEventClass` 尺寸 **88 (`0x58`)**，其 `Save`（slot 13 / 10 共用体 `0x0071F847` 起）只序列化三项：

```
0x0071F847  8B 56 2C            mov  edx, [esi+0x2C]      ; ★ 字段 A
0x0071F84A  8B CF               mov  ecx, edi             ; 流对象
0x0071F84C  52                  push edx
0x0071F84D  E8 FE 24 D8 FF      call 0x4A1D50             ; 写 dword
0x0071F852  8B 46 30            mov  eax, [esi+0x30]      ; ★ 字段 B = 对象指针
0x0071F855  85 C0               test eax, eax
0x0071F857  74 12               je   0x71F86B            ; 为空 ⇒ 跳过
0x0071F859  8B 48 04            mov  ecx, [eax+4]         ; 取该对象 +4 处的接口 vtable
0x0071F85C  83 C0 04            add  eax, 4               ; 调整为接口子对象 this
0x0071F85F  50                  push eax
0x0071F860  FF 51 10            call [ecx+0x10]           ; 调该接口的序列化槽
0x0071F863  50                  push eax
    ...
0x0071F86B  8B 56 34            mov  edx, [esi+0x34]      ; ★ 字段 C
0x0071F86E  8B CF               mov  ecx, edi
0x0071F870  52                  push edx
0x0071F871  E8 DA 24 D8 FF      call 0x4A1D50             ; 写 dword
0x0071F876  5F 5E               pop  edi; pop esi
0x0071F878  C2 04 00            ret  4
```

| 偏移 | 类型 | 语义 | 序列化 |
|:---|:---|:---|:---|
| `+0x2C` | `int32` | **事件 Kind**（合法域 `0x0D..0x3D`，见 `10_map_triggers.md` §3.1） | 作为 dword 直接写 |
| `+0x30` | **指针** | 指向一个**带接口的从属对象**；非空时按其 `+4` 接口 vtable 的第 4 槽（`[vt+0x10]`）序列化 | 条件写（空则跳过） |
| `+0x34` | `int32` | 第二个数值参数 | 作为 dword 写 |

⇒ **`+0x30` 不是普通字段**，而是"带独立 vtable 的子对象指针"。
这与 §0.2 的发现一致：`AbstractClass` 家族用 `+4/+8/+0xC` 挂接口，
而 `TEventClass` 又额外挂了一个**外部**接口对象。

**`0x0071F90D` 的第二处用法** 印证了同一解读：

```
0x0071F90D  8D 46 30            lea  eax, [esi+0x30]      ; 取字段 B 的地址（非值）
0x0071F910  50                  push eax
0x0071F911  68 10 C1 B0 00      push 0xB0C110             ; 全局字符串/键
0x0071F916  E8 25 F9 FA FF      call 0x6CF240
0x0071F91B  83 C6 54            add  esi, 0x54            ; ★ 下一个字段在 +0x54
0x0071F91E  56                  push esi
0x0071F91F  68 10 C1 B0 00      push 0xB0C110
0x0071F924  E8 17 F9 FA FF      call 0x6CF240
```

`0x006CF240` 是**取接口指针的辅助函数**：参数为空时返回 `0x80004003`（`E_POINTER`），
否则读 `[edi]` 拿 vtable。⇒ 这两次调用是"按全局键 `0xB0C110` 查两个接口"。
且 `add esi,0x54` 说明 **`+0x54` 还有第二个接口字段**（`0x54..0x58` 正好 4 字节，到尺寸边界）。

**`0xB0C110` 是什么** [实证]：它落在 `.data` 的 **BSS 尾部**
（`.data` raw 只到 `0x47E000`，而该地址 RVA = `0x70C110`），
即**文件里没有字节、加载时零初始化**的全局。

**更重要的发现**：字面量 `0xB0C110` 在 `.text` 中出现 **489 次**，
且几乎全是同一模式：

```
lea  <reg>, [<obj> + <offset>]     ; 取某字段地址
push <reg>
push 0xB0C110                      ; 全局键
call 0x6CF240  (或 0x6CF2C0)       ; 注册/绑定该字段
```

⇒ `0xB0C110` **不是事件专用键**，而是引擎级**字段注册表的根**：
各处构造函数把"字段地址 + 全局注册表"交给统一 helper，完成元数据登记。
`TEventClass+0x30` 与 `+0x54` 只是这 489 处中的两处。

**对编译器含义**：`+0x30`/`+0x54` 存的是**接口对象指针**（由注册表按类型解析），
不是可硬编码的常量；写这两个字段必须通过引擎的注册机制，
直接填地址会导致序列化走错槽。

（本条把前轮"`0xB0C110` 是某接口键"的猜测**降级为已否**：它是全局注册表根。）

### 2.2 `TActionClass` 与 `TeamClass`

| 类 | 偏移 | 类型 | 语义 | 证据 |
|:---|:---|:---|:---|:---|
| `TActionClass` | `+0x90` | `dword` | **被 `Save` 序列化的最后一个字段** | `0x006E3ECD: mov edx,[esi+0x90]` → `call 0x4A1D50`；`0x006DD310` 同 |
| `TeamClass` | `+0x3C` | `dword` | 当前脚本步；与入参相同则**早退** | `0x006E9059/5C/5E` |

> **`+0x90` 的口径澄清**：`0x006DD8CB` 里的 `mov dl,[ecx+0x90]` **不是读 TActionClass**，
> 而是读 `Execute` 的**栈参数对象**（`ecx` 来自 `[esp+0x254]`，是 `pEvent`/触发者）。
> 判据：`0x006DD8BD: mov ecx,[esp+0x254]` 明确把 ecx 设为该参数；
> 而 `0x006DD8BB: mov esi,ecx` 才是 `this`。所以 `+0x90` 在两处是**两个不同对象的同一偏移**。
> 前轮把它记为 "`TActionClass+0x90` 是 byte" 是**误读**，已在 `LEDGER R-004` 记明。

> 注：`TActionClass` 尺寸 148 = `0x94`，字段在 `+0x90` ⇒ 它是**倒数第一个 dword**，
> 且被 `Save` 写入存档。`0x90+4 = 0x94` 与尺寸精确吻合，可作为"布局自洽"的佐证。

---

## 3. `TeamClass::AI` 早退语义 [实证]

```
0x006E9050  55               push ebp
0x006E9051  8B 6C 24 08      mov  ebp, [esp+8]        ; 调用方传入的"当前脚本步/帧"
0x006E9055  56 57            push esi; push edi
0x006E9057  8B F9            mov  edi, ecx            ; this = TeamClass*
0x006E9059  8B 47 3C         mov  eax, [edi+0x3C]     ; ★ 本队上一步
0x006E905C  3B E8            cmp  ebp, eax
0x006E905E  74 70            je   0x6E90D0           ; 相同 ⇒ 早退，不重复执行
```

⇒ **语义**：`TeamClass` 的记忆化短路。同一"步"不会被重复推进。
对编译器含义：队伍脚本的推进是**由外部传步号驱动**的，不是自走；
重放同一 tick 不会双执行。

---

## 4. 与语料的对照

| 项 | 语料 | 本线 | 判定 |
|:---|:---|:---|:---|
| `TeamTypeClass` 尺寸 | ATLAS 288 | **248** | 前轮已裁（CONFLICTS G-1） |
| `AITriggerTypeClass` 尺寸 | ATLAS 256 | **272** | 前轮已裁（G-2） |
| 上述 8 类尺寸 | 语料未记（未在 §11.2 表内） | 本轮首报 | ⭐ 本线新增 |
| `AbstractClass` 多继承 4 vptr | 语料未记 | 本轮首报 | ⭐ 本线新增 |

⇒ 语料对 `AbstractClass` 的**多继承结构完全没有记载**；
ATLAS §11.2 只列了 `HouseClass`/`CellClass` 等 24 槽类，未涉及本族。

---

## 5. 对战役编译器的直接含义

1. **写任何 `AbstractClass` 派生实例，头部必须是 4 个 vptr**（+0/+4/+8/+0xC），
   不是 1 个。只写 1 个 vptr 会导致接口调用跳到错误地址。
2. **尺寸必须逐类取**：`AbstractClass::GetSize` 返回 0 是桩，不能当基类尺寸用。
3. **`TEventClass` 的事件 Kind 在 `+0x2C`**，配合 `10_map_triggers.md` §3.4 的两级表
   即可判定某 Kind 是否有实现。
4. **`TeamClass` 不需要每帧推进**：`+0x3C` 相同即早退，重放安全。

---

## 6. 下一轮

| # | 悬项 |
|:--|:---|
| L-1 | `AbstractClass` 的 `+0x14..+0x1C` 三个 dword 语义（`Save` 不写，可能只在内存态） |
| L-2 | `+0x10` 与 `+0x20` 的业务语义（是 ID？引用计数？标志位？）——需找更多读点 |
| L-3 | `TaskForceClass` 212 字节的内部结构（29 项数组？） |
| L-4 | `ScriptTypeClass` 564 字节的大块结构 |
| L-5 | `TagClass` / `TriggerClass` 的字段（本轮只证了尺寸） |
| L-6 | `TEventClass` 的 Event/Action 参数区（`+0x30` 之后） |
