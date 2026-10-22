#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A4 / A7 / A8 修复门禁 v2（修掉 v1 的记账断裂假绿）。

★★ v1 的致命缺陷（由异族复核员发现）：
   `check()` 只有定义、零调用；20 条断言全走 `ok.append()`，从不进 `results`。
   于是汇总只统计负控 ⇒ 打出 "0/0 PASS"、退出码恒 0。
   **被测物改坏了门禁也不转红** —— 这就是恒真式假绿。

v2 的三条硬要求：
  1. 每条断言必须经 `check()` 进入 `results`，汇总数必须等于断言总数（自校验）。
  2. 每条断言都配负控（改回旧写法必须转红）；负控自身也进 `results`。
  3. 断言必须**读实际源码**取值，不用裸子串（`"return 3" in t` 塞个死函数就能骗过）。

用法：
  python _verify_probe_a4a7a8.py            # 正控 + 自校验
  python _verify_probe_a4a7a8.py --negctl   # 额外跑负控
"""
import ast
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "_rc4_ab_probe.py"
TEXT = SRC.read_text(encoding="utf-8")

RESULTS = []          # (tag, ok, evidence)


def check(tag, cond, evidence=""):
    """★ 唯一记账入口。任何断言不走这里就不算数。"""
    RESULTS.append((tag, bool(cond), evidence))
    print("  %-46s %s  %s" % (tag, "PASS" if bool(cond) else "FAIL", evidence))
    return bool(cond)


# ------------------------------------------------------------------ 工具
def func_node(src, name):
    """按 AST 取顶层函数节点；找不到返回 None。"""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n
    return None


def func_src(src, name):
    """取函数源码文本（用于精确断言，避免裸子串误命中）。"""
    n = func_node(src, name)
    if n is None:
        return None
    seg = ast.get_source_segment(src, n)
    return seg


def main_returns_3(src):
    """★ 真断言：main() 里必须有一条**可达的** `return 3`。

    不能只 grep "return 3" —— 塞个永不调用的死函数就能骗过。
    这里要求 return 3 出现在 main() 函数体内。
    """
    n = func_node(src, "main")
    if n is None:
        return False, "main() 不存在"
    body = ast.get_source_segment(src, n) or ""
    if not re.search(r"return\s+3\b", body):
        return False, "main() 内无 return 3"
    # 且必须在某个 if 的分支里（不能是无条件 return 3）
    for node in ast.walk(n):
        if isinstance(node, ast.If):
            seg = ast.get_source_segment(src, node) or ""
            if re.search(r"return\s+3\b", seg):
                return True, "return 3 位于 if 分支内"
    return False, "return 3 不在 if 分支内"


# ------------------------------------------------------------------ A7
def a7(src):
    ok = []
    sn = func_src(src, "safe_name") or ""
    ok.append(("A7 safe_name 拒冒号（函数体内）",
               re.search(r'if\s+":"\s+in\s+name\s*:', sn) is not None,
               "safe_name 函数体内有 `if \":\" in name:`"))
    # ★ 用 AST 找真实的 if 节点比较行号，不能用 rfind（文档字符串里也有 `":" in name`）
    colon_ln = path_ln = None
    sn_node = func_node(src, "safe_name")
    if sn_node is not None:
        for st in sn_node.body:
            if not isinstance(st, ast.If):
                continue
            seg = ast.get_source_segment(src, st) or ""
            if '":" in name' in seg and colon_ln is None:
                colon_ln = st.lineno
            if "Path(name).name" in seg and path_ln is None:
                path_ln = st.lineno
    ok.append(("A7 冒号检查早于 Path(name).name",
               colon_ln is not None and path_ln is not None
               and colon_ln < path_ln,
               "冒号 if L%s < Path if L%s" % (colon_ln, path_ln)))
    sd = func_src(src, "safe_dll_name") or ""
    ok.append(("A7 safe_dll_name 存在", bool(sd), ""))
    ok.append(("A7 safe_dll_name 要求 .dll",
               'endswith(".dll")' in sd, ""))
    mn = func_src(src, "main") or ""
    ok.append(("A7 main 调 safe_dll_name（非裸 safe_name）",
               "safe_dll_name(" in mn and "safe_name(args.dll)" not in mn,
               ""))
    return ok


# ------------------------------------------------------------------ A4
def a4(src):
    ok = []
    cu = func_src(src, "_cleanup") or ""
    ok.append(("A4 _cleanup 提升 a8_verdict",
               'rec["a8_verdict"] = a8.get("verdict")' in cu, ""))
    ok.append(("A4 _cleanup 提升 cleanup_ok",
               'rec["cleanup_ok"] =' in cu, ""))
    mn = func_src(src, "main") or ""
    ok.append(("A4 main 读 a8_verdict", 'r.get("a8_verdict")' in mn, ""))
    ok.append(("A4 main 置 results_aborted", "results_aborted = True" in mn, ""))
    reachable, why = main_returns_3(src)
    ok.append(("A4 main 有可达 return 3", reachable, why))
    ok.append(("A4 退出码条件用上 a8",
               re.search(r"if\s+results_aborted\s+or\s+n_a8_ok\s*!=\s*len\(",
                         mn) is not None, ""))
    return ok


# ------------------------------------------------------------------ A8
def a8(src):
    ok = []
    shell = func_node(src, "one_trip")
    ok.append(("A8 one_trip 存在", shell is not None, ""))
    if shell is not None:
        has_finally = any(
            isinstance(h, ast.Try) and h.finalbody for h in ast.walk(shell))
        ok.append(("A8 one_trip 有 finally 块", has_finally, ""))
        # finally 里必须真的调 _cleanup
        fin_src = ""
        for h in ast.walk(shell):
            if isinstance(h, ast.Try) and h.finalbody:
                for st in h.finalbody:
                    fin_src += (ast.get_source_segment(src, st) or "") + "\n"
        ok.append(("A8 finally 内调 _cleanup", "_cleanup(" in fin_src, ""))
        # 主体内不得再有显式 _cleanup（唯一出口）
        body = func_src(src, "_one_trip_body") or ""
        ok.append(("A8 主体内无显式 _cleanup", "_cleanup(" not in body, ""))
    ok.append(("A8 主体已拆到 _one_trip_body",
               func_node(src, "_one_trip_body") is not None, ""))
    cu = func_src(src, "_cleanup") or ""
    ok.append(("A8 _cleanup 幂等短路", 'if rec.get("_cleaned"):' in cu, ""))
    ok.append(("A8 pid 定向击杀存在", 'rec["pid_killed"]' in cu, ""))
    ok.append(("A8 carrier 为 None 时不扫（防 AttributeError）",
               "if carrier is None:" in cu, ""))
    # 早退点必须登记 proc
    body = func_src(src, "_one_trip_body") or ""
    ok.append(("A8 gamemd_not_found 早退登记 proc",
               re.search(r'gamemd_not_found_under_carrier"\s*\n'
                         r'\s*#.*\n?\s*state\["proc"\]\s*=\s*proc', body)
               is not None or
               (body.find("gamemd_not_found_under_carrier") != -1 and
                body.find('state["proc"] = proc') <
                body.find("gamemd_not_found_under_carrier")),
               ""))
    return ok


# ------------------------------------------------------------------ 负控
# 每个变异都必须让**至少一条**断言转红；否则该负控失效。
NEGCTL = [
    ("A7 删掉冒号检查",
     lambda s: re.sub(r'    if ":" in name:\n'
                      r'        raise ValueError\("name contains drive/ADS colon[^\n]*\n',
                      "", s),
     a7),
    ("A7 main 退回裸 safe_name",
     lambda s: s.replace("safe_dll_name(args.dll)", "safe_name(args.dll)"),
     a7),
    ("A4 return 3 改成 return 0",
     lambda s: re.sub(r"return 3", "return 0", s),
     a4),
    ("A4 去掉 results_aborted 置位",
     lambda s: s.replace("results_aborted = True", "pass"),
     a4),
    ("A4 把 return 3 挪进死函数",
     # ★ 正确做法：把 main() 里的 return 3 删掉，另建一个永不调用的函数返回 3。
     #   裸子串断言会因此转绿（骗过），AST 断言必须转红。
     lambda s: re.sub(r"return 3", "return 0", s).replace(
         "def _cleanup(",
         "def _dead_never_called():\n    return 3\n\n\ndef _cleanup(", 1),
     a4),
    ("A8 去掉 finally",
     lambda s: s.replace('    finally:\n        rec = state["rec"]',
                         '    if False:\n        rec = state["rec"]', 1),
     a8),
    ("A8 主体内塞回显式 _cleanup",
     lambda s: s.replace('    rec["guard"] = parse_guard_log(',
                         '    _cleanup(proc, carrier, rec, attached=True)\n'
                         '    rec["guard"] = parse_guard_log(', 1),
     a8),
    ("A8 去掉 carrier None 守卫",
     lambda s: s.replace("    if carrier is None:", "    if False:"),
     a8),
]


def run_group(name, fn, src):
    print()
    print("--- %s ---" % name)
    items = fn(src)
    for tag, cond, ev in items:
        check(tag, cond, ev)
    return len(items)


def main():
    print("=" * 92)
    print("A4 / A7 / A8 修复门禁 v2（v1 曾因记账断裂假绿，本版强制全量记账）")
    print("=" * 92)

    n_assert = 0
    n_assert += run_group("A7", a7, TEXT)
    n_assert += run_group("A4", a4, TEXT)
    n_assert += run_group("A8", a8, TEXT)

    # ★ 自校验：记账数必须等于断言数，否则就是 v1 那种断裂
    n_pos = len(RESULTS)
    check("自校验：断言全量进 results",
          n_pos == n_assert, "%d 记账 / %d 断言" % (n_pos, n_assert))

    if "--negctl" in sys.argv:
        print()
        print("=" * 92)
        print("负控：改回旧写法后，断言必须转红（负控失效也算 FAIL）")
        print("=" * 92)
        for name, mutate, fn in NEGCTL:
            mutated = mutate(TEXT)
            if mutated == TEXT:
                check("负控 %s" % name, False, "变异未命中 ⇒ 负控本身失效")
                continue
            try:
                greens = [t for t, c, _ in fn(mutated) if c]
                total = len(fn(mutated))
            except SyntaxError as e:
                check("负控 %s" % name, True, "变异致语法错误（等价转红）: %s" % e)
                continue
            red = total - len(greens)
            check("负控 %s" % name, red > 0, "转红 %d/%d" % (red, total))

    npass = sum(1 for _, c, _ in RESULTS if c)
    print()
    print("%d/%d PASS" % (npass, len(RESULTS)))
    if npass != len(RESULTS):
        print("失败项：")
        for t, c, e in RESULTS:
            if not c:
                print("  - %s  %s" % (t, e))
    return 0 if npass == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
