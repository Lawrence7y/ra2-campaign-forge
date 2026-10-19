# Warhead Verses / 残差 · 第二轮收口（R-WARHEAD P2）

> [META]
> 任务=R-WARHEAD · 轮次=P2 · 日期 2026-09-30
> 目标：① Verses 读取点全表 + 乘算顺序；② 变形/残差逐条收口；③ 与 ReceiveDamage/DamageArea 交叉；
> ④ 限频/加固/勘误规格
> 二进制：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x400000`
> 证据分级：`[实证]`（字节级已见）/ `[推演]`（结构外推）/ `[待实测]`（未跑）
> 可复算：`out/re_work/re_sprint/R_warhead/`（s01–s04 脚本 + claims*.txt + 反汇编落盘）
> **写作用域**：本文 + `out/re_work/re_sprint/R_warhead/**`；未改任何已有文档/ATLAS/台账

---

## 0. 结论速览

| # | 问题 | 结论 | 等级 |
|---|---|---|---|
| 1 | Verses 读取点数量 | **9 处** FPU 索引访存（前档写「8 处」系计数笔误，清单实为 9 行） | **[实证]** |
> 【W3 勘误 · W3-A6/ISSUE-VERSES-SITES-COUNT】改前：Verses 读取点数量 | **9 处** FPU 索引访存（前档写「8 处；改后：Verses FPU 索引访存共 9 处 (V1/V2a/V2b/V3/V4/V5/V6a/V6b/V6c)；依据：errata_sync_master_table.md:22 (R-E07); warhead_verses_residual_p2.md:18, 58；分级：P1
| 2 | Verses 乘算顺序 | `damage × PercentAtMax → 距离插值 → ×Verses[armor] → double→int`，**Verses 是 int 截断前最后一乘** | **[实证]** |
| 3 | 与 ReceiveDamage 关系 | `0x701900` **本体无 Verses**；经 `0x701D64` 调 `MapClass::GetTotalDamage` 才施加 | **[实证]** |
| 4 | `0x70D4A0` 是什么 | **不是 ReceiveDamage**；是清仇恨引用 helper（扫 `TechnoArray 0xA8EC7C`，比 `Target+0x2B4`） | **[实证]** |
| 5 | Verses 写入/默认值 | LoadFromINI `×0.01` 百分比→倍率；默认串 11×`100%%`；落库 double 1.0 | **[实证]** |
| 6 | Deform 族字段 | `Deform=+0x98`、`DeformThreshhold=+0x100`；**无 Conquer 字段**（`Conquer.CPP` 仅源文件路径） | **[实证]** |
| 7 | 0.71875 交叉 | **与 Verses 百分比算术无关**（雾域常数；Verses 只有 `×0.01`） | **[实证]** |
| 8 | 限频/加固放行 | **可放行**（见 §5 规格）：乘算点已闭环，红线改为「不改 GetTotalDamage 乘序/调用次」 | **[实证]** |

---

## 1. Verses 读取点全表（P0）

### 1.1 ABI 惯用式（修正版，继承 R-03/R-06）

```asm
call  [obj+0x84]                    ; GetType() v[33] → TechnoTypeClass*
mov   ecx, [type+0x9C]              ; Armor 枚举 0..10
mov   eax, [weapon+0xAC]            ; WeaponTypeClass.Warhead → WarheadTypeClass*
fld / fmul  qword [eax + ecx*8 + 0xA0]   ; ★ Verses[armor]，基址 +0xA0
```

- **Armor 源** = `TechnoTypeClass+0x9C`（`ObjectTypeClass.Armor`）`[实证]`
- **Warhead 源** = `WeaponTypeClass+0xAC`（`WarheadTypeClass* Warhead`）`[实证]`
- **基址** = `Warhead+0xA0`（`Verses[0]`）；`+0xB0` = `Verses[2]`，**不是数组起点** `[实证]`

### 1.2 九处站点总表 `[实证]`（全 .text 扩面：`DC/DD` + SIB scale=8 + disp32=0xA0）

| ID | VA | FileOffset | 原始字节 | 指令 | Armor 源寄存器 | 语义簇 |
|---|---|---|---|---|---|---|
| **V1** | `0x0048923D` | `0x08923D` | `DC 8C D7 A0 00 00 00` | `fmul [edi+edx*8+0xA0]` | `edx=[esp+0x18]` | **伤害缩放**（主路径） |
| **V2a** | `0x006F36FE` | `0x2F36FE` | `DD 84 C8 A0 00 00 00` | `fld [eax+ecx*8+0xA0]` | `ecx=[type+0x9C]` | 有效性 `!=0` |
| **V2b** | `0x006F3731` | `0x2F3731` | `DD 84 C2 A0 00 00 00` | `fld [edx+eax*8+0xA0]` | `eax=[type+0x9C]` | 有效性 `!=0`（第二武器） |
| **V3** | `0x006F7D3D` | `0x2F7D3D` | `DD 84 C1 A0 00 00 00` | `fld [ecx+eax*8+0xA0]` | `eax` | 阈值 `>0.02` |
| **V4** | `0x006FCB6A` | `0x2FCB6A` | `DD 84 C7 A0 00 00 00` | `fld [edi+eax*8+0xA0]` | `eax=[type+0x9C]` | 有效性 `!=0`（+BombDisarm 邻接） |
| **V5** | `0x00708AF7` | `0x308AF7` | `DD 84 C1 A0 00 00 00` | `fld [ecx+eax*8+0xA0]` | `eax` | 阈值 `>0.01` |
| **V6a** | `0x0070CEB2` | `0x30CEB2` | `DC 8C C8 A0 00 00 00` | `fmul [eax+ecx*8+0xA0]` | `ecx=[ebx+0x9C]` | 威胁加权（目标==己 → `fchs`） |
| **V6b** | `0x0070CEC7` | `0x30CEC7` | `DC 8C D0 A0 00 00 00` | `fmul [eax+edx*8+0xA0]` | `edx=[ebx+0x9C]` | 威胁加权（目标≠己） |
| **V6c** | `0x0070CF49` | `0x30CF49` | `DC 8C C1 A0 00 00 00` | `fmul [ecx+eax*8+0xA0]` | `eax` | 威胁加权（第三支） |

**计数勘误**：R-03 §0 写「8 处」但 §3.2 表实列 9 行（V1 / V2a / V2b / V3 / V4 / V5 / V6a / V6b / V6c）。本轮独立扫描命中 **9** 条，与表行数一致；「8」为汇总笔误。`[实证]`

**整数形态 `*8+0xA0`：0 命中**（`mov/lea` 侧无 Verses 索引）——印证旧扫描盲区是 FPU `DC/DD` 前缀。`[实证]`

### 1.3 比较常数

| 用途 | VA | 值 | 指令 |
|---|---|---|---|
| `==0` 有效性 | `0x7E2800` | double `0.0` | `fcomp qword [0x7E2800]` |
| 阈值 0.02 | `0x7F4E38` | float `0.02` | `fcomp dword [0x7F4E38]` |
| 阈值 0.01 | `0x7F4E34` | float `0.01` | `fcomp dword [0x7F4E34]` |

`[实证]`（字节复核：`0x7E2800` = 全零 8B；`0x7F4E38`/`0x7F4E34` = 单精度 0.02/0.01）

### 1.4 Armor 枚举 ↔ Verses 下标 `[实证]`

`0x7E5210` 起 11×4B 指针表，解析器 `0x772A50`：

| 下标 | 字符串 | 下标 | 字符串 |
|---|---|---|---|
| 0 | `none` | 6 | `wood` |
| 1 | `flak` | 7 | `steel` |
| 2 | `plate` | 8 | `concrete` |
| 3 | `light` | 9 | `special_1` |
| 4 | `medium` | 10 | `special_2` |
| 5 | `heavy` | | |

---

## 2. 乘算顺序（P0，与百分比算术 / 0.71875 严格切割）

### 2.1 `MapClass::GetTotalDamage @ 0x489180` —— **唯一伤害倍率施加点**

```asm
; ── 正伤害分支（jge 0x4891C6 跳入）──
0x4891C6  fild  [esp+0xC]           ; damage (int)
0x4891CA  fst   [esp+0x8]           ; 保存原始 damage
0x4891CE  fmul  [edi+0x12C]         ; ★ × Warhead.PercentAtMax
0x4891D4  fstp  [esp+0xC]
0x4891D8  fld   [edi+0x124]         ; Warhead.CellSpread
0x4891DE  fmul  [0x7E2224]          ; × float 256.0（格→lepton 量纲）
0x4891E4  call  0x7C5F00            ; double→int
; …距离插值：(orig − scaled) × dist / radius + scaled…
0x489239  fild  [esp+0x1C]          ; 插值后伤害 (int, 已 clamp ≥0)
0x48923D  fmul  [edi+edx*8+0xA0]    ; ★★ × Verses[armor]   ← 最后一乘
0x489244  call  0x7C5F00            ; double→int 截断
; …clamp 到 Rules 上限…
0x489260  ret 8
```

**顺序定谳** `[实证]`：

```
int_damage
  → × PercentAtMax (+0x12C)
  → 距离线性插值（CellSpread +0x124 × 256.0 为半径）
  → clamp ≥ 0
  → × Verses[armor] (+0xA0 + armor×8)     ← Verses 在此
  → double→int 截断
  → clamp 上限
```

### 2.2 与百分比算术的边界（勿混）`[实证]`

| 环节 | 算子 | 常数 | 位置 |
|---|---|---|---|
| **INI 装载** | `fmul qword [0x7E3808]` | double **`0.01`** | `0x75DE31`（仅写入侧） |
| **伤害结算** | `fmul [reg+idx*8+0xA0]` | Verses 已是倍率（1.0=100%） | `0x48923D` 等 9 处 |
| **距离量纲** | `fmul dword [0x7E2224]` | float **`256.0`** | `0x4891DE`（非百分比） |
| **0.71875** | — | 全 exe float 命中 1（`0x803F4E` 非对齐巧合）、double 0 | **雾域/LightConvert，与 Verses 零交集** |

> **交叉勿混声明**：`Verses=100%` → 落库 `1.0` 的 `×0.01` 只发生在 **LoadFromINI**；伤害链上再无百分比换算。
> 0.71875 是迷雾第一段经验增益（`fog_mixing_site_deep_dive.md` 已定谳「未定位为离散乘法」），
> **不得**与 Verses 百分比算术或 `PercentAtMax` 混谈。`[实证]`

---

## 3. 与 ReceiveDamage `0x701900` / `0x70D4A0` / DamageArea `0x489280` 交叉（P0）

### 3.1 三址定性

| 地址 | 真实身份 | 与 Verses 关系 | 等级 |
|---|---|---|---|
| **`0x00701900`** | `TechnoClass::ReceiveDamage`（v[91]） | **本体 0 处 Verses**；`0x701939` 段是火力归一化（`fdivr dmg/(HouseCoeff×Techno+0x158)`），**非 Verses** | **[实证]** |
| **`0x0070D4A0`** | **`ReceiveDamage_Helper`（清仇恨引用）**：`TechnoArray 0xA8EC7C` 逆序遍历，比 `Target+0x2B4` | **与 Verses/伤害倍率无关**（纯指针清零，0 PRNG） | **[实证]** |
| **`0x00489280`** | `DamageArea`（AOE 候选收集） | **本体 0 处 Verses**；只读 `CellSpread+0x124`；经 `v[0x16C]` 调承伤 | **[实证]** |
| **`0x00489180`** | `MapClass::GetTotalDamage` | **★ V1 在此**（`0x48923D`） | **[实证]** |

> **勘误**：`weapons_damage_production.md` 多处把 `0x70D4A0` 写作「ReceiveDamage 内清引用路径 / ReceiveDamage_Helper」并与承伤链并列。
> 实证 `0x70D4A0` **不是** `ReceiveDamage` 的组成部分语义名，而是**独立 helper**（序言 `55 8B E9 56 57 85 ED 75`，
> 含 `0xA8EC7C` + `+0x2B4` 锚点）；任务卡「ReceiveDamage `0x70D4A0`」的说法**应改写为 `TechnoClass::ReceiveDamage @ 0x701900` + `清仇恨 helper @ 0x70D4A0`**。`[实证]`

### 3.2 伤害倍率在链上的哪一步

```
BulletClass::Detonate 0x4690B0
  └─ DamageArea 0x489280                    [无 Verses；收集候选]
       └─ v[0x16C] ReceiveDamage            [0x489AB6: call [edx+0x16C]]
            ├─ 0x701939 火力归一化           [fdivr；HouseType 0x50BD30 × Techno+0x158]
            ├─ …分支/过滤…
            └─ 0x701D64 call GetTotalDamage  [★ Verses 乘算在被调函数内]
                 └─ 0x48923D fmul Verses[armor]
                 └─ 结果写回 [ebx]（伤害槽）
```

`GetTotalDamage(0x489180)` 全部 call 站点 `[实证]`：

| 调用点 | 是否在 ReceiveDamage 内 | 说明 |
|---|---|---|
| `0x005F540F` | 否 | 第三方调用方（近 `0x5F5390` 序言段） |
| `0x006FDD29` | 否 | 近 `FootClass::Fire 0x6FDD50` 邻域 |
| **`0x00701D64`** | **是**（`0x701900..0x702D40`） | **承伤链上唯一入口** |

`DamageArea` / `Detonate` **均不直调** `GetTotalDamage`（0 命中）`[实证]`。

**形参链**（`0x701D4D..0x701D64`）`[实证]`：

```asm
0x701D4D  mov eax,[esi]            ; vtable
0x701D4F  push 0
0x701D53  call [eax+0x88]          ; GetTechnoType? → eax=type
0x701D59  mov ecx,[eax+0x9C]       ; ★ Armor 枚举
0x701D5F  mov edx,ebp              ; pWarhead
0x701D61  push ecx                 ; arg: armor
0x701D62  mov ecx,[ebx]            ; arg: damage（fastcall ecx）
0x701D64  call 0x489180            ; GetTotalDamage(damage, pWarhead, armor, dist)
0x701D69  mov [ebx],eax            ; 回写伤害
```

### 3.3 前档交叉结论复核

| 前档记载 | 本轮判定 |
|---|---|
| R-03「Verses 不在 ReceiveDamage/DamageArea 本体」 | **维持** `[实证]` |
| R-06「V1 属主 = GetTotalDamage」 | **维持并补 call 链** `[实证]` |
| `weapons_damage_production.md` 「Verses 应用点在 0x701939」 | **否定**（R6-E3 + 本轮 P2-C42 空集） |
| 任务卡「ReceiveDamage `0x70D4A0`」 | **地址名错位**，见 §3.1 |

---

## 4. 变形 / 残差逐条收口（P1）

### 4.1 Verses 写入（INI 解析）`[实证]`

| 项 | 值 | 锚点 |
|---|---|---|
| INI 键 | `"Verses"` @ `0x847C38` | imm32 xref |
| 默认值串 | `0x847C40` = **11 项** `100%%,100%%,…,100%%` | 本轮全串复核 `parts=11` |
| 装载循环 | `lea ebx,[esi+0xA0]` / `mov ebp,0xB` / `fstp [ebx]` / `add ebx,8` | `0x75DE06`…`0x75DE52` |
| 百分比换算 | `fmul qword [0x7E3808]` = double **0.01** | `0x75DE31` |
| 落库 | `+0xA0 … +0xF7`（11×double，1.0=100%） | — |
| 函数 | `WarheadTypeClass::LoadFromINI 0x75D3A0`（`esi≡this`） | 序言 `0x75D3B1: 8B F1` |

### 4.2 Deform 族字段 `[实证]`

| 字段 | 偏移 | 类型 | 默认 | INI 键 | 写点 |
|---|---|---|---|---|---|
| `Deform` | **`+0x98`** | double | 0.0 | `"Deform"` @ `0x847D80` | `0x75D792 fstp [esi+0x98]` |
| `DeformThreshhold` | **`+0x100`** | int | 0 | `"DeformThreshhold"` @ `0x847D6C`（**双 h**） | `0x75D7B2 mov [esi+0x100],eax` |
| `ProneDamage` | **`+0xF8`** | double | 1.0 | `"ProneDamage"` @ `0x847CE8` | `0x75D9A4 fstp [esi+0xF8]` |

- **拼写差**：二进制键 = `DeformThreshhold`（Thresh**h**old，双 h）；YRpp `WarheadTypeClass.h:67` = `DeformTreshold`（单 h）。
  按 INI 写键必须用**双 h**，否则静默走默认值。`[实证]`
- **`Conquer` 字段不存在**：`"Conquer"` 作为 INI 键 0 命中；全 exe 大小写不敏感 `conquer` 仅 3 处
  （`D:\ra2mdpost\Conquer.CPP` 源路径 + 2 处邻近杂串）。`[实证]`
  ⇒ 任务中「Deform/Conquer 相关字段」应解读为 **Deform 字段族**（地形变形），与 C&C 源文件名 `Conquer.CPP` 无关。

### 4.3 ProneDamage 消费点（本轮新实证）

`+0xF8` 的 FPU 读点（节选）`[实证]`：

| VA | 归属 | 说明 |
|---|---|---|
| `0x517FDD` | **`InfantryClass::ReceiveDamage 0x517FA0`**（v[91] 覆写） | 步兵俯卧伤害倍率，在子类承伤内 |
| `0x4668D9` 等 12 处 | `BulletClass` 段（`0x466xxx`） | 弹道侧伴生读 |
| `0x75D9A4` | LoadFromINI | 写点（非消费） |

> **补**：R-03 布局表已列 `ProneDamage +0xF8`，但未列消费点；本轮补上「**步兵子类承伤内乘**」这一落点。
> 含义：ProneDamage **不在** `GetTotalDamage`，而在 `InfantryClass::ReceiveDamage` 覆写体内——
> 与 Verses（`GetTotalDamage`）**不同层**，乘序互不覆盖。`[实证]`

### 4.4 残差清单对照（R-03 §6.2 / R-06 §6.2）

| 前档残差 | 本轮状态 | 依据 |
|---|---|---|
| V1 块属主 | **已闭环**（R-06：`GetTotalDamage`）+ 本轮补 3 个 call 点 | P2-C31 / P2b-D1 |
| `+0xAC` 宿主 | **已闭环**（R-06：`WeaponTypeClass`） | 继承 |
| V2–V6 函数属主名 | **部分收口**：V5 入口 `0x7087C0`（自 `0x702A43`＝ReceiveDamage 内调用）；V6 入口 `0x70CD10`（3 处 xref）；V2/V4 仍为内部标签段，入口名 **[待实测]** | P2d-C1 / P2d-D1 |
| HouseClass 字段级 | 未在本任务范围 | — |
| `TechnoClass+0x21C` | 语义收口：**`Owner`（`HouseClass*`）**，被当作 `0x50BD30` 的 `this`（火力系数）`[推演]`（YRpp 字段序 + 调用形参一致；偏移数字级仍以二进制为准） | P2b-E1 / ATLAS §16.3 |
| 真机动态确认 | 仍 **[待实测]**（静态已全闭环） | — |
| `+0x144..0x15B` bool 命名 | 仍 **[待实测]**（不影响本 P0） | R-03 维持 |

---

## 5. 可落地：限频 / 加固 / 勘误规格

### 5.1 勘误块（供 Lead 合并；本代理不写 `errata_patches/**`）

```text
【勘误 2026-09-30 · E-RW-P2 · R-WARHEAD】
1) weapons_damage_production.md L19/128/142：「Verses[11] @ Warhead+0xB0」→ 起于 +0xA0（+0xB0=Verses[2]）。
   （与 R6-E2 同文，此处再钉一次。）
2) L207-208/215/473：「Verses 应用点在 ReceiveDamage 归一化段 0x701939」→ 不成立。
   实证：Verses 乘算在 MapClass::GetTotalDamage 0x48923D（fmul [warhead+armor*8+0xA0]），
   由 ReceiveDamage 0x701D64 调用；0x701939 段为火力归一化（fdivr / HouseType 0x50BD30 × Techno+0x158）。
3) 「0x70D4A0 = ReceiveDamage 清引用路径」→ 0x70D4A0 为独立 helper（清仇恨/Target+0x2B4），
   不是 ReceiveDamage（0x701900）本体；任务卡「ReceiveDamage 0x70D4A0」写法应更正。
4) R-03 §0「8 处 Verses 施加点」→ 应为 9 处（表 §3.2 已列 9 行：V1,V2a,V2b,V3,V4,V5,V6a,V6b,V6c）。
5) DeformThreshhold INI 键为双 h（"DeformThreshhold" @ 0x847D6C）；YRpp 单 h 为拼写差。
权威：docs/re/warhead_verses_residual_p2.md §1–§4。
```

### 5.2 限频 / 加固放行规格（ATLAS §16.3-D 禁令解除条件）

ATLAS 原文：「在未闭环前，任何『按 Verses 加固/限频』的优化不得放行。」

**现前置已满足**（乘算点、Armor 源、Warhead 源、乘序、9 站点全闭环）⇒ **放行，约束如下**：

| # | 规格 | 级别 |
|---|---|---|
| G1 | **可**对 `Verses[11]` 做只读缓存/预取（ATLAS 已豁免 Verses 本身） | 允许 |
| G2 | **禁止**改动 `GetTotalDamage` 乘序：必须保持 `×PercentAtMax → 距离插值 → ×Verses → int` | 红线 |
| G3 | **禁止**改变 `GetTotalDamage` 的调用次数与调用点集合（`0x5F540F / 0x6FDD29 / 0x701D64`） | 红线 |
| G4 | **禁止**把 Verses 乘算上提到 `DamageArea` 或改挂 `ReceiveDamage 0x701900` 内（会绕过 clamp/截断语义） | 红线 |
| G5 | 限频（伤害裁剪/频次帽）必须实现在 **`GetTotalDamage` 返回后**或调用方回写处（`0x701D69 mov [ebx],eax`），且不触碰 RNG | 允许 |
| G6 | `Warhead` 运行期可变字段仍不得缓存（除 Verses）；`Deform/DeformThreshhold/ProneDamage` 同列可变 | 维持 ATLAS |
| G7 | Armor 索引必须经 `TechnoType+0x9C` 现场读取（enum 0..10），不得硬编码表 | 允许 |

> **纯收口声明**：本任务未发现需要新增补丁的缺陷；上表为「放行边界」而非修复清单。
> 若后续要做 Verses 相关加固/限频，按 G1–G7 落地即可，无需再等动态确认（动态确认仍建议做，但不阻塞放行）。

---

## 6. 排除清单

| 假设 | 排除依据 | 等级 |
|---|---|---|
| Verses 施加于 `ReceiveDamage 0x701939` | 该段 `fild/fmul/fdivr` 无 `*8+0xA0`；P2-C42 空集 | `[实证]` |
| Verses 施加于 `DamageArea 0x489280` 本体 | P2-C43 空集；本体只读 CellSpread | `[实证]` |
| `0x70D4A0` 是 ReceiveDamage | 独立序言 + `TechnoArray/Target` 锚点；无伤害运算 | `[实证]` |
| Verses 基址 `+0xB0` | `lea ebx,[esi+0xA0]`；`+0xB0`=Verses[2] | `[实证]` |
| 0.71875 参与 Verses 百分比算术 | 全 exe float 1 处非对齐巧合、double 0；Verses 侧常数只有 0.01 | `[实证]` |
| 存在 `Conquer` 弹头字段 | INI 键 0 命中；仅 `Conquer.CPP` 源路径 | `[实证]` |
| 乘序为「先 Verses 后 PercentAtMax」 | `0x4891CE` 在 `0x48923D` 之前 | `[实证]` |
| Verses 用整数 `mov` 索引 | `*8+0xA0` 整数形态 0 命中 | `[实证]` |

---

## 7. 可复算脚本索引（`out/re_work/re_sprint/R_warhead/`）

| 产物 | 作用 |
|---|---|
| `s01_verses_full_table.py` | 9 站点全表 + 写入点 + 默认串 + 0.71875 边界 |
| `s02_order_chain.py` | 乘算顺序 + call 链 + 0x70D4A0 身份 + Deform 残差 |
| `s03_owners_residue.py` | V2–V6 属主探针 + Armor 表 + ProneDamage 消费 |
| `s04_v2owner_errata.py` | call xref + Infantry ProneDamage + 勘误事实 |
| `claims.txt` / `claims_p2b.txt` / `claims_p2c.txt` / `claims_p2d.txt` | 字节级 claims |
| `s03_verses_read_table.asm` 等 `s*.asm` | 反汇编落盘 |

---

## 8. 一句话

> **Verses 读取点定谳为 9 处 FPU 索引访存（基址 +0xA0，Armor=TechnoType+0x9C，Warhead=WeaponTypeClass+0xAC）；
> 乘算顺序 = damage×PercentAtMax → 距离插值 → ×Verses[armor] → int 截断，且 Verses 不在
> ReceiveDamage(0x701900)/DamageArea(0x489280) 本体，而在 GetTotalDamage(0x48923D)，
> 由 ReceiveDamage 0x701D64 调用；0x70D4A0 是清仇恨 helper 而非 ReceiveDamage。
> Deform=+0x98 / DeformThreshhold=+0x100（INI 双 h）/ 无 Conquer 字段；0.71875 与百分比算术零交集。
> 限频/加固可按 §5.2 G1–G7 放行。**
