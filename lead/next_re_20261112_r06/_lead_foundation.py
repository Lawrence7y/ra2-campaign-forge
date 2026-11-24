#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 裁决：NAPOWR / TESLA / NACNST / GAPOWR 的 Foundation 到底是多少？
直接从未压缩的 mix 或已提取的 artmd.ini 里读，不用任何二手转述。
"""
import re
import struct
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge")


def find_artmd():
    cands = list(BASE.glob("**/artmd.ini"))
    cands = [c for c in cands if c.stat().st_size > 50_000]
    return sorted(cands, key=lambda p: -p.stat().st_size)[:5]


print("=== 候选 artmd.ini ===")
for c in find_artmd():
    print(f"  {c}  {c.stat().st_size} B")

# 尝试直接读最大的那份
cands = find_artmd()
if not cands:
    print("!! 未找到 artmd.ini，需要从 MIX 提取")
    raise SystemExit(1)

p = cands[0]
txt = p.read_text(encoding="latin-1")
print(f"\n使用 {p.name} ({len(txt)} 字符)\n")


def section(name):
    m = re.search(rf"^\[{re.escape(name)}\](.*?)(?=^\[|\Z)", txt, re.S | re.M | re.I)
    return m.group(1) if m else None


for b in ("NAPOWR", "TESLA", "NACNST", "GAPOWR", "ATESLA"):
    body = section(b)
    if body is None:
        print(f"[{b}]  —— 未找到")
        continue
    fnd = re.search(r"^\s*Foundation\s*=\s*(\S+)", body, re.M | re.I)
    print(f"[{b}] Foundation = {fnd.group(1) if fnd else '(未设，用默认)'}")
    # 打印该段前几行便于核查
    lines = [l.strip() for l in body.strip().splitlines() if l.strip()][:6]
    for l in lines:
        print("      ", l)
    print()
