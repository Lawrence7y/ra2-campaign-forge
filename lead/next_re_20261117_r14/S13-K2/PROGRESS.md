# S13-K2 PROGRESS（≤60 行）

目标 `gamemd.exe` SHA-256 `73201CC0…FCF67476`（已核）· capstone 5.0.7 `skipdata=True` · 全部证据字节级、只读目标。
开工基数（本卡现读盘核实，与 PANEL.md 一致）：S13 ∩ atlas = **240**，`named_L=named_S=212`（Class::sub_=0），`proved=47`（19.58%）。

## 结论表（分级 + 证据路径）

| # | 结论 | 分级 | 证据路径 |
|---|---|---|---|
| 1 | **Verses 表 = 每 WarheadTypeClass 实例内 double[11] @ +0xA0..+0xF7（88B）**，非派卡猜的「.rdata 全局 11×N byte 矩阵」；缩放 0–100%→0.0–1.0（×0.01），非 0–255 | 已证（loader 循环+默认串+9 处 FPU 读签名三通道） | `EVIDENCE/VERSES_TABLE.txt`、`VERSES.md` §1–2 |
| 2 | INI `Verses=` 11 百分比按 `strtok(',')` **位置序**落槽：`lea ebx,[esi+0xA0]`/`mov ebp,0xB`/`fstp qword [ebx]`@0x75DE48/`add ebx,8`；乘 0.01@0x7E3808 | 已证（逐指令字节） | `EVIDENCE/VERSES_TABLE.txt`、`work/t2_dump.py` |
| 3 | 11 护甲维度由 `.rdata 0x7E5210` 11 项名表锚定（none..special_2；第 12 项 "Money" 非护甲） | 已证 | `EVIDENCE/VERSES_TABLE.txt`、`work/t2_dump.py` |
| 4 | 伤害乘算链 `GetTotalDamage 0x489180`：`fild [esp+0xC]`→`fmul [edi+0x12C]`→插值→**`fmul qword [edi+edx*8+0xA0]`@0x48923D（×Verses[armor]）**→`_ftol 0x7C5F00`→封顶 `[[0x8871E0]+0x16C8]` | 乘子/地址已证；插值语义 `[静态推断]` | `EVIDENCE/DAMAGE_CHAIN.txt`、`VERSES.md` §3 |
| 5 | **4 类 GetSize 双点闭合 4/4**：Weapon 0x160@0x7730D0 / Warhead 0x1D0@0x75E4F0 / BulletType 0x2F8@0x46C860 / Bullet 0x160@0x46B540，均为 slot12 `B8 imm32 C3` + 工厂 `push size→new 0x7C8E17` 两处独立对上 | 已证（vtable 实读+分配点，§981 槽契约） | `EVIDENCE/GETSIZE_CLOSURE.txt`、`VERSES.md` §4 |
| 6 | 8 个 GetSize/WhatAmI 行按 `UNSOURCED_PROVED.tsv` 恢复路径补证恢复（本卡实存 evidence_path + 双点闭合），非静默提级 | 已证（字节级可独立复算） | `coverage_delta.tsv`、`DISAGREE.md` D2 |
| 7 | 虚调用剔除：4 类核心函数 `call [reg+disp]` disp 集合 {8}/{8,12}/{8}/{14 项} 不计入数据字段读点；跨类 +0xA0 用 scale=8 约束剔除 169 写/432 读噪音 | 已证（方法） | `LAYOUT.md` §2/§4、`work/t3_fields.py` |
| 8 | T4 补名 0 个：27 个 sub_ 全弱语义，按 S 口径无真依据，保持 sub_ | 方法结论 | `UNKNOWNS.md` U4、`DISAGREE.md` D5 |

分级口径：`[已证]`=本卡独立字节级实测（每组给地址+字节+复跑脚本）；跨类/弱语义标 `[静态推断]`/`[未证]`；无虚高。

## 给审计的核心数字（3 个 + 复算）

1. **proved 47 → 55（+8）**：距 50%（120）仍差 65。复算：`t1_targets.py` 得 47；`coverage_delta.tsv` 8 行均 `[已证]` 且 evidence 实存，47+8=55。消费者侧 9 处归 S05/S06/S14（D3），不挪用。
2. **named 212 → 212（+0）**：距 90%（216）差 4。复算：`t1_targets.py` 的 named_S=212；U4 说明为何 27 个 sub_ 不可补名。
3. **Verses 维度 11 × 8B = 88B @ +0xA0..+0xF7**：复算 `work/t2_dump.py`：loader `mov ebp,0xB`+`add ebx,8`+`fstp qword[ebx]`；默认串 0x847C40 恰 11 token；0x7E5210 恰 11 护甲名；全镜像 `scale=8 disp=0xA0` FPU 恰 9 处（`t2_verses_scan.py`）。

## 复跑入口（只读目标，全在 work/）

```
python work/t1_targets.py       # TARGETS.tsv + named/proved 现读盘
python work/t2_dump.py          # Verses loader/ctor/伤害链/装甲名表/默认串 字节
python work/t2_getsize2.py      # 四类 vtable slot11/12 + 工厂 push 双点闭合
python work/t2_verses_scan.py   # 9 处 FPU 消费者 + 27 sub_ 候选
python work/t2_constret.py      # S13 常量返回 entry（14）+ float 0.01/256.0 复核
python work/t2_extra.py         # 消费者归属（区间包含）+ 额外工厂点
python work/t3_fields.py        # 字段访问三分类 + 虚调用剔除数
```

交付：PROGRESS / TARGETS.tsv / LAYOUT.md / VERSES.md / UNKNOWNS.md / DISAGREE.md / EVIDENCE\\ / work\\ / coverage_delta.tsv。未改 `COVERAGE/coverage.tsv`。
