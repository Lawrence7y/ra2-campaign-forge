# -*- coding: utf-8 -*-
"""_ec_criterion.py — 出口判据（完整定义与实现）。

════════════════════════════════════════════════════════════════════
判据定义（本模块即判据本体；所有判定均为纯静态 AST + 源文本，零执行被检脚本）
════════════════════════════════════════════════════════════════════

【第一层】该不该有出口 —— 分类（class），判别轴 = 「判定的消费通道」：
  GATE     验收门禁：存在一个以「程序可消费的二值裁决」形态存在、应送达调用方
           控制流的判定 ⇒ 必须有出口。机器特征（任一）：
             GA1 出口管道：模块内存在 SystemExit 家族出口站点，且出口可达状态
                 集合 ≥2 或状态为动态表达式（数据依赖）；
             GA2 stdout 互斥裁决对：if/elif 链两臂或三元 IfExp 两臂分别出现
                 互斥裁决词对（POS: PASS/PASSED/✅/全部通过；NEG: FAIL/FAILED/
                 ❌/不通过/未通过），或恰一臂出现 NEG（单侧负裁决），且判定
                 条件非恒定；
             GA3 失败累积：裁决函数内 ≥2 处独立失败登记点（X.append/extend/add/
                 += [...]）喂给「if X: return 非零」门。
  ARTIFACT  产物脚本：真写盘（w/a/x/+ 模式 open、write_text、write_bytes）且无
            GA1/GA2 ⇒ 消费方读文件，退出码无关 ⇒ 不需要出口。
  PROBE     探针：无出口、无裁决对、无真写盘，产物=观测值/解读（print 到 stdout，
            由台账以捕获文件引用）⇒ 不判对错 ⇒ 不需要出口。
  UNKNOWN   解析失败 / 证据冲突 / 证据不足 ⇒ 逐件人工，禁止批量处置。

  设计说明：三类之别不在「有没有 print」，在「有没有一个会被下游读的判定」。
  stdout 上的散文结论（成立/不成立、「⇒ 无信号」）是报告；PASS/FAIL 互斥对才是
  布尔决策接口。单侧 NEG（只在失败臂打 FAIL）同属决策接口（调用方靠其缺席推断
  通过），故也算 GATE。被检对象的领域词（如被测检测器自身的 PASS/CATCH 判词）
  因不成对/不在条件两臂上而不会误触发 GA2。

【第二层】合格出口四要件 —— verdict（仅 GATE 类适用）：
  E1 非常量：出口可达状态集合 |S|≥2 或存在动态状态表达式（数据依赖）。
     实现：从出口参数回溯裁决函数（sys.exit(main()) → 解析 main），收集其所有
     Return 的整数常量；非字面量 Return 或内联动态表达式（IfExp/比较式直书）
     ⇒ dynamic。|S|==1 且非 dynamic ⇒ FAIL（CONSTANT_EXIT 型零信息）。
     ★ 静态局限：分支可达性（死分支）判不出，须运行时复核。
  E2 合取驱动：0 分支由「全部检查通过」驱动。
     实现（有裁决函数）：裁决函数及其直接调用的模块级函数内，统计独立失败登记点
     与「if 条件 → return 非零」早退门总数 k；k≥2 ⇒ PASS；k==1 纯标量 ⇒ FAIL。
     实现（内联动态出口，如 sys.exit(0 if ok else 1)）：追踪驱动名，统计 And
     聚合赋值 / 驱动名累计(+=) / global-checker 函数调用点 / 出口比较，证据 ≥2
     ⇒ PASS(w 计数器聚合)；==1 ⇒ FAIL 单标量；==0 ⇒ UNKNOWN。
     ★ 静态局限：登记点是否语义独立（同一数据两种投影）判不出；扫描器形态代码
     的「非零 return」早退门会高估 k（对 E1 FAIL 的件不影响终判）。
  E3 无吞：失败不经被吞的异常通道消失、异常通道不顶替出口。
     实现：裁决链（内联出口时为全模块）上每个 ExceptHandler，若体「惰性」——
     无 re-raise / 无出口调用 / 无失败登记 / 无非零 return / 无 print / 无对
     模块级自定义函数的调用（后者可能间接登记，如 record()）⇒ 吞没候选 ⇒ FAIL。
     另外：无出口管道而以 ≥2 条带裁决词的 assert 承载裁决 ⇒
     E3_IMPLICIT_EXCEPTION（异常通道顶替出口）⇒ FAIL。
     ★ 静态局限：语义级吞没（打印无害文案但丢失失败）判不出。
  E4 摘要绑定：同一次运行中退出码与逐项摘要来自同一份数据。
     实现：名字级数据流 —— 退出门守卫名集合 G（门条件 Name + 失败登记目标名 +
     内联出口驱动名）∩ 摘要引用名集合 P（print 参数 Name + 写盘调用参数 Name +
     迭代打印/写盘的循环源名）≠∅ ⇒ PASS；否则 FAIL。
     ★ 静态局限：名字级≠值级；打印裁剪子集判不出，须运行时对照。

【第三层】verdict 规则：
  GATE:     无出口 ⇒ NEEDS_FIX(E0_MISSING_EXIT)
            E1 FAIL ⇒ NEEDS_FIX(E1_CONSTANT_EXIT)        ← VERIFY_A8 型
            E2/E3/E4 任一 FAIL ⇒ NEEDS_FIX（附行号）
            E1/E2 不确定 ⇒ NEEDS_FIX(UNRESOLVED，需人工)
            全过 ⇒ OK
  ARTIFACT/PROBE: 无出口 ⇒ OK（出口不适用）
            有常量出口 ⇒ EXIT_ZERO_INFO（出口零信息：登记产物/摘要，不登记 EXIT）
            有非常量出口 ⇒ OK（出口仅承载崩溃信号，不承载验收判定）
  UNKNOWN:  NEEDS_FIX（理由码 UNKNOWN_MANUAL —— 语义为「需人工」，不是「需改码」）

  每条 reason 必带 rel:line。宁可 UNKNOWN / NEEDS_FIX(需人工)，不许猜。
"""
import ast
import re

