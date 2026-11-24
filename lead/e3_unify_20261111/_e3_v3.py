# -*- coding: utf-8 -*-
"""_e3_v3.py — E3 第三版判定器（无吞判据）：统一两套既有实现的正确部分，修七条已知缺陷。

接口
    e3(path) -> ("PASS" | "FAIL" | "UNKNOWN", reasons: list[str])

被检脚本只读 + ast.parse，绝不 import / 执行；sys.dont_write_bytecode 在 import 时即置。

七条修复（对照 _ec_criterion_fixed2.py / _ei3_e3.py 两版的真实缺陷）：
  fix1/2 判据侧漏认 —— handler 体命中任一即「把失败传下去了」（强证据）：
         (a) raise；(b) 调 sys.exit/exit/quit/os._exit；
         (c) .append/.extend/.add/.update 且接收端为 Name/Subscript/Attribute；
         (d) Subscript/Attribute 赋值（受 fix7 修饰，见下）；
         (e) 赋值给出口/摘要表达式中的名字（名字集由模块级数据流收集，不是只看 handler 内）；
         (f) break/continue 且 handler 的 try 在循环体内；
         (g) 调模块内函数（ast.walk 全树收集，不用 getattr(fn,'name')）；
         (h) return 非零整常量。
  fix3   scope 抽取 —— 模块函数名一律 ast.walk(tree) 收全部 FunctionDef/AsyncFunctionDef
         （含方法/嵌套），与出口解析出的裁决函数集是否为空无关；彻底弃用
         `e3_scope = scope if v_fns else [tree]`（旧版 v_fns 为空时 user_fns 收空，
         (g) 全漏，_integ_probe_isolated.py 被误判吞没）。
  fix4   print 不算传播 —— print 仅当打印内容含速判词（PASS/FAIL/OK/ERROR/结论）才算
         证据，且此时记 weak=True；handler 只有 weak 证据 ⇒ 记「疑似吞没」而非「已传播」。
         不含速判词的 print 完全不算证据（neg2 的 print("x") 不得算传播）。
  fix5   carve-out 顺序 —— 先逐 handler 算 真传播/疑似/吞没；裸 pass 的豁免放在逐
         handler 分类末尾、聚合之前，只让本 handler 记「疑似」，不再提前 return 全局
         一票否决。聚合：有吞没 ⇒ FAIL；只有疑似 ⇒ UNKNOWN；全真传播 ⇒ PASS。
         保留 impl2 的数据流细化：裸 pass 且 try 体赋值过 wide 名集 ⇒ 失败确曾流经
         可观察状态 ⇒ 仍记「吞没」（neg1 即此形态 ⇒ FAIL）。
  fix6   名字集要宽 —— core（命中 ⇒ 强证据）= sys.exit/exit/quit 参数 +
         raise SystemExit 参数 + 带速判词 print 参数（含出口所调模块级裁决函数的
         Return 名，即 sys.exit(main()) 惯用法）+ finally 体读到的名 +
         merge_*/note_* 等登记前缀函数的赋值目标；
         wide（仅命中 ⇒ 弱证据）= core ∪ 全部模块级赋值目标（含 X=[]/X={} 容器）
         ∪ 模块尾部（顶层语句、不下钻 def/class 体）读到的名。
         宁可宽收；宽集命中绝不产生 PASS，只把 FAIL 抬到 UNKNOWN。
  fix7   Subscript 赋值不算容器写 —— d[k]=v 仅当 v 由异常对象派生（子树含异常绑定名：
         repr(e)/str(e)/f"{e}"/{'error': str(e)} 全覆盖）才算 (c) 容器写；
         r["syntax"]=False 这类标量常量标志 ⇒ 只记弱证据（疑似），绝不算「已传播」。
         fix7 对 Subscript/Attribute 目标优先于 (e)：该赋值只走 fix7 分支，
         不再因基名出现在出口/摘要名集而升为强证据。

静态局限（声明）：名字级 ≠ 值级；别名调用 / 类构造调用 / 被调函数内部的间接登记 /
分支可达性判不出。凡判不了 ⇒ UNKNOWN，不硬判 PASS。
"""
import sys

sys.dont_write_bytecode = True

import ast
import re
from pathlib import Path

__all__ = ["e3"]

# ---------------------------------------------------------------- 词表
_CONTAINER_MUTATORS = frozenset({"append", "extend", "add", "update"})
_EXIT_CALLS = frozenset({"sys.exit", "exit", "quit", "os._exit"})

