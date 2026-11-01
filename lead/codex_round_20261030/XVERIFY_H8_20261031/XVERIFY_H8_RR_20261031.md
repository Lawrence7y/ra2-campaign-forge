# XVERIFY_H8 · RR（复审轮）· harness8 v2 + 发射器副本 v2 + 判档器副本 + 卡片/设计件 v2 修复_delta 判定书（2026-10-31）

审查人：harness8 复审员（Qoder，DeepSeek 族，与实现线 GLM 族**不同族**）；同线续任（前任判定书
`XVERIFY_H8_20261031.md`，本件只核其红项 R-1 / 黄项 Y-1..Y-8 的**修复_delta**，不重做已 CONFIRMED 项）。
被复审件（全部只读）：`lead/goal1_harness8_20261031/qc151_trip.harness8.py`（v2 `dd5459fe0cf3461c`）、
`_launch_h8_20261031.py`（`9a1a795b92eb0b10`）、`_judge_h8_20261031.py`（`2df17debe8a1a731`）、
`LEADER_battle/GOAL1_BATCH_H8_FRAMEBOUND_20261031.md`（`fde822efe22a1598`）、
`HARNESS8_FRAME_BOUND_DESIGN_20261031.md`（`61fec3646da8ab28`）。

## mimosa 声明

**mimosa 未实际运行。** 本 ask 要求的是逐条修复_delta 复验（自跑 diff / AST 守卫证明 / 离线桩实测 /
判档器实跑 / 进程枚举实测），未要求全项目深度安全审计；`security_scan` 按其工具约定仅在明确要求
深度或完整项目审计时调用。本件全部结论均由我**亲自执行**的命令或**亲读**的代码行支撑；
未执行之处逐条标 `UNVERIFIED`。

---

## 0. 一句话结论

**红项 = 0**（R-1 修复**实测生效**，含 A8 端到端 fail-closed 正控）；(1)(2)(3)(4)(5)(7) 全部 CONFIRMED；
(6) 卡片/设计件 **实质 CONFIRMED，但有一处表述被真机产物证伪**（节律「≈410Hz」）⇒
**GO-WITH-CONDITIONS**（条件 C-R1..C-R6，见 §4）。
（程序性事实照旧：v1 字节 `e29a9a07…` 已被修复包原地替换，v1 发射器亦不在盘上/git 索引 ⇒
v1→v2 的 delta 我是用「前任 v1 存档 diff vs 我本轮 v2 diff」两条独立路径重建的，见 §5。）

---

## 1. 逐条判定与证据

### (1) R-1（前任唯一红项）—— **CONFIRMED（已修，实测生效）**

亲跑命令：`python -I -B -X utf8 lead/codex_round_20261030/XVERIFY_H8_20261031/_rr_probe_r1_procs.py`
（importlib 加载**两份原件**，直接调 `PE32/list_procs/game_procs`；`rr_p1_r1.stdout.txt`）：

```
COPY_v2  sizeof=568  n_fields=10  has_parent_field=true  list_procs_count=499  game_procs=[]  last_error=18  own_pid_present=true
MASTER   sizeof=568  n_fields=10  has_parent_field=true  list_procs_count=499  game_procs=[]  last_error=18  own_pid_present=true
三轮 reps：copy [499,499,499] / master [499,499,499]
字段序（两方**逐字段全等**）：dwSize,cntUsage,th32ProcessID,th32DefaultHeapID,th32ModuleID,
                              cntThreads,th32ParentProcessID,pcPriClassBase,dwFlags,szExeFile
```
⇒ 与前任 v1 实测（copy `sizeof=560` / `entries=0` / last error **24=ERROR_BAD_LENGTH**）对照：
**枚举报废通道已消除**；`last_error=18 (ERROR_NO_MORE_FILES)` = 正常耗尽（前任判母本健康的同一口径）。
`_rr_probe_poscontrol.py` 再测：副本与母本**同一时刻**快照 `542/543` 条、字段面相等；
`_rr_probe_p4_misc.py` 证**读出的名字正确**（自 PID → `python.exe`，空名条目 0 个，558 条）。

