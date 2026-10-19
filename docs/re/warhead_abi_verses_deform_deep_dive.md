# WarheadTypeClass Verses / Deform ABI 深挖（R-03）

> [META]
> 任务=R-03 · 负责方=R 轨逆向代理 · 日期 2026-09-30
> 目标：独立实证 Deform 字段偏移、Verses[armor] 乘算施加点、+0xA0 之前字段布局
> 二进制：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x400000`
> 证据分级：`[实证]`（字节级已见）/ `[推演]`（结构外推）/ `[待实测]`（未跑）
> 可复算：`out/re_work/re_sprint/warhead_abi/`（脚本 + claims.txt + 反汇编落盘）
> **写作用域**：本文 + `out/re_work/re_sprint/warhead_abi/**`；未改任何已有文档

---

## 0. 结论速览

| # | 问题 | 结论 | 等级 |
|---|---|---|---|
| 1 | `Deform` 真实偏移 | **`+0x98`（double，8B，`+0x98..+0x9F`）**；源文档 `+0xA8` 为错 | **[实证]** |
| 2 | `+0xA8` 是什么 | `Verses[1]`（armor=Plate 档），不是 Deform | **[实证]** |
| 3 | `Verses[armor]` 乘算施加点 | **8 处 FPU 索引访存已定位**（`fmul/fld [reg+armor*8+0xA0]`），见 §3 | **[实证]** |
> 【W3 勘误 · W3-A6/ISSUE-VERSES-SITES-COUNT】改前：Verses[armor]` 乘算施加点 | **8 处；改后：Verses FPU 索引访存共 9 处 (V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c)；依据：errata_sync_master_table.md:22 (R-E07); warhead_verses_residual_p2.md:18, 58；分级：P1
| 4 | `+0xA0` 之前布局 | AbstractClass `0x00..0x23` + AbstractTypeClass `0x24..0x97`，见 §4 | **[实证]** |
| 5 | E-8 勘误 | 可从「存疑」升级为「定谳：Deform=+0x98」 | **[实证]** |

> 【勘误 2026-09-30 · R-E07 · errata_sync】原文「8 处 FPU 索引访存」系计数笔误。实证为 **9 处**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c），见 §3.2 表（实列 9 行）与 warhead_verses_residual_p2.md:18,58 计数勘误 / §1.2 九处站点总表。原文保留不删字。

> **禁令变更**：在本报告发布前，约定「Deform 偏移闭环前不得按 +0xA8 读写 Deform」。
> 现 Deform 已闭环为 `+0x98` ⇒ 该禁令可解除，改按 **`+0x98`** 读写；`+0xA8` 归 `Verses[1]`。

---

## 1. Deform 偏移定谳（P0）

### 1.1 装载点（LoadFromINI）

`WarheadTypeClass::LoadFromINI` = `0x0075D3A0`（`esi ≡ this` 全程，序言 `0x75D3B1: 8B F1`）。

```asm
; INI 键 "Deform" @ 0x00847D80
0x0075D777  8B 8E 9C 00 00 00    mov  ecx, [esi+0x9C]     ; 默认值 hi
0x0075D77D  8B 96 98 00 00 00    mov  edx, [esi+0x98]     ; 默认值 lo
0x0075D783  51                   push ecx
0x0075D784  52                   push edx
0x0075D785  68 80 7D 84 00       push 0x847D80            ; "Deform"
0x0075D78A  55                   push ebp                 ; section
0x0075D78B  8B CF                mov  ecx, edi
0x0075D78D  E8 3E AC DC FF       call 0x5283D0            ; CCINIClass::Read_Double
0x0075D792  DD 9E 98 00 00 00    fstp qword ptr [esi+0x98] ; ★ Deform ← +0x98
```

`DD 9E 98 00 00 00` = `fstp qword [esi+0x98]`，**双精度 8 字节**，落在 `+0x98..+0x9F`。

### 1.2 构造函数交叉印证

`WarheadTypeClass::ctor` = `0x0075CEC0`：

```asm
0x0075CED8  89 9D 98 00 00 00    mov [ebp+0x98], ebx      ; Deform.lo = 0
0x0075CEDE  89 9D 9C 00 00 00    mov [ebp+0x9C], ebx      ; Deform.hi = 0   → double 0.0
0x0075CEE4  89 9D F8 00 00 00    mov [ebp+0xF8], ebx      ; ProneDamage.lo = 0
0x0075CEEB  C7 85 FC 00 00 00 00 00 F0 3F
                               mov [ebp+0xFC], 0x3FF00000 ; ProneDamage.hi → double 1.0
```

`+0x98` 被当作独立 8 字节标量初始化；`+0xF8` 是 `ProneDamage`（默认 1.0）。
**`+0xA0..+0xF7` 完全留给 Verses，与 Deform 无重叠。**

### 1.3 与源文档冲突

| 来源 | 记载 | 判定 |
|---|---|---|
| `weapons_damage_production.md:127` | `Deform \| 0xA8` | **错**（+0xA8 = Verses[1]） |
| `YRpp/WarheadTypeClass.h` | `double Deform;` 后接 `double Verses[0xB];` | **对**（字段顺序） |
| 本报告 | `Deform = +0x98` | **[实证] 定谳** |

**E-8 定谳**：`Deform` 真实偏移 **`+0x98`**（double）；`+0xA8` = `Verses[1]`。源文档 L127 应改为 `0x98`。

---

## 2. Verses[11] 偏移复核（P0，继承 R6）

装载器（R6 已实证，本任务复核字节一致）：

```asm
0x0075DE06  8D 9E A0 00 00 00    lea  ebx, [esi+0xA0]     ; &Verses[0]
0x0075DE0C  BD 0B 00 00 00       mov  ebp, 0xB            ; 11 次
0x0075DE31  DC 0D 08 38 7E 00    fmul qword [0x7E3808]    ; ×0.01（百分数→倍率）
0x0075DE48  DD 1B                fstp qword [ebx]         ; 落库
0x0075DE52  83 C3 08             add  ebx, 8
```

- 默认值串 `0x00847C40` = `100%%,100%%,…`（11 项）· INI 键 `"Verses"` @ `0x00847C38`
- 覆盖 **`+0xA0 … +0xF7`**（11 × double）
- `+0xB0` = `Verses[2]`（E-2/E-7 维持）

---

## 3. Verses[armor] 施加点（P1，本任务新实证）

### 3.1 ABI 惯用式（全局）

```asm
call  [obj+0x84]                ; GetType()  v[33] → TechnoTypeClass*
mov   ecx, [type+0x9C]          ; ArmorType 枚举 0..10
mov   eax, [obj2+0xAC]          ; WarheadTypeClass*
fld / fmul  qword [eax + ecx*8 + 0xA0]   ; ★ Verses[armor]
```

- **armor 源** = `TechnoTypeClass+0x9C` [实证]
- **warhead 源** = 某对象 `+0xAC`（`WarheadTypeClass*`）[实证；宿主类名 [待实测]]
- 旧扫描「`*8+0xA0/0xB0` 0 命中」的原因：Verses 访存是 **FPU qword**（`DC/DD` 前缀），
  不是整数 `mov`；本任务扩面覆盖 `fmul/fld/fstp/fcomp/fild/fist/movsd/mulsd` 形态后命中。

### 3.2 施加点清单（8 条指令，6 个语义簇）

> 【勘误 2026-09-30 · R-E07 · errata_sync】原文标题「8 条指令」系计数笔误。本表实列 **9 行 / 9 条指令**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c），语义簇仍为 6 个。权威：warhead_verses_residual_p2.md:18,58。原文保留不删字。

| ID | VA | FileOffset | 原始字节 | 反汇编 | 语义 |
|---|---|---|---|---|---|
| **V1** | `0x0048923D` | `0x08923D` | `DC 8C D7 A0 00 00 00` | `fmul qword [edi+edx*8+0xA0]` | **伤害缩放**（整数伤害 × Verses[armor] → int） |
| **V2a** | `0x006F36FE` | `0x2F36FE` | `DD 84 C8 A0 00 00 00` | `fld qword [eax+ecx*8+0xA0]` | 有效性：`Verses[armor] != 0.0` |
| **V2b** | `0x006F3731` | `0x2F3731` | `DD 84 C2 A0 00 00 00` | `fld qword [edx+eax*8+0xA0]` | 同 V2 |
| **V3** | `0x006F7D3D` | `0x2F7D3D` | `DD 84 C1 A0 00 00 00` | `fld qword [ecx+eax*8+0xA0]` | 阈值：`> 0.02` |
| **V4** | `0x006FCB6A` | `0x2FCB6A` | `DD 84 C7 A0 00 00 00` | `fld qword [edi+eax*8+0xA0]` | 有效性：`!= 0.0` |
| **V5** | `0x00708AF7` | `0x308AF7` | `DD 84 C1 A0 00 00 00` | `fld qword [ecx+eax*8+0xA0]` | 阈值：`> 0.01` |
| **V6a** | `0x0070CEB2` | `0x30CEB2` | `DC 8C C8 A0 00 00 00` | `fmul qword [eax+ecx*8+0xA0]` | 伤害/威胁加权（后接 `fchs`） |
| **V6b** | `0x0070CEC7` | `0x30CEC7` | `DC 8C D0 A0 00 00 00` | `fmul qword [eax+edx*8+0xA0]` | 同 V6a |
| **V6c** | `0x0070CF49` | `0x30CF49` | `DC 8C C1 A0 00 00 00` | `fmul qword [ecx+eax*8+0xA0]` | 同 V6a |

### 3.3 V1 详细（主伤害缩放，最接近「施加点」语义）

```asm
; 候选块 0x004891C6..0x0048926A（含 PercentAtMax / CellSpread / Verses）
0x004891C6  DB 44 24 0C          fild dword [esp+0xC]      ; 伤害（int）
0x004891CA  D9 54 24 08          fst  dword [esp+0x8]
0x004891CE  D8 8F 2C 01 00 00    fmul dword [edi+0x12C]    ; × Warhead.PercentAtMax
0x004891D4  D9 5C 24 0C          fstp dword [esp+0xC]
0x004891D8  D9 87 24 01 00 00    fld  dword [edi+0x124]    ; Warhead.CellSpread
   …（距离插值 / 截断）…
0x00489227  33 C9                xor  ecx, ecx
0x00489229  8B 54 24 18          mov  edx, [esp+0x18]      ; ★ armor 参数
0x0048922D  85 F6                test esi, esi
0x0048922F  0F 9E C1             setle cl
0x00489232  49                   dec  ecx
0x00489233  23 CE                and  ecx, esi
0x00489235  89 4C 24 1C          mov  [esp+0x1C], ecx
0x00489239  DB 44 24 1C          fild dword [esp+0x1C]     ; 缩放后伤害
0x0048923D  DC 8C D7 A0 00 00 00 fmul qword [edi+edx*8+0xA0] ; ★★ Verses[armor]
0x00489244  E8 B7 CC 33 00       call 0x7C5F00             ; double→int
0x00489249  8B 0D E0 71 88 00    mov  ecx, [0x8871E0]
0x0048924F  8B 89 C8 16 00 00    mov  ecx, [ecx+0x16C8]    ; 上限
0x00489255  3B C1                cmp  eax, ecx
0x00489257  7C 0C                jl   …
0x00489260  C2 08 00             ret  8                    ; stdcall，2 实参
```

- `edi` = `WarheadTypeClass*`；`edx` = `ArmorType`（来自 `[esp+0x18]`）
- 该块同时消费 `PercentAtMax(+0x12C)` 与 `CellSpread(+0x124)`，是**距离衰减 + 护甲乘数**的合成缩放
- **属主函数**：`0x4891C6` 前无 `E8/E9` 直引（疑似冷分割块/内联片段或经寄存器间接调用）；
  函数入口名 [待实测]。指令本身 **[实证]**。

### 3.4 V2/V4 有效性检查（`Verses[armor] != 0`）

```asm
0x006F36F2  8B 88 9C 00 00 00    mov ecx, [eax+0x9C]       ; Type->Armor
0x006F36F8  8B 82 AC 00 00 00    mov eax, [edx+0xAC]       ; Warhead*
0x006F36FE  DD 84 C8 A0 00 00 00 fld qword [eax+ecx*8+0xA0]
0x006F3705  DC 1D 00 28 7E 00    fcomp qword [0x7E2800]    ; double 0.0
0x006F370D  F6 C4 40             test ah, 0x40
0x006F3710  0F 85 …              jnz  fail                 ; ==0 ⇒ 不可作用
```

语义：**「该 warhead 对该护甲是否有效」= `Verses[armor] != 0`**。
V4（`0x6FCB6A`）同型，且紧随其后读 `Warhead+0x16E`（BombDisarm）/ `+0x157`（Radiation）等 bool，属武器命中判定链。

### 3.5 V3/V5 阈值检查

| ID | 比较常数 | 值 | 指令 |
|---|---|---|---|
| V3 | `0x7F4E38` | float `0.02` | `fcomp dword [0x7F4E38]` |
| V5 | `0x7F4E34` | float `0.01` | `fcomp dword [0x7F4E34]` |

`Verses[armor] > 0.01 / 0.02` 的阈值门（AI 威胁评估 / 自动还击，具体属主 [待实测]）。

### 3.6 V6 伤害/威胁加权（含敌我符号）

```asm
0x0070CEA8  8B 8B 9C 00 00 00    mov ecx, [ebx+0x9C]       ; Armor
0x0070CEAE  DD 44 24 18          fld qword [esp+0x18]      ; 加权底数
0x0070CEB2  DC 8C C8 A0 00 00 00 fmul qword [eax+ecx*8+0xA0] ; ★ Verses[armor]
0x0070CEB9  D9 E0                fchs                      ; 取负（敌我方向）
0x0070CECE  DD 5C 24 10          fstp qword [esp+0x10]
```

后续 `fmul [eax+0x2C0]`（`TechnoType+0x2C0`）+ `fadd` —— 属威胁/伤害估值函数（`0x70CE??` 段），非 `ReceiveDamage` 主路径。

### 3.7 与 ReceiveDamage / DamageArea 的关系

| 函数 | VA | 与 Verses 关系 |
|---|---|---|
| `TechnoClass::ReceiveDamage` | `0x00701900` | **本体无 Verses 访存**（R6-E3 维持：`0x701939` 是火力归一化） |
| `DamageArea` | `0x00489280` | **本体无 Verses 访存**；其前一独立块 `0x4891C6`（V1）是伤害缩放 |
| `Detonate` | `0x004690B0` | **本体无 Verses 访存**（只读 `Warhead.CellSpread +0x124`） |

> **形参链回溯结论**：Verses 乘算**不在** `ReceiveDamage` / `DamageArea` 函数体内，
> 而在 (a) 紧邻 `DamageArea` 的伤害缩放块 V1，(b) 武器有效性判定链 V2–V5，(c) 威胁估值 V6。
> 「在 ReceiveDamage 归一化段算 Verses」的旧认知 **[实证] 不成立**。

---

## 4. WarheadTypeClass +0x00 … +0x130 布局

### 4.1 基类 AbstractClass（ctor `0x410170`）`[实证]`

| 偏移 | 宽度 | 内容 | 锚点 |
|---|---|---|---|
| `+0x00..+0x0C` | 16 | 4× vtable 指针 | ctor `C7 00/04/08/0C` |
| `+0x10` | 4 | `= 0xFFFFFFFF`（索引槽） | `C7 40 10 FF FF FF FF` |
| `+0x14` | 1 | flags（低 3 bit 清零） | `80 E1 F8` / `88 48 14` |
| `+0x18` | 4 | `= 0` | `89 48 18` |
| `+0x1C` | 4 | `= 0` | `89 48 1C` |
| `+0x20` | 1 | `= 0` | `88 48 20` |
| `+0x21..+0x23` | 3 | padding / 未实测 | — |

### 4.2 基类 AbstractTypeClass（ctor `0x410800` + YRpp 对照）`[实证]`

| 偏移 | 宽度 | 内容 | 锚点 |
|---|---|---|---|
| `+0x24` | `0x18` | `char ID[]` | `lea ebx,[ebp+0x24]` |
| `+0x3C` | 1 | `zero_3C` | YRpp |
| `+0x3D` | `0x20` | `char UINameLabel[]` | `mov byte [ebp+0x3D],0` |
| `+0x5D..+0x5F` | 3 | padding | — |
| `+0x60` | 4 | `const wchar_t* UIName` | `mov [ebp+0x60], 0x887734` |
| `+0x64` | `0x31` | `char Name[]` | `lea edi,[ebp+0x64]` + `rep movsd` |
| `+0x95..+0x97` | 3 | padding（对齐 8） | — |

### 4.3 WarheadTypeClass 自有字段 `[实证]`（LoadFromINI 紧窗口关联）

| 偏移 | 类型 | 字段 | 默认 | 锚点（store） |
|---|---|---|---|---|
| **`+0x98`** | **double** | **`Deform`** | 0.0 | `0x75D792 fstp [esi+0x98]` |
| **`+0xA0`** | **double[11]** | **`Verses[0..10]`** | 1.0 | `0x75DE06 lea ebx,[esi+0xA0]` |
| `+0xF8` | double | `ProneDamage` | 1.0 | `0x75D9A4 fstp [esi+0xF8]` |
| `+0x100` | int | `DeformThreshhold` | 0 | `0x75D7B2 mov [esi+0x100],eax` |
| `+0x104` | TypeList | `AnimList` | empty | ctor `lea esi,[ebp+0x104]` |
| `+0x120` | int | `InfDeath` | 0 | `0x75D771 mov [esi+0x120],eax` |
| `+0x124` | float | `CellSpread` | 0 | `0x75D3EB fstp [esi+0x124]` |
| `+0x128` | float | `CellInset` | 0 | `0x75D40A fstp [esi+0x128]` |
| `+0x12C` | float | `PercentAtMax` | 1.0f | `0x75D429 fstp [esi+0x12C]` |
| `+0x130` | bool | `CausesDelayKill` | 0 | `0x75D443 mov [esi+0x130],al` |
| `+0x134` | int | `DelayKillFrames` | 5 | ctor `mov [ebp+0x134],5` |
| `+0x138` | float | `DelayKillAtMax` | 1.0f | `0x75D47C fstp [esi+0x138]` |
| `+0x13C` | float | `CombatLightSize` | 1.0f | `0x75D49B fstp [esi+0x13C]` |
| `+0x140` | int | （AnimList 附属/索引） | 0 | ctor |
| `+0x144` | bool | `Conventional` | 0 | `0x75D4EE mov [esi+0x144],al` |
| `+0x145` | bool | `WallAbsoluteDestroyer` | 0 | `0x75D522` |
| `+0x146` | bool | `PenetratesBunker` | 0 | `0x75D53C` |
| `+0x147` | bool | `Wood` | 0 | `0x75D556` |
| `+0x148..0x149` | bool×2 | （Wall / unknown） | 0 | ctor |
| `+0x14A` | bool | `Sparky` | 0 | `0x75D58A` |
| `+0x14B` | bool | `Sonic` | 0 | `0x75D5A4` |
| `+0x14C` | bool | `DirectRocker` | 0 | `0x75D5D8` |
| `+0x14D` | bool | `Conventional`（重复键，见注） | 0 | `0x75D4EE` |
| `+0x14E` | bool | `Rocker` | 0 | `0x75D5BE` |
| `+0x14F` | bool | （bool 群） | 0 | ctor |
| `+0x150` | bool | `Bright` | 0 | `0x75D60C` |
| `+0x151` | bool | `CLDisableRed` | 0 | `0x75D626` |
| `+0x152` | bool | `CLDisableGreen` | 0 | `0x75D640` |
| `+0x153` | bool | `CLDisableBlue` | 0 | `0x75D65A` |
| `+0x154` | bool | `EMEffect` | 0 | `0x75D7D5` |
| `+0x155` | bool | `MindControl` | 0 | `0x75D7E0` |
| `+0x156` | bool | `Poison` | 0 | `0x75D800` |
| `+0x157` | bool | （Radiation 邻接，见 `0x6FCBAD`） | 0 | ctor |
| `+0x158` | bool | `ElectricAssault` | 0 | `0x75D82E` |
| `+0x159` | bool | `IvanBomb` | 0 | `0x75D84E` |
| `+0x15A` | bool | `Temporal` | 0 | `0x75D871` |
| `+0x15B` | bool | `IsLocomotor` | 0 | `0x75D87C` |
| `+0x15C` | GUID(16) | `Locomotor` | `0x7E9A90` | ctor 16B 拷贝 |
| `+0x16C..0x16E` | bool×3 | `Psychedelic/BombDisarm/…` | 0/1 | `0x75D8FB` / `0x75D91B` |
| `+0x170` | int | `Paralyzes` | 0 | `0x75D93E` |
| `+0x174..0x17B` | bool×8 | `Culling..Veinhole` | 0 | `0x75D949`… |
| `+0x17C` | int | `ShakeXlo` | 0 | `0x75D940` |
| `+0x180` | int | `ShakeXhi` | 0 | `0x75D963` |
| `+0x184` | int | `ShakeYlo` | 0 | `0x75D96E` |
| `+0x188` | int | `ShakeYhi` | 0 | `0x75D98E` |
| `+0x18C` | TypeList | `DebrisTypes` | — | ctor |
| `+0x1A8` | TypeList | `DebrisMaximums` | — | ctor |
| `+0x1C4` | int | `MaxDebris` | 0 | ctor |
| `+0x1C8` | int | `MinDebris` | 0 | ctor |

> **Size() = `0x1D0`**（v[12] = `0x0075E4F0: B8 D0 01 00 00 C3`）`[实证]`
>
> 注：`+0x144`/`+0x14D` 的 bool 群命名与 YRpp 顺序存在 1–2 字节错位可能（`Conventional` 键在
> 紧窗口启发式下被关联到 `+0x14D`，而 `0x144` 也被命中）——**bool 精确名/偏移对**
> 在 `+0x144..0x15B` 区间 [待实测]（不影响 Deform/Verses/CellSpread 三个 P0/P1 主结论）。

---

## 5. 勘误建议（E-8 升级；本节为建议，未改源文档）

### 5.1 E-8 升级为定谳

| 项 | 原文 | 订正 | 证据 |
|---|---|---|---|
| E-8 | `Deform \| 0xA8` | **`Deform \| 0x98`** | `0x75D792 fstp [esi+0x98]` |
| E-8 附注 | 「与 Verses[1] 重叠」 | 「`+0xA8` = `Verses[1]`；Deform 独占 `+0x98`」 | ctor 清零 + LoadFromINI |

**建议补丁块**（供 Lead 合并，本代理不写 `errata_patches/**`）：

```text
【勘误 2026-09-30 · E-8 定谳】原文「Deform | 0xA8」错误。实证：
`Deform` = `WarheadTypeClass+0x98`（double，`+0x98..+0x9F`），
锚点 `0x75D792 = DD 9E 98 00 00 00`（`fstp qword [esi+0x98]`，LoadFromINI）。
`+0xA8` 实为 `Verses[1]`。ctor `0x75CED8/0x75CEDE` 将 `+0x98/+0x9C` 清零印证。
「不得按 +0xA8 读写 Deform」禁令解除，改按 `+0x98` 读写。
权威：`docs/re/warhead_abi_verses_deform_deep_dive.md` §1。
```

### 5.2 Verses 施加点补记

`ARCHITECTURE_ATLAS.md` §16.3-C 现记「[待定位]」。本任务已定位 8 处（§3），
建议升为 `[实证]` 并链到本文 §3.2 表。**旧扫描 0 命中的原因**：只扫整数 `mov`
索引，未覆盖 FPU `DC/DD` 前缀的 `fmul/fld qword [reg+idx*8+disp]`。

> 【勘误 2026-09-30 · R-E07 · errata_sync】原文「已定位 8 处」→ 订正为 **9 处**（§3.2 表实列 9 行）。原文保留不删字。

### 5.3 关闭项

- E-8 **可关闭**（Deform 偏移闭环）。
- Verses 施加点 **可从「未定位」改为「已定位 8 处」**；剩余 [待实测] 仅为
  函数属主命名（V1 块、V2–V5 链、V6 段）与 `+0xAC` 宿主类名。

> 【勘误 2026-09-30 · R-E07 · errata_sync】原文「已定位 8 处」→ 订正为 **9 处**。原文保留不删字。

---

## 6. 排除清单与下一步

### 6.1 已排除 `[实证]`

| 假设 | 排除依据 |
|---|---|
| `Deform = +0xA8` | LoadFromINI `fstp [esi+0x98]`；ctor 清 `+0x98/+0x9C` |
| Verses 施加于 `ReceiveDamage 0x701939` | 该段是火力归一化（R6-E3 维持）；本体无 `*8+0xA0` 访存 |
| Verses 施加于 `DamageArea 0x489280` 本体 | 本体只读 `CellSpread+0x124`；乘算在前一独立块 `0x4891C6` |
| 「全 .text 无 Verses 索引」 | 旧扫描未覆盖 FPU 形态；扩面后 8 命中 |

### 6.2 未闭环 / 下一步 `[待实测]`

1. **V1 块属主**：`0x4891C6` 无 `E8/E9` 直引 —— 需在真机下 `bp 0x4891C6` 看调用栈，
   或扫 `FF /2` 间接调用 / 跳转表。
2. **`+0xAC` 宿主类**：`WarheadTypeClass*` 落在何对象（`BulletClass`？`DamageArgs`？）
   —— 可从 `DamageArea` 实参链或 `Detonate` 的 `this` 偏移反查。
3. **`+0x144..0x15B` bool 精确命名**：紧窗口启发式有 1–2B 错位风险，
   需按「push 键 → call Read_Boolean → mov [esi+off],al」逐条钉死。
4. **真机验证**：改 INI `Deform=0` vs `Deform=2`，观察地形变形；改 `Verses[Armor]`
   观察伤害 —— [待实测] 动态确认。

---

## 7. 可复算脚本索引

| 脚本 | 作用 |
|---|---|
| `s01_strings_scan.py` | Deform/Verses 等 INI 键字符串定位 |
| `s02_disasm_loadfromini.py` | LoadFromINI / ctor 全量反汇编 |
| `s03b_robust_scan.py` | 全 .text 扩面扫描（FPU+SSE+索引） |
| `s04_verses_sites.py` | 8 个施加点现场 + 紧窗口字段表 |
| `s05b_helper_start.py` | V1 块边界 / 常数 / 调用引扫描 |
| `claims.txt` | 字节级 claims 汇总 |
| `s02_loadfromini.asm` / `s04_verses_sites.asm` | 反汇编落盘 |

---

## 8. 一句话

> **`Deform = WarheadTypeClass+0x98`（double）已定谳，`+0xA8` 是 `Verses[1]`；
> `Verses[armor]` 乘算不在 `ReceiveDamage`，而是 8 处 FPU 索引访存
> `fmul/fld [warhead+armor*8+0xA0]`（V1 伤害缩放 / V2–V5 有效性 / V6 威胁加权）。
> E-8 可收口；旧「+0xA8 读写 Deform」禁令解除。**

> 【勘误 2026-09-30 · R-E07 · errata_sync】原文「8 处 FPU 索引访存」→ 订正为 **9 处**（V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c）。原文保留不删字。
