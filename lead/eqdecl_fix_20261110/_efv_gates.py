# _efv_gates.py — 复核员自己的三关 × 9 案例 harness（复刻 _eq_three_gates.py 判定规则，
# --det 可选检测器、输出只落本写域）
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")

CASES = [
    ("关一", "G1a", "S1 半 A⊆B",
     "lead/layer_identity_20261109/LAYER_IDENTITY.md", 104,
     "TAUTOLOGY_OK", None, "TAUTOLOGY"),
    ("关一", "G1b", "S3 :125 逻辑重言式",
     "lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md", 125,
     "TAUTOLOGY_OK", None, "TAUTOLOGY"),
    ("关一", "G1c", "S12 S3 DEFAULT 恒真兜底",
     "lead/score_decomp_20261109/SCORE_DECOMP.md", 235,
     "TAUTOLOGY_OK", None, "TAUTOLOGY"),
    ("关二", "G2a", "S2 :104 依赖图（正确否定句）",
     "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 104,
     "SUBSTANTIVE_OK", None, "SUBSTANTIVE"),
    ("关二", "G2b", "S4 正确等价式",
     "lead/layer_identity_20261109/LAYER_IDENTITY.md", 128,
     "PASS_QUALIFIED", None, "SUBSTANTIVE"),
    ("关二", "G2c", "S7 Fréchet min q_i 恰取等（定理部分）",
     "lead/keff_calc_20261109/KEFF_CALC.md", 262,
     "SUBSTANTIVE_OK", None, "SUBSTANTIVE"),
    ("关三", "G3a", "S1「决定性集合等式」标签",
     "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 108,
     "FAIL", "F3", "SUBSTANTIVE"),
    ("关三", "G3b", "S5「R12 增量 0 bit」全称",
     "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md", 149,
     "FAIL", "F3", "SUBSTANTIVE"),
    ("关三", "G3c", "S8「38/38」",
     "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 107,
     "FAIL", "F3", "SUBSTANTIVE"),
]


def load_detector(p: pathlib.Path):
    spec = importlib.util.spec_from_file_location("det_" + p.stem.replace("-", "_"), p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--det", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    eq = load_detector(pathlib.Path(args.det))

    cache: dict[str, dict] = {}
    rows = []
    for gate, cid, scase, relp, line, exp_v, exp_f, exp_cat in CASES:
        if relp not in cache:
            cache[relp] = eq.scan_file(ROOT / relp)
        rec = cache[relp]
        hit = None
        for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
            for r in rec[bucket]:
                if r["line"] == line:
                    hit = r
                    break
            if hit:
                break
        if hit is None:
            rows.append({"gate": gate, "case": cid, "file:line": f"{relp}:{line}",
                         "actual": "NO_ANCHOR_RECORD", "passed": False})
            continue
        act_v, act_f, act_cat = hit["verdict"], hit["failure_type"], hit["category"]
        if gate == "关一":
            ok = (act_cat == "TAUTOLOGY" and act_f is None and act_v == "TAUTOLOGY_OK")
        elif gate == "关二":
            ok = (act_f is None and act_v in
                  ("SUBSTANTIVE_OK", "PASS_QUALIFIED", "CORRECTLY_SCOPED", "SKIP"))
        else:
            ok = (act_v == "FAIL" and act_f == "F3")
        if exp_cat is not None and act_cat != exp_cat:
            ok = False
        rows.append({
            "gate": gate, "case": cid, "file:line": f"{relp}:{line}",
            "expected": f"{exp_v}/{exp_f or '-'}/{exp_cat}",
            "actual": f"{act_v}/{act_f or '-'}/{act_cat}",
            "actual_verdict": act_v, "actual_failure_type": act_f, "actual_category": act_cat,
            "skip_reason": hit.get("skip_reason"), "flags": hit["flags"], "passed": ok,
        })

    matrix = {}
    for gate in ("关一", "关二", "关三"):
        gr = [r for r in rows if r["gate"] == gate]
        matrix[gate] = {"passed": sum(1 for r in gr if r["passed"]),
                        "total": len(gr), "all_passed": all(r["passed"] for r in gr)}
    out = {
        "tag": args.tag, "detector": str(args.det),
        "n_cases": len(rows), "n_passed": sum(1 for r in rows if r["passed"]),
        "n_failed": sum(1 for r in rows if not r["passed"]),
        "gates": matrix, "rows": rows,
    }
    dest = pathlib.Path(args.out)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"tag": args.tag, "n_passed": out["n_passed"], "n_cases": out["n_cases"],
                      "gates": matrix, "written": str(dest)}, ensure_ascii=False))
    return 0 if out["n_failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
