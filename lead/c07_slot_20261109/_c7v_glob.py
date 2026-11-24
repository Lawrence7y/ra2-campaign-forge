# -*- coding: utf-8 -*-
# _c7v_glob.py — 复核员独立全仓查找 ACCEPTANCE_RECORDS.json（环安全：reparse/junction 不深入 + visited 去重 + 深度上限）
import hashlib, os, sys, time

ROOT = r"D:\Project\ra2-campaign-forge"
TARGET = "ACCEPTANCE_RECORDS.json"
MAX_DEPTH = 60
time0 = time.time()

FILE_ATTRIBUTE_REPARSE_POINT = 0x400
hits = []
dirs_visited = 0
pruned = 0
stack = [(ROOT, 0)]
seen = set()

while stack:
    cur, depth = stack.pop()
    if depth > MAX_DEPTH:
        pruned += 1
        continue
    try:
        st = os.stat(cur)
    except OSError:
        continue
    key = (st.st_dev, getattr(st, "st_ino", 0))
    if key in seen:
        pruned += 1
        continue
    seen.add(key)
    dirs_visited += 1
    try:
        with os.scandir(cur) as it:
            for e in it:
                name = e.name
                try:
                    is_dir = e.is_dir(follow_symlinks=False)
                    # Windows: junction/reparse 点也剪枝，防环
                    if is_dir and hasattr(e, "stat"):
                        try:
                            est = e.stat(follow_symlinks=False)
                            if getattr(est, "st_file_attributes", 0) & FILE_ATTRIBUTE_REPARSE_POINT:
                                pruned += 1
                                continue
                        except OSError:
                            pruned += 1
                            continue
                except OSError:
                    continue
                if name == TARGET and not is_dir:
                    p = e.path
                    try:
                        data = open(p, "rb").read()
                        hits.append((os.path.relpath(p, ROOT), len(data), hashlib.sha256(data).hexdigest()))
                    except OSError as ex:
                        hits.append((os.path.relpath(p, ROOT), -1, str(ex)))
                elif is_dir:
                    stack.append((e.path, depth + 1))
    except OSError:
        continue

print("walk dirsVisited=%d pruned=%d elapsed=%.1fs" % (dirs_visited, pruned, time.time() - time0))
print("hits=%d" % len(hits))
for rel, n, d in sorted(hits):
    print("  %s | bytes=%d | sha256=%s" % (rel, n, d))

p23 = os.path.join(ROOT, "lead", "nextstep_plan_20261106", "ACCEPTANCE_RECORDS.json")
print("NEXT:23 literal path exists =", os.path.exists(p23))
