# W90 REPLICATES · C6/CTRL_C6 重复趟 + 首次渲染通道挂载 主报告

> 卡：NEXT_RE_20261112_R05 · W90（真机小范围执行卡）
> 执行：子代理 `w90-replicates`（GLM-5.3-Flash）｜写域：`lead/next_re_20261112_r05/W90_replicates/`
> 报告落盘：2026-11-14T15:3x+08:00（Get-Date 实测，详见 PROGRESS.md FINAL 段）
> 真机纪律自证：`ra2youli` 真目录全程零改动（FINALIZE.json：real_diff identical_tree=true，
> W44 基线断言 647 文件 / 1,989,215,270 B / 277 maplike 全等，4 锚点 gamemd.exe /
> ddraw.dll / RA2MD.INI / BATTLEMD.INI 跑前跑后 sha256 全等）；沙箱副本收尾
> identical_tree=true；残留 gamemd=0；锁 owner=lead（收尾已还）。

---

## 0 · 一句话判决

**[本次实测]** W88 的 C6 vs CTRL_C6 配对正数在重复趟下**成立**：三对配对比值
**1.857（W88）/ 1.746（W90 pair_c）/ 1.801（W90 pair_d）**，全部 ≥1.10 预注册线，
「初估抬升」85.7% / 74.6% / 80.1%——**A 线"更重战斗抬 CPU"的正向数字从 N=1 配对
变成 N=3 配对有重复支撑**；4/4 趟全部 ≥155 s 有效窗、零崩溃、零引擎错误、零 D1 事件。
W86 非注入渲染通道首次挂载成功（限帧放行间隔 中位 17 ms / p95 18 ms / >50 ms 0 次，
措辞按 W86 纪律，不写显示帧时间/FPS）。

---

## 1 · 四趟明细（[本次实测]；主统计量 = 窗口线程 CPU 消耗率，单核占用率%）

| 趟（唯一目录） | 臂 | ok / outcome | 局内时长 | CPU 消耗率（FILETIME 主通道） | CPU 消耗率（cycle 通道，见 UNKNOWNS U1） | `A8ED50` 非零拍占比 | `X87E8E0` 变化次数 |
|---|---|---|---|---|---|---|---|
| `out\trip_C6_c` | C6（1200 Hunt 交战） | true / VALID_WINDOW_target_reached | 155.005 s | **31.0087 %** | Σcyc 151.117×10⁹，隐含线程频率 ~0.877 GHz | **97.809 %**（25138/25701） | **6509** |
| `out\trip_C6_d` | C6（1200 Hunt 交战） | true / VALID_WINDOW_target_reached | 155.006 s | **31.9659 %** | Σcyc 153.299×10⁹，隐含线程频率 ~0.876 GHz | **93.189 %**（23957/25708） | **6197** |
| `out\trip_CTRL_C6_c` | CTRL_C6（同布局全 Guard） | true / VALID_WINDOW_target_reached | 155.004 s | **17.7624 %** | Σcyc 87.872×10⁹，隐含线程频率 ~0.754 GHz | **0 %**（0/25709） | **0** |
| `out\trip_CTRL_C6_d` | CTRL_C6（同布局全 Guard） | true / VALID_WINDOW_target_reached | 155.003 s | **17.7524 %** | Σcyc 87.156×10⁹，隐含线程频率 ~0.745 GHz | **0 %**（0/25714） | **0** |

每趟采样节拍 6 ms、~25.7k 拍、读失败 0、前台丢失 0、线程时通道失败 0。
机械锚：两趟交战臂 `A8ED50` 首非零样本 idx 均为 **167**（C6_c @1.1455 s、C6_d @1.1402 s，
进入局内后 ~1.1 s，与 W88 的 @0.318 s 同量级但不逐位对齐——进场时机随机，属正常）；
`X87E8E0` 首变 idx C6_c=3 / C6_d=1；两趟对照臂 `A8ED50` 全程 0、`X87E8E0` 全程恒值
（与 W88 对照臂行为一致：完全没进交战路径）。

## 2 · 配对比较（预注册口径：窗口 = [0, min(T_end)]，两趟同窗；禁显著性语言）

| 配对 | 窗口 | 交战臂 | 对照臂 | 比值（FILETIME） | 判读（预注册措辞） |
|---|---|---|---|---|---|
| W88（已签发，照录不重算） | 150.002 s | trip_C6 **33.6062 %** | trip_CTRL_C6 **18.0950 %** | **1.857** | 初估抬升 85.7% |
| W90 pair_c | 155.004 s | trip_C6_c **31.0087 %** | trip_CTRL_C6_c **17.7624 %** | **1.7457** | 初估抬升 74.6% |
| W90 pair_d | 155.003 s | trip_C6_d **31.9659 %** | trip_CTRL_C6_d **17.7524 %** | **1.8007** | 初估抬升 80.1% |

