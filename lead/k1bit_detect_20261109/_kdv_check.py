# -*- coding: utf-8 -*-
"""_kdv_check.py -- independent verification for the k1bit detector review.

READ-ONLY outside lead/k1bit_detect_20261109/.  Writes only _kdv_* outputs there.
No dynamic sampling / process inspection; ast + hashlib + re only.

Checks requested by the review ask, each runnable via:
  python -I -X utf8 D:/Project/ra2-campaign-forge/lead/k1bit_detect_20261109/_kdv_check.py D:/Project/ra2-campaign-forge <step>

Steps:
  fp        recompute the orchestrator's 10 fingerprints (hashlib)
  ast       independently walk ast for any() argument node shapes of 4 gates
  screens   recompute L1/L2/L3/strict-combo confusion matrices over 173 files
  verify    rerun _kd_detect.py / _kd_selftest.py / _kd_literal_vs_semantic.py
  semantics probe the semantic predicate with independently-written fixtures
  boundary check no modification of protected artifacts (fingerprints + git)
"""
import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

WD_NAME = "lead/k1bit_detect_20261109"
BASE = {
    "lead/check_family_20261109/CHECK_FAMILY_LINEAGE.md": ("e5098b23732141df0fcb48631cab5642cb4ec054f47564a2a0233fa6e10539f8", 82856),
    "lead/check_family_20261109/_cf_detect_out.json": ("17e83a81ecf0cca951825d3191bb0772011de1af3269d793922a8db068e5c3c2", 130498),
    "lead/check_family_20261109/_cf_census_out.json": ("e5edea52c3f1959796c8132e7f4d04418c9704f992a59df84ec189d564b800fa", 149737),
    "lead/check_family_20261109/_cf_detect.py": ("832355993a2b0f50bbc77c85f52531862d62fc01eab511cd29d78d06c860ffc1", 7587),
    "lead/d27_ruling_20261106/check_d27.py": ("3b769d7c64c2725100186439725198dbc134a277914e2cb2e9b0af844fe7671c", 3764),
    "lead/d28_ruling_20261106/check_d28.py": ("5b42a34a40046d7a705776002d7aebe8ffda34248849a75b628d40712d9df268", 4539),
    "lead/d29_ruling_20261106/check_d29.py": ("2a50b09adff555dbce4c5740a2af78b779876cad771b6fdf887ba3c0dc780f14", 3906),
    "lead/d30_ruling_20261106/check_d30.py": ("6cb737963fc62a0e045f51247b4fa57ef190acb0b524da3aa6b7713fd05ee9fd", 3926),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
FOUR = ["lead/d27_ruling_20261106/check_d27.py",
        "lead/d28_ruling_20261106/check_d28.py",
        "lead/d29_ruling_20261106/check_d29.py",
        "lead/d30_ruling_20261106/check_d30.py"]


def sha(rel, root):
    raw = (root / rel).read_bytes()
    return hashlib.sha256(raw).hexdigest(), len(raw), raw


def step_fp(root, wd):
    rows = []
    mismatches = []
    for rel, (h0, b0) in BASE.items():
        h, b, _ = sha(rel, root)
        ok = (h == h0 and b == b0)
        rows.append(dict(rel=rel, sha256=h, bytes=b, expected_sha=h0,
                         expected_bytes=b0, ok=ok))
        if not ok:
            mismatches.append(rel)
        print(("OK  " if ok else "MISMATCH "), rel, h, b)
    out = dict(n=len(rows), mismatches=mismatches, rows=rows)
    (wd / "_kdv_fp_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("FP_RESULT n=%d mismatches=%d %s" % (len(rows), len(mismatches), mismatches))


def step_ast(root, wd):
    """Independent ast.walk: enumerate every any() call, its first arg's node type."""
    lit = re.compile(r"any\([^)]*for[^)]*in")
    res = {}
    for rel in FOUR:
        _, _, raw = sha(rel, root)
        text = raw.decode("utf-8-sig", errors="replace")
        tree = ast.parse(text)
        calls = []
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "any":
                a = n.args[0] if n.args else None
                calls.append(dict(line=n.lineno,
                                  arg_type=type(a).__name__ if a is not None else "NONE",
                                  arg_unparse=ast.unparse(a)[:200] if a is not None else "",
                                  n_args=len(n.args)))
        n_regex = len(lit.findall(text))
        res[rel] = dict(any_calls=calls, regex_generator_form_hits=n_regex)
        print(rel, "regex_hits=", n_regex)
        for c in calls:
            print("   line=%s arg=%s n_args=%s :: %s" % (c["line"], c["arg_type"], c["n_args"], c["arg_unparse"]))
    (wd / "_kdv_ast_out.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("AST_RESULT four_files=%d" % len(res))


def main():
    root = Path(sys.argv[1]).resolve()
    wd = root / WD_NAME
    step = sys.argv[2] if len(sys.argv) > 2 else "fp"
    globals()["step_" + step](root, wd)


if __name__ == "__main__":
    main()