**A8 能真的变红（端到端正控，非读码）**：`_rr_probe_preflight_failclosed.py` 直接调副本 `main()`，
只桩 `game_procs`，跑完 A1/A2/A11 真值 + A8：
```
E1 fake=[gamemd.exe]           → A8 got=1 want=0 MISMATCH → "!! 预检不过，不发射"  rc=2  out_dir_created=False
E2 fake=[gamemd,ra2loader]     → A8 got=2 want=0 MISMATCH → rc=2  out_dir_created=False
E4 超长 suffix                 → A8 OK(0) → "out-dir 预演 len=154 (门禁 130) BLOCK" rc=2  out_dir_created=False
```
（该分支在 `OUT_DIR.mkdir` 之前 `return 2` ⇒ 实测**零目录创建、零发射、零真机**。）

**kill_under 零误伤（只读桩，未终止任何真实进程）**：同件对副本 `kill_under` 喂 6 个合成 pid
（3×gamemd + GameMD.EXE + notepad + ra2loader），桩 `k32.OpenProcess/QueryFullProcessImageNameW/
TerminateProcess`（桩可赋 `argtypes`，见 `_StubFn`）：
```
opened_pids = [7771,7772,7773,7775,7776]      # 7774=notepad 连 OpenProcess 都不进（名过滤）
terminated  = [7771,7772]                     # 仅图像路径落在本批载体目录下者
zero_false_positive_on_unrelated = true       # 7773（载体外 gamemd）/7776（game.exe）未被杀
```
⇒ 清理面恢复**有选择性**：按名过滤 + 按载体路径精确判定，与母本语义一致
（`list_procs/game_procs/kill_under/rm_carrier` 四函数 AST `full_equal=True`，见 §2）。

**头部声明 5 处枚举 vs 实 diff**：去注释+去 docstring 的功能级 diff（`_rr_probe_functional_diff.py`
→ `rr_p10_launcher_functional_diff.txt`，注释 token 只剥行尾注释、保留同行代码）：
副本相对母本 **11 行增 / 9 行删**，逐行归类后**全部落进声明的 5 处**：
① `KNOWN_HARNESS`+`HARNESS_BY_SHA16` 各追加 1 条 + 模块缺省 `HARNESS` 路径；② 缺省 `HARNESS_SHA16`；
③ `OUT_DIR`/`TRIP_ID` 命名；④ `PE32` 补行（**功能 diff 中不可见**——`class PE32` 节点与母本 `full_equal=True`
⇒ 只能由上面 `sizeof/字段面` 实测坐实，非声明文字）；⑤ `--variant` 缺省 L1→L3 + `--extra-argv` help 换本批参数。
AST 顶层差异节点 = `{assign:HARNESS, assign:HARNESS_BY_SHA16, assign:HARNESS_SHA16, assign:KNOWN_HARNESS, def:main}`；
`def:main` 内仅 4 处语句 replace（`--suffix` help 文案、`--variant`、`--extra-argv` help、`OUT_DIR`/`TRIP_ID`、banner print），
`build_harness_argv` 除 docstring 外 body **全等**（同输入实测 argv **逐元素相等**：`fullscreen_equal=true / windowed_equal=true`）。
⇒ **「除上述 5 处及注释外与母本逐字一致」基本属实**；两处纯文案行未逐处列举
（`--suffix` help「b/c/d」→「a/b」:179、banner `print(...)` :212），属**登记级瑕疵**，零语义影响 → 见 §3 Y-R1。

### (2) Y-2 跳帧拒采 —— **CONFIRMED（两路径覆盖 + 边界正确 + 不误伤）**

代码亲读：jump 守卫在**循环之后、达标赋值之前** = `qc151_trip.harness8.py:5099`
（`if _h8_frame - _h8_n > H8_OFFSET_MAX_FRAMES:`，常量 `:3889`=2），拒采臂 `:5103-5125` 写
`overrun_kind:"jump"` + payload `verdict`+`h8` + 三行 rec + `return`；
首拍越界臂 `:5043-5068` 补 `overrun_kind:"first_read"`（`:5048`，形态标注在场）。
循环条件 `:5069` `while _h8_frame is None or _h8_frame < _h8_n` ⇒ 首拍 None 会进循环、
中途 None 会继续 ⇒ 两条跳读路径都必然落到 `:5099` 的守卫上（**结构闭合**）。

实测（`_rr_probe_y2_jump.py` → `rr_p2_y2.stdout.txt`；桩替 `_rpm_open/_rpm_u32/_rpm_close/
_measure_poll_span/取证/焦点`，**零真机、零游戏进程**，帽压到 0.2 s）：

