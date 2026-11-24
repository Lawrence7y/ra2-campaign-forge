# 出口判据设计与验证报告（lead/exit_criterion_20261110/）

任务：设计「该不该有出口」与「出口合不合格」的判据，并用真实脚本做正反控。
约束执行情况：零真机（未启动任何游戏进程）、零采样代码（未写 hook/dump/注入）、
两件台账与全部只读目录未改（本任务只新建了写域内文件）、不 commit、不 push。
判据本体 = `_ec_criterion.py`（纯静态 AST，零执行被检脚本）。

---

## 0. 基线指纹复核（实跑 `_ec_fp_baseline.py`，15/15 MATCH）

| 对象 | SHA256 | 字节数 | 结果 |
|---|---|---|---|
| lead/PENDING_DECISIONS.md | 3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7 | 52419 | MATCH |
| lead/GOAL_THREE_TARGETS_20261018.md | 2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede | 759518 | MATCH |
| lead/const_exit_20261109/CONST_EXIT_CENSUS.md | ed3c379fc1021b85a1605c898bee370935e49a9300efe6f6416163f652893f90 | 165107 | MATCH |
| lead/const_exit_20261109/_ce_final_out.json | 87bd73318897da4bc7d9a0449b92396d258b42294c4e5076e09d9274b6e6d14b | 312187 | MATCH |
| lead/andk_rerun_20261109/ANDK_RERUN.md | 9dabbed8c27ccbc7f4fffc2f2dae37211d1cbe19c42c85b3def76abfccda88d5 | 61049 | MATCH |
| lead/andk_rerun_20261109/_ak_summary.json | 36af304c7f7cfbd111686eb0d9bed642d42b7f7111ec5e422dc471ab253c9c00 | 67597 | MATCH |
| lead/d27_ruling_20261106/check_d27.py | 3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c | 3764 | MATCH |
| lead/d28_ruling_20261106/check_d28.py | 5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268 | 4539 | MATCH |
| lead/d29_ruling_20261106/check_d29.py | 2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14 | 3906 | MATCH |
| lead/d30_ruling_20261106/check_d30.py | 6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd | 3926 | MATCH |
| lead/re_line_20261105/D21_RULING/_d21_burden5.py | 7e4091381486663da57fbd2c0ef113bcbc3d6d69352ddf2762a2e891a7ac36ba | 2929 | MATCH |
| lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py | 2d17264e77251270d506c488760df020b18380023d40d118ce8455b7bd930ae6 | 4688 | MATCH |
| lead/re_line_20261105/_leader/_a7_acf_probe.py | e42a79f3c1d1214f8cd7ebf01b92505f095dd7f6db7b1bf2434f3d833f3ac6e5 | 5763 | MATCH |
| lead/re_line_20261105/_leader/_intra_frame_census.py | c4e537ab45dc01219e1ccea0f3e61edfdbfcdcd94f39b0ce6c91c567fd7f0eba | 6279 | MATCH |
| lead/goal1_a8_fix_20261022/VERIFY_A8.py | 179f3af88fac380437311fe4c52f2d8367733f3b92c8b13ab99cb742d12544a2 | 38317 | MATCH |

---

## 1. 第一步复核结论

### 1(a) 9 件样本事实核对（实跑 `_ec_s1_facts.py`）

- **exit_sites / n_exit / has_print / bytes / n_lines：9/9 逐字段一致**（包括四件零出口件的
  `exit_sites=[]` 与 VERIFY_A8 的 `[["call", 800, "sys.exit(main())"]]`）。
- **write_lines：8/9 可复现为「`open(` 调用行」，第 9 件（VERIFY_A8）口径无法完全复现**：
  - `_d21_burden5.py` [20]、`_a7_acf_probe.py` [35,161]、`_intra_frame_census.py` [37,94,165] 全部是
    `io.open(` 调用行（AST 验证，含**读** open）；四件门禁 [] 一致。
  - VERIFY_A8 的 [87,284,285,286,287,303,408,425]：8 行全部含 `ast.dump(`（内存序列化），
    但该文件另有 6 处 `ast.dump(`（:427,:437,:450,:710,:711,:732）**未**被计入；假设一
    （`open\(|\.dump\(|\.write\(` 子串）得 14 行，假设二（仅 `open\(`）得 0 行，均不等于 8 行。
    **结论：编排方 write_lines 的产生规则无法从两个合理假设复现（未验其确切规则），
    且该字段不能当「写盘证据」用**——VERIFY_A8 的 8 行没有一行是真写盘（真写 = 0）。
