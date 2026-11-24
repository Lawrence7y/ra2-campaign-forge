# S06-K5 PROGRESS（卡号 S06-K5）
> 目标 SHA-256 `73201CC0…F67476` 全值自算一致；纯静态；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra；写域仅 S06_K5 目录。
> 纪律 9：盘上复算 S06 分母=848（coverage∩atlas，统一大小写）、proved=103、门槛=424；K4 delta 未并入，并入后=126；卡面一致，未停。

## 结论表（每条带分级 + 证据路径；路径相对本卡）
| entry | 语义名 | 分级 | 判据摘要 | 证据路径 |
|---|---|---|---|---|
| 00483780 | CellClass::SpreadTiberiumToNeighbor | [已证] 行为级全闭环 | 8 环门控 + 0x5FDD20 + 1e-5 + 8 邻向循环 + IncreaseTiberium(typeIndex,3)@0x4838C5；返回被调 al，非 true | EVIDENCE/growth_neighbors_proof.txt |
| 00483710 | CellClass::GrowTiberiumIfAllowed | [已证]（K4 已入账，盘上未并入） | 单格分支 typeIndex,1；本卡独立复扫复核确认 | EVIDENCE/candidate_census.txt |
| 004838E0 | canSpread helper | 不可证（非门控分支） | 被 00483780 调用；缺 0x5FDD20/0x487190/1e-5/rules 门 | EVIDENCE/candidate_census.txt |
| 004839F0 | constructor-like | 不可证 | 写 vtable + call 0x7C8E17；缺 0x5FDD20/0x487190/1e-5/rules 门 | EVIDENCE/candidate_census.txt |
| 0071C730 | TerrainClass::slot23（占位名） | 不可证 | 仅一次调用 00483780，无自身门控；缺 0x5FDD20/0x487190/1e-5/rules 门 | EVIDENCE/candidate_census.txt |
| 00722440 | type-level growth distributor | 不可证（门控分支） | 有 1e-5@+0xA0，调 0x4838E0+00483780；缺 0x5FDD20 与直接 0x487190 | EVIDENCE/candidate_census.txt |
| 00722F00 | type-level growth distributor | 不可证（门控分支） | 有 1e-5@+0xB0，调 00483710；缺 0x5FDD20 与直接 0x487190 | EVIDENCE/candidate_census.txt |
| 0047C060/00480CB0/004818E0 等 | 邻域谓词/遍历 | 不可证 | 缺 IncreaseTiberium/1e-5/rules 门闭环，逐项列于 census | EVIDENCE/candidate_census.txt |

## 任务一：00483780 行为闭环（可复算）
- 门控 G0–G7：force arg(bl) → RulesClass byte0&0x80@0x483796 → [cell+0x44]→0x5FDD20@0x48379E → density[+0x11E]>typeIndex/2@0x4837B7 → [cell+0x11C]==0@0x4837C1 → [type+0xA0]>=1e-5@0x4837D4 → cell dword [+0xE4]==0@0x4837E7 → 二次 0x5FDD20@0x4837EE；fail 收敛 0x483800 xor al,al;ret 4。
- 被调语义：0x5FDD20=coverage S22 [已证]（overlay 类型→矿石类型索引）；0x487190=coverage S06 CellClass::IncreaseTiberium [已证]（已入账地址）。
- 8 邻向：ebx=0..7（0x483840/0x4838AA/0x4838AB），方向=(seed+i)&7，偏移表 0x89F688 字对，GetCell 0x5657A0，canSpread 0x4838E0。
- 增量 3：0x4838C0 `6a03` push 3；栈回溯（callee ret 8/ret 4）证明 arg1=[E+4]=typeIndex，arg2=3。
- 返回值：成功路径无 mov al,1，返回被调 IncreaseTiberium 的 al（可能为 0）；所有 fail 路径返回 0。未写「return true」。

## 任务二：独立候选普查（未复用 K4 扫描器/阈值）
- 自建双通道：Channel A = 逐函数反汇编取行为锚点；Channel B = 裸 E8 rel32 全 .text 扫 + coverage 区间归属（不依赖 atlas entry+size）。
- 候选池 = 24 条（core 信号：5 个增长锚点调用 / 1e-5 引用 / 方向表使用）；全闭包仅 00483710 与 00483780。
- 0x483700–0x483B00 内 4 函数 + 全部直接调用者逐条判：仅 00483780 为新增可证门控分支。
- K4 锚点笔误 0x87190/0x80A80/0x80510（缺前缀 4），疑为 42→1 与 45→1 计数差异根因之一，见 DISAGREE.md。

## 任务三：盘上基线自算
- 分母=848，proved=103，named_L=384，门槛=424；并入 K4 delta(23) 后=126；再并 K5(1) 后=127。与卡面/审计一致。

## 核心数字与复算脚本
- SHA256=73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476
- DELTA_ROWS=1；PROVED_ON_DISK=103/848=12.1462%；+K4=126/848=14.8585%；+K4+K5=127/848=14.9764%
- 复算：`python work/baseline.py`；`python work/scan.py`；`python work/make_evidence.py`（输出 EVIDENCE/）；公共库 `work/k5_lib.py`。
