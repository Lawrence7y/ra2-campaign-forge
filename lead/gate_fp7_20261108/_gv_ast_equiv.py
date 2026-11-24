# -*- coding: utf-8 -*-
"""_gv_ast_equiv.py — 补丁代码块 ≡ 谓词模块的 AST 级语义比对（解析，不执行）。
对 _g7_patch.md 三个 python 代码块逐块 ast.parse，与 _g7_predicates.py 中同名
顶层定义（函数/赋值）剥 docstring 后比对 ast.dump。格式差异（压缩行、注释、
docstring 有无）不参与比较，只比语义结构。
"""
import ast, pathlib, re, sys

WD = pathlib.Path(r"D:\Project\ra2-campaign-forge\lead\gate_fp7_20261108")
patch = (WD / "_g7_patch.md").read_text(encoding="utf-8")
blocks = re.findall(r"```python\n(.*?)```", patch, re.S)
print("patch python 代码块数 = %d" % len(blocks))

def strip_docstrings(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
    return tree

def top_defs(src):
    tree = strip_docstrings(ast.parse(src))
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.Assign)):
            out[ast.dump(node)] = node
    return out

mod_src = (WD / "_g7_predicates.py").read_text(encoding="utf-8")
mod_defs = top_defs(mod_src)
mod_keys = set(mod_defs)
print("模块顶层可比对定义（ast.dump 键）= %d 个" % len(mod_keys))

fails = 0
for i, b in enumerate(blocks):
    bt = strip_docstrings(ast.parse(b, "block%d" % i))
    n_node = 0
    for node in bt.body:
        if not isinstance(node, (ast.FunctionDef, ast.Assign)):
            continue
        n_node += 1
        key = ast.dump(node)
        if key in mod_keys:
            continue
        # 未整节点匹配：按名字找模块同名定义再比
        name = None
        if isinstance(node, ast.FunctionDef):
            name = node.name
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
        cand = None
        tree2 = strip_docstrings(ast.parse(mod_src))
        for m in tree2.body:
            if isinstance(m, ast.FunctionDef) and m.name == name:
                cand = m
            elif isinstance(m, ast.Assign) and isinstance(m.targets[0], ast.Name) and m.targets[0].id == name:
                cand = m
        if cand is not None and ast.dump(cand) == key:
            print("  block%d %s: 名下比对相等" % (i, name))
            continue
        fails += 1
        print("  block%d %s: SEMANTIC DIFF" % (i, name))
        print("    patch-side dump: " + key[:300])
        print("    module-side dump: " + (ast.dump(cand)[:300] if cand is not None else "<无同名定义>"))
    print("  block%d: 比对节点 %d 个" % (i, n_node))

print()
print("==== _gv_ast_equiv verdict: semantic_diff=%d ====" % fails)
sys.exit(1 if fails else 0)
