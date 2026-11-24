# _sh_r678_search.py — R6/R8/R9/R10 穷搜（全只读；剪枝+深度上限+时间预算；逐路 dirsVisited/耗时）
# 写域 = lead/s604_script_hunt_20261109/。不修改任何被搜件。
import os, re, time

REPO = r"D:\Project\ra2-campaign-forge"
WD = os.path.join(REPO, "lead", "s604_script_hunt_20261109")
OUTP = os.path.join(WD, "_sh_r678_out.txt")

REPARSE = 0x400
BASE_SKIP = {".git", "node_modules"}

def N(b, label):
    return (b, label)

CN = ["空档差", "快1/3", "慢1/3"]
NEEDLES6 = [N(b"s604", "s604"), N(b"gapdiff", "gapdiff"), N(b"gap_diff", "gap_diff"),
            N(b"gap-diff", "gap-diff"), N(b"slowframe", "slowframe")]
NEEDLES6 += [(s.encode("utf-8"), l + "(u8)") for s, l in zip(CN, CN)]
NEEDLES6 += [(s.encode("gbk", "replace"), l + "(gbk)") for s, l in zip(CN, CN)]
NEEDLES9 = NEEDLES6 + [N(b"604", "604")]
PY_MARKS = (b"def ", b"import ")

NAME_RE = re.compile(r"(s604|slowframe|gapdiff|gap[_-]?diff|(^|[^0-9])604)", re.I)
MATCH10 = re.compile(r"(604|slowframe|gapdiff|gap[_-]?diff)", re.I)
BACKUP_RE = re.compile(r"(\.swp$|\.swo$|\.swpx$|\.kate-swp$|~$|\.bak$|\.orig$|\.rej$|\.autosave$|\.sav$|^\.#)", re.I)
R9_EXTS = {".log", ".txt", ".out", ".md", ".json", ".jsonl"}
PY_WINDOW = (time.mktime((2026, 11, 4, 0, 0, 0, 0, 0, -1)),
             time.mktime((2026, 11, 8, 23, 59, 59, 0, 0, -1)))

def find_hits(blob, needles, require_py=False):
    low = blob.lower()
    found = []
    first_pos = None
    for b, lab in needles:
        p = low.find(b) if b == b.lower() else blob.find(b)
        if p >= 0:
            found.append(lab)
            if first_pos is None or p < first_pos:
                first_pos = p
    ok = bool(found)
    if require_py:
        ok = ok and any(m in blob for m in PY_MARKS)
    if not ok:
        return False, found, None
    if first_pos is not None:
        ls = blob.rfind(b"\n", 0, first_pos) + 1
        le = blob.find(b"\n", first_pos)
        if le < 0:
            le = len(blob)
        txt = blob[ls:le][:240].decode("utf-8", "replace")
        return True, found, txt
    return True, found, None

def walk(root, max_depth, budget, max_dirs, skip, on_file=None, on_dir=None):
    t0 = time.perf_counter()
    dirs = files = denied = 0
    truncated = False
    missing = False
    if not os.path.isdir(root):
        missing = True
    else:
        stack = [(root, 0)]
        while stack:
            d, dep = stack.pop()
            dirs += 1
            if dirs > max_dirs or (time.perf_counter() - t0) > budget:
                truncated = True
                break
            try:
                ents = list(os.scandir(d))
            except OSError:
                denied += 1
                continue
            for e in ents:
                try:
                    st = e.stat(follow_symlinks=False)
                    if getattr(st, "st_file_attributes", 0) & REPARSE:
                        continue
                    if e.is_dir(follow_symlinks=False):
                        if e.name.lower() in skip:
                            continue
                        if on_dir is not None:
                            on_dir(e)
                        if dep + 1 <= max_depth:
                            stack.append((e.path, dep + 1))
                    else:
                        files += 1
                        if on_file is not None:
                            on_file(e, st)
                except OSError:
                    denied += 1
    return {"dirs": dirs, "files": files, "denied": denied, "truncated": truncated,
            "missing": missing, "elapsed": round(time.perf_counter() - t0, 2)}

def fmt(path, sz, t, extra):
    m = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))
    return f"  HIT {path} | bytes={sz} | mtime={m} | {extra}"

def fmt_ts(t):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

report = []
def emit(s=""):
    report.append(s)