POS_RE = re.compile(r"\bPASS(?:ED|ING)?\b|✅|全部通过|\bOK\b")
NEG_RE = re.compile(r"\bFAIL(?:ED|S)?\b|❌|不通过|未通过")

EXIT_CALL_ATTRS = ("exit", "_exit")


# ---------------------------------------------------------------- 基础读取
def read_source(abs_path):
    with open(abs_path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return raw.decode(enc), enc, None
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace"), "utf-8(replace)", "decode-fallback"


def parse_source(src):
    try:
        return ast.parse(src), None
    except SyntaxError as e:
        return None, "%s (line %s)" % (e.msg, e.lineno)


# ---------------------------------------------------------------- 出口站点
def _is_exit_call(node):
    f = node.func
    if isinstance(f, ast.Name):
        return f.id in ("exit", "quit")
    if isinstance(f, ast.Attribute):
        return f.attr in EXIT_CALL_ATTRS
    return False


def _is_systemexit_construction(node):
    if isinstance(node, ast.Call):
        f = node.func
        return (isinstance(f, ast.Name) and f.id == "SystemExit") or \
               (isinstance(f, ast.Attribute) and f.attr == "SystemExit")
    if isinstance(node, ast.Name):
        return node.id == "SystemExit"
    return False


def collect_exits(tree, src):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None \
                and _is_systemexit_construction(node.exc):
            out.append({"kind": "raise", "line": node.lineno,
                        "snippet": ast.get_source_segment(src, node) or "?"})
        elif isinstance(node, ast.Call) and _is_exit_call(node):
            out.append({"kind": "call", "line": node.lineno,
                        "snippet": ast.get_source_segment(src, node) or "?"})
    out.sort(key=lambda d: d["line"])
    return out


def exit_arg_nodes(exits, tree):
    """出口状态表达式集合：sys.exit(X)/exit(X) → X；raise SystemExit(X) → X；
    裸 raise SystemExit → 无状态表达式（不计入）。"""
    args = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc is not None \
                and _is_systemexit_construction(node.exc):
            if isinstance(node.exc, ast.Call) and node.exc.args:
                args.append(node.exc.args[0])
        elif isinstance(node, ast.Call) and _is_exit_call(node) and node.args:
            args.append(node.args[0])
    return args


# ---------------------------------------------------------------- 真写盘
def collect_true_writes(tree, src):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, (ast.Name, ast.Attribute)) and \
                    getattr(f, "attr", getattr(f, "id", None)) == "open":
                mode = None
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                for kw in node.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        mode = kw.value.value
                if isinstance(mode, str) and any(c in mode for c in "wax+"):
                    tgt = ast.get_source_segment(src, node.args[0]) if node.args else "?"
                    out.append({"line": node.lineno, "how": "open(%r)" % mode,
                                "target": (tgt or "?")[:90]})
            elif isinstance(f, ast.Attribute) and f.attr in ("write_text", "write_bytes"):
                tgt = ast.get_source_segment(src, node.func.value) if node.func.value else "?"
                out.append({"line": node.lineno, "how": f.attr,
                            "target": (tgt or "?")[:90]})
    out.sort(key=lambda d: d["line"])
    return out


