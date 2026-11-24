# S10-K15 PROGRESS（≤60 行）
卡号 S10-K15；只读目标 ra2youli\gamemd.exe（SHA-256 73201CC0…F67476 现场复算一致）；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra。
## 现场基线（2026-11-18T07:18:51+08:00 读盘；统一大小写；grade 只读第 5 列）
COV sha=4B243580…C42C4F size=3,660,997 mtime=07:02:11+08；ATL sha=4527079B…53DB69。S10 528 行、∩atlas 526、表外 2；[已证]114/[静态推断]399/[未证]13 ⇒ 114/526=21.6730%，门槛 263，差 149；named_L/S=513/526=97.5285%。与卡面基线一致。证据 EVIDENCE/BASELINE.txt。
## 视角产出（如实）
1. TechnoClass 火力/冷却核心：0 行。006FB010（StartReloading 上游）仍缺外部枚举锚点，不重复 K13 已否决路径；006FB740（slot260 状态机）虽有 push1/2、+0x220/+0x224/+0x228/+0x22C 写与 RandomRanged/ControlledByHuman，但环①只是内部 stage 值、无盘上已证外部枚举，未交。扫描同簇相邻槽 261/262 发现真正的 area-visibility 计数器开关对，得下列 2 行（属技能簇外溢，不冒充火力语义）。
2. BuildingClass 生产/排队：0 行。S10 非已证行中直调 FactoryClass::DemandProduction/AbandonProduction/CompletedProduction/StartProduction 命中均为 0；避开 KICKOFF 点名的 0x43F180/0x47C620/0x47C3D0 及其调用者（②-b 已做）。
3. HouseClass 经济：0 行。004D9F70/00519630/00739EC0 直调 HouseClass::GiveMoney，但 004D9F70 无自身字段写（环②不足），另两行无外部直接 caller，且都不能补独立环①，未交。
4. Scatter/Guard/Hunt 命令入口：0 行。S10 非已证行无 Scatter/Hunt 名称或外部命令类派发锚点；Guard 命中仅 MissionClass 桩（K9 已清）和 S09 CommandClass（非 S10）；未重挖 K6/K8 的 QueueMission v[122] 家族。
## 交付 2 行（9 列；behavioral；conflict=0；n_sources=4；均为[静态推断]）
- 006FB170 → TechnoClass::EnableAreaVisibilityCounterRefresh_behavior：环① caller 0044D880 [已证] 在 [v+0x414] 调度且 body 把 [this+0x269] 0→1；环②写 +0x269/+0x26C 与 map cell +0x130/+0x134/+0x12C/+0x13C；环③ 5 个外部 vcall caller（含 0044D880 [已证]）；环④ 005657A0/0050B6F0/004F9A50/00657CE0/004F42F0 全盘面 [已证]。
- 006FB470 → TechnoClass::DisableAreaVisibilityCounterRefresh_behavior：环① caller 00452480 BuildingClass::DisableStuff [已证] 以 [this+0x269] 为门控并在 [v+0x418] 调度，body 把该标志 1→0；环②写 +0x269/+0x26C 与 map cell +0x134/+0x130/+0x12C；环③ 6 个外部 vcall caller（含 0044D880/00452480 [已证]）；环④ 00657CE0/004F42F0/005657A0/0050B6F0/004F9A50 全盘面 [已证]。
## 类归属与双通道
RTTI 链 COL=vt-4 → TD=u32(COL+0xC) → TD+8 内联类名：两行均在 Techno/Aircraft/Foot/Infantry/Unit/Building 六类同 slot（261/262），无子类覆盖版直调 ⇒ 归基类 TechnoClass 级，覆盖表 AircraftClass::slot 名只作定位。通道 A=手工 pefile 节表+capstone 逐指令解码；通道 B=裸字节模式查 c6866902000001/c6866902000000 与 E8 rel32 目标；两通道不依赖同一 atlas entry+size 字段（B 仅用区间做输出切片）。
## 结算
本次只交 [静态推断] 2 行，不增加 proved；模拟非零增量只到 named_L/S 513→515。delta 行数/列数/锚点/唯一性见 EVIDENCE/DELTA_VALIDATE.txt。未写台账、未改游戏文件、未 git commit。