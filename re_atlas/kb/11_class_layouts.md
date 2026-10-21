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

> ### ⚠ 本节以下两段已被 `kb/21_swizzle_and_object_fields.md` 撤回（R-012）
>
> `0xB0C110` **不是**"引擎级字段注册表的根"，而是 **`SwizzleManagerClass::Instance`**：
> 静态初始化器 `0x006CF0C8` 直接往它写虚表 `0x7F4108`，而 `0x7F4108` 经 RTTI 反查
> 就是 `SwizzleManagerClass`（社区源 `YRpp/SwizzleManagerClass.h:26` 独立佐证）。
> `0x6CF240` 是该虚表的**槽 4**（`Here_I_Am`），语义是"把指针字段登记进 swizzle 表，
> **并把原字段清零**"（`0x006CF2A8: mov dword ptr [edi], 0`）——不是"元数据登记"。
>
> 另外 `TEventClass` 被登记的字段是**三个**（`+0x28` / `+0x30` / `+0x54`），
> 不是两个；`Save` 序列化**四项**，不是三项。
> 下方原文保留作为撤回留痕，**不要据其写补丁**。

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

> **☠ 以上三段已撤回（R-012）**。正确解读见页首警示框与
> `kb/21_swizzle_and_object_fields.md`：`0xB0C110` 是 `SwizzleManagerClass::Instance`，
> `0x6CF240` 是它的 `Here_I_Am` 槽，语义是"登记指针字段 **并把原字段清零**"，
> 供存档时做指针重定位（swizzling）——**与"字段元数据登记"完全无关**。
> "接口对象指针"这一形式判断仍然成立（`Save` 里确实走 `[p+4]->[vt+0x10]`），
> 但"由注册表按类型解析"是错的：它是从别处赋值进来的外部对象，见 L-21。

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

## 6. `TaskForceClass` 的结构线索（L-4，部分）

`TaskForceClass` 尺寸 **212 (`0xD4`)**，27 槽。各槽体首：

| 槽 | 地址 | 体首 | 判读 |
|---:|---|---|:---|
| 0 | `0x00410260` | `mov eax,[esp+0xC]; push ebx; test eax,eax` | 与 `AbstractClass` slot0 **同址**（继承未覆写） |
| 1 | `0x00410300` | `mov eax,1; ret 4` | 同父类 |
| 2 | `0x00410310` | `mov eax,1; ret 4` | 同父类 |
| 3 | `0x006E8710` | `mov eax,[esp+8]; test eax,eax; jne …; mov eax,0x80004003` | **`GetClassID`**（`E_POINTER` 守卫 + 写 `[0x7E9770]` 起的常量） |
| 4 | `0x00410450` | `mov dl,[ecx+0x20]` | 读 **`AbstractClass` 的 `+0x20` bool**（见 §0.3） |
| 5 | `0x006E86A0` | `call 0x410380` + `lea ecx,[esp+0xC]; push ecx` | **`Load` 包装**（`0x410380` 是带 `E_POINTER` 守卫的接口取值助手） |
| 6 | `0x006E8680` | `push a; push b; push c; call 0x410320; test eax; jl; xor eax` | **`Save` 包装**（`0x410320` 同族助手） |

**关键**：槽 4 读 `AbstractClass+0x20` 的 **bool**，证实 §0.3 推出的 `+0x20 = bool` 是
**派生类实际使用的字段**，不是我误判的填充。

**`0x410320` / `0x410380` / `0x6CF240` 是同一族"接口取值助手"** [实证]：
三者都在参数为空时返回 `0x80004003`（`E_POINTER`），非空则读 `[obj]` 取 vtable 后再分派。
⇒ 这是引擎的**通用 COM 风格包装**，不是各类自己的逻辑。
`TaskForceClass` 的槽 5/6 只是把 `+0x0C/+0x14` 等字段地址交给它做序列化。

**212 字节的字段图** [实证]（扫全部 27 槽体内 `[reg+disp]`，收 `disp < 0xD4` 者）：

