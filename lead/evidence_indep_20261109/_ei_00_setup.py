# -*- coding: utf-8 -*-
"""_ei_00_setup.py — verify orchestrator fingerprints and stage a readable copy of
the hash-matched N13 predicate module inside the sole write domain.
Read-only sources: never modified. python -I -X utf8 + absolute paths + hashlib.
"""
import hashlib
import pathlib
import json

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
W = ROOT / "lead" / "evidence_indep_20261109"

EXPECT = {
    "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_pipeline_20261109/_gp_pipeline.py": ("25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7", 15811),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/chain_vs_single_20261109/_cs_align_out.json": ("9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698", 11594),
    "lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md": ("3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2", 49850),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}
N13_SHA = "e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079"
N13_BYTES = 16649


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def main():
    out = {"fingerprints": {}, "n13_match": []}
    for rel, (sha, n) in EXPECT.items():
        p = ROOT / rel
        got = fp(p) if p.is_file() else ("MISSING", -1)
        out["fingerprints"][rel] = {"expect": [sha, n], "got": list(got),
                                    "match": got == (sha, n)}
    d = ROOT / "lead" / "gate_n13_20261109"
    for p in sorted(d.iterdir()):
        if not p.is_file():
            continue
        sha, n = fp(p)
        if (sha, n) == (N13_SHA, N13_BYTES):
            out["n13_match"].append({"name": p.name, "sha256": sha, "bytes": n})
            # stage a read-only copy inside the sole write domain
            (W / "_ei_n13_predicates_src.py").write_bytes(p.read_bytes())
    out["n13_fingerprint_match"] = bool(out["n13_match"])
    (W / "_ei_00_setup_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
