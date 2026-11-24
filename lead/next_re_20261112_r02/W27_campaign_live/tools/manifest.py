#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""W27 helper: byte-exact manifest of a directory tree (read-only).

Usage: python manifest.py <root> <out.json>
Writes {root, file_count, total_bytes, maplike_count, files:[{rel,size,mtime_ns,sha256}]}.
maplike_count = .yrm + .mpr + .map (the metric Lead pins at 277 for ra2youli).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

MAPLIKE = {".yrm", ".mpr", ".map"}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(root: str, out: str) -> int:
    r = Path(root)
    rows = []
    total = 0
    maplike = 0
    for dirpath, _dirnames, filenames in os.walk(r):
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                st = p.stat()
            except OSError:
                continue
            rel = str(p.relative_to(r))
            rows.append({
                "rel": rel,
                "size": st.st_size,
                "mtime_ns": st.st_mtime_ns,
                "sha256": sha256_file(p),
            })
            total += st.st_size
            if Path(fn).suffix.lower() in MAPLIKE:
                maplike += 1
    rows.sort(key=lambda d: d["rel"].lower())
    payload = {
        "root": str(r),
        "file_count": len(rows),
        "total_bytes": total,
        "maplike_count": maplike,
        "files": rows,
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                         encoding="utf-8")
    print(json.dumps({k: payload[k] for k in
                      ("root", "file_count", "total_bytes", "maplike_count")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
