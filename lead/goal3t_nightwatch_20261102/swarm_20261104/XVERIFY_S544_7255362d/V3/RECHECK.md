# V3/RECHECK.md —— 对 `V3/REPORT.md` 的独立复核

复核员：Qoder（swarm_20261104 / XVERIFY_S544_7255362d / V3 复核席）
日期：2026-11-04
纪律：零真机（未启动/终止任何游戏进程、未读运行中进程内存）；母本与真机数据只读；
只在 `…/XVERIFY_S544_7255362d/V3/`（本件 + `_rc/` 下 9 个自写脚本）落盘；未改台账、未 commit。
所有 python 以 `python -I -X utf8` 执行，全部绝对路径。
**本件里每一个数字都是我从原始 json / png / 源码重算得到的，未采用 REPORT.md 的任何数值。**

被核件：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_7255362d/V3/REPORT.md`

---

## 0. 裁决一览

| 主张 | 核验员判定 | 我的独立判定 | 一句话理由 |
|---|---|---|---|
| V3-A1 导航链 | CONFIRMED | **PARTIAL** | 承重结论成立（三趟导航判定字段全等、失败不在导航）；但「逐字段全等／唯一抖动」被我自己算出的第二个抖动否掉：28 个 NAV 键里 **3 个**取值不同 |
| V3-A2 死因＝命令行漏带绑帧旗标 | CONFIRMED | **PARTIAL** | 机制与身份我全部复现（同字节流 harness、argv 只差 3 token、闸门谓词、5/5 判死、反事实相位）；但支撑它 §6 预测的三条历史统计**都错或已过期**，其中一条被今晚的真机趟 v4h 直接证伪 |
| V3-A3 图其实载入了／TIER_INVALID 是误报 | CONFIRMED | **CONFIRMED** | 逐字段复现，误差 0；我只补一条限度（载入≠开局） |
| V3-A4 崩溃假设被否 | CONFIRMED | **CONFIRMED** | 112/112 一个哈希，我重算一致；「全库」二字实为两个根目录（见 §5.5） |

总判断：**核验员对「v4f/v4g 为什么没出数」的因果结论站得住**；不站得住的是它对**重跑前景**的那一段（§6），
以及 A1 的「全等」措辞与 A2 的普查数字。

---

## 1. V3-A1 · 导航链逐字段对比 —— PARTIAL

我跑的：`python -I -X utf8 D:/…/V3/_rc/rc_a1_nav.py`（自写：三趟 `qc151_fields.json` 全量读入 → distinct (group,key) →
逐键取值三向比较 → NAV 组逐键打 EQ/NE）。

### 1.1 我复现到的（与 REPORT 一致）

```
l3_1101v4e rows = 502 / l3_1101v4f rows = 443 / l3_1101v4g rows = 443
total distinct (group,key) = 432
keys only in v4e = 17 个：BUDGET stage_begin/stage_seconds:measure_w0/w1/w2(6)、MEASURE h7_frame_wait、
  h7_gate_override、h7_nav_to_measure×3、window_1_stats、window_2_stats、META h7_measure_start_frame、
  h8_wait_trace、LAUNCH candidate_ct/pid_30656(2)
