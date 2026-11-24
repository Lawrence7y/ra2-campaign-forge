# -*- coding: utf-8 -*-
"""R16-MERGE-SLOTN-B1 · 前置快照 + 只读预检。
只读打开 coverage.tsv / PANEL.md / delta.tsv，不写任何文件（除打印）。
"""
import csv, hashlib, json, os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_SLOTN_B1", "delta.tsv")

def sha(b): return hashlib.sha256(b).hexdigest()
def stat(p):
    st = os.stat(p)
    with open(p, "rb") as f: b = f.read()
    return dict(path=p, mtime=st.st_mtime, mtime_utc=st.st_mtime,
                bytes=len(b), sha256=sha(b),
                nlines_lf=b.count(b"\n"), crlf=b.count(b"\r\n"), lf_only=b.count(b"\n")-b.count(b"\r\n"))

def parse_tsv_bytes(b):
    # splitlines keep line endings off; use utf-8-sig decode
    txt = b.decode("utf-8-sig")
    lines = txt.splitlines()
    hdr = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        rows.append(ln.split("\t"))
    return hdr, rows

if __name__ == "__main__":
    cov_b = open(COV, "rb").read()
    pan_b = open(PANEL, "rb").read()
    print("=== FRONT MATTER ===")
    print("COV ", json.dumps(stat(COV), ensure_ascii=False))
    print("PAN ", json.dumps(stat(PANEL), ensure_ascii=False))

    # coverage invariants (respect csv.reader semantics as strict_panel does)
    txt = cov_b.decode("utf-8-sig")
    all_lines = txt.splitlines()
    data = all_lines[1:]
    coldist = collections.Counter()
    n_yizheng = 0
    n_sih_yizheng = 0
    # atlas
    ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
    atlas = set()
    with open(ATLAS, encoding="utf-8-sig") as f:
        for i, line in enumerate(f):
            if i == 0: continue
            p = line.rstrip("\r\n").split("\t")
            if p and p[0].strip():
                e = p[0].strip().upper()
                if e.startswith("0X"): e = e[2:]
                try: e = "%08X" % int(e,16)
                except: pass
                atlas.add(e)
    def ne(e):
        e=e.strip().upper()
        if e.startswith("0X"): e=e[2:]
        try: return "%08X"%int(e,16)
        except: return e
    atlas_in_yz = 0; atlas_out_yz = 0
    for ln in data:
        c = ln.split("\t")
        coldist[len(c)] += 1
        if len(c) < 8: continue
        grade = c[4].strip()
        if grade == "[已证]":
            n_yizheng += 1
            if "④" in c[3]:
                n_sih_yizheng += 1
            if ne(c[0]) in atlas:
                atlas_in_yz += 1
            else:
                atlas_out_yz += 1
    print("=== BASELINE (before) ===")
    print("data_rows", len(data), "coldist", dict(coldist))
    print("[已证]", n_yizheng, "atlas内[已证]", atlas_in_yz, "atlas外[已证]", atlas_out_yz)
    print("④已成文([已证]&col4 has ④)", n_sih_yizheng, "pct", round(100.0*n_sih_yizheng/n_yizheng,2))

    # delta read + preflight
    dh, drows = parse_tsv_bytes(open(DELTA,"rb").read())
    print("=== DELTA ===")
    print("header", dh, "nrows", len(drows))
    # map coverage by entry
    cov_by_entry = {}
    for ln in data:
        c = ln.split("\t")
        if len(c) >= 8:
            cov_by_entry.setdefault(ne(c[0]), []).append(c)
    OLD="R14_COMMON §12.4"; NEW="R14_COMMON §12.6"
    strict_pref = 0; repl_total = 0
    for i, d in enumerate(drows, 1):
        e = ne(d[0]); d4 = d[3]
        cand = cov_by_entry.get(e, [])
        if len(cand) != 1:
            print("  ROW %d %s: cov matches=%d  <-- ABNORMAL" % (i,e,len(cand)))
            continue
        cov4 = cand[0][3]
        ok = d4.startswith(cov4)
        cnt = d4.count(OLD)
        strict_pref += int(ok); repl_total += cnt
        # other cols equality
        other_ok = all(cand[0][j]==d[j] for j in [0,1,2,4,5,6,7])
        print("  ROW %2d %s strict_prefix=%s repl§12.4=%d other7cols=%s suffix_bytes=%d cov4_has④=%s" % (
            i,e,ok,cnt,other_ok,len(d4)-len(cov4), "④" in cov4))
    print("strict_prefix_total", strict_pref, "/", len(drows))
    print("replacement_total(§12.4→§12.6)", repl_total, "(expected 15)")
