# _eqv_fp.py — 复核员指纹实算（只读；输出 JSON 到 stdout）
# 用法: python -I -X utf8 _eqv_fp.py <baseline|deliver|final>
import hashlib, json, sys, os

ROOT = r"D:\Project\ra2-campaign-forge"

BASELINE = {
    "lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md": ("165474e20a5bfc80c04c7a3b886ebd19c5a0e0cf254565d37d39c43749f7cc6b", 63401),
    "lead/layer_identity_20261109/LAYER_IDENTITY.md": ("ef6e4cc8a01219e8d0c052061623a7993eaa298f20b04ec95c009bb527f950b3", 59941),
    "lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md": ("f737d8a52b51ded87e2f20cd1368f73b4cf3fb7331c34384b0d4b802caf9c503", 45362),
    "lead/keff_calc_20261109/KEFF_CALC.md": ("4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16", 34964),
    "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md": ("aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523", 36194),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/score_decomp_20261109/SCORE_DECOMP.md": ("dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb", 42573),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/evidence_indep_20261109/_ei_n13_predicates_src.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
}

DELIVER = {
    "lead/eqdecl_gate_20261109/_eq_detector.py": ("f29a34b516c14a1320c5bd28a9788801e2c577ff8ae34eea0f41b3d035363472", 29795),
    "lead/eqdecl_gate_20261109/_eq_CONCLUSION.md": ("75ccfa0eae876eed9f8a8c9abe8557928623974c1cffbb212372d4a669c8439c", 18297),
    "lead/eqdecl_gate_20261109/_eq_DESIGN.md": ("08736dab1f2851cfc18633b5f4ccc14a5d07a3c45e35660f70a5c5f9977c08f5", 23097),
    "lead/eqdecl_gate_20261109/_eq_full_out.json": ("efb6542717e99bf57ab821e1eb759ce3f12f8b1b84fd5ef2bb1253a9aaed2919", 3293219),
    "lead/eqdecl_gate_20261109/_eq_full_run.py": ("1477d5455c2a2cdc31217aca05306de155d6dad480090e550efac925c91b05e0", 16429),
    "lead/eqdecl_gate_20261109/_eq_selftest_out.json": ("42b5d7f3acd3260eb4601d91eb865abf18be505b614d58e44c04671df6fbe21f", 10222),
    "lead/eqdecl_gate_20261109/_eq_three_gates.py": ("63d498b6c60fd3480ef51578b23385e451f37cf6974c5dfef84e7c52a8c8c3d0", 8330),
    "lead/eqdecl_gate_20261109/_eq_three_gates_out.json": ("2c9c4fe995f6164e66e251ab903a73c480f03f80321c5d833ea7ce321d2b64be", 33009),
}

def fp(rel):
    p = os.path.join(ROOT, rel)
    h = hashlib.sha256()
    n = 0
    with open(p, "rb") as f:
        while True:
            b = f.read(65536)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n

def run(table, expect_name):
    out = {}
    all_ok = True
    for rel, (esha, ebytes) in table.items():
        sha, n = fp(rel)
        ok = (sha == esha and n == ebytes)
        if not ok:
            all_ok = False
        out[rel] = {"sha256": sha, "bytes": n, "expect_sha": esha, "expect_bytes": ebytes, "match": ok}
    print(json.dumps({"table": expect_name, "n": len(table), "all_match": all_ok, "files": out}, ensure_ascii=False, indent=1))

mode = sys.argv[1] if len(sys.argv) > 1 else "baseline"
if mode == "baseline":
    run(BASELINE, "orchestrator_baseline_11")
elif mode == "deliver":
    run(DELIVER, "implementer_deliver_8")
elif mode == "final":
    run(BASELINE, "orchestrator_baseline_11")
    run(DELIVER, "implementer_deliver_8")
