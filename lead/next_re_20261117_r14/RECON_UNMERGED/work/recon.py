# -*- coding: utf-8 -*-
"""
RECON-UNMERGED: 只读完整性核查。
问题：26 张无 _audit/VERDICT.md 的卡，其 coverage_delta.tsv 行是否被并入 COVERAGE/coverage.tsv。
不改任何既有文件；所有输出写 RECON_UNMERGED/。
"""
import os, re, json, hashlib, io, sys

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
CUR = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
OUT = os.path.join(ROOT, "RECON_UNMERGED")

CARDS = ["S01_KPROVED","S03_C8","S05_KPROVED4","S05_KPROVED5","S05-K2","S07-K2",
"S09_KPROVED2","S10_K11","S10_K14","S10_KPROVED4","S11_DIRECT","S11_K5","S13_DIRECT",
"S13_K11","S13_KPROVED2","S15_K5","S16_N2","S19-K2","S21_KPROVED2","SEMFIX_6",
"SEMFIX_REST","SEMFIX_S10","SEMFIX_SLOTS","SEMFIX_SLOTS2","SEMFIX_SLOTS3","W177_KA"]

GRADES = ("[已证]","[静态推断]","[未证]")
ENTRY_RE = re.compile(r"^[0-9A-Fa-f]{8}$")

def norm_entry(e):
    return e.strip().upper()

def sha(p):
    h = hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda: f.read(1<<20), b""):
            h.update(b)
    return h.hexdigest()

# ---------- 1. 载入当前基线 ----------
def load_cov(path):
    """返回 dict entry -> dict(fields, raw, lineno); 以及重复 entry 列表"""
    d = {}
    dups = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f, 1):
            line = line.rstrip("\r\n")
            if not line: continue
            if i == 1 and line.startswith("entry,"):   # 表头（逗号）
                header = line
                continue
            parts = line.split("\t")
            if len(parts) != 8:
                print("BADCOLS", path, i, len(parts)); continue
            e = norm_entry(parts[0])
            rec = {"entry":e, "subsystem":parts[1], "name":parts[2],
                   "semantics":parts[3], "grade":parts[4], "evidence_path":parts[5],
                   "n_sources":parts[6], "conflict":parts[7], "lineno":i, "raw":line}
            if e in d: dups.append((e, d[e]["lineno"], i))
            d[e] = rec
    return d, dups

cur, dups = load_cov(CUR)
print("current coverage rows:", len(cur), "dups:", len(dups))

# ---------- 2. 快照时间线 ----------
SNAPS = []
def add_snap(tag, rel):
    p = os.path.join(ROOT, rel)
    if os.path.exists(p):
        SNAPS.append({"tag":tag, "path":p, "mtime":os.path.getmtime(p), "sha":sha(p), "size":os.path.getsize(p)})

for m in range(6, 22):
    add_snap("M%d_before"%m, r"_hygiene\M%d_before\coverage.tsv"%m)
    add_snap("M%d_before(C)"%m, r"_hygiene\M%d_before\COVERAGE\coverage.tsv"%m)
for m in list(range(23,49)):
    add_snap("M%d.bak"%m, r"_hygiene\coverage.M%d.bak"%m)
add_snap("M4_merge_backup", r"M4_merge\_backup\coverage.tsv")
add_snap("AUDIT_ATEXIT_pinned", r"AUDIT_ATEXIT\work\snapshot\coverage_pinned.tsv")
add_snap("P0_RESIDUAL_2_14495", r"P0_RESIDUAL_2\EVIDENCE\coverage_snapshot_14495.tsv")
SNAPS.sort(key=lambda x: x["mtime"])
print("snapshots:", len(SNAPS))

cur_sha = sha(CUR)
print("current sha:", cur_sha[:16], "size", os.path.getsize(CUR))
for s in SNAPS:
    s["is_current"] = (s["sha"] == cur_sha)
    if s["is_current"]: print("  snapshot == CURRENT:", s["tag"])

# ---------- 3. 解析 delta ----------
def parse_delta(path):
    rows = []
    if not os.path.exists(path): return rows
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().split("\n")
    hdr = None
    for ln in lines:
        ln = ln.rstrip("\r")
        if not ln.strip(): continue
        if ln.lstrip().startswith("#"): continue
        parts = ln.split("\t")
        c0 = parts[0].strip()
        if hdr is None and not ENTRY_RE.match(c0):
            hdr = [p.strip() for p in parts]
            continue
        if not ENTRY_RE.match(c0): continue
        # 定位列
        gi = None; ei = None
        if hdr:
            for i,h in enumerate(hdr):
                if h in ("grade",): gi = i
                if h in ("evidence_path",): ei = i
        if gi is None:
            gi = 4 if len(parts) > 4 else None
        if ei is None:
            ei = 5 if len(parts) > 5 else None
        rows.append({
            "entry": norm_entry(c0),
            "subsystem": parts[1].strip() if len(parts)>1 else "",
            "name": parts[2].strip() if len(parts)>2 else "",
            "semantics": parts[3] if len(parts)>3 else "",
            "grade": parts[gi].strip() if gi is not None and len(parts)>gi else "",
            "evidence_path": parts[ei].strip() if ei is not None and len(parts)>ei else "",
            "ncol": len(parts),
        })
    return rows

