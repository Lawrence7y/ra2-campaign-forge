# V1 / §544 口径核验报告

零真机、只读真机 JSON/PNG 与 harness 源码；全部写入仅在本 V1 目录。所有 `python` 均以 `python -I -X utf8` 执行，路径为绝对路径。

## 1. 源码定义（先读源码）

文件：`D:/Project/ra2-campaign-forge/lead/goal1_harness8_20261031/qc151_trip.harness8_v4.py`

- `:4757` `(t_a, f_a), (t_b, f_b) = samples[0], samples[-1]`
- `:4758` `span = t_b - t_a`
- `:4759` `logic = int(f_b) - int(f_a)`
- `:4761-4762` `hz_effective = len(samples) / span`
- `:4765-4771` `frame_edges = [(f, t_first_observed), ...]`（只记 `f` 变化的那次读数）
- `:4784-4790` `logic <= 0` 时 `fps_avg=None`，`span <= 0` 时也不可测
- `:4791` `fps_avg = logic / span`
- `:4794-4802` 对相邻沿：`df == 1` 时 `frame_ms.append((tb - ta) * 1000.0)`；`df > 1` 计 `n_multi_advance` 并整条丢弃；`df <= 0` 不入样
- `:4805-4813` `p50 = _measure_pctl(frame_ms, 0.50)`，`frame_ms_p50=p50`，`fps_p50 = 1000.0 / p50`
- `:4717-4727` `_measure_pctl` 是排序后线性插值分位
- `:4004-4030` `_measure_poll_span` 用 `time.perf_counter()` 定拍，产出 `samples=[(perf_counter, f), ...]`
- `:3843-3845` `MEASURE_HZ=500`、`MEASURE_WINDOWS=3`、`MEASURE_WINDOW_S=25.0`
- `:5308-5333` 每窗调用 25 s 采样，`span_s` 字段写常量 `MEASURE_WINDOW_S`，但 `stats` 用的是 `_measure_stats(w_samples)` 内的实测 `span`
- `:5184-5191` `pre_fps15` 是 settle 尾部 1.5 s 内 `(gate_pts[-1].f - gate_pts[0].f)/(gate_pts[-1].t - gate_pts[0].t)`，与窗内 `live_fps` 不是同一段数据

**一句话定义**：`fps_avg = (末样帧号 − 首样帧号)/(末样 perf_counter − 首样 perf_counter)`，分母是实测采样跨度（正常 25 s 窗约 24.9–25.0 s，并非 JSON 的名义 `span_s` 常量，也并非仅「活段」时间）；`frame_ms_p50` 是 `df==1` 的相邻帧沿时刻差的线性插值中位数；`fps_p50 = 1000 / frame_ms_p50`。

`fps_avg` 与 `fps_p50` 都来自同一套 `time.perf_counter` 与 `CurrentFrame` 读数，但回答不同问题：前者是整窗墙钟期间的平均推进率（把停摆计入），后者是「典型单帧间隔」的倒数（尾段停摆不参与中位数，因为停摆时没有 `f` 变化的沿）。

命令：`Read` 读取上述源码范围；`grep -n "_measure_stats\|MEASURE_HZ\|span_s\|settle_s\|pre_fps15\|MEASURE_WIN\|window_sec\|\"samples\"" .../qc151_trip.harness8_v4.py`（输出见上列行号）。

## 2. 全量枚举与独立复算

命令：

```bash
find "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip" -type f -name "measure_w*.json" | wc -l
find "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip" -type f -name "measure_w*.json" | sort
python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V1/recompute.py" > ".../V1/recompute_out.txt" 2>&1
```

输出（`.../V1/recompute_out.txt`）：