- **真写盘（w/a/x/+ 模式或 write_text/write_bytes，本判据口径）**：
  `_a7_acf_probe.py:161`（`open('w')` → `_a7_acf_probe_out.txt`）、
  `_intra_frame_census.py:165`（`open('w')` → `_intra_frame_census_out.txt`）；其余 7 件真写 = 0。

### 1(b) 四件零信息对象的产物实证 + GOAL 登记行

| 脚本 | 真写盘 | 产物 | stdout | GOAL 登记行（实读原文） |
|---|---|---|---|---|
| `_d21_burden5.py` | 无 | **stdout-only**（无 out.txt 由脚本产出；`D21_RULING/_d21_burden5_out.txt` 在盘上存在，系外部捕获） | 26 处 print（复算表格） | `:7569` 只登记了命令 + `# EXIT=0` |
| `_leader_crossframe_check.py` | 无 | **stdout-only**（`_leader_crossframe_check_out.txt` 在盘上存在，外部捕获） | 44 处 print（三场景模拟+判定） | `:7634` 声称交付 `_out.txt`（EXIT=0） |
| `_a7_acf_probe.py` | `:161` | `_a7_acf_probe_out.txt`（OUT 缓冲镜像，P() 同时 print+append） | 1 处 print + P() | `:8383` 脚本+产物（均 EXIT=0） |
| `_intra_frame_census.py` | `:165` | `_intra_frame_census_out.txt`（OUT 缓冲镜像） | 1 处 print + P() | `:9588`、`:9679`（EXIT=0） |

**结论：正确处置是「改登记口径」（产物+指纹），不是加注**——四件的 EXIT=0 全部零信息；
其中两件（_d21/_crossframe）脚本本体根本没有出口也没有写盘，登记的产物是外部捕获的 stdout。

在盘产物指纹（实跑 hashlib，本任务已取）：

```
lead/re_line_20261105/D21_RULING/_d21_burden5_out.txt             1803 字节
  sha256 = 0d77c9541ddb2eda0eacc15c5251b06667bfa41a1dd49a66012d58355723419a
lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check_out.txt  2839 字节
  sha256 = 2cf4100776eb7461ef784e4fa8ec8f192439851604fde737dcb0816f045f50dc
lead/re_line_20261105/_leader/_a7_acf_probe_out.txt               3318 字节
  sha256 = 54145df6e2e1fa818df82e7ccd92e30ee8bbce972f32cdf9983e9aa50287a439
lead/re_line_20261105/_leader/_intra_frame_census_out.txt         3744 字节
  sha256 = d056f88f331e968b1b6c9bf75c104d35f8df0f2e3b98829f7d94bef1b7940993
```

### 1(c) 四件门禁的出口表达式（正控样板）

| 门禁 | 出口站点 | 出口状态来源（实读 + 判据 E1 实证） |
|---|---|---|
| check_d27.py | `:107` `sys.exit(main())`（call） | main 返回 2@:59（文件缺失）、1@:99（errors 非空）、0@:101（全过）→ 状态 {0,1,2} |
| check_d28.py | `:122` `raise SystemExit(main())`（raise） | main 返回 2@:111、1@:114、0@:116 → {0,1,2} |
| check_d29.py | `:110` `raise SystemExit(main())`（raise） | main 返回 2@:100、1@:103、0@:105 → {0,1,2} |
| check_d30.py | `:110` `raise SystemExit(main())`（raise） | main 返回 2@:100、1@:103、0@:105 → {0,1,2} |

