# RUNLOG.md —— RE-N04 W12 可重复性能基线（时间线）

所有时刻为 UTC（本地 +08:00 = UTC+8）。探针 stdout 存 `out\R{n}_stdout.txt`。

## T0 开工（2026-11-12T18:40Z 前后）

- 实例锁从 `owner=lead`（W11 已归还）接管为 `W12-perf-baseline-subagent`。
- 开工前核对：`gamemd` 残留 0；Proving Grounds 载体实算 SHA-256
  `3e3c874572bc…fbfd5b19` 与卡片钉定一致；R4 载体 `[2]0LoadBench_U0800.yrm` 存在，
  内部 `[Basic] Name= " [2] 0LoadBench U800"`（⇒ 选图模式定为 `LoadBench U800`，回退 `U800`）。
- W7 run1 NDJSON 复核：StartGame 后 0.03 s frame 即推进、loading 段全程 ~31.2 计数/s
  ⇒ 确认速率不是加载/局内判别器，门控按时间切片口径设计（R4 min_load_s=30 留裕量）。

## T1 R1 首趟 —— 中断（2026-11-12T18:44Z）

- 18:44:02 启动 pid 26832，S0 守卫全过（哈希 match、残留 0、载体钉定一致）。
- 18:44:03 `EnumChildWindows` 调用抛 TypeError——转录 W7 绑定时丢了 `wt.HWND`
  （W7 为 `[HWND, c_void_p, LPARAM]` 三参，本探针误写两参）。
- 收尾链正常执行：taskkill、配置逐字节还原自证通过、残留 0；meta/ndjson 存档
  `out\R1_meta.aborted_try1.json` / `out\R1.ndjson.aborted_try1`。
- 修复绑定行后重跑。此失败不影响任何数据集（尚未进入导航）。

## T2 R1 基线趟（2026-11-12T18:46:28Z – 18:49:46Z）

- pid 6120（launcher 37596），主菜单 20.2 s，代码签名 ok，is32=True。
- 地图列表 268 条；模式 `Proving Grounds` 命中 1（索引 265，显示名 `[8] Proving Grounds`，
  空名 0）；UseMap → StartGame → 门控 20.016 s（battle_rate_detected）。
- 稳定段 125.0 s / 4094 拍；收尾：配置还原自证 ✓，残留 0。

## T3 R2 重复性趟（2026-11-12T18:49:52Z – 18:53:10Z）

- pid 38360；同链路：索引 265、门控 20.017 s、4094 拍、收尾干净。

## T4 R3 重复性趟（2026-11-12T18:53:15Z – 18:56:34Z）

- pid 36888；同链路：索引 265、门控 20.013 s、4094 拍、收尾干净。

## T5 R4 换载体趟（2026-11-12T18:56:38Z – 19:00:12Z）

- 命令：`--run 4 --map-patterns "LoadBench U800" "U800" --min-load-s 30 --load-timeout 300
  --allow-low-rate-fallback`。
- pid 38312；模式 `LoadBench U800` 命中 1（索引 96，显示名 `[2] 0LoadBench U800`）；
  门控 35.035 s（**速率门按时触发，低速回退未启用**）；稳定段 125.0 s / 4094 拍；
  收尾：配置还原自证 ✓，残留 0。
- 判定：**R4 成功进图，取得该载体数据**（首次尝试即成功，未用满 2 次重试额度）。

## T6 离线分析与交付

- `analyze_baseline.py --ndjson out\R1..R4.ndjson` ⇒ `out\analysis_summary.json`
  （读数见 PERF_BASELINE.md §3–§5）。
- 分析脚本先用 W7 三趟数据干跑校验（31.2443/31.2494/31.2498，与 W7 已发布读数一致，
  输出显式指向本卡 `out\dryrun_w7_analysis.json`，未写 W7 目录）。
- 交付：PERF_BASELINE.md / SAFETY.md / CONFIG_RESTORE.md / RUNLOG.md / UNCOVERED.md。

## T7 收尾

- `gamemd` 残留复查：0。
- 实例锁恢复 `owner=lead`（purpose=W12 done: RE-N04 4 趟完成，R4 成功）。