```
J1 [None,900]  N=400 → frame_overrun kind=jump  off=500 reject=True   ★ask 指定用例（应拒）✓
J2 [399,400]  N=400 → 达标 off=0  reject=False  note=H8-1              ★ask 指定用例（应达标）✓
J3 [398,400]  N=400 → 达标 off=0  reject=False                          ★ask 指定用例 ✓（循环 exit 后 offset 用真实读数）
K1 [399,402]  N=400 → 达标 off=2 reject=False   ★边界 offset==2 过 ✓
K2 [399,403]  N=400 → frame_overrun kind=jump off=3 reject=True  ★边界 ==3 拒 ✓
M1 [10,900]   → jump 拒（中途跳读）✓    M2 [None,399,402] → 达标（不误伤）✓
M3 [None,None,403] → jump 拒 ✓          T1 [10]×5 → frame_wait_timeout（off=None,timed_out=True）✓
E1 [400]  → 达标 off=0 ✓                 E2 [900] → first_read 拒 ✓
```
**不误伤性全扫描**（`rr_p12_sweep.stdout.txt`，20 例）：
`f0∈{399,398,397,395} × f1∈{400..404}` ⇒ offset 0/1/2 **全部达标**、offset 3/4 **全部 jump 拒**，
与期望判据 **20/20 相符、零 mismatch**。
⇒ 正常 500 Hz 相邻拍 1 帧步进（offset 0..2）**必然通过**；前任 Y-2 的两条漏检路径（首拍 None→跳读、
中途跳读）均被闭合。四条拒采/达标路径 `handle_closed=true` 全测到（finally 纪律未被新块破坏）。

### (3) Y-7（N≥1 校验）—— **CONFIRMED**

读证：`:7542-7546`（在 `getattr(args,'h7_measure_start_frame',None) is not None` 守卫**内**）
`if _h8_n_arg < 1: print(...) ; raise SystemExit(2)`。
离线实测（哑目标图，`--out-dir` 指向我的写域，**零真机、零载体**）：
```
N=0  → EXITCODE=2  stdout "★ H8：--h7-measure-start-frame 必须 ≥1（实得 0）⇒ 拒发"   rr_y7_N0_fresh.stdout.txt
N=-5 → EXITCODE=2  （同上，实得 -5）
N=-1 → EXITCODE=2  （本轮 fresh 复跑，退出前**未创建 ct/**，WORKDIR 空目录被 :7470 提前 mkdir）
parse_args 对照：缺省 None；--h7-measure-start-frame 400 → 400
```
退出码 2 在 harness 自身 `EXIT_*` 常量表（27 条，值集合 `{0,10..29,62,63,64,65,70,130}`）中**未被占用**
⇒ 不撞既有码；与 argparse 非法取值同语义。残留瑕疵：拒发**不落任何盘上留痕**
（`ACTIVE_REC[0]=rec` 在 `:7588`，晚于 `:7542`；`_write_final_records` 见 `rec is None` 直接返回 `:8726`）
⇒ 台账 §488 已把口径写成「exit 2 + 趟目录无产物 = 参数非法拒发」，本件认可该处置（继承前任 C-4）。

### (4) Y-1 判档器副本 —— **CONFIRMED（扩集+翻转，零回归）**

