#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W17 attempt2 对账：ra2youli 全部地图文件的 [Basic].Name vs 列表实测 268 条。

目的（attempt1/2 教训）： skirmish 列表显示名来源未知，官方图显示本地化中文名、
部分自定图显示 GBK 逐字节零扩展的伪 Unicode。本脚本离线对账：
  1) 解析 ra2youli 每张图的 [Basic] Name/MaxPlayer/MinPlayer/MultiplayerOnly/Official；
  2) 对列表项做 GBK 恢复（全字符 ≤0xFF 时按 latin-1 取字节再 GBK 解码）；
  3) 双向匹配，输出：列表中未匹配项、文件中未上列表项、B 的下落。
只读，写 W17_load_B/maplist_reconcile.json。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(r"D:\Project\ra2-campaign-forge")
GAME_DIR = ROOT / "ra2youli"
W17 = ROOT / "lead" / "next_re_20261112_r02" / "W17_load_B"

B_FILENAME = "[8]音速公路_SonicHighways.yrm"


def parse_basic(raw: bytes):
    """从地图字节流提取 [Basic] 段关键字段（ASCII/GBK 混合容错）。
    注意：Name 可能含 '['（如 "[8] Sonic Highways"），段体须截到"行首 ["为止。"""
    out = {}
    m = re.search(rb"\[Basic\]\s*\r?\n(.*?)(?=\r?\n\[|\Z)", raw, re.S)
    if not m:
        return None
    body = m.group(1) or b""
    for key in (b"Name", b"MaxPlayer", b"MinPlayer", b"MultiplayerOnly",
                b"Official", b"GameMode", b"NewINIFormat"):
        km = re.search(rb"^" + key + rb"\s*=\s*([^\r\n]*)", body, re.M)
        if km:
            v = km.group(1)
            try:
                out[key.decode()] = v.decode("gbk", "replace").strip()
            except Exception:
                out[key.decode()] = v.decode("latin-1", "replace").strip()
    return out


def gbk_recover(s: str):
    """列表项 GBK 伪 Unicode 恢复：全字符 ≤0xFF → 逐字符取低字节 → GBK 解码。"""
    if not s or any(ord(c) > 0xFF for c in s):
        return None
    b = bytes(ord(c) & 0xFF for c in s)
    try:
        t = b.decode("gbk")
    except Exception:
        return None
    if any(c in "\ufffd" for c in t):
        return None
    return t


def main():
    entries = json.loads((W17 / "out" / "maplist_names.json")
                         .read_text(encoding="utf-8"))
    for e in entries:
        e["gbk"] = gbk_recover(e["name"])

    files = {}
    for p in sorted(GAME_DIR.iterdir()):
        if p.suffix.lower() not in (".yrm", ".mpr", ".map"):
            continue
        raw = p.read_bytes()
        basic = parse_basic(raw)
        files[p.name] = {"bytes": len(raw), "basic": basic}
    # 出现在列表里的名字集合（raw + gbk 恢复，去空）
    list_names = set()
    for e in entries:
        for k in ("name", "gbk"):
            if e.get(k):
                list_names.add(e[k].strip())

    unmatched_files = []
    matched = {}
    for fn, info in files.items():
        b = info.get("basic") or {}
        nm = (b.get("Name") or "").strip()
        hit = nm in list_names if nm else False
        matched[fn] = {"basic_name": nm, "in_list": hit,
                       "maxp": b.get("MaxPlayer"), "minp": b.get("MinPlayer"),
                       "mp_only": b.get("MultiplayerOnly"),
                       "official": b.get("Official")}
        if not hit:
            unmatched_files.append(fn)

    unmatched_entries = []
    all_basic_names = {((files[f].get("basic") or {}).get("Name") or "").strip()
                       for f in files}
    for e in entries:
        cands = [e.get("name"), e.get("gbk")]
        ok = any(c and c.strip() in all_basic_names for c in cands if c)
        if not ok:
            unmatched_entries.append({"index": e["index"], "name": e["name"],
                                      "gbk": e["gbk"]})

    binfo = files.get(B_FILENAME, {})
    print("files=%d entries=%d" % (len(files), len(entries)))
    print("files matched into list: %d ; files NOT in list: %d"
          % (len(files) - len(unmatched_files), len(unmatched_files)))
    print("B file basic=%s" % json.dumps(binfo.get("basic"), ensure_ascii=False))
    print("B in list:", matched.get(B_FILENAME, {}).get("in_list"))
    print("--- unmatched files (%d) ---" % len(unmatched_files))
    for fn in unmatched_files:
        m = matched[fn]
        print("  %-46s name=%r maxp=%s mp_only=%s official=%s"
              % (fn, m["basic_name"], m["maxp"], m["mp_only"], m["official"]))
    print("--- unmatched entries (%d) ---" % len(unmatched_entries))
    for e in unmatched_entries:
        print("  [%3d] raw=%r gbk=%r" % (e["index"], e["name"], e["gbk"]))

    (W17 / "maplist_reconcile.json").write_text(
        json.dumps({"entries": entries, "files": files,
                    "matched": matched,
                    "unmatched_files": unmatched_files,
                    "unmatched_entries": unmatched_entries},
                   ensure_ascii=False, indent=1),
        encoding="utf-8")
    print("written maplist_reconcile.json")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
