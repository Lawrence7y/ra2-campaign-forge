# HARNESS6 合入报告（补丁副本制 · 零真机）

**结论先行**

1. **母本零改动**：`qc151_trip.harness5.py` 实测 427,456 B / LF16 `f1e5bc7b0ff30c9c` /
   CRLF16 `3b10dae011d08c4b`，与任务书给定值逐位相符；`git status` 对该目录零输出。
2. **四项全部合入**（① WER 检测 / ② 载体隔离计数 / ③ near-limit WARN / ④ `--close-mode`），
   四条标记 `grep -c` 全部 > 0。
3. **零删除行成立**：母本 7782 行 → 副本 8452 行，**删除行 0**；母本行多重集 ⊆ 副本行多重集。
4. **未新增退出码**；`terminate_owned_process` 函数体与母本**逐字节相同**。
5. **有一项我认为需要附加限制才可放心用**：④ `close` 模式在**默认 terminate 下安全**，
   但 `close` 打开时 RC-4 的观测语义仍有结构性盲点（见 §7「诚实边界」第 3 条）。

---

## 1. 母本零改动证明

| 项 | 值 | 出处 |
|:--|:--|:--|
| 字节数 | `427456` | `_gen_harness6.py` 运行时打印 |
| LF sha16 | `f1e5bc7b0ff30c9c` | 同上（生成器断言 `SRC_SHA16` 相等，不等即 fail-closed） |
| CRLF sha16 | `3b10dae011d08c4b` | 独立复算 |
| `git status --porcelain lead/goal1_a8_fix_20261022/` | 空 | 命令实测 |

生成器只 `read_bytes()` 母本，从不 `import` / `exec`（母本 427 KB，import 会执行顶层
`SetProcessDPIAware()` 等）。全部改动通过**源码文本替换**施加。

## 2. 副本指纹

| 项 | 值 |
|:--|:--|
| 路径 | `lead/goal1_harness6_20261022/qc151_trip.harness6.py` |
| 字节数 | `461535`（+34,079） |
| LF sha16 | `a67cc05edd5034f8` |
| CRLF sha16 | `f45ed2040652982c` |
| 行数 | 7782 → 8452（+670） |
| 换行 | 纯 LF（`CR count = 0`，与母本一致） |
| diff | `h6.diff`，37,568 B，`+670 / -0` |

## 3. 四项逐项验收

### ① WER 检测 — `wer_scan_new_reports(rec, since_ts, carrier_dir=None)`

- **锚点**（`src.count(anchor) == 1` 实测）：
  - 函数体：`ANCHOR_C` = `# §10 · ⑤ 导航链与采帧` 段头三行 + `def find_main_window(pid: int) -> tuple:`（命中 1）
  - 调用点：`ANCHOR_H` = `note="★ 非授权趟（直启 gamemd，无 loader 派生进程）")`（命中 1）
- **新增行数**：约 139 行（§9-H6 段内 195 行 + finally 内 13 行调用块，按 diff 归属统计）
- **落盘段名 `WER`，键**：`wer_scan_since_ts`、`wer_scan_roots`、`wer_scan_error`、
  `wer_parse_error`、`wer_report_count`、`wer_reports`、`wer_out_of_carrier`、`wer_verdict`
- **★★ `Sig[]` 按名读值**：`_h6_wer_parse()` 先建 `名称 → 值` 映射（`sig`），取值一律走
  `_h6_sig_first(sig, names)`（中英双语名称表）；`sig_pairs` 只作**顺序留痕**，不参与取值。
  代码注释直接引用 `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` §340 原文。
- **`FriendlyEventName` / `AppPath`** 均记录；`AppPath` 经 `_a8_path_under_carrier`
  判定落在载体外 ⇒ 单独进 `wer_out_of_carrier`。
- **只读**：仅 `is_dir()` / `rglob()` / `stat()` / `read_bytes()`，无任何写、删、改名。
- **★ 未测不等于零**：`LOCALAPPDATA` 缺失、`since_ts` 为 `None`、扫描抛异常
  ⇒ 一律 `wer_verdict = "UNMEASURED"`，**不扫全库冒充本趟**。

