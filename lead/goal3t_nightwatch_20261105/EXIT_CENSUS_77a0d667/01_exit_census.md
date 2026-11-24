# 退场普查 · 37 个 archive_T* 全量逐目录表（EXIT_CENSUS_77a0d667）

数据根 D = `D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip`。
台账 L = `D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md`（5464 行）。
全程只读、零真机、零采样/注入/Hook 代码；python 一律 `python -I -X utf8`。

## 0 · 执行过的检查（原命令口径）

- `find "$D" -maxdepth 1 -type d -name "archive_T*" | sort` → 37 个目录，逐名列于 §2，无遗漏。
- 对每个 archive 读 `qc151_run_log.json`（`python -I -X utf8` + `json.loads(...,encoding="utf-8-sig")`）：不存在写「缺」；解析失败写「解析失败」+异常原文（本轮无解析失败）。全部 21 份存在的 run log 的 `cleanup_failures` 均为 `[]`。
- 对每个 archive 读 `error.txt` 全文（仅 3 个存在：T5/T10/T11）；提取 type / where / repr。
- `find "$D" -name "measure_w*.json"` 全量递归 → 104 份，分布 = D 根层 3 份 + 14 个 archive 子目录 42 份 + 29 个非 archive 子目录 59 份；按目录统计 w0/w1/w2。
- `find "$D" -name "except_post_*.txt"` → 107 份；`sha256sum` 逐份计算 → 107/107 同为 `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`。archive 内 24 份（19 个目录有、18 个目录 0 份），逐份哈希同值。
- 台账 `grep -n <完整目录名>` 逐目录（37 次）：21 个零命中、16 个命中，命中行号与 § 号列于表。
- 复核轮追加全量复算（口径见 §10）：37 个 archive 的 except_post 目录级计数、final_exit=0 且带残件的趟数、§2 表第 9 列 cause 分布、console 文件存在性、`rglob('measure_w*.json')` 分层计数。
- 读 `book_T12_20261017/C_DEFECT.md`、`L1_BASELINE_TRIPS_20261021.md`、`TRIP_ID_RECONCILIATION_20261018.md`、台账 §501/§544、D-16 裁决书作旁证。

## 1 · A 问：final_exit 取值分布（37 个 archive）

| final_exit | 计数 | 目录 |
|:--|--:|:--|
| 0 | 14 | `archive_T5`, `archive_T8`, `archive_T9`, `archive_T12`, `archive_T13`, `archive_T14`, `archive_T15B`, `archive_T16`, `archive_T18`, `archive_T20`, `archive_T21`, `archive_T31`, `archive_T32`, `archive_T33` |
| 1 | 1 | `archive_T10` |
| 19 | 3 | `archive_T11`, `archive_T22`, `archive_T23` |
| 22 | 2 | `archive_T6`, `archive_T7` |
| 63 | 1 | `archive_T19` |
| 缺 | 16 | `archive_T15_ABORTED`, `archive_T17`, `archive_T34`, `archive_T35`, `archive_T36`, `archive_T37`, `archive_T38`, `archive_T39`, `archive_T40`, `archive_T41`, `archive_T42`, `archive_T43`, `archive_T44`, `archive_T45`, `archive_T47`, `archive_T49_u0800` |

合计 14+1+3+2+1+16 = 37。`cleanup_failures` 在 21 份存在 run log 的目录里全为 `[]`；16 个「缺」目录无该键，写「缺」。

★ 注意「缺」不等于「0」：16 个目录无 `qc151_run_log.json`。其中 14 个的 `qc151_fields.json` 仍存 `META.final_exit_code=0` / `MANIFEST.final_rewritten_exit_code=0` / `META.finalize_exit_code=0`，但那是**另一份文件**的旁证，按铁律不补造 run log，本表 `final_exit` 一律记「缺」。

## 2 · 全量逐目录表（37 行，一个不漏）

「except 份数/哈希」列：同目录多份逐份列名与哈希（全部同值，简写为 `n×<hash前 16>` 并在 §5 给逐份清单）。「台账」列：`L<行号>/<§号>`；无命中写「无登记」。

