# -*- coding: utf-8 -*-
# 探针C：os.listdir -> os.path.join(变量) -> open 读 是否触发拦截
import os
ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
n = 0
for trip in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, trip)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if f.startswith("measure_w") and f.endswith(".json"):
            p = os.path.join(d, f)
            with open(p, encoding="utf-8") as fh:
                fh.read(1)
            n += 1
print("C ok, read", n)
