# -*- coding: utf-8 -*-
"""_si_gatecensus.py — 主体识别机制普查：.zcode/workflow-runs+drafts 全部 mjs 门禁代码，
按「DOC=max(cands,st_size)」vs「expected=wd/'X.md' 显式命名」分类，并关联写域下划线风险。只读。"""
import os
import re
import json
import time
from pathlib import Path

ROOT = Path(r"D:/Project/ra2-campaign-forge")
ZC = ROOT / ".zcode"
OUTD = ROOT / "lead/gate_subject_id_20261109"
MAX_DEPTH = 3

sc = json.loads((OUTD / "_si_scan_out.json").read_text(encoding="utf-8"))
rec_by_dir = {r["dir"]: r for r in sc["records"]}

RX_DOC_MAX = re.compile(r"DOC\s*=\s*max\s*\(\s*cands\s*,\s*key\s*=\s*lambda\s+p\s*:\s*p\.stat\(\)\.st_size\s*\)")
RX_MAXCAND = re.compile(r"max\s*\(\s*cands")
RX_EXPECT = re.compile(r"expected\s*=\s*wd\s*/\s*['\"]([^'\"]+)['\"]")
RX_WD = re.compile(r"wd\s*=\s*root\s*/\s*['\"]([^'\"]*lead[^'\"]*)['\"]")
RX_SORTGLOB = re.compile(r"sorted\s*\(\s*wd\.glob\s*\(\s*['\"]\*\.md")


def domain_risk(dom):
    rec = rec_by_dir.get(dom.rstrip("/"))
    if rec is None:
        # 找最近祖先
        parts = dom.split("/")
        for i in range(len(parts), 0, -1):
            rec = rec_by_dir.get("/".join(parts[:i]))
            if rec:
                break
    if rec is None:
        return "N/A"
    return "HIGH" if rec["underCount"] > 0 else "MED"


t0 = time.perf_counter()
dirs_visited = 0
files = 0
rows = []
for dirpath, dirnames, filenames in os.walk(ZC):
    rel = os.path.relpath(dirpath, ZC)
    d = 0 if rel == "." else rel.count(os.sep) + 1
    dirnames[:] = sorted(x for x in dirnames if (not x.startswith(".")) and (d + 1 <= MAX_DEPTH))
    dirs_visited += 1
    for f in sorted(filenames):
        if not f.lower().endswith(".mjs"):
            continue
        files += 1
        p = Path(dirpath) / f
        raw = p.read_text(encoding="utf-8", errors="replace")
        n_docmax = len(RX_DOC_MAX.findall(raw))
        n_maxcand = len(RX_MAXCAND.findall(raw))
        expects = RX_EXPECT.findall(raw)
        wds = RX_WD.findall(raw)
        n_sortglob = len(RX_SORTGLOB.findall(raw))
        if n_docmax == 0 and n_maxcand == 0 and not expects and not wds:
            continue
        dom = ""
        for w in wds:
            if w.startswith("lead/"):
                dom = w.rstrip("/")
                break
        rows.append({
            "file": p.resolve().relative_to(ROOT).as_posix(),
            "docMax": n_docmax,
            "maxCandAny": n_maxcand,
            "explicit": expects[:4],
            "wd": wds[:4],
            "domain": dom,
            "risk": domain_risk(dom) if dom else "N/A",
            "sortedGlobMd": n_sortglob,
        })

elapsed = round(time.perf_counter() - t0, 3)

n_docmax_files = sum(1 for r in rows if r["docMax"] > 0)
n_docmax_sites = sum(r["docMax"] for r in rows)
n_explicit_files = sum(1 for r in rows if r["explicit"])
n_maxonly = sum(1 for r in rows if r["docMax"] == 0 and r["maxCandAny"] > 0)

out = {"dirsVisited": dirs_visited, "elapsedSec": elapsed, "mjsScanned": files,
       "filesWithGateSelection": rows,
       "summary": {
           "filesUsingDocMaxStSize": n_docmax_files,
           "sitesUsingDocMaxStSize": n_docmax_sites,
           "filesUsingMaxCandOnly": n_maxonly,
           "filesUsingExplicitExpected": n_explicit_files,
       }}
(OUTD / "_si_gatecensus_out.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

print("dirsVisited=%d elapsedSec=%s mjsScanned=%d" % (dirs_visited, elapsed, files))
print("含 DOC=max(cands,key=st_size) 的 run 文件数=%d，位点数=%d" % (n_docmax_files, n_docmax_sites))
print("仅含 max(cands...)（变体写法）文件数=%d" % n_maxonly)
print("含 expected=显式命名 的文件数=%d" % n_explicit_files)
print()
print("== DOC=max 门禁 → 目标写域 → 风险 ==")
for r in rows:
    if r["docMax"] > 0:
        print("  %-64s domain=%-38s risk=%-5s sites=%d sortedGlobMd=%d" % (
            r["file"].split("/")[-1][:64], r["domain"], r["risk"], r["docMax"], r["sortedGlobMd"]))
print()
print("== 显式命名门禁 → 目标写域 ==")
for r in rows:
    if r["docMax"] == 0 and r["explicit"]:
        print("  %-64s domain=%-38s expected=%s" % (
            r["file"].split("/")[-1][:64], r["domain"], r["explicit"]))
