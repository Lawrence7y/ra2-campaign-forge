# -*- coding: utf-8 -*-
# 生成 d28 注射副本到 stdout（Python 只读，shell 重定向落盘）
import sys
SRC = r"D:\Project\ra2-campaign-forge\lead\d28_ruling_20261106\check_d28.py"
NEEDLE = '"1681"'
SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"
with open(SRC, "rb") as f:
    t = f.read().decode("utf-8")
assert t.count(NEEDLE) == 1, "needle occurrence != 1: %d" % t.count(NEEDLE)
sys.stdout.buffer.write(t.replace(NEEDLE, '"' + SENTINEL + '"').encode("utf-8"))
