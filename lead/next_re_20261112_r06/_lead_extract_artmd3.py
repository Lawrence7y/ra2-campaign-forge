#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按 CRC 名取 artmd.ini（YR MIX 只存 CRC id）：先顶层，再已知内层容器。"""
import re
import sys
import tempfile
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge")
sys.path.insert(0, str(BASE))
from ra2forge import mixlib  # noqa: E402

GAME = BASE / "ra2youli"
OUT = Path(__file__).resolve().parent / "EVIDENCE_artmd"
OUT.mkdir(exist_ok=True)

INNER_CANDIDATES = ["localmd.mix", "local.mix", "expandmd01.mix", "expandmd98.mix",
                    "ra2md.mix", "ra2.mix", "languagemd.mix", "language.mix"]


def get_from(path, name):
    m = mixlib.MixFile(path)
    try:
        return m.get(name)
    except Exception:
        return None
    finally:
        m.close()


def try_nested(path, depth=0):
    data = get_from(path, "artmd.ini")
    if data:
        return data, f"{path.name}"
    if depth >= 2:
        return None, None
    for inner in INNER_CANDIDATES:
        blob = get_from(path, inner)
        if not blob:
            continue
        with tempfile.NamedTemporaryFile(suffix=".mix", delete=False) as tf:
            tf.write(blob)
            tmp = Path(tf.name)
        d, where = try_nested(tmp, depth + 1)
        if d:
            return d, f"{path.name} -> {where}"
    return None, None


tops = sorted(GAME.glob("*.mix"))
print(f"顶层 MIX {len(tops)} 个，逐个按 CRC 取 artmd.ini\n")

hit = None
for p in tops:
    try:
        d, where = try_nested(p)
    except Exception as e:
        print('    skip', p.name, e); continue
    if d:
        hit = (d, where)
        print(f"  ✓ {where}  -> {len(d)} B")
        break

if not hit:
    print("未命中。列出 ra2md.mix 的前若干条目 id 以便排查：")
    m = mixlib.MixFile(GAME / "ra2md.mix")
    try:
        ids = list(m.names())[:20]
        print("  ", ids)
    finally:
        m.close()
    raise SystemExit(1)

data, where = hit
out = OUT / "artmd.ini"
out.write_bytes(data)
print(f"\n写出 {out} ({len(data)} B)\n")

txt = data.decode("latin-1")
for b in ("NAPOWR", "TESLA", "ATESLA", "NACNST", "GAPOWR"):
    mm = re.search(rf"^\[{b}\](.*?)(?=^\[|\Z)", txt, re.S | re.M | re.I)
    if not mm:
        print(f"[{b}]  未找到")
        continue
    body = mm.group(1)
    f = re.search(r"^\s*Foundation\s*=\s*(\S+)", body, re.M | re.I)
    print(f"[{b}]  Foundation = {f.group(1) if f else '(未设 → 默认)'}")

