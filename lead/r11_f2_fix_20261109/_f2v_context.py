# -*- coding: utf-8 -*-
"""F2V-02: 对 30 件全量重跑原版 r11_scan，定位每条绑定行，打印绑定行±2 行原文，
供独立核对 F2-a/b/c/d 形态归类。只读，不改任何保护件。"""
import importlib.util
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
G7 = REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
spec = importlib.util.spec_from_file_location("_g7v", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

j = json.loads((REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json").read_text(encoding="utf-8"))
res = j["results_30"]

BIND = g7.BIND_RE
bn = 0
for i, r in enumerate(res):
    rel = r["rel"]
    p = REPO / rel
    text = p.read_text(encoding="utf-8")
    d_dir = p.parent
    probs, warns, bindings = g7.r11_scan(text, d_dir, root=REPO)
    matches = list(BIND.finditer(text))
    lines = text.splitlines()
    for m, b in zip(matches, bindings):
        bn += 1
        lineno = text.count("\n", 0, m.start()) + 1
        print("=== #%d %s bind#%d L%d orig_path=%r" % (i, rel, bn, lineno, b["path"]))
        for ln in range(max(1, lineno - 2), min(len(lines), lineno + 2) + 1):
            mark = ">>" if ln == lineno else "  "
            print("%s L%-4d %s" % (mark, ln, lines[ln - 1][:220]))
print("TOTAL_BINDINGS", bn)
