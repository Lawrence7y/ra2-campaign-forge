# 退场普查 · 独立复核（02_verify.md）

复核对象：`D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261105/EXIT_CENSUS_77a0d667/01_exit_census.md`（只读，未修改）。
数据根 D = `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`。
全程零真机、只读 D 与台账；唯一写入目录 = `.../goal3t_nightwatch_20261105/EXIT_CENSUS_77a0d667/`；`python -I -X utf8` + 绝对路径；未 git add / commit；未写任何采样/注入/Hook/MiniDump/SuspendThread/StackWalk 代码。

**判定：NEEDS_REVISION**（8 条异议，见 §7）。

## 0 · 我实际跑过的命令（原口径）

| # | 命令 | 结果 |
|:--|:--|:--|
| C1 | `find "$D" -maxdepth 1 -type d -name "archive_T*" \| sort` 及 `... \| wc -l` | 37 个目录，逐名列于 `_verify_probe_out.txt:4-40` |
| C2 | `for d in $(find "$D" -maxdepth 1 -type d -name "archive_T*" \| sort); do [ -f "$d/qc151_run_log.json" ] ...` | 21 EXISTS / 16 MISSING |
| C3 | `python -I -X utf8 "D:/.../EXIT_CENSUS_77a0d667/_verify_probe.py" > "D:/.../EXIT_CENSUS_77a0d667/_verify_probe_out.txt" 2>&1` | 首次因 `qc151_fields.json` 为 **list of {group,key,value}**、脚本按 dict 取 `.keys()` 抛 `AttributeError: 'list' object has no attribute 'keys'`（原文见首次输出末行）；修正解析后重跑 `EXITCODE=0`，885 行 |
| C4 | `python -I -X utf8 "D:/.../EXIT_CENSUS_77a0d667/_verify_probe2.py" > ".../_verify_probe2_out.txt" 2>&1` | `EXITCODE=0`，163 行 |
| C5 | `python -I -X utf8 "D:/.../EXIT_CENSUS_77a0d667/_verify_compare.py" > ".../_verify_compare_out.txt" 2>&1` | 解析报告 §2 表 37 行；逐格对盘；`MISMATCH COUNT = 0` |
| C6 | `find "$D" -maxdepth 2 -path "*/archive_T*/*" -name "except_post_*.txt" -type f -print0 \| sort -z \| xargs -0 sha256sum \| python -I -X utf8 -c ...` | `files= 24`，`n=24 6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| C7 | `find "$D" -path "*/archive_T*/except_post_*.txt" -type f -exec sha256sum {} \; \| cut -d' ' -f1 \| sort -u` | 唯一一行 `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| C8 | `find "$D" -path "*/archive_T*/error.txt" -type f -print \| sort` + 逐份 `grep -i "^type"` | 3 份：T10 `NameError`、T11 `SystemExit`、T5 `ArgumentError` |
| C9 | `python -I -X utf8 -c` 读台账 `GOAL_THREE_TARGETS_20261018.md`（5464 行）、`TRIP_ID_RECONCILIATION_20261018.md`、`book_T12_20261017/C_DEFECT.md`、`L1_BASELINE_TRIPS_20261021.md`、`RULING_D16.md` | 见 §6 |

我写的证据件（均在本轮唯一可写目录）：`_verify_probe.py` / `_verify_probe_out.txt` / `_verify_probe2.py` / `_verify_probe2_out.txt` / `_verify_compare.py` / `_verify_compare_out.txt` / 本文件 `02_verify.md`。

## 1 · 检查 1：自己 glob 一遍 archive_T*，数总数，与调查员行数比对

- C1 输出：`COUNT = 37`（`_verify_probe_out.txt:3`），37 个目录名逐条列于 `:4-40`。
- 用 C5 解析调查报告 §2 表（`01_exit_census.md:36-74`）：**37 行**，表头 10 列（`_verify_compare_out.txt:2`）。
- C5 输出：`ROW SET: report has 37 dirs; disk has 37 dirs`、`missing from report: []`、`extra in report: []`、`duplicate rows: []`（`_verify_compare_out.txt`）。
- 报告 §0 `01_exit_census.md:9` 写「37 个目录」、§1 `:28` 合计 37、§2 标题 `:32` 写「37 行」⇒ **一致，无异议**。

## 2 · 检查 2：重取全部 final_exit，画直方图，比对 exitHistogram

C3 逐份 `json.loads(read_bytes().decode("utf-8-sig"))` 读 `qc151_run_log.json`；不存在记「缺」，异常记「解析失败」（本轮 21 份存在者全部解析成功，16 份缺件，无解析失败）。C2 独立给出 21 EXISTS / 16 MISSING。

