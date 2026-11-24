# -*- coding: utf-8 -*-
"""重复计数检查：mirror 与 lead 两处同名 measure json 是否逐字节相同。"""
import hashlib
import os

TRIPS = r"D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\qc161_u0400_trip"
LEAD = r"D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


dirs = ["l1c_20261021", "l1d_20261021", "l1e_20261021", "l3_20261021"]
for d in dirs:
    for w in range(3):
        fn = "measure_w%d.json" % w
        a = os.path.join(TRIPS, d, fn)
        b = os.path.join(LEAD, d, fn)
        ea, eb = os.path.exists(a), os.path.exists(b)
        if ea and eb:
            sa, sb = sha(a), sha(b)
            print("%-14s %s  mirror=%s lead=%s  IDENTICAL=%s" % (
                d, fn, sa[:16], sb[:16], sa == sb))
        else:
            print("%-14s %s  exists mirror=%s lead=%s" % (d, fn, ea, eb))

# 另外：lead 根下与 mirror 根下 measure_w*.json
for base in (TRIPS, LEAD):
    for w in range(3):
        p = os.path.join(base, "measure_w%d.json" % w)
        if os.path.exists(p):
            print("ROOT %s -> %s" % (sha(p)[:16], p))
