# EXIT_CRITERION — 出口判据成件（lead/exit_criterion_20261110/）

- 日期：2026-11-10。撰写者：出口判据成件撰写员（动态工作流子件）。
- 回答的问题：**一个脚本的退出码什么时候算证据？什么时候「没有出口」反而是正确形态？**
- 判据本体：`lead/exit_criterion_20261110/_ec_criterion.py`（42136 字节，纯静态 AST + 源文本，零执行被检脚本，仅依赖标准库 ast/re）。
- 约束执行：零真机（本会话未启动任何游戏进程、未 taskkill、未读活进程内存）；零采样代码（未写 hook/MiniDump/SuspendThread/StackWalk/探针注入/动态内存解析）；两件台账与全部只读目录零修改（终态指纹复核见 §6d）；不 commit、不 push；唯一写域 = `lead/exit_criterion_20261110/`（本件新增 `_ecw_*` 前缀文件与 EXIT_CRITERION.md，未动设计员 `_ec_*` 与复核员 `_ecv_*` 任何一字节——`_ec_s3_results.json`/`_ec_s4_results.json` 复跑后与复跑前 sha256 逐字节一致，见 §4a/§5a）。
- 证据规则：本件所有数字与行号均为**本会话实跑/实读**所得；实跑命令与输出摘录随文给出。凡本会话没跑到的一律记入 §6c 未验项，不补造。

---

## 1 目的与边界

**本件只做两件事：设计判据、验证判据。**

1. 不改任何被检脚本（lead/ 下 263 件与 18 件正反控全部原样）；
2. 不加注任何台账（GOAL/PENDING 两件台账零修改，五行改法只给文本见 §5f）；
3. 判据输入是 `(rel, ast_tree, source_text)`，**不运行被检脚本、不读进程、不碰网络**——被检脚本只被 `ast.parse`（`_ec_criterion.py:92-96`）；
4. 判据输出三类判定：该不该有出口（class）、出口合不合格（E1–E4）、下一步动作（verdict）。

**本件最重要的边界原则（铁律的推论）：「零出口」≠「坏脚本」。** 探针（PROBE）与一次性分析产物件（ARTIFACT）本来就不需要出口——它们的产物是观测值或文件，不承载「该不该放行」的二值裁决；判据必须把「不该有出口而没出口」（OK）与「该有出口而没出口」（NEEDS_FIX）分开，不许一刀切。本判据用「**判定的消费通道**」做分类判别轴来划这条线（§3a）。

---

## 2 样本事实复核

### 2a 基线指纹（实跑 `_ecw_fp.py`，19/19 MATCH）

命令：`python -I -X utf8 D:/Project/ra2-campaign-forge/lead/exit_criterion_20261110/_ecw_fp.py`
结果：编排方 15 件基线 + 4 件在盘产物 `_out.txt`，19/19 sha256 与字节数全 MATCH。四件产物指纹：

| 产物 | 字节数 | sha256 |
|---|---|---|
| `lead/re_line_20261105/D21_RULING/_d21_burden5_out.txt` | 1803 | `0d77c9541ddb2eda0eacc15c5251b06667bfa41a1dd49a66012d58355723419a` |
| `lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check_out.txt` | 2839 | `2cf4100776eb7461ef784e4fa8ec8f192439851604fde737dcb0816f045f50dc` |
| `lead/re_line_20261105/_leader/_a7_acf_probe_out.txt` | 3318 | `54145df6e2e1fa818df82e7ccd92e30ee8bbce972f32cdf9983e9aa50287a439` |
| `lead/re_line_20261105/_leader/_intra_frame_census_out.txt` | 3744 | `d056f88f331e968b1b6c9bf75c104d35f8df0f2e3b98829f7d94bef1b7940993` |

（15 件基线逐件哈希与编排方指纹块逐字一致，含 `PENDING_DECISIONS.md` 3765eddb…/52419、`GOAL_THREE_TARGETS_20261018.md` 2baa0de4…/759518。）

### 2b 9 件样本逐字段（实跑 `_ec_s1_facts.py`，复跑输出 RESULT: 8/9 逐字段一致）

命令：`python -I -X utf8 …/_ec_s1_facts.py`。9 件中 8 件 bytes/n_lines/exit_sites/write_lines/has_print 五字段与编排方逐字段一致；唯一分歧是 VERIFY_A8 的 write_lines（见 §2c）。

