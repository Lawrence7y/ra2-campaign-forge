# -*- coding: utf-8 -*-
"""_kdv_recompute.py -- independent, from-scratch literal-screen recomputation.

Ground truth is the ORCHESTRATOR's 40-file confirmed set (_cf_detect_out.json),
NOT the new detector's output; this deliberately avoids circular validation.
The 173-file list comes from _cf_filelist.txt.  Reads bytes directly.

Writes only _kdv_recompute_out.json in the write domain.
"""
import json
import re
import sys
from pathlib import Path

WD_NAME = "lead/k1bit_detect_20261109"
L1 = re.compile(r"any\([^)]*for[^)]*in")
L3_ANY = re.compile(r"\bany\s*\(")
L3_PASS = re.compile(r"^\s*print\(.*PASS")
PASS_LITERAL = re.compile(r"^\s*print\(\s*[\"']PASS")
FOUR = ["lead/d27_ruling_20261106/check_d27.py",
        "lead/d28_ruling_20261106/check_d28.py",
        "lead/d29_ruling_20261106/check_d29.py",
        "lead/d30_ruling_20261106/check_d30.py"]


def orch_any_line(s):
    if "any(" not in s or " for " not in s:
        return False
    head, _, tail = s.partition(" for ")
    return " in " in head and " in " in tail


def main():
    root = Path(sys.argv[1]).resolve()
    wd = root / WD_NAME
    rels = [ln.strip()[2:] if ln.strip().startswith("./") else ln.strip()
            for ln in (root / "lead/check_family_20261109/_cf_filelist.txt")
            .read_text(encoding="utf-8").splitlines() if ln.strip()]
    cf = json.loads((root / "lead/check_family_20261109/_cf_detect_out.json")
                    .read_text(encoding="utf-8"))
    truth = set(cf["confirmed"])
    cen = json.loads((root / "lead/check_family_20261109/_cf_census_out.json")
                     .read_text(encoding="utf-8"))["summary"]
    combo = set(cen["combo_orchany_passliteral"])
    rows = []
    for rel in rels:
        raw = (root / rel).read_bytes()
        text = raw.decode("utf-8-sig", errors="replace")
        lines = text.splitlines()
        rows.append(dict(
            rel=rel, truth=rel in truth,
            L1=bool(L1.search(text)),
            L2=any(orch_any_line(s.strip()) for s in lines),
            L3=(bool(L3_ANY.search(text)) and any(L3_PASS.match(s) for s in lines)),
            combo=rel in combo,
            # for diagnostic: strict combo recomputed from raw text too
            L2_own=any(orch_any_line(s.strip()) for s in lines),
            pass_literal=any(PASS_LITERAL.match(s) for s in lines),
            combo_own=any(orch_any_line(s.strip()) for s in lines) and
                      any(PASS_LITERAL.match(s) for s in lines),
        ))

    def mat(key, hits=None):
        pred = {r["rel"] for r in rows if r[key]} if hits is None else hits
        tp, fn, fp = len(truth & pred), len(truth - pred), len(pred - truth)
        tn = len(set(rels) - truth - pred)
        return dict(n_hits=len(pred), tp=tp, fn=fn, fp=fp, tn=tn,
                    fn_rate=fn / (tp + fn) if tp + fn else None,
                    fp_rate=fp / (tp + fp) if tp + fp else None,
                    misses_confirmed=sorted(truth - pred),
                    false_positives=sorted(pred - truth))

    res = dict(n=len(rels), n_truth=len(truth),
               truth_source="_cf_detect_out.json:confirmed (orchestrator, 40)",
               L1=mat("L1"), L2=mat("L2"), L3=mat("L3"),
               combo_census=mat("combo"), combo_own=mat("combo_own"),
               combo_own_diff=sorted(combo ^ {r["rel"] for r in rows if r["combo_own"]}),
               four={f: {k: next(r for r in rows if r["rel"] == f)[k]
                         for k in ("truth", "L1", "L2", "L3", "combo", "combo_own")}
                     for f in FOUR})
    (wd / "_kdv_recompute_out.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print("n=%d truth=%d" % (res["n"], res["n_truth"]))
    for k in ("L1", "L2", "L3", "combo_census", "combo_own"):
        v = res[k]
        print("%-14s hits=%-3d TP=%-3d FN=%-3d FP=%-3d TN=%-3d fn_rate=%s fp_rate=%s"
              % (k, v["n_hits"], v["tp"], v["fn"], v["fp"], v["tn"],
                 v["fn_rate"], v["fp_rate"]))
    print("combo_own_vs_census_diff=", res["combo_own_diff"])
    print("FOUR:")
    for f, v in res["four"].items():
        print(" ", f, v)
    print("four_hits L1=%d L2=%d L3=%d combo=%d" % (
        sum(v["L1"] for v in res["four"].values()),
        sum(v["L2"] for v in res["four"].values()),
        sum(v["L3"] for v in res["four"].values()),
        sum(v["combo"] for v in res["four"].values())))
    for k in ("L1", "L2", "L3", "combo_census"):
        print("MISS", k, res[k]["misses_confirmed"])
    print("WROTE", (wd / "_kdv_recompute_out.json").as_posix())


if __name__ == "__main__":
    main()
