import os
import datetime

base = "D:/Project/ra2-campaign-forge"
cut = datetime.datetime(2026, 11, 8).timestamp()
dom = "lead/a_residual_n1_20261108"
hits = []
for root, dirs, files in os.walk(base):
    relroot = os.path.relpath(root, base).replace(os.sep, "/")
    if relroot == ".":
        relroot = ""
    dirs[:] = [d for d in dirs if d != ".git"]
    for f in files:
        full = os.path.join(root, f)
        try:
            rel = os.path.relpath(full, base).replace(os.sep, "/")
        except ValueError:
            continue
        if rel.startswith(dom + "/"):
            continue
        try:
            m = os.stat(full).st_mtime
        except (OSError, ValueError):
            continue
        if m >= cut:
            hits.append((datetime.datetime.fromtimestamp(m).isoformat(), rel))
for h in sorted(hits):
    print(h[0], h[1])
print("TOTAL:", len(hits))
