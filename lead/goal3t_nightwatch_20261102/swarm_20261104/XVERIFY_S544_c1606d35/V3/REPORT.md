# V3 / §544 核验报告：v4f / v4g 为什么没进图

**方向**：真机分诊：v4f / v4g 两趟为什么没进图，是不是回归
**铁律**：零真机、零母本改动；写域仅 `XVERIFY_S544_c1606d35/V3/`；python 一律 `python -I -X utf8`；绝对路径；全部数字独立重算。
**结论一句话**：**不是随机导航失败，也不是加载期崩溃，而是命令参数回归**——v4f/v4g 丢掉了 `--h7-measure-start-frame 800 --h8-wait-trace` 两个 flag，导致 harness 在「进战斗前、帧钟还没启动」时就开始 4 秒 settle 窗；`units0=0` 只是这个时序错位的下游读数。按 v4e 的原命令重跑可以成功。

---

## 0. 本轮跑过的命令（全部在本次会话实际执行）

```
# 文件清单（绝对路径，find 枚举，含 .git 排除）
find "D:/Project/ra2-campaign-forge" -type f -name "measure_w*.json" -not -path "*/.git/*"   # 241 个
find "D:/Project/ra2-campaign-forge" -type f -name "except_post_*.txt" -not -path "*/.git/*" # 112 个

# 主探针（导航链 / 异常 / gate / 截图哈希+逐像素差）
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V3/v3_probe.py"
  > ".../V3/v3_probe_out.txt"       # 输出 397 行（SECTION 1-4 + SECTION 5 开头；SECTION 5 全库扫描改用下面更快的文件清单法）

# 全库普查（读 measure_files.txt / except_files.txt，避免 os.walk 扫描 .git）
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V3/v3_census.py"
  > ".../V3/v3_census_out.txt"      # 输出 171 行，EXIT=0

# 补充复算（单次 python -I -X utf8 -c，均实际执行）
#  - 三趟完整 argv dump
#  - harness sha256 = 38244d29…；三趟 harness_sha16 对比
#  - v4e h8_wait_trace.json 逐拍帧号分布
#  - 历史 3 趟 + 三目标趟 samples.f / counters 分布
#  - 全库 112 份 except_post sha256 / 地址直方图（修正大小写敏感后的独立复核）
#  - qc151_fields.json 导航链 ask-named 字段与全部 stage 秒数
#  - EXCEPT 母本 / 载体源 except.txt 的 sha256 与地址
```

源码读取：`lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`
`:3831`（CurrentFrame VA）、`:4004-4045`（`_measure_poll_span`）、`:5037-5172`（H8 frame-wait）、
`:5183-5262`（gate 与 no_advance 分支）、`:7784-7803`（U-5 被动 except 基线）、
`:816-844`（`except_set_diff`）、`:7614`/`:7638`（META 装订）、`:7412`/`:7425`（flag 注册）。

---

## 1. `qc151_fields.json` 导航链逐字段差异表

### 1.1 本件点名要求的字段（独立重算，非复述）

| 字段 | v4e（成功） | v4f（失败） | v4g（失败） | 是否相同 |
|---|---|---|---|---|
| `verify_ok_nav_menu` | `True` | `True` | `True` | ✅ SAME |
| `verify_ok_nav_setup` | `True` | `True` | `True` | ✅ SAME |
| `verify_ok_nav_start` | `True` | `True` | `True` | ✅ SAME |
| `signature_got_nav_menu` | `[61,220,262,304,556]` | 同 | 同 | ✅ SAME |
| `signature_got_nav_setup` | `[262,304,556]` | 同 | 同 | ✅ SAME |
| `signature_got_nav_start` | `[]` | `[]` | `[]` | ✅ SAME |
| `in_tactical_target` | `'skirmish_setup'` | 同 | 同 | ✅ SAME |
| `seconds_to_window` | `25.796` | `29.328` | `28.359` | ❌ DIFF |
| `window_stabilize_seconds` | `12.843` | `11.875` | `11.89` | ❌ DIFF |

补充（同样点名/相关性）：`clicked_nav_*`、`focus_nav_*`、`step_clicked_nav_*`、
`attempts_nav_*`、`wait_screen_nav_*` 的 `ok/expect/want/absent` **全部一致**；
唯一导航内部差别是 v4f 的 `wait_screen_nav_setup_post` 有 2 次 poll（第 1 次
`red_centers=[63,96]` hit=False，第 2 次 `[262,304,556]` hit=True），v4e/v4g 各 1 次 poll 即命中——
即 v4f 多等了一拍，**最终仍全部 `ok=True`**，不构成导航失败。