def _dotted_call_name(func):
    parts = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if isinstance(func, ast.Name):
        parts.append(func.id)
        return ".".join(reversed(parts))
    return None


OUTPUT_WRITE_NAMES = ("sys.stdout.write", "sys.stdout.buffer.write",
                      "sys.stderr.write")


def count_output_channels(tree):
    """(print 调用数, 输出通道 write 调用数)。
    n_stdout_write 同数 sys.stdout.write / sys.stdout.buffer.write / sys.stderr.write；
    普通文件句柄 fh.write（dotted 名非上述三者）不计入。"""
    n_print = 0
    n_stdout_write = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if (isinstance(f, ast.Name) and f.id == "print") or \
               (isinstance(f, ast.Attribute) and f.attr == "print"):
                n_print += 1
            elif isinstance(f, ast.Attribute) and f.attr == "write" \
                    and _dotted_call_name(f) in OUTPUT_WRITE_NAMES:
                n_stdout_write += 1
    return n_print, n_stdout_write


# ---------------------------------------------------------------- 字符串常量（排除 docstring）
def _docstring_nodes(tree):
    docs = set()
    for nd in ast.walk(tree):
        if isinstance(nd, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = nd.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                docs.add(id(b[0].value))
    return docs


def _arm_strings(stmts):
    out = []
    stack = list(stmts)
    seen = set()
    while stack:
        s = stack.pop()
        if id(s) in seen:
            continue
        seen.add(id(s))
        for child in ast.iter_child_nodes(s):
            if isinstance(child, ast.Constant) and isinstance(child.value, str):
                out.append((getattr(child, "lineno", 0), child.value))
            stack.append(child)
    return out


def _test_is_deciding(test):
    for nd in ast.walk(test):
        if isinstance(nd, (ast.Compare, ast.Call, ast.Name)):
            return True
    return False


def _emitter_fns(tree):
    """模块级「只向缓冲 append」的 emitter 函数（如 emit(s)）→ (函数名集, 缓冲名集)。"""
    emitters, buffers = set(), set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and 1 <= len(node.body) <= 3:
            appends = []
            ok_shape = True
            for st in node.body:
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) \
                        and isinstance(st.value.func, ast.Attribute) \
                        and st.value.func.attr == "append" \
                        and isinstance(st.value.func.value, ast.Name):
                    appends.append(st.value.func.value.id)
                else:
                    ok_shape = False
                    break
            if ok_shape and appends:
                emitters.add(node.name)
                buffers |= set(appends)
    return emitters, buffers


def _buffer_printed(tree, buffers):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)) \
                and (getattr(node.func, "id", "") == "print"
                     or getattr(node.func, "attr", "") == "print"):
            for nd in ast.walk(node):
                if isinstance(nd, ast.Name) and nd.id in buffers:
                    return True
    return False


def _if_chain_arms(node):
    arms = [node.body]
    cur = node
    while len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
        cur = cur.orelse[0]
        arms.append(cur.body)
    if cur.orelse:
        arms.append(cur.orelse)
    return arms


