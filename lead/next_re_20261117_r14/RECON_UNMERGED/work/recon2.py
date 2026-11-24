# -*- coding: utf-8 -*-
"""快照时序分析：判定每个 delta 行的语义/grade 是「本卡并入」还是「本卡从盘上抄」。"""
import os, re, json, hashlib

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT  = os.path.join(ROOT, "RECON_UNMERGED")
CUR  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
ENTRY_RE = re.compile(r"^[0-9A-Fa-f]{8}$")

CARDS = ["S05_KPROVED4","S05-K2","S07-K2","S09_KPROVED2","S10_K11","S10_K14",
"S11_DIRECT","S11_K5","S13_K11","S19-K2","SEMFIX_6","SEMFIX_REST","SEMFIX_S10",
"SEMFIX_SLOTS","SEMFIX_SLOTS2","SEMFIX_SLOTS3"]

def parse_delta(path):
    rows=[];hdr=None
    with open(path,"r",encoding="utf-8",errors="replace") as f:
        for ln in f.read().split("\n"):
            ln=ln.rstrip("\r")
            if not ln.strip() or ln.lstrip().startswith("#"): continue
            parts=ln.split("\t"); c0=parts[0].strip()
            if hdr is None and not ENTRY_RE.match(c0):
                hdr=[p.strip() for p in parts]; continue
            if not ENTRY_RE.match(c0): continue
            gi=ei=si=ni=None
            if hdr:
                for i,h in enumerate(hdr):
                    if h=="grade": gi=i
                    elif h=="evidence_path": ei=i
                    elif h=="one_line_semantics": si=i
                    elif h=="name": ni=i
            gi = 4 if gi is None else gi
            ei = 5 if ei is None else ei
            si = 3 if si is None else si
            ni = 2 if ni is None else ni
            rows.append({"entry":c0.upper(),
                "subsystem":parts[1].strip() if len(parts)>1 else "",
                "name":parts[ni].strip() if len(parts)>ni else "",
                "semantics":parts[si] if len(parts)>si else "",
                "grade":parts[gi].strip() if len(parts)>gi else "",
                "evidence_path":parts[ei].strip() if len(parts)>ei else ""})
    return rows

# 需要追踪的 entry 全集
need=set(); card_rows={}
for c in CARDS:
    rs=parse_delta(os.path.join(ROOT,c,"coverage_delta.tsv"))
    card_rows[c]=rs
    for r in rs: need.add(r["entry"])
print("cards with rows:",len(CARDS),"distinct entries:",len(need))

# 快照：按 mtime 排序（去掉重复 sha）
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

cands=[]
for m in range(6,22):
    for rel,tag in ((r"_hygiene\M%d_before\coverage.tsv"%m,"M%d_before"%m),
                    (r"_hygiene\M%d_before\COVERAGE\coverage.tsv"%m,"M%d_before"%m)):
        p=os.path.join(ROOT,rel)
        if os.path.exists(p): cands.append((tag,p))
for m in range(23,49):
    p=os.path.join(ROOT,r"_hygiene\coverage.M%d.bak"%m)
    if os.path.exists(p): cands.append(("M%d.bak"%m,p))
for rel,tag in ((r"M4_merge\_backup\coverage.tsv","M4_merge_backup"),
                (r"AUDIT_ATEXIT\work\snapshot\coverage_pinned.tsv","ATEXIT_pinned"),
                (r"P0_RESIDUAL_2\EVIDENCE\coverage_snapshot_14495.tsv","P0RES2_14495")):
    p=os.path.join(ROOT,rel)
    if os.path.exists(p): cands.append((tag,p))

snaps=[]
seen_sha={}
for tag,p in cands:
    s=sha(p)
    if s in seen_sha:            # 同字节快照只保留最早的标签
        continue
    seen_sha[s]=tag
    snaps.append({"tag":tag,"path":p,"sha":s,"mtime":os.path.getmtime(p)})
snaps.sort(key=lambda x:x["mtime"])
print("distinct snapshots:",len(snaps))

