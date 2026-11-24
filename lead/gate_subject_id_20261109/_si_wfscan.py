# -*- coding: utf-8 -*-
"""_si_wfscan.py — 扫 .zcode/workflow-runs（与 workflow-drafts）内嵌门禁代码里的主体识别选件逻辑。
剪枝：只收 *.mjs；深度上限 3；单件 >50MB 跳过。只读。
输出：_si_wfscan_out.json + stdout 摘要。
"""
import os
import re
import json
import time
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge")
ZC = ROOT / ".zcode"
OUTD = ROOT / "lead/gate_subject_id_20261109"
MAX_DEPTH = 3
SIZE_CAP = 50 * 1024 * 1024

SIZE_RX = re.compile(r"st_size|getsize\s*\(|getmtime|st_mtime")

t0 = time.perf_counter()
dirs_visited = 0
files_seen = 0
files_scanned = 0
skipped_big = 0
results = []

for dirpath, dirnames, filenames in os.walk(ZC):
    rel = os.path.relpath(dirpath, ZC)
    d = 0 if rel == "." else rel.count(os.sep) + 1
    dirnames[:] = sorted(
        x for x in dirnames
        if (not x.startswith(".")) and (d + 1 <= MAX_DEPTH)
    )
    dirs_visited += 1
    for f in sorted(filenames):
        if not f.lower().endswith(".mjs"):
            continue
        files_seen += 1
        p = Path(dirpath) / f
        try:
            sz = p.stat().st_size
        except OSError:
            continue
        if sz > SIZE_CAP:
            skipped_big += 1
            continue
        files_scanned += 1
        txt = p.read_text(encoding="utf-8", errors="replace")
        if "st_size" not in txt and "getsize(" not in txt and "getmtime" not in txt and "st_mtime" not in txt:
            continue
        lines = txt.splitlines()
        marks = []
        for i, ln in enumerate(lines):
            if SIZE_RX.search(ln):
                ctx = "\n".join(lines[max(0, i - 3): i + 4])
                marks.append({
                    "line": i + 1,
                    "text": ln.strip()[:260],
                    "ctxHasMax": bool(re.search(r"max\s*\(", ctx)),
                    "ctx": ctx[:700],
                })
        # 抓门禁名/工作流名线索
        names = set(re.findall(r'name\s*:\s*["\']([^"\']{3,80})["\']', txt)) | \
            set(re.findall(r'CREATE_WORKFLOW_NAME[^"\']{0,20}["\']([^"\']{3,80})["\']', txt))
        gates = sorted(set(re.findall(r'gate[_A-Za-z0-9]*', txt)))[:10]
        counterpart = "counterpart" in txt.lower() or "COUNTERPART_FIX" in txt
        results.append({
            "file": p.resolve().relative_to(ROOT).as_posix(),
            "size": sz,
            "markCount": len(marks),
            "maxNearCount": sum(1 for m in marks if m["ctxHasMax"]),
            "marks": marks[:40],
            "names": sorted(names)[:12],
            "counterpart": counterpart,
        })

elapsed = round(time.perf_counter() - t0, 3)

max_sites = []
for r in results:
    for m in r["marks"]:
        if m["ctxHasMax"]:
            max_sites.append({"file": r["file"], "line": m["line"], "text": m["text"], "ctx": m["ctx"]})

out = {
    "dirsVisited": dirs_visited,
    "elapsedSec": elapsed,
    "mjsSeen": files_seen,
    "mjsScanned": files_scanned,
    "skippedBig": skipped_big,
    "filesWithSizeMarks": results,
    "maxNearSizeSites": max_sites,
}
(OUTD / "_si_wfscan_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("dirsVisited=%d elapsedSec=%s mjsSeen=%d mjsScanned=%d skippedBig=%d filesWithSizeMarks=%d maxNearSizeSites=%d"
      % (dirs_visited, elapsed, files_seen, files_scanned, skipped_big, len(results), len(max_sites)))
print()
for r in results:
    tag = " ★counterpart" if r["counterpart"] else ""
    print("%-72s size=%-9d marks=%-3d maxNear=%d%s" % (
        r["file"], r["size"], r["markCount"], r["maxNearCount"], tag))
    if r["names"]:
        print("    names: %s" % "; ".join(r["names"][:6]))
