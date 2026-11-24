# W98 三点几何预注册（跑前写死，跑中不改）

> 卡：W98（真机矩阵卡，独占机器）｜签发依据：§633（W96 失败复盘）｜生成时间：2026-11-14 17:4x (Asia/Shanghai)

## 唯一要答的问题

`§626` 的「17.75–18.10 % → 31.0–33.6 %（+75~86 %）」里，**行军/寻路的贡献**与**交战/毁伤的贡献**各占多少？
（差值口径 = 「活动 vs 静止」，§627；本卡把它拆开。）

## 三格（单位数量与构成完全相同，只改两军距离）

| 格 | cell id | 敌军 mission | 敌军坐标 | 语义 |
|---|---|---|---|---|
| g_idle | `g_idle` | 全 `Guard` | W85/C6 原远端布局（rows 12-41，三 house 各自分列） | 静止：无行军、无交战 —— 基线 |
| g_near | `g_near` | 全 `Hunt` | **紧贴玩家基地**：1200 辆 MTNK 放到距最近玩家对象（建筑锚点/玩家坦克格）Chebyshev 最近的前 1200 个空格（平局按 row,col；放置池排除全部占用格；坐标只此一改，对象计数不变） | 几乎不行军，但全程交战 |
| g_far | `g_far` | 全 `Hunt` | W85/C6 原远端布局（=G6 原布局） | 行军 + 交战 |

玩家侧三格完全一致：`NACNST`×1 + `NAPOWR`×6（step3）+ `TESLA`×12 + 300 `MTNK Guard`；敌建筑 `GAPOWR`×3 保持 row 8 原位。

- 构成相同：3 house × 400 `MTNK` 不变；只改 `enemy_zone` 旋钮的坐标来源（w94_build.py [W98] knob）。
- **禁止** `Speed=` 任何键（W96 已证该操纵无效且引入新混杂）。本卡旋钮集不含 speed_all_mtnk / player_slow_clone。

## 预注册算法（跑之前写死）

- 令 `R(x)` = 该格 CPU 消耗率（FILETIME 主通道：Σ`win_cpu_ms_delta` / 墙钟，单核占用 %，全采样窗；取 2 趟均值并报极差）。
- **交战的贡献** = `R(g_near) − R(g_idle)`（几乎无行军，差值近似纯交战/毁伤）
- **行军的贡献** = `R(g_far) − R(g_near)`（同为全 Hunt，只差行军距离）
- **总** = `R(g_far) − R(g_idle)`；并报三者的百分比构成。
- **交叉校验（三角恒等式）**：`(R(g_near)−R(g_idle)) + (R(g_far)−R(g_near))` 应 ≈ `R(g_far)−R(g_idle)`（逐值核对，浮点意义下自洽）。
- **禁止** p 值 / CI / "显著"。

## 参照带纪律

- 每批带参照格：`g_idle` 就是（历史 CTRL_C6 = 17.75–18.10 %）。
- 跑完后**先**核 `R(g_far)/R(g_idle)`（2 趟均值之比）是否落在 **1.7–1.9**：
  - 带内 ⇒ 环境干净，做拆分判读；
  - 带外 ⇒ **整批作废**，只报"参照带未复现 + 实测偏移量"，**不得**做任何拆分结论；并排查同机邻居负载（`Get-Process` CPU 时间增长 + 当时是否有 python/agy 等）。
- 历史参照：m1(C6 交战)=31.0–33.6 %；m2(CTRL_C6 静止)=17.75–18.10 %；比值带 1.77–1.86（W95 原始 ndjson 独立复现过）。

## 硬纪律（全部继承 §633）

1. 真机串行 + 锁 `lead\next_re_20261112_r08\.game_instance.lock`（owner=w98-batchrun 于每趟 START / owner=lead 于每趟 FINISHED；初始 claim owner=w98）；启动前 `Get-Process gamemd` 必须为空。
2. 只在沙箱跑（out/sandbox_game，robocopy 自真目录）；跑前跑后对 `ra2youli` 4 锚点哈希（gamemd.exe / ddraw.dll / RA2MD.INI / BATTLEMD.INI）+ 全树 manifest diff；`ra2youli` 有既存旧包 v0.3，**只在沙箱副本卸载**。
3. 禁止注入/调试器/改 gamemd.exe/改 ra2youli/改用户存档/taskkill 非本卡进程。
4. D1：崩溃瞬间（还原前）归档 except.txt（fresh/pre_existing 按 mtime）+ WER + ndjson 尾部；已知 4 种崩溃签名（`0x47C538` 族 / `0x6F36FE` / `Eip=0` / R03 的 `0x51C2D3`），逐趟记 EIP，不合并。
5. D2：`ok` 在终态非正常时 false；outcome 用 `VALID_WINDOW`/`ABORTED_ENGINE_ERROR`/`DEFEAT_DIALOG_*`。
6. D4：每趟归档 design + `.MAP` + `BATTLEMD.INI` + `MAPSELMD.INI` + 四者 sha256。
7. trip 目录唯一；清场按 manifest 差集，禁用 `save*.sav` 通配。
8. 小步落盘：每趟后 `PROGRESS.md` + `HEARTBEAT.txt`（Get-Date，由 batch_runner 自动写）。
9. 分级 `[本次实测]`/`[静态推断]`/`[未证]`。

## 执行计划

- 6 趟 = 3 格 × 2 repeats，`observe_sec=150`（min_valid 150 / hard_cap 200 / sample 6 ms），order=shuffle seed=98（计划 JSON 在执行前生成并归档，即预注册的执行顺序）。
- 运行器：本卡 `work/tools/batch_runner.py`（W94 端到端 + W96 双 bug 修复版，[W98] 增补 enemy_zone 旋钮与 heartbeat 落盘）。

## 解释边界（跑前声明，不改变算法）

- `R(g_far)` 的交战发生在接触之后（约 t≈30 s 起，`[本次实测·历史]`），`R(g_near)` 的交战从 t≈1 s 起全程覆盖，故「行军贡献 = R(g_far) − R(g_near)」按预注册**同时吸收了 g_far 交战窗口更短/更晚的效应**。这是该算法的既定口径，拆分结果按此口径解读；若要再细分属于后续卡。
- `[静态推断]` g_near「目标 ≤3 格内」的逐辆成立在几何上不可行（1200 辆需要 1200 个空格，玩家对象 ≤3 格壳层装不下）；预注册的**可执行定义**是"最近优先前 1200 空格"。构建后实测：**dist_min=1 / dist_max=13 / dist_mean=6.69**（Chebyshev，到最近玩家对象）。即接敌为秒级（Hunt 下 13 格 ≈ 数秒收拢），与 g_far 的 25-60 格长途行军对比成立。
- `[静态推断]` 敌 3×GAPOWR 保持 row 8 原位不动（只改 MTNK 坐标，对象计数不变；MTNK 不依赖电力）。
