# -*- coding: utf-8 -*-
# _tsp_self_scan.py — C07_TRUTH_SELF_PROOF.md 零真实身份值扫描（会话标识值/UUID 段/actor 序号值/TASK 号）。
# 只读实算：python -I -X utf8 + 绝对路径；形制占位符（如 sess_dwf-dwfrun-<UUID>-actor_<n>_<m>）不含真实值，不应命中。
import hashlib
import re

TARGET = r"D:\Project\ra2-campaign-forge\lead\c07_truth_protocol_20261109\C07_TRUTH_SELF_PROOF.md"

PATTERNS = [
    (r"sess_dwf-[0-9a-fA-F]{8}-", "sess_dwf-+8位hex（真实会话标识前缀）"),
    (r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "UUID 形段"),
    (r"actor_[0-9]+_[0-9]+", "actor 序号值"),
    (r"TASK-[0-9]{8}-", "任务号值形"),
]

with open(TARGET, "rb") as f:
    data = f.read()
text = data.decode("utf-8")

hits = 0
for lineno, line in enumerate(text.splitlines(), 1):
    for pat, label in PATTERNS:
        for m in re.finditer(pat, line):
            hits += 1
            print("HIT  L%d  [%s]  %r" % (lineno, label, m.group(0)))

print("TOTAL HITS: %d" % hits)
print("SHA256 = %s" % hashlib.sha256(data).hexdigest())
print("BYTES  = %d" % len(data))
