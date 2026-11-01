#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-07 判定件：28 条静态写盘 sink 的「输入来源」普查。

为什么必须做这一件：D-07 的选项 A 是「他线清零」，但它成立的前提是
**这些告警是可修的**。而「路径穿越」类告警的可修性取决于一件事：
写入路径是否跨越了**信任边界**。

若写的是 `--out <path>` 这种命令行参数，那么调用者=开发者本人，
他本来就有权往任意位置写 ⇒ 不构成越权，属于**工具正常功能**，
「修复」它等于拒绝实现该功能。
若写的是**环境变量 / 外部文件内容 / 网络数据**，才存在真实边界。

本件不靠肉眼：对每条 sink 做 AST 解析，回溯 `open()` 第一个实参到
它的来源（argparse 属性 / os.environ / 字面量 / 函数参数 / 表达式），
并标注该来源是否有 `..` 或 `realpath` 归一化保护。

复跑：python lead/qc161_u0400_trip/_classify_sinks_d07.py
退出码：0 = 普查完成；2 = 有落点无法定位。
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SCAN = Path(r"C:\Users\Administrator\.mimosa\security-scans"
            r"\project-58d54c8400d61bac27a417b2"
            r"\scan-2026-10-23T20-36-58.833Z-8f7e7ad6abd0\findings.json")


def classify_source(node: ast.AST, func_defaults: set[str]) -> tuple[str, str]:
    """回溯表达式，返回 (类别, 证据)。类别是「信任边界」语义，不是语法类别。"""
    # 1) argparse 结果：args.Xxx / a.Xxx / opts.Xxx
    if isinstance(node, ast.Attribute):
        base = node.value
        if isinstance(base, ast.Name):
            return "CLI参数", "%s.%s" % (base.id, node.attr)
        return "属性链", ast.unparse(node)
    # 2) 环境变量
    if isinstance(node, ast.Subscript):
        src = ast.unparse(node)
        if "environ" in src:
            return "环境变量", src
        return "下标", src
    if isinstance(node, ast.Call):
        src = ast.unparse(node)
        if "environ" in src:
            return "环境变量", src
        if node.func.__class__ is ast.Name and node.func.id in ("Path", "str"):
            if node.args:
                return classify_source(node.args[0], func_defaults)
        if node.func.__class__ is ast.Attribute and node.func.attr in (
                "join", "resolve", "absolute", "realpath", "abspath"):
            inner = "?"
            if node.args:
                c, e = classify_source(node.args[0], func_defaults)
                inner = "%s(%s)" % (e, node.func.attr)
                # ★ 归一化算子出现 ⇒ 该链已有防穿越处理
                if node.func.attr in ("resolve", "realpath", "abspath"):
                    return "已归一化", inner
                return c, inner
            return "派生", src
        return "调用", src[:60]
    # 3) 字面量
    if isinstance(node, ast.Constant):
        return "字面量", repr(node.value)[:60]
    # 4) 形参（函数体内部，来源需看调用者）
    if isinstance(node, ast.Name):
        if node.id in func_defaults:
            return "形参", node.id
        return "局部名", node.id
    # 5) f-string
    if isinstance(node, ast.JoinedStr):
        return "f-string", ast.unparse(node)[:60]
    return "其它", ast.unparse(node)[:60]


def enclosing_func(tree: ast.AST, lineno: int) -> ast.AST | None:
    best = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if n.lineno <= lineno <= (n.end_lineno or n.lineno):
                if best is None or n.lineno > best.lineno:
                    best = n
    return best


def trace_local(tree: ast.AST, name: str, before: int,
                params: set[str]) -> tuple[str, str]:
    """把「局部名」往回追一层赋值，判它的真实来源。

    ★ 为什么必须追：不追就只能记「局部名」，而「局部名」对信任边界
      判断毫无信息——它既可能是 CLI 参数，也可能是模块常量。
      本函数只追**同一作用域内、位于 sink 之前**的最后一次赋值。
    """
    rhs = None
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and n.lineno < before:
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    if rhs is None or n.lineno > rhs.lineno:
                        rhs = n
    if rhs is None:
        for n in ast.walk(tree):
            if isinstance(n, ast.AnnAssign) and n.lineno < before:
                t = n.target
                if isinstance(t, ast.Name) and t.id == name and n.value:
                    rhs = n
    if rhs is None:
        return "未赋值/模块级常量", name
    return classify_source(rhs.value, params)


