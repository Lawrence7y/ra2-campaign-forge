# -*- coding: utf-8 -*-
# _w2v_ast.py — 候选模块顶层 import 期 Call 清点（验证 importlib 装载零文件 IO 前提）
import ast

P = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"
src = open(P, "rb").read().decode("utf-8")
lines = src.splitlines()
tree = ast.parse(src)

found = []
guard_skipped = []


def is_main_guard(node):
    t = node.test
    return (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name)
            and t.left.id == "__name__")


def addcall(c):
    ln = getattr(c, "lineno", None)
    seg = (lines[ln - 1].strip() if ln and ln - 1 < len(lines) else "?")
    found.append((ln, seg[:130]))


def findcalls(node):
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            for d in child.decorator_list:
                findcalls(d)
            a = getattr(child, "args", None)
            if a is not None:
                for x in list(a.defaults) + [y for y in a.kw_defaults
                                             if y is not None]:
                    findcalls(x)
            continue
        if isinstance(child, ast.Call):
            addcall(child)
        if isinstance(child, ast.If) and is_main_guard(child):
            guard_skipped.append(getattr(child, "lineno", None))
            continue
        findcalls(child)


for stmt in tree.body:
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for d in stmt.decorator_list:
            findcalls(d)
        for x in list(stmt.args.defaults) + [y for y in stmt.args.kw_defaults
                                             if y is not None]:
            findcalls(x)
        continue
    if isinstance(stmt, ast.ClassDef):
        for d in stmt.decorator_list:
            findcalls(d)
        for b in stmt.bases:
            findcalls(b)
        for s in stmt.body:
            findcalls(s)
        continue
    if isinstance(stmt, ast.If) and is_main_guard(stmt):
        guard_skipped.append(getattr(stmt, "lineno", None))
        continue
    findcalls(stmt)

print("import-time Call count:", len(found))
for ln, seg in sorted(found, key=lambda t: (t[0] or 0)):
    print(":%s: %s" % (ln, seg))
print("main-guard skipped at:", guard_skipped)
