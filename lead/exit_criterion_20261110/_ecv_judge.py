# -*- coding: utf-8 -*-
"""_ecv_judge.py — 复核员独立实现的出口判据。

只依据设计员报告 _ec_report.md §2 的书面规格从零实现（代码结构、遍历方式、数据结构
均为独立编写，未复制 _ec_criterion.py 的实现）。零执行被检脚本，纯静态 AST+源文本。

分类（判别轴=判定的消费通道）：
  GATE     GA1 出口管道（出口站点且可达状态≥2/动态）| GA2 stdout 互斥裁决对/单侧负裁决
           （if/elif 两臂或 IfExp 两臂，POS/NEG 词对或单臂 NEG，条件非恒定）
           | GA3 失败累积（裁决链内 ≥2 处失败登记）；无出口时带裁决词 assert≥2 亦为 GATE（异常通道顶替）
  ARTIFACT 真写盘（open w/a/x/+、write_text、write_bytes）且无 GA1/GA2
  PROBE   无出口/无裁决对/无真写盘而有 print
  UNKNOWN  解析失败或四类特征全无

verdict：GATE 无出口→NEEDS_FIX(E0)；E1 FAIL 或 E2/E3/E4 任一 FAIL→NEEDS_FIX；
E 不确定→NEEDS_FIX(需人工)；全过→OK；ARTIFACT/PROBE 无出口→OK、全常量出口→EXIT_ZERO_INFO；
UNKNOWN→NEEDS_FIX(UNKNOWN_MANUAL)。
"""
import ast
import re

POS_RE = re.compile(r"\bPASS(?:ED|ING)?\b|✅|全部通过|\bOK\b")
NEG_RE = re.compile(r"\bFAIL(?:ED|S)?\b|❌|不通过|未通过")
REG_ATTRS = ("append", "extend", "add", "insert", "appendleft", "update")


def mod_funcs(tree):
    return {n.name: n for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


# ---------------------------------------------------------------- 出口站点
def _is_systemexit(e):
    if isinstance(e, ast.Name):
        return e.id == "SystemExit"
    if isinstance(e, ast.Call):
        f = e.func
        return (isinstance(f, ast.Name) and f.id == "SystemExit") or \
               (isinstance(f, ast.Attribute) and f.attr == "SystemExit")
    return False


def exit_sites(tree):
    """[(lineno, 'raise'|'call', argnode|None)]，按行号排序。"""
    sites = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Raise) and n.exc is not None and _is_systemexit(n.exc):
            arg = n.exc.args[0] if isinstance(n.exc, ast.Call) and n.exc.args else None
            sites.append((n.lineno, "raise", arg))
        elif isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Name) and f.id in ("exit", "quit")) or \
               (isinstance(f, ast.Attribute) and f.attr in ("exit", "_exit")):
                sites.append((n.lineno, "call", n.args[0] if n.args else None))
    return sorted(sites, key=lambda t: t[0])


# ---------------------------------------------------------------- 真写盘 / print
def true_writes(tree):
    res = set()
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        name = f.id if isinstance(f, ast.Name) else \
            (f.attr if isinstance(f, ast.Attribute) else None)
        if name == "open":
            mode = None
            if len(n.args) >= 2 and isinstance(n.args[1], ast.Constant) \
                    and isinstance(n.args[1].value, str):
                mode = n.args[1].value
            for kw in n.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = kw.value.value
            if isinstance(mode, str) and set(mode) & set("wax+"):
                res.add((n.lineno, "open-%s" % mode))
        elif name in ("write_text", "write_bytes"):
            res.add((n.lineno, name))
    return sorted(res)


def n_prints(tree):
    c = 0
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Name) and f.id == "print") or \
               (isinstance(f, ast.Attribute) and f.attr == "print"):
                c += 1
    return c