### 1.2 各 stage 秒数（`stage_seconds:*`，独立重算）

| stage | v4e | v4f | v4g | 备注 |
|---|---|---|---|---|
| `carrier_ownership` | 7.984 | 10.203 | 9.594 | f/g 慢 1.6-2.2 s（宿主负载） |
| `T0` | 2.578 | 3.672 | 3.375 | 同上 |
| `mother_freeze` | 1.797 | 2.985 | 2.89 | 同上 |
| `window` | 13.359 | 12.391 | 12.406 | 相近 |
| `nav_menu` | 3.782 | 3.797 | 3.813 | **几乎相同** |
| `nav_setup` | 3.781 | 4.984 | 3.828 | v4f 多 1.2 s（多一拍 poll） |
| `nav_start` | 3.859 | 3.922 | 3.984 | **几乎相同** |
| `frame` | 0.078 | 0.094 | 0.110 | 相近 |
| `measure_w0` | **25.015** | `<MISSING>` | `<MISSING>` | f/g 没有进入 25 s 测量窗 |
| `measure_w1` | **25.016** | `<MISSING>` | `<MISSING>` | 同上 |
| `measure_w2` | **25.031** | `<MISSING>` | `<MISSING>` | 同上 |
| `T1` | 2.297 | 3.36 | 3.453 | — |

`stage_begin:measure_w0` v4e=`78.375`，v4f/g 缺；
`stage_begin:T1` v4e=`153.437`、v4f=`46.14`、v4g=`44.109`（v4e 多出 3×25 s 窗 + 37 s 绑帧等待）。
`_launch_result.json` 的 `duration_s`：v4e `168.6`、v4f `66.4`、v4g `65.8`。

**判定**：导航链（点击序列、签名、verify）三趟**逐字段一致**；差异全部是「时间偏移」和
「下游 measure 阶段是否存在」。分叉点不在导航。

---

## 2. `except_post_*.txt` 与 `except_set_diff.json`

| 趟 | 文件 | bytes | sha256 | `Exception occurred at` | `Eip` | `Error code` |
|---|---|---|---|---|---|---|
| v4e（成功） | `except_post_20261103T112149364551.txt` | 26405 | `6694b75e46a6e773e…` | `007CFC9F` | `007CFC9F` | `EXCEPTION_SINGLE_STEP` |
| v4f（失败） | `except_post_20261104T172914049535.txt` | 26405 | **同一个 sha** | `007CFC9F` | `007CFC9F` | `EXCEPTION_SINGLE_STEP` |
| v4g（失败） | `except_post_20261104T173316775436.txt` | 26405 | **同一个 sha** | `007CFC9F` | `007CFC9F` | `EXCEPTION_SINGLE_STEP` |

逐字节比对：v4e/v4f/v4g 三份 **26405 bytes / 1046 行全等，`diff_line_count=0`**（`v3_probe_out.txt:212-218`）。

`except_set_diff.json` 三趟**同为 311 bytes、同一 sha256 `f4740d25…`**：
`pre_line_count=1046`、`post_line_count=1046`、`new_line_count=0`、`gone_line_count=0`、
`new_exception_lines=[]`、`new_exception_count=0`、`no_new_exception=true`（`v3_probe_out.txt:220-259`）。

进一步溯源（本次会话实际执行）：
- `lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py:7784-7803`：U-5 规则下 harness
  **被动读取载体现有 `except.txt` 作基线，不覆盖写**；
- 载体源 `_src_L3_sf10c_20261021/except.txt` = 26405 bytes / sha `6694b75e…`，
  `007CFC9F` 出现 3 次、地址 `007CFC9F` —— **异常 dump 是载体自带的预置基线**；
- `ra2bench/except.txt`（`EXCEPT_MASTER`，harness `:317-319`）是另一份 26515 bytes /
  sha `ca175a71…`、地址 `006F9DB6`，本支线并不用它。

**关键回答**：v4e（成功趟）**有完全相同的异常**，且三趟 `no_new_exception=true`。
⇒ `007CFC9F` **不是失败原因**，也不是「加载期崩溃」的证据。

全库普查（`v3_census_out.txt:87-104`，修正大小写后）：
`find` 枚举 112 份 `except_post_*.txt`，**112/112 全部含 `007CFC9F`**，
**112/112 的 `Exception occurred at` 都是 `007CFC9F`**，且 **112 份文件只有 1 个
distinct sha256（`6694b75e…`）**。也就是说这是一条**跨所有趟、与成功失败无关的
预置基线路径**，不是 v4f/v4g 新撞上的问题。