**我独立重取的直方图**（`_verify_probe_out.txt:263-269`）：

| final_exit | 计数 | 目录 |
|:--|--:|:--|
| 0 | 14 | T12,T13,T14,T15B,T16,T18,T20,T21,T31,T32,T33,T5,T8,T9 |
| 1 | 1 | T10 |
| 19 | 3 | T11,T22,T23 |
| 22 | 2 | T6,T7 |
| 63 | 1 | T19 |
| 缺 | 16 | T15_ABORTED,T17,T34,T35,T36,T37,T38,T39,T40,T41,T42,T43,T44,T45,T47,T49_u0800 |
| **合计** | **37** | |

与报告 §1 表（`01_exit_census.md:19-28`）逐值逐目录**完全一致**；§2 表 37 行 `final_exit` 单元格经 C5 逐格比对 `MISMATCH COUNT = 0`。21 份存在 run log 的 `cleanup_failures` 全为 `[]`（`_verify_probe_out.txt:45-260`），与报告 `:10,:28` 一致。⇒ **无异议**。

## 3 · 检查 3：逐个读 error.txt 的 type 行；抽 3 趟读完整 error.txt 看 repr 是否被截错

C8：37 个 archive 内 `error.txt` **恰好 3 份**（`archive_T5` 1174 B、`archive_T10` 569 B、`archive_T11` 637 B），其余 34 个目录**文件不存在**（缺）。逐份 type 行（`_verify_probe_out.txt:47,56,228`；C8 输出）：

| 目录 | type | where | repr（原文） | 报告 §2 对应行 |
|:--|:--|:--|:--|:--|
| `archive_T5` | `ArgumentError` | `qc151_trip.py:791` | `ArgumentError('argument 2: OverflowError: int too long to convert')` | `01_exit_census.md:38` ✓ |
| `archive_T10` | `NameError` | `qc151_trip.py:3356` | `NameError("name 'user32' is not defined")` | `:43` ✓ |
| `archive_T11` | `SystemExit` | `qc151_trip.py:454` | `SystemExit(19)` | `:44` ✓ |

**error.txt 类型分布（独立）**（`_verify_probe_out.txt:271-275`）：`<无/缺/空> 34` / `type = ArgumentError 1` / `type = NameError 1` / `type = SystemExit 1`。报告 §2 表 34 行写「无 @ —」、3 行写上述类型 ⇒ **一致**。

抽 3 趟读**完整** error.txt（正好是全部 3 份非空者，`_verify_probe_out.txt:805-883`）：
- T10 全文 569 B：`repr = NameError("name 'user32' is not defined")`，Traceback 落点 `:3356 user32.keybd_event.argtypes`，末行 `NameError: name 'user32' is not defined`。
- T11 全文 637 B：`repr = SystemExit(19)`，`budget.end_stage("window")` → `:454 sys.exit(EXIT_STAGE_TIMEOUT)` → `SystemExit: 19`。
- T5 全文 1174 B（`_verify_probe2_out.txt:98-112` 逐行）：`repr = ArgumentError('argument 2: OverflowError: int too long to convert')`，链 `main:3146 → s4_injection_gate:823 → s4_enum_modules:791 → ctypes.ArgumentError`。

三份 repr 均短于 300 字符，报告照抄原文、**无截断错误**；`where` 行号与全文 Traceback 落点一致。⇒ **本项无异议**（报告 `:38` 写「error.txt:2-4」对应 type/where/repr 三行，与 `_verify_probe2_out.txt:99-101` 吻合）。

## 4 · 检查 4：问题 C — 37 个目录里全部 except_post 的 sha256，判断有无不同签名

C3（`hashlib.sha256(read_bytes())`）+ C6/C7（独立 CLI `sha256sum` 双路）+ C4 CHECK B：

- 37 个 archive 内 `except_post_*.txt` = **24 份，分布在 19 个目录**（`_verify_probe2_out.txt:2-42`）。
- **24/24 sha256 = `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`**，`distinct (sha256, ESS, 007CFC9F, siglines) combos = 1`（`_verify_probe_out.txt:295-299`）；每份都含 `Error code: EXCEPTION_SINGLE_STEP` 与 `Exception occurred at 007CFC9F`（逐份打印于 `:51-260`）。
- 全库 D 递归 107 份，sha256 唯一值同上；深度分布 `{0:44, 1:63}`（`_verify_probe2_out.txt:44-48`），与报告 `:118` 一致。
- 报告 §5 的 24 行「目录/文件名/sha256」逐行集合与盘上 24 文件**完全一致**（`report-only = []`、`disk-only = []`、`EXACT SET MATCH = True`）。