- `:3-5` `TOTAL_FILES=103`，`ROOT_LEVEL_FILES=3`，`SUBDIR_FILES=100`
- `:7` `BAD_SHAPE=0`；`:8-13` 5 条一致性告警，均为可解释的非推进/错误窗：4 个 `frame_edges=None/[]` 的空窗，以及 `l1_20261023e4/measure_w1.json` 的 frame counter 从 3557 回绕到 0（JSON `logic_frames=-3557`、`note=frame not advancing`），不进入可推进窗集合。
- `:14` 名义 `span_s` 分布：`25.0` 89 个、`4.0` 12 个、`0.0` 2 个
- `:15-16` `WINDOWS_WITH_COMPUTABLE_ADVANCE=63`，`WINDOWS_WITHOUT_COMPUTABLE_ADVANCE=40`；后者包括 37 个零推进/空窗、2 个不足 2 样本错误窗、1 个 counter 回绕窗
- `:58-59` 可推进窗实测 `span` 范围 `(3.998143, 24.999961)`；58 个名义 25 s 窗实测 `(24.899944, 24.999961)`，说明 `fps_avg` 分母确为实测跨度而非写死的 25.0
- `:61-126` 63 窗完整三指标表（`fps_avg` / `live_fps` / `fps_p50`），`live_fps` 严格按本件公式 `(末沿帧号 − 首沿帧号)/(末沿时刻 − 首沿时刻)`，沿表来自 JSON `frame_edges` 并与 `samples` 重建沿表逐项核对。
- `:127-129` 阈值 28：`FPS_AVG_LT_28_COUNT=38`，`FPS_AVG_LT_28_AND_FPS_P50_GE_28_COUNT=14`
- `:144` `LIVE_FPS_LT_28_COUNT=26`
- `:171` `FPS_P50_LT_28_COUNT=24`
- `:196` `FPS_P50_NONE_COUNT=0`（在 63 个可推进窗内；全 103 窗另有 40 个 `fps_p50=null`）

### `fps_avg < 28` 但 `fps_p50 >= 28` 的 14 个窗（逐个列名）

| 窗 | fps_avg | live_fps | fps_p50 | max_stall_s | edge_span_s |
|---|---:|---:|---:|---:|---:|
| `archive_T32/measure_w0.json` | 19.280274 | 31.248416 | 30.912857 | 9.574863 | 15.424782 |
| `archive_T33/measure_w0.json` | 17.760271 | 31.300469 | 31.112425 | 10.814527 | 14.185091 |
| `archive_T34/measure_w0.json` | 0.360002 | 33.952014 | 31.608560 | 24.734760 | 0.265080 |
| `archive_T36/measure_w0.json` | 7.120450 | 31.417418 | 30.887554 | 19.332772 | 5.665647 |
| `archive_T38/measure_w1.json` | 1.160035 | 31.457798 | 30.823290 | 24.077365 | 0.921870 |
| `archive_T39/measure_w1.json` | 1.280039 | 31.450002 | 31.339612 | 23.981746 | 1.017488 |
| `archive_T43/measure_w0.json` | 7.280395 | 31.323813 | 31.348454 | 19.188368 | 5.810276 |
| `archive_T47/measure_w0.json` | 23.001589 | 31.283843 | 31.015446 | 6.618178 | 18.380095 |
| `archive_T49_u0800/measure_w0.json` | 12.680338 | 31.141618 | 31.051079 | 14.820029 | 10.179304 |
| `l1_20261023e1/measure_w0.json` | 2.000796 | 2.009701 | 36.030842 | 3.780845 | 3.980692 |
| `l1_20261023hb/measure_w0.json` | 10.002423 | 10.066570 | 30.159999 | 2.558256 | 3.973548 |
| `l1_20261023hc/measure_w0.json` | 5.750154 | 32.256888 | 31.894874 | 3.286867 | 0.713026 |
| `l3_20261023q/measure_w2.json` | 4.800044 | 31.218107 | 31.125014 | 21.155847 | 3.843923 |
| `l3_20261023r/measure_w1.json` | 19.360434 | 31.099081 | 31.000543 | 9.436279 | 15.563161 |

注意：这 14 个并不全是「前 31fps + 尾停摆」。`l1_20261023e1` 与 `l1_20261023hb` 的 `live_fps` 也分别只有 2.009701 / 10.066570，说明 `fps_p50 >= 28` 还可由「少量推进 + 大量停摆 + 中位间隔取自极少数正常帧」造成，不能把 `fps_p50` 高一律解释成「活段健康」。

