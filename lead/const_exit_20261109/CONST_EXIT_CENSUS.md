# CONST_EXIT_CENSUS.md — 常量出口普查与 EXIT=0 零证据资格（2026-11-09）

> 本件是「常量出口成件」，写入域 `lead/const_exit_20261109/`。全部结论只判**证据资格**（哪一
> 句 `EXIT=0` 能不能当验收证据），不判被引脚本对错、不判门禁是否真的 PASS、不判 k 的具体值。
> 本件不修改任何被检脚本、不重跑任何被检门禁。

---

## 1 目的与边界

**目的**：把「脚本跑完返回 0」这件事拆成三种可达出口形态，判定其中哪些形态下 EXIT=0 零信息
（即对「k 项检查全部通过」不携带信息）；把台账与交付件里因此失格的登记行逐行列出，给出
可写进纪律的成立条件与处置清单。核心命题（判定回件 `what`）：**`EXIT=0` 是否为证据，取决
于「可达出口状态集合」是不是检查结果的函数，而不是 exit 码的数字。**

**纪律边界（本任务全程遵守）**

| 项 | 边界 | 本会话核实 |
|---|---|---|
| 零真机 | 不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，不读活进程内存 | 未启动、未读 |
| 零采样代码 | 不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入，不写动态内存解析 | 未写 |
| 绝对只读 | 两件台账、`lead/k1bit_detect_20261109/`、`lead/detect_triage_20261109/`、`lead/stale_pass_20261109/`、`lead/refsync_scope_20261109/`、`lead/goal1_a8_fix_20261022/`、`lead/d2[7890]_ruling_20261106/`、`lead/masking_effect_20261109/` 一律不修改、不追加、不覆盖 | 只读 `open(...,'rb')` / AST 静态读 |
| 唯一写域 | `lead/const_exit_20261109/`（本任务新建） | 本件 + `_cew_*` 辅助件全部落在此目录 |
| 不改被检脚本 / 不重跑被检门禁 | 本任务的运行**只限于自己的分类器**（枚举候选），不得执行被检脚本或门禁 | 只 `ast.parse` 静态读；`_kd_detect.py` 只调纯 `analyse()`，未调 `main()` |
| 版本控制 | 不 commit、不 push | 未执行 |
| Python / 指纹 | 一律 `python -I -X utf8` + 绝对路径；指纹用 `hashlib` | 见 §2、§6 |

**7 件基线指纹实跑核实**（我本会话实跑
`python -I -X utf8 -c "import hashlib,json,os ... <逐件读字节 sha256>"`，输出 7 行
`OK <basename> <bytes> <sha16>…` 与 `baselines ok: 7 / 7`）：`PENDING_DECISIONS.md`
52419/`3765eddbe96d…`、GOAL_THREE 759518/`2baa0de45d41…`、`_kd_detect_out.json`
251854/`00f77fe0d558…`、`STALE_PASS_INVENTORY.md` 63656/`a72d79b23b13…`、
`REFSYNC_SCOPE_FIX.md` 49958/`83b215ccbbf2…`、`VERIFY_A8.py` 38317/`179f3af88fac…`、
`DETECT_TRIAGE.md` 45228/`579b76ce50cd…`，**7/7 全等编排方基线**。收尾复核件
`_cev_boundary_out.json` 亦记 `n_baselines_ok: 7`、
`protected_files_modified_at_or_after_task_start: []`。

**★★ 分类器是「候选枚举」，不是判据**：编排方分类器与我的复现都只是 AST 近似。任何一件的
最终定级必须**同时给出**①编排方机械 verdict ②人工/AST 依据；两者不一致时**以依据为准并
如实并列**（§3 附录 D 逐件列 44 件）。同理，文本层「行内任一 basename 命中零信息类」只是
枚举上界，不等于「该行的 `EXIT=0` 主语就是那个 basename」（§4 用主语启发式纠正）。

---

## 2 编排方分类器与其实跑

### 2.1 规则逐条（源码 `.zcode/workflow-drafts/常量出口普查与EXIT零证据资格.dwf.ts:42-151`）

**语料与分母**
- `:47-55`：`os.walk('lead')` + `out`（深度上限 99/3），排除 `__pycache__`/`.git`，收集所有
  `.py`，同名多副本存 `idx[f]`（`:55`）。
- `:56-72`：`pat = ([A-Za-z0-9_./\-]+\.py)`；`mark = PASS|exit\s*=\s*0|EXIT=0|SELF_TEST`；
  扫 `lead/**.md`（`:59`，`dp.count(os.sep) > 5` 剪枝 `:61`），逐行（`:67`）取所有 `.py`
  basename，累计 `cited[b] = {files, n}`。
- `:107-108`：读 `lead/k1bit_detect_20261109/_kd_detect_out.json`，`census` = 173 行普查里的
  basename 集合。
- `:110-119`：`sorted(cited.items())`，**跳过 `b not in idx or b in census`**（`:111`），同名
  多副本**只判 `idx[b][0]` 第一份**（`:112`）；`ast.parse`（`:115`），失败记 `unparseable`。

**`sites(tree)`（`:73-106`）**
1. `:74`：`funcs = {x.name: x for x in ast.walk(tree) if isinstance(x, ast.FunctionDef)}`。
2. `:76-78`：**只遍历顶层语句** `for n in tree.body: for c in ast.walk(n)`，且
   `if not isinstance(c, ast.Call): continue` —— 即**完全看不见 `raise SystemExit(...)`**。
3. `:80-85`：只认两种 callee —— `sys.exit`（`ast.Attribute`，`attr=='exit'` 且
   `f.value.id=='sys'`）和裸 `exit`（`ast.Name`）；记录 `out.append((n.lineno, tag, arg))`，
   其中 **`n.lineno` 是顶层语句行，不是 Call 所在行**（`:82/:85`）。
4. `:88-89`：无参 → `('CONSTANT_EXIT', '无参数 -> 退出码 0')`。
5. `:90-91`：`ast.Constant` → `('CONSTANT_EXIT', '字面量 ' + repr(value))`。
6. `:92-101`：`arg` 是 `f()` 且 `f` 在 `funcs` → `rs = [x.value for x in ast.walk(fn)
   if isinstance(x, ast.Return)]`（`:94`，**`ast.walk(fn)` 把嵌套函数的 return 也算进 main**）；
   `kinds` 只分 `none`/`const`/`expr` 三类（`:95-99`）；**若 `not rs` 或 `kinds <=
   {'const','none'}` 就判 `CONSTANT_EXIT`**（`:100-101`）—— 0/1/2 三个可达状态被当成
   「常量」。
7. `:102-103`：否则 `CONDITIONAL_EXIT`（能认出 `return 0 if ok else 1` 这类 `IfExp`）。
8. `:104-105`：其它非字面量表达式 → `CONDITIONAL_EXIT`。

**定级（`:118`）**：`NO_EXIT_AT_ALL`（`ss` 空）/ `CONDITIONAL_EXIT`（任一 site 为
CONDITIONAL）/ `CONSTANT_EXIT`（否则）。

**`ledger_vacuous`（`:122-138`）**：只扫两件台账，逐行取所有 `.py` basename（`:126-130`），
**只要行内任一 basename 命中 `CONSTANT_EXIT`/`NO_EXIT_AT_ALL` 就记一行**（`:133-138`）——
不分辨 `EXIT=0` 的主语。

### 2.2 实跑与输出

判定回件把 `SCAN` 还原为 `lead/const_exit_20261109/_ce_repro.py`（108 行 / 5376 B），实跑
`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/const_exit_20261109/_ce_repro.py`
→ `exit=0`，stdout `{"ok": true}`（`_ce_repro_stdout.txt:1`），stderr JSON 存
`_ce_repro_stderr.json`（54914 B）。

我本会话实跑复现比对
`python -I -X utf8 -c "json.loads(repro)==orch_raw / raw.strip()==repro.strip()"` →
```
repro_stderr bytes 54913
json.loads(repro)==orch_raw ? True
raw.strip()==repro.strip() ? True
```
（唯一字节级差别是 stderr 尾部多一个 `\r\n`，54914 B vs 编排方 54912 B；去空白后相同。）
两件 `lead/gate_fp7_20261108/_g7_reverse_validate.py` / `lead/gate_n13_20261109/_n13_predicates.py` 是编排方与判定方共同产出的真实文件名在
显示层的脱敏，磁盘上确实存在，复现一致。

**编排方输出计数**（我实跑读 `_ce_orchestrator_raw.json`）：

| 项 | 值 |
|---|---|
| `n_cited_basenames` | 464 |
| `n_resolvable_out_of_census` / `n_scanned` | 413 / 413 |
| `n_unread` / `n_unparseable` | 0 / 0 |
| `classes` | `NO_EXIT_AT_ALL: 274`、`CONSTANT_EXIT: 45`、`CONDITIONAL_EXIT: 94` |
| `const_or_noexit` / `conditional` / `unparseable` | 319 / 94 / `[]` |
| `ledger_hits_total` | `PENDING_DECISIONS.md: 12`、`GOAL_THREE_TARGETS_20261018.md: 23`（合计 35，是 **basename 出现次数**，不是行数） |
| `ledger_vacuous` | 10 行（逐行见 §4） |

我另实跑 `python -I -X utf8 -c "<413 件逐件 diff>"` 复核：
`n rows 413 n orch rel 413 / n diff 44 / rel sets equal: True /
pairs {CONSTANT→CONDITIONAL:31, NO_EXIT→CONDITIONAL:9, CONDITIONAL→CONSTANT:2,
NO_EXIT→CONSTANT:2} / orch classes {NO_EXIT:274, CONSTANT:45, CONDITIONAL:94} /
final classes {NO_EXIT:263, CONDITIONAL:132, CONSTANT:18} / zero-info 413: 281 /
set(diff rel)==set(f["diffs"])? True`。

### 2.3 规则硬伤（逐条，带 file:line 依据）

统计源 `lead/const_exit_20261109/_ce_rule_audit_stdout.txt:2-9` 与
`_ce_final_stdout.txt:20-28`；合成样例见 `_ce_rule_audit_stdout.txt:13-80`。

1. **`raise SystemExit` 不算 site**（规则 `:76-78` 只遍历 `ast.Call`）。合成 `raise_only` →
   `orchestrator_sites: []`、`orchestrator_ignores_raise: true`（`_ce_rule_audit_stdout.txt:40-49`）。
   实数：`noexit_with_raise_systemexit: 11`（`:6`）、`RAISE_SYSTEMEXIT: 27`、
   `MIXED: 16`（`_ce_final_stdout.txt:25-26`）。真实例
   `lead/d28_ruling_20261106/check_d28.py:122`、`lead/qc161_u0400_trip/_probe_x_glm_addr_check.py:44`。
2. **「main 的 return 全是字面量」被当成「出口常量」**（规则 `:100-101`）。合成
   `branch_literals`（`return 0` / `return 1` 两个分支）→ `orchestrator_sites` 判
   `CONSTANT_EXIT returns=['0','1']`（`_ce_rule_audit_stdout.txt:14-22`）。实数
   `const_multi_distinct_lit_returns: 24`（`:4`），例如
   `lead/b2b_candidate_review3_20261107/_check_candidate_r3.py:272/122`、
   `lead/count_invariant_20261109/_ci_checks.py:200`、
   `lead/goal2_rc4_trigger_20261022/VERIFY_RC4_TRIPS.py:188`。反过来，判定员换一个更宽口径
   （全文件任意函数的不同字面量 return）得 25 件（`_cev_focus_stdout.txt:64-89`），与 24
   件口径不同，**并列不合并**。
3. **`return 0 if ok else 1` 这条没错**：合成 `ifexp` → `CONDITIONAL_EXIT`
   （`_ce_rule_audit_stdout.txt:27-39`），真实件
   `lead/goal1_a8_fix_20261022/VERIFY_A8B.py:451` 被判 CONDITIONAL 正确。缺陷在于它只认
   `IfExp`，认不出等价的「分支字面量」（见第 2 条）。
4. **混合文件只取 Call 那个 site**：合成 `mixed`（`raise SystemExit(2)` + `sys.exit(main())`
   且 main `return 0`）→ `orchestrator_sites` 仅 1 个、判 `CONSTANT_EXIT`
   （`_ce_rule_audit_stdout.txt:51-68`）。真实件
   `lead/matrix_ab_ruling_20261109/_ab_probe.py:23`（`raise SystemExit("path outside …")`
   ）+ `:236`（`sys.exit(1)`）：编排方 `CONSTANT_EXIT`（字面量 1），实为带错误路径的条件件。
5. **`ast.walk(fn)` 把嵌套函数 return 算进 main**（规则 `:94`）：2 件假 CONDITIONAL —
   `lead/bexec_n4_20261108/_n4_ast_scan.py:304`（main 自身仅 `:300 return 0`，`:259 return d`
   属嵌套函数 `agg_keyed`）、`lead/slowframe_round2_20261107/_proxy_covariate_accounting.py:294`
   （`:290 return 0`，`:224` 的 return 属 `in_set` / 重复函数名 `f`）。依据
   `_cev_adjudicate_stdout.txt:12-13`、`:90-91`、`_cev_focus_stdout.txt:36-63`。
6. **报告 lineno 是顶层语句行而非 Call 行**（规则 `:82/:85`）：`VERIFY_A8.py` 编排方报 799，
   实读 `lead/goal1_a8_fix_20261022/VERIFY_A8.py:799` 是 `if __name__ == "__main__":`、
   `:800` 才是 `sys.exit(main())`；统计 `const_reported_lineno_is_toplevel_not_call: 41`
   （`_ce_rule_audit_stdout.txt:3`）。

### 2.4 ★ d27–d30 生产门禁反例（核心反证）

4 件门禁都在 kd 的 173 行普查内、**根本不在 413 批里**（`_cev_ledger_stdout.txt:38-42` 记
`in_173_census True`）。**若套用编排方 `sites()` 规则**（纯 AST 推演，未执行门禁）：

| 门禁 | 编排方规则会说 | 我实读的 AST 事实 | 真实定级 |
|---|---|---|---|
| `lead/d27_ruling_20261106/check_d27.py` | `CONSTANT_EXIT sites [[104,'sys.exit','CONSTANT_EXIT','all-literal returns 3']]`（`_cev_ledger_stdout.txt:39`） | `:59 return 2`、`:99 return 1`、`:101 return 0`、`:107 sys.exit(main())` | CONDITIONAL_EXIT `[0,1,2]` |
| `lead/d28_ruling_20261106/check_d28.py` | `NO_EXIT_AT_ALL sites []`（`:40`） | `:111/114/116` 返回 `2/1/0`、`:122 raise SystemExit(main())` | CONDITIONAL_EXIT `[0,1,2]` |
| `lead/d29_ruling_20261106/check_d29.py` | `NO_EXIT_AT_ALL sites []`（`:41`） | `:101/104/106` 返回 `2/1/0`、`:110 raise SystemExit(main())` | CONDITIONAL_EXIT `[0,1,2]` |
| `lead/d30_ruling_20261106/check_d30.py` | `NO_EXIT_AT_ALL sites []`（`:42`） | `:101/104/106` 返回 `2/1/0`、`:110 raise SystemExit(main())` | CONDITIONAL_EXIT `[0,1,2]` |

我本会话实跑**自己的最小分类器**（纯 AST，未跑门禁）
`python -I -X utf8 D:/…/_ce_minimal.py <7 个绝对路径>` → `exit=0`：
```
CONSTANT_EXIT [0] VERIFY_A8.py sites@ [800]
CONDITIONAL_EXIT [0, 1] VERIFY_A8B.py sites@ [455]
CONDITIONAL_EXIT [0, 1, 2] check_d27.py sites@ [107]
CONDITIONAL_EXIT [0, 1, 2] check_d28.py sites@ [122]
CONDITIONAL_EXIT [0, 1, 2] check_d29.py sites@ [110]
CONDITIONAL_EXIT [0, 1, 2] check_d30.py sites@ [110]
CONDITIONAL_EXIT [0, 1, 2] _w_d29_A.py sites@ [110]
```
（输出存 `_cew_minimal_verify.json`。）结论：`EXIT=0` 在这 4 件上是**有信息**的 —— 0 分支
只在 `not missing and not failures` 时可达；编排方规则会把 d27 误判成常量、把 d28–d30 误判成
无出口，两种错都使「有信息的 exit=0」被误当成零信息。

---

## 3 ★ 三态定义与逐件归属

### 3.1 判据（我的最终分类器 `lead/const_exit_20261109/_ce_minimal.py:11-34`，AST 依据）

定义 `SITES` = 所有 `ast.Call`（callee 以 `exit`/`quit`/`_exit` 结尾）**＋** 所有 `ast.Raise`
（exc 为 `SystemExit(...)`）。对每个 site 解析**可达出口状态集合**：无参/`None`/数字字面量 →
`{该值}`；字符串字面量 → `{1}`；`f()` 且 `f` 是本文件 `FunctionDef` → 并集于 `f` **自身**
（排除嵌套函数）的 return 表达式，递归；数据依赖表达式（`Name`/`IfExp` 带活条件/`BoolOp`/
`Compare`/`Call` 到未知函数）→ `DATA`。若非零 site 位于条件内，补入隐式正常结束 `0`。

| 态 | 精确判据 | 可观测后果 |
|---|---|---|
| **CONSTANT_EXIT** | `SITES` 非空 ∧ 无 `DATA` ∧ 可达状态集合**恰为 1 个元素** | `EXIT` 恒为 0（或恒为某个值），与 k 项结果无关 ⇒ **`EXIT=0` 零信息**；坏针/失败都不改变出口；唯一有效证据是打印或写出的逐项摘要文本 |
| **NO_EXIT_AT_ALL** | `SITES` 为空 | 正常结束即 0 ⇒ **`EXIT=0` 零信息**，只证明「进程没崩 / 没抛未捕获异常」，不证明任何检查通过 |
| **CONDITIONAL_EXIT** | `SITES` 非空 ∧（有 `DATA` ∨ 可达状态集合 ≥2） | `EXIT=0` **有信息**，但强度取决于 (i) 0 分支是否由 k 项检查的合取驱动、(ii) 失败项是否都能到达非零分支（无 `try/except` 吞掉、无短路绕过、无异常通道顶替） |

**两套 verdict 并列**（同一 413 件，`_ce_final_stdout.txt:2-19`；我实跑逐件 diff 复现）：

| 口径 | NO_EXIT_AT_ALL | CONSTANT_EXIT | CONDITIONAL_EXIT | 零信息存量 |
|---|---|---|---|---|
| 编排方机械 verdict | 274 | 45 | 94 | 319/413 = 77.2% |
| AST 依据最终定级 | 263 | 18 | 132 | **281/413 = 68.0%** |

44 件不一致（`_ce_final_out.json:diffs`，我实跑 `n_diff 44`，逐件表见**附录 D**）：
`CONSTANT→CONDITIONAL 31`、`NO_EXIT→CONDITIONAL 9`、`CONDITIONAL→CONSTANT 2`、
`NO_EXIT→CONSTANT 2`。按缺陷形态：31 件「字面量分支实为多状态」（其中 24 件 main 有 ≥2
个不同字面量 return，另 7 件是条件内非零字面量出口 + 正常结束 0）、9 件「漏 `raise
SystemExit`」、2 件「嵌套 return 误算」、2 件「`NO_EXIT` 实有恒 0 出口」。逐件机械 verdict
＋ AST 依据全表在 `_cev_adjudicate_stdout.txt:5-93` / `_cev_adjudicate_out.json:diffs`；复核件
独立分类器 `_cev_classifier.py --batch` 得 `n_batch 413 / classes {NO_EXIT:263,
CONDITIONAL:132, CONSTANT:18}`，`_cev_compare_stdout.txt:51-55` 记
`agent-final vs mine n_diff 0`、`agree 44 disagree 0`。

### 3.2 逐件表（全量 413 件，均带 `文件:行`）

- **附录 A** — `CONSTANT_EXIT` **全部 18 件**：逐件给编排方 verdict、出口 site 的 `文件:行`、
  可达状态 `{0}`、AST 依据。我本会话实跑 `_ce_minimal.py` 对 18 件全部复验为
  `CONSTANT_EXIT [0]`（输出见本任务 `_cew_minimal_verify.json` 的同类调用，18/18 一致）。
- **附录 B** — `NO_EXIT_AT_ALL` **全部 263 件**：逐件给编排方 verdict、全文行数、`0` 个出口
  site 的 AST 事实（以「末行 `rel:N`」作 `文件:行` 锚点）、SHA256/字节数。我本会话实跑
  `_cew_evidence.py`：413 件**站点数 0 处不一致**（`n_site_count_mismatch: 0`），即归档
  `n_sites` 与我的独立 AST 枚举逐件全等。
- **附录 C** — `CONDITIONAL_EXIT` **全部 132 件**：逐件给编排方 verdict、每个出口 site 的
  `文件:行` + 表达式、可达状态集合。
- **附录 D** — 44 件不一致：机械 verdict / 最终定级 / AST 依据 / 集合，逐件并列。

代表件（其余见附录）：

- `lead/goal1_a8_fix_20261022/VERIFY_A8.py` — CONSTANT_EXIT `{0}`：`:800 sys.exit(main())`，
  `main` 自身 `:796 return 0`；`:52-55` 的 `FAILED.append(key)` 只进 `RESULTS`，`:791-795`
  只 `print`，**与 `:796` 的 `0` 无数据通路**。所以该行
  `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:7522` 的「K1–K10 全 CONFIRMED，REFUTED=0」
  有效、「EXIT=0」半句零信息。
- `lead/re_line_20261105/A1_ERRATA_MAP/_a1_g5_probe.py` — CONSTANT_EXIT `{0}`：
  `:181` 写出 `_a1_g5_probe_out.txt`、`:183` `print("PASS %d / %d")`、`:184 sys.exit(0)`。
  这是量级最大的「第五形态」：文本有信息、exit 码没有。