def dead_code_check(path: Path, func: str) -> tuple[bool, str]:
    """判该 sink 是否落在**零引用函数**内（死代码）。

    ★ 判据不是 grep：grep 会被注释、字符串、同名局部变量骗。
      这里用 AST 找 `Name(ctx=Load)` 与 `Attribute` 引用，并**额外**排除
      动态派发（globals()/eval/exec/getattr-on-module），因为那类调用
      可以让「文本上零引用」的函数仍然可达。
    ★★ 动态派发只算**可能指向本模块全局命名空间**的那些：
      `getattr(args, 'x')` 是从 argparse 对象上取属性，与「按名查本模块函数」
      毫无关系——把它当动态派发会让本判据恒为「不判死代码」（假绿）。
      故只认 `globals()` / `eval` / `exec` / `vars` / `__import__`，
      以及 `getattr(<模块名本身>, ...)` 这种显式模块属性查找。
    """
    src = path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    mod_name = path.stem
    dynamic = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = n.func
        nm = fn.id if fn.__class__ is ast.Name else (
            fn.attr if fn.__class__ is ast.Attribute else "")
        if nm in ("eval", "exec", "globals", "vars", "__import__"):
            dynamic.append((n.lineno, nm))
        elif nm == "getattr" and n.args:
            tgt = n.args[0]
            tn = tgt.id if tgt.__class__ is ast.Name else ""
            if tn in ("sys.modules", mod_name) or tn == "mod":
                dynamic.append((n.lineno, "getattr(%s)" % tn))
    refs = [n.lineno for n in ast.walk(tree)
            if isinstance(n, ast.Name) and n.id == func
            and isinstance(n.ctx, ast.Load)]
    refs += [n.lineno for n in ast.walk(tree)
             if isinstance(n, ast.Attribute) and n.attr == func]
    dead = (len(refs) == 0 and len(dynamic) == 0)
    detail = ("引用=%d 动态派发=%d" % (len(refs), len(dynamic)))
    if dynamic:
        detail += " 动态点=%s" % dynamic[:3]
    return dead, detail