# ---------------------------------------------------------------- 摘要通道
def emitters_and_buffers(tree):
    """模块级「体只做 <buf>.append(...)」的小函数 → (emitter 名集, 确被 print 引用的缓冲名集)。"""
    em, bufs = set(), set()
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and 1 <= len(n.body) <= 3:
            ok = True
            local = []
            for st in n.body:
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call) \
                        and isinstance(st.value.func, ast.Attribute) \
                        and st.value.func.attr == "append" \
                        and isinstance(st.value.func.value, ast.Name):
                    local.append(st.value.func.value.id)
                else:
                    ok = False
                    break
            if ok and local:
                em.add(n.name)
                bufs.update(local)
    printed = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Name) and f.id == "print") or \
               (isinstance(f, ast.Attribute) and f.attr == "print"):
                for x in ast.walk(n):
                    if isinstance(x, ast.Name) and x.id in bufs:
                        printed.add(x.id)
    return em, printed


def _parent_map(tree):
    pm = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            pm[id(ch)] = n
    return pm


def _in_summary_call(pm, node, emitters, buffer_out):
    """node 是否位于某个 print(...) / emitter(...) 调用实参的子树内。"""
    cur = node
    while id(cur) in pm:
        cur = pm[id(cur)]
        if isinstance(cur, ast.Module):
            break
        if isinstance(cur, ast.Call):
            f = cur.func
            if isinstance(f, ast.Name) and (f.id == "print" or (buffer_out and f.id in emitters)):
                return True
            if isinstance(f, ast.Attribute) and f.attr == "print":
                return True
    return False


def _test_deciding(test):
    for x in ast.walk(test):
        if isinstance(x, (ast.Compare, ast.Call, ast.Name)):
            return True
    return False


def _strings_in_calls(stmts, emitters, buffer_out):
    """语句块内所有 print/emitter 调用子树中的字符串常量。"""
    out = []
    stack = list(stmts)
    while stack:
        s = stack.pop()
        if isinstance(s, ast.Call):
            f = s.func
            fid = getattr(f, "id", "") or ""
            fattr = getattr(f, "attr", "") or ""
            if fid == "print" or fattr == "print" or (buffer_out and fid in emitters):
                for x in ast.walk(s):
                    if isinstance(x, ast.Constant) and isinstance(x.value, str):
                        out.append((getattr(x, "lineno", 0), x.value))
                continue
        stack.extend(ast.iter_child_nodes(s))
    return out


def _tokens(strings):
    t = {"NEG": set(), "POS": set()}
    for _, s in strings:
        for m in NEG_RE.finditer(s):
            t["NEG"].add(m.group(0))
        for m in POS_RE.finditer(s):
            t["POS"].add(m.group(0))
    return t


def find_pairs(tree):
    """(互斥裁决对列表, 单侧负裁决列表)——摘要通道上的 if/elif 两臂与 IfExp 两臂。"""
    em, printed = emitters_and_buffers(tree)
    buffer_out = bool(printed)
    pm = _parent_map(tree)
    pairs, sneg = [], []

    def scan(line, test, arms, kind, channel):
        if not _test_deciding(test) or len(arms) < 2:
            return
        info = []
        for stmts in arms:
            if kind == "ifexp":
                toks = _tokens([(0, x.value)
                                for arm in stmts
                                for x in ast.walk(arm)
                                if isinstance(x, ast.Constant) and isinstance(x.value, str)]) \
                    if channel else {"NEG": set(), "POS": set()}
            else:
                toks = _tokens(_strings_in_calls(stmts, em, buffer_out)) if channel \
                    else {"NEG": set(), "POS": set()}
            start = stmts[0].lineno if hasattr(stmts[0], "lineno") else line
            info.append((start, toks))
        for i in range(len(info)):
            for j in range(len(info)):
                if i != j and info[i][1]["NEG"] and info[j][1]["POS"]:
                    pairs.append({"line": line, "neg_at": info[i][0], "pos_at": info[j][0],
                                  "neg": sorted(info[i][1]["NEG"]), "pos": sorted(info[j][1]["POS"]),
                                  "kind": kind})
        negs = [i for i, (_, t) in enumerate(info) if t["NEG"]]
        poss = [i for i, (_, t) in enumerate(info) if t["POS"]]
        if negs and not poss:
            sneg.append({"line": line, "neg_at": info[negs[0]][0],
                         "neg": sorted(info[negs[0]][1]["NEG"]), "kind": kind})

    for n in ast.walk(tree):
        if isinstance(n, ast.If):
            arms = [n.body]
            cur = n
            while len(cur.orelse) == 1 and isinstance(cur.orelse[0], ast.If):
                cur = cur.orelse[0]
                arms.append(cur.body)
            if cur.orelse:
                arms.append(cur.orelse)
            scan(n.lineno, n.test, arms, "if", True)
        elif isinstance(n, ast.IfExp):
            scan(n.lineno, n.test, [[n.body], [n.orelse]], "ifexp",
                 _in_summary_call(pm, n, em, buffer_out))
    return pairs, sneg