出口读的是**裁决函数 main() 的返回值**；main 内 8 项机械检查各自把失败 append 进
errors/failures/missing（check_d27 的 7 处 append：:67,:70,:74,:79,:88,:92,:94），空列表 ⇔ 通过。
**它们不只是「有出口」，而是合格出口的样板**：E1 {0,1,2}✓ E2 多来源合取✓ E3 handler 全部转入
失败登记✓ E4 打印迭代的就是同一批列表✓（第三步正控全 PASS，见 §3）。

一处如实记录：上游提示说 d29/d30 「其实 any() 折叠」——指的是**检查内部**的关键词判定
（`if not any(matches)` @check_d29.py:87 / check_d30.py:87：一个小节命中任一关键词即算该项通过）。
这是检查粒度的 OR 折叠，**不改变出口层面的合取结构**（8 项检查任一失败仍 → exit 1）。
判据按出口层合取判 E2=PASS，并把该 OR 折叠记为检查粒度事实，不作为 NEEDS_FIX 依据。

---

## 2. 第二步判据（完整定义与实现 = `_ec_criterion.py`）

### 2(a) 该不该有出口——分类判别轴 = 「判定的消费通道」

| 类 | 定义 | 机器可判特征（AST/结构，非文件名） | 为什么 |
|---|---|---|---|
| **GATE** | 存在以「程序可消费的二值裁决」形态存在、应送达调用方控制流的判定 ⇒ **需要出口** | GA1 出口管道（SystemExit 家族站点且状态集≥2/动态）；GA2 stdout 摘要通道上的互斥裁决对（if/elif 两臂或 IfExp 两臂出现 POS/NEG 词对，或单臂 NEG）且判定条件非恒定；GA3 失败累积（≥2 处 append 喂「if X: return 非零」门） | stdout 上的散文结论是报告；**互斥 PASS/FAIL 对才是布尔决策接口**——调用方靠退出码/分支消费它。单侧负裁决同理（调用方靠其缺席推断通过） |
| **ARTIFACT** | 产物是文件 ⇒ 退出码无关 ⇒ **不需要出口** | 真写盘：w/a/x/+ 模式 open、write_text、write_bytes（读 open 不算——上一轮口径混淆的教训） | 消费方读文件；登记「产物+指纹」即可，exit 码不承载判定 |
| **PROBE** | 产物是观测值+解读，不判对错 ⇒ **不需要出口** | 无出口/无裁决对/无真写盘，有 print（或 emitter→缓冲→print 数据流） | 产物=观测值；登记通道是捕获的 stdout/摘要文本 |
| **UNKNOWN** | 证据不足/冲突 ⇒ **逐件人工** | 解析失败；四类特征全无（疑似库模块/零可见产物脚本——附库形态提示） | 宁可 UNKNOWN 不许猜 |

摘要通道的实现细节：print 直调，或「纯 append 的模块级 emitter 函数→缓冲变量→print」数据流
（`_c97_check.py` 的 emit():20→out:19→print:205 即此形态）。**通道外的裁决词（return 值、字典值、
outcome 赋值等 verdict-as-data）明确不判**——那是声明的静态盲区（见 §5c），交人工。
被检对象的领域词（如被测检测器自身的 PASS/CATCH 判词）因不成对/不在条件两臂而不会误触发。

### 2(b) 合格出口四要件（仅 GATE 适用；每条含实现与静态局限）

