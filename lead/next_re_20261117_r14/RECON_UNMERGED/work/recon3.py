# -*- coding: utf-8 -*-
"""归属分析：对每个 delta entry，在全部并表记录里找「谁并入的 + 引了哪份审计」。"""
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
            gi=ei=si=ni=None
            if hdr:
                for i,h in enumerate(hdr):
                    if h=="grade":gi=i
                    elif h=="evidence_path":ei=i
                    elif h=="one_line_semantics":si=i
                    elif h=="name":ni=i
            rows.append({"entry":c0.upper(),
                "name":parts[(ni if ni is not None else 2)].strip() if len(parts)>2 else "",
                "semantics":parts[(si if si is not None else 3)] if len(parts)>(si if si is not None else 3) else "",
                "grade":parts[(gi if gi is not None else 4)].strip() if len(parts)>(gi if gi is not None else 4) else "",
                "evidence_path":parts[(ei if ei is not None else 5)].strip() if len(parts)>(ei if ei is not None else 5) else ""})
    return rows

need=set(); card_rows={}
for c in CARDS:
    rs=parse_delta(os.path.join(ROOT,c,"coverage_delta.tsv")); card_rows[c]=rs
    for r in rs: need.add(r["entry"])

# ---- 收集全部并表记录源 ----
REC_SRC=[]
for m in range(1,50):
    d=os.path.join(ROOT,"M%d"%m)
    if os.path.isdir(d):
        for fn in ("MERGE_LOG.tsv",):
            p=os.path.join(d,fn)
            if os.path.exists(p): REC_SRC.append(("M%d"%m,p,"tsv"))
for tag in ("M2_merge","M3_merge","M4_merge","M5_merge","_hygiene"):
    d=os.path.join(ROOT,tag)
    if os.path.isdir(d):
        for fn in os.listdir(d):
            if re.match(r"M\d+_REPORT\.md$",fn) or fn in ("REPORT.md","M8_RECON.tsv"):
                REC_SRC.append((tag+"/"+fn, os.path.join(d,fn), "md"))

# entry -> list of records
attr=collections.defaultdict(list)
log_stat=[]
for tag,p,kind in REC_SRC:
    try: txt=open(p,encoding="utf-8",errors="replace").read()
    except Exception as e: continue
    if kind=="tsv":
        lines=[l for l in txt.split("\n") if l.strip()]
        hdr=lines[0].split("\t")
        for l in lines[1:]:
            parts=l.split("\t")
            if not parts or not ENTRY_RE.match(parts[0].strip()): continue
            e=parts[0].strip().upper()
            if e not in need: continue
            rec=dict(zip(hdr,parts)); rec["_src"]=tag
            attr[e].append(rec)
        log_stat.append((tag,len([l for l in lines[1:] if ENTRY_RE.match(l.split("\t")[0].strip())])))
    else:
        # markdown：按行找 entry
        for ln in txt.split("\n"):
            for mt in re.finditer(r"\b([0-9A-Fa-f]{8})\b",ln):
                e=mt.group(1).upper()
                if e in need: attr[e].append({"_src":tag,"_line":ln.strip()[:400],"evidence_or_basis":ln,"note":""})

json.dump({"_log_stat":log_stat}, open(os.path.join(OUT,"work","_logstat.json"),"w"), ensure_ascii=False)
print("merge record sources:",len(REC_SRC))
print("entries with attribution:",len(attr),"/",len(need))

# ---- audit 存在性 ----
def audit_exists(card):
    return os.path.exists(os.path.join(ROOT,card,"_audit","VERDICT.md"))

rows_out=[]
for c in CARDS:
    for r in card_rows[c]:
        recs=attr.get(r["entry"],[])
        # 只看引用了本卡 delta 或本卡名的记录
        own=[x for x in recs if c in json.dumps(x,ensure_ascii=False)]
        any_audits=[]
        for x in recs:
            blob=json.dumps(x,ensure_ascii=False)
            for mt in AUDIT_RE.finditer(blob):
                any_audits.append((mt.group(1), x.get("_src")))
        rows_out.append({"card":c,"entry":r["entry"],"delta_grade":r["grade"],
                         "n_recs":len(recs),"own_recs":[{k:v for k,v in x.items() if k in ("_src","evidence_or_basis","note","source_card","old_semantics","col_changed","new_value","_line")} for x in own],
                         "audits_cited":sorted(set(any_audits))})
json.dump(rows_out,open(os.path.join(OUT,"work","attrib.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)

print("\n=== attribution summary per card ===")
by=collections.defaultdict(list)
for x in rows_out: by[x["card"]].append(x)
for c in CARDS:
    xs=by[c]
    if not xs: print("%-14s (0 delta rows)"%c); continue
    withrec=sum(1 for x in xs if x["n_recs"]>0)
    withown=sum(1 for x in xs if x["own_recs"])
    auds=sorted({a for x in xs for a,_ in x["audits_cited"]})
    print("%-14s rows=%-3d has_any_rec=%-3d has_own_rec=%-3d audits_cited=%s"%(c,len(xs),withrec,withown,auds))
