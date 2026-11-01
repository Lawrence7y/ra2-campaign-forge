# -*- coding: utf-8 -*-
"""RR-P5：发射器副本 vs 母本 —— 去注释 + 去 docstring 后的**逐行功能 diff**，
   用于核头部「5 处枚举」是否穷尽了功能差异（含 print 文案、help 文案等字面量）。
"""
import ast
import difflib
import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
HERE = Path(__file__).resolve().parent
COPY = ROOT / "lead/goal1_harness8_20261031/_launch_h8_20261031.py"
MASTER = ROOT / "lead/qc161_u0400_trip/_launch_l1_20261023.py"
JUDGE_C = ROOT / "lead/goal1_harness8_20261031/_judge_h8_20261031.py"
JUDGE_M = ROOT / "lead/qc161_u0400_trip/_judge_l1_20261023.py"


def functional_lines(path):
    """去注释（用 tokenize）+ 去 docstring（AST 标记行号），返回剩余非空代码行。"""
    import tokenize
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    doc_lines = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(n, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                for ln in range(body[0].lineno, body[0].end_lineno + 1):
                    doc_lines.add(ln)
    comment_lines = set()
    import io
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            comment_lines.add(tok.start[0])
    out = []
    for i, line in enumerate(src.splitlines(), 1):
        if i in doc_lines or i in comment_lines:
            continue
        if not line.strip():
            continue
        out.append(line.rstrip())
    return out


def main():
    res = {}
    for tag, a, b in (("launcher", MASTER, COPY), ("judge", JUDGE_M, JUDGE_C)):
        la, lb = functional_lines(a), functional_lines(b)
        dl = list(difflib.unified_diff(la, lb, lineterm="", n=0))
        adds = [l[1:].strip() for l in dl if l.startswith("+") and not l.startswith("+++")]
        dels = [l[1:].strip() for l in dl if l.startswith("-") and not l.startswith("---")]
        res[tag] = {"master_functional_lines": len(la), "copy_functional_lines": len(lb),
                    "added": adds, "deleted": dels,
                    "n_added": len(adds), "n_deleted": len(dels)}
    txt = json.dumps(res, ensure_ascii=False, indent=1)
    (HERE / "rr_p5_functional_diff.stdout.txt").write_text(txt, encoding="utf-8")
    print(txt)


if __name__ == "__main__":
    main()
