# -*- coding: utf-8 -*-
# _c7a_fp.py — 指纹实算 + 对照数据源核查（hashlib；只读）。
import hashlib
import json
import os

ROOT = r"D:\Project\ra2-campaign-forge"
FILES = [
    "lead/c07_slot_20261109/_c7_selfcheck.py",
    "lead/c07_slot_20261109/_c7_record_template.json",
    "lead/c07_slot_20261109/_c7_SLOT_PREP.md",
    "lead/c07_slot_20261109/C07_IDENTITY_SLOT.md",
    "lead/pending_factpack_20261108/_fp_N10-C07_Q6.md",
    "lead/d13d14_cards_20261108/DECISION_QUESTIONS.md",
    "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
    "lead/nextstep_plan_20261106/NEXT_STEPS_20261106.md",
    "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json",
    "lead/PENDING_DECISIONS.md",
    "lead/GOAL_THREE_TARGETS_20261018.md",
]

print("== 指纹实算（hashlib.sha256，python -I -X utf8）==")
for rel in FILES:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    if not os.path.exists(p):
        print("%s  MISSING" % rel)
        continue
    with open(p, "rb") as f:
        data = f.read()
    print("%s  sha256=%s bytes=%d" % (rel, hashlib.sha256(data).hexdigest(), len(data)))

print()
print("== 对照数据源：a_residual 两件已登 reviewerSessionId ==")
for rel in ["lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
            "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json"]:
    p = os.path.join(ROOT, rel.replace("/", os.sep))
    try:
        with open(p, "rb") as f:
            obj = json.loads(f.read().decode("utf-8"))
    except Exception as e:
        print("%s  PARSE-FAIL %r" % (rel, e))
        continue
    recs = obj if isinstance(obj, list) else obj.get("records", []) if isinstance(obj, dict) else []
    print("%s  records=%d" % (rel, len(recs)))
    for i, r in enumerate(recs):
        if isinstance(r, dict):
            print("  rec[%d].reviewerSessionId=%r" % (i, r.get("reviewerSessionId")))
