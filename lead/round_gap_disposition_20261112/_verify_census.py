# -*- coding: utf-8 -*-
"""核对 _enum_rounds.json 的口径：逐日期顶层计数 / 报告窗口分解 / 第12个C / 枚举后实时churn。
用法: python -I -X utf8 _verify_census.py
"""
import os
import re
import json
import io
import sys

LEAD = r"D:\Project\ra2-campaign-forge\lead"
SELF = os.path.dirname(os.path.abspath(__file__))
SUFFIX_RE = re.compile(r"2026\d{4}$")

with io.open(os.path.join(SELF, "_enum_rounds.json"), encoding="utf-8") as fh:
    data = json.load(fh)
records = data["records"]

top = [r for r in records if r["depth"] == 0]

lines = []
P = lines.append
P("== A. 逐日期顶层轮次目录计数（来自 _enum_rounds.json 枚举时点快照）==")
dates = {}
for r in top:
    dates.setdefault(r["date"], []).append(r)
for d in sorted(dates):
    sub = dates[d]
    a = sum(1 for r in sub if r["category"] == "A")
    b = sum(1 for r in sub if r["category"] == "B")
    c = sum(1 for r in sub if r["category"] == "C")
    P("%s: n=%d A=%d B=%d C=%d" % (d, len(sub), a, b, c))

win = [r for r in top if "20261106" <= r["date"] <= "20261111"]
a = sum(1 for r in win if r["category"] == "A")
b = sum(1 for r in win if r["category"] == "B")
c = sum(1 for r in win if r["category"] == "C")
P("窗口[20261106..20261111]顶层: n=%d A=%d B=%d C=%d  (报告: 182=153+18+11)" % (len(win), a, b, c))

P("")
P("== B. ge_top(>=20261106 顶层) 中 category=C 的全部目录（锁定第12个C）==")
gt_c = [r for r in top if r["ge_111106"] and r["category"] == "C"]
for r in sorted(gt_c, key=lambda x: x["dir"]):
    P("C: %s (date=%s)" % (r["dir"], r["date"]))
P("ge_top C 总数=%d" % len(gt_c))

P("")
P("== C. 顶层 20261111 全部目录（检验『报告快照后新建』假设）==")
for r in sorted(dates.get("20261111", []), key=lambda x: x["name"]):
    P("%s cat=%s rec=%d md=%d bytes=%d" % (r["name"], r["category"], r["rec_files"], len(r["md"]), r["total_bytes"]))
P("顶层 20261110 全部目录：")
for r in sorted(dates.get("20261110", []), key=lambda x: x["name"]):
    P("%s cat=%s rec=%d md=%d bytes=%d" % (r["name"], r["category"], r["rec_files"], len(r["md"]), r["total_bytes"]))

P("")
P("== D. 枚举时点之后的实时 churn（现在重走一遍顶层，对比 JSON）==")
now_dirs = set()
for entry in os.listdir(LEAD):
    full = os.path.join(LEAD, entry)
    if os.path.isdir(full) and SUFFIX_RE.search(entry):
        now_dirs.add(entry)
json_top_names = set(r["name"] for r in top)
P("现在顶层日期目录数=%d; 枚举快照顶层日期目录数=%d" % (len(now_dirs), len(json_top_names)))
P("枚举后新增(不在快照): %s" % sorted(now_dirs - json_top_names))
P("快照有而现在无(被删?): %s" % sorted(json_top_names - now_dirs))
P("11-12 目录当前状态:")
for n in sorted(x for x in now_dirs if x.endswith("20261112")):
    cnt = 0
    for root, dirs, files in os.walk(os.path.join(LEAD, n)):
        cnt += len(files)
    P("   %s rec=%d" % (n, cnt))

text = "\n".join(lines) + "\n"
sys.stdout.write(text)
with io.open(os.path.join(SELF, "_verify_census_stdout.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text)
