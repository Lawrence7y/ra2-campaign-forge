# -*- coding: utf-8 -*-
# 生成 d29/d30 注射副本到 stdout（Python 只读源文件，不写任何文件；shell 重定向落盘）
# argv: 29|30
import sys
which = sys.argv[1]
if which == "29":
    SRC = r"D:\Project\ra2-campaign-forge\lead\d29_ruling_20261106\check_d29.py"
    NEEDLE = '"前提"'
elif which == "30":
    SRC = r"D:\Project\ra2-campaign-forge\lead\d30_ruling_20261106\check_d30.py"
    NEEDLE = '"误报率"'
else:
    raise SystemExit("bad arg")
SENTINEL = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"
with open(SRC, "rb") as f:
    b = f.read()
t = b.decode("utf-8")
assert t.count(NEEDLE) == 1, "needle occurrence != 1"
sys.stdout.buffer.write(t.replace(NEEDLE, '"' + SENTINEL + '"').encode("utf-8"))