# fix4 速判词：PASS/FAIL/OK/ERROR/结论。ASCII 词用字母环视边界（CJK 相邻不挡匹配）；
# 大小写不敏感 —— 漏记弱证据只会造成误 FAIL，多记只会把 FAIL 降级 UNKNOWN，后者更保守。
_VERDICT_RE = re.compile(
    r"(?<![A-Za-z])(?:PASS(?:ED|ING)?|FAIL(?:ED|S|URE)?|OK|ERRORS?)(?![A-Za-z])|结论",
    re.IGNORECASE,
)

_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
_FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
_LOOP_NODES = (ast.For, ast.AsyncFor, ast.While)
_TRY_NODES = (ast.Try, getattr(ast, "TryStar", ast.Try))
_WITH_NODES = (ast.With, getattr(ast, "AsyncWith", ast.With))
_ASSIGN_NODES = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)

# fix6「merge_*/note_* 这类函数」的前缀解释（登记/汇集体裁词）
_REGISTRAR_PREFIXES = ("merge_", "note_", "record_", "log_", "emit_", "register_")


# ---------------------------------------------------------------- 小工具
def _dotted(node):
    """点分调用名：sys.exit / os._exit / check …"""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return "%s.%s" % (base, node.attr) if base else node.attr
    return ""


def _call_args(call):
    return list(call.args) + [kw.value for kw in call.keywords]


def _is_print_call(node):
    return (isinstance(node, ast.Call)
            and ((isinstance(node.func, ast.Name) and node.func.id == "print")
                 or (isinstance(node.func, ast.Attribute)
                     and node.func.attr == "print")))


def _print_verdict_words(call):
    """print 打印内容里字面出现的速判词（含 f-string 片段）。"""
    found = set()
    for arg in _call_args(call):
        for sub in ast.walk(arg):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                for m in _VERDICT_RE.finditer(sub.value):
                    found.add(m.group(0).upper())
    return found


def _body_nodes(stmts):
    """stmts 执行可达的节点；不下钻嵌套 def/class/lambda 体（它们不在 handler
    执行路径上，不得算作 handler 行为）。"""
    out = []
    stack = list(reversed(list(stmts)))
    while stack:
        node = stack.pop()
        out.append(node)
        if isinstance(node, _SCOPE_NODES):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))
    return out


def _walk_noscope(stmts):
    """生成器版 _body_nodes：模块级扫描用（跳过 def/class/lambda 体）。"""
    stack = list(reversed(list(stmts)))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, _SCOPE_NODES):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))


