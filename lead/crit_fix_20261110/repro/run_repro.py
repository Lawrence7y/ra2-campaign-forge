# -*- coding: utf-8 -*-
"""Load _ec_criterion.py via importlib and print class/verdict/e for 4 repro files."""
import importlib.util
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[3]
CRIT = ROOT / "lead" / "exit_criterion_20261110" / "_ec_criterion.py"
HERE = pathlib.Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location("_ec_criterion_repro", CRIT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

for name in ("rc1_guard_ifexp.py", "rc2_subscript_append.py",
             "rc3_parse_tolerance.py", "rc4_stdout_write.py"):
    p = HERE / name
    r = mod.analyze_file(str(p), "lead/crit_fix_20261110/repro/" + name)
    print(name)
    print("  class   =", r["class"])
    print("  verdict =", r["verdict"])
    print("  e       =", r["e"])
    print("  facts   =", r["facts"])
    for t in r["reasons"]:
        print("  reason  =", t)
    print()
