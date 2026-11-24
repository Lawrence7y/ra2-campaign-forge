# -*- coding: utf-8 -*-
"""_ci_merged_projection.py — 用 merged 候选副本重跑 30 件，投影 compare_out 形态。

只读保护件；产出只写临时目录（tempfile.mkdtemp）。不改 _f2_compare.py /
_f2v_run.py / _f2_compare_out.json / 任何既有产物。零真机、零采样代码。
复刻 _f2_compare.py:35-71 的聚合表达式，仅把 r11_scan_plus 换成候选副本。
"""
import importlib.util
import json
import pathlib
import tempfile

REPO = pathlib.Path(r"D:\Project\ra2-campaign-forge")
R11 = REPO / "lead" / "r11_f2_fix_20261109"
CAND = REPO / "lead" / "merged_contract_20261109" / "_mk_r11plus_candidate.py"
G7 = REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
G9 = REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json"
SRC = R11 / "_f2_compare_out.json"


def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


g7 = load("_ci_g7", G7)
cand = load("_ci_cand", CAND)
base = json.loads(SRC.read_text(encoding="utf-8"))
reg = json.loads(G9.read_text(encoding="utf-8"))["results_30"]
assert len(reg) == len(base["results"]) == 30

# 用候选 bindings 替换 plus.bindings / plus.warnings / plus.verdict（保持其它键逐字）
doc = json.loads(SRC.read_text(encoding="utf-8"))
tot = {k: 0 for k in base["totals"]}
changed_docs = changed_bindings = 0
for r, row in zip(reg, doc["results"]):
    p = pathlib.Path(r["file"])
    text = p.read_bytes().decode("utf-8")
    d_dir = p.parent
    o_prob, o_warn, o_bind = g7.r11_scan(text, d_dir, root=REPO)
    n_prob, n_warn, n_bind = cand.r11_scan_plus(text, d_dir, root=REPO)
    if row["plus"]["bindings"] != n_bind:
        changed_docs += 1
        changed_bindings += sum(1 for a, b in zip(row["plus"]["bindings"], n_bind) if a != b)
    row["plus"]["bindings"] = n_bind
    row["plus"]["warnings"] = n_warn
    row["plus"]["problems"] = n_prob
    row["plus"]["verdict"] = "FAIL" if n_prob else "PASS"
    row["plus_overall"] = "FAIL" if (n_prob or row["other_predicates_fail"]) else "PASS"
    tot["bindings"] += len(o_bind)
    tot["orig_path"] += sum(1 for b in o_bind if b["path"])
    tot["plus_path"] += sum(1 for b in n_bind if b.get("path"))
    tot["orig_match"] += sum(1 for b in o_bind if b["match"] is True)
    tot["plus_match"] += sum(1 for b in n_bind if b.get("match") is True)
    tot["orig_problems"] += len(o_prob)
    tot["plus_problems"] += len(n_prob)
doc["totals"] = tot

tmp = pathlib.Path(tempfile.mkdtemp(prefix="_ci_merged_"))
out = tmp / "merged_projection.json"
out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
print("TEMP OUT:", out)
print("BEFORE:", json.dumps(base["totals"], ensure_ascii=False, sort_keys=True))
print("AFTER :", json.dumps(tot, ensure_ascii=False, sort_keys=True))
print("DRIFT :", {k: (base["totals"][k], tot[k]) for k in tot if base["totals"][k] != tot[k]})
print("changed_docs=%d changed_bindings=%d" % (changed_docs, changed_bindings))
rows = [(i, k, b) for i, r in enumerate(doc["results"])
        for k, b in enumerate(r["plus"]["bindings"])]
from collections import Counter
print("TIER AFTER:", dict(Counter(b.get("tier") for _, _, b in rows)))
print("M (match_no_path) =", sum(1 for _, _, b in rows
                                 if not b.get("path") and b.get("match") is True))
print("E (merged_tier)   =", sum(1 for _, _, b in rows
                                 if b.get("tier") == "SAMEDOC_LINK_EQ"))
print("U (unique_tier)   =", sum(1 for _, _, b in rows
                                 if b.get("tier") == "SAMEDOC_LINK"))
print("__PATH__", str(out))
