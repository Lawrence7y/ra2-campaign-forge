# S13-F1 PROGRESS（≤60 行）

## 结论表（分级 + 证据路径）

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | 链上跳数 = **8**（主链 H1–H8，Fire 本体→死亡；H1 为类相关跳） | 已证（逐跳直呼指令逐字符核对） | `FLOW.md` §2、`EVIDENCE/call_sites.tsv` |
| 2 | Fire 虚槽 = **243 (+0x3CC)**，非卡面猜的 slot85；本体 0x6FDD50；Building/Foot 直连，Unit/Infantry/Aircraft 包装→本体 | 已证（.rdata 定界直读 vtable + 包装器逐字节） | `EVIDENCE/vt_slots.txt`、`EVIDENCE/fire_slots_wrappers.txt` |
| 3 | Primary/Secondary = `GetWeapon(weaponIndex)` v254(+0x3F8)@0x6FDD69，`[ebp+0xC]`=索引（0 主/1 副）；目标合法性 `GetFireError` v240(+0x3C0)=0x6FC0B0 | 已证（thiscall ecx 溯源 + 栈参集合） | `EVIDENCE/trace_alloc_weapon_array.txt`、`EVIDENCE/trace_precision.txt` |
| 4 | **BulletClass 分配大小 = 0x160 (352 B)**；工厂 `push 0x160`@0x6C50BC →new 0x7C8E17→ctor 0x466380@0x6C50CF | 已证（字节通道 + S13-K1 GetSize 双通道） | `EVIDENCE/trace_alloc_weapon_array.txt` |
| 5 | Construct 0x4664C0 写 10 字段：Type+AC/Owner+B0/Target+10C/Speed+110/Warhead+128/Damage+6C/Bright+E0/InheritColor+114/DmgMult+150=0x100；ret 0x1C | 已证 | `EVIDENCE/fn_Bullet_Construct_004664C0.txt` |
| 6 | 飞行/命中：AI v23(+0x5C)=0x4666E0 → Fire(hit)0x468D80@0x466771；引爆 Detonate 0x4690B0→DamageArea 0x489280@0x469A83 | 已证 | `EVIDENCE/call_sites.tsv` |
| 7 | **Verses 定位核对通过**：double[11]@Warhead+0xA0..+0xF7（88 B），loader 循环 0xB 次 stride 8 + ctor rep movsd 20 dword + 全镜像 9 处 FPU 索引访存——三通道 | 已证 | `EVIDENCE/verify_verses.txt` |
| 8 | **Armor→Verses 索引**：Armor=TechnoTypeClass+0x9C（读 @0x701D59）→GetTotalDamage 0x489180→`fmul [edi+edx*8+0xA0]`@0x48923D；维度 11 由 Armor 枚举 0..10 支撑 | 已证（edx/edi 全部写入点回溯） | `EVIDENCE/trace_precision.txt`、`FLOW.md` §4 |
| 9 | 生命值 ≤0 分支：`mov eax,[esi+0x6C]; test; jne`@0x70202E → `mov edi,4`(NowDead)@0x702035；跳转表 @0x702D24 六项；TakeDamage=ReceiveDamage 返回 DamageState(0..5)，ret 0x1C | 已证（逐条打完入口→ret + 跳转表实读） | `EVIDENCE/trace_precision.txt` |
| 10 | 死亡处理：FireDeathWeapon@0x70266D、0x708080@0x7027E9；清引用 0x70D4A0 在 DamageArea 6 处直呼（**不在 ReceiveDamage**） | 已证 | `EVIDENCE/trace_death.txt`、`EVIDENCE/trace_death2.txt` |
| 11 | 子弹生命周期：Array 增 ctor@0x4664AB / 减 dtor 0x466560 内@0x466630；容器 0xA8ED40、Count 0xA8ED50；释放 slot8 dtor 0x46B5C0→0x466560@0x46B5C3→delete 0x7C8B3D@0x46B5D0 | 已证（绝对+基址双形式扫描） | `EVIDENCE/trace_array_factory.txt`、`EVIDENCE/trace_alloc_weapon_array.txt` |

分级口径：`[已证]`=逐字节反汇编 + 多通道/RTTI 实测；本卡 11 条全部已证；无虚高。未决见 `UNKNOWNS.md`，与旧文档分歧见 `DISAGREE.md`。

## 核心数字（4 个，给审计）

1. **链上跳数 = 8**（H1–H8）。复算：`grep -c` `EVIDENCE/call_sites.tsv` 主链 8 跳行 + `FLOW.md` §2 表；H1 三类包装调用点 0x415F12/0x7413CE/0x51DF77。
2. **每跳调用点地址**：0x415F12(H1)·0x6FF859(H2)·0x466771(H3)·0x469033(H4)·0x469A83(H5)·0x489AB6(H6)·0x701D64(H7)·0x70266D(H8)。复算：`python work/dump_chain.py` 后查 `EVIDENCE/call_sites.tsv`；H6 虚调用由 `python work/resolve_gaps.py` 单独产出。
3. **Verses 维度依据 = 11（Armor 枚举 0..10）× 8 B（double）= 88 B @ +0xA0..+0xF7**。复算：`python work/verify_verses.py`（loader 0xB 循环 / ctor 0x14 dword / 全镜像 9 处 FPU 索引访存）+ `ref/yrpp/GeneralDefinitions.h:444-456`。
4. **BulletClass 分配大小 = 0x160**。复算：`python work/trace_alloc.py` 看 0x6C50BC `push 0x160`；对 S13-K1 `EVIDENCE/verify_slots.txt` slot12 GetSize=0x160。

## 双通道声明（纪律 1）

- 通道 A（**不依赖** function_atlas entry+size）：.rdata vtable 定界直读 + 字节级 `E8/FF /2` 调用点 + 立即数 `push 0x160` + loader `mov ebp,0xB`/`add ebx,8`（`verify_verses.py`/`dump_vtables.py`/`dump_chain.py`）。
- 通道 B：function_atlas 区间包含（fn_at）用于站点归属与函数体边界（`re_lib.fn_at`）。
- 两通道不同源：A 读原始字节/.rdata，B 读 atlas.tsv 元数据。链上 8 跳全部满足双通道。

## 复跑入口（全部只读目标）

```
python work/re_lib.py            # 环境自检（skipdata=True）
python work/dump_vtables.py      # 虚表槽直读（否证 slot85 猜测）
python work/verify_verses.py     # Verses 三通道复核
python work/dump_chain.py        # 全链函数反汇编 + 调用点表
python work/resolve_gaps.py      # GetTotalDamage 入口/H6 虚调用/分配点
python work/trace_alloc.py       # 分配/Array/武器选择扫描
python work/trace_death.py       # 死亡分支/跳转表
python work/trace_precision.py   # Armor→Verses 数据流逐指令
```
