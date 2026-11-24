# VERSES.md — S13-K2 · Verses 表结构与伤害乘算链

> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…FCF67476`，ImageBase 0x400000。
> 全部证据字节级、可独立复算：`python work/t2_dump.py`、`python work/t2_getsize2.py`、`python work/t2_verses_scan.py`。
> 分级：以下 `[已证]` 均为本卡独立反汇编读数，非复用前序卡结论。

## 1. 派卡假设的裁定（DISAGREE 详见 DISAGREE.md）

派卡卡面写「**11 种护甲 × N 种弹头 的矩阵**、表在 `.rdata`、元素宽度 byte、0–100%→0–255 缩放」——**这是猜测（纪律 12），字节层不成立**：

| 派卡猜测 | 实测真值 | 证据 |
|---|---|---|
| 全局 11×N 矩阵在 `.rdata` | ❌ **每实例字段**，不在 `.rdata`；`[0x7E5210]` 是 11 项**装甲名字符串表**，不是倍率矩阵 | T2 dump §装甲名表 |
| 元素宽度 byte / 0–255 | ❌ **double（8 字节）**，100%→**1.0**（0–100% 经 ×0.01） | `fstp qword [ebx]`@0x75DE48；`fmul [0x7E3808]`=0.01 |
| 表槽由 INI 键名定位 | ❌ 由 `strtok(',')` **位置序**写入，无按装甲名的键查表 | loader 循环 0x75DE11–0x75DE58 |

## 2. Verses 表的结构（真值）

- **存储**：`WarheadTypeClass` 实例内 `double[11] @ +0xA0..+0xF7`（88 B）。**写它的字段偏移 = +0xA0**；**读它的函数 = `GetTotalDamage 0x489180`**（coverage 归 S06/MapClass，是伤害结算链上的函数，S13-F1 §947 入账的 H7 跳）。
- **维度**：第一维 = **11 种护甲**（enum 0..10，来自 0x7E5210 名表：none/flak/plate/light/medium/heavy/wood/steel/concrete/special_1/special_2）；第二维 = **每个弹头实例一份**（N = WarheadTypeClass 实例数，运行时从 INI `[Warheads]` 建，无全局 N×11 静态矩阵）。
- **元素宽度**：8（`fstp qword ptr [ebx]`@0x75DE48，ModRM 为 m64）。

### INI `Verses=` 键 → 表槽 映射

`Verses=` 的 11 个百分比按**逗号分隔的位置顺序**落槽；第 i 个 token → `warhead->Verses[i]`（i=0..10）：

| 环节 | 地址 | 指令 / 值 |
|---|---|---|
| 目标基址 | 0x75DE06 | `lea ebx,[esi+0xA0]`（esi=WarheadTypeClass* this） |
| 循环次数 | 0x75DE0C | `mov ebp,0xB`（11） |
| 分隔符 | 0x75DE11 | `push 0x25`（`,`） |
| 分词 | 0x75DE14 | `call 0x7CAF30`（strtok） |
| 转整数 | 0x75DE21 | `call 0x7C9BFD`（atoi）；非整数走 0x75DE39 `call 0x7C9D66`（atof） |
| **缩放** | 0x75DE2D–0x75DE31 | `fild [esp+0x10]` → `fmul qword [0x7E3808]`；常量实测 **0.01** ⇒ 0–100% → **0.0–1.0** |
| **写槽** | 0x75DE48 | `fstp qword [ebx]` |
| 步进 | 0x75DE52/0x75DE55/0x75DE58 | `add ebx,8` / `dec ebp` / `jne` |

默认串 @0x847C40（.data）= 11 个 `100%%` ⇒ 默认 11×1.0；构造器另以 `[esi+0xA0]=1.0` + `rep movsd 0x14`（80 B = 10 doubles）补齐 11 项（S13-K1 双通道，本卡字节复核一致）。

## 3. 伤害公式：每一步地址与操作数来源

伤害结算走 S13-F1 §947 入账链，读 Verses 的是 **`GetTotalDamage 0x489180`**（`ret 8`，size 0xED）。调用者在 `ReceiveDamage 0x701900` 内：`0x701D59 mov ecx,[eax+0x9C]`（护甲索引，S13-F1 审计已降 `[静态推断]`，坑4）→ `0x701D61 push ecx` → `0x701D64 call 0x489180`。

| 步 | 地址 | 指令 | 操作数来源 |
|---|---|---|---|
| 1 | 0x4891C6 | `fild dword [esp+0xC]` | 伤害基数（栈参，`this` 值当作 int 读入） |
| 2 | 0x4891CE | `fmul dword [edi+0x12C]` | `edi`=warhead；× Warhead 字段 +0x12C（float） |
| 3 | 0x4891D8/0x4891DE | `fld [edi+0x124]` ; `fmul [0x7E2224]` | × 常量 **256.0**（定点化）；`_ftol`@0x4891E4 |
| 4 | 0x4891E9–0x489220 | `fcomp/fimul/fidiv/fadd` | 按距离比对 base 与 temp 线性插值；`_ftol`→esi |
| 5 | 0x489239 | `fild dword [esp+0x1C]` | 将上述结果 clamp 到 ≥0 后转 float |
| **6** | **0x48923D** | **`fmul qword [edi+edx*8+0xA0]`** | `edi`=warhead，`edx`=护甲索引（栈参 [esp+0x18]）；**× Verses[护甲]** |
| 7 | 0x489244 | `call 0x7C5F00` | `_ftol` 截断 → eax |
| 8 | 0x489249–0x489257 | `cmp eax,[[0x8871E0]+0x16C8]` | 伤害上限封顶，超过取上限 |

**公式**：`damage = min( trunc( max(0,d0) × Verses[armor] ), cap )`，
其中 `d0 = interpolate(base×Warhead[+0x12C], base, trunc(Warhead[+0x124]×256))`。

`_ftol 0x7C5F00`（R14_COMMON §3，1974 调用者）；**不要用 0x485020**（那是矿石价值，S06）。

## 4. GetSize 双向核对（不假定槽 12）

按 §981 槽契约，四类的 GetSize 都在 **slot12（+0x30）**，但这是**.rdata vtable 实读**确定的，非照假定；v[11]=WhatAmI 同为 `B8 imm32 C3`，靠 imm 值（枚举 vs 尺寸）区分，并排除 BulletClass slot35/36 的 `0x7FFFFFFF`/`.data` 反例与抽象基类桩 `0x4C9150`（`33 C0 C3`）。

| 类 | WhatAmI slot11 | GetSize slot12 | 工厂分配点（push→new→ctor） | 闭合 |
|---|---|---|---|---|
| WeaponTypeClass | 0x31 @0x7730E0 | **0x160** @0x7730D0 | push 0x160@0x772FF6 → 0x7C8E17 → ctor 0x771C70 | ✓ |
| WarheadTypeClass | 0x32 @0x75E500 | **0x1D0** @0x75E4F0 | push 0x1D0@0x75E406 → 0x7C8E17 → ctor 0x75CEC0 | ✓ |
| BulletTypeClass | 0x09 @0x46C850 | **0x2F8** @0x46C860 | push 0x2F8@0x46C484 → 0x7C8E17 → ctor 0x46BBC0 | ✓ |
| BulletClass | 0x08 @0x46B550 | **0x160** @0x46B540 | push 0x160@0x6C50BC → 0x7C8E17 → ctor 0x466380 | ✓ |

**4/4 闭合**。分配编码均为 `68 imm32`（尺寸 ≥0x80 无法用 `6A imm8`；6A 形式已纳入扫描、此处不存在）。证据 `EVIDENCE/GETSIZE_CLOSURE.txt`。