### ② 载体隔离计数 — `carrier_isolation_count(rec, carrier_dir, pid)`

- **锚点**：`ANCHOR_C`（同上，命中 1）+ `ANCHOR_F` =
  `term_ct = LAUNCH_TOKEN.ct if (...) else launch_ct` + 空行 + `# ==== 第 3 项：...`（命中 1）
- **新增行数**：约 257 行（§9-H6 内 237 行 + finally 内 18 行）
- **落盘段名 `ISOLATION`，键**：`iso_pid`、`iso_self_probe_ok`、`iso_self_probe`、
  `iso_enum_ok`、`iso_carrier_dir`、`iso_system_root`、`iso_n_modules`、`iso_inside`、
  `iso_system`、`iso_outside`、`iso_outside_detail`、`iso_error`、`iso_verdict`
- **枚举**：`CreateToolhelp32Snapshot(TH32CS_SNAPMODULE|TH32CS_SNAPMODULE32)` +
  `Module32FirstW/NextW`，`ERROR_PARTIAL_COPY` 短重试 3 次。
- **★ 归属判定只用 `Path.relative_to`**（`_h6_path_zone`），**无 `str.startswith`**；
  已用 `D:\carrierX` vs `D:\carrier`、`%SystemRoot%X` vs `%SystemRoot%` 两组反例实测。
- **★ 枚举失败 = `V_FAIL`**：先做**正控**（枚举本进程自己，查不到自己的 exe 名即判枚举器坏）；
  正控失败 / 目标枚举失败 / 载体目录不可解析 / pid 缺失 ⇒ `iso_verdict="V_FAIL"`，
  且 `iso_outside` 保持 `None`（**不是 0**）。
- **越界明细上限 20 条**（`H6_ISO_DETAIL_MAX`），总数另记 `iso_outside`。
- **时序**：插在 `finally` 内、`terminate_owned_process` **之前**（要活进程）。

### ③ near-limit WARN

- **锚点**：`ANCHOR_A`（两行 130/131 常量，命中 1）、`ANCHOR_B`
  = `bad = carrier_pathlen_violations(dirs)` + `if not bad:` + `return`（命中 1）
- **新增行数**：约 24 行（常量 3 + 门禁内 17 + 注释）
- **落盘**：段名 `CARRIER`，键 `pathlen_near_limit`（与既有 `pathlen_gate` 并列）
- **控制台**：`[WARN] carrier dir len=NNN near limit 130` 一行
- **退出码不变**：`carrier_pathlen_gate` 的 `raise RuntimeError` 分支**一行未动**；
  边界实测 126/127/129/130 通过（127..130 各出 1 条 WARN），131/140 硬停。

### ④ `--close-mode {terminate,close}`

- **锚点**：`ANCHOR_D`（`--sg-toggle-y` 段 + `# <<< QC151SG-END argparse` + `return ap.parse_args(argv)`，命中 1）、
  `ANCHOR_E`（`rec.add("META", "started", ...)`，命中 1）、
  `ANCHOR_G`（`term_ok = None ...` + `if term_proc is not None and term_pid is not None:` +
  `try:` + `term_ok = terminate_owned_process(...)`，命中 1）
- **新增行数**：约 230 行（`h6_close_attempt` 105 + argparse 14 + state 6 + finally 31 +
  注释/共用）
- **落盘段名 `CLOSE`，键**：`close_mode`、`close_posted`、`close_exited_s`、
  `close_fallback_terminate`、`close_hwnd`、`close_hwnd_owned_by_pid`、
  `close_wm_close_posted`、`close_already_exited`、`close_error`
- **默认 `terminate` 的控制流**：`_h6_close` 字典先建（纯赋值），
  `if _h6_close["mode"] == "close":` 为假 ⇒ **不调用任何 Win32、不发消息**，
  随后照旧走 `terminate_owned_process`。**不改变**其语义（生成器自检 11：
  该函数体在母本与副本中**逐字节相同**）。
