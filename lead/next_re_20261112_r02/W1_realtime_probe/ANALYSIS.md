# ANALYSIS.md —— 门控跳过 vs 真卡顿（离线重算，只从 NDJSON）

- run_id: `NEXT_RE_20261112_R02`
- 生成时刻(UTC): `2026-11-12T14:36:51.524479+00:00`
- 数据源: `D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe\out\gate_probe_R02b.ndjson`（**只读**，无真机连接）
- 采样拍数 **3569**：`read_status=ok` 3569，读失败 **0**（保留但不参与统计，不当作「未推进」，也不填补）
- 真实单调时钟跨度: **179.963 s**（2026-11-12T14:33:27.810644+00:00 → 2026-11-12T14:36:27.773349+00:00）
- `read_status` 分布: {'ok': 3569}

## 1. 核心判据

| 指标 | 值 |
| --- | --- |
| `frame_advanced=false` 拍数 | **230** |
| 其中 `any_gate_nonzero=true` | **0**（0.000%） |
| 其中 `any_gate_nonzero=false`（四门控全 0 但未推进） | **230**（100.000%） |
| 其中 `any_gate_nonzero=null` | 0 |
| `frame_advanced=true` 拍数 | 3338 |
| `frame_advanced=null`（首拍 / 读失败后一拍） | 1 |

**「四门控全 0 但帧未推进」**：共 230 拍，位于 1 个连续段。
最长连续段：**11450.175 ms**（真实 `t_mono_ns` 差，230 拍，seq 722→951，段首 remark=`menu_open_attempt`）；相邻前后拍夹出的区间上界 12678.004 ms。

最长 10 段（按真实 t_mono_ns 跨度降序）：

| # | 拍数 | span(ms) | enclosed(ms) | seq | remark |
| --- | --- | --- | --- | --- | --- |
| 1 | 230 | 11450.175 | 12678.004 | 722→951 | menu_open_attempt |

> **解释边界**：50 ms 轮询只在采样瞬间看门控字节。两次采样之间某个游戏 tick可能短暂出现门控非零而两次采样都读到 0。因此「四门控全 0 但未推进」**不能证明**该停推不是门控造成的；它只能说明 *在采样瞬间* 四门控为 0。反之，若 `frame_advanced=false` 的拍全部伴随门控非零，则与「门控跳过」一致，但同样不是排它性证明（本批不抓栈，无法定位调用点）。

> **另一层模糊性**：50 ms 轮询窗口内 `frame_advanced=false` 只表示这 50 ms 里帧计数器净增量为 0。若游戏内部逻辑 tick 本身慢于 20 Hz、或采样恰好落在两个tick 之间，也会出现单拍全 0 未推进，并**不构成**「卡顿」。因此单拍计数只能作线索，真正有意义的是**连续段长度**（上表用真实 `t_mono_ns` 差给出）；孤立单拍不应解读为停推。

## 1b. 对核心问题的判定（如实口径）

**问题**：「帧计数停推」是 *门控跳过* 还是 *真的卡顿*？

**本批结论：两趟都没有取得「门控跳过」的正样本，因此无法判定原报告停推属于哪一类。**

- 两趟共 9558 个 `read_status=ok` 拍，四个门控字节 **始终为 0**；
  `exitstate` / `b07784` 也始终为 0。门控跳过路径在本场 `Proving Grounds`
  遭遇战中**一次都没有被触发**。
- 主判据趟（Run 2）里唯一一段「帧未推进」是 **230 拍 / 11450.175 ms** 的连续段，
  段首 remark=`menu_open_attempt`，**完全落在我们主动按 Esc 打开的局内菜单期间**；
  点击 `GUI:ResumeMission` 后立即恢复推进（校验 Δframe=395）。
  这段是「四门控全 0 但帧未推进」，但成因是 **游戏主循环在暂停态下不调用推进函数**，
  属于**非门控的抑制路径**，且是观测自身引入的，**不是自然卡顿**。
- 除该段外，Run 2 的 0–36 s 与 48.6–180 s 共 3338 拍**每一拍都推进**；
  包括 320 拍 `win_foreground=false`（窗口失焦）期间帧计数仍在推进。
- 因此：本批**没有观测到任何自然发生的长停**，也**没有观测到门控跳过**。
  按红线，这**不等于**「长停不存在」或「门控跳过不存在」；
  只说明在这两趟、这张图、这个负载与相位下两者都未出现。