# ---------------------------------------------------------------- assert
def verdict_asserts(tree, src):
    res = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Assert):
            seg = ast.get_source_segment(src, n) or ""
            msg = str(n.msg.value) if isinstance(n.msg, ast.Constant) else ""
            if NEG_RE.search(seg) or NEG_RE.search(msg) or POS_RE.search(msg):
                res.append(n.lineno)
    return res


# ---------------------------------------------------------------- E1
def return_states(fn):
    """fn 体内（不含嵌套 def）全部 Return：整数常量集 + 动态标记 + 行号。"""
    states, dyn, lines = set(), False, []
    stack = list(fn.body)
    while stack:
        s = stack.pop()
        if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(s, ast.Return):
            v = s.value
            if v is None:
                states.add(0)
                lines.append((s.lineno, "return(裸)"))
            elif isinstance(v, ast.Constant) and isinstance(v.value, int) \
                    and not isinstance(v.value, bool):
                states.add(v.value)
                lines.append((s.lineno, "return %d" % v.value))
            elif isinstance(v, ast.Constant):
                lines.append((s.lineno, "return 非int常量"))
            else:
                dyn = True
                lines.append((s.lineno, "return 非字面量"))
        stack.extend(ast.iter_child_nodes(s))
    return states, dyn, lines


def exit_states(sites, modfns):
    states, dyn, lines = set(), False, []
    for ln, _kind, arg in sites:
        if arg is None:
            continue
        if isinstance(arg, ast.Constant) and isinstance(arg.value, int) \
                and not isinstance(arg.value, bool):
            states.add(arg.value)
            lines.append((ln, "exit直书 %d" % arg.value))
        elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Name) \
                and arg.func.id in modfns:
            s, d, ls = return_states(modfns[arg.func.id])
            states |= s
            dyn = dyn or d
            lines += ls
        elif isinstance(arg, ast.Name) and arg.id in modfns:
            s, d, ls = return_states(modfns[arg.id])
            states |= s
            dyn = dyn or d
            lines += ls
        else:
            dyn = True
            lines.append((ln, "动态表达式"))
    return states, dyn, lines


# ---------------------------------------------------------------- E2/E3/E4 辅助
def scope_closure(modfns, roots):
    seen, out, stack = set(), [], list(roots)
    while stack:
        f = stack.pop()
        if id(f) in seen:
            continue
        seen.add(id(f))
        out.append(f)
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id in modfns:
                stack.append(modfns[n.func.id])
    return out


def reg_sites(scope):
    res = set()
    for f in scope:
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in REG_ATTRS and isinstance(n.func.value, ast.Name):
                res.add((n.lineno, n.func.value.id))
            elif isinstance(n, ast.AugAssign) and isinstance(n.op, ast.Add) \
                    and isinstance(n.target, ast.Name) \
                    and isinstance(n.value, (ast.List, ast.Tuple)):
                res.add((n.lineno, n.target.id))
    return sorted(res)


def gate_ifs(scope):
    res = set()
    for f in scope:
        for n in ast.walk(f):
            if isinstance(n, ast.If):
                for r in ast.walk(n):
                    if isinstance(r, ast.Return) and r.value is not None:
                        if isinstance(r.value, ast.Constant) \
                                and isinstance(r.value.value, int) and r.value.value != 0:
                            res.add(n.lineno)
                            break
                        if not isinstance(r.value, ast.Constant):
                            res.add(n.lineno)
                            break
    return sorted(res)


