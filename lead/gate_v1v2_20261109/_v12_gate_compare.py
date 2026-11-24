# -*- coding: utf-8 -*-
r"""_v12_gate_compare.py -- 走生产门禁模块 _g9_gate.check_deliverable 复核 R10/R12，
并逐命中检查 V2_OVERRIDE 是否出现在该命中的分析单元 U 内（排除整文子串假象）。

跑法：python -I -X utf8 D:\Project\ra2-campaign-forge\lead\gate_v1v2_20261109\_v12_gate_compare.py
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
WD = ROOT / "lead" / "gate_v1v2_20261109"
sys.path.insert(0, str(WD))
G9 = ROOT / "lead" / "gate_r9r12_20261109" / "_g9_gate.py"
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    g9 = load(G9, "_g9_gate_v12")
    g7 = load(PRED, "_g7_predicates_v12b")
    import _v12_rule as R

    DOCS = [
        ("c07_slot_20261109", ROOT / "lead" / "c07_slot_20261109" / "C07_IDENTITY_SLOT.md",
         ["已补登", "已填入", "已填", "已代填"]),
        ("c07_truth_protocol_20261109", ROOT / "lead" / "c07_truth_protocol_20261109" / "C07_TRUTH_SELF_PROOF.md",
         ["已填", "已代填", "已提交"]),
    ]
    print("=== F. 生产门禁 _g9_gate.check_deliverable 独立复核（真 import，指纹先验） ===")
    for name, path, bans in DOCS:
        r = g9.check_deliverable(str(path), [], bans, old_gate_contrast=False)
        r10 = r["predicates"]["R10"]
        r12 = r["predicates"]["R12"]
        print("  [%s] verdict=%s R10(items=%d occ=%d kinds=%s problems=%d exempted=%d) R12(double_neg_hits=%d)" %
              (name, r["verdict"], r10["items"], r10["occurrences"], r10["kinds"],
               len(r10["problems"]), r10["exempted"], r12["double_neg_hits"]))
        print("     R10 problems = %s" % json.dumps(r10["problems"], ensure_ascii=False))
        print("     R10 warnings = %s" % json.dumps(r10["warnings"], ensure_ascii=False))

    print("\n=== G. 逐命中：该命中的分析单元 U 内是否含 V2_OVERRIDE 词族 ===")
    for name, path, bans in DOCS:
        text = path.read_bytes().decode("utf-8")
        _, _, hits = g7.r10_scan(text, bans)
        for h in hits:
            tok, pos = h["token"], h["pos"]
            L = text.count("\n", 0, pos) + 1
            v = R.classify_v12(text, pos, pos + len(tok), tok)
            in_u = [k for k in R.V2_OVERRIDE if k in v["unit"]]
            print("  %-32s L%-4d tok=%-6s R10=%-13s V12=%s U内V2_OVERRIDE=%r" %
                  (name, L, tok, h["kind"], v["verdict"], in_u))

    print("\n=== H. 整文 V2_OVERRIDE 子串定位（说明为何不构成 V2：不在任何禁用词命中的 U 内） ===")
    for name, path, bans in DOCS:
        text = path.read_bytes().decode("utf-8")
        for w in ("登记完成", "已签", "登记闭合", "补登完成"):
            for m in __import__("re").finditer(w, text):
                L = text.count("\n", 0, m.start()) + 1
                a = text.rfind("\n", 0, m.start()) + 1
                b = text.find("\n", m.start())
                b = len(text) if b < 0 else b
                line = text[a:b]
                toks = [t for t in bans if t in line]
                print("  %-32s L%-4d %-6s 同行禁用词=%r | %s" % (name, L, w, toks, line[:190]))


if __name__ == "__main__":
    main()
