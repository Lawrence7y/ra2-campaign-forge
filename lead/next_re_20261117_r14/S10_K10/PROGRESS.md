# S10-K10 PROGRESS（≤60 行）
卡号 S10-K10；目标 ra2youli/gamemd.exe SHA 73201CC0...F67476 只读；Python 3.12.10 + capstone 5.0.7(skipdata=True) + pefile 2024.8.26；无 Ghidra。成稿 2026-11-18T05:35+08。
## 现场基线（只读第 5 列；统一大小写）
2026-11-18T05:23:49+08 读盘：coverage.tsv 3656689B SHA 9EF239C2...EC94；atlas 4527079B...DB69。S10 528 行、∩atlas 526、表外 2；盘面 [已证] 107/526=20.3422%，门槛 263，差 156。派卡 112 = 盘面 107 + S10-K9 五行拟议增量；本卡只读不改账，按有效 112 结算。证据 EVIDENCE/BASELINE_K10.txt、BASELINE_DISCREPANCY.txt。
## 本轮视角与得行
1. Deployment/Enter/Load/Unload/Repair 非 mission 状态机：0 行。按 K8F 判据扫状态字段写 + 动作调用；高信号 004DBED0 缺独立枚举/INI 环，006FB010 只有哨兵常量，均失败关闭。
2. 路径/目标相关 SetDestination/MoveTo/Scatter/GuardArea：2 行。全量扫 419 条 S10 非已证行的字段写/调用/字符串，再对 61 条有直接调用者者逐字节展开；006FCDB0 与 004D8FB0 四环齐全。
3. TechnoClass 属性读写：0 新增。004D8FB0 计入视角 2，不重复；其它成对读字段函数缺环③或环①。
4. INI 驱动/静态键串：0 行。S10 候选只发现 EVA_UnitSold、EVA_UnitLost、Tip:Rocket/MachineGun/Repair、POD.SHP 等运行期/UI 串，没有逐键 INI push；不把 UI 串冒充 INI 键。
5. 不重复 K9：排除 0051D6F0/0051DAF0/0051B1F0/0051BAB0/00522340；本轮 2 行均为新 entry。
## 交付 2 行（n_sources=4, conflict=0, name_kind=behavioral）
006FCDB0 TechnoClass::AssignOrClearTargetAndNotifySpawnManager_behavior；004D8FB0 FootClass::ResolveTargetCellAndCacheDescriptor_behavior。
四环锚点见 EVIDENCE/PROOF_R14.txt；逐函数反汇编/调用者见 DISASM_006FCDB0.txt、DISASM_004D8FB0.txt、DISASM_006B7B90.txt、DISASM_006F4AB0.txt；候选扫描见 CANDIDATE_SCAN.tsv、DIRECT_CALLERS_SCAN.tsv。
## 结算
盘面 107 → 109/526=20.7224%（若只看本卡 delta）；有效基线 112 → 114/526=21.6749%，门槛仍差 149。均不写台账。
校验：coverage_delta.tsv 2 行/9 列；entry 唯一、name 唯一、0 placeholder；证据路径存在；字段偏移只进 semantics，不进 name。EVIDENCE/DELTA_VALIDATE_R14.txt。
未写台账、未改游戏文件、未 git commit。