- **`close` 行为**：`find_main_window(pid)` → 复核 `hwnd` 属主 pid → `PostMessageW(WM_CLOSE)` →
  用**自己的** `SYNCHRONIZE` 句柄 `WaitForSingleObject(≤20 s)`。**不碰 `Popen` 状态**，
  把「确认终止」留给 `terminate_owned_process`。
- **回落标注**：超时/无主窗/投递失败/`hwnd` 属主不符 ⇒ `close_fallback_terminate=true`
  （`null` = terminate 模式未尝试；`false` = 真的自行退出）。
- **实测**（合成窗口，非游戏）：
  - 子进程在 `WM_CLOSE` 里 `ExitProcess` ⇒ `posted=true, exited_s=0.016, fallback=false`；
  - 子进程吞掉 `WM_CLOSE` ⇒ `posted=true, exited_s=null, fallback=true`，
    之后回落 `Popen.terminate()` 得 rc=1。

## 4. 零删除行自检

```
mother lines: 7782   copy lines: 8452
removed lines: 0
mother line multiset subset: True
```

生成器自检 8 用 `collections.Counter` 逐行比对（**多重集**语义，不是集合），
任一母本行在副本中出现次数减少即 `ABORT`。本次 `gone = []`。

**逐条列出的「改行」：无。** 全部 8 处补丁都是「保留原锚点行 + 在其前后插入新行」，
锚点行本身逐字保留在副本中（例如 `ANCHOR_B` 三行原样出现在 `PATCH_B` 末尾）。

## 5. 四条标记 `grep -c` 实测

| 标记 | 计数 |
|:--|--:|
| `wer_scan_new_reports` | **14** |
| `carrier_isolation_count` | **22** |
| `near limit 130` | **1** |
| `close-mode` | **3** |

（`near limit 130` 为 1 是预期的：它是控制台告警字面量，只出现在一处 `print`。）

## 6. 生成器自检项（全部 PASS）

| # | 检查 | 结果 |
|:--|:--|:--|
| 1 | 母本 LF16 == `f1e5bc7b0ff30c9c` | PASS |
| 2 | 8 个锚点各自 `count == 1` | PASS（逐个打印 1） |
| 3 | 替换后锚点不复用（每步再断言 1 次） | PASS |
| 4 | `ast.parse` | PASS |
| 5 | 新符号存在且**定义唯一** | PASS |
| 6 | 四条标记计数 > 0 | PASS |
| 7 | **未新增退出码** | PASS（`exit codes added: none`） |
| 8 | 母本关键约束仍在（`carrier_pathlen_gate` / `terminate_owned_process` / `a8_sweep_carrier_processes` / `_a8_enum_probe` / 130 / 131 / `raise RuntimeError`） | PASS |
| 9 | 硬停判据 `if len(s) > CARRIER_PATH_MAX_CHARS:` 仍唯一且未改 | PASS |
| 10 | 零删除行 | PASS |
| 11 | 时序：隔离计数 < close 尝试 < `terminate_owned_process` < WER < 删除链 | PASS |
| 12 | `py_compile`（编到临时目录） | PASS，**仓库内零 `.pyc`** |
| 13 | `terminate_owned_process` 函数体与母本逐字节相同 | PASS |
| 14 | `--close-mode` 缺省 `"terminate"` 且 close 分支有显式守卫 | PASS |
| 15 | `-W error::SyntaxWarning` 下无告警 | PASS（三处 docstring 改为 raw string） |

`python _gen_harness6.py --check` 只跑 1–15 不写盘；不带 `--check` 才写副本与 diff。
**生成器可复跑**：重跑对同一母本产出**同一 sha16**（无时间戳、无随机量）。

## 7. 诚实边界（哪些做不到 / 哪些只是静态自检）

1. **全部四项均未真机验证**。按纪律未启动游戏、未启动 loader、未跑 trip、
   未改注册表、未对 WER 目录做任何写操作。副本只经 `ast.parse` + `py_compile`
   与**函数级隔离测试**（把 §9-H6 段单独 `exec` 进测试命名空间，不 import 母本）。
