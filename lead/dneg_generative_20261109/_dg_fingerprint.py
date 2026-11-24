# -*- coding: utf-8 -*-
"""_dg_fingerprint.py — 独立复核编排方实跑指纹（hashlib，绝对只读）。
零真机、零采样；只做静态字节哈希。输出落本任务写域。"""
import hashlib, json
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge")
FILES = [
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/h5_governance_20261109/_h5_r12_gap_out.json",
    "lead/h5_governance_20261109/_h5_pasteable.py",
    "lead/h5_governance_20261109/_h5_regress_out.json",
    "lead/gate_n13_20261109/_n13_predicates.py",
    "lead/gate_pipeline_20261109/_gp_regression_out.json",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]
DECLARED = {
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/h5_governance_20261109/_h5_r12_gap_out.json": ("ffd552207039b220e2a3e649af32aea25bbcd923fe6f9742a8bdb634cb837dc6", 5056),
    "lead/h5_governance_20261109/_h5_pasteable.py": ("b5ba0a6a06a5ea0bef682ae6943002a4bd86e1ee56590dbe4ba324836bad7b7c", 8540),
    "lead/h5_governance_20261109/_h5_regress_out.json": ("9986ed2d83df56bfb8e6d231f1fb85bf037e04961ebff79723c32d4e3e0a834b", 36167),
    "lead/gate_n13_20261109/_n13_predicates.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
out = []
for rel in FILES:
    p = ROOT / rel
    b = p.read_bytes()
    sha = hashlib.sha256(b).hexdigest()
    n = len(b)
    dsha, dn = DECLARED[rel]
    ok = (sha == dsha and n == dn)
    out.append({"file": rel, "sha256": sha, "bytes": n,
                "declared_sha": dsha, "declared_bytes": dn, "match_declared": ok})
    print("%-58s sha=%s bytes=%d match=%s" % (rel.split("/")[-1], sha, n, ok))
print("\nALL_MATCH =", all(r["match_declared"] for r in out))
(Path("D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109") /
 "_dg_fingerprint_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
