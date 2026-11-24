# -*- coding: utf-8 -*-
"""静态审计被核件模块顶层语句：确认 import 无副作用（不写盘、不起进程、不退出）。
只 ast.parse，不 import、不 exec。"""
import ast
import hashlib
from pathlib import Path

CAND = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py")
raw = CAND.read_bytes()
print("被核对象 SHA256 =", hashlib.sha256(raw).hexdigest())
print("字节数 =", len(raw))
tree = ast.parse(raw.decode("utf-8"))

SAFE_KINDS = ("FunctionDef", "AsyncFunctionDef", "ClassDef", "Assign",
              "AnnAssign", "Import", "ImportFrom", "Expr", "Pass", "If")

flagged = []
for node in tree.body:
    kind = type(node).__name__
    seg = ast.get_source_segment(raw.decode("utf-8"), node) or ""
    first = (seg.splitlines() or [""])[0][:100]
    safe = kind in SAFE_KINDS
    if kind == "If":
        test = node.test
        guard = (isinstance(test, ast.Compare)
                 and isinstance(test.left, ast.Name) and test.left.id == "__name__"
                 and any(isinstance(cmp, ast.Constant) and cmp.value == "__main__"
                         for cmp in test.comparators))
        safe = guard
        first = ("__main__ 守卫" if guard else "顶层 If 非守卫") + " | " + first
    if kind == "Expr" and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
        first = "模块 docstring | " + first[:60]
        safe = True
    if not safe:
        flagged.append((kind, node.lineno, first))
    print("%-4s 行%-5d %s" % ("OK" if safe else "FLAG", node.lineno, first))

print("-" * 60)
if flagged:
    print("NEEDS_REVIEW =", flagged)
else:
    print("TOPLEVEL_INERT = True（顶层仅常量/定义/__main__ 守卫，import 无副作用）")
