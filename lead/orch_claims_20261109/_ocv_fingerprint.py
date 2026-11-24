# -*- coding: utf-8 -*-
"""_ocv_fingerprint.py - independent recomputation of the 9 orchestrator-supplied
fingerprints. Read-only with respect to everything outside stdout.
Absolute literal paths only; no path concatenation."""
import hashlib, json

ROOT = "D:/Project/ra2-campaign-forge/"
EXPECT = {
    ROOT + "lead/pvalue_recalc_20261109/_pv_PVALUE_RECALC.md": ("277df9910d4611e0072faf83bd65e3639667a01b511191d5f74b575e448911ac", 29780),
    ROOT + "lead/keff_calc_20261109/KEFF_CALC.md": ("4ad16cdb7dbb4b9e97ea306b55af6d51e2c262a52b10c75e56e1f5ffa1126e16", 34964),
    ROOT + "lead/score_decomp_20261109/SCORE_DECOMP.md": ("dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb", 42573),
    ROOT + "lead/check_family_20261109/CHECK_FAMILY_LINEAGE.md": ("e5098b23732141df0fcb48631cab5642cb4ec054f47564a2a0233fa6e10539f8", 82856),
    ROOT + "lead/stale_pass_20261109/STALE_PASS_INVENTORY.md": ("a72d79b23b1329207a2c612d4244dec407ffaa4e0b91c397c3febb7a9cddd798", 63656),
    ROOT + "lead/evidence_indep_20261109/EVIDENCE_INDEPENDENCE.md": ("aeab4fc30822dfde9c21489aef9a42a1558dde1f21f091f486bbd94453f7a523", 36194),
    ROOT + "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    ROOT + "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    ROOT + "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

out = []
for p, (sha, nb) in EXPECT.items():
    with open(p, "rb") as f:
        b = f.read()
    got = hashlib.sha256(b).hexdigest()
    out.append({"file": p.replace(ROOT, ""), "sha256": got, "bytes": len(b),
                "expected_sha256": sha, "expected_bytes": nb,
                "sha_match": got == sha, "bytes_match": len(b) == nb})
print(json.dumps({"count": len(out),
                  "all_match": all(x["sha_match"] and x["bytes_match"] for x in out),
                  "items": out}, ensure_ascii=False, indent=2))
