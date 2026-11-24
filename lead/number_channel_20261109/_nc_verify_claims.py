# -*- coding: utf-8 -*-
"""独立复核 ORCH_CLAIMS_AUDIT 的 (a)(b)(c)(d)，全部只读输入。
用法: python -I -X utf8 <本文件绝对路径>
不修改任何既有件；产出仅 stdout（由调用方重定向到本任务写域）。
"""
import ast
import hashlib
import io
import json
import os
import re

ROOT = r"D:\Project\ra2-campaign-forge"
P = lambda rel: os.path.join(ROOT, rel.replace("/", os.sep))

STATS = P("lead/orch_claims_20261109/_oc_stats_out.json")
SCRIPT = P("lead/orch_claims_20261109/_oc_stats.py")
AUDIT = P("lead/orch_claims_20261109/ORCH_CLAIMS_AUDIT.md")
TB89 = P(".zcode/workflow-runs/dwfrun-89df48db-a7c0-4905-85b8-68da3f294695.mjs")
TB86 = P(".zcode/workflow-runs/dwfrun-868215ce-ea87-4e41-a54b-5a0af3c441dd.mjs")
RJ32 = P("lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md")


def read(rel):
    with io.open(P(rel), "r", encoding="utf-8") as f:
        return f.read()


def lowered_lines(path):
    """Decode `export const payload = {...};` -> `lowered` string -> lines."""
    txt = io.open(path, "r", encoding="utf-8").read()
    for l in txt.split("\n"):
        if l.startswith("export const payload"):
            body = l[len("export const payload = "):].rstrip().rstrip(";")
            return json.loads(body)["lowered"].split("\n")
    raise RuntimeError("no payload line in " + path)


out = {}

# ---------------- (a) 19/1/0 ----------------
stats = json.loads(read("lead/orch_claims_20261109/_oc_stats_out.json"))
# 从 _oc_stats.py 的 C 表直接重算，不采信 stats_out 的派生字段
src = read("lead/orch_claims_20261109/_oc_stats.py")
tree = ast.parse(src)
C = None
for node in tree.body:
    if isinstance(node, ast.Assign) and any(
        getattr(t, "id", None) == "C" for t in node.targets
    ):
        C = ast.literal_eval(node.value)
        break
assert C is not None and len(C) == 20, "C table not parsed"
n_wrong = sum(1 for c in C if c[1] not in ("correct", "imprecise"))
n_imprecise = sum(1 for c in C if c[1] == "imprecise")
n_correct = sum(1 for c in C if c[1] == "correct")
out["a"] = {
    "from_C_table": {"total": len(C), "wrong": n_wrong,
                     "imprecise": n_imprecise, "correct": n_correct},
    "from_stats_json": {k: stats[k] for k in ("total", "wrong", "imprecise", "correct")},
    "reproducible": (n_wrong, n_imprecise, n_correct) ==
                    (stats["wrong"], stats["imprecise"], stats["correct"]) == (19, 1, 0),
    "note": "C 表是核查员对 20 条的人工判定录入；本脚本重算的是『录入->统计』这一步，"
            "不是重新判定 20 条真伪。20 条逐条真伪未独立重审，标未验。",
}

# ---------------- (b) 六类分布 ----------------
primary = {}
alln = {}
for c in C:
    primary[c[2]] = primary.get(c[2], 0) + 1
    for x in c[3]:
        alln[x] = alln.get(x, 0) + 1
# 审计件 §3.2 正文表格的声明值（按 six 类归一命名）
declared_primary = {"口径混淆": 7, "串对象": 4, "数少": 3, "数多": 3,
                    "代数错": 2, "设计实验当实跑": 1}
norm = {"把设计实验当实跑": "设计实验当实跑"}
primary_norm = {norm.get(k, k): v for k, v in primary.items()}
out["b"] = {
    "recomputed_primary": primary_norm,
    "stats_json_primary_rawkeys": stats["primary_nature_distribution"],
    "declared_in_audit_3_2": declared_primary,
    "primary_match": primary_norm == declared_primary ==
                     {norm.get(k, k): v for k, v in stats["primary_nature_distribution"].items()},
    "sum_primary": sum(primary_norm.values()),
    "recomputed_all_natures_non_exclusive": {norm.get(k, k): v for k, v in alln.items()},
    "verdict_distribution_recomputed": {
        v: sum(1 for c in C if c[1] == v) for v in
        ("wrong_numeric", "wrong_convention", "wrong_object", "imprecise")
    },
    "collapse_share": "口径混淆+串对象 主性质 = %d/20 = %d%%" %
                      (primary_norm["口径混淆"] + primary_norm["串对象"],
                       5 * (primary_norm["口径混淆"] + primary_norm["串对象"])),
}