| 要件 | 判定 | 实现（AST） | 无法纯静态判的部分 |
|---|---|---|---|
| **E1 非常量** | 出口可达状态集合 \|S\|≥2 或存在动态状态表达式 | 从出口参数回溯裁决函数（`sys.exit(main())`→解析 main），收集全部 Return 整数常量；内联动态表达式（`0 if ok else 1`）⇒ dynamic；\|S\|==1 且非 dynamic ⇒ FAIL | 分支可达性（死分支）——须运行时复核 |
| **E2 合取驱动** | 0 分支由「全部检查通过」驱动 | 有裁决函数：失败登记点（append/extend/add/+= [...]）+「if→return 非零」早退门总数 k≥2 ⇒ PASS；内联动态出口：追踪驱动名的 And 聚合赋值/累计(+=)/global-checker 调用点/出口比较，证据≥2 ⇒ PASS(w)，==1 ⇒ FAIL 单标量 | 登记点是否语义独立；扫描器形态代码的早退门会高估 k |
| **E3 无吞** | 失败不经被吞的异常通道消失、异常通道不顶替出口 | 每个 ExceptHandler 若体「惰性」（无 re-raise/出口调用/失败登记/非零 return/print/对自定义函数的调用）⇒ 吞没候选 ⇒ FAIL；无出口管道而以 ≥2 条带裁决词的 assert 承载裁决 ⇒ E3_IMPLICIT_EXCEPTION | 语义级吞没（打印无害文案但丢失失败） |
| **E4 摘要绑定** | 同一次运行里退出码与逐项摘要来自同一份数据 | 退出门守卫名 G（门条件 Name+失败登记目标名+内联出口驱动名）∩ 摘要引用名 P（print 参数 Name+**写盘调用参数 Name**+迭代打印/写盘的循环源名）≠∅ ⇒ PASS | 名字级≠值级；打印裁剪子集——须运行时对照 |

### 2(c) 判定函数

签名（完整实现在 `_ec_criterion.py::classify`，约 530 行，可粘贴独立运行）：

```
classify(rel, ast_tree, source_text)
  → {"class": GATE|ARTIFACT|PROBE|UNKNOWN,
     "verdict": OK|EXIT_ZERO_INFO|NEEDS_FIX,
     "e": {E0,E1,E2,E3,E4},          # E 要件逐条 PASS/FAIL/UNKNOWN
     "reasons": [(code, "rel:line", 细节), ...],   # 每条带 file:line
     "facts": {出口/真写/print/裁决对/assert 计数}}
```

verdict 规则：GATE 无出口 ⇒ NEEDS_FIX(E0)；E1 FAIL ⇒ NEEDS_FIX（VERIFY_A8 型）；
E2/E3/E4 任一 FAIL ⇒ NEEDS_FIX；E 不确定 ⇒ NEEDS_FIX(需人工)；全过 ⇒ OK。
ARTIFACT/PROBE 无出口 ⇒ OK（出口不适用）；带常量出口 ⇒ EXIT_ZERO_INFO（登记产物不登记 EXIT）。
UNKNOWN ⇒ NEEDS_FIX（理由码 UNKNOWN_MANUAL：语义=需人工，非需改码）。

---

## 3. 第三步正反控（实跑 `_ec_s3_controls.py`；18 件，含 9 件编排方未列样本）

| verdict | class | E1/E2/E3/E4 | 脚本 | 触发要件与依据 |
|---|---|---|---|---|
| OK | GATE | P/P/P/P | check_d27.py | 正控：E1 {0,1,2}(:59,:99,:101)；E2 10 来源；E3 :66 handler 转登记；E4 {errors,missing} 交集 |
| OK | GATE | P/P/P/P | check_d28.py | 正控（raise SystemExit(main()) 正确解析） |
| OK | GATE | P/P/P/P | check_d29.py | 正控 |
| OK | GATE | P/P/P/P | check_d30.py | 正控 |
| NEEDS_FIX | GATE | F/P/P/P | VERIFY_A8.py | **反控①**：E1 FAIL——:796 `return 0` 恒定 ⇒ EXIT=0 零信息；E3 :783 handler 经 record() 登记 → PASS；摘要有据但退出码死值 |
| OK | PROBE | - | _d21_burden5.py | **反控②**：零出口+零真写+26 print ⇒ 探针正确形态，不该有出口 |
| OK | PROBE | - | _leader_crossframe_check.py | 反控②：同上（44 print） |
| OK | ARTIFACT | - | _a7_acf_probe.py | 反控②：真写 :161 ⇒ 产物件，登记产物+指纹 |
| OK | ARTIFACT | - | _intra_frame_census.py | 反控②：真写 :165 |
| OK | GATE | P/P/P/P | _check_dtrigger.py | 新样本：内联出口 `raise SystemExit(0 if ok else 1)`@:228；E2 And 聚合(:34)+17 处检查调用；E4 交集 {ok} |
| OK | GATE | P/P/P/P | _w2w_fp9.py | 新样本：`sys.exit(0 if ok == 9 else 1)`@:45 指纹复核门禁；E2 计数器聚合(:41)+出口比较；E3 :34 handler 打印 READ_FAIL 非吞 |
| NEEDS_FIX | GATE | F/P/F/P | _n4_ast_scan.py | 新样本：E1 :300 `return 0` 恒定 + E3 :57 惰性吞（与普查 CONSTANT_EXIT 一致） |
| NEEDS_FIX | GATE | F/P/P/P | _cm_inject.py | 新样本：E1 :215 恒 0；E4 修复后 {lines} 交集（摘要写盘通道 :213） |
| OK | PROBE | - | _ai2_selfcheck2.py | 新样本：stdout 观测 |
| OK | ARTIFACT | - | _verify_hy4_recompute.py | 新样本：write_text(OUT)@:471 |
| OK | PROBE | - | _cs_attrib.py | 新样本：1 条前置 assert（fingerprint mismatch@:16）非裁决 ⇒ 不触发 GATE（与普查 VERDICT_VIA_ASSERT_ONLY 标记分歧，见 §4 交叉核对） |
| OK | ARTIFACT | - | _cr_real_verify.py | 新样本：verdict 字典写入 `_cr_verify_out.json`:458 ⇒ 产物件（verdict-as-data 盲区，人工复核同判 ARTIFACT） |
| OK | ARTIFACT | - | _cf_compose_lineage.py | 新样本：write_text(OUT)@:409 |

