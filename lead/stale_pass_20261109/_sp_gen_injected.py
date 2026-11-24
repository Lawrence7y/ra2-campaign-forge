# -*- coding: utf-8 -*-
# 生成注射副本到 stdout（Python 只读源文件，不写任何文件；由 shell 重定向落盘）
import sys
SRC = r"D:\Project\ra2-campaign-forge\lead\d27_ruling_20261106\check_d27.py"
NEEDLE = '"卡顿不存在"'
SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"
with open(SRC, "rb") as f:
    b = f.read()
t = b.decode("utf-8")
assert t.count(NEEDLE) == 1, "needle occurrence != 1"
inj = t.replace(NEEDLE, '"' + SENTINEL + '"').encode("utf-8")
sys.stdout.buffer.write(inj)