亲跑（`--trip-dir` 三趟）：
```
python -I -B -X utf8 lead/goal1_harness8_20261031/_judge_h8_20261031.py --trip-dir synth_overrun → EXIT=3
                                                     ……/synth_timeout                          → EXIT=3
                                                     ……/synth_ok                               → EXIT=1
```
**与前任基线（2/2/1）的翻转**由我**同时跑母本判档器**坐实（`_rr_probe_judge_flip.py` →
`rr_p7_judge_flip.stdout.txt`；为不破坏链上取证，我**另建** `rr_fx_*` 副本，未改前任 `synth_*`）：
```
fixture(sha)            master_judge   copy_judge   changed
overrun_v1sha(e29a…)        2               3          ✓   ← 短路集扩集生效
timeout_v1sha(e29a…)        2               3          ✓
overrun_v2sha(dd54…)        2               3          ✓
timeout_v2sha(dd54…)        2               3          ✓
ok_v1sha(e29a…)             1               1          —（两侧 harness 条目 FAIL：v1 不在任何清单）
ok_v2sha(dd54…)             1               1          —（副本侧该条目转 PASS，唯一 FAIL=合成趟故意缺 qc151_fields.json）
```
⇒ 翻转方向与幅度正确；`synth_ok` 仍 EXIT=1 属**正确退役**（合成夹具缺 fields），
副本下 `harness 在已知清单内` 已由 FAIL→PASS（我核 `rr2_judge_synth_ok.txt` 第 13 行）。
**功能差异恰 3 处**（AST 顶层节点差异集 = `{assign:KNOWN_HARNESS, assign:SHORT_CIRCUIT_VERDICTS, def:main}`；
`def:main` 内只有 1 处语句 replace = `check("harness 在已知清单内…")` 的**标签字符串**）：
`:46-47` 两值入 `SHORT_CIRCUIT_VERDICTS`、`:63` 入 `KNOWN_HARNESS`、`:378` 标签文案 ⇒ **仅此三处**。
**零回归实测**：母本 vs 副本对 3 个**真机历史趟**（`l1_20261023 / l1_20261023e4 / l3_20261021`）
EXIT 完全相同（3/1/1），输出差异**仅**在扩集打印与标签文案（`rr_noreg_*.txt`）。
判档器无写操作（`grep write_text|open(` = 0 命中），我跑真机趟后 `find -newermt` 复核**无新文件**。

### (5) v2 中性 —— **CONFIRMED**

```
diff -u harness7 harness8v2 → added 160 / deleted 0 / hunks 4
   @@ -3871,6 +3871,30 @@（H8 const 块）@@ -5003,6 +5027,116 @@（frame-wait）
   @@ -7221,6 +7355,13 @@（argparse）  @@ -7393,6 +7534,25 @@（main-arm）
行数 8607→8767 = +160 ✓；sha256[:16] 自算 = dd5459fe0cf3461c ✓（483,680 B）
```
**最强加性证明（本轮新增方法）**：按 `# >>> H8-BEGIN … # <<< H8-END` 四对标记切块后，
剩余源码与 harness7 **逐字节相等**（`after cutting 4 H8 blocks, equals harness7 bytes? True`；
383,018 字符两侧相同）⇒ 「0 删 + 纯加性 + 删块即还原」三者一次证完。
AST 守卫核（`_rr_probe_ast.py` → `rr_p3_ast.stdout.txt`）：
- `_measure_run`：两个顶层 `Try`，`Try#1 body 22→23`，opcode 级仅一条 `insert h8[2:3]`，
  插入语句 = `If(H8_MEASURE_START_FRAME is not None)`（`:5037`）；
  `handlers/orelse/finalbody` **逐字相等**（母本 `finally: _rpm_close` 未被改写）。
  顶层再核：h7 语句在 h8 中缺失数 = 0（唯一 `replace` 是外层 Try 因内部插入而整体换号，子级对齐显示仅 insert）。
- `main`：`body 48→49`，仅 `insert h8[23]` = `getattr(...) is not None` 守卫；
  H8 守卫块行范围 `7542-7551`，其**嵌套 if** = `_h8_n_arg < 1` ⇒ **N<1 分支确在 `is not None` 守卫内**
  ⇒ 缺省（None）不可达（ask 特别要求抽查的一条，已抽）。
- `parse_args`：`body 22→23`，仅 `insert h8[14]`（`ap.add_argument`）。
- 顶层 call 表达式 h7/h8 各 1 条且相同（`SetProcessDPIAware`）；
  退出码常量 h7/h8 **各 27 条、对称差集为空**；危险 API 计数 h7==h8
  （`WriteProcessMemory 3/3`、`VirtualProtectEx 2/2`、`SetForegroundWindow 16/16`、`TerminateProcess 12/12`）；
  `time.sleep` 14/14、新增 160 行内 `time.sleep/check_trip/begin_stage/end_stage/budget./sys.exit/EXIT_/MiniDump` **全 0**，
  `_doze` 4 次（3 处注释 + 1 处真实调用 `:5096`）。
- 内存编译（`warnings.simplefilter("error")`）h7/h8/发射器副本/判档器副本 **四件零告警**；
  `--help` 双跑 diff：**+6 行（新选项 + 其说明）/ −0 行**，既有选项文本零变动。
- 缺省中性复跑（前任探针原样再跑，不改其脚本）：
  `_probe_default_neutral.py` → `A_default_neutral_rows_equal=True`、`A_rowcount=[9,9]`、`A_h8_state={'frame_wait': None}`；
  `_probe_json_equal.py` → `rows_equal=true (17/17)`、`wallclock_stripped_equal` 三窗全 true、原始差**仅** `t_abs0`。

