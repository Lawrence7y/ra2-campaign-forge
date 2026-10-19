# Warhead ABI 残余与扩展偏移实证（R-06）

> [META]
> 任务=R-06 · 负责方=R 轨逆向代理 · 日期 2026-09-30
> 目标：收残余（+0xAC 宿主、V1 属主函数）+ 扩展 ABI 偏移独立实证
> 二进制：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x400000`
> 证据分级：`[实证]`（字节级已见）/ `[推演]`（结构外推）/ `[待实测]`（未跑）
> 可复算：`out/re_work/re_sprint/warhead_abi2/`（脚本 + claims + 反汇编落盘）
> **写作用域**：本文 + `out/re_work/re_sprint/warhead_abi2/**`；未改任何已有文档

---

## 0. 结论速览

| # | 问题 | 结论 | 等级 |
|---|---|---|---|
| 1 | `obj+0xAC` 宿主类 | **`WeaponTypeClass`**（`WarheadTypeClass* Warhead` 字段） | **[实证]** |
| 2 | V1 块 `0x4891C6` 属主 | **`MapClass::GetTotalDamage` @ `0x489180`**（非独立函数；为正伤害分支入口） | **[实证]** |
| 3 | `ObjectTypeClass/TechnoTypeClass+0x9C` | **`Armor` 枚举**（0..10，11 档），装载点 `0x5F94CD` | **[实证]** |
| 4 | BulletClass 关键偏移 | 6 字段与 YRpp **全部一致**（Construct/ctor/Detonate 三重锚点） | **[实证]** |
| 5 | WeaponTypeClass 关键偏移 | 6 字段与 YRpp **全部一致**（ctor + LoadFromINI 双锚点） | **[实证]** |
| 6 | TechnoClass 关键偏移 | `ArmorMultiplier +0x158` / `FirepowerMultiplier +0x160` 与 YRpp 一致 | **[实证]** |
| 7 | HouseClass::Array | YRpp 记 `0xA80228`，二进制内部布局偏移差 **+4/+0x10** | **[冲突-轻微]** |

---

## 1. [P0] `+0xAC` 宿主类 = `WeaponTypeClass`

### 1.1 排除 `BulletClass`（关键反证）

`BulletClass::Construct` @ `0x004664C0`（YRpp 签名：`Construct(pType, pTarget, pOwner, damage, pWarhead, speed, bright)`）：

```asm
0x004664C4  8B 44 24 04          mov eax, [esp+4]        ; arg1 = pType
0x004664FB  89 81 AC 00 00 00    mov [ecx+0xAC], eax     ; ★ +0xAC ← BulletTypeClass* Type
0x00466501  89 B1 B0 00 00 00    mov [ecx+0xB0], esi     ; +0xB0 ← pOwner
0x004664D8  8B 54 24 14          mov edx, [esp+0x14]     ; arg5 = pWarhead
0x004664DC  89 91 28 01 00 00    mov [ecx+0x128], edx    ; +0x128 ← WarheadTypeClass* WH
```

⇒ **`BulletClass+0xAC = Type`（BulletTypeClass*），`+0x128 = WH`**。Verses 惯用式中 `+0xAC` 被当 `WarheadTypeClass*` 解释，**不可能是 BulletClass**。`[实证]`

`BulletClass::Detonate` @ `0x4690B0` 再印证：`mov eax,[esi+0x128]` 后读 `Warhead+0x17C/0x180`（Shake 字段）。`[实证]`

### 1.2 锁定 `WeaponTypeClass`（正证）

**YRpp `WeaponTypeClass.h`** 继承 `AbstractTypeClass`（自有字段从 `+0x98` 起）：

| 偏移 | 字段 | 宽度 |
|---|---|---|
| `+0x98` | `AmbientDamage` | int |
| `+0x9C` | `Burst` | int |
| `+0xA0` | `Projectile` | ptr |
| `+0xA4` | `Damage` | int |
| `+0xA8` | `Speed` | int |
| **`+0xAC`** | **`Warhead`** | **`WarheadTypeClass*`** |

**构造器** `WeaponTypeClass::ctor` @ `0x00771C70`：`[实证]`

```asm
0x00771C87  89 9E 98 00 00 00    mov [esi+0x98], ebx     ; AmbientDamage = 0
0x00771C8D  C7 86 9C 00 00 00 01 00 00 00
                              mov [esi+0x9C], 1       ; Burst = 1
0x00771C97  89 9E A0 00 00 00    mov [esi+0xA0], ebx     ; Projectile = NULL
0x00771C9D  89 9E A4 00 00 00    mov [esi+0xA4], ebx     ; Damage = 0
0x00771CA3  89 9E A8 00 00 00    mov [esi+0xA8], ebx     ; Speed = 0
0x00771CA9  89 9E AC 00 00 00    mov [esi+0xAC], ebx     ; ★ Warhead = NULL
```

**装载器** `WeaponTypeClass::LoadFromINI` 段 @ `0x00772957`：`[实证]`

```asm
0x00772957  68 B4 83 81 00       push 0x8183B4           ; "Warhead"
0x0077295F  E8 AC 60 DB FF       call 0x528A10           ; CCINIClass::Read_...
0x0077296C  E8 3F BA FE FF       call 0x75E3B0           ; → WarheadTypeClass* 解析
0x00772975  8B AE A0 00 00 00    mov ebp, [esi+0xA0]     ; 顺带读 Projectile（+0xA0 印证）
0x00772992  89 86 AC 00 00 00    mov [esi+0xAC], eax     ; ★★ Warhead ← 解析结果
```

### 1.3 Verses ABI 惯用式修正

```asm
; 修正后的完整惯用式（R-03 §3.1 升级）:
call  [obj+0x84]                          ; GetType() → TechnoTypeClass*
mov   ecx, [type+0x9C]                    ; Armor 枚举 0..10
mov   eax, [weapon+0xAC]                  ; ★ weapon = WeaponTypeClass*，+0xAC = Warhead
fld / fmul  qword [eax + ecx*8 + 0xA0]    ; Verses[armor]
```

> **R-03 遗留「`obj2+0xAC` 宿主类 [待实测]」→ 闭环为 `WeaponTypeClass`。**`[实证]`

---

## 2. [P0] V1 块 `0x4891C6` 属主 = `MapClass::GetTotalDamage`

### 2.1 函数边界重建

**`MapClass::GetTotalDamage`** = `0x00489180`（YRpp `MapClass.h:279`：`__fastcall (int damage, const WarheadTypeClass* pWarhead, Armor armor, int distance)`）。`[实证-头文件锚点 + 字节级]`

```asm
; 序言 0x489180
0x00489180  83 EC 0C             sub  esp, 0xC
0x00489183  56                   push esi
0x00489184  8B F1                mov  esi, ecx          ; esi = damage (arg1)
0x00489186  57                   push edi
0x00489187  8B FA                mov  edi, edx          ; edi = pWarhead (arg2)
; 栈布局：armor=[esp+0x18], distance=[esp+0x1C]（push×2 + sub 0xC 后）

; 负伤害短路 0x4891AB..0x4891C3（ret 8）
0x004891AD  7D 17                jge  0x4891C6          ; ★ damage≥0 → 正伤害路径

; ═══ 正伤害路径 = V1 块 ═══
0x004891C6  DB 44 24 0C          fild [esp+0xC]         ; damage
   …（PercentAtMax / CellSpread 距离插值）…
0x00489229  8B 54 24 18          mov  edx, [esp+0x18]   ; armor
0x0048923D  DC 8C D7 A0 00 00 00 fmul [edi+edx*8+0xA0]  ; ★ V1: Verses[armor]
0x00489244  E8 B7 CC 33 00       call 0x7C5F00          ; double→int
0x00489260  C2 08 00             ret  8                 ; 出口2

; 出口 0x489263..0x48926A（零伤害 / clamp 出口，ret 8）
0x0048926A  C2 08 00             ret  8
```

- **函数边界**：`0x489180` … `0x48926A`（三个出口，全部 `ret 8` = 清理 armor+distance 两个栈参）
- **V1 不是独立函数**，是 `GetTotalDamage` 内部**正伤害分支**的落点（`jge 0x4891C6` 跳入）
- 解释了 R-03「无 E8/E9 直引」——`0x4891C6` 是**函数内标签**，不是入口

### 2.2 xref 清单

| 目标 | 类型 | 位置 | 说明 |
|---|---|---|---|
| `0x489180` | `call` | `0x005F540F` | 调用方 1 |
| `0x489180` | `call` | `0x006FDD29` | 调用方 2 |
| `0x489180` | `call` | `0x00701D64` | 调用方 3（ReceiveDamage 邻域） |
| `0x489180` | `jmp` | — | 0 命中 |
| `0x489180` | imm32/vtable | — | 0 命中（非虚函数） |
| `0x4891C6` | 任何 | — | **0 命中**（内部标签）`[实证]` |

---

## 3. [P1] `+0x9C` = `Armor` 枚举确认

### 3.1 字段归属

`Armor` 声明于 **`ObjectTypeClass`**（YRpp `ObjectTypeClass.h:67`），`TechnoTypeClass` 继承之。偏移链：`AbstractTypeClass` 止于 `+0x98` → `RadialColor(3B) + unused(1B)` → **`Armor @ +0x9C`**。`[实证]`

### 3.2 装载点

```asm
; ObjectTypeClass::LoadFromINI 段（ebx = this）
0x005F94B3  8B 93 9C 00 00 00    mov edx, [ebx+0x9C]    ; 默认值
0x005F94BC  68 D4 D9 81 00       push 0x81D9D4          ; "Armor"
0x005F94C8  E8 23 BF E7 FF       call 0x4753F0          ; CCINIClass::Read_ArmorType
0x005F94CD  89 83 9C 00 00 00    mov [ebx+0x9C], eax    ; ★ Armor ← 枚举值
```

### 3.3 枚举范围 0..10

`Armor` 解析器 @ `0x772A50` 遍历字符串表 `0x7E5210` … `0x7E523C`（**11 × 4B = 0x2C**），命中即返回索引。`[实证]`

| 值 | YRpp `Armor` 枚举 | 值 | YRpp |
|---|---|---|---|
| 0 | `None` | 6 | `Wood` |
| 1 | `Flak` | 7 | `Steel` |
| 2 | `Plate` | 8 | `Concrete` |
| 3 | `Light` | 9 | `Special_1` |
| 4 | `Medium` | 10 | `Special_2` |
| 5 | `Heavy` | | |

与 `Verses[11]` 数组长度 **一一对应**。`[实证]`

---

## 4. [P1] YRpp 对照表（扩展类 ABI 偏移独立实证）

### 4.1 BulletClass

| 偏移 | YRpp 字段 | 二进制锚点 | 判定 |
|---|---|---|---|
| `+0xAC` | `Type` (BulletTypeClass*) | Construct `mov [ecx+0xAC],eax`←pType；ctor 清零 | **一致** |
| `+0xB0` | `Owner` (TechnoClass*) | Construct `mov [ecx+0xB0],esi`←pOwner；ctor 清零 | **一致** |
| `+0xB4` | `unknown_B4` (bool) | ctor `mov [esi+0xB4],bl` | **一致** |
| `+0xB8` | `BulletData Data` | ctor `lea ecx,[esi+0xB8]; call 0x4E1100`（子构造） | **一致** |
| `+0xE0` | `Bright` (bool) | Construct `mov [ecx+0xE0],dl`←bright | **一致** |
| `+0x10C` | `Target` | Construct `mov [ecx+0x10C],edx`←pTarget | **一致** |
| `+0x110` | `Speed` | Construct `mov [ecx+0x110],edx`←speed | **一致** |
| `+0x128` | `WH` (WarheadTypeClass*) | Construct `mov [ecx+0x128],edx`←pWarhead；Detonate 读 | **一致** |

### 4.2 WeaponTypeClass（+0xAC 直接相关，附带实证）

| 偏移 | YRpp 字段 | 二进制锚点 | 判定 |
|---|---|---|---|
| `+0x98` | `AmbientDamage` | ctor 清零 | **一致** |
| `+0x9C` | `Burst` | ctor 置 1 | **一致** |
| `+0xA0` | `Projectile` | ctor 清零；LoadFromINI `mov ebp,[esi+0xA0]` | **一致** |
| `+0xA4` | `Damage` | ctor 清零 | **一致** |
| `+0xA8` | `Speed` | ctor 清零 | **一致** |
| **`+0xAC`** | **`Warhead`** | ctor 清零；LoadFromINI `mov [esi+0xAC],eax` | **一致** |

### 4.3 TechnoClass

| 偏移 | YRpp 字段 | 二进制锚点 | 判定 |
|---|---|---|---|
| `+0x150` | `Flashing` / 附属 | ctor `lea ecx,[esi+0x150]; call 0x74FF30` | **一致** |
| `+0x158` | `ArmorMultiplier` (double) | ctor `mov [esi+0x15C],0x3FF00000`→1.0；ReceiveDamage `fmul [esi+0x158]` | **一致** |
| `+0x160` | `FirepowerMultiplier` (double) | ctor `mov [esi+0x164],0x3FF00000`→1.0 | **一致** |
| `+0x21C` | （指针，YRpp 未命名） | ReceiveDamage `mov ecx,[esi+0x21C]` | **未验**（YRpp 无对应名） |

### 4.4 HouseClass

| 偏移 | YRpp 字段 | 二进制锚点 | 判定 |
|---|---|---|---|
| `Array` 基址 | `0xA80228` | FindByIndex：`[0xA8022C]`=Items、`[0xA80238]`=Count | **冲突-轻微** |
| — | — | YRpp `constant_ptr` 记 `0xA80228`；二进制实际用 `+4`/`+0x10` 访问内部字段 | DynamicVectorClass 布局偏移差 |

> **HouseClass 偏移 [待实测]**：本次未做 HouseClass ctor 字段级钉死（时间预算内优先 P0）。
> FindByIndex 只提供了 Array 间接锚点，不足以产出字段对照表。

---

## 5. 浮点扫描覆盖声明

按任务要求覆盖 `fmul / fld / fstp / fcomp / fild / fist / movsd / mulsd`：
- V1 `fmul qword [edi+edx*8+0xA0]`（`DC 8C D7 A0 00 00 00`）— fmul `[实证]`
- V2a/V2b/V3/V4/V5 `fld qword [reg+idx*8+0xA0]`（`DD 84 xx A0 00 00 00`）— fld `[实证]`
- V6a/V6b/V6c `fmul qword [reg+idx*8+0xA0]`（`DC 8C xx A0 00 00 00`）— fmul `[实证]`
- 比较侧：`fcomp qword [0x7E2800]`（=0.0）、`fcomp dword [0x7F4E38]`（=0.02）、`fcomp dword [0x7F4E34]`（=0.01）`[实证]`
- 本次新增覆盖：`fild`（GetTotalDamage 伤害入口）、`fstp`（落库）、`fnstsw+test ah`（比较后判定）

---

## 6. 排除清单与残余

### 6.1 已排除 `[实证]`

| 假设 | 排除依据 |
|---|---|
| `+0xAC` 宿主 = BulletClass | Construct 存 pType 到 +0xAC，WH 在 +0x128 |
| `+0xAC` 宿主 = WaveClass / 独立上下文 | WeaponTypeClass ctor + LoadFromINI 双锚点直接命中 |
| V1 是独立函数 / 冷分割块 | `0x4891C6` 是 `GetTotalDamage` 内 `jge` 跳转目标 |
| V1 经 vtable/间接调用 | 0 imm32/vtable 引用；纯内部标签 |
| `TechnoTypeClass+0x9C` 是独立字段 | 实为 `ObjectTypeClass.Armor`（继承） |

### 6.2 残余 `[待实测]`

1. **HouseClass 字段级对照**：需 ctor `0x????` 或 LoadFromINI 字段钉死（本次时间预算未完成）。
2. **TechnoClass `+0x21C`**：ReceiveDamage 读该指针，YRpp 无命名——待定类型。
3. **V2–V6 属主函数名**：Verses 有效性/阈值/威胁链的函数入口名（不影响偏移结论）。
4. **真机动态确认**：改 `Verses[Armor]` 观察伤害（静态已闭环，动态待跑）。

---

## 7. 可复算脚本索引

| 脚本 | 作用 |
|---|---|
| `s01_v1_owner.py` | GetTotalDamage 边界重建 + E8/E9/imm32 xref |
| `s02_offAC_host.py` | BulletClass::Construct 反汇编 + 全 .text `+0xAC` 读写扫描 |
| `s03_weapon_armor.py` | WeaponTypeClass::ctor 字段清零 + Armor 装载点 |
| `s04_yrpp_cross.py` | TechnoClass/HouseClass ctor + Warhead 装载 + Detonate 交叉 |
| `s01_gettotaldamage.asm` | GetTotalDamage 全量反汇编 |
| `s02_windows.asm` | V2–V6 现场窗口 |
| `s03_weapon_etc.asm` / `s04_yrpp_cross.asm` | 装载器/ctor 反汇编 |
| `claims.txt` | 字节级 claims 汇总 |

---

## 8. 一句话

> **`obj+0xAC` 宿主定谳为 `WeaponTypeClass`（`Warhead` 字段），BulletClass 被排除（其 WH 在 +0x128）；
> V1 块 `0x4891C6` 是 `MapClass::GetTotalDamage @ 0x489180` 的正伤害分支（非独立函数，故无直引）；
> `+0x9C = Armor`（0..10）经 LoadFromINI 写点 + 解析器 11 项表双向实证；
> BulletClass/WeaponTypeClass/TechnoClass 关键偏移与 YRpp 全部一致，HouseClass Array 有轻微布局偏移差。**
