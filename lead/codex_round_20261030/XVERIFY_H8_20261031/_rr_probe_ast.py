# -*- coding: utf-8 -*-
"""RR-P3：发射器副本 vs 母本 **AST 级功能 diff**（剥 docstring / 剥注释后逐节点比对），
   用于核 v2 头部「5 处枚举」声明是否与实际功能差异相符；并核 harness8 v2 的
   缺省中性（新增语句是否全部落在守卫内）。
"""
import ast
import json
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
COPY = ROOT / "lead/goal1_harness8_20261031/_launch_h8_20261031.py"
MASTER = ROOT / "lead/qc161_u0400_trip/_launch_l1_20261023.py"
H7 = ROOT / "lead/goal1_harness7_20261023/qc151_trip.harness7.py"
H8 = ROOT / "lead/goal1_harness8_20261031/qc151_trip.harness8.py"
HERE = Path(__file__).resolve().parent


def strip_docstrings(tree):
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(n, "body", None)
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                n.body = body[1:] or [ast.Pass()]
    return tree


def sig(node):
    try:
        return ast.dump(node)
    except Exception:
        return "<undumpable>"


def top_level_diff(a, b):
    out = []
    amap = {}
    bmap = {}
    for n in a.body:
        k = key_of(n)
        amap.setdefault(k, []).append(n)
    for n in b.body:
        k = key_of(n)
        bmap.setdefault(k, []).append(n)
    for k in sorted(set(amap) | set(bmap)):
        la = amap.get(k, [])
        lb = bmap.get(k, [])
        sa = [sig(x) for x in la]
        sb = [sig(x) for x in lb]
        if sa != sb:
            out.append({"key": k, "master_only": [x for x in sa if x not in sb],
                        "copy_only": [x for x in sb if x not in sa]})
    return out


def key_of(n):
    if isinstance(n, (ast.Import, ast.ImportFrom)):
        return "import"
    if isinstance(n, ast.ClassDef):
        return "class:" + n.name
    if isinstance(n, (ast.FunctionDef,)):
        return "def:" + n.name
    if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
        return "assign:" + n.targets[0].id
    if isinstance(n, ast.Expr):
        return "expr"
    return "other:" + type(n).__name__


def call_names(tree):
    c = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Attribute):
                c.append(f.attr)
            elif isinstance(f, ast.Name):
                c.append(f.id)
    return c


def count_api(path, toks):
    src = path.read_text(encoding="utf-8", errors="replace")
    return {t: src.count(t) for t in toks}


def find_func(tree, name):
    for n in ast.walk(tree):
        if isinstance(n, ast.FunctionDef) and n.name == name:
            return n
    return None


def guardedness(path, fn_names):
    """对每个函数：逐语句对齐 h7/h8，报告 h8 中新增语句及其守卫条件（父 If 测试）。"""
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    out = {}
    for name in fn_names:
        f = find_func(tree, name)
        if f is None:
            out[name] = "NOT FOUND"
            continue
        stmts = []
        for n in ast.walk(f):
            if isinstance(n, ast.If):
                for b in n.body:
                    stmts.append((sig(n.test), type(b).__name__, b.lineno))
        out[name] = {"if_tests_owning_children": sorted(set(s[0] for s in stmts))[:80],
                     "n_ifs": sum(1 for n in ast.walk(f) if isinstance(n, ast.If)),
                     "lines": [n.lineno for n in ast.walk(f) if isinstance(n, ast.If)
                               and "H8" in sig(n.test)]}
    return out


