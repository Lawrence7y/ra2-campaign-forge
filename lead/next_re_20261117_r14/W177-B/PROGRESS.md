# W177-B · PROGRESS（真机重试卡）

> 卡号 W177-B｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（只读未改）｜ImageBase 0x400000
> 结论：**部分完成**——S0/S1/S2 达成；S3 卡住（下单扣款可见但无法完成可归因放置）；S4 未取得有效样本。
> 成功放置次数（额度扣款+归属+格链三重佐证）= **0**；唯一扣款事件标 [未证]。重叠复现 = **0**（暴露量 0）。

## 结论表

| # | 结论 | 分级 | 证据 |
|---|------|------|------|
| 1 | 开局前后 gamemd.exe/ddraw.dll SHA-256 不变，except.txt 不变（len 26272, mtime 11-13T06:29:17） | [已证] | `EVIDENCE/S0_baseline.txt` + 本文件末「真机收尾」 |
| 2 | 进局成功，画面非黑：`s1_startgame2.png`(nonblack 0.61)、`s1_ingame_full.png` 正常渲染；frame 从 0 递增 | [已证] | `EVIDENCE/s1_startgame2.png`、`s1_ingame_full.png`、各 `*.json` |
| 3 | 目标建筑确为 **NAPOWR**（苏军磁能反應爐 $600），不是 YAPOWR；上一卡的 YAPOWR 是 AI 建筑 | [已证] | `EVIDENCE/tooltip_2327.png`、`s2_baseline3.json`、`sidebar_native.png` |
| 4 | 侧栏额度字段 = `PlayerHouse+0x30C`；玩家 House 由 `[0xA83D4C]` 定位，+0x1EC/+0x1ED=1 | [已证] | `EVIDENCE/credit_probe.png/json` |
| 5 | §951 取格路径 A 可用：74 座建筑全算出合理 cellX/cellY 与 CellClass* | [已证] | `EVIDENCE/s2_baseline3.json`、`OBSERVATIONS.txt` §5 |
| 6 | 点击 NAPOWR 图标使额度 10000→9400（精确 −600）并生成 limbo NAPOWR `0x15effce0`（owner=PlayerHouse, +0x81=1,+0x74=0, cell=0,0） | [已证]（下单事件） | `EVIDENCE/OBSERVATIONS.txt` §3、`v3p01.json`、`v3_sidebar_deployed.png` |
| 7 | 该 limbo 对象未能入格（格链无该对象），随后点击被取消并退款 9400→10000 ⇒ **不构成成功放置** | [已证]（未入格事实） | `EVIDENCE/v3_place_try1.png`、`v3_placed1/2.png`、`v3_final_after.png` |
| 8 | 成功放置次数 = 0；重叠复现 = 0（暴露量 0，未构造出可归因放置，非「找了没找到」） | [已证] | `LIVE.md` 逐次表、`EVIDENCE/OBSERVATIONS.txt` §4 |
| 9 | S4 刻意重叠尝试 ≥10 次不同相对位置 | [未证] | 卡在 S3，无有效放置样本（`UNKNOWNS.md` U1） |

## 核心数字（给审计）
- 成功放置次数（额度佐证）：**0**（唯一 −600 扣款事件因缺格链佐证标 [未证]）。
- `[+0x81]` 取值序列：玩家已放置建筑 `0`；唯一 limbo NAPOWR `0x15effce0` 为 `1`（随后取消）。
- 格链长变化序列：无可归因放置前后变化（暴露量 0）；已存在 NAPOWR `0x156820d0` 链A=1/链B=0。
- 重叠复现次数：**0**（暴露量 0）。`obj+0x21C` 归属：唯一扣款对象 1/1 指向玩家 House `0x10d50d30`，但对象未入格。

## 卡在哪一步
**S3（放置）**：图标点击可扣款并生成 limbo 对象，但 ghost 无法落到可接受格（red-X 禁放/点击取消退款；鼠标停侧栏边缘触发相机 auto-scroll 使固定屏幕坐标失准）。后期基地被 AI 超武摧毁、建造栏变空。按纪律 8/12/18 如实报 [未证]，未用静态推断冒充实测。

## 纪律执行
- 所有点击经 `click_client`（前台+归属校验）；未用裸 SetCursorPos 作点击工具（修正上一卡违规 #6）。
- 未写进程内存/未注入/未改 ra2youli；未 git commit；未改台账。
- 分级不虚高；否定结论（重叠 0）标明暴露量 0。

## 真机收尾声明
本人（W177-B）仅启动上述 pid 的 gamemd.exe；已用 Stop-Process 关闭该 pid，`Get-Process gamemd` 计数 = 0，**无残留进程**。收尾哈希与 except.txt 与开工前一致（见结论 1）。现把 LIVE_LOCK 置为 `RELEASED by W177-B`。

## 交付物
`PROGRESS.md`｜`LIVE.md`｜`UNKNOWNS.md`｜`DISAGREE.md`｜`EVIDENCE/`（117+ 文件，含截图）｜`work/`（脚本可复跑）｜`coverage_delta.tsv`。
