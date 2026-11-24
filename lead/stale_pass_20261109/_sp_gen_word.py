# -*- coding: utf-8 -*-
# 甲' 外壳生成器：把某 gate 的 OR 词表副本替换为「单元素词表」，打印到 stdout。
# 只读源脚本；由 shell 重定向落盘到沙箱。argv: d27|d29|d30|d28, WORD
import sys
BASE = r"D:\Project\ra2-campaign-forge\lead"
CFG = {
    "d27": (r"\d27_ruling_20261106\check_d27.py", '("外推", "卡顿不存在")'),
    "d29": (r"\d29_ruling_20261106\check_d29.py", '("互斥", "前提")'),
    "d30": (r"\d30_ruling_20261106\check_d30.py", '("93.98", "误报率")'),
    "d28": (r"\d28_ruling_20261106\check_d28.py", '("历史数字", "1681")'),
}
key, word = sys.argv[1], sys.argv[2]
rel, orig = CFG[key]
with open(BASE + rel, "rb") as f:
    t = f.read().decode("utf-8")
assert t.count(orig) == 1, "tuple occurrence != 1"
new = '("%s",)' % word
sys.stdout.buffer.write(t.replace(orig, new, 1).encode("utf-8"))