### (6) 卡片 v2 / 设计件勘误 —— **CONFIRMED，含 1 处 REFUTED（表述）**

| 卡片/设计件声明 | 实况核对（本会话执行） | 判定 |
|---|---|---|
| 假说句 Y-3 降格（卡片 `:8` 「units-下降活动窗」、`:11` 「『交火』断言不出现于结论层」） | `grep 交火` 卡片=1 处（纪律句本身）、实现=1 处（`:3879`，同句写「units 字段语义未定义，交火断言保留项沿 §479」）、harness7=0 处 | **CONFIRMED** |
| Y-4 探针不承重（块头声明 + 达标 note + 卡片「探针读数地位」+ 设计件 §6） | 代码 `:5034-5036` 与 `:5137-5138` 双处在场；卡片 `:28-30`；设计件 §6 第二条 | **CONFIRMED** |
| C-5 时间口径（20 min 帽覆盖第 1 趟全程、两趟≈11 min） | 真机既有产物：ha `duration_s=170.2` + hb `241.1` = 411 s ≈ 6.9 min（只读复算，非本会话跑）| **CONFIRMED** |
| 判档器接入（卡片 `:20-21`，EXIT 0/1/2/3/4 语义） | 实跑副本 EXIT=3/3/1 与语义表一致；短路分支的 `h7_smoke_section` 会执行（见 `rr_judge_synth_overrun.txt` 尾部 `[4b]`）| **CONFIRMED** |
| `--frozen-dump` 不传（卡片 `:16-17`） | 发射器 `build_harness_argv` 不含该参；两趟真机 `_launch_result.json` 的 argv **无 `--frozen-dump`**；harness `:7382` 缺省 False | **CONFIRMED（读证+产物证）** |
| 卡片 `:5` 「R-1 sizeof 568 实证、**list_procs 枚举 499 条**实证」 | 我三轮实测分别得 **499 / 543（母本同刻 542）/ 558** ⇒ 数字**当时为真**，但它随系统负载浮动，把它当常量写进卡片不严谨 | 轻（登记） |
| 卡片 `:40` / 代码 note `:5137` 「有效节律…**≈410Hz 实测**」 | 真机两趟**同一行 rec**折算：ha 25349/73.135=**346.6 Hz**、hb 26939/94.676=**284.5 Hz** ⇒ note 文字与同行 value **自相矛盾**；410 Hz 是前任在裸机测 `_doze(0.002)` 的值，非等待期实测 | **REFUTED（表述）** → C-R3 |

### (7) 残余 —— **UNVERIFIED 维持，不因修复升格**

- 120 s 真实等待、真实 RPM 节律、真实 `hz_effective` 全谱、跳帧误拒**发生率**、`--frozen-dump` 组合下的
  MiniDump 触发面 ⇒ 仍 **UNVERIFIED（本 ask 禁止真机）**。
- 例外于「我亲手」的一项：盘上已有**并行线跑完的两趟真机产物**（`l3_20261031ha/hb`，20:06/20:13 落盘）。
  我只做了**只读复算**（`qc151_fields.json`/`measure_w*.json`/`_launch_result.json`/两枚 tee 日志），
  **不是**本会话新跑真机：A8 `got=0 OK`、`h7_measure_start_frame=400`、
  `h7_frame_wait={reached 400, offset 0, overrun false, timed_out false, wait_s 73.135/94.676, poll 25349/26939}`、
  清理「残留进程 无 / 载体残留 无」、`carriers_deleted=True`、
  判档 ha **EXIT=3**（no_advance，短路集扩集在工作）、hb **EXIT=1**（V11-a FAIL min=6.676）。
  ⇒ 这些只证明「v2 与真机相容、修复面在真实链上被走到」，**不**构成对 410 Hz/超时支的实测。
- `main()` 全链执行（main-arm 装订对 `_measure_run` 的可见性）：仍为**读证 + AST + 编译证**，未执行。
- `_adjudicate_h5/h6` 族是否消费 measure verdict：沿用前任读码判定，未全量执行。

---

## 2. 本轮新增发现（登记，不阻断发射）