def _target_names(target):
    """赋值目标触到的名字（Attribute 收属性名 + 基名链；Subscript 收基名链）。"""
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Attribute):
        return {target.attr} | _target_names(target.value)
    if isinstance(target, ast.Subscript):
        return _target_names(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        names = set()
        for el in target.elts:
            names |= _target_names(el)
        return names
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    return set()


def _assigned_names(node):
    """一条语句赋值到的名字（Assign/AnnAssign/AugAssign/NamedExpr/for/with 目标）。"""
    if isinstance(node, ast.Assign):
        names = set()
        for t in node.targets:
            names |= _target_names(t)
        return names
    if isinstance(node, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        return _target_names(node.target)
    if isinstance(node, (ast.For, ast.AsyncFor)):  # While 无 target，不算赋值
        return _target_names(node.target)
    if isinstance(node, _WITH_NODES):
        names = set()
        for item in node.items:
            if item.optional_vars is not None:
                names |= _target_names(item.optional_vars)
        return names
    return set()


def _expr_names(expr):
    """表达式里出现的 Name id 与 Attribute attr。"""
    names = set()
    for sub in ast.walk(expr):
        if isinstance(sub, ast.Name):
            names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr)
    return names


def _exception_derived(value, exc_names):
    """fix7：值表达式子树中出现异常绑定名即视为异常派生
    （repr(e)/str(e)/f"{e}"/{'error': str(e)}/type(e).__name__ 等形态全覆盖）。"""
    if not exc_names or value is None:
        return False
    for sub in ast.walk(value):
        if isinstance(sub, ast.Name) and sub.id in exc_names:
            return True
    return False


# ---------------------------------------------------------------- fix3
def _module_function_names(tree):
    """fix3：ast.walk 全树收全部 FunctionDef/AsyncFunctionDef 名（含方法/嵌套），
    与出口解析出的裁决函数集是否为空无关；不再用 getattr(fn,'name') 依 scope 取名。"""
    return {n.name for n in ast.walk(tree) if isinstance(n, _FUNC_NODES)}


# ---------------------------------------------------------------- fix6
def _name_sets(tree):
    """fix6：返回 (core, wide)。
    core 命中 ⇒ 强证据（真传播）；仅 wide 命中 ⇒ 弱证据（疑似，绝不据此 PASS）。"""
    core = set()
    fn_names = _module_function_names(tree)

    # (i) 出口参数 / raise SystemExit 参数 / 带速判词 print 参数；
    #     出口参数里引用的模块级裁决函数，其全部 Return 值名也入 core
    #     （sys.exit(main()) 惯用法：main 的 return 就是出口状态）。
    exit_fn_names = set()
    for nd in ast.walk(tree):
        if isinstance(nd, ast.Call) and _dotted(nd.func) in _EXIT_CALLS:
            for a in _call_args(nd):
                core |= _expr_names(a)
                for sub in ast.walk(a):
                    if isinstance(sub, ast.Name) and sub.id in fn_names:
                        exit_fn_names.add(sub.id)
        elif (isinstance(nd, ast.Raise) and isinstance(nd.exc, ast.Call)
              and _dotted(nd.exc.func) == "SystemExit"):
            for a in _call_args(nd.exc):
                core |= _expr_names(a)
        elif _is_print_call(nd) and _print_verdict_words(nd):
            for a in _call_args(nd):
                core |= _expr_names(a)
    if exit_fn_names:
        for nd in ast.walk(tree):
            if isinstance(nd, _FUNC_NODES) and nd.name in exit_fn_names:
                for sub in ast.walk(nd):
                    if isinstance(sub, ast.Return) and sub.value is not None:
                        core |= _expr_names(sub.value)

    # (ii) finally 体里被读的名字（fix6：出口/摘要前的最后观察点）
    for nd in ast.walk(tree):
        if isinstance(nd, _TRY_NODES) and nd.finalbody:
            for st in nd.finalbody:
                for sub in ast.walk(st):
                    if isinstance(sub, ast.Name):
                        core.add(sub.id)

    # (iii) 模块尾部（顶层语句、不下钻 def/class 体）被读的名字（fix6）—— 只入 wide
    tail_reads = set()
    for st in tree.body:
        for sub in _walk_noscope([st]):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                tail_reads.add(sub.id)

    # (iv) merge_*/note_* 这类登记函数体内的赋值目标（fix6）
    for nd in ast.walk(tree):
        if isinstance(nd, _FUNC_NODES) and nd.name.startswith(_REGISTRAR_PREFIXES):
            for sub in ast.walk(nd):
                if isinstance(sub, _ASSIGN_NODES):
                    core |= _assigned_names(sub)

    # (v) wide = core ∪ 全部模块级赋值目标（含 X=[]/X={} 容器；fix6 的退一步口径）
    #     ∪ 尾部读
    wide = set(core)
    wide |= tail_reads
    for st in tree.body:
        for sub in _walk_noscope([st]):
            if (isinstance(sub, _ASSIGN_NODES) or isinstance(sub, _LOOP_NODES)
                    or isinstance(sub, _WITH_NODES)):
                wide |= _assigned_names(sub)
    return core, wide


def _handler_context(tree):
    """id(ExceptHandler) -> (in_loop, try_body)。
    in_loop：所属 try 经 for/while 的 body 链可达（循环上下文在嵌套 def/class/lambda
    处复位），供 (f) 判 break/continue 能否真绑定到循环。"""
    context = {}
    stack = [(tree, False)]
    while stack:
        node, in_loop = stack.pop()
        if isinstance(node, _TRY_NODES):
            for h in node.handlers:
                context[id(h)] = (in_loop, list(node.body))
        child_loop = False if isinstance(node, _SCOPE_NODES) else in_loop
        for child in ast.iter_child_nodes(node):
            if isinstance(node, _LOOP_NODES) and any(child is s for s in node.body):
                stack.append((child, True))
            elif isinstance(node, _LOOP_NODES):
                stack.append((child, in_loop))
            else:
                stack.append((child, child_loop))
    return context


def _const_int_value(v):
    """return 值为整常量时返回其值（处理 -1/+1 的 UnaryOp 形态），否则 None。
    bool 不算（True/False 是哨兵不是退出码）。"""
    sign = 1
    if isinstance(v, ast.UnaryOp) and isinstance(v.op, (ast.USub, ast.UAdd)):
        sign = -1 if isinstance(v.op, ast.USub) else 1
        v = v.operand
    if isinstance(v, ast.Constant) and isinstance(v.value, int) \
            and not isinstance(v.value, bool):
        return sign * v.value
    return None


def _is_pass_only(handler):
    """handler 体只有 pass（注释不留 AST 节点）。"""
    return bool(handler.body) and all(isinstance(s, ast.Pass) for s in handler.body)


def _try_body_assigns(try_body, names):
    """try 体（不下钻嵌套作用域）是否赋值过 names 中的名字。"""
    for node in _body_nodes(try_body):
        if (isinstance(node, _ASSIGN_NODES) or isinstance(node, _LOOP_NODES)
                or isinstance(node, _WITH_NODES)):
            if _assigned_names(node) & names:
                return True
    return False


# ---------------------------------------------------------------- fix1/2 + fix4 + fix7
def _handler_evidence(handler, module_fns, s_core, s_wide, in_loop):
    """逐条判据。返回 (strong, weak, notes)：strong=真传播证据，weak=仅疑似证据。"""
    nodes = _body_nodes(handler.body)
    exc_names = {handler.name} if handler.name else set()
    strong, weak, notes = [], [], []
    seen = set()

    def add(bucket, tag):
        if tag not in seen:
            seen.add(tag)
            bucket.append(tag)

    # (a) raise（裸 raise 或带异常都算）
    if any(isinstance(n, ast.Raise) for n in nodes):
        add(strong, "(a) raise 重抛")

    # (b) 出口调用 sys.exit / exit / quit / os._exit
    for n in nodes:
        if isinstance(n, ast.Call) and _dotted(n.func) in _EXIT_CALLS:
            add(strong, "(b) 出口调用 %s" % (_dotted(n.func) or "?"))
            break

    # (c) 容器 mutator：接收端可为 Name / Subscript / Attribute
    for n in nodes:
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in _CONTAINER_MUTATORS
                and isinstance(n.func.value, (ast.Name, ast.Subscript, ast.Attribute))):
            add(strong, "(c) 容器登记 %s.%s(..)" % (_dotted(n.func.value) or "?", n.func.attr))
            break

    # (c/fix7) + (d) + (e)：赋值形态一次扫描。
    # Subscript/Attribute 目标只走本分支（fix7 优先于 (e)，防止
    # r["syntax"]=False 因基名在摘要名集里而被升为强证据）。
    for n in nodes:
        if not isinstance(n, _ASSIGN_NODES):
            continue
        if isinstance(n, ast.NamedExpr):
            targets, value = [n.target], n.value
        else:
            targets = list(n.targets) if isinstance(n, ast.Assign) else [n.target]
            value = n.value  # AnnAssign 可能无值
        names = set()
        for t in targets:
            names |= _target_names(t)
        sub_attr = any(isinstance(t, (ast.Subscript, ast.Attribute)) for t in targets)
        if sub_attr:
            if value is not None and _exception_derived(value, exc_names):
                add(strong, "(c/fix7) 异常派生值写入 %s" % ",".join(sorted(names)))
            elif value is not None and isinstance(value, ast.Constant):
                add(weak, "(d/fix7) 标量常量标志写入 %s（不算传播，仅疑似）"
                    % ",".join(sorted(names)))
            elif value is not None:
                add(strong, "(d) Subscript/Attribute 赋值(动态值) %s"
                    % ",".join(sorted(names)))
        else:
            core_hit = sorted(names & s_core)
            if core_hit:
                add(strong, "(e) 赋值出口/摘要名 %s" % ",".join(core_hit))
            else:
                wide_hit = sorted(names & s_wide)
                if wide_hit:
                    add(weak, "(e/fix6) 仅命中宽名集 %s（疑似）" % ",".join(wide_hit))

    # (f) break/continue 且 handler 的 try 在循环体内
    has_jump = any(isinstance(n, (ast.Break, ast.Continue)) for n in nodes)
    if has_jump and in_loop:
        add(strong, "(f) break/continue 且 handler 在循环体内")
    elif has_jump:
        notes.append("(f~) 有 break/continue 但 handler 不在循环体内，不计")

    # (g) 调模块内函数（fix3：全树 ast.walk 收集，scope 无关）
    for n in nodes:
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id in module_fns:
            add(strong, "(g) 调模块级函数 %s()" % n.func.id)

    # (h) return 非零整常量（-1 走 UnaryOp 形态；bool/None/0/字符串常量不算；
    #     动态值只记疑似）
    for n in nodes:
        if isinstance(n, ast.Return):
            v = n.value
            if v is None:
                continue
            ci = _const_int_value(v)
            if ci is not None:
                if ci != 0:
                    add(strong, "(h) return 非零常量 %d" % ci)
            elif not isinstance(v, ast.Constant):
                add(weak, "(h~) return 动态值（疑似）")

    # fix4：print 仅在含速判词时算证据，且只记 weak；无速判词的 print 完全不算
    for n in nodes:
        if _is_print_call(n):
            words = _print_verdict_words(n)
            if words:
                add(weak, "(fix4) print 含速判词 %s（仅 weak）" % ",".join(sorted(words)))
            else:
                notes.append("(fix4) print 无速判词，不计证据")

    return strong, weak, notes