def main() -> int:
    if not SCAN.is_file():
        print("★ 数据源缺失：%s" % SCAN)
        return 2
    doc = json.loads(SCAN.read_text(encoding="utf-8"))
    # ★ 只取**写盘类**规则。原先用「severity==high 且非跨文件」筛选，会把
    #   `exec` 代码注入（VERIFY_A8.py:510/687）也捞进来，而它们根本没有 open，
    #   于是「未找到 open 调用」→ 早退 → 后面的结论与死代码两节全都不执行。
    #   ★★ 这正是「判据放在早退之后 = 死代码」那个坑的复发，故此处既收窄筛选，
    #   又把早退挪到**所有小节之后**。
    sinks = [f for f in doc["findings"]
             if f["severity"] == "high"
             and f["identity"]["publicClass"] == "path-traversal"]

    print("=" * 100)
    print("D-07 判定：%d 条静态写盘 sink 的输入来源（AST 回溯，非肉眼）" % len(sinks))
    print("=" * 100)

    by_src: dict[str, list] = {}
    unlocated: list[str] = []

    for f in sorted(sinks, key=lambda x: (x["location"]["path"],
                                          x["location"]["line"])):
        p = f["location"]["path"]
        ln = f["location"]["line"]
        fp = ROOT / p
        if not fp.is_file():
            unlocated.append("%s:%d（文件不存在）" % (p, ln))
            continue
        src = fp.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            unlocated.append("%s:%d（parse 失败 %s）" % (p, ln, exc))
            continue

        # 定位该行的 open(...) 调用
        target = None
        for n in ast.walk(tree):
            if isinstance(n, ast.Call):
                fn = n.func
                name = fn.id if fn.__class__ is ast.Name else (
                    fn.attr if fn.__class__ is ast.Attribute else "")
                if name in ("open", "write_bytes", "write_text"):
                    if n.lineno <= ln <= (n.end_lineno or n.lineno):
                        target = n
                        break
        if target is None:
            unlocated.append("%s:%d（未找到 open 调用）" % (p, ln))
            continue

        fn_scope = enclosing_func(tree, ln)
        params: set[str] = set()
        if fn_scope is not None:
            a = fn_scope.args
            for x in list(a.args) + list(a.kwonlyargs):
                params.add(x.arg)

        arg0 = target.args[0] if target.args else None
        if arg0 is None:
            cat, ev = "无实参", "-"
        else:
            cat, ev = classify_source(arg0, params)
            # ★ 追一层：局部名/派生 单独记账没有信息量
            if cat in ("局部名", "派生", "调用", "属性链", "下标"):
                cat2, ev2 = trace_local(tree, ev, ln, params)
                cat, ev = "%s→%s" % (cat, cat2), "%s ⇐ %s" % (ev, ev2)

        by_src.setdefault(cat, []).append((p, ln, ev))
        dead, ddet = (False, "")
        if fn_scope is not None and fn_scope.name:
            dead, ddet = dead_code_check(fp, fn_scope.name)
        print("  %-8s %-50s %-5s ← %s%s"
              % (cat, p if len(p) <= 50 else "…" + p[-49:], ln, ev,
                 ("   [死代码: %s]" % ddet) if dead else ""))

    print("\n[汇总] 按输入来源分组")
    for cat in sorted(by_src, key=lambda c: -len(by_src[c])):
        print("  %-10s %d 条" % (cat, len(by_src[cat])))

    # ---- 信任边界判定 ----
    cli = by_src.get("CLI参数", []) + by_src.get("形参", []) + by_src.get("已归一化", [])
    env = by_src.get("环境变量", [])
    lit = by_src.get("字面量", [])

    print("\n[判定] 信任边界分析")
    print("  ① CLI 参数 / 形参类 = %d 条" % len(cli))
    print("     语义：调用者=开发者本人，本就有权写任意路径 ⇒ **不跨越信任边界**，")
    print("     属工具正常功能；『修复』= 拒绝实现 --out 功能。")
    print("  ② 环境变量类 = %d 条" % len(env))
    print("     语义：**跨越边界**（进程环境由外部设置）⇒ 需要归一化/白名单。")
    print("  ③ 字面量硬编码 = %d 条" % len(lit))
    print("     语义：路径写死在源码里 ⇒ 无外部输入 ⇒ 规则误报。")

    if unlocated:
        print("\n[★ 无法定位 %d 处]（不影响下方结论，仅记账）" % len(unlocated))
        for u in unlocated:
            print("   %s" % u)

    print("\n[结论]")
    print("  28 条静态 sink 中：")
    print("    · %d 条 = CLI/形参（无边界跨越，不可『修』）" % len(cli))
    print("    · %d 条 = 环境变量（有边界，可加固）" % len(env))
    print("    · %d 条 = 字面量（规则误报）" % len(lit))
    print("  ⇒ 选项 A 的『清零』实际要求：改 %d 处 CLI 工具的公开接口语义"
          % len(cli))
    print("    （把 --out 变成受限路径），或给全部站点加归一化后仍会被报")
    print("    ——因为规则命中的是 open(变量) 这个**形状**，不是数据流。")

    # ---- 死代码判定（单独一节，因为它改变了「可修性」的性质）----
    print("\n[死代码] 落在零引用函数内的 sink")
    dead_rows = []
    for f in sorted(sinks, key=lambda x: (x["location"]["path"],
                                          x["location"]["line"])):
        p, ln = f["location"]["path"], f["location"]["line"]
        fp = ROOT / p
        if not fp.is_file():
            continue
        tree = ast.parse(fp.read_text(encoding="utf-8", errors="replace"))
        fs = enclosing_func(tree, ln)
        if fs is None or not fs.name:
            continue
        dead, det = dead_code_check(fp, fs.name)
        if dead:
            dead_rows.append((p, ln, fs.name, det))
            print("  ★ %-56s %-5s  %s()  [%s]"
                  % (p if len(p) <= 56 else "…" + p[-55:], ln, fs.name, det))
    if not dead_rows:
        print("  0 条")
    else:
        print("  ⇒ 这 %d 条所在函数**只有定义、零引用、无动态派发** ⇒ 不可达，"
              "改它们不影响任何行为。" % len(dead_rows))
        print("  ★ 但『不可达』不等于『可以随便改』：它仍在**哈希冻结件**内，"
              "改动会推翻全链断言。⇒ 这 %d 条的处置权归冻结件的所有者。"
              % len(dead_rows))
    # ★ 早退放在**所有小节之后**：改用返回值而非中途 return 2
    return 2 if unlocated else 0


if __name__ == "__main__":
    sys.exit(main())
