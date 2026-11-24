# UNKNOWNS.md — S13-K2 未决项（不臆造，三级分级）

## U1 · Warhead +0x12C / +0x124 的字段语义名 `[静态推断]`
伤害链 `fmul [edi+0x12C]`@0x4891CE、`fld [edi+0x124]`@0x4891D8 读点字节级为真，但这两个偏移在 `WarheadTypeClass` 自己的 INI loader 里无带键名的写点（S13-K1 字段表标为内部系数）。按坑 4「字段偏移不能定语义」，**只报读点+偏移，不赋 YRpp 字段名**（不写成 "Damage"/"SpreadFactor" 之类）。需该类写点的键字符串证据才能升 `[已证]`。

## U2 · 护甲索引 = `[eax+0x9C]` 的语义 `[静态推断]`
`0x701D59 mov ecx,[eax+0x9C]` 是 Verses 索引的唯一来源读点，但 `TechnoTypeClass` 自身无 `Armor=` INI 写点支撑（S13-F1 审计已把此条从 `[已证]` 降为 `[静态推断]`，坑 4）。本卡沿用该分级，不升级。护甲维度 11 本身由 0x7E5210 名表锚定 `[已证]`，但「+0x9C 就是存该枚举的字段」仍 `[静态推断]`。

## U3 · Verses loader 的函数入口与归属 `[未证]`
loader 循环在 0x75DE06..0x75DE58（含 `fstp qword [ebx]`@0x75DE48），位于 0x75DDC0 起的一段函数体内；该段 **不在 function_atlas、不在 coverage**（边界扫描未找到标准 `ret+nop` 入口，序言形态非简单边界）。因此本卡不把 loader 作为新 S13 entry 交付（避免违反「不在 atlas 区间内 ≠ 是函数」——四项判据未全满足）。循环本体字节级 `[已证]`，「它是独立函数、入口地址 X」`[未证]`。

## U4 · T4 补名 0 个（named 212→212，未达 90%）
S13 非已证 `sub_` entry 共 27 个（见 `work/t2_verses_scan.py` 输出），语义栏全为「虚表索引 1 单一指针 / callgraph / 虚表索引 3」等**弱关联**：既无静态 vtable 初始化链（`C7 05 <obj><vt>`）锚到 RTTI 类名，又无唯一字符串/已知名调用者，按 R14-R14 S 口径与「槽位继承须核父类语义一致」的约束，**无法定真名**。纪律要求「拿不到就保持 sub_，不许编名」，故本卡 T4 交 0 行。named 距 90%（216）仍差 4。

## U5 · 伤害插值段（0x4891E9–0x489220）的精确语义 `[静态推断]`
`fcomp`/`fimul [esp+0x1C]`/`fidiv [esp+0x10]`/`fadd` 的逐指令字节为真，但「base 与 temp 之间按距离比插值」是对 FPU 栈操作的解释；函数名 GetTotalDamage 与栈参 damageBase 的来源（0x701D5F `edx=ebp`）未在 S13 侧追到定义唯一写点。乘算链骨架与 Verses 乘子 `[已证]`，插值语义 `[静态推断]`。

## U6 · proved 鸿沟（结构性，非本卡可闭合）
S13 proved 47/240=19.58%，距 50%（120）差 73。本卡可靠增量仅 +8（GetSize/WhatAmI 恢复，见 DISAGREE D2）。原因：9 个 Verses 消费者中 8 个归 S05、1 个归 S06（非 S13），伤害链核心函数 GetTotalDamage/DamageArea 归 S06；余 27 个 `sub_` 无证据升级。要再 +65 需对 S13 其余虚表方法逐条做 RTTI+双点闭合，非单卡工作量。
