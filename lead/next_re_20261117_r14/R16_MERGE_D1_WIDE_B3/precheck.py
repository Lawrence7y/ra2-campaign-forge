# -*- coding: utf-8 -*-
"""R16-MERGE-D1-WIDE-B3 · 只读预检 + 落 pin / before_col4 / baseline。

只读打开 coverage.tsv / PANEL.md / delta.tsv / function_atlas.tsv；
只写本目录（_pin_coverage.tsv / _pin_PANEL.md / before_col4.json / baseline.json）。

17 行来源：R16_D1_WIDE_B3/delta.tsv 的 18 行里排除 005F4B10，余 17 行第 4 列照抄；
第 4 列之外 7 列逐字节不动，grade 不动。
"""
import csv, hashlib, json, os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")

PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
OUT  = os.path.join(ROOT, "R16_MERGE_D1_WIDE_B3")
COV  = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
PANEL= os.path.join(ROOT, "COVERAGE", "PANEL.md")
DELTA= os.path.join(ROOT, "R16_D1_WIDE_B3", "delta.tsv")
ATLAS= os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
EXCLUDE = {"005F4B10"}

def sha(b): return hashlib.sha256(b).hexdigest()
def ne(e):
    e = e.strip().upper()
    if e.startswith("0X"): e = e[2:]
    try: return "%08X" % int(e, 16)
    except ValueError: return e

os.makedirs(OUT, exist_ok=True)

# ---- read raw bytes ----
cov_b  = open(COV, "rb").read()
pan_b  = open(PANEL, "rb").read()
delta_b= open(DELTA, "rb").read()

# ---- write pins (own dir only) ----
open(os.path.join(OUT, "_pin_coverage.tsv"), "wb").write(cov_b)
open(os.path.join(OUT, "_pin_PANEL.md"), "wb").write(pan_b)

# ---- parse coverage at byte level ----
trailing_lf = cov_b.endswith(b"\n")
txt = cov_b.decode("utf-8")
all_lines = txt.split("\n")
header = all_lines[0]
data_lines = all_lines[1:]
if trailing_lf:
    data_lines = data_lines[:-1]
hdr_cols = header.split(",")
rows = [ln.split("\t") for ln in data_lines]

coldist = collections.Counter(len(r) for r in rows)
n_yz = yz_atlas_in = yz_atlas_out = 0
n_A = n_B = 0
n_126_lines = n_126_occ = 0
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
    if "§12.6" in r[3]:
        n_126_lines += 1
        n_126_occ += r[3].count("§12.6")

# ---- parse delta ----
def parse_delta(b):
    dl = b.decode("utf-8-sig").split("\n")
    if dl and dl[-1] == "": dl = dl[:-1]
    hdr = dl[0].split("\t")
    drs = [ln.split("\t") for ln in dl[1:]]
    return hdr, drs

dh, drows = parse_delta(delta_b)
assert dh == hdr_cols, (dh, hdr_cols)
assert len(drows) == 18, len(drows)
assert all(len(d) == 8 for d in drows)
d_entries = [ne(d[0]) for d in drows]
assert len(set(d_entries)) == 18
assert EXCLUDE.issubset(set(d_entries)), EXCLUDE

# 17 rows = 18 minus excluded
target = [d for d in drows if ne(d[0]) not in EXCLUDE]
t_entries = [ne(d[0]) for d in target]
assert len(target) == 17, len(target)

# ---- locate each entry on disk (unique) ----
cov_by_entry = {}
for idx, r in enumerate(rows):
    if len(r) >= 8:
        cov_by_entry.setdefault(ne(r[0]), []).append(idx)

before_col4 = {}
pre_rows = []
for d in target:
    e = ne(d[0])
    cand = cov_by_entry.get(e, [])
    if len(cand) != 1:
        pre_rows.append(dict(entry=e, cov_matches=len(cand), status="ABNORMAL")); continue
    ri = cand[0]
    cov = rows[ri]
    cov4 = cov[3]
    new4 = d[3]
    strict_prefix = new4.startswith(cov4) and len(new4) > len(cov4)
    other_cols_equal = all(cov[j] == d[j] for j in [0,1,2,4,5,6,7])
    before_col4[e] = dict(
        row_index_0based=ri,
        line_number=ri+2,   # header is line 1
        value=cov4,
        value_utf8_hex=cov4.encode("utf-8").hex(),
        grade=cov[4],
    )
    pre_rows.append(dict(
        entry=e, line_number=ri+2,
        strict_prefix=strict_prefix,
        other7cols_byte_equal=other_cols_equal,
        delta4_grade=d[4], cov_grade=cov[4],
        suffix_len_chars=len(new4)-len(cov4),
        cov4_has_char4a="④" in cov4,
        cov4_has_phrase="④ 活表槽位见证" in cov4,
        cov4_has_126="§12.6" in cov4,
        new4_has_char4a="④" in new4,
        new4_has_phrase="④ 活表槽位见证" in new4,
        new4_has_126="§12.6" in new4,
        new4_126_occ=new4.count("§12.6"),
    ))

