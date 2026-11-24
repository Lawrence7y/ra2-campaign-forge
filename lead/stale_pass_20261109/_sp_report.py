# -*- coding: utf-8 -*-
# 汇总报表：从 _sp_broad_raw.json / _sp_scan_raw.json 读，输出精简可读文本到 stdout
import json

BASE = r"D:\Project\ra2-campaign-forge\lead\stale_pass_20261109"
broad = json.load(open(BASE + r"\_sp_broad_raw.json", "r", encoding="utf-8"))
scan = json.load(open(BASE + r"\_sp_scan_raw.json", "r", encoding="utf-8"))

for k in ["PENDING", "GOAL", "REFSYNC_SCOPE_FIX"]:
    v = broad[k]
    print("=== %s nlines=%d hits=%d" % (k, v["nlines"], len(v["hits"])))
    for h in v["hits"]:
        print("%s:%d [%s] | %s" % (k, h["line"], ",".join(h["terms"]), h["text"][:300]))
    print()

print("=== PASS_HITS (all %d, by file %s)" % (scan["PASS_HITS_COUNT"], scan["PASS_BY_FILE"]))
for h in scan["PASS_HITS"]:
    print("%s:%d | %s" % (h["file"], h["line"], h["text"][:260]))
