# 基准图重制：让 U200/U800 在遭遇战下真正承载负载

> 任务卡 MIMO-BENCHMAP · 执行方 MiMo · 工作区 `D:\Project\ra2-campaign-forge`
> 基线 `ra2youli\gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`（只读）
> 本文件为新建；**不覆盖**既有 PROTOCOL.md / report_20260927_r3.md / 游戏目录。
> 证据等级：`[实证]` = 文件:行 / 字段值 / 反汇编 VA；`[推演]` = 由已证事实推出；`[待实测]` = 需真机。

---

## 0. 结论摘要

1. **根因已定谳**：旧基准图把 200/800 个预置单位全部挂在 `Russians`/`Americans` 两个 house 名下；遭遇战（`MultiplayerOnly=1`）只对**大厅选国所对应的玩家槽 house** 实例化预置对象。选国不匹配 ⇒ 整支军队被丢弃。
2. **21/22 的来源**：不是地图负载，而是 `HouseClass::RespawnStartingForces()`（`0x50D440`）生成的**国家默认开局部队**（2 个玩家槽 × MCV+护卫）。
3. **方案 A（已产出）**：14-house fanout —— 把 `target/2` 的兵力写到**每一个**标准 house；运行时 2 个玩家槽 × `target/2` = 目标负载，与选国无关。
4. 新图：`out/loadbench/[2]0LoadBench_U{0050,0200,0800}_H1.yrm`（**未覆盖**旧图）。
5. **历史 ROI 估计（P0-1「+5～12%」等）作废**：建立在未承载负载的图上，不构成基准支撑。

---

## 1. 现状（旧图字段级证据）

| 项 | U0200 | U0800 | 证据 |
|---|---|---|---|
| 文件 | `[2]0LoadBench_U0200.yrm` 14621 B | `[2]0LoadBench_U0800.yrm` 47604 B | `out/loadbench/` |
| MultiplayerOnly | 1 | 1 | `[Basic]` |
| MaxPlayer / MinPlayer | 2 / 2 | 2 / 2 | `[Basic]` |
| 预置 Units | 120（Russians 60 + Americans 60） | 480（240+240） | `[Units]` owner 字段 |
| 预置 Infantry | 80（40+40） | 320（160+160） | `[Infantry]` owner 字段 |
| 合计 | **200** | **800** | |
| owner 分布 | **仅** Russians / Americans | **仅** Russians / Americans | 无 Neutral/Special/Multi* |
| PlayerControl | 双方均为 `no` | 同左 | `[Russians]`/`[Americans]` |
| cell 堆叠 | 200 对象 / 200 唯一 cell | 800 / 800 | max stack=1 |
| 其它 house | 12 个 house IQ=0、无对象 | 同左 | |

完整 dump：`out/re_work/mimo_benchmap/f1_rootcause.txt`。

---

## 2. 根因（为什么是 21/22）

### 2.1 遭遇战 house 实例化规则 `[实证+推演]`

| 事实 | 证据 |
|---|---|
| 遭遇战按玩家槽创建 HouseClass | `MultiplayerOnly=1` + `MaxPlayer=2`；`ScenarioClass.HouseIndices[0x10]`（YRpp ScenarioClass.h:113） |
| 玩家 house 名 = 大厅所选国家名 | `HouseClass.IsPlayer() = CurrentPlayer \|\| PlayerControl`（HouseClass.h:421） |
| 开局部队来自 StartingUnits 而非地图 [Units] | `HouseClass.StartingUnits` + `RespawnStartingForces() @ 0x50D440`（HouseClass.h:246,695） |
| 地图 [Units] 的 owner 必须命中已存在的 HouseClass | RA2 对象创建通用规则；owner 无对应 house ⇒ 对象不实例化 `[推演]` |

### 2.2 21/22 的构成 `[推演]`

2 个玩家槽 × (1 MCV + 若干护卫) ≈ 20–22，与 ZC 实测 21/22 吻合；
与地图预置 200/800 **无交集**。旧图的军队在选国 ≠ Russians/Americans 时全部丢失。

