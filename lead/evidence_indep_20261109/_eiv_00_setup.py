# -*- coding: utf-8 -*-
"""_eiv_00_setup.py — 独立复核员 ① 九件指纹实算 + N13 源按 hashlib 定位 + 只读域基线快照。
只写 lead/evidence_indep_20261109/_eiv_*。零真机、零采样、只读源域。
运行: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/evidence_indep_20261109/_eiv_00_setup.py
"""
import hashlib
import json
import pathlib

ROOT = pathlib.Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "evidence_indep_20261109"

# 编排方给出的九件基线指纹（来自【编排方指纹】与【被核对象】绑定行）
BASELINE = {
    "lead/gate_n13_20261109/_n13_predicates.py": ("e1195b3b220ad97b5b91b8746a24e332b02ce28085452e947554f99b7f2f3079", 16649),
    "lead/gate_v1v2_20261109/_v12_rule.py": ("15e4211ffe8397027757aa4d0fb9b9cc5dc41126a08024b9f6cb5bbd8be4a1c0", 9148),
    "lead/gate_fp7_20261108/_g7_predicates.py": ("02c17e49764a6f87f2b0d26c6689f0cbeb96498509e5c75bf843104829c51120", 11743),
    "lead/gate_pipeline_20261109/_gp_pipeline.py": ("25c7753f097b8e98e1abb424419e42780bc1ed94fed4a674c142be6c6c1625a7", 15811),
    "lead/gate_pipeline_20261109/_gp_regression_out.json": ("d3543657aa4f9914c9023710f6daef8348a12ca0aa11957110e8b7c45baec6fe", 38575),
    "lead/chain_vs_single_20261109/_cs_align_out.json": ("9dc062202fd9c00b2b74ce6393f29a90f18012a9914cf18dc9cd7ffa653f2698", 11594),
    "lead/chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md": ("3397c1c41b0a81e85699f07ce608b9b13e0ab45cba51280a3e78883581768ed2", 49850),
    "lead/PENDING_DECISIONS.md": ("3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7", 52419),
    "lead/GOAL_THREE_TARGETS_20261018.md": ("2baa0de45d4125549262eb595d7518c9ce99efeee120384bf640cded8a933ede", 759518),
}


def fp(p):
    b = p.read_bytes()
    return hashlib.sha256(b).hexdigest(), len(b)


def main():
    out = {"baseline_n": len(BASELINE), "checks": {}, "n13_source_locate": {},
           "readonly_manifest": {}}

    # ---- 8 件按显式路径实算 ----
    for rel, (bsha, bbytes) in BASELINE.items():
        if rel.startswith("{{"):
            continue  # N13 源另行按 hashlib 定位
        p = ROOT / rel
        if not p.is_file():
            out["checks"][rel] = {"exists": False, "match": False}
            continue
        sha, n = fp(p)
        out["checks"][rel] = {"exists": True, "sha256": sha, "bytes": n,
                              "baseline_sha256": bsha, "baseline_bytes": bbytes,
                              "match": (sha == bsha and n == bbytes)}

    # ---- N13 源：按 hashlib 在 gate_n13_20261109/ 全量扫描，找唯一命中 ----
    n13_sha, n13_bytes = BASELINE["lead/gate_n13_20261109/_n13_predicates.py"]
    scan_dir = ROOT / "lead" / "gate_n13_20261109"
    hits = []
    for p in sorted(scan_dir.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            sha, n = fp(p)
            if sha == n13_sha and n == n13_bytes:
                hits.append(str(p.relative_to(ROOT)).replace("\\", "/"))
    # 也在写域内找（撰写人复制了一份 _ei_n13_predicates_src.py）
    wd_hits = []
    for p in sorted(WD.glob("*")):
        if p.is_file():
            sha, n = fp(p)
            if sha == n13_sha and n == n13_bytes:
                wd_hits.append(p.name)
    out["n13_source_locate"] = {
        "target_sha256": n13_sha, "target_bytes": n13_bytes,
        "scan_dir": str(scan_dir.relative_to(ROOT)).replace("\\", "/"),
        "hits_in_gate_n13": hits, "unique_in_gate_n13": len(hits) == 1,
        "hits_in_write_domain": wd_hits,
        "note": "占位键 lead/gate_n13_20261109/_n13_predicates.py 无显式路径；按 hashlib 全量扫描定位"}

    # ---- 只读域基线快照（⑧ 用，before/after 对比）----
    ro_targets = [
        "lead/gate_pipeline_20261109", "lead/chain_vs_single_20261109",
        "lead/gate_n13_20261109", "lead/gate_v1v2_20261109",
        "lead/gate_fp7_20261108", "lead/count_invariant_20261109",
        "lead/PENDING_DECISIONS.md", "lead/GOAL_THREE_TARGETS_20261018.md",
    ]
    snap = {}
    for rel in ro_targets:
        p = ROOT / rel
        if p.is_dir():
            for q in sorted(p.rglob("*")):
                if q.is_file() and "__pycache__" not in q.parts:
                    k = str(q.relative_to(ROOT)).replace("\\", "/")
                    snap[k] = fp(q)
        elif p.is_file():
            snap[rel] = fp(p)
    out["readonly_manifest"] = {"n_files": len(snap), "sha256_bytes": snap}

    (WD / "_eiv_00_setup_out.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (WD / "_eiv_00_manifest_before.json").write_text(
        json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---- 控制台摘要 ----
    all_match = all(v.get("match") for k, v in out["checks"].items())
    print("== ① 九件指纹独立实算 ==")
    for rel, v in out["checks"].items():
        print("  %-70s match=%s sha=%s bytes=%d" %
              (rel, v["match"], v.get("sha256", "-"), v.get("bytes", -1)))
    print("  8 件显式路径全 match =", all_match)
    nl = out["n13_source_locate"]
    print("== N13 源按 hashlib 定位 ==")
    print("  target sha =", nl["target_sha256"], "bytes =", nl["target_bytes"])
    print("  gate_n13 命中 =", nl["hits_in_gate_n13"], "unique =", nl["unique_in_gate_n13"])
    print("  写域命中 =", nl["hits_in_write_domain"])
    print("== 只读域基线 ==")
    print("  n_files =", out["readonly_manifest"]["n_files"])
    print("written: _eiv_00_setup_out.json / _eiv_00_manifest_before.json")


if __name__ == "__main__":
    main()
