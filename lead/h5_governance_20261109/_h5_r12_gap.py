# -*- coding: utf-8 -*-
"""实读并实跑 R12（_g7_predicates.DOUBLE_NEG_RE / r10_context / r12_scan），
枚举覆盖构式并实测漏判构式。只读既有件，输出落本任务写域。"""
import sys, json, re
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PRED = ROOT / "lead" / "gate_fp7_20261108" / "_g7_predicates.py"

import importlib.util
spec = importlib.util.spec_from_file_location("_h5_g7", str(PRED))
g7 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g7)

print("DOUBLE_NEG_RE.pattern =", g7.DOUBLE_NEG_RE.pattern)
print("NEG_WINDOW =", g7.NEG_WINDOW, "CLAUSE_BREAK =", repr(g7.CLAUSE_BREAK))

COVERED = ["不得不", "并非不", "并不是不", "不是不", "无不", "没有不",
           "不无", "不能不", "不可不", "未曾不"]
print("\n=== (a) 声称覆盖的十式，实跑复核 ===")
for c in COVERED:
    print("  %-8s regex=%s" % (c, bool(g7.DOUBLE_NEG_RE.search(c))))

# 候选漏式：都是「否定+否定=肯定」的汉语构式，token 固定为「已生效」
GAPS = [
    ("亦非不", "亦非不宣告 N-4 正式绑定已生效"),
    ("未尝不", "未尝不认为本件已生效"),
    ("未始不", "未始不认为本件已生效"),
    ("莫不",   "莫不认为本件已生效"),
    ("不敢不", "不敢不承认本件已生效"),
    ("不会不", "不会不承认本件已生效"),
    ("不可能不", "不可能不宣告本件已生效"),
    ("未必不", "未必不认为本件已生效"),
    ("未免不", "未免不认为本件已生效"),
    ("岂能不", "岂能不说本件已生效"),
    ("焉能不", "焉能不说本件已生效"),
    ("哪能不", "哪能不说本件已生效"),
    ("不可谓不", "不可谓不宣告本件已生效"),
    ("不为不", "不为不认为本件已生效"),
    ("未有不", "未有不认为本件已生效"),
    ("并非没有", "并非没有宣告本件已生效"),
    ("并非毫无", "并非毫无宣告本件已生效"),
    ("不是没有", "不是没有宣告本件已生效"),
    ("并不否认", "并不否认本件已生效"),
    ("没有不承认", "没有不承认本件已生效"),
]

TOK = "已生效"
rows = []
print("\n=== (b) R10/R12 对候选漏式的实跑（token=%s） ===" % TOK)
for name, text in GAPS:
    pos = text.find(TOK)
    ctx = g7.r10_context(text, pos, pos + len(TOK))
    problems, hits = g7.r12_scan(text, [TOK])
    r = {"construct": name, "text": text, "regex_hit": bool(g7.DOUBLE_NEG_RE.search(name)),
         "r10_kind": ctx["kind"], "r10_dbl": ctx["dbl"], "r10_neg_count": ctx["neg_count"],
         "r12_problems": len(problems), "expect": "CATCH"}
    rows.append(r)
    print("  %-8s DOUBLE_NEG_RE=%-5s r10=%-10s dbl=%-5s r12_problems=%d" %
          (name, r["regex_hit"], ctx["kind"], ctx["dbl"], len(problems)))

# R12 已覆盖构式做对照
print("\n=== (c) R10/R12 对已覆盖构式的实跑对照 ===")
CTRL = ["不得不承认本候选已生效", "并非不宣告已生效", "并不是不认为本件已生效",
        "不是不承认本件已生效", "无不认为本件已生效", "不能不说本件已生效",
        "不可不说本件已生效", "未曾不认为本件已生效"]
for text in CTRL:
    pos = text.find(TOK)
    ctx = g7.r10_context(text, pos, pos + len(TOK))
    problems, hits = g7.r12_scan(text, [TOK])
    print("  %-24s r10=%-12s dbl=%-5s r12_problems=%d" %
          (text, ctx["kind"], ctx["dbl"], len(problems)))

out = {"predicate_file": str(PRED), "double_neg_pattern": g7.DOUBLE_NEG_RE.pattern,
       "covered": COVERED, "gap_rows": rows}
(HERE / "_h5_r12_gap_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
print("\nwritten: _h5_r12_gap_out.json")
