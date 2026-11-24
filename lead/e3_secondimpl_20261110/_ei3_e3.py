"""E3: an independent, AST-only judge for the "swallowed exception channel" question.

Written strictly from the written specification handed to this implementation;
the reference implementation was deliberately not consulted.

Question E3 answers
-------------------
Can a failure of this script vanish down a swallowed ``except`` channel, or can
that channel stand in for the script's exit?

Interface
---------
    e3_verdict(path) -> ("PASS" | "FAIL" | "UNKNOWN", reasons: list[str])

The checked script is read as bytes and handed to ``ast.parse`` — it is never
imported, compiled to a .pyc, or executed.  ``sys.dont_write_bytecode`` is set
at import time.

Definitions used for the two deliberately delicate criteria (d) / (e)
----------------------------------------------------------------------
* "exit expression"  = argument expressions of sys.exit / exit / quit /
  os._exit calls, plus the value expression of every ``return`` (a function's
  exit expression).
* "summary print"    = a call to print whose argument expressions contain a
  string constant (plain or f-string fragment / format spec) carrying a
  success/failure verdict word (PASS/FAIL/OK/ERROR/REFUTED/CONFIRMED/...).
* "exit/summary variable" = every Name id and Attribute attr appearing inside
  those exit expressions / summary prints.  The same set is used by (d) and by
  the bare-pass UNKNOWN carve-out.
* (e) "handler is inside a loop body" = the enclosing Try/TryStar statement is
  reached through the ``body`` of a For/AsyncFor/While (not through its orelse),
  with loop context resetting at nested function / lambda / class scopes, so a
  break/continue in the handler really can bind to an enclosing loop.
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True

import ast
import re
from pathlib import Path


# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------
_CONTAINER_MUTATORS = frozenset({"append", "extend", "add", "update"})
_EXIT_CALLS = frozenset({"sys.exit", "exit", "quit", "os._exit"})

# "PASS/FAIL/OK/ERROR 之类": word-boundary matched, case-insensitive.  Kept
# to the verdict/summary family (status words that say whether a check passed);
# plain descriptive words such as "missing"/"skipped" are deliberately NOT
# included, or a handler that merely logs a condition would falsely pass (f).
_VERDICT_RE = re.compile(
    r"\b(?:"
    r"PASS(?:ED)?|FAIL(?:ED|URE|S)?|OK|ERRORS?|REFUTED|CONFIRMED|"
    r"UNVERIFIABLE|UNKNOWN|VERDICTS?|RESULTS?|SUMMAR(?:Y|IES)|SUCCESS|"
    r"REJECT(?:ED)?|ACCEPT(?:ED)?|ABORT(?:ED)?|INVALID|"
    r"WARN(?:ING|INGS)?|DENY|DENIED|MISMATCH|VIOLATION"
    r")\b",
    re.IGNORECASE,
)

_SCOPE_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)
_TRY_NODES = (ast.Try, getattr(ast, "TryStar", ast.Try))  # except* on 3.11+
_LOOP_NODES = (ast.For, ast.AsyncFor, ast.While)
_ASSIGN_NODES = (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)
_FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


# --------------------------------------------------------------------------
# Small AST helpers
# --------------------------------------------------------------------------
def _dotted(node):
    """Return a dotted callee spelling, e.g. sys.exit / os._exit / record."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _call_args(call):
    return list(call.args) + [kw.value for kw in call.keywords]


def _is_print_call(node):
    return (
        isinstance(node, ast.Call)
        and (
            (isinstance(node.func, ast.Name) and node.func.id == "print")
            or (isinstance(node.func, ast.Attribute) and node.func.attr == "print")
        )
    )


def _print_verdict_words(call):
    """Verdict words literally present in a print's printed content."""
    found = set()
    for arg in _call_args(call):
        for sub in ast.walk(arg):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                for match in _VERDICT_RE.finditer(sub.value):
                    found.add(match.group(0).upper())
    return found


