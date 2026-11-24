# V2 REPORT — 时代效应核验：同负载跨时段差 3 倍，还是被工具链版本混淆了

核验员 V2 · 2026-11-04 · 零真机 / 零改动母本 / 只读真机 json
写域：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V2/`

---

## 0. 语料与口径（先定口径再复算）

语料根目录（由 `xverify_s544.dwf.ts:47` 的 `TRIPS` 常量给出）：
`D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`

```
命令: python -I -X utf8 <V2>/_v2_build.py > <V2>/_v2_data.json
      （脚本内 glob(T/**/measure_w*.json, recursive=True)）
输出: total 103  —  43 个趟目录，103 份 measure_w*.json
      live_fps 可算（>=2 条 frame_edges 且 Δt>0）：64
      gate.units0 非空：99；units0>0：94；units0 与 live_fps 同时可算：64
```

**全部 103 份 JSON 的顶层键普查**（脚本 `_v2_build.py` 输出）：`schema` /
`trip_id` / `map_sha256` / `gamemd_sha256` / `window` / `hz` / `t_clock` /
`t_abs0` / `span_s` / `settle_s` / `gate` / `w1` / `samples` / `counters` /
`stats` / `verdict` / `error` 各 103；`frame_edges` 101；`h8` 2。

> **★ 每份 measure_w*.json 里都没有 `harness_sha16`、没有 `argv`、没有
> harness 版本字段。唯一的 schema 字段是 `schema="MEASURE_V1"`，全库 103/103
> 完全相同**（`_v2_confound_out.txt:1-27`）。故按 ask 第 2 条要求转去趟目录的
> `_launch_result.json` / `qc151_fields.json` 取版本。

`live_fps` 定义按 `xverify_s544.dwf.ts:105`：
`(末沿帧号 − 首沿帧号) / (末沿时刻 − 首沿时刻)`，我直接从每份 json 的
`frame_edges[0]` 与 `frame_edges[-1]` 重算，不采信 json 里的 `stats.fps_avg`。

**§544 的 `fps_avg` 分母**：`qc151_trip.harness8_v4.py:4791`
`st["fps_avg"] = logic / span`，其中 `:4757-4758`
`(t_a,f_a),(t_b,f_b) = samples[0], samples[-1]; span = t_b - t_a; logic = f_b - f_a`。
即分母是整窗实测墙钟跨度（≈25 s，不是硬编码 25）。

---

## 1. 按 `gate.units0` 分组（只列出现 >=3 次的档）

全部输出见 `_v2_data.json` 与 `_v2_confound.py` 的分组打印；完整表（含
`(时刻, live_fps, trip_id)`）由以下命令生成：

```
命令: python -I -X utf8 -c <按 units0 分组打印> (见 §8 命令清单 C3)
```

出现 >=3 次的档共 20 个：`0, 241, 242, 251, 491, 702, 732, 842, 866, 874,
881, 941, 974, 1189, 1225, 1229, 1342, 1347, 1349, 1352`。

**关键发现：没有任意一个「完全相同 units0」的档同时含快窗与慢窗且跨日期**
（`_v2_band_out.txt:30-33`）。跨日期的只有 `units0=0`（10-24/25/26，全慢 2.01–10.07，
全为 harness7）与 `units0=1342`（10-21 的 harness3 三窗 8.78–11.98；
10-31 的 harness8 单窗 3.05，两者都慢、且 harness 不同）。
`具有「跨日期 + 又快又慢」的 units0 档数量 = 0`。

### 1.1 §544 点名四个时刻逐窗独立复算（`_v2_final_out.txt:1-16`）

| 时刻 | 窗 | f0→f1 | Δf / Δt | **live_fps** | units0 | pre_fps15 | fps_avg | harness_sha16 | map_sha256 前16 |
|---|---|---|---|---|---|---|---|---|---|
| 11-01 16:48:39 | w0 | 920→1699 | 779 / 24.983436 s | **31.1807** | 1225 | 30.053 | 31.1619 | `38244d2907e7f7fa` | f3bb0a4efdedd067 |
| 11-03 11:20:31 | w0 | 925→1707 | 782 / 24.994881 s | **31.2864** | 1189 | 31.395 | 31.2801 | `38244d2907e7f7fa` | f3bb0a4efdedd067 |
| 11-03 11:20:56 | w1 | 1707→2487 | 780 / 24.969578 s | **31.2380** | 1189 | 31.395 | 31.2021 | `38244d2907e7f7fa` | f3bb0a4efdedd067 |
| 10-21 19:03:51 | w0 | 957→1186 | 229 / 24.833701 s | **9.2213** | 881 | 8.023 | 9.1603 | **None** (harness3) | 0add791d11aea84d |
| 10-31 20:15:34 | w0 | 437→606 | 169 / 24.885573 s | **6.7911** | 1347 | 6.676 | 6.7872 | `dd5459fe0cf3461c` | f3bb0a4efdedd067 |
| 10-31 20:15:59 | w1 | 607→725 | 118 / 24.798287 s | **4.7584** | 1347 | 6.676 | 4.7317 | `dd5459fe0cf3461c` | f3bb0a4efdedd067 |

（`_v2_final.py` 对每个窗二次 `json.load` 原文件重读 `frame_edges` 断言一致，
`_v2_final_out.txt:16`。）

**判定：数字本身复算通过** —— 快侧确实 31.18–31.29，慢侧 9.22 / 4.76–6.79。
但「同负载」不成立：`units0` 分别是 1225 / 1189 / 881 / 1347，快组均值 1207.0、
慢组均值 1114.0（差 7.7%）；`10-21 19:03` 的 `units0=881` **不在 ask 所述
1180–1360 带内**（`_v2_band_out.txt:35-41`）。而且这些窗的 `Δt≈24.8–25.0 s`
就是整窗跨度，`fps_avg` 与 `live_fps` 几乎相等（差 <0.06）：**§544 想用
「停摆尾段稀释」解释的这批对照窗，本身根本没有尾段停摆**（见 §7）。

---

## 2. ★ 混淆排查（必做）：harness 版本表

### 2.1 版本来源

- `_launch_result.json` 全库 28 份，其中 24 份带 `harness_sha16`；4 份
  （`l1b/l1c/l1d/l1e_20261021`、`l3_20261021` 共 5 个目录中的 4+1）**没有
  `harness_sha16` 字段**，只有 `argv[0]` 指向
  `.../qc151_harness_merge_20261021/qc151_trip.harness3.py`。
- 15 个老趟目录（`archive_T*` / `l1a_20261020` / `t55k_20261020` /
  `l1_20261023c` / TRIP_ROOT）**连 `_launch_result.json` 都没有**；
  我遍搜其 `qc151_fields.json`（72 份全库）里所有含 `harness\d*(_v\d+)?\.py`
  的 value，**0 命中**。**这些趟的 harness 版本无法从现有记录确定**，
  只能以 `argv`/时间戳佐证，故下表标 `None`，不猜。
- 独立复算校验：`hashlib.sha256(open(harness8_v4.py,'rb').read()).hexdigest()[:16]`
  = `38244d2907e7f7fa`，与 `_launch_result.json` 记录一致；
  现存 harness3 文件的 sha16 = `5c56dac5c17a2ba4`（仅作为现存文件指纹，
  不证明当时跑的就是这一份，故不填入表）。

### 2.2 快/慢时段 harness 版本表（`_v2_confound_out.txt:29-107`）

| 组 | 时刻(+08) | 趟目录 | units0 | live_fps | `harness_sha16` | harness 脚本 | map_sha256 前16 |
|---|---|---|---|---|---|---|---|
| **快** | 11-01 16:48 | `l3_1101v4d` | 1225 | 31.181–31.268 | `38244d2907e7f7fa` | harness8_v4.py | f3bb0a4e… |
| **快** | 11-03 11:20 | `l3_1101v4e` | 1189 | 31.238–31.286 | `38244d2907e7f7fa` | harness8_v4.py | f3bb0a4e… |
| 快(部分) | 11-01 09:45 | `l3_1101v4c` | 1229 | 18.54→28.42→30.71 | `38244d2907e7f7fa` | harness8_v4.py | f3bb0a4e… |
| **慢** | 10-21 19:03 | `l1c_20261021` | 881 | 9.13–10.04 | **None** | harness3.py | 0add791d… |
| **慢** | 10-21 21:13 | `l3_20261021` | 1342 | 8.78–11.98 | **None** | harness3.py | f3bb0a4e… |
| **慢** | 10-31 20:08 | `l3_20261031ha` | 1342 | 3.05 | `dd5459fe0cf3461c` | harness8.py | f3bb0a4e… |
| **慢** | 10-31 20:15 | `l3_20261031hb` | 1347 | 4.76–10.61 | `dd5459fe0cf3461c` | harness8.py | f3bb0a4e… |
| 慢 | 11-01 07:06/07:10 | `l3_1101v3a/b` | 1349/1352 | 5.89–16.74 | `37a7c9cdf2ca97e3` | harness8_v3.py | f3bb0a4e… |
| 慢 | 10-21 19:25/20:39 | `l1d/l1e_20261021` | 874/866 | 10.27–14.65 | **None** | harness3.py | 0add791d… |

### 2.3 严格共线性判定（`_v2_band_out.txt:1-11`）

在 §544 对标负载带 `units0∈[1180,1360]` 内，对 22 个有效窗做
`快(>=28) / 慢(<15) × v4 / 非v4` 2×2 列联：

```
FAST n=8  : 100% (38244d2907e7f7fa, harness8_v4.py)   [l3_1101v4c/d/e]
MID  n=2  : 1× v3, 1× v4
SLOW n=12 : 0% v4 —— 5× v3(37a7…) + 3× harness3(NO_SHA16) + 4× harness8(dd54…)
2x2: fast_v4=8 fast_nonv4=0 slow_v4=0 slow_nonv4=12
phi = +1.000000   ⇒ 完全共线
FAST 100% v4 = True ; SLOW 0% v4 = True
```

**明确判定：在 §544 自己划定的对标负载带内，快/慢与 harness 版本完全共线
（φ=+1.0）。「同负载跨会话时段 fps 差 3 倍」不是可分立的「时代效应」，
它与工具链版本差异不可分辨；`harness8_v4.py:5200-5218` 还带 H8 在局闸降级
分支，且 `h7_measure_start_frame` 从 400→800 逐版本递增
（`_v2_band_out.txt:13-28`：慢趟 f0=387/957/1095/1158/434/454/437，
快趟 f0=869/920/925），即采样起点相位也随版本变。按 ask 第 2 条，
「时代效应」这个说法在这个带上不成立。**

**范围诚实披露**：若把带放宽到全部 `units0>=800`（`_v2_final_out.txt:18-25`），
`FAST n=16` 中有 5 窗 harness7(`d019e8…`, `l3_20261023q/r`, 10-30) 和
3 窗无版本记录（`t55k`/`l1a`, 10-20)，此时 `phi=+0.601722`，**不是全库完全
共线**。所以「完全共线」严格限于 §544 对标带及其 11-01/11-03 vs 10-21/10-31
这四组对照；全库范围内仍有 fast 非 v4 的反例，不能一概而论。

### 2.4 一个更直接的相位混淆（`_v2_band_out.txt:13-28`）

`qc151_fields.json` 的 `h7_measure_start_frame`：老趟 None、harness8/v3 为 400、
harness8_v4 为 800。快趟首帧号 f0=869/920/925，慢趟 f0=387/434/454/957/1095/1158。
即「快时段」全部在逻辑帧 800+ 之后才开始采窗；「慢时段」全在 400 附近或
不同导航终点采窗。**测量相位与 harness 版本同步变化**，负载档 `units0` 本身也
不等（1189–1225 vs 881–1347），这是第二个未受控变量。

---

## 3. 地图 / 载体 / tz / 机器状态（`_v2_confound_out.txt:1-27`，`_v2_final_out.txt:46-58`）

- `map_sha256` 全库 **10 个不同值**（103 窗）：`f3bb0a4e…` 33 窗、
  `0add791d…` 22、`9a249526…` 12、`93c2974b…` 9、`60cb0262…` 6、
  `6fac3a3e…` 6、`e7dee568…` 6、`be07d2b4…` 3、`e3acc130…` 3、
  `9e33585c…` 3。**地图不是同一个**。
- `gamemd_sha256` 全库 **1 个值** `73201cc0…676`（103/103）—— 母本未变。
- `schema=MEASURE_V1`、`t_clock=time.perf_counter`、`hz=500` 全库各 1 个值。
- **§544 点名四组**：
  - 快 `l3_1101v4d` / `l3_1101v4e`：`f3bb0a4efdedd067…`
  - 慢 `l3_20261031hb`：`f3bb0a4efdedd067…` → **与快组相同**
  - 慢 `l1c_20261021`：`0add791d11aea84d…` → **与快组不同**
  - 故「快/慢地图相同」只在 10-31 那组成立；10-21 那组连地图都换了。
- `_launch_result.json` 的 `--target-sha256` 与 json 的 `map_sha256` 逐趟一致
  （`l1c`=0add…、`l3_20261021`/`l3_20261031hb`/`v4d`/`v4e`=f3bb…）。
- **载体件数**：`carrier_creation_receipt.json` 15 键（早期 `t55k` 为 12 键），
  `MANIFEST.json` 89 个 `sha256` 条目，快/慢趟一致；`measure_w*.json` 的
  `counters` 每窗 25 条（1 Hz 副读）。
- **tz / 机器状态**：`qc151_fields.json` 所有 `ts` 均为 `+08:00`（无 tz 变更记录）；
  `window_stable_rect` 快/慢各趟均为 `[0,0,2560,1440]`、`DPIaware=True`
  （早期 `archive_T38` 为 `[880,420,1680,1020]`）；`restore_verdict:gamemd.exe=PASS`。
  **未找到任何 CPU/内存/AV/宿主负载的机器状态字段**；`_LEADER_HOST_CONTENTION_20261104.md`
  曾把 v4-b 的 9.22 倍慢归为宿主侧 AV 扫描，但那是另一路推测，本 V2 无原始
  记录可复核，故不采信、也不据此下判定。

---

## 4. 相关系数（自己实现 Pearson，未调库；`_v2_corr.py` / `_v2_corr_out.txt`）

实现：`pearson()` 用 `sxy/√(sxx·syy)`，另附自实现平均秩 Spearman 作稳健性检查。

**样本**：`units0` 非空、`live_fps` 可算且 >0、`pre_fps15` 非空 →
`n=63` 窗，`34` 个独立趟。

| 量 | ρ (Pearson) | Spearman |
|---|---|---|
| `ρ(pre_fps15, live_fps)` 全库 | **+0.871733** | +0.753426 |
| `ρ(units0, live_fps)` 全库 | **−0.350093** | −0.429973 |
| `ρ(pre_fps15, units0)` 全库 | −0.457489 | −0.454130 |

**§544 的 +0.8925 可精确复现，但只在把 `units0=0` 的 3 窗排除后**
（口径变体，`_v2_rho_variant` 输出）：`units0>0` → `n=60,
ρ(pre,live)=+0.892512`；此时 `ρ(units0,live)=−0.585139`。
`units0>=800` 子集则 `ρ(pre,live)=+0.943163`。
即该数字对样本筛选敏感，且筛选条件未在 §544 文本里声明。

**固定 harness 版本内 `ρ(units0, live_fps)`**（`_v2_corr_out.txt:8-17`）：

| harness 组 | n | ρ |
|---|---|---|
| `37a7c9cdf2ca97e3` (v3) | 6 | +0.443479 |
| `38244d2907e7f7fa` (v4) | 9 | **−0.370478** (Spearman −0.843274) |
| `LABEL:None` (老趟，版本未知) | 22 | −0.149869 |
| `LABEL:harness3.py` (无 sha16) | 12 | −0.244375 |
| `d019e8beecfb5fd8` (harness7) | 10 | +0.957151 |
| `dd5459fe0cf3461c` (harness8) | 4 | +0.666494 |
| **各组去均值合并 (pooled within-version)** | 63 | **+0.591069** |

（`units0>0` 口径下 pooled within-version = **−0.069509**；harness7 组
`+0.149428`。`_v2_strict_rho` 输出。）

**判定：全库 ρ(units0,live_fps) 的符号与数值在固定版本内、以及换一次过滤
条件后都不稳定（−0.585 → −0.350 → +0.591 → −0.070）。这个「负载→fps」
的相关是被 harness 版本分层驱动的组间效应（Simpson 型），不构成机制证据。**

---

## 5. 同义反复检查（**判定：是同一个量的两次测量**）

源码逐行：

- `qc151_trip.harness8_v4.py:5184-5191`：
  `pre_fps15 = (gate_pts[-1][1] - gate_pts[0][1]) / _gspan`，
  其中 `gate_pts = [(t,f) for t,f in s_samples if t >= t_cut]`，
  `t_cut = t0s + MEASURE_SETTLE_S - MEASURE_GATE_SPAN_S`（`:5186`），
  `MEASURE_GATE_SPAN_S = 1.5`（`:3848`）、`MEASURE_SETTLE_S = 4.0`（`:3846`）。
- `s_samples` 来自 `_measure_poll_span`（`:5175-5176`），其实现 `:4004-4030`：
  `t_now = time.perf_counter()`（`:4022`）、`f = _rpm_u32(handle,
  MEASURE_CURRENT_FRAME_VA)`（`:4025`）、`samples.append((t_now, f))`（`:4030`）。
- 窗的 `frame_edges` 由同一 `_measure_poll_span` 的 samples 经
  `_measure_stats`（`:4767-4770`）差分得到，`live_fps` 由它的首末沿算出。
- `harness3.py:4043-4050` 的 `pre_fps15` 定义**逐字相同**。

⇒ 两者都是「同一进程读同一个 `CurrentFrame` u32 计数器，配同一个
`time.perf_counter` 时钟，Δ帧号/Δ时间」，只是 `pre_fps15` 取 settle 末 1.5 s、
`live_fps` 取整窗 ≈25 s。**同一个量的两次测量（时间窗不同）**，不是两个独立
物理量。

更硬的证据（`_v2_corr_out.txt:26-66`）：
- `pre_fps15` **每趟只有一个值，被复制到该趟全部 3 个窗**：30 个多窗 trip 里
  **30/30 全相同**（`_v2_rho_variant` 输出）。63 个相关性样本里只有 34 个独立
  的 `pre_fps15` 观测 → **重复计数近 2 倍**。
- 快慢两端几乎恒等：`l3_1101v4e` pre=31.395 / live=31.238–31.286（比值
  0.995–0.997）；`t55k` pre=31.401 / live=31.274–31.284（0.996）；
  `l1c` pre=8.023 / live=9.13–10.04（1.14–1.25）。`|Δ| 中位数 = 0.5541`。
- **按趟取均值去掉重复计数后**：`ρ(pre_fps15, live_fps)` 从 +0.871733 降到
  **+0.813921**（n=34 趟，见 `_v2_corr_out.txt:67`）；`ρ(units0,live_fps)`
  从 −0.350093 变 −0.294512。

**判定：`ρ≈0.89` 只说明「这台机器这个会话/这一趟一直这么快或这么慢」，
是会话级基线速度的自相关。它不证明任何游戏机制、不证明负载与帧率的因果、
也不证明「时代」在起作用。** §544 把它当机制证据属于同义反复。

---

## 6. 趟内 vs 趟间方差（`_v2_corr_out.txt:70-125`）

| 量 | 数值 |
|---|---|
| 趟内（同 trip_id 多窗）fps 极差 **中位数** | **0.5697**（n=16 趟），均值 2.7023，最大 12.1657 |
| 趟间（34 个趟均值）极差 | **31.942**（2.010…33.952），趟均值中位数 31.214 |
| 两趟均值 \|差\| 的中位数 | **5.4368**（561 对） |
| 快趟（趟中位 ≥28，n=9）趟内极差中位 | **0.1642** |
| 慢趟（趟中位 <28，n=7）趟内极差中位 | **3.4354** |

**判定：整趟锁定，不是窗内漂移** —— 趟间差（中位 5.44）约为趟内差（中位
0.57）的 9.5 倍。快趟一旦启动就三个窗全 ~31.2（如 `l3_1101v4e`
31.238/31.286/31.273，极差 0.048）；慢趟则三个窗一起慢且波动更大
（`l3_1101v3a` 5.89/14.07/11.62，极差 8.18）。

例外需在结论里扣掉：`l3_1101v4c`（**同一 harness8_v4**）三窗
18.540 → 28.416 → 30.705，趟内极差 **12.166**，是该 v4 版本里唯一从慢
爬到快的趟 —— 说明「同一版本内也可能有大漂移」，因此「整趟锁定」是统计
倾向而非绝对定律；也说明 §544 把快/慢完全归给版本仍过强。

---

## 7. 附加反证：§544 的「停摆尾段稀释」解释不了这批对照窗

本 V2 主责是时代效应，但顺手核了 §544 的核心改判前提（只读复算）：
对 §544 自己点名的四个对照组，`Δt`（末沿时刻−首沿时刻）都在
**24.80–24.99 s**，即首末沿几乎铺满整个 25 s 窗；`stats.fps_avg` 与
我复算的 `live_fps` 差 <0.06（如 `l1c` 9.1603 vs 9.2213；`v4d`
31.1619 vs 31.1807）。**这批「慢」窗并不是被尾段停摆稀释出来的，它们真的
全程以 6–10 fps 推进**（`l3_20261031hb` w1 的 Δf=118 / 24.798 s 亦如此）。
故「慢窗池里大量假货 / 跨时段差是稀释伪影」在这个对照集上不成立；
真正的「尾段停摆稀释」样本在 `archive_T34`（`fps_avg=0.360`、
`frame_edges` 仅 10 条、`max_stall_s=24.735`）等早期归档趟里，
**与 §544 引用的 11-01/11-03 vs 10-21/10-31 四组不是同一批窗**。

---

## 8. 命令清单（全部在此 ask 内实际执行）

| # | 命令 | 输出 |
|---|---|---|
| C1 | `python -I -X utf8 <V2>/_v2_build.py > <V2>/_v2_data.json`（再接 census `-c`） | 103 窗 / 64 可算 live_fps / 99 units0 非空 / 字段普查 |
| C2 | `python -I -X utf8 <V2>/_v2_confound.py > <V2>/_v2_confound_out.txt` | map/gamemd/schema 普查、每趟 harness 表、关键对照、快慢分布 |
| C3 | `python -I -X utf8 -c <按 units0 分组打印>` | 20 个 >=3 次档的全部 (时刻, live_fps, trip_id) |
| C4 | `python -I -X utf8 <V2>/_v2_corr.py > <V2>/_v2_corr_out.txt` | 全库/固定版本 ρ、同义反复逐窗表、趟内趟间极差 |
| C5 | `python -I -X utf8 <V2>/_v2_final.py > <V2>/_v2_final_out.txt` | 四时刻逐窗二次读取复算、2×2 φ=+0.601722（units0>=800）、同 map 版本序列 |
| C6 | `python -I -X utf8 <V2>/_v2_band.py > <V2>/_v2_band_out.txt` | 1180–1360 带内 2×2 **φ=+1.000000**、`h7_measure_start_frame` 相位表、同负载检索 |
| C7 | `python -I -X utf8 -c <rho 变体 / 严格过滤 / 快趟慢趟极差>` | +0.892512 复现条件、pooled −0.069509、快趟 0.1642 / 慢趟 3.4354 |
| C8 | `python -I -X utf8 -c <hashlib sha16>` + `grep -n` 源码 | v4 sha16 复核一致；harness3 现存 5c56dac5…；源码行号 |
| C9 | `grep -n` `xverify_s544.dwf.ts` / `_launch_result.json` / `qc151_fields.json` 普查 | TRIPS 常量、live_fps 定义、版本字段、tz/rect/carrier |
| C10 | `python -I -X utf8 -c <metadata 逐趟>` | tz 全 +08:00、rect、DPI、carrier 15 键、MANIFEST 89 sha |

**未运行 / 无法完成的检查（如实声明）**：
- 未启动任何 gamemd.exe / ra2loader.exe / YURI，未 taskkill，未读运行中进程
  内存（铁律 1）。全部结论来自离线 json / 源码 / 元数据文件。
- 15 个早期趟目录无 `_launch_result.json`，`qc151_fields.json` 内亦无 harness
  路径/哈希值：**它们的 harness 版本无法从现有记录确定**，本报告一律标
  `None`，未做推测填空。
- 未找到 CPU/内存/宿主 AV/进程争用的机器状态原始字段；故「宿主争用」这类
  第三变量本 V2 不能排除也不能确认（诚实标为不可判定，不作为判定依据）。
- 未做 PNG 目视/像素比对（本 ask 未要求，且第 3 条只问 json 的 map_sha256
  等字段）。

---

## 9. 五条判定汇总

1. **CONFIRMED（数据）**：§544 点名四时刻的 fps 数字全部逐窗复算通过
   （31.1807/31.2864/31.2380 vs 9.2213/6.7911/4.7584）。
2. **REFUTED（时代效应）**：在 §544 对标带 units0∈[1180,1360] 内，
   快/慢与 harness 版本 **φ=+1.000000 完全共线**；且「同负载」不成立、
   地图与采样起始帧相位也变。时代效应不可与版本效应分立。
3. **REFUTED（机制证据）**：`ρ(pre_fps15, live_fps)=+0.8925` 是同义反复
   （同计数器/同时钟/同代码），且每趟单值复制 3 窗造成重复计数；
   按趟去重复后降到 +0.813921。
4. **CONFIRMED（方差结构）**：趟内极差中位 0.5697 vs 两趟均值差中位 5.4368
   ⇒ 整趟锁定而非窗内漂移；但 `l3_1101v4c` 是同版本内极差 12.166 的反例。
5. **PARTIAL（全库范围）**：把带放宽到 units0>=800 时 φ 仅 +0.601722，
   存在 fast 非 v4 反例（harness7 10-30、老趟 10-20）；故「完全共线」
   只对 §544 对标带成立，不能推广为全库定律。