18/18 与设计预期一致。**过拟合检验通过**：9 件新样本覆盖了内联动态出口、计数器聚合、
恒 0 出口、verdict-as-data、前置 assert、emitter 通道等 9 件已知样本未覆盖的形态。

---

## 4. 第四步：263 件 NO_EXIT_AT_ALL 三分类（实跑 `_ec_s4_all.py`）

名单取自 `lead/const_exit_20261109/_ce_final_out.json`（rows 中 cls==NO_EXIT_AT_ALL，263 件，
只读）。全量结果（`_ec_s4_results.json`，每件带 reasons+file:line）：

| 类 | 件数 | verdict | 处置 |
|---|---|---|---|
| **PROBE** | **122** | OK 122 | 不改脚本；登记口径改为「捕获 stdout/摘要文本 + 指纹」，不登记 EXIT |
| **ARTIFACT** | **102** | OK 102 | 不改脚本；登记口径改为「产物文件 + 指纹」，不登记 EXIT（真写形态分布：write_text 72 / open-w 19 / write_bytes 11） |
| **GATE** | **21** | NEEDS_FIX 21 | **必须加出口**（模板见下）+ 已登记行加注；19 件 E0（stdout 互斥裁决对/单侧负裁决而零出口）、2 件 E3（assert 通道顶替） |
| **UNKNOWN** | **18** | NEEDS_FIX(人工) 18 | 逐件人工，不许批量；其中 16 件带「疑似库模块/零可见产物脚本」提示（如 frame_edge_sampler.py 系被 import 的共享库），2 件无提示（`_r9s_samples.py`、`_sp_gen_word.py`——顶层无 def/class 的数据/生成件） |

verdict 合计：OK 224 / NEEDS_FIX 39（21 GATE + 18 UNKNOWN）。
交叉核对：**判据的显式出口检测与普查 NO_EXIT 判定分歧 = 0**（263 件确实全部无显式出口）。

### 4(a) GATE 21 件全名单（本步核心发现）

E0 型 19 件（stdout 互斥裁决对/单侧负裁决，零出口——每件的裁决对现场均已逐行目检，
全部是脚本对**自身检查**的二值裁决，非被测对象领域词误报）：

