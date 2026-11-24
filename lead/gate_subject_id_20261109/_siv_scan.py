# -*- coding: utf-8 -*-
# _siv_scan.py — 复核②⑤：独立重跑写域扫描（剪枝+深度上限）+ 门禁位点普查。全程只读。
import hashlib, json, os, re, sys, time
from pathlib import Path

BASE = Path(r"D:\Project\ra2-campaign-forge")
WD = BASE / r"lead\gate_subject_id_20261109"
OUT = {"traversals": []}
PRUNE_NAMES = {".git", "__pycache__", "node_modules", ".tmp"}

def pruned_dirs(d):
    """剪枝子目录：点目录 + PRUNE_NAMES。"""
    for c in sorted(d.iterdir()):
        if c.is_dir() and not c.name.startswith(".") and c.name not in PRUNE_NAMES:
            yield c

def walk_limited(root, max_depth, exts=None, out_files=None):
    """有界遍历：深度上限 max_depth（root=0），返回 (dirsVisited, files by ext list of Path)。"""
    t0 = time.perf_counter()
    dirs_visited = 0
    found = []
    stat_err = 0
    def rec(d, depth):
        nonlocal dirs_visited, stat_err
        dirs_visited += 1
        try:
            entries = sorted(d.iterdir())
        except OSError:
            return
        for e in entries:
            try:
                if e.is_dir():
                    if depth < max_depth and not e.name.startswith(".") and e.name not in PRUNE_NAMES:
                        rec(e, depth + 1)
                elif e.is_file():
                    if exts is None or e.suffix.lower() in exts:
                        found.append(e)
            except OSError:
                stat_err += 1
    rec(root, 0)
    el = round(time.perf_counter() - t0, 4)
    return dirs_visited, found, el, stat_err

# ---------- A) lead/ 递归（深度上限 6） ----------
t0 = time.perf_counter()
lead = BASE / "lead"
dirs_visited = 0
domains = []  # (path, md list)
def rec_lead(d, depth):
    global dirs_visited
    dirs_visited += 1
    mds, subdirs = [], []
    try:
        entries = sorted(d.iterdir())
    except OSError:
        return
    for e in entries:
        if e.is_dir():
            if depth < 6 and not e.name.startswith(".") and e.name not in PRUNE_NAMES:
                subdirs.append(e)
        elif e.is_file() and e.suffix.lower() == ".md":
            mds.append(e)
    if mds:
        try:
            sized = [(p.name, p.stat().st_size) for p in mds]
            domains.append({"dir": str(d.relative_to(BASE)), "mdCount": len(mds),
                            "bare": [(n, s) for n, s in sized if not n.startswith("_")],
                            "under": [(n, s) for n, s in sized if n.startswith("_")]})
        except OSError as ex:
            domains.append({"dir": str(d.relative_to(BASE)), "error": repr(ex)})
    for sd in subdirs:
        rec_lead(sd, depth + 1)
rec_lead(lead, 0)
elapsed_lead = round(time.perf_counter() - t0, 4)

total_md = sum(x.get("mdCount", 0) for x in domains)
underscore_max = []
bare_multi = []
bare_unique_ok_multi = []
bare_single = []
for x in domains:
    if "error" in x:
        continue
    allf = x["bare"] + x["under"]
    mx = max(allf, key=lambda t: t[1])
    if mx[0].startswith("_"):
        baremax = max(x["bare"], key=lambda t: t[1]) if x["bare"] else None
        underscore_max.append({"dir": x["dir"], "picked": mx[0], "pickedBytes": mx[1],
                               "bareCount": len(x["bare"]),
                               "bareMax": (baremax[0] + " (" + str(baremax[1]) + "B)") if baremax else None,
                               "diff": (mx[1] - baremax[1]) if baremax else None})
    if len(x["bare"]) == 0:
        pass
    elif len(x["bare"]) == 1:
        bare_single.append(x["dir"])
    else:
        bare_multi.append({"dir": x["dir"], "bareCount": len(x["bare"])})
        mxu = max(x["under"], key=lambda t: t[1]) if x["under"] else None
        barm = max(x["bare"], key=lambda t: t[1])
        # 多主件域里 max 全域最大是否落在 bare 上
        if not x["under"] or barm[1] >= mxu[1]:
            bare_unique_ok_multi.append(x["dir"])

# 跨域同名（bare 名，按父目录去重）
name_map = {}
for x in domains:
    if "error" in x:
        continue
    for n, s in x["bare"]:
        name_map.setdefault(n, set()).add(x["dir"])
dup_names = {k: sorted(v) for k, v in name_map.items() if len(v) > 1}

