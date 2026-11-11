# -*- coding: utf-8 -*-
"""lead/ 既有件零改动证明：对 lead/ 全树（排除本写域目录）做 manifest 指纹。
用法: python -I -X utf8 _manifest.py baseline|final
manifest = sha256( 所有 既有文件的 "相对路径|字节数" 行按路径排序拼接 )，hashlib 实算。
另对 3 个关键既有件做内容级 sha256。
"""
import os
import sys
import hashlib

LEAD = r"D:\Project\ra2-campaign-forge\lead"
SELF = os.path.dirname(os.path.abspath(__file__))

entries = []
for root, dirs, files in os.walk(LEAD):
    if os.path.abspath(root) == SELF:
        dirs[:] = []  # 排除本写域
        continue
    for f in files:
        p = os.path.join(root, f)
        rel = os.path.relpath(p, LEAD).replace("\\", "/")
        entries.append((rel, os.path.getsize(p)))
entries.sort()

buf = "\n".join("%s|%d" % (r, s) for r, s in entries).encode("utf-8")
print("manifest_files=%d" % len(entries))
print("manifest_sha256=%s" % hashlib.sha256(buf).hexdigest())

KEY_FILES = [
    "re_progress_check_20261111/RE_PROGRESS_20261111.md",
    "GOAL_THREE_TARGETS_20261018.md",
    "PENDING_DECISIONS.md",
]
for rel in KEY_FILES:
    p = os.path.join(LEAD, rel.replace("/", os.sep))
    if os.path.isfile(p):
        with open(p, "rb") as fh:
            b = fh.read()
        print("key %s sha256=%s size=%d" % (rel, hashlib.sha256(b).hexdigest(), len(b)))
    else:
        print("key %s MISSING" % rel)
