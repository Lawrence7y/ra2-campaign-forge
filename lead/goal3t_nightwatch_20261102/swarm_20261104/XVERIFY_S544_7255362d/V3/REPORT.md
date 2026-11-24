# V3 · 真机分诊：v4f / v4g 为什么没进图 —— 随机导航失败 还是 回归

核验员：Qoder（swarm_20261104 / XVERIFY_S544_7255362d / V3）
日期：2026-11-04
纪律：零真机（未启动/未终止任何游戏进程）、母本只读、写域仅本目录。所有数字均为本次
独立重算（`python -I -X utf8`），不采信被核件里给出的任何数值。

被核三趟（同机、同图、同 gamemd、同 harness）：

| 目录 | trip_id | 起跑（本地） | 结果 |
|---|---|---|---|
| `…/qc161_u0400_trip/l3_1101v4e` | QC161-U0800-L3-V4-20261101E | 2026-11-03T11:19:13 | ok（units0=1189 / pre_fps15=31.395） |
| `…/qc161_u0400_trip/l3_1101v4f` | QC161-U0800-L3-V4-20261101F | 2026-11-04T17:28:24 | no_advance（units0=0 / pre_fps15=0.0） |
| `…/qc161_u0400_trip/l3_1101v4g` | QC161-U0800-L3-V4-20261101G | 2026-11-04T17:32:29 | no_advance（units0=0 / pre_fps15=0.0） |

绝对根：`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/`

---

## 结论（一句话）

**不是随机导航失败，也不是游戏/资产/harness 代码侧回归。两趟失败趟掉的是发射器命令行里的
`--h7-measure-start-frame 800`（绑帧等待）——即「驱动/命令行层」的回归
（`_launch_h8v4_20261101.py:186-188` 的 `--extra-argv` 缺省为空）。
去掉它以后，settle 4s 一定落在地图加载相位里；而窗前在局闸的 `units0` 取的是 settle
「第一行」计数器（`qc151_trip.harness8_v4.py:5192-5196`），加载期恒为 0 ⇒ 闸门必然判死
（:5197-5199）。游戏其实已经把图载进去了：同一 settle 的 t=2.0/3.0s 计数器写着
units=1440/1451 ≥ W1 门槛 150，所以趟件里「units0<150 ⇒ U0400 档不成立（降级移交 Lead）」
是误报。


---

## 1. 导航链逐字段对比（三趟）

命令：`python -I -X utf8 _cmp_fields.py`、`python -I -X utf8 _dump_groups.py`
（输出：`fields_diff.txt` / `groups_dump.txt`）

432 个 distinct `(group,key)`，三趟键集完全同构（各组计数一致，只有 v4e 多出
`stage_*:measure_w1/w2`、`h7_frame_wait`、`h7_gate_override`、`h8_wait_trace`、
`window_1/2_stats` 等 17 个键——那些全是 `--h7/--h8` 开关带来的产物，不是导航差异）。

| 字段 | v4e | v4f | v4g |
|---|---|---|---|
| `NAV.verify_ok_nav_menu` | true | true | true |
| `NAV.verify_ok_nav_setup` | true | true | true |
| `NAV.verify_ok_nav_start` | true | true | true |
| `NAV.signature_got_nav_menu` | `[61,220,262,304,556]` | 同 | 同 |
| `NAV.signature_got_nav_setup` | `[262,304,556]` | 同 | 同 |
| `NAV.signature_got_nav_start` | `[]` | `[]` | `[]` |
| `NAV.clicked_nav_menu / setup / start` | `[700,218] / [700,304] / [700,262]` | 同 | 同 |
| `NAV.attempts_nav_*` | 各 1 次 try，全 ok | 同 | 同 |
| `NAV.focus_nav_*` | `ok:true, attempts:1, bring_to_top, fg_is_ours:true` | 同 | 同 |
| `NAV.esc_locked` | true | true | true |
| `NAV.verdict` | `"OK"` | `"OK"` | `"OK"` |
| `LA.in_tactical_target` | `"skirmish_setup"` | 同 | 同 |
| `WIN.seconds_to_window` | 25.796 | 29.328 | 28.359 |
| `WIN.window_stabilize_seconds` | 12.843 | 11.875 | 11.89 |
| `BUDGET.stage_seconds:nav_menu` | 3.782 | 3.797 | 3.813 |
| `BUDGET.stage_seconds:nav_setup` | 3.781 | **4.984** | 3.828 |
| `BUDGET.stage_seconds:nav_start` | 3.859 | 3.922 | 3.984 |
| `MEASURE.settle_seconds` | 3.998 | 3.998 | 4.000 |
| `MEASURE.h7_nav_to_measure` | 0.078 s | 0.094 s | 0.110 s |