# ---------------- (c) 贴了≠用了 ----------------
L89 = lowered_lines(TB89)


def find_lines(lines, needles):
    return [(i + 1, s.strip()) for i, s in enumerate(lines)
            if any(n in s for n in needles)]


pair89 = find_lines(L89, ["32768", "16384", "0.14013134", "0.8599", "0.14013"])
L86 = lowered_lines(TB86)
pair86 = find_lines(L86, ["10 个域", "5 个", "十个域", "32 域双轨重判结果", "rjText"])
rj = read("lead/gate_rejudge32_20261109/GATE_REJUDGE_32.md").split("\n")
rj_corr = [(i + 1, s.strip()) for i, s in enumerate(rj)
           if ("13 域" in s and "10 域" in s) or ("6 域" in s and "5 域" in s)]

out["c"] = {
    "tb89": os.path.relpath(TB89, ROOT).replace(os.sep, "/"),
    "tb89_paired_lines": pair89,
    "tb89_machine_segment_has_correct_value": any(
        "0.14013134" in s for _, s in pair89),
    "tb89_prose_segment_has_wrong_value": any(
        "16384" in s or "0.86" in s or "0.8599" in s for _, s in pair89),
    "tb89_ask_join_structure": [s.strip()[:90] for s in L89
                               if "ASK_ANALYST = [" in s or '"【编排方实跑指纹】"' in s
                               or '"【背景——' in s],
    "tb86": os.path.relpath(TB86, ROOT).replace(os.sep, "/"),
    "tb86_machine_pasted": [x for x in pair86 if "rjText" in x[1] or "32 域双轨重判结果" in x[1]],
    "tb86_prose_wrong": [x for x in pair86 if "10 个" in x[1] or "5 个" in x[1] or "十个域" in x[1]],
    "tb86_downstream_correction_lines": rj_corr,
    "verdict": "两份任务书均在机器段贴了对值/实跑输出、散文段仍写错值；可复现。",
    "nuance_for_lint": "89df 的 16384/0.8599 是 CLAIMS 里被核的『自述复算错』（被核对象），"
                       "不是本轮新主张；跨段 diff 若不做角色标注会误报，需把 CLAIMS/被核对象段标为 QUOTED。",
}

# ---------------- (d) 18/18 拦截率 ----------------
# 从 C 表逐条取 caught_by_subtask 与 literal_in_taskbook
caught = [c[0] for c in C if c[4]]
literal_yes = [c[0] for c in C if c[6] == "yes"]
literal_no = [c[0] for c in C if c[6] == "no"]
hedged = [c[0] for c in C if c[6] == "hedged"]
self_recount = [c[0] for c in C if c[6] == "self_recount"]
conflict = sorted(set(caught) & set(literal_no))
audit = read("lead/orch_claims_20261109/ORCH_CLAIMS_AUDIT.md")
audit_42 = "\n".join(audit.split("\n")[166:174])  # §4.2 roughly
out["d"] = {
    "stats_json": {"caught_by_subtask": stats["caught_by_subtask"],
                   "not_caught": stats["not_caught"],
                   "not_caught_ids": stats["not_caught_ids"],
                   "misdirected_downstream": stats["misdirected_downstream"],
                   "literal_in_taskbook": stats["literal_in_taskbook"]},
    "from_C_table": {
        "caught_ids": caught, "n_caught": len(caught),
        "literal_yes_ids": literal_yes, "n_yes": len(literal_yes),
        "literal_no_ids": literal_no, "n_no": len(literal_no),
        "hedged_ids": hedged, "n_hedged": len(hedged),
        "self_recount_ids": self_recount, "n_self_recount": len(self_recount),
        "conflict_caught_but_no_literal": conflict,
    },
    "internal_contradiction": bool(conflict),
    "audit_4_2_refutes_18": ("18/18 虚增" in audit_42 or "18/18 不成立" in audit),
    "audit_4_2_strict": "严格口径 = 9/20" in audit,
    "audit_4_2_loose": "宽松口径 = 15/20" in audit,
    "verdict": "18/18 不可复现为『拦截率』：C 表把 #11/#15/#17 同时标 caught=True 与 "
               "literal=no；审计件 §4.2 已自行更正为严格 9/20、宽松 15/20，并明确『18/18 不成立』。"
               "任务书背景段仍写『18/18 拦截率』，与本件结论冲突——本身即又一个『贴了≠用了』实例。",
}

print(json.dumps(out, ensure_ascii=False, indent=2))
