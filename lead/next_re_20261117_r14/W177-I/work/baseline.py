#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-I 基线记录：gamemd/ddraw/ddraw.ini/except.txt 的 SHA256+size+mtime + LIVE_LOCK。
只读磁盘；结果写到自身 card/work/baseline_<tag>.json。"""
import hashlib, json, os, subprocess, sys, datetime

BASE = r"D:\Project\ra2-campaign-forge\ra2youli"
CARD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177-I"
LOCK = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\LIVE_LOCK"
FILES = ["gamemd.exe", "ddraw.dll", "ddraw.ini", "except.txt"]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "before"
    rec = {"tag": tag,
           "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
           "files": {}}
    for name in FILES:
        p = os.path.join(BASE, name)
        st = os.stat(p)
        rec["files"][name] = {
            "size": st.st_size,
            "mtime_utc": datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat(),
            "sha256": sha256(p),
        }
    rec["LIVE_LOCK"] = open(LOCK, encoding="utf-8").read().strip()
    out = os.path.join(CARD, "work", "baseline_%s.json" % tag)
    json.dump(rec, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(rec, ensure_ascii=False, indent=2))
    print("saved", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