唯一导航侧抖动：`NAV.wait_screen_nav_setup_post` 在 v4f 用了两轮
（`navsig_nav_setup_post_00_x.png` 未命中 `red_centers=[63,96]`，第 2 轮 `_01_g` 命中），
`nav_setup` 因此多花 1.2s；但重试机制把它兜住了，**链上没有任何一步在三趟之间判定不同**。

`seconds_to_window` / `stage_seconds` 的 1.2–1.7x 差异出现在**导航之前**的 I/O 段
（T0 2.578→3.672/3.375，T1 2.297→3.36/3.453，mother_freeze 1.797→2.985/2.890，
carrier_ownership 7.984→10.203/9.594），nav 三段几乎一致（1.00–1.32x）——
说明 11-04 当天整台机器（至少 harness 自己的文件/注册表操作）比 11-03 慢，与导航无关。

## 2. 异常件：三趟字节相同，且成功趟也有

命令：`python -I -X utf8 -c "…hash + count…"`（见下）+ `grep -c 007CFC9F`

* `except_post_20261103T112149364551.txt`（v4e）
  `except_post_20261104T172914049535.txt`（v4f）
  `except_post_20261104T173316775436.txt`（v4g）
  → 三者 size=26405、**sha256 全部 = `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`**、
  1046 行、`007CFC9F` 各出现 3 次（头行 / `Eip:` 行 / `Bytes at CS:EIP` 行）。
* 内容：一条 `EXCEPTION_SINGLE_STEP` @ `007CFC9F`，`Internal Version 1.001`。
* 三趟 `except_set_diff.json` **逐字相同**：`pre_line_count=1046, post_line_count=1046,
  new_line_count=0, new_exception_count=0, no_new_exception=true`。
* 全库普查：`lead/` + `out/re_work/…/qc161_u0400_trip/` 下 **112 个 `except_post_*.txt`
  只有 1 个 distinct sha256**（`6694b75e46a6e773…`），112/112 都含 `007CFC9F`，112/112 都是 1046 行。

⇒ `007CFC9F` 是随载体一起带进来的**静态残留件**（跑前=跑后，一条都没新增），
在每一个成功趟里同样存在。**它不是失败原因，也没有任何判别力。**
`TERM.termination_verdict=PASS`、`wait_returncode=1` 三趟一致 ⇒ 收尾正常，无崩溃痕迹。

## 3. `pre_fps15=0.0` 是「读了但不动」，且那个 2001 采样根本不是 25s 窗

命令：`python -I -X utf8 -c "…samples.f Counter…"`

| | v4e | v4f | v4g |
|---|---|---|---|
| `measure_w0.json.span_s` | **25.0** | **4.0** | **4.0** |
| `samples` 条数 | 12502 | 2001 | 2002 |
| `samples.f` 取值种数 | 783 | **1** | **1** |
| `f` 区间 | 925 → 1707 | **0 → 0（全 0）** | **0 → 0（全 0）** |
| `hz_effective` | 500.1 | 500.5 | 500.5 |
| `counters[0].ws_kb / pf_kb` | 137712 / 123440 | 123584 / 111056 | 123712 / 111536 |

* 失败趟的 `measure_w0.json` **不是采样窗**，是 settle：harness:5241-5256 在 `no_advance`
  分支里写的是 `"span_s": MEASURE_SETTLE_S`（=4.0）＋ settle 样本。台账里
  「窗内 2001 个采样」= 4.0s × 500Hz，不是 25s 窗。
* 采样环跑得动（500.5Hz）、`ReadProcessMemory` 读得到（ws/pf 是像样数值且逐行变化）
  ⇒ **「读了但不动」**，不是「游戏没跑」。
* 成功趟 v4e 一上来就是 **925，不是从 0 涨上去**：因为它带了
  `--h7-measure-start-frame 800`，`h7_frame_wait = {reached_frame:800, wait_s:37.073,
  poll_count:14819}`（`l3_1101v4e/h8_wait_trace.json` 逐拍：起点 0.0006s→800@37.0729s）。
  同一条 trace 里 **f 从 0 跳到 1 的时刻是 3.1936s**（0 值连续 1275 拍）。
  ⇒ 也就是说：**导航结束后的头 ~3.2s 里 CurrentFrame 本来就该是 0（还在加载/简报屏）**。

### 闸门为什么「必然」判死（独立复算）

