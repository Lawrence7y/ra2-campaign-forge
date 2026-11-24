拿到 1 个真名：004309D0 = Init_BeaconArt（named 19→20，达标）

# S08-N2 PROGRESS
- 卡号：S08-N2；开工：2026-11-18 16:06 +08:00；收尾：本日
- 目标：为 S08 补 1 个真名（n=22 / named=19 / proved=3，门槛 named=20）
- 交付真名：1 条（004309D0 → Init_BeaconArt），非 docs/台账通道

## 步骤与结论
1. [完成] 骨架落盘（10 分钟内）+ 读 R14_COMMON §8.5 与 CARD.md
2. [完成] ⑨ 停机核验：coverage.tsv∩atlas 复算 S08 n=22 / named(L)=19 / proved=3；3 个 sub_ 即 3 候选
3. [完成] YRpp 本地全库（2433 文件，6/8 位+大小写+raw byte）按 3 地址 grep → 0 命中
4. [完成] YRpp 上游 master（CnCNet/yrpp，2188 文件）按 3 地址 grep → 0 命中（通道①耗尽）
5. [完成] symbol_map.json：004309D0 缺席；0047EFE0/0047F250 全部 srcs=docs/re ⇒ 不可用
6. [完成] 跨项目独立源：grep.app(429 限流) → Sourcegraph → YuriPlanet/vera20k（公开 RA2:YR 重实现）命中
   - src/render/beacon_art.rs:1 等绑定 Init_BeaconArt 0x004309D0（verifiable，见 EVIDENCE）
7. [完成] ⑱ 冲突扫描（entry 地址查全库）：004309D0 无冲突；0047EFE0 OPEN（CONFLICTS.tsv:392）与本名无关
8. [完成] ⑮ 体内出现：capstone/pefile 核实 PBEACON/RDRBEACN、全局 89C474/78、caller 00687BB2 的指令偏移
9. [完成] 写 coverage_delta.tsv / UNKNOWNS.md / EVIDENCE\

## 关键证据（详见 EVIDENCE\PROOF_004309D0.md）
- 通道①(本体)：0x4309D6 push PBEACON.SHP；0x430A3A push RDRBEACN.SHP；0x430A2D/0x430A97 失败串；
  0x4309EF/0x430A53 写全局 [0x89C474]/[0x89C478]；caller 0x687BB2 call 0x4309D0
- 通道②(跨项目独立源)：github.com/YuriPlanet/vera20k src/render/beacon_art.rs:1 明文 `Init_BeaconArt 0x004309D0`；
  transitions.rs:452 `Full_Init 687BB2 -> Init_BeaconArt 4309D0`（与本体 caller 精确吻合）
- 两通道独立：本体二进制 vs 独立开源重实现，非同源；满足 §8.5 主条

## 规则遵守
- 写域仅 S08_N2\ 与 _ghidra\S08-N2\；gamemd.exe 只读
- 未建 venv / 未 pip install / 未 import 其它卡 work 代码
- 非 docs/re / re_atlas/kb / 台账作名；未用编名/占位名