# ---------------------------------------------------------------- stdout 裁决对
def verdict_pairs(tree, src):
    """在「摘要通道」（print 直调，或 emitter 函数→缓冲→print 的数据流）上，
    于 if/elif 链两臂与三元 IfExp 两臂中找互斥裁决对 / 单侧负裁决。
    通道外的裁决词（return 值、字典值、 outcome 赋值等 verdict-as-data）不判 ——
    那是本判据声明的静态盲区，交人工。"""
    pairs, single_neg = [], []
    emitters, buffers = _emitter_fns(tree)
    buffer_out = _buffer_printed(tree, buffers)

    parents = {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            parents[id(ch)] = node

    def in_summary_channel(node):
        cur = node
        while id(cur) in parents:
            cur = parents[id(cur)]
            if isinstance(cur, ast.Module):
                break
            if isinstance(cur, ast.Call):
                f = cur.func
                if isinstance(f, ast.Name) and (f.id == "print" or (buffer_out and f.id in emitters)):
                    return True
                if isinstance(f, ast.Attribute) and f.attr == "print":
                    return True
        return False

    def channel_strings(stmts):
        out = []
        stack = list(stmts)
        seen = set()
        while stack:
            s = stack.pop()
            if id(s) in seen:
                continue
            seen.add(id(s))
            if isinstance(s, ast.Call) and isinstance(s.func, (ast.Name, ast.Attribute)):
                fid = getattr(s.func, "id", "") or ""
                fattr = getattr(s.func, "attr", "") or ""
                if fid == "print" or fattr == "print" or (buffer_out and fid in emitters):
                    for nd in ast.walk(s):
                        if isinstance(nd, ast.Constant) and isinstance(nd.value, str):
                            out.append((getattr(nd, "lineno", 0), nd.value))
            for child in ast.iter_child_nodes(s):
                stack.append(child)
        return out

    def scan_arms(owner_line, test_node, arms, owner_kind, channel_ok):
        if not _test_is_deciding(test_node):
            return
        if len(arms) < 2:
            return
        arm_info = []
        for stmts in arms:
            toks = {"NEG": set(), "POS": set()}
            if channel_ok:
                if owner_kind == "ifexp":
                    # IfExp 的 body/orelse 就是字符串表达式本身（通道已确认）
                    for arm in stmts:
                        for nd in ast.walk(arm):
                            if isinstance(nd, ast.Constant) and isinstance(nd.value, str):
                                toks.setdefault("S", [])
                                s = nd.value
                                for m in NEG_RE.finditer(s):
                                    toks["NEG"].add(m.group(0))
                                for m in POS_RE.finditer(s):
                                    toks["POS"].add(m.group(0))
                else:
                    for ln, s in channel_strings(stmts):
                        for m in NEG_RE.finditer(s):
                            toks["NEG"].add(m.group(0))
                        for m in POS_RE.finditer(s):
                            toks["POS"].add(m.group(0))
            start = stmts[0].lineno if stmts else owner_line
            arm_info.append((start, toks))
        test_src = (ast.get_source_segment(src, test_node) or "?")[:70]
        for i in range(len(arm_info)):
            for j in range(len(arm_info)):
                if i == j:
                    continue
                li, ti = arm_info[i]
                lj, tj = arm_info[j]
                if ti["NEG"] and tj["POS"]:
                    pairs.append({"if_line": owner_line, "neg_arm": li, "pos_arm": lj,
                                  "neg": sorted(ti["NEG"]), "pos": sorted(tj["POS"]),
                                  "test": test_src, "kind": owner_kind})
        neg_idx = [i for i, (a, t) in enumerate(arm_info) if t["NEG"]]
        pos_idx = [i for i, (a, t) in enumerate(arm_info) if t["POS"]]
        if neg_idx and not pos_idx:
            i0 = neg_idx[0]
            single_neg.append({"if_line": owner_line, "neg_arm": arm_info[i0][0],
                               "neg": sorted(arm_info[i0][1]["NEG"]),
                               "test": test_src, "kind": owner_kind})

    for node in ast.walk(tree):
        if isinstance(node, ast.If):
            scan_arms(node.lineno, node.test, _if_chain_arms(node), "if", True)
        elif isinstance(node, ast.IfExp):
            scan_arms(node.lineno, node.test, [[node.body], [node.orelse]], "ifexp",
                      in_summary_channel(node))
    seenp, pded = set(), []
    for p in pairs:
        key = (p["if_line"], tuple(sorted(p["neg"])), tuple(sorted(p["pos"])))
        if key not in seenp:
            seenp.add(key)
            pded.append(p)
    seens, sded = set(), []
    for s in single_neg:
        key = (s["if_line"], tuple(sorted(s["neg"])))
        if key not in seens:
            seens.add(key)
            sded.append(s)
    return pded, sded


# ---------------------------------------------------------------- assert 事实
def assert_facts(tree, src):
    n_assert = 0
    verdict_asserts = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assert):
            n_assert += 1
            seg = ast.get_source_segment(src, node) or ""
            msg = ""
            if isinstance(node.msg, ast.Constant):
                msg = str(node.msg.value)
            if NEG_RE.search(seg) or NEG_RE.search(msg) or POS_RE.search(msg):
                verdict_asserts.append({"line": node.lineno, "snippet": seg[:90]})
    return n_assert, verdict_asserts


