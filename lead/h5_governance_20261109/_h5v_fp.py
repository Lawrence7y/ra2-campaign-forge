# -*- coding: utf-8 -*-
"""_h5v_fp.py — 独立复核①：hashlib 实算八件指纹，与编排方基线逐项核对。
只读，不写任何只读件；输出只打印到 stdout。
lead/gate_n13_20261109/_n13_predicates.py 由运行环境在命令执行前解析为真实路径。"""
import sys, hashlib, json
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(r"D:\Project\ra2-campaign-forge")

BASELINE = {
    "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
    "lead/v12_impact_20261109/_vi_REPORT.md": ("9375f37c0ecc81851944fa5383679ce0f02090b2bce6156a5f31396140bdc085", 32956),
    "lead/v12_impact_20261109/_vi_probe_out.json": ("7fd90337383038a21698beec865147257e3e99d6e3be33babf76b5763c65aeec", 52341),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_n13_20261109/_n13_predicates.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
    "lead/gate_pipeline_20261109/_gp_pipeline.py": ("25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7", 15811),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}

# 占位名按运行环境解析；相对路径一律锚到 ROOT
SECRET_P = Path(r"lead/gate_n13_20261109/_n13_predicates.py")
print("SECRET_P resolved =", SECRET_P, "is_file =", SECRET_P.is_file())

rows = []
for rel, (sha, n) in BASELINE.items():
    p = SECRET_P if rel == "lead/gate_n13_20261109/_n13_predicates.py" else (ROOT / rel)
    if not p.is_file():
        rows.append({"file": rel, "found": False})
        print("%-58s NOT FOUND (%s)" % (rel, p))
        continue
    b = p.read_bytes()
    got_sha, got_n = hashlib.sha256(b).hexdigest(), len(b)
    ok = got_sha == sha and got_n == n
    rows.append({"file": rel, "found": True, "sha": got_sha, "bytes": got_n,
                 "expected_sha": sha, "expected_bytes": n, "match": ok})
    print("%-58s %s %7d  match=%s" % (rel, got_sha, got_n, ok))

print("ALL_MATCH =", all(r.get("match") for r in rows), "count =", len(rows))
print(json.dumps({"rows": rows}, ensure_ascii=False))
