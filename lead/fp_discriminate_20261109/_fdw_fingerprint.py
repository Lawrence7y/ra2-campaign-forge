# -*- coding: utf-8 -*-
"""成件撰写员指纹核验：十件受保护原件 + 关键改版件/输出件，本会话实算（hashlib）。只读，不写任何受保护域。"""
import hashlib
import json
import os
import sys

sys.dont_write_bytecode = True

ROOT = r"D:\Project\ra2-campaign-forge\lead"

# 编排方基线完整 64 位值来自任务指派【编排方指纹】
TARGETS = [
    "PENDING_DECISIONS.md",
    "GOAL_THREE_TARGETS_20261018.md",
    "fp_pattern_20261109/FP_PATTERN_ANALYSIS.md",
    "fp_pattern_20261109/_fp_recompute_out.json",
    "dg_adversarial_20261109/_dga_adversarial_out.json",
    "dg_adversarial_20261109/DG_ADVERSARIAL.md",
    "gate_fp7_20261108/_g7_predicates.py",
    "dneg_generative_20261109/_dg_core.py",
    "dneg_generative_20261109/DNEG_GENERATIVE.md",
    "h5_governance_20261109/_h5_pasteable.py",
]

# 编排方给的完整 64 位基线
EXPECT = {
    "PENDING_DECISIONS.md": "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7",
    "GOAL_THREE_TARGETS_20261018.md": "2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede",
    "fp_pattern_20261109/FP_PATTERN_ANALYSIS.md": "d80b8b0e389da9c88121d648ac90331751586ff9c1710fce07880ee0f87d2d6b",
    "fp_pattern_20261109/_fp_recompute_out.json": "476be04d9b72c6f343a81906e71f70072992bf2ca949c5c0aa8cf6fc0d6c9fff",
    "dg_adversarial_20261109/_dga_adversarial_out.json": "395a0a0a3f9316504510b83c023d078d8adcede33f0d20432cf31fcccf99286c",
    "dg_adversarial_20261109/DG_ADVERSARIAL.md": "e821f91df2add452b239053f69622025d654df40cbb6a6d62536073202cf0deb",
    "gate_fp7_20261108/_g7_predicates.py": "02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120",
    "dneg_generative_20261109/_dg_core.py": "7a8074ef8d85dbc6c64136fc71bb793be1cb3dd8c500245778ce1d6644fe2ae1",
    "dneg_generative_20261109/DNEG_GENERATIVE.md": "94eb2a5ef2528b34659e2e7277914917e2176de08dd17fdd9ae5cd17e50af0d4",
    "h5_governance_20261109/_h5_pasteable.py": "b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c",
}

# 执行员/复核件中需在成件里引用的写域内件（核字节+哈希，供绑定行）
WRITE_DOMAIN = [
    "fp_discriminate_20261109/_fd_dg_core_jia.py",
    "fp_discriminate_20261109/_fd_dg_core_jiac.py",
    "fp_discriminate_20261109/_fd_dg_core_yi.py",
    "fp_discriminate_20261109/_fd_dg_core_yi2.py",
    "fp_discriminate_20261109/_fd_dg_core_yi3.py",
    "fp_discriminate_20261109/_fd_sandbox/_dg_core_base.py",
    "fp_discriminate_20261109/_fd_sandbox/_g7_predicates_base.py",
]

def main():
    rows = []
    ok = True
    for rel in TARGETS:
        p = os.path.join(ROOT, rel)
        with open(p, "rb") as f:
            b = f.read()
        h = hashlib.sha256(b).hexdigest()
        exp = EXPECT[rel]
        match = (h == exp)
        if not match:
            ok = False
        rows.append({"rel": rel, "sha256": h, "bytes": len(b), "match_baseline": match})
    wd = []
    for rel in WRITE_DOMAIN:
        p = os.path.join(ROOT, rel)
        with open(p, "rb") as f:
            b = f.read()
        h = hashlib.sha256(b).hexdigest()
        wd.append({"rel": rel, "sha256": h, "bytes": len(b)})
    out = {"baseline_rows": rows, "write_domain_rows": wd, "all_baseline_match": ok}
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