def handler_facts(scope, modfns):
    user = set(modfns)
    out = []
    for f in scope:
        for n in ast.walk(f):
            if isinstance(n, ast.ExceptHandler):
                flags = {"raise": False, "exit": False, "reg": False,
                         "nz": False, "print": False, "call": False}
                for x in ast.walk(n):
                    if isinstance(x, ast.Raise):
                        flags["raise"] = True
                    elif isinstance(x, ast.Call):
                        g = x.func
                        if (isinstance(g, ast.Name) and g.id in ("exit", "quit")) or \
                           (isinstance(g, ast.Attribute) and g.attr in ("exit", "_exit")):
                            flags["exit"] = True
                        elif isinstance(g, ast.Attribute) and g.attr in REG_ATTRS \
                                and isinstance(g.value, ast.Name):
                            flags["reg"] = True
                        elif isinstance(g, ast.Name) and g.id in user:
                            flags["call"] = True
                        elif (isinstance(g, ast.Name) and g.id == "print") or \
                                (isinstance(g, ast.Attribute) and g.attr == "print"):
                            flags["print"] = True
                    elif isinstance(x, ast.Return) and x.value is not None:
                        if isinstance(x.value, ast.Constant) \
                                and isinstance(x.value.value, int) and x.value.value != 0:
                            flags["nz"] = True
                        elif not isinstance(x.value, ast.Constant):
                            flags["nz"] = True
                out.append({"line": n.lineno, "swallow": not any(flags.values()), "why": flags})
    return out


def inline_evidence(tree, args, modfns):
    """严格按规格：And 聚合赋值 / += 累计 / global-checker 调用点 / 出口比较。
    （刻意不把普通「驱动名赋值」计为证据——规格文本未列。）"""
    drivers = set()
    for a in args:
        for x in ast.walk(a):
            if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load):
                drivers.add(x.id)
    checkers = set()
    for name, f in modfns.items():
        for st in f.body:
            if isinstance(st, ast.Global) and drivers & set(st.names):
                checkers.add(name)
    ev = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id in drivers \
                        and isinstance(n.value, ast.BoolOp) \
                        and isinstance(n.value.op, ast.And):
                    ev.add((n.lineno, "And聚合"))
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name) \
                and n.target.id in drivers:
            ev.add((n.lineno, "+=累计"))
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id in checkers:
            ev.add((n.lineno, "checker调用"))
    for ln, _k, a in exit_sites(tree):
        if isinstance(a, (ast.IfExp, ast.Compare)):
            ev.add((ln, "出口比较"))
    return sorted(ev), sorted(drivers)


def guard_and_summary(scope, drivers):
    G, P = set(), set()
    for f in scope:
        for n in ast.walk(f):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in REG_ATTRS and isinstance(n.func.value, ast.Name):
                G.add(n.func.value.id)
            elif isinstance(n, ast.If):
                hit = False
                for r in ast.walk(n):
                    if isinstance(r, ast.Return) and r.value is not None:
                        if isinstance(r.value, ast.Constant) \
                                and isinstance(r.value.value, int) and r.value.value != 0:
                            hit = True
                            break
                        if not isinstance(r.value, ast.Constant):
                            hit = True
                            break
                if hit:
                    for x in ast.walk(n.test):
                        if isinstance(x, ast.Name):
                            G.add(x.id)
            elif isinstance(n, ast.Call):
                g = n.func
                is_pr = (isinstance(g, ast.Name) and g.id == "print") or \
                        (isinstance(g, ast.Attribute) and g.attr == "print")
                is_wr = isinstance(g, ast.Attribute) and \
                    g.attr in ("write", "write_text", "write_bytes")
                if is_pr or is_wr:
                    for x in ast.walk(n):
                        if isinstance(x, ast.Name):
                            P.add(x.id)
            elif isinstance(n, ast.For):
                has = any(isinstance(x, ast.Call) and
                          ((isinstance(x.func, ast.Name) and x.func.id == "print") or
                           (isinstance(x.func, ast.Attribute) and
                            x.func.attr in ("print", "write", "write_text", "write_bytes")))
                          for x in ast.walk(n))
                if has:
                    for x in ast.walk(n.iter):
                        if isinstance(x, ast.Name):
                            P.add(x.id)
    return G | set(drivers), P