⇒ **「零例外、无第二签名」的结论属实，无异议**。但报告围绕这一结论写的覆盖计数**错误**，见 §7 异议 1。

## 5 · 检查 5：问题 D — 逐个检查 final_exit=0 的目录有无非空 error.txt

C3 SECTION 5（`_verify_probe_out.txt:277-293`）：14 个 `final_exit=0` 目录逐个查 `error.txt`：

```
archive_T12/T13/T14/T15B/T16/T18/T20/T21/T31/T8/T9  → 缺（文件不存在）
archive_T5                                          → 非空(1174 bytes)
archive_T32/T33                                     → 缺
FLAGGED (final_exit=0 AND non-empty error.txt) = ['archive_T5']
```

与报告 §6（`:151-160`）「属实，且只有 `archive_T5` 一趟」**一致**。其时间分离论证亦核实（`_verify_probe2_out.txt:90-119`）：`error.txt` mtime `2026-10-17T08:14:58`，`qc151_run_log.json` / `qc151_fields.json` mtime `11:13:34`，`META.started=2026-10-17T11:13:07+08:00`，`META.finalized=11:13:34+08:00`，`MANIFEST.final_verdict=PASS`、`EXCEPT.new_exception_count=0`、`MANIFEST.final_rewritten_exit_code=0`。按「每趟独立判定」不把 08:14 的残件与 11:13 的收尾混为一谈，报告处理正确。⇒ **无异议**。

## 6 · 检查 6：问题 B — 挑 final_exit=19 的三趟，逐趟读 error.txt 与产物，判断是否同因

C3 SECTION 7（`_verify_probe_out.txt:301-799`）、C4 CHECK E/F（`_verify_probe2_out.txt:121-162`）逐趟读：

| 趟 | run_log | error.txt | console | 阶段超时字段 | 关键产物 |
|:--|:--|:--|:--|:--|:--|
| `archive_T11` | `final_exit=19, cleanup_failures=[]` | **存在**，SystemExit(19) @ `:454`、`budget.end_stage("window")` | T11_console.log 580 B 同 Traceback | `stage_timeout:window=true`、`stage_seconds:window=30.297`、`WIN.window_stable_rect=[0,0,0,0]`、`esc_skip_sent=6` | 零帧 PNG，`MANIFEST.final_verdict=FAIL`，`EXCEPT.new_exception_count=0` |
| `archive_T22` | 同上 | **缺** | T22_console.log 577 B，`budget.end_stage(_step)` → `:464` → `SystemExit: 19` | `stage_timeout:nav_menu=true`、`45.625` | `verify_ok_nav_menu=false`，`signature_got_nav_menu=[61,220,262,304,556]`，`navsig_nav_menu_post_00_x.png` |
| `archive_T23` | 同上 | **缺** | T23_console.log 577 B，`:464` → `SystemExit: 19` | `stage_timeout:nav_menu=true`、`44.672` | `verify_ok_nav_menu=true`，`wait_screen_nav_menu_post.ok=true`，`navsig_nav_menu_post_00_g.png` |

报告 §2/§3 抄录的上述**字段值全部属实**（我逐键重取，`_verify_probe_out.txt:391-400, 562-572, 734-744`），三趟 `trip_id` 各不相同（T11/T22/T23），确属三次独立发射。失败阶段确实不同：T11 在 window，T22/T23 在 nav_menu。

**但归因结论我不认同，见 §7 异议 7**：三趟的即时退出机制是同一个 harness 代码路径；且 T22→T23 的「验证失败→验证通过」并非游戏画面变化，而是 harness 判据 `want` 数组被改动（同一 `red_centers=[61,220,262,304,556]`，T22 `want=[72,220,262,304,556]` / `ok=false`，T23 `want=[220,262,304,556]` / `ok=true`；console 里 `main` 行号 3967→3972、`_main_wrapper` 4185→4190，脚本已改）。`book_T12_20261017/C_DEFECT.md:135-137` 明写触发条件是 `dt > 30` 而非「是否收敛」，并标注同一耦合模式有第二实例；`C_DEFECT.md:44-45` 给 `deadline = time.monotonic() + STAGE_TIMEOUT_S`。T23 无 error.txt、`EXCEPT.new_exception_count=0`、`TERM.terminate_sent=true`，**没有任何游戏侧失败的独立证据**。

## 7 · 异议清单（disagreements，8 条）

