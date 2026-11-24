# -*- coding: utf-8 -*-
"""离线普查：解析 ra2youli 下所有地图的 [Basic]/[Units]/[Infantry]/[Structures]/[Aircraft] 声明量。

目的：不凭文件名，而按**内容**找「声明单位最多」的载体，作为高负载候选。
只读磁盘。
"""
import glob
import hashlib
import os
import re

GAME = r"D:\Project\ra2-campaign-forge\ra2youli"
# 文件名含 []，glob 必须 escape
pat = os.path.join(glob.escape(GAME), "*")
files = [p for p in glob.glob(pat)
         if os.path.isfile(p) and os.path.splitext(p)[1].lower() in (".yrm", ".map", ".mpr")]
print("地图类文件数:", len(files))

SECS = ("Units", "Infantry", "Structures", "Aircraft", "Terrain")


def parse(path):
    d = open(path, "rb").read()
    txt = d.decode("latin1")
    # 名称
    m = re.search(r"(?im)^\s*Name\s*=\s*(.*?)\s*$", txt)
    name = m.group(1) if m else ""
    mx = re.search(r"(?im)^\s*MaxPlayer\s*=\s*(\d+)", txt)
    mn = re.search(r"(?im)^\s*MinPlayer\s*=\s*(\d+)", txt)
    counts = {}
    for s in SECS:
        # 取该节到下一个 [Section] 之间的行
        mm = re.search(r"(?ims)^\[%s\]\s*$(.*?)(?=^\[|\Z)" % s, txt)
        if not mm:
            counts[s] = 0
            continue
        body = mm.group(1)
        # 条目形如  0=OWNER,ID,...
        n = len(re.findall(r"(?m)^\s*\d+\s*=", body))
        counts[s] = n
    has_trig = bool(re.search(r"(?im)^\[Triggers\]", txt))
    return name, (mx.group(1) if mx else ""), (mn.group(1) if mn else ""), counts, has_trig, len(d)


rows = []
for p in files:
    try:
        name, mx, mn, counts, has_trig, size = parse(p)
    except Exception as e:
        print("  解析失败:", os.path.basename(p), e)
        continue
    total = counts["Units"] + counts["Infantry"] + counts["Structures"] + counts["Aircraft"]
    rows.append({
        "file": os.path.basename(p),
        "name": name,
        "maxp": mx, "minp": mn,
        "units": counts["Units"], "inf": counts["Infantry"],
        "struct": counts["Structures"], "air": counts["Aircraft"],
        "total": total, "trig": has_trig, "size": size,
    })

rows.sort(key=lambda r: -r["total"])
print("\n=== 按「声明单位+步兵+建筑+飞机 合计」排序，前 25 ===")
print("%-6s %-6s %-6s %-6s %-6s %-7s %-4s %-8s %s" % (
    "units", "inf", "struct", "air", "total", "maxP", "trig", "bytes", "name / file"))
for r in rows[:25]:
    print("%-6d %-6d %-6d %-6d %-6d %-7s %-4s %-8d %s  [%s]" % (
        r["units"], r["inf"], r["struct"], r["air"], r["total"],
        r["maxp"], "Y" if r["trig"] else "-", r["size"], r["name"][:44], r["file"]))

print("\n=== 统计 ===")
print("合计>0 的地图数:", sum(1 for r in rows if r["total"] > 0))
print("合计>=100 的:", sum(1 for r in rows if r["total"] >= 100))
print("合计>=500 的:", sum(1 for r in rows if r["total"] >= 500))
print("合计最大:", rows[0]["total"], "->", rows[0]["name"], "[", rows[0]["file"], "]")
print("无 [Triggers] 段的（会 ~20s 结束的嫌疑）:", sum(1 for r in rows if not r["trig"]))

out = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r02\W16_map_census\MAP_CENSUS.tsv"
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write("file\tname\tmaxp\tminp\tunits\tinf\tstruct\tair\ttotal\thas_trig\tbytes\n")
    for r in rows:
        f.write("%s\t%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%s\t%d\n" % (
            r["file"], r["name"], r["maxp"], r["minp"], r["units"], r["inf"],
            r["struct"], r["air"], r["total"], "Y" if r["trig"] else "N", r["size"]))
print("\n已落盘:", out)
