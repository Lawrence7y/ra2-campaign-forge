# -*- coding: utf-8 -*-
"""_g7_fp_check.py — 核对编排方给出的被核对象指纹（只读，hashlib）。
零真机、零采样。输出 SHA256 与字节数，供复核回件引用。
"""
import hashlib, json, os, sys

BASE = r"D:\Project\ra2-campaign-forge"
EXPECT = {
    "lead/gate_template_20261108/GATE_TEMPLATE_FIXED.py.txt": "543e79184258f9f96517fdc8d61d42e46a7cd544f11ce0ab3b78d9fd505e9abe",
    "lead/gate_template_20261108/GATE_FALSE_POSITIVES.md": "2011cb866e8a6e857c7c3fcd08e7270e0cc062f8eed47610fa025bf15b5f3244",
    "lead/gate_validate_20261108/GATE_TEMPLATE_REGRESSION.md": "c9093cab4f708d3f2bfd721095e9d8458818dd9d36019d996fd952b24e1a5a19",
    "lead/n4_yi_final_20261108/CANDIDATE_RESIGN_YES_V2.md": "1950d3f31048b9a0503f3e026392ca9e15326c39a76104c5cc3fbbdd0455925b",
    "lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md": "724458d9e2fdaab8ba34d6c7f64612e722f62618381768132246a5cbaa155f4e",
    "lead/n11_protocol_spec_20261108/OBSERVATION_PROTOCOL_SPEC.md": "c0dfb0d17edab4d0d89c43dc48bce4b84354fd13bd89cae7277aa15e82cf65f2",
    "lead/c97_scope_recheck_20261108/C97_SCOPE_RECHECK.md": "6d88fc9241e31e0d6ed7af4988ab712c8e0f4e4caa9d3d92e4f736bf23f46395",
}

out = []
for rel, exp in EXPECT.items():
    p = os.path.join(BASE, rel)
    with open(p, "rb") as f:
        data = f.read()
    sha = hashlib.sha256(data).hexdigest()
    ok = "MATCH" if sha == exp else "MISMATCH"
    out.append({"path": rel, "sha256": sha, "bytes": len(data), "expect": exp, "verdict": ok})

for r in out:
    print(f"{r['verdict']}  bytes={r['bytes']:>6}  {r['path']}")
    print(f"          sha256={r['sha256']}")

bad = [r for r in out if r["verdict"] != "MATCH"]
print("ALL_MATCH" if not bad else f"MISMATCH_COUNT={len(bad)}")