| 偏移 | 出现次数 | 语义 | 证据 |
|:---|---:|:---|:---|
| `+0x04` / `+0x08` / `+0x0C` | 多次 | `AbstractClass` 的接口 vptr（继承） | 与 §0.3 一致 |
| `+0x10` | 2 | `AbstractClass` 的 dword 字段 | 与 §0.3 一致 |
| `+0x14` | 3 | 运行时态字段 | — |
| `+0x18` / `+0x1C` | 1 / 1 | 运行时态 | — |
| `+0x20` | 1 | `AbstractClass` 的 **bool** | 被 slot4 读 |
| `+0x24` / `+0x28` | 2 / 1 | 未知 | — |
| `+0x38` | 2 | 未知 | slot25/26 |
| **`+0x9C`** | **6** | **成员数量（count）** | `0x006E853F: mov eax,[edi+0x9C]` → `cmp esi,eax; jge` 循环上界 |
| **`+0xA4`** | **2** | **成员数组基址** | `0x006E8529: lea ebx,[edi+0xA4]` → 循环里 `mov ecx,ebx` |

**★ `TaskForceClass` 的成员容器 = `{ count @ +0x9C, array @ +0xA4 }`** [实证]

```
0x006E8527  33 F6               xor  esi, esi            ; i = 0
0x006E8529  8D 9F A4 00 00 00   lea  ebx, [edi+0xA4]     ; ★ 数组基址
0x006E852F  56                  push esi
0x006E8530  8D 44 24 14         lea  eax, [esp+0x14]
0x006E8534  68 6C 7F 81 00      push 0x817F6C            ; 格式串/模板
0x006E8539  50                  push eax
0x006E853A  E8 B5 09 0E 00      call 0x7C8EF4            ; sprintf 类
0x006E853F  8B 87 9C 00 00 00   mov  eax, [edi+0x9C]     ; ★ 成员数
0x006E8545  83 C4 0C            add  esp, 0xC
0x006E8548  3B F0               cmp  esi, eax
0x006E854A  7D 1A               jge  0x6E8566            ; i >= count ⇒ 退出
0x006E854C  8B CB               mov  ecx, ebx            ; 数组基址 → ecx
```

⇒ **`+0xA4` 与 `+0x9C` 相距 8 字节，中间 `+0xA0` 未被单独引用**，
说明容器大概率是 `{ ptr @ +0xA0, count @ +0x9C, cap @ +0xA4 }` 或
`{ count @ +0x9C, ??? @ +0xA0, array @ +0xA4 }` 的**非常规顺序**布局，
**不是**标准 `DynamicVectorClass`（后者是 `+4=Items, +0x10=Count`）。
若按标准向量布局解读会错位 —— 这一点必须在编译器侧显式建模。

**`0x7C8EF4`** 是格式化函数（`push 参数; push 目标缓冲; push 模板` 三参）。

⚠ **关于 `0x817F6C` 的口径更正**：该地址在 **`.data`**（可写段），
不是 `.rdata`。虽然其首字节恰好解出 `"%d"`、`0x81C000` 解出 `"%d,%d"`，
但 `.data` 的内容是**运行时可变**的，**不能当作静态格式串**引用。
本轮撤回"格式串实测为 `%d`"的断言 —— 那只是该可写槽在**文件初始状态下**的字节，
运行时可能被初始化代码改写。

**能确定的**：`+0x9C` 是循环上界（`cmp esi,[edi+0x9C]; jge` 已实证），
循环体用一个"取参数、格式化到栈缓冲"的 helper 处理每个成员。
成员具体如何命名/序列化，需在运行时或追踪该 helper 的参数来源才能定，列 L-11。

这解释了 `+0x9C` 为何在循环条件里反复读：它是"要处理多少个成员"的上界。

| # | 悬项 |
|:--|:---|
| L-1 | `AbstractClass` 的 `+0x14..+0x1C` 三个 dword 语义（`Save` 不写，可能只在内存态） |
| L-2 | `+0x10` 与 `+0x20` 的业务语义（是 ID？引用计数？标志位？）——需找更多读点 |
| L-3 | `TaskForceClass` 212 字节的内部结构（29 项数组？） |
| L-4 | `ScriptTypeClass` 564 字节的大块结构 |
| L-5 | `TagClass` / `TriggerClass` 的字段（本轮只证了尺寸） |
| L-6 | `TEventClass` 的 Event/Action 参数区（`+0x30` 之后） |

---

## 7. 序列化顺序：先基类、后派生 [实证]

`ScriptClass::Save`（`0x006914E0`）给出本族**统一模式**：

