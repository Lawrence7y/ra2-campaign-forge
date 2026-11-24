# -*- coding: utf-8 -*-
"""_mrv_toplevel_scan.py — import 前护栏标定：枚举候选模块顶层全部 Call。零写。"""
import ast
import sys

CAND = r"D:\Project\ra2-campaign-forge\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"

with open(CAND, "rb") as fh:
    raw = fh.read()
src = raw.decode("utf-8")
tree = ast.parse(src, filename=CAND)

print("MRV_TOPLEVEL_SCAN_START")
kinds = {}
for st in tree.body:
    kinds[type(st).__name__] = kinds.get(type(st).__name__, 0) + 1
print("toplevel statement kinds:", kinds)

n = 0
for st in tree.body:
    # 语句自身是表达式调用
    if isinstance(st, ast.Expr) and isinstance(st.value, ast.Call):
        n += 1
        print("TOPCALL @:%d  %s" % (st.lineno, ast.get_source_segment(src, st.value.func)))
    # 赋值/注解赋值右值内嵌调用
    if isinstance(st, (ast.Assign, ast.AnnAssign)):
        val = st.value if isinstance(st, ast.Assign) else st.value
        if val is None:
            continue
        for node in ast.walk(val):
            if isinstance(node, ast.Call):
                n += 1
                print("NESTEDCALL @:%d  %s" % (node.lineno,
                      ast.get_source_segment(src, node.func)))
    # 顶层 If 的 test 与 body 顶层调用
    if isinstance(st, ast.If):
        print("TOPIF @:%d  test=%s" % (st.lineno, ast.get_source_segment(src, st.test)))
        for sub in ast.walk(st.test):
            if isinstance(sub, ast.Call):
                n += 1
                print("IFTESTCALL @:%d" % sub.lineno)
        for sub_st in st.body:
            if isinstance(sub_st, ast.Expr) and isinstance(sub_st.value, ast.Call):
                n += 1
                print("IFBODY-TOPCALL @:%d  %s" % (sub_st.lineno,
                      ast.get_source_segment(src, sub_st.value.func)[:60]))
print("total calls seen:", n)
print("MRV_TOPLEVEL_SCAN_DONE")