### 2.3 排除项 `[实证]`

- 非坐标越界：`to_cell` 合法，200/800 对象占唯一 cell。
- 非堆叠丢弃：max stack = 1。
- 非类型非法：MTNK/HTNK/TTNK/E1/GI/FLAKT 均为标准 ID。

---

## 3. 三方案对比

| 维度 | A 改图（14-house fanout）★已落地 | B 改口径（战役图/门限重定） | C 不可行 |
|---|---|---|---|
| 能否在遭遇战承载目标负载 | **能**（2 槽 × target/2） | 能（战役模式 house 可控） | — |
| 与选国无关 | **是** | 否（战役固定 house） | — |
| 是否改门禁 | 否 | 需改 bench_metrics 门限 | — |
| 文件体积 | U800 约 310 KB（14× 冗余） | 正常 | — |
| 风险 | Neutral/Special 为 MultiplayPassive，可能不参与战斗（但仍实例化）`[待实测]` | 破坏 PROTOCOL 遭遇战场景定义 | — |
| 结论 | **采用** | 备选 | 排除 |

**方案 A 设计**：

- 每个标准 house（14 个，含 Neutral/Special）写入 `target/2` 个对象；
- 偶数序 house 占左带（cols 12–42），奇数序占右带（cols 58–88），`mission=Hunt`；
- `Allies=<self>` ⇒ 所有 house 互为敌对，Hunt 会互相搜索；
- IQ=5；`MultiplayerOnly=1`；`FreeRadar=yes`；
- 运行时：2 个玩家槽 house 各实例化 `target/2` = 目标负载；Neutral/Special 为附加负载（可略超）。

**方案 B 规格（未实施）**：改用战役图（`MultiplayerOnly=0`，`PlayerControl=yes` 固定我方 house），
门禁改为「战役模式下 valid_samples ≥500」。需 Lead 另卡改 `bench_metrics.py` 与 PROTOCOL §2。

---

## 4. 新图产物

| 文件 | 字节 | 文件内对象 | 每 house | 2 槽期望负载 |
|---|---|---|---|---|
| `[2]0LoadBench_U0050_H1.yrm` | 22359 | 350 | 25 | **50** |
| `[2]0LoadBench_U0200_H1.yrm` | 79052 | 1400 | 100 | **200** |
| `[2]0LoadBench_U0800_H1.yrm` | 309630 | 5600 | 400 | **800** |

- 构建脚本：`tools/bench_maps/build_bench_maps.py`（可复跑）
- 自检报告：`out/re_work/mimo_benchmap/build_report.json`
- **旧图未覆盖**（sha256 复核：U0200 `da5d0d52…`，U0800 `6754ad99…`）

构建命令：

```powershell
python tools\bench_maps\build_bench_maps.py 50 200 800
```

自检口径（脚本内置）：`total_objects == per_house × n_houses` ∧ `MultiplayerOnly=1` ∧ 含 `[Units]/[Infantry]/[Houses]` ⇒ OK。

---

## 5. 真机验证步骤（交 ZCode，本卡不跑）

| 步骤 | 动作 | 期望 | 判定 |
|---|---|---|---|
| V1 | 将 `out/loadbench/[2]0LoadBench_U0200_H1.yrm`、`U0800_H1.yrm` 复制到游戏地图目录（由 ZCode/Lead 决定目标路径，**本卡不写游戏目录**） | 文件就位 | — |
| V2 | 启动 `gamemd.exe` → 单人遭遇战 → 选 `0LoadBench U0200 H1` → **任意选国**（不需指定 Russia/America）→ 开局 | 地图可进 | — |
| V3 | 开局后立即读机动单位数（遥测：`bench_replay.py` 的 `mobile_count()`，数组 `0x008B4108` 等 Count@+16） | U200：`units_seen ∈ [100, 320]`（2 槽 × 100 ± StartingUnits/Neutral 浮动）；U800：`∈ [400, 1280]` | 出区间即 FAIL |
| V4 | 旧图对照（可选）：同法进旧 `U0200`（非 H1） | `units_seen ≈ 21/22` | 复现根因 |
| V5 | 跑 `python tools\bench_replay.py --tiers 200 800 --windows 3 --window-seconds 20 --warmup 12` | `valid_samples` U200≥300 / U800≥500；`coverage_pct ≥70%` | 达门禁 |
| V6 | `python tools\bench_metrics.py --run <run.json>` | `overall=PASS` | 否则不得宣称达标 |

