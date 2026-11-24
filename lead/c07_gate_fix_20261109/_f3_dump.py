# -*- coding: utf-8 -*-
# _f3_dump.py — 只读工具：1) 36 样本与模板的逐字段差异；2) 两件 ACCEPTANCE_RECORDS 的已登 sessionId 清单。
# 不写任何被核文件。用法：python -I -X utf8 _f3_dump.py
import json
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
TPL = os.path.join(ROOT, "lead", "c07_slot_20261109", "_c7_record_template.json")
SDIR = os.path.join(ROOT, "lead", "c07_gate_audit_20261109", "_c7a_samples")
REGS = [
    "lead/a_residual_20261106/ACCEPTANCE_RECORDS.json",
    "lead/a_residual_n1_20261108/ACCEPTANCE_RECORDS.json",
]


def deep_diff(a, b, path=""):
    out = []
    if type(a) is not type(b):
        out.append((path, "TYPE %r -> %r" % (a, b)))
        return out
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((path + "/" + k, "EXTRA %r" % (b[k],)))
            elif k not in b:
                out.append((path + "/" + k, "MISSING (sample lacks; tpl=%r)" % (a[k],)))
            else:
                out += deep_diff(a[k], b[k], path + "/" + k)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((path, "LEN %d -> %d (%r -> %r)" % (len(a), len(b), a, b)))
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                out += deep_diff(x, y, path + "[%d]" % i)
    else:
        if a != b:
            out.append((path, "%r -> %r" % (a, b)))
    return out


def main():
    with open(TPL, "rb") as f:
        tpl = json.loads(f.read().decode("utf-8"))
    names = sorted(x for x in os.listdir(SDIR) if x.endswith(".json"))
    print("== SAMPLE DIFFS (vs template), %d files ==" % len(names))
    for n in names:
        p = os.path.join(SDIR, n)
        with open(p, "rb") as f:
            obj = json.loads(f.read().decode("utf-8"))
        diffs = deep_diff(tpl, obj)
        print("--- %s (%d diffs)" % (n, len(diffs)))
        for path, d in diffs:
            print("    %s: %s" % (path, d))
    print()
    print("== REGISTERED sessionIds in anti-copy sources ==")
    for rel in REGS:
        p = os.path.join(ROOT, rel.replace("/", os.sep))
        with open(p, "rb") as f:
            obj = json.loads(f.read().decode("utf-8"))
        recs = obj if isinstance(obj, list) else obj.get("records", [])
        ids = []
        for r in recs:
            if isinstance(r, dict):
                ids.append(r.get("reviewerSessionId"))
        print("%s: records=%d ids=%r" % (rel, len(recs), ids))
    return 0


if __name__ == "__main__":
    sys.exit(main())
