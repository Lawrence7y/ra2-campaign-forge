# -*- coding: utf-8 -*-
"""_doc_ast_align_check.py — 独立验证：_g7_patch.md 三代码块与 _g7_predicates.py 语义等价。
方法：AST 解析（不执行）；唯一已知差异 = r11_scan 首部 import 合并行写法，
把两侧 Import 语句展开为逐名 Import 后全等比对。只读既有件，输出到 stdout。
"""
import ast
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
mod = ast.parse((ROOT / "lead/gate_fp7_20261108/_g7_predicates.py").read_text(encoding="utf-8"))
patch_txt = (ROOT / "lead/gate_fp7_20261108/_g7_patch.md").read_text(encoding="utf-8")
blocks = re.findall(r"```python\n(.*?)```", patch_txt, re.S)
print("patch python 代码块数 =", len(blocks))


def expand_imports(stmts):
    """把 `import a as x, b as y` 合并写法展开成逐名 Import（纯排版差异归零）。"""
    out = []
    for stmt in stmts:
        if isinstance(stmt, ast.Import) and len(stmt.names) > 1:
            out.extend(ast.Import(names=[al]) for al in stmt.names)
        else:
            out.append(stmt)
    return out


def find_fn(stmts, name):
    return next(n for n in stmts if isinstance(n, ast.FunctionDef) and n.name == name)


def strip_docstrings(node):
    """递归剥离模块/函数/类体的首个字符串常量（文档字符串，纯注释性差异）。"""
    if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        b = node.body
        if (b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant)
                and isinstance(b[0].value.value, str)):
            node.body = b[1:] or [ast.Pass()]
        for ch in ast.walk(node):
            if ch is node:
                continue
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                cb = ch.body
                if (cb and isinstance(cb[0], ast.Expr) and isinstance(cb[0].value, ast.Constant)
                        and isinstance(cb[0].value.value, str)):
                    ch.body = cb[1:] or [ast.Pass()]
    return node


def norm(stmts):
    out = []
    for s in strip_docstrings(ast.Module(body=list(stmts), type_ignores=[])).body:
        if isinstance(s, ast.Import) and len(s.names) > 1:
            out.extend(ast.Import(names=[al]) for al in s.names)
        else:
            out.append(s)
    return [ast.dump(s) for s in out]


# --- r11_scan：import 展开 + docstring 剥离后全等 ---
mod_r11 = find_fn(mod.body, "r11_scan")
patch_r11 = find_fn(ast.parse(blocks[2]).body, "r11_scan")
same_r11 = norm(mod_r11.body) == norm(patch_r11.body)
print("r11_scan：import 归一化 + docstring 剥离后 AST 全等 =", same_r11)

# --- block0 (R9) / block1 (R10+R12)：同名定义归一化后全等 ---
for i, label in [(0, "block0(R9)"), (1, "block1(R10+R12)")]:
    pdefs = {n.name: n for n in ast.parse(blocks[i]).body if isinstance(n, ast.FunctionDef)}
    all_ok = True
    for name, pfn in pdefs.items():
        mfn = find_fn(mod.body, name)
        ok = norm(mfn.body) == norm(pfn.body)
        all_ok &= ok
        print(f"  {label} def {name}: 归一化后全等 = {ok}")
    top_patch = {t.id: norm([s])[0] for s in ast.parse(blocks[i]).body
                 if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name)
                 for t in s.targets}
    top_mod = {t.id: norm([s])[0] for s in mod.body
               if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name)
               and s.targets[0].id in top_patch
               for t in s.targets}
    print(f"{label} 模块级常量逐名比对 = {all(top_mod.get(k) == v for k, v in top_patch.items())}"
          f"（patch 侧 {sorted(top_patch)}）")

print("ALIGNED_EQUAL" if same_r11 else "ALIGNED_DIFF")