```
NAV 组 28 键中 **25 键三趟逐字节相等**，含全部判定字段：
`verify_ok_nav_menu/setup/start = true`、`step_clicked_nav_* = true`、
`clicked_nav_menu/setup/start = [700,218]/[700,304]/[700,262]`、
`attempts_nav_* = 各 1 次 try（focus_ok/post_ok/pre_ok 全 true）`、
`signature_got_nav_menu = [61,220,262,304,556]`、`signature_got_nav_setup = [262,304,556]`、`signature_got_nav_start = []`、
`focus_nav_* = {attempts:1, ok:true, step:bring_to_top, fg_is_ours:true}`、`esc_locked = true`、`verdict = "OK"`、
`post_start_burst = {ok:true, expect:"battle", burst_owned:true, polls:[{k:0, png:"navsig_burst_00_g.png",
red_centers:[], tactical_colors:10168, hit:true, cap_ok:true}]}`。
`LA.in_tactical_target = skirmish_setup`、`LA.features_target.lum_mean = 17.6537`、`MEASURE.protocol.w1_units0_min = 150` 三趟全等。
时刻/时长类：`WIN.seconds_to_window 25.796/29.328/28.359`、`WIN.window_stabilize_seconds 12.843/11.875/11.89`、
`BUDGET.stage_seconds:T0 2.578/3.672/3.375`、`:T1 2.297/3.36/3.453`、`:mother_freeze 1.797/2.985/2.890`、
`:carrier_ownership 7.984/10.203/9.594`、`:nav_menu 3.782/3.797/3.813`、`:nav_setup 3.781/4.984/3.828`、
`:nav_start 3.859/3.922/3.984`、`MEASURE.settle_seconds 3.998/3.998/4.000`、`nav_to_measure_s 0.078/0.094/0.110` —— 全对得上。
v4f 那次两轮重试我读原文核实：`polls = [{i:0, png:"navsig_nav_setup_post_00_x.png", red_centers:[63,96], hit:false},
{i:1, png:"navsig_nav_setup_post_01_g.png", red_centers:[262,304,556], hit:true}]`，且目录里确有 `_00_x.png`（v4e/v4g 无）⇒ 「重试兜住」成立。

三趟共同存在的键 = 411，其中 **125 个取值不同**（核验员自报 146——它的 `_cmp_fields.py` 把「某趟缺键」也算进 diff；
按「三趟都在且值不同」的口径是 125/126（重复键取首/末次出现差 1 个），两种口径都对，只是 REPORT 没写口径）。
125 个 diff 键全部落在 pid／时刻／路径／内存探针／结果层级（NAV 3、MEASURE 9、WIN 10、QC213 18、QC213P2 16、
LAUNCH 6、ISOLATION 5、BUDGET 26、META 5、S4 2、其余为路径/产物）——**导航链上没有一处判定不同**，这点成立。

### 1.2 我算出来它说错的地方（这是 PARTIAL 的唯一原因）

**「唯一抖动」与「逐字段全等」不成立。** 28 个 NAV 键里 3 个不同：

```
NAV differing: ['h7_nav_end_t', 'wait_screen_nav_menu_pre', 'wait_screen_nav_setup_post']
```

1. `h7_nav_end_t = 8733.593 / 12996.109 / 13238.765` —— 开机单调钟，天然不同（属时刻类，可原谅）；
2. `wait_screen_nav_setup_post` —— 就是它讲的那次 v4f 两轮；
3. **`wait_screen_nav_menu_pre` 是它没登记的第二个抖动**：
   v4e/v4f `red_centers = [61, 96, 220, 262, 304, 346, 388, 556]`（8 条），
   **v4g = [61, 220, 262, 304, 346, 388, 556]（少了 y=96 那条）**。
   ⇒ 「三趟一字不差」「唯一抖动：v4f 的 setup_post」两句字面都不成立。
   承重影响：**无**（y=96 不在 `want=[220,262,304,346,388,556]`、不在 `absent=[]`，三趟 hit/ok 均 true，
   `signature_got_nav_menu` 一致 ⇒ 判定不变）。

顺带把它的另一句纠一下：REPORT 说 v4f/v4g 键集与 v4e「同构，只多 17 键」。我实测
v4f/v4g 各少 19 键 = 那 17 个 `--h7/--h8` 产物 + 2 个**别的趟的 pid 键**（`LAUNCH candidate_ct/pid_<其它 pid>`）；
v4f 与 v4g 彼此键集完全相同。表述略粗，不影响结论。

---

## 2. V3-A2 · 死因＝发射器命令行漏带 --h7-measure-start-frame 800 —— PARTIAL

### 2.1 我复现且认为成立的部分

**(a) 不是 harness 代码回归**（两条独立算法一致）：
```
certutil -hashfile lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py SHA256
  → 38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8