# ---------------------------------------------------------------- 裁决函数解析
def _module_defs(tree):
    return {nd.name: nd for nd in tree.body if isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef))}


def resolve_verdict_fns(tree, args):
    defs = _module_defs(tree)
    fns = []
    for arg in args:
        if isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) and arg.func.id in defs:
            fns.append(defs[arg.func.id])
        elif isinstance(arg, ast.Name) and arg.id in defs:
            fns.append(defs[arg.id])
    uniq, seen = [], set()
    for f in fns:
        if id(f) not in seen:
            seen.add(id(f))
            uniq.append(f)
    return uniq


def returned_states(fn):
    """(整数常量集合, 是否存在非字面量返回, [(line, desc)])。不含嵌套 def。"""
    states, dynamic, lines = set(), False, []

    def walk(stmts):
        nonlocal dynamic
        for s in stmts:
            if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(s, ast.Return):
                v = s.value
                if v is None:
                    states.add(0)
                    lines.append((s.lineno, "return None(缺省)"))
                elif isinstance(v, ast.Constant) and isinstance(v.value, int) \
                        and not isinstance(v.value, bool):
                    states.add(v.value)
                    lines.append((s.lineno, "return %d" % v.value))
                elif isinstance(v, ast.Constant):
                    lines.append((s.lineno, "return %r(非 int 常量)" % (v.value,)))
                else:
                    dynamic = True
                    lines.append((s.lineno, "return <非字面量>"))
            for ch in ast.iter_child_nodes(s):
                if isinstance(ch, list):
                    walk(ch)
                elif isinstance(ch, ast.stmt):
                    walk([ch])

    walk(fn.body)
    return states, dynamic, lines


def scope_set(tree, v_fns):
    defs = _module_defs(tree)
    scope, seen, stack = [], set(), list(v_fns)
    while stack:
        fn = stack.pop()
        if id(fn) in seen:
            continue
        seen.add(id(fn))
        scope.append(fn)
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                    and node.func.id in defs:
                stack.append(defs[node.func.id])
    return scope


def failure_sites(scope):
    sites = []
    for fn in scope:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr in ("append", "extend", "add", "insert",
                                           "appendleft", "update") \
                    and isinstance(node.func.value, ast.Name):
                sites.append((node.lineno, "append", node.func.value.id))
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) \
                    and isinstance(node.op, ast.Add) and isinstance(node.value, (ast.List, ast.Tuple)):
                sites.append((node.lineno, "+=", node.target.id))
    sites.sort()
    out, seen = [], set()
    for ln, kind, name in sites:
        key = (ln, name)
        if key not in seen:
            seen.add(key)
            out.append((ln, kind, name))
    return out


def gate_ifs(scope):
    gates = []
    for fn in scope:
        for node in ast.walk(fn):
            if isinstance(node, ast.If):
                rets = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                nonzero = False
                for r in rets:
                    if r.value is not None and isinstance(r.value, ast.Constant) \
                            and isinstance(r.value.value, int) and r.value.value != 0:
                        nonzero = True
                    elif r.value is not None and not isinstance(r.value, ast.Constant):
                        nonzero = True
                if nonzero:
                    cond = ast.unparse(node.test) if hasattr(ast, "unparse") else "?"
                    gates.append((node.lineno, cond[:70]))
    gates.sort()
    out, seen = [], set()
    for ln, cond in gates:
        if ln not in seen:
            seen.add(ln)
            out.append((ln, cond))
    return out


