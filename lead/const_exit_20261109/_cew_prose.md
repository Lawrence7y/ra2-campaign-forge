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

<!--APPENDIX_MARKER-->
