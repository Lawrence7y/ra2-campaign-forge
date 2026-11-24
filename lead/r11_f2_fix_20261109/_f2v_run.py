# -*- coding: utf-8 -*-
"""F2V-03: 独立对跑——30 件 × (原版 r11_scan vs 增强版 r11_scan_plus)。
覆盖率、match、problems/warnings 增量、绑定行 declared 序列一致性，全部自算。
只读保护件；输出 JSON 到本写域 _f2v_run_out.json。"""
import importlib.util
import json
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
W = REPO / "lead" / "r11_f2_fix_20261109"

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

g7 = load("_g7v_pred", REPO / "lead" / "gate_fp7_20261108" / "_g7_predicates.py")
plus = load("_f2_r11plus_v", W / "_f2_r11plus.py")

j = json.loads((REPO / "lead" / "gate_r9r12_20261109" / "_g9_regression_out.json").read_text(encoding="utf-8"))
res = j["results_30"]

out = []
tot = dict(orig_collected=0, plus_collected=0, orig_match=0, plus_match=0,
           orig_problems=0, plus_problems=0, orig_warnings=0, plus_warnings=0,
           bindings=0)
declared_mismatch = 0
for i, r in enumerate(res):
    rel = r["rel"]
    p = REPO / rel
    text = p.read_text(encoding="utf-8")
    d_dir = p.parent
    op, ow, ob = g7.r11_scan(text, d_dir, root=REPO)
    pp, pw, pb = plus.r11_scan_plus(text, d_dir, root=REPO)
    # 绑定行条数与 declared 序列必须逐一相同
    seq_o = [b["declared"] for b in ob]
    seq_p = [b["declared"] for b in pb]
    seq_ok = seq_o == seq_p
    if not seq_ok:
        declared_mismatch += 1
    rec = {
        "idx": i, "rel": rel,
        "orig_verdict_r11": "FAIL" if op else "PASS",
        "plus_verdict_r11": "FAIL" if pp else "PASS",
        "file_verdict_regression": r["verdict"],
        "n_bindings": len(ob), "declared_seq_same": seq_ok,
        "orig_paths": [b["path"] for b in ob],
        "plus_paths": [b.get("path") for b in pb],
        "orig_match": [b["match"] for b in ob],
        "plus_match": [b.get("match") for b in pb],
        "plus_tiers": [b.get("tier") for b in pb],
        "orig_problems": list(op), "plus_problems": list(pp),
        "orig_warnings": list(ow), "plus_warnings": list(pw),
    }
    # 新增 problem 检测（逐条集合差，消息归一）
    extra = [m for m in pp if m not in op]
    rec["new_problems_vs_orig"] = extra
    out.append(rec)
    tot["bindings"] += len(ob)
    tot["orig_collected"] += sum(1 for b in ob if b["path"])
    tot["plus_collected"] += sum(1 for b in pb if b.get("path"))
    tot["orig_match"] += sum(1 for b in ob if b["match"] is True)
    tot["plus_match"] += sum(1 for b in pb if b.get("match") is True)
    tot["orig_problems"] += len(op)
    tot["plus_problems"] += len(pp)
    tot["orig_warnings"] += len(ow)
    tot["plus_warnings"] += len(pw)

(W / "_f2v_run_out.json").write_text(
    json.dumps({"totals": tot, "declared_mismatch_files": declared_mismatch,
                "results": out}, ensure_ascii=False, indent=1), encoding="utf-8")

print("TOTALS:", json.dumps(tot, ensure_ascii=False))
print("declared_mismatch_files:", declared_mismatch)
newp = [r for r in out if r["new_problems_vs_orig"]]
print("files with NEW problems vs original:", len(newp))
for r in newp:
    print("  #%d %s -> %r" % (r["idx"], r["rel"], r["new_problems_vs_orig"]))
flips = [(r["idx"], r["rel"], r["orig_verdict_r11"], r["plus_verdict_r11"]) for r in out if r["orig_verdict_r11"] != r["plus_verdict_r11"]]
print("R11 verdict flips:", flips)
