# -*- coding: utf-8 -*-
"""_si_scan_domains.py — 主体识别诊断·第一步：复扫 lead/ 全部写域 md 清点。
剪枝：跳过 .git / __pycache__ / node_modules / .tmp 与点开头目录；深度上限 6。
只读：对历史写域仅 stat / walk，不写不删。
输出：_si_scan_out.json + stdout 摘要。
"""
import os
import json
import time
from pathlib import Path

LEAD = Path(r"D:/Project/ra2-campaign-forge/lead")
OUTD = Path(r"D:/Project/ra2-campaign-forge/lead/gate_subject_id_20261109")
MAX_DEPTH = 6
PRUNE_DIRS = {".git", "__pycache__", "node_modules", ".tmp"}

t0 = time.perf_counter()
dirs_visited = 0
stat_errors = 0
records = []

for dirpath, dirnames, filenames in os.walk(LEAD):
    rel = os.path.relpath(dirpath, LEAD)
    d = 0 if rel == "." else rel.count(os.sep) + 1
    dirnames[:] = sorted(
        x for x in dirnames
        if (x not in PRUNE_DIRS) and (not x.startswith(".")) and (d + 1 <= MAX_DEPTH)
    )
    dirs_visited += 1
    mds = []
    for f in filenames:
        if f.lower().endswith(".md"):
            p = Path(dirpath) / f
            try:
                sz = p.stat().st_size
            except OSError:
                stat_errors += 1
                continue
            mds.append((f, sz))
    if not mds:
        continue
    mds_sorted = sorted(mds, key=lambda x: (-x[1], x[0]))
    lname, lsize = mds_sorted[0]
    bare = [(n, s) for (n, s) in mds if not n.startswith("_")]
    bare_sorted = sorted(bare, key=lambda x: (-x[1], x[0]))
    lb = bare_sorted[0] if bare else None
    records.append({
        "dir": "lead" if rel == "." else "lead/" + Path(rel).as_posix(),
        "mdCount": len(mds),
        "largest": [lname, lsize],
        "largestIsUnderscore": lname.startswith("_"),
        "largestBare": ([lb[0], lb[1]] if lb else None),
        "bareCount": len(bare),
        "underCount": len(mds) - len(bare),
        "files": sorted([list(x) for x in mds]),
    })

elapsed = round(time.perf_counter() - t0, 3)

under_all = [r for r in records if r["largestIsUnderscore"]]
under_with_bare = [r for r in under_all if r["bareCount"] > 0]
under_no_bare = [r for r in under_all if r["bareCount"] == 0]
bare_multi = [r for r in records if (not r["largestIsUnderscore"]) and r["mdCount"] > 1]
bare_single = [r for r in records if (not r["largestIsUnderscore"]) and r["mdCount"] == 1]
multi_bare = [r for r in records if r["bareCount"] > 1]

name_map = {}
for r in records:
    for n, s in r["files"]:
        if not n.startswith("_"):
            name_map.setdefault(n, []).append([r["dir"], s])
dup_names = {n: locs for n, locs in sorted(name_map.items()) if len(locs) > 1}

summary = {
    "method": {"maxDepth": MAX_DEPTH, "pruned": sorted(PRUNE_DIRS),
               "walker": "os.walk(topdown, pruned in-place)"},
    "dirsVisited": dirs_visited,
    "elapsedSec": elapsed,
    "statErrors": stat_errors,
    "domainsWithMd": len(records),
    "totalMd": sum(r["mdCount"] for r in records),
    "q_a": {
        "underscoreLargestCount": len(under_all),
        "domains": [r["dir"] for r in under_all],
        "withBareDetail": [
            {"dir": r["dir"], "picked": r["largest"], "bareMax": r["largestBare"],
             "diffBytes": r["largest"][1] - r["largestBare"][1]}
            for r in under_with_bare
        ],
        "allUnderscoreDomains": [
            {"dir": r["dir"], "mdCount": r["mdCount"], "underCount": r["underCount"]}
            for r in under_no_bare
        ],
    },
    "q_c": {
        "bareLuckyMulti": [
            {"dir": r["dir"], "largest": r["largest"], "mdCount": r["mdCount"],
             "bareCount": r["bareCount"]}
            for r in bare_multi
        ],
        "bareTrivialSingleCount": len(bare_single),
    },
    "domainsWithMultiBare": [{"dir": r["dir"], "bareCount": r["bareCount"]} for r in multi_bare],
    "crossDomainDuplicateBareNames": dup_names,
}

(OUTD / "_si_scan_out.json").write_text(
    json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=1),
    encoding="utf-8")

print("dirsVisited=%d elapsedSec=%s statErrors=%d domainsWithMd=%d totalMd=%d" % (
    dirs_visited, elapsed, stat_errors, len(records), summary["totalMd"]))
print("Q(a) max 选中下划线件的写域共 %d 个：" % summary["q_a"]["underscoreLargestCount"])
for x in summary["q_a"]["withBareDetail"]:
    print("  [有非下划线件] %-42s picked=%s(%dB) bareMax=%s(%dB) diff=%dB" % (
        x["dir"], x["picked"][0], x["picked"][1], x["bareMax"][0], x["bareMax"][1], x["diffBytes"]))
for x in summary["q_a"]["allUnderscoreDomains"]:
    print("  [全为下划线件] %-42s mdCount=%d (无主件可选)" % (x["dir"], x["mdCount"]))
print("Q(c) max 恰好选中非下划线件：多文件碰巧挑对 %d 个域；单文件平凡正确 %d 个域" % (
    len(bare_multi), len(bare_single)))
print("同域内非下划线件 >1 的域（多主件歧义）：")
for x in summary["domainsWithMultiBare"]:
    print("  %-42s bareCount=%d" % (x["dir"], x["bareCount"]))
print("跨域同名非下划线件（按文件名找主件的歧义源）：%d 种" % len(dup_names))
for n, locs in sorted(dup_names.items()):
    print("  %s -> %s" % (n, "; ".join("%s(%dB)" % (d, s) for d, s in locs)))
