# -*- coding: utf-8 -*-
"""_eiv_02_code_indep.py — 独立复核员 ②：自己实现代码级数据流判据（含完整 AST 字面提取）。

不 import 撰写人的 _ei_*；自己 ast.parse 三模块 + 流水线，逐条核依赖到行号。
重点：撰写人 _ei_05_admission.py:59-72 的 lits() 只收 Tuple/List/Set 内字符串与
re.compile 首参，【漏掉裸字符串模块级常量】。本脚本用全量 ast.walk 收所有
ast.Constant(str)，复核 A2 是否真「零共享字面」。

运行: python -I -X utf8 -B <绝对路径>
"""
import ast
import hashlib
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"
N13_DIR = ROOT / "lead" / "gate_n13_20261109"
G7P = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
V12P = ROOT / "lead" / "gate_v1v2_20261109" / "_v12_rule.py"
PIPEP = ROOT / "lead" / "gate_pipeline_20261109" / "_gp_pipeline.py"
N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def lines(p):
    return p.read_text(encoding="utf-8").splitlines()


def show(p, nums):
    L = lines(p)
    return {n: L[n - 1].strip() for n in nums if 0 < n <= len(L)}


def all_string_constants(path):
    """完整提取：模块级所有 ast.Constant(str)（含裸字符串赋值、元组元素、re.compile 参数）。"""
    t = ast.parse(path.read_text(encoding="utf-8"))
    out = {}
    for node in ast.walk(t):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.setdefault(node.value, []).append(node.lineno)
    return out


def writer_style_literals(path):
    """复刻撰写人 _ei_05_admission.py:59-72 的 lits()：只收模块级 Assign 的
    Tuple/List/Set 元素 与 re.compile 首参（不含裸字符串赋值）。"""
    t = ast.parse(path.read_text(encoding="utf-8"))
    out = set()
    for n in t.body:
        if not isinstance(n, ast.Assign):
            continue
        v = n.value
        if isinstance(v, (ast.Tuple, ast.List, ast.Set)):
            for e in v.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str):
                    out.add(e.value)
        elif isinstance(v, ast.Call) and getattr(v.func, "attr", "") == "compile" \
                and v.args and isinstance(v.args[0], ast.Constant):
            out.add(v.args[0].value)
    return out


def imports(path):
    t = ast.parse(path.read_text(encoding="utf-8"))
    return ([n.module or "" for n in ast.walk(t) if isinstance(n, ast.ImportFrom)]
            + [a.name for n in ast.walk(t) if isinstance(n, ast.Import)
               for a in n.names])