def _assigns_decision_name(stmts):
    """try/handler 体内是否存在赋值给「判定变量」的候选：
    ast.Name 目标（模块级/函数级变量，含 ok/flag/errors…）一律计入；
    Subscript/Attribute 目标（d[k]=… / obj.x=…）为数据容器写入，不计入。
    裸 Expr / Import / Continue 等不计入。"""
    for st in stmts:
        for nd in ast.walk(st):
            if isinstance(nd, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                tgts = nd.targets if isinstance(nd, ast.Assign) else [nd.target]
                if any(isinstance(t, ast.Name) for t in tgts):
                    return True
    return False


def _parse_tolerance_handler(handler, try_node):
    """解析容错豁免：try 体无判定变量赋值（只构造数据/解析/格式转换），
    且 handler 体为 pass 或仅赋值到数据容器（无 Name 赋值、无重抛/登记/
    非零 return/print/自定义函数调用/控制流语句）。"""
    if _assigns_decision_name(try_node.body):
        return False
    for st in handler.body:
        if isinstance(st, ast.Pass):
            continue
        if isinstance(st, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            tgts = st.targets if isinstance(st, ast.Assign) else [st.target]
            if all(isinstance(t, (ast.Subscript, ast.Attribute)) for t in tgts):
                continue
            return False
        return False
    return True


def swallow_handlers(scope, src):
    """裁决链上的 except handler 分类。
    吞没候选 = handler 体「惰性」：无 re-raise / 无出口调用 / 无失败登记 /
    无非零 return / 无 print / 无对模块级自定义函数的调用。
    parse_only = 仅解析容错（try 体不写判定变量 + handler 仅 pass/容器赋值），
    判据无法静态断言其是否影响判定 ⇒ 豁免吞没帽子，E3 转 UNKNOWN 人工。"""
    user_fns = set()
    for fn in scope:
        nm = getattr(fn, "name", None)
        if nm:
            user_fns.add(nm)
    parent_try = {}
    for fn in scope:
        for tr in ast.walk(fn):
            if isinstance(tr, ast.Try):
                for h in tr.handlers:
                    parent_try[id(h)] = tr
    out = []
    for fn in scope:
        for node in ast.walk(fn):
            if isinstance(node, ast.ExceptHandler):
                body_has = {"raise": False, "exit": False, "register": False,
                            "nonzero": False, "print": False, "user_call": False}
                for nd in ast.walk(node):
                    if isinstance(nd, ast.Raise):
                        body_has["raise"] = True
                    elif isinstance(nd, ast.Call) and _is_exit_call(nd):
                        body_has["exit"] = True
                    elif isinstance(nd, ast.Call) and isinstance(nd.func, ast.Attribute) \
                            and nd.func.attr in ("append", "extend", "add", "update") \
                            and isinstance(nd.func.value, (ast.Name, ast.Subscript, ast.Attribute)):
                        body_has["register"] = True
                    elif isinstance(nd, ast.Call) and isinstance(nd.func, ast.Name) \
                            and nd.func.id in user_fns:
                        body_has["user_call"] = True
                    elif isinstance(nd, ast.Return) and nd.value is not None \
                            and isinstance(nd.value, ast.Constant) \
                            and isinstance(nd.value.value, int) and nd.value.value != 0:
                        body_has["nonzero"] = True
                    elif isinstance(nd, ast.Call) and isinstance(nd.func, (ast.Name, ast.Attribute)) \
                            and (getattr(nd.func, "id", "") == "print"
                                 or getattr(nd.func, "attr", "") == "print"):
                        body_has["print"] = True
                swallowed = not any(body_has.values())
                tr = parent_try.get(id(node))
                parse_only = bool(swallowed and tr is not None
                                  and _parse_tolerance_handler(node, tr))
                out.append({"line": node.lineno, "swallow": swallowed,
                            "parse_only": parse_only,
                            "why": {k: v for k, v in body_has.items() if v},
                            "fn": getattr(fn, "name", "<module>")})
    return out


def gate_and_print_names(scope, src):
    """退出门守卫名 G ∩ 摘要引用名 P（print + 写盘两通道）。"""
    G, P = set(), set()
    for fn in scope:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr in ("append", "extend", "add", "update") \
                    and isinstance(node.func.value, ast.Name):
                G.add(node.func.value.id)
            elif isinstance(node, ast.If):
                rets = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                if any(r.value is not None and isinstance(r.value, ast.Constant)
                       and isinstance(r.value.value, int) and r.value.value != 0 for r in rets):
                    for nd in ast.walk(node.test):
                        if isinstance(nd, ast.Name):
                            G.add(nd.id)
            elif isinstance(node, ast.Return) and isinstance(node.value, ast.IfExp):
                # return 0 if ok else 1 与 if ok: return 0 语义等价，守卫名同收
                for part in (node.value.test, node.value.body, node.value.orelse):
                    for nd in ast.walk(part):
                        if isinstance(nd, ast.Name):
                            G.add(nd.id)
            elif isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)) \
                    and (getattr(node.func, "id", "") == "print"
                         or getattr(node.func, "attr", "") == "print"):
                for nd in ast.walk(node):
                    if isinstance(nd, ast.Name):
                        P.add(nd.id)
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                    and node.func.attr in ("write", "write_text", "write_bytes"):
                for nd in ast.walk(node):
                    if isinstance(nd, ast.Name):
                        P.add(nd.id)
            elif isinstance(node, ast.For):
                has_summary = any(
                    isinstance(n, ast.Call) and isinstance(n.func, (ast.Name, ast.Attribute))
                    and (getattr(n.func, "id", "") == "print"
                         or getattr(n.func, "attr", "") in ("write", "write_text", "write_bytes"))
                    for n in ast.walk(node))
                if has_summary:
                    for nd in ast.walk(node.iter):
                        if isinstance(nd, ast.Name):
                            P.add(nd.id)
    return G, P


