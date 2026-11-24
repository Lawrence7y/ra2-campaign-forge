# -*- coding: utf-8 -*-
# _c7_fp.py — 产物指纹（hashlib 实算）
import hashlib, os

HERE = os.path.dirname(os.path.abspath(__file__))
for fn in ["_c7_SLOT_PREP.md", "_c7_record_template.json", "_c7_selfcheck.py"]:
    p = os.path.join(HERE, fn)
    with open(p, "rb") as f:
        data = f.read()
    print("%s bytes=%d sha256=%s" % (fn, len(data), hashlib.sha256(data).hexdigest()))
