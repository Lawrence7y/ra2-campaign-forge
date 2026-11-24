# -*- coding: utf-8 -*-
"""_ncv_claims.py -- 独立重跑 (a) 19/1/0 与 (b) 六类分布。

不采信设计员的 _nc_verify_claims.py；直接读只读件 _oc_stats.py / _oc_stats_out.json /
ORCH_CLAIMS_AUDIT.md，自己 ast.literal_eval + 自己 Counter。
输出仅 stdout；只读输入，不写任何既有件。
"""
import ast
import io
import json
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
P = lambda rel: os.path.join(ROOT, rel.replace("/", os.sep))


def read(rel):
    with io.open(P(rel), "r", encoding="utf-8") as f:
        return f.read()


src = read("lead/orch_claims_20261109/_oc_stats.py")
tree = ast.parse(src)
C = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "C" for t in node.targets):
        C = ast.literal_eval(node.value)
        break
assert C is not None and len(C) == 20

# (a) 自己按 verdict 列重算
counts = {}
for c in C:
    counts[c[1]] = counts.get(c[1], 0) + 1
a_from_C = {
    "total": len(C),
    "wrong": sum(v for k, v in counts.items() if k not in ("correct", "imprecise")),
    "imprecise": counts.get("imprecise", 0),
    "correct": counts.get("correct", 0),
}
stats = json.loads(read("lead/orch_claims_20261109/_oc_stats_out.json"))
a_from_json = {k: stats[k] for k in ("total", "wrong", "imprecise", "correct")}

# (b) 自己按 primary_nature / all_natures 重算
primary, alln = {}, {}
for c in C:
    primary[c[2]] = primary.get(c[2], 0) + 1
    for x in c[3]:
        alln[x] = alln.get(x, 0) + 1

audit = read("lead/orch_claims_20261109/ORCH_CLAIMS_AUDIT.md")
lines = audit.split("\n")
# 从 §3.2 表格原文抽「| 口径混淆 | 7 |」形态
sec32 = "\n".join(lines[118:140])
declared = {}
for m in re.finditer(r"\|\s*([^|\n]+?)\s*\|\s*(\d+)\s*\|", sec32):
    k = m.group(1).strip()
    if k in ("口径混淆", "串对象", "数少", "数多", "代数错", "设计实验当实跑", "把设计实验当实跑"):
        declared[k] = int(m.group(2))

print(json.dumps({
    "a": {
        "verdict_counts_from_C": counts,
        "from_C_table": a_from_C,
        "from_stats_json": a_from_json,
        "reproducible": a_from_C == a_from_json == {"total": 20, "wrong": 19, "imprecise": 1, "correct": 0},
        "scope_note": "只复现人工录入 -> 统计；逐条真伪未独立重审（未验）",
    },
    "b": {
        "recomputed_primary": primary,
        "stats_json_primary": stats["primary_nature_distribution"],
        "declared_in_audit_3_2_parsed": declared,
        "recomputed_all_natures": alln,
        "stats_json_all_natures": stats["all_natures_distribution_non_exclusive"],
        "sum_primary": sum(primary.values()),
        "collapse_share": "%d/20 = %d%%" % (primary["口径混淆"] + primary["串对象"],
                                            5 * (primary["口径混淆"] + primary["串对象"])),
        "primary_match": primary == stats["primary_nature_distribution"],
        "all_natures_match": alln == stats["all_natures_distribution_non_exclusive"],
    },
    "audit_3_2_window_raw": sec32,
    "c_table_verdict_literal_conflict": {
        "caught_ids": [c[0] for c in C if c[4]],
        "literal_no_ids": [c[0] for c in C if c[6] == "no"],
        "overlap": sorted(set(c[0] for c in C if c[4]) & set(c[0] for c in C if c[6] == "no")),
    },
}, ensure_ascii=False, indent=2))
