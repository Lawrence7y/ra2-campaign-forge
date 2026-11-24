# -*- coding: utf-8 -*-
"""_si_gatescan.py — 主体识别诊断·第五步：找门禁脚本中的「按大小/时间/顺序挑件」逻辑。
scope lead：walk lead/，剪枝 .git/__pycache__/node_modules/.tmp/本任务写域，深度上限 6。
scope root：walk 库根（不含 lead/，含 .tmp/），剪枝同上，深度上限 4（补充查证）。
只读。输出 _si_gatescan_out.json + stdout 摘要。
"""
import os
import re
import json
import time
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge")
LEAD = ROOT / "lead"
OUTD = LEAD / "gate_subject_id_20261109"
MAX_DEPTH_LEAD = 6
MAX_DEPTH_ROOT = 4
SELF = "gate_subject_id_20261109"

SMELLS = {
    "size_argmax":       re.compile(r"max\s*\([^)]*st_size"),
    "st_size_any":       re.compile(r"st_size"),
    "getsize":           re.compile(r"getsize\s*\("),
    "mtime_pick":        re.compile(r"getmtime|st_mtime"),
    "md_glob":           re.compile(r"glob\s*\(\s*['\"][^'\"]*md"),
    "listdir_iterdir":   re.compile(r"listdir\s*\(|iterdir\s*\("),
    "sorted_first":      re.compile(r"sorted\s*\([^)]*\)\s*\[\s*0\s*\]"),
    "underscore_filter": re.compile(r"startswith\s*\(\s*['\"]_"),
}


def walk_collect(base, prune, max_depth, exts):
    t0 = time.perf_counter()
    dirs = 0
    files = []
    for dirpath, dirnames, filenames in os.walk(base):
        rel = os.path.relpath(dirpath, base)
        d = 0 if rel == "." else rel.count(os.sep) + 1
        dirnames[:] = sorted(
            x for x in dirnames
            if (x not in prune) and (not x.startswith(".")) and (d + 1 <= max_depth)
        )
        dirs += 1
        for f in sorted(filenames):
            if any(f.lower().endswith(e) for e in exts):
                files.append(Path(dirpath) / f)
    return files, dirs, round(time.perf_counter() - t0, 3)


def rel_to_root(p):
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def scan_py(p):
    try:
        txt = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"file": rel_to_root(p), "readError": str(e)}
    lines = txt.splitlines()
    hits = []
    for i, ln in enumerate(lines):
        if ("st_size" in ln) or ("getmtime" in ln) or ("st_mtime" in ln) or ("getsize(" in ln):
            lo = max(0, i - 2)
            hi = min(len(lines), i + 3)
            ctx = "\n".join(lines[lo:hi])
            hits.append({
                "line": i + 1,
                "text": ln.strip()[:220],
                "ctxHasMax": bool(re.search(r"max\s*\(", ctx)),
                "ctx": ctx[:500],
            })
    smells = {}
    for name, rx in SMELLS.items():
        ms = [i + 1 for i, ln in enumerate(lines) if rx.search(ln)]
        if ms:
            smells[name] = ms
    return {"file": rel_to_root(p), "size": p.stat().st_size,
            "hits": hits, "smells": smells}


def scan_md(p):
    try:
        sz = p.stat().st_size
        if sz > 4 * 1024 * 1024:
            return {"file": rel_to_root(p), "skippedTooBig": True}
        txt = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"file": rel_to_root(p), "readError": str(e)}
    if ("st_size" not in txt) and ("getsize(" not in txt) and \
       ("getmtime" not in txt) and ("st_mtime" not in txt):
        return None
    lines = txt.splitlines()
    marks = []
    for i, ln in enumerate(lines):
        if ("st_size" in ln) or ("getsize(" in ln) or ("getmtime" in ln) or ("st_mtime" in ln):
            ctx = "\n".join(lines[max(0, i - 2): i + 3])
            marks.append({
                "line": i + 1,
                "text": ln.strip()[:200],
                "ctxHasMax": bool(re.search(r"max\s*\(", ctx)),
            })
    return {"file": rel_to_root(p), "markCount": len(marks), "marks": marks[:12]}


t0 = time.perf_counter()

# ---- scope 1: lead/ ----
prune1 = {".git", "__pycache__", "node_modules", ".tmp", SELF}
pys1, dv1, el1 = walk_collect(LEAD, prune1, MAX_DEPTH_LEAD, [".py"])
py_scans1 = []
for p in pys1:
    s = scan_py(p)
    if s:
        py_scans1.append(s)