- **Y-R1（low）** 发射器头部「5 处枚举」漏列两处纯文案行（`--suffix` help、banner `print`），
  且 `:202` 注释写「ha/hb = 129 ≤ 130」而我实测**两后缀均 130**（仍 ≤ 门禁，可发射，仅注释数字差 1）。
  ⇒ 属「声明穷尽性」瑕疵，非语义差（母本 `PE32/list_procs/game_procs/kill_under/rm_carrier` 功能全等已证）。
- **Y-R2（medium，条件）** 130 门禁的真实余量比卡片说的紧：预演用占位 pid `12345`（5 位），
  而 harness 实际载体名 = `c_<%H%M%S%f 12 字符>_<os.getpid()>`。我用 harness 自己的
  `carrier_pathlen_gate` 实测：
  ```
  suffix=''  pidlen=5→129 PASS   pidlen=6→130 PASS
  suffix='a' pidlen=5→130 PASS   pidlen=6→131 **REJECTED（RuntimeError，mkdir 之前，不新增退出码）**
  suffix='b' 同上
  ```
  本机 pid 实测最大 47912（5 位），历史 **44 枚**载体回执 pid 全为 ≤5 位 ⇒ 本批两后缀确实可发（已实证 ha/hb）。
  但「卡片授权的第 2 趟补发」在**发射 python 进到 6 位 pid 时会被硬拒**（方向 fail-closed、不产半趟）。
  ⇒ 判 CONFIRMED-with-condition，转 C-R2。
- **Y-R3（medium，继承 N-1）** 绑帧**在场性**仍无人判：`--h7-measure-start-frame` 不在
  `build_harness_argv` 缺省里，判档器副本对 `h7_frame_wait` **0 命中**（`grep -c` 实测）⇒
  漏传 `--extra-argv` 会发出一趟**形状完全合法的 harness7 语义趟**并被当本批样本读。
  实现线在 §488 明确**未采**前任 C-1 建议（靠人工双核验兜住）。本件复验其现状，判**须修条件** C-R1。
- **Y-R4（low）C-3 的自检是放宽口径**：实现线新建 `_adjudicate_h8_offline.py`（tee 见
  `c3_offline_adjudicate_h8.txt`），把「note 文本引用」/「容器写入=rec 镜像」计为**引用点**并全判 `[OK]`。
  我独立 grep 复核：`H8_FRAME_WAIT_HZ` 仅定义 `:3894` + 注释 `:5137` ⇒ **零代码引用**（真）；
  `_H8_STATE` 5 处 = 定义 `:3895` + 4 处写入（`:5052/:5077/:5108/:5131`）+ **无读取点**（真）。
  ⇒ 常量/容器的「死键」状态未变，只是自检换口径过关。转 C-R4。
- **Y-R5（low）超时支 `h7_frame_wait` dict 缺 `overrun_kind` 键**（`:5072-5076`），
  与 first_read/jump 两支不对称 ⇒ 判读时「拒采形态」在超时支只能靠 `timed_out` 推。
  实现线 §488 已自列为 v3 积压，与本件一致。转 C-R5。
- **（正面）前任 N-3 已闭合**：`frozen_recheck_h8_v2.txt` / `_post.txt` 第 6 行均已改钉 `dd5459fe…`，
  我逐条复算 **6/6 OK**（harness7 `d019e8be` 母本**逐字节未动**）。
  `frozen_recheck_h8_pre.txt` 第 6 行仍是 v1 `e29a9a07`（mtime 15:37，早于 v2 落盘 18:48）⇒
  **陈旧件未消**，照旧清单跑批前复验会打 MISMATCH。转 C-R6（要么删该陈旧件、要么在其上标注作废）。

---

## 3. 我实际执行的命令（可复算）

