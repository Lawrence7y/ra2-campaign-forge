# -*- coding: utf-8 -*-
"""
_ef_diff45.py — 修复前 vs 修复后 逐行对比（第三步验收核心件）。
数据源：两版检测器（原件 + 修版）对 15 件 .md 现场 scan_file（避免 _ef_full_out.json
里 per_file_full 只存 findings、skips 截断 20 条的不完整 bucket）。
(a) 编排方清点 45 行逐行：before → after（5 行 FAIL 焦点行给机制）。
(b) 全部锚点迁移矩阵；「新增 FAIL」回归检查必须 = 0。
(c) tautology_ok 流失行逐行；undecidables 变化归因；findings 收敛逐行归因。
(d) 围栏残留：围栏外锚点的 [lo,hi] 窗口与围栏区间重叠统计。
运行： python -I -X utf8 <本文件>
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
from collections import Counter

HERE = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_fix_20261110")
ROOT = pathlib.Path(r"D:/Project/ra2-campaign-forge")
ORIG_JSON = pathlib.Path(r"D:/Project/ra2-campaign-forge/lead/eqdecl_gate_20261109/_eq_full_out.json")


def load(p: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


eq_b = load(ROOT / "lead/eqdecl_gate_20261109/_eq_detector.py", "_eq_detector_before")
eq_a = load(HERE / "_ef_detector.py", "_ef_detector_after")

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

LISTED_45 = {
    "lead/layer_identity_20261109/LAYER_IDENTITY.md": [
        1, 13, 22, 26, 87, 104, 110, 112, 116, 122, 126, 127, 128, 182, 189,
        197, 200, 208, 213, 216, 223, 225, 226, 228, 233, 234, 242, 273, 279,
        304, 326, 337, 338, 339, 365, 372, 376, 393, 400, 409, 414],
    "lead/keff_calc_20261109/KEFF_CALC.md": [340],
    "lead/score_decomp_20261109/SCORE_DECOMP.md": [135, 239],
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md": [158],
}

FOCUS = {
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md:158":
        "围栏内脚本 stdout；(a) K7_code_fence_interior",
    "lead/layer_identity_20261109/LAYER_IDENTITY.md:13":
        "目的陈述+「究竟是A还是B」；(b) K3_question_not_assertion",
    "lead/layer_identity_20261109/LAYER_IDENTITY.md:223":
        "表格转述行引 _cs_info.py:39-43；(c) K9_table_relay_row",
    "lead/layer_identity_20261109/LAYER_IDENTITY.md:242":
        "E_eq 整窗被 :240 字面 A=B 毒化；(d) E_eq 锚点局部 → SUBSTANTIVE_OK",
    "lead/layer_identity_20261109/LAYER_IDENTITY.md:338":
        "【复核】转述前缀（I 借自 :339「定理」）；(e) K8_review_paraphrase_prefix",
}


def scan_all(eq) -> dict[str, dict]:
    out = {}
    for relp in FILES:
        rec = eq.scan_file(ROOT / relp)
        out[relp] = rec
    return out


def flat(scans: dict[str, dict]) -> dict[str, dict]:
    out = {}
    for relp, rec in scans.items():
        for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
            for x in rec[bucket]:
                out[f"{relp}:{x['line']}"] = x
    return out


def main() -> int:
    sb, sa = scan_all(eq_b), scan_all(eq_a)
    fb, fa = flat(sb), flat(sa)

    # ---- 基线一致性：现场重扫 vs 存档原件 JSON ----
    orig = json.loads(ORIG_JSON.read_text(encoding="utf-8"))
    print("== (0) 现场重扫（原检测器） vs 存档原件 totals ==")
    ok_all = True
    for k in ("n_anchors", "n_findings", "n_tautology_ok", "n_passes", "n_skips", "n_undecidables"):
        v = sum(r[k] for r in sb.values())
        o = orig["totals"][k]
        ok_all = ok_all and (v == o)
        print(f"  {k}: rescan={v} stored={o} {'OK' if v == o else 'MISMATCH'}")

    # ---- (a) 45 行逐行 ----
    print("\n== (a) 45 行 before → after ==")
    n_chg = 0
    for relp, lns in LISTED_45.items():
        for n in lns:
            fl = f"{relp}:{n}"
            b, a = fb.get(fl), fa.get(fl)
            bv = f"{b['verdict']}/{b['failure_type'] or '-'}" + (f"/{b['skip_reason']}" if b["verdict"] == "SKIP" else "") if b else "GONE"
            av = f"{a['verdict']}/{a['failure_type'] or '-'}" + (f"/{a['skip_reason']}" if a and a["verdict"] == "SKIP" else "") if a else "GONE"
            chg = b and a and (b["verdict"] != a["verdict"] or b.get("skip_reason") != a.get("skip_reason"))
            n_chg += 1 if chg else 0
            focus = FOCUS.get(fl, "")
            print(f"  {fl} | {bv}  →  {av} {'★CHANGED ' + focus if chg else ''}")
    print("  45 行中判定变化的行数 =", n_chg,
          "（其中 before-FAIL → after-FAIL 应为 0）")

    # ---- (b) 迁移矩阵 + 新增 FAIL 回归检查 ----
    print("\n== (b) 迁移矩阵（全部锚点）==")
    trans: Counter = Counter()
    new_fail = []
    for fl, b in fb.items():
        a = fa.get(fl)
        av = a["verdict"] if a else "GONE"
        bkey = b["verdict"] + ("/" + b["failure_type"] if b.get("failure_type") else "")
        akey = av + ("/" + a["failure_type"] if a and a.get("failure_type") else "")
        trans[(bkey, akey)] += 1
        if b["verdict"] != "FAIL" and av == "FAIL":
            new_fail.append(fl)
    for (bv, av), n in sorted(trans.items(), key=lambda kv: -kv[1]):
        mark = "  ★★NEW_FAIL" if av.startswith("FAIL") and not bv.startswith("FAIL") else ""
        print(f"  {n:4d}  {bv}  →  {av}{mark}")
    print("  新增 FAIL 总数 =", len(new_fail), new_fail[:10])

    # ---- (c1) findings 收敛逐行归因 ----
    print("\n== (c1) before-FAIL → after 非 FAIL 逐行归因 ==")
    loose = [(fl, b, fa.get(fl)) for fl, b in fb.items()
             if b["verdict"] == "FAIL" and (not fa.get(fl) or fa[fl]["verdict"] != "FAIL")]
    print("  count =", len(loose))
    c: Counter = Counter()
    ex: dict = {}
    for fl, b, a in loose:
        av = a["verdict"] if a else "GONE"
        sr = a.get("skip_reason") if a else None
        key = (b["failure_type"], av, sr)
        c[key] += 1
        ex.setdefault(key, []).append(fl)
    for key, n in c.most_common():
        print(f"    {key[0]} → {key[1]}/{key[2]}: {n}   例: {ex[key][:4]}")

    # ---- (c2) tautology_ok 流失行 ----
    print("\n== (c2) before TAUTOLOGY_OK → after 非 TAUTOLOGY_OK ==")
    n_taut_lost = 0
    for fl, b in fb.items():
        if b["verdict"] == "TAUTOLOGY_OK":
            a = fa.get(fl)
            if not a or a["verdict"] != "TAUTOLOGY_OK":
                n_taut_lost += 1
                av = a["verdict"] if a else "GONE"
                print(f"  {fl} | → {av}/{a.get('skip_reason') if a else None}"
                      f" cat={a.get('category') if a else None}")
                print(f"      text: {b['text'][:120]}")
    print("  tautology_ok 流失行数 =", n_taut_lost)

    # ---- (c3) undecidables 变化归因 ----
    print("\n== (c3) before UNDECIDABLE → after 去向 ==")
    c2: Counter = Counter()
    ex2: dict = {}
    for fl, b in fb.items():
        if b["verdict"] == "UNDECIDABLE":
            a = fa.get(fl)
            av = a["verdict"] if a else "GONE"
            sr = a.get("skip_reason") if a else None
            c2[(av, sr)] += 1
            ex2.setdefault((av, sr), []).append(fl)
    for (av, sr), n in c2.most_common():
        print(f"    → {av}/{sr}: {n}   例: {ex2[(av, sr)][:3]}")

    # ---- (d) 围栏残留：围栏外锚点窗口 ∩ 围栏区间 ----
    print("\n== (d) 围栏残留（修版未改窗口构成）：围栏外锚点窗口与围栏区间重叠 ==")
    n_ov = 0
    ov_ftype: Counter = Counter()
    ov_ex = []
    for relp, rec in sa.items():
        ranges = rec.get("code_fence_ranges_1based") or []
        if not ranges:
            continue
        for bucket in ("findings", "passes", "tautology_ok", "skips", "undecidables"):
            for x in rec[bucket]:
                if x.get("category") == "CODE" or x.get("skip_reason") == "K7_code_fence_interior":
                    continue
                lo, hi = x["window"]
                for a, b_ in ranges:
                    bhi = b_ if b_ is not None else 10 ** 9
                    if not (hi < a + 1 or lo > bhi - 1):  # 窗口行与围栏内容行(开,闭)开区间相交
                        n_ov += 1
                        ov_ftype[(x["verdict"], x.get("failure_type"))] += 1
                        if len(ov_ex) < 8:
                            ov_ex.append(f"{relp}:{x['line']} win=[{lo},{hi}] fence=[{a},{b_}] {x['verdict']}")
                        break
    print("  围栏外锚点窗口与围栏内容重叠数 =", n_ov)
    for k, v in ov_ftype.most_common():
        print(f"    {k}: {v}")
    for e in ov_ex:
        print("    例:", e)

    out = {
        "totals_rescan_before": {k: sum(r[k] for r in sb.values()) for k in
                                 ("n_anchors", "n_findings", "n_tautology_ok", "n_passes", "n_skips", "n_undecidables")},
        "totals_rescan_after": {k: sum(r[k] for r in sa.values()) for k in
                                ("n_anchors", "n_findings", "n_tautology_ok", "n_passes", "n_skips", "n_undecidables")},
        "findings_by_type_before": dict((t, sum(r["findings_by_type"].get(t, 0) for r in sb.values())) for t in ("F1", "F2", "F3")),
        "findings_by_type_after": dict((t, sum(r["findings_by_type"].get(t, 0) for r in sa.values())) for t in ("F1", "F2", "F3")),
        "n_45_changed": n_chg, "n_new_fail": len(new_fail),
        "n_loose_findings": len(loose),
        "loose_attribution": {f"{k[0]}->{k[1]}/{k[2]}": v for k, v in c.items()},
        "taut_lost": n_taut_lost,
        "fence_window_overlap": {"n": n_ov, "by_verdict": {f"{k[0]}/{k[1]}": v for k, v in ov_ftype.items()},
                                 "examples": ov_ex},
    }
    (HERE / "_ef_diff45_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nwritten:", HERE / "_ef_diff45_out.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
