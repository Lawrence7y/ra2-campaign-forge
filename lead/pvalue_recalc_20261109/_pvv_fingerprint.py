import hashlib, os, json

ROOT = r"D:/Project/ra2-campaign-forge"
files = [
    "lead/score_decomp_20261109/SCORE_DECOMP.md",
    "lead/score_decomp_20261109/_sd_report.md",
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md",
    "lead/gate_pipeline_20261109/_gp_regression_out.json",
    "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json",
    "lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]

baseline = {
    "lead/score_decomp_20261109/SCORE_DECOMP.md": ("dfe7f68692eb7ae752358782acaaa1fc5a42ecbd0a6930205e0dcfe4f6544dcb", 42573),
    "lead/score_decomp_20261109/_sd_report.md": ("58e71cefc024d6874b353cde69d1b39b450f4a79ad08c35e9d235c01dbd725ff", 49202),
    "lead/comparability_20261109/COMPARABILITY_AUDIT.md": ("c00833b3fef5b8b5f93cdfd9d5223f22149878dd868200c1a070d76e553d8ae1", 51927),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/gate_pipeline_20261109/_gp_regression_v1_union_out.json": ("68c7ecd3aafc94be87092bf65f1e3d05ab28cc5a20de5193117f994882e16358", 37461),
    "lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md": ("3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2", 49850),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

ok = 0
for rel in files:
    p = os.path.join(ROOT, rel)
    b = open(p, "rb").read()
    h = hashlib.sha256(b).hexdigest()
    n = len(b)
    exp_h, exp_n = baseline[rel]
    match = (h == exp_h and n == exp_n)
    ok += 1 if match else 0
    print(f"{'OK' if match else 'MISMATCH'} | {rel}")
    print(f"    sha256 = {h}  bytes = {n}")
    print(f"    expected = {exp_h}  bytes = {exp_n}")
    if match:
        print(f"    BINDING: 被核对象 SHA256 = {h}，字节数 = {n}")
print(f"FINGERPRINT_MATCH = {ok}/8")