def main():
    res = {}
    # ---- 发射器：AST 功能 diff ----
    mt = strip_docstrings(ast.parse(MASTER.read_text(encoding="utf-8")))
    ct = strip_docstrings(ast.parse(COPY.read_text(encoding="utf-8")))
    d = top_level_diff(mt, ct)
    res["launcher_top_level_diff"] = [x["key"] for x in d]
    res["launcher_diff_detail"] = [
        {"key": x["key"],
         "master_only": [m[:220] for m in x["master_only"]],
         "copy_only": [c[:220] for c in x["copy_only"]]} for x in d]

    # ---- harness8 v2 守卫核：_measure_run / main 的语句级对齐 ----
    t7 = ast.parse(H7.read_text(encoding="utf-8", errors="replace"))
    t8 = ast.parse(H8.read_text(encoding="utf-8", errors="replace"))
    for fname in ("_measure_run", "main", "parse_args"):
        f7 = find_func(t7, fname)
        f8 = find_func(t8, fname)
        s7 = [sig(x) for x in f7.body]
        s8 = [sig(x) for x in f8.body]
        # 插入位置（difflib 逐语句）
        import difflib
        sm = difflib.SequenceMatcher(None, s7, s8)
        ops = [{"tag": op, "i1": i1, "i2": i2, "j1": j1, "j2": j2}
               for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
        inserted_lines = []
        for op in ops:
            if op["tag"] in ("insert", "replace"):
                for idx in range(op["j1"], op["j2"]):
                    inserted_lines.append(f8.body[idx].lineno)
        res[fname] = {"h7_body_stmts": len(s7), "h8_body_stmts": len(s8),
                      "ops": ops, "h7_stmts_absent_in_h8": len(
                          [x for x in s7 if x not in s8]),
                      "inserted_at_lines": inserted_lines}

    # ---- H8 块内新增语句的守卫归属：逐条走 AST 找父 If 测试 ----
    def h8_guard_map():
        f8 = find_func(t8, "_measure_run")
        rows = []
        for n in ast.walk(f8):
            if isinstance(n, ast.If):
                ts = sig(n.test)
                if "H8_MEASURE_START_FRAME" in ts:
                    # 收集其子树里所有语句行号
                    lines = sorted(x.lineno for x in ast.walk(n)
                                   if hasattr(x, "lineno"))
                    rows.append({"guard": ts, "n_lines": len(lines),
                                 "from": lines[0], "to": lines[-1]})
        return rows
    res["measure_run_H8_guards"] = h8_guard_map()

    def main_h8_guards():
        f8 = find_func(t8, "main")
        rows = []
        for n in ast.walk(f8):
            if isinstance(n, ast.If):
                ts = sig(n.test)
                if "h7_measure_start_frame" in ts:
                    lines = sorted(x.lineno for x in ast.walk(n) if hasattr(x, "lineno"))
                    inner = [c for c in n.body if isinstance(c, ast.If)]
                    rows.append({"guard": ts, "from": lines[0], "to": lines[-1],
                                 "n_lines": len(lines),
                                 "nested_if_guards": [sig(i.test) for i in inner]})
        return rows
    res["main_H8_guards"] = main_h8_guards()

    # ---- 顶层副作用计数 ----
    res["top_level_calls"] = {
        "h7": call_names(ast.Module(body=[n for n in t7.body if isinstance(n, ast.Expr)],
                                   type_ignores=[])),
        "h8": call_names(ast.Module(body=[n for n in t8.body if isinstance(n, ast.Expr)],
                                   type_ignores=[])),
    }

    # ---- 危险 API 计数 ----
    toks = ["SetForegroundWindow", "keybd_event", "mouse_event", "PostMessage",
            "VirtualAllocEx", "CreateRemoteThread", "WriteProcessMemory",
            "VirtualProtectEx", "TerminateProcess", "shutil.rmtree"]
    res["api_counts"] = {"h7": count_api(H7, toks), "h8": count_api(H8, toks)}
    res["launcher_api_counts"] = {"master": count_api(MASTER, toks),
                                  "copy": count_api(COPY, toks)}

    # ---- 退出码常量集合相等 ----
    def exit_consts(p):
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        out = set()
        for n in tree.body:
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) \
                    and n.targets[0].id.startswith("EXIT_"):
                out.add(n.targets[0].id + "=" + sig(n.value))
        return out
    e7, e8 = exit_consts(H7), exit_consts(H8)
    res["exit_consts"] = {"h7": len(e7), "h8": len(e8),
                          "sym_diff": sorted(e7 ^ e8)}

    txt = json.dumps(res, ensure_ascii=False, indent=1)
    (HERE / "rr_p3_ast.stdout.txt").write_text(txt, encoding="utf-8")
    print(txt[:6000])


if __name__ == "__main__":
    main()
