# _shv_r2full.py — R2 全量内容锐针扫描（仓库 + .zcode + .tmp），只读
import os, time, sys

T0 = time.time()
BUDGET = 470.0
MAXDEPTH = 12
NEEDLES = {
    "SHARP": b"dur={fe[i][0]",
    "FULL": b"dur={fe[i][0]:(fe[i][1]-fe[i-1][1])*1000.0",
    "ISPREFIX": b"IS_PREFIX_EXT True",
}
DOMAIN = "lead/s604_script_hunt_20261109".replace("/", os.sep)
PRUNE = {".git", "node_modules", "__pycache__"}
TEXTEXT = {".py", ".md", ".txt", ".json", ".jsonl", ".log", ".out", ".sh", ".bat", ".ps1", ".yml", ".yaml", ".cfg", ".ini", ".toml", ".xml", ".html", ".js", ".ts", ".c", ".h", ".cpp", ".asm", ".idc", ".sql", ".csv", ".muhz7xi2", ""}

def walk(root, maxdepth):
    dirs = 0
    root = os.path.abspath(root)
    stack = [(root, 0)]
    while stack:
        cur, d = stack.pop()
        dirs += 1
        try:
            entries = list(os.scandir(cur))
        except OSError:
            continue
        subdirs, files = [], []
        for e in entries:
            try:
                if e.is_dir(follow_symlinks=False):
                    subdirs.append(e.name)
                else:
                    files.append((e.path, e.stat().st_size, e.stat().st_mtime))
            except OSError:
                pass
        yield cur, subdirs, files, dirs
        if d + 1 < maxdepth:
            for s in subdirs:
                if s not in PRUNE:
                    stack.append((os.path.join(cur, s), d + 1))

def classify(path):
    p = path.replace("\\", "/")
    if "_shv_" in os.path.basename(p) or DOMAIN in p:
        return "EXPECTED(write-domain)"
    if p.startswith("C:/Users/Administrator/.zcode"):
        return "zcode"
    return "MAJOR"

ROOTS = ["D:/Project/ra2-campaign-forge", "C:/Users/Administrator/.zcode", "D:/Project/ra2-campaign-forge/.tmp"]
report = []
for root in ROOTS:
    dirs = files_seen = 0
    t = time.time()
    truncated = False
    hits = []
    for cur, subdirs, files, seen in walk(root, MAXDEPTH):
        dirs = seen
        if (time.time() - T0) > BUDGET:
            truncated = True
            break
        for path, size, mt in files:
            ext = os.path.splitext(path)[1].lower()
            if ext not in TEXTEXT or size > 3 * 1024 * 1024:
                continue
            files_seen += 1
            try:
                with open(path, "rb") as f:
                    blob = f.read()
            except OSError:
                continue
            for nk, nb in NEEDLES.items():
                if nb in blob:
                    rel = path.replace("D:/Project/ra2-campaign-forge/", "").replace("\\", "/")
                    lines = [i + 1 for i, l in enumerate(blob.decode("utf-8", "replace").split("\n")) if nb.decode("utf-8", "replace") in l]
                    hits.append((nk, rel, size, lines[:8]))
                    break
    report.append((root, dirs, files_seen, time.time() - t, truncated, hits))
    print("ROOT %-40s dirs=%d files=%d %.1fs truncated=%s hits=%d" % (root, dirs, files_seen, time.time() - t, truncated, len(hits)), flush=True)
    for h in hits:
        print("   ", classify(h[1]), h, flush=True)

print("\n== SUMMARY ==")
total_hits = sum(len(r[5]) for r in report)
print("total files scanned:", sum(r[2] for r in report), "total hits:", total_hits, "elapsed %.1fs" % (time.time() - T0))
majors = [h for r in report for h in r[5] if classify(h[1]) == "MAJOR"]
print("MAJOR hits (outside write domain):", len(majors))
for h in majors:
    print("   ", h)
