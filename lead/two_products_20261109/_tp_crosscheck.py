# -*- coding: utf-8 -*-
"""_tp_crosscheck.py — 两机读件口径一致性断言（只读产出物，零真机/零采样）。

不修改任何生产者或机读件；只读取两份既有 JSON 并实跑 TP-1..TP-6。
用法：python -I -X utf8 <本文件绝对路径> [A.json] [B.json]
"""
import json
import os
import sys
from pathlib import Path

REPO = Path(r"D:\Project\ra2-campaign-forge")
R11 = REPO / "lead" / "r11_f2_fix_20261109"

# 单点定义：唯一权威的计数维度规格（实现片段见交付文档 §3(e)）
# canonical_key -> (A 别名, B 别名)
CANON = {
    "bindings":       ("bindings", "bindings"),
    "orig_collected": ("orig_path", "orig_collected"),
    "plus_collected": ("plus_path", "plus_collected"),
    "orig_match":     ("orig_match", "orig_match"),
    "plus_match":     ("plus_match", "plus_match"),
    "orig_problems":  ("orig_problems", "orig_problems"),
    "plus_problems":  ("plus_problems", "plus_problems"),
    "orig_warnings":  (None, "orig_warnings"),
    "plus_warnings":  (None, "plus_warnings"),
}
COMMON = [k for k, (a, b) in CANON.items() if a is not None and b is not None]


def canon_from_A(doc):
    """从 A 的 results[] 独立重算全部 9 个 canonical 维度（不看 A.totals）。"""
    R = doc["results"]
    return {
        "bindings": sum(len(r["orig"]["bindings"]) for r in R),
        "orig_collected": sum(1 for r in R for b in r["orig"]["bindings"] if b["path"]),
        "plus_collected": sum(1 for r in R for b in r["plus"]["bindings"] if b.get("path")),
        "orig_match": sum(1 for r in R for b in r["orig"]["bindings"] if b["match"] is True),
        "plus_match": sum(1 for r in R for b in r["plus"]["bindings"] if b.get("match") is True),
        "orig_problems": sum(len(r["orig"]["problems"]) for r in R),
        "plus_problems": sum(len(r["plus"]["problems"]) for r in R),
        "orig_warnings": sum(len(r["orig"]["warnings"]) for r in R),
        "plus_warnings": sum(len(r["plus"]["warnings"]) for r in R),
    }


def canon_from_B(doc):
    """从 B 的 results[] 独立重算全部 9 个 canonical 维度（不看 B.totals）。"""
    R = doc["results"]
    return {
        "bindings": sum(r["n_bindings"] for r in R),
        "orig_collected": sum(1 for r in R for v in r["orig_paths"] if v),
        "plus_collected": sum(1 for r in R for v in r["plus_paths"] if v),
        "orig_match": sum(1 for r in R for v in r["orig_match"] if v is True),
        "plus_match": sum(1 for r in R for v in r["plus_match"] if v is True),
        "orig_problems": sum(len(r["orig_problems"]) for r in R),
        "plus_problems": sum(len(r["plus_problems"]) for r in R),
        "orig_warnings": sum(len(r["orig_warnings"]) for r in R),
        "plus_warnings": sum(len(r["plus_warnings"]) for r in R),
    }


def file_key_A(raw):
    return os.path.normcase(os.path.normpath(raw))


def file_key_B(rel):
    return os.path.normcase(os.path.normpath(os.path.join(str(REPO), rel.replace("/", os.sep))))


def check(A, B):
    v = []
    fa = [file_key_A(r["file"]) for r in A["results"]]
    fb = [file_key_B(r["rel"]) for r in B["results"]]
    # TP-1 文件集与顺序一致（路径归一后）
    if fa != fb or set(fa) != set(fb):
        v.append("TP-1 results[] 文件集/顺序不一致")
    # TP-2 条数一致
    if len(A["results"]) != len(B["results"]):
        v.append("TP-2 results[] 条数不一致")
    # TP-3 逐件绑定行条数一致
    if any(len(a["orig"]["bindings"]) != b["n_bindings"]
           for a, b in zip(A["results"], B["results"])):
        v.append("TP-3 逐件 n_bindings 不一致")
    # TP-4 逐绑定行 path/match/tier 值一致（B 无 declared/match 全键，只比共有投影）
    for i, (a, b) in enumerate(zip(A["results"], B["results"])):
        ob, pb = a["orig"]["bindings"], a["plus"]["bindings"]
        if [x["path"] for x in ob] != b["orig_paths"]:
            v.append("TP-4 idx=%d orig_paths 不一致" % i)
        if [x.get("path") for x in pb] != b["plus_paths"]:
            v.append("TP-4 idx=%d plus_paths 不一致" % i)
        if [x["match"] for x in ob] != b["orig_match"]:
            v.append("TP-4 idx=%d orig_match 不一致" % i)
        if [x.get("match") for x in pb] != b["plus_match"]:
            v.append("TP-4 idx=%d plus_match 不一致" % i)
        if [x.get("tier") for x in pb] != b["plus_tiers"]:
            v.append("TP-4 idx=%d plus_tiers 不一致" % i)
    # TP-5 共同 7 维 totals 值一致（别名归一后）
    ca, cb = canon_from_A(A), canon_from_B(B)
    for k in COMMON:
        if ca[k] != cb[k]:
            v.append("TP-5 canonical %s 不一致 A=%r B=%r" % (k, ca[k], cb[k]))
    # TP-6 各自 totals 与自身 results[] 重算值全等（含别名映射）
    for label, doc, calc, side in (("A", A, ca, 0), ("B", B, cb, 1)):
        for k, (ka, kb) in CANON.items():
            alias = ka if side == 0 else kb
            if alias is None:
                continue
            if doc["totals"].get(alias, "<ABSENT>") != calc[k]:
                v.append("TP-6 %s.totals.%s=%r != recomputed=%r"
                         % (label, alias, doc["totals"].get(alias), calc[k]))
    return v, ca, cb


def main():
    pa = Path(sys.argv[1]) if len(sys.argv) > 1 else R11 / "_f2_compare_out.json"
    pb = Path(sys.argv[2]) if len(sys.argv) > 2 else R11 / "_f2v_run_out.json"
    A = json.loads(pa.read_text(encoding="utf-8"))
    B = json.loads(pb.read_text(encoding="utf-8"))
    v, ca, cb = check(A, B)
    print("A =", pa)
    print("B =", pb)
    print("canonical_from_A =", json.dumps(ca, ensure_ascii=False, sort_keys=True))
    print("canonical_from_B =", json.dumps(cb, ensure_ascii=False, sort_keys=True))
    print("canonical_equal  =", ca == cb)
    print("violations       =", len(v))
    for x in v:
        print("  -", x)
    print("RESULT =", "OK" if not v else "FAIL")
    return 0 if not v else 1


if __name__ == "__main__":
    sys.exit(main())
