# -*- coding: utf-8 -*-
"""_fnr_fingerprints.py -- independently recompute SHA256+bytes of the
orchestrator-provided fingerprints. READ-ONLY on all inputs.
Run: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/falsifiable_no_relax_20261109/_fnr_fingerprints.py
"""
import hashlib, json, os, sys

ROOT = "D:/Project/ra2-campaign-forge"
EXPECT = {
    "lead/gate_r9sem_20261109/_r9s_regress.py": ("16612625a7a5b11aba8b19c895a612f319bd4421c9c095b2ff8285be9214c4b4", 11258),
    "lead/gate_r9sem_20261109/_r9s_regress_out.json": ("5bfb169acc58221ac74873dd99e1236931ac1b08d1eedc8dfb43076cc5b05e25", 75673),
    "lead/gate_r9sem_20261109/_r9s_predicates.py": ("b0265fc57ef4facd06d92b4852344a80d983f14560a8521525ba18e533ae7034", 23111),
    "lead/whitelist_audit_20261109/_WL_WHITELIST_AUDIT.md": ("f9d00b7c9a12a996bac9d89b0bf5a948dfe026e21f472bd825d7924d35a47adc", 52705),
    "lead/whitelist_audit_20261109/_wl_selfproof_out.json": ("e389f262e6b54d537f75c50621afa05d76200353de0fa59965adcd3031a92e72", 880),
    "lead/whitelist_audit_20261109/_wl_step3_struct_out.json": ("3efc6172228bf1e0ff0f098b63987d214c7009850beeb3a6f6d7b83e8311126c", 4269),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

def main():
    rows = []
    for rel, (sha, size) in EXPECT.items():
        p = os.path.join(ROOT, rel)
        b = open(p, "rb").read()
        got = hashlib.sha256(b).hexdigest()
        rows.append({"path": rel, "sha256": got, "bytes": len(b),
                     "sha_match": got == sha, "bytes_match": len(b) == size,
                     "binding": "被核对象 SHA256 = %s，字节数 = %d" % (got, len(b))})
    out = {"all_match": all(r["sha_match"] and r["bytes_match"] for r in rows), "rows": rows}
    print(json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
