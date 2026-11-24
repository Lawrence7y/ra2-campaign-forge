# -*- coding: utf-8 -*-
"""_rjv_step1.py — 独立复核第①②步：七件指纹实算 + 独立双轨重判（不采信 _rj_* 结论）。
只写 lead/gate_rejudge32_20261109/_rjv_*；只读其它一切。python -I -X utf8 + 绝对路径。
"""
import hashlib
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_rejudge32_20261109"

SEVEN = [
    "lead/gate_doc_name_fix_20261109/_dn_regate_out.json",
    "lead/gate_doc_name_fix_20261109/GATE_DOC_NAME_FIX.md",
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/gate_r9r12_20261109/_g9_gate.py",
    "lead/r33e_merge_20261109/_re_linked.py",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]
EXPECTED = {
    "lead/gate_doc_name_fix_20261109/_dn_regate_out.json": ("0d129e409ca5ab744891abccd85a0c0ca0c164ddea8620de634de5079fa8f096", 22133),
    "lead/gate_doc_name_fix_20261109/GATE_DOC_NAME_FIX.md": ("a1006e06836e902ec462186676ef66c4d6301ab8aee58234c05add9b946c46cd", 41361),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_r9r12_20261109/_g9_gate.py": ("a83081eeffc56e830c84ebcfe945114b5e2ac1082467ed04d97634912dacd2a6", 11623),
    "lead/r33e_merge_20261109/_re_linked.py": ("7ca339c6beb728f488903e1b0c748708accf45cd5e3bce45d532290c0c755b52", 19481),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

out = {"step": "independent review step1", "fingerprints": {}, "regate_fresh": {}, "double_track": {}}

# ---------- ① 七件指纹，hashlib 独立实算 ----------
for rel in SEVEN:
    p = ROOT / rel
    b = p.read_bytes()
    sha, n = hashlib.sha256(b).hexdigest(), len(b)
    exp_sha, exp_n = EXPECTED[rel]
    out["fingerprints"][rel] = {
        "sha256": sha, "bytes": n, "expected_sha256": exp_sha,
        "expected_bytes": exp_n, "match": (sha == exp_sha and n == exp_n),
    }

# ---------- ②-a 独立重跑产物（由 Bash 直接跑 _dn_regate_domains.py 重定向到 _rjv_regate_fresh.json） ----------
fresh_path = WD / "_rjv_regate_fresh.json"
baseline_path = ROOT / SEVEN[0]
fresh_bytes = fresh_path.read_bytes()
baseline_bytes = baseline_path.read_bytes()
d = json.loads(fresh_bytes.decode("utf-8"))
rows = d["rows"]
nonempty = [x["domain"] for x in rows if x.get("gateProblems")]
zero_bind = [x["domain"] for x in rows if x.get("bindings") == 0]
out["regate_fresh"] = {
    "fresh_sha256": hashlib.sha256(fresh_bytes).hexdigest(), "fresh_bytes": len(fresh_bytes),
    "delivered_baseline_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
    "delivered_baseline_bytes": len(baseline_bytes),
    "identical_to_delivered": fresh_bytes == baseline_bytes,
    "domains": len(rows),
    "gateProblems_nonempty_count": len(nonempty), "gateProblems_nonempty": sorted(nonempty),
    "bindings_zero_count": len(zero_bind), "bindings_zero": sorted(zero_bind),
    "problem_entries_total": sum(len(x.get("gateProblems", [])) for x in rows),
}

# ---------- ②-b 独立双轨：自己实现，不 import 任何 _rj_* 结论 ----------
G7 = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"
gb = G7.read_bytes()
assert hashlib.sha256(gb).hexdigest() == EXPECTED[SEVEN[2]][0] and len(gb) == EXPECTED[SEVEN[2]][1], "predicate fingerprint mismatch"
spec = importlib.util.spec_from_file_location("_rjv_g7", G7)
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

BIND_LINE_RE = re.compile(r"被核对象 SHA256\s*=\s*`?[0-9a-fA-F]{64}`?")
dt_rows = []
for x in rows:
    banned = x.get("params", {}).get("banned", []) or []
    p = ROOT / x["domain"].rstrip("/") / x["main"]
    rec = {"domain": x["domain"], "main": x["main"], "banned": banned,
           "gateProblems": x.get("gateProblems", []), "bindings": x.get("bindings")}
    if not p.is_file():
        rec["state"] = "MAIN_MISSING"
        dt_rows.append(rec)
        continue
    t = p.read_text(encoding="utf-8", errors="replace")
    rec["state"] = "OK"
    rec["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
    naive = [tok for tok in banned if tok in t] if banned else []
    if banned:
        p10, w10, h10 = g7.r10_scan(t, banned)
        p12, h12 = g7.r12_scan(t, banned)
        kinds = {}
        for h in h10:
            kinds[h["kind"]] = kinds.get(h["kind"], 0) + 1
        rec.update({"naiveHits": naive, "naiveP": len(naive),
                    "r10Problems": p10, "r10P": len(p10), "r10Warnings": len(w10),
                    "r10Kinds": kinds, "r10Occurrences": len(h10),
                    "r12Problems": p12, "r12P": len(p12)})
    else:
        rec.update({"naiveHits": [], "naiveP": 0, "r10Problems": [], "r10P": 0,
                    "r10Warnings": 0, "r10Kinds": {}, "r10Occurrences": 0,
                    "r12Problems": [], "r12P": 0})
    rec["bindingLines"] = len(BIND_LINE_RE.findall(t))
    rec["any_track_hit"] = bool(naive) or rec["r10P"] > 0 or rec["r12P"] > 0
    dt_rows.append(rec)

out["double_track"] = {
    "predicate_sha256": hashlib.sha256(gb).hexdigest(), "predicate_bytes": len(gb),
    "baseline_sha256": hashlib.sha256(baseline_bytes).hexdigest(),
    "domains": len(dt_rows),
    "with_banned_list": sum(1 for r in dt_rows if r["banned"]),
    "hit_on_any_track": sum(1 for r in dt_rows if r["any_track_hit"]),
    "r12_nonzero_domains": [r["domain"] for r in dt_rows if r.get("r12P", 0) > 0],
    "bindingLines_zero_domains": [r["domain"] for r in dt_rows if r.get("bindingLines", -1) == 0],
    "per_domain": [{k: v for k, v in r.items() if k in (
        "domain", "main", "naiveP", "r10P", "r12P", "r10Warnings", "r10Occurrences",
        "r10Kinds", "bindingLines", "any_track_hit", "gateProblems", "bindings")}
        for r in dt_rows],
}

(WD / "_rjv_step1_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({
    "fp_all_match": all(v["match"] for v in out["fingerprints"].values()),
    "fp_details": [(k.split("/")[-1], v["sha256"], v["bytes"], v["match"]) for k, v in out["fingerprints"].items()],
    "regate": out["regate_fresh"],
    "double_track": {k: v for k, v in out["double_track"].items() if k != "per_domain"},
}, ensure_ascii=False, indent=1))