```
sha256[:16] 自算：h8v2 dd5459fe0cf3461c / 发射器 9a1a795b92eb0b10 / 判档器 2df17debe8a1a731
                 harness7 d019e8beecfb5fd8 / 母本发射器 4f2a50cca694e1f5 / 母本判档器 72ca057dfe728188
diff -u harness7 harness8v2                                → 160 增 / 0 删 / 4 hunks（rr_h7_h8v2.diff）
H8 四对标记切块后 == harness7 逐字节                     → True（本轮新增方法）
_rr_probe_r1_procs.py   → sizeof 568 / 10 字段 / 499 条 / last_error 18 / 三轮 reps / kill_under 选择面
_rr_probe_poscontrol.py → A8 正控（桩入游戏进程⇒got≠0）/ 母本对照 / Y-5 读写面 / H8_OFFSET_MAX_FRAMES 引用面
_rr_probe_p4_misc.py    → 进程名可读（self pid=python.exe）/ build_harness_argv 同输入逐元素相等 /
                          内存 compile 零告警（h7+h8+两件副本）/ --help 双跑 diff +6−0
_rr_probe_ast.py        → 发射器顶层差异节点 5 个 / _measure_run+main+parse_args 逐语句对齐 /
                          API 计数 / EXIT 常量对称差 = ∅
_rr_probe_functional_diff.py（+同口径重跑，剥注释不剥行尾同行代码）→ 发射器 11 增/9 删、判档器 4 增/2 删
_rr_probe_y2_jump.py    → 13 例（J/K/M/B/T/E 系列）：jump/first_read/timeout/达标 四路 + 句柄关闭
rr_p12（全扫描 20 例）  → offset 0/1/2 全过、3/4 全拒、20/20 与期望判据相符
_rr_probe_judge_flip.py → 母本 vs 副本 × 6 夹具 ⇒ 翻转表（2→3 ×4，1→1 ×2）
判档器副本实跑          → synth_overrun EXIT=3 / synth_timeout EXIT=3 / synth_ok EXIT=1
判档器零回归            → 母本 vs 副本对 l1_20261023 / l1_20261023e4 / l3_20261021 EXIT 3/1/1 相同
harness N<1 离线跑      → N=0 / -1 / -5 ⇒ exit 2 + 拒发提示（三份 fresh stdout/stderr）
carrier_pathlen_gate 直调 → 130 门禁在 5/6 位 pid 下的 129/130/130/131 实测
冻结件逐条复算          → frozen_recheck_h8_v2.txt 6/6 OK；_post.txt 6/6 OK；_pre.txt 5 OK+1 陈旧
L3 清单/哈希            → files=88 / extra=83 / commas=0 / map f3bb0a4e… / gamemd 73201cc0… / A11 dd5459fe…
真机既有产物只读复算    → ha/hb：A8=0、META=400、h7_frame_wait、残留无、carriers_deleted=True、EXIT 3/1
_probe_default_neutral.py + _probe_json_equal.py 复跑 v2 → 9/9 行全等 + 17/17 + 去墙钟 JSON 全等
```

**未运行 / 无法核验（如实）**：见 §1(7)。另：`v1 发射器副本`已从盘上与 git 索引消失（`git show :path` 空）
⇒ 我对 v1 缺陷的引用只能取前任判定书记录 + 本轮 v2 的正向实测，**未能在本会话复现 v1 的 entries=0**。

---

## 4. GO 判据落点与条件

**红项（v2）= 0；(1)(2)(3)(4)(5)(7) 无 REFUTED；(6) 有一处表述被真机产物证伪 ⇒ GO-WITH-CONDITIONS。**
对象 = harness8 v2 `dd5459fe0cf3461c` + 发射器副本 `9a1a795b92eb0b10` + 判档器副本 `2df17debe8a1a731` + 卡片/设计件 v2。

- **C-R1（medium，发射动作级）** 绑帧在场性必须**双证**，否则该趟直接判「未武装、非本批样本」：
  发射命令显式带 `--extra-argv "--h7-measure-start-frame 400"`，且产物里
  `META.h7_measure_start_frame == 400` ∧ `MEASURE.h7_frame_wait` 行在场（两趟真机我已如此核验成立）。
  判档器副本仍无该断言（Y-R3）⇒ 不得改由判档器「默许」。
- **C-R2（medium）** 130 门禁余量：第 2 趟（suffix a/b）**发前先确认 harness python 的 pid 位数 ≤5**；
  若 `carrier_pathlen_gate` 以 131 打回 ⇒ 按「门禁拒发、非 harness 故障」登记，勿重复试射。
  根治转 v3（预演用真实 pid 位数，或把模板再缩 1 字符）。
- **C-R3（medium，本件唯一 REFUTED 的处置）** 删除/改写两处「≈410Hz 实测」表述：
  代码 `:5137` 达标 note 与卡片 `:40`，改为「名义 500Hz；有效节律一律按本行 `poll_count/wait_s` 折算，
  裸机 `_doze(0.002)` ≈407–411Hz，真机等待期实测 284–347Hz」。
  ⇒ 该行是**落盘留痕**，留着与同行 value 矛盾的数字会误导审计；改后 harness8 哈希变化 ⇒
  须走 C-R5 重冻结 + A11 复验，或在卡片里把 410Hz 显式标为「裸机对照值」二选一。
