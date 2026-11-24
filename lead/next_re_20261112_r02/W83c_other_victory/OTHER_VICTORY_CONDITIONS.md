# W83c · 其余战斗胜利条件真机补测：`destroy_all_buildings` / `destroy_building` / `hunt_wave`

> 执行者 **GLM-5.3-Flash**（卡 W83c，第三次派发，前两次 `work/cn:hy4free` 零产出）｜
> 卡目录 `lead\next_re_20261112_r02\W83c_other_victory\`
> `STARTED.txt` 写于任何读码之前：`2026-11-14T10:05:52+08:00`（ISO + GLM-5.3-Flash + "W83c: third dispatch, hy4 dead"）
> 离线造包 `10:25`（5 包，0 锁）→ 沙箱安装 `10:27` → 真机 7 次启动/5 趟有效 `10:28–10:57` → 收尾还原 `10:57` → 报告 `11:0x`
> 时间盒 140 min，实际约 60 min，①②③全部完成，无降级。
> 分级：`[本次实测]` / `[本次读码]` / `[静态推断]` / `[转引]` / `[待运行验证]`。本报告**不签发**（签发权在 Lead）。
> 工具：复制 W79 工具链到本卡改路径（`work\tools\w83c_*.py`），未 import 任何他卡脚本。

---

## 0 · 一句话结论

- **① `destroy_all_buildings(enemy)` 判胜成立**：40 辆我方 MTNK 全 `Hunt` vs 3 个静止 British ATESLA（光棱塔，武装建筑、无敌方单位），条件 `destroy_all_buildings(enemy=British)`、无 `survive` ⇒ 判胜 **frame 314**（10.05 游戏秒），结算屏引擎自报 **「摧毀敵建築數 3」「所花時間 00:00:10」**；同布局对照臂换 `survive(55)` ⇒ 判胜 **frame 915**。314 ≪ 915 ⇒ **判胜确实由 `AllBuildingsDestroyed(British)→WinnerIs` 触发**。
- **② `destroy_building(structure_tag)` 判胜成立，且"敌方仍有活单位时照样判胜"**：点名建筑（挂 `w83c_tgt` tag 的 ATESLA）被 40 辆 Hunt 坦克打掉 ⇒ **frame 201**（6.43 游戏秒），结算屏 **「摧毀敵建築數 1」**；另一个 British E1 放在 37+ 行外，6.4 游戏秒时**必然还活着**（行军时间远未到）⇒ **点名建筑语义，不隐含"敌方全灭"**。对照臂 `survive(55)` ⇒ frame **915**。
- **③ `hunt_wave` 单独使用（不配任何胜利条件）不判胜**：`[本次实测]` 整局 150 s 无任何结算/失败框（`NO_RESULT_WITHIN_150s`）；`[本次读码]` 编译产物只有 `text@1` + `AllToHunt(British)@3` + 自动判负触发器，**没有任何 win trigger**。与 W79 对照趟 trip5（敌方全灭不自动判胜）互相印证。
- **探针失败框**：全程 **0 次** `defeat_restart_dialog`。出现 1 次 `BLOCKED: timeout waiting to enter`（trip5 首次 tb，主菜单「新戰役」点击未生效的一次性 UI 抖动，与地图/失败框无关，原样重试即成）。
- **真目录零改动自证**：`IDENTICAL_TREE=True`（647 文件 / 1,989,215,270 B，`gamemd.exe` 仍 `73201cc0…`），详见 `REAL_DIR_PROOF.txt`。
- **锁**：每趟 `w83c`→`lead`、`finally` 必还；最终 `.game_instance.lock` `owner=lead`；全程 `gamemd` 残留 0（trip4 收尾一次 2 s 退出延迟，复查已清零）。

---

## 1 · 实验设计

### 1.1 编译语义（`[本次读码]` V15 `builder.py:868-966` / `triggers.py`）

| 设计 objective | 编译为 | 事件/动作序列化 |
|---|---|---|
| `destroy_all_buildings(enemy=British)` | win trigger：`ev_all_buildings_destroyed(4)` → 链尾 `act_winner(8)` | 事件 `,10,0,4`；动作 `,1,0,8` |
| `destroy_building(structure_tag)` | **tag 挂触发**（trigger 的 tag = 结构体的 tag id）+ `ev_destroyed_by_any()` → `act_winner(8)` | 事件 `,7,0,0`；动作 `,1,0,8` |
| `hunt_wave(house,at_second)` | **event-only**：`ev_elapsed_time(N)` → `act_all_to_hunt(4)`，**无 win 动作** | 事件 `,13,0,3`；动作 `,6,0,4` |
| `survive(55)` | win trigger：`ev_elapsed_time(55)` → `act_winner(8)` | 事件 `,13,0,55`（实测判胜 frame = 15N+90 = 915，`[转引]` W79） |

每个任务图还自动带 `AllDestroyed(Russians)→Loser(8)` 判负触发器（事件 `,11,0,8`）。

### 1.2 包与趟（全部 60×60 TEMPERATE，我方 Russians：NACNST+NAPOWR×2 + 40 MTNK，位置/单位行与 W79 ann 臂逐字节相同）

| 包 | 臂 | 敌方（British） | objectives | 真机趟 |
|---|---|---|---|---|
| `db` v3 | ① 实验 | 3× **ATESLA**(36,24/30/36)，无单位 | `text@1` + `destroy_all_buildings` | trip3 |
| `dbc` | ① 对照 | 同 db v3 布局（对象行逐字节相同） | `text@1` + `survive(55)` | trip4 |
| `tb` | ② 实验 | 1× **ATESLA** tag=`w83c_tgt`(36,30) + 1× E1(5,18) 远端静止 | `text@1` + `destroy_building(w83c_tgt)` | trip5b |
| `tbc` | ② 对照 | 同 tb 布局 | `text@1` + `survive(55)` | trip6 |
| `hw` | ③ | 4× E1(36,24/27/30/33) 静止；我方坦克全 **Guard** | `text@1` + `hunt_wave(British,at_second=3)`，**无胜利条件** | trip7 |

### 1.3 造包过程中的两次设计修正（都是 `[本次实测]` 发现，本身就是结论）

| 版本 | 敌方建筑 | 真机结果 | 结论 |
|---|---|---|---|
| db **v1** (trip1) | 3× GAPOWR（无武装电厂） | **NO_RESULT_150s**；t10/t30/t60 截图**逐字节相同**——坦克 154 游戏秒纹丝不动 | **RA2 的 Hunt 目标获取忽略无武装建筑**（无威胁不锁定）；`[Units]/[Houses]/[British]` 节与 W79 ann 臂逐字节相同，唯一变量是目标类型，排除布局/兵力/胜负接线因素 |
| db **v2** (trip2) | 3× ATSLA | **frame 90 即胜**，t00 画面已有「任務完成」且无塔 | ATSLA 型号**在游戏 rules 中不存在**（见 `out\RULES_PROBE.json`）→ 建筑被加载器丢弃 → 英军 0 建筑 → event 10 **空真** ⇒ frame 90 空胜。**「开局即 frame-90 判胜」= 目标建筑型号无效的签名** |
| db **v3** (trip3) | 3× **ATESLA** | **frame 314 判胜**，摧毀敵建築數 3 | 正常实验臂 |

`[静态推断]` ATESLA = 盟军光棱塔（`[ATESLA]` section 实存于 `expandmd01.mix!rulesmd.ini`，743,215 B）；docs/DESIGN.md 写的 `ATSLA` 是错的（见 `DISAGREE.md` D1）。

---

## 2 · ① `destroy_all_buildings`：实验臂 vs 对照臂

### 2.1 两张表（`[本次实测]`）

**实验臂 db（trip3，`destroy_all_buildings(enemy=British)`，无 survive）**

| 项 | 值 |
|---|---|
| outcome | `VICTORY_RESULT_AND_TERMINATION_OK` |
| **判胜 frame** | **314**（stall 确认 frame_stalled=true） |
| 游戏秒（frame/31.25） | 10.05 |
| 结算屏引擎自报 | **摧毀敵建築數 3** ／ 所花時間 **00:00:10** |
| 控件 | `GUI:Continue`+`GUI:HeadsTaken`+`GUI:ParTime`+`GUI:StandaloneScore`+`GUI:YourTime` |
| 终局 | `no_extra_start=true`、EOG=1、未起第 2 关 |
| 地图编译产物 | 唯一 win trigger = `,10,0,4`→`,1,0,8`；无 `,13,0,55`、无 `,11,0,4`（`[本次读码]` BUILD_RESULT.json verify_db） |

**对照臂 dbc（trip4，同布局，`survive(55)`，无歼灭条件）**

| 项 | 值 |
|---|---|
| outcome | `VICTORY_RESULT_AND_TERMINATION_OK` |
| **判胜 frame** | **915**（= 15×55+90，精确复现 W79 规律；stall=true） |
| 结算屏所花時間 | 00:00:30 |
| 地图编译产物 | 唯一 win trigger = `,13,0,55`→`,1,0,8`；**无 `,10,0,4`** |

### 2.2 判定

> **成立：`destroy_all_buildings(enemy)` 能在真机判胜** ✅
> 同布局同兵力：有歼灭条件 ⇒ 314；换成 survive ⇒ **915**。314 处坦克刚清完 3 座塔（结算屏自报 3），915 处塔早已清完却仍在等计时器 ⇒ 引擎**不会**在"敌方建筑全灭"时自动判胜，胜利确由该战斗条件触发。

### 2.3 边界

- 实验臂的敌方建筑是**武装**的（ATESLA 光棱塔）——这是被迫的（v1 证明无武装建筑根本不被攻击），但"3 个建筑 + 无防御单位"的臂型约束保持成立；建筑类型不影响 event 10 的语义（"该 house 建筑数=0"）。
- 敌方无任何单位 ⇒ 该臂不能区分"建筑全灭"与"house 全灭"（后者 W79 已证为 event 11、且引擎不自动判胜）；两事件编译序列不同（`,10,0,4` vs `,11,0,4`），判胜源唯一。
- 单趟，无重复性数据（时间盒所限）；但同引擎 `survive` 对照臂 915 逐点复现 W79，探针链路可信度高。

---

## 3 · ② `destroy_building`：实验臂 vs 对照臂 + 关键子问题

### 3.1 两张表（`[本次实测]`）

**实验臂 tb（trip5b，`destroy_building(structure_tag=w83c_tgt)`，无 survive）**

| 项 | 值 |
|---|---|
| outcome | `VICTORY_RESULT_AND_TERMINATION_OK` |
| **判胜 frame** | **201**（stall=true） |
| 游戏秒 | 6.43 |
| 结算屏引擎自报 | **摧毀敵建築數 1** ／ 所花時間 **00:00:06** |
| 敌方另一个单位 | British E1 @(5,18)（37+ 行外，静止 Guard）：6.43 游戏秒内**不可能被 40 辆刚起步的坦克歼灭** ⇒ 判胜时**敌方仍有活单位** |
| 地图编译产物 | 点名建筑结构行带 tag `0C000000`；win trigger = tag 挂接 + `,7,0,0`→`,1,0,8`；无 `,10,0,4`、无 `,13,0,55` |

**对照臂 tbc（trip6，同布局，`survive(55)`）**

| 项 | 值 |
|---|---|
| outcome | `VICTORY_RESULT_AND_TERMINATION_OK` |
| **判胜 frame** | **915**（stall=true） |
| 地图编译产物 | 唯一 win trigger = `,13,0,55`；无 `,7,0,0`（tag 仍在结构上，但无 tag 触发器） |

### 3.2 关键子问题的回答

> **敌方还有活单位时，`destroy_building` 仍判胜吗？ ⇒ 判胜。** ✅
> frame 201 = 6.43 游戏秒；E1 距坦克阵 37+ 行，MTNK 行军全程远大于此（db 臂 6 行耗 ~9-10 游戏秒），且结算屏「摧毀敵建築數 1」说明死的只有点名建筑。
> ⇒ **`destroy_building` 是"点名建筑"语义**：tag 挂触发的 `DestroyedByAny(7)` 事件只关心**那个 tag** 的建筑物死亡，不检查敌方 house 是否还有单位/建筑。`[本次读码]` 编译层一致：触发器挂在玩家 house 名下，事件不引用敌方 house 索引。
> 对照臂 tbc 915 同布局下等满计时器 ⇒ 引擎也不自动判胜，归因干净。

### 3.3 边界

- 点名建筑用了武装的 ATESLA（同 v1 原因）。tag 语义与武装与否无关（tag 只做触发器挂接），但"坦克愿意打它"依赖武装。
- 若点名建筑被**非我方**力量摧毁（如卖掉、自毁、第三方），`DestroyedByAny` 按编译语义同样算数——本卡未测（`[待运行验证]`）。
- tag 挂在**单位**上的情形未测（设计 schema 允许结构 tag；单位 tag 是否可挂 `destroy_building` 见 `UNKNOWNS.md` U3）。
- trip5 首次进图 BLOCKED（UI 抖动），trip5b 原样重试成功；两者 ndjson 都保留。

---

## 4 · ③ `hunt_wave` 单独使用

| 项 | 值 |
|---|---|
| 包 / 趟 | `hw` / trip7 |
| objectives | `text@1` + `hunt_wave(house=British, at_second=3)`；**无任何胜利条件** |
| 编译产物 | 只有 text、`AllToHunt(6,0,4)@13,0,3`、自动判负 `,11,0,8`；**全图 0 条 win trigger**（builder 出 "no win objective" 警告）`[本次读码]` |
| outcome | **`NO_RESULT_WITHIN_150s`**：150 s 内无胜利结算屏、无失败重试框、无地图错误；frame 一路走到 ~4800+（约 154 游戏秒） |
| 战斗事实 | 我方 40 MTNK 静止 Guard，敌 4 E1 于第 3 秒被令 Hunt（t15 截图坦克阵完好、敌步兵已不在阵前） |

> **单独用 `hunt_wave` 不会判胜** ✅（与卡面设计层判断一致，现升格为 `[本次实测]`）。它只是 `AllToHunt` 行为触发器，与胜利结算完全无接线。与 W79 trip5（敌方全灭也不自动判胜）合并可得：**本引擎的胜利只来自 win trigger 动作（WinnerIs），没有任何隐式自动判胜**。

---

## 5 · 探针三态统计与失败框

| 终局类别 | 趟次 | 明细 |
|---|---|---|
| `victory_score_screen` | 5 | trip2(空胜90) / trip3(314) / trip4(915) / trip5b(201) / trip6(915)，全部 `VICTORY_RESULT_AND_TERMINATION_OK`、`no_extra_start=true` |
| `defeat_restart_dialog` | **0** | **全程未遇到失败重试框**（红线②专项：`GUI:OK`+`GUI:Cancel` 同时可见计 0 次） |
| `NO_RESULT_WITHIN_150s` | 2 | trip1（db v1 无武装建筑不被攻击）、trip7（hw 无 win trigger）——都是**有效实验结果**，不是错误 |
| `BLOCKED: 进图超时` | 1 | trip5：主菜单「新戰役」点击未生效（`screen_trip5_timeout_enter.png` 停在單人遊戲页）；**不是失败框、不是地图错误**；trip5b 重试即成 |
| 地图加载错误 | 0 | `UnableMapSelect/Invalid stage/無法啟始` 0 次 |

frame 读数全部来自 RPM `*(DWORD*)0x00A8ED84`（31.25/s），判胜 frame 均有 2 s 后复读 stall 确认；**无任何数字从截图目测**。

---

## 6 · 真机纪律自证（红线 1–7）

| 红线 | 自证 |
|---|---|
| #1 一趟一锁 | 7 次启动各自 `w83c`→`lead`（trip1,2,3,4,5,5b,6,7），`run_trip*.ndjson` `lock_claimed`/`lock_released` 成对；离线阶段锁恒 `owner=lead`；最终锁 `owner=lead` |
| #2 不写 `ra2youli` | 全部只在 `sandbox_game\`（robocopy 自真目录）运行；`out\real_pre.json` vs `real_post.json` ⇒ **IDENTICAL_TREE=True**（647 文件/1,989,215,270 B/277 map-like，added=removed=changed=mtime_diff=0）；`gamemd.exe` PRE==POST==`73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` |
| #3 只关自己 pid | pid 34792/16708/5096/7844/1156/26612/41068/8704，`WM_CLOSE→taskkill /PID→/F` 仅限自有 pid；残留 0（trip4 一次 2 s 退出延迟，进程清单复查已清零并记录）；无 blanket taskkill |
| #4 配置字节副本+还原 | 首次启动前 `out\pristine\` 21 项逐字节副本+SHA；每趟启动前 `config_pre_snapshot`；收尾 `FINALIZE.json` `config_restore` 全部 `byte_identical`/按基线 absent 处理，`all_ok=True`；`BATTLEMD.INI` 还原 2733 B `7e40691a…` == 官方基线 == pristine == 真目录 PRE/POST，`Scenario=SOV01umd.MAP` 回归；沙箱 identical_tree=True 后删除 |
| #5 探针三态 | 见 §5；失败框 0 次、超时按 `NO_RESULT_WITHIN_150s` 记、无 error 污染 |
| #6 只写本卡目录 | 全部产物在 `W83c_other_victory\`；工具为 W79 模板的**卡内副本**改路径（`w83c_lib/common/build/offline/run/finalize`），未 import 他卡脚本；git 未动；未写 W21–W82、REVIEW |
| #7 分级 | 全文按五级标注 |

---

## 7 · 产物清单

| 文件 | 内容 |
|---|---|
| `OTHER_VICTORY_CONDITIONS.md` | 本报告 |
| `REAL_DIR_PROOF.txt` | 真目录零改动 + 沙箱逐字节还原自证 |
| `UNKNOWNS.md` / `DISAGREE.md` | 未覆盖项 / 与既有文档卡面的分歧 |
| `STARTED.txt` / `HEARTBEAT.txt` / `PROGRESS.md` | 活体信号与小步落盘记录 |
| `out\TRIP_trip*.json`、`out\trip*\TRIP_RESULT.json` | 每趟完整判定 + W59 字段轨迹 + frame 轨迹 |
| `out\run_trip*.ndjson` | 每趟逐步 NDJSON（锁、pid、config_pre、采样、截图、清理） |
| `out\screen_trip*_settlement*.png` | 结算屏（摧毀敵建築數 3 / 1、所花時間 00:00:10 / 00:00:06） |
| `out\screen_trip1_combat_t{10,30,60}.png` | v1 冻结证据（三张逐字节相同） |
| `out\screen_trip5_timeout_enter.png` | trip5 菜单抖动证据 |
| `out\BUILD_RESULT.json` / `OFFLINE_*.json` / `FINALIZE.json` / `RULES_PROBE.json` | 造包断言、安装自证、收尾自证、rules 型号探针 |
| `work\w83c_design_*.json`、`work\pkg_*\W83cProbe\` | 5 个包（v3 生效版；v1/v2 地图被 v3 覆盖前已随 trip1/2 留痕） |
| `work\tools\w83c_*.py`、`EVIDENCE\rules_probe.py`、`EVIDENCE\probe_skeleton.ps1` | 本卡自有工具 |

---

## 8 · 给 Lead 的一句话建议

`[本次实测]` 建议签发表更新为：`destroy_all_buildings(enemy)` **能判胜**（314 vs 对照 915）；`destroy_building(structure_tag)` **能判胜且为点名建筑语义——敌方仍有活单位时照样判胜**（201 vs 对照 915）；`hunt_wave` 单独使用**不判胜**（编译层无 win trigger + 150 s 无结算）。另附两条工程约束：**无武装建筑不会被 Hunt 单位主动攻击**（造"摧毁建筑"臂必须用武装建筑）；**`ATSLA` 型号不存在**（用 `ATESLA`），开局即 frame-90 判胜 = 目标建筑型号无效的空真签名。
