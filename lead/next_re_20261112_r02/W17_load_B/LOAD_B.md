# LOAD_B · RE-N04f 换载体的负载压力对照（单变量：只换地图）——B 臂

run_id `NEXT_RE_20261112_R02` ｜ 卡 RE-N04f / W17 ｜ attempt1+attempt2 均在选图阶段失败，**未进图** ｜ 2026-11-13 05:04–05:10（Asia/Shanghai）
载体 `[8]音速公路_SonicHighways.yrm`（252,270 B / sha256 `0805e637…712f3`，开工实算一致）
B 臂结论分档：**`[B 不可用]`** —— 未进图（未到 StartGame；B 无 skirmish 列表条目）。

---

## §0 本卡能测 / 测不到（卡面固定口径）

**能测**（若进图）：B 臂每拍 CPU 分布（cycle 主通道）、占用率、趋势，及与 A 臂（W15）的单变量对照。
**实际本卡测到**：选图阶段的仪器行为（列表枚举 268 条 + 全名称落盘 + 双 attempt 自愈链全验证）。
**测不到**：B 臂任何局内数据（CPU/拍间隔/候选字段局内变化）——**无 ingame 样本**。
仪器性测不到（沿 W15）：阻塞类等待、GPU、掉帧；8 席位实例化（无已解码地址）。

## §1 B 载体身份（离线实读，卡面更正 ×2）

| 项 | 卡面预期 | 开工实读 | 结论 |
|---|---|---|---|
| 文件名 | `【8】音速公路_SonicHighways.yrm` | **`[8]音速公路_SonicHighways.yrm`**（半角括号） | 卡面写法为普查表归一化 |
| 字节数 | 252,270 B | 252,270 B ✓ | 一致 |
| sha256 | — | `0805e637d3ac14bd8c68ab2acac92b157514f8472c819bbbfecee9c00da712f3` | 钉定入探针 |
| 显示名 | `Invisible Light Post`（普查 name 列） | **`[8] Sonic Highways`**（`[Basic]` 第 1129 行） | **普查表 bug**：name 列取的是文件中**第一个 `Name=`**（第 57 行，属建筑定义段 `Invisible Light Post`+`InvisibleInGame=yes`），不是 `[Basic].Name` |
| MaxPlayer/MinPlayer/GameMode | — | 8 / 2 / battle（MultiplayerOnly=1，Official=yes，NewINIFormat=4，含 `[Events]` 触发器） | 与普查一致 |

## §2 选图结果（两趟 attempt，均 0 命中）

- **条目总数 = 268**（两趟一致；A 臂 W15 亦为 268 ⇒ 列表内容可复现）。
- attempt1 模式 `['[8] Sonic Highways','Sonic Highways','Invisible Light Post']` → **0 命中**，空名/乱码条目 0。
- attempt2 追加中文模式 `['音速公路','音速']` → **仍 0 命中**；全 268 条名称落盘 `out\maplist_names.json`。
- 命中索引：**不存在**（B 无条目，无从取舍）。

## §3 进图判定（预设判据执行结果）

- 判据：frame ≈29–32 计数/s 持续 ≥60 s；`mode[0xA8B238]` 仅旁证。
- 实测：**未到达 StartGame**（选图阶段失败）⇒ 无 ingame 样本 ⇒ **未进图**。
- attempt2 pre-start 采样 39 拍（250 ms 相位）：`A8ED50` 全 0（菜单相位基线）。
- 有效局内时长 = 0 s（<90 s ⇒ 判据分支 `[B 不可用]` 命中）。

## §4 根因：B 为什么不在列表里（277 文件 ↔ 268 条目全量对账）

对账工具：`match_maplist.py` / `match_maplist2.py` → `maplist_reconcile.json` / `maplist_reconcile2.json`。

**列表构成（实测划分，恒等式闭合）**：
- **内置本地化官方图 92 条 = 列表索引 0–91**（全部为正常 UTF-16 中文名 + （N-M）玩家段后缀，如 `冰天雪地（2-8）`）；其中 8 人图恰 6 条：索引 82–87（`危險場所/冰天雪地/長征/爆裂物/俄國輪盤/咫尺天涯（2-8）`）。
- **散装 `.yrm` 文件条目 176 条 = 索引 92–267**（ASCII 名或 GBK/UTF-8 逐字节零扩展的伪 Unicode 名，如 `[8] Proving Grounds`=265、`Hex Bay (2-8)`=267）。
- **`.mpr`/`.map` 文件 0 条上列表**（52 个散装 mpr/map 全部未上图；唯一假匹配 `Noname.mpr`↔内置 `No Name` 为同名列撞名，已识别）。

**未上列表的散装 `.yrm` = 48 张（含 B）**，反向字节级校验 48/48 ABSENT（排除本工具乱码恢复假阴性）。其构成：
- 47 张 `official=yes`，且全部是**西木系官方图英文名**（`(2) Landslide`、`(2) Suspect`、`(8) Cold Hard Truth`、`(8) Cowfields`、`(8) Snow Snow Snow`、`[8] Sonic Highways`…，作者多为 MirageTD / Chrono Vortex 等 YR 官方/半官方作者）；
- 1 张 `prm.yrm`（Name 解析异常的坏文件）。
- 对照组：`official=no` 散装 .yrm 86/87 上列表；`official=yes` 散装 .yrm 仅 90/137 上列表。

