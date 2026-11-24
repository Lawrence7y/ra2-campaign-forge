# LAYOUT.md — S13-K2 · 四类字段布局双支撑（增量）

> 基线（只引用不重做）：S13-K1 四类 RTTI/vftable/槽数 + 越界写扫描 0 处（布局闭合）；
> 字段数审计订正：WeaponTypeClass **87** / WarheadTypeClass **88** / BulletTypeClass **50** / BulletClass **28**（S13-K1 `_audit/VERDICT.md`）。
> 本卡只做**增量**：对 T2 涉及的字段（Verses 块、GetSize/WhatAmI、伤害字段）补写者+读者双支撑，报虚调用剔除数与三种访问形式。
> 复算：`python work/t3_fields.py`、`python work/t2_verses_scan.py`；证据 `EVIDENCE/VERSES_TABLE.txt`、`EVIDENCE/GETSIZE_CLOSURE.txt`。

## 1. 增量字段表（每条该类自己的写点+读点双支撑）

记法：写者/读者站点为绝对 VA；`虚调用剔除` = 扫描中命中 `call [reg+disp]` 但因属虚槽调用而不计入数据字段读点的 disp 集合。

| 类 | 偏移 | 宽度 | 类型 | 写者（本类） | 读者（本类/链上） | 语义 | 分级 |
|---|---|---|---|---|---|---|---|
| WarheadTypeClass | +0xA0..+0xF7 | 8×11 | double[11] | loader `fstp qword [ebx]`@0x75DE48（ebx=self+0xA0，循环×11 stride8，0xB 次）；ctor `rep movsd 0x14`+`[esi+0xA0]=1.0` | 9 处 `scale=8 disp=0xA0` FPU（0x48923D 等，见 VERSES.md §2）；本类消费函数读 +0x12C/+0x124 | **Verses[armor]** 护甲倍率 | `[已证]`（写循环+读签名字节级；维度由 0x7E5210 锚定） |
| WarheadTypeClass | +0x12C | 4 | float | loader/ctor（S13-K1 字段表） | `fmul [edi+0x12C]`@0x4891CE | 伤害蓝图系数 | `[静态推断]`（语义名坑4；读点字节级） |
| WarheadTypeClass | +0x124 | 4 | float | loader/ctor | `fld [edi+0x124]`@0x4891D8 | 距离/等级系数 | `[静态推断]`（同上） |
| WeaponTypeClass | +0xAC | 4 | WarheadTypeClass* | `Warhead=`→0x75E3B0→`[weapon+0xAC]`（S13-K1 结论5） | 读 0x772942/0x772B96（S13-K1 审计） | 弹头指针 | `[已证]` |
| WeaponTypeClass | +0xA0 | 4 | BulletTypeClass* | `Projectile=`→0x46C790→`[weapon+0xA0]` | 读 0x772975/0x772B5E | 子弹类型指针 | `[已证]` |

### GetSize/WhatAmI 槽字段（slot11/slot12，非数据字段而是 vtable 项）

见 VERSES.md §4 表，4 类 ×2 = 8 条，全部字节级双点闭合 `[已证]`，本卡 coverage_delta 交 8 行恢复。

## 2. 虚调用剔除（纪律：`call [reg+disp]` 不计入数据字段读点）

对 4 类核心函数（`t3_fields.py` 按 atlas 区间包含取函数体）扫描，`call [reg+disp]` 的 disp 集合显式剔除：

| 类 | 剔除的虚调用 disp | 个数 |
|---|---|---|
| WeaponTypeClass（ctor/GetSize/WhatAmI） | {8} | 1 |
| WarheadTypeClass（ctor/GetSize/WhatAmI） | {8, 12} | 2 |
| BulletTypeClass（ctor/GetSize/WhatAmI） | {8} | 1 |
| BulletClass（ctor/Construct/AI/GetSize） | {8,16,44,72,88,128,132,164,248,292,436,440,456,460} | 14 |

它们全部是 `call [vptr+disp]`（间接调用虚槽），**不是数据字段读取**，已从读者集合中剔除。

## 3. 三种访问形式都扫（纪律 19 新增第三种）

| 形式 | 处理 | 本卡结果 |
|---|---|---|
| ① 绝对寻址 `[0x........]` | `t3_fields.py` 的 abs 列 | 4 类核心函数内 abs 命中 6/16/12/33 处（多为全局数组、容器项，非本类字段，不纳入本类布局） |
| ② 立即数载入基址 + `[reg+off]` | `mov esi/edi/ebx,<obj>` 后 `[reg+off]` | loader 主通道：`lea ebx,[esi+0xA0]`（esi=this）；伤害链：`[edi+0x12C]`/`[edi+0x124]`/`[edi+edx*8+0xA0]`（edi=warhead） |
| ③ `mov reg,[基址全局] → [reg+idx*4] → [eax+off]`（格数组型，§S06-K3） | 已检查 | 本卡 4 类核心路径**无**此形态；Warhead/Bullet 查找全局数组（如 `[0x8874C4]`/`[0xA83C84]`）走的是 ②的 `mov eax,[glob]`→`[eax+esi*4]` 两段式，**op1 内存操作数已按纪律 19 检查** |

## 4. 跨类陷阱（禁止套用，逐项核对）

| 偏移 | 陷阱 | 本卡处置 |
|---|---|---|
| +0x94 | 层索引 / 别处函数指针 | 本卡 4 类字段表未把 +0x94 计入本类字段 |
| +0x184 | Anim=DelayTimer / 别处函数指针槽 | 未计入 |
| +0x80 | 精灵脏标记（S07 ObjectClass） | 4 类核心函数无此字段访问，未计入 |
| +0xB8 | TiberiumClass 单位价值 / CellClass 本类访问 0 条 | 未套用 |
| +0xA0 | **本卡特别声明**：全镜像 `disp=0xA0` 的非调用访存 169 写/432 读，绝大多数是别的类的栈槽/字段；**只有 `scale=8 + disp=0xA0` 的 FPU 访存（9 处）是 Verses 的特异签名** | 用 scale=8 约束剔除跨类噪音；不把 169/432 当 Verses 读者 |

## 5. 布局闭合（S13-K1 入账，本卡复核无越界）

四类 `max_end ≤ GetSize`：`0x15D≤0x160`（Weapon）、`0x1CC≤0x1D0`（Warhead）、`0x2F8=0x2F8`（BulletType，末字节有主、越界写扫描 0）、`0x159≤0x160`（Bullet）。本卡工厂分配点（push 0x160/0x1d0/0x2f8/0x160）与 GetSize slot12 imm 逐字节相等，独立复核与 S13-K1 一致。