# ---------------------------------------------------------------- 主判定
def classify(rel, tree, src):
    R = []

    def ref(ln):
        return "%s:%d" % (rel, ln)

    modfns = mod_funcs(tree)
    sites = exit_sites(tree)
    args = [a for (_ln, _k, a) in sites if a is not None]
    has_exit = bool(sites)
    writes = true_writes(tree)
    npr = n_prints(tree)
    pairs, sneg = find_pairs(tree)
    va = verdict_asserts(tree, src)

    if has_exit:
        states, dyn, stlines = exit_states(sites, modfns)
    else:
        states, dyn, stlines = set(), False, []
    multi = len(states) >= 2 or dyn

    vfn_roots = []
    for (_ln, _k, a) in sites:
        if isinstance(a, ast.Call) and isinstance(a.func, ast.Name) and a.func.id in modfns:
            vfn_roots.append(modfns[a.func.id])
        elif isinstance(a, ast.Name) and a.id in modfns:
            vfn_roots.append(modfns[a.id])
    scope = scope_closure(modfns, vfn_roots) if vfn_roots else []
    fregs = reg_sites(scope) if scope else []
    gif = gate_ifs(scope) if scope else []

    ga2 = bool(pairs or sneg)
    ga1 = has_exit and multi
    ga3 = has_exit and len(fregs) >= 2

    if has_exit:
        if ga2 or ga1 or ga3:
            cls = "GATE"
        else:
            cls = "ARTIFACT" if writes else ("PROBE" if npr else "UNKNOWN")
            if cls == "UNKNOWN":
                R.append(("CLASS", rel, "有出口但无 GA1/GA2/GA3、无真写盘、无 print → 需人工"))
    else:
        if ga2 or len(va) >= 2:
            cls = "GATE"
        elif writes:
            cls = "ARTIFACT"
        elif npr:
            cls = "PROBE"
        else:
            cls = "UNKNOWN"
            n_def = sum(isinstance(nd, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                        for nd in tree.body)
            if n_def >= 1:
                R.append(("CLASS", rel, "疑似库模块/零可见产物脚本（顶层 def/class %d）→ 先人工" % n_def))
            else:
                R.append(("CLASS", rel, "无出口/无裁决对/无真写盘/无 print → 需人工"))

    e = {"E0": None, "E1": None, "E2": None, "E3": None, "E4": None}

    if cls == "GATE" and not has_exit:
        if pairs:
            p0 = pairs[0]
            R.append(("E0", ref(p0["line"]),
                      "stdout 互斥裁决对（%s / %s，%s）但零出口" % (p0["neg"], p0["pos"], p0["kind"])))
        elif sneg:
            s0 = sneg[0]
            R.append(("E0", ref(s0["line"]), "stdout 单侧负裁决（%s）但零出口" % s0["neg"]))
        else:
            for ln in va[:4]:
                R.append(("E3", ref(ln), "assert 承载裁决（异常通道顶替出口）"))
            e["E0"] = "E3_IMPLICIT"
        return {"rel": rel, "class": cls, "verdict": "NEEDS_FIX", "e": e,
                "reasons": R,
                "facts": {"n_exit": len(sites), "n_writes": len(writes),
                          "n_prints": npr, "n_pairs": len(pairs),
                          "n_single_neg": len(sneg), "n_verdict_asserts": len(va)}}

    if cls == "GATE":
        # E1
        if has_exit and not args:
            e["E1"] = "UNKNOWN"
            R.append(("E1", rel, "裸 raise SystemExit 无状态表达式 → 需人工"))
        elif multi:
            e["E1"] = "PASS"
            R.append(("E1", rel, "PASS：状态 %s%s" %
                      (sorted(states) if states else "{动态}", "∪动态" if dyn else "")))
        else:
            e["E1"] = "FAIL"
            where = ref(stlines[0][0]) if stlines else rel
            R.append(("E1", where, "FAIL：出口可达状态恰为 %s ⇒ 常量出口零信息" % sorted(states)))

        # E2
        if scope:
            total = sorted(set([l for l, _ in fregs] + gif))
            if len(total) >= 2:
                e["E2"] = "PASS"
                R.append(("E2", rel, "PASS：%d 处失败登记/早退门（%s%s）"
                          % (len(total), ", ".join(ref(l) for l in total[:8]),
                             " …" if len(total) > 8 else "")))
            elif len(total) == 1:
                e["E2"] = "FAIL"
                R.append(("E2", ref(total[0]), "FAIL：0 分支由单标量驱动"))
            else:
                e["E2"] = "UNKNOWN"
                R.append(("E2", rel, "裁决链内无失败登记/早退门 → 需人工"))
        else:
            iev, drivers = inline_evidence(tree, args, modfns)
            if len(iev) >= 2:
                e["E2"] = "PASS"
                R.append(("E2", rel, "PASS(w)：内联驱动 %s 证据 %d 处（%s）"
                          % (drivers, len(iev), ", ".join("%s:%s" % (ref(l), d) for l, d in iev[:6]))))
            elif len(iev) == 1:
                e["E2"] = "FAIL"
                R.append(("E2", ref(iev[0][0]), "FAIL：0 分支由单标量驱动（%s）" % (iev[0][1],)))
            else:
                e["E2"] = "UNKNOWN"
                R.append(("E2", rel, "内联驱动名无聚合证据 → 需人工"))

        # E3
        hfacts = handler_facts(scope if scope else [tree], modfns)
        sw = [h for h in hfacts if h["swallow"]]
        if sw:
            e["E3"] = "FAIL"
            for h in sw[:5]:
                R.append(("E3", ref(h["line"]), "FAIL：异常被吞（体惰性）"))
        else:
            e["E3"] = "PASS"
            R.append(("E3", rel, "PASS：%d 个 handler 均不吞" % len(hfacts) if hfacts
                      else "PASS：无 try/except"))

        # E4
        G, P = guard_and_summary(scope if scope else [tree],
                                 set() if scope else set(
                                     x.id for a in args for x in ast.walk(a)
                                     if isinstance(x, ast.Name) and isinstance(x.ctx, ast.Load)))
        inter = sorted(G & P)
        if inter:
            e["E4"] = "PASS"
            R.append(("E4", rel, "PASS：守卫名∩摘要名 = %s" % inter))
        else:
            e["E4"] = "FAIL"
            R.append(("E4", rel, "FAIL：守卫名 %s ∩ 摘要名 %s = ∅" % (sorted(G), sorted(P))))
    else:
        if has_exit and args:
            consts = [a.value for a in args
                      if isinstance(a, ast.Constant) and isinstance(a.value, int)]
            if consts and len(consts) == len(args):
                R.append(("EXIT", ref(sites[0][0]),
                          "常量出口 %s；本类产物=%s，登记应引用产物而非 EXIT"
                          % (sorted(set(consts)), "文件" if writes else "stdout")))
            else:
                R.append(("EXIT", ref(sites[0][0]), "非常量出口，仅崩溃信号"))

    if cls == "UNKNOWN":
        verdict = "NEEDS_FIX"
        R.append(("UNKNOWN", rel, "UNKNOWN_MANUAL：需人工逐件，非需改码"))
    elif cls == "GATE":
        verdict = "OK" if all(e.get(k) == "PASS" for k in ("E1", "E2", "E3", "E4")) else "NEEDS_FIX"
    else:
        if not has_exit:
            verdict = "OK"
            R.append(("CLASS", rel, "%s：出口不适用；登记应引用%s"
                      % (cls, "产物文件+指纹" if writes else "捕获 stdout/摘要")))
        else:
            consts = [a.value for a in args
                      if isinstance(a, ast.Constant) and isinstance(a.value, int)]
            verdict = "EXIT_ZERO_INFO" if consts and len(consts) == len(args) else "OK"

    return {"rel": rel, "class": cls, "verdict": verdict, "e": e, "reasons": R,
            "facts": {"n_exit": len(sites), "n_writes": len(writes), "n_prints": npr,
                      "n_pairs": len(pairs), "n_single_neg": len(sneg),
                      "n_verdict_asserts": len(va)}}


def analyze_file(abs_path, rel):
    raw = open(abs_path, "rb").read()
    src = None
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            src = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if src is None:
        src = raw.decode("utf-8", "replace")
    try:
        tree = ast.parse(src)
    except SyntaxError as ex:
        return {"rel": rel, "class": "UNKNOWN", "verdict": "NEEDS_FIX", "e": {},
                "reasons": [("PARSE", rel, "语法解析失败 → 需人工")], "facts": {}}
    return classify(rel, tree, src)
