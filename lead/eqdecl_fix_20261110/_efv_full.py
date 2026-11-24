# _efv_full.py — 复核员自己的全量跑 harness（复刻 _eq_full_run.py 的文件集与 45 行清单，
# 但 --det 可选检测器、输出只落本写域；绝不写只读目录）
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
OUTDIR = ROOT / "lead/eqdecl_fix_20261110"

READ_DIRS = [
    "lead/tautology_audit_20261109",
    "lead/layer_identity_20261109",
    "lead/metric_audit_20261109",
    "lead/keff_calc_20261109",
    "lead/evidence_indep_20261109",
    "lead/gate_pipeline_20261109",
    "lead/score_decomp_20261109",
    "lead/comparability_20261109",
]
LISTED_LINES = {
    "lead/layer_identity_20261109/LAYER_IDENTITY.md": [
        1, 13, 22, 26, 87, 104, 110, 112, 116, 122, 126, 127, 128, 182, 189,
        197, 200, 208, 213, 216, 223, 225, 226, 228, 233, 234, 242, 273, 279,
        304, 326, 337, 338, 339, 365, 372, 376, 393, 400, 409, 414],
    "lead/keff_calc_20261109/KEFF_CALC.md": [340],
    "lead/score_decomp_20261109/SCORE_DECOMP.md": [135, 239],
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md": [158],
}


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

    md_files = sorted({p for d in READ_DIRS for p in (ROOT / d).glob("*.md")})
    all_recs = [eq.scan_file(p) for p in md_files]

    total_findings = sum(r["n_findings"] for r in all_recs)
    total_anchors = sum(r["n_anchors"] for r in all_recs)
    total_skips = sum(r["n_skips"] for r in all_recs)
    total_undec = sum(r["n_undecidables"] for r in all_recs)
    total_taut = sum(r["n_tautology_ok"] for r in all_recs)
    total_passes = sum(r["n_passes"] for r in all_recs)
    by_ftype: Counter = Counter()
    for r in all_recs:
        by_ftype.update(r["findings_by_type"])

    rec_by_file = {r["file"]: r for r in all_recs}
    listed_rows = []
    for relp, lines in LISTED_LINES.items():
        r = rec_by_file.get(relp)
        all_hits = (r["findings"] + r["passes"] + r["tautology_ok"] +
                    r["skips"] + r["undecidables"]) if r else []
        idx = {x["line"]: x for x in all_hits}
        for n in lines:
            h = idx.get(n)
            listed_rows.append({
                "file:line": f"{relp}:{n}",
                "anchored": h is not None,
                "verdict": h["verdict"] if h else "NOT_AN_ANCHOR",
                "failure_type": h["failure_type"] if h else None,
                "category": h["category"] if h else None,
                "skip_reason": h.get("skip_reason") if h else None,
                "text": (h["text"] if h else None),
            })
    n_anchored = sum(1 for x in listed_rows if x["anchored"])
    n_listed_findings = sum(1 for x in listed_rows if x["verdict"] == "FAIL")

    # 全锚点迁移矩阵底稿：每条记录 (file, line, verdict, ftype, skip_reason, category)
    all_records = []
    for r in all_recs:
        for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
            for x in r[bucket]:
                all_records.append({
                    "file": x["file"], "line": x["line"], "bucket": bucket,
                    "verdict": x["verdict"], "failure_type": x.get("failure_type"),
                    "skip_reason": x.get("skip_reason"), "category": x["category"],
                    "text": x["text"],
                })

    out = {
        "tag": args.tag,
        "detector": str(args.det),
        "scope": {"read_dirs": READ_DIRS, "n_md_files": len(md_files),
                  "md_files": [eq.rel(p) for p in md_files]},
        "totals": {
            "n_files": len(all_recs), "n_anchors": total_anchors,
            "n_findings": total_findings, "n_tautology_ok": total_taut,
            "n_passes": total_passes, "n_skips": total_skips,
            "n_undecidables": total_undec,
        },
        "findings_by_type": dict(by_ftype),
        "by_file": {r["file"]: {
            "n_anchors": r["n_anchors"], "n_findings": r["n_findings"],
            "findings_by_type": r["findings_by_type"],
            "n_tautology_ok": r["n_tautology_ok"], "n_passes": r["n_passes"],
            "n_skips": r["n_skips"], "n_undecidables": r["n_undecidables"],
            "skip_by_reason": r["skip_by_reason"],
        } for r in all_recs},
        "listed_45": {"n_rows": len(listed_rows), "n_anchored": n_anchored,
                      "n_findings": n_listed_findings, "rows": listed_rows},
        "all_records": all_records,
        "findings_full": [
            {"file": x["file"], "line": x["line"], "failure_type": x.get("failure_type"),
             "category": x["category"], "text": x["text"],
             "window_lines": None}
            for r in all_recs for x in r["findings"]
        ],
    }
    dest = pathlib.Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"tag": args.tag, "totals": out["totals"],
                      "findings_by_type": out["findings_by_type"],
                      "listed_45": {"n_anchored": n_anchored, "n_findings": n_listed_findings},
                      "written": str(dest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
