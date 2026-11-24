# W177-D · PROGRESS（真机执行卡 · ②-b 唯一剩余硬缺口）

> 卡号 W177-D｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读未改）｜ImageBase 0x400000
> 目标：刻意构造「同一格链长≥2」（建造重叠），或证明不可构造。全程只读内存+合成输入；未写内存/未注入/未改 ra2youli。

## 开工前检查（逐项）
1. LIVE_LOCK=`W177-D` ✓；残留 gamemd.exe=0 ✓。基线 except.txt 26,272 B / 2026-11-13T06:29:17.2046290+08 / SHA 6907F395…；gamemd `73201CC0…F67476`（4,825,360 B）；ddraw `85E0F7D5…3B03A9`。证据 `work/baseline_start.txt`。
2. 环境 Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26 ✓。R14_COMMON §1/2/5/6/7、STATUS_BOARD、W177-C/B/live_place PROGRESS/LIVE、w165_probe2.py 已读（只读）。RTTI 读器静态自检 BuildingClass vt=0x7E3EBC→COL=0x7fc360→TD=0x818d60→`.?AVBuildingClass@@` ✓（`EVIDENCE/rtti_static.txt`）。

## 结论表
| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | **建造重叠（建筑-建筑同格）未构造成功**：本卡及 W177-C 均无任何建筑-建筑同格实例；本卡全局扫描到的链≥2 全是 InfantryClass（移动中的敌/我步兵），非放置产生 | [已证·本卡] | `EVIDENCE/scan_all_cells_01.txt`、`scan_detail_1/2/3.jsonl`、`infantry_stack_detail_1/2.jsonl` |
| 2 | `0xA8E7AC=0`、`0xA8E9A0=1`、`0xA8ED6B=0`（整个观测窗恒定）⇒ 逐格校验 `0x47C620` 全开、无静态旁路（S12-K2 线索 #11/#12 均未触发）。高频验证：稳态 6 s/409,708 样本（68k/s）+ MCV 部署（真实放置，玩家建筑 0→1）期间 4.36 s/1,767 样本，三值均 **0 跳变** | [已证] | `EVIDENCE/state_bypass_final.jsonl`、`globs_hifreq.jsonl`、`globs_hifreq_deploy.jsonl` |
| 3 | 全部 BuildingClass(92)/InfantryClass(62)/UnitClass(68) 的 `+0x8C=0` ⇒ 全走 head A(`+0xE4`)；head B(`+0xE8`) 对可放置对象恒空，S12-K2 的「head B 绕过」路径不可用 | [已证] | `EVIDENCE/state_bypass_final.jsonl` |
| 4 | 多格建筑挂入其 footprint **所有** 格：NACNST(64,19) 3×3 挂 (64-66,19-21)；NAPOWR(60,24) 挂 (60-62,24-25) ⇒ 部分相交也会被 can-place 的逐格扫描命中 | [已证] | `EVIDENCE/footprint_multicell.jsonl` |
| 5 | 链≥2 在引擎中可达但仅见于步兵：例 cell(48,89) lenA=3，三对象 `0x1568a1f8/0x1568cc28/0x156a7520`，RTTI `.?AVInfantryClass@@`，owner `0x10d66df8`，layer=2，+0x8C=0；两帧(40506→40567,1s)节点集完全相同 | [已证] | `EVIDENCE/infantry_stack_detail_1.jsonl`、`_2.jsonl` |
| 6 | 步兵链≥2 非「稳定≥3s」：定点 0.6s×7 验证时该批单位已移走（frame 40506→42492），目标格链归 0；同格「链≥2」可跨 6 次扫描但节点不断轮换 ⇒ 不作成功判据 | [已证] | `EVIDENCE/stable_target_verify.jsonl`、`stable_track_full.jsonl` |
| 7 | 本卡受控放置（wc_place_v2）下单扣款后 pickup 成功，但候选点 NO_PURE_GREEN（相机 auto-scroll + 侧栏切页），未取得新的可归因建筑放置样本；沿用 W177-C §959 的 10/12 成功与 3 次拒绝为真阴性底座 | [已证] | `EVIDENCE/A_auto*.jsonl`(W177-C)、本卡 `work/wc_place_v2.py` |
| 8 | RTTI 严格 COL+0xC→TD+8 在本镜像可用；建筑只有单一 BuildingClass RTTI（非按型号分类），型号走 type+0x24 短 ID | [已证] | `EVIDENCE/rtti_static.txt`、`work/dsnap.py` |

## 核心数字（给审计，可独立复算）
- **旁路开关三元组 `0/1/0` 高频零跳变**：稳态 409,708 样本/6 s（68,285/s，frame 1225→1411）+ MCV 部署期 1,767 样本/4.36 s，A8E7AC≡0 / A8E9A0≡1 / A8ED6B≡0，transitions=0/0/0。复算：`python work/hifreq_globs.py` / `work/hifreq_deploy.py`，读 `EVIDENCE/globs_hifreq*.jsonl` 每行第3/4/5列逐行 diff。
- **链选择位 `+0x8C=0` 比例 = 222/222**（Building92+Infantry62+Unit68）。复算：`EVIDENCE/state_bypass_final.jsonl` 的 `chainbit_8C_dist`；或 `work/dsnap.py node_detail()`。⇒ head B 绕过对可放置对象不可用。
- **链≥2 实例全图计数**：一次全图扫描链≥2 的格 = 4（早期帧）→ 逐帧移动；节点 RTTI 100% InfantryClass，0 个 BuildingClass。复算：`python work/scan_detail.py`（输出每格完整节点+JSONL）。

## 卡在哪一步
被拒/checkpoint：`can-place [vptr+0x1AC]`（0x43F218/0x43F678 两处）→ `0x47C620` 逐格扫 head A（WhatAmI 6/0x24 拒）→ 占用格拒绝、保持 limbo。本卡观测三开关全开、+0x8C 全 0、footprint 全格挂链，与 W177-C 拒绝态真阴性一致。**没有可写内存/注入的旁路操作被授权**，无法从运行中制造 head-B 对象或翻转开关。路径 A/B/C/E/F 因 ghost/相机控制与无 UI 改地形手段未能取得可归因样本（如实记，未凑数）。

## 真机收尾
真机收尾：进程已关闭 / except.txt 未变（26,272 B、mtime 2026-11-13T06:29:17.2046290+08、SHA 6907F395… 与开工前逐字节一致）/ 无残留 gamemd.exe。本卡仅启动并关闭自身两个 pid（10724、9984，均 Stop-Process）；gamemd.exe `73201CC0…F67476`、ddraw.dll `85E0F7D5…3B03A9` SHA-256 前后不变。证据 `work/baseline_end.txt`。现把 LIVE_LOCK 置为 `RELEASED by W177-D`。
