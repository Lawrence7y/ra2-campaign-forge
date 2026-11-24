# -*- coding: utf-8 -*-
"""_owv_sweep.py — 复核员独立重跑旧措辞普查（只读；全扩展名、多编码解码、深路径上限 12；无文件写，仅 stdout）。
运行：python -I -X utf8 <本文件绝对路径> > <写域>\\_owv_raw_hits.json
"""
import os, json, time, sys

ROOT = r"D:/Project/ra2-campaign-forge/lead"
SELF_DOMAIN = "oldwording_sweep_20261109"

# —— 编排方 25 模式（_ow_sweep.py:9-17 原样转录）——
ORCH_PAT = ["同一持续根因", "持续根因", "AV 瞬时锁", "路径异常", "句柄横跨", "ACL 横跨"]
EXTRA_PAT = [
    "AV瞬时锁", "瞬时锁", "持久根因",
    "句柄/ACL", "句柄被占", "独占句柄", "游戏句柄", "握句柄",
    "同根因", "同一根因",
    "横跨两时点", "横跨 pre", "横跨 post", "横跨pre", "横跨post",
    "显然可达", "必然同源", "必然可达", "会虚报",
]
# —— 复核员补充变体模式（验证「严格超集」并抓漏网变体）——
MINE_PAT = [
    "造成两半", "两半", "双时点", "两时点", "横跨", "持续性根因",
    "部分同源", "源读面", "根因横跨", "跨两时点", "同根",
    "句柄占用", "ACL损坏", "ACL 损坏", "同一持久根因", "一因双时点",
    "跨 pre", "跨 post", "横跨时点",
]
ALL_PAT = sorted(set(ORCH_PAT + EXTRA_PAT + MINE_PAT), key=len, reverse=True)

SKIP_DIRS = {".git"}
MAXDEPTH = 12
MAX_BYTES = 8 * 1024 * 1024


def decode_text(raw):
    for enc in ("utf-8-sig", "gbk", "utf-16"):
        try:
            return raw.decode(enc), enc
        except (UnicodeDecodeError, UnicodeError):
            pass
    return raw.decode("utf-8", errors="replace"), "utf-8-replace"


t0 = time.perf_counter()
dirsVisited = filesScanned = 0
skippedBig = []
walkErrors = []
depthHist = {}
hits = []


def on_walk_err(e):
    walkErrors.append(str(e))


for dirpath, dirnames, filenames in os.walk(ROOT, onerror=on_walk_err):
    rel = os.path.relpath(dirpath, ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    dirsVisited += 1
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    if depth >= MAXDEPTH:
        dirnames[:] = []
    for fn in filenames:
        full = dirpath + os.sep + fn
        try:
            sz = os.path.getsize(full)
        except OSError:
            continue
        if sz > MAX_BYTES:
            skippedBig.append(full[len(ROOT) + 1:].replace("\\", "/"))
            continue
        relf = full[len(ROOT) + 1:].replace("\\", "/")
        depthHist[str(depth)] = depthHist.get(str(depth), 0) + 1
        try:
            with open(full, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        filesScanned += 1
        txt, enc = decode_text(raw)
        selfdom = relf.startswith(SELF_DOMAIN)
        for i, line in enumerate(txt.splitlines(), 1):
            pats = [p for p in ALL_PAT if p in line]
            if pats:
                hits.append({"file": relf, "line": i, "pats": pats,
                             "self": selfdom, "enc": enc, "text": line.strip()[:300]})

elapsed = time.perf_counter() - t0
self_hits = [h for h in hits if h["self"]]
meta = {
    "root": ROOT, "maxdepth": MAXDEPTH, "skip_dirs": sorted(SKIP_DIRS),
    "max_bytes": MAX_BYTES,
    "patternCount": len(ALL_PAT), "orchPatternCount": len(ORCH_PAT) + len(EXTRA_PAT),
    "dirsVisited": dirsVisited, "filesScanned": filesScanned,
    "skippedBigFiles": skippedBig, "walkErrors": walkErrors[:20],
    "depthFileCount": depthHist,
    "elapsedSec": round(elapsed, 3),
    "hitCountAll": len(hits), "hitCountSelfDomain": len(self_hits),
    "hitCountExclSelfDomain": len(hits) - len(self_hits),
    "hitFilesAll": len({h["file"] for h in hits}),
}
print(json.dumps({"meta": meta, "hits": hits}, ensure_ascii=False))