# ---------- 4. 合并记录索引（MERGE_LOG / REPORT） ----------
MERGE_LOGS = []
for m in list(range(22,50)):
    p = os.path.join(ROOT, "M%d"%m, "MERGE_LOG.tsv")
    if os.path.exists(p): MERGE_LOGS.append(("M%d"%m, p))
for tag in ("M2_merge","M3_merge","M4_merge","M5_merge"):
    p = os.path.join(ROOT, tag, "REPORT.md")
    if os.path.exists(p): MERGE_LOGS.append((tag, p))

ml_index = {}   # entry -> list of records
for mtag, p in MERGE_LOGS:
    if p.endswith(".tsv"):
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = [l.rstrip("\r\n") for l in f if l.strip()]
        hdr = lines[0].split("\t")
        for l in lines[1:]:
            parts = l.split("\t")
            if not parts or not ENTRY_RE.match(parts[0].strip()): continue
            rec = dict(zip(hdr, parts))
            rec["_m"] = mtag
            rec["_src"] = p
            ml_index.setdefault(norm_entry(parts[0]), []).append(rec)
print("MERGE_LOG records entries:", len(ml_index))

# ---------- 5. 逐卡逐行判定 ----------
AUDIT_CITE_RE = re.compile(r"([A-Za-z0-9_\-]+)/_audit/VERDICT\.md")

def find_audit_citation(recs):
    cites = []
    for r in recs:
        blob = "\t".join(str(v) for k,v in r.items() if not k.startswith("_"))
        for m in AUDIT_CITE_RE.finditer(blob):
            cites.append((m.group(1), r["_m"]))
    return cites

result = []
for card in CARDS:
    dpath = os.path.join(ROOT, card, "coverage_delta.tsv")
    rows = parse_delta(dpath)
    own_verdict = os.path.exists(os.path.join(ROOT, card, "_audit", "VERDICT.md"))
    per = []
    for r in rows:
        d = cur.get(r["entry"])
        if d is None:
            per.append({**r, "disk":"ABSENT"})
            continue
        g_match = (d["grade"] == r["grade"])
        s_match = (d["semantics"].strip() == r["semantics"].strip())
        e_match = (d["evidence_path"].strip() == r["evidence_path"].strip())
        per.append({**r,
            "disk": "PRESENT",
            "disk_grade": d["grade"], "disk_sem": d["semantics"], "disk_ev": d["evidence_path"],
            "disk_name": d["name"], "disk_subsys": d["subsystem"],
            "g_match": g_match, "s_match": s_match, "e_match": e_match,
            "ml": ml_index.get(r["entry"], []),
        })
    result.append({"card":card, "own_verdict":own_verdict, "nrows":len(rows), "rows":per})

# ---------- 6. 快照差分：定位该行被写入的时点 ----------
def snap_rows_at(tag):
    for s in SNAPS:
        if s["tag"] == tag: return s
    return None

# 用于候选 entry 的判定
def load_snap_cov(s):
    return load_cov(s["path"])[0]

json.dump({"cur_sha":cur_sha, "n_cur":len(cur), "dups":dups,
           "snapshots":[{k:s[k] for k in ("tag","mtime","sha","size","is_current")} for s in SNAPS],
           "cards":[
              {"card":c["card"], "own_verdict":c["own_verdict"], "nrows":c["nrows"],
               "rows":[ {k:(v if k!="ml" else [{kk:vv for kk,vv in r.items() if kk in ("_m","evidence_or_basis","note","col_changed","old_value","new_value")} for r in v]) for k,v in r.items()} for r in c["rows"] ]}
              for c in result]},
          open(os.path.join(OUT,"work","recon_raw.json"),"w",encoding="utf-8"),
          ensure_ascii=False, indent=1)

# 控制台摘要
print("\n=== per card summary ===")
for c in result:
    n = c["nrows"]
    present = sum(1 for r in c["rows"] if r.get("disk")=="PRESENT")
    gs = sum(1 for r in c["rows"] if r.get("g_match") and r.get("s_match"))
    gm = sum(1 for r in c["rows"] if r.get("g_match"))
    sm = sum(1 for r in c["rows"] if r.get("s_match"))
    print("%-14s nrows=%-3d present=%-3d grade_match=%-3d sem_match=%-3d both=%-3d own_verdict=%s"
          %(c["card"], n, present, gm, sm, gs, c["own_verdict"]))
