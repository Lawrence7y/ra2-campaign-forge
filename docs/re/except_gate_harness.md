# except_gate_harness —— 对局后 `except.txt` 门禁（崩溃可观测性）

> [META]
> task=EXCEPT-GATE-HARNESS · 日期 2026-09-30 · 执行方=MiMo（轨道 M · harness）
> 上游依据：`docs/re/except_zc11_forensics.md` §[9]⑨（崩溃靠收尾才发现）+ RESULT_ZC11 [7] 勘误（E-ZC11-7a/b/d）
> 改前备份：`tools/bench_replay.py.before-except-gate`（91,651 B，逐字节保留旧行为）
> 新模块：`tools/check_except_gate.py`
> 本卡**不启动游戏进程**；真机回归（含一次崩溃复现）交 ZCode。离线自检用临时目录。

---

## [0] 结论摘要

1. **对局/分段收尾主动检查 `except.txt` 已落地**：`run_tier`（每局）、`run_evidence_config`（每段）、`run_menu_selftest` 均在收尾调用 `except_gate_end`；结果写入 run JSON（`except_gate` 字段）与门禁报告。
2. **新生判定 = mtime/哈希/size 变化**（相对段基线 + 会话基线双兜底）：`exists` False→True（appeared）、`mtime_ns` 变、`size` 变、`sha256` 变，任一即 fresh；既有 `except.txt` 不变**不算**新生。
3. **不得当 PASS**：严格模式（默认）fresh ⇒ 段 verdict=FAIL + 进程退出码 **2**；`--no-expect-no-except` 宽松模式 ⇒ verdict=**FAIL_LANE**（记录+标记，退出码 0），**两种模式下 fresh 都不会记 PASS**。
4. **T10 ESC 锁 / `bench_cam_reset` 未破坏**：`harness_closeout` 离线单测 **50/50 PASS**；本次 except_gate 离线单测 **40/40 PASS**（含 ESC 门禁 spy、`reset_camera_arrows`/`realign_camera`/`mad_ncc`/MAD_TOL/NCC_TOL 兼容面）。

---

## [1] 变更点（相对 `bench_replay.py.before-except-gate`）

| # | 位置 | 变更 | 理由 |
|:---:|:---|:---|:---|
| 1 | `_except_is_fresh` 处 | **新模块** `tools/check_except_gate.py`：`fingerprint` / `diff_fingerprint` / `ExceptGate` / `selftest` | 可离线 import 的纯判定；游戏目录只读 |
| 2 | 同上 | 新增 `_except_gate_mod` / `make_except_gate` / `get_except_gate` / `except_gate_begin` / `except_gate_end` | 薄集成层，不改 ESC/复位路径 |
| 3 | `_except_is_fresh` | 旧口径（mtime 近 6h）→ **相对门禁基线的 exists/mtime/size/sha256 变化**；旧函数保留为 `_legacy_except_is_fresh` | 旧口径会把「改写既有 except.txt」漏成非新鲜 |
| 4 | `run_tier` | 开局 `except_gate_begin`；`finally` 收尾 `except_gate_end` 并把 `except_gate` 字段写入每个 run 记录 | 每局收尾主动检查（ZC-11 [9]⑨） |
| 5 | `run_evidence_config` | 段始 `except_gate_begin`；采样结束 `except_gate_end`（SKIP/早退路径 `finally` 兜底）；`except_fresh` + `except_gate` 双字段 | 每段收尾主动检查 |
| 6 | `run_menu_selftest` | 段始/收尾接入门禁；结果进 `evaluation` 旁的 `except_gate` 字段 | 菜单自检也不漏检 |
| 7 | `main` | 新增 `--expect-no-except` / `--no-expect-no-except`（**默认严格**）、`--except-gate-out`、`--except-gate-selftest`；会话基线启动快照；`_gate_exit_and_report` 汇总落盘并决定退出码 | 任务要求的开关与报告 |
| 8 | **未改** | `set_esc_locked` / `press_key` ESC 门禁、`try_auto_nav(allow_esc)`、`enter_battle` 双校验、`reset_camera_arrows` / `realign_camera` / `bench_cam_reset.py` 全部原样 | T10 兼容红线 |

### 1.1 判定语义（行为对照）

| 场景 | 旧行为 | 新行为 |
|:---|:---|:---|
| 对局中崩溃写出 `except.txt` | 靠收尾人工发现（ZC-11 事故） | 段收尾 `except_gate_end` 立即检出 `appeared` ⇒ FAIL / FAIL_LANE，写入 run JSON + 报告 |
| 改写既有 `except.txt`（mtime/内容变） | `_except_is_fresh` 仅看 mtime 窗口，可能漏 | `mtime_ns`/`size`/`sha256` 任一变化 ⇒ fresh |
| 既有 `except.txt` 全程未动 | 可能被误报 | 基线一致 ⇒ **不算新生**，PASS |
| 段间写入（段基线恰好覆盖新内容） | — | 会话基线兜底：`summary.session_fresh` 仍检出 |
| fresh 但想继续跑批 | — | `--no-expect-no-except`：记 FAIL_LANE（**不 PASS**），退出码 0，批不中断 |

