# W177-KA · PROGRESS.md

> 卡号 W177-KA｜输入只读 `lead\next_re_20261117_r14\W177-J\`｜本卡全程离线：未启动游戏、未读进程内存、未合成输入、未 import `W177-J\work\branch_recompute.py`｜目标 `gamemd.exe` SHA-256 `73201CC0…F67476`（本卡重算同值，见 `EVIDENCE\ka_47c620_disasm.txt` 首行）｜分级仅 [已证]/[静态推断]/[未证]。

## 结论表
| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | JSONL 实解 24,828 行、0 坏行；7 个标志/全局地址字段 24,828/24,828 全覆盖；时间戳差分中位数 49 µs ⇒ 20,408.2/s（j_run 的 15,517.5/s 是均值口径，非中位数） | [已证] | `EVIDENCE\ka_flag_samples_stats.txt`；`work\ka_parse_samples.py` |
| 2 | 采样窗内取值恒定：arg2+16BF/16BE/16B7/E58 = {0}，A8E9A0={1}，A8E7AC={0}，A8ED6B={0}；悬停→点击窗（t≤0.250017，4,711 样本含点击样本）完全相同 | [已证] | 同上；点击样本 idx=4710 t=0.250017 frame=677 |
| 3 | j_run 与 run_checkpoint 逐字节相同；成功进局（nav_done=true, ingame_frame=30, player_house=0x10d7bbd8），下单成功（10000→9978，player_napowr limbo o1_81=1），拿起 ghost 成功，闭环定位成功（iters=3，hover 113,62；target 113,63） | [已证] | `..\W177-J\EVIDENCE\j_run.json`；`EVIDENCE\ka_run_fields.txt` |
| 4 | 落格失败：landing.main_ok=false、has_building=false、headA=0x157559a8 lenA=3 且 rttiA=3×InfantryClass、ghost_o1_after=1、credits 9400→9400（无退款） | [已证] | `..\W177-J\EVIDENCE\j_run.json`；JSONL；`EVIDENCE\ka_run_fields.txt` |
| 5 | arg2 = [ghost+0x520] = 0x102f7090，RTTI=`.?AVBuildingTypeClass@@`；owner=0x10d7bbd8 RTTI=`.?AVHouseClass@@`；两对象四标志均 0 ⇒ P0_GATE_B U2 的「HouseClass*」静态猜测被真机 RTTI 推翻（台账 §678 早已定 +0x520=BuildingTypeClass） | [已证] | `..\W177-J\EVIDENCE\j_run.json` ghost_arg2_ident；`DISAGREE.md` D1 |
| 6 | 字节级独立重解 0x47C620 分支表成立；0x47C738/0x47C805 两处传选择子 0（0x47C3D0 的 [ebp+0xC] 来自调用方 push ebp=0，ebp 唯一真定义 xor@0x47C62A） | [已证] | `EVIDENCE\ka_47c620_disasm.txt`；`EVIDENCE\ka_47c3d0_prologue.txt` |
| 7 | 依实测四标志全 0 + A8E9A0=1 + A8E7AC=0 ⇒ 走 0x47C738 闸（all-four-flags-zero path）；「该闸实际拒」未直接观测（无 EIP/al/返回点读数） | [静态推断] | `EVIDENCE\ka_47c620_disasm.txt`；`..\W177-J\EVIDENCE\branch_recompute.txt` |
| 8 | 采样存在 281 ms 空洞（frame 677 仅 16 样本后跳到 frame 685）；20.4 kHz 不足以抓 µs 级闸门命中或 <49 µs 帧内翻转，不能据此下「零翻转」结论（错源⑨/⑩） | [已证]（空洞/速率）· [未证]（翻转） | `EVIDENCE\ka_flag_samples_stats.txt` |
| 9 | PNG 辅助：j_hover_anchor 与 j_after_click 目标框绿/红比例逐值相同（0.3755/0.0902）；无同一帧无-ghost 基线，颜色不得判 can-place 放行/拒绝（错源⑫） | [已证]（像素统计）· [未证]（机制） | `EVIDENCE\ka_png_aux.txt` |
| 10 | 闭合 ②-b 仍需一次事件驱动的闸内观测（0x47C853 / 0x47C738 的 EIP 与返回 al/eax）；当前「只读 RPM + 只读上下文、无软断点/无 Hook」授权下做不到 | [静态推断] | `SALVAGE.md` §3；台账 §994 |

## 给审计员的核心数字（可独立复算）
1. **(a)** 样本 **24,828**；标志/全局目标地址 **7** 个（arg2+0x16BF/+0x16BE/+0x16B7/+0xE58、0xA8E9A0、0xA8E7AC、0xA8ED6B；另 8 项派生观测量）；**采样率中位数 20,408.2/s**（dt 中位数 0.000049 s；均值口径 15,517.6/s）。复算 `python work\ka_parse_samples.py`。
2. **(b)** 7 字段全出现；取值集合 `16BF={0},16BE={0},16B7={0},E58={0},A8E9A0={1},A8E7AC={0},A8ED6B={0}`；悬停→点击窗同值。复算同上。
3. **(c)** 落格判定字段 `landing.main_ok=false, has_building=false, lenA=3, ghost_o1_after=1, credits_end=9400`（预点击 9400，无退款）。复算 `python work\ka_run_fields.py`。

## 停机核验
- 样本数/click_frame/landing 与 j_run 及 branch_recompute.txt 一致；中位数速率与 j_run 均值速率定义不同，已双列，未凑数。
- 静态分支表由 pefile+capstone(skipdata=True) 从镜像字节独立重解，未依赖 branch_recompute.py 或 function_atlas.tsv。
- 本卡只写 `W177_KA\`；未改 `W177-J\`、`COVERAGE\coverage.tsv`、`ra2youli\`、台账；未 git commit。`coverage_delta.tsv` 为 0 行（无新增入口）。
