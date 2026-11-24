# -*- coding: utf-8 -*-
"""_integ_make_isolated.py — 任务项 1：候选 → 隔离副本逐字节复制。

源（只读，不改一字）：lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py
目标（唯一写域）：  lead/b2b_isolated_20261107/qc151_trip.isolated.py
复制后实算双方 SHA256+字节数并断言逐字节同一；母本不在本脚本触达范围内。
"""
import hashlib
from pathlib import Path
from shutil import copyfile

ROOT = Path("D:/Project/ra2-campaign-forge")
SRC = ROOT / "lead/b2b_candidate_lf_20261107/qc151_trip.candidate_lf.py"
DST = ROOT / "lead/b2b_isolated_20261107/qc151_trip.isolated.py"


def fp(p: Path):
    d = p.read_bytes()
    return hashlib.sha256(d).hexdigest(), len(d)


h1, b1 = fp(SRC)
copyfile(SRC, DST)
h2, b2 = fp(DST)
print(f"源(候选，只读): {SRC}")
print(f"  sha256 = {h1}")
print(f"  字节数 = {b1}")
print(f"隔离副本(写域): {DST}")
print(f"  sha256 = {h2}")
print(f"  字节数 = {b2}")
same = (h1 == h2) and (b1 == b2)
print("COPY_IDENTICAL =", same)
raise SystemExit(0 if same else 1)
