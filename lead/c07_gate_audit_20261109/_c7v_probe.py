# -*- coding: utf-8 -*-
# _c7v_probe.py — 只读探针：关键件指纹 + H09 对照集实况。零写入。
import hashlib
import json
import os

ROOT = "D:/Project/ra2-campaign-forge"

FILES = [
    "lead/c07_slot_20261109/_c7_selfcheck.py",
    "lead/c07_slot_20261109/_c7_record_template.json",
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md",
    "lead/pending_factpack_20261108/_fp_N10-C07_Q6.md",
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
    "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json",
]

print("== 指纹 ==")
for rel in FILES:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        print("MISSING", rel)
        continue
    b = open(p, "rb").read()
    print(hashlib.sha256(b).hexdigest(), len(b), rel)

print("== a_residual_20261106 记录层 reviewerSessionId 实况 ==")
p = os.path.join(ROOT, "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json")
obj = json.loads(open(p, "rb").read().decode("utf-8"))
recs = obj if isinstance(obj, list) else obj.get("records", [])
print("顶层类型:", type(obj).__name__, "记录数:", len(recs))
n_str = 0
vals = set()
for r in recs:
    if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
        n_str += 1
        vals.add(r["reviewerSessionId"])
print("reviewerSessionId 为字符串的记录数:", n_str, "去重值数:", len(vals))

print("== a_residual_n1 记录层 reviewerSessionId 实况 ==")
p = os.path.join(ROOT, "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json")
obj = json.loads(open(p, "rb").read().decode("utf-8"))
recs = obj.get("records", []) if isinstance(obj, dict) else []
print("记录数:", len(recs))
vals = set()
for r in recs:
    if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
        vals.add(r["reviewerSessionId"])
print("去重值数:", len(vals))
for v in sorted(vals):
    print("  值:", v)

print("== 门禁 H09 对照集基数（复算 load_known_session_ids 口径）==")
known = set()
for rel in ["lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
            "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json"]:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        continue
    try:
        o = json.loads(open(p, "rb").read().decode("utf-8"))
    except (OSError, ValueError):
        continue
    rs = o if isinstance(o, list) else o.get("records", []) if isinstance(o, dict) else []
    for r in rs:
        if isinstance(r, dict) and isinstance(r.get("reviewerSessionId"), str):
            known.add(r["reviewerSessionId"])
print("对照基数 =", len(known))
for v in sorted(known):
    print("  值:", v)