| 目录 | final_exit | cleanup_failures | error.txt 异常类型与定位 | repr（≤300 字符） | measure w0/w1/w2 | except 份数与 sha256 | 台账登记 | 性质判定 | 判定证据 |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| `archive_T5` | 0 | [] | ArgumentError @ D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py:791 | ArgumentError('argument 2: OverflowError: int too long to convert') | 0/0/0 | 5×`6694b75e46a6e773…` | 无登记 | harness 脚本缺陷 | archive_T5/error.txt:2-4 (ArgumentError @ qc151_trip.py:791, s4_enum_modules/GetModuleFileNameExW); archive_T5/qc151_run_log.json final_exit=0; error.txt mtime 08:14:58 早于本趟 11:13:07，属同目录留存的早前失败残件 |
| `archive_T6` | 22 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 环境问题 | archive_T6/qc151_fields.json: TERM.wait_returncode=3221225781(0xC0000135), WIN.main_window_found=false, MANIFEST.pre_delete_file_count=6；L1_BASELINE_TRIPS_20261021.md:39 「T6 六件载体缺 ddraw.dll 启动即亡」 |
| `archive_T7` | 22 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 环境问题 | archive_T7/qc151_fields.json: TERM.wait_returncode=3221225781, WIN.main_window_found=false, MANIFEST.pre_delete_file_count=6；L1_BASELINE_TRIPS_20261021.md:39 同类先例 |
| `archive_T8` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T8/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / TERM.wait_returncode=0 / MANIFEST.final_verdict=PASS / META.final_exit_code=0；无 error.txt、console 0 字节。缺：退场瞬间的独立游戏崩溃/异常证据 |
| `archive_T9` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T9/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T10` | 1 | [] | NameError @ D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py:3356 | NameError("name 'user32' is not defined") | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | harness 脚本缺陷 | archive_T10/error.txt:2-4 NameError("name 'user32' is not defined") @ qc151_trip.py:3356；T10_console.log 同名 Traceback；book_T12_20261017/C_DEFECT.md:111 QC189 定名 |
| `archive_T11` | 19 | [] | SystemExit @ D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py:454 | SystemExit(19) | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | harness 脚本缺陷 | archive_T11/error.txt:2-4 SystemExit(19) @ qc151_trip.py:454 end_stage；qc151_fields.json: BUDGET.stage_timeout:window=true, stage_seconds:window=30.297；book_T12_20261017/C_DEFECT.md:128-133,173-179 定谳 QC188 结构缺陷 |
| `archive_T12` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T12/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=0 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T13` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T13/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=0 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T14` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T14/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=0 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T15B` | 0 | [] | 无 @ — | 无 | 0/0/0 | 2×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T15B/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=0 / final_verdict=PASS；2 份 except_post 均基线哈希；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T15_ABORTED` | 缺 | 缺 | 无 @ — | 无 | 0/0/0 | 0 份 | 无登记 | 人为中止 | archive_T15_ABORTED/ABORTED_NOTE.md:3 「Bash 前台命令被宿主取消信号打断(child asked to stop)，趟脚本未完成收尾」；同文件:4-5 判定 NOT_COMPLETED、数据不得用于结论；qc151_run_log.json 缺 |
| `archive_T16` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T16/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T17` | 缺 | 缺 | 无 @ — | 无 | 0/0/0 | 0 份 | 无登记 | 无法判定 | archive_T17/ 仅 T17_console.log 且 0 字节；qc151_run_log.json 缺、qc151_fields.json 缺；TRIP_ID_RECONCILIATION_20261018.md §2 T17 列「archive 存在但 fields 缺失」。缺：全部退出状态证据 |
| `archive_T18` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T18/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T19` | 63 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T19/qc151_fields.json 键 S4.module_enum_error="EnumProcessModulesEx: cbNeeded=80 > allocated=72 ⇒ 模块表被截断 ⇒ 不能判定"、S4.s4_exit_code=63、S4.s4_gate=enum_failed、S4.trip_verdict=VOID；archive_T19/s4_module_table.txt:2 同文。台账 L1531 的「err=299 / 环境瞬态」是 l3_1101v4a（v4-a）的独立定谳，T19 无 err=299、无 T19 专属文档 ⇒ 不可跨目录搬用；本趟无 error.txt、console 0 字节。缺：S4 硬停的具体触发原因 |
| `archive_T20` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T20/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T21` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | 无法判定 | archive_T21/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T22` | 19 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | harness 脚本缺陷 | archive_T22/T22_console.log: SystemExit: 19 @ qc151_trip.py:464 end_stage（book_T12_20261017/C_DEFECT.md:29-33 同一 dt>30 硬停机制）；qc151_fields.json: BUDGET.stage_seconds:nav_menu=45.625 / stage_timeout:nav_menu=true / NAV.signature_got_nav_menu=[61,220,262,304,556] / NAV.wait_screen_nav_menu_post.want=[72,220,262,304,556]、ok=false、EXCEPT.new_exception_count=0、TERM.terminate_sent=true ⇒ 阶段预算烧满由 harness 硬停，缺游戏侧失败独立证据；无 error.txt |
| `archive_T23` | 19 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | 无登记 | harness 脚本缺陷 | archive_T23/T23_console.log: SystemExit: 19 @ qc151_trip.py:464 end_stage（main 3967→3972、_main_wrapper 4185→4190 表明两趟间脚本已改）；qc151_fields.json: BUDGET.stage_seconds:nav_menu=44.672 / stage_timeout:nav_menu=true / NAV.signature_got_nav_menu 同为 [61,220,262,304,556]，但 NAV.wait_screen_nav_menu_post.want 改为 [220,262,304,556] ⇒ ok=true；EXCEPT.new_exception_count=0、TERM.terminate_sent=true ⇒ 仍是 harness 阶段预算硬停，ok 差异来自判据改动而非游戏侧差异；无 error.txt |
| `archive_T31` | 0 | [] | 无 @ — | 无 | 0/0/0 | 1×`6694b75e46a6e773…` | L80/日志§43 | 无法判定 | archive_T31/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / final_verdict=PASS；无 error.txt、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T32` | 0 | [] | 无 @ — | 无 | 1/1/1 | 0 份 | L51/状态日志·无§号、L83/日志§46、L1059/§480、L1647/§506 等 13 处 | 无法判定 | archive_T32/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / final_verdict=PASS、measure_w0/1/2 齐全；无 error.txt、无 except_post、`find "$D/archive_T32" -iname "*console*"` 输出为空 ⇒ console 文件缺。缺：退场瞬间独立证据 |
| `archive_T33` | 0 | [] | 无 @ — | 无 | 1/1/1 | 0 份 | L2247/§519、L2392/§521、L2486/§522、L2857/§527 等 11 处 | 无法判定 | archive_T33/qc151_run_log.json final_exit=0；qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / final_verdict=PASS、w0/1/2 齐全；无 error.txt、无 except_post、console 0 字节。缺：退场瞬间独立证据 |
| `archive_T34` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L90/日志§57、L2151/§517、L2478/§522、L2849/§527 等 14 处 | 无法判定 | archive_T34/qc151_run_log.json 缺；archive_T34/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T35` | 缺 | 缺 | 无 @ — | 无 | 0/0/0 | 0 份 | L91/日志§60、L4306/§538、L5119/§550 | 无法判定 | archive_T35/qc151_run_log.json 缺；archive_T35/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=0/0/0；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T36` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L2392/§521、L2483/§522、L2732/§525、L2854/§527 等 7 处 | 无法判定 | archive_T36/qc151_run_log.json 缺；archive_T36/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T37` | 缺 | 缺 | 无 @ — | 无 | 0/0/0 | 0 份 | 无登记 | 无法判定 | archive_T37/qc151_run_log.json 缺；archive_T37/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=0/0/0；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T38` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L2062/§516、L2151/§517、L2210/§518、L2479/§522 等 8 处 | 无法判定 | archive_T38/qc151_run_log.json 缺；archive_T38/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T39` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L2480/§522、L2851/§527、L3045/§529、L4235/§538 等 5 处 | 无法判定 | archive_T39/qc151_run_log.json 缺；archive_T39/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T40` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L4236/§538、L4759/§547 | 无法判定 | archive_T40/qc151_run_log.json 缺；archive_T40/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T41` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L4237/§538、L4625/§546、L4640/§546、L4717/§546 等 10 处 | 无法判定 | archive_T41/qc151_run_log.json 缺；archive_T41/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T42` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L4511/§545、L4537/§545、L4538/§545、L4604/§545 等 10 处 | 无法判定 | archive_T42/qc151_run_log.json 缺；archive_T42/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T43` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L2392/§521、L2484/§522、L2855/§527、L3049/§529 等 6 处 | 无法判定 | archive_T43/qc151_run_log.json 缺；archive_T43/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T44` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L4239/§538、L4763/§547 | 无法判定 | archive_T44/qc151_run_log.json 缺；archive_T44/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T45` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L4240/§538、L4539/§545、L4764/§547、L4883/§548 等 6 处 | 无法判定 | archive_T45/qc151_run_log.json 缺；archive_T45/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T47` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L1000/§6、L1019/§478、L1036/§479、L1059/§480 等 9 处 | 无法判定 | archive_T47/qc151_run_log.json 缺；archive_T47/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |
| `archive_T49_u0800` | 缺 | 缺 | 无 @ — | 无 | 1/1/1 | 0 份 | L2393/§521、L2485/§522、L2856/§527、L3050/§529 等 7 处 | 无法判定 | archive_T49_u0800/qc151_run_log.json 缺；archive_T49_u0800/qc151_fields.json: TERM.terminate_sent=true / wait_returncode=1 / MANIFEST.final_verdict=PASS / META.final_exit_code=0 / META.final_rewritten_exit_code=0；measure_w0/1/2=1/1/1；无 error.txt、无 except_post。缺：qc151_run_log.json 原件及退场瞬间独立证据 |