`python -I -X utf8 _gate_replay.py`（谓词照 `qc151_trip.harness8_v4.py:5183-5199` 重写，
断言：所有 `no_advance` 趟的 w0 载荷就是 settle，重算的 `pre_fps15` 与 `units0` 与
`gate` 完全一致——脚本内 assert 通过）：

| dir | verdict | 带 `--h7` | 重算 pre_fps15 | units0(第一行) | f[0] | 首个 units>0 时刻 | 首个 f>0 时刻 |
|---|---|---|---|---|---|---|---|
| l1_20261023e1 | no_advance | False | 5.342 | 0 | 0 | t=2.001s (units=960) | 3.781s |
| l1_20261023hb | no_advance | False | **26.691** | 0 | 0 | t=1.002s (units=499) | 2.558s |
| l1_20261023k | no_advance | False | 12.086 | 0 | 0 | t=2.027s (units=971) | 3.266s |
| **l3_1101v4f** | no_advance | False | 0.0 | 0 | 0 | **t=2.003s (units=1440)** | **4.0s 内从未** |
| **l3_1101v4g** | no_advance | False | 0.0 | 0 | 0 | **t=3.002s (units=1451)** | **4.0s 内从未** |
| l3_1101v4c | ok | True | 18.358 | 1211 | 869 | 0.0s | 0.0s |
| l3_1101v4d | ok | True | 31.159 | 1198 | 920 | 0.0s | 0.0s |
| l3_1101v4e | ok | True | 31.289 | 1157 | 925 | 0.0s | 0.0s |
| l3_1101v3a / v3b | ok | True | 11.823 / 17.335 | 1336 / 1338 | 434 / 454 | 0.0s | 0.0s |
| l3_20261031hb | ok | True | 6.34 | 1341 | 437 | 0.0s | 0.0s |
| l1_20261023e4 | ok | **False** | 29.293 | 697 | **2821** | 0.0s | 0.0s |
| l3_20261023q / r | ok | **False** | 31.114 / 31.247 | 953 / 923 | **2955 / 3100** | 0.0s | 0.0s |

* `units0` 的定义（harness:5192-5196）= settle 计数器**第一行**的 `units`；`gate_ok`（:5197-5199）
  要求 `pre_fps15 ≥ 3.0` **且** `units0 > 0`。
* 不带 `--h7-measure-start-frame` 时 H8 绑帧块「缺省 None ⇒ 本块零执行」（harness:5037-5044），
  settle 起点 = nav 结束后 **0.094 / 0.110s**（`h7_nav_to_measure`）⇒ 第一行必落在加载相位 ⇒
  `units0 = 0` ⇒ 闸门判死。
* **fps 从来不是卡点**：2026-10-23 三趟 pre_fps15 = 5.3 / 26.7 / 12.1 全都 ≥3.0，照样 `no_advance`。
  「settle 起点落在加载相位」的 5 趟 **5/5 全灭**；唯二不带 `--h7` 还成功的 e4/q/r，
  它们的 settle 起点 f=2821/2955/3100（早就不在加载期了，趟长 245-256s vs 失败趟 47-49s）。

⇒ **直接死因 = 在加载相位里开窗采样；这是命令行/驱动层面的回归，且是确定性的，不是随机的。**

### 发射器侧证据（回归落点）

命令：`python -I -X utf8 -c "…sha256/argv…"`

* 三趟 `_launch_result.json` 的 `harness` 全部 =
  `D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`、
  `harness_sha16` 全部 = `38244d2907e7f7fa`；本目录重算该文件 sha256 =
  `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`（前 16 位吻合，
  文件 mtime 2026-11-01 08:25，**跑 v4e 与跑 v4f/v4g 用的是同一个字节流** ⇒ 不是 harness 代码回归）。
* argv 差异只有两项：v4e 尾部有 `--h7-measure-start-frame 800 --h8-wait-trace`，
  v4f/v4g **两项都没有**；其余（target-map/target-sha256/carrier-create-from/
  carrier-create-files/measure/fullscreen/evid-diff/probe-frames）逐字相同。
* 这两项来自发射器的 `--extra-argv`：`_launch_h8v4_20261101.py:186-188`
  `ap.add_argument("--extra-argv", default="", help="… 如 --h7-measure-start-frame 400")`，
  `:203` `extra_argv = [x for x in _a.extra_argv.split() if x]` ⇒ **缺省为空**，
  谁在发射时忘了带这段字符串，绑帧就整块不执行。回归点在**操作/驱动层**，不在 harness 代码里。