```
0x006914E0  56                  push esi
0x006914E1  57                  push edi
0x006914E2  8B 7C 24 0C         mov  edi, [esp+0xC]      ; 流对象
0x006914E6  8B F1               mov  esi, ecx            ; this
0x006914E8  57                  push edi
0x006914E9  E8 22 EF D7 FF      call 0x00410410          ; ★ 先调 AbstractClass::Save
0x006914EE  8B 46 2C            mov  eax, [esi+0x2C]     ; ★ 再写自己的 +0x2C
0x006914F1  8B CF               mov  ecx, edi
0x006914F3  50                  push eax
0x006914F4  E8 57 08 E1 FF      call 0x004A1D50          ; 写 dword
0x006914F9  5F 5E               pop  edi; pop esi
```

⇒ **派生类的 `Save` 第一件事是调基类 `Save`**，然后追加自己的字段。
对编译器的含义：存档字节序列是**基类在前、派生在后**的拼接；
读档顺序必须严格对称，否则后续所有字段错位。

`ScriptClass` 尺寸仅 48 字节，`Save` 只多写**一个** `+0x2C` dword ⇒
其实例数据极简，主要靠继承来的两字段 + 自身一个 dword。

---

## 8. `ScriptTypeClass` 的容器簇

`ScriptTypeClass` 尺寸 **564 (`0x234`)**，字段热点：

| 偏移 | 次数 | 备注 |
|:---|---:|:---|
| `+0x04` / `+0x08` / `+0x0C` | 11 / 12 / 9 | 继承的接口 vptr |
| `+0x10` / `+0x14` | 5 / 4 | 继承字段 |
| `+0x18..+0x28` | 少 | 继承尾部 + 自有 |
| **`+0x98` / `+0x0A0` / `+0x0A4` / `+0x0A8`** | 2 / 9 / 2 / 2 | **容器簇**（与 `TaskForceClass+0x9C/+0xA4` 同族） |

⇒ `+0x98` 一带是本族多处的**统一容器布局**：
`ScriptTypeClass` 在 `+0xA0` 最热（9 次），`TaskForceClass` 在 `+0x9C`（6 次）。
两类偏移差 4 字节 ⇒ 可能是**同一模板类在不同基类尺寸下的实例化**，
或各自带一个额外 dword 前缀。**待下一轮统一建模**（列 L-7）。

---

## 10. 容器簇的统一模型（L-7，本轮解）

把两类在 `0x90..0xB0` 窗口的访问频率并排：

| 偏移 | TaskForceClass (212B) | ScriptTypeClass (564B) |
|:---|---:|---:|
| `+0x98` | 4 | 2 |
| **`+0x9C`** | **6** | — |
| **`+0xA0`** | — | **9** |
| `+0xA4` | 2 | 2 |
| `+0xA8` | 2 | 2 |
| `+0xB0` | 1 | — |

**统一读法**：两类的"计数"字段相差 **4 字节**（`0x9C` vs `0xA0`），
而 `+0x98` / `+0xA4` / `+0xA8` 三者**完全对齐**。这只有一个自洽解释：

```
+0x98 : 容器对象头（两者共有）
+0x9C : (TaskForce 独有) 计数
+0xA0 : (ScriptType 独有) 计数  ← 同一逻辑字段，因基类多 4 字节而右移
+0xA4 : 数组/条目基址
+0xA8 : 容量或尾指针
```

⇒ **不是"同一模板类的不同实例化"，而是同一套"容器三元组"布局
在不同基类尺寸下整体平移 4 字节**。`TaskForceClass` 直接继承 `AbstractTypeClass`（27 槽），
`ScriptTypeClass` 也是，但两者自身前缀不同，导致容器起点差 4。

**`+0xA0` 的循环证据** [实证]（`ScriptTypeClass` slot26 `0x00691831`）：

```
0x00691831  3B B7 A0 00 00 00   cmp  esi, [edi+0xA0]     ; ★ 与 TaskForce 的 +0x9C 同角色
0x00691837  7D 23               jge  0x69185C            ; i >= count ⇒ 退出
0x00691839  8D 4C 24 20         lea  ecx, [esp+0x20]
0x0069183D  51                  push ecx
0x0069183E  8B CB               mov  ecx, ebx
0x00691840  E8 9B 24 09 00      call 0x00723CE0          ; 按索引取条目
```

且 `0x006918CF: mov [esi+0xA0], edi` 是**写**（初始化时置 0 或置初值），
与 `0x00691831` 的读配对 ⇒ 确认它是**计数器**而非指针。

