# -*- coding: utf-8 -*-
"""_ow_sweep.py — 旧措辞普查（只读扫 lead/，带剪枝与深度上限；无文件写，仅 stdout）
运行：python -I -X utf8 <绝对路径> > <写域>\_ow_raw_hits.json
"""
import os, json, time, hashlib

ROOT = r"D:\Project\ra2-campaign-forge\lead"

ORCH_PAT = ["同一持续根因", "持续根因", "D:\lead", "路径异常", "句柄横跨", "ACL 横跨"]
ORCH_PAT[2] = "AV 瞬时锁"
EXTRA_PAT = [
    "AV瞬时锁", "瞬时锁", "持久根因",
    "句柄/ACL", "句柄被占", "独占句柄", "游戏句柄", "握句柄",
    "同根因", "同一根因",
    "横跨两时点", "横跨 pre", "横跨 post", "横跨pre", "横跨post",
    "显然可达", "必然同源", "必然可达", "会虚报",
]
ALL_PAT = sorted(set(ORCH_PAT + EXTRA_PAT), key=len, reverse=True)

SKIP_DIRS = {".git", "__pycache__", "node_modules", "node_modules2", ".venv", ".idea", ".vscode", ".tmp"}
SKIP_DIRS.discard("node_modules2")
MAXDEPTH = 5
MAX_BYTES = 8 * 1024 * 1024
TEXT_EXT = {".md", ".txt", ".py", ".json"}

t0 = time.perf_counter()
dirsVisited = filesScanned = mdScanned = skippedDepth = skippedExt = skippedBig = 0
decodeErr = []
fileMeta = {}
hits = []
depthCount = {}

for dirpath, dirnames, filenames in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    depth = 0 if rel == "." else rel.count(os.sep) + 1
    dirsVisited = dirsVisited + 1
    dirnames[:] = [d for d in dirnames if d not in utf8(dirnames) or True] if False else [d for d in dirnames if d not in SKIP_DIRS]
    if depth >= MAXDEPTH:
        skippedDepth = skippedDepth + len(dirnames)
        dirnames[:] = []
    for fn in filenames:
        ext = os.path.splitext(fn)[1].lower()
        full = dirpath + os.sep + fn
        try:
            sz = os.path.getsize(full)
        except OSError:
            continue
        if ext not in TEXT_EXT:
            skippedExt = skippedExt + 1
            continue
        if sz > MAX_BYTES > 0:
            skippedBig = skippedBig + 1
            continue
        relf = full[len(ROOT) + 1:].replace("\\", "/")
        depthCount[str(depth)] = depthCount.get(str(depth), 0) + 1
        if ext == ".md":
            mdScanned = mdScanned + 1
        try:
            with open(full, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        txt = raw.decode("utf-8", errors="replace")
        if "\ufffd" in txt:
            decodeErr.append(relf)
        fileMeta[relf] = {"bytes": sz, "sha256": hashlib.sha256(raw).hexdigest()}
        filesScanned = filesScanned + 1
        for i, line in enumerate(txt.splitlines(), 1):
            pats = [p for p in ALL_PAT if p in line]
            if pats:
                hits.append({"file": relf, "line": i, "pats": pats, "text": line.strip()[:400]})

elapsed = time.perf_counter() - t0

meta = {
    "root": ROOT, "maxdepth": MAXDEPTH, "skip_dirs": sorted(SKIP_DIRS),
    "max_bytes": MAX_BYTES, "text_ext": sorted(TEXT_EXT),
    "patterns": ALL_PAT, "orchestrator_patterns": ORCH_PAT,
    "dirsVisited": dirsVisited, "filesScanned": filesScanned, "mdScanned": mdScanned,
    "skippedDepthDirs": skippedDepth, "skippedExtFiles": skippedExt, "skippedBigFiles": skippedBig,
    "decodeErrFiles": decodeErr, "depthFileCount": depthCount,
    "elapsedSec": round(elapsed, 3),
    "hitCount": len(hits), "hitFiles": len({h["file"] for h in hits}),
}

print(json.dumps({"meta": meta, "fileMeta": fileMeta, "hits": hits}, ensure_ascii=False, indent=1))
