# -*- coding: utf-8 -*-
# _pf2_read3.py —— V2 §4.2 表头行、B2B_DESIGN 镜像与设计依据定位。只读。
BASE = r"D:\Project\ra2-campaign-forge"

def rd(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8", errors="replace")

V2 = BASE + r"\lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md"
B2B = BASE + r"\lead\b2b_design_20261106\B2B_DESIGN.md"

l = rd(V2).splitlines()
print("---- V2 :108-124 (total=%d) ----" % len(l))
for i in range(107, 124):
    print("%d: %s" % (i + 1, l[i]))
print("")

b = rd(B2B).splitlines()
print("---- B2B_DESIGN.md :305-315 (total=%d) ----" % len(b))
for i in range(304, 315):
    print("%d: %s" % (i + 1, b[i]))
print("")
print("==== B2B_DESIGN.md grep：任意文件状态 / post_read_error / 跑后任意 ====")
n = 0
for i, t in enumerate(b):
    if any(s in t for s in ("任意文件状态", "post_read_error")):
        print("%d: %s" % (i + 1, t[:200]))
        n += 1
        if n >= 15:
            break
print("(hits=%d)" % n)