**`+0xA4` 是数组基址**（`ScriptTypeClass` 同 `TaskForce`）：
由 §6 中 `TaskForceClass` 的 `lea ebx,[edi+0xA4]` 已证；
`ScriptTypeClass` 的 `+0xA4` 亦仅作基址使用。

**`0x723CE0`** 的实测体首是 `mov eax,[ecx+4]; mov ecx,[ecx]; push eax; push ecx;
push <模板>; call 0x7C8EF4` ⇒ 它是**格式化 helper**，不是"按索引取条目"的访问器。
其模板参数在 `.data`（运行时可变），本轮**不判定其语义**（列 L-11）。

⇒ 编译器侧能用的只有：`count @ count_off`（按类取）与 `array base @ +0xA4`。
**元素 stride 仍未实证**（L-9），而 §10.1 的伪代码里 `array[i]` 的 i 缩放
在 stride 未定前**不可直接使用**。

### 10.1 对编译器的统一接口（已实证部分）

```text
count_off(TaskForceClass)   = 0x9C     # 实证
count_off(ScriptTypeClass)  = 0xA0     # 实证
array_base                  = obj + 0xA4   # 两类相同，实证
count                       = *(u32*)(obj + count_off(cls))
```

**只保证以上三项**。`item(i)` 的寻址方式**尚未实证**：
数组元素 stride 未确定（L-9），且本轮把 `0x723CE0` 从"条目访问器"
更正为"格式化 helper"（见 §10 末）。**在 stride 定案前不要按索引直接解引用**。

**警告**：`count_off` **不是全局常量**，必须按类取。硬编码 `0x9C` 会在
`ScriptTypeClass` 上读到错误字段。

---

## 11. 下一轮

| # | 悬项 |
|:--|:---|
| L-1 | `AbstractClass+0x14..+0x1C` 三个 dword 语义 |
| L-2 | `+0x10` / `+0x20(bool)` 的业务语义 |
| L-3 | ✅ 已解：`0xB0C110` = 全局字段注册表根 |
| L-4 | ✅ 已解：`TaskForceClass` 容器 `{count@0x9C, array@0xA4}` |
| L-5 | ✅ 部分解：容器簇统一模型见 §10 |
| L-6 | `TEventClass+0x30` / `+0x54` 两个接口对象的真实类型 |
| L-7 | ✅ 已解：容器簇 = 同套三元组在不同基类尺寸下平移 4 字节 |
| L-8 | 补：`TeamTypeClass` 248 的异族核验 |
| **L-9** | **容器元素大小**（`array[i]` 的 stride）——决定能否按索引正确读写 |
| **L-10** | `+0xA8` 的语义（容量？尾指针？） |
| **L-11** | `0x723CE0` / `0x7C8EF4` 的模板参数来源（模板在 `.data`，运行时可变，需追踪写入点） |

---

## 12. `ScriptTypeClass` 的解析代码（L-9/L-10/L-11 进展）

`ScriptTypeClass` slot25（`0x006918A7` 起）是**从 INI 段解析脚本体**的流程，逐段：

