# -*- coding: utf-8 -*-
"""_bt_repo_scan.py — 只读两查：
(1) 全仓字面扫描两个尾串（字节级，修正 grep -I 会把 mjs 误判二进制漏检的问题）；
(2) 猎尾：对 scope 内每件实算 SHA256（hashlib），查摘要是否含/尾接两尾串。
scope = 仓库根全树，跳过 .git、out、node_modules、本写域(lead/b_unclosed_trace_20261108)、.tmp。
运行: python -I -X utf8 D:/Project/ra2-campaign-forge/lead/b_unclosed_trace_20261108/_bt_repo_scan.py
"""
import hashlib
import os
import sys

ROOT = r"D:\Project\ra2-campaign-forge"
SKIP_DIRS = {".git", "out", "node_modules", ".tmp", "b_unclosed_trace_20261108"}
TAILS = [b"26f3fb61829756dfeecf", b"b6f95763794"]
HUGE = 500 * 1024 * 1024

lit_hits = []   # (relpath, tail, [lines])
hash_hits = []  # (relpath, tail, kind, sha)
n_files = 0
n_bytes = 0
skipped = []

for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        try:
            rel = os.path.relpath(p, ROOT)
        except ValueError as e:
            skipped.append(f"{p!r} relpath_error:{e}")
            continue
        try:
            if os.path.getsize(p) > HUGE:
                skipped.append(rel)
                continue
            with open(p, "rb") as f:
                data = f.read()
        except OSError as e:
            print(f"READ_FAIL\t{rel}\t{e}")
            continue
        n_files += 1
        n_bytes += len(data)
        # (1) 字面命中
        for tail in TAILS:
            idxs = []
            i = data.find(tail)
            while i != -1:
                idxs.append(i)
                i = data.find(tail, i + 1)
            if idxs:
                lines = sorted({data.count(b"\n", 0, x) + 1 for x in idxs})
                lit_hits.append((rel, tail.decode(), len(idxs), lines))
        # (2) 摘要猎尾
        sha = hashlib.sha256(data).hexdigest()
        for tail in TAILS:
            ts = tail.decode()
            if sha.endswith(ts):
                hash_hits.append((rel, ts, "ENDSWITH", sha))
            elif ts in sha:
                hash_hits.append((rel, ts, "CONTAINS", sha))

print(f"scope_files={n_files} scope_bytes={n_bytes} skipped_huge={skipped}")
print("--- 字面命中清单 ---")
for rel, tail, cnt, lines in lit_hits:
    print(f"LIT\t{rel}\t{tail}\tcount={cnt}\tlines={lines[:12]}")
print(f"lit_files={len(set(x[0] for x in lit_hits))} lit_total={sum(x[2] for x in lit_hits)}")
print("--- 摘要猎尾结果 ---")
for rel, ts, kind, sha in hash_hits:
    print(f"HASHHIT\t{rel}\t{ts}\t{kind}\t{sha}")
print(f"hashhit_total={len(hash_hits)}")
sys.stdout.flush()