## 3. 对抗自查：主指标应是谁

`fps_p50` 天然只看 `df==1` 的沿间隔中位数，尾段停摆没有新沿，因而根本不进入分位样本（源码 `:4794-4802`）。把 `fps_p50` 当目标①主指标，会把「前 31 fps、后 20 s 不动」判成「不卡」，等于把用户说的「卡顿」定义改掉；这个窗应算卡顿/停摆，且应单列 `max_stall_s`、结算/终局证据去解释成因，而不是从卡顿池里删掉。

- `fps_avg` 回答「整段墙钟内用户实际拿到多少帧推进」，包含停摆，适合目标①主指标；源码 `:4733` 也明确称其为「主对照指标（总量式，稳健口径）」。
- `fps_p50` 回答「正常推进时的典型帧间隔是多少」，适合区分「全程慢」与「大体正常但尾段停摆」的辅助诊断量。
- `live_fps` 是事后按首末沿切窗的派生量，不是源码 `_measure_stats` 输出的统计量；它可以回答「非零推进阶段内的条件速率」，但把尾段停摆从分母去掉后，不能替代整窗体验指标。源码中没有 `live_fps` 字段（本次对 v4 源码与 103 个 JSON 键的检查均无该字段；全 JSON 键见 `metadata_out.txt`）。

因此 §544 用 `live_fps` 或 `fps_p50` 把低 `fps_avg` 窗整体重判为「假慢」的核心结论被推翻；可保留的有限事实只是：14 个低 `fps_avg` 窗的 `fps_p50 >= 28`，其中 12 个 `live_fps >= 28`（另 2 个不是），这提示需要把「全程慢」与「停摆尾段」分型，而不是改主指标。

## 4. `archive_T34/measure_w0.json` 特别核

命令：

```bash
python -I -X utf8 -c "... 读 archive_T34/measure_w0.json 的 samples.t / samples.f ..." > ".../V1/t34_gap_out.txt" 2>&1
```

输出（`.../V1/t34_gap_out.txt`）：

- `n_samples 12502`，`n_dts 12501`
- `dt_us min 12.000`，`median 2486.000`，`p99 2632.999996`，`max 3886.999999`
- `dt_gt_10ms 0`，`dt_gt_5ms 0`，`dt_gt_3ms 3`
- `dt_sum_s 24.999840000004042`，`wall_span_s 24.999840000004042`
- 10 个恒定帧段；最后一段 `f=302 idx=133..12501 duration_s=24.734760`
- `recompute_out.txt:205-208`：`gap_dt_gt_10ms_count=0`，`gap_dt_gt_10ms_sum_s=0.000000000`，`excess=0.000000000`，`max=0.000000000`

**结论：采样缺口为 0 秒。** 500 Hz 轮询链条完整（最大相邻 `dt=3.887 ms`），低 `fps_avg=0.360002` 不是测量器丢拍，而是 `CurrentFrame` 在 25 s 中只从 293 推进到 302，随后 24.734760 s 保持 302 不动；`fps_p50=31.60856` 只由前 9 个 `df==1` 沿算出。w1/w2 末屏 PNG 显示同一「遭遇战比分」画面（时间 `00:00:10`），w1/w2 JSON 及 `qc151_fields.json:154-160` 记录 `current_frame=302`、零推进、`empty_window=true`。

这正是一个「用户明显卡住/停摆」却会被 `fps_p50` 或 `live_fps` 判成「健康」的反例：T34/w0 的 `live_fps=33.952014` 仅来自 0.265080 s 的 9 帧首末沿；不应据此把该窗从卡顿/停摆证据中剔除。

## 5. 对背景中附带动议的核查（不采信 §544 数字）

命令与输出：