---

## [2] 新参数 / 新 API 用法

### 2.1 CLI

```bash
# 默认严格：对局/分段收尾主动检查；新生 except ⇒ 退出码 2 + 报告
python tools/bench_replay.py --tiers 200 800 --game-dir ra2bench

# 宽松：仅记录并标 FAIL_LANE（不得记 PASS；退出码 0）
python tools/bench_replay.py --tiers 200 --game-dir ra2bench --no-expect-no-except

# 指定门禁报告路径（默认 out/re_work/except_gate/except_gate_<时间戳>.json）
python tools/bench_replay.py --evidence-config 1 --game-dir ra2bench --except-gate-out out/re_work/except_gate/zc11_repro.json

# 离线自检（临时目录，不启动游戏）
python tools/check_except_gate.py --selftest
python tools/bench_replay.py --except-gate-selftest

# 单点指纹复核（只读游戏目录）
python tools/check_except_gate.py --game-dir ra2bench --check
```

### 2.2 Python API

```python
import bench_replay as br

gate = br.make_except_gate(br.GAME_DIR, expect_no_except=True)   # 会话基线立即快照
br.except_gate_begin("u0200_001")
...                                   # 跑对局
seg = br.except_gate_end("u0200_001")  # 段收尾主动检查；verdict/reasons 在 seg["segment_diff"]
summary = gate.summary()               # PASS | FAIL | FAIL_LANE
code = gate.exit_code()                # 0 | 2（严格 FAIL）
rp = gate.write_report()               # out/re_work/except_gate/except_gate_<ts>.json
```

### 2.3 退出码约定

| 码 | 含义 |
|:---:|:---|
| 0 | PASS；或宽松模式 FAIL_LANE（已标记、不放行，但不强制中断批） |
| 1 | 既有通用失败（无采样窗口等） |
| **2** | **except 门禁严格 FAIL（新生 except.txt）** |
| 3 | `check_except_gate --selftest` 自检失败 |

报告 JSON 关键字段：`verdict` / `fresh_segment_count` / `segment_count` / `segments[].segment_diff.reasons`（appeared / mtime_changed / size_changed / sha256_changed / removed）/ `session_fresh` / `session_reasons` / `expect_no_except` / `except_path`。

---

## [3] 回归命令（离线，本卡已跑）

```bash
# ① 语法 / AST
python -m py_compile tools/bench_replay.py tools/check_except_gate.py tools/bench_cam_reset.py

# ② 门禁模块离线自检（18 项判定语义）
python tools/check_except_gate.py --selftest
python tools/bench_replay.py --except-gate-selftest

# ③ except_gate 集成离线单测（40 项：判定 + 集成面 + T10 ESC/cam 兼容）
python out/re_work/except_gate/test_except_gate_offline.py

# ④ T10 ESC 锁 / bench_cam_reset 原离线单测（50 项，须仍全绿）
python out/re_work/harness_closeout/test_cam_reset_offline.py

# ⑤ CLI 向后兼容面
python tools/bench_replay.py --help
```

本卡实测原文摘要：

```
python -m py_compile tools/bench_replay.py tools/check_except_gate.py tools/bench_cam_reset.py → OK
check_except_gate --selftest: 18/18 PASS（无文件/ appeared / 既有不变 / sha256 变 / FAIL_LANE / 会话兜底 / 报告落盘）
test_except_gate_offline.py: PASS=40 FAIL=0
  （含：ESC 锁定拦截 ESC、非 ESC 仍注入、解锁后可注入；reset_camera_arrows/realign_camera/mad_ncc/
    MAD_TOL=2.0/NCC_TOL=0.99 兼容面；enter_battle 签名兼容）
test_cam_reset_offline.py: PASS=50 FAIL=0   ← T10 未破坏
```

真机回归（**交 ZCode，本卡未跑**）建议最小集：

```bash
# 冒烟：正常一局后门禁应 PASS（无 except.txt 或既有未变化）
python tools/bench_replay.py --tiers 200 --windows 1 --window-seconds 8 --game-dir ra2bench
# 期望日志出现 [except-gate] u200_*: PASS 且退出码 0

# 崩溃复现（对应 forensics V1/V2）：同图 U0200 + 随机敌国，观察门禁 FAIL 路径
python tools/bench_replay.py --tiers 200 --windows 1 --window-seconds 20 --game-dir ra2bench
# 若该局崩溃写出 except.txt：
#   期望 [except-gate] u200_*: FAIL reasons=['appeared']，退出码 2，
#   报告 out/re_work/except_gate/except_gate_*.json 含 segments[].verdict=FAIL
```

---

## [4] 写作用域合规

