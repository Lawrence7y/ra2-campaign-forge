# W90 PROGRESS · C6/CTRL_C6 重复趟 + 首次渲染通道挂载

卡：NEXT_RE_20261112_R05 · W90（真机小范围执行卡）
执行：子代理 `w90-replicates`｜写域：`lead/next_re_20261112_r05/W90_replicates/`
唯一目的：把 W88 的 C6 vs CTRL_C6 配对正数（33.606% / 18.095% = 1.857，N=1 配对）
补成有重复支撑（新增一对配对，与 W88 那对并列成 N=3 表）；并把 W86 建好的
非注入渲染通道第一次挂到 trip_C6_c 的同一趟真机上。

预注册（跑前写死，执行未改）：
1. 4 趟唯一目录：trip_C6_c / trip_C6_d / trip_CTRL_C6_c / trip_CTRL_C6_d，永不复用。
2. 每趟有效局内 ≥150 s（MIN_VALID_S=150，采样目标 155 s，6 ms 采样节拍）。
3. 主统计量沿用 W88 预注册口径：窗口线程 CPU 消耗率（Σ GetThreadTimes
   kernel+user ÷ 墙钟，单核占用率%），配对窗口 = [0, min(T_end)]；同窗报
   0xA8ED50 非零拍占比与 X87E8E0 变化次数；FILETIME 与 cycle 双通道并报。
   比值 <1.10 ⇒「本配置下未观测到与交战成比例的负载抬升」；≥1.10 ⇒「初估抬升 X%」。
   禁止显著性语言（显著/不显著/p值/CI）。
4. 渲染通道（仅 trip_C6_c）：进入局内后启动 `exp_rpm_framebeat.py <pid> 150
   <trip>/render_channel`（本卡副本）；措辞纪律 = 只写「限帧放行间隔」，
   禁写「显示帧时间」「FPS」「画面流畅/卡顿」；失败如实记录且不中断主趟。
5. D1 取证：终态异常即抢在还原前归档 except*.txt（fresh/pre_existing 按
   mtime 区分；ra2youli 自带 2026-11-13 except.txt 26,272 B 属 pre_existing）+ WER + ndjson 尾部。
6. D2 语义：ok=true 仅当 ≥150 s 无终态或胜利屏；defeat/引擎错误/异常退出 ⇒ ok=false。
7. 沙箱副本跑（out/sandbox_game），真目录 ra2youli 只读；4 锚点（gamemd.exe /
   ddraw.dll / RA2MD.INI / BATTLEMD.INI）跑前跑后哈希 + 残留进程核对；
   ra2youli 里的旧包 v0.3 不卸载（真目录不动）。

## 时间线

- 2026-11-14T15:13:33+08:00 建卡完成：work/tools + pkg_C6/pkg_CTRL_C6（与 W88
  逐字节 sha256 核对一致）+ 设计 JSON/feature_set 本卡副本 + exp_rpm_framebeat.py
  本卡副本；锁 r05\.game_instance.lock owner=w90 已取（Get-Date 实测）。

- 2026-11-14T15:21:51.602+08:00 trip_C6_c 完成：ok=true outcome=VALID_WINDOW_target_reached，局内 155.005 s（25702 拍，0 读失败/0 前台丢失），A8ED50 首非零 seq=168 @1.1455 s；渲染通道 returncode=0，产物 render_channel\framebeat_1794640742.csv + framebeat_console.log；RA2MD.INI/ddraw.ini 逐字节还原（hash 自证一致），残留 gamemd=0。
- 2026-11-14T15:25:13.599+08:00 trip_C6_d 完成：ok=true outcome=VALID_WINDOW_target_reached，局内 155.006 s（25709 拍，0 读失败/0 前台丢失），A8ED50 首非零 seq=168 @1.1402 s；配置逐字节还原，残留 0。
- 2026-11-14T15:28:40.676+08:00 trip_CTRL_C6_c 完成：ok=true outcome=VALID_WINDOW_target_reached，局内 155.004 s（25710 拍），A8ED50 全程 0（25710/0 非零），配置逐字节还原，残留 0。
- 2026-11-14T15:32:02.994+08:00 trip_CTRL_C6_d 完成：ok=true outcome=VALID_WINDOW_target_reached，局内 155.003 s（25715 拍），A8ED50 全程 0；配置逐字节还原，残留 0。4/4 趟全部完成。

- 2026-11-14T15:36:03.176+08:00 finalize 通过（第 3 次重跑）：卸包 exit 0、引擎掉落物 RA2F_M1.sav 按差集清除、基线存档 SAVE0029.SAV 从真目录字节补回（U4 全程留痕）、全部 pristine byte_identical=true、sandbox identical_tree=true、real identical_tree=true、W44 基线断言通过、4 锚点全等、残留 gamemd=0。
- 2026-11-14T15:36:03.176+08:00 analyze 完成：pair_c 比值 1.7457（初估抬升 74.6%）、pair_d 1.8007（初估抬升 80.1%）；cycle 通道原始比值 1.7198/1.7589（U1）；渲染通道 限帧放行间隔 中位 17 ms / p95 18 ms / p99 18 ms / >50ms 0 次 / 149.991 s 窗 9000 帧。
- 2026-11-14T15:36:03.176+08:00 REPLICATES.md / UNKNOWNS.md / DISAGREE.md 落盘。

## FINAL:

**[本次实测] 4/4 趟全部完成且全部 ok=true（trip_C6_c 155.005 s / trip_C6_d 155.006 s / trip_CTRL_C6_c 155.004 s / trip_CTRL_C6_d 155.003 s 有效局内，零崩溃、零引擎错误、零 D1 事件）；三对配对（FILETIME 主通道，预注册口径）比值列表 = W88 1.857、W90 pair_c 1.746、W90 pair_d 1.801（交战 33.606/31.009/31.967 % vs 对照 18.095/17.762/17.752 %），三对全部 >=1.10 => 「初估抬升 85.7% / 74.6% / 80.1%」——W88 的 C6 交战 CPU 抬升正数在 N=3 配对下有重复支撑；A8ED50 非零拍交战臂 97.8%/93.2% vs 对照臂 0%，X87E8E0 变化 6509/6197 vs 0；W86 渲染通道首次挂载成功（trip_C6_c，限帧放行间隔 中位 17 ms / p95 18 ms / p99 18 ms / >50 ms 0 次 / 149.99 s 窗，按 W86 措辞纪律不写显示帧时间/FPS）；ra2youli 真目录零改动（identical_tree=true、4 锚点全等）、沙箱 identical_tree=true、残留 gamemd=0、锁 owner=lead。交付完成度 4/4 趟 + 渲染通道 1/1。**
