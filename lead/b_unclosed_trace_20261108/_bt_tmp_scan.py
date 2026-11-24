# -*- coding: utf-8 -*-
"""_bt_tmp_scan.py — 补扫 .tmp/（主扫描跳过目录）字面+摘要猎尾，只读。"""
import hashlib, os, sys
ROOT = r"D:\Project\ra2-campaign-forge\.tmp"
TAILS = [b"26f3fb61829756dfeecf", b"b6f95763794"]
n=0; hits=[]
for dp, dn, fns in os.walk(ROOT):
    for fn in fns:
        p=os.path.join(dp,fn)
        try: data=open(p,"rb").read()
        except OSError as e:
            print("READ_FAIL",p,e); continue
        n+=1
        sha=hashlib.sha256(data).hexdigest()
        for tail in TAILS:
            ts=tail.decode()
            c=data.count(tail)
            if c: hits.append(f"LIT {os.path.relpath(p,ROOT)} {ts} count={c}")
            if ts in sha: hits.append(f"HASH {os.path.relpath(p,ROOT)} {ts} {sha}")
print(f"tmp_files={n}")
for h in hits: print(h)
print(f"tmp_hits={len(hits)}")