1. **【C 问覆盖计数错，且与自身表格矛盾】** `01_exit_census.md:120` 「13 个 archive 目录根本没有 except_post 文件」、`:215`「21 个目录有、13 个目录 0 份」——实际为 **19 个目录有、18 个目录 0 份**（`_verify_probe2_out.txt:40-42`：0 份名单 18 个 = T15_ABORTED,T17,T32,T33,T34,T35,T36,T37,T38,T39,T40,T41,T42,T43,T44,T45,T47,T49_u0800）。24 份文件、107/107 同哈希、83 份散在根层与非 archive 目录这些数都对。另 `:120` 「有 3 趟成功趟带残件」错误：实际 **12 个 `final_exit=0` 目录带残件**（T5 5 份、T15B 2 份、T8/T9/T12/T13/T14/T16/T18/T20/T21/T31 各 1 份），只有 T32/T33 两个成功趟 0 份（`_verify_compare_out.txt` 末段 ACTUAL）。报告 §2 表与 §5 的 24 行清单本身是对的，错的是正文统计。
2. **【无法判定计数错】** `:222` 「『无法判定』的 26 个 archive 目录」——按报告 §2 表自身 37 行统计为 **28 个**（分布：harness 脚本缺陷 3、环境问题 5、人为中止 1、无法判定 28）。我按 `01_exit_census.md:36-74` 第 9 列解析得到 `cause distribution= {... '无法判定': 28 ...}`。
3. **【台账零命中数错】** `:213` 「24 个 archive 目录名在台账中零命中」——我用 37 个完整目录名对 `GOAL_THREE_TARGETS_20261018.md` 全文做子串检索：**21 个零命中、16 个命中**（命中：T31,T32,T33,T34,T35,T36,T38,T39,T40,T41,T42,T43,T44,T45,T47,T49_u0800）。其括号内「T5–T23 的 19 个 + T37 + T15_ABORTED/T17 + 早期趟」亦凑不出 24。
4. **【T32 console 写成 0 字节，实际是缺件】** `:59`（T32 行判定证据）、`:222`（概括）称 `console 0 字节`——`find "$D/archive_T32" -iname "*console*"` 输出为空，该目录**没有任何 console 文件**；同样 `archive_T5` 也无（`_verify_probe2_out.txt:67,83` 记 `console=[无]`，C8 复核 T32/T5 计数 0）。按铁律 6 文件不存在应写「缺」。其余 0 字节 console 的目录（T8/T9/T12…/T33 等）核实无误。
5. **【§7 目录数/文件数自相矛盾】** `:164` 「全库合计 43 个目录 / 104 份 measure JSON」——我 `rglob` 实测 104 份分布为：D 根层 3 份 + 14 个 archive 目录 42 份 + 29 个非 archive 子目录 59 份 = 104；43 个目录（29+14）只含 **101** 份，104 需把 D 根层当第 44 个目录。两者不能同时成立（应写「44 目录 / 104 份」或「43 目录 / 101 份」）。29 个非 archive 目录本身的「final_exit 全 0、cleanup_failures=[]、无 error.txt、各 1 份基线哈希」我逐目录核过，无异常。
6. **【§3 对 14 个缺 run log 目录的产物描述不成立】** `:110` 「其余 14 趟 run log 缺但 fields 与 measure 产物在场」——`archive_T35`、`archive_T37` 的 `measure_w*.json` **全缺**（`_verify_probe2_out.txt:70,72` 记 `measure=无`；报告 §2 `:62,:64` 自己也写 `0/0/0`）。应为 12 趟有 measure、2 趟无。
7. **【问题 B 的「同码不同因」归因证据不足，且 T22/T23 差异被误读为游戏侧】** `:56-57`、`:105-107` 把 T22 判「游戏菜单画面不符 ⇒ 环境问题」、T23 判「导航已验证通过仍耗尽预算 ⇒ 环境问题」，并断言 19 的三次「不是同一个原因」。我独立重取：三趟同为 `end_stage` 的 `dt > 30` ⇒ `sys.exit(EXIT_STAGE_TIMEOUT)` 设计性硬停（T11 `qc151_trip.py:454`、T22/T23 `:464`，见三份 console 与 `C_DEFECT.md:24-33,135-137`）；T22/T23 观测到的 `red_centers` 与 `signature_got_nav_menu` **完全相同** `[61,220,262,304,556]`，变的是 harness 的 `NAV.wait_screen_nav_menu_post.want`（T22 `[72,220,262,304,556]` → T23 `[220,262,304,556]`，`_verify_probe2_out.txt:127,139`），`ok` 才由 false 变 true；console 行号 `main 3967→3972`、`_main_wrapper 4185→4190` 表明两趟之间脚本已改动。故「T22 游戏菜单画面不符 vs T23 导航已通过」的差异来自**判据/脚本变更**，不是两次不同的游戏环境故障；T23 无 error.txt、`EXCEPT.new_exception_count=0`、`TERM.terminate_sent=true`，无游戏侧失败独立证据，「环境问题」归因与「三个不同根因」结论均未被证据支持。可保留的是：失败阶段（window vs nav_menu）与症状确实不同，三趟是三次独立事件。
8. **【旁证引用行号/原文小误】** `:211` 称 `TRIP_ID_RECONCILIATION_20261018.md:3` 与台账 `L98` 「均记『现存 37 个 archive』」——该文件 `:3` 是对账方法行，结论「**现存 37 个 archive**」在 `:4`；台账 `L98` 原文为「卡面 §T59：37 archive 零错名」，非「现存 37 个 archive」（`GOAL_THREE_TARGETS_20261018.md:98` 全文我读过）。另 `:108` 引 `L1_BASELINE_TRIPS_20261021.md:23,39`：`:39` 确为 T6 六件载体缺 `ddraw.dll` 先例，`:23` 是另一处上下文，属轻微引用偏差；T6/T7 的 `wait_returncode=3221225781`、`WIN.main_window_found=false`、`pre_delete_file_count=6` 我逐键核过，属实。

