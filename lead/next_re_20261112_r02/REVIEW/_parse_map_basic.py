# -*- coding: utf-8 -*-
"""按 [Basic] 段正确解析指定地图（修正普查脚本的 name 列 bug）。只读。"""
import glob
import os
import re
import sys

GAME = r"D:\Project\ra2-campaign-forge\ra2youli"
SECT_RE = re.compile(r"(?ims)^\[(\w+)\]\s*$(.*?)(?=^\[|\Z)")


def parse(path):
    d = open(path, "rb").read()
    txt = d.decode("latin1")
    secs = {}
    for m in SECT_RE.finditer(txt):
        secs[m.group(1).lower()] = m.group(2)
    basic = secs.get("basic", "")

    def kv(sec, key):
        m = re.search(r"(?im)^\s*%s\s*=\s*(.*?)\s*$" % key, sec)
        return m.group(1) if m else None

    def cnt(secname):
        body = secs.get(secname.lower())
        if body is None:
            return 0
        return len(re.findall(r"(?m)^\s*\d+\s*=", body))

    return {
        "file": os.path.basename(path),
        "bytes": len(d),
        "sec_names": sorted(secs.keys()),
        "basic_Name": kv(basic, "Name"),
        "Official": kv(basic, "Official"),
        "MaxPlayer": kv(basic, "MaxPlayer"),
        "MinPlayer": kv(basic, "MinPlayer"),
        "GameMode": kv(basic, "GameMode"),
        "units": cnt("Units"),
        "inf": cnt("Infantry"),
        "struct": cnt("Structures"),
        "air": cnt("Aircraft"),
        "has_trig": "triggers" in secs,
    }


targets = sys.argv[1:] or ["HexBay", "SonicHighways"]
for t in targets:
    hits = [p for p in glob.glob(os.path.join(glob.escape(GAME), "*"))
            if os.path.isfile(p) and t.lower() in os.path.basename(p).lower()]
    print("=" * 76)
    print("查询 %r → 命中 %d 个文件" % (t, len(hits)))
    for p in hits:
        r = parse(p)
        print("  文件      : %s  (%d B)" % (r["file"], r["bytes"]))
        print("  [Basic].Name = %r" % r["basic_Name"])
        print("  Official=%r MaxPlayer=%r MinPlayer=%r" % (r["Official"], r["MaxPlayer"], r["MinPlayer"]))
        print("  GameMode  = %r" % r["GameMode"])
        print("  Units=%d Infantry=%d Structures=%d Aircraft=%d  合计=%d"
              % (r["units"], r["inf"], r["struct"], r["air"],
                 r["units"] + r["inf"] + r["struct"] + r["air"]))
        print("  has [Triggers] = %s" % r["has_trig"])
        print("  节数=%d" % len(r["sec_names"]))
