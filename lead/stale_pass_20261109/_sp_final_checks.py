# -*- coding: utf-8 -*-
# 末次核验：gate docstring / 逐字短语计数 / GOAL 提及 / 引用数
import re
BASE = r"D:\Project\ra2-campaign-forge\lead"
A = BASE + r"\PENDING_DECISIONS.md"
B = BASE + r"\GOAL_THREE_TARGETS_20261018.md"

for d in ["d27", "d29", "d30", "d28"]:
    p = BASE + "\\" + d + "_ruling_20261106\\check_" + d + ".py"
    with open(p, "r", encoding="utf-8") as f:
        print("DOCSTRING %s: %s" % (d, f.readline().strip()))

ta = open(A, "r", encoding="utf-8").read()
tb = open(B, "r", encoding="utf-8").read()
print()
for s in ["验证通过", "机械检查通过", "逐项通过", "SELF_TEST", "REFSYNC_SCOPE_FIX",
          "check_d27", "check_d29", "check_d30", "_rs_carrier_scan"]:
    print("PHRASE %-24s PENDING=%d GOAL=%d TOTAL=%d" %
          (s, ta.count(s), tb.count(s), ta.count(s) + tb.count(s)))

print()
for s in ["D-27", "D-29", "D-30"]:
    print("GOAL mentions %s = %d" % (s, tb.count(s)))

p = BASE + r"\d27_ruling_20261106\RULING_D27.md"
t = open(p, "r", encoding="utf-8-sig").read()
print()
print("D27_RULING reference count =",
      len(re.findall(r"[A-Za-z0-9_./-]+\.(md|py|json):\d+", t)))