| 样本 | 字节/行数 | exit_sites（实测） | open 行（write_lines 口径实测） | 真写盘（w/a/x/+ 或 write_text/bytes） | has_print |
|---|---|---|---|---|---|
| `_d21_burden5.py` | 2929/73 | 无 | [20]（`:20` `json.load(io.open(p,…))`——**读** open） | **0** | 是（26 处 print） |
| `_leader_crossframe_check.py` | 4688/101 | 无 | [] | **0** | 是（44 处 print） |
| `_a7_acf_probe.py` | 5763/163 | 无 | [35, 161] | **1**（`:161` `open(…,"w")` → `_a7_acf_probe_out.txt`） | 是（1 处 + P() 缓冲） |
| `_intra_frame_census.py` | 6279/167 | 无 | [37, 94, 165] | **1**（`:165` `open(…,"w")` → `_intra_frame_census_out.txt`） | 是（1 处 + P() 缓冲） |
| `check_d27.py` | 3764/107 | `[("call",107,"sys.exit(main())")]` | [] | 0 | 是 |
| `check_d28.py` | 4539/122 | `[("raise",122,"raise SystemExit(main())")]` | [] | 0 | 是 |
| `check_d29.py` | 3906/110 | `[("raise",110,"raise SystemExit(main())")]` | [] | 0 | 是 |
| `check_d30.py` | 3926/110 | `[("raise",110,"raise SystemExit(main())")]` | [] | 0 | 是 |
| `VERIFY_A8.py` | 38317/800 | `[("call",800,"sys.exit(main())")]` | 编排方 [87,284,285,286,287,303,408,425]；open( 口径实测 **[]** | **0** | 是（21 处 print） |

### 2c write_lines 字段的裁决：不可作产物证据

实跑（python -I -X utf8 内联脚本，本会话）对 `VERIFY_A8.py` 逐行检验：

- 含 `ast.dump(` 的行 = **14** 行：[87, 284, 285, 286, 287, 303, 408, 425, 427, 437, 450, 710, 711, 732]。编排方 8 行 ⊂ 这 14 行。
- 假设一（子串 `open\(|\.dump\(|\.write\(`）= 14 行；假设二（仅 `open\(`）= 0 行。**两假设均 ≠ 8 行 ⇒ 产生规则未复现（未验）**。
- 编排方 8 行逐行内容全部是 `ast.dump(…)` 的**内存序列化**（如 `:87` `d.setdefault(n.name, []).append(ast.dump(n))`、`:284` `m_body = [ast.dump(x) for x in m_try.body]`），`.write/.write_text/.write_bytes` 行 = **0**。

**裁决：** write_lines 字段对 VERIFY_A8 既不可复现、又不代表写盘 ⇒ **该字段不可当「写盘产物证据」用**；判据弃用之，自建「真写盘」口径（w/a/x/+ 模式 open、write_text、write_bytes；读 open 不算——§2b 中 `_d21_burden5.py:20` 即读 open 被旧口径误计的实例）。

### 2d 四件零信息对象的产物形态 + GOAL 登记行（实读）

| 脚本 | 真写盘 | 产物形态 | GOAL 登记行（本会话实读原文） |
|---|---|---|---|
| `_d21_burden5.py` | 无 | **stdout-only**（`_d21_burden5_out.txt` 在盘，系外部捕获） | `:7569` `python -I -X utf8 ".../D21_RULING/_d21_burden5.py"  # EXIT=0` |
| `_leader_crossframe_check.py` | 无 | **stdout-only**（`_out.txt` 外部捕获） | `:7634` `> 交付：`V6_V3_REVIEW/_leader_crossframe_check.py` + `_out.txt`（`EXIT=0`）。零真机。` |
| `_a7_acf_probe.py` | `:161-162` `io.open(…,"w").write("\n".join(OUT))` | out.txt = OUT 缓冲镜像（P() 同时 print+append） | `:8383` `…_a7_acf_probe.py` + `_a7_acf_probe_out.txt`（均 `EXIT=0`）。 |
| `_intra_frame_census.py` | `:165-166` 同上 | out.txt = OUT 缓冲镜像 | `:9588`、`:9679`（均 `EXIT=0`） |

`PENDING_DECISIONS.md` 中四件脚本名 0 命中（实跑 `_ec_s1_ledger.py`：搜「_d21_burden5.py」等 6 个名字均 0 行）。**结论：四件的 EXIT=0 全部零信息；正确处置是改登记口径（产物+指纹），不是给脚本加出口**（改法文本见 §5f）。

### 2e 四件门禁的出口表达式原文（正控样板；实读源码）

| 门禁 | 出口站点（实读） | main 返回（实读行号） | 失败登记（实读） |
|---|---|---|---|
| `check_d27.py` | `:107` `sys.exit(main())`（call） | `return 2`@`:59`、`return 1`@`:99`、`return 0`@`:101` ⇒ {0,1,2} | 8 项编号检查、7 处 `errors.append`（:67,:70,:74,:79,:88,:92,:94）+ `:56` missing 早退门 |
| `check_d28.py` | `:122` `raise SystemExit(main())` | `:111`/`:114`/`:116` ⇒ {0,1,2} | append 喂同一退出门 |
| `check_d29.py` | `:110` `raise SystemExit(main())` | `:101`/`:104`/`:106` ⇒ {0,1,2} | 同上 |
| `check_d30.py` | `:110` `raise SystemExit(main())` | `:101`/`:104`/`:106` ⇒ {0,1,2} | 同上 |

- **勘误（复核发现，本会话实读证实）**：`_ec_report.md` §1(c) 把 d29/d30 的 main 返回行写成 100/103/105，手抄偏 1；机器产物 `_ec_s3_results.json` 行号正确（E1 reason 引 :101/:104/:106）。
- `any()` 折叠的定位：d29/d30 `:87` `if not any(matches)` 属**检查内部**的关键词判定（一节命中任一关键词即该项通过），是检查粒度的 OR；出口层 8 项任一失败仍 → return 1（`:102-104`）⇒ **不破坏出口层合取**，判 NEEDS_FIX 才是错。
- 出口读的是裁决函数 main() 的返回值 ⇒ 这是「合格出口」的在库样板（§4 正控全 PASS）。

---

## 3 ★ 判据

判据本体 = `_ec_criterion.py`（911 行，42136 字节，sha256=`e719296fb18bf6ff2112f6be62bca3c1cda19701cb5bd905a18d22fa51b7dc78`，本会话实算）。本节给定义与机器可判特征；§3d 给完整判定函数。

### 3a 第一层：该不该有出口 —— 分类，判别轴 = 判定的消费通道

| 类 | 定义 | 机器可判特征（AST/结构，非文件名） | 为什么 |
|---|---|---|---|
| **GATE** | 存在以「程序可消费的二值裁决」形态存在、应送达调用方控制流的判定 ⇒ **需要出口** | GA1 / GA2 / GA3（任一，见 §3b） | stdout 散文结论是报告；**互斥 PASS/FAIL 对才是布尔决策接口**——调用方靠退出码/分支消费它 |
| **ARTIFACT** | 产物是文件 ⇒ 消费方读文件 ⇒ **不需要出口** | 真写盘：w/a/x/+ 模式 open、write_text、write_bytes（读 open 不算）；且无 GA1/GA2 | 登记「产物+指纹」即可，退出码不承载判定 |
| **PROBE** | 产物是观测值+解读，不判对错 ⇒ **不需要出口** | 无出口、无裁决对、无真写盘，而有 print（或 emitter→缓冲→print 数据流） | 登记通道是捕获的 stdout/摘要文本 |
| **UNKNOWN** | 证据不足/冲突/解析失败 ⇒ **逐件人工，禁止批量** | 解析失败；四类特征全无（附「疑似库模块/零可见产物脚本」提示：统计顶层 def/class 与顶层可执行语句数，`_ec_criterion.py:712-724`） | **宁可 UNKNOWN 不许猜** |

设计要点：三类之别不在「有没有 print」，在「**有没有一个会被下游读的判定**」。单侧 NEG（只在失败臂打 FAIL）同属决策接口（调用方靠其缺席推断通过），也算 GATE。被测对象的领域词（如 `_cs_attrib.py` 的 PASS/CATCH 判词）因不成对/不在条件两臂而不会误触发 GA2——18 件正反控中 `_cs_attrib.py` 判 PROBE OK 实证（§4）。

### 3b 分类机器特征（实现位置均在 `_ec_criterion.py`）

- **GA1 出口管道**：SystemExit 家族出口站点（`collect_exits` `:119-130`：`ast.Raise` 且 exc 为 SystemExit 构造，或 `ast.Call` func 为 `exit/quit/os._exit/.exit`）且出口可达状态集 ≥2 或状态为动态表达式（`exit_arg_nodes` `:133-144` + `returned_states` `:417-447`）。
- **GA2 stdout 互斥裁决对**：`verdict_pairs` `:264-377`。摘要通道 = print 直调，或「纯 append 的模块级 emitter 函数→缓冲变量→print」数据流（`_emitter_fns` `:219-238`、`_buffer_printed` `:241-249`；实例 `_c97_check.py:20` emit→`:19` out→`:205` print）。在 if/elif 链两臂（`_if_chain_arms` `:252-260`）或三元 IfExp 两臂找词对：POS `\bPASS(?:ED|ING)?\b|✅|全部通过|\bOK\b`，NEG `\bFAIL(?:ED|S)?\b|❌|不通过|未通过`（`:74-75`）；或恰一臂 NEG（单侧负裁决）；且判定条件非恒定（`_test_is_deciding` `:212-216` 要求含 Compare/Call/Name）。
- **GA3 失败累积**：`failure_sites` `:466-485`（append/extend/add/insert/appendleft/update 与 `+= [...]`）在裁决链内 ≥2 处，喂 `gate_ifs` `:488-510` 的「if→return 非零」门。
- **裁决函数解析**：`resolve_verdict_fns` `:401-414`（`sys.exit(main())` → main）；`scope_set` `:450-463` 追一层直接调用。
- **判据对退出码同型词不误判**：`_cf_enum_counterpart.py:168` "ALL_PASS" 若 bad==0——POS_RE 不含 ALL_PASS，靠 NEG 单侧（"FAIL"）触发 GA2，实测正确（§5d）。

### 3c 第二层：合格出口四要件 E1–E4（仅 GATE 适用）

| 要件 | 判定 | AST 实现 | 无法纯静态判的部分（声明局限） |
|---|---|---|---|
| **E1 非常量** | 出口可达状态集合 \|S\|≥2 或存在动态状态表达式 | `returned_states` `:417-447` 收集裁决函数全部 Return 整数常量（None 记 0；bool 不算 int）；直书常量并入；非字面量 Return 或内联 IfExp/比较 ⇒ dynamic。`\|S\|≥2 ∪ dynamic ⇒ PASS`；`\|S\|==1` 且非 dynamic ⇒ FAIL（CONSTANT_EXIT 型，EXIT=0 零信息） | 分支可达性（死分支）判不出，须运行时复核 |
| **E2 合取驱动** | 0 分支由「全部检查通过」驱动 | 有裁决函数：`failure_sites`+`gate_ifs` 合计独立来源 k≥2 ⇒ PASS；==1 ⇒ FAIL 单标量；0 ⇒ UNKNOWN。内联动态出口：`inline_exit_evidence` `:595-635` 追驱动名的 And 聚合赋值/累计(+=)/global-checker 调用点/出口比较，证据 ≥2 ⇒ PASS(w)；==1 ⇒ FAIL；==0 ⇒ UNKNOWN | 登记点是否语义独立；扫描器形态代码的早退门会高估 k（对 E1 FAIL 件的终判无影响） |
| **E3 无吞** | 失败不经被吞的异常通道消失、异常通道不顶替出口 | `swallow_handlers` `:513-552`：每个 ExceptHandler 体「惰性」（无 re-raise/出口调用/失败登记/非零 return/print/对模块级自定义函数的调用）⇒ 吞没 ⇒ FAIL。另有：无出口管道而 ≥2 条**带裁决词** assert ⇒ `E3_IMPLICIT_EXCEPTION`（assert_facts `:381-393`）⇒ FAIL | 语义级吞没（打印无害文案但丢失失败）判不出 |
| **E4 摘要绑定** | 同一次运行中退出码与逐项摘要来自同一份数据 | `gate_and_print_names` `:555-592`：退出门守卫名 G（门条件 Name+登记目标名+内联驱动名）∩ 摘要引用名 P（print 参数 Name+写盘调用参数 Name+迭代打印/写盘循环源名）≠∅ ⇒ PASS | **名字级≠值级**；打印裁剪子集判不出，须运行时对照 |

### 3d 判定函数（可粘贴）

**最简可粘贴单元 = `_ec_criterion.py` 整文件**：仅依赖标准库 ast/re，`python -I -X utf8 _ec_criterion.py` 可独立运行（`__main__` 打印判据文档 `:909-910`）；`analyze_file(abs_path, rel)` `:899-906` 是文件级入口。核心判定函数 `classify(rel, tree, src)` 全文如下（与盘上文件 `:639-881` 逐字一致）：

```python
def classify(rel, tree, src):
    """输入 (rel, ast_tree, source_text) → 判定 dict。
    class ∈ {GATE, ARTIFACT, PROBE, UNKNOWN}; verdict ∈ {OK, EXIT_ZERO_INFO, NEEDS_FIX}
    """
    def relref(ln):
        return "%s:%d" % (rel, ln)

    reasons = []
    R = reasons.append

    exits = collect_exits(tree, src)
    writes = collect_true_writes(tree, src)
    n_prints = count_prints(tree)
    pairs, single_neg = verdict_pairs(tree, src)
    n_assert, v_asserts = assert_facts(tree, src)

    pair_evidence = bool(pairs) or bool(single_neg)
    assert_evidence = len(v_asserts) >= 2

    arg_nodes = exit_arg_nodes(tree, tree) if exits else []
    v_fns = resolve_verdict_fns(tree, arg_nodes) if exits else []
    all_states, any_dynamic, state_lines = set(), False, []
    local_fn_ids = set(_module_defs(tree))
    if exits:
        for fn in v_fns:
            s, d, ls = returned_states(fn)
            all_states |= s
            any_dynamic = any_dynamic or d
            state_lines += ls
        for arg in arg_nodes:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                all_states.add(arg.value)
                state_lines.append((arg.lineno, "exit(%d) 直书" % arg.value))
            elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) \
                    and arg.func.id in local_fn_ids:
                pass  # 已由 returned_states 覆盖
            elif isinstance(arg, ast.Name) and arg.id in local_fn_ids:
                pass
            else:
                any_dynamic = True
                state_lines.append((arg.lineno, "出口状态=动态表达式(%s)"
                                    % (ast.get_source_segment(src, arg) or "?")[:50]))

    multi_state = len(all_states) >= 2 or any_dynamic
    f_sites = failure_sites(scope_set(tree, v_fns)) if v_fns else []
    gate_evidence = []
    if pair_evidence:
        gate_evidence.append("GA2:stdout裁决对")
    if multi_state:
        gate_evidence.append("GA1:出口状态%s%s"
                             % (sorted(all_states) if all_states else "{动态}",
                                "∪动态" if any_dynamic else ""))
    if len(f_sites) >= 2:
        gate_evidence.append("GA3:失败累积%d处" % len(f_sites))

    if exits:
        if gate_evidence:
            cls = "GATE"
        else:
            cls = "ARTIFACT" if writes else ("PROBE" if n_prints else "UNKNOWN")
            if cls == "UNKNOWN":
                R(("CLASS", rel, "有出口但无 GA1/GA2/GA3 证据、无真写盘、无 print → 需人工"))
    else:
        if pair_evidence:
            cls = "GATE"
        elif assert_evidence:
            cls = "GATE"
        elif writes:
            cls = "ARTIFACT"
        elif n_prints:
            cls = "PROBE"
        else:
            cls = "UNKNOWN"
            n_def = sum(isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                        for nd in tree.body)
            n_exec = sum(1 for nd in tree.body
                         if not isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                ast.ClassDef, ast.Import, ast.ImportFrom))
                         and not (isinstance(nd, ast.Expr)
                                  and isinstance(nd.value, ast.Constant)))
            if n_def >= 1:
                R(("CLASS", rel, "疑似库模块/零可见产物脚本（顶层 def/class %d 个，顶层可执行语句 %d 条，"
                                "无 print/无写盘/无出口）：前者按库件登记（出口不适用），"
                                "后者须人工定位产物通道" % (n_def, n_exec)))
            else:
                R(("CLASS", rel, "无出口、无裁决对、无真写盘、无 print → 需人工"))

    e = {"E0": None, "E1": None, "E2": None, "E3": None, "E4": None}

    # ---------------- GATE 无出口：E0
    if cls == "GATE" and not exits:
        if pairs:
            p0 = pairs[0]
            R(("E0", relref(p0["if_line"]),
               "stdout 互斥裁决对（%s@%d / %s@%d，%s test=%s）但模块内无任何出口站点 ⇒ 判定传不到调用方"
               % (",".join(p0["neg"]), p0["neg_arm"], ",".join(p0["pos"]), p0["pos_arm"],
                  p0["kind"], p0["test"])))
        elif single_neg:
            s0 = single_neg[0]
            R(("E0", relref(s0["if_line"]),
               "stdout 单侧负裁决（%s@%d，%s test=%s）但模块内无任何出口站点"
               % (",".join(s0["neg"]), s0["neg_arm"], s0["kind"], s0["test"])))
        else:
            for a in v_asserts[:4]:
                R(("E3", relref(a["line"]), "assert 承载裁决（异常通道顶替出口）: %s" % a["snippet"]))
            R(("E3", rel, "共 %d 条裁决型 assert；建议改为失败登记+显式出口" % len(v_asserts)))
            e["E0"] = "E3_IMPLICIT"
        verdict = "NEEDS_FIX"
        return {"rel": rel, "class": cls, "verdict": verdict, "e": e,
                "reasons": reasons,
                "facts": _facts_dict(exits, writes, n_prints, pairs, single_neg,
                                     n_assert, v_asserts)}

    # ---------------- GATE 有出口：E1..E4
    if cls == "GATE":
        # E1
        if not arg_nodes:
            e["E1"] = "UNKNOWN"
            R(("E1", rel, "裸 raise SystemExit 无状态表达式 → E1_UNRESOLVED 需人工"))
        elif len(all_states) >= 2 or any_dynamic:
            e["E1"] = "PASS"
            shown = ", ".join("%s:%s" % (relref(ln), dsc) for ln, dsc in state_lines[:8])
            R(("E1", rel, "PASS：出口可达状态 %s%s（%s%s）"
               % (sorted(all_states) if all_states else "{动态}",
                  "∪动态" if any_dynamic else "", shown,
                  " …" if len(state_lines) > 8 else "")))
        else:
            e["E1"] = "FAIL"
            shown = ", ".join("%s:%s" % (relref(ln), dsc) for ln, dsc in state_lines[:6])
            R(("E1", relref(state_lines[0][0]) if state_lines else rel,
               "FAIL：出口可达状态恰为 %s（%s）⇒ EXIT=0 零信息" % (sorted(all_states), shown)))

        # E2
        scope = scope_set(tree, v_fns) if v_fns else ([tree] if not v_fns else [])
        if v_fns:
            g_sites = gate_ifs(scope)
            total_sites = sorted(set([ln for ln, _, _ in f_sites] + [ln for ln, _ in g_sites]))
            if len(total_sites) >= 2:
                e["E2"] = "PASS"

                def site_desc(ln):
                    for (l, _k, nm) in f_sites:
                        if l == ln:
                            return "append(%s)" % nm
                    for (l, cond) in g_sites:
                        if l == ln:
                            return "早退门(%s)" % cond[:44]
                    return "?"

                ev = ", ".join("%s:%s" % (relref(ln), site_desc(ln))
                               for ln in total_sites[:10])
                R(("E2", rel, "PASS：%d 处独立失败来源喂同一退出门（%s%s）"
                   % (len(total_sites), ev, " …" if len(total_sites) > 10 else "")))
            elif len(total_sites) == 1:
                ln = total_sites[0]
                cond = next((c for l, c in g_sites if l == ln), None)
                e["E2"] = "FAIL"
                R(("E2", relref(ln), "FAIL：0 分支由单标量驱动（%s）" % (cond or "append-only",)))
            else:
                e["E2"] = "UNKNOWN"
                R(("E2", rel, "裁决链内未找到失败登记/早退门 → E2_UNRESOLVED 需人工"))
        else:
            iev, drivers = inline_exit_evidence(tree, arg_nodes)
            if len(iev) >= 2:
                e["E2"] = "PASS"
                R(("E2", rel, "PASS(w)：内联出口驱动 %s 的聚合证据 %d 处（%s%s）"
                   % (drivers, len(iev),
                      ", ".join("%s:%s" % (relref(ln), d) for ln, d in iev[:8]),
                      " …" if len(iev) > 8 else "")))
            elif len(iev) == 1:
                e["E2"] = "FAIL"
                R(("E2", relref(iev[0][0]),
                   "FAIL：0 分支由单标量驱动（%s %s）" % iev[0]))
            else:
                e["E2"] = "UNKNOWN"
                R(("E2", rel, "内联出口驱动名未找到赋值/累计/检查调用 → E2_UNRESOLVED 需人工"))

        # E3（内联出口时扫描全模块 handler）
        e3_scope = scope if v_fns else [tree]
        handlers = swallow_handlers(e3_scope, src)
        sw = [h for h in handlers if h["swallow"]]
        if sw:
            e["E3"] = "FAIL"
            for h in sw[:6]:
                R(("E3", relref(h["line"]),
                   "FAIL：异常被吞（体惰性：无登记/无重抛/无非零出口/无打印/无函数调用），fn=%s" % h["fn"]))
        else:
            e["E3"] = "PASS"
            if handlers:
                R(("E3", rel, "PASS：%d 个 handler 全部把异常转入登记/打印/重抛/非零出口（%s）"
                   % (len(handlers), ", ".join(relref(h["line"]) for h in handlers[:8]))))
            else:
                R(("E3", rel, "PASS：裁决链内无 try/except（无吞点）"))

        # E4
        G, P = gate_and_print_names(scope if v_fns else [tree], src)
        if not v_fns:
            G |= set(inline_exit_evidence(tree, arg_nodes)[1])
        inter = sorted(G & P)
        if inter:
            e["E4"] = "PASS"
            R(("E4", rel, "PASS：退出门守卫名 %s 与摘要引用名交集 = %s（名字级绑定）"
               % (sorted(G), inter)))
        else:
            e["E4"] = "FAIL"
            R(("E4", rel, "FAIL：退出门守卫名 %s 与摘要引用名 %s 无交集 ⇒ 摘要与退出码不同源"
               % (sorted(G), sorted(P))))
    else:
        # 非 GATE：出口零信息/不适用
        if exits and arg_nodes:
            consts = [a.value for a in arg_nodes
                      if isinstance(a, ast.Constant) and isinstance(a.value, int)]
            if consts and len(consts) == len(arg_nodes):
                R(("EXIT", relref(exits[0]["line"]),
                   "出口存在但全部为常量 %s（%s）；本类产物=%s，登记应引用产物而非 EXIT"
                   % (sorted(set(consts)), exits[0]["snippet"][:60],
                      "文件" if writes else "stdout 观测")))
            else:
                R(("EXIT", relref(exits[0]["line"]),
                   "出口非常量（%s），仅承载崩溃信号；本类产物=%s，验收不经退出码"
                   % (exits[0]["snippet"][:60], "文件" if writes else "stdout 观测")))

    # ---------------- verdict
    if cls == "UNKNOWN":
        verdict = "NEEDS_FIX"
        R(("UNKNOWN", rel, "UNKNOWN_MANUAL：语义为「需人工逐件」，不是「需改码」；禁止批量处置"))
    elif cls == "GATE":
        verdict = "OK" if all(e.get(k) == "PASS" for k in ("E1", "E2", "E3", "E4")) else "NEEDS_FIX"
    else:
        if not exits:
            verdict = "OK"
            R(("CLASS", rel, "%s：产物=%s，出口不适用（正确形态）；登记应引用%s"
               % (cls, "文件" if writes else "stdout 观测",
                  "产物文件+指纹" if writes else "捕获的 stdout/摘要文本")))
        else:
            consts = [a for a in arg_nodes
                      if isinstance(a, ast.Constant) and isinstance(a.value, int)]
            verdict = "EXIT_ZERO_INFO" if consts and len(consts) == len(arg_nodes) else "OK"

    return {"rel": rel, "class": cls, "verdict": verdict, "e": e,
            "reasons": reasons,
            "facts": _facts_dict(exits, writes, n_prints, pairs, single_neg,
                                 n_assert, v_asserts)}
```

classify 依赖的同文件助手（行号为 `_ec_criterion.py` 实测行号）：`read_source:81`、`parse_source:92`、`collect_exits:119`、`exit_arg_nodes:133`、`collect_true_writes:148`、`count_prints:173`、`_docstring_nodes:185`、`_arm_strings:196`、`_test_is_deciding:212`、`_emitter_fns:219`、`_buffer_printed:241`、`_if_chain_arms:252`、`verdict_pairs:264`、`assert_facts:381`、`_module_defs:397`、`resolve_verdict_fns:401`、`returned_states:417`、`scope_set:450`、`failure_sites:466`、`gate_ifs:488`、`swallow_handlers:513`、`gate_and_print_names:555`、`inline_exit_evidence:595`、`_facts_dict:884`、`analyze_file:899`。

### 3e verdict 规则

- **GATE**：无出口 ⇒ `NEEDS_FIX(E0)`；E1 FAIL ⇒ `NEEDS_FIX(E1_CONSTANT_EXIT)`（VERIFY_A8 型）；E2/E3/E4 任一 FAIL ⇒ `NEEDS_FIX`（附行号）；E 不确定 ⇒ `NEEDS_FIX(UNRESOLVED 需人工)`；全过 ⇒ `OK`。
- **ARTIFACT / PROBE**：无出口 ⇒ `OK`（出口不适用）；带常量出口 ⇒ `EXIT_ZERO_INFO`（登记产物/摘要，不登记 EXIT）；非常量出口 ⇒ `OK`（仅承载崩溃信号）。
- **UNKNOWN** ⇒ `NEEDS_FIX`，理由码 `UNKNOWN_MANUAL`：语义是「需人工逐件」，**不是**「需改码」。
- 每条 reason 必带 `rel:line`。

### 3f 宁可 UNKNOWN 不猜 + 声明盲区

规则：解析失败 ⇒ UNKNOWN（`analyze_file:902-905`）；判据自身运行异常 ⇒ 显式 UNKNOWN（runner `_ec_s4_all.py:37-40`，不许静默）；E1/E2 证据为 0 ⇒ UNKNOWN 而非 PASS。**声明为静态盲区、明确不判的**（合成控实证见 §4d）：

1. verdict-as-data（裁决词作字典值/返回值流转，如 `{"VERDICT": "PASS"}` 经 json 打印/落盘）；
2. 分支可达性（死分支、恒真 return 1）；
3. E4 名字级≠值级；
4. 语义级吞没；
5. emitter 通道只识别「纯 append 的模块级 emitter→缓冲→print」形态；
6. 被 import 的门禁（出口在调用方）——库形态落 UNKNOWN；
7. 跨文件消费（脚本 A 的 stdout 裁决被脚本 B 解析）；
8. 动态拼接的裁决词字符串；
9. E2 早退门对扫描器形态代码的高估；
10. GA2 不覆盖 match/case 两臂；GA2 词对启发式存在 prose 两臂误报通道（散文里同时出现 PASS/FAIL 词）。

---

## 4 ★ 正反控

### 4a 18 件对照表（实跑 `_ec_s3_controls.py` 复跑复现，输出 json 复跑前后 sha256 一致）

命令：`python -I -X utf8 …/_ec_s3_controls.py`；`_ec_s3_results.json` 复跑前 sha256=`0a01df05053de7eec744560bb822342d1242d38f9aa76198bec09b57ef9eea8f`（21722 字节），复跑后**逐字节相同**。18/18 与设计预期一致：

| # | 角色 | 脚本 | verdict / class | E1/E2/E3/E4 | 触发要件依据（file:line） |
|---|---|---|---|---|---|
| 1 | **正控** | `lead/d27_ruling_20261106/check_d27.py` | OK / GATE | P/P/P/P | E1 {0,1,2}（:59,:99,:101）；E2 10 来源（:48,:56 早退门…）；E3 :66 handler 转登记 |
| 2 | **正控** | `lead/d28_ruling_20261106/check_d28.py` | OK / GATE | P/P/P/P | E1 :111/:114/:116；E2 11 来源；E3 :63,:66 |
| 3 | **正控** | `lead/d29_ruling_20261106/check_d29.py` | OK / GATE | P/P/P/P | E1 :101/:104/:106；E2 11 来源；E3 :59,:61 |
| 4 | **正控** | `lead/d30_ruling_20261106/check_d30.py` | OK / GATE | P/P/P/P | E1 :101/:104/:106；E2 11 来源；E3 :59,:61 |
| 5 | **反控①** | `lead/goal1_a8_fix_20261022/VERIFY_A8.py` | **NEEDS_FIX** / GATE | **F**/P/P/P | E1 FAIL `:796` `return 0` 恒定 ⇒ EXIT=0 零信息；E2 :53,:55 record() 登记；E3 :783 handler 经 record() 转 PASS（`:785`） |
| 6 | **反控②** | `lead/re_line_20261105/D21_RULING/_d21_burden5.py` | OK / PROBE | -/-/-/- | 零出口+零真写+26 print ⇒ 探针正确形态，不该有出口 |
| 7 | **反控②** | `lead/re_line_20261105/V6_V3_REVIEW/_leader_crossframe_check.py` | OK / PROBE | -/-/-/- | 同上（44 print） |
| 8 | **反控②** | `lead/re_line_20261105/_leader/_a7_acf_probe.py` | OK / ARTIFACT | -/-/-/- | 真写 `:161` ⇒ 登记产物+指纹 |
| 9 | **反控②** | `lead/re_line_20261105/_leader/_intra_frame_census.py` | OK / ARTIFACT | -/-/-/- | 真写 `:165` |
| 10 | 新样本 | `lead/dtrigger_compare_20261107/_check_dtrigger.py` | OK / GATE | P/P/P/P | 内联出口 `:228` `raise SystemExit(0 if ok else 1)`；E2 And 聚合 `:34` + 17 处检查调用；E4 交集 {ok} |
| 11 | 新样本 | `lead/w2_samecause_20261109/_w2w_fp9.py` | OK / GATE | P/P/P/P | 出口 `:45` `sys.exit(0 if ok == 9 else 1)`；E2 :29 赋值+:41 累计(+=)+出口比较；E3 :34 handler 打 READ_FAIL 非吞 |
| 12 | 新样本 | `lead/bexec_n4_20261108/_n4_ast_scan.py` | **NEEDS_FIX** / GATE | F/P/**F**/P | E1 `:300` `return 0` 恒定；E3 `:57` handler 体惰性吞（`:58` 仅 decode-replace）——与普查 CONSTANT_EXIT 一致 |
| 13 | 新样本 | `lead/check_masking_20261109/_cm_inject.py` | **NEEDS_FIX** / GATE | F/P/P/P | E1 `:215` `return 0`；E4 摘要写盘通道 `:213` `dest.write_text` |
| 14 | 新样本 | `lead/advset_indep_20261109/_ai2_selfcheck2.py` | OK / PROBE | -/-/-/- | stdout 观测（6 print） |
| 15 | 新样本 | `lead/a_dim_reduced_20261108/_verify_hy4_recompute.py` | OK / ARTIFACT | -/-/-/- | `:471` `write_text(OUT)` |
| 16 | 新样本 | `lead/chain_vs_single_20261109/_cs_attrib.py` | OK / PROBE | -/-/-/- | `:16` 仅 1 条前置 assert（fingerprint mismatch）非裁决 ⇒ 不触发 GATE（被测领域词不误报的实证；与普查 VERDICT_VIA_ASSERT_ONLY 标记的口径差见 §4e） |
| 17 | 新样本 | `lead/cert_realcheck_20261109/_cr_real_verify.py` | OK / ARTIFACT | -/-/-/- | verdict 字典写 `:458` `(WDIR/"_cr_verify_out.json").write_text(…)` ⇒ 产物件（verdict-as-data 盲区，人工复核同判 ARTIFACT） |
| 18 | 新样本 | `lead/check_family_20261109/_cf_compose_lineage.py` | OK / ARTIFACT | -/-/-/- | `:409` `write_text(OUT)` |

**正控判定如实声明：四件门禁正控全部 OK（E1–E4 全 PASS），没有被放水。** 反控① VERIFY_A8 如实判 NEEDS_FIX（E1 FAIL 根因 = main 唯一 return 是恒定 0@`:796`，8 项检查的失败只走 record() 登记+print，退出码不随检查结果变化）。反控② 四件零出口件全部 OK（出口不适用）。若判据把正控判成 NEEDS_FIX 或把反控①放行，均会在本表如实记录——实际未发生。

### 4b 过拟合检验（9 件编排方未列新样本）

9 件新样本覆盖了内联动态出口（#10）、计数器聚合（#11）、恒 0 出口（#12,#13）、verdict-as-data 产物件（#17）、前置 assert（#16）、emitter 通道（GA2 实现在 263 件 `_c97_check.py` 上验证，§5d）等已知 9 件未覆盖的形态。判据实现经多轮修正——设计申报 6 个修正点（Raise 参数解析、IfExp 通道、emitter→缓冲→print 数据流、单标量内联驱动、swallow 惰性体、E4 写盘通道），`_ec_report.md:326-327` 记为「3 轮修正」但同列 6 个修正点；两处轮次口径差如实记录，修正点清单一致，每轮均以 18 件正反控回归（本轮复跑 = 第 N+1 次回归，仍 18/18）。

### 4c 复核员独立重写判据的比对（`_ecv_compare_results.json`，本会话实读）

复核员从零重写判据 `_ecv_judge.py`（27264 字节）后逐件比对：33 对（9 样本 + 12 自选 + 12 合成/改名控）**32/33 全一致**；full263 全量 `class_mismatch=[]`、`reviewer_exit_found=[]`（独立出口检出=0）。唯一分歧：合成控 `_ecv_ctl_c_single_scalar.py`——设计员 E2=PASS，复核员按书面规格应 E2 FAIL ⇒ NEEDS_FIX。根因见 §4d(1)，属「规格与实现二选一对齐」事项，对 263+18 现有语料零影响（`_check_dtrigger`/`_w2w_fp9` 在从紧口径下证据仍 ≥2）。

### 4d 盲区合成控（本会话实跑判据于复核员合成控，逐件给结果）

| 合成控（写域内 `_ecv_ctl_*.py`） | 本会话实跑结果 | 证明什么 |
|---|---|---|
| `_ecv_ctl_f_prose_fp.py` | GATE / NEEDS_FIX（E1 FAIL `:10` exit(0) 直书） | GA2 词对启发式存在 **prose 两臂误报通道**（散文双判据同触发）——已声明盲区；263 件实跑未见实害（若误报，PROBE/ARTIFACT 件会落 GATE，计数会偏，见 §5a 分歧=0） |
| `_ecv_ctl_i_match_case.py` | PROBE / EXIT_ZERO_INFO | match/case 两臂不在 GA2 覆盖内；263 件中 `ast.Match` 计数 = **0**（本会话重扫），语料外无保证 |
| `_ecv_ctl_d_verdict_as_data.py` | PROBE / OK | verdict-as-data 确实不判（声明盲区，不是「判不出写成已覆盖」） |
| `_ecv_ctl_c_single_scalar.py` | GATE / OK（E2=P） | 实现把普通「驱动名赋值」计为内联证据（`_ec_criterion.py:619-620` else 分支），宽于自家规格（docstring `:40-42` 只列 And 聚合/+=/checker 调用/出口比较）——**规格与实现待二选一对齐** |
| `_ecv_ctl_j_main_bool_aggregate.py` | GATE / NEEDS_FIX（E2=**U**） | E2 不追 main 内布尔 And 聚合 ⇒ UNKNOWN→需人工，保守方向，无错判 |
| `_ecv_ctl_r1_selfcheck_probe.py`（= check_d29 改名）/ `_ecv_ctl_r2_gate_verify.py`（= _d21_burden5 改名） | GATE / OK 与 PROBE / OK | 分类**不依赖文件名**（改名门禁仍 GATE，改名探针仍 PROBE） |

### 4e 与普查口径的两处如实差异

- 普查 `VERDICT_VIA_ASSERT_ONLY=54`（263 内带 assert 裁决标记）vs 判据 GATE-E3 仅 2 件：判据要求**带裁决词**（POS/NEG 字样）的 assert ≥2 才触发；其余多为裸 `assert x == y` 守卫形态，判据视为观测而非 stdout 裁决。两口径差异如实呈现，不强行归一（52 件归一留人工，`_ec_report.md:309`）。
- `write_lines` 字段弃用（§2c）。

---

## 5 ★ 263 件三分类处置

### 5a 总量与交叉核对（实跑 `_ec_s4_all.py` 复跑复现，json 复跑前后 sha256 一致）

命令：`python -I -X utf8 …/_ec_s4_all.py`。输出：`census rows = 413 ; final_classes = {'NO_EXIT_AT_ALL': 263, 'CONDITIONAL_EXIT': 132, 'CONSTANT_EXIT': 18}`；`NO_EXIT_AT_ALL = 263`。名单取自 `lead/const_exit_20261109/_ce_final_out.json`（只读）。`_ec_s4_results.json` 复跑前 sha256=`a081f04bc682088c745b8bd61622e92aa1baf6b0f6fe8bf0713d54bb3ea444d8`（199686 字节），复跑后逐字节相同。

| 类 | 件数 | verdict | 显式出口检测与普查分歧 |
|---|---|---|---|
| PROBE | **122** | OK 122 | 分歧 = **0**（263 件确实全部无显式出口；判据 `n_exit>0` 检测与普查 cls 逐件一致） |
| ARTIFACT | **102** | OK 102 | |
| GATE | **21** | NEEDS_FIX 21 | |
| UNKNOWN | **18** | NEEDS_FIX(人工) 18 | |

verdict 合计 **OK 224 / NEEDS_FIX 39**（21+18）。263 件中含 `ast.Match` 的件数 = 0（本会话重扫取证）。复核员独立重写判据全量复跑：class 分歧 0、出口检出分歧 0（`_ecv_compare_results.json` full263 段）。

### 5b PROBE 122 件 —— 不改脚本，改登记口径

处置：脚本不动；登记口径从 `EXIT=0` 改为「**捕获 stdout/摘要文本 + sha256 + 字节数**」，不登记 EXIT。代表（本会话从 `_ec_s4_results.json` 实取，verdict=OK）：

- `lead/advset_indep_20261109/_ai2_baseline.py`（20 print）、`_ai2_selfcheck.py`（22 print）
- `lead/b2b_candidate_review3_20261107/_review_probe_r3.py`（69 print）
- `lead/bexec_n4_20261108/_n4_fingerprint.py`（3 print）

### 5c ARTIFACT 102 件 —— 不改脚本，改登记口径

处置：登记口径改为「**产物文件 + sha256 + 字节数**」，不登记 EXIT。真写形态（每件首写站点分类）：`write_text` 72 / `open-w` 19 / `write_bytes` 11 = 102 件（全量真写站点 152 处：write_text 99 / write_bytes 29 / open 24——本会话按判据 `collect_true_writes` 口径重扫取证）。代表：

- `lead/a_dim_reduced_20261108/_verify_hy4_recompute.py`（`:471` write_text(OUT)）
- `lead/advset_indep_20261109/_ai_grade.py`（`:285` write_text → `_ai_grade_out.json`）、`_ai_invariants.py`（`:190`）
- `lead/b2_preaudit_20261106/_b2_probe.py`（`:292` write_text(OUT)）
- `lead/cert_realcheck_20261109/_cr_real_verify.py`（`:458` 写 `_cr_verify_out.json`）

### 5d GATE 21 件（NEEDS_FIX）—— 必须加出口 + 已登记行加注

**19 件 E0**（stdout 互斥裁决对/单侧负裁决而零出口；每件裁决对现场本会话逐行实读/判据 reason 带行号，全部是脚本对**自身检查**的二值裁决，非被测对象领域词误报）：

```
lead/c07_protocol_attacks_20261109/_pa_a9_nfkc_probe.py :27  "PASS" if SESSION_RE.fullmatch(s) else "FAIL"（本会话实读 :24-29 print 内 IfExp）
lead/c97_scope_recheck_20261108/_c97_check.py           :135 emit→缓冲(:19)→print(:205) 通道 "PASS" if not mismatch else "FAIL"（本会话实读三处）
lead/counterpart_fix_20261109/_cf_enum_counterpart.py   :168 "ALL_PASS" if bad == 0 else "FAIL"（单侧 NEG 触发）
lead/d13b_design_20261106/_test_state_machine.py        :65-69 print("[PASS]…")(:66) / print("[FAIL]…")(:69) 对（本会话实读）
lead/dtrigger_round2_20261107/_dC_recompute.py          :218-219 "PASS" if len(A_nf_eq_ideal)==54 and … else "FAIL"
lead/evidence_indep_20261109/_ei_n13_predicates_src.py  :344 "FAIL" if p else "PASS"（库+内嵌自检混合）
lead/gate_fp7_20261108/_g7_reverse_validate.py          :49  ("PASS" if ok else "FAIL")
lead/gate_n13_20261109/_n13_predicates.py               :344 同上（内嵌最小自检）
lead/gate_v1v2_20261109/_v12_verify.py                  :167 "PASS" if ok else "FAIL"
lead/gate_v1v2_20261109/_v12v_fair.py                   :34  "PASS" if v["verdict"]=="V2" else "FAIL"
lead/matrix_row5_20261109/_r5_probe_import.py           :98  "PROBE_ALL_" + ("PASS" if allpass else "FAIL")
lead/needle_norm_20261109/_nd_l1fix.py                  :84  "FIXTURE_SELF_TEST = PASS/FAIL"
lead/needle_norm_20261109/_nn_norm.py                   :274 同上（allok 驱动）
lead/spec_static_closure_20261108/_sc_scan.py           :117 "OK" if d900 == 900.0 else "FAIL"
lead/strict_exposure_20261109/_se_enum.py               :176 "ALL_PASS" if bad == 0 else "FAIL"（本会话实读）
lead/u5u6_mirror_20261109/_m5_mirror_check.py           :17  f"[{'PASS' if ok else 'FAIL'}] {name}"
lead/w2_samecause_20261109/_w2v_probe1.py               :39  ("PASS" if cond else "FAIL")
lead/w2_samecause_20261109/_w2v_probe2.py               :109 "PASS" if pass_all else "FAIL"
lead/whitelist_audit_20261109/_wl_step1_repro.py        :78  "PASS" if hit else "**FAIL**"
```

**2 件 E3**（assert 通道顶替出口；本会话实读）：

```
lead/r33e_merge_20261109/_re_struct_diff.py          :23-24 assert …,"GUARD FAIL: original drifted"（主判定 struct_ok 写 :54 OUT.write_text(json…)）
lead/re_line_20261105/V6_V3_REVIEW/_v6_r5.py         :110-112 及 :209/:229/:231/:251/:253 assert 承载正反例裁决（本会话实读 :110-113）
```

**加出口模板**（以在库合格样板 `_check_dtrigger.py:31-35` + `:226-228` 为原型，本会话实读逐字核对；四个 E 要件齐全）：

```python
ok = True
def check(name, cond, detail=""):
    global ok
    ok = ok and bool(cond)                                   # E2：And 聚合，全部检查通过才置真
    print(("  [PASS] " if cond else "  [FAIL] ") + name)     # E4：同一 cond 驱动摘要与聚合
# ……各项检查改为 check(...)
print("核验结论: " + ("ALL PASS" if ok else "FAIL"))          # E4：同源总结（:226 原型）
raise SystemExit(0 if ok else 1)                             # E1：动态状态 {0,1}（:228 原型）
```

assert 通道 2 件（`_re_struct_diff`/`_v6_r5`）：把 assert 失败改为失败登记 + 末尾同一出口。**特别注意**：`_n13_predicates.py` 与 `_ei_n13_predicates_src.py` 是「库 + 内嵌自检」混合形态——出口只加在 `if __name__ == "__main__"` 块内，勿动库本体（两件被别的脚本 import 复用）。

### 5e UNKNOWN 18 件 —— 逐件人工，不许批量

16 件带「疑似库模块/零可见产物脚本」提示（先确认有无脚本化运行方式；确认为库件则按共享库产物登记，出口不适用）：`lead/count_invariant_20261109/_civ_lib.py`（def/class 3、顶层可执行 2）、`lead/d13b_design_20261106/_state_machine.py`（1/25）、`lead/gate_fp7_20261108/_g7_predicates.py`（8/13）、`lead/gate_r9sem_20261109/_r9s_predicates.py`（17/32）、`lead/gate_v1v2_20261109/_v12_rule.py`（4/17）、`lead/h5_governance_20261109/_h5_pasteable.py`（4/14）、`lead/minhard_check_20261109/_mhz_blocks2.py`（6/43）、`_mhz_lines2.py`（3/10）、`_mhz_slice.py`（3/21）、`_mhz_verify.py`（7/46）、`lead/r11_f2_fix_20261109/_f2_r11plus.py`（5/9）、`lead/r2_unclosed_cd_20261108/_cd_check.py`（4/109）、`_cdreport_check.py`（4/79）、`_verify_cd.py`（6/163）、`lead/re_line_20261105/A1_SAMPLER_CANDIDATE/frame_edge_sampler.py`（8/8，被 import 共享库）、`lead/re_line_20261105/W8_STATIC_LOCATE/reviews/_f6rev_probe.py`（10/133）。

2 件无提示（顶层无 def/class 的数据/生成件，人工定位产物通道）：`lead/gate_r9sem_20261109/_r9s_samples.py`、`lead/stale_pass_20261109/_sp_gen_word.py`。

（括号内 def/class 与顶层可执行语句数为本会话从 `_ec_s4_results.json` 逐件实取的判据 reason 原文。）

### 5f 五行台账登记的正确改法（只给文本，未改台账；可粘贴）

现文为本会话实读（§2d）；改法文本源自 `_ec_report.md` §4c（复核员逐字核对过与 GOAL 行吻合），其中 `:7634` 按复核建议补注「stdout 捕获件」（与 :7569 口径对齐，系对报告文本的唯一改进）：

| GOAL 行 | 现文（实读） | 改成 |
|---|---|---|
| `:7569` | `python -I -X utf8 ".../D21_RULING/_d21_burden5.py"                        # EXIT=0` | `python -I -X utf8 ".../D21_RULING/_d21_burden5.py"  # 产物 D21_RULING/_d21_burden5_out.txt sha256=0d77c9541ddb2eda0eacc15c5251b06667bfa41a1dd49a66012d58355723419a（1803 字节，stdout 捕获件；脚本零出口，EXIT 不适用）` |
| `:7634` | `> 交付：`V6_V3_REVIEW/_leader_crossframe_check.py` + `_out.txt`（`EXIT=0`）。零真机。` | `> 交付：`V6_V3_REVIEW/_leader_crossframe_check.py` + `_out.txt`（产物 _leader_crossframe_check_out.txt sha256=2cf4100776eb7461ef784e4fa8ec8f192439851604fde737dcb0816f045f50dc，2839 字节，stdout 捕获件；脚本零出口，EXIT 不适用）。零真机。` |
| `:8383` | `   `_leader/_a7_acf_probe.py` + `_a7_acf_probe_out.txt`（均 `EXIT=0`）。` | `   `_leader/_a7_acf_probe.py` + `_a7_acf_probe_out.txt`（产物 _a7_acf_probe_out.txt sha256=54145df6e2e1fa818df82e7ccd92e30ee8bbce972f32cdf9983e9aa50287a439，3318 字节；脚本零出口，EXIT 不适用）。` |
| `:9588` | `> 探针 `_leader/_intra_frame_census.py`，输出 `_leader/_intra_frame_census_out.txt`（`EXIT=0`）。` | `> 探针 `_leader/_intra_frame_census.py`，输出 `_leader/_intra_frame_census_out.txt`（产物 sha256=d056f88f331e968b1b6c9bf75c104d35f8df0f2e3b98829f7d94bef1b7940993，3744 字节；脚本零出口，EXIT 不适用）。` |
| `:9679` | `1. **我亲跑**：`_intra_frame_census.py` 全量 15 窗，`EXIT=0`，输出 40+ 行表格 + 三组汇总。` | `1. **我亲跑**：`_intra_frame_census.py` 全量 15 窗（脚本零出口；产物 _intra_frame_census_out.txt sha256=d056f88f331e968b1b6c9bf75c104d35f8df0f2e3b98829f7d94bef1b7940993，3744 字节），输出 40+ 行表格 + 三组汇总。` |

四件 sha256 与字节数均为本会话实算（§2a）。`:9588` 与 `:9679` 引同一产物 `sha256=d056f88f…0993`（3744 字节）。

### 5g 改造成本（**估算，未实测**）

| 项 | 量 | 单件估算 | 合计估算 |
|---|---|---|---|
| 5 行台账改字（走正常台账流程） | 5 行 | ~2 分钟 | ~10 分钟 |
| GATE 21 件加出口（含复跑验证+登记） | 21 件 | 小件 ~15 分钟、大件（如 345 行 `_n13_predicates`）~30-45 分钟 | **约 8–12 小时** |
| UNKNOWN 18 件人工甄别 | 18 件 | ~5 分钟 | ~1.5 小时 |
| 判据装配成登记前 lint（§6b） | 一次性 | — | ~半天 |

以上全部为估算，未实测；未经任何一件真实改造验证。

---

## 6 复核回件 + 结论 + 未验项

### 6a 复核回件（复核员独立重写判据后的裁决，verdict 如实记录）

**复核 verdict = confirmed。** 复核回件绑定行（格式固定，被核对象 = 判据本体 `_ec_criterion.py`，本会话实算复现同值）：

被核对象 SHA256 = e719296fb18bf6ff2112f6be62bca3c1cda19701cb5bd905a18d22fa51b7dc78，字节数 = 42136

复核要点摘要（本会话逐条实证过的以 ✅ 标注）：

1. ✅ 判据设计、18 件正反控、263 件三分类（102/122/21/18，OK 224/NEEDS_FIX 39）经复核员独立从零重写判据后逐件复现：33 对比对 32/33 一致（唯一分歧 = `_ecv_ctl_c_single_scalar` 的 E2 口径，§4c/§4d）；263 件全量 class 分歧=0、独立出口检出=0。
2. ✅ 四件门禁实读源码确认 GATE/OK 正确（any() 折叠属检查粒度 OR，不破坏出口层合取；判 NEEDS_FIX 才是错）。
3. ✅ VERIFY_A8 GATE+E1 FAIL 正确（main 唯一 return 0@`:796`；handler 经 record() `:783-785` 登记）。
4. ✅ 15 件基线指纹三遍实算全 MATCH；四件 `_out.txt` 指纹与申报一致。
5. ✅ 五行台账改法文本与 GOAL `:7569/:7634/:8383/:9588/:9679` 实读原文逐字吻合、sha256/字节数全对、可粘贴无缺字段。
6. ✅ 盲区清单与实际行为一致（控D 实证 verdict-as-data 确实不判），无「判不出写成已覆盖」。
7. ✅ 零越界：只读域零修改、不 commit（本会话终态复核见 §6d）。

复核发现的问题（均不动摇结论，本会话逐条实证）：**(1)** E2 实现宽于自家书面规格（`_ec_criterion.py:619-620` 把普通「驱动名赋值」计为内联证据，规格 docstring `:40-42` 只列 And 聚合/+=/checker 调用/出口比较）；对 263+18 语料零影响，建议规格与实现二选一对齐。**(2)** 报告 §1(c) d29/d30 的 main 返回行手抄偏 1（写 100/103/105，实为 101/104/106）；机器产物行号正确。**(3)** 两条未申报边界：GA2 prose 两臂误报通道（控F）、match/case 不在覆盖内（控I；263 件 ast.Match=0）。**(4)** E2 不追 main 内布尔 And 聚合（控J → E2 UNKNOWN，保守方向无错判）。**(5)** `:7634` 台账改文宜补「stdout 捕获件」标注（本件 §5f 已按此改进）。

### 6b 结论

**一句话回答**：一个脚本的退出码算证据，当且仅当它承载本模块判定的二值裁决（GATE 类）、由全部检查合取驱动（E2）、失败不被吞（E3）、且与逐项摘要同源（E4）、状态非常量（E1）——四要件同时成立；否则退出码只是进程善后信号，证据应改引产物文件或捕获的摘要文本，「没有出口」对 PROBE/ARTIFACT 是正确形态而非缺陷。

**装哪个环节**：**成件后、台账登记前的门禁 lint**。理由：派发的是任务不是脚本（派发前 lint 无从判起）；只报不拒会让零信息登记继续累积。装配形态：登记前跑 `classify`——GATE+NEEDS_FIX ⇒ 拒收并附 §5d 模板；ARTIFACT/PROBE ⇒ 自动提示登记口径（产物/摘要+指纹，删除 EXIT 字样）；UNKNOWN ⇒ 转人工。次选：在 check_d2x 类验收门禁本体加一条「被验脚本 classify 不得为 GATE+NEEDS_FIX」。

**能力边界**：判通道与绑定（结构层），不判语义。**判不了的**：裁决内容的对错（那是各门禁本体与人工复核的事）；摘要数值的真实性（数据级核对，另一条工作）；一件脚本「该不该被写」；台账登记行其他字段的对错；52 件 census-assert 标记件与判据口径的最终归一（留人工）；§3f/§4d 列出的十条静态盲区（verdict-as-data、分支可达性、名字级≠值级、语义级吞没、emitter 变体、被 import 门禁、跨文件消费、动态拼接判词、E2 高估、match/case 与 prose 误报通道）。

### 6c 未验项（如实）

1. 编排方 write_lines 字段的确切产生规则未复现（两假设得 14/0，均 ≠ 8）——已按「不可作产物证据」处置（§2c）。
2. 四件 `_out.txt` 产物的**内容**未逐行核对（只取了指纹、字节数与真写去向）。
3. 263 件中 21 件 GATE 的**台账登记行**未逐件核对（只核了裁决对现场）。
4. §5g 成本数字全部为估算，未实测（无一件真实改造）。
5. E4 为名字级绑定，值级同源须运行时对照，未做。
6. 分支可达性（死分支/恒真 return 1）静态判不出，未做运行时复核。
7. 判据装配成登记前 lint 的半天成本与接入方式未实测。
8. 复核员 33 对中 1 对分歧（控C 的 E2 口径）未最终裁决——待规格与实现二选一对齐后重判。
9. `_cs_attrib.py` 等与普查 VERDICT_VIA_ASSERT_ONLY 标记的口径差（54 vs 2）未归一，留人工。
10. 设计申报「6 轮修正」与报告 §6「3 轮修正」的轮次口径差未追溯逐轮记录（修正点清单一致）。

### 6d 本会话实跑命令账 + 只读域终态

```
python -I -X utf8 …/_ecw_fp.py                 # 15 基线+4 产物指纹 19/19 MATCH（含复核员绑定对象 _ec_criterion.py 实算）
python -I -X utf8 …/_ec_s1_facts.py            # 9 件样本事实复跑：8/9 逐字段一致（VERIFY_A8 write_lines 口径分歧如实）
python -I -X utf8 …/_ec_s1_ledger.py           # 五行台账行 + PENDING 0 命中取证（只读）
python -I -X utf8 …/_ec_s3_controls.py         # 18 件正反控复跑：18/18 与设计预期一致；json 复跑前后 sha256 逐字节一致
python -I -X utf8 …/_ec_s4_all.py              # 263 件全量复跑：122/102/21/18、OK224/NF39、分歧=0；json 复跑前后 sha256 逐字节一致
python -I -X utf8 …/_ecw_summarize.py          # GATE/UNKNOWN 逐件 reasons、真写形态分布、ast.Match=0 取证（只读）
python -I -X utf8（内联）                        # VERIFY_A8 write_lines 两假设检验；_ecv 合成控 7 件实跑；复核比对 JSON 摘要
Read（Read 工具实读）                            # 五行 GOAL 行、check_d27/d28/d29/d30、_check_dtrigger、_c97、_re_struct_diff、_v6_r5、
                                               # _pa_a9_nfkc_probe、_se_enum、_n4_ast_scan、_cm_inject、_w2w_fp9、
                                               # _d21/_a7/_intra 现场、_cr_real_verify:374/:458、VERIFY_A8:780-798 等
```

本会话写域新增件：`EXIT_CRITERION.md`（本件）、`_ecw_fp.py`、`_ecw_summarize.py`。设计员与复核员既有文件（`_ec_*`、`_ecv_*`）零改动（`_ec_s3_results.json`/`_ec_s4_results.json` 以复跑前后同哈希证实；其余未打开写入通道）。两件台账与全部只读目录零修改；无 commit、无 push。
