# H1 载体装入后分层复测 —— 五类判定与证据

- run_id：`NEXT_RE_20261112_R02`
- 卡：W9（H1 载体装入后的分层复测，真机，单实例，两趟）
- 日期：2026-11-13
- 前置：Lead 已装入 `ra2youli\[2]0LoadBench_U0800_H1.yrm`（309,822 B，SHA-256 `e3acc130…d9e39`），装入前地图类文件 277 → 装入后 278。
- 探针：`h1_probe.py`（--run 第一趟列表判定；--run2 第二趟身份钉死 + 开局采样）。底层实现全部复用 `W7_load_baseline\load_baseline_probe.py`（已验证），本卡未用 SuspendThread/StackWalk64/MiniDump/断点/注入/写目标内存。

---

## 结论（主判定）

**落在类 2：已进列表但名称为空（列表显示字面 `No Name`）。**

- 列表条目 268 → **269**（+1 与装入文件数一致）；目标显示名 `[2] 0LoadBench U0800 H1 fp:1189b6b550ff` 在列表中 **0 命中**（完整名与子串双查）。
- 新增条目 = **索引 [97]**，其显示名称在游戏内存里就是字面 **UTF-16 `"No Name"`**；同一 itemdata 缓冲内嵌 **ASCII 文件名 `[2]0LoadBench_U0800_H1.yrm`** 与 **`No Digest`** —— 条目身份直接钉死，非排序推断。
- 名称读取失败口径的「空名条目」为 0（269 条全部 diag=ok）——`No Name` 不是读取失败，是游戏写入名称槽的兜底文案。

开局补充判定（选中 [97] 实测）：**进图成功（类 4 否），但开局 ~20s 即异常结束进结算屏（类 5 倾向，无画面直接证据，详见 §4）**。

历史遗留问题「H1 高负载图进不了对局」在表现层的机理：**列表里按真名找不到这张图（0 命中），它只以 `No Name` 形态出现**。RE-N03 的类 1（文件未发现）在装入后已排除，问题推进到类 2。

---

## 1. 证据一：离线文件事实（第 2 步）

`[2]0LoadBench_U0800_H1.yrm` 的 `[Basic]`（ASCII 明文，`-LiteralPath` 读取）：

| 字段 | 原值 |
|---|---|
| `Name` | `[2] 0LoadBench U0800 H1 fp:1189b6b550ff` |
| `GameMode` | `standard` |
| `MaxPlayer / MinPlayer` | `2 / 2` |
| `Official` | `no` |
| `EndOfGame` | `no` |
| `MultiplayerOnly` | `1` |
| `Player` | `Russians` |
| `H1Tier / H1Fingerprint` | `U0800 / H1FP1\|U0800\|1189b6b550ff` |

段名普查：**无 `[Triggers]`/`[Tags]`/`[Events]`/`[Actions]`/`[SpecialEffects]` 段**；有 `[Units]`/`[Infantry]`/`[Houses]`/`[Waypoints]`/`[SpecialFlags]`。⇒ 图内**无主动结束机制**，排除「基准图设计内秒结束」的替代解释。

文件↔条目映射（全部 6 个 LoadBench 系文件离线读 `[Basic]Name`）：

| 文件 | [Basic]Name | 列表条目 |
|---|---|---|
| `[2]0LoadBench_U0050.yrm` | `[Pro] [2] Urban Rush` | [92] |
| `[2]0LoadBench_U0100.yrm` | `[2] 0LoadBench U100` | [93] |
| `[2]0LoadBench_U0200.yrm` | `[Pro] [2] Urban Rush` | [94] |
| `[2]0LoadBench_U0400.yrm` | `[Pro] [2] Urban Rush` | [95] |
| `[2]0LoadBench_U0800.yrm` | `[2] 0LoadBench U800` | [96] |
| `[2]0LoadBench_U0800_H1.yrm` | `[2] 0LoadBench U0800 H1 fp:1189b6b550ff` | **列表无此名；[97] 显示 No Name** |

## 2. 证据二：列表证据（第一趟 + 第二趟复核）

两趟列表读取一致（`out\maplist.json` / `out\maplist_run2.json`）：

- 条目总数：**269**（装入前基线 268，Δ=+1，符合预期）。
- 目标命中：**0**（先按完整显示名精确匹配，再按子串 `0loadbench u0800 h1`，均无）。
- 读取失败/空串条目（itemdata=0 / RPM 失败 / UTF-16 解码失败 / 空串）：**0 个**。
- **字面 `No Name` 条目：2 个，索引 [91] 与 [97]**。
- 类 3 复核：不存在名称多候选混淆（0 命中）。备注：若按字面 `No Name` 搜图会命中 2 条（[91]=`prm.yrm`、[97]=H1），存在错选可能；按真名搜则必然找不到。

## 3. 证据三：No Name 条目身份（第二趟 itemdata 缓冲 768B，`out\nn_audit_{91,97,96}.hex`）

| 索引 | 名称槽（UTF-16 头） | 缓冲内 ASCII 文件名 | digest 区 |
|---|---|---|---|
| [91] | `No Name` | `prm.yrm` | `MAYVqKRRpYxsBB4z1DOqHiJdM9M=` |
| **[97]** | **`No Name`** | **`[2]0LoadBench_U0800_H1.yrm`** | **`No Digest`** |
| [96]（对照） | `[2] 0LoadBench U800` | `[2]0LoadBench_U0800.yrm` | `aAH/2zw0qjY15850Ujm4b5XS4Nc=` |

