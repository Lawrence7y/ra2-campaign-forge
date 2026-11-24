# V3 / §544 核验件 独立复核（复核员-V3，2026-11-04）

**被复核件**：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V3/REPORT.md`
（已读全文 345 行；本地 sha256 前 16 = `584b4f9831bab804`）
**铁律遵守**：零真机（未启动 gamemd / ra2loader / YURI，未 taskkill，未读运行中进程内存）；母本与真机 json/png 全程只读；写域仅 `XVERIFY_S544_c1606d35/V3/`；python 一律 `python -I -X utf8`；路径全用绝对路径；未改台账、未 commit。
**独立复算方式**：不采信件中任何数字，直接读原始 `_launch_result.json` / `qc151_fields.json` / `measure_w0.json` / `h8_wait_trace.json` / `except_post_*.txt` / `except_set_diff.json` / `carrier_post_state.json` / `qc151_run_log.json` / `*.png` 与 harness 源码，自己重算。

**范围说明**：任务书给出的「核验员自报结论」JSON 在 V3-A3 之后被截断（末尾停在 `...}, {`），
我只能看到 V3-A1 / V3-A2 / V3-A3 三条完整主张；REPORT.md 正文里没有 `V3-A*` 形式的 ID
（`grep` 结果为空）。本复核即抽这三条最关键的（也是唯一可见的）结论逐条重算。

---

## 0. 本轮实际跑过的命令（全部在本次会话执行）

```
# 枚举三趟/七趟产物、全库文件数
ls -la "D:/Project/ra2-campaign-forge/.../XVERIFY_S544_c1606d35/V3/"
ls -la "D:/Project/ra2-campaign-forge/out/.../qc161_u0400_trip/" 及各 l3_1101v4{a..g}/
find . -type f -name "measure_w*.json" -not -path "./.git/*" | wc -l     # 241
find . -type f -name "except_post_*.txt" -not -path "./.git/*" | wc -l    # 112
find . -type f -name "_launch_result.json" -not -path "./.git/*" > .../V3/_launch_list_recheck.txt   # 45

# 源码
grep -n "h7-measure-start-frame|h8-wait-trace|H8_MEASURE_START_FRAME|..." qc151_trip.harness8_v4.py
     -> 3875/3881/3900/3902/5038/5044/5051/5056/5065/5127/5205/7412/7425/7603/7610/7612/7637/7638
grep -n "tactical_colors|post_start_burst|frame_target_01" qc151_trip.harness8_v4.py
     -> 2909/2930/2937/2951/3591/3595/3652/3662/5550/7388
Read 源码 5030-5269、5180-5264、7775-7824、5535-5562

# 主探针 / 普查脚本（复现）
python -I -X utf8 ".../V3/v3_census.py" > ".../V3/_recheck_census_out.txt"   # EXIT=0, 171 行
diff -q v3_census_out.txt _recheck_census_out.txt                            # IDENTICAL
python -I -X utf8 ".../V3/v3_probe.py" > ".../V3/_recheck_probe_out.txt"      # 被我在 300 s 超时后停止
     # 该脚本 SECTION 5 用 os.walk 扫全库（v3_probe.py:286-345），与 REPORT.md:18 自述一致会卡住；
     # 已产出的 398 行覆盖 SECTION 1-4，逐行与 v3_probe_out.txt 前 398 行完全相同（differing lines count 0）。
     # 我用 12+ 次 `python -I -X utf8 -c` 直接从原始文件重算了 SECTION 1-4 的全部数字，见下。

# 若干独立复算（均为单次 python -I -X utf8 -c，输出见各节）
```

**未做的事（如实报）**：未真机重跑（铁律 1）；`v3_probe.py` 的 SECTION 5/6 全库 os.walk 分支
**未跑完**（超时被我停止，见上），但报告本就把 SECTION 5 改成文件清单法，我另用
`v3_census.py` + 自己的 `find` 枚举独立覆盖了同口径；未查 `.git` 历史版本；未做 OCR；
未对 §544 的 fps 主张作任何判定（不属本方向）。

---

## 1. V3-A1 —— 「同机同命令」不成立：v4f/g 少了两个绑帧等待 flag，属参数回归

**自报 verdict**：REFUTED（对原「同机同命令」前提）。**我的独立判定：PARTIAL。**

### 1.1 站得住的部分：CONFIRMED

`python -I -X utf8 -c` 读七份 `_launch_result.json` 的 `argv` 并按趟号/trip-id 归一化后做
`difflib.unified_diff`，输出**只有三行差异**：

```
---h7-measure-start-frame
-800
---h8-wait-trace
```

`f == g normalized? True`；argc = `24 / 24 / 24 / 24 / 24 / 21 / 21`（a..g）。
`a.count('--h7-measure-start-frame')` = `1,1,1,1,1,0,0`；
`a.count('--h8-wait-trace')` = `1,1,1,1,1,0,0`。所以「v4e 有、v4f/g 出现次数 0」**重算成立**。

非版本回归的三项也重算成立：
- harness 文件 `qc151_trip.harness8_v4.py` 本地 sha256 = `38244d2907e7f7fa3cdd28f2603de432585f7ddd9027e0e0ae6348a0892752a8`，
  前三趟 `_launch_result.json` 的 `harness_sha16` 均为 `38244d2907e7f7fa`；
- `carrier_post_state.json` 三趟 `gamemd.exe` = `4825360 B` /
  `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`；
- `measure_w0.json` 三趟 `map_sha256` = `f3bb0a4efdedd067f5348d3acf01d294c602d3481203cf718809f7ec597b9a36`；
- `qc151_run_log.json` 三趟均 `{"final_exit":0,"cleanup_failures":[]}`。

⇒ **「同机同命令」不成立、差异在调用参数**：CONFIRMED（注意 `harness_sha16` 是趟内记录的字段，
我核对的是当前工作树 harness 文件的 sha；二者一致，但不是运行期快照）。

### 1.2 站不住的部分 ①：「两个绑帧等待 flag」是错的 —— 实际只有一个

读 `qc151_trip.harness8_v4.py`：
- `:5044` `if H8_MEASURE_START_FRAME is not None:` → 整个绑帧等待环 `:5044-5171` 的唯一开关，
  由 `:7612-7614` 的 `--h7-measure-start-frame` 装订；`:5037` 明写「缺省 None ⇒ 本块零执行」；
  `:5205` 的 gate 降级同样只挂在这一个变量上。
- `H8_WAIT_TRACE` 只出现在 `:5056`（`_h8_trace_dump` 是否落盘）、`:5065` / `:5127`（是否 append 轨迹），
  `:7425` 注册、`7637-7639` 装订。它**不改变任何控制流 / gate / 等待时长**，只是记录开关。

⇒ `--h8-wait-trace` 不是「绑帧等待 flag」。报告 §6 标题、§6 机制链第 1 条、
以及「加回 `--h7-measure-start-frame 800 --h8-wait-trace`」把两者并列为原因，属**参数语义误标**。
真正影响结果的只有 `--h7-measure-start-frame 800` 一个。

### 1.3 站不住的部分 ②：「零反例」只是 7 趟样本，不是总体；全库有反例

七趟 `l3_1101v4{a..g}` 是本批次**总体**（`os.listdir` 只有这 7 个 `l3_1101v4*` 目录），
在「同一 harness `38244d29…` + 同一 map」这个限定口径下我重算得到：
带 flag 5 趟 = `ok,ok,ok,frame_wait_timeout,rc63(无 w0)`；不带 flag 2 趟 = `no_advance,no_advance`
（`gate` 分别 `0.0/0` 与 `0.0/0`）。**这个限定口径内「零反例」成立**。

但 `find` 全库 45 份 `_launch_result.json` 重算（`_launch_list_recheck.txt`）给出：
不带两 flag 的 35 趟中 **`verdict=='ok'` 14 趟**（`no_advance` 12、其它 9）；
排除 `XVERIFY_*` 的模拟/合成趟后，真机历史趟仍有 **11 趟 ok**。
其中**同地图 `f3bb0a4e…` 且不带 flag 却 ok** 的真机趟，我逐个读到：

| 趟 | harness_sha16 | `samples.f[0]` | `gate.pre_fps15` | `gate.units0` |
|---|---|---|---|---|
| `l3_20261021` | 无该字段 | 387 | 10.023 | 1342 |
| `l3_20261023q` | `d019e8beecfb5fd8` | 2955 | 31.34 | 974 |
| `l3_20261023r` | `d019e8beecfb5fd8` | 3100 | 30.716 | 941 |

⇒ 若把「丢 flag ⇒ 必然 no_advance」当一般规律读，是**被全库反例推翻的**；报告 §6 只在
v4a..g 表格里写「零反例」，但没有把它明确限定为「同一 harness 版本的 7 趟」，
而 §6 结论段又用「不可能靠随机运气成功到 ok」这种无条件措辞（REPORT.md:293-298）。
这些反例用的是旧 harness（不同 `harness_sha16`），因此**不能**直接否定 v4 批内的因果推断，
但足以否定「无条件不可能」。另有一趟 `l3_20261031ha`（`harness_sha16=dd5459fe…`，
`--h7-measure-start-frame 400` 有、trace 无、同地图）**带绑帧 flag 仍 `no_advance`**
（`pre_fps15=2.678, units0=1342, f0=400, logic_frames=12`），说明 flag 也不是成功的充分条件——
不过报告已用 v4b 的 `frame_wait_timeout` 承认带 flag 会失败，且措辞是「很可能成功」，此点不算反驳。

### 1.4 站不住的部分 ③：相关 → 因果的跨度

flag 与结果在 7 趟里完全共变，但 **flag 同时与「日期/宿主负载」共变**：
v4a..e 是 11-01/11-03，v4f/g 是 11-04；`stage_seconds:carrier_ownership` =
`7.984 / 10.203 / 9.594`（e/f/g）、`seconds_to_window` = `25.796 / 29.328 / 28.359`、
`window_stabilize_seconds` = `12.843 / 11.875 / 11.89`，均为 e 与 f/g 系统性不同。
这不是随机对照：没有 11-04 带 flag 的对照趟，也没有 11-01 不带 flag 的对照趟；
铁律 1 禁止补跑。报告 §8 已承认「未重跑真机」「加回 flag 可成功是推断」，
但 §0 结论句、§6 标题用「**真正的根因**」「**不是…而是…**」的确定因果语气，
比证据强度更硬。**机制链本身有源码支撑**（见下），所以判 PARTIAL 而非 REFUTED。

### 1.5 机制链的数字我逐个重算了，基本对，但有两处小误差

- `h8_wait_trace.json`：`n=800, verdict=ok, wait_s=37.073, samples=14819`；
  帧 0 共 **1275 拍**，最后一拍 `[3.191, 0]`，首个非零 **`[3.1936, 1]`**，
  末拍 `[37.0729, 800]`，distinct frame = **801**（0..800）。⇒ 「前 3.191 s 帧号恒 0、t=3.1936 首个非零」成立。
- `h7_nav_end_t` → `samples.t[0]`：e `8733.593 → 8774.780985` = **41.187985 s**；
  f `12996.109 → 12996.237254` = **0.128254 s**；g `13238.765 → 13238.906296` = **0.141296 s**。
  即 e 的 `41.188`、f/g 的 `0.128 / 0.141` 重算成立。
- 但 `37.073 + 4.0 = 41.073`，与实测 `41.188` 差 **0.115 s**；报告 §6 第 3 条自己写
  `8733.593 + 37.073 + 4.0 ≈ 8774.666` 并注明实测 `8774.780985`，是**近似**；
  而 V3-A1 的 keyFact 写成「41.188 s ＝ 37.073 s 等待＋4 s settle」的等式，严格算不对。
- `measure_w0.json` 三趟 `samples.f`：e `12502` 拍、distinct **783**、min/max `925/1707`；
  f `2001` 拍全 0；g `2002` 拍全 0；`error=None`、f/g `hz_effective=500.5`、
  `stats.logic_frames=0`、`note='frame not advancing'`。⇒ §3 的「读了但不动」成立。
- `counters.units`（含 `t_rel`）：f `[0@0.0, 0@1.0019, 1440@2.0031, 1451@3.0044]`，
  g `[0@0.0, 0@1.0015, 0@2.0022, 1451@3.0023]`；`shape.g_valid` False→True。
  ⇒ 「地图正在加载、单位在生成」成立；`units0` 取首拍非 None 值（`qc151_trip.harness8_v4.py:5192-5196`），
  故为 0，且 `:5197-5199` gate 要求 `pre_fps15>=3.0 ∧ units0>0`，`:5241-5262` 不过即 `no_advance` 并 return。
- **一处口径提醒**：`gate.pre_fps15`（`15.346/1229`、`30.053/1225`、`31.395/1189`）是
  `qc151_fields.json` 里 `MEASURE.gate` 的**记录值**，不是可从 `measure_w0.json` 独立重算的量——
  `measure_w0.json` 存的是 25 s / 4 s 窗样本，settle 的 4 s 样本未写入 payload
  （`:5251-5252` 写的是 `s_samples` 到 w0，但 v4e 的 w0 是 25 s 窗）。
  我用 w0 的 `t/f` 按 `:5186-5191` 公式复算 e 得 **31.289**，与记录值 `31.395` 不同，
  说明该公式不能直接套 w0 样本。因此 V3-A1 keyFact 里这三个数属于「读记录值」，非独立复算。

**V3-A1 综合**：核心事实（命令不同、非版本回归、flag 缺失、时序错位）CONFIRMED；
「两个绑帧等待 flag」REFUTED；「零反例/根因/不可能」是 7 趟样本 + 相关性的过度外推
（全库 14 趟无 flag 却 ok，其中 3 趟同地图），且未做 A/B 重跑。⇒ **PARTIAL**。

---

## 2. V3-A2 —— 「三趟导航链逐字段一致，随机导航失败假设不成立」

**自报 verdict**：REFUTED（对「随机导航失败」）。**我的独立判定：PARTIAL。**

### 2.1 「逐字段一致」字面不成立

用 `v3_probe.py:48-63` 的 `NAV_PATTERNS` 原样重算（`python -I -X utf8 -c`）：
导航链字段并集 **64** 个，其中 **38 个 DIFF**（与 `v3_probe_out.txt:11,77` 的 64/38 一致）。
报告 V3-A2 keyFact 把 38 个 DIFF 概括为「**全部**为时间戳/stage 秒数/measure 阶段存在性」——
我按字段分类重算得到：`stage_begin:*` 17、`stage_seconds:*` 15、
`wait_screen_nav_menu_pre` + `wait_screen_nav_setup_post` **2**、
`h7_nav_end_t` / `h7_nav_to_measure` / `seconds_to_window` / `window_stabilize_seconds` 各 1。
**至少有 2 个是导航内部 poll 内容差异，不是时间戳**：

- `wait_screen_nav_setup_post`：e/g 各 1 拍 `[262,304,556]` hit=True；
  v4f **2 拍**：首拍 `navsig_nav_setup_post_00_x.png` `red_centers=[63,96]` **hit=False**，
  次拍 `navsig_nav_setup_post_01_g.png` `[262,304,556]` hit=True（REPORT.md §1.1 已披露）。
- `wait_screen_nav_menu_pre`（**报告未披露**）：e/f 首拍 `red_centers=[61,96,220,262,304,346,388,556]`，
  **v4g 为 `[61,220,262,304,346,388,556]`，少了 96**；三趟 `ok=True, hit=True` 相同。

另有 `seconds_to_window = 25.796 / 29.328 / 28.359`、
`window_stabilize_seconds = 12.843 / 11.875 / 11.89`、
`stage_seconds:nav_menu = 3.782 / 3.797 / 3.813`、
`nav_setup = 3.781 / 4.984 / 3.828`、`nav_start = 3.859 / 3.922 / 3.984` 全部 DIFF。
⇒ 「逐字段一致」是**被自己的 64/38 表否定的**，只有「点名 9 字段里 7 个 SAME」成立
（我重算：7 SAME，DIFF 的正是 `seconds_to_window` 与 `window_stabilize_seconds`）。
另外 `qc151_fields.json` 存在重复 key（e 76 个 / f,g 各 32 个，`v3_probe.py:24-25` 用
`{e['key']:e}` 取最后一条覆盖），我核对了 64 个导航模式命中的 key **无重复**
（`dup among 64-pattern keys = []`），故此处的 dict 覆盖不影响 64/38 结论。

### 2.2 但「随机导航失败假设不成立」这个结论站得住

我逐字段读三份 `qc151_fields.json` 并重算：
`verify_ok_nav_menu / verify_ok_nav_setup / verify_ok_nav_start` = `True/True/True`（三趟）；
`signature_got_nav_menu=[61,220,262,304,556]`、`signature_got_nav_setup=[262,304,556]`、
`signature_got_nav_start=[]`、`in_tactical_target='skirmish_setup'`（三趟全等）；
`clicked_nav_menu=[700,218]`、`clicked_nav_setup=[700,304]`、`clicked_nav_start=[700,262]`（三趟全等）；
`focus_nav_*` / `step_clicked_nav_*` / `attempts_nav_*` / `wait_screen_nav_setup_pre` /
`wait_screen_nav_start_pre` / `wait_screen_nav_menu_post` / `post_start_burst`（`tactical_colors=10168`、
`red_centers=[]`、`hit=True`）三趟全等；
`NAV.verdict` 三趟均 `'OK'`。
唯一的导航内部差异是上面两处 poll 次数/红钮集，且**最终 `ok=True`、`hit=True` 收敛**。
`stage_begin:measure_w0/1/2` 与 `stage_seconds:measure_w0/1/2` 在 f/g 为 `<MISSING>`，
`stage_begin:T1` = `153.437 / 46.14 / 44.109`，`_launch_result.json` `duration_s` =
`168.6 / 66.4 / 65.8` —— 分叉在导航之后。

⇒ 结论「不是随机导航失败」CONFIRMED；但 headline 的「逐字段一致」REFUTED，
且 keyFact 对 38 个 DIFF 的归类有一处不实（漏 2 个 poll 内容差异、漏报 v4g 的 menu_pre 差异）。
⇒ **PARTIAL**。

---

## 3. V3-A3 —— `007CFC9F` 是预置基线异常，成功趟 v4e 同样有，非失败原因

**自报 verdict**：REFUTED（对「加载期崩溃」）。**我的独立判定：CONFIRMED**（附重复计数口径警告）。

`python -I -X utf8 -c` 逐字节重算：

| 趟 | except 文件 | bytes | lines | sha256 | 占位符命中 |
|---|---|---|---|---|---|
| v4e（成功） | `except_post_20261103T112149364551.txt` | 26405 | 1046 | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` | 3 |
| v4f（失败） | `except_post_20261104T172914049535.txt` | 26405 | 1046 | **同上** | 3 |
| v4g（失败） | `except_post_20261104T173316775436.txt` | 26405 | 1046 | **同上** | 3 |

三份内容逐字节全等 ⇒ `diff_line_count=0`。三行关键内容我直接读到：
`Exception occurred at 007CFC9F`、`Eip:007CFC9F	Esp:00F9C614	Ebp:00F9C634`、
`Error code: EXCEPTION_SINGLE_STEP`。

`except_set_diff.json` 三趟均 **311 B / sha `f4740d25b88f1b42…`**，内容
`pre_line_count=1046, post_line_count=1046, new_line_count=0, gone_line_count=0,
new_exception_count=0, no_new_exception=True`（`method` 为 `collections.Counter 多重集差`）。
载体源 `.../_src_L3_sf10c_20261021/except.txt` = **26405 B / 同一 sha / 占位符 3 次**。
源码 `qc151_trip.harness8_v4.py:7784-7803`：U-5 规则下 `pre_except_txt = _except_pre_path.read_text(...)`
为**被动读取**，`rec.add(...,"baseline_source","passive_read",...)` 并记 `reset_verdict=SKIPPED_U5`，
不覆盖写载体。⇒ 异常 dump 确为载体自带预置件。

全库普查我用自己的 `find` 枚举 + 逐文件读重算：
`extract_files.txt` 112 行、`unique 112`；**112 份只有 1 个 distinct sha256**
（`6694b75e…` 出现 112 次）；`Exception occurred at` 地址直方图 = `007CFC9F: 112`；
占位符命中直方图 `{True: 112}`。全库 `units0==0 ∧ no_advance` 命中 **5** 份
（`l1_20261023e1/hb/k`、`l3_1101v4f/g`），`verdict=='no_advance'` 共 45 份，
`v3_census.py` 复跑 `EXIT=0`、171 行、与 `v3_census_out.txt` 逐字节相同。
前 3 份历史趟 `samples.f` 有推进（distinct 9/41/13，min/max `0-8 / 0-40 / 0-18`，
`pre_fps15` 5.342/26.691/12.086，`counters.units` `[0,0,960,971]` / `[0,499,971,971]` / `[0,0,971,971]`），
v4f/g 全 0 —— 报告 §5 主动指出「同为 `units0=0 ∧ no_advance`，机制并不相同」，
**这一点我重算同意**，报告的口径诚实度较高。

⇒ 成功趟 v4e 有完全相同的异常、`no_new_exception=True`、载体源同 sha、被动基线读取，
故「不是 v4f/g 的失败原因 / 不是加载期崩溃」CONFIRMED。

**⚠ 口径警告（重复计数）**：`112/112` 并非 112 个独立异常样本，而是
**1 份文档 × 112 份拷贝**（`distinct content sha = 1`）；我还查到 6 个重复 basename
（如 `except_post_20261021T184518530551.txt` 在 `lead/qc161_u0400_trip/` 与
`out/re_work/.../qc161_u0400_trip/` 镜像各一份），即至少有 6 份是纯镜像复制。
同理 `frame_target_01.png` 与 `navsig_burst_00_g.png` 在每趟内是**同一张图**
（`b633740a…`，我逐趟重算了 `png count 9/10/9`、`distinct 7/9/8`，重复组含 `b633740a547d`×2）。
报告把这些数表述为「112/112 全部含」「跨所有趟的普遍路径」「三对逐像素差全部 equal」，
虽然 §2 也如实写了「仅 1 个 distinct sha256」、§4 也写了「同一个 sha」，
但「112/112」「5/5」「三对」在读者眼里很容易被当成 112/5/3 个独立样本。
**这不改变结论方向**（1 个预置件反复出现，反而更支持「预置基线」），
但属于任务书点名的「把同一张图/同一份文件重复计数当多个样本」的口径风险，必须标出。

---

## 4. 特别检查：四类陷阱逐项结论

| 陷阱 | 判定 | 依据 |
|---|---|---|
| **像素判据当 OCR** | **未发现冒用** | REPORT.md:328-329 明写「**未做 OCR**：画面判读靠目视 + sha256/逐像素差，没有 OCR 输出」；§4 的「目视内容」「动画帧」用「目视」措辞。`signature_got_nav_*` 是 `red_centers` 红钮中心**像素坐标**（`qc151_trip.harness8_v4.py:2930,3652`），件中称「签名」但未宣称文字识别。`v3_probe.py:131-138` 的 `re.findall` 是**对 .txt 文本**做十六进制地址匹配，不是对 PNG 做 OCR。我另用 Read 工具看了两图：`frame_target_01.png` 确为 `MISSING:'LoadBrief:USA'` 的战前简报/加载画面，`fs_boot_probe.png` 确为 YURI 主菜单，与目视描述相符。 |
| **样本当总体** | **发现，V3-A1** | 「5 趟带 flag→3 成功；2 趟不带→2 失败；**零反例**」只在 7 趟同一 harness 批次内成立；全库 45 份 `_launch_result.json` 中 35 趟不带 flag、14 趟 `ok`（含 11 趟真机）、3 趟同地图 `f3bb0a4e…` 且 ok。报告未写明「零反例」的口径边界，§6 还用「不可能靠随机运气成功」的无条件措辞。另 §5 的「全库普查」把 `XVERIFY_*` 下的 H8 模拟/合成趟计入 45 份 `no_advance`（报告 §5 注已承认「其余 40 份是 H8 模拟/早相位批」）——计入模拟趟本身没错，但不可当真机总体。 |
| **同一张图重复计数当多个样本** | **发现，V3-A3 / §4** | 112 份 `except_post` = 1 个 distinct sha × 112 拷贝（含 6 个镜像重复 basename）；`frame_target_01.png` ≡ `navsig_burst_00_g.png`（同 sha `b633740a…`），三趟「三对逐像素差」其实是**同一张图**的 3 次比较；241 份 `measure_w*.json` 只有 214 个 distinct content sha（最大重复组 3）。报告披露了 sha 相同，但「112/112」「5/5」「三对」的措辞仍有诱导性。 |
| **相关当因果** | **发现，V3-A1** | flag 与结果在 7 趟完全共变，但 flag 与「日期/宿主负载」也完全共变（11-01/03 vs 11-04；`carrier_ownership` 7.984 vs 10.203/9.594；`seconds_to_window` 25.796 vs 29.328/28.359）；没有同日期的 A/B 对照，铁律 1 禁止补跑；报告 §8 已声明未真机重跑、结论为「很可能」，但 §0/§6 用了「真正的根因」「不是…而是…」的确定语气。机制链（`:5044` 零执行 → `:5197-5199` gate → `:5241-5262` return）有源码与时序闭合支撑，故只是**证据强度被高估**，判 PARTIAL 而非 REFUTED。 |

### 另附：图片数值我全部重算过（PIL+numpy，800×600=480000 px）
`frame_target_01.png` 三趟均 `115981 B / sha b633740a… / pixelsha 239fce17…`，
三对 `changed=0/480000, max=0, sum=0`；
`fs_boot_probe.png` e/f/g `295935/287511/287530 B`，三对变化
`113164 (23.5758%) / 113103 (23.5631%) / 460 (0.0958%)`，max `255/207/255`；
`frame_early_01.png` e-vs-f/g `479999/480000 (99.9998%)`、f-vs-g `128/480000 (0.0267%)`。
与 REPORT.md §4 表**逐项一致**。但「f vs g 差异来自菜单背景动画的不同帧」只是
`0.0958%` 像素差 + 目视的**归因推测**，报告 §8:330-331 已承认「未做逐像素归因到具体动画元素」，
本复核同样未做，不把它当已证事实。

---

## 5. 逐条判定汇总

| ID | 自报 verdict | 我的独立判定 | 我重算出的关键数字 |
|---|---|---|---|
| V3-A1 | REFUTED | **PARTIAL** | 归一化 argv 仅差 3 个 token；`harness_sha16=38244d2907e7f7fa`(3/3)、`gamemd.exe=4825360 B / 73201cc0…`(3/3)、`map_sha256=f3bb0a4e…`(3/3)；`h8_wait_trace` 14819 拍/零帧 1275 拍/首个非零 `[3.1936,1]`；nav→measure `41.187985 / 0.128254 / 0.141296 s`；`samples.f` e 783 distinct(925..1707)、f/g 全 0；**但 `--h8-wait-trace` 无控制流作用（只有 1 个绑帧 flag）**；全库 35 趟无 flag 中 14 趟 ok、3 趟同地图 ok；`37.073+4.0=41.073≠41.188` |
| V3-A2 | REFUTED | **PARTIAL** | 64 个导航链字段并集、**38 DIFF**（17 `stage_begin` + 15 `stage_seconds` + 2 `wait_screen_nav_*` poll 内容 + 4 其它）；点名 9 字段 **7 SAME / 2 DIFF**；三个 `verify_ok_nav_*`=True(3/3)、点击坐标/签名/`in_tactical_target` 全等；v4g `menu_pre` 少 `red_centers=96`（报告漏报）、v4f `setup_post` 2 拍(首拍 hit=False) ⇒ 「逐字段一致」不成立，但「非随机导航失败」成立 |
| V3-A3 | REFUTED | **CONFIRMED**（附重复计数警告） | 3 份 except 均 `26405 B / 1046 行 / sha 6694b75e…`、占位符各 3 次、`EXCEPTION_SINGLE_STEP`；3 份 `except_set_diff.json` 均 `311 B / f4740d25… / no_new_exception=True`；载体源 `except.txt` 同 sha；全库 112 份 **1 个 distinct sha**、`ExceptionAddr` 直方图 `007CFC9F:112`；5 份 `units0=0∧no_advance`、45 份 `no_advance`、241 份 measure |

---

## 6. 诚实账

- **未真机重跑**（铁律 1）；「加回 flag 很可能成功」在本复核中仍只是历史 3/3 + 源码机制的推断，未验证。
- `v3_probe.py` 的 SECTION 5/6（`os.walk` 全库）**未跑完**，300 s 超时后由我主动停止；
  已产出的 398 行（SECTION 1-4）与 `v3_probe_out.txt` 前 398 行**逐行相同**；
  同口径改用 `v3_census.py`（`EXIT=0`、输出与 `v3_census_out.txt` 逐字节相同）与我自己的 `find` 枚举覆盖。
- 一次 `os.walk` 全库 `_launch_result.json` 的命令也超时被移到后台，改用 `find` 完成（45 份）；
  该后台任务的结果未用于任何结论。
- 未查 `.git` 历史版本（只读工作树）；未做 OCR；未对 §544 的 fps 主张作判定。
- 任务书给出的自报结论 JSON 被截断，V3-A3 之后若还有主张，本复核**未覆盖**（无法枚举）。
- 本轮在允许写域内新建的文件（仅清单/复现输出，未改任何既有文件）：
  `V3/_launch_list_recheck.txt`、`V3/_recheck_census_out.txt`、`V3/_recheck_probe_out.txt`、`V3/RECHECK.md`。
