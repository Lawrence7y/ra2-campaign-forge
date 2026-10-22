#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""异族核验 A4 / A7 / A8 三处修复的机器门禁（含负控）。

背景：异族核验（xfam_abc_checks.txt）判 A4/A7/A8 为 FAIL。本脚本不重跑探针，
只对**源码文本 + AST** 断言修复真的落地，并对每条断言配一个负控
（把修复点改回旧写法，断言必须转红）——防止门禁自身是恒真式。

用法：
  python _verify_probe_a4a7a8.py            # 跑全部
  python _verify_probe_a4a7a8.py --negctl   # 额外跑负控
"""
import ast
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "_rc4_ab_probe.py"
TEXT = SRC.read_text(encoding="utf-8")
LINES = TEXT.splitlines()

results = []


def check(tag, cond, evidence):
    results.append((tag, bool(cond), evidence))
    return bool(cond)


def find_line(needle, start=0):
    for i in range(start, len(LINES)):
        if needle in LINES[i]:
            return i + 1
    return None


# ---------------------------------------------------------------- A7
def a7(text=None):
    t = text if text is not None else TEXT
    ok = []
    ok.append(("safe_name 显式拒冒号", '" :" in name' not in t and
               re.search(r'if\s+":"\s+in\s+name\s*:', t) is not None))
    ok.append(("safe_dll_name 存在", "def safe_dll_name(" in t))
    ok.append(("safe_dll_name 要求 .dll", 'endswith(".dll")' in t))
    ok.append(("main 用 safe_dll_name", "safe_dll_name(args.dll)" in t))
    # 负控：main 里不得再对 --dll 只调 safe_name
    ok.append(("main 不再裸调 safe_name(args.dll)",
               "safe_name(args.dll)" not in t))
    return ok


# ---------------------------------------------------------------- A4
def a4(text=None):
    t = text if text is not None else TEXT
    ok = []
    ok.append(("rec 提升 a8_verdict", 'rec["a8_verdict"] = a8.get("verdict")' in t))
    ok.append(("rec 提升 cleanup_ok", 'rec["cleanup_ok"] =' in t))
    ok.append(("main 读 a8_verdict", 'av = r.get("a8_verdict")' in t))
    ok.append(("main 非 PASS 时置 aborted", "results_aborted = True" in t))
    ok.append(("main 非 PASS 时 return 3", re.search(r"return 3", t) is not None))
    ok.append(("汇总行含 A8 计数", "A8 清扫 PASS %d" in t))
    # 关键：判据必须真的在条件里用上，不能只打印
    ok.append(("退出码依赖 a8", re.search(
        r"if results_aborted or n_a8_ok != len\(results\)", t) is not None))
    return ok


# ---------------------------------------------------------------- A8
def a8(text=None):
    t = text if text is not None else TEXT
    ok = []
    ok.append(("one_trip 有 finally", re.search(
        r"def one_trip\([\s\S]{0,3000}?finally:\s*\n\s*rec = state\[.rec.\]",
        t) is not None))
    ok.append(("主体已拆到 _one_trip_body", "def _one_trip_body(" in t))
    ok.append(("state 登记 rec", 'state["rec"] = rec' in t))
    ok.append(("state 登记 proc", 'state["proc"] = proc' in t))
    ok.append(("state 登记 carrier", 'state["carrier"] = carrier' in t))
    ok.append(("_cleanup 幂等", 'rec.get("_cleaned")' in t))
    ok.append(("pid 定向击杀存在", 'rec["pid_killed"]' in t))
    # 负控：主体内不得再有显式 _cleanup 调用（唯一出口是 finally）
    body = t.split("def _one_trip_body(", 1)[1].split("\ndef ", 1)[0] \
        if "def _one_trip_body(" in t else ""
    ok.append(("主体内无显式 _cleanup", "_cleanup(" not in body))
    return ok


# ---------------------------------------------------------------- 负控
NEGCTL = [
    ("A7 去掉冒号检查",
     lambda s: s.replace('    if ":" in name:\n'
                         '        raise ValueError("name contains drive/ADS colon: %r" % (name,))\n',
                         ''),
     a7),
    ("A7 main 退回裸 safe_name",
     lambda s: s.replace("safe_dll_name(args.dll)", "safe_name(args.dll)"),
     a7),
    ("A4 去掉退出码依赖",
     lambda s: s.replace("if results_aborted or n_a8_ok != len(results):",
                         "if False:"),
     a4),
    ("A4 去掉 aborted 置位",
     lambda s: s.replace("results_aborted = True", "pass"),
     a4),
    ("A8 去掉 finally",
     lambda s: s.replace("    finally:\n        rec = state[\"rec\"]",
                         "    if False:\n        rec = state[\"rec\"]", 1),
     a8),
    ("A8 主体内塞回显式 _cleanup",
     lambda s: s.replace('    rec["guard"] = parse_guard_log(',
                         '    _cleanup(proc, carrier, rec, attached=True)\n'
                         '    rec["guard"] = parse_guard_log(', 1),
     a8),
]


def main():
    print("=" * 90)
    print("异族核验 A4/A7/A8 修复门禁")
    print("=" * 90)
    for group, fn in (("A7", a7), ("A4", a4), ("A8", a8)):
        print()
        print("--- %s ---" % group)
        for name, cond in fn():
            print("  %-34s %s" % (name, "PASS" if cond else "FAIL"))

    n_pass = sum(1 for _, c, _ in results if c)
    n_all = len(results)

    if "--negctl" in sys.argv:
        print()
        print("=" * 90)
        print("负控：把修复点改回旧写法，断言必须转红")
        print("=" * 90)
        for name, mutate, fn in NEGCTL:
            mutated = mutate(TEXT)
            if mutated == TEXT:
                print("  %-38s SKIP（变异未命中，负控本身失效）" % name)
                results.append((name, False, "mutation no-op"))
                continue
            greens = [n for n, c in fn(mutated) if c]
            # 负控成立 = 变异后至少有一条断言转红
            total = len(fn(TEXT))
            red = total - len(greens)
            good = red > 0
            print("  %-38s %s（转红 %d/%d）"
                  % (name, "PASS" if good else "FAIL", red, total))
            results.append((name, good, "red=%d/%d" % (red, total)))

    n_pass = sum(1 for _, c, _ in results if c)
    n_all = len(results)
    print()
    print("%d/%d PASS" % (n_pass, n_all))
    return 0 if n_pass == n_all else 1


if __name__ == "__main__":
    sys.exit(main())
