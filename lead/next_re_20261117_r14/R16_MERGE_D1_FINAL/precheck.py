# -*- coding: utf-8 -*-
"""R16-MERGE-D1-FINAL · 只读预检 + 落 pin / before_col4。

只读打开 coverage.tsv / PANEL.md / delta.tsv / function_atlas.tsv；
只写本目录（_pin_coverage.tsv / _pin_PANEL.md / before_col4.json / baseline.json）。
"""
import csv, hashlib, json, os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_FINAL")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_D1_FINAL", "delta.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

def sha(b): return hashlib.sha256(b).hexdigest()
def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

# ---- read raw bytes ----
cov_b  = open(COV, "rb").read()
pan_b  = open(PANEL, "rb").read()
delta_b= open(DELTA, "rb").read()

# ---- write pins (own dir only) ----
open(os.path.join(OUT, "_pin_coverage.tsv"), "wb").write(cov_b)
open(os.path.join(OUT, "_pin_PANEL.md"), "wb").write(pan_b)

# ---- parse coverage at byte level ----
cov_lines = cov_b.split(b"\n")           # last element may be b"" if trailing LF
trailing_lf = cov_b.endswith(b"\n")
txt = cov_b.decode("utf-8")
all_lines = txt.split("\n")
header = all_lines[0]
data_lines = all_lines[1:]
if trailing_lf:
    data_lines = data_lines[:-1]         # drop the empty string after final LF
hdr_cols = header.split(",")             # header is comma separated

rows = []
for ln in data_lines:
    rows.append(ln.split("\t"))          # data rows TAB separated

coldist = collections.Counter(len(r) for r in rows)
n_yz = 0
yz_atlas_in = 0
yz_atlas_out = 0
n_A = 0
n_B = 0
n_CLSID_None = 0
n_126_lines = 0
n_126_occ = 0

atlas = set()
with open(ATLAS, encoding="utf-8-sig") as f:
    for i, line in enumerate(f):
        if i == 0: continue
        p = line.rstrip("\r\n").split("\t")
        if p and p[0].strip(): atlas.add(ne(p[0]))

for r in rows:
    if len(r) < 8: continue
    if r[4].strip() == "[已证]":
        n_yz += 1
        if "④" in r[3]: n_A += 1
        if "④ 活表槽位见证" in r[3]: n_B += 1
        if ne(r[0]) in atlas: yz_atlas_in += 1
        else: yz_atlas_out += 1
    if "CLSID None" in "\t".join(r): n_CLSID_None += 1
    if "§12.6" in r[3]:
        n_126_lines += 1
        n_126_occ += r[3].count("§12.6")

# ---- delta ----
dlines = delta_b.decode("utf-8-sig").split("\n")
if dlines and dlines[-1] == "": dlines = dlines[:-1]
dhdr = dlines[0].split("\t")
drows = [ln.split("\t") for ln in dlines[1:]]

cov_by_entry = {}
for idx, r in enumerate(rows):
    if len(r) >= 8:
        cov_by_entry.setdefault(ne(r[0]), []).append(idx)

targets = ["0051B1F0", "0051DAF0", "00522340", "0070B570", "00748190"]
before_col4 = {}
pre_rows = []
for i, d in enumerate(drows, 1):
    e = ne(d[0])
    cand = cov_by_entry.get(e, [])
    if len(cand) != 1:
        pre_rows.append(dict(delta_row=i, entry=e, cov_matches=len(cand), status="ABNORMAL")); continue
    ri = cand[0]
    cov = rows[ri]
    cov4 = cov[3]
    d4 = d[3]
    strict_prefix = d4.startswith(cov4) and len(d4) > len(cov4)
    other_cols_equal = all(cov[j] == d[j] for j in [0,1,2,4,5,6,7])
    before_col4[e] = dict(
        row_index_0based=ri,
        line_number=ri+2,   # header is line 1
        value=cov4,
        value_utf8_hex=cov4.encode("utf-8").hex(),
        grade=cov[4],
    )
    pre_rows.append(dict(
        delta_row=i, entry=e, line_number=ri+2,
        strict_prefix=strict_prefix,
        other7cols_byte_equal=other_cols_equal,
        delta_grade=d[4], cov_grade=cov[4],
        suffix_len_chars=len(d4)-len(cov4),
        cov4_has_char4a="④" in cov4,
        cov4_has_phrase="④ 活表槽位见证" in cov4,
        delta4_has_char4a="④" in d4,
        delta4_has_phrase="④ 活表槽位见证" in d4,
        delta4_has_LiteralWeizheng="[未证]" in d4,
        cov4_bytes_before_sha=hashlib.sha256(cov4.encode("utf-8")).hexdigest(),
    ))

# ---- in-memory AFTER counts (measure, do not extrapolate) ----
after_rows = [list(r) for r in rows]
for e, info in before_col4.items():
    ri = info["row_index_0based"]
    drow = next(d for d in drows if ne(d[0]) == e)
    after_rows[ri][3] = drow[3]

n_A_after = 0; n_B_after = 0
for r in after_rows:
    if len(r) >= 8 and r[4].strip() == "[已证]":
        if "④" in r[3]: n_A_after += 1
        if "④ 活表槽位见证" in r[3]: n_B_after += 1

baseline = dict(
    cov=dict(path=COV, bytes=len(cov_b), sha256=sha(cov_b), lf=cov_b.count(b"\n"),
             crlf=cov_b.count(b"\r\n"), bom=cov_b[:3]==b"\xef\xbb\xbf", trailing_lf=trailing_lf),
    panel=dict(path=PANEL, bytes=len(pan_b), sha256=sha(pan_b), lf=pan_b.count(b"\n"),
               crlf=pan_b.count(b"\r\n"), bom=pan_b[:3]==b"\xef\xbb\xbf",
               trailing_lf=pan_b.endswith(b"\n")),
    delta=dict(path=DELTA, bytes=len(delta_b), sha256=sha(delta_b), header=dhdr, nrows=len(drows)),
    header_cols=hdr_cols,
    invariants_before=dict(data_rows=len(rows), col_dist=dict(coldist),
        grade_yizheng=n_yz, yizheng_atlas_in=yz_atlas_in, yizheng_atlas_out=yz_atlas_out,
        cal_A=n_A, cal_B=n_B, clsid_none=n_CLSID_None,
        sec126_lines=n_126_lines, sec126_occ=n_126_occ),
    cal_after_in_memory=dict(cal_A=n_A_after, cal_B=n_B_after,
        net_A=n_A_after-n_A, net_B=n_B_after-n_B),
    pre_rows=pre_rows,
)

os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, "before_col4.json"), "w", encoding="utf-8") as f:
    json.dump(before_col4, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "baseline.json"), "w", encoding="utf-8") as f:
    json.dump(baseline, f, ensure_ascii=False, indent=1)

print("=== COVERAGE ===", json.dumps(baseline["cov"], ensure_ascii=False))
print("=== PANEL ===", json.dumps(baseline["panel"], ensure_ascii=False))
print("=== DELTA ===", json.dumps(baseline["delta"], ensure_ascii=False))
print("=== HEADER ===", hdr_cols)
print("=== INVARIANTS BEFORE ===", json.dumps(baseline["invariants_before"], ensure_ascii=False))
print("=== CAL AFTER (in-memory) ===", json.dumps(baseline["cal_after_in_memory"], ensure_ascii=False))
print("=== PRE ROWS ===")
for p in pre_rows:
    print(json.dumps(p, ensure_ascii=False))
print("strict_prefix_total", sum(1 for p in pre_rows if p.get("strict_prefix")), "/", len(drows))