```
0x006918A7  8B AC 24 A0 00 00 00   mov  ebp, [esp+0xA0]      ; 参数（INI 段对象）
0x006918AE  56                     push esi
0x006918AF  8B F1                  mov  esi, ecx             ; this
0x006918B1  8B CD                  mov  ecx, ebp
0x006918B3  E8 48 52 E9 FF         call 0x526B00             ; 初始化 ebp 的 +4/+8 为 0
0x006918B8  55                     push ebp
0x006918B9  8B CE                  mov  ecx, esi
0x006918BB  E8 A0 F1 D7 FF         call 0x410A60             ; 前置校验（返回 bool）
0x006918C0  84 C0                  test al, al
0x006918C2  0F 84 9A 00 00 00      je   0x691962             ; 校验失败 ⇒ 退出
0x006918C8  53 57                  push ebx; push edi
0x006918CA  33 FF                  xor  edi, edi             ; i = 0
0x006918CC  8D 5E 24               lea  ebx, [esi+0x24]      ; ★ 另一个对象 @ +0x24
0x006918CF  89 BE A0 00 00 00      mov  [esi+0xA0], edi      ; ★ 计数清零
0x006918D5  57                     push edi
0x006918D6  8D 44 24 1C            lea  eax, [esp+0x1C]
0x006918DA  68 6C 7F 81 00         push <模板 .data>
0x006918DF  50                     push eax
0x006918E0  E8 0F 76 13 00         call 0x7C8EF4             ; 生成第 i 条的键名
0x006918E5  83 C4 0C               add  esp, 0xC
0x006918E8  8D 4C 24 18            lea  ecx, [esp+0x18]
0x006918EC  E8 FF 63 09 00         call 0x727CF0             ; 字符串 → 数值（atoi 类）
0x006918F1  8D 4C 24 28            lea  ecx, [esp+0x28]
0x006918F5  68 80 00 00 00         push 0x80                 ; ★ 缓冲宽 128
0x006918FA  51                     push ecx
0x006918FB  8D 54 24 20            lea  edx, [esp+0x20]
0x006918FF  68 64 9F 88 00         push <模板 .data>
0x00691904  52                     push edx
0x00691905  53                     push ebx                  ; ★ +0x24 对象
0x00691906  8B CD                  mov  ecx, ebp
0x00691908  E8 03 71 E9 FF         call 0x528A10             ; 5 参读取
0x0069190D  85 C0                  test eax, eax
0x0069190F  7E 3C                  jle  0x69194D             ; 读失败/空 ⇒ 结束循环
```

**如实结论（不再往前推）**：

| 项 | 状态 |
|:---|:---|
| `+0x24` | **一个独立对象**（`lea ebx,[esi+0x24]`），作为 5 参调用第 1 实参传入。**归属见 §16 更正**：它是 `AbstractTypeClass` 的 INI 槽，不是 `ScriptTypeClass` 私有 |
| `+0xA0` | **计数器**，循环前清零（`mov [esi+0xA0],edi`），循环条件读它 |
| `0x528A10` | **`ret 0x14` = 5 个 4 字节实参**（`0x00528BC6`/`0x00528BFA` 两处 ret 均为此值），内含 `cmp [esp+0x2c],2; jl` 的最小实参校验 ⇒ 强烈指向 INI `ReadString`（段/键/默认/缓冲/宽度） |
| `0x526B00` | `mov [ecx+4],0; mov [ecx+8],0; ret` ⇒ 把对象 `+4/+8` 清零（小结构初始化） |
| `0x727CF0` | 逐字符遍历字符串，`mov al,[edx]` ⇒ **`atoi`/数字解析** 形态 |
| `0x7C8EF4` | 格式化（模板在 `.data`，运行时可变） |
| 模板 `0x817F6C` / `0x889F64` | **在 `.data`，不做语义判定** |

⇒ **`+0xA4` 不是"已解析的成员数组"**，本轮之前把它当"数组基址"是**过度解读**。
从本段代码看，`+0x24` 才是被读取的容器对象，`+0xA0` 只是已处理条目数。
`+0xA4` 的角色需在别处（写入路径）确认，列 **L-12**。

### 12.1 又一次口径收回

**曾写**（§6、§10）：`+0xA4` = "成员数组基址"，并给出伪代码 `array = obj+0xA4`。

**现状**：`+0xA4` 仅被 `TaskForceClass` 的 `lea ebx,[edi+0xA4]` 当作**传入参数**使用，
本段 `ScriptTypeClass` 代码里 `+0xA4` **根本没出现**（用的是 `+0x24`）。
⇒ **"两类的容器三元组完全对齐"这个模型证据不足**，撤回。
保留的只有：`+0x9C`（TaskForce）与 `+0xA0`（ScriptType）都是**计数**（各有循环实证）。

**新纪律（本线第 5 条）**：
**"两个类同一偏移"不等于"同一字段"**。必须两处都有独立证据（读 + 写/循环）
才能合并建模；仅有"地址相邻"或"都在某个窗口"不构成证据。

---

## 13. 下一轮