- 有价值的正面发现：存在一种**与四门控无关**的帧停推（菜单暂停），
  说明「四门控全 0 但帧未推进」在真机上确实可发生；
  后续若要归因原报告停推，应先复现它，再在停推瞬间同时记录门控与调用点
  （本批禁止抓栈，做不了后者）。

## 2. 四门控非零占比及对应状态

| 门控 | 非零拍数 | 占 ok 拍比例 | 落在 frame_advanced=false 内 | 非零时 remark 状态 |
| --- | --- | --- | --- | --- |
| g1 | 0 | 0.000% | 0 | （无） |
| g2 | 0 | 0.000% | 0 | （无） |
| g3 | 0 | 0.000% | 0 | （无） |
| g4 | 0 | 0.000% | 0 | （无） |

- 门控非零的具体取值: （无）
- `any_gate_nonzero=true` 在全部 ok 拍中: 0（0.000%）；帧号回退（新局边界）拍数: 0。

按 `remark`（脚本排程标注的**外部状态**，不是从帧变化推出来的战斗状态）分段：

| remark | 总拍 | ok | fail | adv=false | 全0未推进 | 门控非零 |
| --- | --- | --- | --- | --- | --- | --- |
| stable_ingame | 2232 | 2232 | 0 | 0 | 0 | 0 |
| focus_lost_window | 320 | 320 | 0 | 0 | 0 | 0 |
| game_start | 288 | 288 | 0 | 0 | 0 | 0 |
| return_to_game | 252 | 252 | 0 | 1 | 1 | 0 |
| focus_regained_window | 247 | 247 | 0 | 0 | 0 | 0 |
| menu_open_attempt | 230 | 230 | 0 | 229 | 229 | 0 |

## 3. 帧推进速率的区间估计（**不是逐帧 FPS**）

- 全程净帧计数推进 Δframe = **5229**，真实耗时 179.963 s ⇒ 平均 **29.056 计数/s**
- 10 s 窗口（按真实 `t_mono_ns` 切分）净推进率区间：**min 4.200 / 中位 31.200 / max 31.317 计数/s**（共 18 个窗口）

| 窗口 | 起(s) | 止(s) | 真实时长(s) | Δframe | 计数/s |
| --- | --- | --- | --- | --- | --- |
| 0 | 0.0 | 10.0 | 10.00 | 311.0 | 31.100 |
| 1 | 10.0 | 20.0 | 10.00 | 313.0 | 31.300 |
| 2 | 20.0 | 30.0 | 10.00 | 312.0 | 31.200 |
| 3 | 30.0 | 40.0 | 10.00 | 190.0 | 19.000 |
| 4 | 40.0 | 50.0 | 10.00 | 42.0 | 4.200 |
| 5 | 50.0 | 60.0 | 10.00 | 313.0 | 31.300 |
| 6 | 60.0 | 70.0 | 10.00 | 312.0 | 31.200 |
| 7 | 70.0 | 80.0 | 10.00 | 313.0 | 31.300 |
| 8 | 80.0 | 90.0 | 10.00 | 312.0 | 31.200 |
| 9 | 90.0 | 100.0 | 10.00 | 311.0 | 31.100 |
| 10 | 100.0 | 110.0 | 10.00 | 313.0 | 31.300 |
| 11 | 110.0 | 120.0 | 10.00 | 312.0 | 31.200 |
| 12 | 120.0 | 130.0 | 10.00 | 313.0 | 31.300 |
| 13 | 130.0 | 140.0 | 10.00 | 312.0 | 31.200 |
| 14 | 140.0 | 150.0 | 10.00 | 313.0 | 31.300 |
| 15 | 150.0 | 160.0 | 10.00 | 312.0 | 31.200 |
| 16 | 160.0 | 170.0 | 10.00 | 313.0 | 31.300 |
| 17 | 170.0 | 180.0 | 9.96 | 312.0 | 31.317 |

> **明确声明**：以上数字是 *50 ms 轮询窗口内帧计数器的净增量 / 真实墙钟时间*，**不是逐帧 FPS**，也不是每帧耗时。一次 50 ms 轮询之间游戏可能推进 0~多个内部 tick，我们只看净值；因此**不提供**逐帧 P95/P99、帧时间分布或 FPS 分位数。该计数器的语义是游戏内部逻辑帧计数（`0x00A8ED84` 在 `0x55DE81` 处 +1），不等同于渲染帧数。

## 4. 辅助字段 / 前台 / 事件（仅登记，不作语义断言）