**遥测字段**：`run.json: units_seen`、`frames.fps_avg`、`valid_samples`、`coverage_pct`。
**注意**：`units_seen` 期望区间应按「2 槽 × per_house + StartingUnits + Neutral/Special 补充」设定，不能用旧的 `expect_units=200 ± 0.5` 硬卡（H1 图运行时可能略超 200）。

---

## 6. 对历史 ROI 估计的处置

| 旧结论 | 处置 | 理由 |
|---|---|---|
| P0-1 渲染优化「+5～12%」 | **作废** | 建立在未承载 U200/U800 负载的图上；有效样本/覆盖率不达门禁 |
| `perf_U0800.json` / `perf-profile.json` 基线 | **维持 INVALID_SAMPLE** | 已由 bench_metrics --historical 判定 |
| 任何引用旧图 FPS 的对比 | **不得引用** | 负载未实例化，FPS 反映的是 21 单位场景 |

**新基线**须由 H1 图 + V5/V6 步骤重测后另立；在此之前不得写任何性能百分比。

---

## 7. 风险与红线

| 红线 | 触及？ | 说明 |
|---|---|---|
| ① 同步语义/命令序 | 否 | 未改游戏代码/存档 |
| ② 随机数消费序 | 否 | |
| ③ 存档结构 | 否 | |
| ④ 渲染像素等价性 | 否 | |
| 启动游戏/注入 | **否** | 本卡纯离线 |

新图会改变遭遇战单位密度与 AI 行为，属**基准场景变更**；性能结论须在 H1 图上重测，不可与旧图混比。

---

## 8. 未闭环清单

| ID | 缺口 | 原因 | 下一步 | 级别 |
|---|---|---|---|---|
| U-MB-1 | Neutral/Special（MultiplayPassive）的预置单位是否实例化 | 离线无法观察运行期 | 真机 V3：若 units_seen 只有 2×per_house 而无额外，说明 Passive 房不实例化（不影响目标负载） | P2 |
| U-MB-2 | H1 图实际 units_seen 区间 | 需真机 | V3 实测后回填期望区间 | **P0** |
| U-MB-3 | 14-house fanout 是否触发引擎对象数上限 | 5600 行文件/800 运行时 | U800 H1 真机进局 | P1 |
| U-MB-4 | 旧图 21/22 是否含 StartingUnits | 推演 | V4 对照实验 | P2 |

---

## 9. 交付物

| 类型 | 路径 |
|---|---|
| 新基准图 ×3 | `out/loadbench/[2]0LoadBench_U{0050,0200,0800}_H1.yrm` |
| 构建脚本 | `tools/bench_maps/build_bench_maps.py` |
| 根因分析脚本 | `tools/bench_maps/analyze_f1_rootcause.py` |
| 根因 dump | `out/re_work/mimo_benchmap/f1_rootcause.txt` |
| 构建自检 | `out/re_work/mimo_benchmap/build_report.json` |
| 本口径文档 | `docs/re/bench_map_rework.md` |

---

## 10. 一句话给下游

> 旧基准图的 200/800 单位全挂在 `Russians`/`Americans`，遭遇战只实例化玩家槽 house 的对象 ⇒ 实际只有 StartingUnits（21/22）；
> 新 H1 图把 `target/2` 兵力扇出到全部 14 个 house，**任意选国**都能载入目标负载；历史性能 ROI 估计作废，须在 H1 图上重测。