* 附带一条台账卫生问题（不影响判定）：`:200-201` 目录/趟号模板把日期**硬编成 1101**
  （`"l%s_1101v4%s"`、`"-V4-20261101"+suffix`），所以 11-04 跑的两趟 trip_id 仍写
  `…20261101F/G`，而 `META.started` 是 `2026-11-04T17:28:24 / 17:32:29`——
  按 trip_id 找「今天的趟」会找不到。
* 旁证：`s4_module_table.txt` 里 v4e 5 个模块、v4f 10 个、v4g 11 个（v4g 多一条
  `apphelp.dll`），三趟 `S4.ra2loader_hits=[]`、`S4.ra2render_hits=[]`、`S4.s4_gate="pass"`、
  `S4.hit_count=0` ⇒ 三趟都是原版直启、零注入，注入环境没有差异（模块数只差在采样时刻）。

## 4. 截图：三趟同一张画面，分叉点在截图之后

命令：python 逐文件 sha256 + `numpy` 逐像素差（`PIL`，800×600×3）

| 文件 | 三趟 sha256 | 逐像素差 |
|---|---|---|
| `frame_target_01.png` | **三趟全等** `b633740a547d8097b80c323dff8136339f96f603b31e71e18357f959addb54c1` | v4e↔v4f / v4e↔v4g / v4f↔v4g 全部 `maxdiff=0`，差异像素 0/480000 |
| `navsig_burst_00_g.png` | **与上面同一个 sha256**（同图） | 同上，0 |
| `fs_boot_probe.png` | 三个不同 sha | v4f↔v4g 仅 460 像素（0.096%），v4e↔v4f 113164 像素（23.58%） |
| `frame_early_01.png` | 三个不同 sha | 开机早期相位，非分叉证据 |
| `navsig_nav_setup_post_00_g.png` | v4e=192138 / v4g=192065；v4f 无此文件（该轮 `_00_x` 未命中） | — |

* `frame_target_01.png`（三趟同图，也就是 burst 那张）打开来看是**遭遇战加载/简报屏**：
  黑底紫网格 + 蓝色选择条「步兵」+ 一行蓝字 `MISSING:'LoadBrief:USA'`。
  成功趟 v4e 的 target 截图**也不是战术地图**。
* `NAV.post_start_burst` 三趟记录完全相同：`{k:0, png:"navsig_burst_00_g.png",
  red_centers:[], tactical_colors:10168, hit:true}` —— 三趟都在**第一拍**就把这张
  加载屏判成了 `battle`。查 harness：burst 的可插拔缝在 `--spot-select` 关（缺省，三趟 argv
  都没有这个旗标）时直接走锚实现（`qc151_trip.harness8_v4.py:3581-3583`），
  锚判据 = `centers == [] and colors >= TACTICAL_COLOR_FLOOR(=600)`（:2922 / :2792）。
  加载屏 10168 ≥ 600 ⇒ 假阳性命中。记录里**没有** `frame_clock`/`criterion` 键，
  证明确实是锚判据在跑，而不是 QC210 的帧钟判据。
  ⇒ 「nav verdict=OK / burst ok」**不能**作为「已进图」的证据。
* ⇒ 三趟在截图时刻还在**同一屏**，结果却分叉：分叉点在 burst/frame 截图之后，
  即「闸门采样的时刻」，与画面、与点击、与游戏状态都无关。

## 5. 历史同类普查（全库）

命令：`cmd //c "dir /s /b measure_w*.json"` → 241 个文件 / 133 个趟目录 →
`python -I -X utf8 _census.py`（`_census_measure.json`）、`_no_advance.py`

* verdict 分布（241 份 measure_*.json）：`ok` 161 / `no_advance` 45 / `frame_overrun` 23 /
  `frame_wait_timeout` 12。**但这 241 份里只有 118 份在真机趟树
  （`…/qc161_u0400_trip/` 或 `t55*`），其余 123 份在
  `lead/codex_round_20261030/XVERIFY_H8*/` 等 mock/回放件目录；真机趟树去重后
  （按 trip_id+目录+文件+窗）为 `ok` 104 / `no_advance` 12 / `frame_wait_timeout` 2。**
* `units0 == 0` 的只有 **5** 份（真机趟树内，逐份复核）：l1_20261023e1 / hb / k（10-23，harness7，无 `--h7`）
  ＋ v4f / v4g（本次，harness8_v4，无 `--h7`）。
* 其中 **`fmax == 0`（CurrentFrame 整个 settle 从未离开 0）只有 v4f 与 v4g 两份**——
  这两份比 10-23 的同类还更「早」一拍；但死法同族：**采样落在加载期**。
* 其余 `no_advance` 是另一类：f 有值但中途冻结（如 l1_20261023：f 恒 3514、units0=672），
  与本次不同。