| # | 悬项 |
|:--|:---|
| L-1 | `AbstractClass+0x14..+0x1C` 三个 dword 语义 |
| L-2 | `+0x10` / `+0x20(bool)` 的业务语义 |
| L-3 | ✅ `0xB0C110` = 全局字段注册表根 |
| L-4 | ✅ `TaskForceClass` 计数 @ `+0x9C`（循环实证） |
| L-5 | 容器统一模型 —— **部分撤回**，见 §12.1 |
| L-6 | `TEventClass+0x30` / `+0x54` 接口对象类型 |
| L-7 | 容器簇统一模型 —— **撤回**，见 §12.1 |
| L-8 | 补：`TeamTypeClass` 248 异族核验 |
| L-9 | 元素 stride（`array[i]`）—— 仍未知 |
| L-10 | `+0xA8` 语义 |
| L-11 | `.data` 模板参数的写入点（决定键名/值格式） |
| **L-12** | **`+0xA4` 的真实角色**（`TaskForce` 传入参数 vs `ScriptType` 未用） |
| **L-13** | **`ScriptTypeClass+0x24` 那个对象的类型**（5 参调用的首实参） |
| **L-14** | `0x528A10` 的**第 2/3 实参语义**（已证 5 参 + `ret 0x14`；段/键/默认/缓冲/宽度 的顺位待确认） |

---

## 14. ★ L-9/L-12/L-10 一并解决：`TaskForceClass` 的成员数组 = `{id, value}` 对，stride 8

`TaskForceClass` slot25 的**存储路径**给出了完整答案（`0x006E8470..0x006E84BC`）：

```
0x006E8470  68 80 00 00 00         push 0x80              ; 缓冲宽 128
0x006E8475  51                     push ecx               ; 键名缓冲
0x006E8476  68 64 9F 88 00         push <模板 .data>
0x006E847B  52                     push edx
0x006E847C  53                     push ebx               ; 段对象
0x006E847D  8B CD                  mov  ecx, ebp
0x006E847F  E8 8C 05 E4 FF         call 0x528A10          ; 5 参读取
0x006E8484  85 C0                  test eax, eax
0x006E8486  7E 3F                  jle  0x6E84C7          ; 读空 ⇒ 结束
0x006E8488  8D 44 24 38            lea  eax, [esp+0x38]
0x006E848C  8D 4C 24 10            lea  ecx, [esp+0x10]
0x006E8490  50                     push eax
0x006E8491  E8 5A CA DD FF         call 0x004C4EF0        ; 解析成"对"
0x006E8496  8B 8E 9C 00 00 00      mov  ecx, [esi+0x9C]   ; ★ 当前计数（也是下一个下标）
0x006E849C  8B 10                  mov  edx, [eax]        ; 对的第 1 个 dword
0x006E849E  89 94 CE A4 00 00 00   mov  [esi + ecx*8 + 0xA4], edx   ; ★ stride = 8
0x006E84A5  8B 40 04               mov  eax, [eax+4]      ; 对的第 2 个 dword
0x006E84A8  89 84 CE A8 00 00 00   mov  [esi + ecx*8 + 0xA8], eax   ; ★ 同一元素的高 4 字节
0x006E84AF  8B 86 9C 00 00 00      mov  eax, [esi+0x9C]
0x006E84B5  8B 8C C6 A8 00 00 00   mov  ecx, [esi + eax*8 + 0xA8]   ; 读回刚写的 value
0x006E84BC  85 C9                  test ecx, ecx
```

### 14.1 最终布局

| 项 | 值 | 证据 |
|:---|:---|:---|
| 元素计数 | `obj + 0x9C`（u32） | 作下标 `ecx`，也作循环上界 |
| 数组基址 | `obj + 0xA4` | `[esi + ecx*8 + 0xA4]` |
| **元素 stride** | **8 字节** | `ecx*8` 伸缩，两次写相差 4（`+0xA4` / `+0xA8`） |
| 元素结构 | `{ dword id_or_index @+0, dword value @+4 }` | 两次连续写同一 `ecx*8` 基址 |
| `+0xA8` | **不是独立字段**，是 `array[i].value` 的地址 | `[esi+ecx*8+0xA8]` 与基址同 stride |

⇒ 这同时解释了 §6 里"§6 中 `+0xA8` 出现 2 次" —— 它其实**恒与 `+0xA4` 成对出现**，
是数组元素的第二半，不是独立成员。**L-10 关闭**。

⇒ **L-12 关闭**：`+0xA4` 确为**数组基址**，但只对 `TaskForceClass` 成立；
§12.1 撤回的只是"`ScriptTypeClass` 也用 `+0xA4`"这个跨类推广，不是它在本类的作用。

### 14.1b `0x004C4EF0` 的作用（部分）