---

## 3. `measure_w0.json` 的 `gate`：`pre_fps15=0.0` 是「没跑」还是「读了但不动」

独立重算 `samples.f` 取值分布（`v3_probe_out.txt:265-330`）：

| 趟 | `verdict` | `span_s` | `samples` 数 | `samples.f` distinct | min/max | `gate.pre_fps15` | `gate.units0` | `stats.note` |
|---|---|---|---|---|---|---|---|---|
| v4e | `ok` | **25.0** | 12502 | **783** 个（925…1707） | 925 / 1707 | 31.395 | 1189 | `''` |
| v4f | `no_advance` | **4.0** | 2001 | **1** 个 `{0:2001}` | 0 / 0 | 0.0 | 0 | `frame not advancing` |
| v4g | `no_advance` | **4.0** | 2002 | **1** 个 `{0:2002}` | 0 / 0 | 0.0 | 0 | `frame not advancing` |

- 失败趟 `samples.f` **全 0，没有别的值**，`all_zero=True`，唯一 run = `(0, 0, 2000/2001, 2001/2002)`。
- **成功趟 v4e 一上来就是 925**（`samples.f[0..9]=[925×10]`），**不是从 0 涨上去的**；
  末值 1707，25 s 内 783 个不同帧号、782 次推进。
- v4f/g 的 `samples.t` 是连续 500Hz 墙钟（v4f `12996.237→13000.235`、
  v4g `13238.906→13242.906`），`error=None`、`hz_effective=500.5` ⇒ **读进程内存成功、采样器在跑**，
  是「读了但 `CurrentFrame` 不动」，不是「游戏没跑/进程挂了」。
- 更强的证据：`counters`（1 Hz 副读）在 4 秒里 **units 在涨**：
  v4f `[0, 0, 1440, 1451]`、v4g `[0, 0, 0, 1451]`；`g_valid` 从 False→True。
  ⇒ **地图正在加载、单位正在生成**，只是 `CurrentFrame` 逻辑帧钟尚未启动。

harness 源码 `qc151_trip.harness8_v4.py:4004-4045`：`_measure_poll_span` 每拍
`_rpm_u32(handle, MEASURE_CURRENT_FRAME_VA)`（VA `0x00A8ED84`，源码 `:3831`），
读失败会记 `errs` 并退避；v4f/g `error=None` 说明 2001/2002 拍**全部读到合法 u32=0**。

**判定**：`pre_fps15=0.0` = **读了但不动**，且是「进战斗前的加载相位」，
不是崩溃、不是 RPM 失败。`gate` 在 `qc151_trip.harness8_v4.py:5197-5199` 要求
`pre_fps15>=3.0 ∧ units0>0`，`:5241-5262` 不过即 `verdict=no_advance` 并跳过三窗
——这解释了为什么 f/g 只有 `measure_w0.json`（且 `span_s=4.0` 只含 settle 段）而没有 w1/w2。

---

## 4. 截图 sha256 与逐像素差

`v3_probe_out.txt:336-350`，独立用 PIL+numpy 逐像素重算（800×600=480000 px）：

### `frame_target_01.png` —— 三趟**同一张画面**
| 趟 | bytes | sha256 | pixel_sha256 |
|---|---|---|---|
| v4e / v4f / v4g | 115981 | `b633740a547d8097b80c323dff8136339f96f603b31e71e18357f959addb54c1` | `239fce17f68243e6a311e621193897ed6b9d1a75d91c31b028cccf3812688437` |

三对逐像素差全部 `equal=True, changed_pixels=0/480000, max_channel_diff=0, sum_abs_diff=0`。
`navsig_burst_00_g.png` 亦与它字节/像素全等（同一个 sha）。
目视内容：游戏内**战前简报/加载画面**（`MISSING:'LoadBrief:USA'` 字样、紫色网格），
**不是战斗画面** ⇒ 这张图在「进战斗」之前拍，三趟拍到完全相同的预置帧。

### `fs_boot_probe.png` —— **不是同一张**
| 趟 | bytes | sha256 |
|---|---|---|
| v4e | 295935 | `401498809d301c5829bc9f6c518a90b85a014411e0ba42fcc16c68b7e9095b07` |
| v4f | 287511 | `6b14e32942e3138ff4853835dc04412a5ad81038f5e0f4f80a9cb46216a227bf` |
| v4g | 287530 | `f89fd0fc75c9ac3a5c0c11792d3c09500a86187f9b749d43089f6ad853567eec` |

