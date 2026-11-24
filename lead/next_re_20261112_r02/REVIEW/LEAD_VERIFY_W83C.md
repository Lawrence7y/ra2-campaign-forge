# LEAD_VERIFY_W83C · 其余三种战斗胜利条件：**两个判胜、一个不是胜利条件**（双臂对照齐全）

> 记录人：Lead｜时间：2026-11-14 11:02｜卡：W83c（**GLM-5.3-Flash**，真机 8 趟；前两次派 Hy4 均零产出）
> 交付：`W83c_other_victory\OTHER_VICTORY_CONDITIONS.md` + `UNKNOWNS.md`(U1–U8) + `DISAGREE.md`(D1–D6) + `out\` + `REAL_DIR_PROOF.txt`
> 我核了盘上 8 份 `TRIP_*.json`（下表是实测，不是采信自述）

## 1 · 八趟实测（我逐趟读 `TRIP_RESULT.json`）

| trip | variant | ok | outcome | kind | frame |
|---|---|---|---|---|---|
| trip1 | `db` v1 | True | `NO_RESULT_WITHIN_150s` | — | — |
| trip2 | `db` v2 | True | `VICTORY_RESULT_AND_TERMINATION_OK` | `victory_score_screen` | **90** |
| trip3 | `db` v3 | True | `VICTORY_RESULT_AND_TERMINATION_OK` | `victory_score_screen` | **314** |
| trip4 | `dbc`（**对照**） | True | `VICTORY_RESULT_AND_TERMINATION_OK` | `victory_score_screen` | **915** |
| trip5 | `tb` | False | `BLOCKED: timeout waiting to enter` | — | — |
| trip5b | `tb` | True | `VICTORY_RESULT_AND_TERMINATION_OK` | `victory_score_screen` | **201** |
| trip6 | `tbc`（**对照**） | True | `VICTORY_RESULT_AND_TERMINATION_OK` | `victory_score_screen` | **915** |
| trip7 | `hw` | True | `NO_RESULT_WITHIN_150s` | — | — |

## 2 · 三个条件的判定

### ① `destroy_all_buildings`：**判胜成立**
- 实验臂 `db` v3：40 MTNK 全 Hunt vs **3 个静止武装建筑**（`ATESLA`）、无敌方单位、**无 `survive`** ⇒ **frame 314**（10.05 游戏秒），引擎自报「**摧毀敵建築數 3**」「所花時間 00:00:10」
- 对照臂 `dbc`：**同布局同兵力**，条件换 `survive(55)` ⇒ **frame 915**
- **314 ≪ 915**，且 314 **不属** `15N+90` 序列 ⇒ **归因干净**

### ② `destroy_building`（点名建筑）：**判胜成立，且不隐含"敌方全灭"**
- 实验臂 `tb`：点名 = 挂 `w83c_tgt` tag 的 `ATESLA`，另放 **1 个 British E1 在 37+ 行外的远端**
- 结果 **frame 201**（6.43 游戏秒），引擎自报「**摧毀敵建築數 1**」「所花時間 00:00:06」
- 对照臂 `tbc`：**frame 915**
- `[签发·关键子问题]` **判胜时敌方仍有活单位** —— frame 201 时那个 E1 必然活着（6.4 游戏秒走不完 37 行），死的只有点名建筑 ⇒ **"点名建筑"语义，不隐含"敌方全灭"**。编译层一致：tag 挂触发 + `DestroyedByAny(7)`，**不引用敌方 house 存活**。

### ③ `hunt_wave` 单独用：**不是胜利条件**
- `hw` 臂：**150 s 无结算、无失败框**（`NO_RESULT_WITHIN_150s`）；编译产物 **0 条 win trigger**（只有 `text@1` + `AllToHunt@3` + 自动判负）
- 与 W79 trip5 合并 ⇒ **本引擎的胜利只来自 `WinnerIs` 动作，无任何隐式自动判胜**

## 3 · 它自己解释了我先前看到的异常（`frame=90`）

`[我 10:46 报的"trip2 判胜 frame=90 太可疑"→ 它给出了根因]`
- **`docs/DESIGN.md` 写的型号 `ATSLA` 在游戏 rules 中不存在**（真名 **`ATESLA`**，它做了 **rules probe 实证**）
- ⇒ 建筑被丢弃 ⇒ 英军 **0 建筑** ⇒ `event 10` **空真** ⇒ **开局 frame 90 即胜**
- `[签发]` **`frame=90` 是"型号无效导致空真"的签名**，不是判胜机制异常。这条**同时校正了 `docs/DESIGN.md` 的型号表**（已入它的 DISAGREE D1–D6）。

## 4 · 两条额外实测发现（我认可，都值得记）

1. **无武装建筑（`GAPOWR` 电厂）不会被 Hunt 单位主动攻击** —— v1 臂坦克 **154 游戏秒纹丝不动**（t10/t30/t60 截图**逐字节相同**）。⇒ **"摧毁建筑"类实验必须用武装建筑**，否则条件永远不成立。
   `[这条解释了 trip1 为何 150 s 超时]` **不是条件没接线，是电厂根本不挨打** —— 这是"实验设计失败"而非"能力缺失"，区分正确。
2. **型号名必须实测**：`docs/DESIGN.md` 的型号表有错，**不能照文档写设计**。

## 5 · 探针与可核性

- **失败重试框 0 次出现**。终局分布：`victory_score_screen` ×5、超时 ×2（均有效：`db` v1 无武装建筑不挨打 / `hw` 无 win trigger）、`BLOCKED` ×1（trip5 点「新戰役」UI 抖动，**原样重试 trip5b 即成功，证据保留**）
- **判胜 frame 全部是 RPM 读数 + stall 复读确认，未从截图目测** ⇒ 这正是我在 §36/§37 立的那条规矩（截图数字不可作证据）被遵守
- `REAL_DIR_PROOF.txt`：`IDENTICAL_TREE=True`（647 文件 / 1,989,215,270 B，added/removed/changed/mtime_diff 全 0）；`gamemd.exe` PRE==POST==`73201cc0…`；沙箱 21 项配置逐字节还原、`BATTLEMD.INI` 回官方 2,733 B / `7e40691a…`、沙箱已删
- 锁：7 次启动全部 `w83c`→`lead` 成对，收尾 `owner=lead`，`gamemd` 残留 0

## 6 · 签发总表（`ra2forge` 战斗胜利条件能力，现已全覆盖）

| 条件 | 判定 | 证据 |
|---|---|---|
| `survive(N)` | ✅ 成立（`frame=15N+90`，机制已定谳见 §618） | W79 + W82 |
| `destroy_all_forces` | ✅ 成立 | W79（frame 274 vs 对照 915） |
| **`destroy_all_buildings`** | ✅ **成立（本卡）** | frame **314** vs 对照 915 |
| **`destroy_building`** | ✅ **成立（本卡）**，且不隐含敌方全灭 | frame **201** vs 对照 915 |
| **`hunt_wave`** | ❌ **不是胜利条件（本卡确认）** | 150 s 不判胜、0 条 win trigger |
| 占领/capture | — | `design.py` 无此类型 |

⇒ **`design.py:43-55` 的五种胜利条件现已全部有真机判定**，无一项停留在"schema 支持但未验"。

`[边界]` `destroy_all_forces`（W79）与另两个（W83c）各用 1 个布局 / 1 镜像；**不得**外推为"任意地图任意兵力都成立"。