python -I -X utf8 → size 489502 | sha16 38244d2907e7f7fa | mtime 2026-11-01 08:25:51
三趟 _launch_result.json 的 harness_sha16 全 = 38244d2907e7f7fa
（旁证：harness8.py = dd5459fe0cf3461c、harness8_v3.py = 37a7c9cdf2ca97e3，排除读错文件）
```
**(b) argv 只差那 3 个 token，其余逐字相同**（我按位置对齐）：
```
v4e argv 24 项，v4f/v4g 各 21 项；v4e 尾部多出 ['--h7-measure-start-frame','800','--h8-wait-trace']
21 项公共段里只有 idx 6/12/14 不同（--carrier 路径、--trip-id、--out-dir）
--target-sha256 三趟 = f3bb0a4efded…；--carrier-create-files 的 sha256[:16] 三趟 = 179c1c0c37b97cff
measure_w0.json 里 gamemd_sha256 三趟 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
⇒ 资产/载体/harness 三趟同一，回归只可能在命令行
```
**(c) 闸门谓词逐行读码核实**（`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`，行号我为它复核过）：
`:3846 MEASURE_SETTLE_S = 4.0`、`:3847 MEASURE_GATE_FPS15_MIN = 3.0`、`:3848 MEASURE_GATE_SPAN_S = 1.5`、
`:3849 MEASURE_W1_UNITS0_MIN = 150`、`:3881 H8_MEASURE_START_FRAME = None`；
`:5037` 块头注释「★ 缺省 None ⇒ 本块零执行」+ `:5044 if H8_MEASURE_START_FRAME is not None:` ⇒ **不带旗标整块不跑**；
`:5184-5191 pre_fps15 = (末帧−首帧)/时长`，取样窗口 = settle 末 `SETTLE−SPAN = 2.5 s 起`；
`:5192-5196 units0 = 第一条 units 非 None 的 settle 计数行（即第一行）`；`:5197-5199 gate_ok = pre_fps15 ≥ 3.0 ∧ units0 > 0`；
`:5205-5209` 绑帧武装时闸门**降级为「帧推进 ∧ units0>0」**（⇒ 旗标的作用是延后采样，不是放宽 units0）；
`:5236-5237 units0<150 ⇒ TIER_INVALID`；`:5241-5262` 不过即 `verdict="no_advance"`、写 `"span_s": MEASURE_SETTLE_S` 的 settle 载荷、`return` 跳全部窗。
**(d) 我独立重算了闸门**（`_rc/rc_a3_gate.py` + 一次性 `-c` 脚本，谓词自写、不复用它）：

| dir | span_s | samples | f 种数 | 我算 pre_fps15 | 件内值 | 我算 units0 | 件内值 | 首个 units>0 | 首个 f>0 |
|---|---|---|---|---|---|---|---|---|---|
| l1_20261023e1 | 4.0 | 2001 | — | 5.342 | 5.342 | 0 | 0 | t=2.000712（960） | 3.7808 s |
| l1_20261023hb | 4.0 | 2001 | — | 26.691 | 26.691 | 0 | 0 | t=1.002048（499） | 2.5583 s |
| l1_20261023k | 4.0 | 2001 | — | 12.086 | 12.086 | 0 | 0 | t=2.027274（971） | 3.2662 s |
| **l3_1101v4f** | 4.0 | 2001 | **1** | 0.0 | 0.0 | 0 | 0 | t=2.003132（**1440**） | **无** |
| **l3_1101v4g** | 4.0 | 2002 | **1** | 0.0 | 0.0 | 0 | 0 | t=3.002314（**1451**） | **无** |

⇒ 五趟重算值与件内 `gate` 完全相等；`units0==0` 的真机趟**恰好这 5 份**（`_rc/rc_denom3.py`），且 `units0==0 ∧ fmax==0` **只有 v4f/v4g 两份**。
**(e) 反事实相位（这条我认为是它最硬的证据，我逐拍重算）**：`l3_1101v4e/h8_wait_trace.json`
14819 拍，`[0.0006, 0]` 起、`[37.0729, 800]` 止，**f==0 连续 1275 拍**、首个 `f>0` 在 **t=3.1936 s**、f 单调不减、distinct f = 801。
⇒ 11-03 那天导航结束后头 ~3.2 s 里 CurrentFrame 本来就是 0 ⇒ 不带绑帧时 settle 第一行必在加载期 ⇒ 判死。
**(f) 回归落点核实**（`lead/goal1_harness8_20261031/_launch_h8v4_20261101.py`）：
`:186-188 --extra-argv default=""`、`:203 extra_argv = [x for x in _a.extra_argv.split() if x]` ⇒ 缺省空；
`:200 OUT_DIR = TRIP / ("l%s_1101v4%s" …)`、`:201 TRIP_ID = … "-V4-20261101" + suffix.upper()` ⇒ 日期硬编 1101，
11-04 两趟 trip_id 仍写 `…20261101F/G` 而 `META.started = 2026-11-04T17:28:24/17:32:29`（我读到）⇒ 台账卫生问题为真。
**(g) 注入环境无差异**：`s4_module_table.txt` 我逐行数 = v4e 5 行、v4f 10 行、v4g 11 行，`apphelp.dll` 只在 v4g；
`S4.ra2loader_hits=[] / ra2render_hits=[] / s4_gate="pass" / hit_count=0` 三趟全等。

### 2.2 我算出来它站不住的部分（三条，都在「历史统计/普查」这一层）

**(1) 「v4b 是唯一一次 120 s 超时、绑帧真机趟 3/3 ok、拒采率≈1/4」——已被今晚的 `l3_1101v4h` 证伪。**
我扫真机趟树 35 个目录时发现它没登记这一趟（`_rc/rc_v4h.py` 输出）：
```
l3_1101v4h  _launch_result.json: harness = qc151_trip.harness8_v4.py, harness_sha16 = 38244d2907e7f7fa, rc 0, dur 191.0
            argv 尾部 = ['--h7-measure-start-frame','800','--h8-wait-trace']   ← 与「恢复 v4e 命令行」逐字相同
            META.started 2026-11-04T18:24:04 / finished 18:26:58（在 v4f 17:28、v4g 17:32 之后）
            MEASURE.verdict = frame_wait_timeout
            h7_frame_wait = {n:800, reached_frame:713, timed_out:true, wait_s:120.002, poll_count:41630}
            h8_wait_trace: 41630 拍，f==0 连续 2965 拍，首个 f>0 在 7.7285 s，119.754 s 才到 713
