# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R16_AUDIT_SLOTN_B3")
from verify import Image, EXE, decode_at, R14

img = Image(EXE)
b = img.read(0x005B4630, 32)
print("005B4630 body head:", b.hex(" ").upper())
i = decode_at(img, 0x005B4639)
print("005B4639:", i.mnemonic, i.op_str)
print("bytes at 005B4639:", img.read(0x005B4639, 8).hex(" ").upper())
# 确认 005B4639 是 005B4630 体内合法指令边界
from verify import decode_reaches
print("decode 005B4630 -> 005B4639 boundary:", decode_reaches(img, 0x005B4630, 0x005B4639))

# PANEL.md 的 D-47 披露
p = os.path.join(R14, "COVERAGE", "PANEL.md")
lines = open(p, "rb").read().split(b"\n")
for idx in range(154, 176):
    if idx < len(lines):
        t = lines[idx].decode("utf-8", "replace")
        if t.strip():
            print("PANEL L%d: %s" % (idx + 1, t[:200]))