**N=3 配对表（比值列表）**：1.857 / 1.746 / 1.801 ——三对全部 ≥1.10，方向一致、
量级一致（1.75–1.86 区间）。三对配对窗口分别为 150.0/155.0/155.0 s（如实标注）。
cycle 通道（QueryThreadCycleTime 原始求和比值，不作频率归一）：
pair_c **1.7198**、pair_d **1.7589**——与 FILETIME 比值方向与量级一致，数值有
~1.5–2.5% 小差，原因见 UNKNOWNS U1（W88"cycle 逐位一致"口径未在本卡复现）。

## 3 · 渲染通道（仅 trip_C6_c，[本次实测]；W86 措辞纪律）

- 挂载方式：进局内后另起进程跑本卡副本 `work\tools\exp_rpm_framebeat.py <pid> 150
  <trip>\render_channel`（W86 r03 原脚本复制入卡，未跨卡调用）；进程外只读 RPM，
  无注入、无调试器；主趟不受其成败影响。
- 产物：`out\trip_C6_c\render_channel\framebeat_1794640742.csv`（9000 帧）
  + `framebeat_console.log`；ddraw.dll 运行时基址 **0x54400000**（枚举成功，非失败）。
- 自洽读数：maxfps=60（通过）、帧间隔=16 ms（通过）、**clamp=210**（W86 文档预期 60，
  偏差如实记录，见 UNKNOWNS U2；主自洽判据未触发 WARN）。
- **【限帧放行间隔】统计**（有效窗 149.991 s，8999 个间隔；阈值 max(50, 3×16)=50 ms）：

| 指标 | 值 |
|---|---|
| 中位 | **17.00 ms** |
| p95 | **18.00 ms** |
| p99 | **18.00 ms** |
| 最大 / 最小间隔 | 39 ms / 1 ms |
| >50 ms 间隔次数 | **0 次（0.00 次/分钟）** |
| 帧数 / 有效时长 | 9000 帧 / 149.99 s（≈60 帧/s 放行节奏，与 maxfps=60 限帧层一致） |

- **措辞纪律**：以上是「cnc-ddraw 限帧放行间隔」（ddraw.dll+0x5F120 放行时刻轮询），
  **不是**「显示帧时间」，**不是** FPS；**不得**据此描述"画面流畅/卡顿"。
  [未证] 该节奏在交战 vs 对照两臂间是否不同（本卡只挂了交战趟一趟，无配对）。

## 4 · 证据分级汇总

- [本次实测]：§1 四趟全部数字（每趟 run.ndjson + TRIP_RESULT.json + D4 installed_inputs/
  归档 + sha256）；§2 三对配对（含照录的 W88 对）；§3 渲染通道 CSV+console；
  `ra2youli` 零改动（FINALIZE.json：real identical_tree=true、4 锚点全等、W44 基线断言）；
  沙箱 identical_tree=true；全程残留 gamemd=0。
- [静态推断]：交战臂 A8ED50 高非零拍占比（93–98%）与 X87E8E0 数千次变化 vs 对照臂
  全 0 / 恒值 ⇒ 交战路径真实发生且对照臂未进入——机理沿用 W88 已签发读码（Bullet
  向量 Count；本卡未做新读码）。
- [未证]：两通道比值差异的成因（U1）；clamp=210 偏差的含义（U2）；渲染通道对
  trip_C6_c CPU 数字的扰动量（U3，未做 ABBA 校准）；>155 s 长时稳态外推。

## 5 · 交付物对照（任务卡 §六）

| 项 | 状态 |
|---|---|
| REPLICATES.md（本文件） | ✅ |
| 4 趟唯一目录 out\trip_*（永不复用，trip 目录由 W90_SUFFIX 预注册强制） | ✅ c/d 两趟各一目录，D1 事件 0（无 except/WER 产生） |
| 每趟 ≥150 s 有效局内 + 6 ms 采样 + RA2MD.INI/ddraw.ini 逐字节备份还原（hash 自证） | ✅ 155.0 s ×4；每趟 per_trip_config_restore byte_identical=true ×3 |
| 渲染通道（trip_C6_c，本卡副本脚本，stdout/JSON 落盘 render_channel\） | ✅ 成功；失败分支未触发 |
| D1 取证 | ✅ 机制全程武装；本轮 0 崩溃 → 0 事件（pre_existing 基线 except.txt 未被触碰） |
| D2 语义 | ✅ 4 趟 ok=true / VALID_WINDOW_target_reached |
| D4 归档（design JSON + .MAP + BATTLEMD.INI + MAPSELMD.INI + sha256） | ✅ 每趟 installed_inputs\ |
| UNKNOWNS.md / DISAGREE.md / PROGRESS.md / HEARTBEAT.txt | ✅ |
| out\FINALIZE.json（identical_tree、锚点、锁、残留） | ✅ 全绿 |
