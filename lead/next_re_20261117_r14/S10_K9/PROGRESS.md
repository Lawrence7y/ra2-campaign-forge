# S10-K9 PROGRESS（≤60 行）
卡号 S10-K9；目标 ra2youli/gamemd.exe SHA-256 73201CC0…F67476，只读；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile，无 Ghidra。成稿 2026-11-18T05:16+08。
## 现场基线（只读第 5 列）
coverage.tsv 3656689B / mtime 05:01:54.340186+08 / SHA 9EF239C2…EC94；atlas 12916 行 SHA 4527079B…DB69。
S10 528 行、∩atlas 526、表外 2；grade 第 5 列实测 [已证] 107 / [静态推断] 406 / [未证] 13。proved 107/526=20.3422%，门槛 263，差 156；与卡面 proved 完全一致。证据 EVIDENCE/BASELINE_K9.txt。
卡面 named_L=511 与当前 name 列复算 513 不一致；本卡按派卡要求只用第 5 列做 grade 基线，未据此停机改账，见 DISAGREE.md。
## 本轮方向 / 得行
1. MissionClass::Update 骨架（005B3060）与 19 条 Mission_* 定时器桩：0 行。骨架本身已 [已证]；桩仅返回 0x1C2，字段写由调用者完成，缺环②（本函数自身写字段），按四环不升。
2. Aircraft/Unit/Building/Foot mission vslot（129..156）：0 行。48 条已在 coverage.tsv 为 [已证]，无新增可证行；不重复 K6/K8F。
3. MissionControl/LoadFromINI/Save/Find 一带：0 行。005B3700/3760/3910/3970 已 [已证]；005F5E80 仅有运行期段键 0xB0C110（文件 raw 外），无静态 INI 键串，失败关闭。
4. 旧 QueueMission +0x1E8 家族：0 行。按 K6/K8F 已扫结论不重挖；本卡 5 行均走 InfantryClass +0x558 mission-state setter，不是同一家族重复。
5. InfantryClass mission-state 状态机（新建方向）：5 行。先全扫 419 条 S10 非已证行的字符串/直接调用/虚调用/字段写特征；再逐字节展开 +0x558/+0x500/+0x3C8/+0x53C 候选及调用者。
## 交付的 5 行（均 behavioral，conflict=0，n_sources=4）
0051D6F0 SetMissionStateFromArgument_behavior；0051DAF0 StopAfterAirborneMissionState_behavior；0051B1F0 RetargetWithMissionFallback_behavior；0051BAB0 ClearRetargetFlagAndRestoreMission_behavior；00522340 ApplyOccupantTargetMissionFallback_behavior。
共同四环：①0x816CAC mission 名表 + YRpp Mission 枚举（27..31）与函数内 0x1B..0x1F 常量；②各行自身字段写（如 +0x6C4/+0x6DC/+0x68D/+0x68E/+0x6E4/+0x5E0/+0x2A8）；③真实调用者实参（00521760 push 0/1/0x21；0051DAA1、0051BBEF、004DAEF3、004D473A 的 ecx=this 与 0/目标参）；④被调字节语义（+0x558→0051D6F0 写 mission-state；StopMoving 004D55C0；005B3A00；RandomRanged）。
R14-R17：name/semantics 不是 vslot 归属；vtable+RTTI 只负责定位/类属，环①枚举、环②自写、环③调用者、环④被调语义互不共用同一证据。类名由 0x7EB058-8→COL 0x8033B8→COL+0xC→TD 0x825508→TD+8 内联串 `.?AVInfantryClass@@` 读出。
## 结算与校验
模拟 proved 107→112/526=21.2928%，门槛仍差 151；named_S 按当前盘面 513→518（strict 71→76）。delta 5 行/9 列，entry/name 唯一，0 placeholder，证据锚点全命中：EVIDENCE/DELTA_VALIDATE.txt。
证据：BASELINE_K9.txt、MISSION_STATE_PROOF.txt、CANDIDATE_DISASM.txt、INFANTRY_STATE_CANDIDATES.txt、FIELD_XREFS.txt、VIRTUAL_CALLERS.txt；脚本 work/。未写台账、未改游戏文件、未 git commit。