### 2.1 缺 run log 的 16 个目录之 `qc151_fields.json` 旁证（不回填 final_exit）

| 目录 | qc151_fields.json 里的退出相关键 |
|:--|:--|
| `archive_T15_ABORTED` | 缺 |
| `archive_T17` | 缺 |
| `archive_T34` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T35` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T36` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T37` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T38` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T39` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T40` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T41` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T42` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T43` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T44` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T45` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T47` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |
| `archive_T49_u0800` | {"finalize_exit_code": 0, "final_rewritten_exit_code": 0, "final_exit_code": 0} |

## 3 · B 问：同一 final_exit 是否指向同一根因（逐值作答）

**总结论：否。同一个退出码不保证同一根因；但也不能把「同一码下的字段差异」当成已证的不同根因。** 修订后逐值结论：0 与 19 两组内部存在可核的证据/产物差异（不等于已证根因不同）；22 组两趟证据同型；1/63 单趟；「缺」组含人为中止与无法判定。特别更正：本表初版把 19 的三趟判成「三个不同根因」（T11=harness、T22/T23=环境问题），复核后**撤回**——三趟的直接退出机制同为 harness 的 `end_stage` 设计性硬停，T22/T23 的游戏侧归因无独立证据支撑。

- **0（14 趟）**：`T5, T8, T9, T12, T13, T14, T15B, T16, T18, T20, T21, T31, T32, T33`。T5 目录里带一份 harness `ctypes.ArgumentError`（且 mtime 早于本趟 3 小时，见 §6/D 问）；其余 13 趟无 error.txt、console 多为 0 字节、`TERM.terminate_sent=true` + `MANIFEST.final_verdict=PASS`，但「为什么结束」缺独立证据，逐趟记「无法判定」。T32/T33 有完整 w0/w1/w2 且无 except_post，其余 12 趟无 measure 产物但都带 except_post 基线残件（T5 五份、T15B 两份、其余各一份）——同为 0 却分属不同产物形态。⇒ 证据充分度与产物形态不同，不可合并；但 13 趟的根因均「无法判定」，不得据此宣称已证根因不同。
- **1（1 趟）**：`T10` = `NameError("name 'user32' is not defined")` @ `qc151_trip.py:3356`。单趟，无「同码异因」可比较；判 harness 脚本缺陷（`book_T12_20261017/C_DEFECT.md:111` QC189 定名）。
- **19（3 趟）——复核后改判**：`T11, T22, T23` 三次都是 `EXIT_STAGE_TIMEOUT=19`，**直接退出机制相同**：三份 console 均落在 `budget.end_stage` → `sys.exit(EXIT_STAGE_TIMEOUT)`（`qc151_trip.py:454` / `:464`），即 `dt > STAGE_TIMEOUT_S(30.0)` 的设计性硬停（`book_T12_20261017/C_DEFECT.md:29-33` 的 `end_stage` 源码、:135-137 的精确边界）。逐趟差异只在**失败阶段**与**脚本版本**：
  - `T11`：`BUDGET.stage_timeout:window=true`（`stage_seconds:window=30.297`），`WIN.window_stable_rect=[0,0,0,0]`、`esc_skip_sent=6` ⇒ 主窗始终达不到 800×600；`C_DEFECT.md:128-133,173-179` 把该趟定谳为 **QC188 结构缺陷**（等待 deadline 与阶段硬停上限耦合，非收敛必然 `exit(19)`+零帧）⇒ harness 脚本缺陷。
  - `T22`：`BUDGET.stage_timeout:nav_menu=true`（`stage_seconds:nav_menu=45.625`）、`NAV.verify_ok_nav_menu=false`；逐趟重取 `NAV.wait_screen_nav_menu_post.polls[0].red_centers=[61,220,262,304,556]`、`want=[72,220,262,304,556]` ⇒ hit=false，ok=false 来自判据 want 含 72 而画面签名首项是 61。
  - `T23`：`BUDGET.stage_timeout:nav_menu=true`（`44.672`）、`NAV.verify_ok_nav_menu=true`；**同一份画面签名 `polls[0].red_centers=[61,220,262,304,556]` 与 `NAV.signature_got_nav_menu` 完全相同**，但 `NAV.wait_screen_nav_menu_post.want` 变成 `[220,262,304,556]` ⇒ hit=true、ok=true。两趟 console 行号 `main 3967→3972`、`_main_wrapper 4185→4190` 表明 T22/T23 之间脚本已改；T23 另记 `EXCEPT.new_exception_count=0`、`TERM.terminate_sent=true`、无 error.txt ⇒ **无游戏侧失败的独立证据**。
  - ⇒ 更正：T22/T23 由「环境问题」改判 **harness 脚本缺陷**（阶段预算硬停，ok 差异是 harness 判据改动），不再声称「游戏菜单画面不符」或「三个不同根因」。可保留的差别只有：失败阶段 window vs nav_menu 不同、三趟是三次独立发射（不同 trip_id/时间戳/console 行号），且 T11 另有 QC188 结构缺陷的专属定谳；T22/T23 的 `want` 改动是否就是超时主因仍缺证据，不补造。