# 编排方口径：lead 一级子域、非递归
t1 = time.perf_counter()
lvl1_dirs = 0
lvl1_md = 0
lvl1_underscore_max = []
for c in sorted(lead.iterdir()):
    if c.is_dir():
        try:
            mds = [p for p in c.iterdir() if p.is_file() and p.suffix.lower() == ".md"]
        except OSError:
            mds = []
        if mds:
            lvl1_dirs += 1
            lvl1_md += len(mds)
            sized = [(p.name, p.stat().st_size) for p in mds]
            mx = max(sized, key=lambda t: t[1])
            if mx[0].startswith("_"):
                lvl1_underscore_max.append(c.name + " -> " + mx[0] + " (" + str(mx[1]) + "B)")
elapsed_orch = round(time.perf_counter() - t1, 4)

print("=== A) lead/ recursive depth6 pruned ===")
print("dirsVisited=" + str(dirs_visited) + " elapsedSec=" + str(elapsed_lead) + " domainsWithMd=" + str(len(domains)) + " totalMd=" + str(total_md))
print("underscoreMaxDomains=" + str(len(underscore_max)))
for u in underscore_max:
    print("  " + u["dir"] + " | picked=" + u["picked"] + " (" + str(u["pickedBytes"]) + "B) bareCount=" + str(u["bareCount"]) + " bareMax=" + str(u["bareMax"]) + " diff=" + str(u["diff"]))
print("bareCount==1 domains=" + str(len(bare_single)) + "  bareCount>1 domains=" + str(len(bare_multi)))
multi_top = sorted(bare_multi, key=lambda d: -d["bareCount"])[:5]
print("  top multi-bare: " + "; ".join(d["dir"] + "=" + str(d["bareCount"]) for d in multi_top))
print("dupBareNameSpecies=" + str(len(dup_names)))
for k in sorted(dup_names, key=lambda k: -len(dup_names[k]))[:8]:
    print("  " + k + " x" + str(len(dup_names[k])) + " dirs")
print("orchestrator-style census: lvl1DirsWithMd=" + str(lvl1_dirs) + " lvl1Md=" + str(lvl1_md) + " elapsedSec=" + str(elapsed_orch) + " underscoreMax=" + str(lvl1_underscore_max))

OUT["traversals"].append({"name": "lead_recursive_d6", "dirsVisited": dirs_visited, "elapsedSec": elapsed_lead,
                          "domainsWithMd": len(domains), "totalMd": total_md,
                          "underscoreMaxDomains": underscore_max, "bareMultiCount": len(bare_multi),
                          "bareSingleCount": len(bare_single), "dupNameSpecies": {k: len(v) for k, v in dup_names.items()},
                          "orchLvl1Dirs": lvl1_dirs, "orchLvl1Md": lvl1_md, "orchUnderscoreMax": lvl1_underscore_max})

# ---------- B) lead/ 内 .py 位点 ----------
t2 = time.perf_counter()
dv2, pys, el2, se2 = walk_limited(lead, 6, exts={".py"})
py_max_size, py_max_mtime = [], []
for p in pys:
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for i, ln in enumerate(t.splitlines(), 1):
        if "max(" in ln and "st_size" in ln:
            py_max_size.append(str(p.relative_to(BASE)) + ":" + str(i))
        if "max(" in ln and ("mtime" in ln or "st_mtime" in ln or "getmtime" in ln):
            py_max_mtime.append(str(p.relative_to(BASE)) + ":" + str(i))
print("=== B) lead .py (d6) === dirsVisited=" + str(dv2) + " elapsedSec=" + str(el2) + " pyScanned=" + str(len(pys)) + " statErrors=" + str(se2))
print("max~st_size sites=" + str(len(py_max_size)) + "  max~mtime sites=" + str(len(py_max_mtime)))
for s in py_max_mtime[:10]:
    print("  mtime site: " + s)
OUT["traversals"].append({"name": "lead_py_d6", "dirsVisited": dv2, "elapsedSec": el2, "pyScanned": len(pys),
                          "max_st_size_sites": py_max_size, "max_mtime_sites": py_max_mtime})

# ---------- C) 库根（不含 lead/）.py，深度上限 4 ----------
t3 = time.perf_counter()
dv3, pys3, el3, se3 = walk_limited(BASE, 4, exts={".py"})
pys3 = [p for p in pys3 if not (str(p).startswith(str(BASE / "lead")) or str(p).startswith(str(BASE / ".git")))]
py3_size, py3_mtime = [], []
for p in pys3:
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for i, ln in enumerate(t.splitlines(), 1):
        if "max(" in ln and "st_size" in ln:
            py3_size.append(str(p.relative_to(BASE)) + ":" + str(i))
        if "max(" in ln and ("mtime" in ln or "st_mtime" in ln or "getmtime" in ln):
            py3_mtime.append(str(p.relative_to(BASE)) + ":" + str(i))