```
⇒ harness8_v4 + 800 的真机趟实际是 **v4b(超时271) / v4c ok / v4d ok / v4e ok / v4h(超时713) / v4a(rc 63 半路死)**：
completed 5 趟里 2 趟拒采 = **40%**，不是 1/4；「唯一一次超时」为假。
时间线上它的普查脚本跑在 18:04–18:17，v4h 落盘在 18:26–18:27，REPORT.md 定稿 18:41——
即**报告写定时证据已在盘上，只是没进它早先的表**。这是 stale，不是算错，但对「重跑会不会成功」这一问是致命的（见 §3）。

**(2) 「唯二不带 --h7-measure-start-frame 还成功的趟（e4/q/r）」——数目与判级都错。**
我按 `_launch_result.json` 里 argv 是否含 `--h7-measure-start-frame` 给全树打表（`_rc/rc_census.py`），
不带旗标却过了闸的真机趟至少 **8 趟**：
```
l1a_20261020   gate ok, units0 730,  窗 f[0] 3849   l1c_20261021  units0 879, f[0] 957
l1d_20261021   units0 870, f[0] 1095                l1e_20261021  units0 865, f[0] 1158
l3_20261021    units0 1330, f[0] 387                l3_20261023q  units0 953, f[0] 2955
l1_20261023e4  units0 697, f[0] 2821                l3_20261023r  units0 923, f[0] 3100
```
而且其中 `l1_20261023e4`、`l3_20261023r` 的**趟级 `MEASURE.verdict = degraded`**（我读 fields），
只有 w0 的 JSON 内层 verdict 是 `ok`——它的表把两层混写成「ok」。
⇒ 「不带旗标 ⇒ 必死」不是定律；**真定律是「settle 起点落在加载相位 ⇒ 第一行 units0=0 ⇒ 死」（5/5，我复现）**。
REPORT 的 §3 正文其实就是这么写的（它引了 f=2821/2955/3100 与趟长差），但 A2 的 keyFact 写成「唯二」并把 e4/r 记成 ok。
顺带：`l3_20261021` 窗起点 f=387 也过闸（units0=1330），说明加载相位远早于 frame 387。

**(3) 「fps 从来不是卡点」——在其 5 趟内为真，作为一般命题为假。**
```
l3_20261031ha：harness8.py(dd5459fe)、argv 带旗标、gate = {pre_fps15 2.678, units0 1342, ok false}
              ⇒ units0>0，死在 pre_fps15 < 3.0 那一半