## 8 · 复核通过的部分（供修订时保留）

- 37 目录集合、§2 表 37 行逐格（`final_exit` / `cleanup_failures` / errorType / repr / except 份数与哈希前缀 / 台账登记列未复核内容）、§1 exitHistogram：**完全一致**（`_verify_compare_out.txt` `MISMATCH COUNT = 0`）。
- 21 份 run log 的 `cleanup_failures=[]`；16 个「缺」不拿 `qc151_fields.json` 的 `final_exit_code=0` 回填（`:30`）——我核了 14 个有 fields 的目录，键确为 `[finalize_exit_code, final_rewritten_exit_code, final_exit_code] = [0,0,0]`，报告处理符合铁律。
- 3 份 error.txt 的 type/where/repr 全文、**无截断**；error.txt 类型分布 34 无 / 1 ArgumentError / 1 NameError / 1 SystemExit。
- 24 份 archive except_post + 全库 107 份 sha256 唯一为 `6694b75e…251`，均含 `EXCEPTION_SINGLE_STEP` / `007CFC9F`；§5 逐份清单与盘面精确相等；**零不同签名**。
- D 问：14 个 `final_exit=0` 中仅 `archive_T5` 有非空 error.txt（1174 B），时间分离与 `EXCEPT.new_exception_count=0` 等字段属实。
- T6/T7（`0xC0000135`）、T19（`s4_exit_code=63`、`cbNeeded=80 > allocated=72`）、T15_ABORTED（`ABORTED_NOTE.md:3-5` NOT_COMPLETED）、T17（仅 0 字节 T17_console.log）、§2.1 的 14 行 fields 旁证、根层 `T54_console.exitcode=19` 与根层 `error.txt=SystemExit(19) @ :490` / 根层 `qc151_run_log.json final_exit=0` 的混合态（`:217`）：抽查均属实。
- 报告 `:225` 称 sha256 双路一致：本轮 C3（`hashlib`）与 C6/C7（`sha256sum`）结果相同，属实。

## 9 · 诚实边界

- 未启动任何游戏/宿主进程、未读活进程内存、未 taskkill；未写采样/注入/Hook/MiniDump/SuspendThread/StackWalk 代码；未 git add / commit；未修改 `01_exit_census.md`。
- 未复核的项：报告 §2「台账登记」列的 §号/行号是否逐条准确（只抽查了 `:211` 涉及的 L80/L98/L1531/L4424/L4747/L4770 与 `RULING_D16.md:35,139`）；§7 表格 29 行的 w0/w1/w2 数值；§3 对 22/63 码的历史定谳是否成立。按「没跑的不算通过」，这些**未全量复核**。
- 本轮对「根因」的判断只依据盘上离线产物与 `C_DEFECT.md` 静态说明，不推断游戏内部机制；三趟 19 是否共享更深的同一上游机制，盘上证据不足，我不下结论。
- 首次 C3 因 `qc151_fields.json` 为 list 结构抛 `AttributeError`（原文见该次输出），修正后重跑成功；本报告所有引用均取自重跑成功后的 `_verify_probe_out.txt`（885 行）。
