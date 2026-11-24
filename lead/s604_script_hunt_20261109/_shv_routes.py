# _shv_routes.py — 复核员三路独立搜索（R1 文件名 / R2 内容锐针 / R3 TEMP+回收站）
# 只读；带剪枝、深度上限、时间预算；每路输出 dirsVisited/filesSeen/耗时/命中
import os, time, sys

T0 = time.time()
BUDGET = 280.0  # 秒，总预算

PRUNE_DIRS = {".git", "node_modules", "__pycache__", "$RECYCLE.BIN", "System Volume Information"}
MAXDEPTH = 8
NEEDLE_SHARP = "dur={fe[i][0]"           # 生成器错误行锐针
NEEDLE_B = "dur={fe[i][0]:(fe[i][1]-fe[i-1][1])*1000.0"  # 完整错误行
NEEDLES_TEXT = ["IS_PREFIX_EXT True", "慢1/3 − 快1/3", "空档差"]

def within_budget():
    return (time.time() - T0) < BUDGET

def walk_pruned(root, maxdepth):
    """yield (dirpath, dirnames, filenames); 统计 dirsVisited"""
    dirs_seen = 0
    root = os.path.abspath(root)
    stack = [(root, 0)]
    while stack:
        cur, d = stack.pop()
        dirs_seen += 1
        try:
            entries = list(os.scandir(cur))
        except OSError:
            yield (cur, [], [], dirs_seen)
            continue
        subdirs, files = [], []
        for e in entries:
            try:
                if e.is_dir(follow_symlinks=False):
                    subdirs.append(e.name)
                else:
                    files.append((e.name, e.stat().st_size, e.stat().st_mtime))
            except OSError:
                pass
        yield (cur, subdirs, files, dirs_seen)
        if d + 1 < maxdepth:
            for s in subdirs:
                if s not in PRUNE_DIRS:
                    stack.append((os.path.join(cur, s), d + 1))

# ---------- R1 仓库文件名搜索 ----------
print("=== R1 repo filename search (604/slowframe/gapdiff), maxdepth=%d ===" % MAXDEPTH)
hits1, dirs1, files1 = [], 0, 0
KEYS = ("604", "slowframe", "gapdiff", "gap_diff")
for cur, subdirs, files, seen in walk_pruned("D:/Project/ra2-campaign-forge", MAXDEPTH):
    dirs1 = seen
    files1 += len(files)
    if not within_budget():
        print("BUDGET STOP R1"); break
    for name, size, mt in files:
        ln = name.lower()
        if any(k in ln for k in KEYS):
            hits1.append((cur.replace("D:/Project/ra2-campaign-forge/", "").replace("\\", "/") + "/" + name, size, mt))
print("R1 dirsVisited=%d filesSeen=%d elapsed=%.1fs hits=%d" % (dirs1, files1, time.time() - T0, len(hits1)))
for h in hits1:
    print("   ", h[0], h[1], "B")

# ---------- R2 内容锐针搜索 ----------
print("\n=== R2 repo content needle search, text files <=3MB, maxdepth=%d ===" % MAXDEPTH)
dirs2 = files2 = 0
hits2 = []
TEXTEXT = {".py", ".md", ".txt", ".json", ".jsonl", ".log", ".out", ".sh", ".bat", ".ps1", ".yml", ".yaml", ".cfg", ".ini", ".toml", ".xml", ".html", ".js", ".ts", ".c", ".h", ".cpp", ".asm", ".idc"}
t2 = time.time()
stopped2 = False
for cur, subdirs, files, seen in walk_pruned("D:/Project/ra2-campaign-forge", MAXDEPTH):
    dirs2 = seen
    if not within_budget():
        stopped2 = True
        print("BUDGET STOP R2 at dirs=%d" % dirs2); break
    for name, size, mt in files:
        ext = os.path.splitext(name)[1].lower()
        if ext not in TEXTEXT or size > 3 * 1024 * 1024:
            continue
        files2 += 1
        path = os.path.join(cur, name)
        try:
            with open(path, "rb") as f:
                blob = f.read()
        except OSError:
            continue
        hay = None
        if NEEDLE_SHARP.encode("utf-8") in blob:
            hay = blob.decode("utf-8", "replace")
            rel = path.replace("D:/Project/ra2-campaign-forge/", "").replace("\\", "/")
            lines = [i + 1 for i, l in enumerate(hay.split("\n")) if NEEDLE_SHARP in l]
            hits2.append(("SHARP", rel, size, lines[:6]))
print("R2 dirsVisited=%d filesScanned=%d elapsed=%.1fs truncated=%s hits=%d" % (dirs2, files2, time.time() - t2, stopped2, len(hits2)))
for h in hits2:
    print("   ", h)

# ---------- R3 TEMP / 回收站 / 系统临时 ----------
print("\n=== R3 TEMP + recycle ===")
WIN_START = 1793798400.0  # 2026-11-04 00:00 +0800 近似
WIN_END = 1794268800.0    # 2026-11-09 24:00 近似 — 窗口放宽到今日
R3_ROOTS = [
    "C:/Users/Administrator/AppData/Local/Temp",
    "C:/Windows/Temp",
    "C:/$Recycle.Bin",
    "C:/Temp",
    "D:/Temp",
    "D:/tmp",
]
py_total = py_inwin = 0
hits3 = []
t3 = time.time()
for root in R3_ROOTS:
    d3 = f3 = 0
    for cur, subdirs, files, seen in walk_pruned(root, 6):
        d3 = seen
        if (time.time() - t3) > 120:
            print("R3 budget stop at", root); break
        for name, size, mt in files:
            if name.lower().endswith(".py"):
                py_total += 1
                if WIN_START <= mt <= WIN_END:
                    py_inwin += 1
                    path = os.path.join(cur, name)
                    try:
                        blob = open(path, "rb").read()
                    except OSError:
                        continue
                    tag = []
                    if b"frame_edges" in blob: tag.append("frame_edges")
                    if NEEDLE_SHARP.encode() in blob: tag.append("SHARP")
                    if "空档".encode() in blob: tag.append("CN空档")
                    if tag:
                        hits3.append((path, size, tag))
    print("   %s dirsVisited=%d elapsed=%.1fs" % (root, d3, time.time() - t3))
print("R3 total py=%d pyInWindow(11-04..09)=%d contentHits=%d elapsed=%.1fs" % (py_total, py_inwin, len(hits3), time.time() - t3))
for h in hits3[:40]:
    print("   ", h)

print("\nTOTAL elapsed %.1fs" % (time.time() - T0))
