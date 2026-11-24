#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""递归抽取 artmd.ini：ra2md.mix -> 内层 *.mix -> artmd.ini，裁决 Foundation。"""
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


def names_of(path):
    m = mixlib.MixFile(path)
    try:
        return list(m.names())
    finally:
        m.close()


def get_entry(path, name):
    m = mixlib.MixFile(path)
    try:
        return m.get(name)
    finally:
        m.close()


# 1) 找顶层哪个 mix 内含 artmd.ini 或含内层 mix
tops = [p for p in sorted(GAME.glob("*.mix"))]
print(f"顶层 MIX {len(tops)} 个")

target = None
for p in tops:
    try:
        ns = names_of(p)
    except Exception:
        continue
    low = {n.lower(): n for n in ns}
    if "artmd.ini" in low:
        print(f"  ✓ 顶层命中 artmd.ini 于 {p.name}")
        target = (p, low["artmd.ini"])
        break

if target is None:
    # 找内层 mix（名字里带 mix 的条目）
    print("  顶层无 artmd.ini，找内层容器…")
    for p in tops:
        try:
            ns = names_of(p)
        except Exception:
            continue
        inner = [n for n in ns if n.lower().endswith(".mix")]
        if inner:
            print(f"    {p.name}: 内层 {inner}")
            for iname in inner:
                try:
                    blob = get_entry(p, iname)
                except Exception:
                    continue
                with tempfile.NamedTemporaryFile(suffix=".mix", delete=False) as tf:
                    tf.write(blob)
                    tmp = Path(tf.name)
                try:
                    ns2 = names_of(tmp)
                except Exception:
                    continue
                low2 = {n.lower(): n for n in ns2}
                if "artmd.ini" in low2:
                    print(f"      ✓✓ {p.name} -> {iname} -> artmd.ini")
                    target = (tmp, low2["artmd.ini"])
                    break
            if target:
                break

if target is None:
    print("\n!! 仍未找到 artmd.ini，需更深的递归或该镜像把它放在别处")
    raise SystemExit(1)

holder, name = target
data = get_entry(holder, name)
out = OUT / "artmd.ini"
out.write_bytes(data)
print(f"\n写出 {out}  ({len(data)} B)\n")

txt = data.decode("latin-1")
for b in ("NAPOWR", "TESLA", "ATESLA", "NACNST", "GAPOWR", "GAPILE"):
    mm = re.search(rf"^\[{b}\](.*?)(?=^\[|\Z)", txt, re.S | re.M | re.I)
    if not mm:
        print(f"[{b}]  未找到")
        continue
    body = mm.group(1)
    f = re.search(r"^\s*Foundation\s*=\s*(\S+)", body, re.M | re.I)
    print(f"[{b}]  Foundation = {f.group(1) if f else '(未设 → 默认)'}")
