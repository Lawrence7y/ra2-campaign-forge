# -*- coding: utf-8 -*-
# _c7_probe3.py — 环安全+进度输出的全仓 ACCEPTANCE_RECORDS.json 查找
import hashlib, os, sys, time

ROOT = r"D:\Project\ra2-campaign-forge"
t0 = time.time()
hits = []
dirs_visited = 0
real_seen = set()
stack = [ROOT]
pruned = []
while stack:
    d = stack.pop()
    try:
        rd = os.path.realpath(d)
    except OSError:
        continue
    if rd in real_seen:
        pruned.append(d)
        continue
    real_seen.add(rd)
    try:
        it = os.scandir(d)
        names = []
        for e in it:
            names.append((e.name, e.is_dir(follow_symlinks=False)))
    except OSError:
        continue
    dirs_visited += 1
    if dirs_visited % 200 == 0:
        sys.stderr.write("progress dirs=%d elapsed=%.1fs stack=%d\n" % (dirs_visited, time.time() - t0, len(stack)))
        sys.stderr.flush()
    for name, isdir in names:
        p = os.path.join(d, name)
        if isdir:
            stack.append(p)
        elif name == "ACCEPTANCE_RECORDS.json":
            try:
                n = os.path.getsize(p)
                with open(p, "rb") as f:
                    h = hashlib.sha256(f.read()).hexdigest()
            except OSError as e:
                n, h = -1, "ERR:" + str(e)
            hits.append((os.path.relpath(p, ROOT).replace("\\", "/"), n, h))
            sys.stderr.write("HIT %s\n" % os.path.relpath(p, ROOT))
            sys.stderr.flush()

print("== A. 全仓（环安全 walk，follow_symlinks=False）ACCEPTANCE_RECORDS.json ==")
for rel, n, h in sorted(hits):
    print("HIT %s bytes=%d sha256=%s" % (rel, n, h))
print("dirsVisited=%d  cyclePruned=%d  elapsed=%.1fs" % (dirs_visited, len(pruned), time.time() - t0))