2. **WER 判据的固有盲点**（不是实现缺陷，是 WER 本身）：
   - `NO_NEW_REPORT` **不证明**本趟没崩——报告可能未生成、被系统策略抑制、
     或 `AppName` 不是 `gamemd.exe`（例如崩溃发生在 loader 内）。
     故代码把 `wer_verdict` 定为「独立旁证」，**不参与任何退出码**。
   - 依赖 `mtime >= since_ts`。`since_ts` 取 `main()` 起始的 `time.time()`
     （wall clock，与 mtime 同钟）；若系统时钟在趟内被调整，可能漏收或误收。
   - 我**没有**在本机真实 WER 目录上跑过（那是读操作，但任务书要求「不读 WER
     目录写操作」——为免歧义，连读也没做）。真实目录结构按
     `lead/goal2_wer_observation_20261022/wer_module_isolation_audit.py` 的口径
     用**合成目录**验证。
3. **`--close-mode close` 的观测语义仍有结构性盲点**（这是我认为需要附条件的一项）：
   - RC-4 是「退出期崩溃」。`WM_CLOSE` 只对**有窗口消息泵**的进程有效；
     `gamemd.exe` 在**菜单 busy-loop / 独占全屏**（`--fullscreen`）下的消息处理
     路径与正常窗模式不同，可能出现「投递成功但永不处理」⇒ 恒回落 terminate。
     此时 `close_fallback_terminate=true` 会如实记录，但**测不到 RC-4**。
   - `find_main_window()` 的判据是「属主 pid 匹配且宽 > 200」，与母本采帧同一口径；
     若游戏窗口尚未建立（提前失败路径），会走 `no_main_window` ⇒ 直接回落。
   - 因此 `close` 模式只应在**已确认主窗存在**的趟里使用，且必须读
     `close_posted` / `close_fallback_terminate` 才能判断这次测量是否有效。
     **只看 `close_exited_s` 有值就宣称「正常退出」是误读**——代码里已用 note 明确写了
     这一点，但判读者仍需遵守。
4. **② 的模块表口径**：Toolhelp 快照与母本 `s4_enum_modules`（psapi）是**两套并列**
   枚举路径。若两者结果不一致（例如 psapi 能看到而 Toolhelp 因权限看不到），
   本卡只记 `V_FAIL`，不尝试对齐。这是有意的 fail-closed。
5. **③ 附带一处防御性修改**：`carrier_pathlen_gate` 开头加了 `dirs = list(dirs)`。
   理由：本卡的 near-limit 块要先遍历 `dirs`，若调用方传的是**生成器**，
   遍历后 `carrier_pathlen_violations(dirs)` 会拿到空序列 ⇒ **静默绕过硬停**。
   物化为 list 不改变内容，硬停判据看到的输入与母本完全相同（已用生成器入参
   实测：140 字符仍 `RuntimeError`，127 字符仍出 WARN）。这是**唯一**一处
   触碰母本既有函数内部的改动，且是插入式（母本三行锚点逐字保留）。
5. **③ 的 127 阈值**是**判断性选择**，不是实证值：本项目实证的是「130 安全 / 131 故障」，
   127 只是提前一段可见的告警下界。它**不参与硬停**，误设的代价仅是多打一行 WARN。
6. **`iso_inside` 在真机上预计很小甚至为 0**：游戏主 exe 若经 `InstallPath`
   绝对路径启动，连 `gamemd.exe` 本身都会被归为「越界」。这是**正确**的观测结果
   （正是要暴露的隔离事实），但读报告时不应把它当成「载体没用上」的故障。
7. **未改动任何既有文件**：`lead/goal1_a8_fix_20261022/` 下零写入；
   未触碰 `ra2youli/`、`ra2render/`、`re_atlas/`、`tools/`、`docs/`。

## 8. 交付件

| 文件 | 字节 | 说明 |
|:--|--:|:--|
| `qc151_trip.harness6.py` | 461535 | 派生件，LF16 `a67cc05edd5034f8` |
| `_gen_harness6.py` | — | 生成器，可复跑，`--check` 只自检 |
| `h6.diff` | 37568 | 与 harness5 的 unified diff，`+670 / -0` |
| `HARNESS6_MERGE.md` | — | 本报告 |
