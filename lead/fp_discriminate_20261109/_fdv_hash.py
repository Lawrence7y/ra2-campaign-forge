import hashlib, os

ROOT = "D:/Project/ra2-campaign-forge"

# 编排方基线（题目给出），外加执行员回件里的两件额外原件
EXPECT = {
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
    "lead/fp_pattern_20261109/FP_PATTERN_ANALYSIS.md": ("d80b8b0e389da9c88121d648ac90331751586ff9c1710fce07880ee0f87d2d6b", 45189),
    "lead/fp_pattern_20261109/_fp_recompute_out.json": ("476be04d9b72c6f343a81906e71f70072992bf2ca949c5c0aa8cf6fc0d6c9fff", 17850),
    "lead/advset_indep_20261109/_dga_adversarial_out.json": ("MISSING", 0),
    "lead/dg_adversarial_20261109/DG_ADVERSARIAL.md": ("e821f91df2add452b239053f69622025d654df40cbb6a6d62536073202cf0deb", 42689),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_fp7_20261108/_dg_core.py": ("MISSING", 0),
    "lead/h5_governance_20261109/_h5_pasteable.py": ("b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c", 8540),
    "lead/dneg_generative_20261109/DNEG_GENERATIVE.md": ("94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4", 46334),
    # 执行员回件的绑定行（非编排方基线，但同属原件）
    "lead/dneg_generative_20261109/_dg_core.py": ("7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1", 12322),
    # 只读探索用（不设基线，仅记录）
    "lead/advset_indep_20261109/_dga_adversarial.py": (None, None),
}

all_ok = True
for rel, (exp_sha, exp_bytes) in EXPECT.items():
    p = ROOT + "/" + rel
    if not os.path.isfile(p):
        ok = (exp_sha == "MISSING")
        print(f"MISSING exists=False {rel}  baseline_expected_missing={ok}")
        if not ok:
            all_ok = False
        continue
    b = open(p, "rb").read()
    sha = hashlib.sha256(b).hexdigest()
    n = len(b)
    if exp_sha is None:
        print(f"EXTRA sha256 = {sha} bytes = {n} {rel}")
        continue
    ok = (sha == exp_sha and n == exp_bytes)
    print(f"{'MATCH' if ok else 'MISMATCH'} sha256 = {sha} bytes = {n} {rel}")
    if not ok:
        all_ok = False
print(f"ALL_BASELINE_OK = {all_ok}")