def run_r6():
    R6 = [
        ("R6a-user-temp", os.environ.get("TEMP", ""), 6, 45, 30000,
         {"scan_exts": {".py", ".txt", ".log", ".md", ".json", ".out"}, "size_cap": 1_000_000, "collect_py": True}, set()),
        ("R6b-system-temp", r"C:\Windows\Temp", 4, 20, 20000,
         {"scan_exts": {".py", ".txt", ".log", ".json"}, "size_cap": 1_000_000, "collect_py": True}, set()),
        ("R6c-recycle", r"C:\$Recycle.Bin", 4, 15, 8000,
         {"scan_exts": {".py"}, "size_cap": 300_000}, set()),
        ("R6d-repo-tmp", os.path.join(REPO, ".tmp"), 6, 25, 5000,
         {"scan_exts": {".py", ".txt", ".log", ".md", ".json", ".jsonl", ".out", ".cjs", ".bat", ".cmd"}, "size_cap": 2_000_000, "collect_py": True}, set()),
        ("R6e-c-temp", r"C:\Temp", 4, 12, 5000,
         {"scan_exts": {".py", ".txt", ".log", ".md", ".json", ".out"}, "size_cap": 2_000_000}, set()),
        ("R6f-d-temp", r"D:\Temp", 4, 12, 5000,
         {"scan_exts": {".py", ".txt", ".log", ".md", ".json", ".out"}, "size_cap": 2_000_000}, set()),
        ("R6g-d-tmp", r"D:\tmp", 4, 12, 5000,
         {"scan_exts": {".py", ".txt", ".log", ".md", ".json", ".out"}, "size_cap": 2_000_000}, set()),
        ("R6h-zcode", r"C:\Users\Administrator\.zcode", 5, 90, 30000,
         {"scan_exts": {".jsonl", ".json", ".txt", ".md", ".log"}, "size_cap": 30_000_000}, {"plugins", "cache"}),
        ("R6i-agents", r"C:\Users\Administrator\.agents", 4, 15, 5000,
         {"scan_exts": {".jsonl", ".json", ".txt", ".md", ".log"}, "size_cap": 5_000_000}, set()),
        ("R6j-code-backups", r"C:\Users\Administrator\AppData\Roaming\Code\Backups", 4, 15, 5000,
         {"scan_all": True, "size_cap": 5_000_000}, set()),
        ("R6k-recent-lnk", r"C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Recent", 3, 10, 3000,
         {"name_only": True, "collect_recent": True}, set()),
    ]
    for label, root, depth, budget, maxd, cfg, extra in R6:
        hits, pys, recents = [], [], []
        cap = cfg.get("size_cap", 1_000_000)
        scan_exts = cfg.get("scan_exts")
        scan_all = cfg.get("scan_all", False)

        def on_file(e, st, cfg=cfg, cap=cap, scan_exts=scan_exts, scan_all=scan_all,
                    hits=hits, pys=pys, recents=recents):
            name = e.name
            sz = st.st_size
            mtime = st.st_mtime
            ext = os.path.splitext(name)[1].lower()
            if cfg.get("collect_py") and ext == ".py" and PY_WINDOW[0] <= mtime <= PY_WINDOW[1] and sz < 300_000:
                if len(pys) < 400:
                    pys.append((e.path, sz, mtime))
            if cfg.get("collect_recent") and ext == ".lnk" and PY_WINDOW[0] <= mtime <= PY_WINDOW[1]:
                if len(recents) < 200:
                    recents.append((e.path, sz, mtime))
            matched = bool(NAME_RE.search(name))
            if matched:
                hits.append((e.path, sz, mtime, "name"))
            do_scan = sz <= cap and (scan_all or (scan_exts is not None and ext in scan_exts))
            if do_scan:
                try:
                    with open(e.path, "rb") as f:
                        blob = f.read(cap)
                except OSError:
                    return
                ok, hs, ex = find_hits(blob, NEEDLES6)
                if ok:
                    hits.append((e.path, sz, mtime, "content[" + ",".join(hs) + "] :: " + (ex or "")))

        st = walk(root, depth, budget, maxd, BASE_SKIP | extra, on_file)
        emit(f"### {label} root={root}")
        emit(f"    stats dirsVisited={st['dirs']} filesSeen={st['files']} denied={st['denied']} "
             f"truncated={st['truncated']} missing={st['missing']} elapsed_s={st['elapsed']} hits={len(hits)} "
             f"pyInWindow={len(pys)} recentLnkInWindow={len(recents)}")
        for h in hits[:80]:
            emit(fmt(*h))
        if len(hits) > 80:
            emit(f"    ...(+{len(hits)-80} more, full list in this file)")
        for p, sz, t in pys[:60]:
            emit(f"  PY-WIN {p} | bytes={sz} | mtime={fmt_ts(t)}")
        if len(pys) > 60:
            emit(f"    ...(+{len(pys)-60} more py in window)")
        for p, sz, t in recents[:60]:
            emit(f"  LNK-WIN {p} | bytes={sz} | mtime={fmt_ts(t)}")
        emit()

