# -*- coding: utf-8 -*-
# 探针D：合并嫌疑模式——docstring 通配、os.walk、os.stat、realpath、星号 join、sha256 读流
import hashlib
import os

BASE = "D:/Project/ra2-campaign-forge"
ROOT = BASE + "/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
DOC = """从原始语料 measure_w*.json 重算（docstring 通配测试）"""

def safe_path(*parts):
    p = os.path.realpath(os.path.join(*[str(x) for x in parts]))
    return p

def sha256_file(p):
    h = hashlib.sha256()
    with open(safe_path(p), "rb") as fh:
        for blk in iter(lambda: fh.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()

n = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        if fn.startswith("measure_w") and fn.endswith(".json"):
            st = os.stat(os.path.join(dirpath, fn)).st_mtime
            n += 1
h1 = sha256_file(ROOT + "/archive_T32/measure_w0.json")
print("D ok", n, DOC[:12], h1[:16])