| 路径 | 动作 |
|:---|:---|
| `tools/bench_replay.py` | 修改（改前备份 `bench_replay.py.before-except-gate`） |
| `tools/check_except_gate.py` | 新增 |
| `out/re_work/except_gate/**` | 新增（离线单测 + 结果 + 门禁报告落点） |
| `out/re_work/errata_patches/by_file/RESULT_ZC11.md.patch` | 新增（勘误补丁块） |
| `docs/re/errata_result_zc11.md` / `docs/re/except_gate_harness.md` | 新增（本文） |
| `out/re_work/zcode_live/RESULT_ZC11.md` / 台账 / `ra2render/**` / `ra2youli/**` / `ra2bench/**` | **未触碰** |
| 游戏进程 | **未启动** |

---

## [5] 已知残留 / 不在本卡

1. **真机崩溃路径回归**：门禁对「真崩溃写出 except.txt」的 FAIL 路径仅离线模拟（临时目录写文件）；需 ZCode 用 forensics V1/V2 场景实测一次。
2. **崩溃时点归因**：门禁只判「新生/变化」，不解析 except.txt 内容；崩溃段归属仍以 `docs/re/except_zc11_forensics.md` 时间线夹逼法为准（可后续加 seg 时间窗自动归因）。
3. **`removed`（except.txt 消失）**：记 reasons 但**不算 fresh**（游戏目录文件被人为挪走不应判崩溃）；若需「挪走即异常」可另卡收紧。
4. **H1 分档失效 / 段 G 动态 dump / vision-dirty 默认**：不在本卡，维持 ZC-11 [9] 原裁决状态。

---

## [6] 产物索引

| 类别 | 路径 |
|:---|:---|
| 改前备份 | `tools/bench_replay.py.before-except-gate`（91,651 B） |
| 新模块 | `tools/check_except_gate.py` |
| 离线单测 | `out/re_work/except_gate/test_except_gate_offline.py`（结果 `test_except_gate_offline_result.txt`） |
| 自检报告落点 | `out/re_work/except_gate/except_gate_*.json`（含 `selftest_except_gate.json`） |
| 勘误补丁块 | `out/re_work/errata_patches/by_file/RESULT_ZC11.md.patch` |
| 勘误登记 | `docs/re/errata_result_zc11.md` |
| 本文 | `docs/re/except_gate_harness.md` |

---

## §九 草稿 —— 供 RESULT_ZC11 §[9] / 台账引用

> 与 `docs/re/errata_result_zc11.md` §九草稿互补：那篇管「[7] 勘误落地」，本节管「门禁实现」的收口表述。

**[P0] 崩溃可观测性（forensics §[9]⑨）—— 本卡已落地（建议关闭该缺口，真机一次崩溃复现交 ZCode）。**
harness 在对局/分段收尾**主动检查游戏目录 `except.txt`**：新生（exists/mtime/size/sha256 变化）⇒ 记入段记录与门禁报告，严格模式退出码 2、宽松模式标 FAIL_LANE，**两种模式均不得记 PASS**。落点：`tools/check_except_gate.py` + `bench_replay` 的 `run_tier` / `run_evidence_config` / `run_menu_selftest` 收尾钩子；开关 `--expect-no-except`（默认严格）/ `--no-expect-no-except`；报告 `out/re_work/except_gate/except_gate_*.json`。ZC-11 那种「崩溃后 harness 继续跑批、靠收尾才登记」的观测缺口在机制上已封口。

**[P0] RESULT_ZC11 [7] 勘误 —— 补丁块就绪（见 `docs/re/errata_result_zc11.md`，待 Lead 解冻粘贴）。**
四处：E-ZC11-7a（[0]⑦）、7b（[7]）、7c（[1] 表 D 脚注）、7d（时间线：崩溃后 harness 未中断）。台账/任务卡「零崩溃」类表述同步改为「崩溃 1 次（原版 SBH），非注入肇因」。

**[P0] U0200 采样有效性 —— 维持待裁决（本卡给标准脚注，不代裁）。**
建议采纳 E-ZC11-7c 脚注方案（「含重启后重跑 + 8 min 空窗」）而非剔除数据；剔除与否由 Lead 裁决。

**[T10 兼容声明] ESC 锁 / 箭头键复位 —— 本卡未破坏（离线双单测全绿）。**
`set_esc_locked` / `press_key(ESC)` 拦截、`try_auto_nav(allow_esc)`、`enter_battle` 双校验、`reset_camera_arrows` / `realign_camera` / `bench_cam_reset.MAD_TOL=2.0` / `NCC_TOL=0.99` 全部原样；`test_cam_reset_offline.py` 50/50、`test_except_gate_offline.py` 40/40（含 ESC spy 与复位兼容面）。

**[其余] H1 分档失效专项 / 段 G 动态手段 / vision-dirty 默认 / 非线性混色桩 —— 本卡不动，维持 ZC-11 [9] 原裁决状态。**
