# -*- coding: utf-8 -*-
"""_r5_ 码序静态证明：AST 提取 classify_except_freshness 顶层分支序列。
零执行、零动态加载：只 ast.parse 只读候选文件，打印分支头/行号/出口实参。
"""
import ast

CAND = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"

src = open(CAND, "rb").read().decode("utf-8")
fn = None
for node in ast.parse(src).body:
    if isinstance(node, ast.FunctionDef) and node.name == "classify_except_freshness":
        fn = node
if fn is None:
    print("ABORT: 函数未找到")
    raise SystemExit(2)

print(f"def classify_except_freshness 起于 :{fn.lineno}，止于 :{fn.end_lineno}")
print("---- 函数体顶层语句序列（行号 | 语句 | _finish 出口实参）----")


def find_finish(stmt):
    """在该语句子树中找 _finish 调用的字面量实参。"""
    out = []
    for n in ast.walk(stmt):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id == "_finish"):
            args = []
            for a in n.args:
                try:
                    args.append(ast.literal_eval(a))
                except Exception:
                    args.append(ast.unparse(a))
            out.append(args)
    return out


for stmt in fn.body:
    ln = stmt.lineno
    head = ast.unparse(stmt)
    if len(head) > 72:
        head = head[:72] + "…"
    fin = find_finish(stmt)
    print(f":{ln}  {head}")
    for args in fin:
        print(f"        → _finish({args[0]!r}, {args[1]!r}, {args[2]!r}, …)")

print("---- done ----")
