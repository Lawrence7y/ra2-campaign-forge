# -*- coding: utf-8 -*-
# _fw_selfhash.py — RULING_STATIC_ORDER.md 落盘后自指纹实算（纯 hashlib 只读，零写盘，零进程接触）
# 命令：python -I -X utf8 D:/Project/ra2-campaign-forge/lead/n10c04_ruling_20261108/_fw_selfhash.py
import hashlib

p = r"D:\Project\ra2-campaign-forge\lead\n10c04_ruling_20261108\RULING_STATIC_ORDER.md"
with open(p, "rb") as f:
    data = f.read()
h = hashlib.sha256(data).hexdigest()
print("被核对象 = lead/n10c04_ruling_20261108/RULING_STATIC_ORDER.md")
print("被核对象 SHA256 = " + h + "，字节数 = " + str(len(data)))
