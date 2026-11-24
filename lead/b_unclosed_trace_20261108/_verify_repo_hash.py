# -*- coding: utf-8 -*-
"""_verify_repo_hash.py — 独立复核「全仓实算 SHA256 含/尾接尾串」与字面命中。
与 _bt_repo_scan.py 不复用实现：分块哈希（1 MiB chunk）、按目录分层计数、
显式登记跳过/读取失败/大文件。只读。
运行: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b_unclosed_trace_20261108/_verify_repo_hash.py
"""
import hashlib
import os
import sys
import time

ROOT = r"D:\Project\ra2-campaign-forge"
SKIP_TOP = {".git", "out", "node_modules", ".tmp", "b_unclosed_trace_20261108"}
TAILS = ("26f3fb61829756dfeecf", "b6f95763794")
BTAILS = tuple(t.encode("ascii") for t in TAILS)
HUGE = 500 * 1024 * 1024

n_files = 0
n_bytes = 0
by_top = {}
lit_files = 0
lit_total = 0
hash_hits = []
read_fail = []
skipped_big = []
t0 = time.time()

for dp, dns, fns in os.walk(ROOT):
    # prune skip dirs at any level (same semantics as original: dirname match)
    dns[:] = [d for d in dns if d not in SKIP_TOP]
    for fn in fns:
        p = os.path.join(dp, fn)
        try:
            rel = os.path.relpath(p, ROOT)
        except ValueError as e:
            read_fail.append((p, "relpath:" + str(e)))
            continue
        try:
            sz = os.path.getsize(p)
            if sz > HUGE:
                skipped_big.append((rel, sz))
                continue
        except OSError as e:
            read_fail.append((rel, "stat:" + str(e)))
            continue
        h = hashlib.sha256()
        first = b""
        lit_counts = [0, 0]
        try:
            with open(p, "rb") as f:
                while True:
                    chunk = f.read(1024 * 1024)
                    if not chunk:
                        break
                    if not first:
                        first = chunk
                    h.update(chunk)
                    n_bytes += len(chunk)
                    for k, bt in enumerate(BTAILS):
                        lit_counts[k] += chunk.count(bt)
        except OSError as e:
            read_fail.append((rel, "read:" + str(e)))
            continue
        n_files += 1
        top = rel.split(os.sep)[0]
        by_top[top] = by_top.get(top, 0) + 1
        sha = h.hexdigest()
        for k, t in enumerate(TAILS):
            if lit_counts[k]:
                lit_files += 1
                lit_total += lit_counts[k]
            if sha.endswith(t):
                hash_hits.append((rel, t, "ENDSWITH", sha))
            elif t in sha:
                hash_hits.append((rel, t, "CONTAINS", sha))

print(f"elapsed_sec={time.time()-t0:.1f}")
print(f"scope_files={n_files} scope_bytes={n_bytes}")
print(f"by_top={by_top}")
print(f"lit_files={lit_files} lit_total={lit_total}  (注: 每文件每尾串计 1 文件)")
print(f"hashhit_total={len(hash_hits)}")
for x in hash_hits:
    print("HASHHIT\t" + "\t".join(x))
print(f"skipped_big={len(skipped_big)} {skipped_big[:5]}")
print(f"read_fail={len(read_fail)}")
for x in read_fail[:20]:
    print("READ_FAIL\t" + "\t".join(str(i) for i in x))
# explicit answer for the two tails
for t in TAILS:
    c = sum(1 for x in hash_hits if x[1] == t)
    print(f"HASH_ANSWER\ttail={t}\tcount={c}")
sys.stdout.flush()