- **22（2 趟）**：`T6, T7` 同为 `EXIT_WINDOW_NOT_FOUND=22`，逐趟 `qc151_fields.json` 都记 `TERM.wait_returncode=3221225781 (0xC0000135 STATUS_DLL_NOT_FOUND)`、`WIN.main_window_found=false`、`MANIFEST.pre_delete_file_count=6`；`L1_BASELINE_TRIPS_20261021.md:23`（22=EXIT_WINDOW_NOT_FOUND 的定义）、`:34-36`（载体只含默认件 ⇒ 缺 ddraw.dll 与 *.mix ⇒ gamemd 加载期即死）、`:39`（T6 六件载体先例）把此类定谳为环境问题。两趟证据同型 ⇒ 判同一类环境问题；但仍是**两次独立发射**（不同 trip_id / 不同时间戳），不是「同一次事件」。
- **63（1 趟）**：`T19` = `S4.module_enum_error="EnumProcessModulesEx: cbNeeded=80 > allocated=72 ⇒ 模块表被截断"`、`s4_exit_code=63`、`s4_gate=enum_failed`、`trip_verdict=VOID`（`archive_T19/s4_module_table.txt:2` 同文）。台账 `L1531` 的「err=299 / 环境瞬态」是 `l3_1101v4a`（v4-a）的独立定谳，本趟字段里没有 err=299、台账全文也无 `archive_T19`/`T19` 登记 ⇒ **不跨目录搬用**，改判「无法判定」（缺：S4 硬停的具体触发原因）。单趟，无同码可比。
- **缺（16 趟）**：`T15_ABORTED` 有人为中止说明（`ABORTED_NOTE.md`）⇒ 人为中止；`T17` 仅一个 0 字节 console、全无 fields/runlog ⇒ 无法判定；其余 14 趟 run log 缺但 fields 在场、`TERM.terminate_sent=true` ⇒ 逐趟「无法判定」，其中 **12 趟有 measure 产物**（T34/T36/T38/T39/T40/T41/T42/T43/T44/T45/T47/T49_u0800）、**2 趟 measure 全缺**（T35/T37，报告 §2 表内也记 0/0/0）。这 16 个「缺」不构成同一种结束方式。

★ **游戏崩溃：37 个 archive 中 0 趟判为游戏崩溃。** `except_post_*.txt` 是 `EXCEPTION_SINGLE_STEP at 007CFC9F` 的历史基线残件（全库同哈希、T5 的 `except_set_diff.json` 记 `new_exception_count=0`），不构成任何一趟的崩溃证据；`TERM.terminate_sent=true` 出现在全部 35 份有 fields 的目录里，说明脚本主动终止。缺独立崩溃证据处一律写「无法判定」，不硬给归因。

## 4 · C 问：107/107 基线残件结论核对（37 个 archive 有无例外）

台账 `L4424`（§544 错误清算第 10 条）：「§544 暗示 v4f/v4g 撞 `007CFC9F` 崩溃 → 全库 107/107 同一基线残件，**成功趟 v4e 同样有**」。

本轮亲核：`find "$D" -name "except_post_*.txt"` = **107 份**（根层 44 + 子目录 63，层次分布 `44 0 / 63 1`）；`sha256sum` 逐份 → **107 份全部为 `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251`**，无第二个哈希。37 个 archive 内共 **24 份**（分布见 §5），逐份文件的 `Error code: EXCEPTION_SINGLE_STEP` 与 `Exception occurred at 007CFC9F` 均相同，且 sha256 全部等于上述值。

**结论：这 37 个 archive 目录里没有任何一趟的 except_post 是例外，零例外。** 复核轮全量复算：37 个 archive 中 **19 个目录有 except_post 文件（共 24 份）、18 个目录 0 份**（0 份名单：T15_ABORTED, T17, T32, T33, T34, T35, T36, T37, T38, T39, T40, T41, T42, T43, T44, T45, T47, T49_u0800）——0 份是「缺件」，不是「不同签名」，不可当例外、也不可填值。台账结论在本范围内成立；「成功趟同样有」的准确口径：`final_exit=0` 的 14 趟里 **12 趟带基线残件**（T5 5 份、T15B 2 份、T8/T9/T12/T13/T14/T16/T18/T20/T21/T31 各 1 份），**仅 T32/T33 两个成功趟 0 份** ⇒ 残件有无与成功与否无关，但绝不是「只有 3 趟成功趟带残件」。

## 5 · 24 份 archive except_post 逐份清单（同目录多份分别算）