**推断（标注为推断，未做改名实验——禁改 ra2youli 文件）**：游戏对散装 .yrm 做了**官方身份表去重**——与内置官方图同身份（同图）的散装英文原版被枚举排除（本地内置块只显示 92 张中的一部分，故 8 人官方图有 13 张散装未上图 > 内置 8 人图 6 条）。B = `[8] Sonic Highways` 属于此集合 ⇒ **skirmish 无法选到 B**。

**仪器新事实（对 Lead 直接有用）**：
1. **W16 普查表 `name` 列不可作显示名**：取的是文件中第一个 `Name=`，建筑定义段在前时错位（B 错成 `Invisible Light Post`）。正确显示名 = `[Basic].Name`。
2. **skirmish 只枚举 `.yrm`**（+内置 MIX 图）；`.mpr/.map` 散装文件不进列表。
3. **`[Basic].Name` 带全角/半角括号、GBK/UTF-8 中文均可显示**，但以 268 条实测名单为准（`maplist_names.json`）。
4. **`[Basic].Name` 同名撞车警告**：`0LoadBench` 五张全部在列表，但 U0050/U0200/U0400 三张图的 `[Basic].Name` **完全相同**（`[Pro] [2] Urban Rush`）——按显示名选图时这三张不可区分（W15 的 A 图 `Proving Grounds` 无此问题，命中 1/268）。下一卡选 B' 必须先核对其显示名在 277 张内唯一，否则单变量"只换地图"会被同名图破坏。普查 name 列同名/错位双重不可靠。

## §5 与 A 臂对照表（数据未产生，判据不适用）

| 维度 | A（W15 实测） | B（本卡） | 相对变化 |
|---|---|---|---|
| 每拍 CPU 中位（cycle） | 1.691 ms | **N/A（未进图）** | N/A |
| 每拍 CPU 均值（FILETIME） | 1.725 ms | N/A | N/A |
| CPU 占用率（窗口线程） | 5.39% 单核 | N/A | N/A |
| 拍率 | 31.2492 计数/s | N/A | N/A |
| 拍间隔（均值/≥64ms） | 32.000 ms / 0 | N/A | N/A |
| 有效段 | 240.006 s | **0 s** | — |

预设判据执行：`[成功造出压力]`（>2.54 ms 或 >10%）不触发；`[无显著差异]`/<20% 不触发；`[中间地带]` 不触发；**`[B 不可用]` 命中**（未进图）。

## §6 趋势 / 候选字段 / 拍间隔

均无数据（无 ingame 样本）。pre-start 相位 39 拍仅证明仪器链路工作正常（采样、RPM 12 地址读、窗口线程 CPU 通道均 ok，读失败 0）。

## §7 结论分档

# **`[B 不可用]`**

依据（三层证据）：
1. **直接证据**：两趟 attempt 在 268 条列表中按 5 个模式（含精确名/子串/中文）选图均 0 命中，未到 StartGame。
2. **全量对账**：277 散装文件 ↔ 268 列表条目划分恒等式闭合（92 内置 + 176 散装 .yrm）；B 名单级与字节级均 ABSENT（48/48 反向校验）。
3. **机制对照**：未上图 48 张 .yrm 中 47 张 official=yes 且全部为西木系官方图英文名，与内置本地化官方图集同身份 ⇒ 官方去重机制排除（推断，标注）。

**不重启凑时长**：失败是结构性（B 不在列表），非瞬态，重试无意义；attempt2 后未再启动游戏。

## §8 交接：下一卡（B 臂重选）建议

- B' 必须满足：散装 `.yrm` ∧ `official≠yes` ∧ `has_trig=Y` ∧ **`[Basic].Name` 在实测 176 条名单内**（以 `maplist_names.json` + `maplist_reconcile2.json` 为准，勿信普查 name 列）。
- 可达图的结构数上限（普查声明口径）：**`[8]黑心湾_HexBay.yrm`（`Hex Bay (2-8)`，列表索引 267）：struct=144、8 人、official=no、has_trig=Y、355,713 B** —— 声明量仅为 B 原选（368 建筑）的 ~39%，且须以实测 CPU 为准（LoadBench 教训）。
- 其余候选见 `UNCOVERED.md` §3（76 个合规候选全表已具备筛选条件）。
- 单变量纪律提醒：换 B' 后与 A 的对照仍成立（配置基线/协议不变）。

## §9 尝试与文件

| attempt | WMI pid | 游戏 pid | 结局 | 自愈 |
|---|---|---|---|---|
| 1 | 38984 | 43632 | 选图 0 命中 → RuntimeError → 收尾 | 完整（残留 0/配置还原/锁回 lead） |
| 2 | 17808 | 39956 | 选图 0 命中 + 全名单落盘 → RuntimeError → 收尾 | 完整（同上） |

`out\run.ndjson` = attempt2 的 49 行（meta 1 + sample 39 + event 7 + meta_end 1 等；attempt1 的 ndjson 被同路径覆盖，其事实记于 RUNLOG §attempt1）。`out\tickcost.csv` 未生成（无 ingame 事件，`analyze_load_b.py` 按无数据分支写 `out\analysis.json` 最小档）。
