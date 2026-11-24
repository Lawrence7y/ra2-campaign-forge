# W90 UNKNOWNS · 本卡未证/异常如实记录

- **U1 cycle 通道与 FILETIME 通道比值有小差（~1.5–2.5%）**：
  pair_c 原始 Σcyc 比 = 1.7198 vs FILETIME 1.7457；pair_d = 1.7589 vs 1.8007。
  逐样本隐含线程周期频率（Δcycles/Δcpu_ms）交战臂 ~0.876 GHz、对照臂 ~0.750 GHz
  ——疑似负载相关频率/turbo 行为差异。**W88 报告的"cycle 通道逐位一致"口径在本卡
  4 趟数据上未复现**（W88 的具体换算口径未随卡留档可查，本卡按原始求和与频率归一
  两种算法都报了，均给出）。成因未证，主统计量仍以 FILETIME（预注册）为准。
- **U2 framebeat 自洽读数 clamp=210**：W86 脚本注释预期「参考上限=60」，实测
  ddraw.dll+0x5EE48 = 210（maxfps=60、interval=16 两个主自洽判据均通过，未触发
  脚本 WARN）。clamp 字段的语义/取值来源未证（可能与配置节或编译期常量有关）。
- **U3 渲染通道轮询对 trip_C6_c 的扰动未校准**：trip_C6_c 采样期间同机另有一个
  ~1 kHz RPM 轮询进程（framebeat）。C6_c 31.01% 略低于 C6_d 31.97%（方向上不像
  抬升），但 W86 预注册的 ETW/RPM ABBA 扰动校准本卡未做。trip_C6_c 的 CPU 数字
  应视为「带轮询观测」口径。
- **U4 引擎局内清理了沙箱基线存档 SAVE0029.SAV**：4 趟收尾时发现沙箱副本里该
  基线文件（810,289 B，随 ra2youli 带入）被引擎删去（引擎同时新写 RA2F_M1.sav，
  已按引擎掉落物清除）。真目录同名文件完好（real_diff identical_tree=true），
  已按字节从真目录补回沙箱（sha256 967f2fc6… 与 sandbox_pre manifest 一致）。
  另：第一次 finalize 我方用 `save*.sav` 通配误把补回的文件又删了一次（工具自身
  缺陷，非引擎行为），当即改为「sandbox_pre manifest 差集判定」并修复重跑；
  两次修复均留痕于 finalize.ndjson / finalize_*.log。
- **U5 限帧放行间隔中位 17 ms（>16.67 ms 名义值）**：1 kHz 轮询量化 +
  timeGetTime 分辨率的贡献未拆分；p95/p99=18 ms 紧贴中位，>50 ms 为 0，
  max 39 ms——放行节奏本身看不出异常，但这不是帧时间结论（W86 措辞纪律）。
- **U6 A8ED50 首非零时刻与 W88 不同**：W88 @0.318 s vs 本卡 @1.14 s。两卡进局
  判定帧数阈值/装载节奏有随机性，属进场时机差，不构成矛盾；无逐位对齐预期。
