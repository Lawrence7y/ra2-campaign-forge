# -*- coding: utf-8 -*-
"""最终逐行判定表：对 26 张卡的每个 delta 行，给出
   - grade / semantics 在快照线上的变迁点（.bak=合并前备份，故变迁卡号=前一张 M）
   - MERGE_LOG 中登记该 entry 的记录（来源卡 + 依据）
   - 判定 A/B/C
"""
import os, re, json, hashlib, collections

ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
OUT  = os.path.join(ROOT,"RECON_UNMERGED")
CUR  = os.path.join(ROOT,"COVERAGE","coverage.tsv")
ENTRY_RE = re.compile(r"^[0-9A-Fa-f]{8}$")
AUDIT_RE = re.compile(r"([A-Za-z0-9_\-\.]+)/_audit/VERDICT\.md")

CARDS = ["S01_KPROVED","S03_C8","S05_KPROVED4","S05_KPROVED5","S05-K2","S07-K2",
"S09_KPROVED2","S10_K11","S10_K14","S10_KPROVED4","S11_DIRECT","S11_K5","S13_DIRECT",
"S13_K11","S13_KPROVED2","S15_K5","S16_N2","S19-K2","S21_KPROVED2","SEMFIX_6",
"SEMFIX_REST","SEMFIX_S10","SEMFIX_SLOTS","SEMFIX_SLOTS2","SEMFIX_SLOTS3","W177_KA"]

def parse_delta(path):
    rows=[];hdr=None
    if not os.path.exists(path): return rows
    with open(path,"r",encoding="utf-8",errors="replace") as f:
        for ln in f.read().split("\n"):
            ln=ln.rstrip("\r")
            if not ln.strip() or ln.lstrip().startswith("#"): continue
            parts=ln.split("\t"); c0=parts[0].strip()
            if hdr is None and not ENTRY_RE.match(c0):
                hdr=[p.strip() for p in parts]; continue
            if not ENTRY_RE.match(c0): continue
            gi=ei=si=None
            if hdr:
                for i,h in enumerate(hdr):
                    if h=="grade":gi=i
                    elif h=="evidence_path":ei=i
                    elif h=="one_line_semantics":si=i
            gi=4 if gi is None else gi; ei=5 if ei is None else ei; si=3 if si is None else si
            rows.append({"entry":c0.upper(),
                "semantics":parts[si] if len(parts)>si else "",
                "grade":parts[gi].strip() if len(parts)>gi else "",
                "evidence_path":parts[ei].strip() if len(parts)>ei else ""})
    return rows

card_rows={c:parse_delta(os.path.join(ROOT,c,"coverage_delta.tsv")) for c in CARDS}
need={r["entry"] for c in CARDS for r in card_rows[c]}

# 快照序列（.bak = 该 M 卡的合并前备份）
snaps=[]
for m in range(23,49):
    p=os.path.join(ROOT,r"_hygiene\coverage.M%d.bak"%m)
    if os.path.exists(p): snaps.append(("M%d_before"%m,os.path.getmtime(p),p))
for m in range(6,22):
    for rel,tag in ((r"_hygiene\M%d_before\coverage.tsv"%m,"M%d_before"%m),
                    (r"_hygiene\M%d_before\COVERAGE\coverage.tsv"%m,"M%d_before"%m)):
        p=os.path.join(ROOT,rel)
        if os.path.exists(p): snaps.append((tag,os.path.getmtime(p),p))
snaps.append(("<CURRENT>",os.path.getmtime(CUR),CUR))
snaps.sort(key=lambda x:x[1])

def pick(path):
    d={}
    for l in open(path,encoding="utf-8",errors="replace"):
        if l.startswith("entry,"): continue
        p=l.rstrip("\n").split("\t")
        if len(p)!=8: continue
        e=p[0].strip().upper()
        if e in need: d[e]=(p[3],p[4])
    return d

series=[]   # [(tag, mtime, {entry:(sem,grade)})]
for tag,mt,p in snaps:
    series.append((tag,mt,pick(p)))
print("snapshot points:",len(series))

def transition(entry, want_sem=None, want_grade=None):
    """返回 (tag_first_key, prev_tag) 表示 key 首次出现的快照点"""
    prev=None; first=None
    for tag,mt,d in series:
        v=d.get(entry)
        if v is None: 
            prev=None; continue
        sem,g=v
        ok=True
        if want_sem is not None: ok = ok and sem.strip()==want_sem.strip()
        if want_grade is not None: ok = ok and g==want_grade
        if ok and (prev is None or not _ok(prev,want_sem,want_grade)):
            first=(tag,prev); break
        prev=v
    return first

def _ok(v,want_sem,want_grade):
    sem,g=v; ok=True
    if want_sem is not None: ok=ok and sem.strip()==want_sem.strip()
    if want_grade is not None: ok=ok and g==want_grade
    return ok

# MERGE_LOG 索引
recs=collections.defaultdict(list)
for m in range(1,50):
    p=os.path.join(ROOT,"M%d"%m,"MERGE_LOG.tsv")
    if not os.path.exists(p): continue
    lines=[l for l in open(p,encoding="utf-8",errors="replace").read().split("\n") if l.strip()]
    hdr=lines[0].split("\t")
    for l in lines[1:]:
        parts=l.split("\t")
        if not parts or not ENTRY_RE.match(parts[0].strip()): continue
        e=parts[0].strip().upper()
        if e not in need: continue
        r=dict(zip(hdr,parts)); r["_m"]="M%d"%m
        recs[e].append(r)

cur={}
for l in open(CUR,encoding="utf-8",errors="replace"):
    if l.startswith("entry,"): continue
    p=l.rstrip("\n").split("\t")
    if len(p)!=8: continue
    cur[p[0].strip().upper()]={"grade":p[4],"semantics":p[3],"name":p[2],"ev":p[5]}

out=[]
for c in CARDS:
    for r in card_rows[c]:
        e=r["entry"]; d=cur.get(e)
        sem_tr=transition(e,want_sem=r["semantics"])
        gr_tr=transition(e,want_grade=r["grade"])
        rr=recs.get(e,[])
        out.append({
          "card":c,"entry":e,
          "delta_grade":r["grade"],
          "disk_grade":d["grade"] if d else None,
          "disk_sem_eq": bool(d and d["semantics"].strip()==r["semantics"].strip()),
          "sem_first_at": sem_tr[0] if sem_tr else None,
          "sem_prev": sem_tr[1] if sem_tr else None,
          "grade_first_at": gr_tr[0] if gr_tr else None,
          "merge_recs":[{"m":x["_m"],
                         "basis":(x.get("evidence_or_basis") or "")[:160],
                         "note":(x.get("note") or "")[:80],
                         "src_card":x.get("source_card","")} for x in rr],
        })

json.dump(out,open(os.path.join(OUT,"work","final_table.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)

print("\n=== 已并入候选：磁盘语义等于 delta 语义的行 ===")
for x in out:
    if x["disk_sem_eq"]:
        print("%-14s %s grade %s->%s sem_first=%s grade_first=%s recs=%s"%(
          x["card"],x["entry"],x["delta_grade"],x["disk_grade"],x["sem_first_at"],x["grade_first_at"],
          [ (y["m"],y["src_card"]) for y in x["merge_recs"]][:3]))
