"""Independent reviewer fingerprint computation (hashlib, raw bytes)."""
import hashlib
import json

R = "D:/Project/ra2-campaign-forge/"
E = [
    ("lead/gate_r9sem_20261109/_r9s_regress.py", "16612625a7a5b11aba8b19c895a612f319bd4421c9c095b2ff8285be9214c4b4", 11258),
    ("lead/gate_r9sem_20261109/_r9s_regress_out.json", "5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25", 75673),
    ("lead/gate_r9sem_20261109/_r9s_predicates.py", "b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034", 23111),
    ("lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md", "f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc", 52705),
    ("lead/whitelist_audit_20261109/_wl_selfproof_out.json", "e389f262e6b54d537f75c50621afa05d76200353de0fa59965adcd3031a92e72", 880),
    ("lead/whitelist_audit_20261109/_wl_step3_struct_out.json", "3efc6172228bf1e0ff0f098b63987d214c7009850beeb3a6f6d7b83e8311126c", 4269),
    ("lead/gate_pipeline_20261109/_gp_regression_out.json", "d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    ("lead/PENDING_DECISIONS.md", "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ("lead/GOAL_THREE_TARGETS_20261018.md", "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
]

rows = []
for rel, es, en in E:
    with open(R + rel, "rb") as f:
        b = f.read()
    h = hashlib.sha256(b).hexdigest()
    n = len(b)
    m = (h == es and n == en)
    rows.append({"path": rel, "sha256": h, "bytes": n, "expected_sha256": es, "expected_bytes": en, "match": m})
    print(("MATCH   " if m else "MISMATCH") + " n=" + str(n) + " sha=" + h + "  " + rel)
am = all(r["match"] for r in rows)
print("N_FILES = " + str(len(rows)))
print("ALL_MATCH = " + str(am))
print("MATCH_COUNT = " + str(sum(1 for r in rows if r["match"])) + "/" + str(len(rows)))
with open("D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnrv_fingerprints_out.json", "w", encoding="utf-8") as f:
    json.dump({"all_match": am, "files": rows}, f, ensure_ascii=False, indent=2)