```
lead/c07_protocol_attacks_20261109/_pa_a9_nfkc_probe.py   :27  "PASS" if SESSION_RE.fullmatch(s) else "FAIL"
lead/c97_scope_recheck_20261108/_c97_check.py             :135 emit→缓冲→print 通道 "PASS" if not mismatch else "FAIL"
lead/counterpart_fix_20261109/_cf_enum_counterpart.py     :168 "ALL_PASS" if bad == 0 else "FAIL"
lead/d13b_design_20261106/_test_state_machine.py          :65/:66 vs :68/:69  print("[PASS]…")/print("[FAIL]…")
lead/dtrigger_round2_20261107/_dC_recompute.py            :218 "PASS" if len(A_nf_eq_ideal)==54 and … else "FAIL"
lead/evidence_indep_20261109/_ei_n13_predicates_src.py    :344 "FAIL" if p else "PASS"（库+内嵌自检）
lead/gate_fp7_20261108/_g7_reverse_validate.py            :49  ("PASS" if ok else "FAIL")
lead/gate_n13_20261109/_n13_predicates.py                 :344 同上（内嵌最小自检）
lead/gate_v1v2_20261109/_v12_verify.py                    :167 "PASS" if ok else "FAIL"
lead/gate_v1v2_20261109/_v12v_fair.py                     :34  "PASS" if v["verdict"]=="V2" else "FAIL"
lead/matrix_row5_20261109/_r5_probe_import.py             :98  "PROBE_ALL_" + ("PASS" if allpass else "FAIL")
lead/needle_norm_20261109/_nd_l1fix.py                    :84  "FIXTURE_SELF_TEST = PASS/FAIL"
lead/needle_norm_20261109/_nn_norm.py                     :274 同上
lead/spec_static_closure_20261108/_sc_scan.py             :117 "OK" if d900 == 900.0 else "FAIL"
lead/strict_exposure_20261109/_se_enum.py                 :176 "ALL_PASS" if bad == 0 else "FAIL"
lead/u5u6_mirror_20261109/_m5_mirror_check.py             :17  f"[{'PASS' if ok else 'FAIL'}] {name}"（CHECKS 累积）
lead/w2_samecause_20261109/_w2v_probe1.py                 :39  ("PASS" if cond else "FAIL")（results 累积）
lead/w2_samecause_20261109/_w2v_probe2.py                 :109 "PASS" if pass_all else "FAIL"
lead/whitelist_audit_20261109/_wl_step1_repro.py          :78  "PASS" if hit else "**FAIL**"
```

E3 型 2 件（assert 通道顶替出口）：

```
lead/r33e_merge_20261109/_re_struct_diff.py     :23,:24  assert …,"GUARD FAIL: original drifted"（主判定 struct_ok 写 :54 JSON）
lead/re_line_20261105/V6_V3_REVIEW/_v6_r5.py    :111,:112,:209,:229,:231,:251,:253  assert 承载正反例裁决
```

### 4(b) 逐类处置

- **GATE（21）**：改模板（以在库合格样板 `_check_dtrigger.py:31-35+226-228` 为原型，四个 E 要件齐全）：

  ```python
  ok = True
  def check(name, cond, detail=""):
      global ok
      ok = ok and bool(cond)                     # E2：And 聚合，全部检查通过才置真
      print(("  [PASS] " if cond else "  [FAIL] ") + name)  # E4：同一 cond 驱动摘要与聚合
  # ……各项检查改为 check(...)
  print("核验结论: " + ("ALL PASS" if ok else "FAIL"))       # E4：同源总结
  raise SystemExit(0 if ok else 1)                           # E1：动态状态 {0,1}
  ```
  assert 通道件（_re_struct_diff/_v6_r5）：把 assert 失败改为失败登记 + 末尾同一出口。
  注意 _n13_predicates/_ei_n13_predicates_src 是「库+内嵌自检」混合形态——出口只加在
  `if __name__ == "__main__"` 块内，勿动库本体（两件均被别的脚本 import 复用）。

- **ARTIFACT / PROBE（224）**：不改脚本。登记口径：ARTIFACT→「产物文件+sha256+字节数」；
  PROBE→「捕获 stdout/摘要文本+sha256+字节数」。EXIT=0 从登记行中删除（零信息）。