- `lead/qc161_u0400_trip/_probe_x_glm_addr_check.py` — CONSTANT_EXIT `{0}`（编排方误判
  `NO_EXIT_AT_ALL`）：`:40-41` 算出 `rc=1`，`:43` 打印 VERDICT，`:44
  raise SystemExit(0)  # 期望 FAIL——本件目的是记录核验，FAIL=预期结果，exit 0`。
  **判定与出口刻意解耦且反转**，是最尖锐的一件。
- `lead/d27_ruling_20261106/check_d27.py:59/99/101/107` — CONDITIONAL `[0,1,2]`（§2.4）。
- `lead/dtrigger_compare_20261107/_check_dtrigger.py:228` — CONDITIONAL：
  `raise SystemExit(0 if ok else 1)`（编排方 `NO_EXIT_AT_ALL`，漏 raise）。

### 3.3 CONDITIONAL 内部再分层：**exit 分支读的不是 k 个检查的合取**

`_ce_ortho_out.json:step2c` 对 132 件逐件 AST 归类，输出
`n_conjunction 15 / n_not_conjunction 117`，
`category_counts {SINGLE_VAR:89, BRANCHED_LITERAL:49, NONE:16, CONJUNCTION:15,
BIT_ACCUM_FOLD:7}`。**另一脚本** `_ce_final_stdout.txt:29-30` 给
`conditional_reads_conjunction: 16 / conditional_not_conjunction: 116`。判定叙述另报
「宽口径 64 件含合取语法 / 68 件不含」。三者口径不同、数字不一致，**如实并列、不合并成
一个数**；其中 64/68 我本会话**未复现**（未找到对应的归档实跑输出，记**未验**）。我自跑
一个更宽的正则（全文件源码文本搜 `all(`/`not fails`/`all_ok`/`nfail==0`/`ok&=`/`ok else`
等）得 107/25 —— 这是**另一口径**（扫全文而非仅出口表达式），不是 64/68 的复现，仅作
边界提示，不据此下结论。

**合取代表（0 分支确由 k 项合取驱动，`文件:行` 已实读）**
- `lead/c07_protocol_attacks_20261109/_pat_fp_verify.py:68` `return 0 if (all(results) and rb) else 1`
- `lead/count_invariant_20261109/_ci_counterexamples.py:152` `sys.exit(0 if all(RESULTS.values()) else 1)`
- `lead/direction_ruling_20261108/_verify_hy4.py:118` `sys.exit(0 if all_ok else 1)`
- `lead/control_20261106/gate_n1_lf_20261107.py:150/:370` `raise SystemExit(0 if not fails else 1)`

**非合取代表（虽 CONDITIONAL，仍不是 k 的度量，`文件:行` 已实读）**
- `lead/b2b_candidate_20261106/tests/test_candidate.py:659` `return 0 if result.wasSuccessful() else 1`
  —— 单一标量，k 项已被 `unittest` 吞成一个 `wasSuccessful()`。
- `lead/b2b_isolated_20261107/_integ_probe_isolated.py:303` `sys.exit(0 if nfail == 0 else 1)`
  —— 单计数器，不是逐项归因。
- `lead/c07_gate_fix_20261109/_g1g5_fp.py:79` `0 if n_ok == len(EXPECT) and s_ok == len(files) else 1`
  —— 计数==k 型，静态上不能证明每个失败项都可达非零分支。
- `lead/b2b_design_20261106/_draft_semantics_check.py:633`
  `raise SystemExit("usage: build | verify | matrix | anchors")` —— 只是用法错误通道，
  不读检查结果。
- `lead/matrix_ab_ruling_20261109/_ab_probe.py:23` 只判路径是否越界，不是「内容对不对」。

`BRANCHED_LITERAL 49` 件是 15 与 64 两个数的差：main 有 0/1/2 分支字面量，分支条件读检查
列表但静态上无法证明是 k 路合取。以上计数均为**语法近似上界，未做数据流证明（未验）**。

### 3.4 第五形态与稀有通道（我本会话实跑 AST 探针）

`_ce_final_stdout.txt:20-28` 的 flag 计数（我在 `_ce_final_out.json:rows` 上独立重算一致）：
`FILE_OR_STDOUT_ONLY_VERDICT 191`、`IMPLICIT_EXCEPTION_CHANNEL 56`、`ASSERT 75`、
`VERDICT_VIA_ASSERT_ONLY 54`、`RAISE_SYSTEMEXIT 27`、`MIXED 16`、`BARE_RAISE 8`。
191 件「检查结果只写进文件/stdout 不回传出口」是量级最大的第五形态 —— 它与
`NO_EXIT_AT_ALL` 语义不同：**文本有信息、exit 码没有**。

我本会话实跑 `python -I -X utf8 -c "<AST 枚举 413 件>"`：
`atexit.register: 0 / os._exit: 0 / quit(): 0 / __del__: 0 / if True 包裹 exit: 0`。
`assert-only` 通道 54 件、未捕获异常顶替 56 件**未逐件定级（未验）**；「exit 依赖 subprocess
returncode / 环境变量 / 读文件内容」形态在 `_ce_ortho.py` 的 EXTERNAL 类可见（如
`qc151_trip.candidate.py` 的 `_main_wrapper`），**未量化（未验）**。4 件含 `atexit` 字样的
文件只是散文（如 `lead/goal2_onetime_census_20261022/_atexit_verdict.py:19`），非注册调用。

---

## 4 ★ 影响面：台账逐行清单、交付件量级、成立条件

### 4.1 两件台账逐行（全 24 行见**附录 E**）

我本会话实跑 `_cew_evidence.py`：`ledgers {n_marked:24, n_flat_final:10, n_flat_orch:10,
n_subject_vac:5}`，与 `_ce_impact_stdout.txt:3-6` 的 `ledger_n_lines 24 /
ledger_orch_vac 10 / ledger_final_vac_flat 10 / ledger_subject_vac 5` 一致；复核件
`_cev_ledger2_stdout.txt` 亦记 `raw_marked_lines 135 / raw_basename_occurrences 35 /
marked_lines_with_py 24`，确证编排方 `ledger_hits_total 12+23=35` 是 **basename 出现次数
而非行数**。

**编排方 `ledger_vacuous` 10 行（逐行复现，`_ce_orchestrator_raw.json`）**

| # | 台账:行 | 编排方挂的 basename | 编排方类 | 我实读原文的主语 | 判定 |
|---|---|---|---|---|---|
| 1 | `lead/PENDING_DECISIONS.md:92` | `_d30_facts.py` | NO_EXIT_AT_ALL | 「门禁 `check_d30.py` 实跑 **exit=0**（2026-11-07 复跑仍 PASS）」 | **归错对象** |
| 2 | `lead/PENDING_DECISIONS.md:105` | `_d29_facts.py` | NO_EXIT_AT_ALL | 「门禁 `check_d29.py` 实跑 **exit=0**」 | **归错对象** |
| 3 | `lead/PENDING_DECISIONS.md:117` | `_d28_facts.py` | NO_EXIT_AT_ALL | 「门禁 `check_d28.py` 实跑 **exit=0**」 | **归错对象** |
| 4 | `lead/PENDING_DECISIONS.md:129` | `_d27_facts.py` | NO_EXIT_AT_ALL | 「门禁 `check_d27.py` 实跑 **exit=0**」 | **归错对象** |
| 5 | `lead/PENDING_DECISIONS.md:162` | `_d26_facts.py` | NO_EXIT_AT_ALL | 「门禁 `check_d26.py` 实跑 **exit=0**」 | **归错对象** |
| 6 | `lead/GOAL_THREE_TARGETS_20261018.md:7569` | `_d21_burden5.py` | NO_EXIT_AT_ALL | `python -I -X utf8 ".../D21_RULING/_d21_burden5.py"  # EXIT=0` | **真零信息** |
| 7 | `lead/GOAL_THREE_TARGETS_20261018.md:7634` | `_leader_crossframe_check.py` | NO_EXIT_AT_ALL | 「交付：… + `_out.txt`（`EXIT=0`）。零真机。」 | **真零信息** |
| 8 | `lead/GOAL_THREE_TARGETS_20261018.md:8383` | `_a7_acf_probe.py` | NO_EXIT_AT_ALL | 「`_leader/_a7_acf_probe.py` + `…_out.txt`（均 `EXIT=0`）」 | **真零信息** |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md:9588` | `_intra_frame_census.py` | NO_EXIT_AT_ALL | 「探针 `_leader/_intra_frame_census.py`，输出 `…_out.txt`（`EXIT=0`）」 | **真零信息** |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md:9679` | `_intra_frame_census.py` | NO_EXIT_AT_ALL | 「**我亲跑**：`_intra_frame_census.py` 全量 15 窗，`EXIT=0`，输出 40+ 行表格」 | **真零信息** |

**5 行归错对象**：`PENDING_DECISIONS.md:92/105/117/129/162` 的 `exit=0` 主语是门禁
`check_d30/29/28/27/26.py`，不是并列的 `_dXX_facts.py`。我实读门禁源：
`check_d27.py:59/99/101/107`、`check_d28.py:111/114/116/122`、
`check_d29.py:101/104/106/110`、`check_d30.py:101/104/106/110` 全为
`CONDITIONAL_EXIT [0,1,2]`；复核件另验 `check_d26.py:111 sys.exit(main())`、
`check_d25.py:84 raise SystemExit(main())` 亦 CONDITIONAL（`_cev_ledger_stdout.txt:13-18`、
`_cev_focus_stdout.txt:1-21` 覆盖 d27–d30）。`_dXX_facts.py` 经 AST 实跑 `sites=[]`
（`_ce_table_out.json:noexit`，如 `lead/d30_ruling_20261106/_d30_facts.py`），**本身确实零
信息，但不是那句 exit=0 的主语**。编排方按「行内任一 basename 命中零信息类」映射，把
exit=0 挂错了对象。

**真正落在零信息类上的台账登记行 = 5 行，全部 NO_EXIT_AT_ALL，全部在
GOAL_THREE_TARGETS_20261018.md**（上表 #6–#10，逐行原文已实读）。`CONSTANT_EXIT` 在两件
台账里 **0 行**（复核件 `_cev_ledger_stdout.txt:2`：`n_constant_flat 0 /
n_constant_subject 0`；`_cev_ledger2_stdout.txt` 全文搜 18 个 CONSTANT basename 分组为空）。
`VERIFY_A8.py` 的 `EXIT=0` 登记在 `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:7522` 与
`lead/goal1_a8_fix_20261022/A8_IMPL_SELF_REPORT.md:135`，**不在两件台账**。

其余：`PENDING_DECISIONS.md:186` 的 `_d25_facts.py` 有 `sys.exit(status)`（`:209`），确为
CONDITIONAL，编排方未列入是对的；`GOAL_THREE_TARGETS_20261018.md:9406` 原文只写
「`test_except_freshness.py` 的 **14/14 PASS**」，**无显式 `EXIT=0` token、主语判不出
（未验）**；`GOAL_THREE:260/261/7196/7197/7258/7401/7404/7446/7566-7568/9220` 主语均为
CONDITIONAL 或 UNRESOLVED（`_cev_ledger_stdout.txt:19-36` 逐行类）。

### 4.2 交付件 `.md` 量级 —— 三套数字如实并列

| 口径 | .md 数 | 标记行 | 扁平零信息 | 主语零信息 | 文件数 |
|---|---|---|---|---|---|
| 编排方扁平（含台账） | — | 1512 | 746 | — | — |
| `_ce_impact_stdout.txt:2-11`（判定实跑，含台账） | 1103 | 1512 | 664（最终） | 268 | 212 |
| 判定叙述 / `_ce_binding_object.json`（**排除两件台账**） | 1103 | 1492 | **656** | **263** | 211 / 125 |
| 我本会话实跑 `_cew_evidence.py`（含台账，见 `_cew_evidence_stdout.txt`） | **1528** | **1968** | 829（最终）/ 911（编排方） | 429 | 268 / 181 |
| 我本会话实跑（排除两件台账） | 1528 | 1944 | 819 / 901 | 424 | 266 / 180 |

**必须如实说明的口径冲突**：
- `_ce_binding_object.json` 与判定叙述给 `n_deliverable_flat_vacuous 656`、
  `n_deliverable_subject_vacuous 263`（211 / 125 个文件、1492 行）；但归档脚本
  `_ce_impact.py:162-175` 实跑 stdout 给 `deliverable_final_vac_flat 664`、
  `deliverable_subject_vac 268`、`deliverable_files_with_vac 212`。**656/263/211/125 与
  664/268/212 不能同时对**，我在本会话遍查 `lead/const_exit_20261109/` 的 `.py/.md/.txt`
  未找到产出 656/263 的归档实跑输出，判定回件自述是「一次扫描」但**其确切命令与输出未
  归档** ⇒ 这两组数**未验**，不得择一当作唯一结论。
- 我自跑得到 1528 个 `.md`、1968 个标记行，与判定时的 1103 / 1512 不同：复核件
  `_cev_stock_out.json:method2_current_corpus` 亦记 `n_cited 481 / n_resolvable 447 /
  zero_information 284`，并明确「430 在今天恰好变成『仅普查外』的件数，与判定员『全库
  430』同名不同义」—— 这是**语料快照漂移**（今日新增 `lead/andk_rerun_20261109/`、
  `lead/const_exit_20261109/` 相关交付件等），不是算错。因此**所有文本层计数都是快照依赖的
  枚举上界**，且 `mark` 正则与「最近 basename 主语」启发式未逐行人工核。
- 三套数**全部是上界**：它们按「行内任一 basename 命中零信息类」或「最近 basename 启发式」
  计数，不等于逐行人工确认的「该行 `EXIT=0` 半句失格」。

代表加注行（原文已实读）：`lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:7522`
（VERIFY_A8.py，CONSTANT_EXIT，「**EXIT=0，K1–K10 全 CONFIRMED，REFUTED=0**」）、
`lead/goal1_a8_fix_20261022/A8_IMPL_SELF_REPORT.md:135`、
`lead/advset_indep_20261109/ADVSET_INDEPENDENCE.md:40-42`
（`_ai2_selfcheck.py` / `_ai2_selfcheck2.py` / `_ai2_baseline.py`，均 NO_EXIT_AT_ALL）、
`lead/stale_pass_20261109/STALE_PASS_INVENTORY.md`（`_ce_impact_out.json:by_file` 记 22 行）、
`lead/chain_vs_single_20261109/CHAIN_VS_SINGLE.md`（15 行）。

### 4.3 「EXIT=0 可作验收证据」的成立条件（当且仅当同时满足）

1. **出口非常量**：被引脚本存在显式出口 site，且可达出口状态集合 ≥2 或出口表达式数据依赖
   （即非 `CONSTANT_EXIT`、非 `NO_EXIT_AT_ALL`）。
2. **合取驱动**：0 分支由 k 项检查的合取或 `计数 == k` 驱动，且任一失败项都能到达非零分支
   （无 `try/except` 吞掉、无短路绕过、无异常通道顶替）。§3.3 显示 132 件 CONDITIONAL 里
   严格合取只有 15（或 16）件。
3. **摘要绑定**：同一次运行有打印/写出的逐项摘要与 `EXIT=0` 绑定（同命令、同 stdout、同
   文件）。
4. **指纹绑定**：脚本 `SHA256 + 字节数` 绑定、未被改动（本件 §1 的 7/7 基线即此类）。
5. **主语绑定**：登记行里 `EXIT=0` 的主语确实是该被引脚本，而不是同行并列的另一个
   basename（§4.1 的 5 行归错对象就是反例）。

否则 `EXIT=0` 只等于「进程没崩」，不得作为验收证据；此时有效证据**只有打印/写出的摘要
文本**（`VERIFY_A8.py` 那行「K1–K10 全 CONFIRMED，REFUTED=0」有效、「EXIT=0」无效）。

> **建议纪律措辞**：只登记同时满足「出口非常量 ∧ 合取驱动 ∧ 摘要绑定 ∧ 指纹绑定 ∧ 主语
> 绑定」的 `EXIT=0`；否则登记摘要文本，不登记 exit 码。
> **建议加注措辞**：「注（常量出口普查 2026-11-09）：本行 `EXIT=0` 半句零信息 —— 被引脚本
> `<basename>` 经 AST 判定为 `<类>`，可达出口状态集合 = `{0}`，与检查结果无关；本行有效
> 证据仅为所引打印/写出摘要 `<stdout/文件名>`。验收须改用打印逐项摘要 + 非零退出并重跑。
> 本注仅为证据资格说明，不代表脚本被改动或门禁被重跑。」

---

## 5 与 k→1bit 家族的关系（正交）

### 5.1 有损映射 vs 零敏感映射

| | k→1bit（`any()` 塌缩） | 常量出口（本件） |
|---|---|---|
| 通道带宽 | k 个输入 → 1 bit | k 个输入 → **出口 0 bit** |
| 丢了什么 | 保留 1 bit、丢失逐输入归因 | 出口对 k 个输入**完全不敏感** |
| 坏针能否被 EXIT 抓到 | 表现为「坏针仍 PASS」；抓到它靠负控/归因探针，**不是 EXIT 本身** | **连坏针都抓不到** —— 坏针本来不改变出口 |

判编排方看法：**基本对，需一处精确化**。二者同族（都是「k 个输入的联合有效性未被完整
观测」），常量出口是更退化的极限（1 bit → 0 bit）。但**常量出口不等于「k 个输入根本没被
观测」**：`lead/goal1_a8_fix_20261022/VERIFY_A8.py:52-55` 仍算出 `FAILED`、`:791-795` 仍
打印逐项结果，内部 1 bit 判定存在且有效；零信息的是**出口通道**，不是检查结果本身。正确
表述是「k 个输入 → 出口 0 bit」，而不是「k 个输入 → 0 bit」。

### 5.2 检测器能否抓到：**verdict 与出口常量正交**（但不能说「完全不共享语法证据」）

- 源码层：`lead/k1bit_detect_20261109/_kd_detect.py:479-487` 的 verdict 分支只读
  `legal / onebit_exit / has_k / accum / real_collapse / attribution`；我复核
  `_cev_ortho_out.json:exit_token_hits` 对 `sys.exit|SystemExit|CONSTANT_EXIT|attainable|
  exit_status|exit_code|returncode` 全库搜索 → `{}`，即**没有任何出口常量概念**。
- 交叉表（`_cev_ortho_out.json:cross_tab`，173 行 kd 全库 × 出口类）：
  `CONFIRMED_K1BIT {CONDITIONAL_EXIT:40}`、`LEGAL_AGGREGATE {NO_EXIT:57, CONDITIONAL:20,
  CONSTANT:3}`、`NO_SELFTEST {NO_EXIT:47}`、`SUSPECT {CONDITIONAL:5, NO_EXIT:1}`。CONFIRMED
  全为 CONDITIONAL，而 CONSTANT 落在 LEGAL_AGGREGATE ⇒ **两个方向都不是函数关系**。
- 双向反例（`_cev_ortho2_out.json:focus_rows`，复核件用纯 `analyse()`，未调 `main()`、未跑
  门禁）：4/4 均 `CONFIRMED_K1BIT`，而出口类分别是
  `VERIFY_A8.py=CONSTANT_EXIT [0]`、`_rs_carrier_scan.py=CONDITIONAL [0,1]`、
  `_me_auditcheck.py=NO_EXIT_AT_ALL []`、`_w_d29_A.py=CONDITIONAL [0,1,2]`。
  `VERIFY_A8.py` 同时是 `CONFIRMED_K1BIT, onebit=[{line:796, expr:'0'}], n_accum=11`
  与 `CONSTANT_EXIT, sts=[0]`（`_ce_kd_a8_out.json`）。
- **★ 一处精确化（复核件新发现）**：`_kd_detect.py:443-445` 的正则
  `^\s*[01]\s*$|ok\s+else` 会把**任何**裸 `return 0` 收进 `onebit`，从不问这个 0 是否
  数据依赖。所以「信号层」并非完全解耦 —— 检测器的 onebit 信号恰好由同一条字面量
  `return 0` 触发。正确表述是「**verdict 不是出口常量性的函数，且三个检测器
  （`_kd_detect.py` / `_cf_detect.py` / 字面筛）都不能判常量出口**」，而不是「两个维度互不
  共享任何语法证据」。`_cf_detect.py:117-124` 只把字面量 `return 0` 收进 `exits` 并算
  P1–P4，对 A8 判 `NOT_FAMILY`（`_ce_ortho_out.json:step4b_orthogonality` 记
  `cf_verdict: NOT_FAMILY, cf_flags {P1:true,P2:true,P3:false,P4:false}`、
  `literal_filters {has_literal_return0:true, has_exit0:false, has_pass_print:false}`）。

### 5.3 最小 AST 判据（可粘贴，全文 `lead/const_exit_20261109/_ce_minimal.py:11-34`）

```
Let SITES = all ast.Call nodes whose callee ends in `exit`/`quit`/`_exit`,
            PLUS all ast.Raise nodes whose exc is SystemExit(...).
For each site, resolve its status argument to a SET of attainable statuses:
  - no arg / None / numeric literal           -> {that status}
  - f() where f is a local FunctionDef        -> union over f's OWN
    `return` expressions (excluding nested functions), recursively
  - a data-dependent expression (Name / IfExp with live test / BoolOp /
    BinOp / Compare / Attribute / Subscript / Call to unknown fn)
                                             -> DATA
  - a literal str                            -> {1} (SystemExit(str) => 1)
Add 0 to the attainable set if a nonzero exit site sits inside a conditional
(there is an implicit normal-termination path).

CONSTANT_EXIT  <=>  SITES is non-empty AND no site is DATA AND
                    the attainable status set has exactly one member.
NO_EXIT_AT_ALL <=>  SITES is empty.
CONDITIONAL_EXIT <=> otherwise.
```
可执行实现见 `_ce_minimal.py:45-147`（`own_returns` 排除嵌套函数 `:54-62`、
`statuses` 常量传播 `:70-103`、`classify` `:106-147`）。我本会话实跑 7 件结果见 §2.4；
另实跑 18 件 CONSTANT 全量复验 18/18 `CONSTANT_EXIT [0]`。与编排方规则的差别
（`_ce_minimal.py:31-34`）：编排方只认 `sys.exit`/`exit` Calls、把「main 的 return 全是
字面量」当 CONSTANT、把嵌套函数 return 算进 main、完全忽略 `raise SystemExit`。