def run_r8():
    hits, edirs = [], []
    t0 = time.perf_counter()

    def on_file(e, st):
        if BACKUP_RE.search(e.name):
            extra = "backupname"
            if st.st_size <= 1_000_000:
                try:
                    with open(e.path, "rb") as f:
                        blob = f.read(1_000_000)
                except OSError:
                    blob = b""
                if blob:
                    ok, hs, ex = find_hits(blob, NEEDLES6)
                    if ok:
                        extra = "backupname+content[" + ",".join(hs) + "] :: " + (ex or "")
            hits.append((e.path, st.st_size, st.st_mtime, extra))

    def on_dir(e):
        if e.name.lower() in (".vscode", ".idea", ".history"):
            edirs.append((e.path, 0, 0, "editor-dir"))

    st = walk(REPO, 5, 60, 30000, BASE_SKIP, on_file, on_dir)
    emit("### R8-editor-remnants root=REPO depth=5")
    emit(f"    stats dirsVisited={st['dirs']} filesSeen={st['files']} denied={st['denied']} "
         f"truncated={st['truncated']} elapsed_s={round(time.perf_counter()-t0,2)} hits={len(hits)+len(edirs)}")
    for h in (edirs + hits)[:80]:
        emit(fmt(*h))
    exist_checks = {
        "VSCode-Backups": r"C:\Users\Administrator\AppData\Roaming\Code\Backups",
        "Notepad++-backup": r"C:\Users\Administrator\AppData\Roaming\Notepad++\backup",
        "JetBrains-LocalHistory": r"C:\Users\Administrator\AppData\Local\JetBrains",
        "repo-.vscode": os.path.join(REPO, ".vscode"),
        "repo-.idea": os.path.join(REPO, ".idea"),
        "OneDrive": r"C:\Users\Administrator\OneDrive",
    }
    emit("    existence checks:")
    for k, p in exist_checks.items():
        emit(f"      {k}: exists={os.path.exists(p)} path={p}")
    emit()

def run_r9():
    hits = []
    t0 = time.perf_counter()

    def on_file(e, st):
        ext = os.path.splitext(e.name)[1].lower()
        if ext not in R9_EXTS:
            return
        sz = st.st_size
        if sz < 1 or sz > 5_000_000:
            return
        try:
            with open(e.path, "rb") as f:
                blob = f.read(5_000_000)
        except OSError:
            return
        ok, hs, ex = find_hits(blob, NEEDLES9, require_py=True)
        if ok:
            hits.append((e.path, sz, st.st_mtime, "[" + ",".join(hs) + "] :: " + (ex or "")))

    st = walk(REPO, 8, 120, 40000, BASE_SKIP, on_file)
    emit("### R9-log-embedded-python root=REPO depth=8 (needles: 空档差/604/s604/gapdiff/slowframe + def/import)")
    emit(f"    stats dirsVisited={st['dirs']} filesSeen={st['files']} denied={st['denied']} "
         f"truncated={st['truncated']} elapsed_s={round(time.perf_counter()-t0,2)} hits={len(hits)}")
    for h in hits[:120]:
        emit(fmt(*h))
    if len(hits) > 120:
        emit(f"    ...(+{len(hits)-120} more)")
    emit()

def run_r10():
    hits = []
    t0 = time.perf_counter()

    def on_file(e, st):
        if MATCH10.search(e.name):
            hits.append((e.path, st.st_size, st.st_mtime, "name604/slowframe/gapdiff"))

    def on_dir(e):
        if MATCH10.search(e.name):
            hits.append((e.path, 0, 0, "DIRNAME-match"))

    st = walk(REPO, 8, 60, 30000, BASE_SKIP, on_file, on_dir)
    emit("### R10-reponame-recheck root=REPO depth=8 (604|slowframe|gapdiff|gap_diff|gap-diff)")
    emit(f"    stats dirsVisited={st['dirs']} filesSeen={st['files']} denied={st['denied']} "
         f"truncated={st['truncated']} elapsed_s={round(time.perf_counter()-t0,2)} hits={len(hits)}")
    for h in hits[:150]:
        emit(fmt(*h))
    if len(hits) > 150:
        emit(f"    ...(+{len(hits)-150} more)")
    emit()

t_all = time.perf_counter()
emit("== S604 脚本残迹穷搜 R6/R8/R9/R10（全只读；逐路 dirsVisited/耗时；预算内截断会如实标注） ==")
emit(f"repo={REPO}  now={fmt_ts(time.time())}")
emit()
run_r6()
run_r8()
run_r9()
run_r10()
emit(f"== total elapsed_s={round(time.perf_counter()-t_all,2)} ==")

with open(OUTP, "w", encoding="utf-8") as f:
    f.write("\n".join(report) + "\n")
print(f"[out] {OUTP}")
print(f"[total] {round(time.perf_counter()-t_all,2)}s, lines={len(report)}")
