# -*- coding: utf-8 -*-
"""汇总 Mimosa 最新扫描的 23 处 high，按目录与规则归类，供裁决 12 审视。"""
import json
import collections
from pathlib import Path

P = Path(r"C:/Users/Administrator/.mimosa/security-scans/"
         r"project-58d54c8400d61bac27a417b2/"
         r"scan-2026-10-22T04-33-44.241Z-23b228f990d6/findings.json")

d = json.loads(P.read_text(encoding="utf-8"))
fs = d["findings"]
print("scanId :", d["scanId"])
print("totals :", json.dumps(d["totals"], ensure_ascii=False))
print("n      :", len(fs))

def norm(p: str) -> str:
    return p.replace("\\", "/")

def top_dir(fp: str) -> str:
    parts = norm(fp).split("/")
    return parts[0] if len(parts) > 1 else fp

print()
print("=== by top-level dir ===")
c = collections.Counter()
for f in fs:
    loc = f.get("location") or {}
    fp = loc.get("file") or loc.get("path") or ""
    c[top_dir(fp)] += 1
for k, v in c.most_common():
    print(f"  {v:>3}  {k}")

print()
print("=== by title (rule) ===")
for k, v in collections.Counter(f.get("title", "") for f in fs).most_common():
    print(f"  {v:>3}  {k}")

print()
print("=== by severity ===")
for k, v in collections.Counter(f.get("severity", "") for f in fs).most_common():
    print(f"  {v:>3}  {k}")

print()
print("=== full list ===")
for i, f in enumerate(fs, 1):
    loc = f.get("location") or {}
    fp = norm(loc.get("file") or loc.get("path") or "?")
    ln = loc.get("line") or loc.get("startLine") or "?"
    print(f"{i:>3}. [{f.get('severity')}] {f.get('title')}")
    print(f"     {fp}:{ln}")
    msg = (f.get("message") or "").replace("\n", " ")
    print(f"     {msg[:200]}")