assert len(before_col4) == 17, len(before_col4)
assert all(p.get("strict_prefix") for p in pre_rows), [p for p in pre_rows if not p.get("strict_prefix")]
assert all(p.get("other7cols_byte_equal") for p in pre_rows)

# excluded row on disk: capture its col4 for check ②
ex_rows = [d for d in drows if ne(d[0]) in EXCLUDE]
assert len(ex_rows) == 1
ex_e = ne(ex_rows[0][0])
assert len(cov_by_entry.get(ex_e, [])) == 1
ex_ri = cov_by_entry[ex_e][0]
ex_col4 = rows[ex_ri][3]
ex_grade = rows[ex_ri][4]

# ---- in-memory AFTER counts (measure, do not extrapolate) ----
after_rows = [list(r) for r in rows]
for e, info in before_col4.items():
    ri = info["row_index_0based"]
    after_rows[ri][3] = next(d[3] for d in target if ne(d[0]) == e)

n_A_after = n_B_after = n_126_lines_after = n_126_occ_after = 0
for r in after_rows:
    if len(r) >= 8 and r[4].strip() == "[已证]":
        if "④" in r[3]: n_A_after += 1
        if "④ 活表槽位见证" in r[3]: n_B_after += 1
    if "§12.6" in r[3]:
        n_126_lines_after += 1
        n_126_occ_after += r[3].count("§12.6")

baseline = dict(
    cov=dict(path=COV, bytes=len(cov_b), sha256=sha(cov_b), lf=cov_b.count(b"\n"),
             crlf=cov_b.count(b"\r\n"), bom=cov_b[:3]==b"\xef\xbb\xbf", trailing_lf=trailing_lf),
    panel=dict(path=PANEL, bytes=len(pan_b), sha256=sha(pan_b), lf=pan_b.count(b"\n"),
               crlf=pan_b.count(b"\r\n"), bom=pan_b[:3]==b"\xef\xbb\xbf",
               trailing_lf=pan_b.endswith(b"\n")),
    delta=dict(path=DELTA, bytes=len(delta_b), sha256=sha(delta_b), header=dh, nrows=len(drows)),
    header_cols=hdr_cols,
    excluded=dict(entry=ex_e, line_number=ex_ri+2, col4=ex_col4,
                  col4_utf8_hex=ex_col4.encode("utf-8").hex(), grade=ex_grade,
                  delta_col4=ex_rows[0][3]),
    invariants_before=dict(data_rows=len(rows), col_dist=dict(coldist),
        grade_yizheng=n_yz, yizheng_atlas_in=yz_atlas_in, yizheng_atlas_out=yz_atlas_out,
        cal_A=n_A, cal_B=n_B, sec126_lines=n_126_lines, sec126_occ=n_126_occ),
    cal_after_in_memory=dict(cal_A=n_A_after, cal_B=n_B_after,
        net_A=n_A_after-n_A, net_B=n_B_after-n_B,
        sec126_lines=n_126_lines_after, sec126_occ=n_126_occ_after,
        sec126_lines_net=n_126_lines_after-n_126_lines,
        sec126_occ_net=n_126_occ_after-n_126_occ),
    pre_rows=pre_rows,
)

with open(os.path.join(OUT, "before_col4.json"), "w", encoding="utf-8") as f:
    json.dump(before_col4, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "baseline.json"), "w", encoding="utf-8") as f:
    json.dump(baseline, f, ensure_ascii=False, indent=1)

print("=== COVERAGE ===", json.dumps(baseline["cov"], ensure_ascii=False))
print("=== PANEL ===", json.dumps(baseline["panel"], ensure_ascii=False))
print("=== DELTA ===", json.dumps(baseline["delta"], ensure_ascii=False))
print("=== HEADER ===", hdr_cols)
print("=== EXCLUDED ===", json.dumps(baseline["excluded"], ensure_ascii=False)[:400])
print("=== INVARIANTS BEFORE ===", json.dumps(baseline["invariants_before"], ensure_ascii=False))
print("=== AFTER (in-memory) ===", json.dumps(baseline["cal_after_in_memory"], ensure_ascii=False))
print("=== PRE ROWS (17) ===")
for p in pre_rows:
    print(json.dumps(p, ensure_ascii=False))
print("strict_prefix_total", sum(1 for p in pre_rows if p.get("strict_prefix")), "/ 17")
