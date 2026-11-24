# W177-E · PROGRESS（真机执行卡 · 建筑落步兵格）

> 卡号 W177-E｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读未改，ImageBase 0x400000，4,825,360 B）｜工具 Python 3.12.10 / capstone 5.0.7 / pefile 2024.8.26。
> 全程只读进程内存 + 合成输入；未写内存/未注入/未改 `ra2youli\`/未联网。写域仅本卡目录。

## 开工前（逐项）
1. `LIVE_LOCK=W177-E` ✓；残留 `gamemd.exe`=0 ✓。基线 `gamemd.exe` 4,825,360 B / SHA `73201CC0…F67476`；`ddraw.dll` 411,648 B / SHA `85E0F7D5…3B03A9`；`except.txt` 26,272 B / 2026-11-12T22:29:17.2046290Z / SHA `6907F395…`（`work/baseline_start.txt`）。

## 结论表
| # | 结论 | 分级 | 证据 |
|---|---|---|---|
| 1 | `0x47C620` 逐格占用扫描只拒 WhatAmI==6(Building)/0x24(Terrain)；InfantryClass(15)/UnitClass(1) 不在拒绝集；全函数 0 次读 `+0xE8`、5 次读 `+0xE4`，head A=`+0xE4` | [已证] | `EVIDENCE/static_verify.txt`（`0x47C668 cmp eax,6`、`0x47C694 cmp eax,0x24`、`0x47C657/683 [edi+0xe4]`） |
| 2 | `0x47E8A0` 挂链 worker 对 WhatAmI==6 且链非空有链尾 append 分支（`0x47E8EB mov [esi+0x30],ebp` / `0x47E8EE mov [ebp+0x30],0`），只在"挂链时链已非空"才有用途 ⇒ 引擎设计预期建筑与非建筑共格链 | [静态推断] | `EVIDENCE/static_verify.txt`（`0x47E8D2 cmp eax,6`、`0x47E8D7 test esi,esi`） |
| 3 | 链长≥2/≥3 在引擎可达且由非放置对象产生：cell(48,93)/(48,97)/(48,101)/(56,97) 各 lenA=3 全 `.?AVInfantryClass@@`；cell(108,120) lenA=2；同一 `this` 跨 2.8 s 不变 | [已证] | `EVIDENCE/precondition_cells.jsonl`、`precondition_stable_inf.jsonl`、`T2_final2_result.json` |
| 4 | T1 达标：6 次放置期高频采样 11,382–28,263/s、每次 2.0 s，每行含 frame/`0xA8E7AC`/`0xA8E9A0`/`+0xE4`/`+0xE8` 头/链长/逐节点 RTTI（fail-closed `[未证]`），全量 JSONL 落盘 | [已证] | `EVIDENCE/T2_try1_48_97.jsonl`（30,351 样本）、`T2_try2..final2*_hifreq.jsonl` |
| 5 | 两步建造可用，建筑可入格链：NAPOWR 从 limbo(o1=1,o2=0) → 落格(o1=0,o2=1,cell链含该对象)，footprint 3×2 全格挂链 | [已证] | `EVIDENCE/T2_try2_48_97_result.json`、`T2_try3_48_97_result.json` |
| 6 | **未构造出"建筑+步兵同格链"**：成功放置的建筑 footprint 均落在目标步兵格的上/下相邻格，无任何格节点集同时含 BuildingClass 与 InfantryClass；链长≥2 的格全为纯 InfantryClass | [未证] | `EVIDENCE/T2_*_result.json`、`precondition_cells.jsonl` |
| 7 | 阻塞**不在** `0x47C620` 检查点：静态拒集不含步兵；live ghost 在步兵格邻域显绿；红色只出现在 footprint 与先前建筑重叠时（WhatAmI==6 拒）。真正卡在 GUI 落格 targeting：3×2 footprint 相对光标有固定偏移 + 相机自动滚动 + 单位持续移动 | [静态推断] | 试1点(380,800)→footprint(46-48,95-96)、试2点(325,828)→(47-49,98-99)、试3点(380,814)红=自身建筑重叠非步兵 |

## 核心数字（给审计，可独立复算）
- **采样率 15,174/s**：`T2_try1_48_97.jsonl` 头 `n=30,351`、`wall_s=2.0001414` ⇒ 30,351/2.0001414=15,174.4/s（>5,000/s 要求，覆盖 click_t=0.35 s 前后 2 s）。复算：`python -c "import json;l=open('EVIDENCE/T2_try1_48_97.jsonl').readlines();h=json.loads(l[0]);print(h['n']/h['wall_s'])"`。其余 5 次同法 11,382–28,263/s。
- **前提链长=3**：`precondition_cells.jsonl` 首行 `cells["48,97"].lenA=3`，三节点 RTTI 均 `.?AVInfantryClass@@`、owner 玩家 House、`layer94`=2、`chainbit_8C`=0。复算：逐行读该 JSONL 的 `lenA`/`rtti_name`。
- **成功构造数 0**：所有 `T2_*_result.json` 的 `result_cells` 中，无一格节点集同时含 BuildingClass 与 InfantryClass；成功放置 3 次（try1/try2/campaign 多次），0 次同格重叠。复算：读各 `result.json` 的 `new_napowr` + `result_cells`。

## 卡在哪一步（T4）
`0x47C620` 未构成阻塞（拒集 {6,0x24} 不含步兵；live footprint 显绿）。落格前唯一实证的拒绝是试3 footprint 与先前 NAPOWR 重叠 → WhatAmI==6 分支返 0（`0x47C6D1 xor al,al`），非步兵。真正未达标的环节是**合成输入的目标格命中**：NAPOWR 3×2 footprint 相对光标约 -2y 偏移（试1→(46-48,95-96)、试2→(47-49,98-99)、试3→(47-49,96-97)，均在步兵格(48,97)上下错位），叠加遭遇战相机自动滚动与单位移动，多格 footprint 无法稳定命中单一步兵格。T3 次路径（多步兵/反向/车辆）受同一 targeting 限制，未取得可归因样本（如实记，未凑数）。**②-b 不能收口为"不可构造"**：字节路径仍开放，缺的是可重复命中目标格的受控状态。

## 真机收尾
真机收尾：进程已关闭 / except.txt 未变（26,272 B、2026-11-12T22:29:17.2046290Z、SHA `6907F395…` 与开工前逐字节一致）/ 无残留 gamemd.exe。本卡仅启动并关闭自身三个 pid（33452、8252、29508，均 Stop-Process）；gamemd.exe `73201CC0…F67476`、ddraw.dll `85E0F7D5…3B03A9` SHA 前后不变。证据 `work/baseline_end.txt`。现把 `LIVE_LOCK` 置为 `RELEASED by W177-E`。