- **C-R4（low）** `_adjudicate_h8_offline.py` 的「无死键」判据要写明是**宽口径**（注释/note 引用计为引用点），
  或按 `_adjudicate_h7.py` C4/C12 原口径改判（`H8_FRAME_WAIT_HZ` 无代码引用、`_H8_STATE` 无读点）。
- **C-R5（程序性，沿用前任 C-0）** 冻结声明：v2 字节自本件起冻结，任何再改动 ⇒ 本件与前任判定书**作废重审**；
  发射前 A11 实得必须 = `dd5459fe0cf3461c`，母本 harness7 复验 `d019e8beecfb5fd8` 零改动（本会话均已复算）。
- **C-R6（low）** 陈旧批前清单 `LEADER_battle/frozen_recheck_h8_pre.txt`（第 6 行仍钉 v1）在发射前
  显式标注作废或改钉 v2 ⇒ 免得跑批前复验打出 MISMATCH 或被顺手改掉而丢批次身份锚。
- 其余继承项状态照旧：C-2（jump 容差 vs 真机 Δ≥3）采 (b) 预登记，本批两趟 offset=0 **未触发**；
  C-4（N<1 拒发不落盘）由台账 §488 口径覆盖；Y-R5（超时支缺 `overrun_kind`）转 v3。

**发射建议：GO-WITH-CONDITIONS**（红项 0；满足 C-R1/C-R2/C-R3/C-R5 后方可发射，C-R4/C-R6 为登记级）。

---

## 5. 程序性事实与自证（写域合规）

- **被审件在审查中换字节**：ask 钉 v1（`e29a9a07e17fdd7f`），盘上为 v2（`dd5459fe0cf3461c`，18:48:37 落盘），
  发射器 v1（`abb8b0ec…`）已被原地替换且 git 索引无副本。我按 ask 的「只核修复_delta」口径对**盘上 v2** 判定，
  并如实登记：ask 文本与盘上不符这一事实本身已被前任 C-0 + 本件 C-R5 覆盖。
- **写域**：本件、7 枚探针（`_rr_probe_*.py`）与全部 stdout/diff/夹具目录
  （`rr_out_*`、`rr_fx_*`、`rr_y7_*`、`rr_p*.txt`、`rr_h7_h8v2.diff`、`rr_launch_master_copy.diff`、
  `rr_judge_*.txt`、`rr_noreg_*.txt`）全在 `lead/codex_round_20261030/XVERIFY_H8_20261031/` 内。
- **未删除任何文件**（前任的 `synth_*` 我保持原样，另建 `rr_fx_*` 做翻转对照）。
- **未启动任何游戏/真机**；进程表为**只读枚举**，`kill_under` 走桩（`terminated` 只含合成 pid）。
- **未做 git 写操作**；未写 `ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md` / `GOAL_THREE_TARGETS_20261018.md`
  （只读引用 §479/§488）。
- **字节码自扰（如实）**：本轮所有解释器调用一律 `python -I -B -X utf8`（`sys.dont_write_bytecode=True`
  已实测为 True），且**全程未使用 `py_compile`**（改用内存 `compile`，等效语法/告警核验且零磁盘副作用）。
  我核查过 `lead/goal1_harness8_20261031/__pycache__/` 三枚 `.pyc` 的 mtime = **19:50:55**：
  该刷新**不是我**做的（我首条探针产物 `rr_p1_r1.stdout.txt` 落盘 19:20:13，其后所有调用都带 `-B`），
  而是**前任自证在案**——其判定书 §5 明文「我跑过 `python -I -B -m py_compile` 刷新了
  `lead/goal1_harness8_20261031/__pycache__/` 三枚 `.pyc`（19:50:55）」。
  我另核三枚 `.pyc` 头部 (mtime,size) 与当前 v2 源**逐项匹配**（`MATCH=True` ×3）⇒ 无陈旧字节码误载风险，
  本轮亦未在任何只读目录产生新写入。
- 只读复算了他线产物（`l3_20261031ha/hb`、`LEADER_battle/*`、`XVERIFY_H8TRIPS_20261031/_raw/*`），未改一字。