逐像素差：
- e vs f：`113164/480000 (23.5758%)` 变化、`max_channel_diff=255`；
- e vs g：`113103/480000 (23.5631%)` 变化、`max_channel_diff=207`；
- **f vs g：`460/480000 (0.0958%)` 变化、`max_channel_diff=255`**（几乎相同）。

目视三张都是 YURI 主菜单（同一 UI），差异来自**菜单背景动画的不同帧**。
⇒ `fs_boot_probe` 不能用来判定「同一张画面」，但它证明三趟都成功进到了主菜单。

辅助：`frame_early_01.png` e vs f/g 差 `479999/480000 (99.9998%)`，f vs g 只差
`128/480000 (0.0267%)`；目视 e 是 ZCode 深色 UI、f 是 Antigravity 亮色 UI —— 都是
**宿主桌面窗口**而非游戏画面（宿主争用副产物），不作为分叉证据。

**判定**：`frame_target_01.png` 相同而结果不同 ⇒ **分叉点在截图之后**（与任务书预期一致），
具体是「点击 start 之后到 `CurrentFrame` 开始推进之前」这段加载期。

---

## 5. 历史同类 `units0=0 ∧ verdict=no_advance` 全库清单

`find` 全库枚举 **241** 份 `measure_w*.json`（`v3_census_out.txt:1,5-27`）。
命中 **5 份**，逐份列出：

| # | 趟目录 / `measure_w0.json` | `pre_fps15` | `units0` | `samples.f` 分布 | except 地址 |
|---|---|---|---|---|---|
| 1 | `l1_20261023e1` | 5.342 | 0 | 9 个值，0→8（**有推进**） | `007CFC9F` |
| 2 | `l1_20261023hb` | 26.691 | 0 | 41 个值，0→40（**有推进**） | `007CFC9F` |
| 3 | `l1_20261023k` | 12.086 | 0 | 13 个值，0→18（**有推进**） | `007CFC9F` |
| 4 | `l3_1101v4f` | **0.0** | 0 | **全 0（2001）** | `007CFC9F` |
| 5 | `l3_1101v4g` | **0.0** | 0 | **全 0（2002）** | `007CFC9F` |

（`verdict=='no_advance'` 不限 units0 共 45 份，其余 40 份是 H8 模拟/早相位批，units0=1342 等，
`v3_census_out.txt:29-74` 全表列出。本件要求的口径是 `units0=0`，故以 5 份为准。）

**except 地址回答**：5/5 全部是 `007CFC9F`；再放大到全库 112 份
`except_post_*.txt` 也是 **112/112 = `007CFC9F`、112/112 同一 sha**。
⇒ 按任务书给的判据，**这是一条「已知的、普遍出现的预置基线异常路径」**，
v4f/v4g **没有撞上新问题**（异常维度）。

但必须点明一个**口径陷阱**：这 5 份里前 3 份（10-23，harness7 `d019e8be…`）
是「帧在推进、units 首拍读到 0」；v4f/g 是「帧完全不推进、units 在涨」。
**同为 `units0=0 ∧ no_advance`，机制并不相同**：
- 历史 3 趟 `counters.units` 分别 `[0,0,960,971]` / `[0,499,971,971]` / `[0,0,971,971]`，
  `pre_fps15` 分别 5.342 / 26.691 / 12.086 ⇒ 帧钟已动，`units0` 取的是 settle 首拍
  （harness `:5192-5196` 取 `s_counters` 里第一个非 None units）；
- v4f/g `pre_fps15=0.0`、帧号恒 0、`counters.units` 末尾到 1440/1451 ⇒ **加载期读帧**。

⇒ 不能把 v4f/g 简单归为「历史同类复现」；它们是**新的失败模式（相位过早）**，
只是共用同一份预置异常基线。

---

## 6. ★ 真正的根因：命令参数回归（本件最强发现）

任务书说「同机同命令的上一趟 v4e 是成功的」——**独立复算后这一条不成立**。

三趟 `_launch_result.json` 的 `argv` 逐项对比（本次会话实际 dump）：