- **UNKNOWN（18）**：逐件人工。16 件库提示件先确认「是否有脚本化运行方式」：确认为库件则按
  「共享库产物」登记（出口不适用）；确认为脚本则人工定位其产物通道后再归类。2 件无提示件
  （`lead/gate_r9sem_20261109/_r9s_samples.py`、`lead/stale_pass_20261109/_sp_gen_word.py`，
  顶层无 def/class）同样人工。

### 4(c) 5 行台账登记的正确改法（只给文本，**未改台账**）

| GOAL 行 | 现文 | 改成 |
|---|---|---|
| :7569 | `python -I -X utf8 ".../D21_RULING/_d21_burden5.py"  # EXIT=0` | `python -I -X utf8 ".../D21_RULING/_d21_burden5.py"  # 产物 D21_RULING/_d21_burden5_out.txt sha256=0d77c9541ddb2eda0eacc15c5251b06667bfa41a1dd49a66012d58355723419a（1803 字节，stdout 捕获件；脚本零出口，EXIT 不适用）` |
| :7634 | ``> 交付：`V6_V3_REVIEW/_leader_crossframe_check.py` + `_out.txt`（`EXIT=0`）。零真机。`` | ``> 交付：`V6_V3_REVIEW/_leader_crossframe_check.py` + `_out.txt`（产物 _leader_crossframe_check_out.txt sha256=2cf4100776eb7461ef784e4fa8ec8f192439851604fde737dcb0816f045f50dc，2839 字节；脚本零出口，EXIT 不适用）。零真机。`` |
| :8383 | ``   `_leader/_a7_acf_probe.py` + `_a7_acf_probe_out.txt`（均 `EXIT=0`）。`` | ``   `_leader/_a7_acf_probe.py` + `_a7_acf_probe_out.txt`（产物 _a7_acf_probe_out.txt sha256=54145df6e2e1fa818df82e7ccd92e30ee8bbce972f32cdf9983e9aa50287a439，3318 字节；脚本零出口，EXIT 不适用）。`` |
| :9588 | ``> 探针 `_leader/_intra_frame_census.py`，输出 `_leader/_intra_frame_census_out.txt`（`EXIT=0`）。`` | ``> 探针 `_leader/_intra_frame_census.py`，输出 `_leader/_intra_frame_census_out.txt`（产物 sha256=d056f88f331e968b1b6c9bf75c104d35f8df0f2e3b98829f7d94bef1b7940993，3744 字节；脚本零出口，EXIT 不适用）。`` |
| :9679 | ``1. **我亲跑**：`_intra_frame_census.py` 全量 15 窗，`EXIT=0`，输出 40+ 行表格 + 三组汇总。`` | ``1. **我亲跑**：`_intra_frame_census.py` 全量 15 窗（脚本零出口；产物 _intra_frame_census_out.txt sha256=d056f88f331e968b1b6c9bf75c104d35f8df0f2e3b98829f7d94bef1b7940993，3744 字节），输出 40+ 行表格 + 三组汇总。`` |

### 4(d) 改造成本（**估算，未实测**）

| 项 | 量 | 单件估算 | 合计估算 |
|---|---|---|---|
| 5 行台账改字（走正常台账流程） | 5 行 | ~2 分钟 | ~10 分钟 |
| GATE 21 件加出口（含复跑验证+登记） | 21 件 | 小件 ~15 分钟、大件（如 345 行 _n13_predicates）~30-45 分钟 | **约 8–12 小时** |
| UNKNOWN 18 件人工甄别 | 18 件 | ~5 分钟 | ~1.5 小时 |
| 判据装配成登记前 lint（若采纳 §5b 建议） | 一次性 | — | ~半天 |

### 4 交叉核对与校准（如实）

- 普查 `VERDICT_VIA_ASSERT_ONLY=54`（263 内 54 件带 assert 裁决标记）vs 判据 GATE-E3 仅 2 件：
  判据要求**带裁决词**（FAIL/PASS 字样）的 assert ≥2 才触发；其余多为裸 `assert x == y` 形态——
  判据视为守卫/观测而非 stdout 裁决。两口径差异如实呈现，不强行归一。