def _body_nodes(stmts):
    """Nodes reachable while these statements execute, minus nested scopes.

    A nested def/class/lambda *body* does not run when its enclosing handler
    runs, so its statements must not be mistaken for handler behaviour.
    """
    out = []
    stack = list(reversed(list(stmts)))
    while stack:
        node = stack.pop()
        out.append(node)
        if isinstance(node, _SCOPE_NODES):
            continue
        stack.extend(reversed(list(ast.iter_child_nodes(node))))
    return out


def _target_names(target):
    """Names touched by an assignment target (incl. attribute/subscript bases)."""
    if isinstance(target, ast.Name):
        return {target.id}
    if isinstance(target, ast.Attribute):
        return {target.attr} | _target_names(target.value)
    if isinstance(target, ast.Subscript):
        return _target_names(target.value)
    if isinstance(target, (ast.Tuple, ast.List)):
        names = set()
        for element in target.elts:
            names |= _target_names(element)
        return names
    if isinstance(target, ast.Starred):
        return _target_names(target.value)
    return set()


def _assigned_names(stmt):
    """Variable names assigned by one statement (Assign/AnnAssign/AugAssign/
    NamedExpr, plus for-targets and with-as bindings)."""
    if isinstance(stmt, ast.Assign):
        names = set()
        for target in stmt.targets:
            names |= _target_names(target)
        return names
    if isinstance(stmt, (ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        return _target_names(stmt.target)
    if isinstance(stmt, _LOOP_NODES):
        return _target_names(stmt.target)
    if isinstance(stmt, (ast.With, getattr(ast, "AsyncWith", ast.With))):
        names = set()
        for item in stmt.items:
            if item.optional_vars is not None:
                names |= _target_names(item.optional_vars)
        return names
    return set()


def _expr_names(expr):
    """Name ids and attribute attrs appearing inside an expression."""
    names = set()
    for sub in ast.walk(expr):
        if isinstance(sub, ast.Name):
            names.add(sub.id)
        elif isinstance(sub, ast.Attribute):
            names.add(sub.attr)
    return names


# --------------------------------------------------------------------------
# Module-wide context: exit/summary variables, loop contexts, guarded try body
# --------------------------------------------------------------------------
def _exit_summary_names(tree):
    """(d)'s comparison set: names in exit expressions or summary prints.

    "Exit expression" is read narrowly, as the script's real exit site:
      * arguments of sys.exit / exit / quit / os._exit calls, and
      * the ``return`` values of the module-level function named by that exit
        call (the ``sys.exit(main())`` idiom -- main's returns ARE the exit
        status), and
      * arguments of ``raise SystemExit(...)``.
    Every helper's incidental ``return`` is deliberately NOT included: a
    handler assigning a same-named local must not be able to borrow an
    unrelated function's return and thereby fake a PASS.
    "Summary print" = a print carrying a verdict word (PASS/FAIL/RESULT/...).
    """
    module_funcs = {n.name: n for n in tree.body if isinstance(n, _FUNC_NODES)}
    names = set()
    exit_call_funcs = set()

    def _collect_exit_args(args):
        for arg in args:
            names.update(_expr_names(arg))
            for sub in ast.walk(arg):
                if isinstance(sub, ast.Name) and sub.id in module_funcs:
                    exit_call_funcs.add(sub.id)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _dotted(node.func) in _EXIT_CALLS:
            _collect_exit_args(_call_args(node))
        if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call) \
                and _dotted(node.exc.func) == "SystemExit":
            _collect_exit_args(_call_args(node.exc))
        if _is_print_call(node) and _print_verdict_words(node):
            for arg in _call_args(node):
                names |= _expr_names(arg)

    for fname in exit_call_funcs:
        for sub in ast.walk(module_funcs[fname]):
            if isinstance(sub, ast.Return) and sub.value is not None:
                names |= _expr_names(sub.value)
    return names


def _handler_context(tree):
    """id(ExceptHandler) -> (inside_loop_body, guarded_try_body).

    (e) is decided here: a handler counts as "in a loop body" only when the
    stack of ancestors reaches its Try through For/AsyncFor/While.body.  Loop
    context is reset when descending into a nested function/lambda/class so a
    break/continue cannot be attributed to an outer loop it cannot bind to.
    Loop ``orelse`` clauses are traversed with the *outer* loop context.
    """
    context = {}
    stack = [(tree, False)]
    while stack:
        node, in_loop = stack.pop()
        if isinstance(node, _TRY_NODES):
            for handler in node.handlers:
                context[id(handler)] = (in_loop, node.body)
        if isinstance(node, _SCOPE_NODES):
            child_loop = False
        else:
            child_loop = in_loop
        for child in ast.iter_child_nodes(node):
            if isinstance(node, _LOOP_NODES) and any(child is s for s in node.body):
                stack.append((child, True))
            elif isinstance(node, _LOOP_NODES):
                stack.append((child, in_loop))
            else:
                stack.append((child, child_loop))
    return context


def _module_function_names(tree):
    """All function/method names defined in this module (for (g))."""
    return {n.name for n in ast.walk(tree) if isinstance(n, _FUNC_NODES)}


def _try_body_assigns(try_body, exit_summary_names):
    """(d)'s UNKNOWN companion: does the guarded try body assign an
    exit/summary variable at all?"""
    for node in _body_nodes(try_body):
        if isinstance(node, _ASSIGN_NODES) or isinstance(node, _LOOP_NODES) \
                or isinstance(node, (ast.With, getattr(ast, "AsyncWith", ast.With))):
            if _assigned_names(node) & exit_summary_names:
                return True
    return False


def _is_pass_only(handler):
    """Handler body is nothing but ``pass`` (comments leave no AST node)."""
    return bool(handler.body) and all(isinstance(s, ast.Pass) for s in handler.body)


# --------------------------------------------------------------------------
# Step 2: does one handler pass the failure down?
# --------------------------------------------------------------------------
def _handler_passes(handler, module_funcs, exit_summary_names, in_loop, try_body):
    nodes = _body_nodes(handler.body)
    matched = []

    # (a) raise -- any raise, bare or with an exception
    if any(isinstance(n, ast.Raise) for n in nodes):
        matched.append("(a) raise")

    # (b) sys.exit / exit / quit / os._exit
    if any(isinstance(n, ast.Call) and _dotted(n.func) in _EXIT_CALLS
           for n in nodes):
        matched.append("(b) exit call")

    # ---- (c) writes the failure into a container -------------------------
    # Two syntactic forms named by the spec:
    #   * X.append(...) / X.extend(...) / X.add(...) / X.update(...), whose
    #     receiver may itself be a subscript -> X[...].append(...)
    #   * d[k] = ... , i.e. an Assign/AugAssign/AnnAssign with a Subscript
    #     target (ev[-1] += ... is the same container write in AugAssign form)
    c_matched = False
    for n in nodes:
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in _CONTAINER_MUTATORS:
            c_matched = True
            break
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            if any(isinstance(t, ast.Subscript) for t in targets):
                c_matched = True
                break
    if c_matched:
        matched.append("(c) container write")
    # ----------------------------------------------------------------------

    # ---- (d) assigns a variable that appears in an exit expression or a
    #          summary print.  Both sides use the SAME name set computed from
    #          the whole module, so a handler cannot pass just because it
    #          assigns a local that is never observed at the exit.
    d_names = set()
    for n in nodes:
        if isinstance(n, _ASSIGN_NODES) or isinstance(n, _LOOP_NODES) \
                or isinstance(n, (ast.With, getattr(ast, "AsyncWith", ast.With))):
            d_names |= _assigned_names(n)
    d_hit = sorted(d_names & exit_summary_names)
    if d_hit:
        matched.append(f"(d) assigns exit/summary var(s): {', '.join(d_hit)}")
    # ----------------------------------------------------------------------

    # ---- (e) break / continue AND the handler is inside a loop body.
    #          The loop-body flag comes from _handler_context(), which walks
    #          ancestor statements and resets at nested scopes; it is NOT a
    #          plain "is there any loop anywhere above me" guess.
    has_jump = any(isinstance(n, (ast.Break, ast.Continue)) for n in nodes)
    if has_jump and in_loop:
        matched.append("(e) break/continue in loop-body handler")
    elif has_jump and not in_loop:
        # Record the near miss: the jump exists but cannot bind to a loop.
        matched.append("(!e) break/continue but handler not in loop body")
    # ----------------------------------------------------------------------

    # (f) print carrying a success/failure verdict word
    verdict_words = set()
    for n in nodes:
        if _is_print_call(n):
            verdict_words |= _print_verdict_words(n)
    if verdict_words:
        matched.append(f"(f) verdict print: {', '.join(sorted(verdict_words))}")

    # (g) calls a function defined in this module
    g_hits = set()
    for n in nodes:
        if not isinstance(n, ast.Call):
            continue
        if isinstance(n.func, ast.Name) and n.func.id in module_funcs:
            g_hits.add(n.func.id)
        elif isinstance(n.func, ast.Attribute) and n.func.attr in module_funcs:
            g_hits.add(n.func.attr)
    if g_hits:
        matched.append(f"(g) module-defined call(s): {', '.join(sorted(g_hits))}")

    # A "(!e)" near miss must NOT be mistaken for a passing criterion.
    effective = [m for m in matched if not m.startswith("(!")]
    return bool(effective), matched, bool(has_jump and not in_loop), d_hit


# --------------------------------------------------------------------------
# Steps 1 + 3: collect handlers, aggregate
# --------------------------------------------------------------------------
def e3_verdict(path):
    """Judge one script.  Returns ('PASS'|'FAIL'|'UNKNOWN', reasons)."""
    reasons = []
    try:
        source = Path(path).read_bytes()
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, ValueError, UnicodeError) as exc:
        return "UNKNOWN", [f"cannot parse {path}: {type(exc).__name__}: {exc}"]

    handlers = [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]
    if not handlers:
        return "PASS", ["step1: 0 except handler(s); no swallowed exception "
                        "channel exists -> E3 PASS"]

    module_funcs = _module_function_names(tree)
    exit_summary_names = _exit_summary_names(tree)
    context = _handler_context(tree)

    reasons.append(
        f"step1: {len(handlers)} except handler(s); "
        f"exit/summary vars = {sorted(exit_summary_names)}; "
        f"module-defined funcs = {len(module_funcs)}"
    )

    swallowing = []
    for handler in handlers:
        in_loop, try_body = context.get(id(handler), (False, []))
        passed, matched, near_miss_e, d_hit = _handler_passes(
            handler, module_funcs, exit_summary_names, in_loop, try_body
        )
        tag = "passes down" if passed else "SWALLOWS"
        detail = "; ".join(matched) if matched else "no criterion (a)-(g) matched"
        reasons.append(f"line {handler.lineno}: {tag} [{detail}]")
        if not passed:
            swallowing.append((handler, try_body, near_miss_e, d_hit))

    if not swallowing:
        reasons.append("step3: every handler passes the failure down -> E3 PASS")
        return "PASS", reasons

    # Bullet 3 is checked before the general FAIL bullet, literally as ordered
    # in the spec: a bare-pass handler whose guarded try body never assigns an
    # exit/summary variable is pure parse tolerance and cannot be judged.
    bare = []
    for handler, try_body, _near_miss_e, _d_hit in swallowing:
        if _is_pass_only(handler) and not _try_body_assigns(try_body,
                                                           exit_summary_names):
            bare.append(handler)
    if bare:
        reasons.append(
            "step3: bare-pass handler(s) at line(s) "
            + ", ".join(str(h.lineno) for h in bare)
            + " with no exit/summary-var assignment in the guarded try body "
              "-> pure parse tolerance, E3 UNKNOWN"
        )
        return "UNKNOWN", reasons

    reasons.append(
        "step3: swallowing handler(s) at line(s) "
        + ", ".join(str(h.lineno) for h, _tb, _nm, _dh in swallowing)
        + " -> E3 FAIL"
    )
    return "FAIL", reasons


if __name__ == "__main__":
    for _p in sys.argv[1:]:
        _v, _r = e3_verdict(_p)
        print(f"{_v}\t{_p}")
        for _line in _r:
            print(f"    {_line}")
