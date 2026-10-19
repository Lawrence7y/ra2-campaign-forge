# harness_closeout_zc11 —— bench_replay ZC-11 收口变更与回归

> [META]
> task=ZC11-HARNESS-CLOSEOUT · 范围=**仅 tools/** · 日期 2026-09-29
> 上游依据：`out/re_work/zcode_live/RESULT_ZC11.md` §段 E / §[3] 勘误 / §[9]②④⑤
> 改前备份：`tools/bench_replay.py.before-zc11-closeout`（81,908 B，逐字节保留旧行为）
> 本卡**不启动游戏进程**；真机回归交 ZCode。离线单测用 `zc11/evidence/segE/**` 截图。

---

## [0] 结论摘要

1. **enter_battle fallback ESC 缺陷已修**（ZC-11 [9]④）：进对局确认前全局禁用 ESC；加载期判定改为「帧推进 + 战术区色数」双校验；已在对局但兵力门禁不过时**只提示、不再兜底导航**（避免 ESC×2 打断开局 ⇒ units_seen 恒 0）。
2. **箭头键等时闭环机位复位已移植**（ZC-11 [9]② / segE3）：RIGHT 1.0s 挪走 ⇄ LEFT 1.0s 等时反向；验收 MAD≤2.0 且 NCC≥0.99，ROADS 静态 ROI 逐字节 0 差；**小地图点击复位继续禁用**（`reset_camera` 仅保留兼容，不再作为对齐手段）。
3. **离线单测 50/50 PASS**，MAD/NCC 与 segE3_record.json **逐值复现**（moved MAD 13.363–13.3683 / back MAD 0.1311–0.1527 / NCC 0.99516–0.99606 / ROADS max_delta=0）。
4. ZC-10A 兼容面未破坏：`verify_screen` / `close_pause_menu` / `reset_camera` / `enter_battle` / `try_auto_nav` 签名与默认行为保留；`--game-dir` 保持向后兼容。

---

## [1] 变更点（相对 `bench_replay.py.before-zc11-closeout`）

| # | 位置 | 变更 | 理由 |
|---|---|---|---|
| 1 | `press_key` 上方 | 新增 `_ESC_LOCKED` / `set_esc_locked()`；`press_key(ESC)` 在锁定时**早退不注入** | 进对局确认前禁用 ESC（[9]④） |
| 2 | `verify_screen` 后 | 新增 `wait_battle_ready()`：帧推进（≥3fps）**且** 战术区色数（`verify_screen("battle")`）双校验 | 加载期口径与 ZC-11 segC/segE 一致，抗假阳性 |
| 3 | `try_auto_nav` | 新增 `allow_esc: bool = True`；`False` 或全局锁定时跳过 logo ESC | 旧行为保留（默认 True）；fallback 路径显式禁 ESC |
| 4 | `enter_battle` | ① 入口 `set_esc_locked(True)`（finally 还原）；② `check()` 改用 `wait_battle_ready`；③ **已在对局但兵力不过 ⇒ 只提示、return False,cnt，不再 try_auto_nav**；④ 仅「确实不在对局」才 ESC-free 兜底导航 | 根除「加载中 ESC×2 打断开局」；H1 713 与门禁不兼容只提示不改 H1 |
| 5 | `reset_camera` | docstring 标注小地图点击**已禁用**，指向 `reset_camera_arrows`；**函数体未改**（ZC-10A 兼容） | 不破坏 ZC-10A 调用面 |
| 6 | `reset_camera` 后 | 新增 `mad_ncc` / `reset_camera_arrows` / `realign_camera` 薄封装 → `tools/bench_cam_reset.py` | segE3 移植；每档切换后可重做对齐 |
| 7 | `run_tier` | 新增 `cam_align: bool = False`：热身后一次闭环对齐（可重做） | 「每档切换后镜头可能被战斗拽走，须可重做对齐」 |
| 8 | `main` | 新增 `--cam-selftest` / `--reset-cam` / `--reset-cam-ref` / `--reset-cam-out` / `--cam-align`；`--game-dir` 不变 | 任务要求的子命令/参数 |
| 9 | **新文件** `tools/bench_cam_reset.py` | `mad_ncc` / `mad_ncc_rgb` / `check_reset_quality` / `hold_key` / `arrow_closed_loop` / `reset_camera_arrows` / `realign_camera` / `selftest` | 隔离纯度量（离线可 import）与 Win32 按键 |

### 1.1 行为对照（旧行为 → 新行为）

| 场景 | 旧行为 | 新行为 |
|---|---|---|
| enter_battle 首次 check 失败（地图加载中） | `try_auto_nav` 开头 **ESC×2 打断开局**，units_seen 恒 0 | ESC 门禁生效，不注入 ESC；继续双校验等待 |
| 已在对局但 units_seen 超门禁（如 H1=713 vs 期望 200） | 误判失败 → 兜底导航 → ESC 打断 | 只打印 `[units]` 提示并 `return False, cnt`，**不导航** |
| 确实不在对局（仍在菜单） | try_auto_nav（含 ESC） | try_auto_nav(**allow_esc=False**)，菜单点击路径不变 |
| 机位复位 | 小地图点击（ZC-10A，空洞 MAD=0） | `reset_camera_arrows` 箭头键闭环；小地图路径仅保留兼容 |
| 兵力门禁失败时的 SKIP 语义 | `return False, 0` | 保持 SKIP 语义，但返回真实 `cnt` 便于诊断（H1 不改） |

---

## [2] 新参数 / 新 API 用法

### 2.1 CLI

```bash
# 离线 MAD/NCC 自检（segE3 截图，不启动游戏）
python tools/bench_replay.py --cam-selftest
python tools/bench_cam_reset.py --selftest

# 对【已在运行】的游戏窗口做箭头键等时闭环复位（本命令不启动游戏）
python tools/bench_replay.py --reset-cam --game-dir ra2bench
python tools/bench_replay.py --reset-cam --reset-cam-ref path/to/ref.png --reset-cam-out out/re_work/harness_closeout/cam_reset

# 基准跑档时每档热身后做一次闭环对齐（镜头被战斗拽走后可重做）
python tools/bench_replay.py --tiers 200 800 --cam-align --game-dir ra2bench

# 向后兼容：--game-dir 语义不变（默认 ra2youli；基准环境分离后指向 ra2bench）
python tools/bench_replay.py --tiers 200 --game-dir ra2bench
```

### 2.2 Python API

```python
import bench_replay as br

# —— ESC 门禁（进对局确认前）——
prev = br.set_esc_locked(True)     # 禁用 ESC；press_key(0x1B) 变为 no-op
try:
    ...
finally:
    br.set_esc_locked(prev)

# —— 加载期双校验（帧推进 + 战术区色数）——
ok = br.wait_battle_ready(mon, hwnd, timeout=30.0)

# —— 箭头键等时闭环复位（推荐）——
res = br.reset_camera_arrows(hwnd, shots=shots, tag="tier200_cam", ref=ref_png, tries=3)
# res["ok"] / res["quality"]["full"]["mad"|"ncc"] / res["quality"]["roads_rgb"]["max_delta"]

# —— 镜头被战斗拽走后重对齐（只 LEFT 等时 hold）——
res = br.realign_camera(hwnd, shots=shots, ref=ref_png)

# —— 纯离线度量 ——
m = br.mad_ncc(ref_png, shot_png, crop_rect=(1010, 600, 1230, 730))  # ROADS
```

### 2.3 等时闭环协议（ZC-11 segE3 已验证）

| 步骤 | 动作 | 期望 |
|---|---|---|
| 挪走 | **RIGHT 1.0s** | 与 ref 的 MAD ≫ 5（实测 ≈13.36，非空洞反证） |
| 复位 | **LEFT 1.0s**（等时反向） | MAD ≤ 2.0（实测 ≈0.13）且 NCC ≥ 0.99（实测 ≈0.996） |
| 静态 ROI | ROADS `(1010,600,1230,730)` | 逐字节 0 差（max_delta=0） |
| 禁止 | 小地图点击复位 | ZC-10A FAIL：点击无效时 MAD=0 属空洞成功 |
| 重对齐 | 每档切换后可重复调用 | 战斗拽走镜头后 `realign_camera` 或重取 ref 再闭环 |

阈值常量：`bench_cam_reset.MAD_TOL=2.0` / `NCC_TOL=0.99` / `LOOP_HOLD_S=1.0` / `ROADS_RECT`。

---

## [3] 回归命令（离线，本卡已跑）

```bash
# ① 语法 / AST
python -m py_compile tools/bench_replay.py tools/bench_cam_reset.py

# ② segE3 MAD/NCC 复现（期望 3/3 PASS，数值与 segE3_record.json 一致）
python tools/bench_cam_reset.py --selftest
python tools/bench_replay.py --cam-selftest

# ③ 离线单测 50 项（MAD/NCC + 阈值 + ESC 门禁 + ZC-10A 兼容面）
python out/re_work/harness_closeout/test_cam_reset_offline.py

# ④ CLI 向后兼容面（--game-dir 仍在）
python tools/bench_replay.py --help
```

本卡实测原文摘要：

```
python -m py_compile tools/bench_replay.py tools/bench_cam_reset.py   → OK
bench_cam_reset --selftest:
  i=0 moved_MAD=13.364   back_MAD=0.1339   back_NCC=0.99572  ROADS_max_delta=0 → PASS
  i=1 moved_MAD=13.3683  back_MAD=0.1527   back_NCC=0.99516  ROADS_max_delta=0 → PASS
  i=2 moved_MAD=13.363   back_MAD=0.1311   back_NCC=0.99606  ROADS_max_delta=0 → PASS
  === 离线自检 PASS ===
test_cam_reset_offline.py: PASS=50 FAIL=0
```

真机回归（**交 ZCode，本卡未跑**）建议最小集：

```bash
# 冒烟：旧缺陷路径 —— 兵力门禁与 H1=713 不兼容时不得再按 ESC
python tools/bench_replay.py --tiers 200 --windows 1 --window-seconds 8 --game-dir ra2bench
# 期望日志出现 [units] 提示且无 ESC 注入；units_seen 非恒 0（若真进了对局）

# 复位：对局内 --reset-cam 或 --cam-align
python tools/bench_replay.py --reset-cam --game-dir ra2bench
# 期望 cam_reset_record.json: ok=true, MAD≤2.0, NCC≥0.99, ROADS max_delta=0
```

---

## [4] 写作用域合规

| 路径 | 动作 |
|---|---|
| `tools/bench_replay.py` | 修改（改前备份 `bench_replay.py.before-zc11-closeout`） |
| `tools/bench_cam_reset.py` | 新增 |
| `out/re_work/harness_closeout/**` | 新增（离线单测 + 复现脚本 + 记录） |
| `docs/re/harness_closeout_zc11.md` | 新增（本文） |
| `ra2render/**` / `ra2youli/**` / `ra2bench/**` / 地图 / 台账 | **未触碰** |
| 游戏进程 | **未启动** |

---

## [5] 已知残留 / 不在本卡

1. **H1 分档失效（P0，ZC-11 [9]⑤）**：units_seen 由对阵国家主导（21–723），与档位无标度。本卡只做「门禁不过时提示且不 ESC 打断」，**不改 H1 图、不改门禁公式**。拆 fanout 前 H1 性能 ROI 数字继续不可用。
2. **真机 enter_battle 路径回归**：本卡仅离线验证逻辑与 ESC 门禁；「加载中不再被打断」需 ZCode 真机最小集确认。
3. **`reset_camera`（小地图）**：保留函数体未改，但文档/注释已标禁用；若后续确认零调用方，可另卡删除。
4. **官方兵力门禁 320 上限**：与 H1=713 不兼容（可提示，不必改 H1）——本卡提示文案已写入 `enter_battle`。

---

## [6] 产物索引

| 类别 | 路径 |
|---|---|
| 改前备份 | `tools/bench_replay.py.before-zc11-closeout` |
| 新模块 | `tools/bench_cam_reset.py` |
| 离线单测 | `out/re_work/harness_closeout/test_cam_reset_offline.py`（结果 `test_cam_reset_offline_result.txt`） |
| segE3 复现脚本 | `out/re_work/harness_closeout/repro_sege3_madncc.py` |
| 本文 | `docs/re/harness_closeout_zc11.md` |

---

## §九 草稿 —— ZC-11 §[9] 待裁决项的收口答复（供写回 RESULT / 收口报告）

> 下文按 RESULT_ZC11 §[9] 编号逐条给出**本卡可关闭 / 仍开放**的草稿表述，供 Lead 裁决后写回。

**② 段 E 复位手段是否固化进 harness —— 本卡已固化（建议关闭该项）。**
可用手段 = 箭头键等时闭环（RIGHT 1.0s ⇄ LEFT 1.0s）+ 复位校验（MAD≤2.0 且 NCC≥0.99，ROADS 静态 ROI 逐字节 0 差）；×3 重复稳定（离线用 segE3 截图逐值复现 0.13/0.996）。实现落点：`tools/bench_cam_reset.py`，入口 `bench_replay.reset_camera_arrows` / `realign_camera` / `--reset-cam` / `--cam-align`。小地图点击复位维持禁用（`reset_camera` 仅兼容保留）。每档切换后镜头被战斗拽走时可 `realign_camera` 重做对齐；失败则重取 ref 或重开局（不伪造对齐成功）。

**④ harness 缺陷修复授权（enter_battle fallback ESC×2 打断开局）—— 本卡已修（建议关闭该项，真机最小集交 ZCode 确认）。**
修复口径与建议一致且已落地：
- 进入 `enter_battle` 即 `set_esc_locked(True)`（finally 还原）⇒ **进对局确认前禁用 ESC**；
- 加载期判定改 `wait_battle_ready` = **帧推进（CurrentFrame ≥3fps）+ 战术区色数（TACTICAL_COLOR_FLOOR）双校验**（segC/segE 同口径）；
- 附加硬化：已在对局但兵力门禁不过时**不再兜底导航**（旧路径正是 ESC 打断根因），只打印 `[units]` 提示并返回真实 cnt。

**⑤ H1 分档失效专项 —— 本卡未拆，维持 P0 开放。**
本卡仅保证：门禁不兼容（713>320）时给出明确提示且不触发 ESC 打断；**不改 H1、不改门禁公式**。fanout 触发机制拆明前，一切以 H1 图为前提的性能 ROI 数字继续不可用。

**① vision-dirty 默认 / ③ 非线性混色桩 / ⑥ 段 G 动态手段 —— 本卡不动，维持原裁决状态。**

---

## [7] 变更文件哈希留痕（收口时）

| 文件 | 说明 |
|---|---|
| `tools/bench_replay.py.before-zc11-closeout` | 81,908 B 改前逐字节备份 |
| `tools/bench_replay.py` | 改后（新增 ESC 门禁 / 双校验 / 闭环复位 / CLI） |
| `tools/bench_cam_reset.py` | 新增（纯度量 + 闭环实现） |