```
0x004C4EF0  83 EC 40              sub  esp, 0x40
0x004C4EF3  8B 54 24 44           mov  edx, [esp+0x44]     ; 输入串
0x004C4F0A  C7 06 00 00 00 00     mov  [esi], 0            ; ★ 清零结果的第 1 dword
0x004C4F10  C7 46 04 00 00 00 00  mov  [esi+4], 0          ; ★ 清零第 2 dword
0x004C4F04  68 5C 08 82 00        push 0x0082085C          ; 模板（在 .data）
```

⇒ 它把输入串解析进一个**两个 dword 的结果结构**，先清零再解析。
这与 §14 的"元素 = `{dword, dword}`"完全吻合 ⇒ 元素确实是 8 字节二元组。

模板 `0x82085C` 在 **`.data`（可写）**，其文件初始字节为 `%d,%s`，
**但按本线第 4 条纪律不当作静态格式串**；只记位置，不据其推语义。

### 14.2 与 `ScriptTypeClass` 的差异（不要再混用）

| 项 | TaskForceClass | ScriptTypeClass |
|:---|:---|:---|
| 计数 | `+0x9C` ✅ 实证 | `+0xA0` ✅ 实证 |
| 数组基址 | `+0xA4`，stride 8 ✅ 实证 | **未找到**（解析走 `+0x24` 子对象） |
| 元素 | `{id, value}` 8 字节 | 未知 |

⇒ **两类的"容器"不是同一套东西**，不得共用伪代码。§12.1 的撤回仍有效。

---

## 15. 下一轮

| # | 悬项 |
|:--|:---|
| L-1 | `AbstractClass+0x14..+0x1C` 三个 dword 语义 |
| L-2 | `+0x10` / `+0x20(bool)` 的业务语义 |
| L-3 | ✅ `0xB0C110` = 全局字段注册表根 |
| L-4 | ✅ `TaskForceClass` 计数 @ `+0x9C` |
| L-5 | 容器统一模型 —— 撤回（§12.1） |
| L-6 | `TEventClass+0x30` / `+0x54` 接口对象类型 |
| L-7 | 容器簇统一模型 —— 撤回（§12.1） |
| L-8 | 补：`TeamTypeClass` 248 异族核验 |
| L-9 | ✅ **stride = 8**（`{id, value}` 对） |
| L-10 | ✅ 关闭：`+0xA8` 是元素第二半，非独立字段 |
| L-11 | `.data` 模板参数的写入点 |
| L-12 | ✅ `+0xA4` = TaskForce 的数组基址（不推广到 ScriptType） |
| L-13 | `ScriptTypeClass+0x24` 对象类型 |
| L-14 | `0x528A10` 第 2/3 实参顺位 |
| **L-15** | `0x004C4EF0` 的实参语义（已证：清零 `[esi]`/`[esi+4]` 两个 dword，再用 `.data` 模板 `0x82085C` 分派；模板在可写段，故不判内容） |

---

## 16. ★ L-13 解：`+0x24` / `+0x64` 是 `AbstractTypeClass` 的 INI 槽，不是脚本专用

**关键归属发现** [实证]：`0x00410A60` 并不是 `ScriptTypeClass` 的私有函数 ——
它在 **`AbstractTypeClass` 的 vtable 里是 slot 25**（`vt=0x007E2000`），
同时被 `SideClass`（`vt=0x007F2EC0`）继承为同一槽。

⇒ §12 里"`ScriptTypeClass` slot25 是脚本解析"的表述**过窄**：
它实际是**所有类型类共用的 `ReadINI`**。

### 16.1 两个槽的语义

| 槽（`AbstractTypeClass`） | VA | 体首 | 判读 |
|---:|---|---|:---|
| 24 | `0x00410C20` | `ret 4` | 空桩 |
| **25** | **`0x00410A60`** | `sub esp,0x434` → `lea ebp,[ebx+0x24]` → `call 0x526810` 校验 → `push 0x31` → `call 0x528A10` | **`ReadINI`** |
| 26 | `0x00410B90` | `push 0; lea edi,[esi+0x24]; call 0x5257C0` → `lea eax,[esi+0x64]` | **`WriteINI`** |

