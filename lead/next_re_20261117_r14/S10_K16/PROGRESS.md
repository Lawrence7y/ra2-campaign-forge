# S10-K16 PROGRESS（≤60 行）
卡号 S10-K16；目标 ra2youli\gamemd.exe 只读复算 SHA-256 73201CC0…F67476；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；未用 Ghidra。
## 现场基线（2026-11-18T07:43:09+08:00 读盘；大小写归一；grade 只读第 5 列）
EXE size=4,825,360；COV sha=4B243580…C42C4F size=3,660,997 mtime=07:02:11+08；ATL sha=4527079B…A73653DB69。S10 528 行、∩atlas 526、表外 2；[已证]114/[静态推断]399/[未证]13 ⇒ 114/526=21.6730%，门槛 263，差 149；named_L/S=513/526=97.5285%。证据 EVIDENCE/BASELINE.txt，与卡面一致。
## 本轮四视角
1. TechnoClass +0x269 邻居槽：3 行。slot259=00701410、slot263=0070B570、slot264=006F4EB0；slot260 按 K15 已否决的内部 stage 值不重复，slot265 按 K13 环①不足不重复。
2. ObjectClass/AbstractClass 一次性实现：0 行。S10∩atlas 中 5 行含 Object/Abstract 字样，盘面全 [已证]；无非已证行可交。
3. owner/house 变更链：1 行，即 slot259 00701410。007014A0=TechnoClass::SetOwner 已 [已证] 且 S05，未碰；0x701000–0x701FFF 其余 S10 非已证缺独立环④或与 slot259 同源，按 R14-R17 不另交。
4. BulletClass/AnimClass 接口：0 行。仅命中 005F5E80（vslot5 析构族，K5/K8 已穷尽）与 00754BE0（21B rep movsd 模板复制，无 vt/字段语义，不能构成严格 behavioral 类名）。
## 交付 3 行（9 列；全部 [静态推断]；name_kind=behavioral；conflict=0；n_sources=3）
- 00701410 / TechnoClass::TypeSoundCacheAndConditionalAudio_behavior：六类同槽 259；body 写 +0x6C/+0x70=[v+0x84]->+0xA0；外部 00519630 读同对且不等时 vcall [v+0x40C]；环④ 007509E0 VocClass::PlayAt [已证]。
- 0070B570 / TechnoClass::ClampAndAdvancePairedFloatState_behavior：六类同槽 263；body 成对写 +0x328/+0x32C/+0x330/+0x334 并 clamp；外部 [已证] 006F9E50 双门控唯一 vcall [v+0x41C]；环④ 004C93D0 [已证]。
- 006F4EB0 / TechnoClass::Mode2NearbyObjectListRefresh_behavior：六类同槽 264；body +0x220==2 / owner!=全局 [0xA83D4C] 门控并建邻近对象栈表；外部 [已证] 006F9E50 两处 mode/cell 门控 vcall [v+0x420]；环④ 005657A0、007C8B3D [已证]。
## 判据与双通道
RTTI：COL=vt-4 → TD=u32(COL+0xC) → TD+8 内联类名；三行均在六类同槽共享、无派生同槽覆盖版 ⇒ 归 TechnoClass 级。环①引用地址均在 body 或明示外部 caller 位置真出现；环④全部数过 call 目标且盘面第 5 列 [已证]，均在 batch 外；同一外部证明不跨环双计。
通道 A=手工 pefile 节表+capstone 逐指令；通道 B=裸字节模式/rel32/vtable dword 复查，三份 PROOF 的 raw@ 检查 match=True，且 B 不依赖 atlas entry+size（仅输出切片用 atlas）。
## 结算
EVIDENCE/DELTA_VALIDATE.txt：rows=3、cols={9}、entry/name 唯一、无占位名、anchors 存在、ring4 called+grade=PASS。模拟合入：proved 仍 114/526=21.6730%，差 149；named_L/S 513→516/526=98.0989%。未写台账、未改游戏文件、未 git commit。
## 证据
EVIDENCE/BASELINE.txt、PROOF_00701410.txt、PROOF_0070B570.txt、PROOF_006F4EB0.txt、ANGLE_SUMMARY.txt、NEIGHBOR_VCALLS.txt、ANGLE24_SCAN.txt、SET_OWNER_NEIGHBORS.txt、VTSLOT_LIST.txt、DELTA_VALIDATE.txt；work/ 存全部脚本与原始扫描。