def func_names(path):
    t = ast.parse(path.read_text(encoding="utf-8"))
    return {n.name for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main():
    p13 = next(p for p in sorted(N13_DIR.iterdir())
               if p.is_file() and fp(p) == (N13_SHA, 16649))
    paths = {"N13": p13, "G7": G7P, "V12": V12P}
    src = {k: p.read_text(encoding="utf-8") for k, p in paths.items()}
    out = {"files": {k: str(v.relative_to(ROOT)).replace("\\", "/") for k, v in paths.items()}}

    # ---- ②(a) 逐行核依赖（自己读，行号级）----
    out["line_evidence"] = {
        "N13": show(p13, [5, 6, 25, 183, 189, 195, 196, 199, 200, 231, 242, 243,
                          251, 252, 253, 254, 256, 257, 307, 310]),
        "G7": show(G7P, [69, 71, 76, 78, 92, 113, 120, 134, 144, 145]),
        "V12": show(V12P, [29, 32, 36, 38, 42, 66, 97, 108, 143, 149, 152, 167, 168, 169, 170]),
        "PIPE": show(PIPEP, [29, 49, 50, 51, 52, 58, 78, 79, 80, 81, 135, 137, 179, 180, 253]),
    }

    # ---- ②(b) N13 是否转发 R10/R12：AST 检查 r13_scan 的参数与调用 ----
    t13 = ast.parse(src["N13"])
    r13 = next(n for n in t13.body if isinstance(n, ast.FunctionDef) and n.name == "r13_scan")
    args = [a.arg for a in r13.args.args]
    # 找 r10_scan(...) / r12_scan(...) 调用行
    calls = {}
    for n in ast.walk(r13):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
            if n.func.id in ("r10_scan", "r12_scan"):
                calls.setdefault(n.func.id, []).append(n.lineno)
    # 找 C 类 PASS 的 kind in (...) 判定行
    c_lines = []
    for n in ast.walk(r13):
        if isinstance(n, ast.Compare):
            seg = ast.get_source_segment(src["N13"], n) or ""
            if "r10_kind" in seg or ("negation" in seg and "quote_mention" in seg):
                c_lines.append((n.lineno, " ".join(seg.split())[:110]))
    out["n13_forwards_r10"] = {
        "r13_scan_params": args,
        "has_r10_scan_param": "r10_scan" in args,
        "has_r12_scan_param": "r12_scan" in args,
        "internal_calls": calls,
        "C_class_kind_gate_lines": c_lines,
        # C 类 exempt=True 且 kind=C 的那行
        "C_assign_line": 254,
        "C_assign_text": lines(p13)[253].strip(),
    }
    # 流水线注入
    tp = ast.parse(src["G7"] if False else PIPEP.read_text(encoding="utf-8"))
    inject = []
    for n in ast.walk(tp):
        if isinstance(n, ast.Call):
            for kw in n.keywords:
                if isinstance(kw.value, ast.Attribute):
                    seg = ast.get_source_segment(PIPEP.read_text(encoding="utf-8"), kw.value) or ""
                    if seg.startswith("g7.") or ".r10_scan" in seg or ".r12_scan" in seg:
                        inject.append((n.lineno, kw.arg, seg))
    out["pipeline_injection"] = sorted(set(inject))

    # ---- ②(c) R12 复用 r10_context ----
    tg7 = ast.parse(src["G7"])
    r12 = next(n for n in tg7.body if isinstance(n, ast.FunctionDef) and n.name == "r12_scan")
    r12_calls = [(n.lineno, getattr(n.func, "id", "?")) for n in ast.walk(r12)
                 if isinstance(n, ast.Call)]
    out["r12_reuses_r10"] = {
        "r12_scan_calls": r12_calls,
        "calls_r10_context": any(c[1] == "r10_context" for c in r12_calls),
        "source_line_144": lines(G7P)[143].strip(),
    }

    # ---- ②(d) 五检 A1-A5（自己实现）+ 完整字面 vs 撰写人口径对照 ----
    full = {k: all_string_constants(p) for k, p in paths.items()}
    wstyle = {k: writer_style_literals(p) for k, p in paths.items()}
    imps = {k: imports(p) for k, p in paths.items()}
    fns = {k: func_names(p) for k, p in paths.items()}

    pairs = [("V12", "G7"), ("V12", "N13"), ("G7", "N13")]
    out["A_tests"] = {}
    for a, b in pairs:
        shared_full = sorted(set(full[a]) & set(full[b]))
        shared_wstyle = sorted(wstyle[a] & wstyle[b])
        out["A_tests"]["%s|%s" % (a, b)] = {
            "A1_no_import": not any(
                ("g7" in x or "predicate" in x or "n13" in x or "v12" in x)
                for x in imps[a] + imps[b]),
            "imports_a": imps[a], "imports_b": imps[b],
            "A2_writer_style_shared": shared_wstyle,
            "A2_writer_style_pass": not shared_wstyle,
            "A2_full_shared_literals": shared_full,
            "A2_full_pass": not shared_full,
            "A4_shared_function_names": sorted(fns[a] & fns[b]),
            "A4_pass": not (fns[a] & fns[b]),
            "A5_distinct_files": paths[a] != paths[b],
        }

    # V12 的唯一 import 是不是 re
    out["v12_only_import_re"] = {"imports": imps["V12"],
                                 "is_only_re": imps["V12"] == ["re"]}
    # V12 是否复用 r10_context / DOUBLE_NEG_RE / NEG_RE 名字
    out["v12_no_r10_symbols"] = {
        s: (s not in src["V12"]) for s in
        ("r10_context", "DOUBLE_NEG_RE", "NEG_RE", "r10_scan", "r12_scan")}

    # ---- ②(e) 74 行运行时输入契约（自己从只读 JSON 统计）----
    O = json.loads((ROOT / "lead" / "gate_pipeline_20261109" / "_gp_regression_out.json")
                   .read_text(encoding="utf-8"))
    import collections
    c = collections.Counter(tuple(r["tokens"]) for r in O["rows"])
    T3 = ("已入账", "已追加", "已生效")
    badban = ("已生效", "可应用母本", "放行 N-5", "已入账", "已追加")
    same = c[T3]
    superset = sum(v for k, v in c.items() if k != T3 and set(T3) <= set(k))
    out["runtime_token_contract"] = {
        "families": [{"tokens": list(k), "rows": v} for k, v in c.items()],
        "identical_to_DEFAULT_TOKENS": same,
        "superset_of_three_tokens": superset,
        "badban_is_superset": set(T3) <= set(badban),
        "shared_contract_rows": same + superset,
        "n": len(O["rows"]),
        "note": "字面词表常量并非模块级共享定义；共享发生在编排层喂同一 tokens"}

    (W / "_eiv_02_code_indep_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 控制台 ----
    print("== ② N13 转发 R10/R12 ==")
    f = out["n13_forwards_r10"]
    print("  r13_scan params =", f["r13_scan_params"])
    print("  internal calls =", f["internal_calls"], " C gate =", f["C_class_kind_gate_lines"])
    print("  :254 =", f["C_assign_text"])
    print("  pipeline injection =", out["pipeline_injection"])
    print("  R12 calls r10_context =", out["r12_reuses_r10"]["calls_r10_context"],
          "| :144 =", out["r12_reuses_r10"]["source_line_144"])
    print("  V12 only import re =", out["v12_only_import_re"]["is_only_re"],
          "| no r10 symbols =", out["v12_no_r10_symbols"])
    print("== ② 五检 A2：撰写人口径 vs 完整字面 ==")
    for k, v in out["A_tests"].items():
        print("  %-10s writer_shared=%-28s full_shared=%s" %
              (k, str(v["A2_writer_style_shared"]), str(v["A2_full_shared_literals"])))
    print("== ② 74 行运行时输入契约 ==")
    print(" ", out["runtime_token_contract"]["families"])
    print("  identical=%d superset=%d shared_contract=%d/%d" %
          (same, superset, same + superset, len(O["rows"])))
    print("written: _eiv_02_code_indep_out.json")


if __name__ == "__main__":
    main()