def _short(seq, n=12):
    seq = list(seq)
    if len(seq) <= n:
        return str(seq)
    return "%s …+%d 项" % (seq[:n], len(seq) - n)


# ---------------------------------------------------------------- 主入口
def e3(path):
    """E3 判定入口：verdict ∈ {PASS, FAIL, UNKNOWN}。"""
    reasons = []
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        return "UNKNOWN", ["read-fail %s: %s: %s" % (path, type(exc).__name__, exc)]
    text = None
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        text = raw.decode("utf-8", "replace")
        reasons.append("decode-fallback: 非 utf-8/gbk，按 replace 解码（可能影响判读）")
    try:
        tree = ast.parse(text, filename=str(path))
    except (SyntaxError, ValueError) as exc:
        return "UNKNOWN", reasons + ["parse-fail %s: %s" % (path, exc)]

    handlers = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]
    if not handlers:
        return "PASS", ["step1: 0 except handler —— 无可吞没的异常通道 ⇒ PASS"]

    module_fns = _module_function_names(tree)          # fix3
    s_core, s_wide = _name_sets(tree)                  # fix6
    context = _handler_context(tree)
    reasons.append("step1: %d except handler；模块函数 %d 个（fix3 全树收集）；"
                   "core=%s；wide补=%s（fix6）"
                   % (len(handlers), len(module_fns),
                      _short(sorted(s_core)), _short(sorted(s_wide - s_core))))

    # fix5：先逐 handler 分类（真传播/疑似/吞没），裸 pass 豁免在分类末尾生效，
    # 最后才聚合 —— 不再有「一个裸 pass 提前 return UNKNOWN」的全局一票否决。
    rows = []
    for h in handlers:
        in_loop, try_body = context.get(id(h), (False, []))
        strong, weak, notes = _handler_evidence(h, module_fns, s_core, s_wide, in_loop)
        if strong:
            cls = "真传播"
        elif weak:
            cls = "疑似"
        elif _is_pass_only(h):
            if _try_body_assigns(try_body, s_wide):
                cls = "吞没"
                notes.append("裸 pass 但 try 体赋值过 wide 可见名 ⇒ 失败曾流经可观察状态")
            else:
                cls = "疑似"
                notes.append("裸 pass 且 try 体不触及可见名 ⇒ 纯容错，判不了")
        else:
            cls = "吞没"
        rows.append((h, cls, strong, weak, notes))
        detail = "; ".join(strong + weak + notes) if (strong or weak or notes) else "无证据"
        reasons.append("line %d: %s ｜ %s" % (h.lineno, cls, detail))

    n_swallow = sum(1 for _h, c, _s, _w, _n in rows if c == "吞没")
    n_suspect = sum(1 for _h, c, _s, _w, _n in rows if c == "疑似")
    if n_swallow:
        reasons.append("汇总(fix5): 吞没 %d / 疑似 %d / 真传播 %d ⇒ FAIL"
                       % (n_swallow, n_suspect, len(rows) - n_swallow - n_suspect))
        return "FAIL", reasons
    if n_suspect:
        reasons.append("汇总(fix5): 无吞没，疑似 %d / 真传播 %d ⇒ UNKNOWN（判不了不硬判）"
                       % (n_suspect, len(rows) - n_suspect))
        return "UNKNOWN", reasons
    reasons.append("汇总(fix5): %d 个 handler 全部真传播 ⇒ PASS" % len(rows))
    return "PASS", reasons


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    for _p in sys.argv[1:]:
        _v, _rs = e3(_p)
        print("%s\t%s" % (_v, _p))
        for _r in _rs:
            print("    " + _r)