mds1, dv_md, el_md = walk_collect(LEAD, prune1, MAX_DEPTH_LEAD, [".md"])
md_scans1 = []
for p in mds1:
    s = scan_md(p)
    if s:
        md_scans1.append(s)

# ---- scope 2: root (excl. lead/, incl. .tmp/) ----
prune2 = {"__pycache__", "node_modules", ".git", "lead"}
pys2, dv2, el2 = walk_collect(ROOT, prune2, MAX_DEPTH_ROOT, [".py"])
py_scans2 = []
for p in pys2:
    s = scan_py(p)
    if s:
        py_scans2.append(s)

elapsed = round(time.perf_counter() - t0, 3)

py_hit1 = [s for s in py_scans1 if s.get("hits")]
py_max1 = []
for s in py_hit1:
    for h in s["hits"]:
        if h["ctxHasMax"]:
            py_max1.append({"file": s["file"], "line": h["line"], "text": h["text"], "ctx": h["ctx"]})
py_smell1 = [s for s in py_scans1 if (not s.get("hits")) and s.get("smells")]
py_hit2 = [s for s in py_scans2 if s.get("hits")]
py_max2 = []
for s in py_hit2:
    for h in s["hits"]:
        if h["ctxHasMax"]:
            py_max2.append({"file": s["file"], "line": h["line"], "text": h["text"], "ctx": h["ctx"]})

smell_summary = {}
for s in py_scans1 + py_scans2:
    for name, ls in (s.get("smells") or {}).items():
        smell_summary.setdefault(name, []).append({"file": s["file"], "lines": ls[:8]})

result = {
    "method": {"maxDepthLead": MAX_DEPTH_LEAD, "maxDepthRoot": MAX_DEPTH_ROOT,
               "prunedLead": sorted(prune1), "prunedRoot": sorted(prune2),
               "note": "本任务写域 gate_subject_id_20261109 从 lead 扫描中剪除，避免自匹配"},
    "leadScope": {"dirsVisitedPy": dv1, "elapsedSecPy": el1,
                  "dirsVisitedMd": dv_md, "elapsedSecMd": el_md,
                  "pyScanned": len(py_scans1), "mdScanned": len(mds1)},
    "rootScope": {"dirsVisited": dv2, "elapsedSec": el2, "pyScanned": len(py_scans2)},
    "leadPyFilesWithStSizeHits": py_hit1,
    "leadPyMaxNearSizeSites": py_max1,
    "leadPySmellOnly": py_smell1,
    "rootPyFilesWithStSizeHits": py_hit2,
    "rootPyMaxNearSizeSites": py_max2,
    "leadMdWithSizeMarks": md_scans1,
    "smellSummary": smell_summary,
    "totalElapsedSec": elapsed,
}

(OUTD / "_si_gatescan_out.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

print("== gatescan ==")
print("lead scope: dirsVisited(py)=%d %.3fs dirsVisited(md)=%d %.3fs pyScanned=%d mdScanned=%d"
      % (dv1, el1, dv_md, el_md, len(py_scans1), len(mds1)))
print("root scope: dirsVisited=%d %.3fs pyScanned=%d" % (dv2, el2, len(py_scans2)))
print("totalElapsedSec=%s" % elapsed)
print("")
print("== lead/ 内 .py 且带 st_size/size 命中的文件：%d ==" % len(py_hit1))
for s in py_hit1:
    print("  %s (smells=%s)" % (s["file"], sorted(s.get("smells", {}).keys())))
    for h in s["hits"]:
        print("    L%d ctxHasMax=%s : %s" % (h["line"], h["ctxHasMax"], h["text"][:150]))
print("")
print("== lead/ 内 max(...) 紧邻 st_size 的位点（候选『max 挑交付件』实证）：%d ==" % len(py_max1))
for x in py_max1:
    print("  %s:%d" % (x["file"], x["line"]))
    print("    ctx: %s" % x["ctx"].replace("\n", " ⏎ ")[:400])
print("")
print("== root/.tmp 内 .py 带命中：%d；其中 max 紧邻：%d ==" % (len(py_hit2), len(py_max2)))
for s in py_hit2:
    print("  %s (smells=%s)" % (s["file"], sorted(s.get("smells", {}).keys())))
    for h in s["hits"]:
        print("    L%d ctxHasMax=%s : %s" % (h["line"], h["ctxHasMax"], h["text"][:150]))
print("")
print("== lead/ 内 .md 提及 st_size/size 选件的：%d 件 ==" % len(md_scans1))
for s in md_scans1:
    print("  %s marks=%d firstLine=%s" % (
        s["file"], s.get("markCount", 0),
        s["marks"][0]["text"][:120] if s.get("marks") else "-"))