```
⇒ 真机趟树里确实存在「units0 正常、fps 判死」的先例。它的 A2 表述「fps 从来不是卡点」应改为
「在 settle 落在加载期的那 5 趟里，fps 达标与否不影响结果（5.342/26.691/12.086 都达标照样死）」。

---

## 3. 单列：§6「重跑会不会成功」—— **REFUTED（按今晚盘上证据）**

核验员结论原话：「原样重跑几乎必败（机制确定 + 历史 5/5）；恢复 v4e 命令行则 harness8_v4+800 真机趟 3/3 ok，
绑帧模式本身约 1/4 拒采率，且拒采时给的是诚实的 frame_wait_timeout」。

我算到的：
* 前半句我认（5/5 + 谓词 + 相位反事实，见 §2.1d/e）。
* 「3/3 ok / 1/4 拒采」**不成立**：v4h（2026-11-04 18:24，恢复旗标后唯一一次重跑）以 `frame_wait_timeout` 收场，
  卡在读数 713；completed 绑帧趟 = 3 ok / 2 timeout（40%）。
* 我还量化了它只定性说过的「今天机器慢」：
  `f` 离开 0 的时刻 v4e=**3.1936 s** vs v4h=**7.7285 s**（2.42×）；
  离开 0 之后的推进速率 v4e = 799 帧 / (37.0729−3.1936) s = **23.58 帧/s**，
  v4h = 712 帧 / (119.754−7.7285) s = **6.35 帧/s**（慢 3.71×）。
  ⇒ 120 s 等待帽今天根本到不了 800（713 为 120 s 内读数）。**恢复旗标不再「大概率成功」**：
  要么把 N 调小（历史上 `--extra-argv "--h7-measure-start-frame 400"` 是 ledger 里的常用值，见 `lead/GOAL_THREE_TARGETS_20261018.md:1197/1214/1417`），
  要么把等待帽加大，要么改成「units0 从 settle 里取第一条 >0 的行」这种相位不敏感谓词。
* 它说「拒采时给的是诚实的 `frame_wait_timeout` 而非假结论」——这句我在 v4b/v4h 两份件上都核实为真
  （v4h `measure_w0.json` 内 `verdict=frame_wait_timeout`、`h8.reached_frame=713`，没写 TIER_INVALID）。

---

## 4. V3-A3 · 「图其实载入了、TIER_INVALID 是误报」—— CONFIRMED

我直接读 `measure_w0.json.counters`（`_rc/rc_a3_gate.py`，逐行原样打印）：
```
l3_1101v4f： t_rel 0.0        units 0     g 0    b 0  techno 0    ws_kb 123584 pf_kb 111056 g_valid false
              t_rel 1.001937  units 0     g 0    b 0  techno 0    ws_kb 127072 pf_kb 114520 g_valid false
              t_rel 2.003132  units 1440  g 1988 b 0  techno 1988 ws_kb 134320 pf_kb 122444 g_valid TRUE
              t_rel 3.00436   units 1451  g 2019 b 0  techno 2018 ws_kb 134860 pf_kb 121936 g_valid TRUE
l3_1101v4g： 0/0/0/1451；1451 那行 t_rel 3.002314, g 2018, ws_kb 134528
件内 w1： {units0:0, valid:false, verdict:"TIER_INVALID", note:"★ units0<150 ⇒ U0400 档不成立…"}
门槛： harness :3849 MEASURE_W1_UNITS0_MIN = 150；三趟 MEASURE.protocol.w1_units0_min = 150（我核 SAME）
```
⇒ **1440/1451 ≫ 150，「档位不成立」是关于这张图的假结论**：规则本身没错（`units0` 按设计就是 settle 第一行，`:5192-5196`），
错在把这个读数当作地图性质。核验员的两条对照我也复现：
* 成功趟同位量级：v4e 件内 `gate.units0 = 1189`（settle，盘上无 settle 载荷，不可独立重算），
  我从 25 s 窗重算 `pre_fps15 = 31.289 / 窗第一行 units = 1157 / stats.logic_frames = 782 / fps_avg = 31.280`（它表里给的就是这组，一致）；
* 「读了但不动」：v4f `samples 2001`、`stats.hz_effective = 500.5`、`stats.note = "frame not advancing"`、
  `max_stall_s = 3.997705`、distinct f = 1（恒 0）、ws_kb 123584→134860 逐行在长 ⇒ 内存读确实在读、进程活着。

**我要补的一条限度（不影响其判定）**：「载入」有证据，「已经在跑这一局」没有——
v4f/v4g 整个 4 s settle 里 CurrentFrame 一次都没推进；v4h 的 trace 显示今天要到 `f=1` 需要 7.73 s。
所以「图载入了」的正确读法是 **地图数据已进内存（units/techno/指针可读且 g_valid 翻真），但 sim 时钟仍未起转**。
另：`h7_nav_to_measure`（nav→measure）三趟 0.078/0.094/0.110 s，说明失败趟确实「紧贴导航结束就开采」。

---

## 5. V3-A4 · 崩溃/异常假设被否 —— CONFIRMED

`python -I -X utf8 _rc/rc_a4_except.py`（我自建枚举 + 哈希，不复用它列的表）：
```
scope = lead/  +  out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip/
except_post_*.txt 命中 = 112
distinct sha256 = 1 → 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251 × 112
行数分布 = {1046 : 112}
三趟目标件：size 26405 / 同一个 sha256 / 1046 行 / 串 007CFC9F 各出现 3 次 / EXCEPTION_SINGLE_STEP 各 1 次
件头核实：'Error code: EXCEPTION_SINGLE_STEP' + 'Exception occurred at 007CFC9F' + 'Internal Version 1.001'
          + 'Release Build: 25 by gsmallwoo - 10/30/2001 - 17:31:36'
