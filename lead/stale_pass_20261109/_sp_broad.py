# -*- coding: utf-8 -*-
# 宽口径扫描两台账：门禁/复跑/SELF_TEST/REFSYNC/哨兵/自检 等所有相关词
# 只读，Python 不写文件
import re, json

A = r"D:\Project\ra2-campaign-forge\lead\PENDING_DECISIONS.md"
B = r"D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md"
C = r"D:\Project\ra2-campaign-forge\lead\refsync_scope_20261109\REFSYNC_SCOPE_FIX.md"

TERMS = ["check_d27", "check_d29", "check_d30", "carrier_scan", "carrier",
         "SELF_TEST", "self_test", "REFSYNC", "refsync", "哨兵", "needle",
         "坏输入", "注入", "门禁", "机械检查", "exit=0", "EXIT=0"]

def scan(tag, p):
    with open(p, "rb") as f:
        lines = f.read().decode("utf-8", errors="replace").split("\n")
    hits = []
    for i, ln in enumerate(lines, 1):
        m = [t for t in TERMS if t in ln]
        if m:
            hits.append({"file": tag, "line": i, "terms": m, "text": ln})
    return {"tag": tag, "nlines": len(lines), "hits": hits}

out = {"PENDING": scan("PENDING", A), "GOAL": scan("GOAL", B),
       "REFSYNC_SCOPE_FIX": scan("REFSYNC_SCOPE_FIX", C),
       "TERMS": TERMS}
print(json.dumps(out, ensure_ascii=False, indent=1))
