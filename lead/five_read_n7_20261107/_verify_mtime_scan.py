# -*- coding: utf-8 -*-
"""扫描近 90 分钟内被修改的仓库文件，复核是否有写域外改动。只读。"""
import os
import time

now = time.time()
WIN = 5400
hits = []
root = os.path.abspath(r"D:\Project\ra2-campaign-forge")
SKIP = {".git", ".mimosa", "node_modules", "__pycache__"}
for dp, dns, fns in os.walk(root):
    dns[:] = [d for d in dns if d not in SKIP]
    for f in fns:
        p = os.path.join(dp, f)
        try:
            m = os.stat(p).st_mtime
        except OSError:
            continue
        if now - m < WIN:
            rel = os.path.relpath(p, root)
            hits.append((m, rel.replace(os.sep, "/")))
hits.sort()
print("recent(<90min) file count =", len(hits))
for m, p in hits:
    print(" ", time.strftime("%H:%M:%S", time.localtime(m)), p)
outside = [p for m, p in hits if not p.startswith("lead/five_read_n7_20261107/")]
print("OUTSIDE write-domain count =", len(outside))
for p in outside:
    print("  OUTSIDE:", p)