三趟 except_set_diff.json（size 311，内容同形）：
  pre_line_count 1046 / post_line_count 1046 / new_line_count 0 / new_exception_count 0 / no_new_exception true
TERM.termination_verdict = PASS ×3，TERM.wait_returncode = 1 ×3
```
⇒ 「静态残留、跑前=跑后、成功趟 v4e 同样带着它 ⇒ 零判别力、非死因」**成立**。
两点如实登记：
1. **它写的「全库普查」实为两个根目录**（keyFacts 里已把 scope 写出，headline 用「全库」二字偏大）。
   我尝试扩到整仓 `dir /s /b *except_post_*.txt`，420 s 未跑完被我终止 ⇒ **超出这两个根的分布我没能复核**（不改变结论：
   112 份里含成功趟 v4e、且三趟 set_diff 证明本次没新增，已足够否掉「崩溃说」）。
2. `007CFC9F` 三处位置的读法（头行 / `Eip:` 行 / `Bytes at CS:EIP` 行）我逐行核到 idx 3、11、17，与其描述一致。

---

## 6. 它「没把像素判据当 OCR / 没把同一张图当多样本」这三查的结果

* **像素判据 vs OCR：没有混用，反而主动降级了它。** 我核实 burst 判据确是像素：
  `harness:2920-2922`（`centers = _red_button_centers(png)`、`colors = _tactical_color_count(png)`、
  `hit = ok_cap and centers == [] and colors >= TACTICAL_COLOR_FLOOR`）、`:2792 TACTICAL_COLOR_FLOOR = 600`、
  `:3581-3583`（`--spot-select` 缺省 off ⇒ 委托锚实现），加载屏 10168 ≥ 600 ⇒ 假阳性。
  它并据「记录里没有 `frame_clock`/`criterion`」断定跑的是锚而非 QC210 帧钟——
  我在 `:3653/:3660` 核到这两键只有 `_burst_battle_qc210_impl` 才写，三趟记录确无 ⇒ 推理成立。
  它还明写「nav verdict=OK / burst ok **不能**作为已进图证据」，方向正确。
  我自己看图核了那张屏：黑底紫网格 + 紫色选择条（「□兵」，首字字模缺失）+ 蓝字 `MISSING:'LoadBrief:USA'` ⇒ **确是加载/简报屏，不是战术地图**。
* **同一张图重复计数：没有当成多样本。** 我逐文件 sha256 + numpy 逐像素：
  `frame_target_01.png` 三趟全等 = `b633740a547d8097b80c323dff8136339f96f603b31e71e18357f959addb54c1`（115981 B, 800×600），
  与 `navsig_burst_00_g.png` **同一字节**（三趟都是），两两 maxdiff=0、差异像素 0/480000；
  `fs_boot_probe.png` 三个不同 sha，v4f↔v4g 仅 460 像素（0.0958%），v4e↔v4f 113164（23.5758%）；
  `navsig_nav_setup_post_00_g.png` v4e 192138 B、v4g 192065 B、v4f 无此文件。
  它把「三趟同图」用来支持「分叉在截图之后」，没有把 1 张图数成 3 个观测 ⇒ 通过。
  （补充：今晚 `l3_1101v4h` 的 target/burst 也是同一张 `b633740a…` ⇒ 同图已扩到 4 趟，仍是一个观测。）
* **样本 vs 总体：它自己主动纠了，且纠得对。** 我复算它的分母（`_rc/rc_denom5.py`）：
  242 份（它 241，差的就是 v4h 的 `measure_w0.json`）= 真机趟树 119 + mock/回放 123（它 118/123）；
  verdict 全量 `ok 161 / no_advance 45 / frame_overrun 23 / frame_wait_timeout 13`（它 161/45/23/12，差 1 = v4h）；
  真机趟树 `ok 104 / no_advance 12 / frame_wait_timeout 3`（它去重后 104/12/2，差 1 = v4h）；
  `lead/` 镜像 12 份 ✓；mock 里 `(pre_fps15 31.333, fps_avg 31.0, units0 1342, ok)` 这一组实际是 **57 份文件 / 19 个目录**
  （它写「19 份」——按目录数是 19，按文件数是 57，即它把重复度**低估了 3 倍**，方向与它的警告一致，不影响结论）。
  `t55k_20261020` 我数到 3 份 measure（它按 t55* 计入真机趟树 ✓），BASE lead 下确有 `t55k_20261020` 目录。
* **相关 vs 因果：** 死因链条（缺旗标→settle 紧贴 nav→第一行在加载期→units0=0→gate 假→w1 TIER_INVALID）
  我逐环独立复现，且 `--h7` 的 gate-override 语义（`:5205-5209` 只降级 fps 半条、保留 `units0>0`）排除了「旗标是放宽门槛用的」这一混淆解释 ⇒ 因果成立。
  唯一被写成因果语气、实际只是相关的是「今天机器慢 ⇒ 更容易赌输」，我把它改成了定量（§3：3.19 s→7.73 s、23.58→6.35 帧/s）。

---

## 7. 我这次没做到 / 没验到的（如实）

1. 整仓 `except_post_*.txt` 分布未跑完（420 s 超时后终止）⇒ A4 的「全库」我只在它声明的两个根内复现。
2. 未做任何真机重跑 ⇒ §6 的判断全部来自盘上既有 242 份 measure 件 + 6 趟 harness8_v4 记录（derived 级）。
3. `l3_1101v4a`（rc 63、`META.finished=None`）为何半路死，我没追（不属被核三趟，且不影响上述四条判定）。
4. 成功趟的 settle 数值（v4e `units0=1189 / pre_fps15=31.395`）盘上没有 settle 载荷 ⇒ 只能引用件内记录，无法独立重算。
5. 11-04 当天机器为何慢，没有主机侧记录可查（与核验员同限）。

---

## 8. 本次实际跑过的命令

```
python -I -X utf8 …/V3/_rc/rc_a1_nav.py           # 三趟 fields 全量比对 + NAV 逐键 EQ/NE
python -I -X utf8 …/V3/_rc/rc_a3_gate.py          # 三趟 measure_w0：重算 pre_fps15/units0/gate/counters
python -I -X utf8 …/V3/_rc/rc_v4h.py              # v4a/b/c/d/e/f/g/h + v3c 的 argv 尾部与 MEASURE 字段
python -I -X utf8 …/V3/_rc/rc_census.py           # 真机趟树 35 目录全量表（verdict/旗标/f[0]/units/趟长）
python -I -X utf8 …/V3/_rc/rc_a4_except.py        # 112 份 except_post 哈希/行数/关键串
python -I -X utf8 …/V3/_rc/rc_screens.py          # 截图 sha256 + PIL/numpy 逐像素差
python -I -X utf8 …/V3/_rc/rc_misc.py             # v4e h8_wait_trace 逐拍 + 门槛常量 + LA/TERM/S4/EXCEPT
python -I -X utf8 …/V3/_rc/rc_denom3.py           # 真机趟树 measure 普查（units0==0 与 fmax==0 交集）
python -I -X utf8 …/V3/_rc/rc_denom5.py           # 242 份 measure 全量 verdict 分布 + mock 同值件统计
python -I -X utf8 …/V3/_rc/rc_dedup.py            # 真机趟树按 (trip_id,dir,file,window) 去重 + 镜像件字节比对
certutil -hashfile D:\…\lead\goal1_harness8_20261031\qc151_trip.harness8_v4.py SHA256
cmd //c "dir /s /b lead\measure_w*.json"  /  "…qc161_u0400_trip\measure_w*.json"   # 138 + 104
```
