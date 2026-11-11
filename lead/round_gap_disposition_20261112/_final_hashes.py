# -*- coding: utf-8 -*-
"""对写域内全部交付件实算 sha256（hashlib），供收尾回执引用。
用法: python -I -X utf8 _final_hashes.py
"""
import hashlib
import io
import os
import sys

SELF = os.path.dirname(os.path.abspath(__file__))
lines = []
for name in sorted(os.listdir(SELF)):
    p = os.path.join(SELF, name)
    if not os.path.isfile(p):
        continue
    with open(p, "rb") as fh:
        b = fh.read()
    lines.append("%s  %d B  sha256=%s" % (name, len(b), hashlib.sha256(b).hexdigest()))
text = "\n".join(lines)
sys.stdout.write(text + "\n")
with io.open(os.path.join(SELF, "_final_hashes.txt"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(text + "\n")
