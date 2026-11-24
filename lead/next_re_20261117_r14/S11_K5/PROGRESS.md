# S11-K5 · PROGRESS（真语义收窄重做）

> 目标 ra2youli\gamemd.exe，自算 SHA-256 73201CC0…F67476；只读 PE，Python 3.12 + capstone 5.0.7(skipdata=True) + pefile，未用 Ghidra；写域仅 S11_K5\。
> 纪律：不把 vtable 槽直指当语义；只认 GetSize 双点闭合 / WhatAmI 枚举+RTTI 语义。K4 FAIL 的 331 行全部原级保留。
> 本卡 **grade 增量 0**：11 条 `[已证]` 行做真语义重证/证据加固；非已证行无任何允许类型候选，故不伪造 ≥15 行升级。

## 结论表

| entry | 结论（证据要点） | 分级 | 证据路径 |
|---|---|---|---|
| 004B4CF0 | DriveLocomotionClass::GetSize：`b870000000c3`=0x70；CI 6C4010 `6a70`@6C403C→new 7C8E17；grade 不变 | [已证] | coverage_delta.tsv；EVIDENCE/getsize_closure.txt |
| 004B66E0 | DropPodLocomotionClass::GetSize：`b830000000c3`=0x30；CI 6C4910 `6a30`→new；grade 不变 | [已证] | 同上 |
| 004D0390 | FlyLocomotionClass::GetSize：`b860000000c3`=0x60；CI 6C4A90 `6a60`→new；grade 不变 | [已证] | 同上 |
| 005172B0 | HoverLocomotionClass::GetSize：`b878000000c3`=0x78；CI 6C4310 `6a78`→new；grade 不变 | [已证] | 同上 |
| 0054DF90 | JumpjetLocomotionClass::GetSize：`b898000000c3`=0x98；CI 6C4190 `68 98 00 00 00`→new；grade 不变 | [已证] | 同上 |
| 005B1B40 | MechLocomotionClass::GetSize：`b834000000c3`=0x34；CI 6C4D90 `6a34`→new；grade 不变 | [已证] | 同上 |
| 006635B0 | RocketLocomotionClass::GetSize：`b860000000c3`=0x60；CI 6C4490 `6a60`→new；grade 不变 | [已证] | 同上 |
| 006A42A0 | ShipLocomotionClass::GetSize：`b870000000c3`=0x70；CI 6C4F10 `6a70`→new；grade 不变 | [已证] | 同上 |
| 0071A120 | TeleportLocomotionClass::GetSize：`b84c000000c3`=0x4C；CI 6C4C10 `6a4c`→new；grade 不变 | [已证] | 同上 |
| 0072A200 | TunnelLocomotionClass::GetSize：`b83c000000c3`=0x3C；CI 6C4610 `6a3c`→new；grade 不变 | [已证] | 同上 |
| 0075CBD0 | WalkLocomotionClass::GetSize：`b83c000000c3`=0x3C；CI 6C4790 `6a3c`→new；grade 不变 | [已证] | 同上 |
| 全局 | GetSize 闭合 11/11，全部在 off0 slot9（非 slot12）；6A=10、68=1；ctor 写 canonical vtables 已记录 | [已证] | EVIDENCE/getsize_closure.txt |
| 全局 | 全 RTTI/VT 重扫 TD=988/COL=1216/VT=1214/slots=14044；AbstractType 表 74 项=0x00..0x49 | [已证] | EVIDENCE/all_rtti.txt；EVIDENCE/abstract_type_enum.txt |
| 全局 | WhatAmI：全 RTTI 锚定 B8 imm32 C3=413；enum+RTTI 语义匹配 69 类，off0 slot11=69；S11 coverage 交集=0 | [已证] | EVIDENCE/whatami_candidates.txt；EVIDENCE/candidate_census.txt |
| 全局 | S11 双通道候选普查：入口形态 B8 imm32 C3=11，非已证=0；vtable 锚定∩S11=11，非已证=0；9 条 `B8 imm C2 04 00` 是 ret 4，不合格 | [已证] | EVIDENCE/candidate_census.txt |
| 全局 | delta 校验：11 行、bad=0、重复 entry=0、重复 name=0、grade 增量=0（atlas 内 10 / 表外 1） | [已证] | EVIDENCE/validate_delta.txt；work/validate_delta.log |

## 核心数字与复算

- 盘上现值：S11 379 行、∩atlas 368、proved 29、named 358、门槛 184；合入后 proved 仍 **29/368 = 7.8804%**。复算：`python work/baseline_recompute.py > EVIDENCE/baseline_recompute.txt`。
- 真语义：GetSize 11/11 双点闭合（语义重证），WhatAmI 69 类语义成立但 0 类落在本 S11 覆盖集；可升级的非已证行 **0**。复算：`python work/rebuild_all_rtti.py` → `python work/prove_semantics.py`。
- 纪律：第 4 条双通道一为覆盖入口裸字节形态、一为全 RTTI/vtable 锚定，二者均不依赖 `function_atlas.tsv` 的 entry+size 作发现；第 5 条无站点归属推断；第 9 条基线现值与卡面一致。
- 顺序：见 `work/README.md`。