print("=== C) root .py (d4, excl lead/.git) === dirsVisited=" + str(dv3) + " elapsedSec=" + str(el3) + " pyScanned=" + str(len(pys3)))
print("max~st_size sites=" + str(len(py3_size)) + "  max~mtime sites=" + str(len(py3_mtime)))
for s in py3_mtime[:10]:
    print("  mtime site: " + s)
OUT["traversals"].append({"name": "root_py_d4", "dirsVisited": dv3, "elapsedSec": el3, "pyScanned": len(pys3),
                          "max_st_size_sites": py3_size, "max_mtime_sites": py3_mtime})

# ---------- D) .zcode 门禁普查（深度上限 3 + agents 深探） ----------
t4 = time.perf_counter()
dv4, mjss, el4, se4 = walk_limited(BASE / ".zcode", 3, exts={".mjs"})
DOC_MAX = "max(cands,key=lambda p:p.stat().st_size)"
docmax_files, explicit_files, maxcands_files, broad_hits = [], [], [], []
wd_map = {}
for p in mjss:
    try:
        t = p.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        continue
    rel = str(p.relative_to(BASE))
    hits = []
    if DOC_MAX in t:
        docmax_files.append(rel)
        hits.append("DOC_MAX")
    if "expected=wd/'" in t:
        explicit_files.append(rel)
        hits.append("EXPLICIT")
    if "max(cands" in t and "DOC_MAX" not in hits:
        maxcands_files.append(rel)
    # 更宽的变体搜捕：max( ... st_size 同行
    for i, ln in enumerate(t.splitlines(), 1):
        if re.search(r"max\([^)\n]{0,80}st_size", ln) and DOC_MAX not in ln and "max(cands,key=lambda p:p.stat().st_size)" not in ln:
            broad_hits.append(rel + ":" + str(i) + " " + ln.strip()[:120])
    m = re.search(r"wd=root/'(lead/[^']+)'", t)
    if m:
        wd_map[rel] = m.group(1)
print("=== D) .zcode mjs (d3) === dirsVisited=" + str(dv4) + " elapsedSec=" + str(el4) + " mjsScanned=" + str(len(mjss)))
print("filesUsingDocMaxStSize=" + str(len(docmax_files)))
print("filesUsingExplicitExpected=" + str(len(explicit_files)) + " -> " + "; ".join(explicit_files))
print("maxCandsOtherFiles=" + str(len(maxcands_files)) + " -> " + "; ".join(maxcands_files[:5]))
print("broadVariantExtraHits=" + str(len(broad_hits)))
for s in broad_hits[:10]:
    print("  " + s)
OUT["traversals"].append({"name": "zcode_mjs_d3", "dirsVisited": dv4, "elapsedSec": el4, "mjsScanned": len(mjss),
                          "docMaxFiles": docmax_files, "explicitFiles": explicit_files,
                          "maxCandsOther": maxcands_files, "broadVariantExtra": broad_hits, "wdMap": wd_map})

# agents 深探（撰写人未扫域）
t5 = time.perf_counter()
agents = BASE / ".zcode" / "agents"
agents_info = None
if agents.is_dir():
    dv5, mjs5, el5, se5 = walk_limited(agents, 3, exts={".mjs", ".py"})
    hits5 = []
    for p in mjs5:
        try:
            t = p.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        if DOC_MAX in t or re.search(r"max\([^)\n]{0,80}st_size", t):
            hits5.append(str(p.relative_to(BASE)))
    agents_info = {"dirsVisited": dv5, "elapsedSec": el5, "filesScanned": len(mjs5), "docMaxHits": hits5}
    print("=== D2) .zcode/agents probe (d3) === dirsVisited=" + str(dv5) + " filesScanned=" + str(len(mjs5)) + " docMaxHits=" + str(len(hits5)) + " elapsedSec=" + str(el5))
    for s in hits5[:10]:
        print("  " + s)
OUT["traversals"].append({"name": "zcode_agents_probe_d3", **(agents_info or {"skipped": True})})

# 36 处清单核对：写域映射
my36 = {}
for rel in docmax_files:
    my36[rel] = wd_map.get(rel, "?")
OUT["docmaxToDomain"] = my36
print("docmax-with-domain-mapped=" + str(sum(1 for v in my36.values() if v != "?")) + "/" + str(len(my36)))

w = WD / "_siv_scan_out.json"
open(w, "w", encoding="utf-8").write(json.dumps(OUT, ensure_ascii=False, indent=1))
print("written=" + str(w))