def inline_exit_evidence(tree, args):
    """内联动态出口（如 sys.exit(0 if ok else 1)）的 E2 证据：驱动名 →
    And 聚合赋值 / 驱动名累计(+=) / global-checker 调用点 / 出口比较。"""
    driver = set()
    for a in args:
        for nd in ast.walk(a):
            if isinstance(nd, ast.Name) and isinstance(nd.ctx, ast.Load):
                driver.add(nd.id)
    ev = []
    checkers = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            globs = set()
            for st in node.body:
                if isinstance(st, ast.Global):
                    globs |= set(st.names)
            if driver & globs:
                checkers.add(node.name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id in driver:
                    if isinstance(node.value, ast.BoolOp) and isinstance(node.value.op, ast.And):
                        ev.append((node.lineno, "And 聚合赋值"))
                    else:
                        ev.append((node.lineno, "驱动名赋值"))
        elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name) \
                and node.target.id in driver:
            ev.append((node.lineno, "驱动名累计(+=)"))
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in checkers:
            ev.append((node.lineno, "检查调用(%s)" % node.func.id))
    for a in args:
        if isinstance(a, (ast.IfExp, ast.Compare)):
            ev.append((a.lineno, "出口表达式比较"))
    out, seen = [], set()
    for ln, d in ev:
        if ln not in seen:
            seen.add(ln)
            out.append((ln, d))
    return sorted(out), sorted(driver)


# ---------------------------------------------------------------- 主判定函数
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
    n_prints, n_stdout_write = count_output_channels(tree)
    n_output = n_prints + n_stdout_write
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
            cls = "ARTIFACT" if writes else ("PROBE" if n_output else "UNKNOWN")
            if cls == "UNKNOWN":
                R(("CLASS", rel, "有出口但无 GA1/GA2/GA3 证据、无真写盘、无 print → 需人工"))
    else:
        if pair_evidence:
            cls = "GATE"
        elif assert_evidence:
            cls = "GATE"
        elif writes:
            cls = "ARTIFACT"
        elif n_output:
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
        real_sw = [h for h in sw if not h.get("parse_only")]
        if real_sw:
            e["E3"] = "FAIL"
            for h in real_sw[:6]:
                R(("E3", relref(h["line"]),
                   "FAIL：异常被吞（体惰性：无登记/无重抛/无非零出口/无打印/无函数调用），fn=%s" % h["fn"]))
        elif sw:
            e["E3"] = "UNKNOWN"
            for h in sw[:6]:
                R(("E3", relref(h["line"]),
                   "UNKNOWN：吞点均为解析容错（try 体不写判定变量 + handler 仅 pass/容器赋值），"
                   "静态判据无法断言其是否影响判定 ⇒ 转人工，不扣缺陷帽子，fn=%s" % h["fn"]))
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


def _facts_dict(exits, writes, n_prints, pairs, single_neg, n_assert, v_asserts):
    return {
        "n_exit": len(exits),
        "exit_lines": [x["line"] for x in exits],
        "n_true_writes": len(writes),
        "true_writes": writes[:6],
        "n_prints": n_prints,
        "n_pairs": len(pairs),
        "n_single_neg": len(single_neg),
        "n_assert": n_assert,
        "n_verdict_asserts": len(v_asserts),
    }


# ---------------------------------------------------------------- 文件级入口
def analyze_file(abs_path, rel):
    src, enc, err = read_source(abs_path)
    tree, perr = parse_source(src)
    if tree is None:
        return {"rel": rel, "class": "UNKNOWN", "verdict": "NEEDS_FIX",
                "e": {}, "reasons": [("PARSE", rel, "语法解析失败 %s → 需人工" % perr)],
                "facts": {}}
    return classify(rel, tree, src)


if __name__ == "__main__":
    print(__doc__)