`0x00410B90` 完整前缀：
```
0x00410B90  53                  push ebx
0x00410B91  8B 5C 24 08         mov  ebx, [esp+8]         ; INI 对象
0x00410B95  56                  push esi
0x00410B96  8B F1               mov  esi, ecx             ; this
0x00410B98  57                  push edi
0x00410B99  6A 00               push 0
0x00410B9B  8D 7E 24            lea  edi, [esi+0x24]      ; ★ 第一个 INI 槽
0x00410B9E  8B CB               mov  ecx, ebx
0x00410BA0  57                  push edi
0x00410BA1  E8 1A 4C 11 00      call 0x5257C0             ; 写出 +0x24 槽
0x00410BA6  8D 46 64            lea  eax, [esi+0x64]      ; ★ 第二个 INI 槽
```

⇒ **`+0x24` 与 `+0x64` 是 `AbstractTypeClass` 前缀里的一对 INI 缓冲**，
所有派生类型类（`ScriptTypeClass` / `TaskForceClass` / `TeamTypeClass` / …）共享。

### 16.2 对前文的更正

- §12 写的"`+0x24` = 独立子对象（**本族通用**）"—— 方向正确，但**归属写错**：
  它不是"ScriptType 族的"，而是 **`AbstractTypeClass` 的**。
- §16 之前把 `ScriptTypeClass+0xA0`（计数）与 `AbstractTypeClass+0x24`（INI 槽）
  混在同一个解析流程描述里，容易让人以为 `+0xA0` 也属于基类。**`+0xA0` 仍是
  `ScriptTypeClass` 自有**。

### 16.3 `push 0x31` 的含义 —— **未判定**

调用点 `0x00410A8C..0x00410AA0` 的压栈序列（从右到左）：

```
push edi               ; 保留（稍后覆盖）
lea  eax, [esp+0x44]   ; 栈缓冲
lea  edi, [ebx+0x64]   ; ★ 第 2 个 INI 槽地址
push 0x31              ; ★ =49，第 5 实参
push eax               ; 第 4 实参：栈缓冲
push edi               ; 第 3 实参：+0x64 槽
push 0x817854          ; 第 2 实参：模板（.data）
push ebp               ; 第 1 实参：+0x24 槽
mov  ecx, esi          ; INI 对象
call 0x528A10          ; ret 0x14 ⇒ 5 实参
```

在 `0x528A10` 内部追第 5 实参（`[esp+0x2c]`）的用途：

| 位置 | 用法 |
|:---|:---|
| `0x00528A26` | `cmp [esp+0x2c], 2; jl` —— 只作"至少 2"的前置校验 |
| `0x00528B6F` | `mov edi,[esp+0x2c]` 后紧接 `mov [ebp+8],esi; mov [ebp+4],ebx; xor eax,eax` |
| `0x00528B84 / BA4 / BAC` | 均在同一返回路径上重复取回 |

⇒ 它**没有**被用作循环上界或 `rep movs` 的计数；观测到的都是"取进 `edi` 后走返回路径"。
**本轮不判定其语义**（可能是成功/失败标志、抑或是被调用方回填的 out 参数）。
列 **L-16**，需要看调用方在 `call` 之后如何使用 `eax` / `edi` 才能定。

---

## 17. 下一轮

| # | 悬项 |
|:--|:---|
| L-1 | `AbstractClass+0x14..+0x1C` 三个 dword 语义 |
| L-2 | `+0x10` / `+0x20(bool)` 的业务语义 |
| L-3 | ✅ `0xB0C110` = 全局字段注册表根 |
| L-4 | ✅ `TaskForceClass` 计数 @ `+0x9C` |
| L-5 | 容器统一模型 —— 撤回（§12.1） |
| L-6 | `TEventClass+0x30` / `+0x54` 接口对象类型 |
| L-7 | 容器簇统一模型 —— 撤回（§12.1） |
| L-8 | 补：`TeamTypeClass` 248 异族核验 |
| L-9 | ✅ stride = 8 |
| L-10 | ✅ `+0xA8` 是元素第二半 |
| L-11 | `.data` 模板参数的写入点 |
| L-12 | ✅ `+0xA4` = TaskForce 数组基址（不推广） |
| L-13 | ✅ `+0x24`/`+0x64` = `AbstractTypeClass` 的 INI 槽对 |
| L-14 | `0x528A10` 第 2/3 实参顺位 |
| L-15 | `0x4C4EF0` 实参语义 |
| **L-16** | `ReadINI` 里 `push 0x31`(49) 的语义（上限 vs 长度） |
