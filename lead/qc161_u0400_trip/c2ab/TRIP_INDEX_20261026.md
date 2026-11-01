# C26 轮全趟索引（2026-10-26，生成件 `_gen_trip_index_20261026.py`，数据源=逐趟 `_rec.json` 原件）

趟数终账：**有效 7（②6 + ①1）/ 作废 1（e1）/ 非趟 3（e2、e3 参数失败；gate_rerun 离线）**。
本索引不替代也不删除任何原始记录；`c2ab_summary.json` 系第二遍 A/B 时被覆写——
首批两趟原件在 `_rec.json` 目录内完整在盘（本索引逐条列路径）。

| trip_id | 线/臂 | 配置 | 关窗后自然退出 | exitcode | 布局/进局 | except | a8/载体 | 有效性 | 异族核验覆盖 |
|--|--|--|--|--|--|--|--|--|--|
| 20261026T133324_CTRL_c2 | CTRL | Guard=1 Bail=0 Dry=0 | 150 s 未退 | None | hook/cave=True | 不变 | PASS/True | 有效 | 覆盖（V2/V3/V4，XVERIFY_C2AB_20261026.md 全 CONFIRMED） |
| 20261026T133604_MAIN_c2 | MAIN | Guard=1 Bail=1 Dry=0 | **15.52 s 退出** | 0 | hook/cave=True | 不变 | PASS/True | 有效 | 覆盖（V2/V3/V4，XVERIFY_C2AB_20261026.md 全 CONFIRMED） |
| 20261026T134240_CTRL_c2 | CTRL | Guard=1 Bail=0 Dry=0 | 150 s 未退 | None | hook/cave=True | 不变 | PASS/True | 有效 | 覆盖（V2/V3/V4，XVERIFY_C2AB_20261026.md 全 CONFIRMED） |
| 20261026T134519_MAIN_c2 | MAIN | Guard=1 Bail=1 Dry=0 | **15.71 s 退出** | 0 | hook/cave=True | 不变 | PASS/True | 有效 | 覆盖（V2/V3/V4，XVERIFY_C2AB_20261026.md 全 CONFIRMED） |
| 20261026T161412_L1REG | MAIN配置进局 | Guard=1 Bail=1 Dry=0 + harness7 导航三连 | 150 s 未退 | None | in_battle=True 帧+1770/58.04s | 键缺失(161412) | PASS/True | 有效（R3=关窗后20s自然退出判据不成立） | 161412：首份判定书 V6 审过（except 直接通道 UNVERIFIABLE） |
| 20261026T200938_L1REG | MAIN配置进局 | Guard=1 Bail=1 Dry=0 + harness7 导航三连 | 150 s 未退 | None | in_battle=True 帧+1792/58.04s | 前后哈希相等（6694b75e…） | PASS/True | 有效（R3=关窗后20s自然退出判据不成立） | 200938：**待异族补核**（XVERIFY_L1REG2 在途/待落） |
| l1_20261023e1 | Arm A 直启零注入 | harness7 d019e8be（短路缺省） / --measure 1 / fullscreen；gate: pre_fps15=5.3 units0=0 ok=False / W0 p50=27.8 p99=3520.5 max=3780.8 mf=8 | - | 0 | - | - | -/- | 作废（units0=0/no_advance，档位证据未取得） | ① 未独立核验——**单列状态：待独立核验**（不受②判定书覆盖） |
| l1_20261023e4 | Arm A 直启零注入 | harness7 d019e8be + --h7-keep-rect-wait / --measure 1 / fullscreen；gate: pre_fps15=30.7 units0=702 ok=True / W0 p50=32.6 p99=61.0 max=69.6 mf=736 | - | 0 | - | - | -/- | 有效（pre_fps15≥25 ⇒ 本会话 31 档可判；W0 受测窗未复现严重停顿） | ① 未独立核验——**单列状态：待独立核验**（不受②判定书覆盖） |
| e2/e3（未成行） | - | --extra-argv "--h7-keep-rect-wait"（空格分隔值） | - | - | - | - | -/- | 非趟（launcher argparse 在预检前拒收，rc=2 零副作用、无载体无进程） | - |
| gate_rerun_20261026 | - | - | - | - | - | - | -/- | 非趟（工件门禁复跑 14/14 PASS rc=0） | - |

## 口径备注（REVIEW_S438 逐条落地）
- **事件日志零命中**（13:32–13:48 / 16:14–16:26）=「查询时窗内未观察到登记事件」，
  **不**证明无 AV；except/直接异常/进程状态三通道证据力各报各的。
- **exitstate 恒 0**（200938 close 后）= 采样未观察到闩 1，**不能**据此定位断点、
  不能推出 c″ 未触发或「必在 0x6BE0B6 之前」——C26-06 离线分析任务书据此收紧。
- **PostMessageW 返回值未入 161412/200938 记录**=投递≠处理，装置有效性未闭合；
  观测驱动候选（_drive_c2_x_probe.py）已补记返回值+错误+hwnd/pid/tid。
- 「缺省 0」实证状态：**未验证**——CTRL 是显式写 0（非键缺失）；两件事分报。
- ① e4：W0 数字来自来源线原件**未逐项异族复算**；W1（logic_frames=-3557）/W2（0 帧）
  自性能样本**剔除**；「自然终局」归因未闭合（待场景证据）。
