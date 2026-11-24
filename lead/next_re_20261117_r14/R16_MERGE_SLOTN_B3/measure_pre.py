# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B3 · READ-ONLY pre-state measurement.

Reads current on-disk coverage.tsv / PANEL.md / delta.tsv and computes, from
scratch, every number the card §2.1 requires. No predicted / old value is used.
Writes nothing to target files; only prints JSON to stdout.
"""
import hashlib, json, os, re, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B3", "delta.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

C4 = "\u2463"                 # ④
SB = "④ 活表槽位见证"          # 口径 B 子串
S126 = "§12.6"
S124 = "§12.4"

def sha(b): return hashlib.sha256(b).hexdigest()

def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

def eol(b):
    return dict(CRLF=b.count(b"\r\n"),
                LF=b.count(b"\n")-b.count(b"\r\n"),
                CR=b.count(b"\r")-b.count(b"\r\n"),
                BOM=(b[:3]==b"\xef\xbb\xbf"),
                ends_nl=b.endswith(b"\n"))

def statinfo(p):
    import datetime
    st=os.stat(p); b=open(p,"rb").read()
    iso=datetime.datetime.fromtimestamp(st.st_mtime,
        datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    return dict(path=p, mtime=st.st_mtime, mtime_local=iso,
                bytes=len(b), sha256=sha(b), lines_nl=b.count(b"\n"),
                eol=eol(b))

def load_atlas():
    s=set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i,line in enumerate(f):
            if i==0: continue
            p=line.rstrip("\r\n").split("\t")
            if p and p[0].strip(): s.add(ne(p[0]))
    return s

def parse_cov(text):
    # split strictly on \n (files measured to be LF-only); keep line content
    lines=text.split("\n")
    # trailing empty if file ends with \n
    header=lines[0]
    data=[ln for ln in lines[1:] if ln!=""]
    return header, data

def cov_metrics(data, atlas):
    coldist=collections.Counter(len(ln.split("\t")) for ln in data)
    yz=ina=outa=na=nb=0
    s126_lines=s124_lines=s126_hits=s124_hits=0
    for ln in data:
        c=ln.split("\t")
        if len(c)<8: continue
        if "[已证]"==c[4].strip():
            yz+=1
            if ne(c[0]) in atlas: ina+=1
            else: outa+=1
            if C4 in c[3]: na+=1
            if SB in c[3]: nb+=1
        if S126 in ln: s126_lines+=1
        if S124 in ln: s124_lines+=1
        s126_hits+=ln.count(S126)
        s124_hits+=ln.count(S124)
    return dict(data_rows=len(data), coldist={str(k):v for k,v in coldist.items()},
                yizheng=yz, atlas_in=ina, atlas_out=outa,
                N_A=na, N_B=nb,
                s126_lines=s126_lines, s124_lines=s124_lines,
                s126_hits=s126_hits, s124_hits=s124_hits)

def main():
    cov_b=open(COV,"rb").read(); pan_b=open(PANEL,"rb").read(); del_b=open(DELTA,"rb").read()
    cov_info=statinfo(COV); pan_info=statinfo(PANEL); del_info=statinfo(DELTA)
    cov_text=cov_b.decode("utf-8"); pan_text=pan_b.decode("utf-8")
    del_text=del_b.decode("utf-8-sig")

    header, data=parse_cov(cov_text)
    atlas=load_atlas()
    m=cov_metrics(data, atlas)

    # delta rows
    dlines=del_text.split("\n")
    drows=[ln.split("\t") for ln in dlines[1:] if ln!=""]
    by_entry={}
    for idx,ln in enumerate(data):
        c=ln.split("\t")
        if len(c)>=8: by_entry.setdefault(ne(c[0]),[]).append(idx)

    targets=[]
    for d in drows:
        e=ne(d[0]); idxs=by_entry.get(e,[])
        entry=dict(entry=e, name=d[2], delta_ncol=len(d),
                   found=(len(idxs)==1), idxs=idxs)
        if len(idxs)==1:
            i=idxs[0]; c=data[i].split("\t")
            entry.update(cov_ncol=len(c),
                         cov_col4=c[3], delta_col4=d[3],
                         strict_prefix=d[3].startswith(c[3]),
                         other_cols_equal=all(c[j]==d[j] for j in (0,1,2,4,5,6,7)),
                         cov_grade=c[4].strip(),
                         before_has_c4=(C4 in c[3]),
                         before_has_sb=(SB in c[3]),
                         append_seg=d[3][len(c[3]):] if d[3].startswith(c[3]) else None,
                         added_bytes=len(d[3].encode("utf-8"))-len(c[3].encode("utf-8")))
            if entry["append_seg"] is not None:
                entry["append_s126_hits"]=entry["append_seg"].count(S126)
                entry["append_s124_hits"]=entry["append_seg"].count(S124)
        targets.append(entry)

    N_pre=sum(1 for t in targets if t.get("before_has_c4"))
    append_s126=sum(t.get("append_s126_hits",0) for t in targets)
    append_s124=sum(t.get("append_s124_hits",0) for t in targets)

    # PANEL anchors
    pan_lines=pan_text.split("\n")
    m87=[i for i,l in enumerate(pan_lines) if l.startswith("> ✅ **M87 补记")]
    m77=[i for i,l in enumerate(pan_lines) if l.startswith("> 📌 **M77 并表实算说明**")]
    m88=[i for i,l in enumerate(pan_lines) if l.startswith("> ✅ **M88 补记")]
    m86=[i for i,l in enumerate(pan_lines) if l.startswith("> ✅ **M86 补记")]

    out=dict(
        coverage=cov_info, panel=pan_info, delta=del_info,
        header=header,
        metrics_before=m,
        atlas_entries=len(atlas),
        n_delta_rows=len(drows),
        N_pre=N_pre,
        N_A_pre=m["N_A"], N_B_pre=m["N_B"],
        append_s126_hits=append_s126, append_s124_hits=append_s124,
        strict_prefix_ok=sum(1 for t in targets if t.get("strict_prefix")),
        other_cols_ok=sum(1 for t in targets if t.get("other_cols_equal")),
        targets=targets,
        panel_anchors=dict(m86=m86,m87=m87,m77=m77,m88=m88),
    )
    print(json.dumps(out, ensure_ascii=False, indent=1))

if __name__=="__main__": main()
