# -*- coding: utf-8 -*-
# 探针A：open(变量路径, "w") 是否触发 Mimosa 拦截
import os
BASE = "D:/Project/ra2-campaign-forge"
OUT = BASE + "/lead/d14_dual_20261107/_dual_probe_a.txt"
p = OUT
with open(p, "w", encoding="utf-8") as fh:
    fh.write("probe var-ok\n")
print("A written:", p, os.path.getsize(p))