⇒ [97] 即 H1 载体：**名称槽被填成 "No Name"，digest 未算出（"No Digest"）**；同族 [96]（U0800.yrm，小 6.4 倍）名称与 digest 都正常。装入前 [91]（`prm.yrm`）已是 No Name，与本次新增无关（插入点在 [97]，其前后索引与文件名序吻合）。

## 4. 证据四：开局行为（第二趟，选中 [97] → UseMap → StartGame → 70s@30ms 采样）

采样：`out\run2.ndjson` 2129 拍、读失败 0。逐拍字段：frame/mode/g1..g4/A8E9A0/ABCD58/exitstate/win_foreground + 5s 间隔 UI 控件快照。

**frame 区间速率曲线（5s 桶，区间口径，非逐帧 FPS；完整表见 `out\analyze_run2.json`）：**

| 时间段 | 速率（计数/s） |
|---|---|
| 0–4.95s | <29（StartGame 点击后首窗，含菜单尾帧） |
| 4.95–20s | **31.12 / 31.28 / 30.71（三桶连续 ≈29–32 局内签名）** |
| 20–70s | **0（停推 49s+，一段连续 stall 21.0s→70.0s）** |

- 2s 滑动窗：min `0.0 @20s`，max `32.59 @4.95s`。
- `mode_A8B238`：2129 拍全部 = 5（已实测口径：mode 不区分加载/局内/闲置，仅记录不判）。
- `exitstate`：全程 0。`g1..g4`：全程 0。`A8E9A0`：全程 1。
- `ABCD58`（帧处理闩候选）：493 拍 1 / 1636 拍 0 —— 1 的时段与 frame 推进段重合，21s 后闩落 0。
- `A8ED50`（Bullet Count 候选，语义未证）：range 0..9；`B0CE88`（脏矩形 Count 候选，语义未证）：range 0..36，局内段有波动（渲染活动存在）。
- UI 时间线：0–20s 无按钮（加载/局内 DDraw 画面）；**~25s 起持续出现 `GUI:Continue` 按钮直至采样结束（70s）**，其间无其他按钮、无退出对话框。

### 类 4 / 类 5 判定

- **类 4（加载失败：停在加载屏/报错/退回菜单）→ 否**。frame 以 ≈31/s 连续推进 15s（≥60s 判据在此场景不适用——游戏在 20s 即结束），且最终落点是**结算屏（Continue 按钮）**，不是加载屏、无报错对话框、未退回主菜单。`GUI:Continue` 结算屏只能出现在战斗结束之后，反证进入过局内。
- **类 5（进图但 owner 未实例化）→ 倾向成立，观测受限不能实锤**。依据：
  1. 图内无 triggers、`EndOfGame=no`（§1）——图自身无结束机制；
  2. 正常遭遇战不可能开局 ~15–20s 自然打完，而本局 20s 即进结算屏；
  3. Bullet Count 候选 `A8ED50` 全程近 0（0..9）——几乎没有战斗活动。
  这与「玩家 owner 未实例化 → 立即判负 → 结算屏」假设相容。但本卡无截图、无单位/owner 计数的已验证地址，**「没观测到」≠「不存在」**，按红线不判实锤。
- 停推说明：21s 后 frame=0 期间窗口处于**结算屏可见 UI 状态**（Continue 按钮），不是无 UI 闲置态；未抓栈（遵守禁令），无需「本卡不判」豁免条款——落点已由 UI 证据定性。

---

## 5. 判定汇总

| 类 | 判定 | 依据 |
|---|---|---|
| 1 文件未发现 | **排除** | 文件在（哈希核对一致）；列表 269；[97] 缓冲含其文件名 |
| 2 已进列表但名称为空 | **✅ 成立（主判定）** | [97] 名称槽 = 字面 "No Name"（游戏内存）；真名 0 命中；附带 "No Digest" |
| 3 选中了错误条目 | 排除（附备注） | 名称 0 命中，无多候选混淆；按 No Name 搜会命中 2 条（[91]/[97]）错选风险存在但非历史路径 |
| 4 加载失败 | 排除 | ≈31/s 局内速率 15s + 可达结算屏 |
| 5 进图但 owner 未实例化 | **倾向成立（待实锤）** | 无 trigger 图 20s 即结束 + A8ED50 近 0；无画面/单位直接证据 |

## 6. 交付物

- `h1_probe.py`（--run / --run2 / --analyze）
- `out\maplist.json`（第一趟 269 条全列表）、`out\maplist_run2.json`（第二趟复核）
- `out\nn_audit_91.hex / nn_audit_97.hex / nn_audit_96.hex`（itemdata 缓冲 768B 原始字节）
- `out\run.ndjson`（第一趟事件流）、`out\run2.ndjson`（第二趟 2129 拍采样）、`out\meta.json`、`out\meta_run2.json`
- `out\analyze_run2.json`（速率曲线/分布/停推段）
- `H1_Layering_Result.md`（本文）、`SAFETY.md`、`CONFIG_RESTORE.md`、`RUNLOG.md`、`UNCOVERED.md`
