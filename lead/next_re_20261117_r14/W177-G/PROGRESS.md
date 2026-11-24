# W177-G · PROGRESS（真机执行卡 · 引擎鼠标所在格全局）

> 卡号 W177-G｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读未改，ImageBase 0x400000，4,825,360 B）｜Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26。
> 全程只读进程内存（ReadProcessMemory）+ 合成鼠标/键盘输入；未写内存/未注入/未改 `ra2youli\`/未联网。写域仅本卡目录。

## 开工前
`LIVE_LOCK=W177-G` ✓；残留 `gamemd.exe`=0 ✓。`gamemd.exe` SHA `73201CC0…F67476`、`ddraw.dll` SHA `85E0F7D5…3B03A9`、`except.txt` 26,272 B / 2026-11-13T06:29:17+08:00 / SHA `6907F395…`（`work/baseline_before.json`）。本卡仅启动自身 pid 32280。

## 结论表（三级分级）
| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | **引擎鼠标所在格全局 = `0x0088095C`**，dword(4B)，编码 packed CellStruct `{X:uint16 lo, Y:uint16 hi}` = `(Y<<16)\|X`，非 `(Y<<9)+X`。读它即得光标格 ⇒ 格空间闭环、无需标定 | [已证] | `HOVER_CELL.md`；`EVIDENCE/t1a_v1_verify.json`（26 点细步进，26/26 取格 MapCoords 自洽）|
| 2 | 动态：细步进中 X 37→43（下右）、Y 80→89（下左）呈阶梯，回中精确复位 `0x00500025`；相机全程 `0x886FA0/4=(0,0)`，位置离边 ≥200px 无滚屏 | [已证] | `EVIDENCE/t1a_v1_verify.json`、`t1a_k10_scan.json` |
| 3 | 静态链：`0x4FB3BC mov [0x88095C],edx`（每帧写）；`0x6DBEB2 mov ecx,[0x88095C]`→`0x6DBECB call 0x5657A0`（GetCellAt，this=0x87F7E8）；`0x4AACEC cmp ax,word[0x88095E]`（逐字读 X/Y）。`.text` 立即数裸字节命中 12 处 | [已证] | `work/t1a_xref.py`、`t1a_xref2.py` |
| 4 | 附：鼠标**像素**全局 `0x00B0CBF8`=X、`0x00B0CBFC`/`0x00B0563C`=Y（逻辑像素=物理/1.875），非格全局 | [已证] | `EVIDENCE/t1a_k10_changes.json`（693/964/318、320/469/471 线性跟踪）|
| 5 | 闭环定位：用 `0x88095C` 作反馈，3 次迭代把光标精确落到任意目标格（如 (35,85)），相机不动、无标定 | [已证] | `EVIDENCE/goto_35_85.json`、`work/goto_cell.py` |
| 6 | T3 采样：try1 165,640 样本 / 75,290/s / distinct-frames=69（2.2 s 窗，click_t=0.4 s，全程 hover 锁定目标格、cam=(0,0)）；1 帧即无效的门槛满足 | [已证] | `EVIDENCE/t2_try1_hifreq.jsonl` 头 + 逐行复算 |
| 7 | 建筑放置机制在偏移锚点下可用：NAPOWR `o1=0/o2=1` 落格，3×2 足迹格挂 BuildingClass 节点（RTTI 定名）| [已证] | `EVIDENCE/offset_off1.json`、`final_final1.json` |
| 8 | **成功构造建筑+步兵同格链：0 次**。放置按钮显绿但锚点格（有步兵）为红/被拒；改偏移锚点后建筑落在相邻格，而步兵带活动命令持续漂移（(32,79)→(30,79)），无法在目标格上锁定 ≥2 节点 | [未证] | `EVIDENCE/decisive_d1_hover.png`（绿足迹+红锚点）、`decisive_d1.json`、`final_final1.json` |

## 核心数字（给审计，可独立复算）
1. **26/26**：`EVIDENCE/t1a_v1_verify.json` 每行 `X_lo/Y_hi` 等于 `cell_check.mapcx/mapcy`。复算：`python -c "import json;[print(r['X_lo'],r['Y_hi'],r['cell_check']['mapcx'],r['cell_check']['mapcy']) for r in json.load(open('EVIDENCE/t1a_v1_verify.json'))['rows']]"`。
2. **直接喂给 GetCellAt 的 1 条指令**：`work/t1a_xref2.py` 输出 `0x006DBECB call 0x5657a0`，其上游 `0x006DBEB2 mov ecx,[0x88095C]`。复算：`python work/t1a_xref2.py`（只读磁盘反汇编）。
3. **75,290/s、distinct=69**：`EVIDENCE/t2_try1_hifreq.jsonl` 头；复算：读每行 `[1]` 去重计数、`len/n_wall`。

## 卡在哪一步（T4：诚实定位）
T1a **完成**（hover 全局已证，格空间闭环成立）。T2 **未构造成功**，卡在两点：① 目标锚点格（有步兵）在 ghost 足迹中显红 ⇒ 被放置校验拒绝（尽管 `0x47C620` 字节层不比较 WhatAmI 15，另有上游 can-place 检查，如 `0x43F218` vcall，本卡未逐字节定位到具体那条）；② 偏移锚点能落建筑，但步兵有活动命令持续漂移，读回时已离开目标格 ⇒ 无法取得"同格 ≥2 且含 BuildingClass"的稳定终态。颜色判据按审计只作辅助、落格以链 RTTI 回读为准。

## 措辞（三分句，不合并）
静态允许（已证字节：`0x47C620` 拒集 {6,0x24,2}，15/1 一次未比较）+ 运行时未兑现（本卡 0 次，建筑在相邻格落、步兵漂移）+ 路径未被证伪（跨类共格链已见 W177-E try5，缺受控静止同格命中）。

## 真机收尾
真机收尾：无残留 gamemd.exe（收尾核查 count=0；本卡唯一启动 pid 32280，收尾时该 pid 已不在，未发现需主动 Stop-Process 的本卡进程）/ except.txt 未变（26,272 B、2026-11-13T06:29:17.2046290+08:00、SHA `6907F395…` 与开工前逐字节一致）/ gamemd `73201CC0…F67476`、ddraw `85E0F7D5…3B03A9` SHA 前后不变。证据 `work/baseline_before.json` + 收尾 SHA 复核。未写内存/未注入/未改 `ra2youli\`/未联网。现把 `LIVE_LOCK` 置为 `RELEASED by W177-G`。