- `python -I -X utf8 .../metadata_out.txt` 对应命令枚举 44 个 `trip_id` 元数据：所有窗 `gamemd_sha256` 均为 `73201cc0...`，`hz=500`，但 `map_sha256` 至少 10 类；`l1c_20261021`（units=881, 10-21）的 map 前缀 `0add791d...`，`l3_1101v4d`（units=1225, 11-01）的 map 前缀 `f3bb0a4e...`，不是同一载体图。
- `python -I -X utf8 .../launch_versions_out.txt` 对应命令枚举 27 份 `_launch_result.json`：`l1c_20261021` 用 `qc151_trip.harness3.py`，`l3_1101v4d` 用 `qc151_trip.harness8_v4.py`；另有 harness6/7/8/v3 等。源码 grep 显示各版本 `_measure_stats` 的 `span`、`fps_avg`、`frame_ms_p50`、`fps_p50` 公式相同，但整条工具链/载体图确实不同，不能把 9.2 vs 31.2 的差直接归因于「同一负载跨会话时段」。
- `python -I -X utf8 .../adversarial_out.txt` 对应命令统计独立性：103 窗分属 44 个 `trip_id`，29 个 trip 有 3 窗；63 个可算窗只来自 34 个 trip。按窗重复计数时 `rho(pre_fps15, live_fps)=0.8717331488140595 (n=63)`；按 trip 均值去重后 `=0.8139209103941468 (n=34)`；仅 25 s 窗 `=0.9583480571138665 (n=58)`；都没有独立复现本件背景声称的 `+0.8925`（本 V1 不负责 V2 的相关系数定稿，此处只报告「该数未被本口径复现」）。
- `pre_fps15` 与 `live_fps` 不是同一个量：源码 `:5186-5191` 用 settle 尾部 1.5 s 的帧差/时差，窗内 `live_fps` 用窗内首末 `frame_edges`；两者都用同一 `perf_counter` 时钟和同一 `CurrentFrame` 计数器，且同一趟 3 窗共享同一个 `pre_fps15`（30 个 trip 的窗内 `pre` 完全相同），所以高相关既有「进局时帧率状态延续」的解释，也有重复计数/同源代码结构，不能当作负载因果的独立验证。源码 `:5197-5224` 还显示 H8 武装时 `pre_fps15` 会「降为数据不设门」。

## 6. 立场汇总

1. `fps_avg` 的分母是实测 `samples[-1].t - samples[0].t`，近似整窗 25 s（或 4 s settle/error 窗），不是硬编码 25.0，也不是「活段」跨度；§544 对分母的定性描述大体成立，但精确措辞应是实测采样跨度。
2. 停摆会稀释 `fps_avg`，14/63 个可推进窗出现 `fps_avg<28` 且 `fps_p50>=28`；但这不能推出「慢窗池大量假货」：停摆本身就是用户可见的卡顿/停摆，`fps_p50` 与 `live_fps` 会把它系统性抹掉。
3. 目标①主指标仍应是 `fps_avg`（并同时报 `max_stall_s`、零推进窗数、结算/终局证据）；`fps_p50`、`live_fps` 只能作分型/诊断，不能改掉「卡顿」定义。
4. `archive_T34/w0` 无采样缺口，0 秒；它用完整 500 Hz 采样证明帧钟停摆 24.734760 s，是反例而非「假慢」证据。
5. 背景里的「同负载跨时段 3 倍差」和 `rho=+0.8925` 在本 V1 的独立复算中未作为稳健因果结论成立：比较跨了不同 harness / 不同 map SHA，3 窗/趟重复计数，且相关系数依过滤条件在 0.48–0.96 间变动，未复现 0.8925。

## 产物

- `.../V1/recompute.py`：只读复算脚本
- `.../V1/recompute_out.txt`：全 103 窗枚举、63 窗三指标表、阈值计数、T34 缺口
- `.../V1/t34_gap_out.txt`：T34 采样间隔与恒定帧段
- `.../V1/metadata_out.txt`：44 个 trip 的 map/gamemd/hz/schema 元数据
- `.../V1/launch_versions_out.txt`：27 份启动记录中的 harness 路径与 map SHA
- `.../V1/adversarial_out.txt`：重复计数、相关系数、同负载跨时段比较
- `.../V1/mixed_classification_out.txt`：14 个混合窗的停摆/沿跨度分型