| 目录 | 文件名 | sha256 |
|:--|:--|:--|
| `archive_T5` | `except_post_20261017T081458810997.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T5` | `except_post_20261017T110336047306.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T5` | `except_post_20261017T110600786981.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T5` | `except_post_20261017T110823674312.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T5` | `except_post_20261017T111323095618.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T6` | `except_post_20261017T124738394283.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T7` | `except_post_20261017T133055150567.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T8` | `except_post_20261017T134654270288.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T9` | `except_post_20261017T140815458952.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T10` | `except_post_20261017T142737965802.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T11` | `except_post_20261017T150156704055.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T12` | `except_post_20261017T192537074930.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T13` | `except_post_20261017T201526735976.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T14` | `except_post_20261017T212134826287.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T15B` | `except_post_20261017T222039585271.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T15B` | `except_post_20261017T223730077556.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T16` | `except_post_20261017T230500846717.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T18` | `except_post_20261017T234726314556.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T19` | `except_post_20261018T021838988933.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T20` | `except_post_20261018T024339149893.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T21` | `except_post_20261018T025925909718.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T22` | `except_post_20261018T033315687119.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T23` | `except_post_20261018T033928816659.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |
| `archive_T31` | `except_post_20261018T082850828056.txt` | `6694b75e46a6e773e1d37c42b0b0de0545cc35eae5a8f5425502e17898aac251` |

## 6 · D 问：final_exit=0 但 error.txt 里有异常（T5 核实）

**核实结果：属实，且只有 `archive_T5` 一趟（37 个 archive 中唯一）。**

- `archive_T5/qc151_run_log.json` = `{"final_exit": 0, "cleanup_failures": []}`；`archive_T5/qc151_fields.json` = `META.final_exit_code=0`、`MANIFEST.final_rewritten_exit_code=0`、`MANIFEST.final_verdict=PASS`、`EXCEPT.new_exception_count=0`。
- `archive_T5/error.txt` 全文首 4 行：`type = ArgumentError` / `where = ...\qc151_u0400_trip\qc151_trip.py:791` / `repr = ArgumentError('argument 2: OverflowError: int too long to convert')`；Traceback 落点 `s4_injection_gate → s4_enum_modules → psapi.GetModuleFileNameExW(h, arr[i], buf, 260)`，末行 `ctypes.ArgumentError`。**这是 harness 自身的 Python 异常，不是游戏崩溃。** 另按铁律 6：`find "$D/archive_T5" -iname "*console*"` 输出为空 ⇒ 该目录 console 文件「缺」（不是 0 字节）。
- 时间分离（`python -I -X utf8` 读 mtime）：`error.txt` 与 `except_post_20261017T081458810997.txt` 同为 **2026-10-17T08:14:58**；而 `qc151_fields.json` 的 `META.started=2026-10-17T11:13:07+08:00`、`finalized=11:13:34`，`qc151_run_log.json` mtime = 11:13:34。同一 `archive_T5` 目录里另有 4 份 except_post（11:03/11:06/11:08/11:13），说明该目录是**复跑/多次尝试的归档袋**，早前的 `error.txt` 未被清掉即被带入。
- 按铁律「不许把同名文件在不同目录/不同时刻当同一次事件」：`error.txt` 的 08:14:58 异常属于**该目录内更早的一次失败尝试**，而 `final_exit=0` 属于 11:13:07 那次成功收尾；两件事不能互相否定。

**这算不算正常退出？** 对「11:13:07 那一趟」而言：算——`final_exit=0`、`cleanup_failures=[]`、`final_rewritten_exit_code=0`、`final_verdict=PASS`、`TERM.terminate_sent=true`、`EXCEPT.new_exception_count=0`，收尾完整，是 harness 记录的正常退出。但**不能把整个归档目录称作「零异常的正常退出」**：目录里确实留着一份 harness `ArgumentError`，它是脚本缺陷的实物证据，属于较早尝试。按本次「每趟独立判定」口径，`archive_T5` 的 cause 记为 **harness 脚本缺陷**（针对目录内留存的异常件），并在上一段明确其与 `final_exit=0` 的时间分离；若只问 `final_exit=0` 那一次运行，答案是没有异常、正常退出。

## 7 · 附节：不是 archive_T 前缀但有 measure 产物的趟（29 个）

`python -I -X utf8` 枚举 D 下所有含 `measure_w*.json` 的非 archive_T* 顶层目录 → **29 个**。复核轮 `rglob('measure_w*.json')` 全量 104 份的准确分层：**D 根层 3 份 + 14 个 archive 子目录 42 份 + 29 个非 archive 子目录 59 份 = 104**；即 43 个子目录只含 101 份，104 份是把 D 根层算作第 44 个含 measure 的目录才成立（不能把「43 个目录」与「104 份」写成同一集合）。全部 29 个的 `qc151_run_log.json` 均存在且 `final_exit=0`、`cleanup_failures=[]`；全部无 `error.txt`；每目录各 1 份 except_post，sha256 全为基线值（复核员逐目录核过，无异常）。

| 目录 | final_exit | error.txt | w0/w1/w2 | except 份数 | 台账登记（前 2 处） |
|:--|:--|:--|:--|--:|:--|
| `l1_20261023` | 0 | 无 | 1/0/0 | 1 | L1037/§479、L1266/§488 等 51 处 |
| `l1_20261023b` | 0 | 无 | 1/0/0 | 1 | L3388/§533、L5423/§554 |
| `l1_20261023c` | 0 | 无 | 1/0/0 | 1 | L2001/§514、L2215/§518 等 3 处 |
| `l1_20261023e1` | 0 | 无 | 1/0/0 | 1 | L2152/§517、L2247/§519 等 6 处 |
| `l1_20261023e4` | 0 | 无 | 1/1/1 | 1 | L1037/§479、L1267/§488 等 24 处 |
| `l1_20261023hb` | 0 | 无 | 1/0/0 | 1 | L2386/§521、L2393/§521 等 5 处 |
| `l1_20261023hc` | 0 | 无 | 1/0/0 | 1 | L2310/§520、L2386/§521 等 7 处 |
| `l1_20261023k` | 0 | 无 | 1/0/0 | 1 | L1266/§488、L1563/§502 等 7 处 |
| `l1a_20261020` | 0 | 无 | 1/1/1 | 1 | L260/日志§313、L300/§317 等 6 处 |
| `l1c_20261021` | 0 | 无 | 1/1/1 | 1 | L2153/§517、L2306/§520 等 5 处 |
| `l1d_20261021` | 0 | 无 | 1/1/1 | 1 | L474/§317、L662/§317 等 5 处 |
| `l1e_20261021` | 0 | 无 | 1/1/1 | 1 | L663/§317、L2253/§519 等 4 处 |
| `l3_1101v3a` | 0 | 无 | 1/1/1 | 1 | L1421/§496、L2155/§517 等 5 处 |
| `l3_1101v3b` | 0 | 无 | 1/1/1 | 1 | L2000/§514、L2156/§517 等 4 处 |
| `l3_1101v3c` | 0 | 无 | 1/0/0 | 1 | L2001/§514、L2215/§518 等 4 处 |
| `l3_1101v4b` | 0 | 无 | 1/0/0 | 1 | L2002/§514、L2215/§518 等 4 处 |
| `l3_1101v4c` | 0 | 无 | 1/1/1 | 1 | L2420/§521、L3751/§537 等 9 处 |
| `l3_1101v4d` | 0 | 无 | 1/1/1 | 1 | L1733/§508、L1787/§510 等 9 处 |
| `l3_1101v4e` | 0 | 无 | 1/1/1 | 1 | L1787/§510、L1864/§513 等 14 处 |
| `l3_1101v4f` | 0 | 无 | 1/0/0 | 1 | 无登记 |
| `l3_1101v4g` | 0 | 无 | 1/0/0 | 1 | 无登记 |
| `l3_1101v4h` | 0 | 无 | 1/0/0 | 1 | L4434/§544、L4444/§544 |
| `l3_20261021` | 0 | 无 | 1/1/1 | 1 | L664/§317、L964/§476 等 15 处 |
| `l3_20261023` | 0 | 无 | 1/0/0 | 1 | L920/§317、L1562/§502 等 35 处 |
| `l3_20261023q` | 0 | 无 | 1/1/1 | 1 | L920/§317、L1562/§502 等 18 处 |
| `l3_20261023r` | 0 | 无 | 1/1/1 | 1 | L2368/§521、L2391/§521 等 15 处 |
| `l3_20261031ha` | 0 | 无 | 1/0/0 | 1 | L2157/§517、L2735/§525 等 3 处 |
| `l3_20261031hb` | 0 | 无 | 1/1/1 | 1 | L1993/§514、L1999/§514 等 9 处 |
| `t55k_20261020` | 0 | 无 | 1/1/1 | 1 | L301/§317、L3386/§533 |

★ 另有 4 个**无 measure 产物但有 error.txt 与 `final_exit=19`** 的非 archive 目录，属本线「怎么结束」的直接旁证，单列于此（不并入 rows）：

| 目录 | final_exit | error 类型/定位 | repr | except 份数 | 台账 |
|:--|:--|:--|:--|--:|:--|
| `l1_u0800_20261020` | 19 | SystemExit @ D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py:490 | SystemExit(19) | 4 | L254/状态日志·无§号 |
| `l1_u0800_e1_20261020` | 19 | SystemExit @ D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py:490 | SystemExit(19) | 1 | 无登记 |
| `l1_u0800_e1b_20261020` | 19 | SystemExit @ D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_carrierfix_20261020\qc151_trip.carrierfix.py:490 | SystemExit(19) | 1 | 无登记 |
| `l1_u0800_e1c_dump_20261020` | 19 | SystemExit @ D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py:490 | SystemExit(19) | 1 | L260/日志§313 |

这 4 趟（及 `l1_u0800_20261020/_r1_failed/error.txt` 子目录，同类 `SystemExit(19)`）在台账 `L250-260`（日志 §303–§313）被反复翻案：先判「完整性检查弹窗」→ 推翻为「csf 初始化失败/进程 5 秒自退」→ `L260` 定谳 **D-117 载体绝对路径 ≥131 字符**，`L259` 明确 E1b/E1c 的 `0x0084F2BA/.data`、`0x0054A56E` 两个崩溃地址「**不能作 ② 证据**，是 csf 框之后的次生现象」。其 `error.txt` 是 harness 的 `SystemExit(19)`（阶段超时设计性硬停），不是游戏崩溃。本节只作范围外旁证，不改任何台账结论。

## 8 · 台账与盘面不一致处（conflicts）

1. **`L80`（日志 §43）「archive_T* 命名止于 T23」与盘面不符**：实际存在 37 个 archive_T*，其中 T31–T49_u0800（含 `archive_T49_u0800`）共 17 个在 T23 之后。该行自身同段又写「T31 产物补档 `archive_T31/`」，前后自相矛盾。盘上旁证：`TRIP_ID_RECONCILIATION_20261018.md:3` 是「对账方法」行、**:4** 才是结论「现存 37 个 archive 全部与其实测 trip-id 一致」；台账 `L98` 原文为「卡面 §T59：37 archive 零错名」，并非「现存 37 个 archive」字样。两处原引行号/原文在初版有误，此处更正；盘面 37 与两处旁证的数量一致 ⇒ 以 37 为准。
2. **16 个 archive 缺 `qc151_run_log.json`**（T15_ABORTED/T17/T34–T45/T47/T49_u0800 中 14 个）而台账大量引用其 `measure_w*.json` 数值，从未登记「final_exit 缺件」。D-16 裁决书 `RULING_D16.md:35,139` 只登记了「23 个目录缺 w0」，未登记 run log 缺口。本表按铁律写「缺」，不拿 `qc151_fields.json` 的 `final_exit_code=0` 回填。
3. **21 个 archive 目录名在台账中零命中**（复核轮用 37 个完整目录名对全文做子串检索：`HIT 16 / MISS 21`）。精确零命中名单（21 个）：`archive_T5, T6, T7, T8, T9, T10, T11, T12, T13, T14, T15B, T15_ABORTED, T16, T17, T18, T19, T20, T21, T22, T23, T37`；命中 16 个 = T31, T32, T33, T34, T35, T36, T38, T39, T40, T41, T42, T43, T44, T45, T47, T49_u0800。台账只用裸 `T5/T11/T17/T23` 等短名。这些趟的退出状态（含 1/19/22/63 四种非 0 码与 T5 的 `final_exit=0`+异常）在台账正文里没有逐目录登记，只有 `book_T12_20261017/C_DEFECT.md`、`L1_BASELINE_TRIPS_20261021.md`、`TRIP_ID_RECONCILIATION_20261018.md` 等盘上旁证。
4. **`L4747/4770`（§547）「全 archive_T* 14 趟」范围表述不成立**：盘面 37 个 archive、14 份现存 w0、23 个目录缺 w0；D-16 `RULING_D16.md:35` 已裁「必须改成『14 份可核 w0 中唯一首拍为零』」。本轮亲核 14 份 w0 目录 = `T32/T33/T34/T36/T38/T39/T40/T41/T42/T43/T44/T45/T47/T49_u0800`，与裁决一致。
5. **「107/107 同一基线」在 archive 范围内的口径需补边界**：`L4424` 说「全库 107/107」，但 37 个 archive 内只有 **24 份**（**19 个目录有、18 个目录 0 份**），其余 83 份散在根层与非 archive 子目录。结论本身无例外（§4），但「每个 archive 趟都有 except_post」这一隐含读法不成立——**18 个** archive 是「缺件」，不是「有例外签名」。
6. **`error.txt` 与 `final_exit` 的时间错配未在台账登记**：`archive_T5` 的 `error.txt`（08:14:58, ArgumentError）比该目录 `qc151_run_log.json`（11:13:34, final_exit=0）早约 3 小时；台账未登记这一残留件，若按「同目录=同一次事件」读就会得出「final_exit=0 却抛未捕获异常」的错误结论。
7. **根层 `T32_console.exitcode`…`T54_console.exitcode` 与 `qc151_run_log.json` 两套退出记录未对账**：根层 23 个 exitcode 文件里 22 个为 0、`T54_console.exitcode=19`（`T54_console.log` 尾为 `SystemExit: 19`），而根层 `qc151_run_log.json` 是 `final_exit=0`、`error.txt` 是 `SystemExit(19) @ :490`。这些是不同时刻的活件被覆写后留下的混合态，台账 `TRIP_ID_RECONCILIATION_20261018.md:9-14` 已登记「单活文件每趟覆写」，但没有逐件退出码对账表。本轮不把根层活件归给任何 archive 趟。

## 9 · 诚实边界

- 本轮没有读活进程、没有真机、没有写任何采样/注入/Hook/MiniDump/SuspendThread/StackWalk 代码；未 git add / commit。
- 「无法判定」的 **29 个** archive 目录不是「已证正常」，只是缺独立退场证据（`error.txt` 缺、console 多为 0 字节/部分为缺、无 crash dialog/WER 件）。§2 表 37 行第 9 列 cause 分布（复核轮改判后重算）：harness 脚本缺陷 5（T5/T10/T11/T22/T23）/ 环境问题 2（T6/T7）/ 人为中止 1（T15_ABORTED）/ 无法判定 29 / 游戏崩溃 0。`TERM.terminate_sent=true` 只能证明脚本发过终止请求。其中 `archive_T5` 与 `archive_T32` 根本没有 console 文件（`find -iname "*console*"` 输出为空）⇒ 按铁律 6 写「缺」，不写「0 字节」；其余 0 字节 console 的目录复核无误。
- `final_exit=0` 与「游戏没崩」不是同义；本轮只判「这一趟是怎么结束的」，不判游戏内部机制。
- 台账 §544 的 107/107 结论本轮只在 37 个 archive 范围内核对（并额外重算了全库 107 份哈希），未复算其「v4e 成功趟同样有」以外的其它统计。
- 所有 sha256 均为整文件 SHA-256，命令 `sha256sum` / `hashlib.sha256(read_bytes())` 双路一致。

## 10 · 复核轮修订记录（NEEDS_REVISION 逐条处置）

复核员 8 条异议**全部接受并已在本文件原地改正**。以下列出本轮实际跑过的命令与输出摘要（Python 一律 `python -I -X utf8` 且路径用绝对路径；另用了 `find` / `grep` / `sed` / `diff` / `wc` 等只读 shell 工具；未启动任何真机、未写任何采样代码、未 git add/commit）。复核员提供的 `_verify_probe2_out.txt` / `_verify_compare_out.txt` 与本文件**同处可写目录** `EXIT_CENSUS_77a0d667/`；本轮**未直接读取其原文**（避免把复核员结论当自己的检查），仅按异议描述逐项独立复算；凡复算一致者采纳，未一致者会在此说明（本轮无不一致项）。

| # | 异议 | 本轮复算命令与输出 | 处置 |
|:--|:--|:--|:--|
| 1 | C 问覆盖计数 | 命令：对 37 个 archive 逐目录 `glob('except_post_*.txt')` 并按目录汇总 + `hashlib.sha256(read_bytes())`。输出：`ARCHIVE_DIRS 37`、`HAS_EXCEPT_DIRS 19`、`NO_EXCEPT_DIRS 18`、`FILES_IN_ARCHIVES 24`、`ALL_FILES 107`、`HASHES {'6694b75e...a251': 107}`、`ROOT_LEVEL 44`；0 份名单 18 个与复核员一致。另对 14 个 `final_exit=0` 目录复算：`WITH_EXCEPT 12`（T5 5、T15B 2、T8/T9/T12/T13/T14/T16/T18/T20/T21/T31 各 1）、`WITHOUT_EXCEPT [(T32,0),(T33,0)]` | 接受。§0、§4、§8-5 的「13 个/21 个/3 趟」分别改为「18 个/19 个/12 趟」；24 份文件数、107/107 同哈希、§5 逐份清单本来就正确，保留 |
| 2 | 无法判定计数 | 命令：解析本报告 §2 主表 37 行的第 9 列 `collections.Counter`。输出（**改判前**）：`ROWS 37`、`{'harness 脚本缺陷': 3, '环境问题': 5, '无法判定': 28, '人为中止': 1}` | 接受。§9 的 26 改 29（改判后）；见下方分布行 |
| 3 | 台账零命中数 | 命令：37 个完整目录名对 `GOAL_THREE_TARGETS_20261018.md` 全文做 `name in text` 子串检索。输出：`TOTAL 37 HIT 16 MISS 21`，命中/未命中名单与复核员一致 | 接受。§0、§8-3 的 24 改 21，并给出精确 21 个零命中名单，删去凑不出 24 的错误括号说明 |
| 4 | T32 console 应写「缺」 | 命令：对 37 个 archive 逐目录 `glob('*console*')` 并打印文件名与字节数。输出：`archive_T5 缺`、`archive_T32 缺`，其余 35 个均有 console（T10 485B / T11 580B / T22 577B / T23 577B / T15B 两份 0B，其余 0B） | 接受。§2 的 T32 行、§6 的 T5 行、§9 概括均改为「缺」，并说明 `find -iname "*console*"` 输出为空；其余 0 字节 console 保留 |
| 5 | §7 目录数/文件数自相矛盾 | 命令：`rglob('measure_w*.json')` 按 `p.parent` 分层。输出：`ALL 104 ROOT_LEVEL 3 SUB 101 ARCHIVE_SUB 42 NONARCH_SUB 59`、`DIRS_WITH_MEASURE 44`、`SUBDIRS_WITH_MEASURE 43`、`ARCHIVE_DIRS_WITH 14 NONARCH_DIRS_WITH 29`；根层 3 份文件名 `measure_w0/1/2.json` | 接受。§0、§7 改为「43 个子目录含 101 份 + D 根层 3 份 = 104 份（共 44 个含 measure 的目录）」，不再把 43 与 104 写成同一集合 |
| 6 | §3 缺 runlog 目录产物描述 | 命令：对 16 个「缺」目录逐目录 `glob('measure_w*.json')`。输出：T34/T36/T38/T39/T40/T41/T42/T43/T44/T45/T47/T49_u0800 共 12 个为 1/1/1；T35/T37 为 0/0/0；T15_ABORTED/T17 亦 0/0/0 | 接受。§3 改「14 趟中 12 趟有 measure、2 趟（T35/T37）measure 全缺」，与 §2 表 :62/:64 的 0/0/0 自洽 |
| 7 | 问题 B：19 三次归因证据不足 | 命令 A：`sed -n '20,36p;128,140p' book_T12_20261017/C_DEFECT.md` → `end_stage` 源码 `:450 if dt > STAGE_TIMEOUT_S` → `:454 sys.exit(EXIT_STAGE_TIMEOUT)`，:135-137「触发条件不是是否收敛而是 dt>30」。命令 B：`diff archive_T22/T22_console.log archive_T23/T23_console.log` → 仅 `main 3967→3972`、`_main_wrapper 4185→4190` 两处行号差，末行同为 `SystemExit: 19`。命令 C：逐趟 `json.loads(qc151_fields.json)` 取 NAV 键 → T22 `want=[72,220,262,304,556] ok=false polls[0].red_centers=[61,220,262,304,556] hit=false`；T23 `want=[220,262,304,556] ok=true polls[0].red_centers=[61,220,262,304,556] hit=true`；两趟 `signature_got_nav_menu` 完全同值。命令 D：T23 `EXCEPT.new_exception_count=0`、`TERM.terminate_sent=true`、`error.txt` 不存在 | **接受并改判**。§2 的 T22/T23 行、§3 的 19 段：撤回「环境问题」与「三个不同根因」，改判 harness 脚本缺陷（同为 `end_stage` 的 dt>30 设计性硬停）；ok 差异来自 harness `want` 判据改动（画面签名同值 + 脚本行号变化），无游戏侧失败独立证据。保留的可核差别：失败阶段 window vs nav_menu、三趟为三次独立发射、T11 另有 QC188 专属定谳 |
| 8 | 旁证引用行号/原文小误 | 命令：`sed -n '1,6p' TRIP_ID_RECONCILIATION_20261018.md` → :3 是对账方法、**:4** 才是「现存 37 个 archive 全部与其实测 trip-id 一致」；`sed -n '98p' GOAL_THREE_TARGETS_20261018.md` → 原文「卡面 §T59：37 archive 零错名」；`sed -n '23p;34,36p;39p' L1_BASELINE_TRIPS_20261021.md` → :23 是 `EXIT_WINDOW_NOT_FOUND=22` 的定义、:34-36 才是「缺 ddraw.dll 与全部 *.mix」、:39 是 T6 先例。另 `grep -n "archive_T19\|T19 "` 台账全文零命中、`grep -rIn "cbNeeded=80\|allocated=72"` 仅命中 `archive_T19/s4_module_table.txt:2` | 接受。§8-1 更正行号与原文；§3 的 22 段改引 `:23/:34-36/:39`；**并追加一项初版过度归因**：T19 的「环境瞬态」原本搬用了台账 L1531 对 `l3_1101v4a`(v4-a, err=299) 的定谳，而 T19 字段里是 `cbNeeded=80 > allocated=72`、无 err=299、台账无 T19 登记 ⇒ §2/§3 把 T19 由「环境问题」改「无法判定」，写明缺 S4 硬停的具体触发原因 |

**修订后的判定分布（37 行 §2 表，本轮改判完成后重跑 `collections.Counter` 实测）**：`POST_EDIT_ROWS 37 DIST {'harness 脚本缺陷': 5, '环境问题': 2, '无法判定': 29, '人为中止': 1}` ⇒ harness 脚本缺陷 5（T5/T10/T11/T22/T23）／环境问题 2（T6/T7）／人为中止 1（T15_ABORTED）／无法判定 29（含 T19）／游戏崩溃 0。§9 正文已同步写 29；初版的「26」与改判前的「28」均不再作为最终口径。

**未采纳/未核实的部分**：无。复核员引用的 `_verify_probe2_out.txt:40-42,67,83,127,139` 与 `_verify_compare_out.txt` 末段 ACTUAL 本轮未读原件（与本文件同目录，可由复核员自行复核），本轮结论全部来自上表所列的独立复算命令。