def pick(path):
    d={}
    with open(path,"r",encoding="utf-8",errors="replace") as f:
        for i,line in enumerate(f,1):
            line=line.rstrip("\r\n")
            if not line or (i==1 and line.startswith("entry,")): continue
            parts=line.split("\t")
            if len(parts)!=8: continue
            e=parts[0].strip().upper()
            if e in need:
                d[e]={"semantics":parts[3],"grade":parts[4],"evidence_path":parts[5],
                      "name":parts[2],"subsystem":parts[1]}
    return d

# 每个快照抽取所需 entry
tl={}   # entry -> [(tag, mtime, rec)]
cur_state=pick(CUR)
cur_mtime=os.path.getmtime(CUR)
for s in snaps:
    d=pick(s["path"])
    for e,rec in d.items():
        tl.setdefault(e,[]).append((s["tag"],s["mtime"],rec))
for e,rec in cur_state.items():
    tl.setdefault(e,[]).append(("<CURRENT>",cur_mtime,rec))
for e in tl: tl[e].sort(key=lambda x:x[1])

json.dump({"snaps":[{k:v for k,v in s.items() if k!="path"} for s in snaps],
           "timeline":{e:[{"tag":t,"mtime":mt,"grade":r["grade"],"sem_sha":hashlib.sha256(r["semantics"].encode()).hexdigest()[:12],"sem_len":len(r["semantics"]),"ev":r["evidence_path"][:120]} for t,mt,r in v] for e,v in tl.items()}},
          open(os.path.join(OUT,"work","timeline.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)

# 逐行判定
import collections
report=[]
for c in CARDS:
    dmt=os.path.getmtime(os.path.join(ROOT,c,"coverage_delta.tsv"))
    for r in card_rows[c]:
        e=r["entry"]; chain=tl.get(e,[])
        # 该 entry 在快照序列里的语义变迁：找出首次出现 delta 语义的快照
        tgt_sem=r["semantics"]
        first_at=None
        for tag,mt,rec in chain:
            if rec["semantics"].strip()==tgt_sem.strip(): first_at=(tag,mt); break
        # 该 entry 首次出现 delta grade 且 semantics 同时相同的点
        merged_by=None
        if chain:
            prev=None
            for i,(tag,mt,rec) in enumerate(chain):
                same_sem = rec["semantics"].strip()==tgt_sem.strip()
                if same_sem and (prev is None or prev["semantics"].strip()!=tgt_sem.strip()):
                    merged_by=(tag,mt); break
                prev=rec
        cur=cur_state.get(e)
        report.append({
            "card":c,"entry":e,
            "delta_mtime":dmt,
            "delta_grade":r["grade"],"delta_ev":r["evidence_path"][:120],
            "disk_grade":cur["grade"] if cur else None,
            "disk_matches_delta_sem": bool(cur and cur["semantics"].strip()==tgt_sem.strip()),
            "disk_matches_delta_grade": bool(cur and cur["grade"]==r["grade"]),
            "disk_matches_delta_ev": bool(cur and cur["evidence_path"].strip()==r["evidence_path"].strip()),
            "sem_first_seen_at": first_at[0] if first_at else None,
            "sem_first_seen_before_delta": bool(first_at and first_at[1] < dmt),
            "transition_tag": merged_by[0] if merged_by else None,
            "transition_after_delta": bool(merged_by and merged_by[1] > dmt),
            "n_snap_points": len(chain),
        })

json.dump(report,open(os.path.join(OUT,"work","row_verdicts.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)

print("\n=== rows: does disk still hold delta semantics? ===")
by=collections.defaultdict(list)
for x in report: by[x["card"]].append(x)
for c in CARDS:
    xs=by[c]
    print("\n## %s  n=%d  delta_mtime=%s"%(c,len(xs),__import__("datetime").datetime.fromtimestamp(xs[0]["delta_mtime"]).strftime("%m-%d %H:%M")))
    for x in xs:
        print("   %s sem_disk=%s grade_disk=%-10s grade_delta=%-10s first_sem=%s before_delta=%s trans=%s"%(
            x["entry"], "Y" if x["disk_matches_delta_sem"] else "N",
            str(x["disk_grade"]), x["delta_grade"], x["sem_first_seen_at"],
            "Y" if x["sem_first_seen_before_delta"] else "N", x["transition_tag"]))
