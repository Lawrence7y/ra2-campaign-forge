# -*- coding: utf-8 -*-
"""_run_controls.py — 用指定判据模块跑 7 件正控 + 3 件负控，输出 JSON。

用法（python -I -X utf8）：
  python -I -X utf8 lead/e3_fix2_20261110/_run_controls.py before
  python -I -X utf8 lead/e3_fix2_20261110/_run_controls.py after

判据模块经 importlib 以绝对路径加载；只读被检脚本，不执行它们。
结果写到本写域 _before.json / _after.json。
"""
import importlib.util
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

BEFORE_CRIT = os.path.join(ROOT, "lead", "crit_fix_20261110", "_ec_criterion_fixed.py")
AFTER_CRIT = os.path.join(HERE, "_ec_criterion_fixed2.py")

CONTROLS = [
    "lead/d27_ruling_20261106/check_d27.py",
    "lead/d28_ruling_20261106/check_d28.py",
    "lead/d29_ruling_20261106/check_d29.py",
    "lead/d30_ruling_20261106/check_d30.py",
    "lead/goal1_a8_fix_20261022/VERIFY_A8.py",
    "lead/dtrigger_compare_20261107/_check_dtrigger.py",
    "lead/w2_samecause_20261109/_w2w_fp9.py",
]
NEGCTLS = [
    "lead/e3_fix2_20261110/negctl/neg1_pass.py",
    "lead/e3_fix2_20261110/negctl/neg2_print.py",
    "lead/e3_fix2_20261110/negctl/neg3_return_none.py",
]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "after"
    crit = BEFORE_CRIT if which == "before" else AFTER_CRIT
    EC = load(crit, "_ec_criterion_" + which)
    rows = []
    print("criterion =", crit)
    print("-" * 110)
    for rel in CONTROLS + NEGCTLS:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        r = EC.analyze_file(p, rel)
        e = r.get("e") or {}
        row = {"rel": rel, "class": r["class"], "verdict": r["verdict"], "e": e,
               "reasons": [list(t) for t in r["reasons"]], "facts": r.get("facts")}
        rows.append(row)
        efmt = "/".join(str(e.get(k, "-")) for k in ("E1", "E2", "E3", "E4")) if e else "-"
        print("%-9s %-9s %-34s %s" % (r["class"], r["verdict"], efmt, rel))
        for code, loc, detail in r["reasons"]:
            if code == "E3":
                print("      E3 @ %-62s %s" % (loc, detail[:150]))
    out = os.path.join(HERE, "_%s.json" % which)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"criterion": crit, "rows": rows}, f, ensure_ascii=False, indent=1)
    print("-" * 110)
    print("written:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
