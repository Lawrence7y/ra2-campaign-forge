# W177-F · PROGRESS（真机执行卡 · 光标→占格标定）

> 卡号 W177-F｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读未改，ImageBase 0x400000，4,825,360 B）｜Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26。
> 全程只读进程内存 + 合成输入；未写内存/未注入/未改 `ra2youli\`/未联网。写域仅本卡目录。

## 开工前（逐项）
1. `LIVE_LOCK=W177-F` ✓；残留 `gamemd.exe`=0 ✓。基线 `gamemd.exe` 4,825,360 B SHA `73201CC0…F67476`（与给定逐字节一致）；`ddraw.dll` 411,648 B SHA `85E0F7D5…3B03A9`；`except.txt` 26,272 B / 2026-11-12T22:29:17.2046290Z / SHA `6907F395…`（`work/baseline_before.json`）。

## 结论表（只用三级）
| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | T1 过定标定完成：同一相机/缩放下 4 个非共线光标点放 NAPOWR，4 点最小二乘解 `origin_cx=0.008295019*sx+0.020593870*sy+86.454981`、`origin_cy=-0.008218391*sx+0.014885057*sy+62.468391`，最大残差 <0.2 格 | [已证] | `CALIBRATION.md`、`EVIDENCE/calibration.jsonl`、`calib_p{1..4}_*.jsonl` |
| 2 | 三点解对第四点外推误差达 (−1,+3) 格 ⇒ "两点/三点解必无残差"是过拟合陷阱；本卡以 4 点过定为准 | [已证] | 本次复算（`PROGRESS` 核心数字 2） |
| 3 | footprint 原点 = NAPOWR 对象 Location(`+0x9C/+0xA0`>>8) = 占据格集合的最小 (cx,cy)；NAPOWR 3×2 占 `[Ox,Ox+2]×[Oy,Oy+1]`，落格后 o1=0/o2=1，6 格全部挂 `cell+0xE4` 链 | [已证] | `EVIDENCE/calibration.jsonl` 四条 `result.occupied_cells`（各 6 格） |
| 4 | 4 段点击期高频采样 53,191–77,549/s（2.0 s/段）、distinct-frame 62–64；均覆盖 click_t=0.35 s 前后 | [已证] | `EVIDENCE/calib_p{1..4}_hifreq.jsonl` 头 + distinct-frame 复算 |
| 5 | 相机在本标定窗静止：`cam_x=cam_y=0` 于每次点击前/后；NACNST 屏幕位置跨窗不变 | [已证] | `calibration.jsonl` 的 `cam_before/preclick/postclick`、`after_p4.png` |
| 6 | 未构造出"建筑+步兵同格链"：本卡只在空地标定，T2 因目标步兵格在标定凸包外 + 鼠标全局扫描把光标留在 x=0 触发边缘滚屏/状态漂移而未取得可归因落格 | [未证] | `EVIDENCE/find_inf_cells`：player 步兵格 cx=72–86 而标定凸包 cx=104–117；`t2a_sidebar.png` 视图已平移 |
| 7 | 引擎 hover 格全局：静态回溯 `0x43F2A7`/`0x44947B` 的 `0x5657A0` 入参来自栈临时 CellStruct，非直接全局；差分内存扫 `0x87F000..0x88F000` 得 16 个候选 change（如 `0x88095C`/`0x880CC4`/`0x880CC8`），**未确认**哪个是 hover 格全局 | [未证] | `work/disas_getcell_calls.txt`、`work/find_mouse_global.py`、`work/mouse_scan_changes.json` |
| 8 | `0x47C620` 拒集 {6 Building,0x24 Terrain,2 Aircraft}、15/1 不比较（审计更正）；`0x43F180` 双层格循环 `call 0x47C620 → test al,al; je 中止`；跨类共链（Unit+2×Infantry）已见于 W177-E try5 | [静态推断] | a-W177-E `VERDICT.md`（本卡未独立复验字节，仅引用审计） |

## 核心数字（给审计，可独立复算）
- **标定残差 <0.2 格**：`calibration.jsonl` 四行 `(screen, result.occupied_cells[0])` 代入 `CALIBRATION.md` 的 LS 式；复算 `python -c "import json;[print(r['screen'],r['result'][list(r['result'])[0]]['location_cell']) for r in map(json.loads,open('EVIDENCE/calibration.jsonl'))]"`。
- **三点外推失败**：p1/p2/p3 解在 p4=(1600,450) 预测 (108,59)、实测 (109,56)，误差 (−1,+3) 格；4 点 LS 后四残差各 <0.2 格。复算见 `CALIBRATION.md` §2 脚注。
- **采样率 53,191–77,549/s、distinct-frame 62–64**：`calib_p1_hifreq.jsonl` 头 `n=106383, rate=53190.6`，逐行第 2 列 distinct=63。复算：读每行 `[1]` 去重计数。
- **成功构造 0 次**：本卡 4 次落格均为空地 NAPOWR（无步兵同格）；T2 未取得可归因落格。复算：`calibration.jsonl` 各 `result.*.occupied_cells` 无 InfantryClass 节点。

## 卡在哪一步（T4）
T1 标定**已完成**（过定、残差 <0.2 格）。T2 **未构造成功**，卡在目标格命中之前：目标步兵格 cx=72–86 落在标定凸包（cx=104–117）之外，线性外推给出负 sy（屏外）；鼠标全局扫描把光标停在屏幕左缘 x=0，触发 RA2 边缘滚屏，视图与侧栏 tab 漂移，后续 T2 点击未命中同一相机态。**未证 ≠ 不可能**：字节路径（拒集不含 15/1、跨类共链已见）仍开放；下一步应先恢复固定相机、用 hover 格全局（或 1×1 探针）在目标格附近就地重标定再闭环放置。

## 措辞（③ 三分句，不合并）
静态允许（已证字节，拒集不含 15/1）+ 运行时未兑现（本卡 0 次、W177-E 0/5）+ 路径未被证伪（跨类共链已见、缺受控静止命中）。

## 真机收尾
真机收尾：进程已关闭 / except.txt 未变（26,272 B、2026-11-12T22:29:17.2046290Z、SHA `6907F395…` 与开工前逐字节一致）/ 无残留 gamemd.exe。本卡只启动并关闭自身 pid 3108（Stop-Process，关闭前核对 Path=`ra2youli\gamemd.exe`）；gamemd.exe `73201CC0…F67476`、ddraw.dll `85E0F7D5…3B03A9` SHA 前后不变。证据 `work/baseline_before.json`、`work/baseline_end.json`。现把 `LIVE_LOCK` 置为 `RELEASED by W177-F`。
