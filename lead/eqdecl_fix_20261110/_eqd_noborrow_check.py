# -*- coding: utf-8 -*-
"""_eqd_noborrow_check.py — 撰写员独立复核【复核】反例实验（noborrow 变体）：
fixed(_ef_detector.py) vs noborrow(_efv_detector_noborrow.py) 的 FAIL 迁移 +
TA:642 / MC:109 / G3c:107 三个关键锚点。只读；输出到终端。
python -I -X utf8 _eqd_noborrow_check.py
"""
import importlib.util
import pathlib

ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
HERE = ROOT / "lead/eqdecl_fix_20261110"
FILES = [
    "lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md",
    "lead/tautology_audit_20261109/_ta_TAUTOLOGY_AUDIT_20261109.md",
    "lead/layer_identity_20261109/LAYER_IDENTITY.md",
    "lead/layer_identity_20261109/_li_LAYER_IDENTITY_PROOF_20261109.md",
    "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md",
    "lead/metric_audit_20261109/_ma_METRIC_AUDIT.md",
    "lead/keff_calc_20261109/KEFF_CALC.md",
    "lead/keff_calc_20261109/_ke_REPORT.md",
    "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md",
    "lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md",
    "lead/gate_pipeline_20261109/_gp_DESIGN.md",
    "lead/score_decomp_20261109/SCORE_DECOMP.md",
    "lead/score_decomp_20261109/_sd_report.md",
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md",
    "lead/comparability_20261109/_cmp_AUDIT_20261109.md",
]


def load(p, name):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


eqf = load(HERE / "_ef_detector.py", "eq_fixed")
eqn = load(HERE / "_efv_detector_noborrow.py", "eq_noborrow")


def fails(eq):
    out = {}
    for relp in FILES:
        rec = eq.scan_file(ROOT / relp)
        for r in rec["findings"]:
            out[(relp, r["line"])] = r["failure_type"]
    return out


ff = fails(eqf)
fn = fails(eqn)
new_fail = sorted(set(fn) - set(ff))
gone_fail = sorted(set(ff) - set(fn))
switch = sorted(k for k in set(ff) & set(fn) if ff[k] != fn[k])
print("fixed FAIL rows:", len(ff), " noborrow FAIL rows:", len(fn))
print("NEW FAIL (fixed->noborrow 新增):", len(new_fail))
for k in new_fail[:10]:
    print("   ", k[0].split("/")[-1] + ":" + str(k[1]), fn[k])
print("FAIL 消解:", len(gone_fail))
print("FAIL 换型:", len(switch), [(k[0].split("/")[-1] + ":" + str(k[1]), ff[k] + "->" + fn[k]) for k in switch])
for relp, line, tag in [
    ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md", 642, "TA:642"),
    ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 109, "MC:109"),
    ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md", 107, "G3c:107"),
]:
    rec_n = eqn.scan_file(ROOT / relp)
    v = None
    for b in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
        for r in rec_n[b]:
            if r["line"] == line:
                v = (b, r["verdict"], r["failure_type"])
    print(tag, "noborrow ->", v)