- `write_lines` 字段：无法完全复现编排方产生规则（§1a），本判据弃用该字段、自建「真写盘」口径。
- `_cs_attrib.py` 等含被测领域词（PASS/CATCH）的件：因不成对/不在条件两臂未被误判为 GATE。

---

## 5. 第五步：结论与边界

### 5(a) 一句话回答：一个脚本的退出码什么时候算证据？

**当且仅当它承载本模块判定的二值裁决、由全部检查合取驱动、失败不被吞、且与逐项摘要同源
（E1-E4 同时成立）——否则退出码只是进程善后信号，证据应改引产物/摘要。**

### 5(b) 装配点建议：**成件后、台账登记前的门禁 lint**

理由：(1) 派发的是任务不是脚本——派发前 lint 无从判起；(2) 只报不拒会让零信息登记继续累积。
装配形态：登记前跑 `classify`——`GATE+NEEDS_FIX` ⇒ 拒收并附 §4b 模板；`ARTIFACT/PROBE` ⇒
自动提示登记口径（产物/摘要 + 指纹，删除 EXIT 字样）；`UNKNOWN` ⇒ 转人工。次选方案：在
check_d2x 类验收门禁本体中加一条「被验脚本 classify 不得为 GATE+NEEDS_FIX」。

### 5(c) 能力边界：结构上判不出的清单

1. **verdict-as-data**：裁决词作为字典值/变量值流转（如 `_crdoc_pasted`/`_crv_pasted` 的
   `{"VERDICT": "PASS"…}` 经 json.dumps 打印/落盘）——静态字面量配对看不到；本轮人工判定
   这三件 cert_realcheck 件为 verdict-bearing（经 stdout JSON/产物文件交付），判据分类为
   PROBE/ARTIFACT，分歧已如实记录。
2. 分支可达性：死分支、恒真条件下的 `return 1`（E1 可能静态高估）——须运行时复核。
3. 名字级≠值级（E4）：打印裁剪子集/不同字段时名字相同、值不同源。
4. 语义级吞没：handler 打印无害文案但丢失失败。
5. emitter 通道识别有限：只识别「纯 append 的模块级 emitter→缓冲→print」形态。
6. 被 import 的门禁：出口在调用方脚本里——库形态件会落 UNKNOWN。
7. 跨文件消费：脚本 A 的 stdout 裁决被脚本 B 解析消费——单文件 AST 不可见。
8. 动态拼接的裁决词字符串。
9. E2 早退门对扫描器形态代码的高估（对 E1 FAIL 件的终判无影响）。
10. inline E2 对「驱动名多次赋值覆盖」的近似。

### 5(d) 这条工作判不了什么（如实）

- 裁决**内容**的对错（判据只判通道与绑定，不判语义正确性——那是各门禁本体与人工复核的事）；
- 摘要数值的真实性（需数据级核对，另一条工作）；
- 一件脚本「该不该被写」；
- 台账登记行其他字段的对错（本工作只对 EXIT/产物引用给出改法）；
- 52 件 census-assert 标记件与判据口径的最终归一（见 §4 交叉核对，留人工）。

---

## 6. 诚实账（实跑命令）

```
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ec_fp_baseline.py   # 15/15 MATCH
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ec_s1_facts.py      # 8/9 一致 + VERIFY_A8 write_lines 口径分歧
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ec_s1_ledger.py     # 台账登记行取证（只读）
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ec_s3_controls.py   # 18 件正反控 → _ec_s3_results.json
python -I -X utf8 D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ec_s4_all.py        # 263 件全量 → _ec_s4_results.json
```

未能做到/未验的事项：(1) 编排方 write_lines 的确切产生规则未复现（两个假设均不成立）；
(2) 四件 _out.txt 产物的**内容**未逐行核对（只取了指纹与存在性）；(3) 263 件中 21 件 GATE 的
裁决对现场已逐件目检其判词对，但未逐件核对它们的台账登记行；(4) 判据实现本身未经独立第二人复核。
判据实现经过 3 轮修正（Raise 参数解析、IfExp 通道、emitter 通道、单标量内联驱动、
swallow 惰性体、E4 写盘通道），每轮以 18 件正反控回归验证。
