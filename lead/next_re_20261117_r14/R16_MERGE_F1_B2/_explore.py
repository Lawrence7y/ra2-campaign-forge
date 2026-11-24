# -*- coding: utf-8 -*-
"""Exploratory analysis for B2 merge - baseline recording + six numbers."""
import os, sys, hashlib, re, json, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL = os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA = os.path.join(ROOT, "R16_F1_B2", "delta.tsv")
OUT = os.path.join(ROOT, "R16_MERGE_F1_B2")

def state(p):
    raw = open(p, "rb").read()
    st = os.stat(p)
    # mtime
    import datetime
    mt = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    # line endings
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n")
    cr = raw.count(b"\r")
    text = raw.decode("utf-8")
    nlines = text.count("\n")  # number of newline chars; trailing-newline aware
    return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                mtime=mt, crlf=crlf, lf_total=lf, cr_total=cr,
                bare_lf=lf-crlf, bare_cr=cr-crlf, newline_chars=nlines,
                ends_with_newline=raw.endswith(b"\n"))

print("=== FILE STATES ===")
for name,p in [("coverage.tsv",COV),("PANEL.md",PANEL),("delta.tsv",DELTA)]:
    s=state(p)
    print(name, json.dumps(s, ensure_ascii=False))

print("\n=== COVERAGE parse ===")
raw = open(COV,"rb").read()
text = raw.decode("utf-8")
lines = text.split("\n")
print("split('\\n') len:", len(lines), "last line repr:", repr(lines[-1][:80]))
header = lines[0]
print("header:", repr(header))
data = [ln for ln in lines[1:] if ln != ""]
print("data rows (nonempty):", len(data))
colcounts = collections.Counter(len(ln.split("\t")) for ln in data)
print("col count dist:", dict(colcounts))
rows = [ln.split("\t") for ln in data]
# grade distribution
grades = collections.Counter(r[4].strip() for r in rows)
print("grade dist:", dict(grades))
proved = sum(1 for r in rows if r[4].strip()=="[已证]")
print("total [已证]:", proved)

# 口径 A: [已证] and col4 (index3) contains ④
A_pre = sum(1 for r in rows if r[4].strip()=="[已证]" and "④" in r[3])
B_pre = sum(1 for r in rows if r[4].strip()=="[已证]" and "④ 活表槽位见证" in r[3])
print("N_A_pre (whole table 口径A):", A_pre)
print("N_B_pre (whole table 口径B):", B_pre)

# atlas in/out for [已证]
import csv
atlas_path = os.path.join(PROJ,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
atlas_entries=set()
if os.path.exists(atlas_path):
    with open(atlas_path,"r",encoding="utf-8",newline="") as f:
        rd=csv.reader(f,delimiter="\t")
        for row in rd:
            if row and re.fullmatch(r"[0-9A-Fa-f]{8}",row[0].strip()):
                atlas_entries.add(row[0].strip().upper())
print("atlas entries loaded:", len(atlas_entries))
in_atlas = sum(1 for r in rows if r[4].strip()=="[已证]" and r[0].strip().upper() in atlas_entries)
out_atlas = proved - in_atlas
print("proved in atlas:", in_atlas, "out atlas:", out_atlas)

print("\n=== DELTA parse ===")
dtext = open(DELTA,"r",encoding="utf-8",newline="").read()
dlines = dtext.split("\n")
dheader=dlines[0]
print("delta header:",repr(dheader))
ddata=[ln for ln in dlines[1:] if ln!=""]
print("delta data rows:",len(ddata))
drows=[ln.split("\t") for ln in ddata]
print("delta col dist:",dict(collections.Counter(len(r) for r in drows)))
dentries=[r[0].strip().upper() for r in drows]
print("delta entries:", dentries)

print("\n=== 18 rows analysis ===")
# find each entry in coverage
row_by_entry={}
for idx,r in enumerate(rows):
    row_by_entry.setdefault(r[0].strip().upper(), []).append(idx)

N_pre_A=0
N_pre_B=0
prefix_bad=[]
col_mismatch=[]
grade_bad=[]
for r in drows:
    e=r[0].strip().upper()
    new4=r[3]
    hits=row_by_entry.get(e,[])
    if len(hits)!=1:
        print("  ENTRY",e,"hit count",len(hits)); continue
    i=hits[0]
    old=rows[i]
    old4=old[3]
    if "④" in old4: N_pre_A+=1
    if "④ 活表槽位见证" in old4: N_pre_B+=1
    if not new4.startswith(old4):
        prefix_bad.append((e,len(old4),len(new4)))
    # compare cols 1,2,3,5,6,7,8 (index 0,1,2,4,5,6,7)
    for ci in [0,1,2,4,5,6,7]:
        if old[ci]!=r[ci]:
            col_mismatch.append((e,ci,repr(old[ci][:60]),repr(r[ci][:60])))
    if old[4].strip()!="[已证]":
        grade_bad.append((e,old[4]))
print("N_pre_A:",N_pre_A)
print("N_pre_B:",N_pre_B)
print("prefix_bad:",prefix_bad)
print("col_mismatch count:",len(col_mismatch))
for m in col_mismatch[:10]: print("  ",m)
print("grade_bad:",grade_bad)
# appended segment analysis
s126=0; s124=0
append_lens=[]
for r in drows:
    e=r[0].strip().upper()
    new4=r[3]
    old=rows[row_by_entry[e][0]][3]
    seg=new4[len(old):]
    append_lens.append(len(seg))
    if "§12.6" in seg: s126+=1
    if "§12.4" in seg: s124+=1
print("append seg §12.6 count:",s126," §12.4 count:",s124)
print("append lens min/max:",min(append_lens),max(append_lens))

print("\n=== PANEL lines 236-250 ===")
plines = text_panel = open(PANEL,"r",encoding="utf-8",newline="").read().split("\n")
for i in range(236,251):
    if i-1 < len(plines):
        print(i, repr(plines[i-1][:160]))