---

## 6 复核回件、结论、处置清单、未验项

### 6.1 复核回件（绑定行格式固定）

被核对象 SHA256 = 6c032bd5c59dcf61e80146ebfa2d9a8603f898eebcbed45719e8c4270c8be332，字节数 = 362

- 被核对象 = `lead/const_exit_20261109/_ce_binding_object.json`（数字摘要的紧凑 JSON，
  362 B）。我本会话实跑
  `python -I -X utf8 -c "import hashlib; b=open('D:/…/_ce_binding_object.json','rb').read(); print(hashlib.sha256(b).hexdigest(), len(b))"`
  → `6c032bd5c59dcf61e80146ebfa2d9a8603f898eebcbed45719e8c4270c8be332 / 362`，
  与判定回件、复核回件给定的 `sha256Line` 逐字一致。
- **复核 verdict = `confirmed`**（如实记；非 `refuted` / `partial`，故**不标 unconfirmed**），
  `ranCommands 61`。复核件自写 `_cev_classifier.py`（未复用 `_ce_repro.py` / `_ce_final.py`
  判据），`--batch` 严格按 413 个 rel 分类 → `{NO_EXIT:263, CONDITIONAL:132, CONSTANT:18}`；
  `_cev_compare_stdout.txt:5` 记 `orchestrator vs mine n_diff 44` 且
  `Counter` 四组与判定逐项相同、`:52-55` 记 `agent-final vs mine n_diff 0`、
  `agree 44 disagree 0`，18 件 CONSTANT 清单排序后完全相等。
- 复核六项点名：①7 件基线 7/7 全等；②独立分类器逐件复现 44 件误判（A 31 件字面量分支
  / B 9 件漏 raise / C 2 件漏 raise 的恒 0 / D 2 件嵌套 return / E 混合形态）；
  ③4 件门禁在 173 普查内、编排方规则会误判而最终定级不会；④台账 24 行逐行、
  `CONSTANT_EXIT` 0 行、5 行归错对象、5 行真零信息；⑤正交性双向反例 + 一处精确化
  （`_kd_detect.py:443-445`）；⑥越界检查 `baselines ok: 7 / 7`、
  `non-_cev_ prefixed files: []`、`protected_files_modified_at_or_after_task_start: []`，
  保护目录 5 个 `__pycache__` 全部早于本会话、脚本均设 `sys.dont_write_bytecode = True`。
- **★ 复核自身指出的精确化 / 风险（不改 confirmed 总判）**：4 件「被引
  CONFIRMED_K1BIT」**不在** `_kd_detect_out.json` 的 173 行里（归档只覆盖
  `_ce_kd_a8_out.json` 的 VERIFY_A8 与 `DETECT_TRIAGE.md:190` 的 `_rs_carrier_scan`；
  `_me_auditcheck.py` / `_w_d29_A.py` 无归档 `--one` 实跑输出，**来源未验**）；
  `283/430` 是**快照依赖**（当前语料重扫 `n_cited 481 / n_resolvable 447 /
  zero_information 284`）；交付件量级与 2(c) 合取子类「本复核未重算，记未验」；归档的
  编排方分类器输出复核**未独立重跑**（只读 `_ce_orchestrator_raw.json`）。

### 6.2 结论：存量数字

我本会话实跑 `python -I -X utf8 -c "<413 件逐件计数>"` 与复核件 `_cev_stock_out.json`：
`method1_archived_413 {n:413, classes {NO_EXIT:263, CONDITIONAL:132, CONSTANT:18},
zero_information:281}`、`method3_agent_430_set {n:430, zero_information:283,
zero_information_413:281, n_agent_vs_my_mismatch:0}`。

| 口径 | 分母 | 零信息存量 | 说明 |
|---|---|---|---|
| **最终定级（413 批，主口径）** | 413 | **281 = 263 NO_EXIT + 18 CONSTANT** | **281/413 = 68.0%** |
| 全库可解析被引脚本 | 430 | **283 = 265 NO_EXIT + 18 CONSTANT** | 283/430 = 65.8%（`_ce_ortho_stdout.txt:3-15`；快照依赖，见 §6.1） |
| 编排方机械口径 | 413 | 319 = 274 + 45 | 319/413 = 77.2%，**高估 38 件** |

分母口径：464 个被引 basename 中 430 个可解析到真实 `.py`（34 个是片段/不存在），
17 个在 kd 的 173 普查内、413 个在普查外；同名多副本只判 `idx[b][0]` 第一份。

### 6.3 处置清单（**我不执行，只列给 Leader**）

**(b) 必须加注的行**
1. 两件台账 **5 行真零信息**：`GOAL_THREE_TARGETS_20261018.md:7569 / 7634 / 8383 / 9588 /
   9679`（全部 NO_EXIT_AT_ALL）。
2. 两件台账 **5 行归错对象需澄清**：`PENDING_DECISIONS.md:92 / 105 / 117 / 129 / 162`
   —— 加注「本行 exit=0 主语是 CONDITIONAL 门禁 `check_dXX.py`，不是 `_dXX_facts.py`；
   该句 exit=0 不是零信息」。这 5 行不是零信息，但编排方 `ledger_vacuous` 列错，必须澄清。
3. `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:7522` 与
   `lead/goal1_a8_fix_20261022/A8_IMPL_SELF_REPORT.md:135`（VERIFY_A8.py，CONSTANT_EXIT，
   「EXIT=0」半句零信息；保留同行的逐项摘要作为有效证据）。
4. 交付件主语级零信息登记行（判定口径 263 行 / `_ce_impact.py` 口径 268 行 / 我本会话
   429 行含台账，均为**上界**，需逐行人工核后按 §4.3 措辞加注）。

**(c) 只需「下次重跑时换成打印摘要 + 非零退出」而不必回溯的**
- 191 件 `FILE_OR_STDOUT_ONLY_VERDICT` 探针/复算脚本：证据本来就是 `.txt/.json` 文本内容，
  交付件登记的也是文本而非 exit 码。
- 263 件 `NO_EXIT_AT_ALL` 中**未被任何验收行点名**的件。
- 132 件 CONDITIONAL 的「非合取」子类：下次重跑把 `raise SystemExit(0 if ok else 1)`
  升级为逐项打印 + 0/1 退出。
- **但凡已写进台账/交付件作为验收结论的 `EXIT=0` 行（上面 (b)3+(b)4），不能只靠下次
  重跑，必须加注**。

**(d) 这条工作判不了什么**
零真机（未启动游戏/加载器、未读活进程内存，运行期证据缺）；未重跑任何被检脚本/门禁
（背景「4 件门禁实跑 PASS exit=0」是编排方陈述，我只验 AST 分支，**未验实跑**）；分类器是
候选枚举（同名 basename 只判第一份副本、34 个 basename 无法解析 464→430）；可达状态集合
是保守静态近似，未做路径敏感/别名/跨模块分析，未处理 `try/except` 吞掉 `SystemExit`、
装饰器、动态 `exec`、信号/`atexit`、子进程 returncode 转发，54 件 assert-only 通道未逐件
定级；台账/交付件的「EXIT=0 半句 vs 摘要」切分用「最近 basename」启发式，1512/1968 行未
逐行人工核，656/664/829、263/268/429 都是上界；未判打印摘要是否真实/是否同一次运行
（属 `stale_pass` / 指纹绑定范畴）；未判 k 的具体值与 k 项是否真的执行、未判 kd 的
`CONFIRMED_K1BIT` 是否正确；CONDITIONAL 合取子类 15/16/64 三个数是语法近似、未做数据流
证明。

**纪律核实收尾**：全程未改被检脚本、未重跑被检门禁、7 件基线零漂移、不 commit/push；
本任务产出仅 `lead/const_exit_20261109/CONST_EXIT_CENSUS.md` 与 `_cew_*` 辅助件（我的
分类器 `_cew_evidence.py` 为纯 AST/文本枚举，未执行任何被检脚本）。

### 6.4 未验项（逐条，不补造）

1. **656 / 263 / 211 文件 / 125 文件 / 1492 行**：判定叙述与 `_ce_binding_object.json`
   给出的交付件口径，与归档 `_ce_impact_stdout.txt` 的 664 / 268 / 212 冲突；产出 656/263
   的确切命令与输出未在 `lead/const_exit_20261109/` 归档，**本会话未复现 ⇒ 未验**。
2. **64 / 68 宽口径合取子类**：判定叙述自述「一次宽口径正则复算」，归档无对应输出；
   `_ce_ortho_out.json:step2c` 只给 15/117、`_ce_final_stdout.txt` 只给 16/116；我自跑的
   107/25 是另一口径、不是复现。**未验**。
3. **真机 / 实跑**：零真机；4 件 d27–d30 门禁「实跑 PASS exit=0」是编排方背景陈述
   （`.zcode/workflow-drafts/常量出口普查与EXIT零证据资格.dwf.ts:211` 附近），我只验 AST
   分支，**未验实跑**；所有被引脚本/门禁均未重跑。
4. **归档编排方分类器输出**：本会话只比对判定方 `_ce_repro.py` 的复现产物
   `_ce_repro_stderr.json` 与 `_ce_orchestrator_raw.json`（`json.loads` 相等、`strip` 相等），
   **未独立重跑 `_ce_repro.py`**；复核件亦明示此项未验。
5. **4 件「被引 CONFIRMED_K1BIT」的来源**：`_me_auditcheck.py` / `_w_d29_A.py` 全库 grep
   未找到编排方或判定方的归档 `--one` 实跑输出，**来源未验**（复核件只用纯 `analyse()`
   得到 4/4 CONFIRMED_K1BIT，实质结论仍成立）。
6. **静态近似边界**：路径敏感/别名/跨模块分析未做；未处理 `try/except` 吞 SystemExit、
   `atexit`、装饰器、动态 `exec`、信号、subprocess returncode 转发；`NO_EXIT_AT_ALL` 不排除
   未捕获异常通道（54 件 assert-only 未逐件定级）。
7. **主语启发式**：`EXIT=0` 主语取「exit token 前最近的 .py basename」，1512（判定快照）/
   1968（本会话快照）行未逐行人工核；`GOAL_THREE_TARGETS_20261018.md:9406` 无显式
   `EXIT=0` token，主语判不出，**未验**。
8. **语料快照**：1103 → 1528 个 `.md`、430 → 447 可解析、281 → 284 零信息（复核件
   `_cev_stock_out.json:method2`）；一切文本层与「全库」计数都是快照依赖，本件已并列，
   不合并。
9. **摘要真伪 / 同一次运行绑定**：未判（属 `stale_pass` / 指纹绑定范畴）。

---

## 附录：逐件归属全表（413 件，每类逐件给 `文件:行` 依据）

> 生成源：我本会话实跑 `_cew_evidence.py`（纯 AST，`n_site_count_mismatch: 0`，413 件站点数与归档逐件全等）、`_ce_final_out.json:rows`、`_ce_orchestrator_raw.json`、`_ce_table_out.json`。列「编排方」= 机械 verdict；「最终」= AST 依据定级。两者不一致以依据为准，并在附录 D 并列。SHA256/字节数来自归档 `rows`（我实跑读取源文件字节），逐件 64 位指纹全量在 `_ce_final_out.json:rows` / `_ce_table_out.json`。

> **`lead/gate_fp7_20261108/_g7_reverse_validate.py` / `lead/gate_n13_20261109/_n13_predicates.py`** 为编排方与判定方共同产出的真实文件名在显示层的脱敏占位符（按铁律原样抄写），对应磁盘上确实存在的两件 .py。

### 附录 A — CONSTANT_EXIT 全部 18 件

判据：`SITES` 非空、无 DATA、可达状态集合恰为 `{0}`。我本会话实跑 `_ce_minimal.py` 对 18 件全部复验 `CONSTANT_EXIT [0]`。

| # | rel | 编排方 | 最终 | 出口 site `文件:行` + AST 事实 | 可达状态 | 末行锚 |
|---|---|---|---|---|---|---|
| 1 | `lead/bexec_n4_20261108/_n4_ast_scan.py` | CONDITIONAL_EXIT | **CONSTANT_EXIT** | `lead/bexec_n4_20261108/_n4_ast_scan.py:304` `main()`；`main` 自身 return `:300` `0` | `{0}` | `lead/bexec_n4_20261108/_n4_ast_scan.py:305`（全文 305 行） |
| 2 | `lead/c07_protocol_attacks_20261109/_pa_a3_mech1.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/c07_protocol_attacks_20261109/_pa_a3_mech1.py:23` `0` | `{0}` | `lead/c07_protocol_attacks_20261109/_pa_a3_mech1.py:24`（全文 24 行） |
| 3 | `lead/c07_protocol_attacks_20261109/_pa_a3_mech2.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/c07_protocol_attacks_20261109/_pa_a3_mech2.py:19` `0` | `{0}` | `lead/c07_protocol_attacks_20261109/_pa_a3_mech2.py:20`（全文 20 行） |
| 4 | `lead/c07_protocol_attacks_20261109/_pa_a4_mech.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/c07_protocol_attacks_20261109/_pa_a4_mech.py:39` `0` | `{0}` | `lead/c07_protocol_attacks_20261109/_pa_a4_mech.py:40`（全文 40 行） |
| 5 | `lead/c07_protocol_attacks_20261109/_pav_a3_mech.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/c07_protocol_attacks_20261109/_pav_a3_mech.py:23` `0` | `{0}` | `lead/c07_protocol_attacks_20261109/_pav_a3_mech.py:24`（全文 24 行） |
| 6 | `lead/check_masking_20261109/_cm_inject.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/check_masking_20261109/_cm_inject.py:219` `main()`；`main` 自身 return `:215` `0` | `{0}` | `lead/check_masking_20261109/_cm_inject.py:220`（全文 220 行） |
| 7 | `lead/check_masking_20261109/_cmv_repro.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/check_masking_20261109/_cmv_repro.py:162` `main()`；`main` 自身 return （无 return，隐式 0） | `{0}` | `lead/check_masking_20261109/_cmv_repro.py:163`（全文 163 行） |
| 8 | `lead/check_masking_20261109/_cmv_template_3way.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/check_masking_20261109/_cmv_template_3way.py:109` `main()`；`main` 自身 return `:105` `0` | `{0}` | `lead/check_masking_20261109/_cmv_template_3way.py:110`（全文 110 行） |
| 9 | `lead/comparability_20261109/_cmp_assert.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/comparability_20261109/_cmp_assert.py:250` `main()`；`main` 自身 return `:246` `0` | `{0}` | `lead/comparability_20261109/_cmp_assert.py:251`（全文 251 行） |
| 10 | `lead/gate_n13_20261109/_n13v_final_probe.py` | NO_EXIT_AT_ALL | **CONSTANT_EXIT** | `lead/gate_n13_20261109/_n13v_final_probe.py:126` `main()`；`main` 自身 return `:122` `0` | `{0}` | `lead/gate_n13_20261109/_n13v_final_probe.py:127`（全文 127 行） |
| 11 | `lead/goal1_a8_fix_20261022/VERIFY_A8.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/goal1_a8_fix_20261022/VERIFY_A8.py:800` `main()`；`main` 自身 return `:796` `0` | `{0}` | `lead/goal1_a8_fix_20261022/VERIFY_A8.py:801`（全文 801 行） |
| 12 | `lead/qc161_u0400_trip/_probe_x_glm_addr_check.py` | NO_EXIT_AT_ALL | **CONSTANT_EXIT** | `lead/qc161_u0400_trip/_probe_x_glm_addr_check.py:44` `0` | `{0}` | `lead/qc161_u0400_trip/_probe_x_glm_addr_check.py:45`（全文 45 行） |
| 13 | `lead/re_line_20261105/A1_ERRATA_MAP/_a1_g5_probe.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/re_line_20261105/A1_ERRATA_MAP/_a1_g5_probe.py:184` `0` | `{0}` | `lead/re_line_20261105/A1_ERRATA_MAP/_a1_g5_probe.py:185`（全文 185 行） |
| 14 | `lead/re_line_20261105/A1_ERRATA_MAP/reviews/_g5_probe_reverify.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/re_line_20261105/A1_ERRATA_MAP/reviews/_g5_probe_reverify.py:184` `0` | `{0}` | `lead/re_line_20261105/A1_ERRATA_MAP/reviews/_g5_probe_reverify.py:185`（全文 185 行） |
| 15 | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t2_mtime_probe.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t2_mtime_probe.py:113` `0` | `{0}` | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/_w11_t2_mtime_probe.py:114`（全文 114 行） |
| 16 | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/reviews/_reviewer_t2_rerun_mtime_probe.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/reviews/_reviewer_t2_rerun_mtime_probe.py:113` `0` | `{0}` | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/reviews/_reviewer_t2_rerun_mtime_probe.py:114`（全文 114 行） |
| 17 | `lead/samedoc_link_20261109/_slw_hashes.py` | CONSTANT_EXIT | **CONSTANT_EXIT** | `lead/samedoc_link_20261109/_slw_hashes.py:125` `main()`；`main` 自身 return （无 return，隐式 0） | `{0}` | `lead/samedoc_link_20261109/_slw_hashes.py:126`（全文 126 行） |
| 18 | `lead/slowframe_round2_20261107/_proxy_covariate_accounting.py` | CONDITIONAL_EXIT | **CONSTANT_EXIT** | `lead/slowframe_round2_20261107/_proxy_covariate_accounting.py:294` `main()`；`main` 自身 return `:290` `0` | `{0}` | `lead/slowframe_round2_20261107/_proxy_covariate_accounting.py:295`（全文 295 行） |

要点：`VERIFY_A8.py:52-55` 的 `FAILED.append` 与 `:796 return 0` 无数据通路；`_probe_x_glm_addr_check.py:40-41` 算出 `rc=1` 但 `:44` 仍 `raise SystemExit(0)`；`_n4_ast_scan.py` / `_proxy_covariate_accounting.py` 两件编排方误判 CONDITIONAL（嵌套函数 return 被 `ast.walk(fn)` 算进 main）。

### 附录 B — NO_EXIT_AT_ALL 全部 263 件

判据：`SITES` 为空；正常结束即 0。逐件给「全文末行 `文件:行`」作锚点 + 我实跑 AST 确认 `n_sites = 0`（与归档 `n_sites` 逐件相等）。`EXIT=0` 只证明进程没崩 / 没抛 未捕获异常。

