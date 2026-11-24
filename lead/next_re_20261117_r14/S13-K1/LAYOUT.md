# S13-K1 LAYOUT — 四个核心战斗类的字段布局

> 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`，ImageBase 0x400000。只读。capstone 5.0.7 `skipdata=True`；
> 类名以 RTTI TypeDescriptor 实测（`work/rtti_extract.py`）；虚表长度**从 .rdata 定界数槽**（不读 `vtables_v2.json`）；
> thiscall `this` 寄存器回溯到首个 `mov reg,ecx`（构造器/loader 逐一确认）；站点归属用函数区间包含。
> 字段语义锚点=INI 键；写者=`mov [obj+off],reg`/`fstp [obj+off]`；读者=同 loader 中 `mov reg,[obj+off]` 取默认值（该类自身读点）。
> 原始未截断证据：`EVIDENCE/ini_fields.tsv`、`EVIDENCE/ctor_offsets.tsv`、`EVIDENCE/field_tables.txt`、`EVIDENCE/rtti_extract.txt`。

## 0 定位总表（RTTI 实测，非文件名启发）

| 类 | TypeDescriptor | COL | vftable(主) | 实测槽数 | slot11=WhatAmI | slot12=GetSize | 构造器入口 | INI loader(slot25) |
|---|---|---|---|---|---|---|---|---|
| WeaponTypeClass | 0x00849248 | 0x0080E3C0 | 0x007F73B8 | 27 | id 0x31 | 0x160 | 0x00771C70 | 0x00772080 |
| WarheadTypeClass | 0x00847C18 | 0x0080D2C0 | 0x007F6B30 | 27 | id 0x32 | 0x1d0 | 0x0075CEC0 | 0x0075D3A0 |
| BulletTypeClass | 0x0081AFB0 | 0x007FC7C8 | 0x007E4948 | 40 | id 0x09 | 0x2f8 | 0x0046BBC0 | 0x0046BEE0 |
| BulletClass | 0x0081AF70 | 0x007FC710 | 0x007E46E4 | 125 | id 0x08 | 0x160 | 0x00466380 | —（运行时对象） |

槽数双通道：`.rdata` 定界连续指针扫描（27/27/40/125）与 `re_atlas/evidence/rtti/symbols.json` 元数据一致；
slot11/slot12 体均为 `mov eax,imm; ret`，实测返回值见上表（`EVIDENCE/verify_slots.txt`）。四张副虚表 `vt-0x2C..vt-0x10` 为多重继承子对象表（见 `rtti_extract.txt`）。

## 1 WeaponTypeClass — 字段数 78（排除 4 个 vptr 槽）

| off | 宽 | 类型/语义 | 写者站点 | 读者站点 |
|---|---|---|---|---|
| 0x98 | 4 | int AmbientDamage | 0x007720C6, 0x771c87 | 0x007720B2 |
| 0x9C | 4 | int Burst | 0x007722CE, 0x771c8d | 0x007722BA |
| 0xA0 | 4 | BulletTypeClass* (Projectile=) | 0x7729AA; conv 0x46C790 | — |
| 0xA4 | 4 | int Damage | 0x007722E8, 0x771c9d | 0x007722D4 |
| 0xA8 | 4 | WRAP_0x00474810 Speed | 0x00772302, 0x771ca3 | 0x007722EE |
| 0xAC | 4 | WarheadTypeClass* (Warhead=) | 0x772992; conv 0x75E3B0 | — |
| 0xB0 | 4 | int ROF | 0x0077231C, 0x771caf | 0x00772308 |
| 0xB4 | 4 | WRAP_0x00474620 Range | 0x00772336, 0x771cb6 | 0x00772322 |
| 0xB8 | 4 | WRAP_0x00474620 MinimumRange | 0x0077235B, 0x771cbf | 0x0077233C |
| 0xBC | ? | [未证] (ctor 默认写) | 0x771f12, 0x772042, 0x7731e2 | — |
| 0xC0 | ? | [未证] (ctor 默认写) | 0x77203c, 0x772061, 0x7731dc, 0x773201 | — |
| 0xC4 | ? | [未证] (ctor 默认写) | 0x77206f, 0x77320f | — |
| 0xC9 | ? | [未证] (ctor 默认写) | 0x772069, 0x773209 | — |
| 0xD8 | ? | [未证] (ctor 默认写) | 0x771f18, 0x77200b, 0x7731ab | — |
| 0xDC | ? | [未证] (ctor 默认写) | 0x772005, 0x77202a, 0x7731a5, 0x7731ca | — |
| 0xE0 | ? | [未证] (ctor 默认写) | 0x772036, 0x7731d6 | — |
| 0xE5 | ? | [未证] (ctor 默认写) | 0x772030, 0x7731d0 | — |
| 0xF4 | ? | [未证] (ctor 默认写) | 0x771f1e, 0x771fd4, 0x773174 | — |
| 0xF8 | ? | [未证] (ctor 默认写) | 0x771fce, 0x771ff3, 0x77316e, 0x773193 | — |
| 0xFC | ? | [未证] (ctor 默认写) | 0x771fff, 0x77319f | — |
| 0x101 | ? | [未证] (ctor 默认写) | 0x771ff9, 0x773199 | — |
| 0x110 | 4 | char*/ptr OccupantAnim | 0x007725CB, 0x771d18 | 0x007725AC |
| 0x114 | 4 | char*/ptr AssaultAnim | 0x007725A6, 0x771d1e | 0x0077255F |
| 0x118 | 4 | char*/ptr OpenToppedAnim | 0x0077260A, 0x771d24 | 0x007725D1 |
| 0x11C | 4 | char*/ptr AttachedParticleSystem | 0x0077293C, 0x771d2a |  |
| 0x120 | ? | [未证] (ctor 默认写) | 0x771d30 | — |
| 0x121 | ? | [未证] (ctor 默认写) | 0x771d36 | — |
| 0x122 | ? | [未证] (ctor 默认写) | 0x771d3c | — |
| 0x123 | ? | [未证] (ctor 默认写) | 0x771d42 | — |
| 0x124 | ? | [未证] (ctor 默认写) | 0x771d48 | — |
| 0x125 | ? | [未证] (ctor 默认写) | 0x771d4e | — |
| 0x126 | ? | [未证] (ctor 默认写) | 0x771d54 | — |
| 0x127 | ? | [未证] (ctor 默认写) | 0x771d5a | — |
| 0x128 | ? | [未证] (ctor 默认写) | 0x771d60 | — |
| 0x129..0x13B | 1 ea | UseFireParticles, UseSparkParticles, OmniFire, DistributedWeaponFire, IsRailgun, Lobber, Bright, IsSonic, Spawner, Limbo | 0x007726D4, 0x771d66, 0x007726F4, 0x771d6c, 0x00772717, 0x771d72, 0x00772722, 0x771d78, 0x00772742,  | 0x007726BA, 0x007726DA, 0x007726EE, 0x00772708, 0x00772728,  |
| 0x13C | 4 | int DisguiseFakeBlinkTime | 0x00772280, 0x771dda | 0x0077226C |
| 0x140..0x155 | 1 ea | InfiniteMindControl, FireWhileMoving, DrainWeapon, FireInTransport, Suicide, TurboBoost, Supress, Camera, Charges, IsLas | 0x00772218, 0x771de0, 0x00772232, 0x771de6, 0x0077224C, 0x771ded, 0x00772266, 0x771df3, 0x0077229A,  | 0x00772204, 0x0077221E, 0x00772238, 0x00772252, 0x00772286,  |
| 0x158 | 4 | int RadLevel | 0x007728F6, 0x771e6b | 0x007728CD |
| 0x15C | 1 | bool IsMagBeam | 0x00772901, 0x771e71 | 0x007728E7 |

## 2 WarheadTypeClass — 字段数 69（排除 4 个 vptr 槽）

| off | 宽 | 类型/语义 | 写者站点 | 读者站点 |
|---|---|---|---|---|
| 0x98 | 8 | double Deform | 0x0075D792, 0x75ced8 | 0x0075D77D |
| 0x9C | ? | [未证] (ctor 默认写) | 0x75cede | — |
| 0xF8 | 8 | double ProneDamage | 0x0075D9A4, 0x75cee4 | 0x0075D989 |
| 0xFC | ? | [未证] (ctor 默认写) | 0x75ceeb | — |
| 0x100 | 4 | int DeformThreshhold | 0x0075D7B2, 0x75cef8 | 0x0075D798 |
| 0x104 | ? | [未证] (ctor 默认写) | 0x75d35f, 0x75e63f | — |
| 0x108 | ? | [未证] (ctor 默认写) | 0x75d359, 0x75d37e, 0x75e639, 0x75e65e | — |
| 0x10C | ? | [未证] (ctor 默认写) | 0x75d38c, 0x75e66c | — |
| 0x111 | ? | [未证] (ctor 默认写) | 0x75d386, 0x75e666 | — |
| 0x120 | 4 | int InfDeath | 0x0075D771, 0x75cf14 | 0x0075D75D |
| 0x124 | 4 | double CellSpread | 0x0075D3EB, 0x75cf1a | 0x0075D3D2 |
| 0x128 | 4 | double CellInset | 0x0075D40A, 0x75cf25 | 0x0075D3F1 |
| 0x12C | 4 | double PercentAtMax | 0x0075D429, 0x75cf2b | 0x0075D410 |
| 0x130 | 1 | bool CausesDelayKill | 0x0075D443, 0x75cf31 | 0x0075D42F |
| 0x134 | 4 | int DelayKillFrames | 0x0075D45D, 0x75cf37 | 0x0075D449 |
| 0x138 | 4 | double DelayKillAtMax | 0x0075D47C, 0x75cf41 | 0x0075D466 |
| 0x13C | 4 | double CombatLightSize | 0x0075D49B, 0x75cf47 | 0x0075D482 |
| 0x140 | 4 | WRAP_0x00644890 [converter] | 0x0075D4D4, 0x75cf4d |  |
| 0x144..0x15B | 1 ea | Wall, WallAbsoluteDestroyer, PenetratesBunker, Wood, Tiberium, Verses, Sparky, Sonic, Fire, Conventional, Rocker, Direct | 0x0075D508, 0x75cf53, 0x0075D522, 0x75cf59, 0x0075D53C, 0x75cf5f, 0x0075D556, 0x75cf65, 0x0075D570,  | 0x0075D4F4, 0x0075D50E, 0x0075D528, 0x0075D542, 0x0075D55C,  |
| 0x15C | ? | [未证] (ctor 默认写) | 0x75cfee | — |
| 0x16C..0x16E | 1 ea | Airstrike, Psychedelic, BombDisarm | 0x0075D8F0, 0x75d009, 0x0075D8FB, 0x75d00f, 0x0075D91B, 0x75d01a | 0x0075D8C1, 0x0075D8E1, 0x0075D901 |
| 0x170 | 4 | int Paralyzes | 0x0075D93E, 0x75d020 | 0x0075D915 |
| 0x174..0x17B | 1 ea | Culling, MakesDisguise, NukeMaker, Radiation, PsychicDamage, AffectsAllies, Bullets, Veinhole | 0x0075D949, 0x75d026, 0x0075D969, 0x75d02c, 0x0075D983, 0x75d032, 0x0075D9C7, 0x75d038, 0x0075D9D2,  | 0x0075D92F, 0x0075D94F, 0x0075D963, 0x0075D9B8, 0x0075D9D8,  |
| 0x17C | 4 | int ShakeXlo | 0x0075DA40, 0x75d056 | 0x0075DA26 |
| 0x180 | 4 | int ShakeXhi | 0x0075DA63, 0x75d05c | 0x0075DA3A |
| 0x184 | 4 | int ShakeYlo | 0x0075DA6E, 0x75d06e | 0x0075DA54 |
| 0x188 | 4 | int ShakeYhi | 0x0075DA8E, 0x75d074 | 0x0075DA74 |
| 0x18C | ? | [未证] (ctor 默认写) | 0x75d328, 0x75e608 | — |
| 0x190 | ? | [未证] (ctor 默认写) | 0x75d322, 0x75d347, 0x75e602, 0x75e627 | — |
| 0x194 | ? | [未证] (ctor 默认写) | 0x75d353, 0x75e633 | — |
| 0x199 | ? | [未证] (ctor 默认写) | 0x75d34d, 0x75e62d | — |
| 0x1A8 | ? | [未证] (ctor 默认写) | 0x75d2f3, 0x75e5d1 | — |
| 0x1AC | ? | [未证] (ctor 默认写) | 0x75d2e9, 0x75d310, 0x75e5c8, 0x75e5f0 | — |
| 0x1B0 | ? | [未证] (ctor 默认写) | 0x75d31c, 0x75e5fc | — |
| 0x1B5 | ? | [未证] (ctor 默认写) | 0x75d316, 0x75e5f6 | — |
| 0x1C4 | 4 | int MaxDebris | 0x0075DAB1, 0x75d0ae | 0x0075DA88 |
| 0x1C8 | 4 | int MinDebris | 0x0075DABE, 0x75d0b4 | 0x0075DAA2 |

## 3 BulletTypeClass — 字段数 50（排除 4 个 vptr 槽）

| off | 宽 | 类型/语义 | 写者站点 | 读者站点 |
|---|---|---|---|---|
| 0x22F | ? | [未证] (ctor 默认写) | 0x46bd0c | — |
| 0x230 | ? | [未证] (ctor 默认写) | 0x46bd13 | — |
| 0x231 | ? | [未证] (ctor 默认写) | 0x46bd19 | — |
| 0x232 | ? | [未证] (ctor 默认写) | 0x46bd1f | — |
| 0x233 | ? | [未证] (ctor 默认写) | 0x46bd26 | — |
| 0x234 | ? | [未证] (ctor 默认写) | 0x46bd05 | — |
| 0x235 | ? | [未证] (ctor 默认写) | 0x46bd2d | — |
| 0x294..0x2A9 | 1 ea | Airburst, Floater, SubjectToCliffs, SubjectToElevation, SubjectToWalls, VeryHigh, Shadow, Arcing, Dropping, Level, Invis | 0x0046C1A7, 0x46bbd5, 0x0046BFDE, 0x46bbdb, 0x0046BFF8, 0x46bbe1, 0x0046C012, 0x46bbe7, 0x0046C02C,  | 0x0046C17E, 0x0046BFCA, 0x0046BFE4, 0x0046BFFE, 0x0046C018,  |
| 0x2AC | 4 | int Cluster | 0x0046C1B2, 0x46bc72 | 0x0046C198 |
| 0x2B0 | 4 | char*/ptr AirburstWeapon | 0x0046C2DB, 0x46bc7c | 0x0046C298 |
| 0x2B4 | 4 | char*/ptr ShrapnelWeapon | 0x0046C31F, 0x46bc82 | 0x0046C2E1 |
| 0x2B8 | 4 | int ShrapnelCount | 0x0046C32A, 0x46bc88 | 0x0046C310 |
| 0x2BC | 4 | int DetonationAltitude | 0x0046C34A, 0x46bc8e | 0x0046C330 |
| 0x2C0 | 1 | bool Vertical | 0x0046C36D, 0x46bc94 | 0x0046C344 |
| 0x2C8 | 8 | double Elasticity | 0x0046BF76, 0x46bc65 | 0x0046BF61 |
| 0x2CC | ? | [未证] (ctor 默认写) | 0x46bc9a | — |
| 0x2D0 | 4 | int Acceleration | 0x0046BF90, 0x46bc44 | 0x0046BF7C |
| 0x2D4 | 4 | WRAP_0x00474A90 Color | 0x0046BFAA, 0x46bca4 | 0x0046BF96 |
| 0x2D8 | 4 | char*/ptr Trailer | 0x0046C231, 0x46bcaa | 0x0046C1F5 |
| 0x2DC | 4 | int ROT | 0x0046BF3B, 0x46bcb0 | 0x0046BF27 |
| 0x2E0 | 4 | int CourseLockDuration | 0x0046BF55, 0x46bcb6 | 0x0046BF41 |
| 0x2E4 | 4 | int SpawnDelay | 0x0046C24E, 0x46bc4a | 0x0046C237 |
| 0x2E8 | ? | [未证] (ctor 默认写) | 0x46bcbc | — |
| 0x2EC | 1 | bool Scalable | 0x0046C1E2, 0x46bcc2 | 0x0046C1B8 |
| 0x2F0 | 4 | int Arm | 0x0046BF21, 0x46bcc8 | 0x0046BF08 |
| 0x2F4..0x2F7 | 1 ea | AnimLow, AnimHigh, AnimRate, Flat | 0x0046C399, 0x46bcce, 0x0046C3C3, 0x46bcd4, 0x0046C3D5, 0x46bcda, 0x0046C292, 0x46bce0 | 0x0046C380, 0x0046C39F, 0x0046C3BD, 0x0046C272 |

## 4 BulletClass — 字段数 28（排除 4 个 vptr 槽）

| off | 宽 | 类型/语义 | 写者站点 | 读者站点 |
|---|---|---|---|---|
| 0xAC | ? | [未证] (ctor 默认写) | 0x466391, 0x4665e9 | — |
| 0xB0 | ? | [未证] (ctor 默认写) | 0x466397, 0x4665f3 | — |
| 0xB4 | ? | [未证] (ctor 默认写) | 0x46639d | — |
| 0xE0 | ? | [未证] (ctor 默认写) | 0x4663bf | — |
| 0x100 | ? | [未证] (ctor 默认写) | 0x4663c5 | — |
| 0x104 | ? | [未证] (ctor 默认写) | 0x4663b0 | — |
| 0x105 | ? | [未证] (ctor 默认写) | 0x4663b6 | — |
| 0x108 | ? | [未证] (ctor 默认写) | 0x4663cb | — |
| 0x10C | ? | [未证] (ctor 默认写) | 0x4663d1 | — |
| 0x110 | ? | [未证] (ctor 默认写) | 0x4663d7 | — |
| 0x114 | ? | [未证] (ctor 默认写) | 0x4663dd | — |
| 0x118 | ? | [未证] (ctor 默认写) | 0x4663e3 | — |
| 0x120 | ? | [未证] (ctor 默认写) | 0x4663aa | — |
| 0x124 | ? | [未证] (ctor 默认写) | 0x4663e9 | — |
| 0x128 | ? | [未证] (ctor 默认写) | 0x4663ef | — |
| 0x12C | ? | [未证] (ctor 默认写) | 0x4663f5 | — |
| 0x12D | ? | [未证] (ctor 默认写) | 0x4663fb | — |
| 0x130 | ? | [未证] (ctor 默认写) | 0x466401 | — |
| 0x134 | ? | [未证] (ctor 默认写) | 0x466444 | — |
| 0x138 | ? | [未证] (ctor 默认写) | 0x46644a | — |
| 0x13C | ? | [未证] (ctor 默认写) | 0x466450 | — |
| 0x140 | ? | [未证] (ctor 默认写) | 0x466456 | — |
| 0x144 | ? | [未证] (ctor 默认写) | 0x46645c | — |
| 0x148 | ? | [未证] (ctor 默认写) | 0x466462 | — |
| 0x14C | ? | [未证] (ctor 默认写) | 0x466407 | — |
| 0x14E | ? | [未证] (ctor 默认写) | 0x46640e | — |
| 0x154 | ? | [未证] (ctor 默认写) | 0x466419, 0x4665fd | — |
| 0x158 | ? | [未证] (ctor 默认写) | 0x46641f, 0x466586 | — |

## 5 一致性核对（字段表 max_end ≤ GetSize）

| 类 | 字段数(排除vptr) | 最大字段偏移+宽 | GetSize/分配 | 结论 |
|---|---|---|---|---|
| WeaponTypeClass | 78 | 0x15D | 0x160 | 吻合 |
| WarheadTypeClass | 69 | 0x1CC | 0x1D0 | 吻合 |
| BulletTypeClass | 50 | 0x2F8 | 0x2F8 | 吻合 |
| BulletClass | 28 | 0x159 | 0x160 | 吻合 |

## 6 WeaponTypeClass ↔ WarheadTypeClass 引用关系（task 4）

`Warhead=` 键 → `ReadString@0x77295F`（key `0x8183b4`="Warhead"，默认取当前 `+0xAC`）→ `call 0x75E3B0`（字符串→WarheadTypeClass* 解析器）→ `mov [esi+0xAC],eax @0x772992`。
即 **WeaponTypeClass+0xAC = WarheadTypeClass\***。同段 `Projectile=`（key `0x849268`）→ `call 0x46C790` → `mov [esi+0xA0],eax @0x7729AA`，即 **+0xA0 = BulletTypeClass\***。
证据：`EVIDENCE/inspect_special.txt`（逐条），写者站点 `ini_fields.tsv`；构造器同样在 `0x771CA9/0x771C97` 清这两个指针。

## 7 Verses 伤害倍率矩阵（task 5）

`Verses=` 键（默认串 "100%,…" 共 11 项，`0x847c40`）→ `ReadString@0x75DDE6` → `strtok(',')@0x7c9cc2` → 循环 `strchr('%')@0x7caf30` + `atoi@0x7c9bfd` ×常数 `@0x7e3808` → `fstp qword [ebx] @0x75DE48`，
其中 `lea ebx,[esi+0xA0]`、`mov ebp,0xB`（11 次）、`add ebx,8`。构造器 `0x75CEC0` 内 `lea esi,[ebp+0xA0]` + `mov ecx,0x14; rep movsd @0x75D1A7` 独立复现 11 个 double 的初始化（首项 1.0 = `0x3FF0000000000000`）。
**维度 11（护甲类型）× double(8B)，行主序连续 @ WarheadTypeClass+0xA0..+0xF7（88 B）**。+0x149 的 byte 不是 INI 字段，而是 0x75DE80/0x75DE98 依 +0xC0/+0xD0 与阈值 `0x7e2800` 比较得到的派生标志（原工具误标为 Verses，已更正）。
