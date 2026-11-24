# -*- coding: utf-8 -*-
# _hd_fp_bind.py — hashlib 实算绑定行。用法：python -I -X utf8 <本脚本绝对路径> <被核对象绝对路径>...
# 输出格式与协议绑定行形制一致（_f3_c7check.py:68 BINDING_FMT 同款，无反引号无插入字符）。
import hashlib
import sys

for p in sys.argv[1:]:
    with open(p, "rb") as f:
        b = f.read()
    print("被核对象 SHA256 = %s，字节数 = %d" % (hashlib.sha256(b).hexdigest(), len(b)))
