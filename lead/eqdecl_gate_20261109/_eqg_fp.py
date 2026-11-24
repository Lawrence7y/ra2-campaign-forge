import hashlib, os, json
BASE = r"D:\Project\ra2-campaign-forge"
INSPECTED = [
 ("lead/tautology_audit_20261109/TAUTOLOGY_AUDIT.md","165474e20a5bfc80c04c7a3b886ebd19c5a0e0cf254565d37d39c43749f7cc6b",63401),
 ("lead/layer_identity_20261109/LAYER_IDENTITY.md","ef6e4cc8a01219e8d0c052061623a7993eaa298f20b04ec95c009bb527f950b3",59941),
 ("lead/metric_audit_20261109/METRIC_CONVENTION_AUDIT.md","f737d8a52b51ded87e2f20cd1368f73b4cf3fb7331c34384b0d4b802caf9c503",45362),
 ("lead/keff_calc_20261109/KEFF_CALC.md","4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16",34964),
 ("lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md","aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523",36194),
 ("lead/gate_pipeline_20261109/_gp_regression_out.json","d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe",38575),
 ("lead/score_decomp_20261109/SCORE_DECOMP.md","dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb",42573),
 ("lead/PENDING_DECISIONS.md","3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",52419),
 ("lead/GOAL_THREE_TARGETS_20261018.md","2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",759518),
 ("lead/gate_fp7_20261108/_g7_predicates.py","02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120",11743),
 ("lead/evidence_indep_20261109/_ei_n13_predicates_src.py","e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079",16649),
]
DELIVERABLE = [
 ("lead/eqdecl_gate_20261109/_eq_detector.py","f29a34b516c14a1320c5bd28a9788801e2c577ff8ae34eea0f41b3d035363472",29795),
 ("lead/eqdecl_gate_20261109/_eq_CONCLUSION.md","75ccfa0eae876eed9f8a8c9abe8557928623974c1cffbb212372d4a669c8439c",18297),
 ("lead/eqdecl_gate_20261109/_eq_DESIGN.md","08736dab1f2851cfc18633b5f4ccc14a5d07a3c45e35660f70a5c5f9977c08f5",23097),
 ("lead/eqdecl_gate_20261109/_eq_full_out.json","efb6542717e99bf57ab821e1eb759ce3f12f8b1b84fd5ef2bb1253a9aaed2919",3293219),
 ("lead/eqdecl_gate_20261109/_eq_full_run.py","1477d5455c2a2cdc31217aca05306de155d6dad480090e550efac925c91b05e0",16429),
 ("lead/eqdecl_gate_20261109/_eq_selftest_out.json","42b5d7f3acd3260eb4601d91eb865abf18be505b614d58e44c04671df6fbe21f",10222),
 ("lead/eqdecl_gate_20261109/_eq_three_gates.py","63d498b6c60fd3480ef51578b23385e451f37cf6974c5dfef84e7c52a8c8c3d0",8330),
 ("lead/eqdecl_gate_20261109/_eq_three_gates_out.json","2c9c4fe995f6164e66e251ab903a73c480f03f80321c5d833ea7ce321d2b64be",33009),
]
def check(name, items):
    ok_all = True
    for rel, sha, nb in items:
        p = os.path.join(BASE, rel)
        try:
            data = open(p, "rb").read()
            h = hashlib.sha256(data).hexdigest()
            ok = (h == sha and len(data) == nb)
            ok_all = ok_all and ok
            print(("OK       " if ok else "MISMATCH ") + rel + " " + h + " " + str(len(data)))
        except OSError as e:
            ok_all = False
            print("READFAIL " + rel + " " + repr(e))
    print(name + "_ALL_MATCH =", ok_all)
    return ok_all

a = check("INSPECTED", INSPECTED)
b = check("DELIVERABLE", DELIVERABLE)
wd = os.path.join(BASE, "lead", "eqdecl_gate_20261109")
known = set(x[0] for x in DELIVERABLE)
extra = []
for root, dirs, files in os.walk(wd):
    for fn in sorted(files):
        full = os.path.join(root, fn)
        rel = os.path.relpath(full, BASE).replace("\\", "/")
        if rel not in known:
            try:
                data = open(full, "rb").read()
                extra.append([rel, hashlib.sha256(data).hexdigest(), len(data)])
            except OSError as e:
                extra.append([rel, "READFAIL", 0])
print("EXTRA_FILES =", json.dumps(extra, ensure_ascii=False))
print("FINAL_MATCH =", (a and b))