| # | rel | 编排方 | 最终 | AST 依据（`文件:行`，0 个出口 site） | SHA256[:12] / B |
|---|---|---|---|---|---|
| 1 | `lead/a_dim_reduced_20261108/_verify_hy4_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/a_dim_reduced_20261108/_verify_hy4_recompute.py:473`（全文 473 行，`n_sites=0`） | `ab83d60687fb` / 19739 |
| 2 | `lead/advset_indep_20261109/_ai2_baseline.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/advset_indep_20261109/_ai2_baseline.py:182`（全文 182 行，`n_sites=0`） | `4f0737d7ed0d` / 8224 |
| 3 | `lead/advset_indep_20261109/_ai2_selfcheck.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/advset_indep_20261109/_ai2_selfcheck.py:88`（全文 88 行，`n_sites=0`） | `9833bfd96105` / 4325 |
| 4 | `lead/advset_indep_20261109/_ai2_selfcheck2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/advset_indep_20261109/_ai2_selfcheck2.py:52`（全文 52 行，`n_sites=0`） | `b20fc14614a6` / 2533 |
| 5 | `lead/advset_indep_20261109/_ai_grade.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/advset_indep_20261109/_ai_grade.py:287`（全文 287 行，`n_sites=0`） | `ee791c1a032d` / 17821 |
| 6 | `lead/advset_indep_20261109/_ai_invariants.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/advset_indep_20261109/_ai_invariants.py:192`（全文 192 行，`n_sites=0`） | `569edaa46f36` / 13522 |
| 7 | `lead/advset_indep_20261109/_ai_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/advset_indep_20261109/_ai_verify.py:639`（全文 639 行，`n_sites=0`） | `7a8da35f076c` / 33183 |
| 8 | `lead/b2_preaudit_20261106/_b2_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/b2_preaudit_20261106/_b2_probe.py:293`（全文 293 行，`n_sites=0`） | `5894d64410bd` / 16100 |
| 9 | `lead/b2b_candidate_review3_20261107/_review_probe_r3.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/b2b_candidate_review3_20261107/_review_probe_r3.py:690`（全文 690 行，`n_sites=0`） | `71743cfd400b` / 32214 |
| 10 | `lead/bexec_n4_20261108/_n4_fingerprint.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/bexec_n4_20261108/_n4_fingerprint.py:19`（全文 19 行，`n_sites=0`） | `bf6944ca00ff` / 800 |
| 11 | `lead/c07_protocol_attacks_20261109/_pa_a9_nfkc_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/c07_protocol_attacks_20261109/_pa_a9_nfkc_probe.py:35`（全文 35 行，`n_sites=0`） | `f1e020e92372` / 1668 |
| 12 | `lead/c97_scope_recheck_20261108/_c97_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/c97_scope_recheck_20261108/_c97_check.py:206`（全文 206 行，`n_sites=0`） | `059aba6218c1` / 10698 |
| 13 | `lead/c97_scope_recheck_20261108/_verify_ast.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/c97_scope_recheck_20261108/_verify_ast.py:74`（全文 74 行，`n_sites=0`） | `bc682f9da698` / 3993 |
| 14 | `lead/c97_scope_recheck_20261108/_verify_counts.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/c97_scope_recheck_20261108/_verify_counts.py:118`（全文 118 行，`n_sites=0`） | `bb5c4b28d586` / 5422 |
| 15 | `lead/cert_realcheck_20261109/_cr_build_seal.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/cert_realcheck_20261109/_cr_build_seal.py:116`（全文 116 行，`n_sites=0`） | `2e539d392b0a` / 5376 |
| 16 | `lead/cert_realcheck_20261109/_cr_real_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/cert_realcheck_20261109/_cr_real_verify.py:466`（全文 466 行，`n_sites=0`） | `3d8ab1092ebf` / 21178 |
| 17 | `lead/cert_realcheck_20261109/_crdoc_colocated.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/cert_realcheck_20261109/_crdoc_colocated.py:96`（全文 96 行，`n_sites=0`） | `b94e452623a8` / 4009 |
| 18 | `lead/cert_realcheck_20261109/_crdoc_pasted.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/cert_realcheck_20261109/_crdoc_pasted.py:149`（全文 149 行，`n_sites=0`） | `bbea935f46af` / 7558 |
| 19 | `lead/cert_realcheck_20261109/_crdoc_run.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/cert_realcheck_20261109/_crdoc_run.py:536`（全文 536 行，`n_sites=0`） | `561e2a0e68e3` / 24931 |
| 20 | `lead/cert_realcheck_20261109/_crv_holes.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/cert_realcheck_20261109/_crv_holes.py:228`（全文 228 行，`n_sites=0`） | `01a687ffa872` / 10054 |
| 21 | `lead/cert_realcheck_20261109/_crv_pasted.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/cert_realcheck_20261109/_crv_pasted.py:155`（全文 155 行，`n_sites=0`） | `fbb091ea52e2` / 8156 |
| 22 | `lead/cert_realcheck_20261109/_crv_real_tests.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/cert_realcheck_20261109/_crv_real_tests.py:266`（全文 266 行，`n_sites=0`） | `156cd527f0fb` / 11178 |
| 23 | `lead/chain_vs_single_20261109/_cs_align.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/chain_vs_single_20261109/_cs_align.py:197`（全文 197 行，`n_sites=0`） | `6925c0060de3` / 11195 |
| 24 | `lead/chain_vs_single_20261109/_cs_attrib.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/chain_vs_single_20261109/_cs_attrib.py:154`（全文 154 行，`n_sites=0`） | `5c7856641e36` / 9134 |
| 25 | `lead/chain_vs_single_20261109/_cs_info.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/chain_vs_single_20261109/_cs_info.py:66`（全文 66 行，`n_sites=0`） | `b1c51eaac3b9` / 3499 |
| 26 | `lead/chain_vs_single_20261109/_csv_align.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/chain_vs_single_20261109/_csv_align.py:156`（全文 156 行，`n_sites=0`） | `b6fd76432a31` / 7650 |
| 27 | `lead/chain_vs_single_20261109/_csv_attrib.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/chain_vs_single_20261109/_csv_attrib.py:146`（全文 146 行，`n_sites=0`） | `93b6ad16340d` / 8710 |
| 28 | `lead/chain_vs_single_20261109/_csv_consistency.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/chain_vs_single_20261109/_csv_consistency.py:107`（全文 107 行，`n_sites=0`） | `33105b1979b5` / 6132 |
| 29 | `lead/chain_vs_single_20261109/_csv_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/chain_vs_single_20261109/_csv_recompute.py:151`（全文 151 行，`n_sites=0`） | `59f454c73f65` / 7901 |
| 30 | `lead/check_family_20261109/_cf_census.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/check_family_20261109/_cf_census.py:207`（全文 207 行，`n_sites=0`） | `72eb7c58e115` / 10980 |
| 31 | `lead/check_family_20261109/_cf_compose_lineage.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/check_family_20261109/_cf_compose_lineage.py:415`（全文 415 行，`n_sites=0`） | `8ccac7c6158c` / 45320 |
| 32 | `lead/check_family_20261109/_cf_detect.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/check_family_20261109/_cf_detect.py:165`（全文 165 行，`n_sites=0`） | `832355993a2b` / 7587 |
| 33 | `lead/check_family_20261109/_cfv_census.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/check_family_20261109/_cfv_census.py:297`（全文 297 行，`n_sites=0`） | `12763ec84446` / 12133 |
| 34 | `lead/check_fp_audit_20261109/_cfaa_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/check_fp_audit_20261109/_cfaa_verify.py:648`（全文 648 行，`n_sites=0`） | `b13e258337a8` / 30370 |
| 35 | `lead/check_fp_audit_20261109/_cfav_probe2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/check_fp_audit_20261109/_cfav_probe2.py:350`（全文 350 行，`n_sites=0`） | `5a68def84d6e` / 16662 |
| 36 | `lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s04_windows.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/codex_round_20261030/XVERIFY_TRIPS_20261030/_xv_s04_windows.py:82`（全文 82 行，`n_sites=0`） | `b6e349a535bf` / 4241 |
| 37 | `lead/count_invariant_20261109/_civ_lib.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/count_invariant_20261109/_civ_lib.py:148`（全文 148 行，`n_sites=0`） | `ffa3bcba10ac` / 7334 |
| 38 | `lead/counterpart_fix_20261109/_cf_enum_counterpart.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/counterpart_fix_20261109/_cf_enum_counterpart.py:401`（全文 401 行，`n_sites=0`） | `1c8d2da34c3a` / 17880 |
| 39 | `lead/counterpart_fix_20261109/_cfv_enum.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/counterpart_fix_20261109/_cfv_enum.py:296`（全文 296 行，`n_sites=0`） | `52d3350e2c14` / 13430 |
| 40 | `lead/d13b_design_20261106/_state_machine.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d13b_design_20261106/_state_machine.py:416`（全文 416 行，`n_sites=0`） | `b1ff8c671675` / 23834 |
| 41 | `lead/d13b_design_20261106/_test_state_machine.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d13b_design_20261106/_test_state_machine.py:274`（全文 274 行，`n_sites=0`） | `d7fb6f55c07d` / 14509 |
| 42 | `lead/d14_dual_20261107/_dual_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d14_dual_20261107/_dual_recompute.py:451`（全文 451 行，`n_sites=0`） | `697a9cf9b4d6` / 20965 |
| 43 | `lead/d14_dual_20261107/_dual_xcheck_scipy.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d14_dual_20261107/_dual_xcheck_scipy.py:145`（全文 145 行，`n_sites=0`） | `bc86acaeb120` / 5372 |
| 44 | `lead/d14_dual_20261107/_verify_independent.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d14_dual_20261107/_verify_independent.py:257`（全文 257 行，`n_sites=0`） | `a985b065185f` / 10753 |
| 45 | `lead/d26_ruling_20261106/_d26_facts.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d26_ruling_20261106/_d26_facts.py:124`（全文 124 行，`n_sites=0`） | `8a40105409bc` / 6040 |
| 46 | `lead/d27_ruling_20261106/_d27_facts.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d27_ruling_20261106/_d27_facts.py:109`（全文 109 行，`n_sites=0`） | `da1b6019c4bc` / 7669 |
| 47 | `lead/d28_ruling_20261106/_d28_facts.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d28_ruling_20261106/_d28_facts.py:98`（全文 98 行，`n_sites=0`） | `798c31cd458d` / 6087 |
| 48 | `lead/d29_ruling_20261106/_d29_facts.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d29_ruling_20261106/_d29_facts.py:82`（全文 82 行，`n_sites=0`） | `724672a25c52` / 4845 |
| 49 | `lead/d30_ruling_20261106/_d30_facts.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d30_ruling_20261106/_d30_facts.py:144`（全文 144 行，`n_sites=0`） | `95b7ca614639` / 8431 |
| 50 | `lead/d_o1o4_necessity_20261108/_d14_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/d_o1o4_necessity_20261108/_d14_recompute.py:132`（全文 132 行，`n_sites=0`） | `95c0434b4fbe` / 6248 |
| 51 | `lead/deliverable_anchor_20261108/_da_fp_inventory.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/deliverable_anchor_20261108/_da_fp_inventory.py:43`（全文 43 行，`n_sites=0`） | `e4518f2578f9` / 1277 |
| 52 | `lead/deliverable_anchor_20261108/_spec2_fp_all.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/deliverable_anchor_20261108/_spec2_fp_all.py:129`（全文 129 行，`n_sites=0`） | `f8869a486b89` / 4074 |
| 53 | `lead/detect_triage_20261109/_dt_leak.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/detect_triage_20261109/_dt_leak.py:84`（全文 84 行，`n_sites=0`） | `6c591d4f81ba` / 3529 |
| 54 | `lead/detect_triage_20261109/_dt_repro.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/detect_triage_20261109/_dt_repro.py:188`（全文 188 行，`n_sites=0`） | `b2464b3a4563` / 9189 |
| 55 | `lead/dg_adversarial_20261109/_dgaw_extra.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dg_adversarial_20261109/_dgaw_extra.py:72`（全文 72 行，`n_sites=0`） | `320490b5a8fb` / 3371 |
| 56 | `lead/dg_adversarial_20261109/_dgaw_regress.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dg_adversarial_20261109/_dgaw_regress.py:191`（全文 191 行，`n_sites=0`） | `e15e4ec5c57f` / 7342 |
| 57 | `lead/dg_adversarial_20261109/_dgaw_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dg_adversarial_20261109/_dgaw_verify.py:352`（全文 352 行，`n_sites=0`） | `66e12ff52358` / 18269 |
| 58 | `lead/dneg_generative_20261109/_dg_core.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dneg_generative_20261109/_dg_core.py:211`（全文 211 行，`n_sites=0`） | `7a8074ef8d85` / 12322 |
| 59 | `lead/dneg_generative_20261109/_dg_step34.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dneg_generative_20261109/_dg_step34.py:288`（全文 288 行，`n_sites=0`） | `ee4f6db3177a` / 15771 |
| 60 | `lead/dneg_generative_20261109/_dgv_chain.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dneg_generative_20261109/_dgv_chain.py:180`（全文 180 行，`n_sites=0`） | `d68fd844589c` / 8830 |
| 61 | `lead/dneg_generative_20261109/_dgv_neg2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dneg_generative_20261109/_dgv_neg2.py:150`（全文 150 行，`n_sites=0`） | `33de02bdad41` / 8891 |
| 62 | `lead/dtrigger_round2_20261107/_dB_anchor_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dtrigger_round2_20261107/_dB_anchor_recompute.py:524`（全文 524 行，`n_sites=0`） | `44b10371cdc2` / 27324 |
| 63 | `lead/dtrigger_round2_20261107/_dC_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dtrigger_round2_20261107/_dC_recompute.py:430`（全文 430 行，`n_sites=0`） | `ec64adac558e` / 23115 |
| 64 | `lead/dtrigger_round2_20261107/_verify_A_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dtrigger_round2_20261107/_verify_A_recompute.py:758`（全文 758 行，`n_sites=0`） | `5d906aa00069` / 36794 |
| 65 | `lead/dtrigger_round2_20261107/_verify_B_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/dtrigger_round2_20261107/_verify_B_recompute.py:337`（全文 337 行，`n_sites=0`） | `11246dce64d5` / 14966 |
| 66 | `lead/early_trigger_feasibility_20261106/_feasibility_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/early_trigger_feasibility_20261106/_feasibility_probe.py:689`（全文 689 行，`n_sites=0`） | `1e37ea992e4f` / 31026 |
| 67 | `lead/evidence_indep_20261109/_ei_05_admission.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/evidence_indep_20261109/_ei_05_admission.py:320`（全文 320 行，`n_sites=0`） | `146598620ced` / 17184 |
| 68 | `lead/evidence_indep_20261109/_ei_07_final.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/evidence_indep_20261109/_ei_07_final.py:107`（全文 107 行，`n_sites=0`） | `92cda814199b` / 5397 |
| 69 | `lead/evidence_indep_20261109/_ei_n13_predicates_src.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/evidence_indep_20261109/_ei_n13_predicates_src.py:346`（全文 346 行，`n_sites=0`） | `e1195b3b220a` / 16649 |
| 70 | `lead/evidence_indep_20261109/_eind_manifest.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/evidence_indep_20261109/_eind_manifest.py:46`（全文 46 行，`n_sites=0`） | `b1894972bd72` / 1755 |
| 71 | `lead/evidence_indep_20261109/_eind_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/evidence_indep_20261109/_eind_verify.py:381`（全文 381 行，`n_sites=0`） | `ba0d4317e3a5` / 20760 |
| 72 | `lead/falsifiable_no_relax_20261109/_fnr_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/falsifiable_no_relax_20261109/_fnr_check.py:555`（全文 555 行，`n_sites=0`） | `94d89881f6a2` / 28811 |
| 73 | `lead/falsifiable_no_relax_20261109/_fnr_replay.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/falsifiable_no_relax_20261109/_fnr_replay.py:301`（全文 301 行，`n_sites=0`） | `2c1d12645a46` / 14675 |
| 74 | `lead/falsifiable_no_relax_20261109/_fnrd_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/falsifiable_no_relax_20261109/_fnrd_verify.py:195`（全文 195 行，`n_sites=0`） | `0c233aa3b87e` / 8937 |
| 75 | `lead/falsifiable_no_relax_20261109/_fnrv_replay.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/falsifiable_no_relax_20261109/_fnrv_replay.py:118`（全文 118 行，`n_sites=0`） | `8f24cd7532ed` / 6887 |
| 76 | `lead/fp_pattern_20261109/_fp_classify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/fp_pattern_20261109/_fp_classify.py:124`（全文 124 行，`n_sites=0`） | `7c962bd91aee` / 6782 |
| 77 | `lead/fp_pattern_20261109/_fp_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/fp_pattern_20261109/_fp_recompute.py:367`（全文 367 行，`n_sites=0`） | `e26717d523af` / 20315 |
| 78 | `lead/gate_doc_name_fix_20261109/_dn_regate_domains.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_doc_name_fix_20261109/_dn_regate_domains.py:174`（全文 174 行，`n_sites=0`） | `ffa9ce4d757b` / 6761 |
| 79 | `lead/gate_doc_name_fix_20261109/_dn_sandbox_run.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_doc_name_fix_20261109/_dn_sandbox_run.py:36`（全文 36 行，`n_sites=0`） | `b7c3d148b9f7` / 1601 |
| 80 | `lead/gate_doc_name_fix_20261109/_dnw_s1s4.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_doc_name_fix_20261109/_dnw_s1s4.py:124`（全文 124 行，`n_sites=0`） | `876c6b2a19e0` / 5885 |
| 81 | `lead/gate_fp7_20261108/_g7_predicates.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_fp7_20261108/_g7_predicates.py:223`（全文 223 行，`n_sites=0`） | `02c17e49764a` / 11743 |
| 82 | `lead/gate_fp7_20261108/_g7_reverse_validate.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_fp7_20261108/_g7_reverse_validate.py:178`（全文 178 行，`n_sites=0`） | `353866f40d6b` / 10468 |
| 83 | `lead/gate_n13_20261109/_n13_predicates.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_n13_20261109/_n13_predicates.py:346`（全文 346 行，`n_sites=0`） | `e1195b3b220a` / 16649 |
| 84 | `lead/gate_pipeline_20261109/_gp_compose_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_pipeline_20261109/_gp_compose_check.py:157`（全文 157 行，`n_sites=0`） | `d8c8a93f00c6` / 7780 |
| 85 | `lead/gate_pipeline_20261109/_gp_pipeline.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_pipeline_20261109/_gp_pipeline.py:278`（全文 278 行，`n_sites=0`） | `25c7753f097b` / 15811 |
| 86 | `lead/gate_pipeline_20261109/_gp_regression.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_pipeline_20261109/_gp_regression.py:247`（全文 247 行，`n_sites=0`） | `1804e5bfb4c3` / 13017 |
| 87 | `lead/gate_pipeline_20261109/_gpv_regress.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_pipeline_20261109/_gpv_regress.py:102`（全文 102 行，`n_sites=0`） | `595b84334de4` / 5337 |
| 88 | `lead/gate_r9sem_20261109/_r9s_predicates.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_r9sem_20261109/_r9s_predicates.py:459`（全文 459 行，`n_sites=0`） | `b0265fc57ef4` / 23111 |
| 89 | `lead/gate_r9sem_20261109/_r9s_samples.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_r9sem_20261109/_r9s_samples.py:199`（全文 199 行，`n_sites=0`） | `5c103ddfa2c1` / 17721 |
| 90 | `lead/gate_r9sem_20261109/_r9sd_final_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_r9sem_20261109/_r9sd_final_verify.py:376`（全文 376 行，`n_sites=0`） | `1b424450adf3` / 17986 |
| 91 | `lead/gate_rejudge32_20261109/_rj_delivery_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_rejudge32_20261109/_rj_delivery_verify.py:229`（全文 229 行，`n_sites=0`） | `1a63ec1bce52` / 10743 |
| 92 | `lead/gate_rejudge32_20261109/_rj_double_track.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_rejudge32_20261109/_rj_double_track.py:134`（全文 134 行，`n_sites=0`） | `ed39cc556b93` / 5761 |
| 93 | `lead/gate_subject_id_20261109/_si_gate_self_extracted.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_subject_id_20261109/_si_gate_self_extracted.py:23`（全文 23 行，`n_sites=0`） | `83a81c084e1f` / 1402 |
| 94 | `lead/gate_v1v2_20261109/_v12_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_v1v2_20261109/_v12_probe.py:104`（全文 104 行，`n_sites=0`） | `36dd1de81b34` / 4560 |
| 95 | `lead/gate_v1v2_20261109/_v12_rule.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_v1v2_20261109/_v12_rule.py:171`（全文 171 行，`n_sites=0`） | `15e4211ffe83` / 9148 |
| 96 | `lead/gate_v1v2_20261109/_v12_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_v1v2_20261109/_v12_verify.py:260`（全文 260 行，`n_sites=0`） | `b8901523e3f1` / 18134 |
| 97 | `lead/gate_v1v2_20261109/_v12v_fair.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_v1v2_20261109/_v12v_fair.py:111`（全文 111 行，`n_sites=0`） | `eac15bacc0be` / 6179 |
| 98 | `lead/gate_v1v2_20261109/_v12w_fpcheck.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_v1v2_20261109/_v12w_fpcheck.py:74`（全文 74 行，`n_sites=0`） | `86e489557d2e` / 3609 |
| 99 | `lead/gate_validate_20261108/_gv_gates/858e5e0b.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_validate_20261108/_gv_gates/858e5e0b.py:14`（全文 14 行，`n_sites=0`） | `7999fcf00312` / 827 |
| 100 | `lead/gate_validate_20261108/_gv_replay_original.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_validate_20261108/_gv_replay_original.py:58`（全文 58 行，`n_sites=0`） | `5bb9255896c2` / 2374 |
| 101 | `lead/gate_validate_20261108/_gv_run_fixtures.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/gate_validate_20261108/_gv_run_fixtures.py:71`（全文 71 行，`n_sites=0`） | `d23e6b31af4e` / 4090 |
| 102 | `lead/goal3t_nightwatch_20261102/_xbatch_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/_xbatch_verify.py:329`（全文 329 行，`n_sites=0`） | `206cbbaed070` / 12735 |
| 103 | `lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/night_10cf63f5/ex3_screenshot_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/night_10cf63f5/ex3_screenshot_check.py:65`（全文 65 行，`n_sites=0`） | `34f8333dee10` / 2997 |
| 104 | `lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/night_10cf63f5/r1_check_47windows.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/night_10cf63f5/r1_check_47windows.py:121`（全文 121 行，`n_sites=0`） | `83a9be9ae6a7` / 7166 |
| 105 | `lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/night_10cf63f5/recheck_addon_4s_v4c.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/night_10cf63f5/recheck_addon_4s_v4c.py:31`（全文 31 行，`n_sites=0`） | `0d69603bc14d` / 1633 |
| 106 | `lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/night_10cf63f5/recount_eight.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/ADJUDICATE_a70d00e5/night_10cf63f5/recount_eight.py:126`（全文 126 行，`n_sites=0`） | `220889832886` / 6258 |
| 107 | `lead/goal3t_nightwatch_20261102/swarm_20261104/P04/VERIFY_data.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/P04/VERIFY_data.py:267`（全文 267 行，`n_sites=0`） | `3b00aa855643` / 11995 |
| 108 | `lead/goal3t_nightwatch_20261102/swarm_20261104/P04/VERIFY_mech.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/P04/VERIFY_mech.py:62`（全文 62 行，`n_sites=0`） | `bde01d53cd21` / 2846 |
| 109 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/probe_e4_t42.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S543_0a451d0b/V2/probe_e4_t42.py:92`（全文 92 行，`n_sites=0`） | `1f2a0c9eac97` / 3691 |
| 110 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V3/v3_census.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/V3/v3_census.py:128`（全文 128 行，`n_sites=0`） | `e95e42dc4aec` / 5396 |
| 111 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/_verdict_final.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/_verdict_final.py:132`（全文 132 行，`n_sites=0`） | `5cf3eb9318e9` / 7576 |
| 112 | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/_verdict_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/XVERIFY_S544_c1606d35/_verdict_recompute.py:195`（全文 195 行，`n_sites=0`） | `ce1db4b7dbc8` / 10575 |
| 113 | `lead/goal3t_nightwatch_20261102/swarm_20261104/_leader_slow_decomp2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/goal3t_nightwatch_20261102/swarm_20261104/_leader_slow_decomp2.py:132`（全文 132 行，`n_sites=0`） | `9ae483586c06` / 4850 |
| 114 | `lead/h5_governance_20261109/_h5_pasteable.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/h5_governance_20261109/_h5_pasteable.py:174`（全文 174 行，`n_sites=0`） | `b5ba0a6a06a5` / 8540 |
| 115 | `lead/h5_governance_20261109/_h5v_core.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/h5_governance_20261109/_h5v_core.py:214`（全文 214 行，`n_sites=0`） | `739e2e4f7cff` / 11336 |
| 116 | `lead/h5_governance_20261109/_h5v_extra.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/h5_governance_20261109/_h5v_extra.py:131`（全文 131 行，`n_sites=0`） | `14ba4e964919` / 5818 |
| 117 | `lead/h5_governance_20261109/_h5v_final.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/h5_governance_20261109/_h5v_final.py:130`（全文 130 行，`n_sites=0`） | `cacdf240c989` / 6359 |
| 118 | `lead/h5_governance_20261109/_h5v_full.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/h5_governance_20261109/_h5v_full.py:221`（全文 221 行，`n_sites=0`） | `2da2a61c9545` / 12360 |
| 119 | `lead/handoff_pack_20261109/_hp_ap_checks.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/handoff_pack_20261109/_hp_ap_checks.py:188`（全文 188 行，`n_sites=0`） | `5b131062059b` / 12945 |
| 120 | `lead/handoff_pack_20261109/_hp_fp_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/handoff_pack_20261109/_hp_fp_verify.py:52`（全文 52 行，`n_sites=0`） | `95e870d39a1a` / 3156 |
| 121 | `lead/k1bit_detect_20261109/_kd_detect.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/k1bit_detect_20261109/_kd_detect.py:531`（全文 531 行，`n_sites=0`） | `42d8ff33cc19` / 24378 |
| 122 | `lead/k1bit_detect_20261109/_kdv_quant.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/k1bit_detect_20261109/_kdv_quant.py:124`（全文 124 行，`n_sites=0`） | `a125759c7327` / 5522 |
| 123 | `lead/k1bit_detect_20261109/_kdv_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/k1bit_detect_20261109/_kdv_verify.py:135`（全文 135 行，`n_sites=0`） | `2867099cb359` / 6193 |
| 124 | `lead/keff_calc_20261109/_ke_calc.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/keff_calc_20261109/_ke_calc.py:647`（全文 647 行，`n_sites=0`） | `9c0669343e4b` / 47757 |
| 125 | `lead/layer_identity_20261109/_liv_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/layer_identity_20261109/_liv_verify.py:131`（全文 131 行，`n_sites=0`） | `3790dd11bad6` / 5274 |
| 126 | `lead/ledger_appendix_20261108/_la_d14_recompute_copy.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/ledger_appendix_20261108/_la_d14_recompute_copy.py:132`（全文 132 行，`n_sites=0`） | `32cccfe5d531` / 6250 |
| 127 | `lead/ledger_appendix_20261108/_la_r3_recompute_copy.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/ledger_appendix_20261108/_la_r3_recompute_copy.py:229`（全文 229 行，`n_sites=0`） | `834697251ac5` / 12665 |
| 128 | `lead/masking_effect_20261109/_me_auditcheck.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/masking_effect_20261109/_me_auditcheck.py:220`（全文 220 行，`n_sites=0`） | `8220de3ba67b` / 10527 |
| 129 | `lead/masking_effect_20261109/_me_auditcheck_search.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/masking_effect_20261109/_me_auditcheck_search.py:118`（全文 118 行，`n_sites=0`） | `f20546f0cfd2` / 4951 |
| 130 | `lead/masking_effect_20261109/_me_design.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/masking_effect_20261109/_me_design.py:204`（全文 204 行，`n_sites=0`） | `b62253fedd01` / 9711 |
| 131 | `lead/masking_effect_20261109/_me_repro.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/masking_effect_20261109/_me_repro.py:55`（全文 55 行，`n_sites=0`） | `4a2e9c7eb5a9` / 2440 |
| 132 | `lead/masking_effect_20261109/_mev_final.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/masking_effect_20261109/_mev_final.py:96`（全文 96 行，`n_sites=0`） | `975462373017` / 5482 |
| 133 | `lead/masking_effect_20261109/_mev_step5.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/masking_effect_20261109/_mev_step5.py:163`（全文 163 行，`n_sites=0`） | `cde440810267` / 7542 |
| 134 | `lead/matrix_row5_20261109/_r5_probe_import.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/matrix_row5_20261109/_r5_probe_import.py:99`（全文 99 行，`n_sites=0`） | `476c2e199a13` / 5578 |
| 135 | `lead/merged_consumer_audit_20261109/_mc_count.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_consumer_audit_20261109/_mc_count.py:116`（全文 116 行，`n_sites=0`） | `2a26fd08b762` / 5204 |
| 136 | `lead/merged_consumer_audit_20261109/_mc_crosscheck.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_consumer_audit_20261109/_mc_crosscheck.py:76`（全文 76 行，`n_sites=0`） | `0108da5ac014` / 3256 |
| 137 | `lead/merged_consumer_audit_20261109/_mc_detail.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_consumer_audit_20261109/_mc_detail.py:128`（全文 128 行，`n_sites=0`） | `e6e60effc54d` / 5187 |
| 138 | `lead/merged_consumer_audit_20261109/_mc_empirical.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_consumer_audit_20261109/_mc_empirical.py:144`（全文 144 行，`n_sites=0`） | `363bb229a769` / 5768 |
| 139 | `lead/merged_consumer_audit_20261109/_mc_scan.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_consumer_audit_20261109/_mc_scan.py:135`（全文 135 行，`n_sites=0`） | `139f6afa08d3` / 6283 |
| 140 | `lead/merged_consumer_audit_20261109/_mcf_scan.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_consumer_audit_20261109/_mcf_scan.py:118`（全文 118 行，`n_sites=0`） | `bbfa389ee231` / 5345 |
| 141 | `lead/merged_consumer_audit_20261109/_mcv_empirical.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_consumer_audit_20261109/_mcv_empirical.py:150`（全文 150 行，`n_sites=0`） | `024cec7f5fed` / 5087 |
| 142 | `lead/merged_contract_20261109/_mk_build_candidate.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_contract_20261109/_mk_build_candidate.py:129`（全文 129 行，`n_sites=0`） | `b97708719b14` / 6330 |
| 143 | `lead/merged_contract_20261109/_mk_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_contract_20261109/_mk_probe.py:169`（全文 169 行，`n_sites=0`） | `27d17352e1d9` / 8695 |
| 144 | `lead/merged_contract_20261109/_mk_project.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_contract_20261109/_mk_project.py:111`（全文 111 行，`n_sites=0`） | `933c89b9a1c2` / 5533 |
| 145 | `lead/merged_safety_20261109/_ms_counterexample.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_safety_20261109/_ms_counterexample.py:115`（全文 115 行，`n_sites=0`） | `1175c6b3abd9` / 5123 |
| 146 | `lead/merged_safety_20261109/_ms_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_safety_20261109/_ms_probe.py:539`（全文 539 行，`n_sites=0`） | `03fafd606377` / 25283 |
| 147 | `lead/merged_safety_20261109/_ms_regress.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_safety_20261109/_ms_regress.py:82`（全文 82 行，`n_sites=0`） | `272d10818866` / 2775 |
| 148 | `lead/merged_safety_20261109/_ms_tight.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_safety_20261109/_ms_tight.py:235`（全文 235 行，`n_sites=0`） | `60dc39bbb358` / 11120 |
| 149 | `lead/merged_safety_20261109/_ms_v9_candidate.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_safety_20261109/_ms_v9_candidate.py:60`（全文 60 行，`n_sites=0`） | `fa66843908e1` / 3051 |
| 150 | `lead/merged_safety_20261109/_ms_v9_candidate_v2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/merged_safety_20261109/_ms_v9_candidate_v2.py:49`（全文 49 行，`n_sites=0`） | `90e8092f6d7c` / 2279 |
| 151 | `lead/metric_audit_20261109/_ma_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/metric_audit_20261109/_ma_verify.py:181`（全文 181 行，`n_sites=0`） | `146184354cbc` / 9387 |
| 152 | `lead/minhard_check_20261109/_mhz_blocks2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/minhard_check_20261109/_mhz_blocks2.py:156`（全文 156 行，`n_sites=0`） | `33b725200fd5` / 7889 |
| 153 | `lead/minhard_check_20261109/_mhz_lines2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/minhard_check_20261109/_mhz_lines2.py:37`（全文 37 行，`n_sites=0`） | `96d28574c8b6` / 1454 |
| 154 | `lead/minhard_check_20261109/_mhz_slice.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/minhard_check_20261109/_mhz_slice.py:42`（全文 42 行，`n_sites=0`） | `398a2bb95458` / 1914 |
| 155 | `lead/minhard_check_20261109/_mhz_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/minhard_check_20261109/_mhz_verify.py:187`（全文 187 行，`n_sites=0`） | `0bb406fc842f` / 10208 |
| 156 | `lead/n10c04_ruling_20261108/_ro_fp_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/n10c04_ruling_20261108/_ro_fp_check.py:72`（全文 72 行，`n_sites=0`） | `a1ed3d8a9e63` / 4138 |
| 157 | `lead/n1_r2_verify_20261108/_v_line_checks.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/n1_r2_verify_20261108/_v_line_checks.py:108`（全文 108 行，`n_sites=0`） | `eb7c32f1cb6c` / 4422 |
| 158 | `lead/n9_erratum_20261108/_er_check_b0cd48.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/n9_erratum_20261108/_er_check_b0cd48.py:112`（全文 112 行，`n_sites=0`） | `f3896d81ce16` / 5209 |
| 159 | `lead/n9_erratum_20261108/_er_report_hash.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/n9_erratum_20261108/_er_report_hash.py:44`（全文 44 行，`n_sites=0`） | `d4d027f31192` / 3374 |
| 160 | `lead/n9_erratum_20261108/_er_report_pe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/n9_erratum_20261108/_er_report_pe.py:118`（全文 118 行，`n_sites=0`） | `4a1e1644d279` / 6036 |
| 161 | `lead/needle_norm_20261109/_nd_l1fix.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/needle_norm_20261109/_nd_l1fix.py:124`（全文 124 行，`n_sites=0`） | `96749b23992c` / 5649 |
| 162 | `lead/needle_norm_20261109/_nn_norm.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/needle_norm_20261109/_nn_norm.py:278`（全文 278 行，`n_sites=0`） | `fdc3500f4044` / 13220 |
| 163 | `lead/orch_claims_20261109/_oc_ledger_scan.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/orch_claims_20261109/_oc_ledger_scan.py:23`（全文 23 行，`n_sites=0`） | `8954019783dd` / 925 |
| 164 | `lead/orch_claims_20261109/_ocw_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/orch_claims_20261109/_ocw_verify.py:156`（全文 156 行，`n_sites=0`） | `33117e520efa` / 7777 |
| 165 | `lead/p11_stations_20261108/_p11_stations_scan.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/p11_stations_20261108/_p11_stations_scan.py:411`（全文 411 行，`n_sites=0`） | `bbb273dd3dae` / 16629 |
| 166 | `lead/p11_stations_20261108/_p11_supplement.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/p11_stations_20261108/_p11_supplement.py:172`（全文 172 行，`n_sites=0`） | `803c54077166` / 6275 |
| 167 | `lead/p11_stations_20261108/_p11_supplement2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/p11_stations_20261108/_p11_supplement2.py:98`（全文 98 行，`n_sites=0`） | `21a8cada1229` / 4162 |
| 168 | `lead/qc161_u0400_trip/c2ab_x/_bhang_p1_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/qc161_u0400_trip/c2ab_x/_bhang_p1_verify.py:78`（全文 78 行，`n_sites=0`） | `d6cafe7a2d8d` / 2809 |
| 169 | `lead/r11_f2_fix_20261109/_f2_compare.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2_compare.py:104`（全文 104 行，`n_sites=0`） | `12e55acf4244` / 4821 |
| 170 | `lead/r11_f2_fix_20261109/_f2_r11plus.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2_r11plus.py:311`（全文 311 行，`n_sites=0`） | `83f8217fb9a1` / 15723 |
| 171 | `lead/r11_f2_fix_20261109/_f2v_edge.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2v_edge.py:85`（全文 85 行，`n_sites=0`） | `aecd22a0a324` / 4713 |
| 172 | `lead/r11_f2_fix_20261109/_f2v_final.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2v_final.py:62`（全文 62 行，`n_sites=0`） | `63d30ba45e67` / 2524 |
| 173 | `lead/r11_f2_fix_20261109/_f2v_run.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2v_run.py:82`（全文 82 行，`n_sites=0`） | `75108dcaee49` / 3469 |
| 174 | `lead/r11_f2_fix_20261109/_f2v_verify9.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2v_verify9.py:38`（全文 38 行，`n_sites=0`） | `c22f28ad4228` / 1618 |
| 175 | `lead/r11_f2_fix_20261109/_f2w_checks.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2w_checks.py:51`（全文 51 行，`n_sites=0`） | `23c5eebb77b4` / 2189 |
| 176 | `lead/r11_f2_fix_20261109/_f2w_dogfood.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2w_dogfood.py:58`（全文 58 行，`n_sites=0`） | `f591993c3c66` / 2784 |
| 177 | `lead/r11_f2_fix_20261109/_f2w_extract.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2w_extract.py:34`（全文 34 行，`n_sites=0`） | `1eb22164c783` / 1564 |
| 178 | `lead/r11_f2_fix_20261109/_f2w_final.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2w_final.py:41`（全文 41 行，`n_sites=0`） | `32c252452642` / 2049 |
| 179 | `lead/r11_f2_fix_20261109/_f2w_pass.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r11_f2_fix_20261109/_f2w_pass.py:26`（全文 26 行，`n_sites=0`） | `9d2d91862972` / 1289 |
| 180 | `lead/r2_unclosed_cd_20261108/_cd_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r2_unclosed_cd_20261108/_cd_check.py:317`（全文 317 行，`n_sites=0`） | `7fbb9a574d57` / 15031 |
| 181 | `lead/r2_unclosed_cd_20261108/_cdreport_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r2_unclosed_cd_20261108/_cdreport_check.py:236`（全文 236 行，`n_sites=0`） | `909d7a815e5e` / 10405 |
| 182 | `lead/r2_unclosed_cd_20261108/_verify_cd.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r2_unclosed_cd_20261108/_verify_cd.py:425`（全文 425 行，`n_sites=0`） | `81903652cb2e` / 21038 |
| 183 | `lead/r33e_merge_20261109/_re_fp_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r33e_merge_20261109/_re_fp_check.py:40`（全文 40 行，`n_sites=0`） | `eec157bd3566` / 1975 |
| 184 | `lead/r33e_merge_20261109/_re_struct_diff.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/r33e_merge_20261109/_re_struct_diff.py:60`（全文 60 行，`n_sites=0`） | `aa891a02ab62` / 3053 |
| 185 | `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py:479`（全文 479 行，`n_sites=0`） | `b382e893bafc` / 21411 |
| 186 | `lead/re_line_20261105/A2_EDGE_BURDEN/_a2_burden_census.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/A2_EDGE_BURDEN/_a2_burden_census.py:132`（全文 132 行，`n_sites=0`） | `722de738f74b` / 5888 |
| 187 | `lead/re_line_20261105/D21_RULING/_d21_burden5.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/D21_RULING/_d21_burden5.py:74`（全文 74 行，`n_sites=0`） | `7e4091381486` / 2929 |
| 188 | `lead/re_line_20261105/D24_RULING/_d24_facts.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/D24_RULING/_d24_facts.py:28`（全文 28 行，`n_sites=0`） | `68d581ce4559` / 1761 |
| 189 | `lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py:102`（全文 102 行，`n_sites=0`） | `2d17264e7725` / 4688 |
| 190 | `lead/re_line_20261105/V6_V3_REVIEW/_v6_r1.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/V6_V3_REVIEW/_v6_r1.py:402`（全文 402 行，`n_sites=0`） | `6f7a22967637` / 20172 |
| 191 | `lead/re_line_20261105/V6_V3_REVIEW/_v6_r5.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/V6_V3_REVIEW/_v6_r5.py:289`（全文 289 行，`n_sites=0`） | `d03ac5cad125` / 15177 |
| 192 | `lead/re_line_20261105/V6_V3_REVIEW/reviews/_r2_independent_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/V6_V3_REVIEW/reviews/_r2_independent_check.py:203`（全文 203 行，`n_sites=0`） | `9cb7001b6ab8` / 10173 |
| 193 | `lead/re_line_20261105/W10_COSTBOUND_RECHECK/reviews/_probe_review_t1.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W10_COSTBOUND_RECHECK/reviews/_probe_review_t1.py:201`（全文 201 行，`n_sites=0`） | `a8c0cb76ed0a` / 10457 |
| 194 | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/except_freshness.py:279`（全文 279 行，`n_sites=0`） | `e6685167f5d2` / 13190 |
| 195 | `lead/re_line_20261105/W1_HOLD_SURFACE/sections/_q3b_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W1_HOLD_SURFACE/sections/_q3b_probe.py:276`（全文 276 行，`n_sites=0`） | `92c387e85a04` / 10123 |
| 196 | `lead/re_line_20261105/W5_HARNESS_EXT/_build_ext.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W5_HARNESS_EXT/_build_ext.py:292`（全文 292 行，`n_sites=0`） | `aff56a740e12` / 10948 |
| 197 | `lead/re_line_20261105/W5_HARNESS_EXT/_w5_burden.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W5_HARNESS_EXT/_w5_burden.py:249`（全文 249 行，`n_sites=0`） | `7fa00ce98e82` / 12021 |
| 198 | `lead/re_line_20261105/W7_W4_REVIEW/_w7_a2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W7_W4_REVIEW/_w7_a2.py:299`（全文 299 行，`n_sites=0`） | `96ae91eb2b02` / 13066 |
| 199 | `lead/re_line_20261105/W7_W4_REVIEW/_w7_a3.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W7_W4_REVIEW/_w7_a3.py:272`（全文 272 行，`n_sites=0`） | `46042f176086` / 10961 |
| 200 | `lead/re_line_20261105/W7_W4_REVIEW/_w7_a4.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W7_W4_REVIEW/_w7_a4.py:302`（全文 302 行，`n_sites=0`） | `414109510d2f` / 15528 |
| 201 | `lead/re_line_20261105/W7_W4_REVIEW/_w7_b1.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W7_W4_REVIEW/_w7_b1.py:228`（全文 228 行，`n_sites=0`） | `395b8fbe3bb4` / 11491 |
| 202 | `lead/re_line_20261105/W7_W4_REVIEW/_w7_b2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W7_W4_REVIEW/_w7_b2.py:400`（全文 400 行，`n_sites=0`） | `da5d784fed8e` / 23200 |
| 203 | `lead/re_line_20261105/W7_W4_REVIEW/_w7_c.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W7_W4_REVIEW/_w7_c.py:279`（全文 279 行，`n_sites=0`） | `f7424255758f` / 13847 |
| 204 | `lead/re_line_20261105/W8_STATIC_LOCATE/_w8_f6.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W8_STATIC_LOCATE/_w8_f6.py:149`（全文 149 行，`n_sites=0`） | `6abebdf478dc` / 6284 |
| 205 | `lead/re_line_20261105/W8_STATIC_LOCATE/_w8_f7.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W8_STATIC_LOCATE/_w8_f7.py:303`（全文 303 行，`n_sites=0`） | `c66fe3591057` / 12215 |
| 206 | `lead/re_line_20261105/W8_STATIC_LOCATE/reviews/_f6rev_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W8_STATIC_LOCATE/reviews/_f6rev_probe.py:265`（全文 265 行，`n_sites=0`） | `2c8082c9840c` / 11000 |
| 207 | `lead/re_line_20261105/W8_STATIC_LOCATE/reviews/_f6rev_probe2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W8_STATIC_LOCATE/reviews/_f6rev_probe2.py:60`（全文 60 行，`n_sites=0`） | `75aa17448409` / 2470 |
| 208 | `lead/re_line_20261105/W8_STATIC_LOCATE/reviews/_f8rev_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W8_STATIC_LOCATE/reviews/_f8rev_probe.py:386`（全文 386 行，`n_sites=0`） | `2e678e4d02b2` / 15045 |
| 209 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q1.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q1.py:356`（全文 356 行，`n_sites=0`） | `1176af83803b` / 14693 |
| 210 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q3.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q3.py:336`（全文 336 行，`n_sites=0`） | `11a6ae345835` / 16661 |
| 211 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q3_final.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q3_final.py:94`（全文 94 行，`n_sites=0`） | `a43840d425b2` / 4364 |
| 212 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q3_handler.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q3_handler.py:177`（全文 177 行，`n_sites=0`） | `62a4df52bab4` / 7567 |
| 213 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q5.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/_w9_q5.py:96`（全文 96 行，`n_sites=0`） | `f8327bc779de` / 4237 |
| 214 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q3_review_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q3_review_probe.py:281`（全文 281 行，`n_sites=0`） | `6b4eacd48bc3` / 13260 |
| 215 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q4_exact_rerun.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q4_exact_rerun.py:298`（全文 298 行，`n_sites=0`） | `6ca7ae1a7152` / 14614 |
| 216 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q4_review_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q4_review_probe.py:180`（全文 180 行，`n_sites=0`） | `504fcae67429` / 8477 |
| 217 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q5_exact_rerun.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q5_exact_rerun.py:96`（全文 96 行，`n_sites=0`） | `cc04b9059018` / 4349 |
| 218 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q5_review_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_Q5_review_probe.py:92`（全文 92 行，`n_sites=0`） | `4fdbbde858af` / 4041 |
| 219 | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_q2_review_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/reviews/_q2_review_probe.py:124`（全文 124 行，`n_sites=0`） | `989cb806567f` / 5398 |
| 220 | `lead/re_line_20261105/_leader/_a7_acf_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/_leader/_a7_acf_probe.py:164`（全文 164 行，`n_sites=0`） | `e42a79f3c1d1` / 5763 |
| 221 | `lead/re_line_20261105/_leader/_intra_frame_census.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/re_line_20261105/_leader/_intra_frame_census.py:168`（全文 168 行，`n_sites=0`） | `c4e537ab45dc` / 6279 |
| 222 | `lead/s604_attribution_20261108/_sa_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/s604_attribution_20261108/_sa_probe.py:213`（全文 213 行，`n_sites=0`） | `aaaeedb88284` / 10753 |
| 223 | `lead/s604_refsync_full_20261109/_full_checks.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/s604_refsync_full_20261109/_full_checks.py:110`（全文 110 行，`n_sites=0`） | `a8d1c0b3a228` / 4424 |
| 224 | `lead/s604_refsync_full_20261109/_full_fp.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/s604_refsync_full_20261109/_full_fp.py:100`（全文 100 行，`n_sites=0`） | `16320626c3f9` / 5207 |
| 225 | `lead/s604_refsync_full_20261109/_rf_verify_fp.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/s604_refsync_full_20261109/_rf_verify_fp.py:98`（全文 98 行，`n_sites=0`） | `3a1516964229` / 3910 |
| 226 | `lead/s604_script_hunt_20261109/_sh_gen512655_payload.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/s604_script_hunt_20261109/_sh_gen512655_payload.py:34`（全文 34 行，`n_sites=0`） | `a6ad4afe7349` / 1641 |
| 227 | `lead/s604_verdict_entry_20261109/_ve_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/s604_verdict_entry_20261109/_ve_check.py:102`（全文 102 行，`n_sites=0`） | `e6d426243ade` / 4969 |
| 228 | `lead/s604_verdict_entry_20261109/_vev_fp.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/s604_verdict_entry_20261109/_vev_fp.py:48`（全文 48 行，`n_sites=0`） | `4c6007e7c516` / 2250 |
| 229 | `lead/slowframe_r3_20261108/_r3_recompute_gapdiff.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/slowframe_r3_20261108/_r3_recompute_gapdiff.py:229`（全文 229 行，`n_sites=0`） | `9e2749523230` / 12659 |
| 230 | `lead/slowwindow_n8_20261108/_n8_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/slowwindow_n8_20261108/_n8_recompute.py:290`（全文 290 行，`n_sites=0`） | `0b4ee1250232` / 13002 |
| 231 | `lead/slowwindow_n8_20261108/_n8_s603_summary.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/slowwindow_n8_20261108/_n8_s603_summary.py:116`（全文 116 行，`n_sites=0`） | `359d7abec5d8` / 5167 |
| 232 | `lead/slowwindow_n8_20261108/_n8_variants.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/slowwindow_n8_20261108/_n8_variants.py:188`（全文 188 行，`n_sites=0`） | `e94b40490b5b` / 7456 |
| 233 | `lead/slowwindow_n8_20261108/_verify_recompute.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/slowwindow_n8_20261108/_verify_recompute.py:323`（全文 323 行，`n_sites=0`） | `7ac42029b5cf` / 14724 |
| 234 | `lead/spec_static_closure_20261108/_sc_mix.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/spec_static_closure_20261108/_sc_mix.py:126`（全文 126 行，`n_sites=0`） | `ae7a7adf2760` / 5308 |
| 235 | `lead/spec_static_closure_20261108/_sc_p7.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/spec_static_closure_20261108/_sc_p7.py:183`（全文 183 行，`n_sites=0`） | `fa2e4466e60e` / 6501 |
| 236 | `lead/spec_static_closure_20261108/_sc_scan.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/spec_static_closure_20261108/_sc_scan.py:563`（全文 563 行，`n_sites=0`） | `a034a6182f7a` / 23880 |
| 237 | `lead/stale_pass_20261109/_sp_4gate_compare.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_4gate_compare.py:43`（全文 43 行，`n_sites=0`） | `9810643904ff` / 2268 |
| 238 | `lead/stale_pass_20261109/_sp_andk.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_andk.py:44`（全文 44 行，`n_sites=0`） | `7f6e34b1daea` / 1961 |
| 239 | `lead/stale_pass_20261109/_sp_broad.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_broad.py:28`（全文 28 行，`n_sites=0`） | `f7f64b72de3d` / 1178 |
| 240 | `lead/stale_pass_20261109/_sp_classify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_classify.py:63`（全文 63 行，`n_sites=0`） | `de2a2a4d56e9` / 2893 |
| 241 | `lead/stale_pass_20261109/_sp_dist.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_dist.py:53`（全文 53 行，`n_sites=0`） | `27284e0d88ac` / 2658 |
| 242 | `lead/stale_pass_20261109/_sp_final_checks.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_final_checks.py:30`（全文 30 行，`n_sites=0`） | `ed7b27e5872b` / 1144 |
| 243 | `lead/stale_pass_20261109/_sp_gen_word.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_gen_word.py:19`（全文 19 行，`n_sites=0`） | `2877580cddbe` / 863 |
| 244 | `lead/stale_pass_20261109/_sp_scan.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_scan.py:44`（全文 44 行，`n_sites=0`） | `0a8ac9cc869f` / 1776 |
| 245 | `lead/stale_pass_20261109/_sp_tally.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_sp_tally.py:58`（全文 58 行，`n_sites=0`） | `64f0d89af5b8` / 2192 |
| 246 | `lead/stale_pass_20261109/_spi_final.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_spi_final.py:65`（全文 65 行，`n_sites=0`） | `0496b177c439` / 3618 |
| 247 | `lead/stale_pass_20261109/_spi_hash.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_spi_hash.py:34`（全文 34 行，`n_sites=0`） | `a9fb6f34817c` / 1875 |
| 248 | `lead/stale_pass_20261109/_spi_lines.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_spi_lines.py:24`（全文 24 行，`n_sites=0`） | `04156ca448ca` / 1208 |
| 249 | `lead/stale_pass_20261109/_spi_src_lines.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_spi_src_lines.py:28`（全文 28 行，`n_sites=0`） | `9a86e40d4b8b` / 1478 |
| 250 | `lead/stale_pass_20261109/_spi_verify.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stale_pass_20261109/_spi_verify.py:74`（全文 74 行，`n_sites=0`） | `a3d887f9ab05` / 4426 |
| 251 | `lead/stall_event_def_20261106/_stall_probe.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/stall_event_def_20261106/_stall_probe.py:354`（全文 354 行，`n_sites=0`） | `de882a9a678c` / 14612 |
| 252 | `lead/static_spec_n9_20261107/_n9_fingerprint.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/static_spec_n9_20261107/_n9_fingerprint.py:38`（全文 38 行，`n_sites=0`） | `9e567c5c294f` / 1693 |
| 253 | `lead/strict_exposure_20261109/_se_enum.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/strict_exposure_20261109/_se_enum.py:341`（全文 341 行，`n_sites=0`） | `0f5f271385ba` / 16748 |
| 254 | `lead/strict_exposure_20261109/_se_fp.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/strict_exposure_20261109/_se_fp.py:43`（全文 43 行，`n_sites=0`） | `d41be5eb718a` / 2149 |
| 255 | `lead/u5u6_mirror_20261109/_m5_mirror_check.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/u5u6_mirror_20261109/_m5_mirror_check.py:154`（全文 154 行，`n_sites=0`） | `1e23f04cda2a` / 8073 |
| 256 | `lead/w2_samecause_20261109/_w2v_fp.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/w2_samecause_20261109/_w2v_fp.py:38`（全文 38 行，`n_sites=0`） | `0c1743063fc7` / 1910 |
| 257 | `lead/w2_samecause_20261109/_w2v_probe1.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/w2_samecause_20261109/_w2v_probe1.py:225`（全文 225 行，`n_sites=0`） | `82de21ea03a0` / 8256 |
| 258 | `lead/w2_samecause_20261109/_w2v_probe2.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/w2_samecause_20261109/_w2v_probe2.py:110`（全文 110 行，`n_sites=0`） | `1e4b21d98f72` / 3754 |
| 259 | `lead/whitelist_audit_20261109/_wl_selfproof.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/whitelist_audit_20261109/_wl_selfproof.py:81`（全文 81 行，`n_sites=0`） | `ac0d9d4b8b79` / 5396 |
| 260 | `lead/whitelist_audit_20261109/_wl_step1_repro.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/whitelist_audit_20261109/_wl_step1_repro.py:145`（全文 145 行，`n_sites=0`） | `7dfa7611e2eb` / 7586 |
| 261 | `lead/whitelist_audit_20261109/_wlw_gate.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/whitelist_audit_20261109/_wlw_gate.py:54`（全文 54 行，`n_sites=0`） | `4acad815ee9f` / 2446 |
| 262 | `lead/whitelist_audit_20261109/_wlw_stepC.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `lead/whitelist_audit_20261109/_wlw_stepC.py:308`（全文 308 行，`n_sites=0`） | `d82947c29be2` / 16374 |
| 263 | `out/re_work/_audit_task12.py` | NO_EXIT_AT_ALL | NO_EXIT_AT_ALL | `out/re_work/_audit_task12.py:53`（全文 53 行，`n_sites=0`） | `fd148c184e0f` / 3229 |

其中台账 5 行真零信息登记的对象全部在此表：`lead/re_line_20261105/D21_RULING/_d21_burden5.py`、`lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py`、`lead/re_line_20261105/_leader/_a7_acf_probe.py`、`lead/re_line_20261105/_leader/_intra_frame_census.py`（被 2 行点名）。另有 `lead/d26_ruling_20261106/_d26_facts.py` … `lead/d30_ruling_20261106/_d30_facts.py` 五件（AST `n_sites=0`），它们是 `PENDING_DECISIONS.md:92/105/117/129/162` 行内并列被引 的事实脚本，**不是那句 exit=0 的主语**。

`FILE_OR_STDOUT_ONLY_VERDICT` 191 件、`VERDICT_VIA_ASSERT_ONLY` 54 件在本表内部分重叠（flag 计数见 `_ce_final_stdout.txt:20-28`）；assert-only 通道**未逐件定级（未验）**。

### 附录 C — CONDITIONAL_EXIT 全部 132 件

判据：`SITES` 非空 ∧（有 DATA ∨ 可达状态集合 ≥2）。逐件给每个出口 site 的 `文件:行` + 表达式；`EXIT=0` 有信息，但强度取决于 §3.3 的合取/失败可达性条件。

| # | rel | 编排方 | 最终 | 出口 site（`文件:行` = 表达式） | 可达状态 |
|---|---|---|---|---|---|
| 1 | `lead/b2b_candidate_20261106/qc151_trip.candidate.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/b2b_candidate_20261106/qc151_trip.candidate.py:489` = `EXIT_LAUNCH_LIMIT`; `lead/b2b_candidate_20261106/qc151_trip.candidate.py:505` = `EXIT_STAGE_TIMEOUT`; `lead/b2b_candidate_20261106/qc151_trip.candidate.py:516` = `EXIT_TRIP_BUDGET`; `lead/b2b_candidate_20261106/qc151_trip.candidate.py:1148` = `EXIT_PID_NOT_FOUND`; `lead/b2b_candidate_20261106/qc151_trip.candidate.py:1159` = `EXIT_PID_IDENTITY_UNVERIFIED`; `lead/b2b_candidate_20261106/qc151_trip.candidate.py:1175` = `EXIT_PID_NOT_FOUND`; `lead/b2b_candidate_20261106/qc151_trip.candidate.py:6447` = `f'★ U-3：★ --out-dir 落在受保护子树内 ⇒ 拒绝：{WORKDIR}'`; `lead/b2b_candidate_20261106/qc151_trip.candidate.py:7437` = `written`; `lead/b2b_candidate_20261106/qc151_trip.candidate.py:7533` = `_entry()` | `0,1+DATA` |
| 2 | `lead/b2b_candidate_20261106/tests/test_candidate.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/b2b_candidate_20261106/tests/test_candidate.py:663` = `run_all_tests()` | `0,1+DATA` |
| 3 | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:489` = `EXIT_LAUNCH_LIMIT`; `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:505` = `EXIT_STAGE_TIMEOUT`; `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:516` = `EXIT_TRIP_BUDGET`; `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:1148` = `EXIT_PID_NOT_FOUND`; `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:1159` = `EXIT_PID_IDENTITY_UNVERIFIED`; `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:1175` = `EXIT_PID_NOT_FOUND`; `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:6447` = `f'★ U-3：★ --out-dir 落在受保护子树内 ⇒ 拒绝：{WORKDIR}'`; `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:7437` = `written`; `lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py:7533` = `_entry()` | `0,1+DATA` |
| 4 | `lead/b2b_candidate_review3_20261107/_check_candidate_r3.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/b2b_candidate_review3_20261107/_check_candidate_r3.py:276` = `main()` | `0,1,2` |
| 5 | `lead/b2b_candidate_review3_20261107/_test_candidate_lf.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/b2b_candidate_review3_20261107/_test_candidate_lf.py:663` = `run_all_tests()` | `0,1+DATA` |
| 6 | `lead/b2b_design_20261106/_draft_semantics_check.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/b2b_design_20261106/_draft_semantics_check.py:633` = `'usage: build | verify | matrix | anchors'` | `0,1` |
| 7 | `lead/b2b_isolated_20261107/_integ_check_isolated.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/b2b_isolated_20261107/_integ_check_isolated.py:276` = `main()` | `0,1,2` |
| 8 | `lead/b2b_isolated_20261107/_integ_probe_isolated.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/b2b_isolated_20261107/_integ_probe_isolated.py:303` = `0 if nfail == 0 else 1` | `0,1+DATA` |
| 9 | `lead/b2b_isolated_20261107/_integ_test_isolated.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/b2b_isolated_20261107/_integ_test_isolated.py:663` = `run_all_tests()` | `0,1+DATA` |
| 10 | `lead/b2b_isolated_20261107/qc151_trip.isolated.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/b2b_isolated_20261107/qc151_trip.isolated.py:489` = `EXIT_LAUNCH_LIMIT`; `lead/b2b_isolated_20261107/qc151_trip.isolated.py:505` = `EXIT_STAGE_TIMEOUT`; `lead/b2b_isolated_20261107/qc151_trip.isolated.py:516` = `EXIT_TRIP_BUDGET`; `lead/b2b_isolated_20261107/qc151_trip.isolated.py:1148` = `EXIT_PID_NOT_FOUND`; `lead/b2b_isolated_20261107/qc151_trip.isolated.py:1159` = `EXIT_PID_IDENTITY_UNVERIFIED`; `lead/b2b_isolated_20261107/qc151_trip.isolated.py:1175` = `EXIT_PID_NOT_FOUND`; `lead/b2b_isolated_20261107/qc151_trip.isolated.py:6447` = `f'★ U-3：★ --out-dir 落在受保护子树内 ⇒ 拒绝：{WORKDIR}'`; `lead/b2b_isolated_20261107/qc151_trip.isolated.py:7437` = `written`; `lead/b2b_isolated_20261107/qc151_trip.isolated.py:7533` = `_entry()` | `0,1+DATA` |
| 11 | `lead/c07_gate_fix_20261109/_f3_c7check.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/c07_gate_fix_20261109/_f3_c7check.py:608` = `main(sys.argv)` | `0,1,2+DATA` |
| 12 | `lead/c07_gate_fix_20261109/_g1g5_fp.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/c07_gate_fix_20261109/_g1g5_fp.py:83` = `main()` | `0,1+DATA` |
| 13 | `lead/c07_protocol_attacks_20261109/_pat_fp_verify.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/c07_protocol_attacks_20261109/_pat_fp_verify.py:72` = `main()` | `0,1+DATA` |
| 14 | `lead/c07_slot_20261109/_c7_selfcheck.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/c07_slot_20261109/_c7_selfcheck.py:217` = `main(sys.argv)` | `0,1,2+DATA` |
| 15 | `lead/check_masking_20261109/_cmd_template_fixed.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/check_masking_20261109/_cmd_template_fixed.py:96` = `main()` | `0,1+DATA` |
| 16 | `lead/check_masking_20261109/_cmv_template_port.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/check_masking_20261109/_cmv_template_port.py:97` = `main()` | `0,1+DATA` |
| 17 | `lead/codex_round_20261030/XVERIFY_V3_20261101/_probe_v3_review.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/codex_round_20261030/XVERIFY_V3_20261101/_probe_v3_review.py:105` = `'FATAL: gate-override 块未定位'`; `lead/codex_round_20261030/XVERIFY_V3_20261101/_probe_v3_review.py:171` = `1 if fails else 0` | `0,1+DATA` |
| 18 | `lead/codex_round_20261030/XVERIFY_V4_20261101/_probe_h87_dump.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/codex_round_20261030/XVERIFY_V4_20261101/_probe_h87_dump.py:292` = `0 if not FAILS else 1` | `0,1+DATA` |
| 19 | `lead/codex_round_20261030/XVERIFY_V4_20261101/_probe_trace_volume.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/codex_round_20261030/XVERIFY_V4_20261101/_probe_trace_volume.py:101` = `0 if not FAILS else 1` | `0,1+DATA` |
| 20 | `lead/control_20261106/gate_n1_lf_20261107.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/control_20261106/gate_n1_lf_20261107.py:150` = `0 if not fails else 1`; `lead/control_20261106/gate_n1_lf_20261107.py:156` = `1`; `lead/control_20261106/gate_n1_lf_20261107.py:370` = `0 if not fails else 1` | `0,1+DATA` |
| 21 | `lead/count_invariant_20261109/_ci_checks.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/count_invariant_20261109/_ci_checks.py:200` = `main()` | `0,1,2` |
| 22 | `lead/count_invariant_20261109/_ci_counterexamples.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/count_invariant_20261109/_ci_counterexamples.py:152` = `0 if all(RESULTS.values()) else 1` | `0,1+DATA` |
| 23 | `lead/count_invariant_20261109/_cii_checks.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/count_invariant_20261109/_cii_checks.py:198` = `main()` | `0,1,2` |
| 24 | `lead/count_invariant_20261109/_cii_counterexamples.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/count_invariant_20261109/_cii_counterexamples.py:224` = `0 if all(RESULTS.values()) else 1` | `0,1+DATA` |
| 25 | `lead/d25_ruling_20261106/_d25_facts.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/d25_ruling_20261106/_d25_facts.py:209` = `status` | `0,1+DATA` |
| 26 | `lead/deliverable_anchor_20261108/_da_anchor_selfcheck.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/deliverable_anchor_20261108/_da_anchor_selfcheck.py:39` = `main(sys.argv[1])` | `0,2,3,4` |
| 27 | `lead/deliverable_anchor_20261108/_spec2_anchor_check.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/deliverable_anchor_20261108/_spec2_anchor_check.py:77` = `main()` | `0,3,4,5` |
| 28 | `lead/deliverable_anchor_20261108/_verify_hy4_anchor.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/deliverable_anchor_20261108/_verify_hy4_anchor.py:271` = `2` | `0,2` |
| 29 | `lead/direction_ruling_20261108/_verify_hy4.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/direction_ruling_20261108/_verify_hy4.py:118` = `0 if all_ok else 1` | `0,1+DATA` |
| 30 | `lead/dtrigger_compare_20261107/_check_dtrigger.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/dtrigger_compare_20261107/_check_dtrigger.py:228` = `0 if ok else 1` | `0,1+DATA` |
| 31 | `lead/dtrigger_compare_20261107/_check_metrics.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/dtrigger_compare_20261107/_check_metrics.py:292` = `0 if ok else 1` | `0,1+DATA` |
| 32 | `lead/gate_n13_20261109/_n13_migration_check.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/gate_n13_20261109/_n13_migration_check.py:106` = `main()` | `0,1+DATA` |
| 33 | `lead/gate_n13_20261109/_n13_regression.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/gate_n13_20261109/_n13_regression.py:259` = `main()` | `0,1+DATA` |
| 34 | `lead/gate_n13_20261109/_n13v_migration.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/gate_n13_20261109/_n13v_migration.py:170` = `main()` | `0,1+DATA` |
| 35 | `lead/gate_r9r12_20261109/_g9_gate.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/gate_r9r12_20261109/_g9_gate.py:238` = `0 if ok else 1` | `0,1+DATA` |
| 36 | `lead/gate_r9sem_20261109/_r9s_g9_candidate.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/gate_r9sem_20261109/_r9s_g9_candidate.py:239` = `0 if ok else 1` | `0,1+DATA` |
| 37 | `lead/gate_r9sem_20261109/_r9s_regress.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/gate_r9sem_20261109/_r9s_regress.py:237` = `0 if OUT['verdict'] == 'PASS' else 1` | `0,1+DATA` |
| 38 | `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:489` = `EXIT_LAUNCH_LIMIT`; `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:505` = `EXIT_STAGE_TIMEOUT`; `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:516` = `EXIT_TRIP_BUDGET`; `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:1148` = `EXIT_PID_NOT_FOUND`; `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:1159` = `EXIT_PID_IDENTITY_UNVERIFIED`; `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:1175` = `EXIT_PID_NOT_FOUND`; `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:6447` = `f'★ U-3：★ --out-dir 落在受保护子树内 ⇒ 拒绝：{WORKDIR}'`; `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:7437` = `written`; `lead/gate_validate_20261108/_verify_vectors/v2_newedge/qc151_trip.plus1.py:7533` = `_entry()` | `0,1+DATA` |
| 39 | `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:489` = `EXIT_LAUNCH_LIMIT`; `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:505` = `EXIT_STAGE_TIMEOUT`; `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:516` = `EXIT_TRIP_BUDGET`; `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:1148` = `EXIT_PID_NOT_FOUND`; `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:1159` = `EXIT_PID_IDENTITY_UNVERIFIED`; `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:1175` = `EXIT_PID_NOT_FOUND`; `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:6447` = `f'★ U-3：★ --out-dir 落在受保护子树内 ⇒ 拒绝：{WORKDIR}'`; `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:7437` = `written`; `lead/gate_validate_20261108/_verify_vectors/v7_bypass/qc151_trip.newcall.py:7533` = `_entry()` | `0,1+DATA` |
| 40 | `lead/goal1_a8_fix_20261022/VERIFY_A8B.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal1_a8_fix_20261022/VERIFY_A8B.py:455` = `main()` | `0,1+DATA` |
| 41 | `lead/goal1_a8_fix_20261022/_a8_negctl.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal1_a8_fix_20261022/_a8_negctl.py:156` = `main()` | `0,1+DATA` |
| 42 | `lead/goal1_a8_fix_20261022/_gen_harness4.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal1_a8_fix_20261022/_gen_harness4.py:389` = `main()` | `0,1` |
| 43 | `lead/goal1_a8_fix_20261022/_test_enum_probe.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal1_a8_fix_20261022/_test_enum_probe.py:151` = `main()` | `0,1+DATA` |
| 44 | `lead/goal1_a8_fix_20261022/_test_path_scope.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal1_a8_fix_20261022/_test_path_scope.py:122` = `main()` | `0,1+DATA` |
| 45 | `lead/goal1_boot_fingerprint_20261022/_redact_fingerprint.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal1_boot_fingerprint_20261022/_redact_fingerprint.py:150` = `main()` | `0,1,2` |
| 46 | `lead/goal1_harness6_20261022/_verify_wer_sig.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal1_harness6_20261022/_verify_wer_sig.py:129` = `main()` | `0,1+DATA` |
| 47 | `lead/goal1_harness6_20261022/qc151_trip.harness6.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal1_harness6_20261022/qc151_trip.harness6.py:618` = `EXIT_LAUNCH_LIMIT`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:634` = `EXIT_STAGE_TIMEOUT`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:645` = `EXIT_TRIP_BUDGET`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:1336` = `EXIT_PID_NOT_FOUND`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:1347` = `EXIT_PID_IDENTITY_UNVERIFIED`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:1363` = `EXIT_PID_NOT_FOUND`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:7253` = `f'★ U-3：★ --out-dir 落在受保护子树内 ⇒ 拒绝：{WORKDIR}'`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:7650` = `EXIT_PID_DEAD`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:8387` = `written`; `lead/goal1_harness6_20261022/qc151_trip.harness6.py:8483` = `_entry()` | `0,1+DATA` |
| 48 | `lead/goal1_harness8_20261031/_judge_h8v4_20261101.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal1_harness8_20261031/_judge_h8v4_20261101.py:639` = `main()` | `0,1+DATA` |
| 49 | `lead/goal2_onetime_census_20261022/VERIFY_GUARD.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_onetime_census_20261022/VERIFY_GUARD.py:62` = `2` | `0,2` |
| 50 | `lead/goal2_onetime_census_20261022/_atexit_verdict.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_onetime_census_20261022/_atexit_verdict.py:253` = `main()` | `0,1+DATA` |
| 51 | `lead/goal2_onetime_census_20261022/_exit_vs_init.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_onetime_census_20261022/_exit_vs_init.py:285` = `main()` | `0,1+DATA` |
| 52 | `lead/goal2_onetime_census_20261022/_singleton_identity_rejudge.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_onetime_census_20261022/_singleton_identity_rejudge.py:280` = `main()` | `0,1+DATA` |
| 53 | `lead/goal2_rc4_fixv5_20261022/_esp_bfs.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_esp_bfs.py:308` = `main()` | `0,1+DATA` |
| 54 | `lead/goal2_rc4_fixv5_20261022/_esp_fullpath.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_esp_fullpath.py:570` = `main()` | `0,1+DATA` |
| 55 | `lead/goal2_rc4_fixv5_20261022/_lead_audit_probe_h6.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_lead_audit_probe_h6.py:329` = `main()` | `0,1+DATA` |
| 56 | `lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py:924` = `main()` | `0,2,3` |
| 57 | `lead/goal2_rc4_fixv5_20261022/_selftest_todo6_verdict.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_selftest_todo6_verdict.py:126` = `main()` | `0,1+DATA` |
| 58 | `lead/goal2_rc4_fixv5_20261022/_survey_6930a0.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_survey_6930a0.py:213` = `main()` | `0,1+DATA` |
| 59 | `lead/goal2_rc4_fixv5_20261022/_todo7_creation_trigger.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_todo7_creation_trigger.py:374` = `main()` | `0,1+DATA` |
| 60 | `lead/goal2_rc4_fixv5_20261022/_verify_a8_runtime.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_verify_a8_runtime.py:249` = `main()` | `0,1+DATA` |
| 61 | `lead/goal2_rc4_fixv5_20261022/_verify_ecx_dataflow.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_verify_ecx_dataflow.py:734` = `main()` | `0,1+DATA` |
| 62 | `lead/goal2_rc4_fixv5_20261022/_verify_guard_premise.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_verify_guard_premise.py:476` = `main()` | `0,1+DATA` |
| 63 | `lead/goal2_rc4_fixv5_20261022/_verify_patch_coverage.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_verify_patch_coverage.py:314` = `main()` | `0,1+DATA` |
| 64 | `lead/goal2_rc4_fixv5_20261022/_verify_patch_v5.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_verify_patch_v5.py:771` = `main()` | `0,1+DATA` |
| 65 | `lead/goal2_rc4_fixv5_20261022/_verify_probe_a4a7a8.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_verify_probe_a4a7a8.py:266` = `main()` | `0,1+DATA` |
| 66 | `lead/goal2_rc4_fixv5_20261022/_verify_stack_offset.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_verify_stack_offset.py:821` = `main()` | `0,1+DATA` |
| 67 | `lead/goal2_rc4_fixv5_20261022/_verify_wmclose_chain.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_verify_wmclose_chain.py:225` = `main()` | `0,1+DATA` |
| 68 | `lead/goal2_rc4_fixv5_20261022/_vtable_slot14.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_fixv5_20261022/_vtable_slot14.py:447` = `main()` | `0,1+DATA` |
| 69 | `lead/goal2_rc4_frameproof_20261022/VERIFY_FRAME.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_frameproof_20261022/VERIFY_FRAME.py:74` = `'not an MZ image: %s' % path`; `lead/goal2_rc4_frameproof_20261022/VERIFY_FRAME.py:77` = `'bad PE signature at e_lfanew=0x%x' % self.e_lfanew`; `lead/goal2_rc4_frameproof_20261022/VERIFY_FRAME.py:84` = `'expected PE32 (0x10b), got 0x%x' % self.magic`; `lead/goal2_rc4_frameproof_20261022/VERIFY_FRAME.py:145` = `'section %s not found' % section_name`; `lead/goal2_rc4_frameproof_20261022/VERIFY_FRAME.py:216` = `'missing input: %s' % p`; `lead/goal2_rc4_frameproof_20261022/VERIFY_FRAME.py:432` = `main()` | `0,1+DATA` |
| 70 | `lead/goal2_rc4_frameproof_20261022/_g_deref_census_v2.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_frameproof_20261022/_g_deref_census_v2.py:406` = `main()` | `0,1+DATA` |
| 71 | `lead/goal2_rc4_frameproof_20261022/_rc4_fix_v4_proof.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_frameproof_20261022/_rc4_fix_v4_proof.py:363` = `main()` | `0,1+DATA` |
| 72 | `lead/goal2_rc4_trigger_20261022/VERIFY_RC4_MINIDUMP.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/VERIFY_RC4_MINIDUMP.py:256` = `main()` | `0,1,2` |
| 73 | `lead/goal2_rc4_trigger_20261022/VERIFY_RC4_TRIPS.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/VERIFY_RC4_TRIPS.py:188` = `main()` | `0,1,2` |
| 74 | `lead/goal2_rc4_trigger_20261022/_dispatch_expand.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_dispatch_expand.py:324` = `main()` | `0,1` |
| 75 | `lead/goal2_rc4_trigger_20261022/_dispatch_negctl.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_dispatch_negctl.py:22` = `1`; `lead/goal2_rc4_trigger_20261022/_dispatch_negctl.py:62` = `1`; `lead/goal2_rc4_trigger_20261022/_dispatch_negctl.py:64` = `0` | `0,1` |
| 76 | `lead/goal2_rc4_trigger_20261022/_guard_audit.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_guard_audit.py:251` = `main()` | `0,1` |
| 77 | `lead/goal2_rc4_trigger_20261022/_input_path.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_input_path.py:203` = `main()` | `0,1` |
| 78 | `lead/goal2_rc4_trigger_20261022/_insert_corrections.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_insert_corrections.py:100` = `main()` | `0,1` |
| 79 | `lead/goal2_rc4_trigger_20261022/_rc4_reconcile_v2.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_rc4_reconcile_v2.py:448` = `main()` | `0,1+DATA` |
| 80 | `lead/goal2_rc4_trigger_20261022/_reachability.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_reachability.py:191` = `main()` | `0,1,2,3` |
| 81 | `lead/goal2_rc4_trigger_20261022/_vtable_census.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_vtable_census.py:162` = `main()` | `0,1` |
| 82 | `lead/goal2_rc4_trigger_20261022/_vtable_closure.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_vtable_closure.py:161` = `main()` | `0,1` |
| 83 | `lead/goal2_rc4_trigger_20261022/_window_anchor.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/goal2_rc4_trigger_20261022/_window_anchor.py:358` = `main()` | `0,1` |
| 84 | `lead/goal3_p1sbh_merge_20261020/_work/mkdiff.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal3_p1sbh_merge_20261020/_work/mkdiff.py:65` = `'hunk %d context not unique' % (idx + 1)` | `0,1+DATA` |
| 85 | `lead/goal3_verifyhooks_fix_20261020/verify_hooks.v2.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/goal3_verifyhooks_fix_20261020/verify_hooks.v2.py:528` = `main()` | `0,1,2+DATA` |
| 86 | `lead/k1bit_detect_20261109/_kdp_validate.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/k1bit_detect_20261109/_kdp_validate.py:201` = `main()` | `0,1+DATA` |
| 87 | `lead/k1bit_detect_20261109/_kdv_legal_all.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/k1bit_detect_20261109/_kdv_legal_all.py:25` = `main()` | `0,1` |
| 88 | `lead/masking_effect_20261109/_me_auditcheck_plan2.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/masking_effect_20261109/_me_auditcheck_plan2.py:205` = `0 if all_good else 1` | `0,1+DATA` |
| 89 | `lead/matrix_ab_ruling_20261109/_ab_probe.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/matrix_ab_ruling_20261109/_ab_probe.py:23` = `'path outside allowed BASE rejected: %r' % p`; `lead/matrix_ab_ruling_20261109/_ab_probe.py:236` = `1` | `0,1+DATA` |
| 90 | `lead/matrix_ab_ruling_20261109/_rv2_probe_20261109.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/matrix_ab_ruling_20261109/_rv2_probe_20261109.py:387` = `1` | `0,1` |
| 91 | `lead/matrix_binding_20261108/_m_rebuild.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/matrix_binding_20261108/_m_rebuild.py:42` = `2`; `lead/matrix_binding_20261108/_m_rebuild.py:90` = `2`; `lead/matrix_binding_20261108/_m_rebuild.py:109` = `2`; `lead/matrix_binding_20261108/_m_rebuild.py:118` = `2`; `lead/matrix_binding_20261108/_m_rebuild.py:164` = `2` | `0,2` |
| 92 | `lead/n10c04_ruling_20261108/_rv_n10c04_ruling_audit.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/n10c04_ruling_20261108/_rv_n10c04_ruling_audit.py:7` = `'repository argument must be an absolute path'`; `lead/n10c04_ruling_20261108/_rv_n10c04_ruling_audit.py:64` = `0 if all_ok else 1` | `0,1+DATA` |
| 93 | `lead/qc161_u0400_trip/_adjudicate_h3.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_adjudicate_h3.py:489` = `self_mutation()`; `lead/qc161_u0400_trip/_adjudicate_h3.py:490` = `main()` | `0,1+DATA` |
| 94 | `lead/qc161_u0400_trip/_adjudicate_h5.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_adjudicate_h5.py:587` = `self_mutation()`; `lead/qc161_u0400_trip/_adjudicate_h5.py:588` = `main()` | `0,1+DATA` |
| 95 | `lead/qc161_u0400_trip/_adjudicate_h6.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_adjudicate_h6.py:368` = `0`; `lead/qc161_u0400_trip/_adjudicate_h6.py:370` = `self_mutation()`; `lead/qc161_u0400_trip/_adjudicate_h6.py:371` = `main()` | `0,1+DATA` |
| 96 | `lead/qc161_u0400_trip/_drive_c2_x_e12.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_drive_c2_x_e12.py:617` = `main()` | `0,1,2,3+DATA` |
| 97 | `lead/qc161_u0400_trip/_drive_c2_x_e12_selftest.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_drive_c2_x_e12_selftest.py:64` = `4`; `lead/qc161_u0400_trip/_drive_c2_x_e12_selftest.py:789` = `main_suite()` | `0,1,4+DATA` |
| 98 | `lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_drive_c2_x_probe_v2.py:1046` = `main()` | `0,1,2,3+DATA` |
| 99 | `lead/qc161_u0400_trip/_preflight_h1.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_preflight_h1.py:196` = `1` | `0,1` |
| 100 | `lead/qc161_u0400_trip/_preview_h7_forms.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_preview_h7_forms.py:95` = `'unknown mode'`; `lead/qc161_u0400_trip/_preview_h7_forms.py:227` = `main()` | `0,1` |
| 101 | `lead/qc161_u0400_trip/_probe_d09b_hang.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_probe_d09b_hang.py:480` = `main()` | `0,2` |
| 102 | `lead/qc161_u0400_trip/_probe_h5_wer_census.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_probe_h5_wer_census.py:299` = `main()` | `0,1+DATA` |
| 103 | `lead/qc161_u0400_trip/_trip_plan_h1.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_trip_plan_h1.py:363` = `main()` | `0,1+DATA` |
| 104 | `lead/qc161_u0400_trip/_verify_dumps_rip.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_verify_dumps_rip.py:207` = `main()` | `0,1+DATA` |
| 105 | `lead/qc161_u0400_trip/_verify_h2e_smoke.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_verify_h2e_smoke.py:345` = `main()` | `0,1+DATA` |
| 106 | `lead/qc161_u0400_trip/_verify_judge_h2.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_verify_judge_h2.py:127` = `'★ 变异 %s 锚点不唯一（出现 %d 次）—— 拒绝将就：%r' % (label, n, anchor[:80])`; `lead/qc161_u0400_trip/_verify_judge_h2.py:134` = `'判档器不存在: %s' % JUDGE`; `lead/qc161_u0400_trip/_verify_judge_h2.py:332` = `main()` | `0,1+DATA` |
| 107 | `lead/qc161_u0400_trip/_verify_launcher_h2.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_verify_launcher_h2.py:66` = `'发射器不存在: %s' % LAUNCHER`; `lead/qc161_u0400_trip/_verify_launcher_h2.py:277` = `main()` | `0,1+DATA` |
| 108 | `lead/qc161_u0400_trip/_verify_preflight_h1.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_verify_preflight_h1.py:120` = `main()` | `0,1+DATA` |
| 109 | `lead/qc161_u0400_trip/_verify_trip_plan_h1.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_verify_trip_plan_h1.py:142` = `main()` | `0,1+DATA` |
| 110 | `lead/qc161_u0400_trip/_verify_vkio_fix.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_verify_vkio_fix.py:179` = `main()` | `0,1+DATA` |
| 111 | `lead/qc161_u0400_trip/_x_channel_probe_20261027.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/_x_channel_probe_20261027.py:517` = `main()` | `0,1,2,3+DATA` |
| 112 | `lead/qc161_u0400_trip/selfcheck_mutation_v2.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/qc161_u0400_trip/selfcheck_mutation_v2.py:127` = `main()` | `0,1,2` |
| 113 | `lead/r11_f2_fix_20261109/_f2_selftest.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/r11_f2_fix_20261109/_f2_selftest.py:151` = `1 if n_fail else 0` | `0,1+DATA` |
| 114 | `lead/r33e_merge_20261109/_re_j4_cases.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/r33e_merge_20261109/_re_j4_cases.py:28` = `'GUARD FAIL: %r' % guard`; `lead/r33e_merge_20261109/_re_j4_cases.py:202` = `0 if all((x['ok'] for x in A)) else 1` | `0,1+DATA` |
| 115 | `lead/r33e_merge_20261109/_re_linked.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/r33e_merge_20261109/_re_linked.py:348` = `main(sys.argv)` | `0,2` |
| 116 | `lead/r33e_merge_20261109/_re_parity_extra.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/r33e_merge_20261109/_re_parity_extra.py:49` = `'GUARD FAIL: read-only original drifted'`; `lead/r33e_merge_20261109/_re_parity_extra.py:269` = `0 if all((x['ok'] for x in A)) else 1` | `0,1+DATA` |
| 117 | `lead/r33e_merge_20261109/_re_run10_diff.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/r33e_merge_20261109/_re_run10_diff.py:31` = `'GUARD FAIL: original fingerprint drifted: %r' % guard_sl`; `lead/r33e_merge_20261109/_re_run10_diff.py:204` = `0 if all((a['ok'] for a in A)) else 1` | `0,1+DATA` |
| 118 | `lead/r33e_merge_20261109/_rev_cases.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/r33e_merge_20261109/_rev_cases.py:415` = `0 if all((x['ok'] for x in A)) else 1` | `0,1+DATA` |
| 119 | `lead/r33e_merge_20261109/_rev_core.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/r33e_merge_20261109/_rev_core.py:264` = `0 if all((a['ok'] for a in A)) else 1` | `0,1+DATA` |
| 120 | `lead/r33e_merge_20261109/_rev_edge25.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/r33e_merge_20261109/_rev_edge25.py:125` = `0 if all((x['ok'] for x in A)) else 1` | `0,1+DATA` |
| 121 | `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/re_line_20261105/A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py:356` = `0 if FAIL == 0 else 1` | `0,1+DATA` |
| 122 | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/test_except_freshness.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/re_line_20261105/W11_EXCEPT_FRESHNESS/candidate/test_except_freshness.py:224` = `main()` | `0,1+DATA` |
| 123 | `lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/re_line_20261105/W5_HARNESS_EXT/_w5_diff_proof.py:232` = `0 if success else 1` | `0,1+DATA` |
| 124 | `lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/re_line_20261105/W5_HARNESS_EXT/_w5_test.py:827` = `main()` | `0,1+DATA` |
| 125 | `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:654` = `EXIT_LAUNCH_LIMIT`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:670` = `EXIT_STAGE_TIMEOUT`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:681` = `EXIT_TRIP_BUDGET`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:1418` = `EXIT_PID_NOT_FOUND`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:1429` = `EXIT_PID_IDENTITY_UNVERIFIED`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:1445` = `EXIT_PID_NOT_FOUND`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:7765` = `f'★ U-3：★ --out-dir 落在受保护子树内 ⇒ 拒绝：{WORKDIR}'`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:7844` = `2`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:7860` = `2`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:8220` = `EXIT_PID_DEAD`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:8993` = `written`; `lead/re_line_20261105/W5_HARNESS_EXT/qc151_trip.harness8_v4_ext.py:9089` = `_entry()` | `0,1,2+DATA` |
| 126 | `lead/refsync_scope_20261109/_rs_carrier_scan.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/refsync_scope_20261109/_rs_carrier_scan.py:352` = `main()` | `0,1+DATA` |
| 127 | `lead/samedoc_link_20261109/_sl_link.py` | CONSTANT_EXIT | CONDITIONAL_EXIT | `lead/samedoc_link_20261109/_sl_link.py:255` = `main(sys.argv)` | `0,2` |
| 128 | `lead/samedoc_link_20261109/_sl_selftest.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/samedoc_link_20261109/_sl_selftest.py:170` = `0 if n_pass == len(results) else 1` | `0,1+DATA` |
| 129 | `lead/samedoc_link_20261109/_slv_multitest.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/samedoc_link_20261109/_slv_multitest.py:143` = `0 if n_pass == len(out) else 1` | `0,1+DATA` |
| 130 | `lead/samedoc_link_20261109/_slw_fix4.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/samedoc_link_20261109/_slw_fix4.py:133` = `0 if n_pass == len(results) else 1` | `0,1+DATA` |
| 131 | `lead/stale_pass_20261109/_sp_sandbox/d29/_w_d29_A.py` | NO_EXIT_AT_ALL | CONDITIONAL_EXIT | `lead/stale_pass_20261109/_sp_sandbox/d29/_w_d29_A.py:110` = `main()` | `0,1,2` |
| 132 | `lead/w2_samecause_20261109/_w2w_fp9.py` | CONDITIONAL_EXIT | CONDITIONAL_EXIT | `lead/w2_samecause_20261109/_w2w_fp9.py:45` = `0 if ok == 9 else 1` | `0,1+DATA` |

代表：`lead/d27_ruling_20261106/check_d27.py:59/99/101/107`（0/1/2 真分支，§2.4）、`lead/goal1_a8_fix_20261022/VERIFY_A8B.py:451/455`（`return 0 if not ref else 1`）、`lead/dtrigger_compare_20261107/_check_dtrigger.py:228`（`raise SystemExit(0 if ok else 1)`）、`lead/count_invariant_20261109/_ci_counterexamples.py:152`（`0 if all(RESULTS.values()) else 1`）、`lead/refsync_scope_20261109/_rs_carrier_scan.py:349/352`（72 次被引，CONDITIONAL）。4 件生产门禁 d27–d30 **不在 413 批内**（在 kd 173 普查内），故不列本表，见 §2.4。

### 附录 D — 44 件「机械 verdict ≠ AST 依据」逐件并列

依据源：`_cev_adjudicate_stdout.txt:5-93`（复核件独立分类器逐件 AST 依据）、`_ce_compare_stdout.txt:4-55`、我实跑 `_cew_evidence.py` 的 site `文件:行`。分组：A=31 件字面量分支实为多状态；B=9 件漏 `raise SystemExit`；C=2 件漏 raise 的恒 0；D=2 件嵌套 return 误算；E=混合形态（归 A/B）。

| # | 组 | rel | 编排方机械 verdict | 最终（依据为准） | AST 依据（`文件:行`） | 可达状态 |
|---|---|---|---|---|---|---|
| 1 | D | `lead/bexec_n4_20261108/_n4_ast_scan.py` | **CONDITIONAL_EXIT** | **CONSTANT_EXIT** | `lead/bexec_n4_20261108/_n4_ast_scan.py:304` `main()`；{"orch": "CONDITIONAL_EXIT", "agent_final": "CONSTANT_EXIT", "my_mechanical": "CONSTANT_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_retu | `[0]` |
| 2 | D | `lead/slowframe_round2_20261107/_proxy_covariate_accounting.py` | **CONDITIONAL_EXIT** | **CONSTANT_EXIT** | `lead/slowframe_round2_20261107/_proxy_covariate_accounting.py:294` `main()`；{"orch": "CONDITIONAL_EXIT", "agent_final": "CONSTANT_EXIT", "my_mechanical": "CONSTANT_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_retu | `[0]` |
| 3 | A | `lead/b2b_candidate_review3_20261107/_check_candidate_r3.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/b2b_candidate_review3_20261107/_check_candidate_r3.py:276` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1, 2]` |
| 4 | A | `lead/b2b_isolated_20261107/_integ_check_isolated.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/b2b_isolated_20261107/_integ_check_isolated.py:276` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1, 2]` |
| 5 | A | `lead/count_invariant_20261109/_ci_checks.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/count_invariant_20261109/_ci_checks.py:200` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1, 2]` |
| 6 | A | `lead/count_invariant_20261109/_cii_checks.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/count_invariant_20261109/_cii_checks.py:198` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1, 2]` |
| 7 | A | `lead/deliverable_anchor_20261108/_da_anchor_selfcheck.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/deliverable_anchor_20261108/_da_anchor_selfcheck.py:39` `main(sys.argv[1])`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 2, 3, 4]` |
| 8 | A | `lead/deliverable_anchor_20261108/_spec2_anchor_check.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/deliverable_anchor_20261108/_spec2_anchor_check.py:77` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 3, 4, 5]` |
| 9 | A | `lead/deliverable_anchor_20261108/_verify_hy4_anchor.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/deliverable_anchor_20261108/_verify_hy4_anchor.py:271` `2`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 2]` |
| 10 | A | `lead/goal1_a8_fix_20261022/_gen_harness4.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal1_a8_fix_20261022/_gen_harness4.py:389` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 11 | A | `lead/goal1_boot_fingerprint_20261022/_redact_fingerprint.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal1_boot_fingerprint_20261022/_redact_fingerprint.py:150` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1, 2]` |
| 12 | A | `lead/goal2_onetime_census_20261022/VERIFY_GUARD.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_onetime_census_20261022/VERIFY_GUARD.py:62` `2`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 2]` |
| 13 | A | `lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_fixv5_20261022/_rc4_ab_probe.py:924` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 2, 3]` |
| 14 | A | `lead/goal2_rc4_trigger_20261022/VERIFY_RC4_TRIPS.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/VERIFY_RC4_TRIPS.py:188` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1, 2]` |
| 15 | A | `lead/goal2_rc4_trigger_20261022/_dispatch_expand.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_dispatch_expand.py:324` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 16 | A | `lead/goal2_rc4_trigger_20261022/_dispatch_negctl.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_dispatch_negctl.py:22` `1`; `lead/goal2_rc4_trigger_20261022/_dispatch_negctl.py:62` `1`; `lead/goal2_rc4_trigger_20261022/_dispatch_negctl.py:64` `0`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 17 | A | `lead/goal2_rc4_trigger_20261022/_guard_audit.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_guard_audit.py:251` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 18 | A | `lead/goal2_rc4_trigger_20261022/_input_path.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_input_path.py:203` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 19 | A | `lead/goal2_rc4_trigger_20261022/_insert_corrections.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_insert_corrections.py:100` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 20 | A | `lead/goal2_rc4_trigger_20261022/_reachability.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_reachability.py:191` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1, 2, 3]` |
| 21 | A | `lead/goal2_rc4_trigger_20261022/_vtable_census.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_vtable_census.py:162` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 22 | A | `lead/goal2_rc4_trigger_20261022/_vtable_closure.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_vtable_closure.py:161` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 23 | A | `lead/goal2_rc4_trigger_20261022/_window_anchor.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/goal2_rc4_trigger_20261022/_window_anchor.py:358` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 24 | A | `lead/k1bit_detect_20261109/_kdv_legal_all.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/k1bit_detect_20261109/_kdv_legal_all.py:25` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 25 | A | `lead/matrix_ab_ruling_20261109/_ab_probe.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/matrix_ab_ruling_20261109/_ab_probe.py:23` `'path outside allowed BASE rejected: %r' % p`; `lead/matrix_ab_ruling_20261109/_ab_probe.py:236` `1`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]+DATA` |
| 26 | A | `lead/matrix_ab_ruling_20261109/_rv2_probe_20261109.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/matrix_ab_ruling_20261109/_rv2_probe_20261109.py:387` `1`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 27 | A | `lead/matrix_binding_20261108/_m_rebuild.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/matrix_binding_20261108/_m_rebuild.py:42` `2`; `lead/matrix_binding_20261108/_m_rebuild.py:90` `2`; `lead/matrix_binding_20261108/_m_rebuild.py:109` `2`; `lead/matrix_binding_20261108/_m_rebuild.py:118` `2`; `lead/matrix_binding_20261108/_m_rebuild.py:164` `2`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 2]` |
| 28 | A | `lead/qc161_u0400_trip/_preflight_h1.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/qc161_u0400_trip/_preflight_h1.py:196` `1`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 29 | A | `lead/qc161_u0400_trip/_preview_h7_forms.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/qc161_u0400_trip/_preview_h7_forms.py:95` `'unknown mode'`; `lead/qc161_u0400_trip/_preview_h7_forms.py:227` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1]` |
| 30 | A | `lead/qc161_u0400_trip/_probe_d09b_hang.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/qc161_u0400_trip/_probe_d09b_hang.py:480` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 2]` |
| 31 | A | `lead/qc161_u0400_trip/selfcheck_mutation_v2.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/qc161_u0400_trip/selfcheck_mutation_v2.py:127` `main()`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 1, 2]` |
| 32 | A | `lead/r33e_merge_20261109/_re_linked.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/r33e_merge_20261109/_re_linked.py:348` `main(sys.argv)`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 2]` |
| 33 | A | `lead/samedoc_link_20261109/_sl_link.py` | **CONSTANT_EXIT** | **CONDITIONAL_EXIT** | `lead/samedoc_link_20261109/_sl_link.py:255` `main(sys.argv)`；{"orch": "CONSTANT_EXIT", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_r | `[0, 2]` |
| 34 | B | `lead/b2b_design_20261106/_draft_semantics_check.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/b2b_design_20261106/_draft_semantics_check.py:633` `'usage: build | verify | matrix | anchors'`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1]` |
| 35 | B | `lead/c07_gate_fix_20261109/_g1g5_fp.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/c07_gate_fix_20261109/_g1g5_fp.py:83` `main()`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1]+DATA` |
| 36 | B | `lead/control_20261106/gate_n1_lf_20261107.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/control_20261106/gate_n1_lf_20261107.py:150` `0 if not fails else 1`; `lead/control_20261106/gate_n1_lf_20261107.py:156` `1`; `lead/control_20261106/gate_n1_lf_20261107.py:370` `0 if not fails else 1`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1]+DATA` |
| 37 | B | `lead/dtrigger_compare_20261107/_check_dtrigger.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/dtrigger_compare_20261107/_check_dtrigger.py:228` `0 if ok else 1`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1]+DATA` |
| 38 | B | `lead/dtrigger_compare_20261107/_check_metrics.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/dtrigger_compare_20261107/_check_metrics.py:292` `0 if ok else 1`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1]+DATA` |
| 39 | B | `lead/gate_n13_20261109/_n13v_migration.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/gate_n13_20261109/_n13v_migration.py:170` `main()`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1]+DATA` |
| 40 | B | `lead/n10c04_ruling_20261108/_rv_n10c04_ruling_audit.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/n10c04_ruling_20261108/_rv_n10c04_ruling_audit.py:7` `'repository argument must be an absolute path'`; `lead/n10c04_ruling_20261108/_rv_n10c04_ruling_audit.py:64` `0 if all_ok else 1`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1]+DATA` |
| 41 | B | `lead/r11_f2_fix_20261109/_f2_selftest.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/r11_f2_fix_20261109/_f2_selftest.py:151` `1 if n_fail else 0`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1]+DATA` |
| 42 | B | `lead/stale_pass_20261109/_sp_sandbox/d29/_w_d29_A.py` | **NO_EXIT_AT_ALL** | **CONDITIONAL_EXIT** | `lead/stale_pass_20261109/_sp_sandbox/d29/_w_d29_A.py:110` `main()`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONDITIONAL_EXIT", "my_mechanical": "CONDITIONAL_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_ | `[0, 1, 2]` |
| 43 | C | `lead/gate_n13_20261109/_n13v_final_probe.py` | **NO_EXIT_AT_ALL** | **CONSTANT_EXIT** | `lead/gate_n13_20261109/_n13v_final_probe.py:126` `main()`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONSTANT_EXIT", "my_mechanical": "CONSTANT_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_return | `[0]` |
| 44 | C | `lead/qc161_u0400_trip/_probe_x_glm_addr_check.py` | **NO_EXIT_AT_ALL** | **CONSTANT_EXIT** | `lead/qc161_u0400_trip/_probe_x_glm_addr_check.py:44` `0`；{"orch": "NO_EXIT_AT_ALL", "agent_final": "CONSTANT_EXIT", "my_mechanical": "CONSTANT_EXIT", "agree_agent_final": true, "ast_facts": {"main_lit_return | `[0]` |

复核件 `_cev_compare_stdout.txt:5` 记 `orchestrator vs mine n_diff 44 Counter({CONSTANT→CONDITIONAL:31, NO_EXIT→CONDITIONAL:9, CONDITIONAL→CONSTANT:2, NO_EXIT→CONSTANT:2})`，与判定 `_ce_final_out.json:diffs` 逐件全等（`_cev_compare_stdout.txt:55`：`agree 44 disagree 0`）。

### 附录 E — 两件台账全部 24 个标记行逐行清单

源：`_ce_impact_out.json:ledger.lines`（我本会话实读两件台账原文逐行核对）、`_cev_ledger_stdout.txt:12-36`。`flat` = 「行内任一 basename 命中零信息类」（编排方 口径）；`主语类` = 「`EXIT=0` 最近 basename」的 AST 最终定级。

| # | 台账:行 | 行内 basenames → 类 | 原文摘录 | flat 命中 | `EXIT=0` 主语 / 类 | 处置 |
|---|---|---|---|---|---|---|
| 1 | `lead/PENDING_DECISIONS.md:92` | _d30_facts.py→NO_EXIT_AT_ALL, check_d30.py→NOT_IN_413 | 裁决书 `lead/d30_ruling_20261106/RULING_D30.md`（13,197 B / `d5afc90c50bbf57b…3983d04f`）+ 事实核证 `FACTCHECK.md`（11,394 B）+ `_d30_facts.py`/`_out.txt`；门禁 `ch | 是 | `check_d30.py` / `NOT_IN_413` | **加注：归错对象（主语是 CONDITIONAL 门禁）** |
| 2 | `lead/PENDING_DECISIONS.md:105` | _d29_facts.py→NO_EXIT_AT_ALL, check_d29.py→NOT_IN_413 | 裁决书 `lead/d29_ruling_20261106/RULING_D29.md`（12,258 B / `325c950eec4d3275…7212afb`）+ `FACTCHECK.md`（12,647 B）+ `_d29_facts.py`/`_out.txt`；门禁 `check_d2 | 是 | `check_d29.py` / `NOT_IN_413` | **加注：归错对象（主语是 CONDITIONAL 门禁）** |
| 3 | `lead/PENDING_DECISIONS.md:117` | _d28_facts.py→NO_EXIT_AT_ALL, check_d28.py→NOT_IN_413 | 裁决书 `lead/d28_ruling_20261106/RULING_D28.md`（13,897 B / `29bb247fbf82d80a…763b5f15`）+ `FACTCHECK.md`（13,028 B）+ `_d28_facts.py`/`_out.txt`；门禁 `check_d | 是 | `check_d28.py` / `NOT_IN_413` | **加注：归错对象（主语是 CONDITIONAL 门禁）** |
| 4 | `lead/PENDING_DECISIONS.md:129` | _d27_facts.py→NO_EXIT_AT_ALL, check_d27.py→NOT_IN_413 | 裁决书 `lead/d27_ruling_20261106/RULING_D27.md`（17,658 B，71 处引用）+ 事实核证 `FACTCHECK.md` + `_d27_facts.py`/`_out.txt`；门禁 `check_d27.py` 实跑 **exit=0**。 | 是 | `check_d27.py` / `NOT_IN_413` | **加注：归错对象（主语是 CONDITIONAL 门禁）** |
| 5 | `lead/PENDING_DECISIONS.md:162` | _d26_facts.py→NO_EXIT_AT_ALL, check_d26.py→NOT_IN_413 | 裁决书 `lead/d26_ruling_20261106/RULING_D26.md`（15,373 B）+ `FACTCHECK.md` + `_d26_facts.py`/`_out.txt`；门禁 `check_d26.py` 实跑 **exit=0**。 | 是 | `check_d26.py` / `NOT_IN_413` | **加注：归错对象（主语是 CONDITIONAL 门禁）** |
| 6 | `lead/PENDING_DECISIONS.md:186` | _d25_facts.py→CONDITIONAL_EXIT, check_d25.py→NOT_IN_413 | 裁决书 `lead/d25_ruling_20261106/RULING_D25.md`（15,545 B）+ 事实核证 `FACTCHECK.md` + `_d25_facts.py`/`_out.txt`；门禁 `check_d25.py` 实跑 **exit=0**。 | 否 | `check_d25.py` / `NOT_IN_413` | 无需加注（CONDITIONAL） |
| 7 | `lead/GOAL_THREE_TARGETS_20261018.md:260` | qc151_trip.py→NOT_IN_413, path_ab_probe.py→NOT_IN_413, dialog_text_probe.py→NOT_IN_413, launch_e2_shortpath.py→NOT_IN_413 | - 2026-10-20 20:1x **E2 短路径趟 = L1 首次完整生命周期（日志 §313 续）**：out-dir 改 `l1a_20261020`（载体 129 字符 < 131）后 **EXIT=0**（main/finalize 全 0）；导航链 nav_menu→nav_setu | 否 | `qc151_trip.py` / `NOT_IN_413` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 8 | `lead/GOAL_THREE_TARGETS_20261018.md:261` | mkdiff.py→CONDITIONAL_EXIT, verify_hooks.py→NOT_IN_413 | - 2026-10-20 22:4x **★★ P1+SBH 合批编译通过 + verify_hooks 假绿揪出（日志 §314）**：5 段合并 5/5 干净命中、**CL_EXIT=0 / LINK_EXIT=0**（产物 `build/ra2render_merged.dll` 178,68 | 否 | `mkdiff.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 9 | `lead/GOAL_THREE_TARGETS_20261018.md:7196` | _w5_diff_proof.py→CONDITIONAL_EXIT | / `_w5_diff_proof.py` + `_out.txt` / **我亲自重跑** / `EXIT=0`，最终判定 **PASS** / | 否 | `_w5_diff_proof.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 10 | `lead/GOAL_THREE_TARGETS_20261018.md:7197` | _w5_test.py→CONDITIONAL_EXIT | / `_w5_test.py` + `_out.txt` / **我亲自重跑** / `EXIT=0`，6 条用例全 PASS / | 否 | `_w5_test.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 11 | `lead/GOAL_THREE_TARGETS_20261018.md:7258` | _w5_diff_proof.py→CONDITIONAL_EXIT, _w5_test.py→CONDITIONAL_EXIT | 1. **我亲自重跑**：`_w5_diff_proof.py`、`_w5_test.py`（均 `EXIT=0`）+ 我自己的两支静态核查脚本。 | 否 | `_w5_test.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 12 | `lead/GOAL_THREE_TARGETS_20261018.md:7401` | _w5_diff_proof.py→CONDITIONAL_EXIT | _w5_diff_proof.py  → EXIT=0，删 8 块后 SHA256 == 母本 38244d29…752a8   PASS | 否 | `_w5_diff_proof.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 13 | `lead/GOAL_THREE_TARGETS_20261018.md:7404` | _w5_test.py→CONDITIONAL_EXIT | _w5_test.py        → EXIT=0，6 条用例全 PASS | 否 | `_w5_test.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 14 | `lead/GOAL_THREE_TARGETS_20261018.md:7446` | _w5_test.py→CONDITIONAL_EXIT | `_w5_test.py` **均由我重跑**（均 `EXIT=0`）；`W5_HARNESS_EXT.md` 六节结构与两个标记在场。 | 否 | `_w5_test.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 15 | `lead/GOAL_THREE_TARGETS_20261018.md:7566` | test_frame_edge_sampler.py→CONDITIONAL_EXIT | python -I -X utf8 ".../A1_SAMPLER_CANDIDATE/test_frame_edge_sampler.py"   # EXIT=0  PASS=85 FAIL=0 | 否 | `test_frame_edge_sampler.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 16 | `lead/GOAL_THREE_TARGETS_20261018.md:7567` | _w5_test.py→CONDITIONAL_EXIT | python -I -X utf8 ".../W5_HARNESS_EXT/_w5_test.py"                        # EXIT=0  6 用例全 PASS | 否 | `_w5_test.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 17 | `lead/GOAL_THREE_TARGETS_20261018.md:7568` | _w5_diff_proof.py→CONDITIONAL_EXIT | python -I -X utf8 ".../W5_HARNESS_EXT/_w5_diff_proof.py"                  # EXIT=0  最终判定 PASS | 否 | `_w5_diff_proof.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 18 | `lead/GOAL_THREE_TARGETS_20261018.md:7569` | _d21_burden5.py→NO_EXIT_AT_ALL | python -I -X utf8 ".../D21_RULING/_d21_burden5.py"                        # EXIT=0 | 是 | `_d21_burden5.py` / `NO_EXIT_AT_ALL` | **加注：真零信息** |
| 19 | `lead/GOAL_THREE_TARGETS_20261018.md:7634` | _leader_crossframe_check.py→NO_EXIT_AT_ALL | > 交付：`V6_V3_REVIEW/_leader_crossframe_check.py` + `_out.txt`（`EXIT=0`）。零真机。 | 是 | `_leader_crossframe_check.py` / `NO_EXIT_AT_ALL` | **加注：真零信息** |
| 20 | `lead/GOAL_THREE_TARGETS_20261018.md:8383` | _a7_acf_probe.py→NO_EXIT_AT_ALL | `_leader/_a7_acf_probe.py` + `_a7_acf_probe_out.txt`（均 `EXIT=0`）。 | 是 | `_a7_acf_probe.py` / `NO_EXIT_AT_ALL` | **加注：真零信息** |
| 21 | `lead/GOAL_THREE_TARGETS_20261018.md:9220` | test_except_freshness.py→CONDITIONAL_EXIT | 1. **我亲跑**：`test_except_freshness.py` **14/14 PASS / EXIT=0**（上面贴的就是我自己的输出）； | 否 | `test_except_freshness.py` / `CONDITIONAL_EXIT` | 无需加注（主语 CONDITIONAL / UNRESOLVED） |
| 22 | `lead/GOAL_THREE_TARGETS_20261018.md:9406` | test_except_freshness.py→CONDITIONAL_EXIT | 1. **我亲验**：`test_except_freshness.py` 的 **14/14 PASS**（两次跑，§598 与本轮）； | 否 | `（无 EXIT=0 token）` / `未验` | 未验（无 EXIT=0 token） |
| 23 | `lead/GOAL_THREE_TARGETS_20261018.md:9588` | _intra_frame_census.py→NO_EXIT_AT_ALL | > 探针 `_leader/_intra_frame_census.py`，输出 `_leader/_intra_frame_census_out.txt`（`EXIT=0`）。 | 是 | `_intra_frame_census.py` / `NO_EXIT_AT_ALL` | **加注：真零信息** |
| 24 | `lead/GOAL_THREE_TARGETS_20261018.md:9679` | _intra_frame_census.py→NO_EXIT_AT_ALL | 1. **我亲跑**：`_intra_frame_census.py` 全量 15 窗，`EXIT=0`，输出 40+ 行表格 + 三组汇总。 | 是 | `_intra_frame_census.py` / `NO_EXIT_AT_ALL` | **加注：真零信息** |

`CONSTANT_EXIT` 在两件台账里 **0 行**（`_cev_ledger_stdout.txt:2`：`n_constant_flat 0 / n_constant_subject 0`）。编排方 `ledger_hits_total` `{PENDING:12, GOAL_THREE:23}` = 35 是 **basename 出现次数**，不是行数（`_cev_ledger2_stdout.txt`：`raw_basename_occurrences 35 / marked_lines_with_py 24`）。