- `win_foreground` 分布: {'True': 3249, 'False': 320}
- `exitstate` (0x00A8EDD8) 前 12 值: [('0', 3569)]
- `b07784` (0x00B07784) 前 12 值: [('0', 3569)]
- 事件行 10 条，分布: {'run_start_polling': 1, 'phase_game_start': 1, 'phase_stable_ingame': 1, 'event_esc_open_menu': 1, 'event_esc_return_game': 1, 'event_verify_resume': 1, 'event_focus_lost': 1, 'event_focus_regained': 1, 'phase_stable_ingame_3': 1, 'polling_end': 1}

事件明细：

- `run_start_polling` @ None s, remark=`game_start`, detail=`{"code_signature_ok": true, "is32": true, "map": {"display_name": "[8] Proving Grounds", "index": 265, "n_hits": 1, "n_items": 268, "pattern": "Proving Grounds"}}`
- `phase_game_start` @ 0.0 s, remark=`game_start`, detail=`{}`
- `phase_stable_ingame` @ 14.4 s, remark=`stable_ingame`, detail=`{}`
- `event_esc_open_menu` @ 36.0 s, remark=`menu_open_attempt`, detail=`{"action": "keybd_event(VK_ESCAPE)", "frame_at_menu": 1455, "intent": "打开局内菜单（是否真的暂停以帧/门控读数为准）", "menu_button_texts": ["GUI:ResumeMission", "GUI:GameControls", "GUI:LoadGame", "GUI:AbortMission", "GUI:SaveGame", "GUI:DeleteGame"]}`
- `event_esc_return_game` @ 48.628 s, remark=`return_to_game`, detail=`{"action": "click_resume_button", "intent": "从菜单返回对局", "result": {"clicked": true, "hwnd": 9836410, "method": "button", "text": "GUI:ResumeMission"}}`
- `event_verify_resume` @ 61.228 s, remark=`stable_ingame`, detail=`{"delta_since_menu": 395, "frame_at_menu": 1455, "frame_now": 1850, "resume_action": {"clicked": true, "hwnd": 9836410, "method": "button", "text": "GUI:ResumeMission"}, "resumed": true}`
- `event_focus_lost` @ 82.828 s, remark=`focus_lost_window`, detail=`{"action": "SetForegroundWindow(other_hwnd)", "intent": "窗口失焦", "other_hwnd": 70980, "success": true}`
- `event_focus_regained` @ 99.013 s, remark=`focus_regained_window`, detail=`{"action": "SetForegroundWindow(game_hwnd)", "intent": "切回游戏", "success": true}`
- `phase_stable_ingame_3` @ 111.613 s, remark=`stable_ingame`, detail=`{}`
- `polling_end` @ None s, remark=`polling_end`, detail=`{"n_read_fail": 0, "n_samples": 3569, "observed_seconds": 180.0126463}`

## 5. 结论口径

1. 判据只用 `frame_advanced` 与四个门控字节；**没有**用「帧在变」定义战斗状态。
2. 本次是 50 ms 间隔的只读轮询（主判据 1 趟 180 s，另有 1 趟 300 s 受自身干预污染）。**没观测到长停 ≠ 长停不存在**；未被本次观测覆盖的时长、地图、负载与随机相位都可能出现长停。
3. 「四门控全 0 但帧未推进」若存在，只能作为「*可能是*真的卡顿/非门控原因」的**线索**，不能作为排它结论：门控可在采样间非零、也可能存在本批未登记的其它跳过路径；本批禁止抓栈，无法给出调用点级归因。

## 附录 —— 多趟运行对比（均只从各自 NDJSON 离线重算）

主表为本次最后一路样本；下表为同一批次内其它路原始记录，**原始 NDJSON 一律不删改**。

| NDJSON | 采样 | adv=false | 其中门控非零 | 四门控全0未推进 | 全程门控非零拍 | 最长段(ms) | 时长(s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe\out\gate_probe_R02b.ndjson | 3569 | 230 | 0 | 230 | 0 | 11450.175 | 180.0 |
| D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W1_realtime_probe\out\out\gate_probe_R02.ndjson | 5989 | 4789 | 0 | 4789 | 0 | 239804.121 | 300.0 |

> 第一趟（run1）的 Esc 返回动作失效，导致约 240 s 处于**局内菜单暂停**；该段虽为「四门控全 0 但帧未推进」，但属于 **观测自身引入的扰动**，**不得**解读为自然卡顿，也不得据此宣称「长停已被复现」。第二趟修正了返回动作并加了恢复校验，以第二趟为主判据。
