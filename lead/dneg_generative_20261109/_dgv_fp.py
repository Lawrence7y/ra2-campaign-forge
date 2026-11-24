# -*- coding: utf-8 -*-
r"""_dgv_fp.py — 独立复核①：编排方 8 件基线指纹，自算 hashlib，不采信任何 JSON 结论。
另给保护件 + 设计件目录快照，用于⑦越界核验（可重复运行，比较两次输出）。
零真机、零采样；纯静态字节哈希。输出只落 lead/dneg_generative_20261109/。
实跑：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/dneg_generative_20261109/_dgv_fp.py
"""
import hashlib, json, sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path("D:/Project/ra2-campaign-forge")
WD = ROOT / "lead" / "dneg_generative_20261109"

# 编排方声明的 8 件（逐字抄自任务书【编排方指纹】，不是从 _dg_fingerprint.py 读）
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

# 额外保护件（任务书点名只读目录 /\ 台账），用于⑦
EXTRA = [
    "lead/gate_fp7_20261108/_g7_predicates.py",
    "lead/gate_pipeline_20261109/_gp_pipeline.py",
    "lead/gate_pipeline_20261109/_gp_regression.py",
    "lead/gate_n13_20261109/_n13_pasteable.py",
    "lead/h5_governance_20261109/_h5_pasteable.py",
    "lead/h5_governance_20261109/H5_GOVERNANCE_FIX.md",
    "lead/gate_pipeline_20261109/GATE_PIPELINE_COMPOSE.md",
]

print("=== ① 八件指纹（自算 hashlib.sha256）===")
rows = []
for rel, (dsha, dsize) in DECLARED.items():
    p = ROOT / rel
    b = p.read_bytes()
    sha, n = hashlib.sha256(b).hexdigest(), len(b)
    ok = (sha == dsha and n == dsize)
    rows.append({"file": rel, "sha256": sha, "bytes": n,
                 "declared_sha": dsha, "declared_bytes": dsize, "match": ok})
    print("  %-62s sha=%s bytes=%-7d declared=%s/%d MATCH=%s" %
          (rel, sha, n, dsha[:12], dsize, ok))
print("  → ALL_MATCH =", all(r["match"] for r in rows), " (n=%d)" % len(rows))

print("\n=== ⑦-a 额外保护件快照 ===")
extra_rows = []
for rel in EXTRA:
    p = ROOT / rel
    if not p.is_file():
        print("  MISSING", rel)
        continue
    b = p.read_bytes()
    r = {"file": rel, "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)}
    extra_rows.append(r)
    print("  %-70s %s %d" % (rel, r["sha256"], r["bytes"]))

print("\n=== ⑦-b 写域文件清单（按名）===")
wd_rows = []
for p in sorted(WD.iterdir()):
    if p.is_file():
        b = p.read_bytes()
        wd_rows.append({"name": p.name, "sha256": hashlib.sha256(b).hexdigest(),
                        "bytes": len(b)})
        print("  %-28s %d %s" % (p.name, len(b), hashlib.sha256(b).hexdigest()[:16]))

out = {"declared8": rows, "all_match": all(r["match"] for r in rows),
       "extra_protected": extra_rows, "write_domain_files": wd_rows}
(WD / "_dgv_fp_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print("\nwritten: _dgv_fp_out.json")
