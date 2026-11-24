#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 ra2youli 的 MIX 中抽取 artmd.ini，裁决 NAPOWR/TESLA/NACNST/GAPOWR 的 Foundation。

用 ra2forge.mixlib（项目自带，已验证可读 YR MIX）。
"""
import re
import sys
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge")
sys.path.insert(0, str(BASE))

from ra2forge import mixlib  # noqa: E402

GAME = BASE / "ra2youli"
OUT = Path(__file__).resolve().parent / "EVIDENCE_artmd"
OUT.mkdir(exist_ok=True)

TARGET = "artmd.ini"


def try_mix(path: Path):
    try:
        m = mixlib.MixFile(path)
    except Exception as e:
        return None
    try:
        names = [n for n in m.names() ] if hasattr(m, "names") else []
    except Exception:
        names = []
    return m if names else m


def main():
    mixes = sorted(GAME.glob("*.mix"))
    print(f"扫描 {len(mixes)} 个 MIX 找 {TARGET}\n")
    found = []
    for p in mixes:
        try:
            m = mixlib.MixFile(p)
        except Exception:
            continue
        # 尝试按名取
        try:
            data = m.get_file(TARGET)
        except Exception:
            data = None
        if data:
            found.append((p.name, len(data), data))
            print(f"  ✓ {p.name}  -> {len(data)} B")
    if not found:
        print("主 MIX 未直接命中，尝试 expandmd*.mix / localmd.mix 等")
        for p in mixes:
            print("   ", p.name)
        return 1

    # 用最大的那份
    found.sort(key=lambda t: -t[1])
    name, size, data = found[0]
    out = OUT / f"artmd_from_{name}.ini"
    out.write_bytes(data)
    print(f"\n写出 {out}  ({size} B)\n")

    txt = data.decode("latin-1")
    for b in ("NAPOWR", "TESLA", "ATESLA", "NACNST", "GAPOWR"):
        mm = re.search(rf"^\[{b}\](.*?)(?=^\[|\Z)", txt, re.S | re.M | re.I)
        if not mm:
            print(f"[{b}]  未找到")
            continue
        body = mm.group(1)
        f = re.search(r"^\s*Foundation\s*=\s*(\S+)", body, re.M | re.I)
        print(f"[{b}]  Foundation = {f.group(1) if f else '(未设 -> 默认 1x1)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
