# W65 · UNKNOWNS.md（未决 / 未测 / 待运行验证）

> 执行者 Hy4｜`[待运行验证]` 与 `[静态推断]` 一律不冒充 `[本次实测]`。本卡未事后放宽任何阈值。

## U1 ★（最重要）FROZEN 判据 B-2 对「采样行数」敏感 —— 本轮 `SHIFT_DETECTED` 的结构性成因

- `[本次实测]` `out\b_compare.json`：`verdict=SHIFT_DETECTED`, `reason=discrete_or_ui_mismatch`；`discrete_mismatch` 五个字段的**取值集合完全相同**，仅计数 `20113` vs `20229` 不等。
- `[本次读码]` `tool_b_stats.py:148-149` `multiset()` = `Counter(str(value))`（值→**计数**），`:203-207` 逐字段 `ma != mb` 判不等；`CRITERIA_SPEC.md §2.1` 明文「多重集（值→计数）」、`§2.4` B-2 在 B-3/B-4 之前短路。
- `[本次实测]` 四趟按任务卡「约 1–2 分钟采样 / 两臂同一 cadence」以**固定墙钟 75 s** 结束，行数由调度抖动决定：10084 / 10029 / 10023 / 10206 ⇒ 合并臂 20113 / 20229。任何按墙钟定长的采集都会出现此不等。
- `[静态推断]` 若两臂行数恰好相等，`discrete_mismatch` 为空 ⇒ 判据会走到 B-3（`D_ks=0.001286 ≤ max(N_ks=0.001572, D_floor=0.05)` 且 `p=0.766 ≥ α`）⇒ `SAME_DISTRIBUTION`。**这只是对判据行为的推断，不是本卡结论、不是签发**；本卡不为此截断/补齐数据。
- `[待运行验证]` 需 Lead 另开卡裁决：是把离散字段改为「比较取值集合（忽略计数）」，还是要求每趟**事先声明固定 N 行**、或按 `dframe` 序列长度归一。任何修改都违反 §3.4，本卡无权做。
- 附带：W62 工具自检的合成轨迹每条固定 400 行（`tool_b_stats.py:278 N_SAMPLES=400`），**从未覆盖「不等长轨迹」这一路径** ⇒ 该敏感性在自检里不可见。`[本次读码]`。

## U2 合并臂的拼接边界伪差

- `[本次实测]` A 合并臂 `dframe` 含 1 个 `-2316`，B 合并臂含 1 个 `-2357`（`out\w65_descriptive_stats.json`）；来自 `A = A1∪A2` 逐行拼接后跨边界求一阶差分（A1 末帧 2385 → A2 首帧 69）。
- `[静态推断]` 两臂各一个、对称，对 KS 的贡献 ≈1/20000；同时使合并臂 `CV` 从 ≈1.81 膨胀到 ≈139/144。分位数 `Q` 不受影响（仍 0,0,0,0,1）。
- `[待运行验证]` 若 Lead 认为该伪差不可接受，需在判据层事先声明「轨迹拼接时是否剔除边界差分」，本卡按 FROZEN 工具 `_merge()` 语义原样保留、未剔除。

## U3 本卡只覆盖一个场景 / 一个观测量集合

- `[本次实测]` 场景 = 官方苏联战役第一关 `SOV01UMD.MAP`（`battle_idx=1`，`stage_idx=0`，`end_of_game=0`，`skip_map_select=0`），1366×768 游戏窗口 / 2560×1440 桌面，零输入，75 s，6 ms cadence。
- `[待运行验证]` 其它战役/徽章、`battlemd:inplace` 就地改写臂、多关链（W63 的 M1→M2→M3）、`end_of_game=1` 终关、`skip_map_select=1`、其它分辨率/语言版本、更长（>600 s）采样、渲染侧观测量，均**未测**。本卡结论不外推。

## U4 `ui_controls` 在局内退化为 `[0]`

- `[本次实测]` 四趟全部 `ui_controls=[0]`（`J_ui=1.0`）。局内 UI 由引擎自绘，Win32 可见控件只剩顶层窗口（id 0）。
- `[静态推断]` 因此本轮 `ui_controls` 对 A/B 差异**无分辨力**；它是 FROZEN 观测量集合的一部分，但在此场景下不构成有效判别信号。菜单态控件集更丰富（见 `w65_run.ndjson` 的 `campaign_menu_controls`），但本卡采样段在局内。
- `[待运行验证]` 若要用 `θ_ui=0.95` 做有效判别，需在判据层事先声明采样段包含菜单态 / 或改观测量。

## U5 B 臂选用 append 路线而非 `battlemd:inplace`

- `[本次读码]` 任务卡指定 `W60_battlemd_inplace\ra2forge_patched_v15\` 工具链，但只说「装 v15 包」，未指定 feature-set。本卡用 append 路线（包内 `BATTLEMD98.INI`，无 `BATTLEMD.INI`），理由见 `DISAGREE.md` D1。
- `[待运行验证]` **inplace 臂（改写 `[SOV1]` 指向自定义 M1）本卡未跑**。该臂 `map_name` 必然不同，会由 B-2 触发 `SHIFT_DETECTED`；是否值得跑、以及长时任务不自动 `survive(8)` 通关的设计，由 Lead 裁决。

## U6 C-6 不适用

- `[本次实测]` `c_audit_B_arm.json` 的 `C-6_inplace_bak_and_restore = null`：append 路线不是 inplace，无 `.bak` 声明内改写，按 `tool_c_writeaudit.py:233` 逻辑不评。W62 的 C-B 用例已 PASS 覆盖 inplace 的 `.bak` 逐字节还原 `[转引]`，本卡未重做。

## U7 真机环境外部条件

- `[本次实测]` 四趟 `step0_desktop_precheck pass=true`（`WinSta0\Default`，EnumWindows 405–418 / 可见 22–25，ImageGrab 2560×1440）。
- `[待运行验证]` 无头/不同交互桌面、并发其它真机代理、D3D/ddraw 渲染后端差异下的表现未测。HANDOFF §5 已明确同一写域同一时刻只派一个真机代理；本卡凭锁文件约束，未见他方活体实例。

## U8 未测的统计功效

- `[静态推断]` `dframe` 在 6 ms cadence 下是近似 Bernoulli(p≈0.232) 的离散量，KS 分辨率受 `D_floor=0.05` 限制；本判据能检出的最小平移量级未在本卡实测（W62 的 B-NEG 用 +5 平移，是合成数据 `[转引]`）。「未检出」永远不等于「不存在」。
- `[待运行验证]` 若 Lead 需要功效曲线，应另开卡用真机注入已知幅度扰动做正对照。