* 真实趟的 `frame_wait_timeout` 只有两例（l3_1101v3c n=1200 卡在 1058/120s；
  l3_1101v4b n=800 卡在 271/120s），其余 33 条 overrun/timeout 都在
  `lead/codex_round_20261030/XVERIFY_H8_20261101*/` 的 mock/回放件里，不是真机。
* `007CFC9F` 在全部 112 份 `except_post_*.txt` 里普遍出现（且 112 份字节全等）
  ⇒ **它是加载期（其实是载体自带）的静态残留，不是 v4f/v4g 撞上的新问题。**

## 6. 重跑会不会成功

* **原样重跑（不带 `--h7-measure-start-frame`）：几乎必败。** 机制是确定性的：
  settle 第一行必在加载期 ⇒ `units0=0` ⇒ 闸门 `units0>0` 半条永远不满足。
  历史上「settle 起点落在加载期」的 5 趟 5/5 全灭，包括 fps 达标（26.7）的那几趟。
* **带上 `--h7-measure-start-frame 800`（+ `--h8-wait-trace`，即 v4e 的完整命令行）：
  大概率成功。** harness8_v4 + 800 绑帧的真机趟 v4c / v4d / v4e 全部 `ok`（3/3），
  绑帧实测等待 37.073s 达标、未超时未越界；v4b 是唯一一次 120s 超时（f 卡在 271）。
  也就是说绑帧模式本身仍有失败率（1/4 ≈ 25% 的 `frame_wait_timeout`），
  但它失败时给的是 `frame_wait_timeout`（诚实拒采），而不是 v4f/v4g 这种
  「units0=0 ⇒ 档位不成立」的**假结论**。
* 注意 11-04 当天机器整体偏慢（harness 自身 I/O 段 1.2-1.7x，`seconds_to_window`
  29.3/28.4 vs 25.8，且 4.0s 内 CurrentFrame 仍未离开 0，v4e 是 3.19s 离开）⇒
  不带绑帧时「赌 4s 内 tick 起来」这条线今天比昨天更偏失败一侧。

## 7. 顺手给本线的一条口径提醒（非本次判定，但同源）

`python -I -X utf8 -c "…"` 对 53 份 `verdict=ok, window=0` 的 measure 件算了
`pre_fps15 / stats.fps_avg`：中位比 1.011，但区间 **0.749 – 87.174**（T34 31.388 vs 0.36），
且 `units0` 从 241 到 1352 不等 —— `pre_fps15` 是「settle 末 1.5s 的相位数」，
  对**采样起点落在战斗相位哪里**极敏感，不是负载量。普查里同一趟会成对/成组重复出现：
  241 份文件里 **123 份是 mock/回放件**（19 份 trip_id 为空但数值逐字相同
  `pre_fps15=31.333 / fps_avg=31.0 / units0=1342`，全在
  `lead/codex_round_20261030/XVERIFY_H8_20261031/eq7*/eq8*/rr_fx_ok_*/synth_ok/…`），
  另有 **12 份是同一真机趟的镜像拷贝**
  （`lead/qc161_u0400_trip/l1c_20261021/…` ↔ `out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/l1c_20261021/…`
  这类，l1c/l1d/l1e/l3_20261021/t55k 各一对）。
  ⇒ **241 份 measure 文件 ≠ 241 个独立样本**，做相关系数前必须先按趟去重。

---

## 复现命令（本次实际跑过的）

```
python -I -X utf8 _cmp_fields.py      > fields_diff.txt
python -I -X utf8 _dump_groups.py     > groups_dump.txt
python -I -X utf8 _census.py          > _census_measure.json
python -I -X utf8 _no_advance.py
python -I -X utf8 _trips_census.py     > _trips_census.json
python -I -X utf8 _gate_replay.py
cmd //c "dir /s /b measure_w*.json"   > _list_all_measure.txt        (241 行)
cmd //c "dir /s /b lead\except_post_*.txt /s" + 同 out 树             (112 份)
python -I -X utf8 -c "…sha256 + numpy 逐像素差…"
```

（以上脚本都在本目录：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/`）

未做的检查（如实记录）：
* 未做任何真机重跑来验证「重跑会不会成功」——第 6 节是从 241 份既有真机件的分布推出来的，
  属于 derived 级，不是 byte 级。
* 未解释 11-04 当天机器为何整体偏慢（无当时的主机活动记录可读）。
* `QC213/QC213P2` 探针读数在三趟间的差异（v4g 的 `*_c5574/*_c5588` 全为 0，
  v4e=486/127…）未追：harness:5041-5043 已声明该批探针不承重。