| flag | v4e | v4f | v4g |
|---|---|---|---|
| harness 路径 | `qc151_trip.harness8_v4.py` | 同 | 同 |
| `harness_sha16` | `38244d2907e7f7fa` | 同 | 同 |
| `--target-map` / `--target-sha256` | 同 `f3bb0a4e…` | 同 | 同 |
| `--carrier-create-files` | 同 79 件 | 同 | 同 |
| `--measure 1 --fullscreen --evid-diff --probe-frames …` | 同 | 同 | 同 |
| **`--h7-measure-start-frame 800`** | **有** | **无** | **无** |
| **`--h8-wait-trace`** | **有** | **无** | **无** |
| `rc` / `duration_s` | 0 / 168.6 | 0 / 66.4 | 0 / 65.8 |
| `map_sha256` / `gamemd_sha256`（measure_w0） | `f3bb0a4e…` / `73201cc0…` | 同 | 同 |

三趟 harness 文件 sha256 独立重算 = `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`，
与三份 `_launch_result.json` 的 `harness_sha16` 前 16 位一致 ⇒ **不是 harness 版本回归，是调用参数回归**。
`carrier_post_state.json` 三趟 `gamemd.exe` 均 4825360 B / sha `73201cc0…` ⇒ 母本未变。
`qc151_run_log.json` 三趟均 `{"final_exit":0,"cleanup_failures":[]}` ⇒ 进程正常收尾。

把 v4a…v4g 全部拉齐（本次会话实际执行）：

| 趟 | `--h7-measure-start-frame` | `--h8-wait-trace` | `verdict` | `gate.pre_fps15` / `units0` |
|---|---|---|---|---|
| v4a | 800 | 有 | （rc=63，无 measure json） | — |
| v4b | 800 | 有 | `frame_wait_timeout` | `null / null` |
| v4c | 800 | 有 | `ok` | 15.346 / 1229 |
| v4d | 800 | 有 | `ok` | 30.053 / 1225 |
| **v4e** | **800** | **有** | **`ok`** | **31.395 / 1189** |
| **v4f** | **无** | **无** | **`no_advance`** | **0.0 / 0** |
| **v4g** | **无** | **无** | **`no_advance`** | **0.0 / 0** |

**5 趟带 flag → 3 成功（v4c/d/e）+ 1 超时 + 1 rc63；2 趟不带 flag → 2 失败。零反例。**

### 机制链（源码 + 数据闭合）

1. `qc151_trip.harness8_v4.py:5044-5172`：仅当 `H8_MEASURE_START_FRAME is not None`
   才进入绑帧等待环，轮询 `CurrentFrame` 直到 `≥N`（v4e N=800）；
   `:7612-7614` 由 `--h7-measure-start-frame` 装订；`:5205-5218` 同时把 gate 降级为
   「settle 内帧推进≥1 ∧ units0>0」。v4f/g 不带 flag ⇒ **整块零执行**
   （源码 `:5037` 注释「缺省 None ⇒ 本块零执行」）。
2. v4e 的 `h8_wait_trace.json`（实测 14819 拍）：`n=800`、`verdict=ok`、
   `wait_s=37.073`；**前 3.191 秒帧号恒 0**，首个非零 `frame=1` 在 `t=3.1936 s`，
   到 37.073 s 才到 800。即「点击 start → 帧钟启动」本身有 ≈3.2 s 空窗，
   到 800 帧需 ≈37 s。
3. v4e 时序闭合：`h7_nav_end_t=8733.593` + `wait_s 37.073` + `settle 4.0`
   ≈ `8774.666`，实测 `samples.t[0]=8774.780985`；settle 4 s 内帧 800→925
   （125 帧 / 4 s = **31.25 fps**，与 `pre_fps15=31.395` 自洽）。
4. v4f/g 时序：`h7_nav_end_t` 到 `samples.t[0]` 只差 **0.128 s / 0.141 s**
   （`h7_nav_to_measure.nav_to_measure_s` = 0.094 / 0.110）⇒ **点击 start 后立刻开始 4 s settle**，
   整段 settle 落在「帧钟还没启动」的加载期，所以 2001/2002 拍全读到 0。
5. `:5197-5199` gate 不过 → `:5241-5262` 写 `verdict=no_advance` 的 w0（span_s=4.0）并
   `return`，**跳过全部采样窗**（所以 f/g 没有 w1/w2，也没有 stage_begin:measure_w0/1/2）。
6. 与此同时 `counters.units` 从 0 涨到 1440/1451 ⇒ **地图正在载入、单位在生成**，
   不是崩溃；`except_set_diff.no_new_exception=true` 也排除新崩溃。

### 直接原因归类（任务书 6 选 1）

