# -*- coding: utf-8 -*-
# O1′ 复核员自做 AST 顶层（import 期）副作用扫描 —— 独立于撰写人的 _o1_astcheck.py。
# 只读候选文件，不执行它；列出 import 期会真正执行的调用（跳过 def/class/lambda 体，
# 但计入其装饰器与参数默认值；计入顶层 if/try/with 体）。
import ast
from pathlib import Path

CAND = Path(r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py")
src = CAND.read_text(encoding="utf-8")
tree = ast.parse(src, filename=str(CAND))

calls = []


def add_call(node):
    if isinstance(node, ast.Call):
        seg = ""
        try:
            seg = ast.get_source_segment(src, node) or ""
        except Exception:
            pass
        calls.append((node.lineno, seg.replace("\n", " ")[:140]))


def walk(n):
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
        for d in getattr(n, "decorator_list", []) or []:
            for c in ast.walk(d):
                add_call(c)
        args = getattr(n, "args", None)
        if args is not None:
            for d in list(args.defaults) + [d for d in args.kw_defaults if d is not None]:
                for c in ast.walk(d):
                    add_call(c)
        if isinstance(n, ast.ClassDef):
            for b in n.bases:
                for c in ast.walk(b):
                    add_call(c)
        return
    add_call(n)
    for ch in ast.iter_child_nodes(n):
        walk(ch)


for st in tree.body:
    walk(st)

calls.sort()
print(f"top-level (import-time) call count = {len(calls)}")
for ln, seg in calls:
    print(f"  :{ln}  {seg}")

DANGER = ("open(", "write_text", "write_bytes", "mkdir", ".system", "Popen",
          "subprocess", "socket", "urlopen", "remove(", "rmtree", "unlink",
          "shutil", "rename(", "taskkill", "gamemd", "ra2loader", "YURI")
flags = [(ln, seg) for ln, seg in calls if any(d in seg for d in DANGER)]
print("DANGER-flagged:", "NONE" if not flags else "")
for ln, seg in flags:
    print(f"  !! :{ln}  {seg}")