**「其它」——具体是：命令丢了绑帧等待 flag，测量窗起点被提前到「点进去了但地图还在加载、
逻辑帧钟未启动」的相位。** 不是「导航没点进去」（三个 `verify_ok_nav_*` 全 True、
`in_tactical_target='skirmish_setup'`），不是「加载期崩溃」（无新异常、进程 rc=0、
units 在涨），也不是「地图没载」（units 已生成到 1451）——是**测量开始得太早**。

### 重跑一趟是否可能成功

- **按 v4f/g 当前这条无 flag 命令重跑：不可能靠「随机运气」成功到 `ok`**，至少不能稳定成功。
  v4e 的实测轨迹显示帧钟在 start 后 ≈3.19 s 才开始动，而无 flag 时 4 s settle 窗
  在 start 后 0.1 s 就开始、且 gate 只看 settle 末 1.5 s；即使帧钟在 3.19 s 启动，
  settle 内最多剩 0.8 s、`pre_fps15` 也难达 3.0 fps 门槛且 `units0` 取首拍仍为 0
  （`units0>0` 是 gate 硬条件，源码 `:5199`）。这解释了 v4f/v4g **连续两趟同样失败**，
  不是随机导航抖动。
- **恢复 v4e 的完整命令（加回 `--h7-measure-start-frame 800 --h8-wait-trace`）重跑：
  很可能成功**——v4c/v4d/v4e 三趟同配置连续成功，v4b 是 `frame_wait_timeout`
  （绑帧等待超时，属于已知可重试的相位问题，不是 no_advance）。
  注意：这里**没有做真机重跑验证**（铁律 1），结论是基于同配置 3/3 成功的历史证据 +
  源码机制 + 时序闭合的推断，判为「很可能」而非「保证」。

---

## 7. 与 §544 主线的关系（本方向的边界）

本方向（V3）只负责 v4f/v4g 分诊，**不复核** §544 的「活段 fps / 分母 25 s /
跨会话 3 倍 / ρ=0.8925」等主张（那是 V1/V2 的职责）。但有一条必须提醒主线：

**v4f/v4g 这两趟根本不该进入任何 fps 统计池。** 它们的 `measure_w0.json`
`span_s=4.0`（只是 settle 段）、`stats.fps_avg=None`、`verdict=no_advance`、
`logic_frames=0`、无 w1/w2。若 §544 的「慢窗池」把它们按「零推进/停摆尾段」计入，
那是把**门控失败的废趟**当成了「运行后停摆」，属于口径污染。
本轮独立重算：全库 `verdict=='no_advance'` 共 45 份、`units0==0` 共 5 份，
其中 v4f/v4g 是唯一两帧号全 0 且 `pre_fps15=0.0` 的（其余 3 份帧号有推进）。
这一条如实报出，供汇总员处置；**本方向不据此推翻 §544 的 fps 主张**。

---

## 8. 诚实账：本轮没查到 / 没做的事

- **未重跑真机**（铁律 1）。「加回 flag 可成功」是历史 3/3 + 源码机制的推断，不是实测。
- **未确认「为什么 11-04 的命令会丢这两个 flag」**：本轮只读了三趟产物与 harness 源码，
  没有找到 11-04 的调用脚本 / launcher 记录（可能不在本仓库或未落盘）。
  只能判定「参数回归」这个事实，无法归因到人或某次编辑。
- **未做 OCR**：`frame_target_01.png` / `fs_boot_probe.png` 的画面判读靠目视 +
  sha256/逐像素差，没有 OCR 输出。
- `fs_boot_probe.png` 三张 sha 都不同，逐像素差 23.56%/23.56%/0.096%；
  目视同为主菜单，差异判为动画帧，**未做逐像素归因到具体动画元素**。
- 全库 112 份 `except_post_*.txt` 中 `007CFC9F` 普查用 `find` 枚举 + 文件内容读，
  **未校验 `.git` 历史版本**（只读工作树）。
- 本方向的 §544 背景被要求「推翻它」，但本方向的任务是 v4f/v4g 分诊；
  **没有对 §544 的 fps 主张作任何判定**，未推翻也未确认。

---

## 9. 产物清单（均在允许写域内）

- `V3/v3_probe.py` / `V3/v3_probe_out.txt`（397 行，SECTION 1-4 全量输出）
- `V3/v3_census.py` / `V3/v3_census_out.txt`（171 行，SECTION 5/6 全量输出）
- `V3/measure_files.txt`（241 行）/ `V3/except_files.txt`（112 行）
- `V3/REPORT.md`（本文件）
